#!/usr/bin/env python3
"""v0.3 experiment program (spec v0.3 §13-14).

    python3 scripts/run_v03_experiments.py --seeds 30 --workers 4 --executor process

Per seed (one job):
  training  : agm_v3 (exploration mode) on network, scientific, planning with the TRAINING regime library → memory M_s
  transfer  : on each Y (telemetry_grid, lab_assay, allocation) and Z (network_rules, scientific_drift, planning_stable)
              environment with HELD-OUT regime combinations, all agents:
              fixed, adaptive, search, task_memory, architecture_memory, always_adapt, never_adapt,
              agm_cold, agm_full, agm_no_principle, agm_no_archmem, agm_no_negative, agm_no_economics, agm_no_regime
Every memory-reading agent gets its own copy of M_s (isolation). Manifests are stored and re-runnable.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import traceback
from multiprocessing import Pool
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
V03 = ROOT / "results" / "v03"
TRAIN = ["network", "scientific", "planning"]
Y_SET = ["telemetry_grid", "lab_assay", "allocation"]
Z_SET = ["network_rules", "scientific_drift", "planning_stable"]
TASK = {"network": "anomaly_detection", "scientific": "scientific_verification", "planning": "resource_planning"}
BASE = {"network": "network", "scientific": "scientific", "planning": "planning", "telemetry_grid": "network", "lab_assay": "scientific", "allocation": "planning",
        "network_rules": "network", "scientific_drift": "scientific", "planning_stable": "planning"}
FIXED = {"network": {"roles": ["broad_filter", "robust_estimator", "change_detector"]}, "scientific": {"roles": ["broad_filter", "robust_estimator", "change_detector"]},
         "planning": {"roles": ["broad_filter", "robust_estimator", "rule_check"]}}


def fixed_arch(domain: str) -> dict:
    from core.registry import CapabilityRegistry
    reg = CapabilityRegistry.load()
    by_role = {}
    for k in reg.keys_for_domain(domain):
        if k.startswith("component:"):
            c = k.split(":", 1)[1]
            by_role.setdefault(reg.get("component", c).params.get("role", c), c)
    comps = [by_role[r] for r in FIXED[BASE[domain]]["roles"] if r in by_role]
    return {"perception": {"mode": "parallel", "components": comps}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}


def base(name, domain, seed, tags, agents, regime_set, description=""):
    b = BASE[domain]
    return {"experiment": {
        "name": name, "description": description, "tags": tags, "seed": seed, "repeats": 1,
        "task": {"type": TASK[b], "domain": domain, "dataset_size": 3000, "noise": 0.1, "anomaly_rate": 0.03, "verification_required": b == "scientific", "priority": 1},
        "environment": {"cpu": 1, "memory_mb": 512, "latency_ms": 2000, "network": False, "available_capabilities": "all"},
        "objective": {"quality_threshold": 0.0}, "budget": {"max_seconds": 600, "max_cost": 1.0, "step_timeout_s": 30},
        "schedule": {"steps": 9, "step_seconds": 10, "validation_fraction": 0.2, "validation_mode": "recent"},
        "regime": {"set": regime_set, "oracle_points": 48}, "events": [], "agents": agents}}


def v3(name, db=None, explore=False, **flags):
    a = {"name": name, "type": "agm_v3", "max_evaluations": 6, "explore_all": explore, **flags}
    if db:
        a["memory"] = {"read": True, "write": True, "db": str(db)}
        a["principle_memory"] = {"read": True, "write": True, "db": str(db)}
    return a


def v2(name, memory_mode, db):
    return {"name": name, "type": "agm_v2", "max_evaluations": 6, "memory_mode": memory_mode, "memory": {"read": True, "write": True, "db": str(db)},
            "principle_memory": {"read": True, "write": True, "db": str(db)}}


def run_spec(spec, db_path, executor, mdir, rdir):
    from core.db import Database
    from experiments.manifest import parse_experiment
    from experiments.run import ExperimentRunner
    (mdir / f"{spec['experiment']['name']}_s{spec['experiment']['seed']}.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
    return ExperimentRunner(parse_experiment(spec), db=Database(db_path), executor_name=executor, results_root=rdir, quiet=True).run(seed=spec["experiment"]["seed"])


def job(args):
    s, executor = args
    mdir, rdir, memdir, dbdir = V03 / "manifests", V03 / "runs", V03 / "memory", V03 / "db"
    db_path = dbdir / f"worker_{os.getpid()}.sqlite"
    t0 = time.time()
    out = {"seed": s, "ids": {}, "error": None}
    try:
        mem = memdir / f"train_{s}.sqlite"
        mem.unlink(missing_ok=True)
        for i, d in enumerate(TRAIN):
            spec = base(f"v03_train_{d}", d, 10000 + 100 * i + s, ["v03_train"], [v3("agm_train", db=mem, explore=True)], "training",
                        description=f"v0.3 training run in {d} with the training regime library; AGM v0.3 in exploration mode writes memory.")
            out["ids"][f"train_{d}"] = run_spec(spec, db_path, executor, mdir, rdir)
        for j, d in enumerate(Y_SET + Z_SET):
            copies = {}
            for tag in ("full", "no_principle", "no_archmem", "no_negative", "no_economics", "no_regime", "task", "arch"):
                c = memdir / f"{d}_{s}_{tag}.sqlite"
                shutil.copy(mem, c); copies[tag] = c
            agents = [{"name": "fixed", "type": "fixed", "architecture": fixed_arch(d)}, {"name": "adaptive", "type": "adaptive", "library": "roles"},
                      {"name": "search", "type": "search", "space": "auto", "max_evaluations": 6},
                      v2("task_memory", "task", copies["task"]), v2("architecture_memory", "architecture", copies["arch"]),
                      v3("always_adapt", economics_mode="always_adapt"), v3("never_adapt", economics_mode="never_adapt"),
                      v3("agm_cold"), v3("agm_full", db=copies["full"]), v3("agm_no_principle", db=copies["no_principle"], use_principles=False),
                      v3("agm_no_archmem", db=copies["no_archmem"], use_archmem=False), v3("agm_no_negative", db=copies["no_negative"], use_negative=False),
                      v3("agm_no_economics", db=copies["no_economics"], economics_mode="always_adapt"), v3("agm_no_regime", db=copies["no_regime"], regime_detection=False)]
            kind = "Y" if d in Y_SET else "Z"
            spec = base(f"v03_{kind}_{d}", d, 20000 + 100 * j + s, [f"v03_{kind}"], agents, "heldout",
                        description=f"v0.3 {'blind-transfer' if kind == 'Y' else 'false-analogy'} environment {d} with held-out regime combinations; all agents, memory from the training runs of the same seed.")
            out["ids"][f"{kind}_{d}"] = run_spec(spec, db_path, executor, mdir, rdir)
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}"
    out["seconds"] = time.time() - t0
    return out


def job_with_retry(args):
    res = job(args)
    if res["error"] and "locked" in res["error"].lower():
        time.sleep(10)
        res = job(args)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--executor", default="process", choices=["docker", "process"])
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()
    if args.fresh and V03.exists():
        shutil.rmtree(V03)
    for d in ("manifests", "runs", "memory", "db", "analysis", "plots"):
        (V03 / d).mkdir(parents=True, exist_ok=True)
    import subprocess
    (V03 / "registration.json").write_text(json.dumps({"registration_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                                                        "design_doc": "docs/v0.3_design.md", "started": time.strftime("%Y-%m-%dT%H:%M:%S")}))
    seeds = list(range(args.seeds))
    if args.resume and (V03 / "driver_log.jsonl").exists():
        done = {json.loads(l)["seed"] for l in (V03 / "driver_log.jsonl").read_text().splitlines() if l.strip() and not json.loads(l).get("error")}
        seeds = [s for s in seeds if s not in done]
        print(f"resume: {len(done)} done, {len(seeds)} remaining", flush=True)
    jobs = [(s, args.executor) for s in seeds]
    t0 = time.time()
    log = (V03 / "driver_log.jsonl").open("a")
    print(f"{len(jobs)} jobs (1 per seed), {args.workers} workers, executor={args.executor}", flush=True)
    with Pool(args.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(job_with_retry, jobs)):
            log.write(json.dumps(res) + "\n"); log.flush()
            print(f"[{i + 1}/{len(jobs)}] seed {res['seed']} {'ERROR' if res['error'] else 'ok'} {res['seconds']:.0f}s (elapsed {time.time() - t0:.0f}s)", flush=True)
            if res["error"]:
                print(res["error"][-600:], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
