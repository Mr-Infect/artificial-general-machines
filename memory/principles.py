"""Architectural principles (v0.2, spec sections 2-5).

A principle is a human-readable, inspectable statement about computational
organization: a structural pattern expressed over abstract component *roles*
and IR fields, the conditions under which it was observed, its expected effect,
and separate epistemic states for what was observed, what is hypothesized,
what has been experimentally supported and what has been contradicted.

Extraction is deterministic and rule-based (no LLM). Each rule looks at one
step's decision record (environment, selected architecture, rejected
candidates with their measured validation results, execution result) and
proposes a principle *as a hypothesis*. Validation happens only when a
principle-derived architecture is later tested under new conditions.
"""
from __future__ import annotations

import json
import math
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

from architecture.distance import architecture_distance, roles_of
from architecture.ir import ArchitectureIR
from core.db import Database, PrincipleRow, utcnow
from core.ids import new_id
from core.registry import CapabilityRegistry

PRINCIPLE_SCHEMA_VERSION = "0.2"


class PrincipleStatus(str, Enum):
    UNTESTED = "UNTESTED"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class Evidence(BaseModel):
    experiment_id: str
    domain: str
    step: int
    kind: str                 # observed | hypothesized | supported | contradicted
    summary: str
    values: Dict[str, Any] = Field(default_factory=dict)
    recorded_at: str = Field(default_factory=utcnow)


class Condition(BaseModel):
    """A readable, testable condition on the environment/task, e.g. memory_mb <= 128."""
    key: str
    op: str        # <=, >=, ==, in, between
    value: Any

    def holds(self, ctx: Dict[str, Any]) -> Optional[bool]:
        if self.key not in ctx or ctx[self.key] is None:
            return None
        x = ctx[self.key]
        try:
            if self.op == "<=":
                return x <= self.value
            if self.op == ">=":
                return x >= self.value
            if self.op == "==":
                return x == self.value
            if self.op == "in":
                return x in self.value
            if self.op == "between":
                return self.value[0] <= x <= self.value[1]
        except TypeError:
            return None
        return None

    def describe(self) -> str:
        return f"{self.key} {self.op} {self.value}"


class StructuralPattern(BaseModel):
    """Constraints an architecture must satisfy to *implement* the principle.

    All fields optional; an empty pattern matches everything (and is useless).
    """
    model_config = {"protected_namespaces": ()}
    required_roles: List[str] = Field(default_factory=list)      # roles that must be present in perception
    forbidden_roles: List[str] = Field(default_factory=list)
    min_components: Optional[int] = None
    max_components: Optional[int] = None
    perception_mode: Optional[str] = None
    reasoning_types: Optional[List[str]] = None
    model_cost_class: Optional[str] = None                        # cheap | expensive
    memory_types: Optional[List[str]] = None
    verification_types: Optional[List[str]] = None
    cheap_stage_before_verification: Optional[bool] = None       # all perception components cheap + verification present

    def matches(self, ir: ArchitectureIR, registry: CapabilityRegistry) -> Tuple[bool, List[str]]:
        a = ir.architecture
        roles = roles_of(ir, registry)
        why: List[str] = []
        for r in self.required_roles:
            if r not in roles:
                why.append(f"missing role {r}")
        for r in self.forbidden_roles:
            if r in roles:
                why.append(f"forbidden role {r} present")
        n = len(a.perception.components)
        if self.min_components is not None and n < self.min_components:
            why.append(f"needs >= {self.min_components} components")
        if self.max_components is not None and n > self.max_components:
            why.append(f"needs <= {self.max_components} components")
        if self.perception_mode and a.perception.mode != self.perception_mode:
            why.append(f"perception.mode != {self.perception_mode}")
        if self.reasoning_types and a.reasoning.type not in self.reasoning_types:
            why.append(f"reasoning.type not in {self.reasoning_types}")
        if self.model_cost_class:
            cls = "expensive" if a.reasoning.model == "large_reasoner" else "cheap"
            if cls != self.model_cost_class:
                why.append(f"reasoning model is {cls}, needs {self.model_cost_class}")
        if self.memory_types and a.memory.type not in self.memory_types:
            why.append(f"memory.type not in {self.memory_types}")
        if self.verification_types and a.verification.type not in self.verification_types:
            why.append(f"verification.type not in {self.verification_types}")
        if self.cheap_stage_before_verification is not None:
            cheap = all((registry.get("component", c) or object()).__dict__.get("params", {}).get("cost_class", "cheap") == "cheap"
                        for c in a.perception.components)
            has_v = a.verification.type != "none"
            if (cheap and has_v) != self.cheap_stage_before_verification:
                why.append("cheap-stage-before-verification constraint violated")
        return (not why), why

    def describe(self) -> str:
        parts = []
        if self.required_roles:
            parts.append("roles " + "+".join(self.required_roles))
        if self.forbidden_roles:
            parts.append("without " + "/".join(self.forbidden_roles))
        if self.min_components is not None or self.max_components is not None:
            parts.append(f"components in [{self.min_components or 1}, {self.max_components or '∞'}]")
        if self.perception_mode:
            parts.append(f"perception {self.perception_mode}")
        if self.reasoning_types:
            parts.append("reasoning " + "/".join(self.reasoning_types))
        if self.model_cost_class:
            parts.append(f"{self.model_cost_class} model")
        if self.memory_types:
            parts.append("memory " + "/".join(self.memory_types))
        if self.verification_types:
            parts.append("verification " + "/".join(self.verification_types))
        if self.cheap_stage_before_verification:
            parts.append("cheap filtering stage before verification")
        return "; ".join(parts) or "(unconstrained)"


class ArchitecturalPrinciple(BaseModel):
    id: str
    name: str
    description: str
    structural_pattern: StructuralPattern
    preconditions: List[Condition] = Field(default_factory=list)        # task-level
    resource_conditions: List[Condition] = Field(default_factory=list)  # environment resources
    objective_conditions: List[Condition] = Field(default_factory=list)
    uncertainty_conditions: List[Condition] = Field(default_factory=list)
    expected_effect: Dict[str, str] = Field(default_factory=dict)       # metric -> expectation, e.g. quality: ">= target"
    known_failures: List[str] = Field(default_factory=list)
    supporting_experiments: List[str] = Field(default_factory=list)
    contradicting_experiments: List[str] = Field(default_factory=list)
    source_architectures: List[str] = Field(default_factory=list)
    source_domains: List[str] = Field(default_factory=list)
    candidate_transfer_domains: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence_count: int = 0
    status: PrincipleStatus = PrincipleStatus.UNTESTED
    evidence: List[Evidence] = Field(default_factory=list)
    rule: str = ""
    schema_version: str = PRINCIPLE_SCHEMA_VERSION
    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)

    # ---- epistemic bookkeeping -------------------------------------------------
    def observed(self) -> List[Evidence]:
        return [e for e in self.evidence if e.kind == "observed"]

    def supported(self) -> List[Evidence]:
        return [e for e in self.evidence if e.kind == "supported"]

    def contradicted(self) -> List[Evidence]:
        return [e for e in self.evidence if e.kind == "contradicted"]

    def recompute_status(self) -> None:
        """Status policy (documented in docs/principles.md):
        - no validation evidence                      → UNTESTED
        - exactly one validation, supporting          → INCONCLUSIVE (a single experiment is never knowledge)
        - >=2 supports and contradictions <= supports/3 → SUPPORTED
        - supports > 0 and contradictions > 0         → PARTIALLY_SUPPORTED
        - >=2 contradictions and no supports          → CONTRADICTED
        - one contradiction only                      → INCONCLUSIVE
        confidence = supports / (supports + contradictions + 1), so a principle never reaches 1.0.
        Supports and contradictions are counted by distinct experiment ids.
        """
        # counted by DISTINCT experiments: many steps of one run are one test, never several
        s = len({e.experiment_id for e in self.supported()})
        c = len({e.experiment_id for e in self.contradicted()})
        if s + c == 0:
            self.status = PrincipleStatus.UNTESTED
        elif s >= 2 and c <= s / 3:
            self.status = PrincipleStatus.SUPPORTED
        elif s > 0 and c > 0:
            self.status = PrincipleStatus.PARTIALLY_SUPPORTED
        elif c >= 2 and s == 0:
            self.status = PrincipleStatus.CONTRADICTED
        else:
            self.status = PrincipleStatus.INCONCLUSIVE
        self.confidence = s / (s + c + 1)
        self.evidence_count = len(self.evidence)
        self.supporting_experiments = sorted({e.experiment_id for e in self.supported()})
        self.contradicting_experiments = sorted({e.experiment_id for e in self.contradicted()})
        self.updated_at = utcnow()

    def conditions(self) -> List[Condition]:
        return self.preconditions + self.resource_conditions + self.objective_conditions + self.uncertainty_conditions

    def applicability(self, ctx: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Fraction of conditions that hold in ctx (unknown keys count as half) and the unmet ones."""
        conds = self.conditions()
        if not conds:
            return 0.5, []
        score, unmet = 0.0, []
        for c in conds:
            h = c.holds(ctx)
            if h is None:
                score += 0.5
            elif h:
                score += 1.0
            else:
                unmet.append(c.describe())
        return score / len(conds), unmet

    def render(self) -> str:
        """Human-readable card."""
        L = [f"Principle {self.id} — {self.name} [{self.status.value}, confidence {self.confidence:.2f}, evidence {self.evidence_count}]",
             f"  {self.description}",
             f"  Structural pattern: {self.structural_pattern.describe()}"]
        for label, conds in (("Preconditions", self.preconditions), ("Resource conditions", self.resource_conditions),
                             ("Objective conditions", self.objective_conditions), ("Uncertainty conditions", self.uncertainty_conditions)):
            if conds:
                L.append(f"  {label}: " + ", ".join(c.describe() for c in conds))
        L.append("  Expected effect: " + ", ".join(f"{k} {v}" for k, v in self.expected_effect.items()))
        L.append(f"  Observed in: {', '.join(self.source_domains) or '-'}; supported by: {', '.join(self.supporting_experiments) or '-'}; "
                 f"contradicted by: {', '.join(self.contradicting_experiments) or '-'}")
        if self.known_failures:
            L.append("  Known failures: " + "; ".join(self.known_failures))
        L.append("  Candidate transfer domains: " + (", ".join(self.candidate_transfer_domains) or "-"))
        return "\n".join(L)


# ------------------------------------------------------------------------------
# condition context: the observable facts a principle's conditions are tested against

def condition_context(env: Dict[str, Any], task: Dict[str, Any], target_quality: float,
                      registry: Optional[CapabilityRegistry] = None) -> Dict[str, Any]:
    avail = env.get("available_capabilities") or []
    return {
        "memory_mb": env.get("memory_mb"), "cpu": env.get("cpu"), "latency_ms": env.get("latency_ms"),
        "network": env.get("network"), "priority": env.get("priority"), "cost_budget": env.get("cost_budget"),
        "verification_cost_factor": env.get("verification_cost_factor", 1.0),
        "expensive_model_available": ("model:large_reasoner" in avail) if avail else True,
        "task_type": task.get("type"), "domain": task.get("domain"),
        "verification_required": task.get("verification_required", False),
        "noise": task.get("noise"), "anomaly_rate": task.get("anomaly_rate"), "target_quality": target_quality,
    }


def _bucket_conditions(ctx: Dict[str, Any]) -> Dict[str, Condition]:
    """Readable ranges derived from the observed value (used when generalizing an observation)."""
    out: Dict[str, Condition] = {}
    m = ctx.get("memory_mb")
    if m is not None:
        out["memory"] = Condition(key="memory_mb", op="<=", value=128) if m <= 128 else Condition(key="memory_mb", op=">=", value=129)
    n = ctx.get("noise")
    if n is not None:
        out["noise"] = Condition(key="noise", op=">=", value=0.1) if n >= 0.1 else Condition(key="noise", op="<=", value=0.09)
    out["verification_cost"] = Condition(key="verification_cost_factor", op=">=", value=2.0) if ctx.get("verification_cost_factor", 1.0) >= 2 else Condition(key="verification_cost_factor", op="<=", value=1.99)
    out["expensive_model"] = Condition(key="expensive_model_available", op="==", value=bool(ctx.get("expensive_model_available", True)))
    out["verification_required"] = Condition(key="verification_required", op="==", value=bool(ctx.get("verification_required", False)))
    out["target"] = Condition(key="target_quality", op=">=", value=0.8) if (ctx.get("target_quality") or 0) >= 0.8 else Condition(key="target_quality", op="<=", value=0.79)
    return out


# ------------------------------------------------------------------------------
# extraction rules

class DecisionRecord(BaseModel):
    """Everything an extraction rule may look at for one step."""
    experiment_id: str
    domain: str
    step: int
    env: Dict[str, Any]
    task: Dict[str, Any]
    target_quality: float
    selected: Dict[str, Any]                  # IR dict
    selected_result: Dict[str, Any]           # quality, cost, runtime_s, memory_mb, violations, failed
    rejected: List[Dict[str, Any]] = Field(default_factory=list)   # {"architecture": IR dict, "result": {...}, "reason": str}
    execution: Optional[Dict[str, Any]] = None   # task execution result (quality, cpu, memory, cost)
    adaptation_cost: float = 0.0


def _ir(d: Dict[str, Any]) -> ArchitectureIR:
    return ArchitectureIR.from_dict(d)


def _cheap(ir: ArchitectureIR, registry: CapabilityRegistry) -> bool:
    return all((registry.get("component", c).params.get("cost_class", "cheap") if registry.get("component", c) else "cheap") == "cheap"
               for c in ir.architecture.perception.components)


RULES: Dict[str, str] = {
    "cheap_filter_before_verification": "Use cheap broad filtering before a verification stage when the unverified alternative loses quality.",
    "minimal_perception_under_tight_memory": "Under a tight memory limit, a single robust estimator with a cheap model preserves quality at lower resource estimate.",
    "ensemble_perception_under_uncertainty": "Under higher noise, combining several cheap perception roles beats any single one.",
    "cheap_model_suffices": "Prefer the cheap reasoning model when an expensive-model alternative gives no quality gain.",
    "rule_roles_for_verification_tasks": "When the task requires verification, include rule-check/consistency roles in perception.",
    "expensive_analysis_only_when_affordable": "Use an expensive analysis stage only when it beats cheap alternatives and the budget allows it.",
}


def extract_principles(rec: DecisionRecord, registry: CapabilityRegistry) -> List[ArchitecturalPrinciple]:
    """Deterministic extraction. Returns candidate principles as HYPOTHESES (status UNTESTED)."""
    sel = _ir(rec.selected)
    a = sel.architecture
    sel_q = float(rec.selected_result.get("quality", 0.0))
    ctx = condition_context(rec.env, rec.task, rec.target_quality, registry)
    buckets = _bucket_conditions(ctx)
    rejected = [(_ir(r["architecture"]), r.get("result") or {}, r.get("reason", "")) for r in rec.rejected]
    found: List[ArchitecturalPrinciple] = []

    def mk(rule: str, pattern: StructuralPattern, pre: List[Condition], res: List[Condition], obj: List[Condition],
           unc: List[Condition], effect: Dict[str, str], summary: str, values: Dict[str, Any]) -> ArchitecturalPrinciple:
        p = ArchitecturalPrinciple(id=new_id("prn"), name=rule, description=RULES[rule], structural_pattern=pattern,
                                   preconditions=pre, resource_conditions=res, objective_conditions=obj, uncertainty_conditions=unc,
                                   expected_effect=effect, source_architectures=[sel.hash()], source_domains=[rec.domain],
                                   candidate_transfer_domains=[d for d in ("network", "scientific", "planning") if d != rec.domain], rule=rule)
        p.evidence.append(Evidence(experiment_id=rec.experiment_id, domain=rec.domain, step=rec.step, kind="observed", summary=summary, values=values))
        p.evidence.append(Evidence(experiment_id=rec.experiment_id, domain=rec.domain, step=rec.step, kind="hypothesized",
                                   summary=f"Generalization: {RULES[rule]} Conditions: " + ", ".join(c.describe() for c in pre + res + obj + unc)))
        p.recompute_status()
        return p

    # Rule 1: cheap filter before verification
    if a.verification.type != "none" and _cheap(sel, registry):
        worse = [(r, res) for r, res, _ in rejected if r.architecture.verification.type == "none" and res.get("quality") is not None and res["quality"] < sel_q - 0.02]
        if worse:
            best_unverified = max(res["quality"] for _, res in worse)
            found.append(mk("cheap_filter_before_verification",
                            StructuralPattern(cheap_stage_before_verification=True, verification_types=["rule_based", "execution_based", "model_based"]),
                            [buckets["verification_required"]], [buckets["memory"], buckets["verification_cost"]], [buckets["target"]], [buckets["noise"]],
                            {"quality": "higher than the same perception without verification", "memory_mb": "no increase"},
                            f"selected {sel.name} q={sel_q:.3f} with {a.verification.type} verification; best unverified rejected q={best_unverified:.3f}",
                            {"selected_quality": sel_q, "best_unverified_quality": best_unverified, "n_rejected_unverified": len(worse)}))

    # Rule 2: minimal perception under tight memory
    if (ctx.get("memory_mb") or 1e9) <= 128 and len(a.perception.components) == 1 and a.reasoning.model != "large_reasoner" and sel_q >= rec.target_quality:
        bigger = [(r, res) for r, res, _ in rejected if len(r.architecture.perception.components) > 1]
        found.append(mk("minimal_perception_under_tight_memory",
                        StructuralPattern(required_roles=[roles_of(sel, registry)[0]], max_components=1, model_cost_class="cheap"),
                        [], [Condition(key="memory_mb", op="<=", value=128)], [buckets["target"]], [buckets["noise"]],
                        {"quality": ">= target", "memory_mb": "lower estimate than multi-component alternatives"},
                        f"single {a.perception.components[0]} met target q={sel_q:.3f} under {ctx['memory_mb']}MB; {len(bigger)} larger candidates rejected",
                        {"selected_quality": sel_q, "memory_mb": ctx["memory_mb"], "n_rejected_larger": len(bigger),
                         "best_larger_quality": max([res.get("quality", 0.0) for _, res in bigger], default=None)}))

    # Rule 3: ensemble under uncertainty
    if len(a.perception.components) >= 2 and (ctx.get("noise") or 0) >= 0.1:
        singles = [(r, res) for r, res, _ in rejected if len(r.architecture.perception.components) == 1 and res.get("quality") is not None]
        if singles and max(res["quality"] for _, res in singles) < sel_q - 0.02:
            found.append(mk("ensemble_perception_under_uncertainty",
                            StructuralPattern(min_components=2, required_roles=sorted(set(roles_of(sel, registry)))[:2], reasoning_types=["parallel", "hierarchical", "sequential"]),
                            [], [buckets["memory"]], [buckets["target"]], [Condition(key="noise", op=">=", value=0.1)],
                            {"quality": "higher than the best single-component alternative"},
                            f"ensemble of {len(a.perception.components)} beat best single (q={max(res['quality'] for _, res in singles):.3f}) with q={sel_q:.3f}",
                            {"selected_quality": sel_q, "best_single_quality": max(res["quality"] for _, res in singles), "n_components": len(a.perception.components)}))

    # Rule 4: cheap model suffices
    if a.reasoning.model != "large_reasoner":
        exp = [(r, res) for r, res, _ in rejected if r.architecture.reasoning.model == "large_reasoner" and res.get("quality") is not None]
        if exp and max(res["quality"] for _, res in exp) <= sel_q + 0.01:
            found.append(mk("cheap_model_suffices", StructuralPattern(model_cost_class="cheap"),
                            [], [buckets["memory"]], [buckets["target"]], [buckets["noise"]],
                            {"quality": ">= expensive-model alternative", "cost": "lower per batch"},
                            f"cheap model q={sel_q:.3f} >= best expensive-model candidate q={max(res['quality'] for _, res in exp):.3f}",
                            {"selected_quality": sel_q, "best_expensive_quality": max(res["quality"] for _, res in exp)}))

    # Rule 5: rule roles for verification tasks
    roles = set(roles_of(sel, registry))
    if rec.task.get("verification_required") and roles & {"rule_check", "consistency_check"}:
        without = [(r, res) for r, res, _ in rejected if not (set(roles_of(r, registry)) & {"rule_check", "consistency_check"}) and res.get("quality") is not None]
        if without and max(res["quality"] for _, res in without) < sel_q - 0.02:
            found.append(mk("rule_roles_for_verification_tasks", StructuralPattern(required_roles=sorted(roles & {"rule_check", "consistency_check"})),
                            [Condition(key="verification_required", op="==", value=True)], [], [buckets["target"]], [buckets["noise"]],
                            {"quality": "higher than perception without rule/consistency roles"},
                            f"rule roles q={sel_q:.3f} vs best without q={max(res['quality'] for _, res in without):.3f}",
                            {"selected_quality": sel_q, "best_without_quality": max(res["quality"] for _, res in without)}))

    # Rule 6: expensive analysis only when it wins
    if "expensive_analyzer" in roles or a.reasoning.model == "large_reasoner":
        cheap_alts = [(r, res) for r, res, _ in rejected if _cheap(r, registry) and r.architecture.reasoning.model != "large_reasoner" and res.get("quality") is not None]
        if cheap_alts and max(res["quality"] for _, res in cheap_alts) < sel_q - 0.05:
            found.append(mk("expensive_analysis_only_when_affordable", StructuralPattern(model_cost_class="expensive") if a.reasoning.model == "large_reasoner" else StructuralPattern(required_roles=["expensive_analyzer"]),
                            [], [Condition(key="memory_mb", op=">=", value=129), buckets["expensive_model"]], [buckets["target"]], [buckets["noise"]],
                            {"quality": "> cheap alternatives by >= 0.05", "cost": "higher"},
                            f"expensive stage q={sel_q:.3f} vs best cheap q={max(res['quality'] for _, res in cheap_alts):.3f}",
                            {"selected_quality": sel_q, "best_cheap_quality": max(res["quality"] for _, res in cheap_alts)}))
    return found


# ------------------------------------------------------------------------------
# instantiation: principle -> architecture in a target capability model

def instantiate(principle: ArchitecturalPrinciple, capability_model: Dict[str, List[str]], registry: CapabilityRegistry,
                base: Optional[ArchitectureIR] = None) -> Optional[ArchitectureIR]:
    """Build an architecture that satisfies the principle's structural pattern using only
    capabilities available in the target domain. Returns None when impossible."""
    pat = principle.structural_pattern
    comps_avail = capability_model.get("component", [])
    by_role: Dict[str, List[str]] = {}
    for c in comps_avail:
        cap = registry.get("component", c)
        by_role.setdefault(cap.params.get("role", c) if cap else c, []).append(c)
    comps: List[str] = []
    for r in pat.required_roles:
        if r not in by_role:
            return None
        comps.append(by_role[r][0])
    if pat.cheap_stage_before_verification or (pat.min_components and len(comps) < pat.min_components):
        for r, names in by_role.items():
            cap = registry.get("component", names[0])
            if r in pat.forbidden_roles or (cap and cap.params.get("cost_class") == "expensive"):
                continue
            for n in names:
                if n not in comps:
                    comps.append(n)
            target_n = pat.min_components or 2
            if len(comps) >= max(target_n, 2):
                break
    if not comps:
        if base is not None:
            comps = [c for c in base.architecture.perception.components if c in comps_avail]
        if not comps:
            pref = [r for r in ("robust_estimator", "broad_filter", "rule_check") if r in by_role]
            comps = [by_role[pref[0]][0]] if pref else comps_avail[:1]
    if pat.max_components is not None:
        comps = comps[: pat.max_components]
    if pat.forbidden_roles:
        comps = [c for c in comps if (registry.get("component", c).params.get("role") if registry.get("component", c) else c) not in pat.forbidden_roles] or comps
    n = len(comps)
    if pat.reasoning_types:
        rtype = pat.reasoning_types[0]
    elif base is not None and (n >= 2 or base.architecture.reasoning.type in ("direct", "sequential", "iterative")):
        rtype = base.architecture.reasoning.type
    else:
        rtype = "parallel" if n >= 2 else "direct"
    if rtype in ("parallel", "hierarchical") and n < 2:
        rtype = "direct"
    models = capability_model.get("model", [])
    if pat.model_cost_class == "expensive" and "large_reasoner" in models:
        model = "large_reasoner"
    else:
        model = "small_reasoner" if "small_reasoner" in models else (models[0] if models else "small_reasoner")
    vtypes = [v for v in (pat.verification_types or (["rule_based"] if pat.cheap_stage_before_verification else ["none"])) if v in capability_model.get("verification", [v])]
    vtype = vtypes[0] if vtypes else "none"
    mtypes = [m for m in (pat.memory_types or ["none"]) if m in capability_model.get("memory", [m])]
    mtype = mtypes[0] if mtypes else "none"
    body = {"perception": {"mode": pat.perception_mode or ("single" if n == 1 else "parallel"), "components": comps},
            "reasoning": {"type": rtype, "model": model, "threshold": base.architecture.reasoning.threshold if base else 0.5,
                          "iterations": 2 if rtype == "iterative" else 1},
            "memory": {"type": mtype}, "verification": {"type": vtype, "model": "small_reasoner" if vtype == "model_based" else None}}
    try:
        ir = ArchitectureIR(name=f"prn_{principle.rule[:18]}", architecture=body, metadata={"principle_id": principle.id, "principle_rule": principle.rule})
    except Exception:
        return None
    ok, _ = pat.matches(ir, registry)
    return ir if ok else None


# ------------------------------------------------------------------------------
# memory

class PrincipleMemory:
    def __init__(self, db: Database, readable: bool = True, writable: bool = True):
        self.db, self.readable, self.writable = db, readable, writable
        self.reads = self.writes = 0

    def all(self) -> List[ArchitecturalPrinciple]:
        return [ArchitecturalPrinciple.model_validate(p) for p in self.db.principles()]

    def get(self, principle_id: str) -> Optional[ArchitecturalPrinciple]:
        for p in self.all():
            if p.id == principle_id:
                return p
        return None

    def store(self, p: ArchitecturalPrinciple) -> None:
        if not self.writable:
            return
        self.writes += 1
        p.recompute_status()
        self.db.add(PrincipleRow(principle_id=p.id, name=p.name, status=p.status.value, confidence=p.confidence,
                                 evidence_count=p.evidence_count, updated_at=p.updated_at, json=p.model_dump_json()))

    def merge(self, candidate: ArchitecturalPrinciple) -> ArchitecturalPrinciple:
        """Merge a freshly extracted hypothesis into an existing principle with the same rule and
        structural pattern (evidence accumulates; conditions widen to the union). Returns the stored one."""
        for p in self.all():
            if p.rule == candidate.rule and p.structural_pattern == candidate.structural_pattern:
                p.evidence.extend(candidate.evidence)
                p.source_architectures = sorted(set(p.source_architectures) | set(candidate.source_architectures))
                p.source_domains = sorted(set(p.source_domains) | set(candidate.source_domains))
                p.candidate_transfer_domains = [d for d in ("network", "scientific", "planning") if d not in p.source_domains]
                p.recompute_status()
                self.store(p)
                return p
        self.store(candidate)
        return candidate

    def retrieve(self, ctx: Dict[str, Any], k: int = 5, exclude_experiment: Optional[str] = None,
                 min_applicability: float = 0.5) -> List[Tuple[ArchitecturalPrinciple, float, List[str]]]:
        """Principles whose conditions apply to ctx, ranked by applicability × (0.5 + confidence),
        contradicted principles last. Returns (principle, score, unmet_conditions)."""
        if not self.readable:
            return []
        self.reads += 1
        out = []
        for p in self.all():
            if exclude_experiment and all(e.experiment_id == exclude_experiment for e in p.evidence):
                continue
            app, unmet = p.applicability(ctx)
            if app < min_applicability:
                continue
            penalty = 0.25 if p.status == PrincipleStatus.CONTRADICTED else 1.0
            out.append((p, app * (0.5 + p.confidence) * penalty, unmet))
        out.sort(key=lambda t: t[1], reverse=True)
        return out[:k]


# ------------------------------------------------------------------------------
# validation

class PrincipleEvaluator:
    """Turns a test of a principle-derived architecture under NEW conditions into evidence.

    A test is *supporting* when the instantiated architecture achieved the expected effect relative
    to the best non-principle alternative evaluated under the same conditions (quality within 0.02 or
    better AND, if the principle promises a resource effect, resource estimate not worse). A test is
    *contradicting* when quality is lower by more than 0.05 or the architecture failed. Anything in
    between is recorded as inconclusive evidence and does not change the status counts.
    """

    def __init__(self, memory: PrincipleMemory):
        self.memory = memory

    def record_test(self, principle_id: str, experiment_id: str, domain: str, step: int, tested_quality: float,
                    baseline_quality: Optional[float], tested_failed: bool, tested_memory_mb: Optional[float] = None,
                    baseline_memory_mb: Optional[float] = None, extra: Optional[Dict[str, Any]] = None) -> Optional[str]:
        p = self.memory.get(principle_id)
        if p is None:
            return None
        if experiment_id in {e.experiment_id for e in p.observed()}:
            return None   # a principle cannot be validated by the experiment that produced it
        values = {"tested_quality": tested_quality, "baseline_quality": baseline_quality, "tested_failed": tested_failed,
                  "tested_memory_mb": tested_memory_mb, "baseline_memory_mb": baseline_memory_mb, **(extra or {})}
        if tested_failed:
            kind, summary = "contradicted", "principle-derived architecture failed to execute"
        elif baseline_quality is None:
            kind, summary = "inconclusive", "no baseline alternative evaluated under the same conditions"
        else:
            delta = tested_quality - baseline_quality
            resource_ok = True
            if "memory_mb" in p.expected_effect and tested_memory_mb is not None and baseline_memory_mb is not None:
                resource_ok = tested_memory_mb <= baseline_memory_mb + 1e-6
            if delta >= -0.02 and resource_ok:
                kind, summary = "supported", f"quality {tested_quality:.3f} vs baseline {baseline_quality:.3f} (Δ {delta:+.3f}); resource effect {'ok' if resource_ok else 'not met'}"
            elif delta < -0.05:
                kind, summary = "contradicted", f"quality {tested_quality:.3f} vs baseline {baseline_quality:.3f} (Δ {delta:+.3f})"
            else:
                kind, summary = "inconclusive", f"quality {tested_quality:.3f} vs baseline {baseline_quality:.3f} (Δ {delta:+.3f}) within noise band"
        p.evidence.append(Evidence(experiment_id=experiment_id, domain=domain, step=step, kind=kind, summary=summary, values=values))
        if kind == "contradicted":
            p.known_failures.append(f"{domain}/{experiment_id[-6:]}: {summary}")
        p.recompute_status()
        self.memory.store(p)
        return kind

    def evaluate_offline(self, principle: ArchitecturalPrinciple, conditions: Sequence[Dict[str, Any]], registry: CapabilityRegistry,
                         run_candidate, baseline_ir: ArchitectureIR, experiment_id: str) -> List[Dict[str, Any]]:
        """Test a principle outside an experiment: for each condition (env, task, capability_model, domain)
        instantiate, execute via ``run_candidate(ir, condition) -> (quality, failed, memory_mb)`` and compare
        with the baseline architecture. Used by tests and by scripts/validate_principles.py."""
        results = []
        for i, cond in enumerate(conditions):
            ir = instantiate(principle, cond["capability_model"], registry, base=baseline_ir)
            if ir is None:
                results.append({"condition": i, "instantiated": False})
                continue
            q, failed, mem = run_candidate(ir, cond)
            bq, bfailed, bmem = run_candidate(baseline_ir, cond)
            kind = self.record_test(principle.id, experiment_id, cond["domain"], i, q, None if bfailed else bq, failed, mem, bmem)
            results.append({"condition": i, "instantiated": True, "architecture": ir.hash(), "quality": q, "baseline_quality": bq, "evidence": kind})
        return results
