"""Architecture validation beyond the schema (Section 4).

Two layers:
* ``validate_against_registry`` — every referenced capability must exist.
* ``validate_against_environment`` — the architecture must be runnable under
  the *current* environment profile (available capabilities, network, memory).
The second layer is what makes environmental change bite: an architecture
that was valid at t=0 may become invalid at t=20.
"""
from __future__ import annotations

from typing import Any, Dict, List

from architecture.ir import ArchitectureIR
from core.registry import CapabilityRegistry


def validate_against_registry(ir: ArchitectureIR, registry: CapabilityRegistry) -> List[str]:
    errors: List[str] = []
    a = ir.architecture
    for comp in a.perception.components:
        if not registry.has("component", comp):
            errors.append(f"unknown perception component {comp!r}")
    if not registry.has("reasoning", a.reasoning.type):
        errors.append(f"unknown reasoning type {a.reasoning.type!r}")
    if not registry.has("model", a.reasoning.model):
        errors.append(f"unknown reasoning model {a.reasoning.model!r}")
    if not registry.has("memory", a.memory.type):
        errors.append(f"unknown memory type {a.memory.type!r}")
    if not registry.has("verification", a.verification.type):
        errors.append(f"unknown verification type {a.verification.type!r}")
    if a.verification.type == "model_based":
        if not a.verification.model:
            errors.append("model_based verification requires verification.model")
        elif not registry.has("model", a.verification.model):
            errors.append(f"unknown verification model {a.verification.model!r}")
    for t in a.tools:
        if not registry.has("tool", t):
            errors.append(f"unknown tool {t!r}")
    if a.reasoning.type in ("parallel", "hierarchical") and len(a.perception.components) < 2:
        errors.append(f"{a.reasoning.type} reasoning requires at least two perception components")
    if a.reasoning.type == "iterative" and a.reasoning.iterations < 2:
        errors.append("iterative reasoning requires reasoning.iterations >= 2")
    if a.memory.type == "vector" and "embedding_model" not in _models_used(ir):
        # vector memory implicitly uses the embedding model; make it explicit for accounting
        pass
    return errors


def _models_used(ir: ArchitectureIR) -> List[str]:
    a = ir.architecture
    used = [a.reasoning.model]
    if a.verification.type == "model_based" and a.verification.model:
        used.append(a.verification.model)
    if a.memory.type == "vector":
        used.append("embedding_model")
    return used


def required_capabilities(ir: ArchitectureIR) -> List[str]:
    """Capability keys (kind:name) the architecture needs at runtime."""
    a = ir.architecture
    keys = [f"component:{c}" for c in a.perception.components]
    keys += [f"model:{m}" for m in _models_used(ir)]
    keys += [f"reasoning:{a.reasoning.type}", f"memory:{a.memory.type}", f"verification:{a.verification.type}"]
    keys += [f"tool:{t}" for t in a.tools]
    return sorted(set(keys))


def validate_against_environment(ir: ArchitectureIR, env: Dict[str, Any], registry: CapabilityRegistry,
                                 estimated_memory_mb: float) -> List[str]:
    """``env`` is the *observable* environment snapshot (see environments/profile.py)."""
    violations: List[str] = []
    available = set(env.get("available_capabilities", []))
    for key in required_capabilities(ir):
        if available and key not in available:
            violations.append(f"capability_unavailable:{key}")
    if not env.get("network", False):
        for key in required_capabilities(ir):
            kind, name = key.split(":", 1)
            cap = registry.get(kind, name)
            if cap and cap.requires_network:
                violations.append(f"network_required:{key}")
    if estimated_memory_mb > env.get("memory_mb", float("inf")):
        violations.append(f"memory_estimate_exceeds_limit:{estimated_memory_mb:.0f}>{env.get('memory_mb')}")
    if env.get("privacy") == "local_only" and "tool:search" in required_capabilities(ir):
        violations.append("privacy_violation:tool:search")
    return violations
