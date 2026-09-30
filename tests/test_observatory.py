import json

import yaml
from fastapi.testclient import TestClient

from experiments.manifest import parse_experiment
from experiments.run import ExperimentRunner
from observability import api as obs


MANIFEST = """
experiment:
  name: test_obs
  seed: 4
  task: {type: anomaly_detection, domain: network, dataset_size: 500, noise: 0.1, anomaly_rate: 0.04}
  environment: {cpu: 1, memory_mb: 512, latency_ms: 5000, network: true}
  objective: {quality_threshold: 0.8}
  budget: {max_seconds: 60, max_cost: 0.2, step_timeout_s: 20}
  schedule: {steps: 2, step_seconds: 10, validation_fraction: 0.25}
  events: [{t: 10, type: memory_reduction, params: {memory_mb: 80}}]
  agents:
    - {name: fixed, type: fixed}
    - {name: agm_v2, type: agm_v2, max_evaluations: 3, memory_mode: principle, principle_memory: {read: true, write: true, db: PDB}}
"""


def test_dashboard_api_and_websocket(tmp_db, tmp_path, results_root):
    spec = parse_experiment(yaml.safe_load(MANIFEST.replace("PDB", str(tmp_path / "p.sqlite"))))
    eid = ExperimentRunner(spec, db=tmp_db, executor_name="process", results_root=results_root, quiet=True).run()
    c = TestClient(obs.app)
    q = {"db_path": str(tmp_db.path)}
    runs = c.get("/runs", params=q).json()
    assert {r["agent"] for r in runs} == {"fixed", "agm_v2"} and all(r["n_events"] > 0 for r in runs)
    rid = f"{eid}.agm_v2"
    r = c.get(f"/runs/{rid}", params=q).json()
    assert r["state"]["completed"] and r["state"]["current_architecture"]["alias"].startswith("A-")
    evs = c.get(f"/runs/{rid}/events", params=q).json()
    assert [e["seq"] for e in evs] == list(range(len(evs)))
    mid = c.get(f"/runs/{rid}/state", params={**q, "at": len(evs) // 2}).json()
    assert not mid["completed"] and mid["last_seq"] == len(evs) // 2
    assert c.get(f"/runs/{rid}/explanations", params=q).json()[0]["selected"]
    archs = c.get(f"/runs/{rid}/architectures", params=q).json()
    assert archs and all(a["alias"] for a in archs)
    lin = c.get(f"/runs/{rid}/lineage", params=q).json()
    assert lin["nodes"] and lin["current"]
    h = archs[0]["hash"]
    assert c.get(f"/architectures/{h}", params=q).status_code == 200
    assert "ancestors" in c.get(f"/architectures/{h}/lineage", params=q).json()
    other = archs[-1]["hash"]
    d = c.get(f"/architectures/{h}/diff/{other}", params=q).json()
    assert "structural_distance" in d["distance"] and "highest_level" in d["novelty_of_a_vs_b"]
    assert "retrieved" in c.get(f"/runs/{rid}/principles", params=q).json()
    assert "attempted" in c.get(f"/runs/{rid}/transfer", params=q).json()
    par = c.get(f"/experiments/{eid}/pareto", params=q).json()
    assert set(par["classification"]) == {"fixed", "agm_v2"} and par["frontier"] and set(par["objectives"]) >= {"quality_mean", "latency_ms", "max_memory_mb", "adaptation_cost", "architecture_evaluations", "failure_rate"}
    assert c.get("/runs/nope", params=q).status_code == 404
    # WebSocket streaming delivers the recorded events in order and signals the end of a completed run
    with c.websocket_connect(f"/ws/runs/{rid}?after=-1&db_path={tmp_db.path}") as ws:
        got = []
        while True:
            m = json.loads(ws.receive_text())
            if m["event_type"] == "_STREAM_END":
                break
            got.append(m)
        assert [g["seq"] for g in got] == list(range(len(evs))) and got[0]["event_type"] == "RUN_STARTED"
    assert c.get("/").status_code == 200 and "AGM Architecture Observatory" in c.get("/").text
