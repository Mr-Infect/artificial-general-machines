"""Compositional Architecture IR for ARCHETYPE (spec §3.2, §24).

Same conventions as ``architecture/ir.py`` (pure data, canonical JSON, sha256[:16] identity, lineage),
but the body is a composition tree so that organizational differences are *structural*:

    {"op": "unit", "p": name}
    {"op": "serial", "c": [node, ...]}
    {"op": "parallel", "c": [node, ...], "merge": name}        fan-out to children, merged by a fan-in primitive
    {"op": "conditional", "router": name, "c": [node, ...]}    one branch selected per input
    {"op": "loop", "body": node, "gate": name, "n": int}       body repeated until the gate passes (max n)
    {"op": "hier", "dec": name, "body": node, "depth": int}    recursive decomposition, ``depth`` levels

Primitive names are local to one environment. This module is learner-visible: it knows interface
signatures only, never abstract roles.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

IR_VERSION = "archetype-ir-0.1"
LIMITS = {"max_depth": 9, "max_branching": 4, "max_nodes": 96, "max_loop": 4, "max_hier_depth": 3}
Node = Dict[str, Any]


def unit(p: str) -> Node:
    return {"op": "unit", "p": p}


def serial(children: List[Node]) -> Node:
    return {"op": "serial", "c": list(children)}


def parallel(children: List[Node], merge: str) -> Node:
    return {"op": "parallel", "c": list(children), "merge": merge}


def conditional(router: str, children: List[Node]) -> Node:
    return {"op": "conditional", "router": router, "c": list(children)}


def loop(body: Node, gate: str, n: int) -> Node:
    return {"op": "loop", "body": body, "gate": gate, "n": int(n)}


def hier(dec: str, body: Node, depth: int) -> Node:
    return {"op": "hier", "dec": dec, "body": body, "depth": int(depth)}


def _key(node: Node) -> str:
    return json.dumps(node, sort_keys=True, separators=(",", ":"))


def normalize(node: Node) -> Node:
    """Canonical form: nested serials flattened, one-child serials collapsed, unordered children sorted."""
    op = node["op"]
    if op == "unit":
        return {"op": "unit", "p": node["p"]}
    if op == "serial":
        out: List[Node] = []
        for c in map(normalize, node["c"]):
            out.extend(c["c"] if c["op"] == "serial" else [c])
        return out[0] if len(out) == 1 else {"op": "serial", "c": out}
    if op == "parallel":
        return {"op": "parallel", "c": sorted(map(normalize, node["c"]), key=_key), "merge": node["merge"]}
    if op == "conditional":
        return {"op": "conditional", "router": node["router"], "c": sorted(map(normalize, node["c"]), key=_key)}
    if op == "loop":
        return {"op": "loop", "body": normalize(node["body"]), "gate": node["gate"], "n": int(node["n"])}
    if op == "hier":
        return {"op": "hier", "dec": node["dec"], "body": normalize(node["body"]), "depth": int(node["depth"])}
    raise ValueError(f"unknown op {op!r}")


def children(node: Node) -> List[Node]:
    op = node["op"]
    return node["c"] if op in ("serial", "parallel", "conditional") else [node["body"]] if op in ("loop", "hier") else []


def primitives_used(node: Node) -> List[str]:
    own = [node[k] for k in ("p", "merge", "router", "gate", "dec") if k in node]
    return own + [p for c in children(node) for p in primitives_used(c)]


def count_nodes(node: Node) -> int:
    return 1 + sum(count_nodes(c) for c in children(node))


def depth(node: Node) -> int:
    return 1 + max((depth(c) for c in children(node)), default=0)


def structural_operations(node: Node) -> int:
    """Number of composition operators (everything that is not a plain unit)."""
    return (0 if node["op"] == "unit" else 1) + sum(structural_operations(c) for c in children(node))


class ArchGraph(BaseModel):
    ir_version: str = IR_VERSION
    name: str = "unnamed"
    root: Dict[str, Any]
    parent_hash: Optional[str] = None
    lineage: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def canonical(self) -> str:
        return json.dumps({"ir_version": self.ir_version, "root": normalize(self.root)}, sort_keys=True, separators=(",", ":"))

    def hash(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()[:16]

    def derive(self, root: Node, name: Optional[str] = None) -> "ArchGraph":
        return ArchGraph(name=name or self.name, root=root, parent_hash=self.hash(), lineage=self.lineage + [self.hash()], metadata=dict(self.metadata))


def validate(node: Node, primitives: Dict[str, Dict[str, Any]], limits: Dict[str, int] = LIMITS) -> List[str]:
    """Structural validation against an environment's public primitive inventory (name -> public spec)."""
    errors: List[str] = []

    def sig(name: str) -> Dict[str, Any]:
        return primitives[name]["signature"] if name in primitives else {}

    def walk(n: Node) -> None:
        op = n.get("op")
        for name in [n[k] for k in ("p", "merge", "router", "gate", "dec") if k in n]:
            if name not in primitives:
                errors.append(f"unknown primitive {name!r}")
        if op == "unit":
            return
        if op in ("serial", "parallel", "conditional"):
            if not n["c"]:
                errors.append(f"{op} needs children")
            if op != "serial" and not 2 <= len(n["c"]) <= limits["max_branching"]:
                errors.append(f"{op} needs 2..{limits['max_branching']} children")
            if op == "parallel" and not sig(n["merge"]).get("fan_in"):
                errors.append("parallel.merge must be a fan-in primitive")
            if op == "conditional" and not sig(n["router"]).get("selects"):
                errors.append("conditional.router must be a selecting primitive")
        elif op == "loop":
            if not sig(n["gate"]).get("gates"):
                errors.append("loop.gate must be a gating primitive")
            if not 2 <= n["n"] <= limits["max_loop"]:
                errors.append(f"loop.n must be 2..{limits['max_loop']}")
        elif op == "hier":
            if sig(n["dec"]).get("fan_out", 1) < 2:
                errors.append("hier.dec must be a fan-out primitive")
            if not 1 <= n["depth"] <= limits["max_hier_depth"]:
                errors.append(f"hier.depth must be 1..{limits['max_hier_depth']}")
        else:
            errors.append(f"unknown op {op!r}")
            return
        for c in children(n):
            walk(c)

    walk(node)
    if not errors:
        if count_nodes(node) > limits["max_nodes"]:
            errors.append("too many nodes")
        if depth(node) > limits["max_depth"]:
            errors.append("too deep")
    return errors
