"""Environment relation model: induces principles from (features, transformation effect) rows.

Interpretable by construction: per transformation a regression tree of depth <= 2 (conjunctions of at
most two threshold relations) gives the readable rules; a small bag of such trees grown on bootstrap
samples gives the confidence estimate and an out-of-bag test of the relation.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from archetype.memory.principles import HELP_DELTA, Principle, Tree, leaf_for, rules_of
from archetype.util import rng_for

MIN_LEAF, MIN_QUALITY, MAX_DEPTH, N_TREES, FEATURE_SHARE = 3, 0.25, 2, 15, 1.0
Row = Tuple[Dict[str, float], float, str]         # (features, effect, opaque token)


def best_split(xs: List[float], ys: List[float]) -> Optional[Dict[str, float]]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    x, y = [xs[i] for i in order], [ys[i] for i in order]
    n = len(y)
    span = x[-1] - x[0]
    c1, c2 = [0.0], [0.0]
    for v in y:
        c1.append(c1[-1] + v)
        c2.append(c2[-1] + v * v)
    total = c2[n] - c1[n] ** 2 / n
    if total <= 1e-12 or span <= 1e-12:
        return None
    best = None
    for i in range(MIN_LEAF, n - MIN_LEAF + 1):
        if x[i] <= x[i - 1]:
            continue
        sse = (c2[i] - c1[i] ** 2 / i) + (c2[n] - c2[i]) - (c1[n] - c1[i]) ** 2 / (n - i)
        q = (1 - sse / total) * (0.7 + 0.3 * min(1.0, (x[i] - x[i - 1]) / span * 10))      # explained variance, favouring wide margins
        if best is None or q > best["quality"]:
            best = {"quality": q, "threshold": (x[i] + x[i - 1]) / 2}
    return best


def _leaf(ys: List[float]) -> Tree:
    return {"leaf": True, "mean": sum(ys) / len(ys), "rate": (sum(y > HELP_DELTA for y in ys) + 1) / (len(ys) + 2), "n": len(ys)}


def grow(rows: List[Row], features: List[str], depth: int = 0) -> Tree:
    ys = [r[1] for r in rows]
    if depth >= MAX_DEPTH or len(rows) < 2 * MIN_LEAF:
        return _leaf(ys)
    best_f, best = None, None
    for f in features:
        s = best_split([r[0][f] for r in rows], ys)
        if s and s["quality"] >= MIN_QUALITY and (best is None or s["quality"] > best["quality"]):
            best_f, best = f, s
    if best is None:
        return _leaf(ys)
    low = [r for r in rows if r[0][best_f] <= best["threshold"]]
    high = [r for r in rows if r[0][best_f] > best["threshold"]]
    return {"feature": best_f, "threshold": best["threshold"], "quality": best["quality"], "mean": sum(ys) / len(ys), "n": len(ys),
            "low": grow(low, features, depth + 1), "high": grow(high, features, depth + 1)}


def fit_principle(transformation: str, rows: List[Row], features: List[str], pid: str) -> Principle:
    ys = [r[1] for r in rows]
    p = Principle(id=pid, transformation=transformation, mean_effect=sum(ys) / len(ys),
                  base_rate=(sum(y > HELP_DELTA for y in ys) + 1) / (len(ys) + 2), source_environments=sorted({r[2] for r in rows}))
    p.canonical = grow(rows, features)
    for r in rules_of(p.canonical):
        if r["effect"] > HELP_DELTA:
            p.antecedent.append(r)
        elif r["conditions"] and r["parent_effect"] > HELP_DELTA:
            p.contraindications.append({"kind": "observable", **r})
    p.expected_gain = max((r["effect"] for r in p.antecedent), default=p.mean_effect)
    for f in p.features_used():
        xs = [r[0][f] for r in rows]
        p.applicability_range[f] = [min(xs), max(xs)]
    # bagged trees: confidence estimate + out-of-bag test of the relation
    rng = rng_for("bag", transformation, len(rows), round(sum(ys), 6))
    n, k = len(rows), max(1, round(len(features) * FEATURE_SHARE))
    oob: List[List[float]] = [[] for _ in rows]
    for _ in range(N_TREES):
        idx = [rng.randrange(n) for _ in range(n)]
        tree = grow([rows[i] for i in idx], features if k >= len(features) else rng.sample(features, k))
        p.model.append(tree)
        for i in set(range(n)) - set(idx):
            oob[i].append(leaf_for(tree, rows[i][0]).get("rate", 0.5))
    for i, votes in enumerate(oob):
        if votes:
            ok = (sum(votes) / len(votes) >= 0.5) == (rows[i][1] > HELP_DELTA)
            p.support_count += int(ok)
            p.contradiction_count += int(not ok)
    return p
