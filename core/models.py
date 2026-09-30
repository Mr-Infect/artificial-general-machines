"""Core laboratory entities (Section 3 of the specification).

These are plain Pydantic models. Persistence lives in ``core/db.py``; the
Architecture IR lives in ``architecture/ir.py``. Everything here is
serializable so that any run can be reproduced from its manifest.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    anomaly_detection = "anomaly_detection"
    scientific_verification = "scientific_verification"


class Task(BaseModel):
    """What must be accomplished, independent of how."""
    type: TaskType
    domain: str = Field(description="Domain label, e.g. network or scientific")
    dataset_size: int = 2000
    noise: float = 0.05
    anomaly_rate: float = 0.03
    accuracy_requirement: float = 0.85
    verification_required: bool = False
    priority: int = 1


class ConstraintSet(BaseModel):
    """Hard limits that an execution must respect."""
    cpu: float = 1.0
    memory_mb: int = 512
    latency_ms: int = 1000
    deadline_s: float = 60.0
    max_cost: float = 0.10
    network: bool = False
    privacy: str = "local_only"


class Capability(BaseModel):
    """One entry in the capability registry."""
    name: str
    kind: str  # model | reasoning | memory | verification | tool | component
    description: str = ""
    cost_per_call: float = 0.0        # simulated USD
    latency_ms: float = 0.0           # simulated latency proxy per call
    memory_mb: float = 0.0            # simulated footprint
    cpu_weight: float = 1.0           # relative compute cost
    requires_network: bool = False
    tokens_per_call: int = 0          # simulated token usage
    params: Dict[str, Any] = Field(default_factory=dict)


class ArchitectureCandidate(BaseModel):
    """A proposed architecture awaiting or under evaluation."""
    candidate_id: str
    architecture_hash: str
    architecture: Dict[str, Any]
    source: str = "manual"  # manual | search | memory | mutation | synthesis
    parent_hash: Optional[str] = None
    predicted_quality: Optional[float] = None
    predicted_cost: Optional[float] = None


class SandboxResult(BaseModel):
    """What the sandbox returns for every run (Section 7)."""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    runtime_s: float = 0.0
    cpu_time_s: float = 0.0
    max_memory_mb: float = 0.0
    timed_out: bool = False
    resource_violation: Optional[str] = None
    artifact: Optional[Dict[str, Any]] = None
    executor: str = "docker"


class Execution(BaseModel):
    execution_id: str
    experiment_id: str
    agent: str
    step: int
    logical_time_s: float
    architecture_hash: str
    architecture: Dict[str, Any]
    environment_snapshot: Dict[str, Any]
    purpose: str = "task"   # task | candidate_evaluation | replay
    result: SandboxResult


class Evaluation(BaseModel):
    execution_id: str
    quality: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    constraint_violations: List[str] = Field(default_factory=list)
    failed: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class Metric(BaseModel):
    experiment_id: str
    agent: str
    step: Optional[int]
    name: str
    value: float
    unit: str = ""


class AdaptationOutcome(str, Enum):
    ADAPT = "ADAPT"
    DO_NOT_ADAPT = "DO_NOT_ADAPT"
    PARTIAL_ADAPT = "PARTIAL_ADAPT"
    TERMINATE = "TERMINATE"


class AdaptationDecision(BaseModel):
    """Recorded verbatim with every input value (Section 9)."""
    decision_id: str
    experiment_id: str
    agent: str
    step: int
    current_architecture_hash: str
    expected_quality: float
    expected_improvement: float
    search_cost: float
    synthesis_cost: float
    validation_cost: float
    execution_cost: float
    deadline_remaining_s: float
    resource_budget_remaining: float
    outcome: AdaptationOutcome
    rationale: str


class ArchitecturalPattern(BaseModel):
    """Structural memory record (Section 10)."""
    pattern_id: str
    environment_signature: Dict[str, float]
    task_characteristics: Dict[str, Any]
    architecture: Dict[str, Any]
    architecture_hash: str
    resource_consumption: Dict[str, float]
    quality: float
    latency_ms: float
    failures: int
    constraints: Dict[str, Any]
    adaptation_cost: float
    transfer_history: List[Dict[str, Any]] = Field(default_factory=list)
    success_conditions: List[str] = Field(default_factory=list)
    failure_conditions: List[str] = Field(default_factory=list)
    source_experiment: str = ""
    source_domain: str = ""


class Experiment(BaseModel):
    experiment_id: str
    name: str
    manifest: Dict[str, Any]
    manifest_hash: str
    git_commit: str
    seed: int
    started_at: str
    finished_at: Optional[str] = None
    status: str = "running"
    executor: str = "docker"
