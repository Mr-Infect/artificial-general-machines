import json

import yaml

from experiments.manifest import ExperimentSpec, parse_experiment
from experiments.report import experiment_report, render_markdown, suite_report, render_suite_markdown, pareto_front, bootstrap_ci
from experiments.run import ExperimentRunner

MANIFEST = """
experiment:
  name: test_small
  seed: 5
  task: {type: anomaly_detection, domain: network, dataset_size: 600, noise: 0.05, anomaly_rate: 0.04}
  environment: {cpu: 1, memory_mb: 512, latency_ms: 5000, network: true}
  objective: {quality_threshold: 0.8}
  budget: {max_seconds: 60, max_cost: 0.2, step_timeout_s: 20}
  schedule: {steps: 3, step_seconds: 10, validation_fraction: 0.25}
  events:
    - {t: 10, type: memory_reduction, params: {memory_mb: 100}}
    - {t: 20, type: capability_removal, params: {capabilities: [model:large_reasoner]}}
  agents:
    - {name: fixed, type: fixed, architecture: {perception: {components: [statistical_detector, anomaly_detector]}, reasoning: {type: hierarchical, model: large_reasoner}}}
    - {name: adaptive, type: adaptive}
    - {name: search, type: search, max_evaluations: 3}
    - {name: self_evolving, type: self_evolving, mutations_per_step: 1}
    - {name: agm_cold, type: agm, max_evaluations: 3, memory: {read: false, write: true, db: MEMDB}}
    - {name: agm_memory, type: agm, max_evaluations: 3, memory: {read: true, write: true, db: MEMDB}}
"""


def _spec(tmp_path):
    raw = yaml.safe_load(MANIFEST.replace("MEMDB", str(tmp_path / "mem.sqlite")))
    return parse_experiment(raw)


def test_full_experiment_process_executor(tmp_db, tmp_path, results_root):
    spec = _spec(tmp_path)
    runner = ExperimentRunner(spec, db=tmp_db, executor_name="process", results_root=results_root, quiet=True)
    eid = runner.run()
    exp = tmp_db.experiment(eid)
    assert exp["status"] == "finished" and set(exp["summary"]) == {"fixed", "adaptive", "search", "self_evolving", "agm_cold", "agm_memory"}
    # the fixed agent's large-model architecture becomes invalid at t=10 (memory) and t=20 (capability removal)
    fixed_execs = [e for e in tmp_db.executions(eid, "fixed") if e["purpose"] == "task"]
    assert fixed_execs[0]["result"]["exit_code"] == 0
    assert fixed_execs[1]["result"]["resource_violation"] == "architecture_invalid_for_environment"
    assert exp["summary"]["fixed"]["failures"] == 2 and exp["summary"]["fixed"]["constraint_violations"] >= 2
    # adaptive agents kept running
    assert exp["summary"]["adaptive"]["failures"] == 0
    assert exp["summary"]["search"]["architecture_evaluations"] > 0
    # environment transitions recorded for every agent
    events = tmp_db.env_events(eid)
    assert {e["event"]["type"] for e in events} == {"memory_reduction", "capability_removal"}
    assert len(events) == 2 * len(spec.agents)
    # adaptation decisions recorded with all inputs
    decs = tmp_db.decisions(eid)
    assert decs and all(k in decs[0] for k in ("search_cost", "validation_cost", "deadline_remaining_s", "outcome", "rationale"))
    # metrics beyond accuracy
    names = {m["name"] for m in tmp_db.metrics(eid)}
    for required in ("quality", "accuracy", "latency_ms", "cpu_time_s", "memory_mb", "cost", "search_time_s", "architecture_evaluations",
                     "model_calls", "tokens", "adaptation_cost", "execution_cost", "total_cost", "constraint_violations", "failures", "novelty"):
        assert required in names, required
    # provenance and reports on disk
    d = results_root / eid
    prov = json.loads((d / "provenance.json").read_text())
    assert prov["seed"] == 5 and prov["manifest_hash"] and "git" in prov and prov["executor"] == "process"
    assert (d / "report.md").exists() and (d / "telemetry_fixed.jsonl").exists()
    r = experiment_report(tmp_db, eid)
    assert r["pareto_front_cost"] and "agm_memory" in r["transfer"]
    md = render_markdown(r)
    assert "does not declare any agent successful" in md
    # structural memory was written by the AGM agents
    assert exp["summary"]["agm_cold"]["memory_writes"] == 3
    s = suite_report(tmp_db, ["test_small"])
    assert s["experiments"]["test_small"]["n_runs"] == 1
    assert render_suite_markdown(s, "t")


def test_replay_is_deterministic(tmp_db, tmp_path, results_root):
    from experiments import run as runmod
    spec = _spec(tmp_path).model_copy(update={"agents": _spec(tmp_path).agents[:3]})
    runner = ExperimentRunner(spec, db=tmp_db, executor_name="process", results_root=results_root, quiet=True)
    eid = runner.run()
    rep = runmod.replay(eid, executor="process", db=tmp_db, quiet=True, results_root=results_root)
    assert rep["steps_compared"] == 9 and rep["deterministic"], rep


def test_report_helpers():
    assert pareto_front({"a": (1.0, 0.5), "b": (2.0, 0.6), "c": (2.0, 0.4), "d": (0.5, 0.5)}) == ["d", "b"]
    m, lo, hi = bootstrap_ci([0.5, 0.6, 0.7, 0.8])
    assert lo <= m <= hi and abs(m - 0.65) < 1e-9
    assert bootstrap_ci([0.3]) == (0.3, 0.3, 0.3)
