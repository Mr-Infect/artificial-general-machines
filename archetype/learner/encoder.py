"""Observation encoder: a generic battery of descriptive statistics (learner-visible inputs only).

Deliberately not one estimator per latent property: these are standard, scale/sign/order-invariant
summaries of each observation channel plus a few plain size descriptors. Which of them matter for which
architectural transformation is left to the relation model.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List

FEATURES: List[str] = []


def _z(xs: List[float]) -> List[float]:
    m = statistics.fmean(xs)
    sd = statistics.pstdev(xs) or 1.0
    return [(x - m) / sd for x in xs]


def _acf(z: List[float], lag: int) -> float:
    n = len(z)
    return sum(z[i] * z[i + lag] for i in range(n - lag)) / (n - lag) if n > lag else 0.0


def _kurt(z: List[float]) -> float:
    return statistics.fmean(v ** 4 for v in z)


def _corr(a: List[float], b: List[float]) -> float:
    return statistics.fmean(x * y for x, y in zip(_z(a), _z(b)))


def encode(view: Dict[str, Any]) -> Dict[str, float]:
    obs, prims = view["observations"], view["primitives"]
    f: Dict[str, float] = {}
    # ---- series
    cols = [_z(v) for v in obs["series"].values()]
    n = len(cols[0])
    for lag in (1, 2, 5, 10):
        f[f"series.acf{lag}"] = statistics.fmean(abs(_acf(c, lag)) for c in cols)
    diffs = [[c[i + 1] - c[i] for i in range(n - 1)] for c in cols]
    f["series.diff_var_ratio"] = statistics.fmean(statistics.pvariance(d) for d in diffs)
    f["series.diff_kurtosis"] = statistics.fmean(_kurt(_z(d)) for d in diffs)
    out_frac = []
    for d in diffs:
        med = statistics.median(d)
        mad = statistics.median(abs(x - med) for x in d) or 1e-9
        out_frac.append(sum(abs(x - med) > 5 * mad for x in d) / len(d))
    f["series.diff_outlier_fraction"] = statistics.fmean(out_frac)
    f["series.level_kurtosis"] = statistics.fmean(_kurt(c) for c in cols)
    f["series.abs_skew"] = statistics.fmean(abs(statistics.fmean(v ** 3 for v in c)) for c in cols)
    f["series.half_shift"] = statistics.fmean(abs(statistics.fmean(c[: n // 2]) - statistics.fmean(c[n // 2:])) for c in cols)
    pairs = [abs(statistics.fmean(x * y for x, y in zip(cols[i], cols[j]))) for i in range(len(cols)) for j in range(i + 1, len(cols))]
    f["series.cross_correlation"] = statistics.fmean(pairs) if pairs else 0.0
    f["series.log_length"] = math.log(n)
    f["series.width"] = float(len(cols))
    # ---- relations
    rel = obs["relations"]
    req = {r["id"]: r["requires"] for r in rel}
    needed = {p for r in rel for p in r["requires"]}
    m = len(rel)
    depth: Dict[str, int] = {}

    def d(i: str) -> int:
        if i not in depth:
            depth[i] = 1 + max((d(p) for p in req[i]), default=0)
        return depth[i]
    longest = max(d(i) for i in req)
    layers: Dict[int, int] = {}
    for i in req:
        layers[depth[i]] = layers.get(depth[i], 0) + 1
    nonroot = [len(v) for v in req.values() if v]
    f["relations.log_items"] = math.log(m)
    f["relations.root_fraction"] = sum(1 for v in req.values() if not v) / m
    f["relations.isolated_fraction"] = sum(1 for i, v in req.items() if not v and i not in needed) / m
    f["relations.longest_path"] = float(longest)
    f["relations.longest_path_ratio"] = longest / m
    f["relations.mean_in_degree"] = statistics.fmean(nonroot) if nonroot else 0.0
    f["relations.max_in_degree"] = float(max(nonroot, default=0))
    f["relations.leaf_fraction"] = sum(1 for i in req if i not in needed) / m
    f["relations.max_layer_fraction"] = max(layers.values()) / m
    # ---- episodes
    ep = obs["episodes"]
    lags = [e["lag"] for e in ep]
    f["episodes.mean_lag"] = statistics.fmean(lags)
    f["episodes.median_lag"] = float(statistics.median(lags))
    f["episodes.zero_lag_fraction"] = sum(1 for x in lags if x == 0) / len(lags)
    f["episodes.reverted_fraction"] = sum(1 for e in ep if e["reverted"]) / len(ep)
    f["episodes.signal_outcome_correlation"] = _corr([e["signal"] for e in ep], [e["outcome"] for e in ep])
    f["episodes.log_count"] = math.log(len(ep))
    f["episodes.distinct_actions"] = float(len({e["action"] for e in ep}))
    # ---- limits and price sheet (relative prices only: the currency is arbitrary)
    sig = {k: v["signature"] for k, v in prims.items()}
    cost = {k: v["cost"] for k, v in prims.items()}
    plain = sorted(cost[k] for k, s in sig.items() if s["fan_out"] < 2 and not any(s[x] for x in ("fan_in", "gates", "stateful", "selects", "tunes")))
    unit_price = plain[0]
    gates = [cost[k] for k, s in sig.items() if s["gates"]]
    merges = [cost[k] for k, s in sig.items() if s["fan_in"]]
    f["prices.cap_ratio"] = obs["limits"]["cap"] / unit_price
    f["prices.gate_ratio"] = (min(gates) / unit_price) if gates else 0.0
    f["prices.merge_ratio"] = (min(merges) / unit_price) if merges else 0.0
    f["prices.top_grade_ratio"] = plain[-1] / unit_price
    f["prices.median_ratio"] = statistics.median(cost.values()) / unit_price
    f["inventory.size"] = float(len(prims))
    f["inventory.grades"] = float(len(plain))
    f["inventory.max_fan_out"] = float(max(s["fan_out"] for s in sig.values()))
    return {k: round(v, 6) for k, v in f.items()}


FEATURE_GROUPS = {"size": ["series.log_length", "series.width", "relations.log_items", "episodes.log_count", "episodes.distinct_actions",
                           "inventory.size", "inventory.grades", "inventory.max_fan_out"]}
