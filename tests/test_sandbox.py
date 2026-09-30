import pytest

from architecture.ir import ArchitectureIR
from compiler import compile_ir
from environments.synthetic import batch_payload, generate
from runtime.executor import DockerExecutor, ProcessExecutor
from tests.conftest import docker_available


def _payload(registry, n=300):
    ds = generate("network", n, 0.05, 0.03, 3)
    ir = ArchitectureIR(architecture={"perception": {"components": ["anomaly_detector"]}, "reasoning": {"type": "direct"}})
    spec = compile_ir(ir, registry, {"cpu": 1, "memory_mb": 128, "timeout_s": 10}).model_dump()
    return {"spec": spec, "data": batch_payload(ds, 0, n), "state": {}}, ds


def test_process_executor_returns_full_result(registry):
    payload, ds = _payload(registry)
    r = ProcessExecutor().run(payload, {"cpu": 1, "memory_mb": 128, "timeout_s": 10})
    assert r.exit_code == 0 and r.artifact["ok"] and not r.timed_out
    assert len(r.artifact["predictions"]) == len(ds["records"])
    assert r.cpu_time_s > 0 and r.max_memory_mb > 0 and r.runtime_s > 0
    assert r.artifact["accounting"]["model_calls"] == 1


def test_runner_is_deterministic(registry):
    payload, _ = _payload(registry)
    a = ProcessExecutor().run(payload, {"timeout_s": 10}).artifact["predictions"]
    b = ProcessExecutor().run(payload, {"timeout_s": 10}).artifact["predictions"]
    assert a == b


def test_runner_reports_errors_not_crashes(registry):
    payload, _ = _payload(registry)
    payload["spec"]["pipeline"]["reasoning"]["type"] = "not_a_type"
    r = ProcessExecutor().run(payload, {"timeout_s": 10})
    assert r.exit_code == 3 and r.artifact["ok"] is False and "unknown reasoning type" in r.artifact["error"]


@pytest.mark.skipif(not docker_available(), reason="docker not available")
def test_docker_executor_isolation_and_timeout(registry):
    payload, ds = _payload(registry)
    dx = DockerExecutor()
    r = dx.run(payload, {"cpu": 0.5, "memory_mb": 64, "timeout_s": 20})
    assert r.exit_code == 0 and r.artifact["ok"] and r.executor == "docker"
    assert len(r.artifact["predictions"]) == len(ds["records"])
    big, _ = _payload(registry, n=40000)
    r = dx.run(big, {"cpu": 0.1, "memory_mb": 64, "timeout_s": 1})
    assert r.timed_out and r.resource_violation == "timeout" and r.exit_code == -9
