"""Synthetic exercise environments (Sections 11 and 16).

Domain A ``network``: synthetic network telemetry with bursts, drops,
latency spikes and error surges, plus benign drift.
Domain B ``scientific``: synthetic instrument readings with declared
physical ranges and cross-feature relations; anomalies are out-of-range
readings, spikes, relation breaks (calibration faults) and stuck sensors.

Datasets are deterministic functions of (domain, size, noise, anomaly_rate,
seed) and are cached under ``datasets/``.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "datasets"

DOMAINS = {
    "network": {
        "feature_names": ["bytes_per_s", "packets_per_s", "latency_ms", "error_rate"],
        "ranges": {"bytes_per_s": [0, 5e6], "packets_per_s": [0, 20000], "latency_ms": [0, 2000], "error_rate": [0, 1]},
        "relations": [{"x": "bytes_per_s", "y": "packets_per_s", "kind": "linear", "a": 0.002, "b": 0.0}],
        "task_type": "anomaly_detection",
    },
    "scientific": {
        "feature_names": ["temperature_k", "pressure_kpa", "voltage_v", "flow_lpm"],
        "ranges": {"temperature_k": [250, 400], "pressure_kpa": [80, 140], "voltage_v": [0, 5], "flow_lpm": [0, 30]},
        "relations": [{"x": "temperature_k", "y": "pressure_kpa", "kind": "linear", "a": 0.35, "b": -5.0},
                      {"x": "pressure_kpa", "y": "flow_lpm", "kind": "sqrt", "a": 1.2, "b": 0.0}],
        "task_type": "scientific_verification",
    },
}


def dataset_key(domain: str, size: int, noise: float, anomaly_rate: float, seed: int) -> str:
    raw = json.dumps([domain, size, noise, anomaly_rate, seed], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _stratified_starts(rng: random.Random, size: int, n: int) -> List[int]:
    """Spread anomaly segments over the stream (one per stratum, jittered) so that
    every batch of a multi-step experiment contains some positives."""
    stratum = (size - 40) / n
    starts = []
    for k in range(n):
        lo = int(20 + k * stratum)
        hi = max(lo + 1, int(20 + (k + 1) * stratum) - 12)
        starts.append(rng.randint(lo, hi))
    return sorted(starts)


def _network(rng: random.Random, size: int, noise: float, anomaly_rate: float) -> Tuple[List[List[float]], List[int], List[Dict[str, Any]]]:
    recs, labels, segments = [], [0] * size, []
    drift = 0.0
    n_anom = max(1, int(size * anomaly_rate / 4))  # ~4 records per segment on average
    starts = _stratified_starts(rng, size, n_anom)
    kinds = ["burst", "drop", "latency_spike", "error_surge"]
    anom_at: Dict[int, str] = {}
    for s in starts:
        k = rng.choice(kinds)
        length = rng.randint(1, 8)
        for i in range(s, min(size, s + length)):
            anom_at[i] = k
            labels[i] = 1
        segments.append({"start": s, "length": length, "kind": k})
    for t in range(size):
        if t % 400 == 0 and t > 0:
            drift += rng.uniform(-0.15, 0.15)  # benign slow level shift
        diurnal = 1.0 + 0.3 * math.sin(2 * math.pi * t / 600.0) + drift
        b = 1.0e6 * diurnal * (1 + rng.gauss(0, noise))
        p = 0.002 * b * (1 + rng.gauss(0, noise * 0.7))
        lat = 40.0 * (1 + rng.gauss(0, noise * 1.5))
        err = abs(rng.gauss(0.01, noise * 0.02))
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


def _scientific(rng: random.Random, size: int, noise: float, anomaly_rate: float):
    recs, labels, segments = [], [0] * size, []
    n_anom = max(1, int(size * anomaly_rate / 4))
    starts = _stratified_starts(rng, size, n_anom)
    kinds = ["out_of_range", "spike", "relation_break", "stuck_sensor"]
    anom_at: Dict[int, str] = {}
    for s in starts:
        k = rng.choice(kinds)
        length = rng.randint(1, 8) if k != "stuck_sensor" else rng.randint(4, 10)
        for i in range(s, min(size, s + length)):
            anom_at[i] = k
            labels[i] = 1
        segments.append({"start": s, "length": length, "kind": k})
    stuck_val = None
    for t in range(size):
        temp = 300.0 + 20.0 * math.sin(2 * math.pi * t / 500.0) + rng.gauss(0, 3 * noise * 10)
        pres = 0.35 * temp - 5.0 + rng.gauss(0, noise * 8)
        volt = 3.3 + rng.gauss(0, noise * 2)
        flow = 1.2 * math.sqrt(max(pres, 0)) + rng.gauss(0, noise * 4)
        k = anom_at.get(t)
        if k == "out_of_range":
            which = rng.choice(["temp", "pres", "volt"])
            if which == "temp":
                temp = rng.choice([rng.uniform(200, 245), rng.uniform(405, 450)])
            elif which == "pres":
                pres = rng.choice([rng.uniform(40, 75), rng.uniform(145, 180)])
            else:
                volt = rng.choice([rng.uniform(-1, -0.1), rng.uniform(5.2, 7)])
        elif k == "spike":
            temp += rng.choice([-1, 1]) * rng.uniform(15, 40)
        elif k == "relation_break":
            pres = 0.35 * temp - 5.0 + rng.choice([-1, 1]) * rng.uniform(8, 20)
        elif k == "stuck_sensor":
            if stuck_val is None:
                stuck_val = (temp, pres)
            temp, pres = stuck_val
        else:
            stuck_val = None
        recs.append([round(temp, 3), round(pres, 3), round(volt, 4), round(flow, 3)])
    return recs, labels, segments


def generate(domain: str, size: int, noise: float, anomaly_rate: float, seed: int) -> Dict[str, Any]:
    if domain not in DOMAINS:
        raise ValueError(f"unknown domain {domain}")
    rng = random.Random(seed)
    if domain == "network":
        recs, labels, segments = _network(rng, size, noise, anomaly_rate)
    else:
        recs, labels, segments = _scientific(rng, size, noise, anomaly_rate)
    meta = DOMAINS[domain]
    return {"domain": domain, "size": size, "noise": noise, "anomaly_rate": anomaly_rate, "seed": seed,
            "feature_names": meta["feature_names"], "ranges": meta["ranges"], "relations": meta["relations"],
            "task_type": meta["task_type"], "records": recs, "labels": labels, "segments": segments,
            "dataset_id": dataset_key(domain, size, noise, anomaly_rate, seed)}


def load_or_generate(domain: str, size: int, noise: float, anomaly_rate: float, seed: int) -> Dict[str, Any]:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    key = dataset_key(domain, size, noise, anomaly_rate, seed)
    path = DATASET_DIR / f"{domain}_{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    ds = generate(domain, size, noise, anomaly_rate, seed)
    path.write_text(json.dumps(ds))
    return ds


def batch_payload(ds: Dict[str, Any], start: int, end: int) -> Dict[str, Any]:
    """The part of a dataset a sandbox is allowed to see: records only, no labels."""
    return {"records": ds["records"][start:end], "feature_names": ds["feature_names"], "ranges": ds["ranges"],
            "relations": ds["relations"], "domain": ds["domain"]}
