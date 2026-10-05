# ARCHETYPE — pre-registration

Written and committed **before** the evaluation run on the registered seeds. The machine-readable
companion is `archetype/reports/registration.json` (commit, seeds, configuration hash, thresholds and
content hashes of every code file that defines environments, learner, baselines and analysis).

After this commit nothing below may change: no threshold, metric, learner rule, environment constant,
family definition, baseline, or budget. A defect that invalidates measurements may be fixed only in the
open: the fix, the reason and the affected jobs are recorded in the final report, the affected jobs are
re-run from scratch, and the registration hash mismatch is reported.

## 1. Hypothesis

**H.** A sufficiently general computational system can discover transferable relationships between
structural properties of an environment and the computational organization required to perform well in
it. Concretely, a frozen learner should (a) predict in an unseen environment, from observations alone,
which architectural transformations will help; (b) keep doing so when vocabulary, representation,
scales and primitives change; (c) reconstruct a suitable architecture from local primitives with fewer
evaluations than cold systems; (d) refuse transfer when a surface look-alike has a different latent
structure; (e) change its architectural preference in the right direction when exactly one latent
property is changed.

**H0 (what the experiment tries to establish instead).** Everything ARCHETYPE achieves is matched by
task memory, architecture copying, surface similarity, unconditional principles, or ordinary
architecture search under the same budget.

## 2. What is fixed

- **Worlds.** 10 training families, 5 isomorphic + 5 compositional hold-out transfer families, 10
  false-analogy families (`archetype/latent_structure/families.py`); 3 surface realizations each, the
  third fully token-scrambled; one genome per (family, seed).
- **Budgets.** Training exploration 60 evaluations per environment (shared by all agents); ARCHETYPE
  counterfactual experiments: 3 source environments x 15 knobs x 2 directions x 22 evaluations = 1980
  evaluations per seed (reported as training cost); phase 1: 40 evaluations; phase 2: 20.
- **Agents.** B0 fixed, B1 adaptive workflow, B2 search in two variants (`search`: random restarts +
  mutation; `search_screen`: one-factor screening, compose, local search), B3 task memory, B4
  architecture memory, B5 principle memory (unconditional), B6 always adapt, B7 never adapt, B8 random
  transfer, B9 surface similarity, B10 latent oracle (reads the genome; analysis only, excluded from
  every criterion), B11 ARCHETYPE, and eight single-component ablations of ARCHETYPE ("without
  structural memory" is the cold system; "without regime detection", "without contraindications",
  "without transfer confidence", "without counterfactual testing", "without adaptation economics",
  "without structural analogy", "without architecture reconstruction"). All share one configuration
  space and one local-search routine.
- **Seeds.** Development: 0-9 (used to build and calibrate; never evidence). Registered: 1000-1029.
  Replication (only if triggered): 2000-2029.

## 3. Metrics (definitions used by the criteria)

- **Reference optimum**: exhaustive noise-free maximum over the shared configuration space of the
  environment. **Gap closure** of an architecture: (u - u_single_pass) / (u_opt - u_single_pass).
- **Useful**: gap closure >= 0.8. **E2U**: evaluations spent in phase 1 before the agent's declared
  incumbent is first useful; censored at budget + 1 = 41.
- **Useful-evaluation reduction** vs X: E2U(X) - E2U(ARCHETYPE), seed means, paired by seed.
- **Truth of "transformation t helps in environment e"**: noise-free effect of t on the single-pass
  base > 0.02.
- **Transfer prediction**: an agent's zero-evaluation score per (environment, transformation), AUROC
  against the truth; *pooled* over all pairs and *within-transformation* (mean of per-transformation
  AUROCs, which removes base rates between transformations).
- **Trap**: a transformation with noise-free effect > 0.02 in the look-alike training environment and
  < -0.005 in the false-analogy environment. **False transfer**: a trap is present in the final phase-1
  architecture and removing it would raise noise-free utility by more than 0.01.
- **Interventional pair**: two environments on one surface with one latent property at 0.1 and 0.9.
  Material for t when the noise-free effect of t changes by >= 0.03. *Prediction accuracy*: the
  zero-evaluation score for t moves (by >= 0.01) in the true direction. *Choice accuracy*: t enters or
  leaves the final architecture exactly as it enters or leaves the noise-free optimum.
- **MEMORIZED TRANSFER**: role-level distance of the final architecture to every architecture observed
  in training (exploration and counterfactual experiments, at role level) < 0.10.
  **STRUCTURAL RECONSTRUCTION EVENT**: distance >= 0.10, every accepted principle's transformation is
  present and truly helps, and the architecture is useful.
- Statistics: `experiments.analysis.describe / paired` (2000 bootstrap resamples, 95% CI). "Significant"
  means the CI excludes zero. Unit of analysis: seed.

## 4. Kill criteria

| id | fails when | registered pass rule |
|---|---|---|
| K1 | structural transfer prediction does not outperform surface-similarity transfer | ARCHETYPE minus B9 significant and positive for both pooled and within-transformation AUROC over all test environments, and ARCHETYPE within-transformation AUROC >= 0.65 |
| K2 | no significant useful-evaluation reduction on >= 2 unseen environments | E2U reduction significant against **both** search variants in at least 2 of the 10 transfer families |
| K3 | false-transfer rate remains high | ARCHETYPE false-transfer rate <= 0.20 and not significantly higher than `search_screen` |
| K4 | counterfactual interventions do not change architecture choice as predicted | prediction accuracy on observable-property pairs >= 0.60 with the lower CI bound above 0.5 (hidden-only pairs and choice accuracy are reported, not gated: a frozen learner cannot see a hidden-only change without evaluating) |
| K5 | no structurally reconstructed architecture provides measurable benefit | at least one transfer family with reconstruction events in >= 50% of its episodes, on >= 2 of 3 surfaces, and significant E2U reduction against both search variants in that family |
| K6 | architecture search performs equally well or better everywhere | pooled E2U reduction over transfer families significant against both search variants and at least one family won against both |
| K7 | results disappear when superficial cues are randomized | on fully scrambled surfaces only: within-transformation AUROC advantage over B9 significant and E2U reduction against `search_screen` significant |
| K8 | principle memory improves apparent transfer but hurts controlled counterfactuals | NOT (memory significantly reduces E2U in transfer AND significantly lowers gap closure on interventional environments, relative to the same agent without structural memory) |

## 5. Success conditions (all required for BREAKTHROUGH_CANDIDATE)

| id | condition | operationalization |
|---|---|---|
| S1 | predicts when transfer will be useful | K1 and pooled AUROC significantly above B5 (base rates) |
| S2 | survives changed vocabulary / representation | within-transformation AUROC advantage over B9 significant on scrambled surfaces and on hold-out families |
| S3 | better than search in >= 2 of 3 unseen transfer environments | significant E2U reduction against both search variants in >= 7 of 10 transfer families |
| S4 | >= 1 structurally reconstructed architecture | >= 1 structural reconstruction event |
| S5 | the reconstruction gives measurable benefit | K5 |
| S6 | counterfactuals move preference as predicted | K4 |
| S7 | avoids harmful false-analogy transfer | K3 |
| S8 | survives removal of superficial signals | K7 |
| S9 | survives held-out families | significant E2U reduction against both search variants in >= 3 of 5 hold-out families |
| S10 | survives 30+ seeds | 30 seeds, <= 5% missing records |

## 6. Verdict rule (implemented in `archetype/metrics/analysis.py::verdict`)

1. fewer than 30 seeds or more than 5% missing records -> **INCONCLUSIVE**
2. S1-S10 all hold -> **BREAKTHROUGH_CANDIDATE**, which automatically triggers the replication of
   section 7; if the replication does not reach the same verdict the result is reported as
   PARTIAL_SUPPORT
3. K6 fails, or K1 and K2 both fail -> **NO_DISTINCT_CAPABILITY**
4. otherwise -> **PARTIAL_SUPPORT**, and the report lists exactly which criteria passed

Ablations: if removing a component improves E2U, gap closure or the false-transfer rate with a CI
excluding zero and hurts none of them, it is recorded as evidence against that component.

## 7. Replication (spec §35)

`archetype/experiments/replicate.py`: 30 new seeds (2000-2029), 3 new surface realizations of every
family (surface indices 3-5), and one new false-analogy family (`FX0`, which breaks only one hidden
relation of its source). Runs only on a BREAKTHROUGH_CANDIDATE verdict.

## 8. Sanity experiment (run before this registration)

`python -m archetype.experiments.sanity` — 3 seeds, 3 structural families, 1 transfer, 1 false analogy,
plus learner-free checks over all families. Result stored in `archetype/reports/sanity_report.json`.
All checks passed: no latent information in learner-visible views, learner code does not import
evaluator code, encoder invariant to renaming / reordering / rescaling, scrambled surfaces carry no
theme vocabulary, equivalent organization rebuilt from a disjoint inventory, >= 1000 configurations
everywhere, false analogies harmful and isomorphic twins transferable, no universal architecture,
interventions change exactly one property, hidden-only interventions leave the whole view identical,
complete provenance, bit-identical replay, consistent oracle bound, search neither trivial nor hopeless.

## 9. Development log (everything changed after first contact with data, and why)

All of this happened on development seeds, before registration.

1. **Fitness calibration (learner-free).** The first fitness function had one organization winning
   almost everywhere and floors at zero utility; false analogies were not harmful. Error sources were
   made quadratic, every transformation was given an intrinsic cost outside its niche, the utility map
   was made smooth, and coefficients were set so that the landscape diagnostics pass (several
   organizations optimal, no universal architecture, harmful false analogies, transferable twins).
2. **Noise and budget calibration, judged on search baselines only.** With the first noise level plain
   search failed to become useful in about half of the episodes even with 30 evaluations. Evaluation
   noise and failure probability were reduced and the phase-1 budget set to 40.
3. **Local search made noise-robust for every agent** (improvements are confirmed by a second
   evaluation; configurations are compared by their mean).
4. **Reference optimum made exhaustive** (coordinate ascent was sometimes beaten by agents).
5. **Relation model.** One-feature stump committees could not express conjunctions; replaced by depth-2
   trees with bagging. Feature subsampling in the bag was removed after a unit test on synthetic data
   showed it diluted a correctly learned conjunction.
6. **Unobservable-condition flag** changed from "any flip" to "at least 2 flips and >= 15% of
   interventions without observable change on a supporting source", because single flips were noise.
7. **Tested transformations are replicated once when the measured effect is within 0.03 of the
   acceptance threshold.** Economics patience set to 8.
8. **Architecture limits** raised (depth 9, 96 nodes) after a unit test showed some composed
   configurations were rejected as too deep.
9. **Sanity-check defects fixed** (a resource field named like a role; a vocabulary check that read
   field names).

Observed on development seeds before registration, stated here so the reader knows what the author
expected: ARCHETYPE's zero-evaluation scores predicted transformation usefulness clearly better than
surface similarity, but its evaluations-to-useful were **not** clearly better than `search_screen` or
architecture memory. No component was tuned further to change that.

## 10. Limitations known before the run

1. The structure-to-organization relationship is **planted** in a simulated fitness function; generator
   and learner have one author. A positive result is about recovering and transferring a planted
   relation under controls, not about natural environments.
2. Architectures are scored by simulation; they do not process the observation data.
3. Primitives expose interface signatures (the lab's one fixed shared language), so recognizing what a
   primitive can do is not part of what is tested.
4. Evaluations run in-process (`executor: inprocess-simulator`), not in the Docker/process sandbox.
5. Observation channel kinds and their inner field names are a fixed sensor API; everything inside is
   randomized.
6. All agents search the same hand-designed configuration space; trees outside it are valid but unused.
7. False analogies differ from their source only in unobservable properties, so no frozen learner can
   detect them without evaluating; what is measured is whether testing prevents harmful adoption.
8. ARCHETYPE spends 1980 extra training evaluations per seed on counterfactual experiments that the
   baselines do not get; the "without counterfactual testing" ablation shows what that buys.
9. Interventional pairs reuse transfer families on their first surface.
