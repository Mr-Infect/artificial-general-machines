"""Architecture Intermediate Representation (Section 4).

The IR is the *only* thing an agent (or a future LLM proposer) may produce.
It never contains code. ``compiler/`` turns a validated IR into a sandbox
configuration that the generic runner in ``sandbox/runner.py`` interprets.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Literal, Optional, Tuple

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

IR_VERSION = "0.1"

PerceptionMode = Literal["single", "sequential", "parallel"]
ReasoningType = Literal["direct", "sequential", "parallel", "hierarchical", "iterative"]
MemoryType = Literal["none", "episodic", "vector", "graph"]
VerificationType = Literal["none", "rule_based", "model_based", "execution_based"]


class InputSpec(BaseModel):
    type: Literal["stream", "batch"] = "stream"
    batch_size: int = Field(200, ge=10, le=100000)


class PerceptionSpec(BaseModel):
    mode: PerceptionMode = "parallel"
    components: List[str] = Field(default_factory=lambda: ["statistical_detector"])
    window: int = Field(50, ge=5, le=5000)

    @field_validator("components")
    @classmethod
    def _non_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("perception.components must contain at least one component")
        if len(set(v)) != len(v):
            raise ValueError("perception.components must not contain duplicates")
        return v


class ReasoningSpec(BaseModel):
    type: ReasoningType = "direct"
    model: str = "small_reasoner"
    threshold: float = Field(0.5, ge=0.0, le=1.0)
    iterations: int = Field(1, ge=1, le=10)


class MemorySpec(BaseModel):
    type: MemoryType = "none"
    capacity: int = Field(500, ge=0, le=100000)


class VerificationSpec(BaseModel):
    type: VerificationType = "none"
    model: Optional[str] = None
    strictness: float = Field(0.5, ge=0.0, le=1.0)


class OutputSpec(BaseModel):
    confidence: bool = True


class ArchitectureBody(BaseModel):
    input: InputSpec = Field(default_factory=InputSpec)
    perception: PerceptionSpec = Field(default_factory=PerceptionSpec)
    reasoning: ReasoningSpec = Field(default_factory=ReasoningSpec)
    memory: MemorySpec = Field(default_factory=MemorySpec)
    verification: VerificationSpec = Field(default_factory=VerificationSpec)
    tools: List[str] = Field(default_factory=lambda: ["python"])
    output: OutputSpec = Field(default_factory=OutputSpec)


class ArchitectureIR(BaseModel):
    ir_version: str = IR_VERSION
    name: str = "unnamed"
    architecture: ArchitectureBody = Field(default_factory=ArchitectureBody)
    parent_hash: Optional[str] = None
    lineage: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("ir_version")
    @classmethod
    def _version(cls, v: str) -> str:
        if v != IR_VERSION:
            raise ValueError(f"unsupported ir_version {v!r}; supported: {IR_VERSION}")
        return v

    # --- serialization ------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(mode="json")

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=True)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArchitectureIR":
        return cls.model_validate(d)

    @classmethod
    def from_yaml(cls, text: str) -> "ArchitectureIR":
        return cls.from_dict(yaml.safe_load(text))

    # --- hashing ------------------------------------------------------
    def canonical(self) -> str:
        """Canonical form: only the structural content contributes to the hash."""
        return json.dumps({"ir_version": self.ir_version, "architecture": self.architecture.model_dump(mode="json")},
                          sort_keys=True, separators=(",", ":"))

    def hash(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()[:16]

    # --- versioning ---------------------------------------------------
    def derive(self, name: Optional[str] = None, **changes: Any) -> "ArchitectureIR":
        """Return a new version whose parent is this architecture.

        ``changes`` are dotted paths into the architecture body, e.g.
        ``derive(**{"reasoning.model": "large_reasoner"})``.
        """
        body = self.architecture.model_dump(mode="json")
        for path, value in changes.items():
            node = body
            parts = path.split(".")
            for p in parts[:-1]:
                node = node.setdefault(p, {})
            node[parts[-1]] = value
        child = ArchitectureIR(ir_version=self.ir_version, name=name or self.name,
                               architecture=ArchitectureBody.model_validate(body),
                               parent_hash=self.hash(), lineage=self.lineage + [self.hash()],
                               metadata=dict(self.metadata))
        return child


# --- comparison --------------------------------------------------------

def _flatten(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        elif isinstance(v, list):
            out[key] = tuple(sorted(map(str, v)))
        else:
            out[key] = v
    return out


def compare(a: ArchitectureIR, b: ArchitectureIR) -> Dict[str, Any]:
    """Structural diff plus a normalized distance in [0, 1].

    Distance counts differing leaf fields over the union of fields; list
    fields (components, tools) contribute their Jaccard distance instead.
    """
    fa = _flatten(a.architecture.model_dump(mode="json"))
    fb = _flatten(b.architecture.model_dump(mode="json"))
    keys = sorted(set(fa) | set(fb))
    diff: Dict[str, Tuple[Any, Any]] = {}
    total = 0.0
    for k in keys:
        va, vb = fa.get(k), fb.get(k)
        if isinstance(va, tuple) or isinstance(vb, tuple):
            sa, sb = set(va or ()), set(vb or ())
            union = sa | sb
            d = 0.0 if not union else 1 - len(sa & sb) / len(union)
        else:
            d = 0.0 if va == vb else 1.0
        if d > 0:
            diff[k] = (va, vb)
        total += d
    return {"same": not diff, "distance": total / max(1, len(keys)), "diff": diff,
            "hash_a": a.hash(), "hash_b": b.hash()}


def novelty(candidate: ArchitectureIR, known: List[ArchitectureIR]) -> float:
    """Minimum structural distance to any known architecture (1.0 if none known)."""
    if not known:
        return 1.0
    return min(compare(candidate, k)["distance"] for k in known)


def try_parse(d: Dict[str, Any]) -> Tuple[Optional[ArchitectureIR], List[str]]:
    """Schema validation returning (ir, errors) rather than raising."""
    try:
        return ArchitectureIR.from_dict(d), []
    except ValidationError as e:
        return None, [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
