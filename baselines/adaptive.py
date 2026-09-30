"""B1 Adaptive Agent: rule-based selection among preset architectures.

It may switch presets in response to telemetry but never searches or
evaluates candidates in the sandbox.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

from architecture.ir import ArchitectureIR
from baselines.base import Agent, AgentContext, ir_from_config

ROOT = Path(__file__).resolve().parent.parent


class AdaptiveAgent(Agent):
    kind = "adaptive"

    def __init__(self, name, config, registry):
        super().__init__(name, config, registry)
        self.library_mode = config.get("library", "configs/adaptive_library.yaml")
        if self.library_mode == "roles":
            self.presets: Dict[str, ArchitectureIR] = {}   # built from roles once the environment is seen
        else:
            raw = yaml.safe_load((ROOT / self.library_mode).read_text())["presets"]
            self.presets = {k: ir_from_config(v, name=k) for k, v in raw.items()}
        self.tried: List[str] = []
        self.current_name = None
        self.current = self.presets.get(config.get("initial", "standard"))

    def known_architectures(self) -> List[ArchitectureIR]:
        return list(self.presets.values())

    ROLE_PRESETS = {   # role-based presets (v0.3): the same organizations in any component vocabulary
        "lightweight": {"roles": ["robust_estimator"], "reasoning": "direct", "model": "small_reasoner", "memory": "none", "verification": "none"},
        "standard": {"roles": ["broad_filter", "robust_estimator", "change_detector"], "reasoning": "parallel", "model": "small_reasoner", "memory": "none", "verification": "rule_based"},
        "verified": {"roles": ["rule_check", "consistency_check", "robust_estimator"], "reasoning": "parallel", "model": "small_reasoner", "memory": "none", "verification": "rule_based"},
        "heavy": {"roles": ["broad_filter", "robust_estimator", "change_detector"], "reasoning": "hierarchical", "model": "large_reasoner", "memory": "episodic", "verification": "execution_based"},
    }

    def _build_role_presets(self, ctx: AgentContext) -> None:
        avail = set(ctx.env.get("available_capabilities", []))
        by_role: Dict[str, str] = {}
        for c in self.registry.names("component"):
            if avail and f"component:{c}" not in avail:
                continue
            role = (self.registry.get("component", c) or object()).__dict__.get("params", {}).get("role", c)
            by_role.setdefault(role, c)
        for name, spec in self.ROLE_PRESETS.items():
            comps = [by_role[r] for r in spec["roles"] if r in by_role]
            if not comps:
                continue
            rtype = spec["reasoning"] if len(comps) >= 2 or spec["reasoning"] in ("direct", "sequential", "iterative") else "direct"
            body = {"perception": {"mode": "single" if len(comps) == 1 else "parallel", "components": comps},
                    "reasoning": {"type": rtype, "model": spec["model"], "threshold": 0.5}, "memory": {"type": spec["memory"]}, "verification": {"type": spec["verification"]}}
            try:
                self.presets[name] = ArchitectureIR(name=name, architecture=body)
            except Exception:
                continue
        if self.current is None and "standard" in self.presets:
            self.current = self.presets["standard"]

    def _valid(self, ctx: AgentContext) -> Dict[str, ArchitectureIR]:
        if self.library_mode == "roles" and not self.presets:
            self._build_role_presets(ctx)
        return {k: v for k, v in self.presets.items() if not ctx.validate(v)}

    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR:
        env = ctx.env
        valid = self._valid(ctx)
        if not valid:  # nothing runnable; keep current (execution will be refused and recorded)
            return self.current
        choice = None
        pfx = "planning_" if ctx.task.get("domain") == "planning" else ""
        if env.get("memory_mb", 1e9) < self.config.get("low_memory_mb", 200) and pfx + "lightweight" in valid:
            choice = pfx + "lightweight"
        elif ctx.task.get("verification_required") and "verified" in valid:
            choice = "verified"
        elif env.get("priority", 1) >= 2 and pfx + "heavy" in valid and ctx.budget_remaining > self.config.get("heavy_min_budget", 0.05):
            choice = pfx + "heavy"
        elif pfx + "standard" in valid:
            choice = pfx + "standard"
        else:
            choice = sorted(valid, key=lambda k: ctx.estimate(valid[k])["cost_per_batch"])[0]
        # If the last step missed the target, try an untried valid preset (cheapest first).
        last_q = (ctx.last_evaluation or {}).get("quality")
        if last_q is not None and last_q < ctx.target_quality:
            untried = [k for k in sorted(valid, key=lambda k: ctx.estimate(valid[k])["cost_per_batch"]) if k not in self.tried]
            if untried:
                choice = untried[0]
        self.current_name = choice
        self.current = valid[choice]
        if choice not in self.tried:
            self.tried.append(choice)
        return self.current
