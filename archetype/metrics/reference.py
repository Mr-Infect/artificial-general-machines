"""Evaluator-side reference quantities (noise-free). EVALUATOR ONLY: uses Environment.true_utility."""
from __future__ import annotations

import itertools
from collections import OrderedDict
from typing import Any, Dict, List, Tuple

from archetype.architecture import generate as Gen
from archetype.latent_structure import fitness as F

USEFUL_GAP = 0.8     # an incumbent is "useful" when it closes this fraction of the gap between single-pass and the reference optimum


_TABLES: "OrderedDict[tuple, list]" = OrderedDict()


def config_table(env) -> List[Tuple[Gen.Config, Dict[str, Any]]]:
    """Every configuration the local inventory can express, with its role-level features (small LRU cache:
    interventions and regime shifts reuse the inventory unless they change prices)."""
    key = (env.key, env.genome["verification_cost"])
    if key not in _TABLES:
        prims = env.primitives
        opt = Gen.options(prims)
        seen: Dict[tuple, Gen.Config] = {}
        for vals in itertools.product(*[opt[k] for k in Gen.KEYS]):
            c = Gen.normalize_config(dict(zip(Gen.KEYS, vals)), prims)
            seen[tuple(c[k] for k in Gen.KEYS)] = c
        _TABLES[key] = [(c, env.features(Gen.compose(c, prims))) for c in seen.values()]
        while len(_TABLES) > 3:
            _TABLES.popitem(last=False)
    _TABLES.move_to_end(key)
    return _TABLES[key]


def reference_optimum(env) -> Dict[str, Any]:
    """Exhaustive noise-free optimum over the shared configuration space."""
    best_cfg, best_u = None, -1.0
    for cfg, feats in config_table(env):
        u = F.true_utility(env.genome, feats)
        if u > best_u:
            best_cfg, best_u = cfg, u
    base_u = env.true_utility(Gen.compose(Gen.BASE, env.primitives))
    return {"config": best_cfg, "utility": best_u, "base_utility": base_u, "useful_threshold": base_u + USEFUL_GAP * (best_u - base_u)}


def gap_closure(u: float, ref: Dict[str, Any]) -> float:
    span = ref["utility"] - ref["base_utility"]
    return 0.0 if span <= 1e-9 else (u - ref["base_utility"]) / span


def transformation_effects(env, context: Gen.Config = None) -> Dict[str, float]:
    """Noise-free marginal effect of each single organizational change in a given context (default: base)."""
    from archetype.learner.transformations import TRANSFORMATIONS, apply
    prims = env.primitives
    out: Dict[str, float] = {}
    for t in TRANSFORMATIONS:
        ctx, new = apply(t, context or Gen.BASE, prims)
        if new == ctx:
            out[t] = 0.0
            continue
        out[t] = env.true_utility(Gen.compose(new, prims)) - env.true_utility(Gen.compose(ctx, prims))
    return out
