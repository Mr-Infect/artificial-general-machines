"""AGM v0.3 (spec v0.3 §4-6, 9-11): regime detection, applicability decisions, negative knowledge,
ablation flags. Extends AGM v0.2; everything downstream (evaluation on the shared window, sandbox,
scoring, budgets) is identical to the other agents.

Ablation flags (config):
  use_principles (bool)      principle memory on/off
  use_archmem (bool)         architecture-pattern memory on/off
  use_negative (bool)        negative principles used to demote candidates on/off
  economics_mode             economic | always_adapt | never_adapt
  regime_detection (bool)    regime detector on/off (off: adaptation is triggered only by validation failure or economics)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from architecture.distance import architecture_distance
from architecture.ir import ArchitectureIR
from architecture.validate import validate_against_registry
from baselines.agm import AGMAgent
from baselines.agm_v2 import AGMv2Agent
from baselines.base import AgentContext
from memory.principles import PrincipleStatus, applicability_decision, condition_context, instantiate
from observability.events import EventType


class AGMv3Agent(AGMv2Agent):
    kind = "agm_v3"

    def __init__(self, name, config, registry):
        self.use_principles = bool(config.get("use_principles", True))
        self.use_archmem = bool(config.get("use_archmem", True))
        self.use_negative = bool(config.get("use_negative", True))
        self.regime_detection = bool(config.get("regime_detection", True))
        mode = "full" if (self.use_principles and self.use_archmem) else "principle" if self.use_principles else "architecture" if self.use_archmem else "none"
        super().__init__(name, {**config, "memory_mode": config.get("memory_mode", mode)}, registry)
        self.history: List[Dict[str, Any]] = []       # per-step observations + quality
        self.detections: List[Dict[str, Any]] = []
        self.regime_flag = False
        self.principle_decisions: List[Dict[str, Any]] = []
        self.negative_applications = 0
        self.switches: List[Dict[str, Any]] = []
        self.step_log: List[Dict[str, Any]] = []
        self._last_env: Optional[Dict[str, Any]] = None
        self._step_new = 0

    # ---------------------------------------------------------------- regime detection (no labels)
    def _detect_regime_change(self, ctx: AgentContext) -> Tuple[bool, List[str]]:
        signals: List[str] = []
        env = ctx.env
        if self._last_env is not None:
            for k in ("memory_mb", "cpu", "verification_cost_factor", "failure_penalty", "network"):
                if env.get(k) != self._last_env.get(k):
                    signals.append(f"constraint {k}: {self._last_env.get(k)} → {env.get(k)}")
            if set(env.get("available_capabilities", [])) != set(self._last_env.get("available_capabilities", [])):
                signals.append("capability set changed")
        self._last_env = dict(env)
        if not self.regime_detection:
            return bool(signals), signals + (["(regime detection disabled: constraint changes only)"] if signals else [])
        last = ctx.snapshot.get("last_execution") or {}
        obs = last.get("observations") or {}
        q = last.get("quality")
        if q is not None and len(self.history) >= 2:
            prev = [h["quality"] for h in self.history[-3:] if h.get("quality") is not None]
            if prev:
                mean_prev = sum(prev) / len(prev)
                if mean_prev - q > 0.15:
                    signals.append(f"quality drop {mean_prev:.2f} → {q:.2f}")
        if obs and len(self.history) >= 2:
            for key in ("flag_rate", "score_std", "input_dispersion", "ambiguous_fraction"):
                prev = [h["observations"].get(key) for h in self.history[-3:] if h.get("observations") and h["observations"].get(key) is not None]
                cur = obs.get(key)
                if cur is None or not prev:
                    continue
                m = sum(prev) / len(prev)
                if m > 1e-9 and abs(cur - m) / m > 0.6 and abs(cur - m) > 0.02:
                    signals.append(f"observation {key}: {m:.3f} → {cur:.3f}")
        return bool(signals), signals

    # ---------------------------------------------------------------- synthesis with decisions + negative knowledge
    def _synthesize(self, ctx: AgentContext, caps: Dict[str, List[str]]):
        out: List[Tuple[ArchitectureIR, str, Optional[float]]] = []
        negatives = []
        if ctx.principle_memory is not None and self.use_principles:
            cctx = condition_context(ctx.env, ctx.task, ctx.target_quality, self.registry)
            got = ctx.principle_memory.retrieve(cctx, k=self.memory_k, exclude_experiment=ctx.experiment_id)
            cards, decisions = [], []
            for principle, score, unmet in got:
                app, _ = principle.applicability(cctx)
                decision, why = applicability_decision(principle, app, unmet)
                if principle.polarity == "negative":
                    decision = "REJECT" if decision in ("TRUST", "TEST", "ADAPT") else decision   # negative knowledge is applied as a veto, never instantiated
                    if decision == "REJECT" and self.use_negative:
                        negatives.append((principle, app))
                rec = {"principle_id": principle.id, "rule": principle.rule, "polarity": principle.polarity, "status": principle.status.value, "confidence": principle.confidence,
                       "applicability": round(app, 3), "decision": decision, "reason": why, "cross_domain": ctx.domain not in principle.source_domains}
                decisions.append(rec)
                cards.append({"id": principle.id, "name": principle.name, "status": principle.status.value, "confidence": principle.confidence, "applicability": round(score, 3),
                              "unmet": unmet, "source_domains": principle.source_domains, "pattern": principle.structural_pattern.describe(), "description": principle.description,
                              "polarity": principle.polarity, "decision": decision})
                if principle.polarity == "negative" or decision in ("IGNORE", "REJECT"):
                    continue
                ir = instantiate(principle, caps, self.registry, base=self.current)
                if ir is None:
                    continue
                cross = ctx.domain not in principle.source_domains
                ir = ir.model_copy(update={"metadata": {**ir.metadata, "cross_domain": cross, "principle_status": principle.status.value, "decision": decision}})
                sup = principle.supported()
                if sup:
                    pred = sum(e.values.get("tested_quality", 0.0) for e in sup) / len(sup)
                else:
                    obs = [e.values.get("selected_quality") for e in principle.observed() if e.values.get("selected_quality") is not None]
                    pred = (sum(obs) / len(obs)) * (0.5 + 0.5 * score) if obs else None
                if pred is not None:
                    pred *= {"TRUST": 1.0, "TEST": 0.85, "ADAPT": 0.7}[decision]
                out.append((ir, "principle", pred))
                if cross:
                    ctx.emit(EventType.TRANSFER_ATTEMPTED, architecture_hash=ir.hash(), reason=f"principle {principle.id} ({decision}) from {principle.source_domains} instantiated in {ctx.domain}",
                             payload={"principle_id": principle.id, "source_domains": principle.source_domains, "target_domain": ctx.domain, "status": principle.status.value, "decision": decision})
            for d in decisions:
                ctx.emit(EventType.PRINCIPLE_DECISION, reason=f"{d['decision']}: {d['reason']}", payload=d)
            self.principle_decisions.extend([{"step": ctx.step, **d} for d in decisions])
            ctx.emit(EventType.PRINCIPLE_RETRIEVED, reason=f"{len(cards)} principle(s) retrieved", payload={"principles": cards, "mode": self.memory_mode})
        if ctx.memory is not None and self.use_archmem:
            got = ctx.memory.retrieve(ctx.env, ctx.task, k=self.memory_k, exclude_experiment=ctx.experiment_id)
            items = []
            for pattern, sim in got:
                ir = self._adapt_to_capabilities(ArchitectureIR.from_dict(pattern.architecture), caps)
                if ir is None:
                    continue
                ir = ir.model_copy(update={"name": f"mem_{pattern.pattern_id[-6:]}", "metadata": {"pattern_id": pattern.pattern_id, "similarity": sim, "source_domain": pattern.source_domain}})
                out.append((ir, "memory", pattern.quality * (0.5 + 0.5 * sim)))
                items.append({"pattern_id": pattern.pattern_id, "hash": ir.hash(), "similarity": round(sim, 3), "source_domain": pattern.source_domain, "quality": pattern.quality})
            ctx.emit(EventType.MEMORY_RETRIEVED, reason=f"{len(items)} structural pattern(s) applicable", payload={"n": len(items), "patterns": items, "mode": self.memory_mode})
        saved = ctx.memory
        ctx.memory = None
        try:
            out.extend(AGMAgent._synthesize(self, ctx, caps))
        finally:
            ctx.memory = saved
        out.extend(self._wide_synthesis(ctx, caps))
        # validity + dedupe (keep best prediction)
        final, index = [], {}
        for ir, src, pq in out:
            h = ir.hash()
            if h in index:
                i = index[h]
                if pq is not None and (final[i][2] is None or pq > final[i][2]):
                    final[i] = (final[i][0], final[i][1], pq)
                continue
            if validate_against_registry(ir, self.registry) or ctx.validate(ir):
                continue
            index[h] = len(final)
            final.append((ir, src, pq))
        # negative knowledge: demote candidates matching an applicable negative principle
        if negatives:
            demoted = []
            for i, (ir, src, pq) in enumerate(final):
                for principle, app in negatives:
                    ok, _ = principle.structural_pattern.matches(ir, self.registry)
                    if ok:
                        base_pred = pq if pq is not None else 0.5
                        final[i] = (ir, src, base_pred * 0.3)
                        demoted.append((ir.hash(), principle.id))
                        break
            self.negative_applications += len(demoted)
            for h, pid in demoted:
                ctx.emit(EventType.ARCHITECTURE_REJECTED, architecture_hash=h, reason=f"demoted by negative knowledge {pid}", payload={"negative_principle": pid, "demoted": True})
        return final

    # ---------------------------------------------------------------- main
    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR:
        changed, signals = self._detect_regime_change(ctx)
        self.regime_flag = changed
        if changed:
            self.detections.append({"step": ctx.step, "signals": signals})
            ctx.emit(EventType.REGIME_CHANGE_DETECTED, reason="; ".join(signals), payload={"signals": signals, "step": ctx.step})
            # architecture-mismatch hypothesis: the current architecture's expected quality is no longer trusted
            if self.current is not None:
                self.expected_quality[self.current.hash()] = min(self.expected_quality.get(self.current.hash(), 0.0), max(0.0, (ctx.snapshot.get("last_execution") or {}).get("quality", 0.0) * 0.8))
        prev = self.current
        evals_before = self._evals_total
        chosen = super().select_architecture(ctx)
        self._step_new = self._evals_total - evals_before
        if prev is not None and chosen.hash() != prev.hash():
            d = architecture_distance(chosen, prev, self.registry)["structural_distance"]
            self.switches.append({"step": ctx.step, "from": prev.hash(), "to": chosen.hash(), "distance": d, "after_detection": changed})
            ctx.emit(EventType.ARCHITECTURE_SWITCHED, architecture_hash=chosen.hash(), reason=f"switched from {ctx.alias(prev.hash())} (structural distance {d:.2f})",
                     payload={"from": prev.hash(), "to": chosen.hash(), "distance": d, "after_detection": changed})
        return chosen

    def observe(self, ctx: AgentContext, evaluation: Dict[str, Any], execution: Dict[str, Any]) -> None:
        super().observe(ctx, evaluation, execution)
        self.history.append({"step": ctx.step, "quality": evaluation.get("quality"), "observations": execution.get("observations"), "target": ctx.target_quality})
        d = self.decisions_v2[-1] if self.decisions_v2 else None
        self.step_log.append({"step": ctx.step, "detected": self.regime_flag, "decision": d.outcome if d else None, "new_evaluations": self._step_new,
                              "switched": bool(self.switches and self.switches[-1]["step"] == ctx.step), "quality": evaluation.get("quality"),
                              "met_target": (evaluation.get("quality") or 0) >= ctx.target_quality, "target": ctx.target_quality, "failed": evaluation.get("failed")})

    def summary(self) -> Dict[str, Any]:
        s = super().summary()
        s.update({"use_principles": self.use_principles, "use_archmem": self.use_archmem, "use_negative": self.use_negative, "regime_detection": self.regime_detection,
                  "detections": self.detections, "switches": self.switches, "principle_decisions": self.principle_decisions,
                  "decision_counts": {k: sum(1 for d in self.principle_decisions if d["decision"] == k) for k in ("TRUST", "TEST", "IGNORE", "REJECT", "ADAPT")},
                  "negative_applications": self.negative_applications, "step_log": self.step_log})
        return s
