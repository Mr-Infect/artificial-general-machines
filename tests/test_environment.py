from environments.profile import DynamicEnvironment, EnvironmentEvent, EnvironmentProfile
from environments.scoring import score
from environments.synthetic import generate


def test_events_fire_in_order_and_are_recorded():
    seen = []
    env = DynamicEnvironment(EnvironmentProfile(memory_mb=512, network=True, available_capabilities=["model:large_reasoner", "model:small_reasoner"]),
                             [EnvironmentEvent(t=10, type="memory_reduction", params={"factor": 0.5}),
                              EnvironmentEvent(t=20, type="network_loss"),
                              EnvironmentEvent(t=20, type="capability_removal", params={"capabilities": ["model:large_reasoner"]}),
                              EnvironmentEvent(t=30, type="latency_reduction", params={"latency_ms": 100}),
                              EnvironmentEvent(t=40, type="priority_increase", params={"priority": 3})],
                             on_transition=lambda t, ev, b, a: seen.append(ev.type.value))
    assert env.advance(0) == [] and env.profile.memory_mb == 512
    env.advance(15)
    assert env.profile.memory_mb == 256 and env.profile.network is True
    env.advance(25)
    assert env.profile.network is False and env.profile.available_capabilities == ["model:small_reasoner"]
    env.advance(45)
    assert env.profile.latency_ms == 100 and env.profile.priority == 3
    assert seen == ["memory_reduction", "network_loss", "capability_removal", "latency_reduction", "priority_increase"]
    assert len(env.transitions) == 5 and env.transitions[0]["before"]["memory_mb"] == 512


def test_dataset_is_deterministic_and_labelled():
    a = generate("network", 1000, 0.05, 0.03, 7)
    b = generate("network", 1000, 0.05, 0.03, 7)
    c = generate("network", 1000, 0.05, 0.03, 8)
    assert a["records"] == b["records"] and a["labels"] == b["labels"]
    assert a["records"] != c["records"]
    assert 0 < sum(a["labels"]) < 200
    s = generate("scientific", 1000, 0.05, 0.03, 7)
    assert s["feature_names"] != a["feature_names"] and s["relations"]


def test_score_handles_no_positives():
    assert score([0, 0, 0], [0, 0, 0])["quality"] == 1.0
    assert score([1, 0, 0], [0, 0, 0])["quality"] < 1.0
    s = score([1, 1, 0, 0], [1, 0, 1, 0])
    assert abs(s["f1"] - 0.5) < 1e-9 and s["quality"] == s["f1"]
