"""Experiment manifests (Section 14): YAML in, validated Pydantic out."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from environments.profile import EnvironmentEvent

ROOT = Path(__file__).resolve().parent.parent


class TaskSpec(BaseModel):
    type: str = "anomaly_detection"
    domain: str = "network"
    dataset_size: int = 2000
    noise: float = 0.05
    anomaly_rate: float = 0.03
    verification_required: bool = False
    priority: int = 1


class EnvSpec(BaseModel):
    cpu: float = 1.0
    memory_mb: int = 512
    latency_ms: int = 2000
    network: bool = False
    privacy: str = "local_only"
    energy_budget: float = 1.0
    available_capabilities: Any = "all"   # "all" or a list of kind:name keys
    verification_cost_factor: float = 1.0


class ObjectiveSpec(BaseModel):
    quality_threshold: float = 0.85


class BudgetSpec(BaseModel):
    max_seconds: float = 120.0
    max_cost: float = 0.5
    step_timeout_s: float = 30.0


class ScheduleSpec(BaseModel):
    steps: int = 5
    step_seconds: float = 10.0
    validation_fraction: float = 0.2


class AgentSpec(BaseModel):
    name: str
    type: str
    model_config = {"extra": "allow"}


class ExperimentSpec(BaseModel):
    name: str
    description: str = ""
    seed: int = 42
    repeats: int = 1
    executor: Optional[str] = None
    task: TaskSpec = Field(default_factory=TaskSpec)
    environment: EnvSpec = Field(default_factory=EnvSpec)
    objective: ObjectiveSpec = Field(default_factory=ObjectiveSpec)
    budget: BudgetSpec = Field(default_factory=BudgetSpec)
    schedule: ScheduleSpec = Field(default_factory=ScheduleSpec)
    events: List[EnvironmentEvent] = Field(default_factory=list)
    agents: List[AgentSpec] = Field(default_factory=lambda: [AgentSpec(name="fixed", type="fixed"), AgentSpec(name="adaptive", type="adaptive")])
    memory_db: Optional[str] = None    # shared structural-memory database (suite-level override)
    tags: List[str] = Field(default_factory=list)


class SuiteSpec(BaseModel):
    name: str
    description: str = ""
    memory_db: Optional[str] = None
    experiments: List[Any]   # inline experiment dicts or paths to manifests


def manifest_hash(d: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]


def load_manifest(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return yaml.safe_load(p.read_text())


def parse_experiment(raw: Dict[str, Any]) -> ExperimentSpec:
    body = raw.get("experiment", raw)
    return ExperimentSpec.model_validate(body)


def parse_suite(raw: Dict[str, Any]) -> SuiteSpec:
    return SuiteSpec.model_validate(raw["suite"])


def expand_suite(suite: SuiteSpec, base_dir: Path) -> List[ExperimentSpec]:
    specs: List[ExperimentSpec] = []
    for item in suite.experiments:
        if isinstance(item, str):
            p = Path(item)
            raw = load_manifest(p if p.is_absolute() else (base_dir / p if (base_dir / p).exists() else p))
            spec = parse_experiment(raw)
        else:
            spec = parse_experiment(item)
        if suite.memory_db and not spec.memory_db:
            spec = spec.model_copy(update={"memory_db": suite.memory_db})
        specs.append(spec)
    return specs
