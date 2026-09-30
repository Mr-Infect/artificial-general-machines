#!/usr/bin/env python3
"""v0.2 experiment program driver (spec sections 21-28).

    python3 scripts/run_v02_experiments.py --seeds 30 --workers 3 --executor docker

Generates one manifest per (experiment, seed) under results/v02/manifests/ (each is runnable on
its own with ``python -m experiments.run``), runs them with a process pool, and stores everything
under results/v02/. Memory files are per seed so every comparison is paired and isolated.

Job per seed:
  exp1  A (all baselines + AGM v0.1 + AGM v0.2, cold) → B (same + memory variants reading A's memory)
  exp2  sources A, B, C (AGM v0.2, writes memory) → merged warm memories → targets A, B, C with
        cold / from-S / warm-all / memory-mode ablations / economics ablations / AGM v0.1 memory
  exp8  held-out conditions on A, B, C: cold vs warm (memory from the standard-condition sources)
Experiments 3, 4, 5, 6, 7 are analyses over the exp2 target runs (see experiments/analysis.py).
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
V02 = ROOT / "results" / "v02"

DOMAINS = {
    "A": {"domain": "network", "type": "anomaly_detection", "target": 0.85, "verification_required": False,
          "fixed": {"perception": {"mode": "parallel", "components": ["statistical_detector", "anomaly_detector", "rate_detector"]},
                    "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}},
    "B": {"domain": "scientific", "type": "scientific_verification", "target": 0.80, "verification_required": True,
          "fixed": {"perception": {"mode": "parallel", "components": ["statistical_detector", "anomaly_detector", "rate_detector"]},
                    "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}},
    "C": {"domain": "planning", "type": "resource_planning", "target": 0.75, "verification_required": False,
          "fixed": {"perception": {"mode": "parallel", "components": ["priority_filter", "risk_estimator", "feasibility_checker"], "window": 20},
                    "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}},
}
EVENTS = [{"t": 10, "type": "memory_reduction", "params": {"memory_mb": 80}}, {"t": 20, "type": "network_loss"},
          {"t": 20, "type": "capability_removal", "params": {"capabilities": ["model:large_reasoner", "tool:search", "component:lookahead_planner"]}},
          {"t": 30, "type": "latency_reduction", "params": {"latency_ms": 800}}, {"t": 40, "type": "priority_increase", "params": {"priority": 3}}]
HELD_OUT_ENV = {"cpu": 0.5, "memory_mb": 100, "latency_ms": 1500, "network": True, "available_capabilities": "all", "verification_cost_factor": 8.0}
HELD_OUT_NOISE = 0.3


def base(name, key, seed, tags, agents, env=None, noise=0.1, events=EVENTS, description=""):
    d = DOMAINS[key]
    return {"experiment": {
        "name": name, "description": description, "tags": tags, "seed": seed, "repeats": 1,
        "task": {"type": d["type"], "domain": d["domain"], "dataset_size": 2000, "noise": noise, "anomaly_rate": 0.03,
                 "verification_required": d["verification_required"], "priority": 1},
        "environment": env or {"cpu": 1, "memory_mb": 512, "latency_ms": 2000, "network": True, "available_capabilities": "all"},
        "objective": {"quality_threshold": 0.0, "top_fraction": 0.1}, "budget": {"max_seconds": 120, "max_cost": 0.25, "step_timeout_s": 30},
        "schedule": {"steps": 5, "step_seconds": 10, "validation_fraction": 0.2}, "events": events, "agents": agents}}


def v2(name, memory_mode="none", econ="economic", db=None, read=True, write=True, max_evals=6, explore=False):
    a = {"name": name, "type": "agm_v2", "max_evaluations": max_evals, "memory_mode": memory_mode, "economics_mode": econ, "explore_all": explore}
    if db and memory_mode != "none":
        a["memory"] = {"read": read, "write": write, "db": str(db)}
        a["principle_memory"] = {"read": read, "write": write, "db": str(db)}
    return a


def v1(name, db=None, read=True, write=True, max_evals=6):
    a = {"name": name, "type": "agm", "max_evaluations": max_evals}
    if db:
        a["memory"] = {"read": read, "write": write, "db": str(db)}
    return a


def baselines(key):
    return [{"name": "fixed", "type": "fixed", "architecture": DOMAINS[key]["fixed"]}, {"name": "adaptive", "type": "adaptive"},
            {"name": "search", "type": "search", "max_evaluations": 8}, {"name": "self_evolving", "type": "self_evolving", "mutations_per_step": 2}]


def run_spec(spec: dict, db_path: Path, executor: str, mdir: Path, rdir: Path) -> str:
    from core.db import Database
    from experiments.manifest import parse_experiment
    from experiments.run import ExperimentRunner
    name = f"{spec['experiment']['name']}_s{spec['experiment']['seed']}.yaml"
    (mdir / name).write_text(yaml.safe_dump(spec, sort_keys=False))
    runner = ExperimentRunner(parse_experiment(spec), db=Database(db_path), executor_name=executor, results_root=rdir, quiet=True)
    return runner.run(seed=spec["experiment"]["seed"])


def job(args):
    kind, s, executor = args
    mdir, rdir, memdir, dbdir = V02 / "manifests", V02 / "runs", V02 / "memory", V02 / "db"
    db_path = dbdir / f"worker_{os.getpid()}.sqlite"
    t0 = time.time()
    out = {"kind": kind, "seed": s, "ids": {}, "error": None}
    try:
        if kind == "exp1":
            m1, m2 = memdir / f"exp1_v1_A_{s}.sqlite", memdir / f"exp1_v2_A_{s}.sqlite"
            for p in (m1, m2):
                p.unlink(missing_ok=True)
            specA = base("v02_exp1_A", "A", 1000 + s, ["v02_exp1"], baselines("A") + [v1("agm_v1_cold", m1), v2("agm_v2_cold", "full", db=m2), v2("agm_v2_explore", "full", db=m2, max_evals=8, explore=True)],
                         description="Exp 1 repeatability: Domain A source run (AGM variants write memory).")
            out["ids"]["A"] = run_spec(specA, db_path, executor, mdir, rdir)
            specB = base("v02_exp1_B", "B", 2000 + s, ["v02_exp1"], baselines("B") + [v1("agm_v1_cold"), v1("agm_v1_memory", m1), v2("agm_v2_cold", "none"), v2("agm_v2_memory", "full", db=m2)],
                         description="Exp 1 repeatability: Domain B with AGM v0.1 and v0.2, cold vs memory from Domain A (paired by seed).")
            out["ids"]["B"] = run_spec(specB, db_path, executor, mdir, rdir)
        elif kind == "exp2":
            from memory.merge import merge_memory_dbs
            src = {}
            for i, S in enumerate("ABC"):
                m = memdir / f"exp2_src_{S}_{s}.sqlite"
                m.unlink(missing_ok=True)
                spec = base(f"v02_exp2_src_{S}", S, 3000 + 100 * i + s, ["v02_exp2_src"], [v2("agm_v2_src", "full", db=m, max_evals=8, explore=True)],
                            description=f"Exp 2 source run in domain {S}: AGM v0.2 in exploration mode (evaluates up to 8 candidates per step regardless of early target) writes patterns and principles.")
                out["ids"][f"src_{S}"] = run_spec(spec, db_path, executor, mdir, rdir)
                src[S] = m
            for i, T in enumerate("ABC"):
                others = [S for S in "ABC" if S != T]
                merged = memdir / f"exp2_warm_{T}_{s}.sqlite"
                merge_memory_dbs([src[S] for S in others], merged)
                copies = {}
                for tag in ("full", "architecture", "principle", "task", "v1"):
                    c = memdir / f"exp2_warm_{T}_{s}_{tag}.sqlite"
                    shutil.copy(merged, c)
                    copies[tag] = c
                fromS = {}
                for S in others:
                    c = memdir / f"exp2_from_{S}_to_{T}_{s}.sqlite"
                    shutil.copy(src[S], c)
                    fromS[S] = c
                agents = [v2("v2_cold", "none")] + [v2(f"v2_from_{S}", "full", db=fromS[S]) for S in others] + [
                    v2("v2_warm_full", "full", db=copies["full"]), v2("v2_warm_architecture", "architecture", db=copies["architecture"]),
                    v2("v2_warm_principle", "principle", db=copies["principle"]), v2("v2_warm_task", "task", db=copies["task"]),
                    v2("v2_always_adapt", "none", econ="always_adapt"), v2("v2_never_adapt", "none", econ="never_adapt"),
                    v1("v1_warm_architecture", copies["v1"])]
                spec = base(f"v02_exp2_tgt_{T}", T, 4000 + 100 * i + s, ["v02_exp2_tgt"], agents,
                            description=f"Exp 2/3/4/5/7 target run in domain {T}: cold vs transferred memory (from each other domain and merged), memory-mode and economics ablations, AGM v0.1 with warm architecture memory.")
                out["ids"][f"tgt_{T}"] = run_spec(spec, db_path, executor, mdir, rdir)
                # exp8 held-out conditions with the standard-condition warm memory
                warm8 = memdir / f"exp8_warm_{T}_{s}.sqlite"
                shutil.copy(merged, warm8)
                spec8 = base(f"v02_exp8_heldout_{T}", T, 5000 + 100 * i + s, ["v02_exp8"], [v2("v2_cold", "none"), v2("v2_warm_full", "full", db=warm8)],
                             env=HELD_OUT_ENV, noise=HELD_OUT_NOISE,
                             description=f"Exp 8 held-out conditions in domain {T} (cpu 0.5, memory 100MB from t=0, noise {HELD_OUT_NOISE}, verification cost ×8): cold vs warm memory learned under standard conditions.")
                out["ids"][f"heldout_{T}"] = run_spec(spec8, db_path, executor, mdir, rdir)
    except Exception as e:  # keep failures as data
        out["error"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}"
    out["seconds"] = time.time() - t0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--executor", default="docker", choices=["docker", "process"])
    ap.add_argument("--only", nargs="*", default=["exp1", "exp2"], help="job kinds: exp1 exp2")
    ap.add_argument("--fresh", action="store_true", help="delete results/v02 first")
    args = ap.parse_args()
    if args.fresh and V02.exists():
        shutil.rmtree(V02)
    for d in ("manifests", "runs", "memory", "db", "analysis"):
        (V02 / d).mkdir(parents=True, exist_ok=True)
    if args.executor == "docker":
        from runtime.executor import DockerExecutor
        DockerExecutor().ensure_image()
    jobs = [(k, s, args.executor) for s in range(args.seeds) for k in args.only]
    t0 = time.time()
    log = (V02 / "driver_log.jsonl").open("a")
    print(f"{len(jobs)} jobs, {args.workers} workers, executor={args.executor}", flush=True)
    with Pool(args.workers) as pool:
        for i, res in enumerate(pool.imap_unordered(job, jobs)):
            log.write(json.dumps(res) + "\n"); log.flush()
            print(f"[{i + 1}/{len(jobs)}] {res['kind']} seed {res['seed']} {'ERROR' if res['error'] else 'ok'} {res['seconds']:.0f}s (elapsed {time.time() - t0:.0f}s)", flush=True)
            if res["error"]:
                print(res["error"][-600:], flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
