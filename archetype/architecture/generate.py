"""Architecture construction from interface signatures (learner-visible; shared by every agent).

A *config* is a small dict of organizational choices; ``compose`` turns it into a composition tree made of
the environment's own primitives, selected by signature only. Search baselines and ARCHETYPE use the same
configuration space, so no agent has a privileged parametrization.

    grade  executor grade index (ordered by price)        loop   0 | 2 | 3   critic loop iterations
    h      0..3  decomposition levels                     mem    0 | 1       retrieval before reasoning
    w      1..4  parallel workers (needs h >= 1)          route  0 | 2 | 3   conditional branches
    r      1..3  redundant independent solvers            tune   0 | 1       explore/exploit controller
    g      0..2  staged gates
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from archetype.architecture import graph as G

Config = Dict[str, int]
KEYS = ("grade", "h", "w", "r", "g", "loop", "mem", "route", "tune")
BASE: Config = {"grade": 0, "h": 0, "w": 1, "r": 1, "g": 0, "loop": 0, "mem": 0, "route": 0, "tune": 0}


def classify(primitives: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Group local primitives by what their signature lets them do (cheapest first)."""
    by_cost = sorted(primitives, key=lambda n: (primitives[n]["cost"], n))
    s = {n: primitives[n]["signature"] for n in by_cost}
    plain = [n for n in by_cost if s[n]["fan_out"] < 2 and not any(s[n][k] for k in ("fan_in", "gates", "stateful", "selects", "tunes"))]
    return {"exec": plain,
            "dec": [n for n in by_cost if s[n]["fan_out"] >= 2],
            "merge": sorted([n for n in by_cost if s[n]["fan_in"]], key=lambda n: (s[n]["gates"], primitives[n]["cost"], n)),
            "gate": sorted([n for n in by_cost if s[n]["gates"]], key=lambda n: (s[n]["fan_in"], primitives[n]["cost"], n)),
            "store": [n for n in by_cost if s[n]["stateful"]],
            "router": [n for n in by_cost if s[n]["selects"]],
            "tuner": [n for n in by_cost if s[n]["tunes"]]}


def options(primitives: Dict[str, Dict[str, Any]]) -> Dict[str, List[int]]:
    c = classify(primitives)
    return {"grade": list(range(len(c["exec"]))),
            "h": [0, 1, 2, 3] if c["dec"] else [0],
            "w": [1, 2, 3, 4] if c["dec"] and c["merge"] else [1],
            "r": [1, 2, 3] if c["merge"] else [1],
            "g": [0, 1, 2] if c["gate"] else [0],
            "loop": [0, 2, 3] if c["gate"] else [0],
            "mem": [0, 1] if c["store"] else [0],
            "route": [0, 2, 3] if c["router"] and len(c["exec"]) >= 2 else [0],
            "tune": [0, 1] if c["tuner"] else [0]}


def normalize_config(cfg: Config, primitives: Dict[str, Dict[str, Any]]) -> Config:
    """Clamp a config to what the local inventory can express (missing functions drop out)."""
    opt = options(primitives)
    out = {k: (cfg.get(k, BASE[k]) if cfg.get(k, BASE[k]) in opt[k] else max([v for v in opt[k] if v <= cfg.get(k, BASE[k])], default=opt[k][0])) for k in KEYS}
    if out["h"] == 0:
        out["w"] = 1
    return out


def space_size(primitives: Dict[str, Dict[str, Any]]) -> int:
    opt = options(primitives)
    n = 1
    for k in KEYS:
        if k != "w":
            n *= len(opt[k])
    # w only varies when h >= 1
    h_levels = len(opt["h"])
    return n // h_levels * (1 + (h_levels - 1) * len(opt["w"]))


def compose(cfg: Config, primitives: Dict[str, Dict[str, Any]]) -> G.ArchGraph:
    cfg = normalize_config(cfg, primitives)
    c = classify(primitives)
    ex = c["exec"]
    core = G.unit(ex[cfg["grade"]])
    if cfg["loop"]:
        core = G.loop(core, c["gate"][0], cfg["loop"])
    if cfg["g"] >= 1:
        core = G.serial([core, G.unit(c["gate"][0])])
    if cfg["w"] > 1:
        core = G.parallel([core] * cfg["w"], c["merge"][0])
    if cfg["h"] >= 1:
        core = G.hier(c["dec"][0], core, cfg["h"])
    if cfg["r"] > 1:        # redundancy replicates the whole (possibly decomposed) pipeline and takes a consensus
        core = G.parallel([core] * cfg["r"], c["merge"][0])
    if cfg["route"]:
        alt = [G.unit(ex[(cfg["grade"] + 1) % len(ex)])]
        if cfg["route"] >= 3:
            alt.append(G.serial([G.unit(ex[cfg["grade"]]), G.unit(c["gate"][0])]) if c["gate"] else G.unit(ex[(cfg["grade"] + 2) % len(ex)]))
        branches, seen = [core], {G._key(G.normalize(core))}
        for a in alt:
            if G._key(G.normalize(a)) not in seen:
                branches.append(a)
                seen.add(G._key(G.normalize(a)))
        if len(branches) >= 2:
            core = G.conditional(c["router"][0], branches)
    if cfg["tune"]:
        core = G.serial([G.unit(c["tuner"][0]), core])
    if cfg["mem"]:
        core = G.serial([G.unit(c["store"][0]), core])
    if cfg["g"] >= 2:
        core = G.serial([core, G.unit(c["gate"][0])])
    return G.ArchGraph(name="composed", root=G.normalize(core), metadata={"config": cfg})


def random_config(rng, primitives: Dict[str, Dict[str, Any]]) -> Config:
    opt = options(primitives)
    return normalize_config({k: rng.choice(opt[k]) for k in KEYS}, primitives)


def mutate(cfg: Config, rng, primitives: Dict[str, Dict[str, Any]], n: int = 1) -> Config:
    opt = options(primitives)
    out = dict(cfg)
    keys = [k for k in KEYS if len(opt[k]) > 1 and not (k == "w" and out["h"] == 0)]
    for k in rng.sample(keys, min(n, len(keys))) if keys else []:
        out[k] = rng.choice([v for v in opt[k] if v != out[k]])
    return normalize_config(out, primitives)


def random_tree(rng, primitives: Dict[str, Dict[str, Any]], max_depth: int = 3) -> G.Node:
    """Unconstrained random valid tree over the grammar (used to measure the size of the space)."""
    c = classify(primitives)
    names = list(primitives)

    def gen(d: int) -> G.Node:
        ops = ["unit"] if d >= max_depth else ["unit", "unit", "serial", "parallel", "conditional", "loop", "hier"]
        op = rng.choice(ops)
        if op == "serial":
            return G.serial([gen(d + 1) for _ in range(rng.randint(2, 3))])
        if op == "parallel" and c["merge"]:
            return G.parallel([gen(d + 1) for _ in range(rng.randint(2, 4))], rng.choice(c["merge"]))
        if op == "conditional" and c["router"]:
            return G.conditional(rng.choice(c["router"]), [gen(d + 1) for _ in range(rng.randint(2, 3))])
        if op == "loop" and c["gate"]:
            return G.loop(gen(d + 1), rng.choice(c["gate"]), rng.randint(2, 4))
        if op == "hier" and c["dec"]:
            return G.hier(rng.choice(c["dec"]), gen(d + 1), rng.randint(1, 3))
        return G.unit(rng.choice(names))

    return G.normalize(gen(0))
