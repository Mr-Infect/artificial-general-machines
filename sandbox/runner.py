"""Generic sandbox runner. Interprets a compiled architecture spec over a data batch.

Stdlib only. Reads one JSON document from stdin:
  {"spec": <CompiledSpec>, "data": {"records": [[...]], "feature_names": [...],
   "ranges": {...}, "relations": [...]}, "state": {...}}
Writes one JSON document to stdout with predictions, confidences, accounting,
carried state and self-measured resource usage. Nothing here is generated
code: every branch is a fixed interpretation of a registry capability.
"""
import json
import math
import resource
import sys
import time


# ----------------------------------------------------------------------------
# helpers

def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs, m=None):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs) if m is None else m
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _clip(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


# ----------------------------------------------------------------------------
# perception components: each returns a per-record score in [0, 1]

def statistical_detector(cols, window, prior):
    """Rolling z-score against the trailing window (seeded from prior stats)."""
    n = len(cols[0]) if cols else 0
    scores = [0.0] * n
    for j, col in enumerate(cols):
        pm = prior.get("mean", {}).get(str(j))
        ps = prior.get("std", {}).get(str(j))
        for i in range(n):
            lo = max(0, i - window)
            hist = col[lo:i]
            if len(hist) >= 5:
                m, s = _mean(hist), _std(hist)
            elif pm is not None:
                m, s = pm, ps or 1.0
            else:
                continue
            s = s if s > 1e-9 else 1e-9
            z = abs(col[i] - m) / s
            scores[i] = max(scores[i], _clip(z / 8.0))
    return scores


def anomaly_detector(cols, window, prior):
    """Median absolute deviation detector: robust to contaminated windows."""
    n = len(cols[0]) if cols else 0
    scores = [0.0] * n
    for col in cols:
        for i in range(n):
            lo = max(0, i - window)
            hist = col[lo:i]
            if len(hist) < 5:
                continue
            med = _median(hist)
            mad = _median([abs(x - med) for x in hist]) * 1.4826
            mad = mad if mad > 1e-9 else 1e-9
            z = abs(col[i] - med) / mad
            scores[i] = max(scores[i], _clip(z / 12.0))
    return scores


def rate_detector(cols, window, prior):
    """First-difference burst detector."""
    n = len(cols[0]) if cols else 0
    scores = [0.0] * n
    for col in cols:
        diffs = [0.0] + [col[i] - col[i - 1] for i in range(1, n)]
        for i in range(1, n):
            lo = max(1, i - window)
            hist = [abs(d) for d in diffs[lo:i]]
            if len(hist) < 5:
                continue
            m = _mean(hist) + 1e-9
            scores[i] = max(scores[i], _clip(abs(diffs[i]) / (10.0 * m)))
    return scores


def range_validator(cols, ranges, feature_names):
    """Declared physical/protocol ranges. Score 1 outside, graded near the edge."""
    n = len(cols[0]) if cols else 0
    scores = [0.0] * n
    for j, name in enumerate(feature_names):
        r = ranges.get(name)
        if not r:
            continue
        lo, hi = r
        span = (hi - lo) or 1.0
        for i in range(n):
            x = cols[j][i]
            if x < lo or x > hi:
                scores[i] = 1.0
            else:
                edge = min(x - lo, hi - x) / span
                if edge < 0.02:
                    scores[i] = max(scores[i], 0.6)
    return scores


def consistency_checker(cols, relations, feature_names, window, prior):
    """Cross-feature relations: y ~= a*x + b (linear) or y ~= a*sqrt(x) + b (sqrt).
    Residuals are scaled by the trailing residual spread."""
    n = len(cols[0]) if cols else 0
    scores = [0.0] * n
    idx = {name: k for k, name in enumerate(feature_names)}
    for rel in relations:
        if rel["x"] not in idx or rel["y"] not in idx:
            continue
        xs, ys = cols[idx[rel["x"]]], cols[idx[rel["y"]]]
        a, b = rel.get("a", 1.0), rel.get("b", 0.0)
        if rel.get("kind") == "sqrt":
            pred = [a * math.sqrt(max(x, 0.0)) + b for x in xs]
        else:
            pred = [a * x + b for x in xs]
        res = [abs(y - p) for y, p in zip(ys, pred)]
        for i in range(n):
            lo = max(0, i - window)
            hist = res[lo:i]
            scale = (_median(hist) if len(hist) >= 5 else prior.get("res_scale", 1.0)) + 1e-9
            scores[i] = max(scores[i], _clip(res[i] / (12.0 * scale)))
    return scores


COMPONENTS = {"statistical_detector", "anomaly_detector", "rate_detector", "range_validator", "consistency_checker"}


def run_component(name, cols, window, data, prior):
    if name == "statistical_detector":
        return statistical_detector(cols, window, prior)
    if name == "anomaly_detector":
        return anomaly_detector(cols, window, prior)
    if name == "rate_detector":
        return rate_detector(cols, window, prior)
    if name == "range_validator":
        return range_validator(cols, data.get("ranges", {}), data["feature_names"])
    if name == "consistency_checker":
        return consistency_checker(cols, data.get("relations", []), data["feature_names"], window, prior)
    raise ValueError("unknown component %s" % name)


# ----------------------------------------------------------------------------
# reasoning / models

class Accounting:
    def __init__(self, profiles):
        self.profiles = profiles
        self.model_calls = 0
        self.tokens = 0
        self.cost = 0.0
        self.latency_ms = 0.0
        self.component_calls = 0
        self.calls = {}

    def charge(self, key, n=1, tokens_scale=1.0):
        p = self.profiles.get(key)
        if p is None:
            return
        self.calls[key] = self.calls.get(key, 0) + n
        if key.startswith("model:"):
            self.model_calls += n
            self.tokens += int(p.get("tokens_per_call", 0) * tokens_scale) * n
        self.cost += p.get("cost_per_call", 0.0) * n
        self.latency_ms += p.get("latency_ms", 0.0) * n


def combine(score_lists, mode):
    n = len(score_lists[0])
    if mode == "parallel":
        return [max(s[i] for s in score_lists) for i in range(n)]
    if mode == "sequential":
        # later components refine earlier ones: weighted by position
        w = [k + 1 for k in range(len(score_lists))]
        tot = float(sum(w))
        return [sum(w[k] * score_lists[k][i] for k in range(len(score_lists))) / tot for i in range(n)]
    return [_mean([s[i] for s in score_lists]) for i in range(n)]


def model_refine(model, cols, comps, window, data, prior, base, acct, n_records):
    """A 'model call'. small_reasoner: mean; large_reasoner: multi-scale re-detection
    with consistency weighting; classifier: passthrough."""
    acct.charge("model:%s" % model, 1, tokens_scale=n_records / 200.0)
    if model == "large_reasoner":
        scales = [max(5, window // 2), window, min(5000, window * 2)]
        acc = [0.0] * n_records
        for w in scales:
            per = [run_component(c, cols, w, data, prior) for c in comps]
            acct.component_calls += len(comps)
            # weight components by how confidently (bimodally) they score
            weights = []
            for s in per:
                m = _mean(s)
                weights.append(0.5 + _std(s, m))
            tw = sum(weights)
            for i in range(n_records):
                acc[i] += sum(weights[k] * per[k][i] for k in range(len(per))) / tw
        refined = [a / len(scales) for a in acc]
        return [0.5 * base[i] + 0.5 * refined[i] for i in range(n_records)]
    if model == "classifier":
        return base
    return base  # small_reasoner / embedding_model: keep base combination


def reason(spec, cols, data, prior, acct):
    p = spec["pipeline"]
    per = p["perception"]
    r = p["reasoning"]
    comps = per["components"]
    window = per["window"]
    n = len(cols[0])
    score_lists = [run_component(c, cols, window, data, prior) for c in comps]
    acct.component_calls += len(comps)
    rtype = r["type"]
    thr = r["threshold"]
    model = r["model"]

    if rtype == "direct":
        scores = combine(score_lists, "mean")
        acct.charge("model:%s" % model, 1, tokens_scale=n / 200.0)
    elif rtype == "sequential":
        scores = combine(score_lists, "sequential")
        acct.charge("model:%s" % model, 1, tokens_scale=n / 200.0)
    elif rtype == "parallel":
        scores = combine(score_lists, "parallel")
        acct.charge("model:%s" % model, 1, tokens_scale=n / 200.0)
    elif rtype == "hierarchical":
        base = combine(score_lists, "mean")
        # level 2: refine only ambiguous records around the threshold
        band = 0.15
        ambiguous = [i for i in range(n) if abs(base[i] - thr) < band]
        refined = model_refine(model, cols, comps, window, data, prior, base, acct, n)
        scores = list(base)
        for i in ambiguous:
            scores[i] = refined[i]
    elif rtype == "iterative":
        scores = combine(score_lists, "mean")
        target = prior.get("contamination", 0.03)
        for _ in range(r["iterations"]):
            scores = model_refine(model, cols, comps, window, data, prior, scores, acct, n)
            flagged = sum(1 for s in scores if s > thr) / float(n)
            # move threshold toward the expected contamination level
            if flagged > target * 2:
                thr = min(0.95, thr + 0.05)
            elif flagged < target / 2:
                thr = max(0.05, thr - 0.05)
    else:
        raise ValueError("unknown reasoning type %s" % rtype)
    return scores, score_lists, thr


# ----------------------------------------------------------------------------
# memory

def load_prior(spec, state, cols):
    mtype = spec["pipeline"]["memory"]["type"]
    prior = {}
    if mtype == "none" or not state:
        return prior
    if mtype in ("episodic", "graph", "vector"):
        prior.update(state.get("stats", {}))
    return prior


def update_state(spec, state, cols, scores, thr, acct, data):
    mtype = spec["pipeline"]["memory"]["type"]
    cap = spec["pipeline"]["memory"]["capacity"]
    if mtype == "none":
        return {}
    stats = {"mean": {}, "std": {}}
    for j, col in enumerate(cols):
        tail = col[-min(len(col), cap):]
        m = _mean(tail)
        stats["mean"][str(j)] = m
        stats["std"][str(j)] = _std(tail, m)
    flagged = sum(1 for s in scores if s > thr)
    stats["contamination"] = max(0.005, flagged / float(len(scores)))
    new_state = {"stats": stats}
    if mtype == "vector":
        # embed flagged windows; a real embedding model would be called here
        acct.charge("model:embedding_model", 1, tokens_scale=max(1, flagged) / 10.0)
        vecs = state.get("vectors", []) if state else []
        for i, s in enumerate(scores):
            if s > thr:
                vecs.append([cols[j][i] for j in range(len(cols))])
        new_state["vectors"] = vecs[-cap:]
    if mtype == "graph":
        edges = state.get("edges", {}) if state else {}
        for i, s in enumerate(scores):
            if s > thr:
                key = ",".join(str(j) for j in range(len(cols)) if abs(cols[j][i] - stats["mean"][str(j)]) > 2 * (stats["std"][str(j)] or 1))
                edges[key] = edges.get(key, 0) + 1
        new_state["edges"] = edges
    return new_state


def vector_boost(spec, state, cols, scores):
    """Vector memory: boost records close to a previously seen anomaly vector."""
    if spec["pipeline"]["memory"]["type"] != "vector" or not state or not state.get("vectors"):
        return scores
    vecs = state["vectors"]
    scale = []
    for j in range(len(cols)):
        s = _std(cols[j]) or 1.0
        scale.append(s)
    out = list(scores)
    for i in range(len(scores)):
        if scores[i] < 0.2:
            continue
        rec = [cols[j][i] for j in range(len(cols))]
        best = min(sum(((rec[j] - v[j]) / scale[j]) ** 2 for j in range(len(rec))) for v in vecs)
        if best < 1.0:
            out[i] = min(1.0, scores[i] + 0.2)
    return out


# ----------------------------------------------------------------------------
# verification

def verify(spec, cols, data, prior, scores, score_lists, thr, acct):
    v = spec["pipeline"]["verification"]
    vtype = v["type"]
    strict = v["strictness"]
    n = len(scores)
    flagged = [i for i in range(n) if scores[i] > thr]
    keep = set(flagged)
    if vtype == "none":
        return keep, thr
    if vtype == "rule_based":
        need = 2 if len(score_lists) > 1 else 1
        for i in flagged:
            agree = sum(1 for s in score_lists if s[i] > thr)
            if agree < need and scores[i] < thr + 0.25 * strict:
                keep.discard(i)
    elif vtype == "model_based":
        model = v.get("model") or "small_reasoner"
        window = spec["pipeline"]["perception"]["window"]
        comps = spec["pipeline"]["perception"]["components"]
        refined = model_refine(model, cols, comps, window, data, prior, scores, acct, n)
        for i in flagged:
            if refined[i] < thr - 0.1 * (1 - strict):
                keep.discard(i)
    elif vtype == "execution_based":
        # re-execute detection with a different window and require agreement
        window = max(5, spec["pipeline"]["perception"]["window"] * 2)
        comps = spec["pipeline"]["perception"]["components"]
        again = combine([run_component(c, cols, window, data, prior) for c in comps], "parallel")
        acct.component_calls += len(comps)
        for i in flagged:
            if again[i] < thr * (0.5 + 0.5 * strict):
                keep.discard(i)
    return keep, thr



# ----------------------------------------------------------------------------
# planning domain (records are jobs: tick, value, cost, est_duration, uncertainty, deadline)

def _plan_ctx(data):
    recs = data["records"]
    nominal = {t["tick"]: t["nominal_capacity"] for t in data.get("ticks", [])}
    history = [(t["nominal_capacity"], t["realized_capacity"]) for t in data.get("ticks", []) if t.get("realized_capacity") is not None]
    return recs, nominal, history


def _rank01(xs):
    """Rank-normalize to [0, 1] (1 = best)."""
    n = len(xs)
    if n <= 1:
        return [1.0] * n
    order = sorted(range(n), key=lambda i: xs[i])
    out = [0.0] * n
    for r, i in enumerate(order):
        out[i] = r / (n - 1)
    return out


def _fit_scores(recs, capacity_by_tick, order_key):
    """Greedy fit at arrival tick in order of order_key: 1 if the job fits, else 0."""
    used = {}
    fit = [0.0] * len(recs)
    for i in sorted(range(len(recs)), key=order_key):
        t, val, cost, est, unc, dl = recs[i]
        cap = capacity_by_tick.get(int(t), 0.0)
        need = cost * est
        if used.get(int(t), 0.0) + need <= cap:
            used[int(t)] = used.get(int(t), 0.0) + need
            fit[i] = 1.0
    return fit


def priority_filter(data, window, prior):
    recs, _, _ = _plan_ctx(data)
    return _rank01([r[1] / max(r[2], 1e-6) for r in recs])


def risk_estimator(data, window, prior):
    recs, _, _ = _plan_ctx(data)
    return _rank01([(r[1] / max(r[2], 1e-6)) * (1.0 - min(0.9, r[4])) for r in recs])


def capacity_forecaster(data, window, prior):
    """Estimate realized/nominal bias from history (or carried prior) and fit jobs to forecast capacity."""
    recs, nominal, history = _plan_ctx(data)
    tail = history[-window:]
    if tail:
        bias = sum(r / n for n, r in tail) / len(tail)
    else:
        bias = prior.get("capacity_bias", 1.0)
    forecast = {t: c * bias for t, c in nominal.items()}
    return _fit_scores(recs, forecast, lambda i: -(recs[i][1] / max(recs[i][2], 1e-6)))


def feasibility_checker(data, window, prior):
    recs, nominal, _ = _plan_ctx(data)
    return _fit_scores(recs, nominal, lambda i: -(recs[i][1] / max(recs[i][2], 1e-6)))


def lookahead_planner(data, window, prior, pessimism=1.0):
    """Deadline-aware multi-tick greedy with deferral + improvement passes. Deliberately expensive."""
    recs, nominal, history = _plan_ctx(data)
    bias = prior.get("capacity_bias", 1.0)
    cap = {t: c * bias for t, c in nominal.items()}
    used = {}
    assign = {}
    order = sorted(range(len(recs)), key=lambda i: -(recs[i][1] / max(recs[i][2] * recs[i][3], 1e-6)))
    for i in order:
        t, val, cost, est, unc, dl = recs[i]
        need = cost * est * (1 + pessimism * unc)
        for tt in range(int(t), int(dl) + 1):
            if tt in cap and used.get(tt, 0.0) + need <= cap[tt]:
                used[tt] = used.get(tt, 0.0) + need
                assign[i] = tt
                break
    for _pass in range(3):  # improvement passes (cost grows with passes)
        for i in order:
            if i in assign:
                continue
            t, val, cost, est, unc, dl = recs[i]
            need = cost * est * (1 + pessimism * unc)
            for tt in range(int(t), int(dl) + 1):
                if tt not in cap:
                    continue
                holders = [j for j, tj in assign.items() if tj == tt]
                for j in sorted(holders, key=lambda j: recs[j][1]):
                    jneed = recs[j][2] * recs[j][3] * (1 + pessimism * recs[j][4])
                    if recs[j][1] < val and used[tt] - jneed + need <= cap[tt]:
                        used[tt] += need - jneed
                        del assign[j]
                        assign[i] = tt
                        break
                if i in assign:
                    break
    scores = [1.0 if i in assign else 0.0 for i in range(len(recs))]
    return scores, [assign.get(i) for i in range(len(recs))]


PLANNING_COMPONENTS = {"priority_filter", "risk_estimator", "capacity_forecaster", "feasibility_checker", "lookahead_planner"}


def run_planning_component(name, data, window, prior, assignments_out):
    if name == "priority_filter":
        return priority_filter(data, window, prior)
    if name == "risk_estimator":
        return risk_estimator(data, window, prior)
    if name == "capacity_forecaster":
        return capacity_forecaster(data, window, prior)
    if name == "feasibility_checker":
        return feasibility_checker(data, window, prior)
    if name == "lookahead_planner":
        scores, assign = lookahead_planner(data, window, prior)
        assignments_out.append(assign)
        return scores
    raise ValueError("unknown planning component %s" % name)


def _capacity_trim(recs, scores, thr, nominal, factor=1.0):
    """Verification helper: keep flagged jobs in score order while they fit factor*nominal."""
    keep = set()
    used = {}
    for i in sorted(range(len(recs)), key=lambda i: -scores[i]):
        if scores[i] <= thr:
            continue
        t, val, cost, est, unc, dl = recs[i]
        need = cost * est * factor
        cap = nominal.get(int(t), 0.0)
        if used.get(int(t), 0.0) + need <= cap:
            used[int(t)] = used.get(int(t), 0.0) + need
            keep.add(i)
    return keep


def execute_planning(spec, data, state, acct):
    p = spec["pipeline"]
    recs, nominal, history = _plan_ctx(data)
    n = len(recs)
    prior = state.get("stats", {}) if (state and p["memory"]["type"] != "none") else {}
    comps = p["perception"]["components"]
    window = p["perception"]["window"]
    r = p["reasoning"]
    thr, model = r["threshold"], r["model"]
    assignments_out = []
    score_lists = [run_planning_component(c, data, window, prior, assignments_out) for c in comps]
    acct.component_calls += len(comps)
    mode = {"direct": "mean", "sequential": "sequential", "parallel": "parallel", "hierarchical": "mean", "iterative": "mean"}[r["type"]]
    scores = combine(score_lists, mode)
    acct.charge("model:%s" % model, 1, tokens_scale=n / 200.0)

    def refine(base):
        """A model call: large_reasoner re-plans at three pessimism levels and averages fit; small keeps base."""
        acct.charge("model:%s" % model, 1, tokens_scale=n / 200.0)
        if model != "large_reasoner":
            return base
        acc = [0.0] * n
        for pess in (0.5, 1.0, 1.5):
            fit = _fit_scores(recs, {t: c * prior.get("capacity_bias", 1.0) for t, c in nominal.items()},
                              lambda i: -(base[i]))
            _s, _a = lookahead_planner(data, window, prior, pessimism=pess)
            acct.component_calls += 1
            for i in range(n):
                acc[i] += 0.5 * fit[i] + 0.5 * _s[i]
        return [0.5 * base[i] + 0.5 * acc[i] / 3 for i in range(n)]

    if r["type"] == "hierarchical":
        refined = refine(scores)
        for i in range(n):
            if abs(scores[i] - thr) < 0.15:
                scores[i] = refined[i]
    elif r["type"] == "iterative":
        for _ in range(r["iterations"]):
            scores = refine(scores)
            keep = _capacity_trim(recs, scores, thr, nominal)
            flagged = sum(1 for s_ in scores if s_ > thr)
            if flagged and len(keep) < 0.8 * flagged:
                thr = min(0.95, thr + 0.05)
            elif flagged and len(keep) == flagged:
                thr = max(0.05, thr - 0.05)

    # verification
    v = p["verification"]
    if v["type"] == "none":
        keep = {i for i in range(n) if scores[i] > thr}
    elif v["type"] == "rule_based":
        keep = _capacity_trim(recs, scores, thr, nominal, factor=1.0)
    elif v["type"] == "execution_based":
        keep = _capacity_trim(recs, scores, thr, nominal, factor=1.0 + v["strictness"] * 0.5)
        acct.component_calls += 1
    elif v["type"] == "model_based":
        refined = refine(scores)
        keep = {i for i in range(n) if scores[i] > thr and refined[i] >= thr - 0.1 * (1 - v["strictness"])}
    else:
        keep = {i for i in range(n) if scores[i] > thr}
    preds = [1 if i in keep else 0 for i in range(n)]
    assignments = None
    if assignments_out:
        assignments = [assignments_out[-1][i] if preds[i] else None for i in range(n)]
    # memory: carry the capacity bias estimate forward
    new_state = {}
    if p["memory"]["type"] != "none":
        tail = history[-max(5, p["memory"]["capacity"] // 10):]
        bias = sum(rr / nn for nn, rr in tail) / len(tail) if tail else prior.get("capacity_bias", 1.0)
        new_state = {"stats": {"capacity_bias": bias}}
        if p["memory"]["type"] == "vector":
            acct.charge("model:embedding_model", 1)
    out = {"predictions": preds, "threshold": thr, "state": new_state}
    if assignments is not None:
        out["assignments"] = assignments
    if p["output"].get("confidence", True):
        out["confidence"] = [round(s_, 4) for s_ in scores]
    return out

# ----------------------------------------------------------------------------
# main

def execute(payload):
    spec = payload["spec"]
    data = payload["data"]
    state = payload.get("state") or {}
    records = data["records"]
    nfeat = len(data["feature_names"])
    cols = [[float(r[j]) for r in records] for j in range(nfeat)]
    acct = Accounting(spec.get("cost_profiles", {}))
    for key in spec.get("required_capabilities", []):
        if key.startswith("tool:") or key.startswith("reasoning:") or key.startswith("memory:") or key.startswith("verification:"):
            acct.charge(key, 1)
    if data.get("domain") == "planning":
        out = execute_planning(spec, data, state, acct)
        out["accounting"] = {"model_calls": acct.model_calls, "tokens": acct.tokens, "cost": round(acct.cost, 6),
                             "simulated_latency_ms": acct.latency_ms, "component_calls": acct.component_calls, "calls": acct.calls}
        return out
    prior = load_prior(spec, state, cols)
    scores, score_lists, thr = reason(spec, cols, data, prior, acct)
    scores = vector_boost(spec, state, cols, scores)
    keep, thr = verify(spec, cols, data, prior, scores, score_lists, thr, acct)
    preds = [1 if i in keep else 0 for i in range(len(scores))]
    new_state = update_state(spec, state, cols, scores, thr, acct, data)
    out = {"predictions": preds, "threshold": thr}
    if spec["pipeline"]["output"].get("confidence", True):
        out["confidence"] = [round(s, 4) for s in scores]
    out["accounting"] = {"model_calls": acct.model_calls, "tokens": acct.tokens, "cost": round(acct.cost, 6),
                         "simulated_latency_ms": acct.latency_ms, "component_calls": acct.component_calls,
                         "calls": acct.calls}
    out["state"] = new_state
    return out


def main():
    t0 = time.monotonic()
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
        out = execute(payload)
        out["ok"] = True
    except Exception as e:  # report, never crash silently
        out = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
    ru = resource.getrusage(resource.RUSAGE_SELF)
    out["cpu_time_s"] = ru.ru_utime + ru.ru_stime
    out["max_rss_mb"] = ru.ru_maxrss / 1024.0
    out["runtime_s"] = time.monotonic() - t0
    sys.stdout.write(json.dumps(out))
    sys.stdout.flush()
    sys.exit(0 if out.get("ok") else 3)


if __name__ == "__main__":
    main()
