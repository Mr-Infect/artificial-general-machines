"""Architecture distance and novelty levels (v0.2, spec sections 9 and 10).

``architecture_distance(a, b, registry)`` returns a dictionary of separately
measured differences plus one documented weighted aggregate. ``novelty_levels``
classifies a candidate relative to a reference set on five separate levels;
no single arbitrary novelty score is used.

Distances are in [0, 1]. Definitions (both architectures' bodies are the IR):

component_difference     Jaccard distance of perception component *names*.
role_difference          Jaccard distance of the abstract *roles* of those components
                         (roles come from the registry; this is what makes cross-domain
                         comparison possible when vocabularies differ).
topology_difference      Hamming distance over the stage layout: perception.mode,
                         component-count bucket (1 / 2 / 3+), memory stage present,
                         verification stage present.
control_flow_difference  0 if reasoning.type equal; 0.5 if both single-pass or both
                         multi-pass (direct/sequential/parallel vs hierarchical/iterative);
                         1 otherwise; plus 0.25 if the iteration count differs (capped at 1).
memory_strategy_difference     0 if memory.type equal, 0.5 if both non-none, else 1.
verification_difference        0 if types equal, 0.5 if both non-none, else 1; +0.25 if the
                               verification model differs (capped at 1).
parallelism_difference   Hamming distance over (perception parallel?, reasoning parallel?).
parameter_difference     mean normalised absolute difference over threshold, window (log),
                         batch_size (log), strictness, iterations.
resource_profile_difference    mean normalised difference of compiled estimates
                               (memory_mb, cost_per_batch, latency_ms, cpu_weight),
                               each as |a-b| / max(a, b).
structural_distance      weighted sum: role 0.20, component 0.10, topology 0.20, control 0.20,
                         memory 0.10, verification 0.10, parallelism 0.10.
                         Parameters and resource profile are reported but NOT part of the
                         structural distance, so parameter tweaks have structural distance 0.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from architecture.ir import ArchitectureIR
from core.registry import CapabilityRegistry

MULTI_PASS = {"hierarchical", "iterative"}
PARALLEL_REASONING = {"parallel", "hierarchical"}
WEIGHTS = {"role_difference": 0.20, "component_difference": 0.10, "topology_difference": 0.20,
           "control_flow_difference": 0.20, "memory_strategy_difference": 0.10,
           "verification_difference": 0.10, "parallelism_difference": 0.10}


def _jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    sa, sb = set(a), set(b)
    u = sa | sb
    return 0.0 if not u else 1 - len(sa & sb) / len(u)


def roles_of(ir: ArchitectureIR, registry: CapabilityRegistry) -> List[str]:
    out = []
    for c in ir.architecture.perception.components:
        cap = registry.get("component", c)
        out.append(cap.params.get("role", c) if cap else c)
    return out


def topology_signature(ir: ArchitectureIR) -> Tuple[str, str, bool, bool]:
    a = ir.architecture
    n = len(a.perception.components)
    bucket = "1" if n == 1 else "2" if n == 2 else "3+"
    return (a.perception.mode, bucket, a.memory.type != "none", a.verification.type != "none")


def control_signature(ir: ArchitectureIR) -> Tuple[str, int]:
    return (ir.architecture.reasoning.type, ir.architecture.reasoning.iterations)


def pattern_signature(ir: ArchitectureIR, registry: CapabilityRegistry) -> Tuple:
    """The abstract architectural pattern: roles, topology, control class, memory, verification."""
    a = ir.architecture
    return (tuple(sorted(set(roles_of(ir, registry)))), topology_signature(ir), a.reasoning.type,
            a.memory.type, a.verification.type)


def _hamming(a: Sequence[Any], b: Sequence[Any]) -> float:
    return sum(1 for x, y in zip(a, b) if x != y) / max(1, len(a))


def _norm_diff(x: float, y: float) -> float:
    m = max(abs(x), abs(y))
    return 0.0 if m == 0 else abs(x - y) / m


def architecture_distance(a: ArchitectureIR, b: ArchitectureIR, registry: CapabilityRegistry,
                          estimates_a: Optional[Dict[str, float]] = None,
                          estimates_b: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    A, B = a.architecture, b.architecture
    d: Dict[str, float] = {}
    d["component_difference"] = _jaccard(A.perception.components, B.perception.components)
    d["role_difference"] = _jaccard(roles_of(a, registry), roles_of(b, registry))
    d["topology_difference"] = _hamming(topology_signature(a), topology_signature(b))
    if A.reasoning.type == B.reasoning.type:
        cf = 0.0
    elif (A.reasoning.type in MULTI_PASS) == (B.reasoning.type in MULTI_PASS):
        cf = 0.5
    else:
        cf = 1.0
    if A.reasoning.iterations != B.reasoning.iterations:
        cf = min(1.0, cf + 0.25)
    d["control_flow_difference"] = cf
    if A.memory.type == B.memory.type:
        d["memory_strategy_difference"] = 0.0
    elif A.memory.type != "none" and B.memory.type != "none":
        d["memory_strategy_difference"] = 0.5
    else:
        d["memory_strategy_difference"] = 1.0
    if A.verification.type == B.verification.type:
        vd = 0.0
    elif A.verification.type != "none" and B.verification.type != "none":
        vd = 0.5
    else:
        vd = 1.0
    if A.verification.model != B.verification.model:
        vd = min(1.0, vd + 0.25)
    d["verification_difference"] = vd
    d["parallelism_difference"] = _hamming((A.perception.mode == "parallel", A.reasoning.type in PARALLEL_REASONING),
                                           (B.perception.mode == "parallel", B.reasoning.type in PARALLEL_REASONING))
    params = [abs(A.reasoning.threshold - B.reasoning.threshold),
              abs(math.log2(A.perception.window) - math.log2(B.perception.window)) / 10.0,
              abs(math.log2(A.input.batch_size) - math.log2(B.input.batch_size)) / 14.0,
              abs(A.verification.strictness - B.verification.strictness),
              abs(A.reasoning.iterations - B.reasoning.iterations) / 9.0]
    d["parameter_difference"] = min(1.0, sum(params) / len(params))
    if estimates_a and estimates_b:
        keys = ["memory_mb", "cost_per_batch", "latency_ms", "cpu_weight"]
        d["resource_profile_difference"] = sum(_norm_diff(estimates_a[k], estimates_b[k]) for k in keys) / len(keys)
    else:
        d["resource_profile_difference"] = float("nan")
    d["structural_distance"] = sum(WEIGHTS[k] * d[k] for k in WEIGHTS)
    return d


LEVELS = ["A_parameter_variation", "B_component_replacement", "C_topology_modification",
          "D_new_control_organization", "E_unseen_architectural_pattern"]


def novelty_levels(candidate: ArchitectureIR, reference: Sequence[ArchitectureIR], registry: CapabilityRegistry,
                   reference_perf: Optional[Dict[str, float]] = None, candidate_perf: Optional[float] = None,
                   candidate_source_domain: Optional[str] = None, target_domain: Optional[str] = None) -> Dict[str, Any]:
    """Classify a candidate relative to a reference set.

    Returns the five boundary levels (each True/False), the highest level crossed, and the four
    separate novelty kinds:
      syntactic  - hash not present in the reference set
      structural - min structural_distance to the reference set (0 if none crossed)
      functional - |candidate quality - quality of nearest reference| when both known, else None
      transfer   - candidate came from a different domain's memory AND is structurally distinct
                   from every reference (None when source domain unknown)
    Level definitions (relative to the *nearest* reference by structural distance):
      A  same pattern signature, only parameters differ
      B  roles/components differ, topology and control identical
      C  topology differs (stage layout), control organization identical
      D  control organization (reasoning type class) differs from ALL references
      E  pattern signature (roles+topology+control+memory+verification) not present in ANY reference
    """
    out: Dict[str, Any] = {k: False for k in LEVELS}
    h = candidate.hash()
    hashes = {r.hash() for r in reference}
    out["syntactic_novelty"] = h not in hashes
    if not reference:
        out.update({"structural_novelty": 1.0, "highest_level": "E_unseen_architectural_pattern", "nearest_hash": None,
                    "functional_novelty": None, "transfer_novelty": None})
        out["E_unseen_architectural_pattern"] = True
        return out
    dists = [(architecture_distance(candidate, r, registry), r) for r in reference]
    dmin, nearest = min(dists, key=lambda t: t[0]["structural_distance"])
    out["structural_novelty"] = dmin["structural_distance"]
    out["nearest_hash"] = nearest.hash()
    out["nearest_distance"] = {k: v for k, v in dmin.items()}
    same_pattern = pattern_signature(candidate, registry) == pattern_signature(nearest, registry)
    if same_pattern and dmin["structural_distance"] == 0 and h != nearest.hash():
        out["A_parameter_variation"] = True
    if (dmin["role_difference"] > 0 or dmin["component_difference"] > 0) and dmin["topology_difference"] == 0 and dmin["control_flow_difference"] == 0:
        out["B_component_replacement"] = True
    if dmin["topology_difference"] > 0 and dmin["control_flow_difference"] == 0:
        out["C_topology_modification"] = True
    ref_controls = {control_signature(r)[0] for r in reference}
    if candidate.architecture.reasoning.type not in ref_controls:
        out["D_new_control_organization"] = True
    ref_patterns = {pattern_signature(r, registry) for r in reference}
    if pattern_signature(candidate, registry) not in ref_patterns:
        out["E_unseen_architectural_pattern"] = True
    highest = None
    for lvl in reversed(LEVELS):
        if out[lvl]:
            highest = lvl
            break
    out["highest_level"] = highest
    if reference_perf and candidate_perf is not None and nearest.hash() in reference_perf:
        out["functional_novelty"] = abs(candidate_perf - reference_perf[nearest.hash()])
    else:
        out["functional_novelty"] = None
    if candidate_source_domain is not None and target_domain is not None:
        out["transfer_novelty"] = bool(candidate_source_domain != target_domain and dmin["structural_distance"] > 0)
    else:
        out["transfer_novelty"] = None
    return out
