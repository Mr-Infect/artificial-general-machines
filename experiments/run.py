"""Experiment runner (Sections 12-15).

    python -m experiments.run experiments/manifests/example.yaml
    python -m experiments.run --replay <experiment_id>

One manifest -> one or more experiments (``repeats`` seeds). For each agent
the runner walks the stream in steps; before every step it advances the
dynamic environment, builds the telemetry snapshot, asks the agent for an
architecture, validates it against the *current* environment, compiles it,
executes it in the sandbox, scores it, and records everything.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from architecture.ir import ArchitectureIR, novelty
from architecture.validate import validate_against_environment, validate_against_registry
from baselines import build_agent
from baselines.base import AgentContext, CandidateResult
from compiler import compile_ir, CompileError
from core.db import (AdaptationDecisionRow, ArchitectureRow, Database, EvaluationRow, ExecutionRow, ExperimentRow, utcnow)
from core.ids import new_id
from core.models import AdaptationDecision, Evaluation, Execution, SandboxResult
from core.registry import CapabilityRegistry
from environments.profile import DynamicEnvironment, EnvironmentProfile
from environments.scoring import evaluate_batch as _eb_v1, score
from environments.synthetic import batch_payload as _bp_v1, load_or_generate
from environments import regimes as R
from experiments.manifest import (ExperimentSpec, expand_suite, load_manifest, manifest_hash, parse_experiment, parse_suite)
from memory.structural import StructuralMemory
from memory.principles import PrincipleMemory
from observability.events import EventLog, EventType
from runtime.executor import get_executor
from telemetry.telemetry import Telemetry

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def batch_payload(ds, start, end):
    return R.batch_payload(ds, start, end) if "base_domain" in ds else _bp_v1(ds, start, end)


def evaluate_batch(ds, start, end, artifact):
    return R.evaluate_batch(ds, start, end, artifact) if "base_domain" in ds else _eb_v1(ds, start, end, artifact)


def git_commit() -> Dict[str, Any]:
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, timeout=5)
        if rev.returncode != 0:
            return {"commit": "no-git", "dirty": True}
        return {"commit": rev.stdout.strip(), "dirty": bool(dirty.stdout.strip())}
    except Exception:
        return {"commit": "unknown", "dirty": True}


class AgentRun:
    """Per-agent mutable accounting during one experiment."""

    def __init__(self, name: str):
        self.name = name
        self.cost_execution = 0.0
        self.cost_adaptation = 0.0
        self.wall_used_s = 0.0
        self.search_time_s = 0.0
        self.arch_evaluations = 0
        self.model_calls = 0
        self.tokens = 0
        self.cpu_time_s = 0.0
        self.violations: List[str] = []
        self.failures = 0
        self.qualities: List[float] = []
        self.time_to_target_logical: Optional[float] = None
        self.time_to_target_wall: Optional[float] = None
        self.architectures_used: List[ArchitectureIR] = []
        self.novelties: List[float] = []
        self.max_memory_mb = 0.0
        self.candidate_log: List[Dict[str, Any]] = []

    @property
    def total_cost(self) -> float:
        return self.cost_execution + self.cost_adaptation


class ExperimentRunner:
    def __init__(self, spec: ExperimentSpec, db: Optional[Database] = None, executor_name: Optional[str] = None,
                 results_root: Path = RESULTS, quiet: bool = False):
        self.spec = spec
        self.db = db or Database()
        self.registry = CapabilityRegistry.load()
        self.executor = get_executor(executor_name or spec.executor)
        self.results_root = results_root
        self.quiet = quiet

    def log(self, msg: str) -> None:
        if not self.quiet:
            print(msg, flush=True)

    # ------------------------------------------------------------------
    def run(self, seed: Optional[int] = None) -> str:
        spec = self.spec
        seed = spec.seed if seed is None else seed
        experiment_id = new_id("exp")
        manifest = spec.model_dump(mode="json")
        manifest["seed"] = seed
        mhash = manifest_hash(manifest)
        results_dir = self.results_root / experiment_id
        results_dir.mkdir(parents=True, exist_ok=True)
        git = git_commit()
        image_id = getattr(self.executor, "ensure_image", lambda: None)()
        started = utcnow()
        self.log(f"[{experiment_id}] {spec.name} seed={seed} executor={self.executor.name}")

        # Dataset and split (identical for every agent).
        task = spec.task.model_dump()
        regime_info: Optional[Dict[str, Any]] = None
        if spec.regime is not None:
            schedule = spec.regime.schedule or R.sample_schedule(R.TRAINING_SET if spec.regime.set == "training" else R.HELDOUT_SET, spec.schedule.steps, seed)
            ds = self._load_regime_dataset(task["domain"], task["dataset_size"], schedule, spec.schedule.steps, seed, spec.schedule.validation_fraction)
            n_val, batch, steps = ds["validation_records"], ds["batch_size"], spec.schedule.steps
            n_stream = len(ds["records"]) - n_val
            regime_info = {"set": spec.regime.set, "schedule": schedule, "regime_by_step": [R.regime_at(schedule, st) for st in range(steps)],
                           "transitions": [x["start_step"] for x in schedule[1:]], "params": {r: R.REGIMES[r] for r in {x["regime"] for x in schedule}}}
        else:
            ds = load_or_generate(task["domain"], task["dataset_size"], task["noise"], task["anomaly_rate"], seed)
            n_val = int(len(ds["records"]) * spec.schedule.validation_fraction)
            n_stream = len(ds["records"]) - n_val
            steps = spec.schedule.steps
            batch = max(10, n_stream // steps)
        self._regime_info = regime_info

        target_info = self._objective_target(spec, ds, n_val) if regime_info is None else self._regime_targets(spec, ds, n_val, batch, regime_info)
        provenance = {
            "experiment_id": experiment_id, "name": spec.name, "manifest": manifest, "manifest_hash": mhash, "objective": target_info, "regime": regime_info,
            "git": git, "seed": seed, "dataset_id": ds["dataset_id"], "validation_records": n_val,
            "stream_records": n_stream, "batch_size": batch, "executor": self.executor.name,
            "sandbox_image": image_id, "registry_capabilities": self.registry.all_keys(),
            "python": sys.version.split()[0], "started_at": started, "host": Telemetry.host_sample(),
            "model_identifier": "simulated-registry-models", "model_configuration": {c.name: c.model_dump() for c in self.registry.all() if c.kind == "model"},
        }
        (results_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        self.db.add(ExperimentRow(experiment_id=experiment_id, name=spec.name, manifest_hash=mhash, git_commit=git["commit"],
                                  seed=seed, status="running", executor=self.executor.name, started_at=started,
                                  json=json.dumps({"experiment_id": experiment_id, "name": spec.name, "manifest": manifest,
                                                   "manifest_hash": mhash, "git_commit": git["commit"], "seed": seed,
                                                   "started_at": started, "status": "running", "executor": self.executor.name,
                                                   "objective": {k: v for k, v in target_info.items() if k != "space_results"}, "regime": regime_info})))
        if regime_info is not None:
            (results_dir / "hidden_truth.json").write_text(json.dumps({"regime": regime_info, "objective": {k: v for k, v in target_info.items() if k != "space_results"}}, indent=1))

        summaries: Dict[str, Any] = {}
        for agent_spec in spec.agents:
            summaries[agent_spec.name] = self._run_agent(experiment_id, seed, agent_spec, ds, n_val, batch, results_dir, provenance, target_info["target"],
                                                         target_by_step=target_info.get("target_by_step"))

        finished = utcnow()
        provenance["finished_at"] = finished
        provenance["agents"] = summaries
        (results_dir / "provenance.json").write_text(json.dumps(provenance, indent=2, default=str))
        row_json = json.loads(self.db.experiment(experiment_id) and json.dumps(self.db.experiment(experiment_id)) or "{}")
        row_json.update({"finished_at": finished, "status": "finished", "summary": summaries, "provenance_path": str(results_dir / "provenance.json")})
        self.db.add(ExperimentRow(experiment_id=experiment_id, name=spec.name, manifest_hash=mhash, git_commit=git["commit"],
                                  seed=seed, status="finished", executor=self.executor.name, started_at=started,
                                  finished_at=finished, json=json.dumps(row_json, default=str)))
        from experiments.report import write_experiment_report
        write_experiment_report(self.db, experiment_id, results_dir)
        from experiments.bundle import write_bundle
        write_bundle(self.db, experiment_id, results_dir, self.registry)
        self.log(f"[{experiment_id}] finished -> {results_dir}")
        return experiment_id

    # ------------------------------------------------------------------
    def _load_regime_dataset(self, domain, size, schedule, steps, seed, vf):
        R.S.DATASET_DIR.mkdir(parents=True, exist_ok=True)
        structure = {"network_rules": "rules", "scientific_drift": "drift", "planning_stable": "stable"}.get(domain, "native")
        key = R.dataset_key(domain, size, schedule, seed, structure)
        path = R.S.DATASET_DIR / f"{domain}_{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        ds = R.generate(domain, size, schedule, steps, seed, vf)
        path.write_text(json.dumps(ds))
        return ds

    def _regime_targets(self, spec: ExperimentSpec, ds, n_val: int, batch: int, regime_info: Dict[str, Any]) -> Dict[str, Any]:
        """Lab oracle per regime: a deterministic sample of the wide space evaluated on the first batch of each
        regime under that regime's limits and capability availability (validity enforced). Target per regime =
        top-decile validation quality. Hidden from agents; recorded in provenance/hidden_truth.json."""
        from baselines.agm_v2 import enumerate_wide_space
        from runtime.executor import ProcessExecutor
        from architecture.validate import validate_against_environment
        task = spec.task.model_dump()
        caps_all = self.registry.keys_for_domain(task["domain"])
        px = ProcessExecutor()
        targets, space_results = {}, {}
        steps = spec.schedule.steps
        for x in regime_info["schedule"]:
            rname, st = x["regime"], x["start_step"]
            reg = R.REGIMES[rname]
            caps = [k for k in caps_all if reg["large_model"] or k != "model:large_reasoner"]
            cap_model = {kind: [k.split(":", 1)[1] for k in caps if k.startswith(kind + ":")] for kind in ("component", "model", "reasoning", "memory", "verification", "tool")}
            space = enumerate_wide_space(cap_model, big_ok=reg["large_model"])
            rng = random.Random(f"oracle:{rname}:{ds['dataset_id']}")
            singles = [ir for ir in space if len(ir.architecture.perception.components) == 1]
            rest = [ir for ir in space if len(ir.architecture.perception.components) > 1]
            rng.shuffle(rest)
            sample = singles + rest[: max(0, spec.regime.oracle_points - len(singles))]
            env = {"memory_mb": reg["memory_mb"], "cpu": reg["cpu"], "network": False, "privacy": "local_only", "available_capabilities": caps}
            limits = {"cpu": reg["cpu"], "memory_mb": reg["memory_mb"], "verification_cost_factor": reg["vcf"], "timeout_s": 30}
            start, end = n_val + st * batch, n_val + (st + 1) * batch if st < steps - 1 else len(ds["records"])
            payload = batch_payload(ds, start, end)
            res = []
            for ir in sample:
                try:
                    c = compile_ir(ir, self.registry, limits)
                except CompileError:
                    continue
                if validate_against_environment(ir, env, self.registry, c.estimates["memory_mb"]):
                    res.append({"hash": ir.hash(), "name": ir.name, "quality": None, "invalid": True})
                    continue
                sb = px.run({"spec": c.model_dump(), "data": payload, "state": {}}, limits)
                ok = sb.artifact is not None and sb.artifact.get("ok")
                q = evaluate_batch(ds, start, end, sb.artifact)["quality"] if ok else 0.0
                res.append({"hash": ir.hash(), "name": ir.name, "quality": q, "invalid": False})
            qs = sorted((r["quality"] for r in res if r["quality"] is not None), reverse=True)
            k = max(1, int(round(0.1 * len(qs)))) if qs else 1
            targets[rname] = round(qs[k - 1], 4) if qs else 0.0
            space_results[rname] = {"n_sampled": len(sample), "n_valid": len(qs), "best": qs[0] if qs else None, "target": targets[rname], "results": res}
            self.log(f"  regime {rname} (from step {st}): {len(qs)} valid of {len(sample)} sampled; best {qs[0] if qs else 0:.3f}; target {targets[rname]:.3f}")
        target_by_step = [targets[r] for r in regime_info["regime_by_step"]]
        return {"mode": "regime_top_decile", "target": target_by_step[0], "target_by_regime": targets, "target_by_step": target_by_step, "space_results": space_results}

    def _objective_target(self, spec: ExperimentSpec, ds, n_val: int) -> Dict[str, Any]:
        """Lab-side oracle for relative targets: evaluate the enumerated wide space on the validation
        slice with the process executor (deterministic; not an agent) and take relative_to_best × best."""
        info = {"mode": "fixed", "target": spec.objective.quality_threshold, "floor": spec.objective.quality_threshold}
        if spec.objective.relative_to_best is None and spec.objective.top_fraction is None:
            return info
        from baselines.agm_v2 import enumerate_wide_space
        from runtime.executor import ProcessExecutor
        task = spec.task.model_dump()
        caps = self.registry.keys_for_domain(task["domain"])
        cap_model = {kind: [k.split(":", 1)[1] for k in caps if k.startswith(kind + ":")] for kind in ("component", "model", "reasoning", "memory", "verification", "tool")}
        space = enumerate_wide_space(cap_model, big_ok=True)
        payload = batch_payload(ds, 0, n_val)
        best, best_name, results = 0.0, None, []
        px = ProcessExecutor()
        for ir in space:
            try:
                c = compile_ir(ir, self.registry, {"timeout_s": 30})
            except CompileError:
                continue
            sb = px.run({"spec": c.model_dump(), "data": payload, "state": {}}, {"timeout_s": 30})
            ok = sb.artifact is not None and sb.artifact.get("ok")
            q = evaluate_batch(ds, 0, n_val, sb.artifact)["quality"] if ok else 0.0
            results.append({"hash": ir.hash(), "name": ir.name, "quality": q})
            if q > best:
                best, best_name = q, ir.name
        if spec.objective.top_fraction is not None:
            qs = sorted((r["quality"] for r in results), reverse=True)
            k = max(1, int(round(spec.objective.top_fraction * len(qs))))
            target = max(spec.objective.quality_threshold, qs[k - 1])
            mode = "top_fraction"
        else:
            target = max(spec.objective.quality_threshold, spec.objective.relative_to_best * best)
            mode = "relative_to_best"
        info.update({"mode": mode, "relative_to_best": spec.objective.relative_to_best, "top_fraction": spec.objective.top_fraction,
                     "best_validation_quality": best, "best_architecture": best_name, "n_space": len(results), "target": round(target, 4), "space_results": results,
                     "quantile_of_target": sum(1 for r in results if r["quality"] >= target) / max(1, len(results))})
        self.log(f"  objective ({mode}): best validation quality {best:.3f} ({best_name}); target = {target:.3f} "
                 f"({info['quantile_of_target']:.0%} of {len(results)} space points reach it)")
        return info

    def _run_agent(self, experiment_id: str, seed: int, agent_spec, ds, n_val: int, batch: int, results_dir: Path,
                   provenance: Dict[str, Any], target: float, target_by_step: Optional[List[float]] = None) -> Dict[str, Any]:
        spec = self.spec
        regime_info = getattr(self, "_regime_info", None)
        cfg = agent_spec.model_dump()
        agent = build_agent(agent_spec.name, cfg, self.registry)
        rng = random.Random(f"{seed}:{agent_spec.name}")
        telemetry = Telemetry(self.db, experiment_id, agent_spec.name, results_dir)
        run = AgentRun(agent_spec.name)
        task = spec.task.model_dump()

        # structural memory (only agents that declare it)
        memory = None
        mem_cfg = cfg.get("memory")
        if mem_cfg:
            db_path = mem_cfg.get("db") or spec.memory_db
            memory = StructuralMemory.open(str(ROOT / db_path) if db_path and not Path(db_path).is_absolute() else db_path,
                                           readable=bool(mem_cfg.get("read", True)), writable=bool(mem_cfg.get("write", True)))
            if hasattr(agent, "initial_memory_archs") and memory.readable:
                agent.initial_memory_archs = [ArchitectureIR.from_dict(p.architecture) for p in memory.all()]

        principle_memory = None
        pm_cfg = cfg.get("principle_memory")
        if pm_cfg:
            db_path = pm_cfg.get("db") or spec.memory_db
            pdb = Database(ROOT / db_path if db_path and not Path(db_path).is_absolute() else Path(db_path)) if db_path else self.db
            principle_memory = PrincipleMemory(pdb, readable=bool(pm_cfg.get("read", True)), writable=bool(pm_cfg.get("write", True)))
        elog = EventLog(self.db, experiment_id, agent_spec.name, results_dir, domain=task["domain"])
        env_caps = spec.environment.available_capabilities
        avail = self.registry.keys_for_domain(task["domain"]) if env_caps == "all" else list(env_caps)
        prof_kwargs = dict(cpu=spec.environment.cpu, memory_mb=spec.environment.memory_mb, latency_ms=spec.environment.latency_ms, network=spec.environment.network,
                           privacy=spec.environment.privacy, energy_budget=spec.environment.energy_budget, deadline_s=spec.budget.max_seconds,
                           cost_budget=spec.budget.max_cost, priority=task["priority"], verification_cost_factor=spec.environment.verification_cost_factor)
        events = list(spec.events)
        if regime_info is not None:
            ov = R.initial_profile_overrides(regime_info["schedule"])
            prof_kwargs.update(memory_mb=ov["memory_mb"], cpu=ov["cpu"], verification_cost_factor=ov["verification_cost_factor"], failure_penalty=ov["failure_penalty"])
            if not ov["large_model"]:
                avail = [k for k in avail if k != "model:large_reasoner"]
            from environments.profile import EnvironmentEvent
            events += [EnvironmentEvent.model_validate(e) for e in R.env_events_for(regime_info["schedule"], spec.schedule.step_seconds, avail)]
        profile = EnvironmentProfile(available_capabilities=avail, **prof_kwargs)
        def _on_transition(t, ev, b, a):
            telemetry.record_env_transition(t, ev.model_dump(mode="json"), b.observable(), a.observable())
            elog.set_context(step_time[1], t, a.observable())
            elog.emit(EventType.CONSTRAINT_CHANGED, reason=f"{ev.type.value} {ev.params}", constraints=a.observable(),
                      payload={"event": ev.model_dump(mode="json"), "before": b.observable(), "after": a.observable()})
        env = DynamicEnvironment(profile, events, on_transition=_on_transition)
        elog.set_context(0, 0.0, profile.observable())
        elog.emit(EventType.RUN_STARTED, reason=f"run {agent_spec.name} ({agent.kind}) on {task['domain']}", constraints=profile.observable(),
                  payload={"agent_type": agent.kind, "agent_config": cfg, "objective": {"quality_threshold": target}, "constraints": profile.observable(),
                           "seed": seed, "task": task, "steps": spec.schedule.steps})
        known_at_start = agent.known_architectures()
        val_payload = batch_payload(ds, 0, n_val)
        val_range = [0, n_val]   # candidate-evaluation window; moves to the most recent labelled batch in validation_mode=recent
        last_eval: Optional[Dict[str, Any]] = None
        step_records: List[Dict[str, Any]] = []

        def budget() -> Dict[str, float]:
            return {"cost_remaining": env.profile.cost_budget - run.total_cost, "cost_spent": run.total_cost,
                    "deadline_remaining_s": env.profile.deadline_s - run.wall_used_s, "wall_used_s": run.wall_used_s}

        def limits() -> Dict[str, Any]:
            p = env.profile
            return {"cpu": p.cpu, "memory_mb": p.memory_mb, "verification_cost_factor": p.verification_cost_factor,
                    "timeout_s": max(1.0, min(spec.budget.step_timeout_s, max(1.0, p.deadline_s - run.wall_used_s)))}

        def validate(ir: ArchitectureIR) -> List[str]:
            errs = validate_against_registry(ir, self.registry)
            if errs:
                return errs
            est = compile_ir(ir, self.registry, limits()).estimates
            return validate_against_environment(ir, env.observable(), self.registry, est["memory_mb"])

        def estimate(ir: ArchitectureIR) -> Dict[str, float]:
            try:
                return compile_ir(ir, self.registry, limits()).estimates
            except CompileError:
                return {"memory_mb": 1e9, "cost_per_batch": 1e9, "latency_ms": 1e9, "cpu_weight": 1e9}

        def record_decision(d) -> None:
            """Accepts a v0.1 AdaptationDecision (pydantic) or a v0.2 EconomicsV2Decision (dataclass)."""
            if hasattr(d, "model_dump_json"):
                payload, outcome = d.model_dump(mode="json"), d.outcome.value
            else:
                payload, outcome = d.to_dict(), d.outcome
            self.db.add(AdaptationDecisionRow(decision_id=d.decision_id, experiment_id=experiment_id, agent=agent_spec.name,
                                              step=d.step, outcome=outcome, json=json.dumps(payload, default=str)))
            telemetry.record("adaptation_decision", step_time[0], payload)

        def evaluate_candidate(ir: ArchitectureIR, source: str) -> CandidateResult:
            """Sandbox run on the validation slice. Counted and charged as adaptation."""
            t0 = time.monotonic()
            run.arch_evaluations += 1
            self.db.add(ArchitectureRow(architecture_hash=ir.hash(), ir_version=ir.ir_version, parent_hash=ir.parent_hash,
                                        first_seen_experiment=experiment_id, json=ir.to_json()))
            elog.emit(EventType.VALIDATION_STARTED, architecture_hash=ir.hash(), reason=f"validate candidate ({source})", payload={"purpose": "candidate_evaluation"})
            violations = validate(ir)
            if violations:
                elog.emit(EventType.VALIDATION_FAILED, architecture_hash=ir.hash(), reason="; ".join(violations), payload={"purpose": "candidate_evaluation", "violations": violations})
                res = CandidateResult(architecture_hash=ir.hash(), quality=0.0, cost=0.0, runtime_s=0.0, cpu_time_s=0.0,
                                      memory_mb=0.0, violations=violations, failed=True, source=source)
            else:
                spec_c = compile_ir(ir, self.registry, limits())
                elog.emit(EventType.COMPILATION_STARTED, architecture_hash=ir.hash(), payload={"purpose": "candidate_evaluation", "estimates": spec_c.estimates})
                elog.emit(EventType.EXECUTION_STARTED, architecture_hash=ir.hash(), payload={"purpose": "candidate_evaluation", "limits": limits()})
                sb = self.executor.run({"spec": spec_c.model_dump(), "data": val_payload, "state": {}}, limits())
                ok = sb.artifact is not None and sb.artifact.get("ok") and not sb.timed_out
                q = evaluate_batch(ds, val_range[0], val_range[1], sb.artifact)["quality"] if ok else 0.0
                cost = float(sb.artifact["accounting"]["cost"]) if ok else 0.0
                run.cost_adaptation += cost
                run.wall_used_s += sb.runtime_s
                run.cpu_time_s += sb.cpu_time_s
                if ok:
                    run.model_calls += sb.artifact["accounting"]["model_calls"]
                    run.tokens += sb.artifact["accounting"]["tokens"]
                self._persist_execution(experiment_id, agent_spec.name, step_time[1], step_time[0], ir, env.observable(),
                                        "candidate_evaluation", sb, {"quality": q, "source": source})
                xpay = {"purpose": "candidate_evaluation", "runtime_s": sb.runtime_s, "cpu_time_s": sb.cpu_time_s, "max_memory_mb": sb.max_memory_mb,
                        "cost": cost, "violation": sb.resource_violation, "exit_code": sb.exit_code, "executor": sb.executor}
                if sb.resource_violation:
                    elog.emit(EventType.RESOURCE_LIMIT_HIT, architecture_hash=ir.hash(), reason=sb.resource_violation, payload=xpay)
                elog.emit(EventType.EXECUTION_COMPLETED if ok else EventType.EXECUTION_FAILED, architecture_hash=ir.hash(),
                          reason=None if ok else (sb.resource_violation or f"exit {sb.exit_code}"), actual_cost=cost, payload=xpay)
                elog.emit(EventType.RESULT_EVALUATED, architecture_hash=ir.hash(), payload={"purpose": "candidate_evaluation", "quality": q, "source": source, "failed": not ok})
                res = CandidateResult(architecture_hash=ir.hash(), quality=q, cost=cost, runtime_s=sb.runtime_s,
                                      cpu_time_s=sb.cpu_time_s, memory_mb=sb.max_memory_mb,
                                      violations=[sb.resource_violation] if sb.resource_violation else [], failed=not ok, source=source)
            run.search_time_s += time.monotonic() - t0
            run.candidate_log.append({"step": step_time[1], **res.model_dump()})
            telemetry.record("candidate_evaluation", step_time[0], res.model_dump())
            return res

        step_time = [0.0, 0]  # [logical_time, step]
        target_all = target
        for step in range(spec.schedule.steps):
            t = step * spec.schedule.step_seconds
            step_time[0], step_time[1] = t, step
            if target_by_step:
                target = target_by_step[step]
            if spec.schedule.validation_mode == "recent" and step > 0:
                ps, pe = n_val + (step - 1) * batch, n_val + step * batch
                val_payload, val_range = batch_payload(ds, ps, pe), [ps, pe]
            elog.set_context(step, t, env.observable())
            env.advance(t)
            elog.set_context(step, t, env.observable())
            snapshot = telemetry.snapshot(env.observable(), budget())
            elog.emit(EventType.ENVIRONMENT_OBSERVED, constraints=env.observable(),
                      payload={"snapshot": {k: v for k, v in snapshot.items() if k != "host"}, "budget": budget()})
            snapshot["target_quality"] = target
            ctx = AgentContext(experiment_id=experiment_id, agent_name=agent_spec.name, step=step, logical_time_s=t,
                               snapshot=snapshot, registry=self.registry, task=task, target_quality=target, rng=rng,
                               last_evaluation=last_eval, validate=validate, evaluate_candidate=evaluate_candidate,
                               record_decision=record_decision, estimate=estimate, memory=memory, emit=elog.emit,
                               principle_memory=principle_memory, domain=task["domain"], alias=elog.alias,
                               register_architecture=lambda a: self.db.add(ArchitectureRow(architecture_hash=a.hash(), ir_version=a.ir_version,
                                   parent_hash=a.parent_hash, first_seen_experiment=experiment_id, json=a.to_json())))
            t0 = time.monotonic()
            ir = agent.select_architecture(ctx)
            think = time.monotonic() - t0
            run.search_time_s += think
            run.wall_used_s += think

            # Novelty relative to what the agent could have used without discovery + what it already ran.
            nov = novelty(ir, known_at_start + run.architectures_used)
            run.novelties.append(nov)
            run.architectures_used.append(ir)
            self.db.add(ArchitectureRow(architecture_hash=ir.hash(), ir_version=ir.ir_version, parent_hash=ir.parent_hash,
                                        first_seen_experiment=experiment_id, json=ir.to_json()))

            start, end = n_val + step * batch, n_val + (step + 1) * batch if step < spec.schedule.steps - 1 else len(ds["records"])
            labels = ds["labels"][start:end]
            if agent.kind not in ("agm_v2",):   # v2 emits its own selection event with candidates and reasons
                elog.emit(EventType.ARCHITECTURE_SELECTED, architecture_hash=ir.hash(), reason=f"{agent.kind} agent selected {ir.name}",
                          payload={"name": ir.name, "parent_hash": ir.parent_hash, "source": agent.kind, "novelty": nov})
            elog.emit(EventType.VALIDATION_STARTED, architecture_hash=ir.hash(), payload={"purpose": "task"})
            violations = validate(ir)
            deadline_over = run.wall_used_s > env.profile.deadline_s
            if violations:
                elog.emit(EventType.VALIDATION_FAILED, architecture_hash=ir.hash(), reason="; ".join(violations), payload={"purpose": "task", "violations": violations})
                elog.emit(EventType.EXECUTION_FAILED, architecture_hash=ir.hash(), reason="refused: architecture invalid under current environment",
                          payload={"purpose": "task", "violation": "architecture_invalid_for_environment", "cost": 0.0, "runtime_s": 0.0, "cpu_time_s": 0.0, "max_memory_mb": 0.0})
                sb = SandboxResult(exit_code=-1, resource_violation="architecture_invalid_for_environment", executor=self.executor.name,
                                   stderr="; ".join(violations))
                ev = Evaluation(execution_id="", quality=0.0, accuracy=0.0, precision=0.0, recall=0.0, f1=0.0,
                                constraint_violations=violations, failed=True, details={"reason": "refused: architecture invalid under current environment"})
            else:
                comp = compile_ir(ir, self.registry, limits())
                elog.emit(EventType.COMPILATION_STARTED, architecture_hash=ir.hash(), payload={"purpose": "task", "estimates": comp.estimates})
                state = getattr(agent, "_carried_state", {}).get(ir.hash(), {})
                elog.emit(EventType.EXECUTION_STARTED, architecture_hash=ir.hash(), payload={"purpose": "task", "limits": limits(), "batch": [start, end]})
                sb = self.executor.run({"spec": comp.model_dump(), "data": batch_payload(ds, start, end), "state": state}, limits())
                ok = sb.artifact is not None and sb.artifact.get("ok") and not sb.timed_out
                cv: List[str] = []
                if sb.resource_violation:
                    cv.append(sb.resource_violation)
                if sb.runtime_s * 1000.0 > env.profile.latency_ms:
                    cv.append(f"latency_exceeded:{sb.runtime_s * 1000:.0f}ms>{env.profile.latency_ms}ms")
                if ok:
                    sc = evaluate_batch(ds, start, end, sb.artifact)
                    cost = float(sb.artifact["accounting"]["cost"])
                    run.cost_execution += cost
                    run.model_calls += sb.artifact["accounting"]["model_calls"]
                    run.tokens += sb.artifact["accounting"]["tokens"]
                    if not hasattr(agent, "_carried_state"):
                        agent._carried_state = {}
                    agent._carried_state[ir.hash()] = sb.artifact.get("state", {})
                else:
                    sc = {"quality": 0.0, "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
                    cv.append("execution_failed")
                if run.total_cost > env.profile.cost_budget:
                    cv.append("cost_budget_exceeded")
                if deadline_over:
                    cv.append("deadline_exceeded")
                run.wall_used_s += sb.runtime_s
                run.cpu_time_s += sb.cpu_time_s
                run.max_memory_mb = max(run.max_memory_mb, sb.max_memory_mb)
                xpay = {"purpose": "task", "runtime_s": sb.runtime_s, "cpu_time_s": sb.cpu_time_s, "max_memory_mb": sb.max_memory_mb,
                        "cost": float(sb.artifact["accounting"]["cost"]) if ok else 0.0, "violation": sb.resource_violation, "exit_code": sb.exit_code,
                        "violations": cv, "executor": sb.executor}
                if sb.resource_violation or any(v.startswith("latency_exceeded") for v in cv):
                    elog.emit(EventType.RESOURCE_LIMIT_HIT, architecture_hash=ir.hash(), reason=sb.resource_violation or "; ".join(cv), payload=xpay)
                elog.emit(EventType.EXECUTION_COMPLETED if ok else EventType.EXECUTION_FAILED, architecture_hash=ir.hash(),
                          reason=None if ok else (sb.resource_violation or f"exit {sb.exit_code}"), actual_cost=xpay["cost"], payload=xpay)
                ev = Evaluation(execution_id="", quality=sc["quality"], accuracy=sc["accuracy"], precision=sc["precision"],
                                recall=sc["recall"], f1=sc["f1"], constraint_violations=cv, failed=not ok, details=sc)
            exec_id = self._persist_execution(experiment_id, agent_spec.name, step, t, ir, env.observable(), "task", sb,
                                              {"quality": ev.quality, "labels_n": len(labels), "batch": [start, end]})
            ev.execution_id = exec_id
            self.db.add(EvaluationRow(execution_id=exec_id, experiment_id=experiment_id, agent=agent_spec.name, quality=ev.quality,
                                      f1=ev.f1, failed=int(ev.failed), violations=len(ev.constraint_violations), json=ev.model_dump_json()))
            run.qualities.append(ev.quality)
            run.violations += ev.constraint_violations
            run.failures += int(ev.failed)
            if ev.quality >= target and run.time_to_target_logical is None:
                run.time_to_target_logical, run.time_to_target_wall = t, run.wall_used_s
            step_cost = float(sb.artifact["accounting"]["cost"]) if sb.artifact and sb.artifact.get("ok") else 0.0
            summary = {"step": step, "quality": ev.quality, "runtime_s": sb.runtime_s, "cpu_time_s": sb.cpu_time_s,
                       "max_memory_mb": sb.max_memory_mb, "cost": step_cost, "violations": ev.constraint_violations,
                       "failed": ev.failed, "architecture_hash": ir.hash(), "architecture_name": ir.name, "novelty": nov, "target": target,
                       "observations": (sb.artifact or {}).get("observations") if sb.artifact else None,
                       "net_quality": ev.quality - (env.profile.failure_penalty if ev.failed else 0.0)}
            step_records.append({"step": step, "quality": ev.quality, "net_quality": summary["net_quality"], "target": target, "met": ev.quality >= target,
                                 "failed": ev.failed, "hash": ir.hash(), "evaluations_so_far": run.arch_evaluations, "cost_so_far": run.total_cost,
                                 "memory_mb": env.profile.memory_mb, "runtime_s": sb.runtime_s, "max_memory_mb": sb.max_memory_mb})
            telemetry.record_execution(t, summary)
            elog.emit(EventType.RESULT_EVALUATED, architecture_hash=ir.hash(),
                      payload={"purpose": "task", "quality": ev.quality, "accuracy": ev.accuracy, "f1": ev.f1, "failed": ev.failed,
                               "violations": ev.constraint_violations, "target": target, "met_target": ev.quality >= target})
            last_eval = ev.model_dump(mode="json")
            agent.observe(ctx, last_eval, summary)
            for k, v in (("quality", ev.quality), ("accuracy", ev.accuracy), ("latency_ms", sb.runtime_s * 1000), ("cpu_time_s", sb.cpu_time_s),
                         ("memory_mb", sb.max_memory_mb), ("cost", step_cost), ("violations", len(ev.constraint_violations)),
                         ("failed", int(ev.failed)), ("novelty", nov)):
                self.db.add_metric(experiment_id, agent_spec.name, step, k, v)
            self.log(f"  {agent_spec.name:12s} step {step} t={t:>5.0f}s arch={ir.name[:28]:28s} q={ev.quality:.3f} "
                     f"rt={sb.runtime_s:.2f}s mem={env.profile.memory_mb}MB viol={ev.constraint_violations}")

        agg = {
            "quality_mean": sum(run.qualities) / len(run.qualities), "quality_min": min(run.qualities), "quality_final": run.qualities[-1],
            "steps_at_target": sum(1 for q in run.qualities if q >= target), "time_to_target_logical_s": run.time_to_target_logical,
            "time_to_target_wall_s": run.time_to_target_wall, "search_time_s": run.search_time_s,
            "architecture_evaluations": run.arch_evaluations, "model_calls": run.model_calls, "tokens": run.tokens,
            "cpu_time_s": run.cpu_time_s, "max_memory_mb": run.max_memory_mb, "wall_used_s": run.wall_used_s,
            "execution_cost": run.cost_execution, "adaptation_cost": run.cost_adaptation, "total_cost": run.total_cost,
            "constraint_violations": len(run.violations), "violation_list": run.violations, "failures": run.failures,
            "novelty_mean": sum(run.novelties) / len(run.novelties), "novelty_max": max(run.novelties),
            "distinct_architectures": len({a.hash() for a in run.architectures_used}),
            "architectures": [{"step": i, "hash": a.hash(), "name": a.name} for i, a in enumerate(run.architectures_used)],
            "memory_reads": memory.reads if memory else 0, "memory_writes": memory.writes if memory else 0,
            "principle_reads": principle_memory.reads if principle_memory else 0, "principle_writes": principle_memory.writes if principle_memory else 0,
            "run_id": elog.run_id, "n_events": elog.seq + 1, "architecture_aliases": dict(elog.aliases),
            "agent_extra": agent.summary() if hasattr(agent, "summary") else {},
            "env_transitions": len(env.transitions), "decisions": getattr(agent, "decisions", []),
            "step_records": step_records, "net_quality_mean": sum(r["net_quality"] for r in step_records) / len(step_records),
            "steps_met_target": sum(1 for r in step_records if r["met"]), "target_by_step": target_by_step,
        }
        for k in ("quality_mean", "quality_min", "quality_final", "search_time_s", "architecture_evaluations", "model_calls", "tokens",
                  "cpu_time_s", "max_memory_mb", "execution_cost", "adaptation_cost", "total_cost", "constraint_violations",
                  "failures", "novelty_mean", "wall_used_s"):
            self.db.add_metric(experiment_id, agent_spec.name, None, k, agg[k])
        if run.time_to_target_logical is not None:
            self.db.add_metric(experiment_id, agent_spec.name, None, "time_to_target_logical_s", run.time_to_target_logical, "s")
            self.db.add_metric(experiment_id, agent_spec.name, None, "time_to_target_wall_s", run.time_to_target_wall, "s")
        elog.emit(EventType.RUN_COMPLETED, reason="run finished", payload={k: v for k, v in agg.items() if k not in ("decisions",)})
        elog.close()
        telemetry.close()
        return agg

    def _persist_execution(self, experiment_id, agent, step, t, ir, env_obs, purpose, sb: SandboxResult, extra) -> str:
        exec_id = new_id("exe")
        ex = Execution(execution_id=exec_id, experiment_id=experiment_id, agent=agent, step=step, logical_time_s=t,
                       architecture_hash=ir.hash(), architecture=ir.to_dict(), environment_snapshot=env_obs, purpose=purpose, result=sb)
        d = ex.model_dump(mode="json")
        d["extra"] = extra
        if d["result"].get("artifact"):
            art = d["result"]["artifact"]
            # keep artifacts compact in the DB: predictions/confidence are summarised, full state dropped
            d["result"]["artifact"] = {k: v for k, v in art.items() if k not in ("predictions", "confidence", "state")}
            d["result"]["artifact"]["n_predictions"] = len(art.get("predictions", []))
            d["result"]["artifact"]["n_flagged"] = int(sum(art.get("predictions", [])))
            d["result"]["artifact"]["predictions_sha"] = __import__("hashlib").sha256(json.dumps(art.get("predictions", [])).encode()).hexdigest()[:16]
        self.db.add(ExecutionRow(execution_id=exec_id, experiment_id=experiment_id, agent=agent, step=step, logical_time_s=t,
                                 architecture_hash=ir.hash(), purpose=purpose, exit_code=sb.exit_code, timed_out=int(sb.timed_out),
                                 runtime_s=sb.runtime_s, cpu_time_s=sb.cpu_time_s, max_memory_mb=sb.max_memory_mb, json=json.dumps(d)))
        return exec_id


# ----------------------------------------------------------------------
def run_manifest(path: str, executor: Optional[str] = None, db: Optional[Database] = None, quiet: bool = False) -> List[str]:
    raw = load_manifest(path)
    db = db or Database()
    ids: List[str] = []
    if "suite" in raw:
        suite = parse_suite(raw)
        specs = expand_suite(suite, Path(path).resolve().parent)
        if not quiet:
            print(f"suite {suite.name}: {len(specs)} experiments, shared memory db={suite.memory_db}")
    else:
        specs = [parse_experiment(raw)]
    for spec in specs:
        runner = ExperimentRunner(spec, db=db, executor_name=executor, quiet=quiet)
        for r in range(spec.repeats):
            ids.append(runner.run(seed=spec.seed + r))
    return ids


def replay(experiment_id: str, executor: Optional[str] = None, db: Optional[Database] = None, quiet: bool = False,
           results_root: Optional[Path] = None) -> Dict[str, Any]:
    """Re-run an experiment from its stored manifest and compare per-step outputs."""
    db = db or Database()
    results_root = results_root or RESULTS
    orig = db.experiment(experiment_id)
    if not orig:
        raise SystemExit(f"unknown experiment {experiment_id}")
    spec = ExperimentSpec.model_validate(orig["manifest"])
    runner = ExperimentRunner(spec, db=db, executor_name=executor or orig.get("executor"), results_root=results_root, quiet=quiet)
    new_id_ = runner.run(seed=orig["seed"])
    def sig(eid):
        return {(e["agent"], e["step"]): (e["architecture_hash"], (e["result"].get("artifact") or {}).get("predictions_sha"))
                for e in db.executions(eid) if e["purpose"] == "task"}
    a, b = sig(experiment_id), sig(new_id_)
    same = sum(1 for k in a if a[k] == b.get(k))
    report = {"original": experiment_id, "replay": new_id_, "steps_compared": len(a), "steps_identical": same,
              "deterministic": same == len(a), "differences": [{"agent_step": list(k), "original": a[k], "replay": b.get(k)} for k in a if a[k] != b.get(k)]}
    (results_root / new_id_ / "replay_check.json").write_text(json.dumps(report, indent=2))
    if not quiet:
        print(json.dumps(report, indent=2))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run AGM laboratory experiments from a YAML manifest.")
    ap.add_argument("manifest", nargs="?", help="path to experiment or suite manifest")
    ap.add_argument("--executor", choices=["docker", "process"], help="override executor (default from manifest/env)")
    ap.add_argument("--replay", metavar="EXPERIMENT_ID", help="replay a stored experiment and check determinism")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    if args.replay:
        replay(args.replay, executor=args.executor, quiet=args.quiet)
        return
    if not args.manifest:
        ap.error("manifest path required (or --replay)")
    ids = run_manifest(args.manifest, executor=args.executor, quiet=args.quiet)
    print("experiments:", " ".join(ids))


if __name__ == "__main__":
    main()
