"""Compile a validated Architecture IR into a sandbox execution spec (Section 4).

The compiled spec is pure data. It contains the resolved pipeline, the cost
profile of each capability (so the sandbox can account model calls, tokens
and simulated money consistently) and the resource limits. The generic
runner in ``sandbox/runner.py`` interprets it; no generated code is ever run.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from architecture.ir import ArchitectureIR
from architecture.validate import required_capabilities, validate_against_registry
from core.registry import CapabilityRegistry


class CompiledSpec(BaseModel):
    spec_version: str = "0.1"
    architecture_hash: str
    pipeline: Dict[str, Any]
    cost_profiles: Dict[str, Dict[str, float]]
    limits: Dict[str, Any]
    estimates: Dict[str, float]
    required_capabilities: List[str] = Field(default_factory=list)


class CompileError(Exception):
    pass


def _profile(cap) -> Dict[str, float]:
    return {"cost_per_call": cap.cost_per_call, "latency_ms": cap.latency_ms, "memory_mb": cap.memory_mb,
            "cpu_weight": cap.cpu_weight, "tokens_per_call": cap.tokens_per_call}


def compile_ir(ir: ArchitectureIR, registry: CapabilityRegistry, limits: Dict[str, Any]) -> CompiledSpec:
    errors = validate_against_registry(ir, registry)
    if errors:
        raise CompileError("; ".join(errors))
    a = ir.architecture
    req = required_capabilities(ir)
    profiles: Dict[str, Dict[str, float]] = {}
    for key in req:
        kind, name = key.split(":", 1)
        cap = registry.get(kind, name)
        profiles[key] = _profile(cap)

    # Static estimates used by adaptation economics and environment validation.
    base_runtime_mb = 40.0  # python interpreter footprint in the sandbox
    est_memory = base_runtime_mb + sum(p["memory_mb"] for p in profiles.values())
    calls_per_batch = 1 + (a.reasoning.iterations if a.reasoning.type == "iterative" else 0)
    verify_calls = 1 if a.verification.type == "model_based" else 0
    est_cost_batch = (profiles[f"model:{a.reasoning.model}"]["cost_per_call"] * calls_per_batch
                      + (profiles[f"model:{a.verification.model}"]["cost_per_call"] if verify_calls else 0.0)
                      + sum(p["cost_per_call"] for k, p in profiles.items() if k.startswith("tool:")))
    est_latency = sum(p["latency_ms"] for p in profiles.values()) * max(1, calls_per_batch)
    est_cpu_weight = sum(p["cpu_weight"] for p in profiles.values())

    pipeline = {
        "input": a.input.model_dump(),
        "perception": a.perception.model_dump(),
        "reasoning": a.reasoning.model_dump(),
        "memory": a.memory.model_dump(),
        "verification": a.verification.model_dump(),
        "tools": list(a.tools),
        "output": a.output.model_dump(),
    }
    return CompiledSpec(architecture_hash=ir.hash(), pipeline=pipeline, cost_profiles=profiles,
                        limits=dict(limits), required_capabilities=req,
                        estimates={"memory_mb": est_memory, "cost_per_batch": est_cost_batch,
                                   "latency_ms": est_latency, "cpu_weight": est_cpu_weight})
