"""ARCHETYPE experiment protocol: one seed = training world -> freeze -> transfer world, false-analogy
world and interventional pairs, with every agent on identical environments and budgets.

Evaluator-side module: it owns the environments and all noise-free bookkeeping. Agents only ever receive a
``Ctx`` (learner-visible view + counted callbacks).
"""
from __future__ import annotations

import copy
import time
from typing import Any, Dict, List, Optional

from archetype import VERSION
from archetype.architecture import generate as Gen
from archetype.architecture import graph as G
from archetype.architecture import roles as R
from archetype.architecture.primitives import PRIMITIVE_GRAMMAR_VERSION
from archetype.baselines.base import BudgetExhausted, Ctx, Experience, explore
from archetype.baselines.transfer_agents import surface_similarity
from archetype.environments.world import Environment, Lab, make_env
from archetype.experiments.roster import ROSTER, build_agent
from archetype.latent_structure.families import FAMILIES, families, shift_genome
from archetype.latent_structure.fitness import FITNESS_VERSION
from archetype.latent_structure.genome import HIDDEN_ONLY, PROPERTIES
from archetype.learner.archetype_agent import LEARNER_VERSION
from archetype.learner.transformations import TRANSFORMATIONS, present
from archetype.metrics.reference import gap_closure, reference_optimum, transformation_effects
from archetype.util import rng_for, stable_hash

DEFAULT_CONFIG: Dict[str, Any] = {
    "train_budget": 60, "phase1_budget": 40, "phase2_budget": 20, "surfaces": 3,
    "agents": list(ROSTER), "train_families": None, "test_families": None,
    "intervention_agents": ["archetype", "archetype_no_structural_memory", "archetype_no_counterfactual", "principle_memory", "search_screen", "surface_similarity"],
    "intervention_families": None, "intervention_properties": list(PROPERTIES), "interventions": True,
    "decoupled_control": True,
    "surface_offset": 0, "extra_false_families": [],      # used only by the replication of spec §35
}
EXECUTOR = "inprocess-simulator"


# ---------------------------------------------------------------------------------- bookkeeping

class RefSet:
    """Role-level record of every architecture observed in training (for novelty / memorized-transfer checks)."""

    def __init__(self):
        self.items: Dict[str, Any] = {}
        self._cache: Dict[str, float] = {}

    def add(self, env: Environment, arch: G.ArchGraph) -> None:
        tree = env.role_tree(arch)
        k = G._key(tree)
        if k not in self.items:
            self.items[k] = (tree, env.features(arch))

    def novelty(self, env: Environment, arch: G.ArchGraph) -> float:
        tree = env.role_tree(arch)
        k = G._key(tree)
        if k not in self._cache:
            self._cache[k] = 0.0 if k in self.items else R.novelty(tree, env.features(arch), list(self.items.values()))
        return self._cache[k]


class Tracker:
    """Counts evaluations and follows the declared incumbent with noise-free utility (never shown to agents)."""

    def __init__(self, env: Environment, ref: Dict[str, Any]):
        self.env, self.ref = env, ref
        self.evals = self.failures = 0
        self.incumbent: Optional[G.ArchGraph] = None
        self.e2u: Optional[int] = None
        self.curve: List[List[float]] = []
        self.cost = 0.0

    def on_eval(self, arch: G.ArchGraph, res: Dict[str, Any]) -> None:
        self.evals += 1
        self.failures += int(res["failed"])
        self.cost += res["cost"] / self.env.shape["currency"]

    def on_declare(self, arch: G.ArchGraph) -> None:
        self.incumbent = arch
        u = self.env.true_utility(arch)
        self.curve.append([self.evals, round(gap_closure(u, self.ref), 4)])
        if self.e2u is None and u >= self.ref["useful_threshold"] - 1e-12:
            self.e2u = self.evals


def make_ctx(env: Environment, budget: int, key: tuple, tracker: Optional[Tracker] = None, refset: Optional[RefSet] = None, phase: int = 1) -> Ctx:
    rng_eval = rng_for("eval", *key)

    def evaluate(arch: G.ArchGraph) -> Dict[str, Any]:
        res = env.evaluate(arch, rng_eval)
        if tracker:
            tracker.on_eval(arch, res)
        if refset is not None and res["valid"]:
            refset.add(env, arch)
        return res

    def declare(arch: G.ArchGraph) -> None:
        if tracker:
            tracker.on_declare(arch)

    return Ctx(env.view(), budget, evaluate, declare, rng_for("agent", *key), phase=phase)


class LabSession:
    """Training-time intervention access for one agent (spec §27). Not available after the freeze."""

    def __init__(self, lab: Lab, seed: int, agent: str, refset: RefSet):
        self.lab, self.seed, self.agent, self.refset = lab, seed, agent, refset
        self.evaluations = 0
        self.closed = False

    @property
    def n_knobs(self) -> int:
        return self.lab.n_knobs

    def open(self, token: str, knob: int, direction: str, budget: int) -> Ctx:
        if self.closed:
            raise RuntimeError("the intervention lab is closed after training (learned knowledge is frozen)")
        env = self.lab.intervene(token, knob, direction)
        self.evaluations += budget
        return make_ctx(env, budget, (self.seed, "cf", self.agent, token, knob, direction), refset=self.refset)


# ---------------------------------------------------------------------------------- per-architecture facts

def removal_effect(env: Environment, cfg: Gen.Config, t: str) -> float:
    """Noise-free utility lost by removing transformation ``t`` from ``cfg`` (negative: the element hurts)."""
    key, value, _ = TRANSFORMATIONS[t]
    lower = dict(cfg)
    lower[key] = {"h": value - 1, "g": value - 1}.get(key, Gen.BASE[key])
    lower = Gen.normalize_config(lower, env.primitives)
    return env.true_utility(Gen.compose(cfg, env.primitives)) - env.true_utility(Gen.compose(lower, env.primitives))


def describe_arch(env: Environment, arch: G.ArchGraph, ref: Dict[str, Any], refset: RefSet) -> Dict[str, Any]:
    f = env.features(arch)
    u = env.true_utility(arch)
    cfg = arch.metadata.get("config")
    opt = Gen.compose(ref["config"], env.primitives)
    return {"hash": arch.hash(), "config": cfg, "utility": round(u, 5), "regret": round(ref["utility"] - u, 5), "gap": round(gap_closure(u, ref), 4), "useful": u >= ref["useful_threshold"] - 1e-12,
            "organization": R.organization(f), "operations": f["n_ops"], "nodes": f["n_nodes"], "cost": round(f["cost"], 3), "latency": round(f["latency"], 2),
            "memory": round(f["memory"], 2), "novelty": round(refset.novelty(env, arch), 4),
            "distance_to_optimum": round(R.role_distance(env.role_tree(arch), f, env.role_tree(opt), env.features(opt))["aggregate"], 4),
            "present": [t for t in TRANSFORMATIONS if cfg and present(t, cfg)],
            "harmful": [t for t in TRANSFORMATIONS if cfg and present(t, cfg) and removal_effect(env, cfg, t) < -0.01]}


def env_record(env: Environment, ref: Dict[str, Any], train: Dict[str, Any], seed: int) -> Dict[str, Any]:
    eff = transformation_effects(env)
    rec = {**env.provenance(), "reference": {"config": ref["config"], "utility": round(ref["utility"], 5), "base_utility": round(ref["base_utility"], 5),
                                             "organization": R.organization(env.features(Gen.compose(ref["config"], env.primitives)))},
           "truth_effects": {t: round(v, 5) for t, v in eff.items()}, "space_size": Gen.space_size(env.primitives), "primitives": len(env.primitives),
           "latent_distance_nearest_train": round(min(env.genome.distance(e.genome) for e in train["envs"]), 4),
           "surface_similarity_nearest_train": round(max(surface_similarity(env.view(), e.view()) for e in train["envs"]), 4)}
    fam = env.family
    if fam.matched:
        m = train["by_key"].get((fam.matched, env.surface_index))
        if m is not None:
            meff = train["effects"][(fam.matched, env.surface_index)]
            rec["matched"] = {"family": fam.matched, "latent_distance": round(env.genome.distance(m.genome), 4), "surface_similarity": round(surface_similarity(env.view(), m.view()), 4)}
            # trap: helped in the look-alike training environment, hurts here
            rec["traps"] = [t for t in TRANSFORMATIONS if meff[t] > 0.02 and eff[t] < -0.005]
            src_cfg = Gen.normalize_config(train["refs"][(fam.matched, env.surface_index)]["config"], env.primitives)
            rec["matched_optimum_gap_here"] = round(gap_closure(env.true_utility(Gen.compose(src_cfg, env.primitives)), ref), 4)
    return rec


# ---------------------------------------------------------------------------------- episodes

def run_phase(agent, ctx: Ctx, phase: int, incumbent: Optional[Gen.Config]) -> None:
    try:
        if phase == 1:
            agent.act(ctx)
        else:
            agent.phase2(ctx, incumbent)
    except BudgetExhausted:
        pass


def run_episode(agent, env: Environment, ref: Dict[str, Any], env2: Environment, ref2: Dict[str, Any], seed: int, cfg: Dict[str, Any], refset: RefSet,
                phases: int = 2, matched: Optional[Environment] = None) -> Dict[str, Any]:
    key = (seed, env.family.id, env.surface_index, agent.name)
    if getattr(agent, "privileged", False):
        agent.attach(env)
    scores = agent.transfer_scores(env.view())
    agent.report = {}
    tr = Tracker(env, ref)
    ctx = make_ctx(env, cfg["phase1_budget"], key + (1,), tr)
    run_phase(agent, ctx, 1, None)
    if tr.incumbent is None:
        tr.on_declare(Gen.compose(Gen.BASE, env.primitives))
    final = tr.incumbent
    rec: Dict[str, Any] = {"agent": agent.name, "family": env.family.id, "world": env.family.world, "surface": env.surface_index, "seed": seed,
                           "scores": {t: round(v, 4) for t, v in scores.items()} if scores else None,
                           "phase1": {"evaluations": tr.evals, "e2u": tr.e2u, "failures": tr.failures, "evaluation_cost": round(tr.cost, 3), "curve": tr.curve,
                                      "final": describe_arch(env, final, ref, refset)}}
    if matched is not None and scores:
        # evaluator-side question (spec §10): how transferable does the frozen learner consider the look-alike training environment?
        ms = agent.transfer_scores(matched.view())
        rec["matched_scores"] = {t: round(v, 4) for t, v in ms.items()}
    report = copy.deepcopy(agent.report)
    for k in ("proposal", "prediction"):          # proposal: built after testing; prediction: built from frozen knowledge alone
        if report.get(k) is not None:
            rec["phase1"][k] = describe_arch(env, Gen.compose(report[k], env.primitives), ref, refset)
    if phases >= 2:
        if getattr(agent, "privileged", False):
            agent.attach(env2)
        tr2 = Tracker(env2, ref2)
        ctx2 = make_ctx(env2, cfg["phase2_budget"], key + (2,), tr2, phase=2)
        inc_cfg = final.metadata.get("config") or dict(Gen.BASE)
        tr2.on_declare(Gen.compose(inc_cfg, env2.primitives))
        run_phase(agent, ctx2, 2, inc_cfg)
        rec["phase2"] = {"evaluations": tr2.evals, "e2u": tr2.e2u, "failures": tr2.failures, "kept_gap": tr2.curve[0][1],
                         "final": describe_arch(env2, tr2.incumbent, ref2, refset), "regime": copy.deepcopy(agent.report.get("regime"))}
    report.pop("phase2", None)
    rec["report"] = report
    return rec


# ---------------------------------------------------------------------------------- one seed

def run_seed(seed: int, config: Optional[Dict[str, Any]] = None, provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    t0 = time.time()
    lab, refset = Lab(seed), RefSet()
    train_fams = [f for f in families("train") if not cfg["train_families"] or f.id in cfg["train_families"]]
    test_fams = [f for f in families("transfer") + families("false") if not cfg["test_families"] or f.id in cfg["test_families"]]
    test_fams += [FAMILIES[f] for f in cfg["extra_false_families"]]
    surfaces = range(cfg["surface_offset"], cfg["surface_offset"] + cfg["surfaces"])
    # ---- training world (shared exploration; identical for every agent)
    experience: List[Experience] = []
    train: Dict[str, Any] = {"envs": [], "by_key": {}, "effects": {}, "refs": {}}
    for fam in train_fams:
        for s in surfaces:
            env = make_env(fam.id, seed, s)
            lab.register(env)
            ctx = make_ctx(env, cfg["train_budget"], (seed, "explore", fam.id, s), refset=refset)
            try:
                experience.append(explore(ctx))
            except BudgetExhausted:
                raise RuntimeError("training exploration exceeded its budget")
            train["envs"].append(env)
            train["by_key"][(fam.id, s)] = env
            train["effects"][(fam.id, s)] = transformation_effects(env)
            train["refs"][(fam.id, s)] = reference_optimum(env)
    # ---- fit and freeze
    agents, snapshots = {}, {}
    for name in cfg["agents"]:
        a = build_agent(name)
        session = LabSession(lab, seed, name, refset) if a.uses_lab else None
        a.fit(copy.deepcopy(experience), session)
        if session:
            session.closed = True
        snap = a.snapshot()
        snapshots[name] = {"hash": stable_hash(snap), "training_evaluations": sum(e.evaluations for e in experience),
                           "counterfactual_evaluations": session.evaluations if session else 0, "snapshot": snap if name.startswith("archetype") else None}
        agents[name] = a
    frozen = {n: s["hash"] for n, s in snapshots.items()}
    # ---- transfer and false-analogy worlds
    envs, episodes = [], []
    for fam in test_fams:
        for s in surfaces:
            env = make_env(fam.id, seed, s)
            ref = reference_optimum(env)
            shifted = rng_for("shift?", seed, fam.id, s).random() < 0.5
            g2, prop = shift_genome(fam, env.genome, seed * 31 + s) if shifted else (env.genome, None)
            env2 = env.with_genome(g2, window=1)
            ref2 = reference_optimum(env2)
            er = env_record(env, ref, train, seed)
            er["phase2"] = {"shifted": shifted, "property": prop, "hidden_only": prop in HIDDEN_ONLY if prop else None, "genome_hash": g2.hash(),
                            "reference_utility": round(ref2["utility"], 5)}
            envs.append(er)
            for name, a in agents.items():
                episodes.append(run_episode(a, env, ref, env2, ref2, seed, cfg, refset, matched=train["by_key"].get((fam.matched, s)) if fam.matched else None))
    # ---- control: observations generated from a DIFFERENT family's structure than the one that drives fitness.
    # If the learner's predictions come from observed structure, they must stop tracking the truth here.
    controls = []
    if cfg["decoupled_control"] and "archetype" in agents and len(test_fams) > 1:
        for i, fam in enumerate(test_fams):
            other = test_fams[(i + len(test_fams) // 2) % len(test_fams)]
            for s in surfaces:
                env = Environment(fam, seed, s, obs_genome=make_env(other.id, seed, s).genome)
                sc = agents["archetype"].transfer_scores(env.view())
                controls.append({"family": fam.id, "surface": s, "observations_from": other.id, "scores": {t: round(v, 4) for t, v in sc.items()}})
    # ---- interventional pairs (frozen agents; exactly one latent property differs within a pair)
    interventions = []
    if cfg["interventions"]:
        ifams = [f for f in families("transfer") if (not cfg["intervention_families"] or f.id in cfg["intervention_families"]) and (not cfg["test_families"] or f.id in cfg["test_families"])]
        for fam in ifams:
            base = make_env(fam.id, seed, cfg["surface_offset"])
            for prop in cfg["intervention_properties"]:
                for level, value in (("low", 0.1), ("high", 0.9)):
                    env = base.with_genome(base.genome.intervene(prop, value), window=2)
                    ref = reference_optimum(env)
                    eff = transformation_effects(env)
                    row = {"seed": seed, "family": fam.id, "property": prop, "hidden_only": prop in HIDDEN_ONLY, "level": level, "genome_hash": env.genome.hash(),
                           "truth_effects": {t: round(v, 5) for t, v in eff.items()}, "optimum_present": [t for t in TRANSFORMATIONS if present(t, ref["config"])], "agents": {}}
                    for name in cfg["intervention_agents"]:
                        if name not in agents:
                            continue
                        a = agents[name]
                        e = run_episode(a, env, ref, env, ref, seed, cfg, refset, phases=1)
                        row["agents"][name] = {"scores": e["scores"], "present": e["phase1"]["final"]["present"], "gap": e["phase1"]["final"]["gap"],
                                               "e2u": e["phase1"]["e2u"], "evaluations": e["phase1"]["evaluations"]}
                    interventions.append(row)
    # the frozen knowledge must be unchanged by testing
    for name, a in agents.items():
        if stable_hash(a.snapshot()) != frozen[name]:
            raise RuntimeError(f"agent {name} changed its frozen knowledge during evaluation")
    result = {"seed": seed, "config": cfg, "config_hash": stable_hash(cfg), "environments": envs, "episodes": episodes, "interventions": interventions, "controls": controls,
              "agents": snapshots, "training": {"environments": len(experience), "observed_role_graphs": len(refset.items),
                                                "intervention_log": [{k: v for k, v in x.items() if k != "value"} for x in lab.log][:0]}}
    result["record_hash"] = stable_hash({k: result[k] for k in ("environments", "episodes", "interventions")})
    result["provenance"] = {**(provenance or {}), "seed": seed, "versions": {"archetype": VERSION, "ir": G.IR_VERSION, "fitness": FITNESS_VERSION,
                            "primitive_grammar": PRIMITIVE_GRAMMAR_VERSION, "learner": LEARNER_VERSION}, "executor": EXECUTOR,
                            "resource_limits": {"train_budget": cfg["train_budget"], "phase1_budget": cfg["phase1_budget"], "phase2_budget": cfg["phase2_budget"], **G.LIMITS},
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wall_seconds": round(time.time() - t0, 1)}
    return result
