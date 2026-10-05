"""Surface realization (spec §4, §5, §21): EnvironmentStructure -> TaskSurface. EVALUATOR ONLY.

Randomized per surface: vocabulary and tokens, feature names, feature order, numeric ranges and signs,
series length and width, item ids, task and output labels, score scale and direction, primitive names,
cost currency. Only OBSERVABLE genome properties influence the observation channels; hidden-only
properties leave no trace here by construction (a test checks it).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List

from archetype.latent_structure.genome import HIDDEN_ONLY, EnvironmentGenome

THEMES: Dict[str, List[str]] = {
    "network": "packet flow port router latency probe subnet burst jitter trace socket relay beacon tunnel uplink mesh gateway payload frame hop queue link node peer".split(),
    "science": "assay sample reagent trial cohort titrate spectrum isotope probe culture buffer dose replicate control yield plate strain batch signal blank column phase solvent run".split(),
    "logistics": "cargo depot route pallet shift dock truck lane crate manifest slot convoy stock parcel hub load fleet yard bay order pick wave tier haul".split(),
    "finance": "ledger trade hedge quote spread yield bond margin swap tick book order float asset desk fund lot basis curve strike rate index fee cap".split(),
    "medical": "triage ward chart dose vital scan panel symptom consult referral bed nurse round lab swab pulse intake record case clinic visit screen risk score".split(),
    "agriculture": "furrow seed plot harvest soil sprout irrigate orchard graze silo crop pest yield mulch barn herd tiller acre root bloom frost compost seedbed trough".split(),
    "energy": "turbine grid feeder breaker load reactor panel inverter storage peak outage substation meter flux dam boiler rotor relay fuel cell demand ramp tariff phase".split(),
    "legal": "clause brief docket statute filing motion verdict counsel claim appeal exhibit precedent ruling writ tort lien deposition hearing waiver draft notice plea bench code".split(),
    "manufacturing": "lathe weld press fixture spindle batch gauge mold conveyor rivet tolerance casting jig kiln forge reel coil stamp die shim bore scrap cell torque".split(),
    "gaming": "quest raid loot spawn guild rune level boss arena patch skill mana lobby shard token realm duel craft buff totem scout siege relic combo".split(),
}
TASK_FORMS = ["decide whether each {a} {b} needs action", "rank every {a} by {b} priority", "produce a {a} plan across {b} windows",
              "estimate the {a} value of each {b}", "flag every {a} whose {b} is abnormal", "assign each {a} to a {b}"]
OUTPUT_FORMS = ["binary label", "ordered list", "assignment table", "numeric estimate", "set of flags"]


def vocabulary(theme: str, scrambled: bool, rng, n: int = 80) -> List[str]:
    """A pool of unique tokens. Scrambled surfaces carry no theme at all (random hex)."""
    if scrambled:
        return ["x" + "".join(rng.choice("0123456789abcdef") for _ in range(6)) + str(i) for i in range(n)]
    words = THEMES[theme]
    pool = {f"{rng.choice(words)}_{rng.choice(words)}" for _ in range(n * 3)}
    pool = sorted(pool)
    rng.shuffle(pool)
    return pool[:n]


def shape(rng) -> Dict[str, Any]:
    lo = rng.choice([0.0, 0.0, 1.0, -1.0, 10.0])
    return {"n": rng.randint(120, 260), "features": rng.randint(3, 8), "items": rng.randint(14, 30), "episodes": rng.randint(30, 60),
            "score_lo": lo, "score_hi": lo + rng.choice([1.0, 5.0, 10.0, 100.0]), "maximize": rng.random() < 0.6,
            "task_form": rng.randrange(len(TASK_FORMS)), "output_form": rng.randrange(len(OUTPUT_FORMS)), "currency": 10 ** rng.uniform(-1, 2)}


def task_spec(sh: Dict[str, Any], vocab: List[str]) -> Dict[str, Any]:
    return {"label": TASK_FORMS[sh["task_form"]].format(a=vocab[0], b=vocab[1]), "output": OUTPUT_FORMS[sh["output_form"]] + " per " + vocab[2],
            "objective": "maximize" if sh["maximize"] else "minimize", "score_range": [sh["score_lo"], sh["score_hi"]]}


def to_score(u: float, sh: Dict[str, Any]) -> float:
    span = sh["score_hi"] - sh["score_lo"]
    return sh["score_lo"] + span * (u if sh["maximize"] else 1 - u)


def observations(genome: EnvironmentGenome, sh: Dict[str, Any], names: List[str], rng) -> Dict[str, Any]:
    g = genome.as_dict()
    for p in HIDDEN_ONLY:          # make it impossible for a hidden-only property to reach an observation
        g.pop(p)
    names = list(names)
    # --- series ---------------------------------------------------------------
    n, F = sh["n"], sh["features"]
    phi = 0.05 + 0.9 * g["temporal_correlation"]
    innov = math.sqrt(1 - phi * phi)
    p_jump = 0.002 + 0.06 * g["state_volatility"]
    nsd = 0.2 + 2.5 * g["observation_noise"]
    x, level, sig = 0.0, 0.0, []
    for _ in range(n):
        x = phi * x + innov * rng.gauss(0, 1)
        if rng.random() < p_jump:
            level += rng.gauss(0, 3)
        sig.append(x + level)
    series: Dict[str, List[float]] = {}
    for _ in range(F):
        a = rng.choice([-1, 1]) * 10 ** rng.uniform(-2, 3)
        b = rng.uniform(-5, 5) * abs(a)
        load = rng.uniform(0.6, 1.4)
        series[names.pop()] = [round(a * (load * s + nsd * rng.gauss(0, 1)) + b, 6) for s in sig]
    # --- relations (work-item dependency graph) ---------------------------------
    m = sh["items"]
    ids = [names.pop() for _ in range(m)]
    n_iso = int(round(g["parallelizability"] * 0.7 * m))
    chained = ids[n_iso:]
    layers_n = max(1, min(len(chained), 1 + int(round(g["dependency_depth"] * 6))))
    layers: List[List[str]] = [[] for _ in range(layers_n)]
    for i, it in enumerate(chained):
        layers[i % layers_n if i < layers_n else rng.randrange(layers_n)].append(it)
    relations = [{"id": it, "requires": []} for it in ids[:n_iso]]
    for li, layer in enumerate(layers):
        for it in layer:
            req: List[str] = []
            if li > 0:
                k = 1 + (rng.random() < g["branching_factor"]) + (rng.random() < 0.5 * g["branching_factor"])
                req = rng.sample(layers[li - 1], min(k, len(layers[li - 1])))
            relations.append({"id": it, "requires": sorted(req)})
    rng.shuffle(relations)
    # --- episodes (action / outcome log) -----------------------------------------
    actions = [names.pop() for _ in range(4)]
    scale = 10 ** rng.uniform(-1, 2)
    episodes = []
    for _ in range(sh["episodes"]):
        s = rng.gauss(0, 1)
        episodes.append({"action": rng.choice(actions), "lag": int(rng.expovariate(1 / (0.5 + 8 * g["delayed_feedback"]))),
                         "reverted": rng.random() < g["action_reversibility"], "signal": round(scale * s, 5), "outcome": round(scale * (s + 0.3 * rng.gauss(0, 1)), 5)})
    limits = {"cap": round(sh["currency"] * 30 * (1.3 - g["resource_constraint"]), 5)}
    return {"series": series, "relations": relations, "episodes": episodes, "limits": limits}
