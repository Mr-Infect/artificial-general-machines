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
        lib_path = ROOT / config.get("library", "configs/adaptive_library.yaml")
        raw = yaml.safe_load(lib_path.read_text())["presets"]
        self.presets: Dict[str, ArchitectureIR] = {k: ir_from_config(v, name=k) for k, v in raw.items()}
        self.tried: List[str] = []
        self.current_name = None
        self.current = self.presets.get(config.get("initial", "standard"))

    def known_architectures(self) -> List[ArchitectureIR]:
        return list(self.presets.values())

    def _valid(self, ctx: AgentContext) -> Dict[str, ArchitectureIR]:
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
