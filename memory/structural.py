"""Structural memory (Section 10): architectural experience, not conversation.

Patterns are indexed by an environment signature and task characteristics.
Retrieval is by structural/environmental similarity so that experience from
one domain can be *offered* in another; whether it helps is measured, not
assumed.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.db import Database, PatternRow
from core.ids import new_id
from core.models import ArchitecturalPattern

SIGNATURE_KEYS = ["cpu", "log_memory", "log_latency", "network", "priority", "log_cost_budget", "n_capabilities"]


def environment_signature(env: Dict[str, Any]) -> Dict[str, float]:
    return {
        "cpu": float(env.get("cpu", 1.0)),
        "log_memory": math.log2(max(1.0, float(env.get("memory_mb", 512)))),
        "log_latency": math.log10(max(1.0, float(env.get("latency_ms", 1000)))),
        "network": 1.0 if env.get("network") else 0.0,
        "priority": float(env.get("priority", 1)),
        "log_cost_budget": math.log10(max(1e-4, float(env.get("cost_budget", 0.1)))),
        "n_capabilities": float(len(env.get("available_capabilities", []))),
    }


def task_characteristics(task: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": task.get("type"), "domain": task.get("domain"), "anomaly_rate": task.get("anomaly_rate"),
            "noise": task.get("noise"), "verification_required": task.get("verification_required", False),
            "accuracy_requirement": task.get("accuracy_requirement")}


# Scale factors so no single signature dimension dominates.
_SCALE = {"cpu": 2.0, "log_memory": 3.0, "log_latency": 1.5, "network": 1.0, "priority": 3.0, "log_cost_budget": 1.5, "n_capabilities": 10.0}


def env_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    d2 = sum(((a.get(k, 0.0) - b.get(k, 0.0)) / _SCALE[k]) ** 2 for k in SIGNATURE_KEYS)
    return 1.0 / (1.0 + math.sqrt(d2))


def task_similarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    s = 0.0
    s += 0.4 if a.get("type") == b.get("type") else 0.0
    s += 0.2 if a.get("domain") == b.get("domain") else 0.0
    s += 0.2 if a.get("verification_required") == b.get("verification_required") else 0.0
    ra, rb = a.get("anomaly_rate") or 0.0, b.get("anomaly_rate") or 0.0
    s += 0.2 * (1.0 - min(1.0, abs(ra - rb) / 0.1))
    return s


class StructuralMemory:
    def __init__(self, db: Database, readable: bool = True, writable: bool = True):
        self.db = db
        self.readable = readable
        self.writable = writable
        self.reads = 0
        self.writes = 0

    @classmethod
    def open(cls, path: Optional[str], readable: bool = True, writable: bool = True) -> "StructuralMemory":
        return cls(Database(Path(path)) if path else Database(), readable=readable, writable=writable)

    def store(self, pattern: ArchitecturalPattern) -> None:
        if not self.writable:
            return
        self.writes += 1
        self.db.add(PatternRow(pattern_id=pattern.pattern_id, architecture_hash=pattern.architecture_hash,
                               source_experiment=pattern.source_experiment, source_domain=pattern.source_domain,
                               quality=pattern.quality, json=pattern.model_dump_json()))

    def all(self) -> List[ArchitecturalPattern]:
        return [ArchitecturalPattern.model_validate(p) for p in self.db.patterns()]

    def retrieve(self, env: Dict[str, Any], task: Dict[str, Any], k: int = 5,
                 exclude_experiment: Optional[str] = None) -> List[Tuple[ArchitecturalPattern, float]]:
        """Return up to k (pattern, similarity) pairs, best first.

        Score = env similarity * (0.5 + 0.5 task similarity) * quality. Patterns
        from the running experiment can be excluded to prevent self-retrieval.
        """
        if not self.readable:
            return []
        self.reads += 1
        sig = environment_signature(env)
        tc = task_characteristics(task)
        scored = []
        for p in self.all():
            if exclude_experiment and p.source_experiment == exclude_experiment:
                continue
            s = env_similarity(sig, p.environment_signature) * (0.5 + 0.5 * task_similarity(tc, p.task_characteristics))
            scored.append((p, s * max(0.0, p.quality)))
        scored.sort(key=lambda x: x[1], reverse=True)
        # de-duplicate by architecture hash keeping the best-scoring instance
        seen, out = set(), []
        for p, s in scored:
            if p.architecture_hash in seen:
                continue
            seen.add(p.architecture_hash)
            out.append((p, s))
            if len(out) >= k:
                break
        return out

    def record_transfer(self, pattern_id: str, target_experiment: str, target_domain: str, outcome_quality: float) -> None:
        """Append a transfer event to a pattern's history (for later analysis)."""
        if not self.writable:
            return
        for raw in self.db.patterns():
            if raw["pattern_id"] == pattern_id:
                p = ArchitecturalPattern.model_validate(raw)
                p.transfer_history.append({"experiment": target_experiment, "domain": target_domain, "quality": outcome_quality})
                self.store(p)
                return


def make_pattern(env: Dict[str, Any], task: Dict[str, Any], architecture: Dict[str, Any], architecture_hash: str,
                 resources: Dict[str, float], quality: float, latency_ms: float, failures: int,
                 constraints: Dict[str, Any], adaptation_cost: float, experiment_id: str, domain: str,
                 target_quality: float) -> ArchitecturalPattern:
    success = [f"quality>={target_quality}"] if quality >= target_quality else []
    failure = [] if quality >= target_quality else [f"quality<{target_quality}"]
    if failures:
        failure.append("execution_failures")
    if resources.get("memory_mb", 0) > env.get("memory_mb", 1e9):
        failure.append("memory_over_limit")
    return ArchitecturalPattern(pattern_id=new_id("pat"), environment_signature=environment_signature(env),
                                task_characteristics=task_characteristics(task), architecture=architecture,
                                architecture_hash=architecture_hash, resource_consumption=resources, quality=quality,
                                latency_ms=latency_ms, failures=failures, constraints=constraints,
                                adaptation_cost=adaptation_cost, success_conditions=success,
                                failure_conditions=failure, source_experiment=experiment_id, source_domain=domain)
