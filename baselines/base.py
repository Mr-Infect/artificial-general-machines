"""Agent interface shared by all baselines (Section 8).

Agents never touch the sandbox, the dataset or the environment schedule.
They receive an ``AgentContext`` each step and return an Architecture IR.
Candidate evaluation goes through ``ctx.evaluate_candidate`` so that every
architecture evaluation is counted and charged identically for all agents.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from architecture.ir import ArchitectureIR
from core.models import AdaptationDecision
from core.registry import CapabilityRegistry


class CandidateResult(BaseModel):
    architecture_hash: str
    quality: float
    cost: float
    runtime_s: float
    cpu_time_s: float
    memory_mb: float
    violations: List[str] = Field(default_factory=list)
    failed: bool = False
    source: str = "unknown"


class AgentContext:
    def __init__(self, *, experiment_id: str, agent_name: str, step: int, logical_time_s: float,
                 snapshot: Dict[str, Any], registry: CapabilityRegistry, task: Dict[str, Any],
                 target_quality: float, rng: random.Random, last_evaluation: Optional[Dict[str, Any]],
                 validate: Callable[[ArchitectureIR], List[str]],
                 evaluate_candidate: Callable[[ArchitectureIR, str], CandidateResult],
                 record_decision: Callable[[AdaptationDecision], None],
                 estimate: Callable[[ArchitectureIR], Dict[str, float]],
                 memory: Any = None):
        self.experiment_id = experiment_id
        self.agent_name = agent_name
        self.step = step
        self.logical_time_s = logical_time_s
        self.snapshot = snapshot
        self.registry = registry
        self.task = task
        self.target_quality = target_quality
        self.rng = rng
        self.last_evaluation = last_evaluation
        self.validate = validate
        self.evaluate_candidate = evaluate_candidate
        self.record_decision = record_decision
        self.estimate = estimate
        self.memory = memory

    @property
    def env(self) -> Dict[str, Any]:
        return self.snapshot["environment"]

    @property
    def budget_remaining(self) -> float:
        return float(self.snapshot["budget"]["cost_remaining"])

    @property
    def deadline_remaining_s(self) -> float:
        return float(self.snapshot["budget"]["deadline_remaining_s"])


class Agent(ABC):
    kind: str = "abstract"

    def __init__(self, name: str, config: Dict[str, Any], registry: CapabilityRegistry):
        self.name = name
        self.config = config
        self.registry = registry
        self.current: Optional[ArchitectureIR] = None

    @abstractmethod
    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR: ...

    def observe(self, ctx: AgentContext, evaluation: Dict[str, Any], execution: Dict[str, Any]) -> None:
        return None

    def known_architectures(self) -> List[ArchitectureIR]:
        """Architectures the agent had access to before the experiment (novelty baseline)."""
        return [self.current] if self.current else []


def ir_from_config(cfg: Dict[str, Any], name: str = "configured") -> ArchitectureIR:
    if "ir_version" in cfg or "architecture" in cfg:
        return ArchitectureIR.from_dict({"name": name, **cfg})
    return ArchitectureIR(name=name, architecture=cfg)
