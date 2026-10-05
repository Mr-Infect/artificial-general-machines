"""Hidden architecture fitness (spec §23). EVALUATOR ONLY.

    utility = task value(structural match between genome and organization)
              + throughput - interference - integration loss - resource cost,   plus evaluation noise

``features`` come from ``archetype.architecture.roles.features``. The function is never shown to an
agent; agents see only noisy scores on a surface-specific scale. Constants were calibrated on
development seeds *before* registration (docs/archetype_registration.md) and are frozen afterwards.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from archetype.latent_structure.genome import EnvironmentGenome
from archetype.util import clip

FITNESS_VERSION = "archetype-fitness-0.1"
_REDUNDANCY = {1: 0.0, 2: 0.25, 3: 0.5, 4: 0.6}
_CATCH = {0: 0.0, 1: 0.55, 2: 0.75, 3: 0.85}
_ROUTE = {0: 0.0, 1: 0.0, 2: 0.6, 3: 0.8}


def breakdown(g: EnvironmentGenome, f: Dict[str, Any]) -> Dict[str, float]:
    """Noise-free expected utility in [0, 1] with its components."""
    if f["n_exec"] == 0:
        return {"utility": 0.0, "p_fail": 1.0, "raw": -1.0}
    dep, br, noise, tc, vol = g["dependency_depth"], g["branching_factor"], g["observation_noise"], g["temporal_correlation"], g["state_volatility"]
    vcost, rev, res, adv, delay = g["verification_cost"], g["action_reversibility"], g["resource_constraint"], g["adversariality"], g["delayed_feedback"]
    decay, par, coup, unc, fc = g["information_decay"], g["parallelizability"], g["coupling"], g["uncertainty"], g["failure_cost"]
    h, w, r, gates, loop, mem, route, tune = f["h"], f["w"], f["r"], f["g"], f["loop"], f["mem"], f["route"], f["tune"]

    # per-unit error sources (quadratic: negligible at neutral levels, dominant when a property is high)
    e_noise, e_unc, e_adv = 0.45 * noise ** 2, 0.45 * unc ** 2, 0.30 * adv ** 2
    e_skill, e_vol, e_delay = 0.25 * (1 - f["exec_strength"]), 0.40 * vol ** 2, 0.35 * delay ** 2 * (1 - 0.3 * rev)
    extra, overhead, bonus = 0.0, 0.0, 0.0
    # redundancy -> consensus: independent errors cancel unless solvers are coupled
    rho = _REDUNDANCY[r] * (1 - 0.85 * coup) * (1.0 if f["has_agg"] else 0.5)
    e_noise *= 1 - rho
    e_adv *= 1 - 0.5 * rho
    overhead += 0.02 * (r - 1)
    # critic loop: revision needs immediate feedback
    if loop:
        k = 0.6 * (1 - 0.5 ** (loop - 1)) * (1 - delay)
        e_unc *= 1 - k
        e_skill *= 1 - k
        overhead += 0.03
    # explore/exploit controller: exploration resolves uncertainty when actions can be undone; it always pays a tax
    if tune:
        e_unc *= 1 - 0.6 * rev
        extra += 0.20 * (1 - rev)
        overhead += 0.04
    # memory: context denoises when the past is informative; stale memory misleads
    if mem:
        e_noise *= 1 - 0.6 * mem * tc * (1 - decay)
        e_skill *= 1 - 0.4 * mem * tc * (1 - decay)
        extra += mem * (0.30 * vol * decay + 0.12 * decay)
        bonus += 0.18 * mem * tc * (1 - decay)
    # adaptive branching: follows regime changes unless an adversary games the routing; misroutes in calm regimes
    if route >= 2:
        e_vol *= 1 - _ROUTE[route] * (1 - adv)
        extra += 0.08 * (1 - vol) + 0.10 * adv
        overhead += 0.03
    # planning ahead: only useful when the future is predictable; rigid plans hurt under uncertainty
    if h >= 1:
        e_delay *= 1 - 0.75 * (1 - unc)
        extra += 0.10 * unc ** 2
    p_unit = 1 - clip(e_noise + e_unc + e_adv + e_skill + e_vol + e_delay + extra, 0.0, 0.95)
    # dependency compounding, relieved by decomposition
    chain = 1 + 4 * dep * dep / (1 + 1.5 * h)
    q = p_unit ** chain
    # verification: caught errors are neutral, uncaught errors cost; every gate also rejects some good work
    catch = _CATCH[gates]
    if loop and not gates:
        catch = 0.3
    penalty_scale = 0.15 + 1.6 * fc
    task = q * (1 - 0.10 * gates) - (1 - q) * (1 - catch) * penalty_scale
    # parallel workers: throughput vs interference
    spread = 1 - 1 / w
    throughput = 0.40 * par * spread * (0.5 + 0.5 * br)
    interference = 0.60 * coup * spread * (0.7 if f["has_agg"] else 1.0)
    integration = 0.04 * h
    verification_time = 0.10 * vcost * (gates + (1 if loop else 0))
    resource = (0.006 + 0.03 * res) * f["cost"]
    raw = task + bonus + throughput - interference - integration - verification_time - resource - overhead
    p_fail = clip(0.003 * f["n_nodes"] * (0.5 + vol), 0.0, 0.5)
    if f["memory"] > 40 * (1.6 - res):
        p_fail = max(p_fail, 0.8)
    u = (1 - p_fail) / (1 + math.exp(-3.0 * (raw - 0.15)))      # smooth squashing: no floor or ceiling plateaus
    return {"utility": u, "p_fail": p_fail, "raw": raw, "task": task, "q": q, "p_unit": p_unit, "throughput": throughput,
            "interference": interference, "resource": resource}


def true_utility(g: EnvironmentGenome, f: Dict[str, Any]) -> float:
    return breakdown(g, f)["utility"]


def noise_sd(g: EnvironmentGenome) -> float:
    return 0.010 + 0.018 * g["uncertainty"] + 0.012 * g["observation_noise"]


def sample(g: EnvironmentGenome, f: Dict[str, Any], rng) -> Dict[str, Any]:
    """One noisy evaluation: returns utility in [0, 1] and whether the run failed."""
    b = breakdown(g, f)
    if rng.random() < b["p_fail"]:
        return {"utility": 0.0, "failed": True}
    conditional = b["utility"] / (1 - b["p_fail"]) if b["p_fail"] < 1 else 0.0
    return {"utility": clip(conditional + rng.gauss(0.0, noise_sd(g))), "failed": False}
