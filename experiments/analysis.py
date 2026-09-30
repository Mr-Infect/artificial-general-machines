"""Cross-seed analysis of the v0.2 experiment program (spec sections 12-13, 21-28, 35).

    python -m experiments.analysis --db results/v02/db/*.sqlite --out results/v02/analysis

Reads every finished experiment from the given databases, groups by experiment name, and produces
results/v02/analysis/analysis.json + analysis.md. Nothing here decides success; the success-criteria
table reports, per criterion, the measured evidence and whether the pre-registered threshold was met.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from core.db import Database

ROOT = Path(__file__).resolve().parent.parent
METRICS = ["quality_mean", "quality_min", "time_to_target_logical_s", "architecture_evaluations", "adaptation_cost", "total_cost", "cpu_time_s",
           "max_memory_mb", "wall_used_s", "failures", "constraint_violations", "novelty_mean", "distinct_architectures"]
EXTRA = ["evaluations_to_target", "principle_reuse", "principles_created", "final_distance_to_initial", "max_distance_to_initial", "mean_decision_error", "mean_cost_estimate_error"]


# ------------------------------------------------------------------ statistics

def describe(xs: Sequence[Optional[float]], n_boot: int = 2000, seed: int = 0) -> Dict[str, Any]:
    vals = [float(x) for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    n = len(vals)
    if n == 0:
        return {"n": 0, "n_missing": len(xs), "mean": None, "median": None, "sd": None, "ci95": [None, None]}
    rng = random.Random(seed)
    if n > 1:
        boots = sorted(statistics.fmean(rng.choices(vals, k=n)) for _ in range(n_boot))
        ci = [boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]]
        sd = statistics.stdev(vals)
    else:
        ci, sd = [vals[0], vals[0]], 0.0
    return {"n": n, "n_missing": len(xs) - n, "mean": statistics.fmean(vals), "median": statistics.median(vals), "sd": sd, "ci95": ci,
            "min": min(vals), "max": max(vals)}


def paired(a: Sequence[Optional[float]], b: Sequence[Optional[float]], n_boot: int = 2000, seed: int = 0) -> Dict[str, Any]:
    """Paired delta b - a over seeds where both are present; bootstrap CI; Cohen's d for paired data;
    sign counts; fraction of pairs where both are missing (e.g. target never reached)."""
    pairs = [(float(x), float(y)) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pairs)
    out: Dict[str, Any] = {"n_pairs": n, "n_total": len(a), "n_both_missing": sum(1 for x, y in zip(a, b) if x is None and y is None),
                           "n_only_a": sum(1 for x, y in zip(a, b) if x is not None and y is None), "n_only_b": sum(1 for x, y in zip(a, b) if x is None and y is not None)}
    if n == 0:
        out.update({"delta_mean": None, "delta_median": None, "ci95": [None, None], "effect_size_d": None, "positive": 0, "negative": 0, "zero": 0})
        return out
    d = [y - x for x, y in pairs]
    rng = random.Random(seed)
    if n > 1:
        boots = sorted(statistics.fmean(rng.choices(d, k=n)) for _ in range(n_boot))
        ci = [boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot) - 1]]
        sd = statistics.stdev(d)
        eff = (statistics.fmean(d) / sd) if sd > 1e-12 else (0.0 if abs(statistics.fmean(d)) < 1e-12 else math.copysign(float("inf"), statistics.fmean(d)))
    else:
        ci, eff = [d[0], d[0]], None
    out.update({"delta_mean": statistics.fmean(d), "delta_median": statistics.median(d), "ci95": ci, "effect_size_d": None if eff is None or math.isinf(eff) else eff,
                "effect_size_note": "infinite (zero variance)" if eff is not None and math.isinf(eff) else None,
                "positive": sum(1 for x in d if x > 1e-12), "negative": sum(1 for x in d if x < -1e-12), "zero": sum(1 for x in d if abs(x) <= 1e-12),
                "mean_a": statistics.fmean(x for x, _ in pairs), "mean_b": statistics.fmean(y for _, y in pairs)})
    return out


def ci_excludes_zero(p: Dict[str, Any]) -> Optional[bool]:
    lo, hi = p.get("ci95", [None, None])
    if lo is None or hi is None:
        return None
    return lo > 0 or hi < 0


# ------------------------------------------------------------------ loading

def load(db_paths: Sequence[str]) -> Dict[str, List[Dict[str, Any]]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in db_paths:
        for e in Database(Path(p)).experiments():
            if e.get("status") == "finished" and e.get("summary"):
                e["_db"] = p
                groups[e["name"]].append(e)
    for k in groups:
        groups[k].sort(key=lambda e: e["seed"])
    return groups


def series(runs: List[Dict[str, Any]], agent: str, metric: str) -> List[Optional[float]]:
    out = []
    for e in runs:
        s = e["summary"].get(agent)
        if s is None:
            out.append(None)
            continue
        if metric in s:
            out.append(s[metric])
        else:
            out.append((s.get("agent_extra") or {}).get(metric))
    return out


def per_run_steps(runs: List[Dict[str, Any]], agent: str) -> int:
    return runs[0]["manifest"]["schedule"]["steps"] if runs else 5


def agent_table(runs: List[Dict[str, Any]], agents: List[str]) -> Dict[str, Dict[str, Any]]:
    steps = per_run_steps(runs, agents[0]) if agents else 5
    table = {}
    for a in agents:
        row = {m: describe(series(runs, a, m)) for m in METRICS + EXTRA}
        fails = series(runs, a, "failures")
        row["failure_rate"] = describe([None if f is None else f / steps for f in fails])
        t2t = series(runs, a, "time_to_target_logical_s")
        row["target_reached_fraction"] = sum(1 for x in t2t if x is not None) / max(1, len(t2t))
        ac, tc = series(runs, a, "adaptation_cost"), series(runs, a, "total_cost")
        row["adaptation_overhead"] = describe([None if (x is None or y in (None, 0)) else x / y for x, y in zip(ac, tc)])
        table[a] = row
    return table


# ------------------------------------------------------------------ experiment-specific analyses

def exp1(groups) -> Dict[str, Any]:
    out = {"description": "Repeatability of the v0.1 negative transfer result across 30 seeds, with AGM v0.1 and v0.2.", "domains": {}}
    for key, name in (("A", "v02_exp1_A"), ("B", "v02_exp1_B")):
        runs = groups.get(name, [])
        if not runs:
            continue
        agents = sorted({a for e in runs for a in e["summary"]})
        d = {"n_runs": len(runs), "seeds": [e["seed"] for e in runs], "agents": agent_table(runs, agents)}
        if key == "B":
            d["paired"] = {}
            for v, cold, mem in (("v1", "agm_v1_cold", "agm_v1_memory"), ("v2", "agm_v2_cold", "agm_v2_memory")):
                d["paired"][v] = {m: paired(series(runs, cold, m), series(runs, mem, m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target", "time_to_target_logical_s", "failures")}
        out["domains"][key] = d
    return out


def exp2(groups) -> Dict[str, Any]:
    matrix: Dict[str, Any] = {}
    for T in "ABC":
        runs = groups.get(f"v02_exp2_tgt_{T}", [])
        if not runs:
            continue
        for S in "ABC":
            if S == T:
                continue
            a = f"v2_from_{S}"
            cell = {"n_runs": len(runs)}
            for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target", "time_to_target_logical_s", "cpu_time_s", "max_memory_mb", "failures", "final_distance_to_initial", "principle_reuse"):
                cell[m] = paired(series(runs, "v2_cold", m), series(runs, a, m))
            cell["cold"] = {m: describe(series(runs, "v2_cold", m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target")}
            cell["transferred"] = {m: describe(series(runs, a, m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target", "principle_reuse")}
            cell["principle_tests"] = _principle_tests(runs, a)
            cell["architecture_distance_transferred_vs_cold_final"] = _final_distance(runs, "v2_cold", a)
            matrix[f"{S}->{T}"] = cell
    return {"description": "Transfer matrix: per target domain, AGM v0.2 cold vs AGM v0.2 with memory from one source domain (paired by seed).", "matrix": matrix}


def _principle_tests(runs, agent) -> Dict[str, Any]:
    kinds: Dict[str, int] = defaultdict(int)
    n_runs_with_test = 0
    for e in runs:
        tests = ((e["summary"].get(agent) or {}).get("agent_extra") or {}).get("principles_tested") or []
        if tests:
            n_runs_with_test += 1
        for t in tests:
            kinds[t["kind"]] += 1
    return {"runs_with_tests": n_runs_with_test, "counts": dict(kinds)}


def _final_distance(runs, a, b) -> Dict[str, Any]:
    from architecture.distance import architecture_distance
    from architecture.ir import ArchitectureIR
    from core.registry import CapabilityRegistry
    reg = CapabilityRegistry.load()
    ds = []
    for e in runs:
        sa, sb = e["summary"].get(a), e["summary"].get(b)
        if not sa or not sb:
            continue
        ha, hb = sa["architectures"][-1]["hash"], sb["architectures"][-1]["hash"]
        db = Database(Path(e["_db"]))
        ra, rb = db.architecture(ha), db.architecture(hb)
        if ra and rb:
            ds.append(architecture_distance(ArchitectureIR.from_dict(ra), ArchitectureIR.from_dict(rb), reg)["structural_distance"])
    return {**describe(ds), "fraction_identical": (sum(1 for d in ds if d == 0) / len(ds)) if ds else None}


def ablations(groups) -> Dict[str, Any]:
    out = {"memory_modes": {}, "economics": {}, "cold_vs_warm": {}, "v1_vs_v2": {}}
    for T in "ABC":
        runs = groups.get(f"v02_exp2_tgt_{T}", [])
        if not runs:
            continue
        mm = {}
        for a in ("v2_warm_task", "v2_warm_architecture", "v2_warm_principle", "v2_warm_full"):
            mm[a] = {m: paired(series(runs, "v2_cold", m), series(runs, a, m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target", "failures", "principle_reuse")}
        mm["principle_vs_architecture"] = {m: paired(series(runs, "v2_warm_architecture", m), series(runs, "v2_warm_principle", m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target")}
        mm["full_vs_architecture"] = {m: paired(series(runs, "v2_warm_architecture", m), series(runs, "v2_warm_full", m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target")}
        mm["table"] = agent_table(runs, ["v2_cold", "v2_warm_task", "v2_warm_architecture", "v2_warm_principle", "v2_warm_full"])
        out["memory_modes"][T] = mm
        ec = {"table": agent_table(runs, ["v2_cold", "v2_always_adapt", "v2_never_adapt"])}
        for a in ("v2_always_adapt", "v2_never_adapt"):
            ec[a] = {m: paired(series(runs, "v2_cold", m), series(runs, a, m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "cpu_time_s", "wall_used_s", "failures")}
        ec["wasted_evaluations"] = {a: describe(_wasted(runs, a)) for a in ("v2_cold", "v2_always_adapt", "v2_never_adapt")}
        ec["decision_outcomes"] = {a: _outcomes(runs, a) for a in ("v2_cold", "v2_always_adapt", "v2_never_adapt")}
        ec["decision_error"] = {a: describe(series(runs, a, "mean_decision_error")) for a in ("v2_cold", "v2_always_adapt", "v2_never_adapt")}
        ec["cost_estimate_error"] = {a: describe(series(runs, a, "mean_cost_estimate_error")) for a in ("v2_cold", "v2_always_adapt", "v2_never_adapt")}
        out["economics"][T] = ec
        out["cold_vs_warm"][T] = {m: paired(series(runs, "v2_cold", m), series(runs, "v2_warm_full", m)) for m in
                                  ("evaluations_to_target", "time_to_target_logical_s", "architecture_evaluations", "adaptation_cost", "quality_mean", "failures", "cpu_time_s", "max_memory_mb")}
        out["v1_vs_v2"][T] = {m: paired(series(runs, "v1_warm_architecture", m), series(runs, "v2_warm_full", m)) for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "failures")}
    return out


def _wasted(runs, agent) -> List[Optional[float]]:
    """Evaluations after the target was first reached on validation (0 when never reached: nothing was 'wasted' by definition,
    reported separately as None to avoid rewarding never-reaching)."""
    out = []
    for e in runs:
        s = e["summary"].get(agent)
        if not s:
            out.append(None)
            continue
        e2t = (s.get("agent_extra") or {}).get("evaluations_to_target")
        out.append(None if e2t is None else s["architecture_evaluations"] - e2t)
    return out


def _outcomes(runs, agent) -> Dict[str, float]:
    tot: Dict[str, int] = defaultdict(int)
    for e in runs:
        for k, v in (((e["summary"].get(agent) or {}).get("agent_extra") or {}).get("decision_outcomes") or {}).items():
            tot[k] += v
    n = sum(tot.values()) or 1
    return {k: v / n for k, v in tot.items()}


def distance_analysis(groups) -> Dict[str, Any]:
    """Exp 6: are useful solutions nearby mutations or new architectural regions?"""
    out = {}
    for name, runs in groups.items():
        if "exp2_tgt" not in name and "exp1" not in name:
            continue
        for a in sorted({x for e in runs for x in e["summary"] if x.startswith("v2_") or x.startswith("agm_v2")}):
            hist = []
            for e in runs:
                s = e["summary"].get(a)
                if not s:
                    continue
                ex = s.get("agent_extra") or {}
                for h in ex.get("selected_history") or []:
                    hist.append({**h, "seed": e["seed"], "quality_mean": s["quality_mean"], "reached": s["time_to_target_logical_s"] is not None})
            if not hist:
                continue
            finals = [h for h in hist if h["step"] == max(x["step"] for x in hist if x["seed"] == h["seed"])]
            levels: Dict[str, int] = defaultdict(int)
            for h in finals:
                levels[str(h.get("novelty_level"))] += 1
            out[f"{name}:{a}"] = {"final_distance_to_initial": describe([h["distance_to_initial"] for h in finals]),
                                  "fraction_final_identical_to_initial": sum(1 for h in finals if h["distance_to_initial"] == 0) / len(finals),
                                  "max_distance_to_initial": describe([max(x["distance_to_initial"] for x in hist if x["seed"] == h["seed"]) for h in finals]),
                                  "final_novelty_levels_vs_prior_memory": dict(levels),
                                  "distance_of_reached_vs_not": {"reached": describe([h["distance_to_initial"] for h in finals if h["reached"]]),
                                                                 "not_reached": describe([h["distance_to_initial"] for h in finals if not h["reached"]])},
                                  "cross_domain_selected_fraction": sum(1 for h in hist if h.get("cross_domain")) / len(hist)}
    return out


def heldout(groups) -> Dict[str, Any]:
    out = {}
    for T in "ABC":
        runs = groups.get(f"v02_exp8_heldout_{T}", [])
        if not runs:
            continue
        out[T] = {"n_runs": len(runs), "table": agent_table(runs, ["v2_cold", "v2_warm_full"]),
                  "paired": {m: paired(series(runs, "v2_cold", m), series(runs, "v2_warm_full", m)) for m in
                             ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target", "failures", "principle_reuse")},
                  "principle_tests": _principle_tests(runs, "v2_warm_full")}
    return out


def principle_inventory(memory_glob: str) -> Dict[str, Any]:
    from collections import Counter
    statuses, rules, n_files = Counter(), Counter(), 0
    for p in glob.glob(memory_glob):
        n_files += 1
        for r in Database(Path(p)).principles():
            statuses[r["status"]] += 1
            rules[r["rule"]] += 1
    return {"memory_files": n_files, "status_counts": dict(statuses), "rule_counts": dict(rules)}


# ------------------------------------------------------------------ success criteria (pre-registered thresholds)

def criteria(res: Dict[str, Any]) -> List[Dict[str, Any]]:
    C = []
    inv = res.get("principle_inventory", {}).get("status_counts", {})
    created = sum(inv.values())
    C.append({"id": "A", "statement": "Architectural principles can be extracted from experience.",
              "evidence": f"{created} principle records across memory files; status counts {inv}",
              "met": created > 0})
    validated = inv.get("SUPPORTED", 0) + inv.get("PARTIALLY_SUPPORTED", 0) + inv.get("CONTRADICTED", 0)
    tests = sum(sum(c["principle_tests"]["counts"].values()) for c in res.get("exp2", {}).get("matrix", {}).values())
    C.append({"id": "B", "statement": "Principles can be experimentally validated (tested under new conditions with recorded outcomes).",
              "evidence": f"{tests} principle tests recorded in transfer targets; {validated} principles reached a non-UNTESTED status", "met": tests > 0 and validated > 0})
    cells = res.get("exp2", {}).get("matrix", {})
    reuse_cells = [k for k, c in cells.items() if (c["transferred"]["principle_reuse"]["mean"] or 0) > 0]
    C.append({"id": "C", "statement": "Validated principles transfer to a genuinely different domain (principle-derived architectures instantiated and evaluated in the target).",
              "evidence": f"principle reuse > 0 in {len(reuse_cells)}/{len(cells)} source→target cells: {reuse_cells}", "met": len(reuse_cells) > 0})
    red = [(k, c["adaptation_cost"]) for k, c in cells.items()]
    sig = [k for k, p in red if p["delta_mean"] is not None and p["delta_mean"] < 0 and ci_excludes_zero(p)]
    worse = [k for k, p in red if p["delta_mean"] is not None and p["delta_mean"] > 0 and ci_excludes_zero(p)]
    e2t = [(k, c["evaluations_to_target"]) for k, c in cells.items()]
    sig_e2t = [k for k, p in e2t if p["delta_mean"] is not None and p["delta_mean"] < 0 and ci_excludes_zero(p)]
    C.append({"id": "D", "statement": "Transfer reduces adaptation/search cost (paired Δ adaptation cost < 0 with 95% CI excluding 0, or Δ evaluations-to-target < 0 likewise).",
              "evidence": f"cells with significant cost reduction: {sig}; with significant cost increase: {worse}; with significant evaluations-to-target reduction: {sig_e2t}",
              "met": len(sig) > 0 or len(sig_e2t) > 0})
    ec = res.get("ablations", {}).get("economics", {})
    dna = {T: ec[T]["decision_outcomes"].get("v2_cold", {}).get("DO_NOT_ADAPT", 0) for T in ec}
    fewer = {T: ec[T]["v2_always_adapt"]["architecture_evaluations"]["delta_mean"] for T in ec}
    qual = {T: ec[T]["v2_always_adapt"]["quality_mean"]["delta_mean"] for T in ec}
    C.append({"id": "E", "statement": "The machine decides not to adapt when adaptation is uneconomical (DO_NOT_ADAPT occurs; always-adapt spends more evaluations without higher quality).",
              "evidence": f"DO_NOT_ADAPT share of decisions per domain {dna}; Δ evaluations (always_adapt − economic) {fewer}; Δ quality {qual}",
              "met": any(v > 0 for v in dna.values()) and all((v or 0) >= 0 for v in fewer.values()) and all((v or 0) <= 0.01 for v in qual.values())})
    dist = [(k, c["architecture_distance_transferred_vs_cold_final"]) for k, c in cells.items()]
    nonzero = [k for k, d in dist if d.get("mean") is not None and d["mean"] > 0]
    C.append({"id": "F", "statement": "Useful transferred architectures are not merely memorized copies (structural distance between transferred and cold final architectures > 0 in some cells, and transferred architectures differ from source architectures).",
              "evidence": f"cells where transferred final architecture differs structurally from the cold final: {nonzero}; fraction identical per cell: " + str({k: d.get('fraction_identical') for k, d in dist}),
              "met": len(nonzero) > 0 and len(sig) > 0})
    C.append({"id": "G", "statement": "The benefit survives multiple random seeds (criterion D holds with n ≥ 30 paired seeds and CI excluding 0).",
              "evidence": f"n_pairs per cell: { {k: c['adaptation_cost']['n_pairs'] for k, c in cells.items()} }",
              "met": (len(sig) > 0 or len(sig_e2t) > 0) and all(c["adaptation_cost"]["n_pairs"] >= 30 for c in cells.values())})
    return C


# ------------------------------------------------------------------ rendering

def _p(p: Dict[str, Any]) -> str:
    if p.get("delta_mean") is None:
        return f"— (pairs {p.get('n_pairs', 0)}, both-missing {p.get('n_both_missing', 0)})"
    star = "*" if ci_excludes_zero(p) else ""
    d = p.get("effect_size_d")
    return f"{p['delta_mean']:+.4g} [{p['ci95'][0]:+.3g}, {p['ci95'][1]:+.3g}]{star} d={'—' if d is None else f'{d:.2f}'} (+{p['positive']}/−{p['negative']}/={p['zero']}, n={p['n_pairs']})"


def _d(x: Dict[str, Any]) -> str:
    if x.get("mean") is None:
        return "—"
    return f"{x['mean']:.4g} (med {x['median']:.3g}, sd {x['sd']:.2g}) [{x['ci95'][0]:.3g}, {x['ci95'][1]:.3g}] n={x['n']}"


def render(res: Dict[str, Any]) -> str:
    L = ["# v0.2 analysis\n", "Paired deltas are (variant − reference) over seeds; `*` marks a bootstrap 95% CI that excludes 0; d is Cohen's d on paired differences. Means are shown with median, sd, CI and n.\n"]
    e1 = res.get("exp1", {})
    L.append("## Experiment 1 — repeatability (30 seeds, Domains A and B)\n")
    for key, d in e1.get("domains", {}).items():
        L.append(f"### Domain {key} (n={d['n_runs']})\n")
        agents = list(d["agents"])
        L.append("| metric | " + " | ".join(agents) + " |"); L.append("|---|" + "---|" * len(agents))
        for m in ("quality_mean", "architecture_evaluations", "adaptation_cost", "evaluations_to_target", "failure_rate", "adaptation_overhead", "target_reached_fraction"):
            L.append(f"| {m} | " + " | ".join((f"{d['agents'][a][m]:.2f}" if m == "target_reached_fraction" else _d(d["agents"][a][m])) for a in agents) + " |")
        if "paired" in d:
            L.append("\nPaired memory − cold:\n")
            for v, pm in d["paired"].items():
                L.append(f"- AGM {v}: " + "; ".join(f"{m} {_p(p)}" for m, p in pm.items()))
        L.append("")
    L.append("## Experiment 2 — transfer matrix (AGM v0.2, memory from one source domain vs cold, paired)\n")
    L.append("| S→T | Δ adaptation cost | Δ evaluations | Δ evaluations-to-target | Δ quality | Δ failures | principle reuse (mean) | tests (kinds) | transferred-vs-cold final distance |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for k, c in res.get("exp2", {}).get("matrix", {}).items():
        L.append(f"| {k} | {_p(c['adaptation_cost'])} | {_p(c['architecture_evaluations'])} | {_p(c['evaluations_to_target'])} | {_p(c['quality_mean'])} | {_p(c['failures'])} | {c['transferred']['principle_reuse']['mean'] if c['transferred']['principle_reuse']['mean'] is not None else '—'} | {c['principle_tests']['counts']} | {_d(c['architecture_distance_transferred_vs_cold_final'])} identical {c['architecture_distance_transferred_vs_cold_final'].get('fraction_identical')} |")
    ab = res.get("ablations", {})
    L.append("\n## Experiments 3 & 4 — principle and memory ablations (target domain, warm memory from the two other domains; variant − cold)\n")
    for T, mm in ab.get("memory_modes", {}).items():
        L.append(f"### Domain {T}\n")
        L.append("| variant | Δ adaptation cost | Δ evaluations | Δ evaluations-to-target | Δ quality | principle reuse |")
        L.append("|---|---|---|---|---|---|")
        for a in ("v2_warm_task", "v2_warm_architecture", "v2_warm_principle", "v2_warm_full"):
            L.append(f"| {a} | {_p(mm[a]['adaptation_cost'])} | {_p(mm[a]['architecture_evaluations'])} | {_p(mm[a]['evaluations_to_target'])} | {_p(mm[a]['quality_mean'])} | {_p(mm[a]['principle_reuse'])} |")
        L.append(f"| principle − architecture | {_p(mm['principle_vs_architecture']['adaptation_cost'])} | {_p(mm['principle_vs_architecture']['architecture_evaluations'])} | {_p(mm['principle_vs_architecture']['evaluations_to_target'])} | {_p(mm['principle_vs_architecture']['quality_mean'])} | |")
        L.append(f"| full − architecture | {_p(mm['full_vs_architecture']['adaptation_cost'])} | {_p(mm['full_vs_architecture']['architecture_evaluations'])} | {_p(mm['full_vs_architecture']['evaluations_to_target'])} | {_p(mm['full_vs_architecture']['quality_mean'])} | |")
        L.append("")
    L.append("## Experiment 5 — adaptation economics ablation (variant − economic)\n")
    for T, ec in ab.get("economics", {}).items():
        L.append(f"### Domain {T}\n")
        L.append(f"- decision outcome shares: { {a: {k: round(v, 2) for k, v in o.items()} for a, o in ec['decision_outcomes'].items()} }")
        for a in ("v2_always_adapt", "v2_never_adapt"):
            L.append(f"- {a}: Δ evaluations {_p(ec[a]['architecture_evaluations'])}; Δ adaptation cost {_p(ec[a]['adaptation_cost'])}; Δ quality {_p(ec[a]['quality_mean'])}; Δ cpu {_p(ec[a]['cpu_time_s'])}; Δ wall {_p(ec[a]['wall_used_s'])}; Δ failures {_p(ec[a]['failures'])}")
        L.append(f"- wasted evaluations after target reached: { {a: _d(x) for a, x in ec['wasted_evaluations'].items()} }")
        L.append(f"- mean decision error (realized − expected net value): { {a: _d(x) for a, x in ec['decision_error'].items()} }")
        L.append(f"- mean cost-estimate error (actual − estimated adaptation cost, quality units): { {a: _d(x) for a, x in ec['cost_estimate_error'].items()} }\n")
    L.append("## Experiment 6 — architecture distance\n")
    L.append("| run:agent | final distance to initial | fraction final identical to initial | max distance | final novelty level vs prior memory | distance reached vs not | cross-domain selected fraction |")
    L.append("|---|---|---|---|---|---|---|")
    for k, v in res.get("distance", {}).items():
        L.append(f"| {k} | {_d(v['final_distance_to_initial'])} | {v['fraction_final_identical_to_initial']:.2f} | {_d(v['max_distance_to_initial'])} | {v['final_novelty_levels_vs_prior_memory']} | {_d(v['distance_of_reached_vs_not']['reached'])} vs {_d(v['distance_of_reached_vs_not']['not_reached'])} | {v['cross_domain_selected_fraction']:.2f} |")
    L.append("\n## Experiment 7 — cold vs warm (warm = memory from the two other domains; warm − cold)\n")
    for T, cw in ab.get("cold_vs_warm", {}).items():
        L.append(f"- Domain {T}: " + "; ".join(f"{m} {_p(p)}" for m, p in cw.items()))
    L.append("\n## AGM v0.1 (architecture memory) vs AGM v0.2 (full memory), warm, paired\n")
    for T, cw in ab.get("v1_vs_v2", {}).items():
        L.append(f"- Domain {T}: " + "; ".join(f"{m} {_p(p)}" for m, p in cw.items()))
    L.append("\n## Experiment 8 — held-out conditions (warm − cold)\n")
    for T, h in res.get("heldout", {}).items():
        L.append(f"- Domain {T} (n={h['n_runs']}): " + "; ".join(f"{m} {_p(p)}" for m, p in h["paired"].items()) + f"; principle tests {h['principle_tests']['counts']}")
    L.append("\n## Principle inventory (all memory files)\n")
    L.append(f"- {res.get('principle_inventory')}")
    L.append("\n## Success criteria (pre-registered)\n")
    L.append("| id | criterion | evidence | met |"); L.append("|---|---|---|---|")
    for c in res.get("criteria", []):
        L.append(f"| {c['id']} | {c['statement']} | {c['evidence']} | {'yes' if c['met'] else 'no'} |")
    L.append(f"\nCriteria met: {sum(1 for c in res.get('criteria', []) if c['met'])} of {len(res.get('criteria', []))}. All must hold for the v0.2 hypothesis to be considered supported.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", nargs="+", default=[str(p) for p in sorted((ROOT / "results" / "v02" / "db").glob("*.sqlite"))])
    ap.add_argument("--out", default=str(ROOT / "results" / "v02" / "analysis"))
    ap.add_argument("--memory-glob", default=str(ROOT / "results" / "v02" / "memory" / "*.sqlite"))
    args = ap.parse_args(argv)
    groups = load(args.db)
    res = {"n_experiments": sum(len(v) for v in groups.values()), "groups": {k: len(v) for k, v in groups.items()},
           "executors": sorted({e.get("executor") for v in groups.values() for e in v}), "git_commits": sorted({e.get("git_commit") for v in groups.values() for e in v}),
           "exp1": exp1(groups), "exp2": exp2(groups), "ablations": ablations(groups), "distance": distance_analysis(groups), "heldout": heldout(groups),
           "principle_inventory": principle_inventory(args.memory_glob)}
    res["criteria"] = criteria(res)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    (out / "analysis.md").write_text(render(res))
    print(out / "analysis.md")
    print(f"experiments: {res['n_experiments']}; criteria met: {sum(1 for c in res['criteria'] if c['met'])}/{len(res['criteria'])}")


if __name__ == "__main__":
    main()
