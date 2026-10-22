"""Metric primitives (pure functions; no access to environments)."""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple


def auroc(pairs: Sequence[Tuple[float, bool]]) -> Optional[float]:
    """Probability that a positive is scored above a negative (ties count half). None if a class is empty."""
    pos = sorted(s for s, y in pairs if y)
    neg = sorted(s for s, y in pairs if not y)
    if not pos or not neg:
        return None
    # rank-sum formulation
    allv = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg])
    rank_sum, i = 0.0, 0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        avg = (i + j + 1) / 2
        rank_sum += avg * sum(lbl for _, lbl in allv[i:j])
        i = j
    return (rank_sum - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def auprc(pairs: Sequence[Tuple[float, bool]]) -> Optional[float]:
    """Average precision."""
    n_pos = sum(1 for _, y in pairs if y)
    if not n_pos:
        return None
    tp, ap = 0, 0.0
    for k, (_, y) in enumerate(sorted(pairs, key=lambda p: -p[0]), 1):
        if y:
            tp += 1
            ap += tp / k
    return ap / n_pos


def calibration(pairs: Sequence[Tuple[float, bool]], bins: int = 10) -> Dict[str, float]:
    """Expected calibration error and Brier score for probabilities in [0, 1]."""
    if not pairs:
        return {"ece": None, "brier": None, "n": 0}
    buckets: List[List[Tuple[float, bool]]] = [[] for _ in range(bins)]
    for s, y in pairs:
        buckets[min(bins - 1, int(s * bins))].append((s, y))
    ece = sum(len(b) / len(pairs) * abs(sum(s for s, _ in b) / len(b) - sum(y for _, y in b) / len(b)) for b in buckets if b)
    return {"ece": ece, "brier": sum((s - y) ** 2 for s, y in pairs) / len(pairs), "n": len(pairs)}


def risk_coverage(items: Sequence[Tuple[float, bool]], points: Sequence[float] = (0.2, 0.4, 0.6, 0.8, 1.0)) -> List[Dict[str, float]]:
    """Selective prediction: items are (certainty, correct). Risk among the most certain share of items."""
    ranked = sorted(items, key=lambda x: -x[0])
    out = []
    for c in points:
        k = max(1, int(round(c * len(ranked))))
        out.append({"coverage": c, "risk": 1 - sum(ok for _, ok in ranked[:k]) / k, "n": k})
    return out


def mean(xs: Sequence[Optional[float]]) -> Optional[float]:
    v = [x for x in xs if x is not None]
    return sum(v) / len(v) if v else None
