"""Domain C: resource-constrained planning (v0.2, spec section 6).

A stream of jobs arrives over discrete ticks. Each job has a value, a resource
cost, an *estimated* duration factor with a per-job uncertainty, and a deadline
(ticks after arrival). Every tick has a *nominal* capacity; the *realized*
capacity deviates by a persistent regime bias plus noise. A plan selects jobs
(and optionally defers them to a later tick before their deadline). Selected
jobs are processed in selection order; once realized capacity is exhausted the
remaining selected jobs fail and cost a penalty. Quality is realized value
divided by an oracle plan computed with the hidden true durations and
capacities.

What the sandbox may see (``batch_payload``): the jobs of the batch, the nominal
capacity of every tick, and the realized capacity of ticks *before* the batch
(history). It never sees true durations, realized capacity of the batch ticks,
or the oracle. See docs/domain_planning.md.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from typing import Any, Dict, List, Optional, Tuple

FEATURES = ["tick", "value", "cost", "est_duration", "uncertainty", "deadline"]
PENALTY = 0.5  # fraction of a failed job's value charged as penalty


def dataset_key(size: int, noise: float, load: float, seed: int) -> str:
    return hashlib.sha256(json.dumps(["planning", size, noise, load, seed], sort_keys=True).encode()).hexdigest()[:16]


def generate(size: int, noise: float, load: float, seed: int) -> Dict[str, Any]:
    """size = number of jobs; noise = capacity/duration uncertainty scale; load = mean demand / capacity."""
    rng = random.Random(seed)
    jobs: List[List[float]] = []
    truth: List[float] = []          # true duration factor per job
    ticks: List[Dict[str, Any]] = []
    tick = 0
    regime_len = rng.randint(40, 80)
    regime_cap = rng.uniform(80, 120)
    regime_bias = rng.uniform(-0.25, 0.1)
    while len(jobs) < size:
        if tick > 0 and tick % regime_len == 0:
            regime_cap = rng.uniform(60, 140)
            regime_bias = rng.uniform(-0.3, 0.1) * (1 + noise)
        nominal = regime_cap * (1 + 0.15 * math.sin(2 * math.pi * tick / 30.0))
        realized = max(10.0, nominal * (1 + regime_bias + rng.gauss(0, noise * 0.5)))
        ticks.append({"tick": tick, "nominal_capacity": round(nominal, 2), "realized_capacity": round(realized, 2)})
        n_jobs = max(1, int(rng.gauss(5, 1.5)))
        for _ in range(n_jobs):
            if len(jobs) >= size:
                break
            cost = rng.uniform(5, 40) * load
            value = cost * rng.lognormvariate(0.0, 0.5)
            unc = rng.uniform(0.05, 0.6) * (0.5 + noise)
            est = rng.uniform(0.8, 1.2)
            true = max(0.3, est * (1 + rng.gauss(0, unc)))
            deadline = tick + rng.choice([0, 0, 1, 2, 3, 5])
            jobs.append([tick, round(value, 3), round(cost, 3), round(est, 3), round(unc, 3), deadline])
            truth.append(round(true, 4))
        tick += 1
    labels, oracle_assign = oracle_plan(jobs, truth, ticks)
    return {"domain": "planning", "size": size, "noise": noise, "load": load, "seed": seed, "feature_names": FEATURES,
            "ranges": {}, "relations": [], "task_type": "resource_planning", "records": jobs, "truth": truth, "ticks": ticks,
            "labels": labels, "oracle_assignments": oracle_assign, "dataset_id": dataset_key(size, noise, load, seed)}


def simulate(jobs: List[List[float]], truth: List[float], ticks: List[Dict[str, Any]], selected: List[int],
             assignments: Optional[List[Optional[int]]] = None) -> Dict[str, Any]:
    """Run a plan against hidden truth. Returns realized value, penalties, per-job outcome."""
    cap = {t["tick"]: t["realized_capacity"] for t in ticks}
    used: Dict[int, float] = {}
    outcome = [0] * len(jobs)     # 0 not selected, 1 completed, -1 failed
    value = penalty = 0.0
    for i, s in enumerate(selected):
        if not s:
            continue
        arrival, val, cost, _, _, deadline = jobs[i]
        t = int(assignments[i]) if assignments and assignments[i] is not None else int(arrival)
        if t < arrival or t > deadline or t not in cap:
            outcome[i] = -1
            penalty += PENALTY * val
            continue
        need = cost * truth[i]
        if used.get(t, 0.0) + need <= cap[t]:
            used[t] = used.get(t, 0.0) + need
            outcome[i] = 1
            value += val
        else:
            used[t] = cap[t]
            outcome[i] = -1
            penalty += PENALTY * val
    return {"realized_value": value, "penalty": penalty, "net_value": value - penalty, "outcome": outcome,
            "n_completed": sum(1 for o in outcome if o == 1), "n_failed": sum(1 for o in outcome if o == -1)}


def oracle_plan(jobs: List[List[float]], truth: List[float], ticks: List[Dict[str, Any]]) -> List[int]:
    """Strong (not provably optimal) plan using hidden truth: density-greedy with deferral inside the
    deadline window, followed by a swap-improvement pass. Deterministic."""
    cap = {t["tick"]: t["realized_capacity"] for t in ticks}
    order = sorted(range(len(jobs)), key=lambda i: -(jobs[i][1] / (jobs[i][2] * truth[i])))
    used: Dict[int, float] = {}
    assign: Dict[int, int] = {}
    for i in order:
        arrival, val, cost, _, _, deadline = jobs[i]
        need = cost * truth[i]
        for t in range(int(arrival), int(deadline) + 1):
            if t in cap and used.get(t, 0.0) + need <= cap[t]:
                used[t] = used.get(t, 0.0) + need
                assign[i] = t
                break
    # improvement pass: try to fit unassigned jobs by evicting a lower-value job at some feasible tick
    for i in order:
        if i in assign:
            continue
        arrival, val, cost, _, _, deadline = jobs[i]
        need = cost * truth[i]
        for t in range(int(arrival), int(deadline) + 1):
            if t not in cap:
                continue
            holders = [j for j, tj in assign.items() if tj == t]
            for j in sorted(holders, key=lambda j: jobs[j][1]):
                if jobs[j][1] < val and used[t] - jobs[j][2] * truth[j] + need <= cap[t]:
                    used[t] += need - jobs[j][2] * truth[j]
                    del assign[j]
                    assign[i] = t
                    break
            if i in assign:
                break
    return [1 if i in assign else 0 for i in range(len(jobs))], [assign.get(i) for i in range(len(jobs))]


def oracle_value(ds: Dict[str, Any], start: int, end: int) -> float:
    jobs, truth = ds["records"][start:end], ds["truth"][start:end]
    plan, assign = oracle_plan(jobs, truth, ds["ticks"])
    return simulate(jobs, truth, ds["ticks"], plan, assign)["net_value"]


def batch_payload(ds: Dict[str, Any], start: int, end: int) -> Dict[str, Any]:
    first_tick = int(ds["records"][start][0]) if start < len(ds["records"]) else 0
    ticks = [{"tick": t["tick"], "nominal_capacity": t["nominal_capacity"],
              "realized_capacity": t["realized_capacity"] if t["tick"] < first_tick else None} for t in ds["ticks"]]
    return {"records": ds["records"][start:end], "feature_names": FEATURES, "ranges": {}, "relations": [],
            "domain": "planning", "ticks": ticks}


def score_batch(ds: Dict[str, Any], start: int, end: int, predictions: List[int], assignments: Optional[List[Optional[int]]] = None) -> Dict[str, float]:
    jobs, truth = ds["records"][start:end], ds["truth"][start:end]
    sim = simulate(jobs, truth, ds["ticks"], predictions, assignments)
    oracle = oracle_value(ds, start, end)
    labels = ds["labels"][start:end]
    tp = sum(1 for p, l in zip(predictions, labels) if p and l)
    fp = sum(1 for p, l in zip(predictions, labels) if p and not l)
    fn = sum(1 for p, l in zip(predictions, labels) if not p and l)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    quality = max(0.0, min(1.0, sim["net_value"] / oracle)) if oracle > 0 else (1.0 if sim["net_value"] >= 0 else 0.0)
    return {"quality": quality, "f1": f1, "precision": precision, "recall": recall,
            "accuracy": sum(1 for p, l in zip(predictions, labels) if p == l) / max(1, len(labels)),
            "realized_value": sim["realized_value"], "penalty": sim["penalty"], "net_value": sim["net_value"],
            "oracle_value": oracle, "n_completed": sim["n_completed"], "n_failed": sim["n_failed"], "n_selected": int(sum(predictions))}
