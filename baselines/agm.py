"""B4 AGM prototype (bounded, v0.1).

Implements the components named in Section 8 without open-ended invention:
environment model, objective model, capability model, architecture synthesis
(from registry primitives and structural memory), adaptation economics,
structural memory, and architectural transfer (memory persisted across
experiments). It cannot modify code and cannot leave the registry.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from architecture.ir import ArchitectureIR, novelty
from architecture.validate import validate_against_registry
from baselines.base import Agent, AgentContext, CandidateResult
from core.models import AdaptationOutcome
from memory.structural import make_pattern
from runtime.economics import EconomicsInputs, decide


class AGMAgent(Agent):
    kind = "agm"

    def __init__(self, name, config, registry):
        super().__init__(name, config, registry)
        self.max_evaluations = int(config.get("max_evaluations", 6))
        self.partial_evaluations = int(config.get("partial_evaluations", 2))
        self.exploration_prior = float(config.get("exploration_prior", 0.15))
        self.memory_k = int(config.get("memory_k", 5))
        self.evaluated: Dict[str, CandidateResult] = {}
        self.expected_quality: Dict[str, float] = {}
        self.adaptation_cost_total = 0.0
        self.retrieved: List[Tuple[str, str]] = []  # (pattern_id, arch hash) offered by memory
        self.used_pattern_ids: Dict[str, str] = {}
        self.terminated = False
        self.decisions: List[Dict[str, Any]] = []
        self.initial_memory_archs: List[ArchitectureIR] = []

    # --- environment / objective / capability models ------------------------
    def _capability_model(self, ctx: AgentContext) -> Dict[str, List[str]]:
        avail = set(ctx.env.get("available_capabilities", []))
        def ok(kind, n):
            return not avail or f"{kind}:{n}" in avail
        model = {kind: [n for n in self.registry.names(kind) if ok(kind, n)]
                 for kind in ("component", "model", "reasoning", "memory", "verification", "tool")}
        if not ctx.env.get("network"):
            model["tool"] = [t for t in model["tool"] if not (self.registry.get("tool", t) or object()).__dict__.get("requires_network")]
        return model

    def _objective(self, ctx: AgentContext) -> Dict[str, float]:
        return {"target": ctx.target_quality, "priority": ctx.env.get("priority", 1),
                "cost_remaining": ctx.budget_remaining, "deadline_remaining_s": ctx.deadline_remaining_s}

    # --- synthesis ---------------------------------------------------------------
    def _adapt_to_capabilities(self, ir: ArchitectureIR, caps: Dict[str, List[str]]) -> Optional[ArchitectureIR]:
        a = ir.architecture
        changes: Dict[str, Any] = {}
        comps = [c for c in a.perception.components if c in caps["component"]]
        if not comps:
            return None
        if comps != list(a.perception.components):
            changes["perception.components"] = comps
        if a.reasoning.model not in caps["model"]:
            if "small_reasoner" in caps["model"]:
                changes["reasoning.model"] = "small_reasoner"
            else:
                return None
        if a.reasoning.type in ("parallel", "hierarchical") and len(comps) < 2:
            changes["reasoning.type"] = "direct"
        if a.memory.type not in caps["memory"]:
            changes["memory.type"] = "none"
        if a.verification.type not in caps["verification"] or (
                a.verification.type == "model_based" and a.verification.model not in caps["model"]):
            changes["verification.type"] = "rule_based" if "rule_based" in caps["verification"] else "none"
            changes["verification.model"] = None
        tools = [t for t in a.tools if t in caps["tool"]] or ["python"]
        if tools != list(a.tools):
            changes["tools"] = tools
        return ir.derive(name=ir.name, **changes) if changes else ir

    def _synthesize(self, ctx: AgentContext, caps: Dict[str, List[str]]) -> List[Tuple[ArchitectureIR, str, Optional[float]]]:
        """Return (candidate, source, predicted_quality) triples."""
        out: List[Tuple[ArchitectureIR, str, Optional[float]]] = []
        env = ctx.env
        # 1. structural memory
        if ctx.memory is not None:
            for pattern, sim in ctx.memory.retrieve(env, ctx.task, k=self.memory_k, exclude_experiment=ctx.experiment_id):
                ir = ArchitectureIR.from_dict(pattern.architecture)
                ir = self._adapt_to_capabilities(ir, caps)
                if ir is None:
                    continue
                ir = ir.model_copy(update={"name": f"mem_{pattern.pattern_id[-6:]}", "metadata": {"pattern_id": pattern.pattern_id, "similarity": sim, "source_domain": pattern.source_domain}})
                out.append((ir, "memory", pattern.quality * (0.5 + 0.5 * sim)))
                self.retrieved.append((pattern.pattern_id, ir.hash()))
        # 2. heuristic synthesis from the capability model and environment model
        comps = caps["component"]
        tight_memory = env.get("memory_mb", 512) < 200
        big_model_ok = "large_reasoner" in caps["model"] and not tight_memory and ctx.budget_remaining > 0.05
        want_verify = bool(ctx.task.get("verification_required"))
        verification = "rule_based" if ("rule_based" in caps["verification"] and want_verify) else ("none" if "none" in caps["verification"] else caps["verification"][0])
        memory_t = "episodic" if ("episodic" in caps["memory"] and not tight_memory) else "none"
        combos: List[List[str]] = [[c] for c in comps]
        if len(comps) >= 2:
            combos.append(comps[:3])
            combos.append(comps)
            robust = [c for c in comps if c in ("anomaly_detector", "range_validator", "consistency_checker")]
            if len(robust) >= 2:
                combos.append(robust)
        seen = set()
        for cs in combos:
            key = tuple(cs)
            if key in seen:
                continue
            seen.add(key)
            single = len(cs) == 1
            variants = [("direct" if single else "parallel", "small_reasoner")]
            if not single and big_model_ok and "hierarchical" in caps["reasoning"]:
                variants.append(("hierarchical", "large_reasoner"))
            for rtype, model in variants:
                body = {"perception": {"mode": "single" if single else "parallel", "components": cs},
                        "reasoning": {"type": rtype, "model": model, "threshold": 0.5},
                        "memory": {"type": memory_t if not single else "none"},
                        "verification": {"type": verification if not single else "none"}}
                try:
                    ir = ArchitectureIR(name=f"syn_{'+'.join(c[:4] for c in cs)}_{rtype}", architecture=body)
                except Exception:
                    continue
                out.append((ir, "synthesis", None))
        # 3. local variation of the current architecture
        if self.current is not None:
            for change in ({"reasoning.threshold": round(min(0.95, self.current.architecture.reasoning.threshold + 0.1), 2)},
                           {"reasoning.threshold": round(max(0.05, self.current.architecture.reasoning.threshold - 0.1), 2)}):
                try:
                    out.append((self.current.derive(name="local", **change), "local", None))
                except Exception:
                    pass
        # validity filter + dedupe
        final, hashes = [], set()
        for ir, src, pq in out:
            h = ir.hash()
            if h in hashes or validate_against_registry(ir, self.registry) or ctx.validate(ir):
                continue
            hashes.add(h)
            final.append((ir, src, pq))
        return final

    # --- main loop ----------------------------------------------------------------
    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR:
        caps = self._capability_model(ctx)
        current_valid = self.current is not None and not ctx.validate(self.current)
        cur_hash = self.current.hash() if self.current else "none"
        cur_q = self.expected_quality.get(cur_hash, 0.0) if current_valid else 0.0
        candidates = self._synthesize(ctx, caps) if not self.terminated else []
        best_pred = max([pq for _, _, pq in candidates if pq is not None], default=None)
        # Objective model: with a memory prediction, the expected gain is prediction - current; without one,
        # the gap to the target (bounded below by the exploration prior) is what adaptation could recover.
        gap = max(0.0, ctx.target_quality - cur_q)
        if not candidates:
            exp_impr = 0.0
        elif best_pred is not None:
            exp_impr = max(best_pred - cur_q, gap if cur_q < ctx.target_quality else 0.0)
        else:
            exp_impr = max(self.exploration_prior, gap)
        est_cost = [ctx.estimate(ir)["cost_per_batch"] for ir, _, _ in candidates] or [0.0]
        n_eval = min(self.max_evaluations, len(candidates))
        avg_eval_cost = sum(sorted(est_cost)[:n_eval]) / max(1, n_eval)
        last_rt = (ctx.snapshot.get("last_execution") or {}).get("runtime_s", 0.5)
        x = EconomicsInputs(current_architecture_hash=cur_hash, expected_quality=cur_q, expected_improvement=exp_impr,
                            search_cost=avg_eval_cost * n_eval, synthesis_cost=0.0,
                            validation_cost=avg_eval_cost, execution_cost=ctx.estimate(self.current)["cost_per_batch"] if self.current else avg_eval_cost,
                            deadline_remaining_s=ctx.deadline_remaining_s, resource_budget_remaining=ctx.budget_remaining,
                            target_quality=ctx.target_quality, priority=ctx.env.get("priority", 1), current_valid=current_valid,
                            expected_adaptation_seconds=max(0.2, last_rt) * n_eval)
        decision = decide(ctx.experiment_id, self.name, ctx.step, x)
        ctx.record_decision(decision)
        self.decisions.append(decision.model_dump(mode="json"))
        outcome = decision.outcome
        if outcome == AdaptationOutcome.TERMINATE:
            self.terminated = True
            return self.current or self._fallback(ctx, caps)
        if outcome == AdaptationOutcome.DO_NOT_ADAPT and current_valid:
            return self.current
        budget_n = n_eval if outcome == AdaptationOutcome.ADAPT else min(self.partial_evaluations, len(candidates))
        # rank: memory predictions first, then synthesis, cheapest first within a class
        ranked = sorted(candidates, key=lambda t: (-(t[2] if t[2] is not None else -1), ctx.estimate(t[0])["cost_per_batch"]))
        best_ir, best_res = (self.current if current_valid else None), None
        if current_valid:
            best_res = self.evaluated.get(cur_hash)
        for ir, src, _ in ranked[:budget_n]:
            h = ir.hash()
            res = self.evaluated.get(h) or ctx.evaluate_candidate(ir, f"agm_{src}")
            self.evaluated[h] = res
            self.adaptation_cost_total += res.cost
            self.expected_quality[h] = res.quality
            if res.failed:
                continue
            if best_res is None or (res.quality, -res.cost) > (best_res.quality, -best_res.cost):
                best_ir, best_res = ir, res
        if best_ir is None:
            best_ir = self._fallback(ctx, caps)
        self.current = best_ir
        pid = best_ir.metadata.get("pattern_id") if best_ir else None
        if pid:
            self.used_pattern_ids[best_ir.hash()] = pid
        return best_ir

    def _fallback(self, ctx: AgentContext, caps: Dict[str, List[str]]) -> ArchitectureIR:
        comp = "anomaly_detector" if "anomaly_detector" in caps["component"] else (caps["component"] or ["statistical_detector"])[0]
        model = "small_reasoner" if "small_reasoner" in caps["model"] else (caps["model"] or ["small_reasoner"])[0]
        return ArchitectureIR(name="fallback", architecture={"perception": {"mode": "single", "components": [comp]},
                                                             "reasoning": {"type": "direct", "model": model}})

    def observe(self, ctx: AgentContext, evaluation: Dict[str, Any], execution: Dict[str, Any]) -> None:
        if self.current is None:
            return
        h = self.current.hash()
        q = float(evaluation.get("quality", 0.0))
        self.expected_quality[h] = q if not evaluation.get("failed") else 0.0
        if ctx.memory is None:
            return
        pattern = make_pattern(env=ctx.env, task=ctx.task, architecture=self.current.to_dict(), architecture_hash=h,
                               resources={"cpu_time_s": execution.get("cpu_time_s", 0.0), "memory_mb": execution.get("max_memory_mb", 0.0),
                                          "cost": execution.get("cost", 0.0), "runtime_s": execution.get("runtime_s", 0.0)},
                               quality=q, latency_ms=execution.get("runtime_s", 0.0) * 1000.0,
                               failures=1 if evaluation.get("failed") else 0,
                               constraints={"violations": evaluation.get("constraint_violations", [])},
                               adaptation_cost=self.adaptation_cost_total, experiment_id=ctx.experiment_id,
                               domain=str(ctx.task.get("domain")), target_quality=ctx.target_quality)
        ctx.memory.store(pattern)
        pid = self.used_pattern_ids.get(h)
        if pid:
            ctx.memory.record_transfer(pid, ctx.experiment_id, str(ctx.task.get("domain")), q)

    def known_architectures(self) -> List[ArchitectureIR]:
        return list(self.initial_memory_archs)
