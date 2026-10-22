"""ARCHETYPE analysis: metrics, paired statistics, kill criteria K1-K8, success conditions S1-S10, verdict.

    python -m archetype.metrics.analysis results/archetype/<run>

Statistics reuse the laboratory's functions (bootstrap 95% CI, paired deltas by seed). The unit of analysis
is the seed. Thresholds are the registered ones (docs/archetype_registration.md) and are not adjusted here.
No code path declares success: the output is the criteria table and one of four registered verdicts.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from archetype.architecture.roles import MEMORIZED_THRESHOLD
from archetype.metrics import core as M
from experiments.analysis import ci_excludes_zero, describe, paired

TRANSFORMATIONS = ["decompose", "deepen", "parallelize", "replicate", "gate", "revise", "recall", "branch", "tune", "upgrade"]
TRANSFER_WORLDS = ("transfer_iso", "transfer_holdout")
HELP, USEFUL_T, HARM = 0.02, 0.03, -0.01
SEARCHES = ("search", "search_screen")
# registered thresholds
TH = {"K1_min_auroc": 0.65, "K2_min_families": 2, "S3_min_families": 7, "S9_min_holdout_families": 3, "K3_max_false_transfer": 0.20,
      "K4_min_accuracy": 0.60, "K5_min_event_rate": 0.50, "max_missing": 0.05, "min_seeds": 30}
SPEC_PAIRS = [("failure_cost", "gate"), ("parallelizability", "parallelize"), ("dependency_depth", "decompose"), ("observation_noise", "replicate"), ("delayed_feedback", "decompose")]


def load(run_dir: str) -> List[Dict[str, Any]]:
    return [json.loads(p.read_text()) for p in sorted(Path(run_dir).glob("seed_*.json"))]


def _sig(p: Dict[str, Any], positive: bool = True) -> bool:
    lo, hi = p.get("ci95", [None, None])
    return lo is not None and (lo > 0 if positive else hi < 0)


def _clip(g: float) -> float:
    return max(-1.0, min(1.0, g))


class Data:
    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.seeds = [r["seed"] for r in results]
        self.b1 = results[0]["config"]["phase1_budget"]
        self.agents = results[0]["config"]["agents"]
        self.env = {r["seed"]: {(e["family"], e["surface_index"]): e for e in r["environments"]} for r in results}
        self.eps: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
        for r in results:
            d: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for e in r["episodes"]:
                d[e["agent"]].append(e)
            self.eps[r["seed"]] = d

    def truth(self, ep: Dict[str, Any]) -> Dict[str, float]:
        return self.env[ep["seed"]][(ep["family"], ep["surface"])]["truth_effects"]

    def envrec(self, ep: Dict[str, Any]) -> Dict[str, Any]:
        return self.env[ep["seed"]][(ep["family"], ep["surface"])]

    def e2u(self, ep: Dict[str, Any]) -> float:
        v = ep["phase1"]["e2u"]
        return float(self.b1 + 1 if v is None else v)

    def series(self, agent: str, fn: Callable[[Dict[str, Any]], Optional[float]], keep: Callable[[Dict[str, Any]], bool]) -> List[Optional[float]]:
        """One value per seed: the mean of ``fn`` over that seed's episodes passing ``keep``."""
        return [M.mean([fn(e) for e in self.eps[s].get(agent, []) if keep(e)]) for s in self.seeds]


def in_world(*worlds: str) -> Callable[[Dict[str, Any]], bool]:
    return lambda e: e["world"] in worlds


# ------------------------------------------------------------------------------------------ tables

def agent_tables(D: Data) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    fns = {"e2u": D.e2u, "censored": lambda e: float(e["phase1"]["e2u"] is None), "gap": lambda e: _clip(e["phase1"]["final"]["gap"]),
           "regret": lambda e: e["phase1"]["final"]["regret"], "evaluations": lambda e: float(e["phase1"]["evaluations"]),
           "adaptation_cost": lambda e: e["phase1"]["evaluation_cost"], "failure_rate": lambda e: e["phase1"]["failures"] / max(1, e["phase1"]["evaluations"]),
           "novelty": lambda e: e["phase1"]["final"]["novelty"], "operations": lambda e: float(e["phase1"]["final"]["operations"]),
           "arch_cost": lambda e: e["phase1"]["final"]["cost"], "latency": lambda e: e["phase1"]["final"]["latency"], "memory": lambda e: e["phase1"]["final"]["memory"],
           "harmful_element": lambda e: float(bool(e["phase1"]["final"]["harmful"])), "phase2_evaluations": lambda e: float(e["phase2"]["evaluations"]),
           "phase2_gap": lambda e: _clip(e["phase2"]["final"]["gap"])}
    for world in ("transfer_iso", "transfer_holdout", "false"):
        out[world] = {a: {k: describe(D.series(a, fn, in_world(world))) for k, fn in fns.items()} for a in D.agents}
    return out


def reductions(D: Data) -> Dict[str, Any]:
    """Useful-evaluation reduction of ARCHETYPE against each comparator: comparator e2u - archetype e2u (positive = fewer needed)."""
    fams = sorted({e["family"] for e in D.results[0]["episodes"]})
    comps = [a for a in D.agents if a not in ("archetype", "latent_oracle")]
    out: Dict[str, Any] = {"by_family": {}, "pooled": {}}
    for c in comps:
        out["by_family"][c] = {f: paired(D.series("archetype", D.e2u, lambda e, f=f: e["family"] == f), D.series(c, D.e2u, lambda e, f=f: e["family"] == f)) for f in fams}
        out["pooled"][c] = {w: paired(D.series("archetype", D.e2u, in_world(*ws)), D.series(c, D.e2u, in_world(*ws)))
                            for w, ws in (("transfer", TRANSFER_WORLDS), ("transfer_iso", ("transfer_iso",)), ("transfer_holdout", ("transfer_holdout",)), ("false", ("false",)))}
        out["pooled"][c]["transfer_scrambled"] = paired(D.series("archetype", D.e2u, lambda e: e["world"] in TRANSFER_WORLDS and e["surface"] % 3 == 2),
                                                        D.series(c, D.e2u, lambda e: e["world"] in TRANSFER_WORLDS and e["surface"] % 3 == 2))
        out["pooled"][c]["quality_transfer"] = paired(D.series(c, lambda e: _clip(e["phase1"]["final"]["gap"]), in_world(*TRANSFER_WORLDS)),
                                                      D.series("archetype", lambda e: _clip(e["phase1"]["final"]["gap"]), in_world(*TRANSFER_WORLDS)))
        out["pooled"][c]["quality_false"] = paired(D.series(c, lambda e: _clip(e["phase1"]["final"]["gap"]), in_world("false")),
                                                   D.series("archetype", lambda e: _clip(e["phase1"]["final"]["gap"]), in_world("false")))
    return out


def _pairs(D: Data, seed: int, agent: str, keep) -> Dict[str, list]:
    by_t: Dict[str, list] = defaultdict(list)
    for e in D.eps[seed].get(agent, []):
        if e["scores"] and keep(e):
            tr = D.truth(e)
            for t, s in e["scores"].items():
                by_t[t].append((s, tr[t] > HELP))
    return by_t


def prediction(D: Data) -> Dict[str, Any]:
    """Does a zero-evaluation score predict that a transformation will help? (spec §10)"""
    scopes = {"all": lambda e: True, "transfer": in_world(*TRANSFER_WORLDS), "transfer_iso": in_world("transfer_iso"), "transfer_holdout": in_world("transfer_holdout"),
              "false": in_world("false"), "scrambled": lambda e: e["surface"] % 3 == 2, "themed": lambda e: e["surface"] % 3 != 2}
    scorers = [a for a in D.agents if any(e["scores"] for e in D.eps[D.seeds[0]].get(a, []))]
    raw: Dict[str, Dict[str, Dict[str, list]]] = {a: {sc: {"pooled": [], "within": [], "auprc": []} for sc in scopes} for a in scorers}
    for a in scorers:
        for sc, keep in scopes.items():
            for s in D.seeds:
                by_t = _pairs(D, s, a, keep)
                allp = [p for v in by_t.values() for p in v]
                raw[a][sc]["pooled"].append(M.auroc(allp))
                raw[a][sc]["auprc"].append(M.auprc(allp))
                raw[a][sc]["within"].append(M.mean([M.auroc(v) for v in by_t.values()]))
    out: Dict[str, Any] = {"agents": {a: {sc: {k: describe(v) for k, v in d.items()} for sc, d in raw[a].items()} for a in scorers}, "versus": {}}
    if "archetype" in raw:
        for other in scorers:
            if other != "archetype":
                out["versus"][other] = {sc: {k: paired(raw[other][sc][k], raw["archetype"][sc][k]) for k in ("pooled", "within")} for sc in scopes}
        conf = [(s, y) for seed in D.seeds for v in _pairs(D, seed, "archetype", lambda e: True).values() for s, y in v]
        out["calibration"] = M.calibration(conf)
        out["per_transformation"] = {t: describe([M.auroc(_pairs(D, s, "archetype", lambda e: True).get(t, [])) for s in D.seeds]) for t in TRANSFORMATIONS}
    return out


def _adopted(dec: Dict[str, Any]) -> bool:
    return dec["decision"] == "TRUST" or dec.get("outcome") == "ACCEPTED"


def transfer_outcomes(D: Data) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    # false transfer (K3): a trap transformation (helped in the look-alike training environment, hurts here) ends up, harmful, in the final architecture
    def false_transfer(e):
        traps = set(D.envrec(e).get("traps", []))
        return None if not traps else float(bool(traps & set(e["phase1"]["final"]["harmful"])))
    out["false_transfer_rate"] = {a: describe(D.series(a, false_transfer, in_world("false"))) for a in D.agents}
    out["false_transfer_vs"] = {c: paired(D.series("archetype", false_transfer, in_world("false")), D.series(c, false_transfer, in_world("false"))) for c in D.agents if c != "archetype"}
    out["environments_with_traps"] = describe([M.mean([float(bool(v.get("traps"))) for v in D.env[s].values() if v["world"] == "false"]) for s in D.seeds])
    out["matched_optimum_gap_in_false"] = describe([M.mean([_clip(v["matched_optimum_gap_here"]) for v in D.env[s].values() if v["world"] == "false"]) for s in D.seeds])
    out["matched_optimum_gap_in_iso"] = describe([M.mean([_clip(v["matched_optimum_gap_here"]) for v in D.env[s].values() if v["world"] == "transfer_iso"]) for s in D.seeds])
    variants = [a for a in D.agents if a.startswith("archetype")]
    dec: Dict[str, Any] = {}
    for a in variants:
        trap_adopt, missed, struct, pred_ok, org_match, decisions, env_dec = [], [], [], [], [], Counter(), Counter()
        for s in D.seeds:
            ta, ms, st, po, om = [], [], [], [], []
            for e in D.eps[s].get(a, []):
                d = e["report"].get("decisions") or {}
                env_dec[e["report"].get("environment_decision", "BUILD_NEW")] += 1
                tr, er = D.truth(e), D.envrec(e)
                for t, x in d.items():
                    decisions[x["decision"] + ("/" + x["outcome"] if "outcome" in x else "")] += 1
                    if e["world"] == "false" and t in er.get("traps", []):
                        ta.append(float(_adopted(x)))
                    if e["world"] in TRANSFER_WORLDS and tr[t] > USEFUL_T:
                        ms.append(float(not _adopted(x)))
                if e["world"] in TRANSFER_WORLDS and d:
                    st.append(float(bool(e["phase1"].get("proposal", {}).get("useful"))))
                    po.append(float(bool(e["phase1"].get("prediction", {}).get("useful"))))
                    if "proposal" in e["phase1"]:
                        om.append(float(e["phase1"]["proposal"]["organization"] == er["reference"]["organization"]))
            for acc, v in ((trap_adopt, ta), (missed, ms), (struct, st), (pred_ok, po), (org_match, om)):
                acc.append(M.mean(v))
        dec[a] = {"trap_adoption_rate": describe(trap_adopt), "missed_transfer_rate": describe(missed), "structural_transfer_success": describe(struct),
                  "zero_evaluation_transfer_success": describe(pred_ok), "reconstruction_organization_match": describe(org_match),
                  "principle_decisions": dict(decisions), "environment_decisions": dict(env_dec)}
    out["archetype_variants"] = dec
    return out


def counterfactuals(D: Data) -> Dict[str, Any]:
    """Interventional pairs (spec §11, §12): exactly one latent property differs between 'low' and 'high'."""
    agents = D.results[0]["config"]["intervention_agents"]
    acc = {a: {k: [] for k in ("prediction_all", "prediction_observable", "prediction_hidden", "choice_all", "choice_observable", "choice_hidden", "gap")} for a in agents}
    spec = {f"{p}->{t}": {"truth_direction": [], **{a: [] for a in agents}} for p, t in SPEC_PAIRS}
    n_material = []
    for r in D.results:
        groups: Dict[tuple, Dict[str, Any]] = defaultdict(dict)
        for row in r["interventions"]:
            groups[(row["family"], row["property"])][row["level"]] = row
        per = {a: {k: [] for k in acc[a]} for a in agents}
        nm = 0
        for (fam, prop), g in groups.items():
            if len(g) < 2:
                continue
            lo, hi = g["low"], g["high"]
            hid = "hidden" if lo["hidden_only"] else "observable"
            for t in TRANSFORMATIONS:
                dt = hi["truth_effects"][t] - lo["truth_effects"][t]
                key = f"{prop}->{t}"
                if key in spec:
                    spec[key]["truth_direction"].append(dt)
                material = abs(dt) >= 0.03
                nm += int(material)
                opt_d = (t in hi["optimum_present"]) - (t in lo["optimum_present"])
                for a in agents:
                    if a not in lo["agents"] or a not in hi["agents"]:
                        continue
                    la, ha = lo["agents"][a], hi["agents"][a]
                    if material and la["scores"]:
                        ds = ha["scores"][t] - la["scores"][t]
                        ok = float(abs(ds) >= 0.01 and (ds > 0) == (dt > 0))
                        per[a]["prediction_all"].append(ok)
                        per[a]["prediction_" + hid].append(ok)
                        if key in spec:
                            spec[key][a].append(ok)
                    if opt_d != 0:
                        ok = float(((t in ha["present"]) - (t in la["present"])) == opt_d)
                        per[a]["choice_all"].append(ok)
                        per[a]["choice_" + hid].append(ok)
            for a in agents:
                for lvl in (lo, hi):
                    if a in lvl["agents"]:
                        per[a]["gap"].append(_clip(lvl["agents"][a]["gap"]))
        n_material.append(nm)
        for a in agents:
            for k in acc[a]:
                acc[a][k].append(M.mean(per[a][k]))
    out = {"agents": {a: {k: describe(v) for k, v in acc[a].items()} for a in agents}, "material_pairs_per_seed": describe(n_material),
           "spec_pairs": {k: {"mean_truth_change": M.mean(v["truth_direction"]), **{a: M.mean(v[a]) for a in agents if v[a]}} for k, v in spec.items()}}
    if "archetype" in acc and "archetype_no_structural_memory" in acc:
        out["memory_vs_cold_gap"] = paired(acc["archetype_no_structural_memory"]["gap"], acc["archetype"]["gap"])
        out["memory_vs_cold_choice"] = paired(acc["archetype_no_structural_memory"]["choice_all"], acc["archetype"]["choice_all"])
    return out


def _gap_at(ep: Dict[str, Any], n: int) -> float:
    g = 0.0
    for k, v in ep["phase1"]["curve"]:
        if k <= n:
            g = v
    return g


def reconstruction(D: Data, red: Dict[str, Any]) -> Dict[str, Any]:
    """STRUCTURAL RECONSTRUCTION EVENTS (spec §14) and the stricter breakthrough events (spec §34)."""
    events, by_family = [], defaultdict(lambda: {"episodes": 0, "events": 0, "surfaces": set(), "seeds": set()})
    for s in D.seeds:
        screen = {(e["family"], e["surface"]): e for e in D.eps[s].get("search_screen", [])}
        for e in D.eps[s].get("archetype", []):
            if e["world"] not in TRANSFER_WORLDS:
                continue
            fam = by_family[e["family"]]
            fam["episodes"] += 1
            fin, rep, tr, er = e["phase1"]["final"], e["report"], D.truth(e), D.envrec(e)
            accepted = rep.get("accepted") or []
            novel = fin["novelty"] >= MEMORIZED_THRESHOLD
            relation_ok = bool(accepted) and all(tr[t] > HELP for t in accepted) and all(t in fin["present"] for t in accepted)
            if not (novel and relation_ok and fin["useful"]):
                continue
            cold = screen.get((e["family"], e["surface"]))
            cold_gap = _gap_at(cold, e["phase1"]["evaluations"]) if cold else None
            fam["events"] += 1
            fam["surfaces"].add(e["surface"])
            fam["seeds"].add(s)
            conf = M.mean([rep["decisions"][t]["confidence"] for t in accepted])
            events.append({"source_environment": er.get("matched", {}).get("family"), "target_environment": f"{e['family']}/surface{e['surface']}", "world": e["world"],
                           "latent_relation": {t: round(tr[t], 4) for t in accepted}, "source_architecture": "not copied: built from principles over local primitives",
                           "reconstructed_architecture": {"config": fin["config"], "organization": fin["organization"], "hash": fin["hash"]},
                           "architecture_distance": fin["novelty"], "surface_distance": round(1 - er["surface_similarity_nearest_train"], 4),
                           "quality_gain": round(fin["utility"] - er["reference"]["base_utility"], 5),
                           "evaluation_reduction": (D.e2u(cold) - D.e2u(e)) if cold else None, "adaptation_cost": e["phase1"]["evaluation_cost"], "confidence": conf,
                           "seed": s, "cold_gap_at_same_budget": cold_gap, "cold_equivalent_within_budget": cold_gap is not None and cold_gap >= 0.8})
    fams = {}
    for f, v in by_family.items():
        rate = v["events"] / max(1, v["episodes"])
        beats = all(_sig(red["by_family"][c][f]) for c in SEARCHES)
        fams[f] = {"event_rate": rate, "surfaces_with_events": len(v["surfaces"]), "seeds_with_events": len(v["seeds"]), "beats_both_searches_e2u": beats,
                   "passes": rate >= TH["K5_min_event_rate"] and len(v["surfaces"]) >= 2 and beats}
    passing = {f for f, v in fams.items() if v["passes"]}
    for ev in events:
        fam = ev["target_environment"].split("/")[0]
        ev["replication_count"] = fams[fam]["seeds_with_events"]
        ev["breakthrough_conditions_met"] = fam in passing and not ev["cold_equivalent_within_budget"]
    return {"events": events, "n_events": len(events), "by_family": fams, "families_passing": sorted(passing),
            "novel_final_share": describe(D.series("archetype", lambda e: float(e["phase1"]["final"]["novelty"] >= MEMORIZED_THRESHOLD), in_world(*TRANSFER_WORLDS))),
            "novelty_by_agent": {a: describe(D.series(a, lambda e: e["phase1"]["final"]["novelty"], in_world(*TRANSFER_WORLDS))) for a in D.agents}}


def ablations(D: Data) -> Dict[str, Any]:
    def ft(e):
        traps = set(D.envrec(e).get("traps", []))
        return None if not traps else float(bool(traps & set(e["phase1"]["final"]["harmful"])))
    out = {}
    for a in [x for x in D.agents if x.startswith("archetype_no_")]:
        d = {"e2u_transfer": paired(D.series("archetype", D.e2u, in_world(*TRANSFER_WORLDS)), D.series(a, D.e2u, in_world(*TRANSFER_WORLDS))),
             "e2u_false": paired(D.series("archetype", D.e2u, in_world("false")), D.series(a, D.e2u, in_world("false"))),
             "gap_transfer": paired(D.series("archetype", lambda e: _clip(e["phase1"]["final"]["gap"]), in_world(*TRANSFER_WORLDS)), D.series(a, lambda e: _clip(e["phase1"]["final"]["gap"]), in_world(*TRANSFER_WORLDS))),
             "gap_false": paired(D.series("archetype", lambda e: _clip(e["phase1"]["final"]["gap"]), in_world("false")), D.series(a, lambda e: _clip(e["phase1"]["final"]["gap"]), in_world("false"))),
             "false_transfer": paired(D.series("archetype", ft, in_world("false")), D.series(a, ft, in_world("false"))),
             "evaluations": paired(D.series("archetype", lambda e: float(e["phase1"]["evaluations"]), lambda e: True), D.series(a, lambda e: float(e["phase1"]["evaluations"]), lambda e: True)),
             "phase2_gap": paired(D.series("archetype", lambda e: _clip(e["phase2"]["final"]["gap"]), lambda e: True), D.series(a, lambda e: _clip(e["phase2"]["final"]["gap"]), lambda e: True))}
        # deltas are (ablated - full). Removing the component IMPROVES things when e2u/false_transfer go down or gap goes up.
        better = [k for k in ("e2u_transfer", "e2u_false", "false_transfer") if _sig(d[k], positive=False)] + [k for k in ("gap_transfer", "gap_false", "phase2_gap") if _sig(d[k])]
        worse = [k for k in ("e2u_transfer", "e2u_false", "false_transfer") if _sig(d[k])] + [k for k in ("gap_transfer", "gap_false", "phase2_gap") if _sig(d[k], positive=False)]
        d["removal_improves"], d["removal_hurts"] = better, worse
        d["evidence_against_component"] = bool(better) and not worse
        out[a] = d
    return out


def selective(D: Data) -> Dict[str, Any]:
    items, decided, abstained = [], [], []
    for s in D.seeds:
        for e in D.eps[s].get("archetype", []):
            tr = D.truth(e)
            for t, x in (e["report"].get("decisions") or {}).items():
                ok = (x["confidence"] >= 0.5) == (tr[t] > HELP)
                items.append((abs(x["confidence"] - 0.5), ok))
                (abstained if x["decision"] == "ABSTAIN" else decided).append(ok)
    n = max(1, len(items))
    return {"coverage": len(decided) / n, "risk_when_decided": 1 - sum(decided) / max(1, len(decided)), "risk_if_forced_on_abstained": 1 - sum(abstained) / max(1, len(abstained)),
            "risk_at_full_coverage": 1 - sum(ok for _, ok in items) / n, "risk_coverage_curve": M.risk_coverage(items)}


def regimes(D: Data) -> Dict[str, Any]:
    out = {}
    def sh(flag):
        return lambda e: D.envrec(e)["phase2"]["shifted"] == flag
    for a in D.agents:
        out[a] = {"gap_after_shift": describe(D.series(a, lambda e: _clip(e["phase2"]["final"]["gap"]), sh(True))),
                  "gap_kept_before_adapting": describe(D.series(a, lambda e: _clip(e["phase2"]["kept_gap"]), sh(True))),
                  "evaluations_when_shifted": describe(D.series(a, lambda e: float(e["phase2"]["evaluations"]), sh(True))),
                  "evaluations_when_not_shifted": describe(D.series(a, lambda e: float(e["phase2"]["evaluations"]), sh(False)))}
        if a.startswith("archetype"):
            det = lambda e: float(bool((e["phase2"].get("regime") or {}).get("detected")))
            out[a]["detection_rate"] = describe(D.series(a, det, sh(True)))
            out[a]["false_alarm_rate"] = describe(D.series(a, det, sh(False)))
    return out


def analogy(D: Data) -> Dict[str, Any]:
    """Environment-level structural analogy (spec §10): does predicted transferability from the look-alike training
    environment track true usefulness of its optimum here? Isomorphic vs false-analogy environments only."""
    def cos(a, b):
        na, nb = math.sqrt(sum(v * v for v in a.values())), math.sqrt(sum(v * v for v in b.values()))
        return sum(a[t] * b[t] for t in a) / (na * nb) if na and nb else 0.0
    res = {"archetype": [], "surface_similarity": [], "latent_distance_oracle": []}
    for s in D.seeds:
        pa, ps, pl = [], [], []
        for e in D.eps[s].get("archetype", []):
            er = D.envrec(e)
            if "matched" not in er or "matched_scores" not in e:
                continue
            y = er["matched_optimum_gap_here"] >= 0.8
            pa.append((cos(e["scores"], e["matched_scores"]), y))
            ps.append((er["matched"]["surface_similarity"], y))
            pl.append((-er["matched"]["latent_distance"], y))
        for k, v in (("archetype", pa), ("surface_similarity", ps), ("latent_distance_oracle", pl)):
            res[k].append(M.auroc(v))
    return {"auroc": {k: describe(v) for k, v in res.items()}, "archetype_vs_surface": paired(res["surface_similarity"], res["archetype"]),
            "note": "zero-evaluation scores; false analogies differ from their source only in unobservable properties"}


def memory_stats(D: Data) -> Dict[str, Any]:
    stat, n, hid, retired, cf, reuse, contra, prec = Counter(), [], [], [], [], [], [], []
    for r in D.results:
        snap = (r["agents"].get("archetype") or {}).get("snapshot")
        if not snap:
            continue
        ps = snap["store"]["principles"]
        n.append(len(ps))
        hid.append(sum(p["hidden_sensitive"] for p in ps.values()))
        retired.append(len(snap["store"]["retired"]))
        cf.append(snap["training"]["counterfactual_evaluations"])
        for p in ps.values():
            stat[p["status"]] += 1
        used = tested = rejected = tp = pp = 0
        for e in D.eps[r["seed"]].get("archetype", []):
            tr = D.truth(e)
            for t, x in (e["report"].get("decisions") or {}).items():
                used += x["decision"] in ("TRUST", "TEST")
                if "outcome" in x:
                    tested += 1
                    rejected += x["outcome"] == "REJECTED"
                if x["confidence"] >= 0.5:
                    pp += 1
                    tp += tr[t] > HELP
        m = max(1, len(D.eps[r["seed"]].get("archetype", [])))
        reuse.append(used / m)
        contra.append(rejected / max(1, tested))
        prec.append(tp / max(1, pp))
    return {"principles": describe(n), "hidden_sensitive": describe(hid), "retired": describe(retired), "status_counts": dict(stat), "counterfactual_evaluations": describe(cf),
            "principle_reuse_per_environment": describe(reuse), "principle_contradiction_rate": describe(contra), "memory_precision": describe(prec)}


def decoupled_control(D: Data) -> Dict[str, Any]:
    """Within-transformation AUROC of ARCHETYPE when its observations come from another family's structure."""
    real, ctrl = [], []
    for r in D.results:
        if not r.get("controls"):
            continue
        by_t_c, by_t_r = defaultdict(list), defaultdict(list)
        eps = {(e["family"], e["surface"]): e for e in D.eps[r["seed"]].get("archetype", [])}
        for c in r["controls"]:
            tr = D.env[r["seed"]][(c["family"], c["surface"])]["truth_effects"]
            e = eps.get((c["family"], c["surface"]))
            for t in TRANSFORMATIONS:
                by_t_c[t].append((c["scores"][t], tr[t] > HELP))
                if e and e["scores"]:
                    by_t_r[t].append((e["scores"][t], tr[t] > HELP))
        ctrl.append(M.mean([M.auroc(v) for v in by_t_c.values()]))
        real.append(M.mean([M.auroc(v) for v in by_t_r.values()]))
    return {"within_auroc_real_observations": describe(real), "within_auroc_decoupled_observations": describe(ctrl), "real_minus_decoupled": paired(ctrl, real)}


# ------------------------------------------------------------------------------------------ criteria and verdict

def criteria(res: Dict[str, Any]) -> Dict[str, Any]:
    red, pred, tro, cf, rec = res["reductions"], res["prediction"], res["transfer_outcomes"], res["counterfactuals"], res["reconstruction"]
    fams_t = [f for f in red["by_family"]["search"] if f[0] in "BH"]
    win = {f: all(_sig(red["by_family"][c][f]) for c in SEARCHES) for f in fams_t}
    lose_all = all(not _sig(red["by_family"][c][f]) for f in fams_t for c in SEARCHES)
    vs_surface = pred["versus"].get("surface_similarity", {})
    a_within = pred["agents"]["archetype"]["all"]["within"]["mean"]
    k1 = bool(vs_surface) and _sig(vs_surface["all"]["within"]) and _sig(vs_surface["all"]["pooled"]) and (a_within or 0) >= TH["K1_min_auroc"]
    n_win = sum(win.values())
    k2 = n_win >= TH["K2_min_families"]
    ftr = tro["false_transfer_rate"]["archetype"]["mean"]
    k3 = ftr is not None and ftr <= TH["K3_max_false_transfer"] and not _sig(tro["false_transfer_vs"]["search_screen"], positive=False)
    cfa = cf["agents"].get("archetype", {})
    k4_obs = cfa.get("prediction_observable", {})
    k4 = bool(k4_obs) and (k4_obs.get("mean") or 0) >= TH["K4_min_accuracy"] and (k4_obs.get("ci95", [0])[0] or 0) > 0.5
    k5 = bool(rec["families_passing"])
    pooled_screen = red["pooled"]["search_screen"]["transfer"]
    k6 = n_win >= 1 and _sig(pooled_screen) and _sig(red["pooled"]["search"]["transfer"])
    scr = vs_surface.get("scrambled", {})
    k7 = bool(scr) and _sig(scr["within"]) and _sig(red["pooled"]["search_screen"]["transfer_scrambled"])
    mem_t = red["pooled"]["archetype_no_structural_memory"]["transfer"]
    k8_triggered = _sig(mem_t) and ("memory_vs_cold_gap" in cf and _sig(cf["memory_vs_cold_gap"], positive=False))
    K = [
        {"id": "K1", "criterion": "structural transfer prediction outperforms surface-similarity transfer", "passed": k1,
         "evidence": f"within-transformation AUROC archetype {a_within}, delta vs surface {vs_surface.get('all', {}).get('within', {}).get('delta_mean')} CI {vs_surface.get('all', {}).get('within', {}).get('ci95')}; pooled delta {vs_surface.get('all', {}).get('pooled', {}).get('delta_mean')} CI {vs_surface.get('all', {}).get('pooled', {}).get('ci95')}; threshold AUROC >= {TH['K1_min_auroc']}"},
        {"id": "K2", "criterion": "significant useful-evaluation reduction vs both searches on >= 2 unseen transfer families", "passed": k2,
         "evidence": f"{n_win} of {len(fams_t)} transfer families: {sorted(f for f, w in win.items() if w)}"},
        {"id": "K3", "criterion": "false-transfer rate stays low on false-analogy environments", "passed": k3,
         "evidence": f"false-transfer rate {ftr} (threshold <= {TH['K3_max_false_transfer']}); vs search_screen delta {tro['false_transfer_vs']['search_screen'].get('delta_mean')} CI {tro['false_transfer_vs']['search_screen'].get('ci95')}"},
        {"id": "K4", "criterion": "counterfactual interventions change the predicted architectural preference in the true direction", "passed": k4,
         "evidence": f"observable-property pairs: accuracy {k4_obs.get('mean')} CI {k4_obs.get('ci95')} (threshold >= {TH['K4_min_accuracy']}, CI above 0.5); hidden-only pairs: {cfa.get('prediction_hidden', {}).get('mean')}; choice-level all: {cfa.get('choice_all', {}).get('mean')}"},
        {"id": "K5", "criterion": "a structurally reconstructed (novel) architecture provides measurable benefit", "passed": k5,
         "evidence": f"families passing: {rec['families_passing']}; reconstruction events: {rec['n_events']}; share of final architectures that are novel: {rec['novel_final_share']['mean']}"},
        {"id": "K6", "criterion": "architecture search is NOT equal or better everywhere", "passed": k6,
         "evidence": f"pooled transfer reduction vs search_screen {pooled_screen.get('delta_mean')} CI {pooled_screen.get('ci95')}; vs search {red['pooled']['search']['transfer'].get('delta_mean')} CI {red['pooled']['search']['transfer'].get('ci95')}; families won {n_win}; no family won: {lose_all}"},
        {"id": "K7", "criterion": "results survive randomization of superficial cues (fully scrambled surfaces)", "passed": k7,
         "evidence": f"scrambled surfaces: within-AUROC delta vs surface {scr.get('within', {}).get('delta_mean')} CI {scr.get('within', {}).get('ci95')}; e2u reduction vs search_screen {red['pooled']['search_screen']['transfer_scrambled'].get('delta_mean')} CI {red['pooled']['search_screen']['transfer_scrambled'].get('ci95')}"},
        {"id": "K8", "criterion": "structural memory does NOT improve apparent transfer while hurting controlled counterfactuals", "passed": not k8_triggered,
         "evidence": f"e2u reduction from memory (transfer) {mem_t.get('delta_mean')} CI {mem_t.get('ci95')}; memory minus cold gap on interventional environments {cf.get('memory_vs_cold_gap', {}).get('delta_mean')} CI {cf.get('memory_vs_cold_gap', {}).get('ci95')}"},
    ]
    vs_base = pred["versus"].get("principle_memory", {})
    hold_w = pred["versus"].get("surface_similarity", {}).get("transfer_holdout", {})
    hold_fams = [f for f in fams_t if f[0] == "H"]
    S = [
        {"id": "S1", "condition": "predicts when architectural transfer will be useful", "holds": k1 and bool(vs_base) and _sig(vs_base["all"]["pooled"])},
        {"id": "S2", "condition": "prediction survives changed vocabulary / task representation", "holds": bool(scr) and _sig(scr["within"]) and bool(hold_w) and _sig(hold_w["within"])},
        {"id": "S3", "condition": "better than architecture search in at least 2 of 3 unseen transfer environments", "holds": n_win >= TH["S3_min_families"]},
        {"id": "S4", "condition": "at least one structurally reconstructed architecture not present in training", "holds": rec["n_events"] >= 1},
        {"id": "S5", "condition": "the reconstructed architecture provides measurable benefit", "holds": k5},
        {"id": "S6", "condition": "counterfactual interventions change preference in the predicted direction", "holds": k4},
        {"id": "S7", "condition": "avoids harmful transfer to false-analogy environments", "holds": k3},
        {"id": "S8", "condition": "survives removal of superficial similarity signals", "holds": k7},
        {"id": "S9", "condition": "survives held-out environment families", "holds": sum(win[f] for f in hold_fams) >= TH["S9_min_holdout_families"]},
        {"id": "S10", "condition": "survives 30+ seeds", "holds": res["n_seeds"] >= TH["min_seeds"] and res["missing_fraction"] <= TH["max_missing"]},
    ]
    return {"K": K, "S": S, "verdict": verdict(K, S, res["n_seeds"], res["missing_fraction"])}


def verdict(K: List[Dict[str, Any]], S: List[Dict[str, Any]], n_seeds: int, missing: float) -> str:
    """Registered verdict rule. Exactly one of the four registered outcomes; nothing else can be returned."""
    k = {x["id"]: x["passed"] for x in K}
    if n_seeds < TH["min_seeds"] or missing > TH["max_missing"]:
        return "INCONCLUSIVE"
    if all(s["holds"] for s in S):
        return "BREAKTHROUGH_CANDIDATE"
    if not k["K6"] or (not k["K1"] and not k["K2"]):
        return "NO_DISTINCT_CAPABILITY"
    return "PARTIAL_SUPPORT"


def analyze(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    D = Data(results)
    expected = sum(len(r["environments"]) * len(r["config"]["agents"]) for r in results)
    res: Dict[str, Any] = {"n_seeds": len(results), "seeds": D.seeds, "agents": D.agents, "budget": {"phase1": D.b1, "phase2": results[0]["config"]["phase2_budget"]},
                           "missing_fraction": 1 - sum(len(r["episodes"]) for r in results) / max(1, expected),
                           "provenance": {"commits": sorted({r["provenance"].get("git", {}).get("commit", "?") for r in results}),
                                          "dirty": any(r["provenance"].get("git", {}).get("dirty", True) for r in results),
                                          "config_hashes": sorted({r["config_hash"] for r in results}), "versions": results[0]["provenance"]["versions"],
                                          "executor": results[0]["provenance"]["executor"]}}
    res["tables"] = agent_tables(D)
    res["reductions"] = reductions(D)
    res["prediction"] = prediction(D)
    res["transfer_outcomes"] = transfer_outcomes(D)
    res["counterfactuals"] = counterfactuals(D) if results[0]["interventions"] else {"agents": {}, "spec_pairs": {}, "material_pairs_per_seed": describe([])}
    res["reconstruction"] = reconstruction(D, res["reductions"])
    res["ablations"] = ablations(D)
    res["selective"] = selective(D)
    res["regimes"] = regimes(D)
    res["analogy"] = analogy(D)
    res["memory"] = memory_stats(D)
    res["environment"] = {"space_size": describe([e["space_size"] for r in results for e in r["environments"]]),
                          "organizations_of_reference_optima": dict(Counter(e["reference"]["organization"] for r in results for e in r["environments"])),
                          "latent_distance_nearest_train": {w: describe([e["latent_distance_nearest_train"] for r in results for e in r["environments"] if e["world"] == w]) for w in ("transfer_iso", "transfer_holdout", "false")},
                          "surface_similarity_nearest_train": {w: describe([e["surface_similarity_nearest_train"] for r in results for e in r["environments"] if e["world"] == w]) for w in ("transfer_iso", "transfer_holdout", "false")}}
    res["controls"] = decoupled_control(D)
    res["criteria"] = criteria(res)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    a = ap.parse_args(argv)
    res = analyze(load(a.run_dir))
    out = Path(a.run_dir) / "analysis.json"
    out.write_text(json.dumps(res, indent=1, default=str))
    print(f"seeds: {res['n_seeds']}  missing: {res['missing_fraction']:.3f}")
    for k in res["criteria"]["K"]:
        print(f"{k['id']}  {'PASS' if k['passed'] else 'FAIL'}  {k['criterion']}\n      {k['evidence']}")
    for s in res["criteria"]["S"]:
        print(f"{s['id']}  {'holds' if s['holds'] else 'does not hold'}  {s['condition']}")
    print("verdict:", res["criteria"]["verdict"])
    print("written:", out)


if __name__ == "__main__":
    main()
