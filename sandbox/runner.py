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
