"""B3 Self-Evolving Agent: hill-climbs by mutating its own Architecture IR.

Mutation is restricted to the IR (never code) and every mutant is evaluated
in the sandbox on the validation slice before adoption.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from architecture.ir import ArchitectureIR
from baselines.base import Agent, AgentContext, CandidateResult, ir_from_config
from baselines.fixed import DEFAULT

MUTATIONS = ["reasoning.type", "reasoning.model", "reasoning.threshold", "perception.components",
             "perception.window", "memory.type", "verification.type"]


class SelfEvolvingAgent(Agent):
    kind = "self_evolving"

    def __init__(self, name, config, registry):
        super().__init__(name, config, registry)
        self.current = ir_from_config(config.get("architecture", DEFAULT), name=f"{name}_seed")
        self.seed_ir = self.current
        self.mutations_per_step = int(config.get("mutations_per_step", 2))
        self.best_score: Optional[float] = None

    def known_architectures(self) -> List[ArchitectureIR]:
        return [self.seed_ir]

    def _mutate(self, ir: ArchitectureIR, ctx: AgentContext) -> ArchitectureIR:
        a = ir.architecture
        reg = self.registry
        op = ctx.rng.choice(MUTATIONS)
        changes: Dict[str, Any] = {}
        if op == "reasoning.type":
            changes[op] = ctx.rng.choice(reg.names("reasoning"))
            if changes[op] == "iterative":
                changes["reasoning.iterations"] = ctx.rng.randint(2, 4)
        elif op == "reasoning.model":
            changes[op] = ctx.rng.choice([m for m in reg.names("model") if m != "embedding_model"])
        elif op == "reasoning.threshold":
            changes[op] = round(min(0.95, max(0.05, a.reasoning.threshold + ctx.rng.choice([-0.1, 0.1]))), 2)
        elif op == "perception.components":
            comps = list(a.perception.components)
            pool = reg.names("component")
            if len(comps) > 1 and ctx.rng.random() < 0.5:
                comps.remove(ctx.rng.choice(comps))
            else:
                extra = [c for c in pool if c not in comps]
                if extra:
                    comps.append(ctx.rng.choice(extra))
            changes[op] = comps
        elif op == "perception.window":
            changes[op] = int(min(5000, max(5, a.perception.window * ctx.rng.choice([0.5, 2]))))
        elif op == "memory.type":
            changes[op] = ctx.rng.choice(reg.names("memory"))
        elif op == "verification.type":
            v = ctx.rng.choice(reg.names("verification"))
            changes[op] = v
            changes["verification.model"] = "small_reasoner" if v == "model_based" else None
        try:
            return ir.derive(name=f"{self.name}_gen{len(ir.lineage) + 1}", **changes)
        except Exception:
            return ir

    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR:
        if ctx.budget_remaining <= 0 or ctx.deadline_remaining_s <= 0:
            return self.current
        if ctx.validate(self.current):
            self.best_score = None  # current is invalid; anything valid beats it
        if self.best_score is None and not ctx.validate(self.current):
            self.best_score = ctx.evaluate_candidate(self.current, "mutation_baseline").quality
        for _ in range(self.mutations_per_step):
            mutant = self._mutate(self.current, ctx)
            if mutant.hash() == self.current.hash() or ctx.validate(mutant):
                continue
            res: CandidateResult = ctx.evaluate_candidate(mutant, "mutation")
            if not res.failed and (self.best_score is None or res.quality > self.best_score):
                self.current, self.best_score = mutant, res.quality
        return self.current
