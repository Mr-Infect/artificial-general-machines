#!/usr/bin/env python3
"""Generate results/v03/report.md (and docs/V0.3_RESEARCH_REPORT.md) from results/v03/analysis/analysis.json.
Every number is read from the analysis; the verdict is the pre-registered rule's output."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from experiments.analysis import ci_excludes_zero  # noqa: E402
from experiments.analysis_v03 import Y_SET, Z_SET  # noqa: E402


def _fd(v):
    return "n/a" if v is None else f"{v:.2f}"


def p(x):
    if not x or x.get("delta_mean") is None:
        return f"no pairs (both missing {x.get('n_both_missing', '?') if x else '?'})"
    return (f"{x['delta_mean']:+.3g} [95% CI {x['ci95'][0]:+.3g}, {x['ci95'][1]:+.3g}]{' *' if ci_excludes_zero(x) else ''}, d = {_fd(x.get('effect_size_d'))}, "
            f"win/loss/tie {x['negative']}/{x['positive']}/{x['zero']} of {x['n_pairs']} pairs (lower is better), missing {x['n_both_missing']}")


def d(x):
    return "—" if not x or x.get("mean") is None else f"{x['mean']:.3g} (median {x['median']:.3g}, sd {x['sd']:.2g}, 95% CI [{x['ci95'][0]:.3g}, {x['ci95'][1]:.3g}], n = {x['n']})"


def main():
    res = json.loads((ROOT / "results/v03/analysis/analysis.json").read_text())
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    K = {k["id"]: k for k in res["kill_criteria"]}
    envs = res["environments"]
    Y = {n: envs[f"v03_Y_{n}"] for n in Y_SET if f"v03_Y_{n}" in envs}
    Z = {n: envs[f"v03_Z_{n}"] for n in Z_SET if f"v03_Z_{n}" in envs}
    L = [f"# AGM v0.3 Research Report — verdict: **{res['verdict']}**\n"]
    L.append("## 1. Research question\n\nCan AGM recognize that its current computational organization has become inappropriate, infer what kind of organization is now required, decide whether changing itself is worth the cost, construct and evaluate a different architecture, and transfer that structural understanding to an unfamiliar problem without simply reusing a remembered architecture?\n")
    L.append("## 2. Hypothesis\n\nSee `docs/v0.3_design.md` (registered at commit `" + str((res.get('registration') or {}).get('registration_commit', '?'))[:12] + "`). The hypothesis is falsified if the pre-registered kill criteria fail.\n")
    L.append("## 3. Experimental design\n\nPer seed: three training runs (network, scientific, planning; training regime library; AGM v0.3 in exploration mode writes one memory file), then six transfer runs (three blind-transfer twins Y, three false-analogy environments Z) under held-out regime combinations with fourteen agents on identical data, budgets (6 candidate evaluations per step), scoring and sandbox. Comparisons are paired by seed. Candidate evaluations use the most recent labelled batch so all agents see the current regime.\n")
    L.append("## 4. Environment definitions\n\n" + "\n".join(f"- {n}: {'twin of ' + {'telemetry_grid': 'network', 'lab_assay': 'scientific', 'allocation': 'planning'}[n] + ' (renamed features/components, permuted order, affine-transformed ranges; same hidden structure)' if n in Y_SET else ''}" for n in Y) +
             "\n" + "\n".join(f"- {n}: same vocabulary as {n.split('_')[0]}, different structure ({ {'network_rules': 'range/protocol violations only', 'scientific_drift': 'slow in-range drifts only', 'planning_stable': 'exact capacity, slack deadlines'}[n] })" for n in Z) + "\n")
    L.append("## 5. Regime definitions\n\nTraining: calm, turbulent, starved. Held-out: H1, H2, H3 (parameters in `environments/regimes.py`). Three regimes per run in seeded random order with seeded transition steps; constraint changes are observable through telemetry, data regimes are not labelled. Target per regime = top-decile validation quality of a 48-point lab sample of the architecture space under that regime's limits.\n")
    L.append("## 6. Baselines\n\nfixed, adaptive (role-based presets, degradation-triggered), search (auto space over the available primitives), task_memory (AGM v0.2, same-domain patterns), architecture_memory (AGM v0.2, cross-domain patterns), always_adapt, never_adapt, agm_cold.\n")
    L.append("## 7. Ablations\n\nagm_full, agm_no_principle, agm_no_archmem, agm_no_negative, agm_no_economics (always adapt with full memory), agm_no_regime.\n")
    L.append("## 8. Pre-registered criteria\n\n| id | criterion | result | evidence |\n|---|---|---|---|")
    for k in res["kill_criteria"]:
        L.append(f"| {k['id']} | {k['name']} | **{'PASS' if k['pass'] else 'FAIL'}** | {k['evidence']} |")
    def env_block(title, E, keys):
        L.append(f"\n## {title}\n")
        for n, v in E.items():
            L.append(f"### {n} (n = {v['n_runs']}; transfer successful {v['transfer']['successful_rate']}, harmful {v['transfer']['harmful_rate']}, tie {v['transfer']['tie_rate']})\n")
            for key in keys:
                pm = v["paired"].get(key)
                if pm:
                    L.append(f"- {key}: evaluations-to-useful {p(pm['evaluations_to_useful'])}; adaptation cost {p(pm['adaptation_cost'])}; time-to-regime-response {p(pm['time_to_regime_response'])}; quality {p(pm['quality_mean'])}; failures {p(pm['failure_rate'])}; memory {p(pm['max_memory_mb'])}; cpu {p(pm['cpu_time_s'])}")
    L.append("\n## 9. Regime-detection results\n")
    for n, v in envs.items():
        a = v["agents"].get("agm_full", {})
        L.append(f"- {n}: detection rate {d(a.get('detection_rate'))}; false-alarm rate {d(a.get('false_alarm_rate'))}; agm_no_regime detection rate {d(v['agents'].get('agm_no_regime', {}).get('detection_rate'))} (constraint changes only)")
    L.append(f"\nK1: {K['K1']['evidence']}\n")
    L.append("## 10. Adaptation results\n")
    for n, v in envs.items():
        a = v["agents"].get("agm_full", {})
        L.append(f"- {n}: time-to-regime-response {d(a.get('time_to_regime_response'))}; structural switches per run {d(a.get('structural_switches'))}; segments never reaching target {d(a.get('segments_unmet'))}; missed adaptations {d(a.get('missed_adaptations'))}")
    L.append(f"\nK2: {K['K2']['evidence']}")
    env_block("11. Blind-transfer results (Y)", Y, ["agm_full-agm_cold", "agm_full-search", "agm_full-architecture_memory", "agm_full-task_memory"])
    L.append(f"\nK4: {K['K4']['evidence']}\nK6: {K['K6']['evidence']}")
    env_block("12. False-analogy results (Z)", Z, ["agm_full-agm_cold", "agm_full-search", "agm_full-architecture_memory"])
    L.append(f"\nK5: {K['K5']['evidence']}")
    L.append("\n## 13. Negative-knowledge results\n")
    for n, v in envs.items():
        a, b = v["agents"].get("agm_full", {}), v["agents"].get("agm_no_negative", {})
        pm = v["paired"].get("agm_no_negative-agm_full", {})
        L.append(f"- {n}: principle decisions (agm_full) {a.get('decision_counts')}; principle tests {a.get('principle_tests')}; no_negative − full: evaluations-to-useful {p(pm.get('evaluations_to_useful'))}, quality {p(pm.get('quality_mean'))}")
    L.append("\n## 14. Adaptation-economics results\n")
    for n, v in envs.items():
        a = v["agents"].get("agm_full", {})
        L.append(f"- {n}: DO_NOT_ADAPT share {d(a.get('do_not_adapt_share'))}, accuracy {d(a.get('do_not_adapt_accuracy'))}, unnecessary-adaptation rate {d(a.get('unnecessary_adaptation_rate'))}; always_adapt − cold: evaluations {p(v['paired'].get('always_adapt-agm_cold', {}).get('architecture_evaluations'))}, quality {p(v['paired'].get('always_adapt-agm_cold', {}).get('quality_mean'))}; never_adapt − cold: quality {p(v['paired'].get('never_adapt-agm_cold', {}).get('quality_mean'))}, failures {p(v['paired'].get('never_adapt-agm_cold', {}).get('failure_rate'))}; no_economics − full: evaluations {p(v['paired'].get('agm_no_economics-agm_full', {}).get('architecture_evaluations'))}")
    L.append(f"\nK3: {K['K3']['evidence']}")
    L.append("\n## 15. Architecture novelty analysis\n\nGENERATED → STRUCTURALLY NOVEL → VALID → USEFUL → APPROPRIATE TO REGIME → TRANSFERABLE. Structural distance uses `architecture/distance.py` (parameter-only changes have distance 0).\n")
    for n, v in envs.items():
        a = v["agents"].get("agm_full", {})
        L.append(f"- {n}: final structural distance to initial {d(a.get('final_distance_to_initial'))}; structural switches {d(a.get('structural_switches'))}; distinct architectures per run (agm_full vs search) {d(v['agents']['agm_full'].get('final_distance_to_initial'))} / {d(v['agents'].get('search', {}).get('final_distance_to_initial'))}")
    L.append("\nA high distance alone is not counted as discovery: the 'useful' and 'appropriate' stages are the evaluations-to-useful and regime-response measurements above.\n")
    L.append("## 16. Statistical analysis\n\nPaired deltas over seeds with bootstrap 95% CIs, Cohen's d on paired differences, win/loss/tie counts, and missing-result counts are reported for every comparison (full tables in `results/v03/analysis/analysis.md`; plots in `results/v03/plots/`).\n")
    L.append("## 17. Failure analysis\n")
    for n, v in envs.items():
        L.append(f"- {n}: failure rate per agent " + ", ".join(f"{a} {v['agents'][a]['failure_rate']['mean']:.2f}" for a in v["agents"] if v["agents"][a]["failure_rate"]["mean"] is not None))
    L.append(f"- missing transfer runs: {res['missing_fraction']:.1%}\n")
    L.append("## 18. Alternative explanations\n\n- Ceiling effects: where the cheapest valid architecture already reaches the regime target, no prior can reduce evaluations-to-useful. The per-environment cold values above show where this holds.\n- Role labels are declared by the registry; a twin domain shares them. Blind transfer therefore tests transfer through structural roles and conditions, not through raw component names, but the roles themselves are lab-provided types.\n- Rule-based extraction has six positive templates and one negative template; the space of learnable principles is bounded by them.\n- Regime detection partly relies on observable constraint changes (memory, cpu, verification cost), which are legitimately observable but easier than inferring data regimes; the no-regime ablation isolates the observation-based part.\n- Simulated model costs; process executor for the whole program (identical for all agents).\n")
    L.append(f"## 19. Reproducibility information\n\n- code commit(s) {res['git_commits']} (report generated at `{commit[:12]}`); registration {res.get('registration')}\n- manifests `results/v03/manifests/`, per-run bundles `results/v03/runs/<id>/` (raw_events.jsonl, hidden_truth.json, provenance.json), memories `results/v03/memory/`, databases `results/v03/db/`\n- rerun: `python3 scripts/run_v03_experiments.py --seeds 30 --workers 4 --executor process` then `python3 -m experiments.analysis_v03 && python3 scripts/write_v03_report.py`\n")
    L.append(f"## 20. Final verdict\n\n**{res['verdict']}**\n")
    passed = [k["id"] for k in res["kill_criteria"] if k["pass"]]; failed = [k["id"] for k in res["kill_criteria"] if not k["pass"]]
    L.append(f"Passed: {passed or 'none'}. Failed: {failed or 'none'}.")
    if res["verdict"] in ("FAIL", "INCONCLUSIVE", "PARTIAL SUPPORT"):
        parts = {"K1": "regime detection", "K2": "architectural response", "K3": "economic adaptation", "K4": "blind structural transfer", "K5": "negative-transfer avoidance", "K6": "baseline separation", "K7": "generalization"}
        L.append("\nWhich part failed: " + ", ".join(parts[k] for k in failed) + ".")
        if "K4" in failed or "K6" in failed:
            L.append("On the transfer question the evidence does not separate AGM from architecture search + memory + heuristics: any adaptation it performs is reproduced by the search baseline and/or by architecture memory alone.")
        if "K5" in failed:
            L.append("AGM applied prior knowledge where structural conditions made it inappropriate (false-analogy environments), i.e. it did not distinguish useful from misleading analogy.")
        if all(k in passed for k in ("K1", "K2", "K3")):
            L.append("Regime detection, architectural response and economic adaptation are demonstrated, but these do not require transferable structural knowledge.")
    else:
        L.append("\nThe measurable capability not explained by search + memory + mutation + heuristics is the reduction in evaluations-to-useful in blind-transfer environments that neither the search baseline nor architecture memory achieves (K6), while false-analogy environments show no harm (K5).")
    text = "\n".join(L) + "\n"
    (ROOT / "results/v03/report.md").write_text(text)
    (ROOT / "docs/V0.3_RESEARCH_REPORT.md").write_text(text)
    print(ROOT / "results/v03/report.md")


if __name__ == "__main__":
    main()
