"""Report generation (Section 17). Raw measurements, never verdicts.

    python -m experiments.report <experiment_id> [...]      one report per experiment
    python -m experiments.report --suite <name-or-tag>       cross-experiment comparison with CIs

Bootstrap confidence intervals are computed over repeated seeds when there
are at least two; otherwise the report says so. Pareto frontiers are over
(total_cost, quality_mean). Transfer measurements compare agents whose names
end in ``_memory`` with their ``_cold`` counterparts in the same experiment.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from core.db import Database

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

AGG_METRICS = ["quality_mean", "quality_min", "quality_final", "time_to_target_logical_s", "time_to_target_wall_s",
               "search_time_s", "architecture_evaluations", "model_calls", "tokens", "cpu_time_s", "max_memory_mb",
               "execution_cost", "adaptation_cost", "total_cost", "constraint_violations", "failures", "novelty_mean",
               "distinct_architectures", "wall_used_s"]


def bootstrap_ci(xs: Sequence[float], n: int = 2000, alpha: float = 0.05, seed: int = 0) -> Tuple[float, float, float]:
    xs = [x for x in xs if x is not None]
    if not xs:
        return (float("nan"),) * 3
    if len(xs) == 1:
        return xs[0], xs[0], xs[0]
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return statistics.fmean(xs), means[int(alpha / 2 * n)], means[int((1 - alpha / 2) * n) - 1]


def pareto_front(points: Dict[str, Tuple[float, float]]) -> List[str]:
    """points: name -> (cost, quality). Minimise cost, maximise quality."""
    front = []
    for a, (ca, qa) in points.items():
        dominated = any((cb <= ca and qb >= qa) and (cb < ca or qb > qa) for b, (cb, qb) in points.items() if b != a)
        if not dominated:
            front.append(a)
    return sorted(front, key=lambda n: points[n][0])


def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def experiment_report(db: Database, experiment_id: str) -> Dict[str, Any]:
    exp = db.experiment(experiment_id)
    if not exp:
        raise ValueError(f"unknown experiment {experiment_id}")
    summary: Dict[str, Any] = exp.get("summary", {})
    manifest = exp["manifest"]
    target = manifest["objective"]["quality_threshold"]
    execs = db.executions(experiment_id)
    evals = {e["execution_id"]: e for e in db.evaluations(experiment_id)}
    events = db.env_events(experiment_id)
    decisions = db.decisions(experiment_id)
    per_step: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    failed_runs = []
    for e in execs:
        ev = evals.get(e["execution_id"])
        rec = {"step": e["step"], "t": e["logical_time_s"], "purpose": e["purpose"], "arch": e["architecture_hash"],
               "name": e["architecture"].get("name"), "runtime_s": e["result"]["runtime_s"], "cpu_time_s": e["result"]["cpu_time_s"],
               "memory_mb": e["result"]["max_memory_mb"], "exit_code": e["result"]["exit_code"],
               "violation": e["result"].get("resource_violation"), "quality": (ev or {}).get("quality", e.get("extra", {}).get("quality")),
               "env_memory_mb": e["environment_snapshot"].get("memory_mb"), "env_network": e["environment_snapshot"].get("network")}
        if e["purpose"] == "task":
            per_step[e["agent"]].append(rec)
        if e["result"]["exit_code"] != 0 or e["result"].get("resource_violation") or (ev and ev.get("failed")):
            failed_runs.append({"agent": e["agent"], **rec, "stderr": e["result"].get("stderr", "")[:300]})
    points = {a: (s["total_cost"], s["quality_mean"]) for a, s in summary.items()}
    cpu_points = {a: (s["cpu_time_s"], s["quality_mean"]) for a, s in summary.items()}
    normalized = {a: {"quality_per_dollar": (s["quality_mean"] / s["total_cost"]) if s["total_cost"] > 0 else None,
                      "quality_per_cpu_second": (s["quality_mean"] / s["cpu_time_s"]) if s["cpu_time_s"] > 0 else None,
                      "adaptation_overhead_cost": (s["adaptation_cost"] / s["total_cost"]) if s["total_cost"] > 0 else 0.0,
                      "adaptation_overhead_time": (s["search_time_s"] / s["wall_used_s"]) if s["wall_used_s"] > 0 else 0.0}
                  for a, s in summary.items()}
    transfer = {}
    for a in summary:
        if a.endswith("_memory") and a[:-7] + "_cold" in summary:
            c, m = summary[a[:-7] + "_cold"], summary[a]
            transfer[a] = {"delta_quality_mean": m["quality_mean"] - c["quality_mean"],
                           "delta_quality_first_step": (per_step[a][0]["quality"] - per_step[a[:-7] + "_cold"][0]["quality"]) if per_step[a] and per_step[a[:-7] + "_cold"] else None,
                           "delta_time_to_target_logical_s": (None if m["time_to_target_logical_s"] is None or c["time_to_target_logical_s"] is None
                                                              else m["time_to_target_logical_s"] - c["time_to_target_logical_s"]),
                           "delta_architecture_evaluations": m["architecture_evaluations"] - c["architecture_evaluations"],
                           "delta_adaptation_cost": m["adaptation_cost"] - c["adaptation_cost"],
                           "delta_total_cost": m["total_cost"] - c["total_cost"],
                           "cold_reached_target": c["time_to_target_logical_s"] is not None,
                           "memory_reached_target": m["time_to_target_logical_s"] is not None}
    return {"experiment_id": experiment_id, "name": exp["name"], "seed": exp["seed"], "git_commit": exp["git_commit"],
            "manifest_hash": exp["manifest_hash"], "executor": exp.get("executor"), "target_quality": target,
            "task": manifest["task"], "environment": manifest["environment"], "events": manifest.get("events", []),
            "agents": summary, "per_step": per_step, "env_transitions": events, "adaptation_decisions": decisions,
            "pareto_front_cost": pareto_front(points), "pareto_front_cpu": pareto_front(cpu_points),
            "resource_normalized": normalized, "transfer": transfer, "failed_runs": failed_runs,
            "n_executions": len(execs), "n_candidate_evaluations": sum(1 for e in execs if e["purpose"] == "candidate_evaluation")}


def render_markdown(r: Dict[str, Any]) -> str:
    L: List[str] = []
    L.append(f"# Experiment report: {r['name']}\n")
    L.append(f"- id: `{r['experiment_id']}`  seed: {r['seed']}  executor: {r['executor']}  git: `{r['git_commit'][:12]}`  manifest: `{r['manifest_hash']}`")
    L.append(f"- task: {r['task']['type']} / {r['task']['domain']} (n={r['task']['dataset_size']}, noise={r['task']['noise']}, anomaly_rate={r['task']['anomaly_rate']})")
    L.append(f"- target quality: {r['target_quality']}  executions: {r['n_executions']} (candidate evaluations: {r['n_candidate_evaluations']})\n")
    L.append("This report lists measurements. It does not declare any agent successful.\n")
    agents = list(r["agents"])
    L.append("## Aggregate metrics per agent\n")
    L.append("| metric | " + " | ".join(agents) + " |")
    L.append("|---|" + "---|" * len(agents))
    for m in AGG_METRICS:
        L.append(f"| {m} | " + " | ".join(_fmt(r["agents"][a].get(m)) for a in agents) + " |")
    L.append("\n## Resource-normalized comparison\n")
    L.append("| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |")
    L.append("|---|---|---|---|---|")
    for a in agents:
        n = r["resource_normalized"][a]
        L.append(f"| {a} | {_fmt(n['quality_per_dollar'])} | {_fmt(n['quality_per_cpu_second'])} | {_fmt(n['adaptation_overhead_cost'])} | {_fmt(n['adaptation_overhead_time'])} |")
    L.append(f"\nPareto front (min total_cost, max quality_mean): {', '.join(r['pareto_front_cost'])}")
    L.append(f"Pareto front (min cpu_time_s, max quality_mean): {', '.join(r['pareto_front_cpu'])}\n")
    L.append("## Quality per step\n")
    steps = max((len(v) for v in r["per_step"].values()), default=0)
    L.append("| agent | " + " | ".join(f"t={r['per_step'][agents[0]][i]['t']:.0f}" for i in range(steps)) + " |")
    L.append("|---|" + "---|" * steps)
    for a in agents:
        L.append(f"| {a} | " + " | ".join(f"{_fmt(s['quality'])} ({s['name'][:14] if s['name'] else ''})" for s in r["per_step"][a]) + " |")
    L.append("\n## Environment transitions\n")
    if r["env_transitions"]:
        seen = set()
        for ev in r["env_transitions"]:
            key = (ev["t"], json.dumps(ev["event"], sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            L.append(f"- t={ev['t']:.0f}: {ev['event']['type']} {ev['event'].get('params', {})} → memory={ev['after']['memory_mb']}MB cpu={ev['after']['cpu']} network={ev['after']['network']} latency={ev['after']['latency_ms']}ms priority={ev['after']['priority']} caps={len(ev['after']['available_capabilities'])}")
    else:
        L.append("- none")
    L.append("\n## Adaptation decisions\n")
    if r["adaptation_decisions"]:
        L.append("| agent | step | outcome | expected_quality | expected_improvement | search_cost | validation_cost | budget_remaining | deadline_remaining_s | rationale |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for d in r["adaptation_decisions"]:
            L.append(f"| {d['agent']} | {d['step']} | {d['outcome']} | {_fmt(d['expected_quality'])} | {_fmt(d['expected_improvement'])} | {_fmt(d['search_cost'])} | {_fmt(d['validation_cost'])} | {_fmt(d['resource_budget_remaining'])} | {_fmt(d['deadline_remaining_s'])} | {d['rationale']} |")
    else:
        L.append("- none recorded")
    if r["transfer"]:
        L.append("\n## Transfer measurements (memory vs cold)\n")
        for a, t in r["transfer"].items():
            L.append(f"- {a}: " + ", ".join(f"{k}={_fmt(v)}" for k, v in t.items()))
    L.append("\n## Failed or violating executions\n")
    if r["failed_runs"]:
        L.append("| agent | step | purpose | arch | exit | violation | quality | stderr |")
        L.append("|---|---|---|---|---|---|---|---|")
        for f in r["failed_runs"]:
            L.append(f"| {f['agent']} | {f['step']} | {f['purpose']} | {f['arch']} | {f['exit_code']} | {f['violation']} | {_fmt(f['quality'])} | {f['stderr'][:80].replace('|', '/')} |")
    else:
        L.append("- none")
    L.append("\nAll executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.")
    return "\n".join(L) + "\n"


def write_experiment_report(db: Database, experiment_id: str, results_dir: Optional[Path] = None) -> Path:
    r = experiment_report(db, experiment_id)
    results_dir = results_dir or (RESULTS / experiment_id)
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "report.json").write_text(json.dumps(r, indent=2, default=str))
    (results_dir / "report.md").write_text(render_markdown(r))
    return results_dir / "report.md"


# ------------------------------------------------------------------ suite / cross-experiment

def suite_report(db: Database, names: List[str]) -> Dict[str, Any]:
    exps = [e for e in db.experiments() if e.get("status") == "finished" and (e["name"] in names or any(t in names for t in e["manifest"].get("tags", [])))]
    by_name: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for e in exps:
        by_name[e["name"]].append(e)
    out: Dict[str, Any] = {"experiments": {}, "transfer": {}}
    for name, runs in by_name.items():
        agents = sorted({a for e in runs for a in e.get("summary", {})})
        table: Dict[str, Dict[str, Any]] = {}
        for a in agents:
            table[a] = {"n_runs": sum(1 for e in runs if a in e.get("summary", {}))}
            for m in AGG_METRICS:
                vals = [e["summary"][a].get(m) for e in runs if a in e.get("summary", {})]
                mean, lo, hi = bootstrap_ci(vals)
                table[a][m] = {"mean": mean, "ci95": [lo, hi], "n": len([v for v in vals if v is not None])}
            reached = [e["summary"][a].get("time_to_target_logical_s") is not None for e in runs if a in e.get("summary", {})]
            table[a]["target_reached_fraction"] = sum(reached) / len(reached) if reached else None
        points = {a: (table[a]["total_cost"]["mean"], table[a]["quality_mean"]["mean"]) for a in agents}
        out["experiments"][name] = {"n_runs": len(runs), "seeds": [e["seed"] for e in runs], "ids": [e["experiment_id"] for e in runs],
                                    "domain": runs[0]["manifest"]["task"]["domain"], "agents": table, "pareto_front_cost": pareto_front(points)}
        # transfer: paired per seed
        for a in agents:
            if a.endswith("_memory") and a[:-7] + "_cold" in agents:
                deltas_q, deltas_t, deltas_e, deltas_c = [], [], [], []
                for e in runs:
                    s = e.get("summary", {})
                    if a in s and a[:-7] + "_cold" in s:
                        m, c = s[a], s[a[:-7] + "_cold"]
                        deltas_q.append(m["quality_mean"] - c["quality_mean"])
                        deltas_e.append(m["architecture_evaluations"] - c["architecture_evaluations"])
                        deltas_c.append(m["total_cost"] - c["total_cost"])
                        if m["time_to_target_logical_s"] is not None and c["time_to_target_logical_s"] is not None:
                            deltas_t.append(m["time_to_target_logical_s"] - c["time_to_target_logical_s"])
                out["transfer"][f"{name}:{a}"] = {"delta_quality_mean": bootstrap_ci(deltas_q), "delta_time_to_target_logical_s": bootstrap_ci(deltas_t),
                                                  "delta_architecture_evaluations": bootstrap_ci(deltas_e), "delta_total_cost": bootstrap_ci(deltas_c),
                                                  "n_pairs": len(deltas_q), "n_pairs_with_target": len(deltas_t)}
    return out


def render_suite_markdown(s: Dict[str, Any], title: str) -> str:
    L = [f"# Suite report: {title}\n", "Means with bootstrap 95% CIs over seeds. A CI equal to the mean means n=1 (no interval available).\n"]
    for name, ex in s["experiments"].items():
        L.append(f"## {name} (domain={ex['domain']}, runs={ex['n_runs']}, seeds={ex['seeds']})\n")
        agents = list(ex["agents"])
        L.append("| metric | " + " | ".join(agents) + " |")
        L.append("|---|" + "---|" * len(agents))
        for m in AGG_METRICS:
            cells = []
            for a in agents:
                v = ex["agents"][a][m]
                cells.append("—" if v["n"] == 0 else f"{v['mean']:.3g} [{v['ci95'][0]:.3g}, {v['ci95'][1]:.3g}]")
            L.append(f"| {m} | " + " | ".join(cells) + " |")
        L.append("| target_reached_fraction | " + " | ".join(_fmt(ex["agents"][a]["target_reached_fraction"]) for a in agents) + " |")
        L.append(f"\nPareto front (cost vs quality, means): {', '.join(ex['pareto_front_cost'])}\n")
    if s["transfer"]:
        L.append("## Transfer measurements (memory − cold, paired by seed)\n")
        L.append("| experiment:agent | Δ quality_mean [CI] | Δ time_to_target_s [CI] | Δ arch evaluations [CI] | Δ total_cost [CI] | pairs |")
        L.append("|---|---|---|---|---|---|")
        for k, t in s["transfer"].items():
            def f(x):
                return "—" if x[0] != x[0] else f"{x[0]:.3g} [{x[1]:.3g}, {x[2]:.3g}]"
            L.append(f"| {k} | {f(t['delta_quality_mean'])} | {f(t['delta_time_to_target_logical_s'])} | {f(t['delta_architecture_evaluations'])} | {f(t['delta_total_cost'])} | {t['n_pairs']} ({t['n_pairs_with_target']} with target) |")
        L.append("\nA positive Δ quality or negative Δ time/evaluations is consistent with transfer benefit; whether it is meaningful depends on the CI and on the number of seeds.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate AGM laboratory reports from SQLite.")
    ap.add_argument("ids", nargs="*", help="experiment ids")
    ap.add_argument("--suite", nargs="+", help="experiment names or tags to aggregate")
    ap.add_argument("--out", help="output path for the suite report (markdown)")
    args = ap.parse_args(argv)
    db = Database()
    for eid in args.ids:
        print(write_experiment_report(db, eid))
    if args.suite:
        s = suite_report(db, args.suite)
        md = render_suite_markdown(s, " ".join(args.suite))
        out = Path(args.out) if args.out else RESULTS / f"suite_{'_'.join(args.suite)}.md"
        out.write_text(md)
        out.with_suffix(".json").write_text(json.dumps(s, indent=2, default=str))
        print(out)


if __name__ == "__main__":
    main()
