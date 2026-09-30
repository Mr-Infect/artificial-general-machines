"""B2 Architecture Search: evaluate candidates from a predefined space on the
validation slice and keep the best valid one. Re-searches only when the
current architecture becomes invalid or misses the target repeatedly."""
from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from architecture.ir import ArchitectureIR
from baselines.base import Agent, AgentContext, CandidateResult

ROOT = Path(__file__).resolve().parent.parent


def enumerate_space(space: Dict[str, List[Any]]) -> List[ArchitectureIR]:
    keys = list(space)
    out = []
    for combo in itertools.product(*(space[k] for k in keys)):
        body: Dict[str, Any] = {}
        for k, v in zip(keys, combo):
            node = body
            parts = k.split(".")
            for p in parts[:-1]:
                node = node.setdefault(p, {})
            node[parts[-1]] = v
        try:
            out.append(ArchitectureIR(name="search", architecture=body))
        except Exception:
            continue
    return out


class SearchAgent(Agent):
    kind = "search"

    def __init__(self, name, config, registry):
        super().__init__(name, config, registry)
        path = ROOT / config.get("space", "configs/architecture_space.yaml")
        self.space = enumerate_space(yaml.safe_load(path.read_text())["space"])
        self.max_evaluations = int(config.get("max_evaluations", 12))
        self.patience = int(config.get("patience", 2))
        self.misses = 0
        self.best: Optional[CandidateResult] = None
        self.evaluated: Dict[str, CandidateResult] = {}

    def known_architectures(self) -> List[ArchitectureIR]:
        return self.space

    def _search(self, ctx: AgentContext) -> Optional[ArchitectureIR]:
        from architecture.validate import validate_against_registry
        valid = [ir for ir in self.space if not validate_against_registry(ir, self.registry) and not ctx.validate(ir)]
        if not valid:
            return None
        pool = list(valid)
        ctx.rng.shuffle(pool)
        pool = pool[: self.max_evaluations]
        best_ir, best_res = None, None
        for ir in pool:
            h = ir.hash()
            res = self.evaluated.get(h) or ctx.evaluate_candidate(ir, "search")
            self.evaluated[h] = res
            if res.failed:
                continue
            key = (res.quality, -res.cost)
            if best_res is None or key > (best_res.quality, -best_res.cost):
                best_ir, best_res = ir, res
        self.best = best_res
        return best_ir

    def select_architecture(self, ctx: AgentContext) -> ArchitectureIR:
        need = self.current is None or bool(ctx.validate(self.current))
        last_q = (ctx.last_evaluation or {}).get("quality")
        if last_q is not None and last_q < ctx.target_quality:
            self.misses += 1
        else:
            self.misses = 0
        if self.misses >= self.patience:
            need, self.misses = True, 0
        if need and ctx.budget_remaining > 0 and ctx.deadline_remaining_s > 0:
            found = self._search(ctx)
            if found is not None:
                self.current = found
        if self.current is None:  # nothing affordable; fall back to the cheapest valid entry
            valid = [ir for ir in self.space if not ctx.validate(ir)]
            self.current = min(valid, key=lambda ir: ctx.estimate(ir)["cost_per_batch"]) if valid else self.space[0]
        return self.current
