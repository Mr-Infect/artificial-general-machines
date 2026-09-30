from architecture.ir import ArchitectureIR
from architecture.validate import validate_against_environment
from compiler import compile_ir
from environments.planning import generate, oracle_plan, score_batch, simulate
from environments.synthetic import batch_payload, load_or_generate
from runtime.executor import ProcessExecutor


def test_planning_dataset_deterministic_and_oracle_dominates():
    a = generate(600, 0.1, 1.3, 11)
    b = generate(600, 0.1, 1.3, 11)
    assert a["records"] == b["records"] and a["truth"] == b["truth"] and a["labels"] == b["labels"]
    n = len(a["records"])
    oracle = score_batch(a, 0, n, a["labels"], a["oracle_assignments"])
    assert oracle["quality"] == 1.0 and oracle["n_failed"] == 0
    for plan in ([1] * n, [0] * n, [i % 2 for i in range(n)]):
        assert score_batch(a, 0, n, plan)["quality"] <= 1.0
    assert score_batch(a, 0, n, [1] * n)["n_failed"] > 0     # overload fails jobs
    assert score_batch(a, 0, n, [0] * n)["quality"] == 0.0


def test_sandbox_never_sees_truth():
    ds = generate(300, 0.1, 1.3, 2)
    bp = batch_payload(ds, 100, 200)
    assert "truth" not in bp and "labels" not in bp
    first_tick = int(ds["records"][100][0])
    assert all(t["realized_capacity"] is None for t in bp["ticks"] if t["tick"] >= first_tick)
    assert any(t["realized_capacity"] is not None for t in bp["ticks"] if t["tick"] < first_tick)


def test_planning_architectures_run_and_differ(registry):
    ds = generate(800, 0.15, 1.4, 3)
    n = len(ds["records"])
    archs = {
        "select_all_filter": {"perception": {"mode": "single", "components": ["priority_filter"]}, "reasoning": {"type": "direct", "threshold": 0.05}},
        "feasible": {"perception": {"mode": "single", "components": ["feasibility_checker"]}, "reasoning": {"type": "direct"}},
        "forecast_exec": {"perception": {"components": ["priority_filter", "capacity_forecaster"]}, "reasoning": {"type": "parallel"},
                          "memory": {"type": "episodic"}, "verification": {"type": "execution_based"}},
        "lookahead": {"perception": {"components": ["priority_filter", "capacity_forecaster", "lookahead_planner"]},
                      "reasoning": {"type": "hierarchical", "model": "large_reasoner", "threshold": 0.45}, "verification": {"type": "execution_based"}},
    }
    qual = {}
    for name, body in archs.items():
        ir = ArchitectureIR(name=name, architecture=body)
        spec = compile_ir(ir, registry, {"timeout_s": 30}).model_dump()
        state, preds, assigns = {}, [], []
        for s in range(0, n, 400):
            r = ProcessExecutor().run({"spec": spec, "data": batch_payload(ds, s, min(n, s + 400)), "state": state}, {"timeout_s": 30})
            assert r.artifact and r.artifact["ok"], r.artifact
            preds += r.artifact["predictions"]
            assigns += r.artifact.get("assignments") or [None] * len(r.artifact["predictions"])
            state = r.artifact["state"]
        qual[name] = score_batch(ds, 0, n, preds, assigns)["quality"]
    assert len({round(q, 3) for q in qual.values()}) >= 3, qual
    assert qual["feasible"] > qual["select_all_filter"]


def test_cross_domain_isolation(registry):
    env = {"memory_mb": 512, "network": False, "privacy": "local_only", "available_capabilities": registry.keys_for_domain("planning")}
    anomaly_ir = ArchitectureIR(architecture={"perception": {"mode": "single", "components": ["anomaly_detector"]}, "reasoning": {"type": "direct"}})
    plan_ir = ArchitectureIR(architecture={"perception": {"mode": "single", "components": ["feasibility_checker"]}, "reasoning": {"type": "direct"}})
    assert any(v.startswith("capability_unavailable:component:anomaly_detector") for v in validate_against_environment(anomaly_ir, env, registry, 50))
    assert validate_against_environment(plan_ir, env, registry, 50) == []
    env_a = dict(env, available_capabilities=registry.keys_for_domain("network"))
    assert any("feasibility_checker" in v for v in validate_against_environment(plan_ir, env_a, registry, 50))
    assert "component:lookahead_planner" not in registry.keys_for_domain("network")
