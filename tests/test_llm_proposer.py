from baselines.llm_proposer import LLMArchitectureProposer, StubBackend, parse_proposals, policy_validate
from architecture.ir import ArchitectureIR


class Ctx:
    domain = "network"
    task = {"type": "anomaly_detection", "domain": "network"}
    target_quality = 0.85
    env = {"memory_mb": 512, "cpu": 1, "latency_ms": 2000, "network": False, "priority": 1, "privacy": "local_only"}
    def validate(self, ir):
        return []


def test_llm_pipeline_validates_and_rejects(registry):
    good = "name: a\narchitecture:\n  perception: {mode: single, components: [anomaly_detector]}\n  reasoning: {type: direct, model: small_reasoner}\n"
    bad_schema = "name: b\narchitecture:\n  reasoning: {type: teleport}\n"
    bad_registry = "name: c\narchitecture:\n  perception: {mode: single, components: [quantum_oracle]}\n"
    bad_env = "name: d\narchitecture:\n  perception: {components: [anomaly_detector, statistical_detector]}\n  reasoning: {type: parallel}\n  tools: [python, search]\n"
    text = "\n---\n".join([good, bad_schema, bad_registry, bad_env])
    caps = {"component": registry.names("component"), "model": registry.names("model"), "reasoning": registry.names("reasoning"),
            "memory": registry.names("memory"), "verification": registry.names("verification"), "tool": registry.names("tool")}
    env = {**Ctx.env, "available_capabilities": registry.keys_for_domain("network")}
    prop = LLMArchitectureProposer(registry, StubBackend(text))
    accepted = prop.propose(Ctx(), caps, None, env, {"cpu": 1, "memory_mb": 512, "timeout_s": 30})
    assert len(accepted) == 1 and accepted[0].metadata["source"] == "llm" and isinstance(accepted[0], ArchitectureIR)
    stages = [l["stage"] for l in prop.log]
    assert stages.count("accepted") == 1 and "schema" in stages and "registry" in stages and "environment" in stages
    # policy: anything that looks like code/commands/files is refused wholesale
    assert policy_validate("architecture: {}\ncommand: rm -rf /") and policy_validate("path: /etc/passwd")
    prop2 = LLMArchitectureProposer(registry, StubBackend("name: x\nscript: |\n  import os\n"))
    assert prop2.propose(Ctx(), caps, None, env, {"timeout_s": 30}) == [] and prop2.log[0]["stage"] == "policy"
    docs, errs = parse_proposals("```yaml\nname: q\narchitecture: {}\n```\n---\n: : bad")
    assert len(docs) == 1 and errs
