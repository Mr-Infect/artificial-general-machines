"""EnvironmentGenome: the hidden structural description of an environment (spec §3.1, §22).

EVALUATOR ONLY. Nothing under archetype/learner, archetype/transfer, archetype/memory or
archetype/baselines (except the latent oracle) may import this module; a test enforces it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from archetype.util import stable_hash

# Properties that leave a statistical trace in the observation channels (surface.py).
OBSERVABLE = ("dependency_depth", "branching_factor", "parallelizability", "observation_noise", "temporal_correlation",
              "state_volatility", "resource_constraint", "verification_cost", "delayed_feedback", "action_reversibility")
# Properties with no observational proxy: they show only in evaluation outcomes.
HIDDEN_ONLY = ("coupling", "adversariality", "information_decay", "uncertainty", "failure_cost")
PROPERTIES: Tuple[str, ...] = OBSERVABLE + HIDDEN_ONLY


@dataclass(frozen=True)
class EnvironmentGenome:
    values: Tuple[float, ...]

    def __post_init__(self):
        if len(self.values) != len(PROPERTIES):
            raise ValueError(f"genome needs {len(PROPERTIES)} values")
        if any(not 0.0 <= v <= 1.0 for v in self.values):
            raise ValueError("genome values must lie in [0, 1]")

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "EnvironmentGenome":
        return cls(tuple(round(float(d[p]), 6) for p in PROPERTIES))

    def as_dict(self) -> Dict[str, float]:
        return dict(zip(PROPERTIES, self.values))

    def __getitem__(self, prop: str) -> float:
        return self.values[PROPERTIES.index(prop)]

    def hash(self) -> str:
        return stable_hash(self.values)

    def intervene(self, prop: str, value: float) -> "EnvironmentGenome":
        """Counterfactual genome: exactly one property changed (spec §11, §12)."""
        d = self.as_dict()
        d[prop] = value
        return EnvironmentGenome.from_dict(d)

    def distance(self, other: "EnvironmentGenome") -> float:
        """Latent structure distance: mean absolute difference over properties, in [0, 1]."""
        return sum(abs(a - b) for a, b in zip(self.values, other.values)) / len(self.values)
