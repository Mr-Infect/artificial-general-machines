"""AGM v0.2 (spec sections 2-5, 8-11, 15, 23-25).

Differences from the v0.1 prototype (which is kept unchanged in baselines/agm.py):

* memory_mode ablation: none | task | architecture | principle | full
    task         v0.1 structural patterns, same-domain retrieval only
    architecture v0.1 structural patterns, cross-domain retrieval (what v0.1 did)
    principle    architectural principles only (memory/principles.py)
    full         patterns + principles
* economics_mode ablation: economic | always_adapt | never_adapt (runtime/economics_v2.py)
* principle extraction after every step (rule-based) and principle validation whenever a
  principle-derived architecture is tested under conditions that did not produce it
* every action emits an event on the run's event stream
* per-candidate structural distance to the current architecture and to the initial one

Everything else (candidate evaluation on the shared validation slice, the sandbox, scoring,
budgets) is identical to the other agents.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from architecture.distance import architecture_distance, novelty_levels
from architecture.ir import ArchitectureIR
from architecture.validate import validate_against_registry
from baselines.agm import AGMAgent
from baselines.base import AgentContext, CandidateResult
from core.models import AdaptationOutcome
from memory.principles import (DecisionRecord, PrincipleEvaluator, PrincipleStatus, condition_context, extract_principles, instantiate)
from memory.structural import make_pattern
from observability.events import EventType
from runtime.economics_v2 import EconomicsV2Inputs, decide_v2, settle

MEMORY_MODES = ("none", "task", "architecture", "principle", "full")
ECON_MODES = ("economic", "always_adapt", "never_adapt")


class AGMv2Agent(AGMAgent):
    kind = "agm_v2"

    def __init__(self, name, config, registry):
        super().__init__(name, config, registry)
        self.memory_mode = config.get("memory_mode", "full")
        self.economics_mode = config.get("economics_mode", "economic")
        if self.memory_mode not in MEMORY_MODES or self.economics_mode not in ECON_MODES:
            raise ValueError(f"bad ablation mode {self.memory_mode}/{self.economics_mode}")
        self.initial: Optional[ArchitectureIR] = None
        self.decisions_v2: List[Any] = []
        self._pending_decision = None
        self._step_candidates: List[Tuple[ArchitectureIR, str, Optional[float]]] = []
        self._step_results: Dict[str, CandidateResult] = {}
        self._step_new_evals: List[str] = []
        self._adapt_cost_before = 0.0
        self._adapt_seconds = 0.0
        self.principles_created: List[str] = []
        self.principles_tested: List[Dict[str, Any]] = []
        self.principle_reuse = 0
        self.transfers: List[Dict[str, Any]] = []
        self.selected_history: List[Dict[str, Any]] = []
        self.memory_hashes: List[str] = []
        self.evaluations_to_target: Optional[int] = None
        self._evals_total = 0

    # ---------------------------------------------------------------- memory access respecting ablation
    def _use_patterns(self) -> bool:
        return self.memory_mode in ("task", "architecture", "full")

    def _use_principles(self) -> bool:
        return self.memory_mode in ("principle", "full")

    def _synthesize(self, ctx: AgentContext, caps: Dict[str, List[str]]):
        out: List[Tuple[ArchitectureIR, str, Optional[float]]] = []
        env = ctx.env
        # 1. structural patterns (v0.1 memory)
        if ctx.memory is not None and self._use_patterns():
            got = ctx.memory.retrieve(env, ctx.task, k=self.memory_k, exclude_experiment=ctx.experiment_id)
            if self.memory_mode == "task":
                got = [(p, s) for p, s in got if p.source_domain == ctx.domain]
            items = []
            for pattern, sim in got:
                ir = self._adapt_to_capabilities(ArchitectureIR.from_dict(pattern.architecture), caps)
                if ir is None:
                    continue
                ir = ir.model_copy(update={"name": f"mem_{pattern.pattern_id[-6:]}", "metadata": {"pattern_id": pattern.pattern_id, "similarity": sim, "source_domain": pattern.source_domain}})
                out.append((ir, "memory", pattern.quality * (0.5 + 0.5 * sim)))
                self.retrieved.append((pattern.pattern_id, ir.hash()))
                items.append({"pattern_id": pattern.pattern_id, "hash": ir.hash(), "similarity": round(sim, 3), "source_domain": pattern.source_domain, "quality": pattern.quality})
            ctx.emit(EventType.MEMORY_RETRIEVED, reason=f"{len(items)} structural pattern(s) applicable", payload={"n": len(items), "patterns": items, "mode": self.memory_mode})
        # 2. principles
        if ctx.principle_memory is not None and self._use_principles():
            cctx = condition_context(env, ctx.task, ctx.target_quality, self.registry)
            got = ctx.principle_memory.retrieve(cctx, k=self.memory_k, exclude_experiment=ctx.experiment_id)
            cards = []
            for principle, score, unmet in got:
                cards.append({"id": principle.id, "name": principle.name, "status": principle.status.value, "confidence": principle.confidence,
                              "applicability": round(score, 3), "unmet": unmet, "source_domains": principle.source_domains,
                              "pattern": principle.structural_pattern.describe(), "description": principle.description})
                ir = instantiate(principle, caps, self.registry, base=self.current)
                if ir is None:
                    continue
                cross = ctx.domain not in principle.source_domains
                ir = ir.model_copy(update={"metadata": {**ir.metadata, "cross_domain": cross, "principle_status": principle.status.value}})
                pred = None
                sup = principle.supported()
                if sup:
                    pred = sum(e.values.get("tested_quality", 0.0) for e in sup) / len(sup)
                out.append((ir, "principle", pred))
                if cross:
                    ctx.emit(EventType.TRANSFER_ATTEMPTED, architecture_hash=ir.hash(), reason=f"principle {principle.id} from {principle.source_domains} instantiated in {ctx.domain}",
                             payload={"principle_id": principle.id, "source_domains": principle.source_domains, "target_domain": ctx.domain, "status": principle.status.value})
            ctx.emit(EventType.PRINCIPLE_RETRIEVED, reason=f"{len(cards)} principle(s) applicable", payload={"principles": cards, "mode": self.memory_mode})
        # 3/4. heuristic synthesis + local variations (identical to v0.1)
        saved_memory = ctx.memory
        ctx.memory = None
        try:
            base = AGMAgent._synthesize(self, ctx, caps)
        finally:
            ctx.memory = saved_memory
        out.extend(base)
        final, hashes = [], set()
        for ir, src, pq in out:
            h = ir.hash()
            if h in hashes or validate_against_registry(ir, self.registry) or ctx.validate(ir):
                continue
            hashes.add(h)
            final.append((ir, src, pq))
        return final

    # ---------------------------------------------------------------- main
    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR:
        t_start = time.monotonic()
        caps = self._capability_model(ctx)
        env = ctx.env
        tight = env.get("memory_mb", 512) < 200
        reqs = {"memory_tight": tight, "expensive_model_available": "large_reasoner" in caps["model"], "network": bool(env.get("network")),
                "verification_required": bool(ctx.task.get("verification_required")), "priority": env.get("priority", 1),
                "available_components": caps["component"], "target_quality": ctx.target_quality}
        ctx.emit(EventType.CAPABILITY_REQUIREMENT_INFERRED, reason=("tight memory → cheap components; " if tight else "") +
                 ("expensive model unavailable; " if not reqs["expensive_model_available"] else "") + f"{len(caps['component'])} components available",
                 payload=reqs)
        current_valid = self.current is not None and not ctx.validate(self.current)
        cur_hash = self.current.hash() if self.current else "none"
        cur_q = self.expected_quality.get(cur_hash, 0.0) if current_valid else 0.0
        candidates = self._synthesize(ctx, caps) if not self.terminated else []
        candidates = [(ir, src, self.evaluated[ir.hash()].quality if ir.hash() in self.evaluated else pq) for ir, src, pq in candidates]
        unevaluated = [c for c in candidates if c[0].hash() not in self.evaluated]
        cand_payload = []
        for ir, src, pq in candidates:
            est = ctx.estimate(ir)
            dist = architecture_distance(ir, self.current, self.registry) if self.current else None
            cand_payload.append({"hash": ir.hash(), "name": ir.name, "source": src, "parent_hash": ir.parent_hash,
                                 "predicted_quality": None if pq is None else round(pq, 3), "estimated_cost": round(est["cost_per_batch"], 5),
                                 "estimated_latency_ms": est["latency_ms"], "estimated_memory_mb": est["memory_mb"],
                                 "distance_to_current": None if dist is None else round(dist["structural_distance"], 3),
                                 "evaluated": ir.hash() in self.evaluated, "principle_id": ir.metadata.get("principle_id"),
                                 "cross_domain": ir.metadata.get("cross_domain", ir.metadata.get("source_domain") not in (None, ctx.domain))})
        ctx.emit(EventType.ARCHITECTURE_GENERATED, reason=f"{len(candidates)} candidates ({len(unevaluated)} unevaluated)", candidate_architectures=cand_payload,
                 payload={"current": cur_hash, "current_valid": current_valid, "current_expected_quality": cur_q})
        self._step_candidates = candidates

        # ---- economics v2
        best_pred = max([pq for _, _, pq in candidates if pq is not None], default=None)
        gap = max(0.0, ctx.target_quality - cur_q)
        if not candidates:
            exp_impr = 0.0
        elif best_pred is not None:
            exp_impr = best_pred - cur_q
            if unevaluated and cur_q < ctx.target_quality:
                exp_impr = max(exp_impr, gap)
        else:
            exp_impr = max(self.exploration_prior, gap)
        est_costs = sorted(ctx.estimate(ir)["cost_per_batch"] for ir, _, _ in unevaluated) or [0.0]
        n_eval = min(self.max_evaluations, len(unevaluated))
        search_cost = sum(est_costs[:n_eval])
        cur_est = ctx.estimate(self.current) if self.current else {"memory_mb": 0, "cost_per_batch": est_costs[0]}
        headroom = env.get("memory_mb", 512) - cur_est["memory_mb"]
        resource_benefit = 0.05 if (current_valid and headroom < 0.2 * env.get("memory_mb", 512) and any(ctx.estimate(ir)["memory_mb"] < cur_est["memory_mb"] for ir, _, _ in candidates)) else 0.0
        recent_viol = ctx.snapshot.get("recent_violations", [])
        risk_reduction = 0.1 if (current_valid and recent_viol) else 0.0
        last_rt = (ctx.snapshot.get("last_execution") or {}).get("runtime_s", 0.5)
        known_frac = (len(candidates) - len(unevaluated)) / max(1, len(candidates))
        x = EconomicsV2Inputs(current_architecture_hash=cur_hash, current_valid=current_valid, expected_quality=cur_q, expected_improvement=exp_impr,
                              expected_resource_benefit=resource_benefit, expected_risk_reduction=risk_reduction, search_cost_usd=search_cost,
                              synthesis_cost_usd=0.0, validation_cost_usd=est_costs[0] if unevaluated else 0.0,
                              execution_overhead_s=max(0.2, last_rt) * n_eval, failure_risk=0.1 * (1 - known_frac) if unevaluated else 0.0,
                              deadline_remaining_s=ctx.deadline_remaining_s, budget_remaining_usd=ctx.budget_remaining, target_quality=ctx.target_quality,
                              priority=env.get("priority", 1), n_unevaluated_candidates=len(unevaluated))
        d = decide_v2(ctx.experiment_id, self.name, ctx.step, x, mode=self.economics_mode)
        self._pending_decision = d
        self._adapt_cost_before = self.adaptation_cost_total
        ctx.emit(EventType.DO_NOT_ADAPT if d.outcome == "DO_NOT_ADAPT" else EventType.ADAPTATION_DECISION, reason=d.rationale,
                 expected_gain=d.expected_gain, estimated_cost=d.estimated_adaptation_cost,
                 payload={"decision_id": d.decision_id, "outcome": d.outcome, "net_expected": d.net_expected, "mode": d.mode, "inputs": d.inputs})
        outcome = AdaptationOutcome(d.outcome)
        self._step_results = {}
        self._step_new_evals = []
        if outcome == AdaptationOutcome.TERMINATE:
            self.terminated = True
            chosen = self.current or self._fallback(ctx, caps)
            self._finish_selection(ctx, chosen, "terminated; keeping current architecture", candidates, t_start)
            return chosen
        if outcome == AdaptationOutcome.DO_NOT_ADAPT and current_valid:
            for ir, src, pq in candidates:
                ctx.emit(EventType.ARCHITECTURE_REJECTED, architecture_hash=ir.hash(), reason="not evaluated: DO_NOT_ADAPT", payload={"source": src, "predicted_quality": pq})
            self._finish_selection(ctx, self.current, "DO_NOT_ADAPT: current architecture kept", candidates, t_start)
            return self.current
        budget_n = n_eval if outcome == AdaptationOutcome.ADAPT else min(self.partial_evaluations, len(unevaluated))
        ranked = sorted(candidates, key=lambda t: (-(t[2] if t[2] is not None else -1), ctx.estimate(t[0])["cost_per_batch"]))
        best_ir, best_res = (self.current if current_valid else None), (self.evaluated.get(cur_hash) if current_valid else None)
        new_evals = 0
        stopped = False
        for ir, src, _ in ranked:
            h = ir.hash()
            if h in self.evaluated:
                res = self.evaluated[h]
            else:
                if new_evals >= budget_n or stopped:
                    ctx.emit(EventType.ARCHITECTURE_REJECTED, architecture_hash=h, reason="not evaluated: evaluation budget exhausted" if not stopped else "not evaluated: target already met by an evaluated candidate", payload={"source": src})
                    continue
                res = ctx.evaluate_candidate(ir, f"agm_{src}")
                new_evals += 1
                self._evals_total += 1
                self._step_new_evals.append(h)
                self.evaluated[h] = res
                self.adaptation_cost_total += res.cost
                self.expected_quality[h] = res.quality
                if ir.metadata.get("principle_id"):
                    self.principle_reuse += 1
            self._step_results[h] = res
            if res.failed:
                ctx.emit(EventType.ARCHITECTURE_REJECTED, architecture_hash=h, reason=f"failed on validation slice: {', '.join(res.violations) or 'execution failed'}", payload={"source": src})
                continue
            if best_res is None or (res.quality, -res.cost) > (best_res.quality, -best_res.cost):
                best_ir, best_res = ir, res
            if best_res is not None and best_res.quality >= ctx.target_quality and new_evals > 0:
                stopped = True
        for ir, src, _ in candidates:
            h = ir.hash()
            if h in self._step_results and best_ir is not None and h != best_ir.hash() and not self._step_results[h].failed:
                r = self._step_results[h]
                ctx.emit(EventType.ARCHITECTURE_REJECTED, architecture_hash=h,
                         reason=f"validation quality {r.quality:.3f} vs selected {best_res.quality:.3f}" if r.quality < best_res.quality else f"same quality {r.quality:.3f} but higher cost {r.cost:.4f} vs {best_res.cost:.4f}",
                         payload={"source": src, "quality": r.quality, "cost": r.cost})
        if best_ir is None:
            best_ir = self._fallback(ctx, caps)
            reason = "no candidate succeeded; fallback architecture"
        else:
            reason = f"best validation quality {best_res.quality:.3f} at cost {best_res.cost:.4f} ({'kept current' if best_ir is self.current else 'new'})" if best_res else "kept current"
        if self.evaluations_to_target is None and best_res is not None and best_res.quality >= ctx.target_quality:
            self.evaluations_to_target = self._evals_total
        self._finish_selection(ctx, best_ir, reason, candidates, t_start)
        return best_ir

    def _finish_selection(self, ctx: AgentContext, ir: ArchitectureIR, reason: str, candidates, t_start: float) -> None:
        if self.initial is None:
            self.initial = ir
        self._adapt_seconds = time.monotonic() - t_start
        src = next((s for c, s, _ in candidates if c.hash() == ir.hash()), "current")
        d_init = architecture_distance(ir, self.initial, self.registry)["structural_distance"]
        d_prev = architecture_distance(ir, self.current, self.registry)["structural_distance"] if self.current else 0.0
        lv = novelty_levels(ir, [ArchitectureIR.from_dict(a) for a in self._reference_archs()], self.registry) if self._reference_archs() else {}
        pid = ir.metadata.get("principle_id")
        if pid:
            self.used_pattern_ids[ir.hash()] = self.used_pattern_ids.get(ir.hash(), ir.metadata.get("pattern_id", ""))
        ctx.emit(EventType.ARCHITECTURE_SELECTED, architecture_hash=ir.hash(), reason=reason,
                 payload={"name": ir.name, "parent_hash": ir.parent_hash, "source": src, "principle_id": pid, "cross_domain": ir.metadata.get("cross_domain", False),
                          "distance_to_initial": round(d_init, 3), "distance_to_previous": round(d_prev, 3), "novelty_level": lv.get("highest_level"),
                          "components": ir.architecture.perception.components, "reasoning": ir.architecture.reasoning.type, "memory": ir.architecture.memory.type,
                          "verification": ir.architecture.verification.type, "estimates": ctx.estimate(ir), "ir": ir.to_dict()})
        self.selected_history.append({"step": ctx.step, "hash": ir.hash(), "source": src, "principle_id": pid, "distance_to_initial": d_init,
                                      "distance_to_previous": d_prev, "novelty_level": lv.get("highest_level"), "cross_domain": bool(ir.metadata.get("cross_domain", False))})
        self.current = ir

    def _reference_archs(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self.initial_memory_archs] if self.initial_memory_archs else []

    # ---------------------------------------------------------------- learning
    def observe(self, ctx: AgentContext, evaluation: Dict[str, Any], execution: Dict[str, Any]) -> None:
        if self.current is None:
            return
        h = self.current.hash()
        q = float(evaluation.get("quality", 0.0))
        self.expected_quality[h] = q if not evaluation.get("failed") else 0.0
        # settle economics
        d = self._pending_decision
        if d is not None:
            settle(d, self.adaptation_cost_total - self._adapt_cost_before, self._adapt_seconds, q, bool(evaluation.get("failed")))
            self.decisions_v2.append(d)
            ctx.record_decision(d)
            ctx.emit(EventType.ADAPTATION_DECISION, reason="settled: actual cost recorded", expected_gain=d.expected_gain, estimated_cost=d.estimated_adaptation_cost,
                     actual_cost=d.actual_adaptation_cost, payload={"decision_id": d.decision_id, "outcome": d.outcome, "phase": "settled", "realized_gain": d.realized_gain,
                                                                    "decision_error": d.decision_error, "cost_estimate_error": d.cost_estimate_error})
            self._pending_decision = None
        # structural pattern memory (write)
        if ctx.memory is not None and self._use_patterns():
            pattern = make_pattern(env=ctx.env, task=ctx.task, architecture=self.current.to_dict(), architecture_hash=h,
                                   resources={"cpu_time_s": execution.get("cpu_time_s", 0.0), "memory_mb": execution.get("max_memory_mb", 0.0),
                                              "cost": execution.get("cost", 0.0), "runtime_s": execution.get("runtime_s", 0.0)},
                                   quality=q, latency_ms=execution.get("runtime_s", 0.0) * 1000.0, failures=1 if evaluation.get("failed") else 0,
                                   constraints={"violations": evaluation.get("constraint_violations", [])}, adaptation_cost=self.adaptation_cost_total,
                                   experiment_id=ctx.experiment_id, domain=str(ctx.domain), target_quality=ctx.target_quality)
            ctx.memory.store(pattern)
        # principles: validation of a principle-derived selection, then extraction
        pm = ctx.principle_memory
        if pm is not None and self._use_principles():
            sel_res = self._step_results.get(h)
            pid = self.current.metadata.get("principle_id")
            if pid and sel_res is not None:
                others = [r for hh, r in self._step_results.items() if hh != h and not r.failed and not self._cand_meta(hh).get("principle_id")]
                baseline = max((r.quality for r in others), default=None)
                kind = PrincipleEvaluator(pm).record_test(pid, ctx.experiment_id, str(ctx.domain), ctx.step, sel_res.quality, baseline, sel_res.failed,
                                                          sel_res.memory_mb, max((r.memory_mb for r in others), default=None),
                                                          extra={"task_quality": q, "cross_domain": self.current.metadata.get("cross_domain", False)})
                if kind:
                    self.principles_tested.append({"principle_id": pid, "step": ctx.step, "kind": kind, "tested": sel_res.quality, "baseline": baseline})
                    p = pm.get(pid)
                    et = EventType.PRINCIPLE_SUPPORTED if kind == "supported" else EventType.PRINCIPLE_CONTRADICTED if kind == "contradicted" else EventType.PRINCIPLE_RETRIEVED
                    ctx.emit(et, reason=f"principle {pid} test {kind} (validation {sel_res.quality:.3f} vs baseline {baseline})",
                             payload={"principle_id": pid, "kind": kind, "status": p.status.value if p else None, "confidence": p.confidence if p else None,
                                      "tested_quality": sel_res.quality, "baseline_quality": baseline, "principles": [] if kind == "inconclusive" else None} if kind != "inconclusive"
                             else {"principle_id": pid, "kind": kind, "principles": [{"id": pid, "status": p.status.value if p else None, "note": "inconclusive test"}]})
                    if self.current.metadata.get("cross_domain"):
                        rec = {"principle_id": pid, "step": ctx.step, "kind": kind, "target_domain": ctx.domain, "task_quality": q}
                        self.transfers.append(rec)
                        ctx.emit(EventType.TRANSFER_COMPLETED, architecture_hash=h, reason=f"cross-domain principle {pid}: {kind}", payload=rec)
            # extraction from this step's decision
            rejected = []
            for ir, src, _ in self._step_candidates:
                hh = ir.hash()
                if hh == h:
                    continue
                r = self._step_results.get(hh)
                rejected.append({"architecture": ir.to_dict(), "result": r.model_dump() if r else {}, "reason": "lower validation quality" if r else "not evaluated"})
            if sel_res is not None:
                rec = DecisionRecord(experiment_id=ctx.experiment_id, domain=str(ctx.domain), step=ctx.step, env=ctx.env, task=ctx.task, target_quality=ctx.target_quality,
                                     selected=self.current.to_dict(), selected_result=sel_res.model_dump(), rejected=rejected,
                                     execution={"quality": q, **{k: execution.get(k) for k in ("cpu_time_s", "max_memory_mb", "cost", "runtime_s")}},
                                     adaptation_cost=self.adaptation_cost_total - self._adapt_cost_before)
                for cand in extract_principles(rec, self.registry):
                    stored = pm.merge(cand)
                    self.principles_created.append(stored.id)
                    ctx.emit(EventType.PRINCIPLE_CREATED, reason=f"{stored.rule}: {stored.description}",
                             payload={"principle_id": stored.id, "rule": stored.rule, "status": stored.status.value, "evidence_count": stored.evidence_count,
                                      "pattern": stored.structural_pattern.describe(), "conditions": [c.describe() for c in stored.conditions()],
                                      "card": stored.render(), "new": stored.id == cand.id})

    def _cand_meta(self, h: str) -> Dict[str, Any]:
        for ir, _, _ in self._step_candidates:
            if ir.hash() == h:
                return ir.metadata
        return {}

    def summary(self) -> Dict[str, Any]:
        errs = [d.decision_error for d in self.decisions_v2 if d.decision_error is not None]
        cerrs = [d.cost_estimate_error for d in self.decisions_v2 if d.cost_estimate_error is not None]
        return {"memory_mode": self.memory_mode, "economics_mode": self.economics_mode, "principle_reuse": self.principle_reuse,
                "principles_created": len(set(self.principles_created)), "principles_tested": self.principles_tested,
                "transfers": self.transfers, "evaluations_to_target": self.evaluations_to_target,
                "decisions": [d.to_dict() for d in self.decisions_v2],
                "decision_outcomes": {o: sum(1 for d in self.decisions_v2 if d.outcome == o) for o in ("ADAPT", "PARTIAL_ADAPT", "DO_NOT_ADAPT", "TERMINATE")},
                "mean_decision_error": sum(errs) / len(errs) if errs else None, "mean_cost_estimate_error": sum(cerrs) / len(cerrs) if cerrs else None,
                "selected_history": self.selected_history,
                "final_distance_to_initial": self.selected_history[-1]["distance_to_initial"] if self.selected_history else None,
                "max_distance_to_initial": max((s["distance_to_initial"] for s in self.selected_history), default=None)}
