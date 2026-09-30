"""B0 Fixed Agent: a static architecture, never changes."""
from __future__ import annotations

from architecture.ir import ArchitectureIR
from baselines.base import Agent, AgentContext, ir_from_config

DEFAULT = {"perception": {"mode": "parallel", "components": ["statistical_detector", "anomaly_detector", "rate_detector"]},
           "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5},
           "memory": {"type": "none"}, "verification": {"type": "rule_based"}}


class FixedAgent(Agent):
    kind = "fixed"

    def __init__(self, name, config, registry):
        super().__init__(name, config, registry)
        self.current = ir_from_config(config.get("architecture", DEFAULT), name=f"{name}_fixed")

    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR:
        return self.current
