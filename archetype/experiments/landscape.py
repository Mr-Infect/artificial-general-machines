"""Landscape diagnostics on the hidden fitness (evaluator side; no learner involved).

    python -m archetype.experiments.landscape --seeds 0 1 2

Used to calibrate the ENVIRONMENT before registration and as part of the sanity checks:
  * organizations differ between families (no trivial universal architecture),
  * the organization that is best in a training family is harmful in its false analogy,
  * transfer (isomorphic) families share the training optimum's organization.
"""
from __future__ import annotations

import argparse
import statistics
from collections import Counter
from typing import Any, Dict, List

from archetype.architecture import generate as Gen
from archetype.architecture import roles as R
from archetype.environments.world import make_env
from archetype.latent_structure.families import FAMILIES, families
from archetype.metrics.reference import gap_closure, reference_optimum, transformation_effects


def diagnose(seeds: List[int], verbose: bool = False) -> Dict[str, Any]:
    orgs: Counter = Counter()
    rows, harm, iso, universal = [], [], [], {}
    for seed in seeds:
        refs = {}
        for fam in FAMILIES.values():
            env = make_env(fam.id, seed, 0)
            ref = reference_optimum(env)
            refs[fam.id] = (env, ref)
            f = env.features(Gen.compose(ref["config"], env.primitives))
            orgs[R.organization(f)] += 1
            eff = transformation_effects(env)
            rows.append({"seed": seed, "family": fam.id, "world": fam.world, "factors": fam.factors, "base": ref["base_utility"], "best": ref["utility"],
                         "org": R.organization(f), "config": {k: v for k, v in ref["config"].items() if v != Gen.BASE[k]},
                         "effects": {t: round(e, 3) for t, e in eff.items() if abs(e) >= 0.02}})
        for fam in FAMILIES.values():
            if not fam.matched:
                continue
            env, ref = refs[fam.id]
            src_cfg = refs[fam.matched][1]["config"]
            gc = gap_closure(env.true_utility(Gen.compose(src_cfg, env.primitives)), ref)
            (harm if fam.world == "false" else iso).append(gc)
        # best single config across all training families (universal architecture check)
        train = [refs[f.id] for f in families("train")]
        cands = [ref["config"] for _, ref in refs.values()] + [dict(Gen.BASE)]
        best = max(statistics.fmean(gap_closure(e.true_utility(Gen.compose(c, e.primitives)), r) for e, r in train) for c in cands)
        universal[seed] = best
    out = {"organizations": dict(orgs), "rows": rows,
           "false_analogy_gap_closure_of_training_optimum": {"mean": statistics.fmean(harm), "max": max(harm), "share_below_zero": sum(h < 0 for h in harm) / len(harm), "share_useful": sum(h >= 0.8 for h in harm) / len(harm)},
           "isomorphic_gap_closure_of_training_optimum": {"mean": statistics.fmean(iso), "min": min(iso), "share_useful": sum(h >= 0.8 for h in iso) / len(iso)},
           "best_universal_config_mean_gap_closure": universal,
           "mean_gain_over_single_pass": statistics.fmean(r["best"] - r["base"] for r in rows)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--rows", action="store_true")
    a = ap.parse_args(argv)
    d = diagnose(a.seeds)
    if a.rows:
        for r in d["rows"]:
            print(r["seed"], r["family"], r["world"][:10].ljust(10), "".join(r["factors"]), f"{r['base']:.3f} -> {r['best']:.3f}", r["org"], r["config"], r["effects"])
    for k, v in d.items():
        if k != "rows":
            print(k, v)


if __name__ == "__main__":
    main()
