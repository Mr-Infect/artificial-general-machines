"""EnvironmentProfile and dynamic environment events (Sections 6 and 12).

The runner holds the event *schedule*; agents only ever see the observable
snapshot exposed through telemetry. Every transition is recorded.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class EnvironmentProfile(BaseModel):
    cpu: float = 1.0
    memory_mb: int = 512
    latency_ms: int = 1000
    energy_budget: float = 1.0          # proxy: relative energy units allowed per batch
    network: bool = False
    privacy: str = "local_only"          # local_only | shared
    deadline_s: float = 60.0
    cost_budget: float = 0.10
    available_capabilities: List[str] = Field(default_factory=list)  # kind:name keys; empty = all
    priority: int = 1
    verification_cost_factor: float = 1.0   # scales cost/latency/cpu of verification capabilities (held-out conditions)

    def observable(self) -> Dict[str, Any]:
        """The view agents receive. Identical to the profile today, but kept as a
        separate method so hidden fields can be added later without leaking."""
        return self.model_dump(mode="json")


class EventType(str, Enum):
    memory_reduction = "memory_reduction"
    cpu_reduction = "cpu_reduction"
    network_loss = "network_loss"
    network_restore = "network_restore"
    latency_reduction = "latency_reduction"
    capability_removal = "capability_removal"
    capability_addition = "capability_addition"
    deadline_reduction = "deadline_reduction"
    priority_increase = "priority_increase"
    cost_budget_reduction = "cost_budget_reduction"


class EnvironmentEvent(BaseModel):
    t: float = Field(description="logical time in seconds at which the event fires")
    type: EventType
    params: Dict[str, Any] = Field(default_factory=dict)


def apply_event(profile: EnvironmentProfile, event: EnvironmentEvent) -> EnvironmentProfile:
    p = profile.model_copy(deep=True)
    q = event.params
    if event.type == EventType.memory_reduction:
        if "memory_mb" in q:
            p.memory_mb = int(q["memory_mb"])
        else:
            p.memory_mb = int(p.memory_mb * float(q.get("factor", 0.5)))
    elif event.type == EventType.cpu_reduction:
        p.cpu = float(q["cpu"]) if "cpu" in q else p.cpu * float(q.get("factor", 0.5))
    elif event.type == EventType.network_loss:
        p.network = False
    elif event.type == EventType.network_restore:
        p.network = True
    elif event.type == EventType.latency_reduction:
        p.latency_ms = int(q["latency_ms"]) if "latency_ms" in q else int(p.latency_ms * float(q.get("factor", 0.5)))
    elif event.type == EventType.capability_removal:
        removed = set(q.get("capabilities", []))
        p.available_capabilities = [c for c in p.available_capabilities if c not in removed]
    elif event.type == EventType.capability_addition:
        for c in q.get("capabilities", []):
            if c not in p.available_capabilities:
                p.available_capabilities.append(c)
    elif event.type == EventType.deadline_reduction:
        p.deadline_s = float(q["deadline_s"]) if "deadline_s" in q else p.deadline_s * float(q.get("factor", 0.5))
    elif event.type == EventType.priority_increase:
        p.priority = int(q.get("priority", p.priority + 1))
    elif event.type == EventType.cost_budget_reduction:
        p.cost_budget = float(q["cost_budget"]) if "cost_budget" in q else p.cost_budget * float(q.get("factor", 0.5))
    return p


class DynamicEnvironment:
    """Holds the current profile and fires scheduled events as logical time advances."""

    def __init__(self, initial: EnvironmentProfile, schedule: List[EnvironmentEvent],
                 on_transition: Optional[Callable[[float, EnvironmentEvent, EnvironmentProfile, EnvironmentProfile], None]] = None):
        self.initial = initial.model_copy(deep=True)
        self.profile = initial.model_copy(deep=True)
        self.schedule = sorted(schedule, key=lambda e: e.t)
        self._fired: List[EnvironmentEvent] = []
        self._on_transition = on_transition
        self.transitions: List[Dict[str, Any]] = []

    def advance(self, logical_time_s: float) -> List[EnvironmentEvent]:
        fired: List[EnvironmentEvent] = []
        for ev in self.schedule:
            if ev in self._fired or ev.t > logical_time_s:
                continue
            before = self.profile
            self.profile = apply_event(before, ev)
            self._fired.append(ev)
            fired.append(ev)
            record = {"t": logical_time_s, "event": ev.model_dump(mode="json"),
                      "before": before.observable(), "after": self.profile.observable()}
            self.transitions.append(record)
            if self._on_transition:
                self._on_transition(logical_time_s, ev, before, self.profile)
        return fired

    def observable(self) -> Dict[str, Any]:
        return self.profile.observable()
