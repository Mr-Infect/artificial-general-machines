"""Per-environment primitive inventories. EVALUATOR ONLY (holds hidden roles and strengths).

Agents receive only ``public(inventory)``: random names, interface signature, cost / latency / ram in a
randomized currency. The abstract role set and the strength of a primitive never leave the evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List

ROLES = ("decomposition", "execution", "aggregation", "verification", "memory", "control", "adaptation")
SIGNATURE_FIELDS = ("fan_out", "fan_in", "gates", "stateful", "selects", "tunes")
PRIMITIVE_GRAMMAR_VERSION = "archetype-primitives-0.1"


@dataclass(frozen=True)
class Primitive:
    name: str
    roles: FrozenSet[str]            # hidden
    strength: float                  # hidden (execution quality level; 0 for non-executors)
    cost: float                      # true cost units (base executor = 1.0)
    latency: float
    memory: float
    fan_out: int = 1
    signature: Dict[str, Any] = field(default_factory=dict, compare=False)


def _sig(roles: FrozenSet[str], fan_out: int) -> Dict[str, Any]:
    return {"fan_out": fan_out if "decomposition" in roles else 1, "fan_in": "aggregation" in roles, "gates": "verification" in roles,
            "stateful": "memory" in roles, "selects": "control" in roles, "tunes": "adaptation" in roles}


def make_inventory(rng, names: List[str], verification_cost: float) -> Dict[str, Primitive]:
    """``names`` is a pool of unique surface tokens; ``verification_cost`` is the genome property (it sets gate prices)."""
    names = list(names)
    out: List[Primitive] = []

    def add(roles, strength=0.0, cost=1.0, memory=2.0, fan_out=1):
        roles = frozenset(roles)
        c = cost * rng.uniform(0.9, 1.1)
        out.append(Primitive(names.pop(), roles, strength, round(c, 4), round(c * rng.uniform(8, 12), 3), round(memory * rng.uniform(0.9, 1.1), 3),
                             fan_out, _sig(roles, fan_out)))

    grades = [(0.55, 1.0, 4), (0.72, 2.2, 8), (0.88, 4.5, 16)] if rng.random() < 0.6 else [(0.55, 1.0, 4), (0.8, 3.2, 12)]
    for s, c, m in grades:
        add(["execution"], strength=s, cost=c, memory=m)
    add(["decomposition"], cost=0.8, fan_out=rng.randint(2, 4))
    gate_cost = 0.3 + 3.5 * verification_cost
    add(["verification"], cost=gate_cost)
    if rng.random() < 0.3:      # combined validator-aggregator instead of a standalone aggregator
        add(["aggregation", "verification"], cost=(0.5 + gate_cost) * 0.85)
    else:
        add(["aggregation"], cost=0.5)
    optional = [(["memory"], 0.7, 12.0), (["control"], 0.5, 2.0), (["adaptation"], 0.6, 2.0)]
    dropped = rng.randrange(3) if rng.random() < 0.15 else -1
    for i, (roles, c, m) in enumerate(optional):
        if i != dropped:
            add(roles, cost=c, memory=m)
    rng.shuffle(out)
    return {p.name: p for p in out}


def public(inventory: Dict[str, Primitive], currency: float, rng) -> Dict[str, Dict[str, Any]]:
    """Learner-visible view: shuffled order, signature, resource numbers in the surface's currency."""
    items = list(inventory.values())
    rng.shuffle(items)
    return {p.name: {"signature": dict(p.signature), "cost": round(p.cost * currency, 6), "latency": p.latency, "ram": p.memory} for p in items}
