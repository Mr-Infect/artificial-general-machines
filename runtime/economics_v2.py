"""Adaptation economics v0.2 (spec section 8).

    expected_gain = expected_improvement + expected_resource_benefit + expected_risk_reduction
    estimated_adaptation_cost = search + synthesis + validation + execution_overhead + failure_risk

All terms are in "quality units" (a quality gain of 0.1 is worth 0.1) so that
costs, which are money, time and risk, are converted with explicit, recorded
exchange rates. The decision record keeps every input, the exchange rates, and
after adaptation the *actual* cost and the decision error, so that later
analysis can ask whether the machine reasons correctly about its own economics.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from core.ids import new_id
from core.models import AdaptationOutcome


@dataclass
class EconomicsV2Inputs:
    current_architecture_hash: str
    current_valid: bool
    expected_quality: float               # of current architecture (0 if invalid)
    expected_improvement: float           # best predicted candidate quality - current
    expected_resource_benefit: float      # quality-units credit for predicted resource savings (e.g. memory headroom)
    expected_risk_reduction: float        # quality-units credit for reducing predicted failure risk of current arch
    search_cost_usd: float                # to evaluate the planned candidates
    synthesis_cost_usd: float
    validation_cost_usd: float
    execution_overhead_s: float           # wall seconds the adaptation will consume
    failure_risk: float                   # probability [0,1] that the adapted architecture fails (unknown candidates)
    deadline_remaining_s: float
    budget_remaining_usd: float
    target_quality: float
    priority: int = 1
    n_unevaluated_candidates: int = 0
    # exchange rates (recorded with the decision)
    usd_to_quality: float = 1.0            # 1 USD of budget == this many quality units when budget is 1 USD (scaled by remaining budget)
    seconds_to_quality: float = 1.0
    failure_penalty_quality: float = 0.3   # a failed adapted architecture costs this many quality units


@dataclass
class EconomicsV2Decision:
    decision_id: str
    experiment_id: str
    agent: str
    step: int
    outcome: str
    expected_gain: float
    estimated_adaptation_cost: float
    net_expected: float
    rationale: str
    inputs: Dict[str, Any]
    actual_adaptation_cost: Optional[float] = None    # filled after the step (quality units, same conversion)
    actual_adaptation_cost_usd: Optional[float] = None
    actual_adaptation_seconds: Optional[float] = None
    realized_gain: Optional[float] = None             # quality achieved - expected_quality of previous architecture
    decision_error: Optional[float] = None            # (realized_gain - actual_cost) - net_expected
    cost_estimate_error: Optional[float] = None       # actual_adaptation_cost - estimated_adaptation_cost
    mode: str = "economic"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def decide_v2(experiment_id: str, agent: str, step: int, x: EconomicsV2Inputs, mode: str = "economic") -> EconomicsV2Decision:
    """mode: economic (default) | always_adapt | never_adapt (ablations, spec section 25)."""
    budget = max(x.budget_remaining_usd, 1e-9)
    deadline = max(x.deadline_remaining_s, 1e-9)
    money_cost = (x.search_cost_usd + x.synthesis_cost_usd + x.validation_cost_usd) / budget * x.usd_to_quality
    time_cost = x.execution_overhead_s / deadline * x.seconds_to_quality
    risk_cost = x.failure_risk * x.failure_penalty_quality
    est_cost = money_cost + time_cost + risk_cost
    priority_weight = 1.0 + 0.25 * (x.priority - 1)
    gain = priority_weight * (max(0.0, x.expected_improvement) + x.expected_resource_benefit + x.expected_risk_reduction)
    net = gain - est_cost
    unaffordable = (x.search_cost_usd + x.synthesis_cost_usd + x.validation_cost_usd) > x.budget_remaining_usd or x.execution_overhead_s > x.deadline_remaining_s

    if x.deadline_remaining_s <= 0 or x.budget_remaining_usd <= 0:
        outcome, why = AdaptationOutcome.TERMINATE, "deadline or budget exhausted"
    elif mode == "never_adapt":
        outcome, why = (AdaptationOutcome.ADAPT if not x.current_valid else AdaptationOutcome.DO_NOT_ADAPT), "ablation: never adapt (unless current architecture is invalid)"
    elif mode == "always_adapt":
        outcome, why = (AdaptationOutcome.ADAPT if x.n_unevaluated_candidates > 0 or not x.current_valid else AdaptationOutcome.DO_NOT_ADAPT), "ablation: always adapt while unevaluated candidates exist"
    elif not x.current_valid:
        outcome, why = (AdaptationOutcome.ADAPT if not unaffordable else AdaptationOutcome.PARTIAL_ADAPT), "current architecture invalid under environment"
    elif x.n_unevaluated_candidates == 0 and x.expected_improvement <= 0:
        outcome, why = AdaptationOutcome.DO_NOT_ADAPT, "no unevaluated candidate predicted to improve on the current architecture"
    elif x.expected_quality >= x.target_quality and x.expected_improvement < 0.05 and x.expected_risk_reduction < 0.05:
        outcome, why = AdaptationOutcome.DO_NOT_ADAPT, "target met; expected gain negligible"
    elif unaffordable:
        outcome, why = (AdaptationOutcome.PARTIAL_ADAPT if x.validation_cost_usd <= x.budget_remaining_usd and x.expected_quality < x.target_quality
                        else AdaptationOutcome.DO_NOT_ADAPT), "full adaptation unaffordable"
    elif net > 0:
        outcome, why = AdaptationOutcome.ADAPT, f"net expected value {net:+.3f} > 0"
    elif net > -0.5 * est_cost:
        outcome, why = AdaptationOutcome.PARTIAL_ADAPT, f"net expected value {net:+.3f} within half of cost; partial adaptation"
    else:
        outcome, why = AdaptationOutcome.DO_NOT_ADAPT, f"net expected value {net:+.3f} <= -half cost; adaptation not economically justified"
    rationale = (f"{why} (gain={gain:.3f}: impr {x.expected_improvement:.3f} + resource {x.expected_resource_benefit:.3f} + risk {x.expected_risk_reduction:.3f}; "
                 f"cost={est_cost:.3f}: money {money_cost:.3f} + time {time_cost:.3f} + failure-risk {risk_cost:.3f}; priority×{priority_weight:.2f})")
    return EconomicsV2Decision(decision_id=new_id("dec"), experiment_id=experiment_id, agent=agent, step=step, outcome=outcome.value,
                               expected_gain=gain, estimated_adaptation_cost=est_cost, net_expected=net, rationale=rationale, inputs=asdict(x), mode=mode)


def settle(d: EconomicsV2Decision, actual_usd: float, actual_seconds: float, realized_quality: Optional[float], failed: bool) -> EconomicsV2Decision:
    """Fill in actual cost and decision error after the step, using the same exchange rates."""
    x = d.inputs
    budget = max(x["budget_remaining_usd"], 1e-9)
    deadline = max(x["deadline_remaining_s"], 1e-9)
    actual = actual_usd / budget * x["usd_to_quality"] + actual_seconds / deadline * x["seconds_to_quality"] + (x["failure_penalty_quality"] if failed else 0.0)
    d.actual_adaptation_cost, d.actual_adaptation_cost_usd, d.actual_adaptation_seconds = actual, actual_usd, actual_seconds
    d.cost_estimate_error = actual - d.estimated_adaptation_cost
    if realized_quality is not None:
        d.realized_gain = realized_quality - x["expected_quality"]
        d.decision_error = (d.realized_gain - actual) - d.net_expected
    return d
