from core.models import AdaptationOutcome
from memory.structural import StructuralMemory, environment_signature, make_pattern
from runtime.economics import EconomicsInputs, decide


def _inputs(**kw):
    base = dict(current_architecture_hash="h", expected_quality=0.7, expected_improvement=0.2, search_cost=0.01,
                synthesis_cost=0.0, validation_cost=0.002, execution_cost=0.001, deadline_remaining_s=50, resource_budget_remaining=0.2,
                target_quality=0.85, priority=1, current_valid=True, expected_adaptation_seconds=2.0)
    base.update(kw)
    return EconomicsInputs(**base)


def test_decisions_cover_all_outcomes():
    assert decide("e", "a", 0, _inputs()).outcome == AdaptationOutcome.ADAPT
    assert decide("e", "a", 0, _inputs(expected_quality=0.9, expected_improvement=0.01)).outcome == AdaptationOutcome.DO_NOT_ADAPT
    assert decide("e", "a", 0, _inputs(expected_improvement=0.01, search_cost=0.1)).outcome == AdaptationOutcome.DO_NOT_ADAPT
    assert decide("e", "a", 0, _inputs(search_cost=0.5)).outcome == AdaptationOutcome.PARTIAL_ADAPT
    assert decide("e", "a", 0, _inputs(deadline_remaining_s=0)).outcome == AdaptationOutcome.TERMINATE
    assert decide("e", "a", 0, _inputs(current_valid=False)).outcome == AdaptationOutcome.ADAPT
    d = decide("e", "a", 3, _inputs())
    assert d.search_cost == 0.01 and d.step == 3 and "cost_ratio" in d.rationale


def test_structural_memory_retrieval_prefers_similar_environments(tmp_db):
    mem = StructuralMemory(tmp_db)
    task = {"type": "anomaly_detection", "domain": "network", "anomaly_rate": 0.03, "noise": 0.05}
    env_small = {"cpu": 1, "memory_mb": 128, "latency_ms": 500, "network": False, "priority": 1, "cost_budget": 0.1, "available_capabilities": ["a"]}
    env_big = {"cpu": 4, "memory_mb": 4096, "latency_ms": 5000, "network": True, "priority": 1, "cost_budget": 1.0, "available_capabilities": ["a", "b"]}
    arch = {"ir_version": "0.1", "name": "x", "architecture": {}}
    for env, h, q in ((env_small, "small", 0.9), (env_big, "big", 0.9)):
        mem.store(make_pattern(env, task, arch, h, {"cpu_time_s": 1}, q, 100, 0, {}, 0.0, "exp1", "network", 0.85))
    got = mem.retrieve(env_small, task, k=2)
    assert [p.architecture_hash for p, _ in got] == ["small", "big"]
    assert mem.retrieve(env_small, task, exclude_experiment="exp1") == []
    other = {**task, "domain": "scientific", "type": "scientific_verification"}
    assert mem.retrieve(env_small, other, k=1)[0][0].architecture_hash == "small"
    mem.record_transfer(got[0][0].pattern_id, "exp2", "scientific", 0.8)
    assert mem.all()[0].transfer_history or mem.all()[1].transfer_history
    assert set(environment_signature(env_small)) == {"cpu", "log_memory", "log_latency", "network", "priority", "log_cost_budget", "n_capabilities"}
