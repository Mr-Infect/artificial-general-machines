"""Structural principles (spec §8, §28, §29): relations between environment structure and an
architectural transformation, with contraindications, confidence, history and forgetting.

A principle never names an environment, a domain or a primitive. Its antecedent is a set of rules, each a
conjunction of at most two threshold relations over encoder features; its consequent is a transformation
with an expected effect. Rules whose effect is non-positive inside a region where the transformation is
otherwise predicted to help are stored as contraindications.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

HELP_DELTA = 0.02            # an effect above this (normalized score units) counts as "helps"
STATUSES = ("HYPOTHESIS", "SUPPORTED", "CONDITIONAL", "CONTRADICTED", "RETIRED")
RETIRE_TRUST, RETIRE_MIN_TESTS = 0.35, 8
Tree = Dict[str, Any]        # {"leaf": bool, "mean", "rate", "n"} or {"feature", "threshold", "mean", "low": Tree, "high": Tree}


def leaf_for(tree: Tree, x: Dict[str, float], max_depth: int = 9) -> Tree:
    node, d = tree, 0
    while not node.get("leaf") and d < max_depth:
        node = node["high"] if x[node["feature"]] > node["threshold"] else node["low"]
        d += 1
    return node


def rules_of(tree: Tree) -> List[Dict[str, Any]]:
    """Flatten a tree into rules: conjunction of conditions -> effect, with the mean of the parent region."""
    out: List[Dict[str, Any]] = []

    def walk(node: Tree, conds: List[Dict[str, Any]], parent_mean: float) -> None:
        if node.get("leaf"):
            out.append({"conditions": conds, "effect": node["mean"], "rate": node["rate"], "n": node["n"], "parent_effect": parent_mean})
            return
        for side, above in (("low", False), ("high", True)):
            walk(node[side], conds + [{"feature": node["feature"], "threshold": node["threshold"], "above": above}], node["mean"])
    walk(tree, [], tree["mean"])
    return out


def _holds(conds: List[Dict[str, Any]], x: Dict[str, float]) -> bool:
    return all((x[c["feature"]] > c["threshold"]) == c["above"] for c in conds)


@dataclass
class Principle:
    id: str
    transformation: str                                  # predicted organization (architectural transformation)
    antecedent: List[Dict[str, Any]] = field(default_factory=list)          # rules under which the transformation helps
    contraindications: List[Dict[str, Any]] = field(default_factory=list)   # rules under which it must NOT be used
    model: List[Tree] = field(default_factory=list)      # bagged shallow trees behind the confidence estimate
    canonical: Optional[Tree] = None                     # the tree the readable rules come from
    expected_gain: float = 0.0                           # mean effect where the antecedent holds
    expected_cost: float = 0.0
    mean_effect: float = 0.0
    base_rate: float = 0.5
    support_count: int = 0
    contradiction_count: int = 0
    applicability_range: Dict[str, List[float]] = field(default_factory=dict)
    source_environments: List[str] = field(default_factory=list)      # opaque tokens only
    successful_transfers: int = 0
    failed_transfers: int = 0
    counterfactual_results: List[Dict[str, Any]] = field(default_factory=list)
    hidden_sensitive: bool = False                       # effect changed under an intervention that left all observations unchanged
    last_tested: Optional[int] = None
    status: str = "HYPOTHESIS"

    @property
    def confidence(self) -> float:
        """Trust in the principle: Beta-mean over every test it has faced (out-of-bag, counterfactuals, transfers)."""
        return (self.support_count + 1) / (self.support_count + self.contradiction_count + 2)

    @property
    def active(self) -> bool:
        return self.status != "RETIRED"

    def features_used(self) -> List[str]:
        return sorted({c["feature"] for r in self.antecedent + self.contraindications for c in r.get("conditions", [])})

    def predict(self, x: Dict[str, float], use_relations: bool = True, use_contraindications: bool = True) -> Dict[str, Any]:
        out = {"contraindicated": False, "out_of_range": False}
        depth = 9 if use_contraindications else 1          # without contraindications only the first relation is read
        if not self.model or not use_relations:
            p, expected = self.base_rate, self.mean_effect
        else:
            leaves = [leaf_for(t, x, depth) for t in self.model]
            p = sum(l.get("rate", 0.5) for l in leaves) / len(leaves)
            expected = sum(l["mean"] for l in leaves) / len(leaves)
            for f, (lo, hi) in self.applicability_range.items():
                span = (hi - lo) or 1.0
                if x[f] < lo - 0.5 * span or x[f] > hi + 0.5 * span:
                    out["out_of_range"] = True
            if use_contraindications:
                for c in self.contraindications:
                    if c.get("kind") == "observable" and _holds(c["conditions"], x):
                        out["contraindicated"] = True
        out.update({"p_help": p, "expected": expected, "confidence": 0.5 + (p - 0.5) * self.confidence})
        return out

    def record_test(self, correct: bool, step: int, kind: str, detail: Optional[Dict[str, Any]] = None) -> None:
        """Every test moves trust; repeated failure retires the principle (controlled forgetting)."""
        if correct:
            self.support_count += 1
        else:
            self.contradiction_count += 1
        self.last_tested = step
        if kind == "counterfactual":
            self.counterfactual_results.append({"correct": correct, **(detail or {})})
        elif kind == "transfer":
            self.successful_transfers += int(correct)
            self.failed_transfers += int(not correct)
        tests = self.support_count + self.contradiction_count
        if tests >= RETIRE_MIN_TESTS and self.confidence < RETIRE_TRUST:
            self.status = "RETIRED"
        elif self.confidence < 0.5:
            self.status = "CONTRADICTED"

    def describe(self) -> str:
        def cond(r):
            return " AND ".join(f"{c['feature']} {'>' if c['above'] else '<='} {c['threshold']:.3g}" for c in r["conditions"]) or "ALWAYS"
        pos = " OR ".join(f"({cond(r)} => {r['effect']:+.3f})" for r in self.antecedent) or "no structural condition found"
        neg = "; ".join(f"NOT when {cond(c)}" if c.get("kind") == "observable" else "UNOBSERVABLE CONDITION: must be tested before use" for c in self.contraindications)
        return f"{self.transformation}: IF {pos} [trust {self.confidence:.2f}, {self.status}]" + (f" CONTRAINDICATED: {neg}" if neg else "")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["confidence"] = round(self.confidence, 4)
        d["description"] = self.describe()
        return d


class PrincipleStore:
    def __init__(self):
        self.principles: Dict[str, Principle] = {}       # keyed by transformation
        self.retired: List[Principle] = []

    def put(self, p: Principle) -> None:
        self.principles[p.transformation] = p

    def active(self) -> List[Principle]:
        return [p for p in self.principles.values() if p.active]

    def forget(self) -> int:
        """Move retired principles out of use; returns how many were forgotten."""
        gone = [t for t, p in self.principles.items() if not p.active]
        for t in gone:
            self.retired.append(self.principles.pop(t))
        return len(gone)

    def to_dict(self) -> Dict[str, Any]:
        return {"principles": {t: p.to_dict() for t, p in sorted(self.principles.items())}, "retired": [p.to_dict() for p in self.retired]}
