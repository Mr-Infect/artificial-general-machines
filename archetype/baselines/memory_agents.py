"""Memory baselines: B3 task memory, B4 architecture memory, B5 principle memory (unconditional), B7 never adapt.
All are fitted on exactly the same shared training experience as ARCHETYPE."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Set

from archetype.architecture import generate as Gen
from archetype.baselines.base import Agent, Ctx, Experience, compose_from, hill_climb
from archetype.baselines.simple import SearchingAgent
from archetype.learner.transformations import TRANSFORMATIONS, apply, present


def tokens(view: Dict[str, Any]) -> Set[str]:
    """Word-level surface vocabulary of an environment (names and labels only)."""
    obs = view["observations"]
    raw = [view["task"]["label"], view["task"]["output"], *obs["series"], *view["primitives"], *(r["id"] for r in obs["relations"]), *(e["action"] for e in obs["episodes"])]
    return {w for s in raw for w in re.split(r"[^a-z0-9]+", s.lower()) if len(w) > 2}


def jaccard(a: Set[str], b: Set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def _key(cfg: Gen.Config) -> str:
    return ",".join(str(cfg[k]) for k in Gen.KEYS)


class TaskMemoryAgent(SearchingAgent):
    """B3: remembers which architecture worked for which task (recognized by its vocabulary)."""
    kind = "task_memory"

    def fit(self, experience: List[Experience], lab: Any = None) -> None:
        self.memory = [(tokens(e.view), e.best_config) for e in experience]

    def snapshot(self):
        return {"entries": len(self.memory)}

    def act(self, ctx: Ctx) -> None:
        mine = tokens(ctx.view)
        sim, cfg = max(((jaccard(mine, t), c) for t, c in self.memory), key=lambda x: x[0])
        self.report = {"similarity": round(sim, 4), "reused": sim >= 0.3}
        if sim < 0.3:
            _, self.best_v = hill_climb(ctx, Gen.BASE, None, p_random=0.2)
            return
        cfg = Gen.normalize_config(cfg, ctx.primitives)
        ctx.declare(cfg)
        v, base_v = ctx.evaluate(cfg), ctx.evaluate(Gen.BASE)
        _, self.best_v = hill_climb(ctx, *((cfg, v) if v >= base_v else (dict(Gen.BASE), base_v)), p_random=0.2)


class ArchitectureMemoryAgent(SearchingAgent):
    """B4: remembers the best architectures themselves (as signature-level configurations) and tries them first."""
    kind = "architecture_memory"
    top_k = 5

    def fit(self, experience: List[Experience], lab: Any = None) -> None:
        count: Counter = Counter()
        value: Dict[str, float] = {}
        cfgs: Dict[str, Gen.Config] = {}
        for e in experience:
            k = _key(e.best_config)
            count[k] += 1
            value[k] = value.get(k, 0.0) + e.best_value - e.base_value
            cfgs[k] = e.best_config
        self.ranked = [cfgs[k] for k in sorted(cfgs, key=lambda k: (-count[k], -value[k], k))]

    def snapshot(self):
        return {"architectures": self.ranked}

    def act(self, ctx: Ctx) -> None:
        tried = {}
        ctx.evaluate(Gen.BASE)
        for cfg in self.ranked:
            cfg = Gen.normalize_config(cfg, ctx.primitives)
            if _key(cfg) in tried or len(tried) >= self.top_k:
                continue
            tried[_key(cfg)] = ctx.evaluate(cfg)
            ctx.declare(max(ctx.trace, key=lambda e: e["value"])["config"])
        best = max(ctx.trace, key=lambda e: e["value"])
        _, self.best_v = hill_climb(ctx, best["config"], best["value"], p_random=0.2)


class NeverAdaptAgent(ArchitectureMemoryAgent):
    """B7: deploys the most frequent training architecture once and never evaluates or changes anything."""
    kind = "never_adapt"

    def act(self, ctx: Ctx) -> None:
        ctx.declare(Gen.normalize_config(self.ranked[0], ctx.primitives))

    def phase2(self, ctx: Ctx, incumbent: Gen.Config) -> None:
        ctx.declare(incumbent)


class PrincipleMemoryAgent(SearchingAgent):
    """B5: AGM-style principles. "Transformation X is useful" with no antecedent, no contraindication, no
    counterfactual testing: mean training effect and how often it helped. Tests the most promising ones."""
    kind = "principle_memory"
    top_k = 5

    def fit(self, experience: List[Experience], lab: Any = None) -> None:
        n = len(experience)
        self.mean = {t: sum(e.effects[t] for e in experience) / n for t in TRANSFORMATIONS}
        self.rate = {t: sum(e.effects[t] > 0.02 for e in experience) / n for t in TRANSFORMATIONS}

    def snapshot(self):
        return {"mean": self.mean, "rate": self.rate}

    def transfer_scores(self, view):
        return dict(self.rate)

    def act(self, ctx: Ctx) -> None:
        base_v = ctx.evaluate(Gen.BASE)
        accepted = []
        for t in sorted(TRANSFORMATIONS, key=lambda t: -self.rate[t])[: self.top_k]:
            c, new = apply(t, Gen.BASE, ctx.primitives)
            if new == c:
                continue
            if ctx.mean(c) is None:
                ctx.evaluate(c)
            if ctx.evaluate(new) - ctx.mean(c) > 0.02:
                accepted.append(t)
        self.report = {"accepted": accepted}
        if accepted:
            ctx.evaluate(compose_from(accepted, ctx.primitives))
        best = max(ctx.trace, key=lambda e: e["value"])
        ctx.declare(best["config"])
        _, self.best_v = hill_climb(ctx, best["config"], best["value"], p_random=0.2)
