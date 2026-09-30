"""LLMArchitectureProposer (v0.2, spec section 29). NOT used by any experiment in v0.2.

Pipeline:  LLM → Architecture IR (text) → schema validation → policy validation → compiler → sandbox

The model may only emit IR. It cannot execute commands, touch files, reach the network, change
sandbox policy, bypass the IR, or bypass validation: the proposer returns *candidate IRs* to the
same harness that evaluates every other agent's candidates. Policy validation rejects anything
outside the registry, anything requiring capabilities unavailable in the environment, and anything
above resource limits, exactly as for other agents. Rejections are recorded as research data.

Backends: ``HTTPBackend`` (Anthropic Messages API over urllib; needs ANTHROPIC_API_KEY) and
``StubBackend`` (returns fixed text; tests only, never an experimental condition).
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional, Protocol, Tuple

import yaml

from architecture.ir import ArchitectureIR, try_parse
from architecture.validate import validate_against_environment, validate_against_registry
from baselines.agm_v2 import AGMv2Agent
from baselines.base import AgentContext
from compiler import CompileError, compile_ir
from core.registry import CapabilityRegistry

FORBIDDEN_KEYS = {"code", "script", "exec", "command", "shell", "path", "file", "url", "docker", "mount", "network_policy"}


class Backend(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class StubBackend:
    """Tests only: returns canned text."""
    def __init__(self, text: str):
        self.text = text
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        return self.text


class HTTPBackend:
    def __init__(self, model: str = "claude-sonnet-5-5", api_key: Optional[str] = None, max_tokens: int = 1200):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.max_tokens = max_tokens
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

    def complete(self, system: str, user: str) -> str:
        body = json.dumps({"model": self.model, "max_tokens": self.max_tokens, "system": system, "messages": [{"role": "user", "content": user}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST",
                                     headers={"content-type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
        return "".join(part.get("text", "") for part in data.get("content", []))


SYSTEM = ("You design architectures for a fixed sandbox runner. Reply ONLY with YAML documents separated by '---', each a complete "
          "Architecture IR: keys architecture.perception{mode,components,window}, architecture.reasoning{type,model,threshold,iterations}, "
          "architecture.memory{type,capacity}, architecture.verification{type,model,strictness}, architecture.tools, architecture.output{confidence}. "
          "Use only the components, models, reasoning/memory/verification types listed. No code, no commands, no files, no URLs.")


def policy_validate(text: str) -> List[str]:
    problems = []
    low = text.lower()
    for k in FORBIDDEN_KEYS:
        if re.search(rf"\b{k}\b\s*:", low):
            problems.append(f"forbidden key {k!r}")
    if "```" in text and "yaml" not in low:
        problems.append("code fence without yaml")
    return problems


def parse_proposals(text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    text = text.replace("```yaml", "").replace("```", "")
    docs, errors = [], []
    for i, chunk in enumerate(text.split("\n---")):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            d = yaml.safe_load(chunk)
        except yaml.YAMLError as e:
            errors.append(f"doc {i}: yaml error {e}")
            continue
        if not isinstance(d, dict):
            errors.append(f"doc {i}: not a mapping")
            continue
        docs.append(d)
    return docs, errors


class LLMArchitectureProposer:
    def __init__(self, registry: CapabilityRegistry, backend: Backend, max_proposals: int = 6):
        self.registry = registry
        self.backend = backend
        self.max_proposals = max_proposals
        self.log: List[Dict[str, Any]] = []   # every proposal and its fate (research data)

    def prompt(self, ctx: AgentContext, caps: Dict[str, List[str]], current: Optional[ArchitectureIR]) -> str:
        env = ctx.env
        return (f"Domain: {ctx.domain}. Task: {json.dumps(ctx.task)}. Target quality: {ctx.target_quality}.\n"
                f"Environment: memory {env.get('memory_mb')}MB, cpu {env.get('cpu')}, latency budget {env.get('latency_ms')}ms, network {env.get('network')}, priority {env.get('priority')}.\n"
                f"Available components: {caps['component']}. Models: {caps['model']}. Reasoning: {caps['reasoning']}. Memory: {caps['memory']}. Verification: {caps['verification']}.\n"
                f"Current architecture: {current.to_yaml() if current else 'none'}\n"
                f"Propose up to {self.max_proposals} distinct architectures likely to reach the target at low resource cost.")

    def propose(self, ctx: AgentContext, caps: Dict[str, List[str]], current: Optional[ArchitectureIR], env_obs: Dict[str, Any], limits: Dict[str, Any]) -> List[ArchitectureIR]:
        text = self.backend.complete(SYSTEM, self.prompt(ctx, caps, current))
        accepted: List[ArchitectureIR] = []
        pol = policy_validate(text)
        if pol:
            self.log.append({"stage": "policy", "accepted": False, "problems": pol, "text": text[:500]})
            return []
        docs, errs = parse_proposals(text)
        for e in errs:
            self.log.append({"stage": "parse", "accepted": False, "problems": [e]})
        for d in docs[: self.max_proposals]:
            d.setdefault("name", "llm_proposal")
            ir, schema_errs = try_parse(d)
            if ir is None:
                self.log.append({"stage": "schema", "accepted": False, "problems": schema_errs, "doc": d})
                continue
            reg_errs = validate_against_registry(ir, self.registry)
            if reg_errs:
                self.log.append({"stage": "registry", "accepted": False, "problems": reg_errs, "hash": ir.hash()})
                continue
            try:
                est = compile_ir(ir, self.registry, limits).estimates
            except CompileError as e:
                self.log.append({"stage": "compile", "accepted": False, "problems": [str(e)], "hash": ir.hash()})
                continue
            env_errs = validate_against_environment(ir, env_obs, self.registry, est["memory_mb"])
            if env_errs:
                self.log.append({"stage": "environment", "accepted": False, "problems": env_errs, "hash": ir.hash()})
                continue
            ir = ir.model_copy(update={"name": f"llm_{ir.name[:20]}", "metadata": {**ir.metadata, "source": "llm"}})
            self.log.append({"stage": "accepted", "accepted": True, "hash": ir.hash()})
            accepted.append(ir)
        return accepted


class LLMAGMAgent(AGMv2Agent):
    """AGM v0.2 whose candidate set is extended by LLM proposals. Everything downstream (economics,
    evaluation, selection, memory) is identical to AGM v0.2. Not used by any v0.2 experiment."""
    kind = "agm_llm"

    def __init__(self, name, config, registry, backend: Optional[Backend] = None):
        super().__init__(name, config, registry)
        self.proposer = LLMArchitectureProposer(registry, backend or HTTPBackend(model=config.get("model", "claude-sonnet-5-5")), int(config.get("max_proposals", 6)))

    def _synthesize(self, ctx: AgentContext, caps: Dict[str, List[str]]):
        out = super()._synthesize(ctx, caps)
        limits = {"cpu": ctx.env.get("cpu", 1), "memory_mb": ctx.env.get("memory_mb", 512), "timeout_s": 30}
        for ir in self.proposer.propose(ctx, caps, self.current, ctx.env, limits):
            if ir.hash() not in {c[0].hash() for c in out} and not ctx.validate(ir):
                out.append((ir, "llm", None))
        return out

    def summary(self) -> Dict[str, Any]:
        s = super().summary()
        s["llm_proposals"] = self.proposer.log
        return s
