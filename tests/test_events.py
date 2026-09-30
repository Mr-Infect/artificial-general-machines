import json

import yaml

from experiments.manifest import parse_experiment
from experiments.run import ExperimentRunner
from observability.events import Event, EventType, PIPELINE, STAGE_OF, explanations, fold_state, load_events, verify_ordering

MANIFEST = """
experiment:
  name: test_events
  seed: 9
  task: {type: anomaly_detection, domain: network, dataset_size: 600, noise: 0.1, anomaly_rate: 0.04}
  environment: {cpu: 1, memory_mb: 512, latency_ms: 5000, network: true}
  objective: {quality_threshold: 0.8}
  budget: {max_seconds: 60, max_cost: 0.2, step_timeout_s: 20}
  schedule: {steps: 3, step_seconds: 10, validation_fraction: 0.25}
  events:
    - {t: 10, type: memory_reduction, params: {memory_mb: 80}}
    - {t: 20, type: capability_removal, params: {capabilities: [model:large_reasoner]}}
  agents:
    - {name: fixed, type: fixed, architecture: {perception: {components: [statistical_detector, anomaly_detector]}, reasoning: {type: hierarchical, model: large_reasoner}}}
    - {name: agm_v2, type: agm_v2, max_evaluations: 3, memory: {read: true, write: true, db: MEMDB}, principle_memory: {read: true, write: true, db: MEMDB}}
"""


def _run(tmp_db, tmp_path, results_root):
    spec = parse_experiment(yaml.safe_load(MANIFEST.replace("MEMDB", str(tmp_path / "mem.sqlite"))))
    return ExperimentRunner(spec, db=tmp_db, executor_name="process", results_root=results_root, quiet=True).run(), spec


def test_event_schema_ordering_and_replay(tmp_db, tmp_path, results_root):
    eid, spec = _run(tmp_db, tmp_path, results_root)
    path = results_root / eid / "raw_events.jsonl"
    events = load_events(path)
    assert verify_ordering(events) == []
    runs = {e.run_id for e in events}
    assert runs == {f"{eid}.fixed", f"{eid}.agm_v2"}
    for e in events:
        assert Event.model_validate_json(e.model_dump_json()) == e      # schema round trip
        assert e.stage in PIPELINE
    assert set(STAGE_OF) == set(EventType)
    # DB copy matches the file copy exactly, in order
    for run in runs:
        from_db = [Event.model_validate(d) for d in tmp_db.events(run)]
        from_file = [e for e in events if e.run_id == run]
        assert [e.seq for e in from_db] == list(range(len(from_file))) and from_db == from_file
    fixed = [e for e in events if e.agent == "fixed"]
    types = [e.event_type for e in fixed]
    assert types[0] == EventType.RUN_STARTED and types[-1] == EventType.RUN_COMPLETED
    assert EventType.CONSTRAINT_CHANGED in types and EventType.VALIDATION_FAILED in types and EventType.EXECUTION_FAILED in types
    st = fold_state(fixed)
    assert st["completed"] and st["counters"]["failures"] == 2 and len(st["failures"]) >= 2 and st["environment"]["memory_mb"] == 80
    # state at an earlier point differs from the final state and is reproducible
    mid = fold_state(fixed, upto=len(fixed) // 2)
    assert not mid["completed"] and mid["last_seq"] == len(fixed) // 2 and fold_state(fixed, upto=len(fixed) // 2) == mid
    agm = [e for e in events if e.agent == "agm_v2"]
    at = [e.event_type for e in agm]
    for t in (EventType.CAPABILITY_REQUIREMENT_INFERRED, EventType.PRINCIPLE_RETRIEVED, EventType.ARCHITECTURE_GENERATED,
              EventType.ARCHITECTURE_SELECTED, EventType.ADAPTATION_DECISION, EventType.RESULT_EVALUATED):
        assert t in at, t
    assert any(e.candidate_architectures for e in agm if e.event_type == EventType.ARCHITECTURE_GENERATED)
    sa = fold_state(agm)
    assert sa["current_architecture"] and sa["current_architecture"]["alias"].startswith("A-") and sa["decisions"]
    assert sa["counters"]["architecture_evaluations"] == tmp_db.experiment(eid)["summary"]["agm_v2"]["architecture_evaluations"]
    ex = explanations(agm)
    assert len(ex) == 3 and all(k in ex[0] for k in ("observed", "retrieved", "considered", "rejected", "selected", "expected", "actual", "learned"))
    assert ex[0]["selected"] and ex[0]["expected"]
    # failed execution recorded as research data
    assert (results_root / eid / "report.json").exists()
    rep = json.loads((results_root / eid / "report.json").read_text())
    assert rep["failed_runs"] and any(f["agent"] == "fixed" for f in rep["failed_runs"])


def test_agm_v2_ablation_modes_and_decisions(tmp_db, tmp_path, results_root):
    raw = yaml.safe_load(MANIFEST.replace("MEMDB", str(tmp_path / "mem.sqlite")))
    raw["experiment"]["agents"] = [
        {"name": "never", "type": "agm_v2", "max_evaluations": 3, "economics_mode": "never_adapt", "memory_mode": "none"},
        {"name": "always", "type": "agm_v2", "max_evaluations": 3, "economics_mode": "always_adapt", "memory_mode": "none"},
        {"name": "econ", "type": "agm_v2", "max_evaluations": 3, "economics_mode": "economic", "memory_mode": "principle",
         "principle_memory": {"read": True, "write": True, "db": str(tmp_path / "p.sqlite")}},
    ]
    spec = parse_experiment(raw)
    eid = ExperimentRunner(spec, db=tmp_db, executor_name="process", results_root=results_root, quiet=True).run()
    s = tmp_db.experiment(eid)["summary"]
    never, always, econ = s["never"]["agent_extra"], s["always"]["agent_extra"], s["econ"]["agent_extra"]
    assert never["decision_outcomes"]["DO_NOT_ADAPT"] >= 1 and s["never"]["architecture_evaluations"] <= s["always"]["architecture_evaluations"]
    assert always["decision_outcomes"]["ADAPT"] >= 2
    for d in econ["decisions"]:
        assert d["actual_adaptation_cost"] is not None and "decision_error" in d and d["inputs"]["search_cost_usd"] >= 0
    assert econ["principles_created"] >= 0 and "mean_decision_error" in econ
    decs = tmp_db.decisions(eid)
    assert any(d.get("mode") == "never_adapt" for d in decs)
