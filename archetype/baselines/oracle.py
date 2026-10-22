"""B10 latent-oracle transfer: an upper bound that READS THE HIDDEN GENOME.

Analysis only. It is the single agent allowed to touch evaluator internals, it is excluded from every
criterion, and the experiment protocol attaches the environment to it explicitly.
"""
from __future__ import annotations

from archetype.architecture import generate as Gen
from archetype.baselines.base import Agent, Ctx
from archetype.metrics.reference import reference_optimum


class LatentOracleAgent(Agent):
    kind = "latent_oracle"
    privileged = True

    def attach(self, env) -> None:
        self._env = env

    def act(self, ctx: Ctx) -> None:
        ctx.declare(reference_optimum(self._env)["config"])

    def phase2(self, ctx: Ctx, incumbent: Gen.Config) -> None:
        self.act(ctx)
