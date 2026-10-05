"""Structural families (spec §31, §32). EVALUATOR ONLY.

A *factor* pins a few genome properties high or low. A *family* is a pair of factors; the remaining
properties are sampled from neutral default ranges per seed. Worlds:

  train             10 factor pairs
  transfer_iso      5 pairs that also occur in training (fresh genome sample, unseen surface themes)
  transfer_holdout  5 pairs that never occur in training (compositional hold-out)
  false             one per training family: identical observable properties and vocabulary theme,
                    hidden-only pinned properties flipped

In the training world hidden-only properties are confounded with observable ones through the factors
(e.g. factor P: wide, parallelizable work always comes with low coupling). False analogies break that.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from archetype.latent_structure.genome import HIDDEN_ONLY, OBSERVABLE, PROPERTIES, EnvironmentGenome
from archetype.util import rng_for

HI, LO = (0.75, 0.95), (0.05, 0.2)

# factor -> {property: "hi" | "lo"}
FACTORS: Dict[str, Dict[str, str]] = {
    "V": {"observation_noise": "hi", "verification_cost": "lo", "failure_cost": "hi"},
    "P": {"parallelizability": "hi", "branching_factor": "hi", "coupling": "lo"},
    "D": {"dependency_depth": "hi"},
    "M": {"temporal_correlation": "hi", "state_volatility": "lo", "information_decay": "lo"},
    "X": {"action_reversibility": "hi", "uncertainty": "hi"},
    "L": {"delayed_feedback": "hi", "action_reversibility": "lo", "uncertainty": "lo"},
    "S": {"state_volatility": "hi", "adversariality": "lo"},
    "R": {"resource_constraint": "hi"},
    "C": {"observation_noise": "hi", "verification_cost": "hi", "coupling": "lo"},
}

DEFAULT_RANGE: Dict[str, Tuple[float, float]] = {p: (0.1, 0.4) for p in OBSERVABLE}
DEFAULT_RANGE.update({"verification_cost": (0.4, 0.7), "action_reversibility": (0.35, 0.6), "resource_constraint": (0.15, 0.4),
                      "coupling": (0.45, 0.75), "adversariality": (0.05, 0.3), "information_decay": (0.5, 0.8),
                      "uncertainty": (0.15, 0.4), "failure_cost": (0.1, 0.35)})

TRAIN_PAIRS = [("V", "P"), ("V", "D"), ("P", "M"), ("D", "L"), ("M", "L"), ("X", "S"), ("X", "P"), ("S", "R"), ("R", "C"), ("C", "D")]
HOLDOUT_PAIRS = [("V", "M"), ("P", "S"), ("D", "X"), ("L", "R"), ("C", "M")]
ISO_PAIRS = [("V", "P"), ("D", "L"), ("X", "S"), ("R", "C"), ("P", "M")]

TRAIN_THEMES = ["network", "science", "logistics", "finance", "medical"]
TRANSFER_THEMES = ["agriculture", "energy", "legal", "manufacturing", "gaming"]


@dataclass(frozen=True)
class Family:
    id: str
    world: str                      # train | transfer_iso | transfer_holdout | false
    factors: Tuple[str, str]
    theme: str
    matched: Optional[str] = None   # training family this one mirrors (transfer_iso, false)

    def pinned(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for f in self.factors:
            for prop, level in FACTORS[f].items():
                if out.get(prop, level) != level:
                    raise ValueError(f"family {self.id}: factors {self.factors} conflict on {prop}")
                out[prop] = level
        return out


def _build() -> Dict[str, Family]:
    fams: List[Family] = []
    for i, pair in enumerate(TRAIN_PAIRS):
        fams.append(Family(f"T{i:02d}", "train", pair, TRAIN_THEMES[i % 5]))
    train_by_pair = {f.factors: f.id for f in fams}
    for i, pair in enumerate(ISO_PAIRS):
        fams.append(Family(f"B{i:02d}", "transfer_iso", pair, TRANSFER_THEMES[i % 5], matched=train_by_pair[pair]))
    for i, pair in enumerate(HOLDOUT_PAIRS):
        fams.append(Family(f"H{i:02d}", "transfer_holdout", pair, TRANSFER_THEMES[(i + 2) % 5]))
    for i, pair in enumerate(TRAIN_PAIRS):
        fams.append(Family(f"F{i:02d}", "false", pair, TRAIN_THEMES[i % 5], matched=f"T{i:02d}"))
    # reserved for the automatic replication of an apparent breakthrough (spec §35): a NEW false analogy, never used otherwise
    fams.append(Family("FX0", "false_reserve", TRAIN_PAIRS[0], TRAIN_THEMES[0], matched="T00"))
    return {f.id: f for f in fams}


FAMILIES: Dict[str, Family] = _build()


def families(world: str) -> List[Family]:
    if world == "transfer":
        return [f for f in FAMILIES.values() if f.world.startswith("transfer")]
    return [f for f in FAMILIES.values() if f.world == world]


def _draw(rng, level_or_range) -> float:
    lo, hi = {"hi": HI, "lo": LO}.get(level_or_range, level_or_range)
    return round(rng.uniform(lo, hi), 4)


def sample_genome(family: Family, seed: int) -> EnvironmentGenome:
    """One genome per (family, seed); the three surface realizations of a family share it."""
    if family.world.startswith("false"):
        base = sample_genome(FAMILIES[family.matched], seed).as_dict()
        rng = rng_for("genome-false", seed, family.id)
        hidden = sorted(p for p in family.pinned() if p in HIDDEN_ONLY)
        flip = hidden[:1] if family.world == "false_reserve" else hidden      # the reserve analogy breaks only one hidden relation
        for prop, level in family.pinned().items():
            if prop in flip:
                base[prop] = _draw(rng, "lo" if level == "hi" else "hi")
        return EnvironmentGenome.from_dict(base)
    rng = rng_for("genome", seed, family.id)
    pinned = family.pinned()
    return EnvironmentGenome.from_dict({p: _draw(rng, pinned.get(p, DEFAULT_RANGE[p])) for p in PROPERTIES})


def shift_genome(family: Family, genome: EnvironmentGenome, seed: int) -> Tuple[EnvironmentGenome, str]:
    """Phase-2 regime shift: one pinned property of the family flips (hi <-> lo)."""
    rng = rng_for("shift", seed, family.id)
    pinned = family.pinned()
    prop = rng.choice(sorted(pinned))
    return genome.intervene(prop, _draw(rng, "lo" if pinned[prop] == "hi" else "hi")), prop
