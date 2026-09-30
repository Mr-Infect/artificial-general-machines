"""v0.3 analysis (spec v0.3 §12, 15, 19): metrics, paired comparisons, kill criteria, verdict, plots.

    python -m experiments.analysis_v03 [--db results/v03/db/*.sqlite] [--out results/v03/analysis]

Kill-criteria thresholds are those pre-registered in docs/v0.3_design.md and are not adjusted here.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from experiments.analysis import ci_excludes_zero, describe, load, paired

ROOT = Path(__file__).resolve().parent.parent
Y_SET = ["telemetry_grid", "lab_assay", "allocation"]
Z_SET = ["network_rules", "scientific_drift", "planning_stable"]
AGENTS = ["fixed", "adaptive", "search", "task_memory", "architecture_memory", "always_adapt", "never_adapt", "agm_cold", "agm_full",
          "agm_no_principle", "agm_no_archmem", "agm_no_negative", "agm_no_economics", "agm_no_regime"]
V3 = [a for a in AGENTS if a.startswith("agm_") or a in ("always_adapt", "never_adapt")]


# ------------------------------------------------------------------ per-run derived metrics

def derive(e: Dict[str, Any], agent: str) -> Optional[Dict[str, Any]]:
    s = e["summary"].get(agent)
    if not s:
        return None
    reg = e.get("regime") or {}
    sched = reg.get("schedule") or []
    transitions = reg.get("transitions") or []
    recs = s.get("step_records") or []
    steps = len(recs)
    x = s.get("agent_extra") or {}
    out: Dict[str, Any] = {"quality_mean": s["quality_mean"], "net_quality_mean": s.get("net_quality_mean"), "adaptation_cost": s["adaptation_cost"],
                           "architecture_evaluations": s["architecture_evaluations"], "failures": s["failures"], "failure_rate": s["failures"] / max(1, steps),
                           "cpu_time_s": s["cpu_time_s"], "max_memory_mb": s["max_memory_mb"], "steps_met_target": s.get("steps_met_target"),
                           "distinct_architectures": s["distinct_architectures"], "principle_reuse": x.get("principle_reuse"),
                           "final_distance_to_initial": x.get("final_distance_to_initial"), "max_distance_to_initial": x.get("max_distance_to_initial")}
    # evaluations-to-useful per regime segment
    segs = []
    for i, seg in enumerate(sched):
        a = seg["start_step"]
        b = sched[i + 1]["start_step"] if i + 1 < len(sched) else steps
        before = recs[a - 1]["evaluations_so_far"] if a > 0 else 0
        met_step = next((r["step"] for r in recs[a:b] if r["met"]), None)
        segs.append({"regime": seg["regime"], "start": a, "met_step": met_step,
                     "evaluations_to_useful": (recs[met_step]["evaluations_so_far"] - before) if met_step is not None else None,
                     "steps_to_useful": (met_step - a) if met_step is not None else None})
    e2u = [g["evaluations_to_useful"] for g in segs if g["evaluations_to_useful"] is not None]
    out["evaluations_to_useful"] = statistics.fmean(e2u) if e2u else None
    out["segments_unmet"] = sum(1 for g in segs if g["met_step"] is None)
    out["segments"] = segs
    # regime response at true transitions
    resp = []
    for t in transitions:
        if t >= steps:
            continue
        seg = next(g for g in segs if g["start"] == t)
        pre_ok = recs[t]["met"]
        resp.append({"transition": t, "pre_arch_meets_new_target": pre_ok, "steps_to_useful": seg["steps_to_useful"], "reached_within_3": seg["steps_to_useful"] is not None and seg["steps_to_useful"] <= 3})
    out["responses"] = resp
    ttr = [r["steps_to_useful"] for r in resp if r["steps_to_useful"] is not None]
    out["time_to_regime_response"] = statistics.fmean(ttr) if ttr else None
    # v3-specific: detection, switches, decisions
    if "detections" in x:
        det_steps = [d["step"] for d in x["detections"]]
        hits = [any(t <= d <= t + 2 for d in det_steps) for t in transitions]
        out["detection_rate"] = sum(hits) / len(hits) if hits else None
        non_tr = [st for st in range(1, steps) if not any(t <= st <= t + 2 for t in transitions)]
        fa = [d for d in det_steps if not any(t <= d <= t + 2 for t in transitions)]
        out["false_alarm_rate"] = len(fa) / len(non_tr) if non_tr else None
        out["detection_delay"] = statistics.fmean([min((d - t) for d in det_steps if t <= d <= t + 2) for t, h in zip(transitions, hits) if h]) if any(hits) else None
        sw = x.get("switches") or []
        # architectural response: transitions where the pre-transition arch missed the new target
        need = [r for r in resp if not r["pre_arch_meets_new_target"]]
        out["needed_response"] = len(need)
        out["responded_within_3"] = sum(1 for r in need if r["reached_within_3"])
        out["responded_with_structural_change"] = sum(1 for r in need if r["reached_within_3"] and any(w["step"] >= r["transition"] and w["step"] <= r["transition"] + 3 and w["distance"] > 0 for w in sw))
        log = x.get("step_log") or []
        dna = [l for l in log if l["decision"] == "DO_NOT_ADAPT"]
        nxt = {l["step"]: l for l in log}
        ok = [l for l in dna if l["met_target"]]
        out["do_not_adapt_share"] = len(dna) / len(log) if log else None
        out["do_not_adapt_accuracy"] = len(ok) / len(dna) if dna else None
        prev_met = {l["step"]: l["met_target"] for l in log}
        unnecessary = [l for l in log if l["step"] > 0 and l["new_evaluations"] > 0 and not l["detected"] and prev_met.get(l["step"] - 1)]
        eligible = [l for l in log if l["step"] > 0 and not l["detected"] and prev_met.get(l["step"] - 1)]
        out["unnecessary_adaptation_rate"] = len(unnecessary) / len(eligible) if eligible else None
        missed = 0
        for t in transitions:
            if t < steps and not recs[t]["met"] and not any(l["new_evaluations"] > 0 for l in log if t <= l["step"] <= t + 2):
                missed += 1
        out["missed_adaptations"] = missed
        out["decision_counts"] = x.get("decision_counts")
        out["negative_applications"] = x.get("negative_applications")
        out["switch_distances"] = [w["distance"] for w in sw]
        out["structural_switches"] = sum(1 for w in sw if w["distance"] > 0)
        tests = x.get("principles_tested") or []
        out["principle_tests"] = {k: sum(1 for t in tests if t["kind"] == k) for k in ("supported", "contradicted", "inconclusive")}
    return out


def series(runs, agent, metric):
    return [(derive(e, agent) or {}).get(metric) for e in runs]


# ------------------------------------------------------------------ per-environment analysis

def env_analysis(runs: List[Dict[str, Any]], seeds: Optional[set] = None) -> Dict[str, Any]:
    if seeds is not None:
        runs = [e for e in runs if e["seed"] % 100 in seeds]
    agents = [a for a in AGENTS if any(a in e["summary"] for e in runs)]
    table = {a: {m: describe(series(runs, a, m)) for m in ("quality_mean", "net_quality_mean", "adaptation_cost", "architecture_evaluations", "evaluations_to_useful", "time_to_regime_response",
                                                           "failure_rate", "cpu_time_s", "max_memory_mb", "final_distance_to_initial", "principle_reuse", "detection_rate", "false_alarm_rate",
                                                           "do_not_adapt_share", "do_not_adapt_accuracy", "unnecessary_adaptation_rate", "missed_adaptations", "structural_switches")} for a in agents}
    for a in agents:
        table[a]["segments_unmet"] = describe(series(runs, a, "segments_unmet"))
        pt = defaultdict(int)
        for e in runs:
            for k, v in ((derive(e, a) or {}).get("principle_tests") or {}).items():
                pt[k] += v
        table[a]["principle_tests"] = dict(pt)
        dc = defaultdict(int)
        for e in runs:
            for k, v in ((derive(e, a) or {}).get("decision_counts") or {}).items():
                dc[k] += v
        table[a]["decision_counts"] = dict(dc)
    metrics = ("evaluations_to_useful", "adaptation_cost", "architecture_evaluations", "time_to_regime_response", "quality_mean", "net_quality_mean", "failure_rate", "cpu_time_s", "max_memory_mb")
    pairs = {}
    for ref, var in (("agm_cold", "agm_full"), ("search", "agm_full"), ("architecture_memory", "agm_full"), ("task_memory", "agm_full"),
                     ("agm_full", "agm_no_principle"), ("agm_full", "agm_no_archmem"), ("agm_full", "agm_no_negative"), ("agm_full", "agm_no_economics"),
                     ("agm_full", "agm_no_regime"), ("agm_cold", "always_adapt"), ("agm_cold", "never_adapt"), ("agm_cold", "search")):
        if ref in agents and var in agents:
            pairs[f"{var}-{ref}"] = {m: paired(series(runs, ref, m), series(runs, var, m)) for m in metrics}
    # transfer success / harm per seed (agm_full vs agm_cold on evaluations-to-useful, then adaptation cost as tie-breaker)
    succ = harm = tie = 0
    for e in runs:
        c, f = derive(e, "agm_cold"), derive(e, "agm_full")
        if not c or not f:
            continue
        cv, fv = c["evaluations_to_useful"], f["evaluations_to_useful"]
        if cv is None and fv is None:
            key = (c["adaptation_cost"], f["adaptation_cost"])
        elif cv is None:
            succ += 1; continue
        elif fv is None:
            harm += 1; continue
        else:
            key = (cv, fv)
        if key[1] < key[0] - 1e-9: succ += 1
        elif key[1] > key[0] + 1e-9: harm += 1
        else: tie += 1
    n = succ + harm + tie
    return {"n_runs": len(runs), "seeds": [e["seed"] for e in runs], "agents": table, "paired": pairs,
            "transfer": {"successful_rate": succ / n if n else None, "harmful_rate": harm / n if n else None, "tie_rate": tie / n if n else None, "n": n}}


# ------------------------------------------------------------------ kill criteria

def kill_criteria(res: Dict[str, Any]) -> List[Dict[str, Any]]:
    Y = {d: res["environments"].get(f"v03_Y_{d}") for d in Y_SET}
    Z = {d: res["environments"].get(f"v03_Z_{d}") for d in Z_SET}
    allenv = {**{f"Y:{d}": v for d, v in Y.items()}, **{f"Z:{d}": v for d, v in Z.items()}}
    def mean_over(envs, agent, metric):
        vals = [v["agents"][agent][metric]["mean"] for v in envs.values() if v and agent in v["agents"] and v["agents"][agent][metric]["mean"] is not None]
        return statistics.fmean(vals) if vals else None
    K = []
    dr, fa = mean_over(allenv, "agm_full", "detection_rate"), mean_over(allenv, "agm_full", "false_alarm_rate")
    K.append({"id": "K1", "name": "regime detection", "pass": dr is not None and dr >= 0.7 and fa is not None and fa <= 0.3,
              "evidence": f"detection rate (within 2 steps) {dr}; false-alarm rate per non-transition step {fa}; thresholds ≥0.7 and ≤0.3"})
    need = resp = struct = 0
    for v in allenv.values():
        if not v:
            continue
        for e in v.get("_runs", []):
            d = derive(e, "agm_full")
            if d:
                need += d.get("needed_response", 0); resp += d.get("responded_within_3", 0); struct += d.get("responded_with_structural_change", 0)
    r2 = resp / need if need else None
    s2 = struct / resp if resp else None
    K.append({"id": "K2", "name": "architectural response", "pass": r2 is not None and r2 >= 0.6 and s2 is not None and s2 >= 0.5,
              "evidence": f"transitions needing a response {need}; reached new target within 3 steps {resp} ({r2}); of those with structural change {struct} ({s2}); thresholds ≥0.6 and ≥0.5"})
    share, acc = mean_over(allenv, "agm_full", "do_not_adapt_share"), mean_over(allenv, "agm_full", "do_not_adapt_accuracy")
    K.append({"id": "K3", "name": "economic adaptation", "pass": share is not None and 0.1 <= share <= 0.9 and acc is not None and acc >= 0.7,
              "evidence": f"DO_NOT_ADAPT share {share}; accuracy (kept architecture met target) {acc}; thresholds share in [0.1,0.9], accuracy ≥0.7"})
    def sig_better(env, key, metric):
        p = env["paired"].get(key, {}).get(metric) if env else None
        return p is not None and p.get("delta_mean") is not None and p["delta_mean"] < 0 and ci_excludes_zero(p)
    def sig_worse(env, key, metric, sign=1):
        p = env["paired"].get(key, {}).get(metric) if env else None
        return p is not None and p.get("delta_mean") is not None and p["delta_mean"] * sign > 0 and ci_excludes_zero(p)
    y_better = [d for d, v in Y.items() if sig_better(v, "agm_full-agm_cold", "evaluations_to_useful")]
    y_worse = [d for d, v in Y.items() if sig_worse(v, "agm_full-agm_cold", "evaluations_to_useful")]
    K.append({"id": "K4", "name": "blind structural transfer", "pass": len(y_better) >= 2 and not y_worse,
              "evidence": f"Y environments with significant reduction of evaluations-to-useful (agm_full − agm_cold): {y_better}; with significant increase: {y_worse}; threshold ≥2 of 3 and none worse"})
    z_worse = [d for d, v in Z.items() if sig_worse(v, "agm_full-agm_cold", "evaluations_to_useful") or sig_worse(v, "agm_full-agm_cold", "quality_mean", sign=-1)]
    def reject_rate(envs):
        tot = defaultdict(int)
        for v in envs.values():
            if v and "agm_full" in v["agents"]:
                for k, c in v["agents"]["agm_full"]["decision_counts"].items():
                    tot[k] += c
        n = sum(tot.values())
        return ((tot.get("REJECT", 0) + tot.get("IGNORE", 0)) / n) if n else None
    rz, ry = reject_rate(Z), reject_rate(Y)
    K.append({"id": "K5", "name": "negative-transfer avoidance", "pass": not z_worse and rz is not None and ry is not None and rz > ry,
              "evidence": f"Z environments where agm_full is significantly worse than cold: {z_worse}; REJECT+IGNORE decision rate Z {rz} vs Y {ry}; requires none worse and rate Z > Y"})
    y_sep = [d for d, v in Y.items() if sig_better(v, "agm_full-search", "evaluations_to_useful") and sig_better(v, "agm_full-architecture_memory", "evaluations_to_useful")]
    K.append({"id": "K6", "name": "baseline separation", "pass": len(y_sep) >= 2,
              "evidence": f"Y environments where agm_full beats BOTH search and architecture_memory on evaluations-to-useful (significant): {y_sep}; threshold ≥2 of 3"})
    held = res.get("heldout_seed_half", {})
    yh_better = [d for d in Y_SET if sig_better(held.get(f"v03_Y_{d}"), "agm_full-agm_cold", "evaluations_to_useful")]
    yh_worse = [d for d in Y_SET if sig_worse(held.get(f"v03_Y_{d}"), "agm_full-agm_cold", "evaluations_to_useful")]
    K.append({"id": "K7", "name": "generalization", "pass": len(yh_better) >= 2 and not yh_worse,
              "evidence": f"K4 on held-out seed half (seeds 15-29): better {yh_better}, worse {yh_worse}; Y regimes are held-out combinations by construction"})
    return K


def verdict(K: List[Dict[str, Any]], missing_fraction: float) -> str:
    p = {k["id"]: k["pass"] for k in K}
    if missing_fraction > 0.2:
        return "INCONCLUSIVE"
    if all(p.values()):
        return "SUPPORT"
    if p["K1"] and p["K2"] and p["K3"] and (p["K4"] or p["K6"]) and p["K5"]:
        return "PARTIAL SUPPORT"
    if (not p["K4"] and not p["K6"]) or not p["K5"]:
        return "FAIL"
    return "INCONCLUSIVE"


# ------------------------------------------------------------------ plots (plain SVG, no dependencies)

def svg_bar(pairs: Dict[str, Dict[str, Any]], title: str, path: Path) -> None:
    keys = list(pairs)
    W, H, L = 720, 40 + 26 * len(keys), 240
    vals = [(pairs[k]["delta_mean"] or 0, pairs[k]["ci95"][0] or 0, pairs[k]["ci95"][1] or 0) for k in keys]
    lo = min([v[1] for v in vals] + [0]); hi = max([v[2] for v in vals] + [0]); span = (hi - lo) or 1
    x = lambda v: L + (v - lo) / span * (W - L - 20)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="11">', f'<text x="10" y="16" font-size="13">{title}</text>',
             f'<line x1="{x(0)}" y1="24" x2="{x(0)}" y2="{H - 10}" stroke="#888"/>']
    for i, k in enumerate(keys):
        d, a, b = vals[i]; y = 40 + 26 * i
        col = "#2a7" if b < 0 else "#c33" if a > 0 else "#888"
        parts.append(f'<text x="8" y="{y + 4}">{k}</text><line x1="{x(a)}" y1="{y}" x2="{x(b)}" y2="{y}" stroke="{col}" stroke-width="2"/><circle cx="{x(d)}" cy="{y}" r="4" fill="{col}"/>'
                     f'<text x="{W - 15}" y="{y + 4}" text-anchor="end">{d:+.3g}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", nargs="+", default=[str(p) for p in sorted((ROOT / "results" / "v03" / "db").glob("*.sqlite"))])
    ap.add_argument("--out", default=str(ROOT / "results" / "v03" / "analysis"))
    args = ap.parse_args(argv)
    groups = load(args.db)
    envs: Dict[str, Any] = {}
    held: Dict[str, Any] = {}
    for name, runs in groups.items():
        if name.startswith("v03_Y_") or name.startswith("v03_Z_"):
            envs[name] = env_analysis(runs)
            envs[name]["_runs"] = runs
            held[name] = env_analysis(runs, seeds=set(range(15, 30)))
    expected = 6 * max([len(r) for n, r in groups.items() if n.startswith("v03_train_")] + [0])
    got = sum(v["n_runs"] for v in envs.values())
    reg_path = ROOT / "results" / "v03" / "registration.json"
    res = {"n_experiments": sum(len(v) for v in groups.values()), "groups": {k: len(v) for k, v in groups.items()}, "executors": sorted({e.get("executor") for v in groups.values() for e in v}),
           "git_commits": sorted({e.get("git_commit") for v in groups.values() for e in v}), "registration": json.loads(reg_path.read_text()) if reg_path.exists() else None,
           "missing_fraction": (1 - got / expected) if expected else 1.0, "environments": envs, "heldout_seed_half": held,
           "training": {n: {"n_runs": len(r), "principles_created": describe([((e["summary"].get("agm_train") or {}).get("agent_extra") or {}).get("principles_created") for e in r]),
                            "quality_mean": describe([(e["summary"].get("agm_train") or {}).get("quality_mean") for e in r])} for n, r in groups.items() if n.startswith("v03_train_")}}
    res["kill_criteria"] = kill_criteria(res)
    res["verdict"] = verdict(res["kill_criteria"], res["missing_fraction"])
    for v in envs.values():
        v.pop("_runs", None)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    plots = out.parent / "plots"; plots.mkdir(parents=True, exist_ok=True)
    for name, v in envs.items():
        for m in ("evaluations_to_useful", "adaptation_cost", "quality_mean"):
            svg_bar({k: p[m] for k, p in v["paired"].items()}, f"{name}: paired Δ {m} (variant − reference)", plots / f"{name}_{m}.svg")
    (out / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    (out / "analysis.md").write_text(render(res))
    print(out / "analysis.md"); print("verdict:", res["verdict"])


def _p(p):
    if not p or p.get("delta_mean") is None:
        return f"— (pairs {p.get('n_pairs', 0) if p else 0})"
    return f"{p['delta_mean']:+.3g} [{p['ci95'][0]:+.3g}, {p['ci95'][1]:+.3g}]{'*' if ci_excludes_zero(p) else ''} d={'—' if p.get('effect_size_d') is None else f'{p['effect_size_d']:.2f}'} (+{p['positive']}/−{p['negative']}/={p['zero']}, n={p['n_pairs']}, missing {p['n_both_missing']})"


def _d(x):
    return "—" if not x or x.get("mean") is None else f"{x['mean']:.3g} (med {x['median']:.3g}, sd {x['sd']:.2g}) [{x['ci95'][0]:.3g}, {x['ci95'][1]:.3g}] n={x['n']}"


def render(res) -> str:
    L = [f"# v0.3 analysis — verdict: **{res['verdict']}**\n", f"experiments {res['n_experiments']}; missing transfer runs {res['missing_fraction']:.1%}; executors {res['executors']}; commits {[c[:10] for c in res['git_commits']]}; registration {res.get('registration')}\n",
         "## Kill criteria (pre-registered in docs/v0.3_design.md)\n", "| id | criterion | pass | evidence |", "|---|---|---|---|"]
    for k in res["kill_criteria"]:
        L.append(f"| {k['id']} | {k['name']} | {'PASS' if k['pass'] else 'FAIL'} | {k['evidence']} |")
    for name, v in res["environments"].items():
        L.append(f"\n## {name} (n={v['n_runs']}) — transfer success {v['transfer']['successful_rate']}, harmful {v['transfer']['harmful_rate']}, tie {v['transfer']['tie_rate']}\n")
        agents = list(v["agents"])
        L.append("| metric | " + " | ".join(agents) + " |"); L.append("|---|" + "---|" * len(agents))
        for m in ("quality_mean", "net_quality_mean", "evaluations_to_useful", "segments_unmet", "time_to_regime_response", "adaptation_cost", "architecture_evaluations", "failure_rate",
                  "cpu_time_s", "max_memory_mb", "final_distance_to_initial", "structural_switches", "detection_rate", "false_alarm_rate", "do_not_adapt_share", "do_not_adapt_accuracy",
                  "unnecessary_adaptation_rate", "missed_adaptations", "principle_reuse"):
            L.append(f"| {m} | " + " | ".join(_d(v["agents"][a].get(m)) for a in agents) + " |")
        L.append("| principle tests | " + " | ".join(str(v["agents"][a].get("principle_tests") or "") for a in agents) + " |")
        L.append("| principle decisions | " + " | ".join(str(v["agents"][a].get("decision_counts") or "") for a in agents) + " |")
        L.append("\nPaired comparisons (variant − reference):\n")
        for k, pm in v["paired"].items():
            L.append(f"- {k}: e2u {_p(pm['evaluations_to_useful'])}; adapt cost {_p(pm['adaptation_cost'])}; quality {_p(pm['quality_mean'])}; failures {_p(pm['failure_rate'])}; response {_p(pm['time_to_regime_response'])}")
    L.append("\n## Training runs\n")
    for n, t in res["training"].items():
        L.append(f"- {n}: n={t['n_runs']}, quality {_d(t['quality_mean'])}, principles created {_d(t['principles_created'])}")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
