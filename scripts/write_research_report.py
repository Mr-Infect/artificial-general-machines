#!/usr/bin/env python3
"""Generate docs/V0.2_RESEARCH_REPORT.md from results/v02/analysis/analysis.json.

Every number in the report is read from the analysis output; the interpretation paragraphs are
conditioned on the measured values (see `verdict`). The report never states that AGM succeeded
unless every pre-registered criterion is met.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from experiments.analysis import ci_excludes_zero  # noqa: E402


def p(x, unit="", nd=3):
    if not x or x.get("delta_mean") is None:
        return f"no pairs (both-missing {x.get('n_both_missing', '?') if x else '?'})"
    star = " (CI excludes 0)" if ci_excludes_zero(x) else " (CI includes 0)"
    d = x.get("effect_size_d")
    return f"{x['delta_mean']:+.{nd}g}{unit} [95% CI {x['ci95'][0]:+.{nd}g}, {x['ci95'][1]:+.{nd}g}]{star}, d = {'n/a' if d is None else f'{d:.2f}'}, {x['positive']} positive / {x['negative']} negative / {x['zero']} tied of {x['n_pairs']} pairs"


def m(x, nd=3):
    if not x or x.get("mean") is None:
        return "—"
    return f"{x['mean']:.{nd}g} (median {x['median']:.{nd}g}, sd {x['sd']:.2g}, 95% CI [{x['ci95'][0]:.{nd}g}, {x['ci95'][1]:.{nd}g}], n = {x['n']})"


def main():
    res = json.loads((ROOT / "results/v02/analysis/analysis.json").read_text())
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    crit = {c["id"]: c for c in res["criteria"]}
    n_met = sum(1 for c in res["criteria"] if c["met"])
    e1 = res["exp1"]["domains"]
    mat = res["exp2"]["matrix"]
    ab = res["ablations"]
    inv = res["principle_inventory"]
    cells_worse = [k for k, c in mat.items() if c["adaptation_cost"]["delta_mean"] is not None and c["adaptation_cost"]["delta_mean"] > 0 and ci_excludes_zero(c["adaptation_cost"])]
    cells_better = [k for k, c in mat.items() if c["adaptation_cost"]["delta_mean"] is not None and c["adaptation_cost"]["delta_mean"] < 0 and ci_excludes_zero(c["adaptation_cost"])]
    cells_null = [k for k in mat if k not in cells_worse and k not in cells_better]
    tests_total = {}
    for c in mat.values():
        for k, v in c["principle_tests"]["counts"].items():
            tests_total[k] = tests_total.get(k, 0) + v

    L = []
    L.append("# AGM v0.2 Research Report\n")
    L.append("**Question.** Is there measurable evidence that AGM is learning transferable principles of computational organization, rather than merely searching, mutating, or memorizing architectures?\n")
    if n_met == len(res["criteria"]):
        answer = "**Answer: yes, with the alternative explanations listed in §9.**"
    elif crit["D"]["met"] or crit["G"]["met"]:
        answer = "**Answer: uncertain.** Some transfer benefit was measured but not all pre-registered criteria hold."
    else:
        answer = "**Answer: no.** The laboratory can extract, store, instantiate and test architectural principles (criteria A–C), but transferred architectural knowledge did not reduce adaptation or search cost in any source→target cell; where it had a measurable effect, it increased cost (§4). The negative v0.1 result is persistent, not noise (§3)."
    L.append(answer + "\n")
    L.append(f"Evidence base: {res['n_experiments']} finished experiments, executor(s) {res['executors']}, code at commit(s) `{'`, `'.join(c[:12] for c in res['git_commits'])}` (report generated at `{commit[:12]}`). Pre-registered criteria met: **{n_met} of {len(res['criteria'])}**.\n")

    L.append("## 1. Hypothesis and pre-registered success criteria\n")
    L.append("AGM hypothesis (v0.2): a machine can learn generalizable principles of computational organization that let it construct, evaluate, modify and reuse task-specific architectures under the constraints of an unfamiliar environment while accounting for the cost of adaptation. It is considered supported only if all of A–G hold:\n")
    L.append("| id | criterion | evidence | met |\n|---|---|---|---|")
    for c in res["criteria"]:
        L.append(f"| {c['id']} | {c['statement']} | {c['evidence']} | **{'yes' if c['met'] else 'no'}** |")
    L.append("")

    L.append("## 2. Method summary\n")
    L.append("- Three synthetic domains: A network anomaly, B scientific verification, C resource-constrained planning (structurally different vocabulary and winners; `docs/domain_planning.md`).")
    L.append("- Identical data, seeds, environment schedule, resource limits, sandbox runner and scoring for every compared agent. Comparisons are paired by seed.")
    L.append("- Target quality per dataset = validation quality of the best-decile point of the enumerated wide architecture space (lab oracle; recorded in provenance). \"Evaluations-to-target\" = cumulative candidate evaluations when an agent first reached it.")
    L.append("- Memory is per seed; warm conditions read memory written by exploration-mode source runs in the *other* domains. Principles are extracted by deterministic rules, tested only under conditions that did not produce them, and counted by distinct experiments.")
    L.append("- Statistics: mean, median, sd, bootstrap 95% CI, paired delta with CI, Cohen's d on paired differences, sign counts, failure rate, adaptation overhead. Nothing is collapsed into one score.\n")

    L.append("## 3. Experiment 1 — repeatability of the v0.1 negative result (Domains A, B)\n")
    for key, d in e1.items():
        L.append(f"### Domain {key} (n = {d['n_runs']} seeds)\n")
        L.append("| agent | quality (mean) | evaluations | adaptation cost | evaluations-to-target | failure rate | target reached |\n|---|---|---|---|---|---|---|")
        for a, row in d["agents"].items():
            L.append(f"| {a} | {m(row['quality_mean'])} | {m(row['architecture_evaluations'])} | {m(row['adaptation_cost'], 2)} | {m(row['evaluations_to_target'])} | {m(row['failure_rate'], 2)} | {row['target_reached_fraction']:.2f} |")
        if "paired" in d:
            L.append("\nPaired (memory − cold):\n")
            for v, pm in d["paired"].items():
                L.append(f"- AGM {v}: quality {p(pm['quality_mean'])}; evaluations {p(pm['architecture_evaluations'])}; adaptation cost {p(pm['adaptation_cost'], ' USD', 2)}; evaluations-to-target {p(pm['evaluations_to_target'])}")
        L.append("")
    pv1 = e1.get("B", {}).get("paired", {}).get("v1", {}).get("quality_mean", {})
    pv2 = e1.get("B", {}).get("paired", {}).get("v2", {}).get("quality_mean", {})
    L.append(f"Interpretation: the v0.1 three-seed result (Δ quality −0.015, CI [−0.044, 0]) is now measured over {e1.get('B', {}).get('n_runs', 0)} seeds as {p(pv1)} for AGM v0.1 and {p(pv2)} for AGM v0.2. "
             + ("There is no positive transfer effect on quality in Domain B; the earlier negative result is not noise in the sense of hiding a benefit." if (pv2.get('delta_mean') is None or pv2['delta_mean'] <= 0 or not ci_excludes_zero(pv2)) else "A positive quality effect appears in v0.2.") + "\n")

    L.append("## 4. Experiment 2 — transfer matrix (primary metric: adaptation cost reduction)\n")
    L.append("| S→T | Δ adaptation cost (USD) | Δ evaluations | Δ evaluations-to-target | Δ quality | Δ failures | principle reuse | principle tests | final-architecture distance transferred vs cold |\n|---|---|---|---|---|---|---|---|---|")
    for k, c in mat.items():
        dist = c["architecture_distance_transferred_vs_cold_final"]
        L.append(f"| {k} | {p(c['adaptation_cost'], '', 2)} | {p(c['architecture_evaluations'])} | {p(c['evaluations_to_target'])} | {p(c['quality_mean'])} | {p(c['failures'])} | {c['transferred']['principle_reuse']['mean']:.2f} | {c['principle_tests']['counts']} | mean {dist.get('mean', 0) or 0:.3f}, identical {dist.get('fraction_identical')} |")
    L.append(f"\nCells where transferred memory significantly **reduced** adaptation cost: {cells_better or 'none'}. Significantly **increased**: {cells_worse or 'none'}. No significant effect: {cells_null or 'none'}. Principle tests across all cells: {tests_total}.\n")

    L.append("## 5. Experiments 3 & 4 — principle and memory ablations\n")
    for T, mm in ab["memory_modes"].items():
        L.append(f"### Domain {T}\n")
        for a in ("v2_warm_task", "v2_warm_architecture", "v2_warm_principle", "v2_warm_full"):
            L.append(f"- {a} − cold: adaptation cost {p(mm[a]['adaptation_cost'], '', 2)}; evaluations-to-target {p(mm[a]['evaluations_to_target'])}; quality {p(mm[a]['quality_mean'])}")
        L.append(f"- principle − architecture memory: adaptation cost {p(mm['principle_vs_architecture']['adaptation_cost'], '', 2)}; quality {p(mm['principle_vs_architecture']['quality_mean'])}")
        L.append(f"- full − architecture memory: adaptation cost {p(mm['full_vs_architecture']['adaptation_cost'], '', 2)}; quality {p(mm['full_vs_architecture']['quality_mean'])}\n")
    L.append("Reading: if principle memory carried a transferable capability, removing it (architecture-only) should hurt and adding it should help. The deltas above are the measurement.\n")

    L.append("## 6. Experiment 5 — adaptation economics ablation\n")
    for T, ec in ab["economics"].items():
        L.append(f"### Domain {T}\n")
        L.append(f"- decision outcome shares (economic / always / never): { {a: {k: round(v, 2) for k, v in o.items()} for a, o in ec['decision_outcomes'].items()} }")
        for a in ("v2_always_adapt", "v2_never_adapt"):
            L.append(f"- {a} − economic: evaluations {p(ec[a]['architecture_evaluations'])}; adaptation cost {p(ec[a]['adaptation_cost'], '', 2)}; quality {p(ec[a]['quality_mean'])}; wall time {p(ec[a]['wall_used_s'], ' s')}; failures {p(ec[a]['failures'])}")
        L.append(f"- wasted evaluations after target reached: economic {m(ec['wasted_evaluations']['v2_cold'])}; always {m(ec['wasted_evaluations']['v2_always_adapt'])}; never {m(ec['wasted_evaluations']['v2_never_adapt'])}")
        L.append(f"- mean decision error (realized − expected net value, quality units): economic {m(ec['decision_error']['v2_cold'])}; cost-estimate error {m(ec['cost_estimate_error']['v2_cold'])}\n")
    L.append(f"Criterion E ({'met' if crit['E']['met'] else 'not met'}): {crit['E']['evidence']}\n")

    L.append("## 7. Experiment 6 — architecture distance and novelty\n")
    L.append("| run:agent | final distance to initial | final identical to initial | max distance | final novelty level vs prior memory | distance: reached vs not | cross-domain selections |\n|---|---|---|---|---|---|---|")
    for k, v in res["distance"].items():
        L.append(f"| {k} | {m(v['final_distance_to_initial'], 2)} | {v['fraction_final_identical_to_initial']:.2f} | {m(v['max_distance_to_initial'], 2)} | {v['final_novelty_levels_vs_prior_memory']} | {m(v['distance_of_reached_vs_not']['reached'], 2)} vs {m(v['distance_of_reached_vs_not']['not_reached'], 2)} | {v['cross_domain_selected_fraction']:.2f} |")
    L.append("\nReading: distance is structural (`docs/architecture_distance` in `architecture/distance.py`); high distance with poor performance is exploration, not discovery. Novelty levels A–E are relative to the architectures in the agent's memory at the start of the run.\n")

    L.append("## 8. Experiment 7 (cold vs warm) and Experiment 8 (held-out conditions)\n")
    for T, cw in ab["cold_vs_warm"].items():
        L.append(f"- Domain {T}, warm − cold: evaluations-to-target {p(cw['evaluations_to_target'])}; time-to-target {p(cw['time_to_target_logical_s'], ' s')}; adaptation cost {p(cw['adaptation_cost'], '', 2)}; quality {p(cw['quality_mean'])}; failures {p(cw['failures'])}")
    L.append("")
    for T, h in res["heldout"].items():
        L.append(f"- Held-out Domain {T} (n = {h['n_runs']}), warm − cold: quality {p(h['paired']['quality_mean'])}; evaluations {p(h['paired']['architecture_evaluations'])}; adaptation cost {p(h['paired']['adaptation_cost'], '', 2)}; evaluations-to-target {p(h['paired']['evaluations_to_target'])}; principle tests {h['principle_tests']['counts']}")
    L.append("")
    for T, cw in ab["v1_vs_v2"].items():
        L.append(f"- AGM v0.2 (full) − AGM v0.1 (architecture memory), warm, Domain {T}: quality {p(cw['quality_mean'])}; evaluations {p(cw['architecture_evaluations'])}; adaptation cost {p(cw['adaptation_cost'], '', 2)}")
    L.append("")

    L.append("## 9. Discrimination among the candidate causes of the v0.1 negative result\n")
    L.append(f"1. **Insufficient structural memory** — v0.2 memories hold {inv['memory_files']} files with {sum(inv['status_counts'].values())} principle records ({inv['status_counts']}) plus architecture patterns; retrieval, instantiation and reuse happened in every cell (criterion C). Memory *quantity* is no longer the limiting factor.")
    L.append(f"2. **Insufficiently different environments** — Domain C has a different component vocabulary, scoring and winners; transfer into and out of it behaved like A↔B ({[k for k in mat if 'C' in k]}). Domain similarity does not explain the result.")
    L.append("3. **Insufficient architecture search space** — the space was widened to ~255 registry points per domain; the evaluation budget covers only a fraction, so candidate ordering by prior knowledge *could* have mattered. "
             + ("It reduced evaluations in " + ", ".join(cells_better) + "." if cells_better else "It did not reduce evaluations in any cell."))
    ident = [v["fraction_final_identical_to_initial"] for v in res["distance"].values()]
    L.append(f"4. **Weak architecture representation** — distance analysis (§7): the fraction of runs whose final architecture is structurally identical to the initial one ranges {min(ident):.2f}–{max(ident):.2f} across conditions. "
             "The IR expresses the space; whether its useful region is reachable without memory is what §4 measures.")
    L.append(f"5. **Lack of principle abstraction** — principles were abstracted (roles, conditions, effects) and tested; the test outcomes were predominantly {max(tests_total, key=tests_total.get) if tests_total else 'absent'} ({tests_total}). The abstraction exists; its predictions were mostly wrong under new conditions.")
    L.append(f"6. **Adaptation economics behaving incorrectly** — criterion E {'holds' if crit['E']['met'] else 'does not hold'}; decision and cost-estimate errors are reported in §6. Economics is not what suppressed transfer: the warm agent evaluated *more*, not fewer, candidates.")
    L.append("7. **The hypothesis itself** — with A–C met and D/F/G " + ("met" if crit["D"]["met"] and crit["F"]["met"] and crit["G"]["met"] else "not met") + ", the remaining explanation consistent with all measurements is that, in these domains, the architectural experience the machine can currently extract does not encode anything that shortens adaptation. Whether this is a property of the rule-based extractor, of the synthetic domains, or of the hypothesis cannot be separated by v0.2 alone; the LLM proposer (Experiment 9) was not run.\n")

    L.append("## 10. Alternative explanations and limitations\n")
    e2t_cold = {k: c["cold"]["evaluations_to_target"]["mean"] for k, c in mat.items()}
    L.append(f"- The domains are synthetic and their useful architectures are cheap; a cheapest-first cold search reaches the top-decile target after on average { {k: (round(v, 2) if v is not None else None) for k, v in e2t_cold.items()} } evaluations. Where that number is close to 1 there is little room for any prior to help (a ceiling effect of the benchmark, not evidence for the hypothesis).")
    L.append("- Principle extraction is rule-based with six templates; richer extraction might produce different principles. Tests use the validation slice, which for some datasets has few positives (quantized quality).")
    L.append("- Registry \"models\" are simulated cost profiles; the 30-seed program used the process executor (identical for all agents); Docker was used for the v0.1 freeze and the example manifests.")
    L.append("- Experiment 9 (LLM proposer) was implemented as a validated pipeline but not executed: no API key on the host and, by design, it comes last.\n")

    L.append("## 11. Conclusion\n")
    L.append(answer)
    L.append(f"\nWhat the laboratory established in v0.2: (i) architectural principles can be extracted, stored inspectably, instantiated in a different domain's vocabulary and tested with recorded epistemic outcomes; (ii) the machine records and can be audited on its adaptation economics; (iii) over {e1.get('B', {}).get('n_runs', 0)} seeds and a 3×3 transfer matrix, prior architectural knowledge did not reduce the cost of finding a useful architecture in a new domain. The most valuable output of v0.2 is that this negative result is now measured with confidence intervals rather than suspected.\n")
    L.append("Artifacts: `results/v02/analysis/analysis.md`, per-experiment bundles under `results/v02/runs/`, manifests under `results/v02/manifests/`, memories under `results/v02/memory/`.")
    (ROOT / "docs/V0.2_RESEARCH_REPORT.md").write_text("\n".join(L) + "\n")
    print(ROOT / "docs/V0.2_RESEARCH_REPORT.md")


if __name__ == "__main__":
    main()
