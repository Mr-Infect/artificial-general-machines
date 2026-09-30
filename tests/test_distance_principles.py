import json

from architecture.distance import architecture_distance, novelty_levels, LEVELS
from architecture.ir import ArchitectureIR
from memory.principles import (ArchitecturalPrinciple, Condition, DecisionRecord, PrincipleEvaluator, PrincipleMemory,
                               PrincipleStatus, StructuralPattern, condition_context, extract_principles, instantiate)


def _ir(components, rtype="parallel", model="small_reasoner", verification="none", memory="none", mode=None):
    mode = mode or ("single" if len(components) == 1 else "parallel")
    if rtype in ("parallel", "hierarchical") and len(components) < 2:
        rtype = "direct"
    return ArchitectureIR(architecture={"perception": {"mode": mode, "components": components},
                                        "reasoning": {"type": rtype, "model": model},
                                        "memory": {"type": memory}, "verification": {"type": verification}})


def test_distance_components_are_separate_and_bounded(registry):
    a = _ir(["statistical_detector", "anomaly_detector"], verification="rule_based")
    b = a.derive(**{"reasoning.threshold": 0.7})
    d = architecture_distance(a, b, registry)
    assert d["structural_distance"] == 0 and d["parameter_difference"] > 0
    c = _ir(["priority_filter", "risk_estimator"], verification="rule_based")
    d = architecture_distance(a, c, registry)
    assert d["component_difference"] == 1.0 and d["role_difference"] == 0.0 and d["topology_difference"] == 0
    e = _ir(["anomaly_detector"], rtype="iterative", memory="vector")
    d = architecture_distance(a, e, registry)
    assert all(0 <= d[k] <= 1 for k in d if k != "resource_profile_difference") and d["resource_profile_difference"] is None
    assert d["control_flow_difference"] == 1.0 and d["verification_difference"] == 1.0
    assert architecture_distance(a, a, registry)["structural_distance"] == 0


def test_novelty_levels_are_reported_separately(registry):
    base = _ir(["statistical_detector", "anomaly_detector"], verification="rule_based")
    ref = [base]
    lv = novelty_levels(base.derive(**{"perception.window": 100}), ref, registry)
    assert lv["A_parameter_variation"] and lv["highest_level"] == "A_parameter_variation" and lv["syntactic_novelty"]
    lv = novelty_levels(_ir(["rate_detector", "anomaly_detector"], verification="rule_based"), ref, registry)
    assert lv["B_component_replacement"] and not lv["C_topology_modification"]
    lv = novelty_levels(_ir(["statistical_detector", "anomaly_detector"], verification="none"), ref, registry)
    assert lv["C_topology_modification"] and lv["highest_level"] in ("C_topology_modification", "E_unseen_architectural_pattern")
    lv = novelty_levels(_ir(["statistical_detector", "anomaly_detector"], rtype="iterative", verification="rule_based"), ref, registry)
    assert lv["D_new_control_organization"] and lv["E_unseen_architectural_pattern"]
    lv = novelty_levels(base, ref, registry)
    assert lv["highest_level"] is None and not lv["syntactic_novelty"]
    assert set(LEVELS) <= set(lv)
    lv = novelty_levels(_ir(["priority_filter", "risk_estimator"], verification="rule_based"), ref, registry,
                        candidate_source_domain="network", target_domain="planning")
    assert lv["transfer_novelty"] is True


def _record(selected, rejected, env=None, task=None, q=0.9, exp="exp_src"):
    env = env or {"memory_mb": 96, "cpu": 1, "latency_ms": 800, "network": False, "priority": 1, "cost_budget": 0.2, "available_capabilities": []}
    task = task or {"type": "anomaly_detection", "domain": "network", "noise": 0.1, "anomaly_rate": 0.03, "verification_required": False}
    return DecisionRecord(experiment_id=exp, domain=task["domain"], step=1, env=env, task=task, target_quality=0.85,
                          selected=selected.to_dict(), selected_result={"quality": q, "cost": 0.001},
                          rejected=[{"architecture": r.to_dict(), "result": {"quality": rq}, "reason": "lower validation quality"} for r, rq in rejected])


def test_principle_extraction_serialization_and_readability(registry):
    sel = _ir(["statistical_detector", "anomaly_detector"], verification="rule_based")
    rej = [(_ir(["statistical_detector", "anomaly_detector"]), 0.80), (_ir(["anomaly_detector"]), 0.70),
           (_ir(["statistical_detector", "anomaly_detector"], model="large_reasoner"), 0.88)]
    found = extract_principles(_record(sel, rej), registry)
    rules = {p.rule for p in found}
    assert {"cheap_filter_before_verification", "ensemble_perception_under_uncertainty", "cheap_model_suffices"} <= rules
    p = next(p for p in found if p.rule == "cheap_filter_before_verification")
    assert p.status == PrincipleStatus.UNTESTED and p.confidence == 0 and len(p.observed()) == 1
    assert {e.kind for e in p.evidence} == {"observed", "hypothesized"}
    assert "planning" in p.candidate_transfer_domains and "network" in p.source_domains
    round_trip = ArchitecturalPrinciple.model_validate(json.loads(p.model_dump_json()))
    assert round_trip == p
    card = p.render()
    assert "cheap filtering stage before verification" in card and "UNTESTED" in card


def test_principle_memory_merge_retrieve_instantiate(tmp_db, registry):
    mem = PrincipleMemory(tmp_db)
    sel = _ir(["statistical_detector", "anomaly_detector"], verification="rule_based")
    rej = [(_ir(["statistical_detector", "anomaly_detector"]), 0.80)]
    p1 = extract_principles(_record(sel, rej), registry)[0]
    p2 = extract_principles(_record(sel, rej, exp="exp_src2"), registry)[0]
    stored = mem.merge(p1)
    merged = mem.merge(p2)
    assert merged.id == stored.id and merged.evidence_count == 4 and len(mem.all()) == 1
    ctx = condition_context({"memory_mb": 100, "cpu": 1, "latency_ms": 500, "network": False, "priority": 1, "cost_budget": 0.2,
                             "available_capabilities": ["model:small_reasoner"]},
                            {"type": "planning", "domain": "planning", "noise": 0.2, "anomaly_rate": 0.0, "verification_required": False}, 0.85, registry)
    got = mem.retrieve(ctx, k=3)
    assert got and got[0][0].id == stored.id
    assert mem.retrieve(ctx, exclude_experiment="exp_src") and not PrincipleMemory(tmp_db).retrieve(ctx, exclude_experiment="exp_src", min_applicability=1.01)
    caps = {"component": ["priority_filter", "risk_estimator", "feasibility_checker", "lookahead_planner"], "model": ["small_reasoner"],
            "reasoning": ["direct", "parallel"], "memory": ["none"], "verification": ["none", "rule_based", "execution_based"], "tool": ["python"]}
    ir = instantiate(stored, caps, registry)
    assert ir is not None and ir.architecture.verification.type != "none"
    assert set(ir.architecture.perception.components) <= set(caps["component"]) and "lookahead_planner" not in ir.architecture.perception.components
    assert ir.metadata["principle_id"] == stored.id
    ok, why = stored.structural_pattern.matches(ir, registry)
    assert ok, why


def test_principle_validation_states_and_contradiction(tmp_db, registry):
    mem = PrincipleMemory(tmp_db)
    sel = _ir(["statistical_detector", "anomaly_detector"], verification="rule_based")
    p = mem.merge(extract_principles(_record(sel, [(_ir(["statistical_detector", "anomaly_detector"]), 0.80)]), registry)[0])
    ev = PrincipleEvaluator(mem)
    assert ev.record_test(p.id, "exp_src", "network", 2, 0.9, 0.8, False) is None   # own experiment cannot validate
    assert ev.record_test(p.id, "exp_t1", "scientific", 0, 0.88, 0.85, False) == "supported"
    assert mem.get(p.id).status == PrincipleStatus.INCONCLUSIVE      # a single supporting test is not knowledge
    assert ev.record_test(p.id, "exp_t2", "planning", 0, 0.80, 0.79, False) == "supported"
    assert mem.get(p.id).status == PrincipleStatus.SUPPORTED and 0 < mem.get(p.id).confidence < 1
    assert ev.record_test(p.id, "exp_t3", "planning", 1, 0.50, 0.79, False) == "contradicted"
    q = mem.get(p.id)
    assert q.status == PrincipleStatus.PARTIALLY_SUPPORTED and q.known_failures and "exp_t3" in q.contradicting_experiments
    assert ev.record_test(p.id, "exp_t4", "planning", 1, 0.75, 0.79, False) == "inconclusive"
    assert ev.record_test(p.id, "exp_t5", "planning", 1, 0.0, 0.79, True) == "contradicted"
    p2 = mem.merge(extract_principles(_record(_ir(["anomaly_detector"]), [(_ir(["statistical_detector", "anomaly_detector"]), 0.7)], q=0.9, exp="exp_x"), registry)[0])
    ev.record_test(p2.id, "exp_c1", "planning", 0, 0.4, 0.8, False); ev.record_test(p2.id, "exp_c2", "planning", 0, 0.3, 0.8, False)
    assert mem.get(p2.id).status == PrincipleStatus.CONTRADICTED
    ctx = condition_context({"memory_mb": 100, "available_capabilities": []}, {"domain": "planning", "noise": 0.2}, 0.85)
    ranked = mem.retrieve(ctx, k=5)
    assert ranked[-1][0].id == p2.id   # contradicted principles rank last
    cond = Condition(key="memory_mb", op="<=", value=128)
    assert cond.holds({"memory_mb": 64}) and not cond.holds({"memory_mb": 512}) and cond.holds({}) is None
