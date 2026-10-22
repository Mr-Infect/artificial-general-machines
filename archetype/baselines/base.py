"""Agent protocol shared by every ARCHETYPE agent (same idea as baselines/base.py of the AGM lab).

Agents never hold an Environment. They receive a ``Ctx``: the learner-visible view (observations, task
specification, local primitives), a counted ``evaluate`` callback and ``declare`` for their incumbent.
Everything an agent may know is reachable from here; nothing latent is.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from archetype.architecture import generate as Gen
from archetype.architecture.graph import ArchGraph
from archetype.learner.transformations import TRANSFORMATIONS, apply


class BudgetExhausted(Exception):
    pass


class Ctx:
    def __init__(self, view: Dict[str, Any], budget: int, evaluate: Callable[[ArchGraph], Dict[str, Any]],
                 declare: Callable[[ArchGraph], None], rng, phase: int = 1):
        self.view, self.budget, self.rng, self.phase = view, budget, rng, phase
        self.primitives: Dict[str, Dict[str, Any]] = view["primitives"]
        self.used = 0
        self._evaluate, self._declare = evaluate, declare
        self.trace: List[Dict[str, Any]] = []
        self.cache: Dict[str, List[float]] = {}

    @property
    def remaining(self) -> int:
        return self.budget - self.used

    def value(self, result: Dict[str, Any]) -> float:
        """Normalize a surface score to [0, 1], higher is better, using only the task specification."""
        lo, hi = self.view["task"]["score_range"]
        v = (result["score"] - lo) / (hi - lo)
        return v if self.view["task"]["objective"] == "maximize" else 1 - v

    def evaluate(self, cfg: Gen.Config) -> float:
        """One counted evaluation of the architecture composed from ``cfg``; returns the normalized value."""
        if self.used >= self.budget:
            raise BudgetExhausted()
        cfg = Gen.normalize_config(cfg, self.primitives)
        res = self._evaluate(Gen.compose(cfg, self.primitives))
        self.used += 1
        v = self.value(res)
        self.cache.setdefault(_k(cfg), []).append(v)
        self.trace.append({"n": self.used, "config": cfg, "value": round(v, 5), "failed": res["failed"]})
        return v

    def mean(self, cfg: Gen.Config) -> Optional[float]:
        vals = self.cache.get(_k(Gen.normalize_config(cfg, self.primitives)))
        return sum(vals) / len(vals) if vals else None

    def declare(self, cfg: Gen.Config) -> None:
        self._declare(Gen.compose(cfg, self.primitives))


def _k(cfg: Gen.Config) -> str:
    return ",".join(str(cfg[k]) for k in Gen.KEYS)


@dataclass
class Experience:
    """What the shared training exploration recorded in one training environment (identical for all agents)."""
    token: str
    view: Dict[str, Any]
    base_value: float
    effects: Dict[str, float]                                   # transformation -> mean observed delta (paired, replicated)
    evaluated: List[Tuple[Gen.Config, float]] = field(default_factory=list)
    best_config: Gen.Config = field(default_factory=dict)
    best_value: float = 0.0
    evaluations: int = 0


def measure_effects(ctx: Ctx, reps: int = 2, only: Optional[List[str]] = None) -> Tuple[float, Dict[str, float]]:
    """Paired, replicated measurement of each transformation's effect in its context."""
    out: Dict[str, float] = {}
    for _ in range(reps):
        ctx.evaluate(Gen.BASE)
    for t in (only or list(TRANSFORMATIONS)):
        c, new = apply(t, Gen.BASE, ctx.primitives)
        if new == c:
            out[t] = 0.0
            continue
        while len(ctx.cache.get(_k(c), [])) < reps:
            ctx.evaluate(c)
        for _ in range(reps):
            ctx.evaluate(new)
        out[t] = ctx.mean(new) - ctx.mean(c)
    return ctx.mean(Gen.BASE), out


def compose_from(transformations: List[str], primitives: Dict[str, Dict[str, Any]]) -> Gen.Config:
    cfg = dict(Gen.BASE)
    for t in transformations:
        key, value, override = TRANSFORMATIONS[t]
        for k, v in override.items():
            cfg[k] = max(cfg[k], v)
        cfg[key] = max(cfg[key], value)
    return Gen.normalize_config(cfg, primitives)


def hill_climb(ctx: Ctx, start: Gen.Config, start_value: Optional[float], patience: Optional[int] = None,
               p_random: float = 0.0, reserve: int = 0) -> Tuple[Gen.Config, float]:
    """Shared local search over the configuration space (used by every searching agent).

    Evaluations are noisy, so an apparent improvement is confirmed by a second evaluation and configurations
    are compared by the mean of everything measured for them. ``patience`` (adaptation economics) stops after
    that many consecutive candidates that failed to improve; ``None`` spends the whole budget."""
    best = Gen.normalize_config(start, ctx.primitives)
    if ctx.mean(best) is None and ctx.remaining > reserve:
        ctx.evaluate(best)
    best_v = ctx.mean(best) if ctx.mean(best) is not None else (start_value or 0.0)
    ctx.declare(best)
    stale = 0
    while ctx.remaining > reserve and (patience is None or stale < patience):
        cand = Gen.random_config(ctx.rng, ctx.primitives) if ctx.rng.random() < p_random else Gen.mutate(best, ctx.rng, ctx.primitives, n=1 if ctx.rng.random() < 0.7 else 2)
        if cand == best:
            continue
        v = ctx.evaluate(cand)
        if v > best_v and ctx.remaining > reserve:
            ctx.evaluate(cand)                      # confirm
        if ctx.mean(cand) > best_v:
            best, best_v, stale = cand, ctx.mean(cand), 0
            ctx.declare(best)
        else:
            stale += 1
    return best, best_v


def explore(ctx: Ctx) -> Experience:
    """Neutral training exploration: screen every transformation, compose the positive ones, then local search."""
    base_v, eff = measure_effects(ctx, reps=2)
    start = compose_from([t for t, d in eff.items() if d > 0.02], ctx.primitives)
    v0 = ctx.evaluate(start)
    cands = [(Gen.BASE, base_v), (start, v0)]
    best, best_v = max(cands, key=lambda x: x[1])
    best, best_v = hill_climb(ctx, best, best_v, reserve=3)
    # re-check the top configurations once to damp the winner's curse
    top = sorted({_k(e["config"]): e["config"] for e in ctx.trace}.values(), key=lambda c: -ctx.mean(c))[:3]
    for c in top:
        if ctx.remaining > 0:
            ctx.evaluate(c)
    best = max(top, key=lambda c: ctx.mean(c))
    evaluated = [(e["config"], e["value"]) for e in ctx.trace]
    return Experience(token=ctx.view["token"], view=ctx.view, base_value=base_v, effects=eff, evaluated=evaluated,
                      best_config=best, best_value=ctx.mean(best), evaluations=ctx.used)


class Agent:
    """Base class. ``fit`` sees only the shared training experience (and, for ARCHETYPE, the intervention lab)."""
    kind = "abstract"
    uses_lab = False

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name, self.config = name, dict(config or {})
        self.report: Dict[str, Any] = {}

    def fit(self, experience: List[Experience], lab: Any = None) -> None:
        return None

    def snapshot(self) -> Dict[str, Any]:
        """Frozen learned state (hashed by the protocol after training)."""
        return {}

    def transfer_scores(self, view: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Zero-evaluation prediction, per transformation, that it will help here (None: agent makes no such claim)."""
        return None

    def act(self, ctx: Ctx) -> None:
        raise NotImplementedError

    def phase2(self, ctx: Ctx, incumbent: Gen.Config) -> None:
        """Called after a possible hidden regime shift with fresh observations. Default: keep the incumbent."""
        ctx.declare(incumbent)
