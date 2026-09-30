"""v0.3 environments: hidden regimes, structural twins (blind transfer), false analogies.

A v0.3 dataset is a stream of `steps` batches; each batch belongs to one hidden regime. The
regime changes the data process (noise, volatility, rate) and the constraints (memory, cpu,
verification cost factor, expensive-model availability, failure penalty). Constraint changes are
turned into environment events by the runner; the data regime is never exposed to agents.

Domains:
  training X : network, scientific, planning                    (native vocabulary)
  transfer Y : telemetry_grid, lab_assay, allocation             (twins: renamed, permuted, affine-transformed)
  false Z    : network_rules, scientific_drift, planning_stable   (same vocabulary as X, different structure)
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from typing import Any, Dict, List, Optional, Tuple

from environments import planning as P
from environments import synthetic as S

REGIMES = {
    "calm":      {"noise": 0.05, "volatility": 0.5, "rate": 0.03, "memory_mb": 512, "cpu": 1.0,  "vcf": 1.0, "penalty": 0.0, "large_model": True},
    "turbulent": {"noise": 0.25, "volatility": 3.0, "rate": 0.03, "memory_mb": 512, "cpu": 1.0,  "vcf": 6.0, "penalty": 0.2, "large_model": True},
    "starved":   {"noise": 0.10, "volatility": 1.0, "rate": 0.03, "memory_mb": 90,  "cpu": 0.5,  "vcf": 1.0, "penalty": 0.5, "large_model": False},
    "H1":        {"noise": 0.35, "volatility": 2.0, "rate": 0.03, "memory_mb": 512, "cpu": 1.0,  "vcf": 8.0, "penalty": 0.3, "large_model": True},
    "H2":        {"noise": 0.05, "volatility": 0.5, "rate": 0.03, "memory_mb": 100, "cpu": 0.5,  "vcf": 4.0, "penalty": 0.5, "large_model": False},
    "H3":        {"noise": 0.20, "volatility": 4.0, "rate": 0.03, "memory_mb": 128, "cpu": 0.75, "vcf": 2.0, "penalty": 0.2, "large_model": True},
}
TRAINING_SET = ["calm", "turbulent", "starved"]
HELDOUT_SET = ["H1", "H2", "H3"]

BASE_OF = {"network": "network", "scientific": "scientific", "planning": "planning",
           "telemetry_grid": "network", "lab_assay": "scientific", "allocation": "planning",
           "network_rules": "network", "scientific_drift": "scientific", "planning_stable": "planning"}
TWINS = {"telemetry_grid", "lab_assay", "allocation"}
FALSE = {"network_rules", "scientific_drift", "planning_stable"}
TASK_TYPE = {"network": "anomaly_detection", "scientific": "scientific_verification", "planning": "resource_planning"}

# --- structural twins: renamed features/components, permuted order, affine transforms ----------
TWIN_FEATURES = {
    "telemetry_grid": {"names": ["fault_ratio", "lag", "flux_a", "flux_b"], "perm": [3, 2, 0, 1],       # new index i takes old feature perm[i]
                       "affine": [(1000.0, 5.0), (0.01, -0.2), (2.5e-6, 1.0), (0.05, 3.0)]},
    "lab_assay": {"names": ["reagent_pressure", "signal_v", "bath_temp", "throughput"], "perm": [1, 2, 0, 3],
                  "affine": [(10.0, -700.0), (100.0, 0.0), (1.8, -459.67), (0.25, 2.0)]},
    "allocation": {"names": ["slot", "worth", "bandwidth_units", "estimate", "jitter", "expiry"], "perm": [0, 1, 2, 3, 4, 5],
                   "affine": [(1.0, 0.0), (3.0, 0.0), (0.5, 0.0), (1.0, 0.0), (1.0, 0.0), (1.0, 0.0)]},
}
COMPONENT_ALIASES = {  # twin component name -> implementation name (used by the sandbox runner)
    "flux_zscore": "statistical_detector", "robust_flux": "anomaly_detector", "flux_delta": "rate_detector",
    "flux_bounds": "range_validator", "flux_relation": "consistency_checker",
    "request_ranker": "priority_filter", "risk_weighting": "risk_estimator", "bandwidth_forecast": "capacity_forecaster",
    "admission_check": "feasibility_checker", "horizon_scheduler": "lookahead_planner",
}


def dataset_key(domain: str, size: int, schedule: List[Dict[str, Any]], seed: int, structure: str) -> str:
    return hashlib.sha256(json.dumps([domain, size, schedule, seed, structure, "v0.3"], sort_keys=True).encode()).hexdigest()[:16]


def sample_schedule(regime_set: List[str], steps: int, seed: int) -> List[Dict[str, Any]]:
    """Three regimes in seeded random order with seeded transition steps (first in {2,3,4}, second in {5,6,7})."""
    rng = random.Random(f"schedule:{seed}")
    order = list(regime_set)
    rng.shuffle(order)
    t1 = rng.choice([2, 3, 4])
    t2 = rng.choice([5, 6, 7])
    return [{"regime": order[0], "start_step": 0}, {"regime": order[1], "start_step": t1}, {"regime": order[2], "start_step": t2}]


def regime_at(schedule: List[Dict[str, Any]], step: int) -> str:
    cur = schedule[0]["regime"]
    for s in schedule:
        if step >= s["start_step"]:
            cur = s["regime"]
    return cur


# --- segment generators (base domains with volatility + structure variants) -------------------

def _segment(base: str, structure: str, n: int, reg: Dict[str, Any], seed: int, tick0: int) -> Dict[str, Any]:
    """Generate n records of one regime. Returns dict(records, labels, truth?, ticks?, segments)."""
    rng = random.Random(seed)
    noise, vol, rate = reg["noise"], reg["volatility"], reg["rate"]
    if base == "network":
        if structure == "rules":
            return _network_rules(rng, n, noise, rate)
        recs, labels, segs = S._network(rng, n, noise, rate) if vol == 1.0 else _network_vol(rng, n, noise, rate, vol)
        return {"records": recs, "labels": labels, "segments": segs}
    if base == "scientific":
        if structure == "drift":
            return _scientific_drift(rng, n, noise, rate)
        recs, labels, segs = S._scientific(rng, n, noise, rate) if vol == 1.0 else _scientific_vol(rng, n, noise, rate, vol)
        return {"records": recs, "labels": labels, "segments": segs}
    if base == "planning":
        return _planning_segment(rng, n, noise, rate, vol, tick0, stable=(structure == "stable"))
    raise ValueError(base)


def _network_vol(rng, size, noise, rate, vol):
    """Network with volatility: drift shifts every 400/vol records with magnitude scaled by vol."""
    recs, labels, segments = [], [0] * size, []
    drift = 0.0
    n_anom = max(1, int(size * rate / 4))
    starts = S._stratified_starts(rng, size, n_anom)
    kinds = ["burst", "drop", "latency_spike", "error_surge"]
    anom_at = {}
    for s in starts:
        k = rng.choice(kinds); length = rng.randint(1, 8)
        for i in range(s, min(size, s + length)):
            anom_at[i] = k; labels[i] = 1
        segments.append({"start": s, "length": length, "kind": k})
    period = max(20, int(400 / vol))
    for t in range(size):
        if t % period == 0 and t > 0:
            drift += rng.uniform(-0.15, 0.15) * vol
        diurnal = 1.0 + 0.3 * math.sin(2 * math.pi * t / 600.0) + drift
        b = 1.0e6 * max(0.05, diurnal) * (1 + rng.gauss(0, noise))
        p = 0.002 * b * (1 + rng.gauss(0, noise * 0.7))
        lat = 40.0 * (1 + rng.gauss(0, noise * 1.5)); err = abs(rng.gauss(0.01, noise * 0.02))
        k = anom_at.get(t)
        if k == "burst":
            f = rng.uniform(3, 6); b *= f; p *= f * rng.uniform(0.8, 1.2)
        elif k == "drop":
            b *= rng.uniform(0.0, 0.1); p *= rng.uniform(0.0, 0.15)
        elif k == "latency_spike":
            lat *= rng.uniform(5, 15)
        elif k == "error_surge":
            err = rng.uniform(0.2, 0.8)
        recs.append([round(b, 2), round(p, 2), round(lat, 3), round(err, 5)])
    return recs, labels, segments


def _network_rules(rng, size, noise, rate):
    """False analogy: network vocabulary, but anomalies are protocol/range violations only."""
    recs, labels = [], [0] * size
    n_anom = max(1, int(size * rate / 2))
    for s in S._stratified_starts(rng, size, n_anom):
        for i in range(s, min(size, s + rng.randint(1, 3))):
            labels[i] = 1
    for t in range(size):
        b = 1.0e6 * (1 + 0.3 * math.sin(2 * math.pi * t / 600.0)) * (1 + rng.gauss(0, noise))
        p = 0.002 * b * (1 + rng.gauss(0, noise * 0.7)); lat = 40.0 * (1 + rng.gauss(0, noise * 1.5)); err = abs(rng.gauss(0.01, noise * 0.02))
        if labels[t]:
            which = rng.choice(["b", "p", "lat", "err"])
            if which == "b": b = rng.uniform(5.1e6, 8e6)
            elif which == "p": p = rng.uniform(20500, 30000)
            elif which == "lat": lat = rng.uniform(2100, 4000)
            else: err = rng.uniform(1.01, 1.5)
        recs.append([round(b, 2), round(p, 2), round(lat, 3), round(err, 5)])
    return {"records": recs, "labels": labels, "segments": []}


def _scientific_vol(rng, size, noise, rate, vol):
    recs, labels, segments = S._scientific(rng, size, noise, rate)
    # volatility: superimpose calibration wobble that grows with vol (benign, not labelled)
    for t in range(size):
        w = 1 + 0.02 * vol * math.sin(2 * math.pi * t / max(30, 200 / vol))
        recs[t][0] = round(recs[t][0] * w, 3); recs[t][1] = round(recs[t][1] * w, 3)
    return recs, labels, segments


def _scientific_drift(rng, size, noise, rate):
    """False analogy: scientific vocabulary, anomalies are slow in-range drifts (20-40 records)."""
    recs, labels = [], [0] * size
    n_anom = max(1, int(size * rate / 25))
    starts = S._stratified_starts(rng, size, n_anom)
    drift_at = {}
    for s in starts:
        L = rng.randint(20, 40); sign = rng.choice([-1, 1])
        for i in range(s, min(size, s + L)):
            drift_at[i] = sign * (i - s) / L * 12.0; labels[i] = 1
    for t in range(size):
        temp = 300.0 + 20.0 * math.sin(2 * math.pi * t / 500.0) + rng.gauss(0, 3 * noise * 10) + drift_at.get(t, 0.0)
        pres = 0.35 * temp - 5.0 + rng.gauss(0, noise * 8); volt = 3.3 + rng.gauss(0, noise * 2)
        flow = 1.2 * math.sqrt(max(pres, 0)) + rng.gauss(0, noise * 4)
        recs.append([round(temp, 3), round(pres, 3), round(volt, 4), round(flow, 3)])
    return {"records": recs, "labels": labels, "segments": []}


def _planning_segment(rng, n, noise, rate, vol, tick0, stable=False):
    load = 1.0 + rate * 10
    jobs, truth, ticks = [], [], []
    tick = tick0
    regime_len = max(10, int(rng.randint(40, 80) / vol)); regime_cap = rng.uniform(80, 120); regime_bias = 0.0 if stable else rng.uniform(-0.25, 0.1)
    while len(jobs) < n:
        if tick > tick0 and (tick - tick0) % regime_len == 0:
            regime_cap = rng.uniform(60, 140); regime_bias = 0.0 if stable else rng.uniform(-0.3, 0.1) * (1 + noise)
        nominal = regime_cap * (1 + 0.15 * math.sin(2 * math.pi * tick / 30.0))
        realized = nominal if stable else max(10.0, nominal * (1 + regime_bias + rng.gauss(0, noise * 0.5)))
        ticks.append({"tick": tick, "nominal_capacity": round(nominal, 2), "realized_capacity": round(realized, 2)})
        for _ in range(max(1, int(rng.gauss(5, 1.5)))):
            if len(jobs) >= n:
                break
            cost = rng.uniform(5, 40) * load; value = cost * rng.lognormvariate(0.0, 0.5)
            unc = 0.0 if stable else rng.uniform(0.05, 0.6) * (0.5 + noise)
            est = rng.uniform(0.8, 1.2); true = est if stable else max(0.3, est * (1 + rng.gauss(0, unc)))
            deadline = tick + (5 if stable else rng.choice([0, 0, 1, 2, 3, 5]))
            jobs.append([tick, round(value, 3), round(cost, 3), round(est, 3), round(unc, 3), deadline]); truth.append(round(true, 4))
        tick += 1
    return {"records": jobs, "truth": truth, "ticks": ticks, "labels": None, "segments": []}


# --- assembly --------------------------------------------------------------------------------

def generate(domain: str, size: int, schedule: List[Dict[str, Any]], steps: int, seed: int, validation_fraction: float = 0.2) -> Dict[str, Any]:
    base = BASE_OF[domain]
    structure = {"network_rules": "rules", "scientific_drift": "drift", "planning_stable": "stable"}.get(domain, "native")
    n_val = int(size * validation_fraction)
    n_stream = size - n_val
    batch = n_stream // steps
    reg0 = REGIMES[schedule[0]["regime"]]
    parts = [("val", _segment(base, structure, n_val, reg0, seed * 7919 + 1, 0))]
    tick = max((t["tick"] for t in parts[0][1].get("ticks", [])), default=-1) + 1
    for step in range(steps):
        n = batch if step < steps - 1 else n_stream - batch * (steps - 1)
        reg = REGIMES[regime_at(schedule, step)]
        seg = _segment(base, structure, n, reg, seed * 7919 + 2 + step, tick)
        tick = max((t["tick"] for t in seg.get("ticks", [])), default=tick - 1) + 1
        parts.append((f"step{step}", seg))
    records, labels, truth, ticks = [], [], [], []
    for _, seg in parts:
        records += seg["records"]
        if base == "planning":
            truth += seg["truth"]; ticks += seg["ticks"]
        else:
            labels += seg["labels"]
    ds: Dict[str, Any] = {"domain": domain, "base_domain": base, "structure": structure, "size": size, "seed": seed, "schedule": schedule, "steps": steps,
                          "records": records, "task_type": TASK_TYPE[base], "validation_records": n_val, "batch_size": batch,
                          "dataset_id": dataset_key(domain, size, schedule, seed, structure)}
    if base == "planning":
        ds.update({"truth": truth, "ticks": ticks, "feature_names": list(P.FEATURES), "ranges": {}, "relations": []})
        ds["labels"], ds["oracle_assignments"] = P.oracle_plan(records, truth, ticks)
    else:
        meta = S.DOMAINS[base]
        ds.update({"labels": labels, "feature_names": list(meta["feature_names"]), "ranges": dict(meta["ranges"]), "relations": [dict(r) for r in meta["relations"]]})
    if domain in TWINS:
        ds = _twin_transform(ds, domain)
    return ds


def _twin_transform(ds: Dict[str, Any], domain: str) -> Dict[str, Any]:
    tw = TWIN_FEATURES[domain]
    perm, aff, names = tw["perm"], tw["affine"], tw["names"]
    old_names = ds["feature_names"]
    new_records = []
    for r in ds["records"]:
        new_records.append([round(aff[i][0] * r[perm[i]] + aff[i][1], 5) for i in range(len(perm))])
    ds["records"] = new_records
    ds["feature_names"] = names
    if ds["base_domain"] == "planning":
        # value/cost scaled: capacity scales with cost (index 2), so scale ticks accordingly
        cs = aff[2][0]
        ds["ticks"] = [{**t, "nominal_capacity": round(t["nominal_capacity"] * cs, 3), "realized_capacity": round(t["realized_capacity"] * cs, 3)} for t in ds["ticks"]]
        ds["value_scale"], ds["cost_scale"] = aff[1][0], cs
    else:
        new_ranges, new_rel = {}, []
        inv = {perm[i]: i for i in range(len(perm))}  # old index -> new index
        for i in range(len(perm)):
            lo, hi = ds["ranges"][old_names[perm[i]]]
            a, b = aff[i]
            new_ranges[names[i]] = [min(a * lo + b, a * hi + b), max(a * lo + b, a * hi + b)]
        for rel in ds["relations"]:
            xi, yi = inv[old_names.index(rel["x"])], inv[old_names.index(rel["y"])]
            ax, bx = aff[xi]; ay, by = aff[yi]
            if rel["kind"] == "linear":   # y = a x + b  ->  y' = ay*(a*(x'-bx)/ax + b) + by
                new_rel.append({"x": names[xi], "y": names[yi], "kind": "linear", "a": ay * rel["a"] / ax, "b": ay * (rel["b"] - rel["a"] * bx / ax) + by})
            # sqrt relations do not survive an affine transform of x exactly; the twin drops them (documented)
        ds["ranges"], ds["relations"] = new_ranges, new_rel
    return ds


def batch_payload(ds: Dict[str, Any], start: int, end: int) -> Dict[str, Any]:
    if ds["base_domain"] == "planning":
        p = P.batch_payload(ds, start, end)
        p["feature_names"] = ds["feature_names"]; p["domain"] = ds["domain"]; p["base_domain"] = "planning"
        return p
    return {"records": ds["records"][start:end], "feature_names": ds["feature_names"], "ranges": ds["ranges"], "relations": ds["relations"],
            "domain": ds["domain"], "base_domain": ds["base_domain"]}


def evaluate_batch(ds: Dict[str, Any], start: int, end: int, artifact: Dict[str, Any]) -> Dict[str, float]:
    from environments.scoring import score
    preds = artifact["predictions"]
    if ds["base_domain"] == "planning":
        sc = P.score_batch(ds, start, end, preds, artifact.get("assignments"))
        return sc
    return score(preds, ds["labels"][start:end])


def env_events_for(schedule: List[Dict[str, Any]], step_seconds: float, registry_keys: List[str]) -> List[Dict[str, Any]]:
    """Constraint changes at each regime transition, as runner events (observable through telemetry)."""
    events = []
    for s in schedule[1:]:
        r = REGIMES[s["regime"]]
        t = s["start_step"] * step_seconds
        events.append({"t": t, "type": "memory_reduction", "params": {"memory_mb": r["memory_mb"]}})
        events.append({"t": t, "type": "cpu_reduction", "params": {"cpu": r["cpu"]}})
        events.append({"t": t, "type": "verification_cost_change", "params": {"verification_cost_factor": r["vcf"], "failure_penalty": r["penalty"]}})
        if r["large_model"]:
            events.append({"t": t, "type": "capability_addition", "params": {"capabilities": ["model:large_reasoner"]}})
        else:
            events.append({"t": t, "type": "capability_removal", "params": {"capabilities": ["model:large_reasoner"]}})
    return events


def initial_profile_overrides(schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
    r = REGIMES[schedule[0]["regime"]]
    return {"memory_mb": r["memory_mb"], "cpu": r["cpu"], "verification_cost_factor": r["vcf"], "failure_penalty": r["penalty"], "large_model": r["large_model"]}
