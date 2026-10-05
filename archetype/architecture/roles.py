"""ArchitectureGraph: the role-normalized view of an architecture (spec §25). EVALUATOR ONLY.

Maps a composition tree built from local primitives onto abstract roles, extracts the organizational
features the hidden fitness function reads, classifies the organization (ARCH_1..ARCH_10) and measures
role-level structural distance (so that planner->workers->verifier and scheduler->simulators->validator
compare as equivalent although no name is shared).
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Sequence

from archetype.architecture import graph as G
from archetype.architecture.primitives import Primitive

ORGANIZATIONS = {
    "ARCH_1": "single-pass sequential", "ARCH_2": "planner -> executor", "ARCH_3": "planner -> parallel workers -> aggregator",
    "ARCH_4": "decompose -> solve -> verify", "ARCH_5": "hypothesis -> critic -> revision", "ARCH_6": "memory retrieval -> reasoning -> verification",
    "ARCH_7": "adaptive branching", "ARCH_8": "hierarchical decomposition", "ARCH_9": "redundant reasoning -> consensus",
    "ARCH_10": "exploration -> exploitation controller"}
ORG_FEATURES = ("h", "w", "r", "g", "loop", "mem", "route", "tune")
ORG_SCALE = {"h": 3, "w": 3, "r": 2, "g": 3, "loop": 3, "mem": 1, "route": 3, "tune": 1}
MEMORIZED_THRESHOLD = 0.10      # role distance below this to any previously observed architecture = MEMORIZED TRANSFER


def role_tree(node: G.Node, inv: Dict[str, Primitive]) -> G.Node:
    """The same tree with every primitive replaced by its sorted role tuple; canonical."""
    def r(name):
        return "+".join(sorted(inv[name].roles))
    out = {"op": node["op"]}
    for k in ("p", "merge", "router", "gate", "dec"):
        if k in node:
            out[k] = r(node[k])
    for k in ("n", "depth"):
        if k in node:
            out[k] = node[k]
    if "c" in node:
        out["c"] = [role_tree(c, inv) for c in node["c"]]
    if "body" in node:
        out["body"] = role_tree(node["body"], inv)
    return G.normalize(out)


def features(node: G.Node, inv: Dict[str, Primitive]) -> Dict[str, Any]:
    acc = {"h": 0, "w": 1, "r": 1, "g": 0, "loop": 0, "mem": 0.0, "route": 0, "tune": 0, "has_agg": False, "strengths": [], "seen_exec": False}

    def walk(n: G.Node, levels: int) -> Dict[str, float]:
        op = n["op"]
        acc["h"] = max(acc["h"], levels)
        if op == "unit":
            p = inv[n["p"]]
            if "execution" in p.roles:
                acc["strengths"].append(p.strength)
                acc["seen_exec"] = True
            if "verification" in p.roles:
                acc["g"] += 1
            if "memory" in p.roles:
                acc["mem"] = max(acc["mem"], 0.5 if acc["seen_exec"] else 1.0)
            if "adaptation" in p.roles:
                acc["tune"] = 1
            return {"cost": p.cost, "latency": p.latency, "memory": p.memory}
        if op == "serial":
            tot = {"cost": 0.0, "latency": 0.0, "memory": 0.0}
            lv = levels
            for c in n["c"]:
                s = walk(c, lv)
                if c["op"] == "unit" and "decomposition" in inv[c["p"]].roles:
                    lv += 1        # a planner in front of the rest of the pipeline
                    acc["h"] = max(acc["h"], lv)
                for k in tot:
                    tot[k] += s[k]
            return tot
        if op == "parallel":
            m = inv[n["merge"]]
            acc["has_agg"] = acc["has_agg"] or "aggregation" in m.roles
            if "verification" in m.roles:
                acc["g"] += 1
            key = "w" if levels > 0 else "r"
            acc[key] = max(acc[key], len(n["c"]))
            subs = [walk(c, levels) for c in n["c"]]
            return {"cost": m.cost + sum(s["cost"] for s in subs), "latency": m.latency + max(s["latency"] for s in subs),
                    "memory": m.memory + sum(s["memory"] for s in subs)}
        if op == "conditional":
            p = inv[n["router"]]
            if "control" in p.roles:
                acc["route"] = max(acc["route"], len({G._key(c) for c in n["c"]}))
            subs = [walk(c, levels) for c in n["c"]]
            k = len(subs)
            return {"cost": p.cost + sum(s["cost"] for s in subs) / k, "latency": p.latency + sum(s["latency"] for s in subs) / k,
                    "memory": p.memory + max(s["memory"] for s in subs)}
        if op == "loop":
            p = inv[n["gate"]]
            if "verification" in p.roles:
                acc["loop"] = max(acc["loop"], n["n"])
            s = walk(n["body"], levels)
            return {"cost": n["n"] * (s["cost"] + p.cost), "latency": n["n"] * (s["latency"] + p.latency), "memory": s["memory"] + p.memory}
        if op == "hier":
            p = inv[n["dec"]]
            d = n["depth"] if "decomposition" in p.roles else 0
            s = walk(n["body"], levels + d)
            mult = 1 + 0.5 * n["depth"]
            return {"cost": p.cost * n["depth"] + s["cost"] * mult, "latency": p.latency * n["depth"] + s["latency"] * mult, "memory": p.memory + s["memory"]}
        raise ValueError(op)

    res = walk(G.normalize(node), 0)
    st = acc.pop("strengths")
    acc.pop("seen_exec")
    acc.update({"n_exec": len(st), "exec_strength": sum(st) / len(st) if st else 0.0, "n_nodes": G.count_nodes(node),
                "n_ops": G.structural_operations(node), "cost": res["cost"], "latency": res["latency"], "memory": res["memory"]})
    acc["h"], acc["w"], acc["r"], acc["g"], acc["loop"], acc["route"] = min(acc["h"], 3), min(acc["w"], 4), min(acc["r"], 4), min(acc["g"], 3), min(acc["loop"], 4), min(acc["route"], 3)
    return acc


def organization(f: Dict[str, Any]) -> str:
    """Dominant organization class (ordered from most to least specific control structure)."""
    if f["tune"]:
        return "ARCH_10"
    if f["route"] >= 2:
        return "ARCH_7"
    if f["loop"]:
        return "ARCH_5"
    if f["h"] >= 2:
        return "ARCH_8"
    if f["r"] >= 2:
        return "ARCH_9"
    if f["mem"] and f["g"]:
        return "ARCH_6"
    if f["h"] >= 1 and f["w"] >= 2:
        return "ARCH_3"
    if f["h"] >= 1 and f["g"]:
        return "ARCH_4"
    if f["h"] >= 1:
        return "ARCH_2"
    return "ARCH_1"


def org_vector(f: Dict[str, Any]) -> Dict[str, float]:
    base = {"w": 1, "r": 1}
    return {k: (f[k] - base.get(k, 0)) / ORG_SCALE[k] for k in ORG_FEATURES}


def _bag(tree: G.Node, what: str) -> Counter:
    c: Counter = Counter()

    def walk(n):
        if what == "ops":
            c[n["op"]] += 1
        else:
            for k in ("p", "merge", "router", "gate", "dec"):
                if k in n:
                    for role in n[k].split("+"):
                        c[role] += 1
        for ch in G.children(n):
            walk(ch)
    walk(tree)
    return c


def _bag_distance(a: Counter, b: Counter) -> float:
    keys = set(a) | set(b)
    union = sum(max(a[k], b[k]) for k in keys)
    return 0.0 if not union else 1 - sum(min(a[k], b[k]) for k in keys) / union


def role_distance(tree_a: G.Node, feat_a: Dict[str, Any], tree_b: G.Node, feat_b: Dict[str, Any]) -> Dict[str, float]:
    """Separately reported components (all in [0, 1]) and their unweighted mean. Inputs are role trees."""
    va, vb = org_vector(feat_a), org_vector(feat_b)
    comp = {"role_multiset": _bag_distance(_bag(tree_a, "roles"), _bag(tree_b, "roles")),
            "operator_multiset": _bag_distance(_bag(tree_a, "ops"), _bag(tree_b, "ops")),
            "organization_features": sum(abs(va[k] - vb[k]) for k in ORG_FEATURES) / len(ORG_FEATURES),
            "identical": 0.0 if G._key(tree_a) == G._key(tree_b) else 1.0}
    comp["aggregate"] = (comp["role_multiset"] + comp["operator_multiset"] + comp["organization_features"]) / 3
    return comp


def novelty(tree: G.Node, feat: Dict[str, Any], reference: Sequence[Any]) -> float:
    """Minimum aggregate role distance to a reference set of (role_tree, features); 1.0 if the set is empty."""
    return min((role_distance(tree, feat, t, f)["aggregate"] for t, f in reference), default=1.0)
