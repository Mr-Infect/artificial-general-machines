"""Adaptation economics (Section 9).

``decide`` turns explicit cost and benefit estimates into one of four
outcomes and returns the full record so the decision can be audited. The
policy is deliberately simple and parameterized; the point is that the
system *can* conclude adaptation is not worth it.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.ids import new_id
from core.models import AdaptationDecision, AdaptationOutcome


@dataclass
class EconomicsInputs:
    current_architecture_hash: str
    expected_quality: float          # of the current architecture under current env (0 if invalid)
    expected_improvement: float      # best-case quality gain from adapting
    search_cost: float               # simulated USD to evaluate candidates
    synthesis_cost: float            # simulated USD to generate candidates
    validation_cost: float           # simulated USD to validate the chosen candidate
    execution_cost: float            # simulated USD per task step with the current architecture
    deadline_remaining_s: float
    resource_budget_remaining: float  # simulated USD
    target_quality: float
    priority: int = 1
    current_valid: bool = True
    expected_adaptation_seconds: float = 0.0


def decide(experiment_id: str, agent: str, step: int, x: EconomicsInputs,
           benefit_scale: float = 1.0) -> AdaptationDecision:
    total_adapt_cost = x.search_cost + x.synthesis_cost + x.validation_cost
    budget = max(x.resource_budget_remaining, 1e-9)
    cost_ratio = total_adapt_cost / budget
    time_ratio = x.expected_adaptation_seconds / max(x.deadline_remaining_s, 1e-9)
    priority_weight = 1.0 + 0.25 * (x.priority - 1)
    benefit = benefit_scale * priority_weight * max(0.0, x.expected_improvement)
    price = cost_ratio + time_ratio

    if x.deadline_remaining_s <= 0 or x.resource_budget_remaining <= 0:
        outcome, why = AdaptationOutcome.TERMINATE, "deadline or budget exhausted"
    elif not x.current_valid:
        if total_adapt_cost <= x.resource_budget_remaining and x.expected_adaptation_seconds <= x.deadline_remaining_s:
            outcome, why = AdaptationOutcome.ADAPT, "current architecture invalid under environment"
        else:
            outcome, why = AdaptationOutcome.PARTIAL_ADAPT, "current architecture invalid; full search unaffordable"
    elif x.expected_quality >= x.target_quality and x.expected_improvement < 0.05:
        outcome, why = AdaptationOutcome.DO_NOT_ADAPT, "target met; expected improvement negligible"
    elif total_adapt_cost > x.resource_budget_remaining or x.expected_adaptation_seconds > x.deadline_remaining_s:
        if x.validation_cost <= x.resource_budget_remaining and x.expected_quality < x.target_quality:
            outcome, why = AdaptationOutcome.PARTIAL_ADAPT, "full adaptation unaffordable; cheap partial adaptation allowed"
        else:
            outcome, why = AdaptationOutcome.DO_NOT_ADAPT, "adaptation unaffordable"
    elif benefit > price:
        outcome, why = AdaptationOutcome.ADAPT, f"benefit {benefit:.3f} > price {price:.3f}"
    elif benefit > 0.5 * price:
        outcome, why = AdaptationOutcome.PARTIAL_ADAPT, f"benefit {benefit:.3f} within half of price {price:.3f}"
    else:
        outcome, why = AdaptationOutcome.DO_NOT_ADAPT, f"benefit {benefit:.3f} <= half of price {price:.3f}"

    return AdaptationDecision(
        decision_id=new_id("dec"), experiment_id=experiment_id, agent=agent, step=step,
        current_architecture_hash=x.current_architecture_hash, expected_quality=x.expected_quality,
        expected_improvement=x.expected_improvement, search_cost=x.search_cost, synthesis_cost=x.synthesis_cost,
        validation_cost=x.validation_cost, execution_cost=x.execution_cost,
        deadline_remaining_s=x.deadline_remaining_s, resource_budget_remaining=x.resource_budget_remaining,
        outcome=outcome, rationale=f"{why} (cost_ratio={cost_ratio:.3f}, time_ratio={time_ratio:.3f}, priority_weight={priority_weight:.2f})")
