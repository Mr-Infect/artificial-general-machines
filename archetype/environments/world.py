"""Environment (evaluator side) and the learner-visible view (spec §20). 

``Environment`` owns the genome, the role inventory and the hidden fitness. Agents never hold it: the
experiment protocol passes them ``Environment.view()`` (plain JSON-able data) and an ``evaluate`` closure.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from archetype.architecture import graph as G
from archetype.architecture import primitives as P
from archetype.architecture import roles as R
from archetype.environments import surface as S
from archetype.latent_structure import fitness as F
from archetype.latent_structure.families import FAMILIES, Family, sample_genome
from archetype.latent_structure.genome import PROPERTIES, EnvironmentGenome
from archetype.util import rng_for, stable_hash


class Environment:
    def __init__(self, family: Family, seed: int, surface_index: int, genome: Optional[EnvironmentGenome] = None, window: int = 0,
                 obs_genome: Optional[EnvironmentGenome] = None):
        self.family, self.seed, self.surface_index, self.window = family, seed, surface_index, window
        self.genome = genome or sample_genome(family, seed)
        self.key = (seed, family.id, surface_index)
        # false analogies share theme AND shapes with the training family they mimic
        shape_owner = family.matched if family.world.startswith("false") else family.id
        self.scrambled = surface_index % 3 == 2
        self.shape = S.shape(rng_for("shape", seed, shape_owner, surface_index))
        self.surface_seed = stable_hash(("surface", *self.key))
        vocab = S.vocabulary(family.theme, self.scrambled, rng_for("vocab", *self.key))
        self.task = S.task_spec(self.shape, vocab)
        self.inventory = P.make_inventory(rng_for("inventory", *self.key), vocab[3:20], self.genome["verification_cost"])
        self.primitives = P.public(self.inventory, self.shape["currency"], rng_for("public", *self.key))
        # obs_genome is a CONTROL only (sanity check): observations generated from a different structure than the fitness
        self.observations = S.observations(obs_genome or self.genome, self.shape, vocab[20:], rng_for("obs", *self.key, window))
        self.token = stable_hash(("token", *self.key, "archetype-opaque"))
        self.evaluations = 0

    # ------------------------------------------------------------------ learner-visible
    def view(self) -> Dict[str, Any]:
        return {"token": self.token, "task": dict(self.task), "observations": self.observations, "primitives": self.primitives, "limits": dict(G.LIMITS)}

    def evaluate(self, arch: G.ArchGraph, rng) -> Dict[str, Any]:
        """One counted, noisy evaluation. Returns only surface-level outcomes."""
        self.evaluations += 1
        errors = G.validate(arch.root, self.primitives)
        if errors:
            return {"valid": False, "errors": errors, "failed": True, "score": S.to_score(0.0, self.shape), "cost": 0.0, "latency": 0.0, "memory": 0.0, "operations": 0}
        f = R.features(arch.root, self.inventory)
        out = F.sample(self.genome, f, rng)
        return {"valid": True, "errors": [], "failed": out["failed"], "score": round(S.to_score(out["utility"], self.shape), 6),
                "cost": round(f["cost"] * self.shape["currency"], 6), "latency": round(f["latency"], 3), "memory": round(f["memory"], 3),
                "operations": f["n_ops"]}

    # ------------------------------------------------------------------ evaluator-only
    def features(self, arch: G.ArchGraph) -> Dict[str, Any]:
        return R.features(arch.root, self.inventory)

    def true_utility(self, arch: G.ArchGraph) -> float:
        if G.validate(arch.root, self.primitives):
            return 0.0
        return F.true_utility(self.genome, self.features(arch))

    def role_tree(self, arch: G.ArchGraph) -> G.Node:
        return R.role_tree(arch.root, self.inventory)

    def with_genome(self, genome: EnvironmentGenome, window: Optional[int] = None) -> "Environment":
        """Same surface (names, shapes, inventory layout), different latent structure: interventions and regime shifts."""
        return Environment(self.family, self.seed, self.surface_index, genome=genome, window=self.window if window is None else window)

    def provenance(self) -> Dict[str, Any]:
        return {"family": self.family.id, "world": self.family.world, "seed": self.seed, "surface_index": self.surface_index, "surface_seed": self.surface_seed,
                "genome_hash": self.genome.hash(), "scrambled": self.scrambled, "theme": self.family.theme, "window": self.window}


class Lab:
    """Intervention interface offered to agents during TRAINING only (spec §27).

    Agents address latent properties through anonymous knob indices whose meaning they do not know; the
    permutation is seeded per seed. ``intervene`` returns a new environment with exactly one property moved.
    """

    def __init__(self, seed: int):
        self.seed = seed
        self._props = list(PROPERTIES)
        rng_for("knobs", seed).shuffle(self._props)
        self._envs: Dict[str, Environment] = {}
        self.log: List[Dict[str, Any]] = []

    @property
    def n_knobs(self) -> int:
        return len(self._props)

    def register(self, env: Environment) -> None:
        self._envs[env.token] = env

    def intervene(self, token: str, knob: int, direction: str) -> Environment:
        env = self._envs[token]
        prop = self._props[knob]
        rng = rng_for("intervene", self.seed, token, knob, direction)
        value = round(rng.uniform(0.8, 0.95) if direction == "up" else rng.uniform(0.05, 0.2), 4)
        new = env.with_genome(env.genome.intervene(prop, value))
        new.token = stable_hash(("cf", token, knob, direction))
        self._envs[new.token] = new
        self.log.append({"source": token, "token": new.token, "property": prop, "direction": direction, "value": value})
        return new


def make_env(family_id: str, seed: int, surface_index: int) -> Environment:
    return Environment(FAMILIES[family_id], seed, surface_index)
