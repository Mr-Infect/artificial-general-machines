from architecture.ir import ArchitectureIR, compare, novelty, try_parse
from architecture.validate import validate_against_environment, validate_against_registry
from compiler import compile_ir, CompileError
from environments.profile import EnvironmentProfile


def test_hash_is_stable_and_structural(registry):
    a = ArchitectureIR(name="x", architecture={"perception": {"components": ["anomaly_detector"]}})
    b = ArchitectureIR(name="y", architecture={"perception": {"components": ["anomaly_detector"]}}, metadata={"note": 1})
    assert a.hash() == b.hash()
    assert a.hash() == ArchitectureIR.from_yaml(a.to_yaml()).hash()


def test_derive_tracks_lineage_and_diff():
    a = ArchitectureIR(architecture={"perception": {"components": ["anomaly_detector", "rate_detector"]}, "reasoning": {"type": "parallel"}})
    b = a.derive(**{"reasoning.model": "large_reasoner"})
    assert b.parent_hash == a.hash() and b.lineage == [a.hash()]
    d = compare(a, b)
    assert not d["same"] and "reasoning.model" in d["diff"] and 0 < d["distance"] < 1
    assert novelty(b, [a]) == d["distance"] and novelty(a, []) == 1.0


def test_schema_and_registry_validation(registry):
    ir, errs = try_parse({"architecture": {"reasoning": {"type": "bogus"}}})
    assert ir is None and errs
    bad = ArchitectureIR(architecture={"perception": {"components": ["no_such_component"]}, "reasoning": {"type": "parallel"}})
    errs = validate_against_registry(bad, registry)
    assert any("unknown perception component" in e for e in errs)
    assert any("requires at least two" in e for e in errs)
    try:
        compile_ir(bad, registry, {})
        assert False, "expected CompileError"
    except CompileError:
        pass


def test_environment_validation_bites(registry):
    ir = ArchitectureIR(architecture={"perception": {"components": ["anomaly_detector", "statistical_detector"]},
                                      "reasoning": {"type": "hierarchical", "model": "large_reasoner"}, "tools": ["python", "search"]})
    spec = compile_ir(ir, registry, {"cpu": 1, "memory_mb": 512, "timeout_s": 10})
    env = EnvironmentProfile(memory_mb=512, network=True, privacy="shared", available_capabilities=registry.all_keys()).observable()
    assert validate_against_environment(ir, env, registry, spec.estimates["memory_mb"]) == []
    env["network"] = False
    env["memory_mb"] = 100
    env["available_capabilities"] = [k for k in env["available_capabilities"] if k != "model:large_reasoner"]
    v = validate_against_environment(ir, env, registry, spec.estimates["memory_mb"])
    assert any(x.startswith("network_required") for x in v)
    assert any(x.startswith("memory_estimate_exceeds_limit") for x in v)
    assert "capability_unavailable:model:large_reasoner" in v
