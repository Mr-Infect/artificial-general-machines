"""Per-experiment results bundle (v0.2, spec section 33).

results/<experiment_id>/
    raw_events.jsonl    written live by the runner
    metrics.json        per-agent aggregates + per-step metrics
    architectures.json  every architecture generated/executed, with alias, lineage, distances, novelty levels
    principles.json     principles retrieved/created/tested during the experiment (from events)
    transfer.json       transfer attempts/completions and memory-vs-cold deltas
    pareto.json         multi-objective classification (dominated / non-dominated) and resource-normalized measures
    failures.json       every failed, refused, violating or rejected item
    report.md           report with the mandated sections; the conclusion is generated from measurements
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from architecture.distance import architecture_distance, novelty_levels
from architecture.ir import ArchitectureIR
from core.db import Database
from core.registry import CapabilityRegistry
from experiments.report import experiment_report, pareto_front
from observability.events import Event, fold_state

OBJECTIVES = {"quality_mean": True, "latency_ms": False, "max_memory_mb": False, "adaptation_cost": False, "architecture_evaluations": False, "failure_rate": False}


def pareto_classification(r: Dict[str, Any]) -> Dict[str, Any]:
    pts = {}
    for a, s in r["agents"].items():
        steps = r["per_step"].get(a, [])
        pts[a] = {"quality_mean": s["quality_mean"], "latency_ms": sum(x["runtime_s"] for x in steps) / max(1, len(steps)) * 1000,
                  "max_memory_mb": s["max_memory_mb"], "adaptation_cost": s["adaptation_cost"], "architecture_evaluations": s["architecture_evaluations"],
                  "failure_rate": s["failures"] / max(1, len(steps))}
    def dom(p, q):
        return all((p[k] >= q[k]) if mx else (p[k] <= q[k]) for k, mx in OBJECTIVES.items()) and any((p[k] > q[k]) if mx else (p[k] < q[k]) for k, mx in OBJECTIVES.items())
    cls = {a: ("dominated" if any(dom(pts[b], pts[a]) for b in pts if b != a) else "non-dominated") for a in pts}
    norm = {a: {"quality_per_adaptation_cost": (pts[a]["quality_mean"] / pts[a]["adaptation_cost"]) if pts[a]["adaptation_cost"] > 0 else None,
                "quality_per_architecture_evaluation": (pts[a]["quality_mean"] / pts[a]["architecture_evaluations"]) if pts[a]["architecture_evaluations"] > 0 else None,
                "raw_quality": pts[a]["quality_mean"]} for a in pts}
    return {"objectives": OBJECTIVES, "points": pts, "classification": cls, "frontier": [a for a, c in cls.items() if c == "non-dominated"],
            "pareto_cost_quality": pareto_front({a: (r["agents"][a]["total_cost"], r["agents"][a]["quality_mean"]) for a in r["agents"]}), "resource_normalized": norm}


def write_bundle(db: Database, experiment_id: str, results_dir: Path, registry: CapabilityRegistry) -> Dict[str, Any]:
    r = experiment_report(db, experiment_id)
    exp = db.experiment(experiment_id)
    results_dir.mkdir(parents=True, exist_ok=True)
    events_path = results_dir / "raw_events.jsonl"
    events: List[Event] = []
    if events_path.exists():
        for line in events_path.read_text().splitlines():
            if line.strip():
                events.append(Event.model_validate_json(line))
    by_agent: Dict[str, List[Event]] = {}
    for e in events:
        by_agent.setdefault(e.agent, []).append(e)
    states = {a: fold_state(evs) for a, evs in by_agent.items()}

    metrics = {"experiment_id": experiment_id, "name": exp["name"], "seed": exp["seed"], "target_quality": r["target_quality"],
               "agents": {a: {k: v for k, v in s.items() if k not in ("decisions", "agent_extra", "architectures")} for a, s in r["agents"].items()},
               "agent_extra": {a: s.get("agent_extra", {}) for a, s in r["agents"].items()}, "per_step": r["per_step"]}
    (results_dir / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str))

    archs: Dict[str, Any] = {}
    for a, st in states.items():
        executed = [x["hash"] for x in st["executions"] if x["purpose"] == "task"]
        initial = executed[0] if executed else None
        for h, info in st["architectures"].items():
            row = db.architecture(h)
            if not row:
                continue
            ir = ArchitectureIR.from_dict(row)
            entry = {"agent": a, "alias": info["alias"], "hash": h, "name": ir.name, "parent_hash": ir.parent_hash, "lineage": ir.lineage, "source": info.get("source"),
                     "created_step": info.get("created_step"), "reason": info.get("reason"), "performance": info.get("performance"), "ir": row,
                     "executed_as_task": h in executed, "components": ir.architecture.perception.components, "reasoning": ir.architecture.reasoning.type,
                     "memory": ir.architecture.memory.type, "verification": ir.architecture.verification.type}
            if initial and initial != h and db.architecture(initial):
                iir = ArchitectureIR.from_dict(db.architecture(initial))
                entry["distance_to_initial"] = architecture_distance(ir, iir, registry)
                entry["novelty_vs_initial"] = novelty_levels(ir, [iir], registry)
            archs[f"{a}:{h}"] = entry
        seq, prev = [], None
        for h in executed:
            row = db.architecture(h)
            if not row:
                continue
            ir = ArchitectureIR.from_dict(row)
            d_prev = architecture_distance(ir, ArchitectureIR.from_dict(db.architecture(prev)), registry)["structural_distance"] if prev else 0.0
            seq.append({"hash": h, "alias": st["architectures"].get(h, {}).get("alias"), "distance_to_previous": d_prev})
            prev = h
        archs[f"{a}:__sequence__"] = seq
    (results_dir / "architectures.json").write_text(json.dumps(archs, indent=1, default=str))

    principles = {a: st["principles"] for a, st in states.items()}
    principles["_tests"] = {a: s.get("agent_extra", {}).get("principles_tested") for a, s in r["agents"].items()}
    (results_dir / "principles.json").write_text(json.dumps(principles, indent=1, default=str))
    transfer = {"pairs": r["transfer"], "attempts": {a: [e.payload for e in evs if e.event_type.value == "TRANSFER_ATTEMPTED"] for a, evs in by_agent.items()},
                "completions": {a: [e.payload for e in evs if e.event_type.value == "TRANSFER_COMPLETED"] for a, evs in by_agent.items()},
                "principle_reuse": {a: s.get("agent_extra", {}).get("principle_reuse") for a, s in r["agents"].items()}}
    (results_dir / "transfer.json").write_text(json.dumps(transfer, indent=1, default=str))
    pareto = pareto_classification(r)
    (results_dir / "pareto.json").write_text(json.dumps(pareto, indent=1, default=str))
    failures = {"failed_executions": r["failed_runs"], "event_failures": {a: st["failures"] for a, st in states.items()},
                "rejected_architectures": {a: [{"seq": e.seq, "step": e.step, "architecture": e.selected_architecture, "reason": e.reason} for e in evs if e.event_type.value == "ARCHITECTURE_REJECTED"] for a, evs in by_agent.items()},
                "contradicted_principles": {a: st["principles"]["contradicted"] for a, st in states.items()},
                "decision_errors": {a: [{"step": d["step"], "outcome": d["outcome"], "decision_error": d.get("decision_error"), "cost_estimate_error": d.get("cost_estimate_error")}
                                        for d in s.get("agent_extra", {}).get("decisions", [])] for a, s in r["agents"].items()}}
    (results_dir / "failures.json").write_text(json.dumps(failures, indent=1, default=str))
    (results_dir / "report.md").write_text(render_report(r, exp, pareto, transfer, failures, states, archs))
    return {"metrics": metrics, "pareto": pareto, "transfer": transfer, "failures": failures}


def _f(v):
    return "—" if v is None else (f"{v:.4g}" if isinstance(v, float) else str(v))


def render_report(r, exp, pareto, transfer, failures, states, archs) -> str:
    m = exp["manifest"]
    agents = list(r["agents"])
    target = r["target_quality"]
    L = [f"# Experiment report: {r['name']}\n", "## Hypothesis\n",
         m.get("description") or "Compare the listed agents on identical data, constraints and scoring; measure quality, cost, adaptation and transfer.",
         "\n## Experimental conditions\n",
         f"- id `{r['experiment_id']}`, seed {r['seed']}, executor {r['executor']}, git `{r['git_commit'][:12]}`, manifest `{r['manifest_hash']}`",
         f"- task {m['task']}\n- environment {m['environment']}\n- events {m.get('events', [])}\n- objective quality ≥ {target}; budget {m['budget']}",
         "\n## Baselines\n"]
    for a in agents:
        L.append(f"- {a}: {json.dumps({k: v for k, v in next((x for x in m['agents'] if x['name'] == a), {}).items() if k != 'name'})}")
    L.append("\n## Results\n")
    keys = ["quality_mean", "quality_min", "quality_final", "time_to_target_logical_s", "architecture_evaluations", "adaptation_cost", "execution_cost", "total_cost",
            "cpu_time_s", "max_memory_mb", "constraint_violations", "failures", "novelty_mean", "distinct_architectures"]
    L.append("| metric | " + " | ".join(agents) + " |"); L.append("|---|" + "---|" * len(agents))
    for k in keys:
        L.append(f"| {k} | " + " | ".join(_f(r["agents"][a].get(k)) for a in agents) + " |")
    L.append("\n## Statistical analysis\n\nSingle seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.")
    L.append("\n## Architecture changes\n")
    for a in agents:
        seq = archs.get(f"{a}:__sequence__", [])
        L.append(f"- {a}: " + " → ".join(f"{s['alias'] or s['hash'][:8]} (Δprev {s['distance_to_previous']:.2f})" for s in seq))
    L.append("\n## Transfer results\n")
    for a, t in transfer["pairs"].items():
        L.append(f"- {a}: " + ", ".join(f"{k}={_f(v)}" for k, v in t.items()))
    att = sum(len(v) for v in transfer["attempts"].values()); comp = sum(len(v) for v in transfer["completions"].values())
    L.append(f"- cross-domain principle instantiations attempted: {att}; completed with a recorded test: {comp}; principle reuse per agent: {transfer['principle_reuse']}")
    L.append("\n## Adaptation economics\n")
    for a, st in states.items():
        ds = st["decisions"]
        if ds:
            outs: Dict[str, int] = {}
            for d in ds:
                outs[d.get("outcome")] = outs.get(d.get("outcome"), 0) + 1
            errs = [d.get("decision_error") for d in ds if d.get("decision_error") is not None]
            L.append(f"- {a}: decisions {outs}; mean decision error {_f(sum(errs) / len(errs)) if errs else '—'}")
    L.append("\n## Failures\n")
    L.append(f"- failed/refused/violating executions: {len(failures['failed_executions'])}")
    for f in failures["failed_executions"][:20]:
        L.append(f"  - {f['agent']} step {f['step']} {f['purpose']} {f['arch']}: {f['violation'] or f['exit_code']}")
    L.append(f"- rejected architectures: { {a: len(v) for a, v in failures['rejected_architectures'].items()} }")
    L.append(f"- contradicted principles: { {a: len(v) for a, v in failures['contradicted_principles'].items()} }")
    L.append("\n## Counterexamples\n")
    worst = [(a, min(s["quality"] for s in r["per_step"][a])) for a in agents if r["per_step"].get(a)]
    L.append("- lowest per-step quality per agent: " + ", ".join(f"{a} {q:.3f}" for a, q in worst))
    L.append("\n## Interpretation\n")
    L.append(f"- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = {pareto['frontier']}; dominated = {[a for a, c in pareto['classification'].items() if c == 'dominated']}")
    L.append(f"- resource-normalized (quality per adaptation cost; distinct from raw quality): { {a: _f(v['quality_per_adaptation_cost']) for a, v in pareto['resource_normalized'].items()} }")
    L.append("\n## Limitations\n\n- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.")
    L.append("\n## Conclusion\n")
    met = [a for a in agents if r["agents"][a]["time_to_target_logical_s"] is not None]
    L.append(f"- Agents that reached the target quality {target} at some step: {met or 'none'}. Agents with zero failures: {[a for a in agents if r['agents'][a]['failures'] == 0]}.")
    L.append("- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.")
    return "\n".join(L) + "\n"
