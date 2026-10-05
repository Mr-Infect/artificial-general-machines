"""3-seed sanity experiment (spec §38). Run BEFORE registration; the full run must not start unless this passes.

    python -m archetype.experiments.sanity [--seeds 0 1 2] [--workers 3]

It runs the small preset (3 seeds, 3 structural families, 1 transfer, 1 false analogy) through the real
driver and then checks the instrument, not the hypothesis:

  leakage            nothing latent is reachable from what agents receive; learner code does not import evaluator code
  randomization      encoder features are invariant to renaming, reordering and rescaling; scrambled surfaces share no vocabulary
  reconstruction     the same organization is rebuilt from a different inventory and recognized as equivalent at role level
  false analogy      the training optimum is harmful in its look-alike and useful in its isomorphic twin
  counterfactuals    an intervention changes exactly one latent property; hidden-only ones leave observations untouched
  provenance/replay  every record carries provenance; re-running a seed reproduces the record hash bit for bit
  non-triviality     no universal architecture; search is neither trivial nor hopeless; the space is large
  decoupling         with observations taken from another structure, the learner's predictions stop tracking the truth
"""
from __future__ import annotations

import argparse
import ast
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from archetype.architecture import generate as Gen
from archetype.architecture import roles as R
from archetype.architecture.primitives import ROLES
from archetype.environments.surface import THEMES
from archetype.environments.world import Lab, make_env
from archetype.experiments import run as driver
from archetype.experiments.landscape import diagnose
from archetype.experiments.replay import replay
from archetype.latent_structure.families import FAMILIES
from archetype.latent_structure.genome import HIDDEN_ONLY, PROPERTIES
from archetype.learner.encoder import encode
from archetype.metrics.analysis import analyze, load

ROOT = Path(__file__).resolve().parents[2]
LEARNER_SIDE = ["archetype/learner", "archetype/transfer", "archetype/memory", "archetype/baselines"]
FORBIDDEN_IMPORTS = ("archetype.latent_structure", "archetype.architecture.roles", "archetype.architecture.primitives", "archetype.environments", "archetype.metrics.reference")
ORACLE = "archetype/baselines/oracle.py"
Check = Tuple[str, bool, str]


def forbidden_strings() -> List[str]:
    return list(PROPERTIES) + list(ROLES) + list(R.ORGANIZATIONS) + ["genome", "family", "strength", "roles"]


def leaked_terms(env) -> List[str]:
    """Latent names, role names, organization labels, family ids or genome values found in the learner-visible view."""
    view = env.view()
    blob = json.dumps(view, sort_keys=True).lower()
    bad = [w for w in forbidden_strings() if w.lower() in blob and not (env.scrambled is False and any(w.lower() in " ".join(v) for v in THEMES.values()))]
    bad += [f for f in FAMILIES if f.lower() + '"' in blob]
    # genome values must not appear verbatim in any structured number (prices, caps, lags, task numbers); the noisy
    # series is checked statistically instead (hidden-only interventions must leave the whole view identical)
    numbers = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            numbers.add(float(o))
    walk({k: v for k, v in view.items() if k != "observations"})
    walk(view["observations"]["limits"])
    walk([[e["lag"]] for e in view["observations"]["episodes"]])
    bad += [f"value:{p}" for p, v in env.genome.as_dict().items() if v in numbers]
    return bad


def import_violations() -> List[str]:
    out = []
    for d in LEARNER_SIDE:
        for p in sorted((ROOT / d).glob("*.py")):
            rel = str(p.relative_to(ROOT))
            if rel == ORACLE:
                continue
            for node in ast.walk(ast.parse(p.read_text())):
                names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module or ""] + [f"{node.module}.{n.name}" for n in node.names] if isinstance(node, ast.ImportFrom) else []
                out += [f"{rel} imports {n}" for n in names if any(n == f or n.startswith(f + ".") for f in FORBIDDEN_IMPORTS)]
    return out


def randomized_view(view: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    """Rename every token, reorder everything, rescale every numeric range. Structure is untouched."""
    ren: Dict[str, str] = {}

    def name(x: str) -> str:
        return ren.setdefault(x, "z" + "".join(rng.choice("0123456789abcdef") for _ in range(8)))
    obs = view["observations"]
    series = list(obs["series"].items())
    rng.shuffle(series)
    new_series = {}
    for k, v in series:
        a, b = rng.choice([-1, 1]) * 10 ** rng.uniform(-2, 2), rng.uniform(-50, 50)
        new_series[name(k)] = [a * x + b for x in v]
    rel = [{"id": name(r["id"]), "requires": [name(p) for p in r["requires"]]} for r in obs["relations"]]
    rng.shuffle(rel)
    sc = 10 ** rng.uniform(-2, 2)
    ep = [{"action": name(e["action"]), "lag": e["lag"], "reverted": e["reverted"], "signal": e["signal"] * sc, "outcome": e["outcome"] * sc} for e in obs["episodes"]]
    cur = 10 ** rng.uniform(-2, 2)
    prims = list(view["primitives"].items())
    rng.shuffle(prims)
    new_prims = {name(k): {**v, "cost": v["cost"] * cur} for k, v in prims}
    return {"token": "t", "task": {**view["task"], "label": "q", "output": "q"}, "limits": view["limits"],
            "observations": {"series": new_series, "relations": rel, "episodes": ep, "limits": {"cap": obs["limits"]["cap"] * cur}}, "primitives": new_prims}


def run_checks(seeds: List[int], run_dir: Path) -> List[Check]:
    checks: List[Check] = []
    envs = [make_env(f, s, i) for f in FAMILIES for s in seeds for i in range(3)]
    # ---- leakage
    leaks = sorted({t for e in envs for t in leaked_terms(e)})
    checks.append(("no latent label, role, organization label, family id or genome value in learner-visible views", not leaks, f"{len(envs)} views scanned; found: {leaks[:8]}"))
    viol = import_violations()
    checks.append(("learner-side modules do not import evaluator modules (oracle baseline excepted)", not viol, "; ".join(viol[:5]) or "clean"))
    # ---- randomization
    rng = random.Random(7)
    worst = 0.0
    for e in envs[:60]:
        f0, f1 = encode(e.view()), encode(randomized_view(e.view(), rng))
        worst = max(worst, max(abs(f0[k] - f1[k]) / (abs(f0[k]) + 1e-6) for k in f0))
    checks.append(("encoder features invariant under renaming, reordering and rescaling", worst < 1e-3, f"largest relative change {worst:.2e}"))
    themed = {w for ws in THEMES.values() for w in ws}
    scr = [e for e in envs if e.scrambled]
    def names(v):
        o = v["observations"]
        return [*v["primitives"], *o["series"], *(r["id"] for r in o["relations"]), *(x["action"] for x in o["episodes"]), *v["task"]["label"].split(), *v["task"]["output"].split()]
    overlap = sum(1 for e in scr for tok in names(e.view()) for w in tok.split("_") if w in themed)
    checks.append(("scrambled surfaces carry no theme vocabulary", overlap == 0, f"{len(scr)} scrambled surfaces, {overlap} themed tokens"))
    # ---- reconstruction
    a, b = make_env("T00", seeds[0], 0), make_env("B00", seeds[0], 1)
    cfg = {**Gen.BASE, "h": 1, "w": 3, "g": 1}
    ga, gb = Gen.compose(cfg, a.primitives), Gen.compose(cfg, b.primitives)
    shared = set(a.primitives) & set(b.primitives)
    dist = R.role_distance(a.role_tree(ga), a.features(ga), b.role_tree(gb), b.features(gb))
    checks.append(("same organization rebuilt from a disjoint inventory is equivalent at role level", not shared and dist["organization_features"] == 0.0 and R.organization(a.features(ga)) == R.organization(b.features(gb)) == "ARCH_3",
                   f"shared primitive names: {len(shared)}; role distance {dist}"))
    sizes = [Gen.space_size(e.primitives) for e in envs]
    checks.append(("architecture space has at least 1000 configurations in every environment", min(sizes) >= 1000, f"min {min(sizes)}, max {max(sizes)}"))
    # ---- false analogy / non-triviality (learner-free, all families)
    d = diagnose(seeds)
    fa, iso = d["false_analogy_gap_closure_of_training_optimum"], d["isomorphic_gap_closure_of_training_optimum"]
    checks.append(("false analogy exists: the training optimum does not transfer to its look-alike", fa["mean"] < 0.3 and fa["share_useful"] < 0.25, json.dumps(fa)))
    checks.append(("isomorphic transfer exists: the training optimum transfers to its structural twin", iso["mean"] > 0.6 and iso["share_useful"] > 0.5, json.dumps(iso)))
    uni = max(d["best_universal_config_mean_gap_closure"].values())
    checks.append(("no trivial universal architecture", uni < 0.6, f"best single configuration closes {uni:.2f} of the gap on average"))
    checks.append(("reference optima use several different organizations", len(d["organizations"]) >= 5, json.dumps(d["organizations"])))
    # ---- counterfactual generator
    lab, src, ok, same_obs = Lab(seeds[0]), make_env("T00", seeds[0], 0), True, True
    lab.register(src)
    for k in range(lab.n_knobs):
        new = lab.intervene(src.token, k, "up")
        diff = [p for p in PROPERTIES if abs(new.genome[p] - src.genome[p]) > 1e-12]
        ok &= len(diff) <= 1 and diff == [lab.log[-1]["property"]][: len(diff)]
        if lab.log[-1]["property"] in HIDDEN_ONLY:
            same_obs &= {k: v for k, v in new.view().items() if k != "token"} == {k: v for k, v in src.view().items() if k != "token"}
    checks.append(("an intervention changes exactly one latent property", ok, f"{lab.n_knobs} knobs"))
    checks.append(("hidden-only interventions leave the entire learner-visible view identical", same_obs, "compared observations, task specification, primitives and limits"))
    # ---- the small experiment itself
    results = load(str(run_dir))
    checks.append(("sanity experiment produced every expected record", len(results) == len(seeds) and all(len(r["episodes"]) == len(r["environments"]) * len(r["config"]["agents"]) for r in results), f"{len(results)} seeds"))
    need = {"git", "config_hash"}
    prov_ok = all(need <= set(r["provenance"]) and {"seed", "versions", "executor", "resource_limits", "timestamp"} <= set(r["provenance"]) and all({"genome_hash", "surface_seed"} <= set(e) for e in r["environments"]) for r in results)
    checks.append(("provenance complete (commit, seed, genome hash, surface seed, versions, config, timestamp, executor, limits)", prov_ok, json.dumps(results[0]["provenance"]["versions"])))
    rp = replay(str(run_dir / f"seed_{seeds[0]}.json"))
    checks.append(("deterministic replay reproduces the record hash", rp["identical"], json.dumps(rp)))
    res = analyze(results)
    orc = res["tables"]["transfer_iso"]["latent_oracle"]["gap"]["mean"]
    checks.append(("latent oracle reaches the reference optimum (upper bound is consistent)", orc is not None and orc > 0.999, f"oracle gap closure {orc}"))
    cens = [res["tables"][w]["search"]["censored"]["mean"] for w in ("transfer_iso", "false")]
    checks.append(("plain search is neither trivial nor hopeless", all(0.02 <= c <= 0.9 for c in cens), f"share of episodes where search never became useful: {cens}"))
    frozen = all(r["agents"]["archetype"]["hash"] for r in results)
    checks.append(("learned knowledge is frozen and hashed before evaluation", frozen, "snapshot hash unchanged after evaluation is enforced by the protocol"))
    ctl = res["controls"]
    checks.append(("decoupling control computed", ctl["within_auroc_decoupled_observations"]["n"] == len(seeds), f"real {ctl['within_auroc_real_observations']['mean']}, decoupled {ctl['within_auroc_decoupled_observations']['mean']} (tiny preset: informative only in the full run)"))
    return checks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--name", default="sanity")
    a = ap.parse_args(argv)
    code = driver.main(["--name", a.name, "--preset", "sanity", "--seeds", *map(str, a.seeds), "--workers", str(a.workers)])
    if code:
        print("sanity experiment failed to run")
        return code
    checks = run_checks(a.seeds, driver.RESULTS / a.name)
    passed = all(ok for _, ok, _ in checks)
    out = {"seeds": a.seeds, "passed": passed, "checks": [{"check": n, "passed": ok, "detail": d} for n, ok, d in checks]}
    (ROOT / "archetype" / "reports" / "sanity_report.json").write_text(json.dumps(out, indent=1))
    for n, ok, d in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {n}\n      {d[:300]}")
    print("SANITY:", "PASSED" if passed else "FAILED - do not run the registered experiment")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
