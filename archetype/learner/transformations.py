"""Architectural transformations: the unit of structural knowledge (learner-visible).

A transformation is one organizational change applied to a context configuration, expressed only in
terms of what interface signatures allow. Principles predict the effect of a transformation from
environment structure; they never store an architecture of a particular environment.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

from archetype.architecture import generate as Gen

# name -> (config key, value, context override applied before measuring)
TRANSFORMATIONS: Dict[str, Tuple[str, int, Dict[str, int]]] = {
    "decompose": ("h", 1, {}),                 # planner / decomposition in front of execution
    "deepen": ("h", 2, {"h": 1}),             # hierarchical decomposition
    "parallelize": ("w", 3, {"h": 1}),        # parallel workers behind a decomposer, merged by a fan-in primitive
    "replicate": ("r", 3, {}),                # redundant independent solvers -> consensus
    "gate": ("g", 1, {}),                     # verification stage
    "revise": ("loop", 2, {}),                # critic / revision loop
    "recall": ("mem", 1, {}),                 # retrieval before reasoning
    "branch": ("route", 2, {}),               # adaptive branching
    "tune": ("tune", 1, {}),                  # explore/exploit controller
    "upgrade": ("grade", 1, {}),              # stronger executor
}


def apply(t: str, context: Gen.Config, primitives: Dict[str, Dict[str, Any]]) -> Tuple[Gen.Config, Gen.Config]:
    """Returns (context, context + transformation), both normalized to the local inventory."""
    key, value, override = TRANSFORMATIONS[t]
    ctx = Gen.normalize_config({**context, **override}, primitives)
    return ctx, Gen.normalize_config({**ctx, key: max(value, ctx[key]) if key in ("h", "g") else value}, primitives)


def present(t: str, cfg: Gen.Config) -> bool:
    key, value, _ = TRANSFORMATIONS[t]
    return cfg.get(key, Gen.BASE[key]) >= value if key != "grade" else cfg.get("grade", 0) >= 1
