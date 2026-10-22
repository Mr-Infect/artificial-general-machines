"""Transfer baselines: B8 random structural transfer, B9 surface-similarity transfer."""
from __future__ import annotations

from typing import Any, Dict, List

from archetype.architecture import generate as Gen
from archetype.baselines.base import Ctx, Experience, hill_climb
from archetype.baselines.memory_agents import jaccard, tokens
from archetype.baselines.simple import SearchingAgent
from archetype.learner.transformations import TRANSFORMATIONS, present


def shape_descriptor(view: Dict[str, Any]) -> List[float]:
    obs, task = view["observations"], view["task"]
    return [len(next(iter(obs["series"].values()))), len(obs["series"]), len(obs["relations"]), len(obs["episodes"]), len(view["primitives"]),
            task["score_range"][0], task["score_range"][1], 1.0 if task["objective"] == "maximize" else 0.0, float(len(task["label"]))]


def surface_similarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """Similarity of what two environments look like: vocabulary overlap and shape/scale agreement. No structure."""
    sa, sb = shape_descriptor(a), shape_descriptor(b)
    shape = sum(1 - abs(x - y) / max(abs(x), abs(y), 1e-9) for x, y in zip(sa, sb)) / len(sa)
    return 0.6 * jaccard(tokens(a), tokens(b)) + 0.4 * shape


class _ReuseThenSearch(SearchingAgent):
    def _reuse(self, ctx: Ctx, cfg: Gen.Config) -> None:
        cfg = Gen.normalize_config(cfg, ctx.primitives)
        ctx.declare(cfg)
        v, base_v = ctx.evaluate(cfg), ctx.evaluate(Gen.BASE)
        _, self.best_v = hill_climb(ctx, *((cfg, v) if v >= base_v else (dict(Gen.BASE), base_v)), p_random=0.2)


class RandomTransferAgent(_ReuseThenSearch):
    """B8: transfers the best architecture of a randomly chosen training environment."""
    kind = "random_transfer"

    def fit(self, experience: List[Experience], lab: Any = None) -> None:
        self.configs = [e.best_config for e in experience]

    def transfer_scores(self, view):
        return None

    def act(self, ctx: Ctx) -> None:
        self._reuse(ctx, ctx.rng.choice(self.configs))


class SurfaceSimilarityAgent(_ReuseThenSearch):
    """B9: transfers from the training environment that looks most similar on the surface."""
    kind = "surface_similarity"

    def fit(self, experience: List[Experience], lab: Any = None) -> None:
        self.memory = [(e.view, e.best_config) for e in experience]

    def _nearest(self, view):
        return max(((surface_similarity(view, v), c) for v, c in self.memory), key=lambda x: x[0])

    def transfer_scores(self, view):
        sim, cfg = self._nearest(view)
        return {t: sim * (1.0 if present(t, cfg) else 0.0) for t in TRANSFORMATIONS}

    def act(self, ctx: Ctx) -> None:
        sim, cfg = self._nearest(ctx.view)
        self.report = {"similarity": round(sim, 4)}
        self._reuse(ctx, cfg)
