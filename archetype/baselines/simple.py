"""Baselines without learned memory: B0 fixed, B1 adaptive workflow, B2 architecture search (two variants),
B6 always adapt. All use the shared configuration space and the shared local search."""
from __future__ import annotations

from archetype.architecture import generate as Gen
from archetype.baselines.base import Agent, Ctx, compose_from, hill_climb, measure_effects
from archetype.transfer.decisions import DROP

PRESETS = [dict(Gen.BASE), {**Gen.BASE, "grade": 1, "g": 1}, {**Gen.BASE, "h": 1, "w": 3, "g": 1}, {**Gen.BASE, "r": 3, "g": 1}, {**Gen.BASE, "grade": 1, "mem": 1}]


class SearchingAgent(Agent):
    """Common phase-2 behaviour: re-check the incumbent, search again only if its score dropped."""
    best_v = 0.0

    def phase2(self, ctx: Ctx, incumbent: Gen.Config) -> None:
        ctx.declare(incumbent)
        v = ctx.evaluate(incumbent)
        if self.best_v - v > DROP:
            _, self.best_v = hill_climb(ctx, incumbent, v, p_random=0.2)


class FixedAgent(Agent):
    kind = "fixed"

    def act(self, ctx: Ctx) -> None:
        ctx.declare(PRESETS[1])


class AdaptiveAgent(SearchingAgent):
    """B1: a hand-written workflow library; picks the best preset, re-picks on degradation."""
    kind = "adaptive"

    def act(self, ctx: Ctx) -> None:
        scored = [(ctx.evaluate(p), i) for i, p in enumerate(PRESETS)]
        self.best_v, i = max(scored)
        ctx.declare(PRESETS[i])

    def phase2(self, ctx: Ctx, incumbent: Gen.Config) -> None:
        ctx.declare(incumbent)
        if self.best_v - ctx.evaluate(incumbent) > DROP:
            self.act(ctx)


class SearchAgent(SearchingAgent):
    """B2: random restarts + local mutation over the full configuration space, whole budget."""
    kind = "search"

    def act(self, ctx: Ctx) -> None:
        _, self.best_v = hill_climb(ctx, Gen.BASE, None, p_random=0.2)


class ScreenSearchAgent(SearchingAgent):
    """B2 (strong variant): one-factor screening, compose what helped, then local search. No memory."""
    kind = "search_screen"

    def act(self, ctx: Ctx) -> None:
        base_v, eff = measure_effects(ctx, reps=1)
        start = compose_from([t for t, d in eff.items() if d > 0.02], ctx.primitives)
        v = ctx.evaluate(start)
        best = max(ctx.trace, key=lambda e: e["value"])
        ctx.declare(best["config"])
        _, self.best_v = hill_climb(ctx, best["config"], best["value"])


class AlwaysAdaptAgent(SearchAgent):
    """B6: searches with the whole budget in every phase, whether or not anything changed."""
    kind = "always_adapt"

    def phase2(self, ctx: Ctx, incumbent: Gen.Config) -> None:
        _, self.best_v = hill_climb(ctx, incumbent, None, p_random=0.2)
