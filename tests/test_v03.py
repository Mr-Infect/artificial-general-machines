import json

import yaml

from environments.regimes import (COMPONENT_ALIASES, HELDOUT_SET, REGIMES, TRAINING_SET, generate, regime_at, sample_schedule)
from experiments.manifest import parse_experiment
from experiments.run import ExperimentRunner
from memory.principles import (ArchitecturalPrinciple, DecisionRecord, PrincipleMemory, StructuralPattern, applicability_decision, extract_principles)
from architecture.ir import ArchitectureIR


def test_schedules_are_seeded_and_vary():
    a, b, c = sample_schedule(TRAINING_SET, 9, 1), sample_schedule(TRAINING_SET, 9, 1), sample_schedule(TRAINING_SET, 9, 2)
    assert a == b and a != c
    assert a[0]["start_step"] == 0 and 2 <= a[1]["start_step"] <= 4 and 5 <= a[2]["start_step"] <= 7
    assert {s["regime"] for s in a} == set(TRAINING_SET)
    assert regime_at(a, 0) == a[0]["regime"] and regime_at(a, 8) == a[2]["regime"]
    assert set(HELDOUT_SET).isdisjoint(TRAINING_SET)


def test_twins_differ_on_surface_but_share_structure():
    sch = sample_schedule(HELDOUT_SET, 9, 4)
    x, y = generate("network", 900, sch, 9, 4), generate("telemetry_grid", 900, sch, 9, 4)
    assert x["labels"] == y["labels"]                         # same hidden structure
    assert x["feature_names"] != y["feature_names"] and x["records"][0] != y["records"][0]   # different surface
    assert set(x["ranges"]) != set(y["ranges"])
    z = generate("network_rules", 900, sch, 9, 4)
    assert z["feature_names"] == x["feature_names"] and z["labels"] != x["labels"]   # same surface, different structure
    for k, v in COMPONENT_ALIASES.items():
        assert v in ("statistical_detector", "anomaly_detector", "rate_detector", "range_validator", "consistency_checker",
                     "priority_filter", "risk_estimator", "capacity_forecaster", "feasibility_checker", "lookahead_planner")
    p = generate("allocation", 600, sch, 9, 4)
    assert p["base_domain"] == "planning" and p["feature_names"][1] == "worth" and p["truth"]


def test_negative_knowledge_and_decisions(registry):
    sel = ArchitectureIR(architecture={"perception": {"mode": "single", "components": ["anomaly_detector"]}, "reasoning": {"type": "direct"}})
    bad = ArchitectureIR(architecture={"perception": {"components": ["statistical_detector", "rate_detector"]}, "reasoning": {"type": "hierarchical", "model": "large_reasoner"}})
    rec = DecisionRecord(experiment_id="e1", domain="network", step=1, env={"memory_mb": 96, "available_capabilities": []},
                         task={"type": "anomaly_detection", "domain": "network", "noise": 0.25, "anomaly_rate": 0.03}, target_quality=0.9,
                         selected=sel.to_dict(), selected_result={"quality": 0.92}, rejected=[{"architecture": bad.to_dict(), "result": {"quality": 0.3, "failed": False}, "reason": "low"}])
    found = extract_principles(rec, registry)
    neg = [p for p in found if p.polarity == "negative"]
    assert neg and neg[0].rule == "failed_under_conditions" and neg[0].structural_pattern.matches(bad, registry)[0] and not neg[0].structural_pattern.matches(sel, registry)[0]
    p = ArchitecturalPrinciple(id="p", name="n", description="d", structural_pattern=StructuralPattern())
    assert applicability_decision(p, 0.1, ["x"])[0] == "IGNORE" and applicability_decision(p, 0.9, [])[0] == "TEST"
    assert applicability_decision(p, 0.6, ["memory_mb <= 128"])[0] == "ADAPT"
    p.status = p.status.CONTRADICTED
    assert applicability_decision(p, 0.9, [])[0] == "REJECT"


MANIFEST = """
experiment:
  name: v03_test
  seed: 5
  task: {type: anomaly_detection, domain: telemetry_grid, dataset_size: 900, noise: 0.1, anomaly_rate: 0.04}
  environment: {cpu: 1, memory_mb: 512, latency_ms: 5000, network: false}
  objective: {quality_threshold: 0.0}
  budget: {max_seconds: 300, max_cost: 1.0, step_timeout_s: 20}
  schedule: {steps: 9, step_seconds: 10, validation_fraction: 0.2, validation_mode: recent}
  regime: {set: heldout, oracle_points: 12}
  agents:
    - {name: search, type: search, space: auto, max_evaluations: 3}
    - {name: adaptive, type: adaptive, library: roles}
    - {name: agm_full, type: agm_v3, max_evaluations: 3, memory: {read: true, write: true, db: MDB}, principle_memory: {read: true, write: true, db: MDB}}
    - {name: agm_no_regime, type: agm_v3, max_evaluations: 3, regime_detection: false}
"""


def test_v03_runner_hidden_regimes_and_agents(tmp_db, tmp_path, results_root):
    spec = parse_experiment(yaml.safe_load(MANIFEST.replace("MDB", str(tmp_path / "m.sqlite"))))
    eid = ExperimentRunner(spec, db=tmp_db, executor_name="process", results_root=results_root, quiet=True).run()
    exp = tmp_db.experiment(eid)
    assert exp["regime"]["set"] == "heldout" and len(exp["regime"]["transitions"]) == 2 and exp["objective"]["mode"] == "regime_top_decile"
    truth = json.loads((results_root / eid / "hidden_truth.json").read_text())
    assert len(truth["objective"]["target_by_step"]) == 9
    # the regime label never reaches agents: no event payload or snapshot contains the schedule
    ev_text = (results_root / eid / "raw_events.jsonl").read_text()
    assert "start_step" not in ev_text and "regime_by_step" not in ev_text
    s = exp["summary"]
    assert s["search"]["failures"] == 0 and s["adaptive"]["failures"] == 0     # role-based baselines run in the twin vocabulary
    full = s["agm_full"]["agent_extra"]
    assert "detections" in full and "switches" in full and "decision_counts" in full and len(full["step_log"]) == 9
    assert any(d["step"] in exp["regime"]["transitions"] for d in full["detections"])
    nr = s["agm_no_regime"]["agent_extra"]
    assert nr["regime_detection"] is False
    assert any(e for e in ev_text.splitlines() if '"REGIME_CHANGE_DETECTED"' in e)
    assert len(s["agm_full"]["step_records"]) == 9 and "net_quality_mean" in s["agm_full"]
