"""ARCHETYPE unit tests (spec §36)."""
import itertools
import random

import pytest

from archetype.architecture import generate as Gen
from archetype.architecture import graph as G
from archetype.architecture import roles as R
from archetype.environments.world import Lab, make_env
from archetype.experiments import sanity
from archetype.experiments.protocol import run_seed
from archetype.latent_structure import fitness as F
from archetype.latent_structure.families import FAMILIES, HOLDOUT_PAIRS, TRAIN_PAIRS, families, sample_genome
from archetype.latent_structure.genome import HIDDEN_ONLY, OBSERVABLE, PROPERTIES, EnvironmentGenome
from archetype.learner.encoder import encode
from archetype.learner.relation import fit_principle
from archetype.memory.principles import Principle, PrincipleStore
from archetype.metrics import analysis as A
from archetype.metrics import core as M
from archetype.metrics.reference import reference_optimum, transformation_effects
from archetype.transfer import decisions as D

SMALL = {"train_families": ["T00", "T03"], "test_families": ["B00", "F00"], "surfaces": 2, "interventions": True, "intervention_properties": ["failure_cost", "parallelizability"],
         "agents": ["search", "search_screen", "surface_similarity", "principle_memory", "latent_oracle", "archetype", "archetype_no_structural_memory", "archetype_no_counterfactual"],
         "train_budget": 40, "phase1_budget": 20, "phase2_budget": 8}


@pytest.fixture(scope="module")
def small_run():
    return run_seed(5, SMALL)


# ---------------------------------------------------------------- latent environment generation
def test_genome_generation_is_deterministic_and_respects_family_pins():
    for fam in FAMILIES.values():
        g = sample_genome(fam, 3)
        assert g == sample_genome(fam, 3) and g.hash() == sample_genome(fam, 3).hash()
        assert g != sample_genome(fam, 4)
        if fam.world != "false":
            for prop, level in fam.pinned().items():
                assert (g[prop] >= 0.75) if level == "hi" else (g[prop] <= 0.2)


def test_matrix_and_holdout_combinations():
    assert len(families("train")) == 10 and len(families("transfer")) == 10 and len(families("false")) == 10
    assert not {frozenset(p) for p in HOLDOUT_PAIRS} & {frozenset(p) for p in TRAIN_PAIRS}
    seen = {f for p in TRAIN_PAIRS for f in p}
    assert all(f in seen for p in HOLDOUT_PAIRS for f in p)      # hold-outs are new COMBINATIONS of seen factors


def test_false_analogy_keeps_observables_and_flips_hidden():
    for fam in families("false"):
        src, g = sample_genome(FAMILIES[fam.matched], 2), sample_genome(fam, 2)
        assert all(g[p] == src[p] for p in OBSERVABLE)
        assert any(abs(g[p] - src[p]) > 0.5 for p in HIDDEN_ONLY)


def test_fitness_is_hidden_noisy_and_structure_dependent():
    env = make_env("T00", 0, 0)
    arch = Gen.compose({**Gen.BASE, "g": 1}, env.primitives)
    f = env.features(arch)
    draws = {round(F.sample(env.genome, f, random.Random(i))["utility"], 6) for i in range(20)}
    assert len(draws) > 10                                          # stochastic
    lo, hi = env.genome.intervene("failure_cost", 0.05), env.genome.intervene("failure_cost", 0.95)
    base = env.features(Gen.compose(Gen.BASE, env.primitives))
    assert (F.true_utility(hi, f) - F.true_utility(hi, base)) > (F.true_utility(lo, f) - F.true_utility(lo, base))


# ---------------------------------------------------------------- surface randomization
def test_surfaces_of_one_family_share_structure_not_vocabulary():
    a, b, c = (make_env("T02", 1, i) for i in range(3))
    assert a.genome == b.genome == c.genome
    assert not set(a.primitives) & set(b.primitives) and not set(a.primitives) & set(c.primitives)
    assert a.surface_seed != b.surface_seed and c.scrambled and not a.scrambled


def test_encoder_is_invariant_to_surface_randomization():
    rng = random.Random(1)
    v = make_env("T05", 0, 0).view()
    f0, f1 = encode(v), encode(sanity.randomized_view(v, rng))
    assert all(abs(f0[k] - f1[k]) <= 1e-6 * (1 + abs(f0[k])) for k in f0)


def test_learner_view_contains_nothing_latent():
    for fam, s in itertools.product(["T00", "B03", "H01", "F07"], range(3)):
        assert sanity.leaked_terms(make_env(fam, 0, s)) == []
    assert sanity.import_violations() == []


def test_hidden_properties_never_reach_observations():
    env = make_env("T04", 0, 1)
    for p in HIDDEN_ONLY:
        other = env.with_genome(env.genome.intervene(p, 0.99 - env.genome[p]))
        assert {k: v for k, v in other.view().items() if k != "token"} == {k: v for k, v in env.view().items() if k != "token"}


# ---------------------------------------------------------------- architecture generation / canonicalization
def test_every_configuration_composes_to_a_valid_architecture():
    env = make_env("H00", 0, 0)
    rng = random.Random(0)
    hashes = set()
    for _ in range(300):
        g = Gen.compose(Gen.random_config(rng, env.primitives), env.primitives)
        assert G.validate(g.root, env.primitives) == []
        hashes.add(g.hash())
    for e in (make_env(f, 1, s) for f in ("T00", "T07", "B03", "F05") for s in range(3)):      # the largest expressible architecture is valid everywhere
        opt = Gen.options(e.primitives)
        assert G.validate(Gen.compose({k: max(v) for k, v in opt.items()}, e.primitives).root, e.primitives) == []
    assert len(hashes) > 150 and Gen.space_size(env.primitives) >= 1000
    for _ in range(100):
        assert G.validate(Gen.random_tree(rng, env.primitives), env.primitives) == []


def test_canonicalization():
    a = G.ArchGraph(root=G.parallel([G.unit("x"), G.serial([G.unit("y"), G.serial([G.unit("z")])])], "m"))
    b = G.ArchGraph(root=G.parallel([G.serial([G.unit("y"), G.unit("z")]), G.unit("x")], "m"), name="other")
    assert a.hash() == b.hash()
    assert a.hash() != G.ArchGraph(root=G.parallel([G.unit("x"), G.unit("y")], "m")).hash()
    child = a.derive(G.unit("x"))
    assert child.parent_hash == a.hash() and child.lineage == [a.hash()]


def test_validation_rejects_wrong_signatures():
    env = make_env("T00", 0, 0)
    c = Gen.classify(env.primitives)
    assert G.validate(G.parallel([G.unit(c["exec"][0]), G.unit(c["exec"][0])], c["exec"][0]), env.primitives)      # merge is not fan-in
    assert G.validate(G.unit("no_such_primitive"), env.primitives)
    assert env.evaluate(G.ArchGraph(root=G.unit("no_such_primitive")), random.Random(0))["valid"] is False


def test_organizations_are_structural():
    env = make_env("T02", 0, 0)
    orgs = {name: R.organization(env.features(Gen.compose({**Gen.BASE, **cfg}, env.primitives))) for name, cfg in {
        "ARCH_1": {}, "ARCH_2": {"h": 1}, "ARCH_3": {"h": 1, "w": 3}, "ARCH_4": {"h": 1, "g": 1}, "ARCH_5": {"loop": 2}, "ARCH_6": {"mem": 1, "g": 1},
        "ARCH_7": {"route": 2}, "ARCH_8": {"h": 2}, "ARCH_9": {"r": 3}, "ARCH_10": {"tune": 1}}.items()}
    assert all(k == v for k, v in orgs.items()), orgs


# ---------------------------------------------------------------- structural distance / reconstruction
def test_structural_distance_and_reconstruction_across_inventories():
    a, b = make_env("T00", 0, 0), make_env("H02", 0, 1)
    assert not set(a.primitives) & set(b.primitives)
    cfg = {**Gen.BASE, "h": 1, "w": 3, "g": 1}
    ga, gb = Gen.compose(cfg, a.primitives), Gen.compose(cfg, b.primitives)
    d = R.role_distance(a.role_tree(ga), a.features(ga), b.role_tree(gb), b.features(gb))
    assert d["organization_features"] == 0 and d["aggregate"] < R.MEMORIZED_THRESHOLD       # equivalent although no name is shared
    gc = Gen.compose({**Gen.BASE, "r": 3, "mem": 1}, b.primitives)
    d2 = R.role_distance(a.role_tree(ga), a.features(ga), b.role_tree(gc), b.features(gc))
    d3 = R.role_distance(b.role_tree(gc), b.features(gc), a.role_tree(ga), a.features(ga))
    assert d2["aggregate"] > R.MEMORIZED_THRESHOLD and abs(d2["aggregate"] - d3["aggregate"]) < 1e-12
    assert R.novelty(a.role_tree(ga), a.features(ga), []) == 1.0


# ---------------------------------------------------------------- principles
def _rows(n=40, seed=0):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        x = {"a": rng.random(), "b": rng.random(), "junk": rng.random(), **{f"j{k}": rng.random() for k in range(7)}}
        y = (0.2 if x["a"] > 0.5 and x["b"] < 0.6 else -0.05) + rng.gauss(0, 0.01)
        rows.append((x, y, f"tok{i}"))
    return rows


def test_principle_creation_recovers_relation_and_contraindication():
    feats = ["a", "b", "junk"] + [f"j{k}" for k in range(7)]
    X = lambda a, b: {"a": a, "b": b, "junk": 0.5, **{f"j{k}": 0.5 for k in range(7)}}
    p = fit_principle("gate", _rows(), feats, "P00")
    assert p.antecedent and {"a", "b"} <= set(p.features_used()) and "junk" not in p.features_used()
    assert p.predict(X(0.9, 0.1))["p_help"] > 0.7
    assert p.predict(X(0.1, 0.1))["p_help"] < 0.3
    assert any(c["kind"] == "observable" for c in p.contraindications)           # a > .5 but b high: must NOT be used
    assert p.predict(X(0.9, 0.9))["contraindicated"]
    assert all(not t.startswith("T0") for t in p.source_environments) and "IF" in p.describe()


def test_principle_contradiction_confidence_and_forgetting():
    p = Principle(id="P", transformation="gate")
    c0 = p.confidence
    p.record_test(True, 1, "counterfactual", {"knob": 0})
    assert p.confidence > c0 and p.counterfactual_results[-1]["correct"]
    for i in range(3):
        p.record_test(False, 2 + i, "transfer")
    assert p.contradiction_count == 3 and p.failed_transfers == 3 and p.status == "CONTRADICTED"
    for i in range(8):
        p.record_test(False, 9 + i, "counterfactual")
    assert p.status == "RETIRED" and not p.active
    store = PrincipleStore()
    store.put(p)
    store.put(Principle(id="Q", transformation="tune"))
    assert store.forget() == 1 and [q.id for q in store.active()] == ["Q"] and len(store.retired) == 1


# ---------------------------------------------------------------- decisions / abstention
def test_transfer_decisions_and_abstention():
    def pred(c, contra=False, oor=False):
        return {"confidence": c, "p_help": c, "contraindicated": contra, "out_of_range": oor, "expected": 0.1}
    assert D.decide(pred(0.9), False) == "TRUST"
    assert D.decide(pred(0.9), True) == "TEST"                 # unobservable condition known: never trusted blindly
    assert D.decide(pred(0.9, contra=True), False) == "REJECT"
    assert D.decide(pred(0.6), False) == "TEST"
    assert D.decide(pred(0.3), False) == "ABSTAIN"             # "I don't know whether this transfers"
    assert D.decide(pred(0.1), False) == "IGNORE"
    assert D.decide(pred(0.9, oor=True), False) == "TEST"
    assert {D.decide(pred(c / 20), False) for c in range(21)} == {"TRUST", "TEST", "ABSTAIN", "IGNORE"}      # "always reuse" is impossible
    rc = M.risk_coverage([(0.9, True), (0.8, True), (0.2, False), (0.1, False)], points=(0.5, 1.0))
    assert rc[0]["risk"] == 0.0 and rc[1]["risk"] == 0.5


# ---------------------------------------------------------------- counterfactual generation
def test_counterfactual_generation():
    lab, env = Lab(0), make_env("T03", 0, 0)
    lab.register(env)
    props = set()
    for k in range(lab.n_knobs):
        new = lab.intervene(env.token, k, "down")
        diff = [p for p in PROPERTIES if new.genome[p] != env.genome[p]]
        assert len(diff) <= 1 and set(new.primitives) == set(env.primitives)
        props.add(lab.log[-1]["property"])
    assert props == set(PROPERTIES) and Lab(0)._props == lab._props and Lab(1)._props != lab._props


def test_interventions_move_the_true_preference():
    env = make_env("B00", 0, 0)
    lo, hi = env.with_genome(env.genome.intervene("parallelizability", 0.1)), env.with_genome(env.genome.intervene("parallelizability", 0.9))
    assert transformation_effects(hi)["parallelize"] > transformation_effects(lo)["parallelize"]
    ref = reference_optimum(env)
    assert ref["utility"] >= ref["base_utility"] and ref["useful_threshold"] <= ref["utility"]


# ---------------------------------------------------------------- protocol: provenance, replay, freeze, anti-cheating
def test_provenance_and_records(small_run):
    r = small_run
    assert {"versions", "executor", "resource_limits", "timestamp", "seed"} <= set(r["provenance"])
    assert all({"genome_hash", "surface_seed", "truth_effects", "reference"} <= set(e) for e in r["environments"])
    assert len(r["episodes"]) == len(r["environments"]) * len(SMALL["agents"])
    assert all(e["phase1"]["evaluations"] <= SMALL["phase1_budget"] and e["phase2"]["evaluations"] <= SMALL["phase2_budget"] for e in r["episodes"])
    orc = [e for e in r["episodes"] if e["agent"] == "latent_oracle"]
    assert all(abs(e["phase1"]["final"]["gap"] - 1) < 1e-9 and e["phase1"]["evaluations"] == 0 for e in orc)
    assert r["agents"]["archetype"]["counterfactual_evaluations"] > 0 and r["agents"]["archetype_no_counterfactual"]["counterfactual_evaluations"] == 0
    snap = r["agents"]["archetype"]["snapshot"]["store"]
    blob = str(snap)
    assert not any(f in blob for f in FAMILIES) and not any(p in blob for p in PROPERTIES)      # memory holds no family id and no latent name


def test_deterministic_replay(small_run):
    assert run_seed(5, SMALL)["record_hash"] == small_run["record_hash"]
    assert run_seed(6, SMALL)["record_hash"] != small_run["record_hash"]


def test_analysis_and_verdict_rule(small_run):
    res = A.analyze([small_run])
    assert res["criteria"]["verdict"] == "INCONCLUSIVE"            # one seed can never support a claim
    assert [k["id"] for k in res["criteria"]["K"]] == [f"K{i}" for i in range(1, 9)] and len(res["criteria"]["S"]) == 10
    S_all = [{"holds": True}] * 10
    K = lambda **o: [{"id": f"K{i}", "passed": o.get(f"K{i}", True)} for i in range(1, 9)]
    assert A.verdict(K(), S_all, 30, 0.0) == "BREAKTHROUGH_CANDIDATE"
    assert A.verdict(K(K6=False), [{"holds": False}], 30, 0.0) == "NO_DISTINCT_CAPABILITY"
    assert A.verdict(K(K1=False, K2=False), [{"holds": False}], 30, 0.0) == "NO_DISTINCT_CAPABILITY"
    assert A.verdict(K(K5=False), [{"holds": False}], 30, 0.0) == "PARTIAL_SUPPORT"
    assert A.verdict(K(), S_all, 30, 0.2) == "INCONCLUSIVE" and A.verdict(K(), S_all, 3, 0.0) == "INCONCLUSIVE"


def test_metric_primitives():
    assert M.auroc([(0.9, True), (0.8, True), (0.1, False)]) == 1.0 and M.auroc([(0.5, True), (0.5, False)]) == 0.5 and M.auroc([(1, True)]) is None
    assert M.auprc([(0.9, True), (0.1, False)]) == 1.0
    assert M.calibration([(1.0, True), (0.0, False)])["ece"] == 0.0
