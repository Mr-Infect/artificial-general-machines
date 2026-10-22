"""Report writer (spec §33, §34).

    python -m archetype.reports.write_report results/archetype/registered

Writes archetype/reports/archetype_final.md, breakthrough_events.jsonl and reconstruction_events.jsonl.
Every sentence that states an outcome is selected by the data; the verdict is the registered rule's output.
If the verdict is BREAKTHROUGH_CANDIDATE the replication of spec §35 runs first and must agree.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from archetype.architecture.roles import MEMORIZED_THRESHOLD, ORGANIZATIONS
from archetype.experiments.registration import DEVELOPMENT_SEEDS, REGISTERED_SEEDS, code_hashes
from archetype.metrics.analysis import SEARCHES, TH, analyze, load

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "archetype" / "reports"
QUESTION = ("Did the system learn a transferable relationship between environmental structure and computational organization that cannot be explained by "
            "task memorization, architecture copying, surface similarity, or ordinary architecture search?")
NAMES = {"fixed": "B0 fixed", "adaptive": "B1 adaptive workflow", "search": "B2 search (mutation)", "search_screen": "B2 search (screening)", "task_memory": "B3 task memory",
         "architecture_memory": "B4 architecture memory", "principle_memory": "B5 principle memory", "always_adapt": "B6 always adapt", "never_adapt": "B7 never adapt",
         "random_transfer": "B8 random transfer", "surface_similarity": "B9 surface similarity", "latent_oracle": "B10 latent oracle (analysis only)", "archetype": "B11 ARCHETYPE"}


def f(x: Optional[float], d: int = 3) -> str:
    return "n/a" if x is None else f"{x:.{d}f}"


def ci(p: Dict[str, Any], d: int = 3) -> str:
    lo, hi = p.get("ci95", [None, None])
    return "n/a" if lo is None else f"[{lo:.{d}f}, {hi:.{d}f}]"


def ms(p: Dict[str, Any], d: int = 2) -> str:
    return "n/a" if p.get("mean") is None else f"{p['mean']:.{d}f} {ci(p, d)}"


def dl(p: Dict[str, Any], d: int = 2) -> str:
    if p.get("delta_mean") is None:
        return "n/a"
    lo, hi = p["ci95"]
    star = " *" if (lo > 0 or hi < 0) else ""
    return f"{p['delta_mean']:+.{d}f} {ci(p, d)}{star}"


def table(header: List[str], rows: List[List[str]]) -> str:
    return "\n".join(["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + ["| " + " | ".join(r) + " |" for r in rows])


def answer(verdict: str, K: Dict[str, bool], S: Dict[str, bool]) -> str:
    if verdict == "BREAKTHROUGH_CANDIDATE":
        return "**YES, as a candidate, within this synthetic laboratory only.** All ten registered success conditions held in the registered run and in the automatic replication. The experiments are listed in sections 8-13."
    if verdict == "NO_DISTINCT_CAPABILITY":
        return "**NO.**"
    if verdict == "PARTIAL_SUPPORT":
        return "**PARTIAL.** Only what is listed below as demonstrated was demonstrated."
    return "**The run cannot answer the question (INCONCLUSIVE).**"


def build(run_dir: Path) -> str:
    results = load(str(run_dir))
    res = analyze(results)
    (run_dir / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    reg = json.loads((OUT / "registration.json").read_text()) if (OUT / "registration.json").exists() else None
    sanity = json.loads((OUT / "sanity_report.json").read_text()) if (OUT / "sanity_report.json").exists() else None
    crit = res["criteria"]
    verdict = crit["verdict"]
    replication = None
    if verdict == "BREAKTHROUGH_CANDIDATE":
        from archetype.experiments.replicate import main as replicate
        replication = replicate()
        if replication != "BREAKTHROUGH_CANDIDATE":
            verdict = "PARTIAL_SUPPORT"
    K = {k["id"]: k["passed"] for k in crit["K"]}
    S = {s["id"]: s["holds"] for s in crit["S"]}
    T, red, pred, tro, cf, rec, abl = res["tables"], res["reductions"], res["prediction"], res["transfer_outcomes"], res["counterfactuals"], res["reconstruction"], res["ablations"]
    agents = res["agents"]
    registered = bool(reg) and sorted(res["seeds"]) == REGISTERED_SEEDS
    hashes_ok = bool(reg) and reg["code_hashes"] == code_hashes()
    commit_ok = bool(reg) and res["provenance"]["commits"] and not res["provenance"]["dirty"]
    arch_v = tro["archetype_variants"].get("archetype", {})
    L: List[str] = []
    A = L.append
    A(f"# ARCHETYPE final report — verdict: **{verdict}**\n")
    A("*Learning the relationship between environment structure and computational organization.* A separate experimental phase on the AGM laboratory. "
      "The AGM hypothesis (v0.1-v0.3) concluded with verdict FAIL; nothing here revises that.\n")
    # 1 ------------------------------------------------------------------
    A("## 1. Executive summary\n")
    A(f"- Run: {res['n_seeds']} seeds ({min(res['seeds'])}-{max(res['seeds'])}), {len(agents)} agents, missing records {res['missing_fraction']:.1%}. "
      f"{'This is the registered evaluation run.' if registered else 'THIS IS NOT THE REGISTERED RUN (seeds differ from the registration); it is not evidence.'}")
    A(f"- Registered verdict rule output: **{verdict}**." + (f" Automatic replication verdict: {replication}." if replication else ""))
    A(f"- Kill criteria passed: {', '.join(k for k, v in K.items() if v) or 'none'}. Failed: {', '.join(k for k, v in K.items() if not v) or 'none'}.")
    A(f"- Success conditions holding: {', '.join(k for k, v in S.items() if v) or 'none'}. Not holding: {', '.join(k for k, v in S.items() if not v) or 'none'}.")
    A(f"- Final question: {answer(verdict, K, S)}")
    A("- **Scope of any claim.** The structure-to-organization relationship in this laboratory is planted by the experimenter in a hidden, simulated fitness function, and "
      "the generator and the learner have the same author. Results say whether a simple interpretable learner recovers and transfers a planted relationship under the "
      "controls below. They say nothing about whether such relationships exist in natural task environments. Architectures are scored by simulation; they do not process data.\n")
    # 2 ------------------------------------------------------------------
    A("## 2. Hypothesis\n")
    A("**H.** A sufficiently general computational system can discover transferable relationships between structural properties of an environment and the computational "
      "organization required to perform well in it: it experiences training environments, extracts structural relations rather than memorizing tasks, recognizes a structural "
      "correspondence in an environment with different vocabulary, representation and primitives, reconstructs an appropriate architecture there with fewer evaluations than a "
      "cold system, and rejects transfer when the correspondence is false.\n")
    A(f"Registered in `docs/archetype_registration.md` and `archetype/reports/registration.json`"
      + (f" at commit `{reg['git']['commit'][:12]}` ({reg['registered_at']})." if reg else " (registration record missing).") + "\n")
    # 3 ------------------------------------------------------------------
    b = res["budget"]
    A("## 3. Experimental design\n")
    A(f"Per seed: (1) **training world**, 10 structural families x 3 surface realizations, one shared exploration of {results[0]['config']['train_budget']} evaluations per environment "
      f"recorded identically for every agent; ARCHETYPE variants may additionally run counterfactual experiments through anonymous intervention knobs. (2) **Freeze**: each agent's "
      f"learned state is hashed; the protocol aborts if it changes during evaluation. (3) **Transfer world**: 5 isomorphic families (same latent region as a training family, unseen "
      f"vocabulary themes, shapes, scales and primitive inventories) and 5 compositional hold-out families (factor pairs never seen in training). (4) **False-analogy world**: 10 "
      f"families that copy the vocabulary theme, shapes and all observable properties of a training family and flip its hidden-only properties. (5) **Interventional pairs**: for "
      f"every transfer family and every latent property, two environments that differ in exactly that property.\n")
    A(f"Each test episode: phase 1 with {b['phase1']} evaluations, then (in about half of the environments) a hidden shift of one latent property and phase 2 with {b['phase2']} "
      f"evaluations. After every evaluation the agent's declared incumbent is scored noise-free by the evaluator. *Useful* = the incumbent closes at least 80% of the gap between "
      f"single-pass and the exhaustive noise-free optimum. **Evaluations-to-useful (E2U)** is censored at {b['phase1'] + 1}. The third surface of every family is fully "
      f"token-scrambled. Unit of analysis: the seed. Statistics: bootstrap 95% CI and paired deltas (`experiments.analysis`). `*` marks a CI excluding zero.\n")
    # 4 ------------------------------------------------------------------
    env = res["environment"]
    A("## 4. Environment generator\n")
    A("`EnvironmentGenome`: 15 hidden properties in [0, 1]. Ten leave statistical traces in the observation channels (dependency depth, branching factor, parallelizability, "
      "observation noise, temporal correlation, state volatility, resource constraint, verification cost, delayed feedback, action reversibility); five are **hidden-only** and "
      "show only in evaluation outcomes (coupling, adversariality, information decay, uncertainty, failure cost). Families are pairs of structural factors; in training, hidden-only "
      "properties are confounded with observable ones through the factors, and false analogies break that confounding. Fitness = structural match of genome and role-level "
      "organization, minus costs, plus noise and failure events (`archetype/latent_structure/fitness.py`), never shown to agents.\n")
    A(table(["world", "latent distance to nearest training genome", "surface similarity to nearest training environment"],
            [[w, ms(env["latent_distance_nearest_train"][w], 3), ms(env["surface_similarity_nearest_train"][w], 3)] for w in ("transfer_iso", "transfer_holdout", "false")]) + "\n")
    A(f"In false-analogy environments the organization that was optimal in the look-alike training environment closes {ms(tro['matched_optimum_gap_in_false'])} of the gap "
      f"(isomorphic twins: {ms(tro['matched_optimum_gap_in_iso'])}); {ms(tro['environments_with_traps'])} of false-analogy environments contain at least one *trap* "
      f"(a transformation that helped in the look-alike and hurts here).\n")
    # 5 ------------------------------------------------------------------
    A("## 5. Architecture space\n")
    A("Composition trees over `unit | serial | parallel+merge | conditional | loop | hier`, canonicalized and hashed (`archetype/architecture/graph.py`). Each environment has its "
      "own primitives with random names; agents see interface signatures and prices only. The evaluator maps trees to abstract roles to classify the ten organizations and to "
      f"measure role-level distance. Configurations per environment: {ms(env['space_size'], 0)} (min {env['space_size']['min']:.0f}).\n")
    A("Organization of the noise-free optimum across test environments: " + ", ".join(f"{k} {ORGANIZATIONS[k]} ({v})" for k, v in sorted(env["organizations_of_reference_optima"].items(), key=lambda x: -x[1])) + ".\n")
    # 6 ------------------------------------------------------------------
    mem = res["memory"]
    A("## 6. Learner\n")
    A("Observation encoder (37 generic scale/sign/order-invariant statistics) -> relation model (per architectural transformation, a depth-2 regression tree for readable rules "
      "and 15 bagged trees for confidence) -> principles with antecedent rules, contraindications, trust, history and status -> counterfactual experiments in training "
      "(test, refine, flag unobservable conditions, retire) -> per-principle decision TRUST / TEST / REJECT / IGNORE / ABSTAIN -> architecture constructor from local primitives "
      "by signature -> refinement with an economics stop -> regime detection between phases. No neural network, no language model.\n")
    A(table(["quantity (per seed)", "mean [95% CI]"],
            [["principles in use", ms(mem["principles"])], ["principles flagged as depending on an unobservable condition", ms(mem["hidden_sensitive"])], ["principles retired (forgotten)", ms(mem["retired"])],
             ["counterfactual evaluations in training", ms(mem["counterfactual_evaluations"], 0)], ["principles applied or tested per environment", ms(mem["principle_reuse_per_environment"])],
             ["share of tested principles contradicted by the test", ms(mem["principle_contradiction_rate"])], ["memory precision (predicted to help and truly helps)", ms(mem["memory_precision"])]]) + "\n")
    A(f"Principle status counts over all seeds: {mem['status_counts']}.\n")
    ex = (results[0]["agents"].get("archetype") or {}).get("snapshot")
    if ex:
        A(f"Principles learned in seed {results[0]['seed']} (verbatim from the frozen memory):\n")
        A("```\n" + "\n".join(p["description"] for p in ex["store"]["principles"].values()) + "\n```\n")
    # 7 ------------------------------------------------------------------
    A("## 7. Baselines\n")
    for w, title in (("transfer_iso", "Isomorphic transfer families"), ("transfer_holdout", "Compositional hold-out families"), ("false", "False-analogy families")):
        A(f"**{title}** (phase 1; mean over seeds [95% CI])\n")
        A(table(["agent", "E2U", "never useful", "final gap closure", "evaluations used", "failure rate", "harmful element in final", "novelty"],
                [[NAMES.get(a, a), ms(T[w][a]["e2u"], 1), ms(T[w][a]["censored"]), ms(T[w][a]["gap"]), ms(T[w][a]["evaluations"], 1), ms(T[w][a]["failure_rate"], 3),
                  ms(T[w][a]["harmful_element"]), ms(T[w][a]["novelty"], 3)] for a in agents]) + "\n")
    A("Secondary resource metrics of the final architecture (transfer worlds pooled by world): structural operations, cost units, latency, memory units.\n")
    A(table(["agent", "operations (iso)", "cost (iso)", "latency (iso)", "memory (iso)", "adaptation cost in evaluation price units (iso)"],
            [[NAMES.get(a, a), ms(T["transfer_iso"][a]["operations"], 1), ms(T["transfer_iso"][a]["arch_cost"], 1), ms(T["transfer_iso"][a]["latency"], 0), ms(T["transfer_iso"][a]["memory"], 1),
              ms(T["transfer_iso"][a]["adaptation_cost"], 0)] for a in agents]) + "\n")
    # 8 ------------------------------------------------------------------
    A("## 8. Transfer matrix\n")
    A("Useful-evaluation reduction of ARCHETYPE: comparator E2U minus ARCHETYPE E2U, paired by seed (positive = ARCHETYPE needed fewer evaluations).\n")
    comps = ["search", "search_screen", "architecture_memory", "principle_memory", "surface_similarity", "archetype_no_structural_memory"]
    fams = sorted(red["by_family"]["search"])
    A(table(["family"] + [NAMES.get(c, c) for c in comps], [[fam] + [dl(red["by_family"][c][fam], 1) for c in comps] for fam in fams]) + "\n")
    A(table(["pooled"] + [NAMES.get(c, c) for c in comps],
            [[w] + [dl(red["pooled"][c][w], 1) for c in comps] for w in ("transfer", "transfer_iso", "transfer_holdout", "transfer_scrambled", "false")]) + "\n")
    A("Final quality (gap closure) of ARCHETYPE minus comparator:\n")
    A(table(["scope"] + [NAMES.get(c, c) for c in comps], [[w] + [dl(red["pooled"][c][w], 3) for c in comps] for w in ("quality_transfer", "quality_false")]) + "\n")
    A("**Predicting when a transformation will help** (zero evaluations; AUROC against the noise-free effect; *within* = averaged per transformation, which removes base rates):\n")
    scorers = list(pred["agents"])
    A(table(["agent", "pooled AUROC (all)", "within AUROC (all)", "within (iso)", "within (hold-out)", "within (false)", "within (scrambled)", "AUPRC (all)"],
            [[NAMES.get(a, a), ms(pred["agents"][a]["all"]["pooled"], 3), ms(pred["agents"][a]["all"]["within"], 3), ms(pred["agents"][a]["transfer_iso"]["within"], 3),
              ms(pred["agents"][a]["transfer_holdout"]["within"], 3), ms(pred["agents"][a]["false"]["within"], 3), ms(pred["agents"][a]["scrambled"]["within"], 3),
              ms(pred["agents"][a]["all"]["auprc"], 3)] for a in scorers]) + "\n")
    if "calibration" in pred:
        A(f"ARCHETYPE confidence calibration: ECE {f(pred['calibration']['ece'])}, Brier {f(pred['calibration']['brier'])} over {pred['calibration']['n']} (environment, transformation) pairs. "
          f"Per transformation AUROC: " + ", ".join(f"{t} {f(v['mean'], 2)}" for t, v in pred["per_transformation"].items()) + ".\n")
    an = res["analogy"]
    A(f"**Environment-level structural analogy** (is the look-alike training environment's optimum useful here? isomorphic twins vs false analogies; AUROC): ARCHETYPE zero-evaluation "
      f"score similarity {ms(an['auroc']['archetype'], 3)}, surface similarity {ms(an['auroc']['surface_similarity'], 3)}, latent distance (oracle) {ms(an['auroc']['latent_distance_oracle'], 3)}. "
      f"False analogies differ from their source only in unobservable properties, so a zero-evaluation score cannot separate them; separation has to come from testing (section 11).\n")
    ctl = res["controls"]
    A(f"**Decoupling control.** With observations generated from a different family's structure than the one driving fitness, ARCHETYPE's within-transformation AUROC is "
      f"{ms(ctl['within_auroc_decoupled_observations'], 3)} against {ms(ctl['within_auroc_real_observations'], 3)} with real observations (difference {dl(ctl['real_minus_decoupled'], 3)}).\n")
    if arch_v:
        A(f"**Structural transfer success** (transfer worlds): architecture built from accepted principles is useful in {ms(arch_v['structural_transfer_success'])} of environments; "
          f"built from frozen knowledge alone with zero evaluations: {ms(arch_v['zero_evaluation_transfer_success'])}; proposal has the same organization class as the optimum: "
          f"{ms(arch_v['reconstruction_organization_match'])}; missed-transfer rate (truly useful transformation not adopted): {ms(arch_v['missed_transfer_rate'])}.\n")
        A(f"Decisions over all test environments: per principle {arch_v['principle_decisions']}; per environment {arch_v['environment_decisions']}.\n")
    sel = res["selective"]
    A(f"**Abstention.** Coverage {f(sel['coverage'])}; risk when the learner decided {f(sel['risk_when_decided'])}; risk had it been forced to decide on the abstained cases "
      f"{f(sel['risk_if_forced_on_abstained'])}; risk at full coverage {f(sel['risk_at_full_coverage'])}. Risk-coverage curve (most confident first): "
      + ", ".join(f"{p['coverage']:.0%}: {p['risk']:.3f}" for p in sel["risk_coverage_curve"]) + ".\n")
    # 9 ------------------------------------------------------------------
    A("## 9. Counterfactual results\n")
    if cf["agents"]:
        A(f"Interventional pairs: same surface, exactly one latent property set low (0.1) vs high (0.9). A pair is *material* for a transformation when its noise-free effect changes "
          f"by at least 0.03 ({ms(cf['material_pairs_per_seed'], 0)} material pairs per seed). *Prediction*: the zero-evaluation score moves in the true direction. "
          f"*Choice*: the transformation enters or leaves the final architecture exactly as it enters or leaves the noise-free optimum.\n")
        A(table(["agent", "prediction, observable properties", "prediction, hidden-only properties", "choice, observable", "choice, hidden-only", "gap closure on interventional environments"],
                [[NAMES.get(a, a), ms(v["prediction_observable"]), ms(v["prediction_hidden"]), ms(v["choice_observable"]), ms(v["choice_hidden"]), ms(v["gap"])] for a, v in cf["agents"].items()]) + "\n")
        A("The five pairs named in the specification (mean change of the true effect from low to high; share of cases where each agent's prediction moved the right way):\n")
        ia = list(cf["agents"])
        A(table(["intervention -> transformation", "true change"] + [NAMES.get(a, a) for a in ia],
                [[k, f(v["mean_truth_change"])] + [f(v.get(a), 2) for a in ia] for k, v in cf["spec_pairs"].items()]) + "\n")
        if "memory_vs_cold_gap" in cf:
            A(f"Structural memory vs the same agent without it on interventional environments: gap closure {dl(cf['memory_vs_cold_gap'], 3)}, choice accuracy {dl(cf['memory_vs_cold_choice'], 3)}.\n")
    else:
        A("No interventional pairs in this run.\n")
    # 10 -----------------------------------------------------------------
    A("## 10. Structural reconstruction events\n")
    A(f"A final architecture counts as a STRUCTURAL RECONSTRUCTION EVENT when (1) its role-level distance to every architecture observed in training is at least {MEMORIZED_THRESHOLD} "
      f"(otherwise it is MEMORIZED TRANSFER), (2) every accepted principle's transformation is present and truly helps, and (3) it is useful. Events: **{rec['n_events']}**. "
      f"Share of ARCHETYPE's final architectures in transfer worlds that are novel at role level: {ms(rec['novel_final_share'])}.\n")
    A(table(["family", "event rate", "surfaces with events", "seeds with events", "beats both searches on E2U", "passes K5"],
            [[k, f(v["event_rate"], 2), str(v["surfaces_with_events"]), str(v["seeds_with_events"]), str(v["beats_both_searches_e2u"]), str(v["passes"])] for k, v in sorted(rec["by_family"].items())]) + "\n")
    n_break = sum(1 for e in rec["events"] if e["breakthrough_conditions_met"])
    A(f"Events meeting every condition of the breakthrough event log (spec §34): **{n_break}** (written to `breakthrough_events.jsonl`; all reconstruction events are in `reconstruction_events.jsonl`).\n")
    # 11 -----------------------------------------------------------------
    A("## 11. False-transfer results\n")
    A("False transfer: a trap transformation ends up, harmful, in the final phase-1 architecture of a false-analogy environment.\n")
    A(table(["agent", "false-transfer rate", "agent minus ARCHETYPE (paired)"],
            [[NAMES.get(a, a), ms(tro["false_transfer_rate"][a]), dl(tro["false_transfer_vs"][a]) if a in tro["false_transfer_vs"] else "-"] for a in agents]) + "\n")
    if arch_v:
        A(f"At decision level, ARCHETYPE adopted {ms(arch_v['trap_adoption_rate'])} of trap transformations (TRUST, or TEST followed by acceptance).\n")
    # 12 -----------------------------------------------------------------
    A("## 12. Ablations\n")
    A("Each row removes one component. Deltas are ablated minus full, paired by seed. For E2U and false transfer a negative delta means the removal helped; for gap closure a positive delta means the removal helped.\n")
    A(table(["ablation", "E2U transfer", "E2U false", "gap transfer", "gap false", "false-transfer rate", "evaluations used", "phase-2 gap", "evidence against the component"],
            [[a.replace("archetype_no_", "without "), dl(v["e2u_transfer"], 1), dl(v["e2u_false"], 1), dl(v["gap_transfer"], 3), dl(v["gap_false"], 3), dl(v["false_transfer"], 3),
              dl(v["evaluations"], 1), dl(v["phase2_gap"], 3), "YES: " + ", ".join(v["removal_improves"]) if v["evidence_against_component"] else ("mixed: improves " + ", ".join(v["removal_improves"]) if v["removal_improves"] else "no")]
             for a, v in abl.items()]) + "\n")
    rg = res["regimes"]
    A("Regime shift (phase 2):\n")
    A(table(["agent", "gap after a shift", "gap of the kept incumbent before adapting", "evaluations when shifted", "evaluations when nothing changed", "detection rate", "false-alarm rate"],
            [[NAMES.get(a, a), ms(v["gap_after_shift"]), ms(v["gap_kept_before_adapting"]), ms(v["evaluations_when_shifted"], 1), ms(v["evaluations_when_not_shifted"], 1),
              ms(v["detection_rate"]) if "detection_rate" in v else "-", ms(v["false_alarm_rate"]) if "false_alarm_rate" in v else "-"] for a, v in rg.items()]) + "\n")
    # 13 -----------------------------------------------------------------
    A("## 13. Statistical analysis\n")
    A(f"Seeds: {res['n_seeds']}. Paired comparisons by seed with 2000 bootstrap resamples; a comparison is called significant only when its 95% CI excludes zero. No correction for "
      f"multiple comparisons is applied to the descriptive tables; the registered criteria are the fixed set below. Family-level criteria use the mean over the three surfaces of the family within a seed. "
      f"Censoring: E2U is set to budget + 1 when an agent never becomes useful, which compresses differences among agents that often fail.\n")
    # 14 -----------------------------------------------------------------
    A("## 14. Failure cases\n")
    worse = [fam for fam in fams if fam[0] in "BH" and any((red["by_family"][c][fam].get("ci95") or [0, 0])[1] is not None and red["by_family"][c][fam]["ci95"][1] < 0 for c in SEARCHES)]
    A(f"- Transfer families where ARCHETYPE needed significantly MORE evaluations than a search baseline: {worse or 'none'}.")
    if "per_transformation" in pred:
        weak = [t for t, v in pred["per_transformation"].items() if v["mean"] is not None and v["mean"] < 0.6]
        A(f"- Transformations whose usefulness ARCHETYPE could not predict (AUROC below 0.6): {weak or 'none'}.")
    against = [a.replace("archetype_no_", "") for a, v in abl.items() if v["evidence_against_component"]]
    A(f"- Components whose removal improved results (evidence against the component): {against or 'none'}.")
    if cf["agents"].get("archetype"):
        A(f"- Hidden-only interventions: zero-evaluation prediction accuracy {ms(cf['agents']['archetype']['prediction_hidden'])}. By construction the frozen learner sees no difference between the two environments of such a pair.")
    A(f"- Failed kill criteria: {', '.join(k['id'] + ' (' + k['criterion'] + ')' for k in crit['K'] if not k['passed']) or 'none'}.\n")
    # 15 -----------------------------------------------------------------
    A("## 15. Reproducibility\n")
    pv = res["provenance"]
    A(f"- Run commit(s): {pv['commits']}; working tree dirty during the run: {pv['dirty']}; configuration hash(es): {pv['config_hashes']}; executor: `{pv['executor']}`; versions: {pv['versions']}.")
    A(f"- Registration: {'commit ' + reg['git']['commit'][:12] + ', config hash ' + reg['config_hash'] if reg else 'missing'}; code identical to the registered code: {hashes_ok}; run made from a clean commit: {bool(commit_ok)}.")
    A(f"- Development seeds {DEVELOPMENT_SEEDS[0]}-{DEVELOPMENT_SEEDS[-1]} were used to build and calibrate; they are not evidence. Registered seeds: {REGISTERED_SEEDS[0]}-{REGISTERED_SEEDS[-1]}.")
    A("- Every seed shard records seed, genome hashes, surface seeds, configuration, timestamps and a record hash; `python -m archetype.experiments.replay <shard>` re-executes it and compares the hash.")
    A("- Commands: `python -m archetype.experiments.sanity`, `python -m archetype.experiments.registration`, "
      "`python -m archetype.experiments.run --name registered --seeds $(seq 1000 1029) --workers 8`, `python -m archetype.reports.write_report results/archetype/registered`.")
    if sanity:
        A(f"- Sanity experiment (3 seeds, before registration): {'passed' if sanity['passed'] else 'FAILED'}, {sum(c['passed'] for c in sanity['checks'])} of {len(sanity['checks'])} checks.\n")
    # 16 -----------------------------------------------------------------
    A("## 16. Kill criteria\n")
    A(table(["id", "criterion", "result", "evidence"], [[k["id"], k["criterion"], "**PASS**" if k["passed"] else "**FAIL**", k["evidence"]] for k in crit["K"]]) + "\n")
    A(table(["id", "success condition", "holds"], [[s["id"], s["condition"], "yes" if s["holds"] else "no"] for s in crit["S"]]) + "\n")
    # 17 -----------------------------------------------------------------
    A("## 17. Final verdict\n")
    A(f"**{verdict}**\n")
    A(f"> {QUESTION}\n")
    A(answer(verdict, K, S) + "\n")
    shown = []
    if K["K1"]:
        shown.append("the frozen learner's zero-evaluation scores predict which architectural transformations help in unseen environments better than surface similarity does, including on fully scrambled surfaces" if K["K7"] or S["S2"] else
                     "the frozen learner's zero-evaluation scores predict which architectural transformations help in unseen environments better than surface similarity does")
    if K["K2"]:
        shown.append(f"a significant reduction of evaluations-to-useful against both search baselines in {sum(1 for fam in fams if fam[0] in 'BH' and all((red['by_family'][c][fam].get('ci95') or [0, 0])[0] is not None and red['by_family'][c][fam]['ci95'][0] > 0 for c in SEARCHES))} of 10 transfer families")
    if K["K3"]:
        shown.append("a low rate of harmful transfer into false-analogy environments")
    if K["K4"]:
        shown.append("predicted preferences that move in the true direction under single-property interventions on observable properties")
    if K["K5"]:
        shown.append("at least one family with replicated structural reconstruction events that beat cold search")
    not_shown = [k["criterion"] for k in crit["K"] if not k["passed"]]
    A("Demonstrated in this run: " + ("; ".join(shown) + "." if shown else "nothing beyond the baselines."))
    A("Not demonstrated: " + ("; ".join(not_shown) + "." if not_shown else "-"))
    if verdict != "BREAKTHROUGH_CANDIDATE":
        A("\nNo breakthrough is claimed. Thresholds, metrics, learner, environments and search budgets were fixed before this run and were not changed afterwards.")
    A("\nWhatever the verdict, it concerns a planted relationship in a simulated laboratory (section 1).")
    (OUT / "reconstruction_events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in rec["events"]))
    (OUT / "breakthrough_events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in rec["events"] if e["breakthrough_conditions_met"]))
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    run_dir = Path((argv or sys.argv[1:])[0])
    out_name = (argv or sys.argv[1:])[1] if len(argv or sys.argv[1:]) > 1 else "archetype_final.md"
    text = build(run_dir)
    (OUT / out_name).write_text(text)
    print(f"written: {OUT / out_name}")
    print(text.split("\n")[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
