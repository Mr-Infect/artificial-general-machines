# ARCHETYPE final report — verdict: **NO_DISTINCT_CAPABILITY**

*Learning the relationship between environment structure and computational organization.* A separate experimental phase on the AGM laboratory. The AGM hypothesis (v0.1-v0.3) concluded with verdict FAIL; nothing here revises that.

## 1. Executive summary

- Run: 30 seeds (1000-1029), 21 agents, missing records 0.0%. This is the registered evaluation run.
- Registered verdict rule output: **NO_DISTINCT_CAPABILITY**.
- Kill criteria passed: K1, K3, K8. Failed: K2, K4, K5, K6, K7.
- Success conditions holding: S1, S2, S4, S7, S10. Not holding: S3, S5, S6, S8, S9.
- Final question: **NO.**
- **Scope of any claim.** The structure-to-organization relationship in this laboratory is planted by the experimenter in a hidden, simulated fitness function, and the generator and the learner have the same author. Results say whether a simple interpretable learner recovers and transfers a planted relationship under the controls below. They say nothing about whether such relationships exist in natural task environments. Architectures are scored by simulation; they do not process data.

## 2. Hypothesis

**H.** A sufficiently general computational system can discover transferable relationships between structural properties of an environment and the computational organization required to perform well in it: it experiences training environments, extracts structural relations rather than memorizing tasks, recognizes a structural correspondence in an environment with different vocabulary, representation and primitives, reconstructs an appropriate architecture there with fewer evaluations than a cold system, and rejects transfer when the correspondence is false.

Registered in `docs/archetype_registration.md` and `archetype/reports/registration.json` at commit `bc514ebee35f` (2026-10-05T19:24:40Z).

## 3. Experimental design

Per seed: (1) **training world**, 10 structural families x 3 surface realizations, one shared exploration of 60 evaluations per environment recorded identically for every agent; ARCHETYPE variants may additionally run counterfactual experiments through anonymous intervention knobs. (2) **Freeze**: each agent's learned state is hashed; the protocol aborts if it changes during evaluation. (3) **Transfer world**: 5 isomorphic families (same latent region as a training family, unseen vocabulary themes, shapes, scales and primitive inventories) and 5 compositional hold-out families (factor pairs never seen in training). (4) **False-analogy world**: 10 families that copy the vocabulary theme, shapes and all observable properties of a training family and flip its hidden-only properties. (5) **Interventional pairs**: for every transfer family and every latent property, two environments that differ in exactly that property.

Each test episode: phase 1 with 40 evaluations, then (in about half of the environments) a hidden shift of one latent property and phase 2 with 20 evaluations. After every evaluation the agent's declared incumbent is scored noise-free by the evaluator. *Useful* = the incumbent closes at least 80% of the gap between single-pass and the exhaustive noise-free optimum. **Evaluations-to-useful (E2U)** is censored at 41. The third surface of every family is fully token-scrambled. Unit of analysis: the seed. Statistics: bootstrap 95% CI and paired deltas (`experiments.analysis`). `*` marks a CI excluding zero.

## 4. Environment generator

`EnvironmentGenome`: 15 hidden properties in [0, 1]. Ten leave statistical traces in the observation channels (dependency depth, branching factor, parallelizability, observation noise, temporal correlation, state volatility, resource constraint, verification cost, delayed feedback, action reversibility); five are **hidden-only** and show only in evaluation outcomes (coupling, adversariality, information decay, uncertainty, failure cost). Families are pairs of structural factors; in training, hidden-only properties are confounded with observable ones through the factors, and false analogies break that confounding. Fitness = structural match of genome and role-level organization, minus costs, plus noise and failure events (`archetype/latent_structure/fitness.py`), never shown to agents.

| world | latent distance to nearest training genome | surface similarity to nearest training environment |
|---|---|---|
| transfer_iso | 0.085 [0.083, 0.086] | 0.375 [0.373, 0.377] |
| transfer_holdout | 0.164 [0.162, 0.166] | 0.376 [0.374, 0.378] |
| false | 0.072 [0.071, 0.074] | 0.795 [0.778, 0.810] |

In false-analogy environments the organization that was optimal in the look-alike training environment closes -0.21 [-0.26, -0.18] of the gap (isomorphic twins: 0.82 [0.78, 0.86]); 0.83 [0.81, 0.85] of false-analogy environments contain at least one *trap* (a transformation that helped in the look-alike and hurts here).

## 5. Architecture space

Composition trees over `unit | serial | parallel+merge | conditional | loop | hier`, canonicalized and hashed (`archetype/architecture/graph.py`). Each environment has its own primitives with random names; agents see interface signatures and prices only. The evaluator maps trees to abstract roles to classify the ten organizations and to measure role-level distance. Configurations per environment: 9997 [9855, 10132] (min 2808).

Organization of the noise-free optimum across test environments: ARCH_1 single-pass sequential (658), ARCH_2 planner -> executor (213), ARCH_8 hierarchical decomposition (178), ARCH_10 exploration -> exploitation controller (170), ARCH_9 redundant reasoning -> consensus (133), ARCH_7 adaptive branching (128), ARCH_6 memory retrieval -> reasoning -> verification (124), ARCH_3 planner -> parallel workers -> aggregator (113), ARCH_4 decompose -> solve -> verify (83).

## 6. Learner

Observation encoder (37 generic scale/sign/order-invariant statistics) -> relation model (per architectural transformation, a depth-2 regression tree for readable rules and 15 bagged trees for confidence) -> principles with antecedent rules, contraindications, trust, history and status -> counterfactual experiments in training (test, refine, flag unobservable conditions, retire) -> per-principle decision TRUST / TEST / REJECT / IGNORE / ABSTAIN -> architecture constructor from local primitives by signature -> refinement with an economics stop -> regime detection between phases. No neural network, no language model.

| quantity (per seed) | mean [95% CI] |
|---|---|
| principles in use | 10.00 [10.00, 10.00] |
| principles flagged as depending on an unobservable condition | 1.70 [1.13, 2.33] |
| principles retired (forgotten) | 0.00 [0.00, 0.00] |
| counterfactual evaluations in training | 1954 [1942, 1966] |
| principles applied or tested per environment | 3.78 [3.59, 3.98] |
| share of tested principles contradicted by the test | 0.49 [0.47, 0.51] |
| memory precision (predicted to help and truly helps) | 0.56 [0.55, 0.58] |

Principle status counts over all seeds: {'CONDITIONAL': 279, 'SUPPORTED': 19, 'CONTRADICTED': 2}.

Principles learned in seed 1000 (verbatim from the frozen memory):

```
branch: IF (series.diff_kurtosis <= 4.33 AND prices.median_ratio <= 0.735 => +0.072) OR (series.diff_kurtosis > 4.33 => +0.085) [trust 0.89, CONDITIONAL]
decompose: IF (relations.max_layer_fraction <= 0.273 => +0.294) OR (relations.max_layer_fraction > 0.273 AND relations.longest_path > 6.5 => +0.153) [trust 0.87, CONDITIONAL]
deepen: IF (relations.longest_path > 6.5 AND series.cross_correlation > 0.586 => +0.040) [trust 0.86, CONDITIONAL] CONTRAINDICATED: NOT when relations.longest_path > 6.5 AND series.cross_correlation <= 0.586
gate: IF (ALWAYS => +0.057) [trust 0.83, CONDITIONAL]
parallelize: IF (relations.isolated_fraction > 0.468 AND series.log_length <= 5.23 => +0.033) OR (relations.isolated_fraction > 0.468 AND series.log_length > 5.23 => +0.151) [trust 0.91, CONDITIONAL] CONTRAINDICATED: UNOBSERVABLE CONDITION: must be tested before use
recall: IF no structural condition found [trust 0.91, SUPPORTED]
replicate: IF no structural condition found [trust 0.63, CONDITIONAL]
revise: IF (prices.cap_ratio > 20.5 AND series.half_shift > 1.51 => +0.088) [trust 0.71, CONDITIONAL] CONTRAINDICATED: NOT when prices.cap_ratio > 20.5 AND series.half_shift <= 1.51
tune: IF (episodes.reverted_fraction > 0.659 AND series.acf5 > 0.726 => +0.128) [trust 0.80, CONDITIONAL] CONTRAINDICATED: NOT when episodes.reverted_fraction > 0.659 AND series.acf5 <= 0.726
upgrade: IF (ALWAYS => +0.024) [trust 0.50, CONTRADICTED]
```

## 7. Baselines

**Isomorphic transfer families** (phase 1; mean over seeds [95% CI])

| agent | E2U | never useful | final gap closure | evaluations used | failure rate | harmful element in final | novelty |
|---|---|---|---|---|---|---|---|
| B0 fixed | 40.3 [39.4, 41.0] | 0.98 [0.96, 1.00] | 0.06 [0.03, 0.09] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.38 [0.36, 0.40] | 0.000 [0.000, 0.000] |
| B1 adaptive workflow | 27.7 [27.1, 28.5] | 0.63 [0.61, 0.65] | 0.45 [0.43, 0.47] | 5.0 [5.0, 5.0] | 0.014 [0.009, 0.019] | 0.06 [0.04, 0.08] | 0.004 [0.002, 0.006] |
| B2 search (mutation) | 25.5 [23.9, 27.2] | 0.32 [0.27, 0.38] | 0.78 [0.75, 0.81] | 40.0 [40.0, 40.0] | 0.115 [0.110, 0.121] | 0.28 [0.23, 0.32] | 0.013 [0.010, 0.017] |
| B2 search (screening) | 20.1 [19.4, 20.9] | 0.17 [0.14, 0.20] | 0.87 [0.85, 0.89] | 40.0 [40.0, 40.0] | 0.058 [0.054, 0.063] | 0.19 [0.16, 0.22] | 0.008 [0.005, 0.011] |
| B3 task memory | 25.1 [23.5, 26.5] | 0.31 [0.27, 0.36] | 0.80 [0.78, 0.82] | 40.0 [40.0, 40.0] | 0.120 [0.114, 0.126] | 0.27 [0.24, 0.31] | 0.013 [0.010, 0.015] |
| B4 architecture memory | 15.3 [13.9, 16.5] | 0.19 [0.16, 0.23] | 0.82 [0.78, 0.86] | 40.0 [40.0, 40.0] | 0.129 [0.124, 0.134] | 0.22 [0.18, 0.26] | 0.007 [0.005, 0.010] |
| B5 principle memory | 20.0 [18.9, 21.2] | 0.20 [0.16, 0.24] | 0.85 [0.83, 0.87] | 40.0 [40.0, 40.0] | 0.121 [0.115, 0.129] | 0.22 [0.18, 0.27] | 0.007 [0.005, 0.011] |
| B6 always adapt | 26.0 [24.5, 27.6] | 0.35 [0.31, 0.40] | 0.78 [0.76, 0.80] | 40.0 [40.0, 40.0] | 0.124 [0.119, 0.129] | 0.28 [0.24, 0.32] | 0.012 [0.009, 0.015] |
| B7 never adapt | 34.5 [33.4, 35.8] | 0.84 [0.82, 0.87] | 0.03 [-0.02, 0.08] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.69 [0.63, 0.75] | 0.000 [0.000, 0.000] |
| B8 random transfer | 24.1 [22.6, 25.7] | 0.32 [0.27, 0.36] | 0.78 [0.76, 0.81] | 40.0 [40.0, 40.0] | 0.124 [0.119, 0.129] | 0.28 [0.24, 0.32] | 0.012 [0.009, 0.015] |
| B9 surface similarity | 25.5 [24.3, 26.7] | 0.34 [0.31, 0.38] | 0.76 [0.74, 0.78] | 40.0 [40.0, 40.0] | 0.126 [0.121, 0.132] | 0.29 [0.24, 0.33] | 0.012 [0.010, 0.016] |
| B10 latent oracle (analysis only) | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.00 [0.00, 0.00] | 0.008 [0.005, 0.011] |
| B11 ARCHETYPE | 22.6 [21.3, 23.9] | 0.38 [0.34, 0.42] | 0.76 [0.73, 0.78] | 20.9 [20.3, 21.6] | 0.045 [0.040, 0.049] | 0.15 [0.13, 0.18] | 0.008 [0.006, 0.011] |
| archetype_no_structural_memory | 26.7 [25.0, 28.1] | 0.53 [0.48, 0.58] | 0.67 [0.64, 0.70] | 19.1 [18.5, 19.7] | 0.037 [0.032, 0.043] | 0.24 [0.21, 0.28] | 0.010 [0.008, 0.012] |
| archetype_no_contraindications | 24.0 [23.0, 25.0] | 0.30 [0.26, 0.34] | 0.82 [0.79, 0.84] | 26.9 [26.4, 27.5] | 0.037 [0.034, 0.041] | 0.21 [0.18, 0.24] | 0.010 [0.007, 0.014] |
| archetype_no_transfer_confidence | 24.1 [22.2, 26.0] | 0.48 [0.44, 0.54] | 0.67 [0.64, 0.70] | 17.5 [16.9, 18.0] | 0.062 [0.054, 0.069] | 0.32 [0.28, 0.36] | 0.010 [0.008, 0.012] |
| archetype_no_counterfactual | 21.8 [20.6, 23.0] | 0.34 [0.30, 0.39] | 0.78 [0.75, 0.80] | 21.2 [20.6, 21.8] | 0.043 [0.038, 0.047] | 0.18 [0.14, 0.21] | 0.008 [0.006, 0.011] |
| archetype_no_economics | 22.7 [21.3, 23.9] | 0.20 [0.16, 0.24] | 0.85 [0.82, 0.87] | 40.0 [40.0, 40.0] | 0.056 [0.050, 0.061] | 0.21 [0.17, 0.25] | 0.009 [0.006, 0.012] |
| archetype_no_regime_detection | 22.1 [20.9, 23.4] | 0.35 [0.31, 0.39] | 0.77 [0.75, 0.80] | 21.3 [20.6, 22.0] | 0.041 [0.036, 0.047] | 0.24 [0.21, 0.27] | 0.008 [0.006, 0.010] |
| archetype_no_structural_analogy | 24.0 [22.9, 25.2] | 0.37 [0.33, 0.41] | 0.76 [0.74, 0.79] | 23.0 [22.3, 23.7] | 0.035 [0.030, 0.040] | 0.19 [0.16, 0.22] | 0.007 [0.005, 0.010] |
| archetype_no_reconstruction | 18.3 [16.3, 20.4] | 0.38 [0.33, 0.44] | 0.75 [0.71, 0.78] | 15.5 [15.0, 16.0] | 0.058 [0.051, 0.066] | 0.23 [0.18, 0.28] | 0.010 [0.008, 0.014] |

**Compositional hold-out families** (phase 1; mean over seeds [95% CI])

| agent | E2U | never useful | final gap closure | evaluations used | failure rate | harmful element in final | novelty |
|---|---|---|---|---|---|---|---|
| B0 fixed | 40.8 [40.5, 41.0] | 1.00 [0.99, 1.00] | 0.21 [0.19, 0.24] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.32 [0.27, 0.36] | 0.000 [0.000, 0.000] |
| B1 adaptive workflow | 33.5 [32.4, 34.5] | 0.79 [0.76, 0.82] | 0.44 [0.42, 0.46] | 5.0 [5.0, 5.0] | 0.010 [0.007, 0.013] | 0.10 [0.08, 0.13] | 0.001 [0.000, 0.002] |
| B2 search (mutation) | 26.7 [25.5, 27.8] | 0.36 [0.31, 0.40] | 0.80 [0.78, 0.82] | 40.0 [40.0, 40.0] | 0.118 [0.113, 0.123] | 0.30 [0.26, 0.34] | 0.018 [0.013, 0.023] |
| B2 search (screening) | 19.7 [18.9, 20.5] | 0.14 [0.11, 0.17] | 0.90 [0.89, 0.91] | 40.0 [40.0, 40.0] | 0.052 [0.047, 0.057] | 0.14 [0.12, 0.17] | 0.020 [0.016, 0.024] |
| B3 task memory | 27.1 [26.3, 27.9] | 0.38 [0.34, 0.41] | 0.81 [0.79, 0.82] | 40.0 [40.0, 40.0] | 0.116 [0.110, 0.122] | 0.31 [0.27, 0.35] | 0.017 [0.013, 0.021] |
| B4 architecture memory | 21.7 [20.3, 23.2] | 0.28 [0.24, 0.32] | 0.84 [0.82, 0.86] | 40.0 [40.0, 40.0] | 0.123 [0.117, 0.129] | 0.25 [0.20, 0.31] | 0.012 [0.008, 0.016] |
| B5 principle memory | 21.7 [20.7, 22.7] | 0.23 [0.19, 0.27] | 0.87 [0.86, 0.88] | 40.0 [40.0, 40.0] | 0.109 [0.105, 0.114] | 0.18 [0.15, 0.21] | 0.021 [0.016, 0.026] |
| B6 always adapt | 27.0 [25.8, 28.2] | 0.40 [0.37, 0.44] | 0.77 [0.75, 0.80] | 40.0 [40.0, 40.0] | 0.116 [0.110, 0.122] | 0.30 [0.26, 0.34] | 0.016 [0.012, 0.021] |
| B7 never adapt | 37.8 [36.2, 39.3] | 0.92 [0.88, 0.96] | 0.09 [0.03, 0.15] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.58 [0.52, 0.64] | 0.000 [0.000, 0.000] |
| B8 random transfer | 25.5 [24.4, 26.7] | 0.37 [0.33, 0.41] | 0.80 [0.78, 0.81] | 40.0 [40.0, 40.0] | 0.125 [0.119, 0.130] | 0.33 [0.30, 0.37] | 0.016 [0.012, 0.019] |
| B9 surface similarity | 25.3 [24.0, 26.8] | 0.33 [0.29, 0.37] | 0.82 [0.80, 0.84] | 40.0 [40.0, 40.0] | 0.128 [0.123, 0.133] | 0.31 [0.28, 0.34] | 0.020 [0.016, 0.025] |
| B10 latent oracle (analysis only) | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.00 [0.00, 0.00] | 0.020 [0.015, 0.025] |
| B11 ARCHETYPE | 21.8 [20.7, 23.1] | 0.33 [0.30, 0.38] | 0.80 [0.77, 0.82] | 21.4 [20.8, 22.1] | 0.040 [0.036, 0.045] | 0.18 [0.15, 0.21] | 0.018 [0.014, 0.021] |
| archetype_no_structural_memory | 28.8 [27.6, 30.0] | 0.60 [0.56, 0.64] | 0.62 [0.59, 0.65] | 19.1 [18.4, 19.8] | 0.038 [0.033, 0.042] | 0.32 [0.29, 0.36] | 0.014 [0.010, 0.018] |
| archetype_no_contraindications | 23.5 [22.5, 24.6] | 0.30 [0.26, 0.34] | 0.83 [0.81, 0.85] | 26.8 [26.1, 27.3] | 0.039 [0.035, 0.043] | 0.17 [0.14, 0.20] | 0.014 [0.010, 0.017] |
| archetype_no_transfer_confidence | 23.6 [22.1, 25.2] | 0.46 [0.42, 0.51] | 0.71 [0.68, 0.74] | 18.1 [17.5, 18.8] | 0.062 [0.055, 0.068] | 0.35 [0.31, 0.39] | 0.016 [0.013, 0.020] |
| archetype_no_counterfactual | 23.2 [21.9, 24.5] | 0.38 [0.33, 0.42] | 0.77 [0.75, 0.79] | 21.8 [21.1, 22.5] | 0.040 [0.035, 0.045] | 0.16 [0.13, 0.20] | 0.015 [0.011, 0.018] |
| archetype_no_economics | 22.1 [21.1, 23.0] | 0.18 [0.15, 0.22] | 0.88 [0.86, 0.89] | 40.0 [40.0, 40.0] | 0.047 [0.042, 0.053] | 0.18 [0.15, 0.21] | 0.022 [0.018, 0.026] |
| archetype_no_regime_detection | 22.8 [21.7, 23.9] | 0.37 [0.33, 0.41] | 0.78 [0.76, 0.80] | 21.7 [21.0, 22.3] | 0.042 [0.037, 0.047] | 0.19 [0.16, 0.22] | 0.015 [0.011, 0.019] |
| archetype_no_structural_analogy | 25.2 [24.0, 26.3] | 0.40 [0.35, 0.45] | 0.75 [0.72, 0.78] | 23.5 [22.7, 24.3] | 0.034 [0.029, 0.038] | 0.17 [0.13, 0.22] | 0.013 [0.009, 0.018] |
| archetype_no_reconstruction | 28.6 [27.2, 29.9] | 0.59 [0.55, 0.63] | 0.64 [0.62, 0.67] | 18.5 [17.8, 19.1] | 0.058 [0.050, 0.066] | 0.43 [0.39, 0.47] | 0.015 [0.012, 0.019] |

**False-analogy families** (phase 1; mean over seeds [95% CI])

| agent | E2U | never useful | final gap closure | evaluations used | failure rate | harmful element in final | novelty |
|---|---|---|---|---|---|---|---|
| B0 fixed | 24.6 [23.6, 25.5] | 0.60 [0.58, 0.62] | 0.39 [0.35, 0.43] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.32 [0.31, 0.34] | 0.000 [0.000, 0.000] |
| B1 adaptive workflow | 27.2 [26.2, 28.1] | 0.62 [0.59, 0.64] | 0.50 [0.48, 0.52] | 5.0 [5.0, 5.0] | 0.015 [0.012, 0.018] | 0.14 [0.11, 0.16] | 0.001 [0.000, 0.001] |
| B2 search (mutation) | 28.6 [27.8, 29.4] | 0.48 [0.45, 0.51] | 0.67 [0.65, 0.69] | 40.0 [40.0, 40.0] | 0.104 [0.100, 0.108] | 0.20 [0.17, 0.23] | 0.005 [0.004, 0.006] |
| B2 search (screening) | 23.1 [22.3, 24.0] | 0.28 [0.25, 0.30] | 0.79 [0.78, 0.81] | 40.0 [40.0, 40.0] | 0.024 [0.023, 0.026] | 0.10 [0.09, 0.12] | 0.002 [0.001, 0.003] |
| B3 task memory | 27.3 [26.4, 28.2] | 0.46 [0.43, 0.49] | 0.68 [0.66, 0.70] | 40.0 [40.0, 40.0] | 0.109 [0.106, 0.112] | 0.21 [0.18, 0.24] | 0.003 [0.002, 0.004] |
| B4 architecture memory | 27.8 [26.4, 29.2] | 0.49 [0.45, 0.53] | 0.63 [0.61, 0.66] | 40.0 [40.0, 40.0] | 0.104 [0.099, 0.108] | 0.24 [0.21, 0.26] | 0.002 [0.001, 0.003] |
| B5 principle memory | 21.9 [20.7, 23.0] | 0.33 [0.30, 0.36] | 0.78 [0.76, 0.80] | 40.0 [40.0, 40.0] | 0.091 [0.088, 0.094] | 0.11 [0.09, 0.12] | 0.001 [0.000, 0.001] |
| B6 always adapt | 28.0 [26.8, 29.2] | 0.46 [0.42, 0.50] | 0.66 [0.64, 0.69] | 40.0 [40.0, 40.0] | 0.102 [0.098, 0.105] | 0.20 [0.18, 0.22] | 0.005 [0.004, 0.007] |
| B7 never adapt | 39.4 [38.2, 40.3] | 0.96 [0.93, 0.98] | -0.32 [-0.41, -0.23] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.79 [0.73, 0.84] | 0.000 [0.000, 0.000] |
| B8 random transfer | 28.6 [27.7, 29.5] | 0.50 [0.47, 0.53] | 0.65 [0.62, 0.67] | 40.0 [40.0, 40.0] | 0.107 [0.104, 0.111] | 0.22 [0.19, 0.24] | 0.003 [0.002, 0.005] |
| B9 surface similarity | 26.9 [25.8, 28.0] | 0.45 [0.41, 0.48] | 0.67 [0.65, 0.69] | 40.0 [40.0, 40.0] | 0.107 [0.102, 0.111] | 0.21 [0.18, 0.23] | 0.003 [0.002, 0.005] |
| B10 latent oracle (analysis only) | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.0 [0.0, 0.0] | 0.000 [0.000, 0.000] | 0.00 [0.00, 0.00] | 0.000 [0.000, 0.000] |
| B11 ARCHETYPE | 24.6 [23.4, 25.8] | 0.47 [0.43, 0.51] | 0.69 [0.67, 0.72] | 18.8 [18.3, 19.2] | 0.018 [0.016, 0.021] | 0.09 [0.08, 0.11] | 0.001 [0.000, 0.001] |
| archetype_no_structural_memory | 30.1 [29.3, 31.1] | 0.66 [0.63, 0.69] | 0.48 [0.45, 0.51] | 15.9 [15.6, 16.2] | 0.023 [0.021, 0.026] | 0.20 [0.17, 0.23] | 0.004 [0.003, 0.005] |
| archetype_no_contraindications | 27.3 [26.2, 28.4] | 0.44 [0.40, 0.48] | 0.73 [0.71, 0.75] | 25.0 [24.6, 25.4] | 0.015 [0.013, 0.017] | 0.07 [0.05, 0.09] | 0.001 [0.000, 0.001] |
| archetype_no_transfer_confidence | 27.7 [26.0, 29.1] | 0.61 [0.57, 0.65] | 0.52 [0.49, 0.55] | 15.4 [15.0, 15.7] | 0.036 [0.032, 0.040] | 0.26 [0.24, 0.29] | 0.003 [0.002, 0.004] |
| archetype_no_counterfactual | 25.1 [23.7, 26.5] | 0.49 [0.44, 0.53] | 0.70 [0.66, 0.73] | 18.8 [18.4, 19.3] | 0.015 [0.013, 0.017] | 0.07 [0.05, 0.09] | 0.001 [0.000, 0.001] |
| archetype_no_economics | 25.0 [23.9, 26.1] | 0.31 [0.28, 0.35] | 0.79 [0.77, 0.81] | 40.0 [40.0, 40.0] | 0.023 [0.021, 0.025] | 0.12 [0.10, 0.15] | 0.002 [0.001, 0.003] |
| archetype_no_regime_detection | 24.3 [22.7, 25.9] | 0.47 [0.42, 0.51] | 0.72 [0.69, 0.74] | 18.7 [18.4, 19.1] | 0.018 [0.016, 0.020] | 0.09 [0.07, 0.11] | 0.001 [0.000, 0.002] |
| archetype_no_structural_analogy | 24.1 [22.8, 25.3] | 0.42 [0.39, 0.45] | 0.73 [0.71, 0.76] | 20.6 [19.7, 21.5] | 0.017 [0.016, 0.019] | 0.09 [0.07, 0.11] | 0.001 [0.001, 0.002] |
| archetype_no_reconstruction | 30.0 [28.9, 31.2] | 0.68 [0.65, 0.71] | 0.47 [0.45, 0.50] | 15.3 [14.9, 15.7] | 0.033 [0.030, 0.038] | 0.25 [0.23, 0.28] | 0.003 [0.002, 0.005] |

Secondary resource metrics of the final architecture (transfer worlds pooled by world): structural operations, cost units, latency, memory units.

| agent | operations (iso) | cost (iso) | latency (iso) | memory (iso) | adaptation cost in evaluation price units (iso) |
|---|---|---|---|---|---|
| B0 fixed | 1.0 [1.0, 1.0] | 4.7 [4.7, 4.8] | 47 [46, 48] | 11.6 [11.4, 11.7] | 0 [0, 0] |
| B1 adaptive workflow | 1.6 [1.6, 1.7] | 4.7 [4.5, 4.9] | 36 [35, 37] | 14.5 [14.2, 14.7] | 36 [36, 36] |
| B2 search (mutation) | 2.4 [2.3, 2.5] | 6.0 [5.8, 6.3] | 49 [47, 51] | 19.3 [18.6, 20.0] | 692 [673, 712] |
| B2 search (screening) | 2.3 [2.2, 2.4] | 6.3 [6.0, 6.5] | 47 [46, 49] | 19.0 [18.3, 19.7] | 378 [365, 392] |
| B3 task memory | 2.5 [2.3, 2.6] | 6.0 [5.8, 6.2] | 49 [47, 51] | 19.1 [18.5, 19.7] | 697 [680, 714] |
| B4 architecture memory | 2.4 [2.3, 2.6] | 6.6 [6.3, 6.8] | 49 [47, 51] | 20.0 [19.4, 20.5] | 724 [704, 745] |
| B5 principle memory | 2.3 [2.2, 2.4] | 6.2 [6.0, 6.4] | 47 [46, 48] | 19.2 [18.7, 19.8] | 670 [646, 696] |
| B6 always adapt | 2.4 [2.3, 2.6] | 6.0 [5.8, 6.3] | 49 [47, 51] | 19.3 [18.6, 20.1] | 699 [675, 725] |
| B7 never adapt | 1.3 [1.1, 1.4] | 4.9 [4.5, 5.3] | 41 [34, 48] | 15.8 [14.0, 17.6] | 0 [0, 0] |
| B8 random transfer | 2.5 [2.4, 2.7] | 6.2 [6.0, 6.5] | 49 [47, 51] | 19.6 [18.9, 20.3] | 742 [717, 767] |
| B9 surface similarity | 2.5 [2.3, 2.6] | 6.0 [5.7, 6.3] | 47 [45, 49] | 19.2 [18.5, 19.8] | 722 [698, 747] |
| B10 latent oracle (analysis only) | 2.4 [2.3, 2.5] | 6.3 [6.1, 6.5] | 47 [46, 48] | 20.1 [19.5, 20.7] | 0 [0, 0] |
| B11 ARCHETYPE | 2.1 [2.0, 2.3] | 5.9 [5.6, 6.2] | 43 [41, 45] | 16.7 [16.1, 17.3] | 172 [163, 180] |
| archetype_no_structural_memory | 2.0 [1.8, 2.1] | 5.4 [5.1, 5.7] | 44 [42, 47] | 16.9 [16.1, 17.7] | 153 [146, 161] |
| archetype_no_contraindications | 2.3 [2.2, 2.4] | 6.0 [5.7, 6.2] | 44 [42, 46] | 17.7 [17.0, 18.3] | 194 [188, 200] |
| archetype_no_transfer_confidence | 2.3 [2.2, 2.4] | 6.6 [6.2, 6.9] | 50 [46, 53] | 18.0 [17.4, 18.7] | 192 [178, 207] |
| archetype_no_counterfactual | 2.1 [2.0, 2.2] | 5.9 [5.6, 6.2] | 43 [41, 45] | 17.1 [16.3, 17.9] | 168 [158, 178] |
| archetype_no_economics | 2.3 [2.2, 2.4] | 6.5 [6.1, 6.8] | 49 [47, 51] | 19.4 [18.7, 20.0] | 367 [354, 381] |
| archetype_no_regime_detection | 2.2 [2.1, 2.4] | 6.1 [5.9, 6.3] | 45 [43, 46] | 17.4 [16.7, 18.0] | 172 [164, 179] |
| archetype_no_structural_analogy | 2.0 [1.8, 2.1] | 5.5 [5.2, 5.7] | 43 [41, 45] | 16.5 [15.9, 17.2] | 173 [161, 185] |
| archetype_no_reconstruction | 2.4 [2.2, 2.5] | 6.0 [5.6, 6.3] | 46 [44, 48] | 18.3 [17.5, 19.1] | 148 [137, 160] |

## 8. Transfer matrix

Useful-evaluation reduction of ARCHETYPE: comparator E2U minus ARCHETYPE E2U, paired by seed (positive = ARCHETYPE needed fewer evaluations).

| family | B2 search (mutation) | B2 search (screening) | B4 architecture memory | B5 principle memory | B9 surface similarity | archetype_no_structural_memory |
|---|---|---|---|---|---|---|
| B00 | +3.0 [-0.9, 6.9] | +2.0 [-1.8, 5.9] | -8.3 [-12.5, -3.9] * | -4.6 [-8.4, -0.9] * | +3.0 [-1.7, 7.8] | +6.1 [2.1, 10.2] * |
| B01 | +13.7 [10.8, 16.6] * | +1.0 [-0.4, 2.3] | -7.1 [-8.8, -5.6] * | +0.2 [-1.8, 2.4] | +10.7 [7.0, 14.1] * | +12.3 [9.1, 15.6] * |
| B02 | -5.1 [-9.6, -0.6] * | -0.8 [-3.8, 2.0] | -4.6 [-9.2, -0.1] * | +2.3 [-0.0, 4.7] | -1.7 [-5.9, 2.5] | -0.2 [-4.4, 3.6] |
| B03 | +7.6 [3.5, 11.6] * | -2.6 [-7.1, 1.5] | -4.1 [-9.3, 1.0] | -4.1 [-8.6, 0.3] | +8.6 [3.9, 13.3] * | +7.6 [2.5, 12.6] * |
| B04 | -5.0 [-9.4, -0.1] * | -12.2 [-15.9, -8.2] * | -12.6 [-17.8, -7.6] * | -6.9 [-10.0, -3.9] * | -6.3 [-10.1, -2.5] * | -5.5 [-9.9, -0.9] * |
| F00 | -1.9 [-5.4, 1.4] | -2.0 [-6.0, 1.9] | -3.9 [-8.2, 0.6] | -6.3 [-9.7, -2.4] * | -1.8 [-5.1, 1.6] | -2.3 [-5.3, 0.7] |
| F01 | +6.9 [2.7, 10.9] * | +0.5 [-2.8, 3.7] | -2.6 [-6.5, 1.3] | -0.8 [-4.4, 3.0] | +2.6 [-1.2, 6.3] | +6.0 [1.8, 10.0] * |
| F02 | -1.1 [-5.2, 3.1] | -0.2 [-3.3, 2.8] | +2.9 [-2.0, 7.8] | -3.2 [-6.2, -0.1] * | -0.9 [-4.3, 2.4] | +4.7 [0.9, 8.9] * |
| F03 | +8.1 [3.7, 12.5] * | -2.2 [-6.0, 1.5] | +13.8 [9.1, 18.1] * | -4.3 [-8.6, -0.3] * | +11.8 [7.3, 15.9] * | +8.9 [4.2, 13.2] * |
| F04 | +1.8 [-2.9, 6.2] | -3.1 [-7.1, 0.9] | +9.4 [5.6, 13.4] * | -4.8 [-8.3, -1.5] * | +1.1 [-3.5, 5.8] | +5.0 [0.4, 9.6] * |
| F05 | +8.7 [4.6, 12.9] * | +0.4 [-3.6, 4.5] | +8.7 [4.5, 12.8] * | -1.3 [-4.8, 2.4] | +8.0 [3.4, 12.4] * | +8.6 [4.3, 12.7] * |
| F06 | -3.3 [-7.0, 0.6] | -1.3 [-3.7, 0.9] | +1.3 [-2.8, 5.8] | -3.1 [-5.8, -0.3] * | -3.8 [-7.1, -0.4] * | +0.5 [-4.2, 5.2] |
| F07 | +8.0 [3.1, 13.1] * | -3.5 [-7.2, 0.2] | +12.5 [6.7, 17.8] * | -8.4 [-12.2, -4.8] * | +8.2 [3.3, 12.5] * | +8.7 [3.9, 13.2] * |
| F08 | +4.3 [-0.1, 8.4] | -1.6 [-5.3, 2.0] | +2.9 [-2.4, 8.1] | -2.5 [-6.9, 2.2] | +3.2 [-1.4, 8.2] | +8.4 [4.8, 11.8] * |
| F09 | +8.5 [4.1, 12.9] * | -1.5 [-5.6, 2.4] | -13.4 [-17.5, -9.7] * | +7.3 [3.7, 10.6] * | -5.2 [-9.8, -0.8] * | +7.1 [2.9, 11.0] * |
| H00 | -0.9 [-4.8, 3.3] | -1.1 [-4.6, 2.0] | -4.0 [-8.3, 0.5] | -3.8 [-7.6, 0.1] | -2.8 [-6.2, 0.5] | -0.9 [-4.4, 2.8] |
| H01 | +8.4 [4.1, 12.1] * | -3.4 [-7.1, 0.2] | +6.8 [2.4, 11.1] * | +3.9 [-0.5, 7.9] | +7.7 [3.8, 11.6] * | +11.0 [7.2, 14.5] * |
| H02 | +0.5 [-2.9, 3.8] | -2.3 [-5.2, 0.4] | -0.1 [-4.1, 3.8] | +1.1 [-1.8, 4.0] | -0.9 [-4.2, 2.4] | +1.8 [-1.4, 5.1] |
| H03 | +18.2 [15.5, 21.0] * | +5.0 [3.8, 6.1] * | +9.5 [5.1, 14.2] * | -0.1 [-1.1, 0.8] | +18.6 [16.0, 21.3] * | +23.5 [20.5, 26.5] * |
| H04 | -2.1 [-7.5, 3.2] | -8.8 [-12.7, -5.0] * | -12.9 [-17.8, -8.0] * | -1.5 [-5.9, 2.6] | -5.1 [-10.2, -0.0] * | -0.5 [-5.1, 3.9] |

| pooled | B2 search (mutation) | B2 search (screening) | B4 architecture memory | B5 principle memory | B9 surface similarity | archetype_no_structural_memory |
|---|---|---|---|---|---|---|
| transfer | +3.8 [2.7, 5.1] * | -2.3 [-3.2, -1.5] * | -3.8 [-4.8, -2.7] * | -1.4 [-2.4, -0.4] * | +3.2 [1.8, 4.5] * | +5.5 [4.5, 6.6] * |
| transfer_iso | +2.8 [0.7, 5.1] * | -2.5 [-3.8, -1.2] * | -7.4 [-9.1, -5.7] * | -2.6 [-4.1, -1.1] * | +2.8 [1.0, 4.8] * | +4.1 [1.9, 6.1] * |
| transfer_holdout | +4.8 [3.5, 6.1] * | -2.1 [-3.6, -0.7] * | -0.1 [-2.1, 1.8] | -0.1 [-1.7, 1.3] | +3.5 [1.6, 5.4] * | +7.0 [5.8, 8.2] * |
| transfer_scrambled | +2.2 [0.6, 4.0] * | -2.3 [-3.9, -0.6] * | -4.0 [-5.9, -2.0] * | -2.7 [-4.4, -1.0] * | +2.8 [0.8, 4.9] * | +4.8 [2.8, 7.0] * |
| false | +4.0 [2.7, 5.3] * | -1.4 [-2.7, -0.4] * | +3.2 [1.4, 5.0] * | -2.7 [-4.1, -1.5] * | +2.3 [0.6, 4.1] * | +5.6 [4.3, 6.7] * |

Final quality (gap closure) of ARCHETYPE minus comparator:

| scope | B2 search (mutation) | B2 search (screening) | B4 architecture memory | B5 principle memory | B9 surface similarity | archetype_no_structural_memory |
|---|---|---|---|---|---|---|
| quality_transfer | -0.013 [-0.032, 0.007] | -0.106 [-0.122, -0.091] * | -0.053 [-0.074, -0.032] * | -0.081 [-0.098, -0.065] * | -0.015 [-0.032, 0.001] | +0.133 [0.111, 0.154] * |
| quality_false | +0.023 [-0.006, 0.052] | -0.102 [-0.129, -0.074] * | +0.059 [0.021, 0.098] * | -0.087 [-0.114, -0.061] * | +0.025 [-0.014, 0.066] | +0.211 [0.184, 0.239] * |

**Predicting when a transformation will help** (zero evaluations; AUROC against the noise-free effect; *within* = averaged per transformation, which removes base rates):

| agent | pooled AUROC (all) | within AUROC (all) | within (iso) | within (hold-out) | within (false) | within (scrambled) | AUPRC (all) |
|---|---|---|---|---|---|---|---|
| B5 principle memory | 0.744 [0.736, 0.752] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.547 [0.528, 0.565] |
| B9 surface similarity | 0.567 [0.557, 0.576] | 0.518 [0.509, 0.526] | 0.493 [0.477, 0.508] | 0.503 [0.489, 0.517] | 0.589 [0.577, 0.601] | 0.508 [0.496, 0.520] | 0.347 [0.335, 0.360] |
| B11 ARCHETYPE | 0.803 [0.795, 0.811] | 0.740 [0.731, 0.750] | 0.800 [0.788, 0.812] | 0.747 [0.722, 0.772] | 0.715 [0.701, 0.729] | 0.742 [0.731, 0.753] | 0.557 [0.539, 0.577] |
| archetype_no_contraindications | 0.684 [0.666, 0.703] | 0.627 [0.611, 0.643] | 0.662 [0.642, 0.683] | 0.609 [0.582, 0.638] | 0.626 [0.607, 0.646] | 0.626 [0.608, 0.643] | 0.497 [0.473, 0.522] |
| archetype_no_transfer_confidence | 0.804 [0.797, 0.811] | 0.742 [0.730, 0.753] | 0.796 [0.779, 0.814] | 0.757 [0.733, 0.781] | 0.708 [0.689, 0.725] | 0.739 [0.724, 0.754] | 0.562 [0.544, 0.581] |
| archetype_no_counterfactual | 0.806 [0.797, 0.815] | 0.743 [0.733, 0.753] | 0.800 [0.782, 0.819] | 0.734 [0.710, 0.757] | 0.731 [0.720, 0.742] | 0.741 [0.727, 0.755] | 0.573 [0.556, 0.592] |
| archetype_no_economics | 0.803 [0.795, 0.812] | 0.740 [0.725, 0.754] | 0.802 [0.784, 0.820] | 0.751 [0.725, 0.773] | 0.712 [0.692, 0.731] | 0.735 [0.719, 0.750] | 0.558 [0.542, 0.576] |
| archetype_no_regime_detection | 0.804 [0.796, 0.812] | 0.741 [0.727, 0.754] | 0.798 [0.784, 0.813] | 0.758 [0.733, 0.782] | 0.699 [0.679, 0.718] | 0.740 [0.723, 0.755] | 0.558 [0.540, 0.578] |
| archetype_no_structural_analogy | 0.730 [0.723, 0.737] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.500 [0.500, 0.500] | 0.536 [0.520, 0.550] |
| archetype_no_reconstruction | 0.803 [0.795, 0.810] | 0.742 [0.731, 0.753] | 0.802 [0.788, 0.817] | 0.749 [0.722, 0.773] | 0.709 [0.694, 0.724] | 0.743 [0.731, 0.756] | 0.562 [0.541, 0.581] |

ARCHETYPE confidence calibration: ECE 0.089, Brier 0.164 over 18000 (environment, transformation) pairs. Per transformation AUROC: decompose 0.69, deepen 0.92, parallelize 0.82, replicate 0.72, gate 0.75, revise 0.80, recall 0.48, branch 0.69, tune 0.90, upgrade 0.63.

**Environment-level structural analogy** (is the look-alike training environment's optimum useful here? isomorphic twins vs false analogies; AUROC): ARCHETYPE zero-evaluation score similarity 0.415 [0.380, 0.448], surface similarity 0.160 [0.127, 0.193], latent distance (oracle) 0.517 [0.482, 0.555]. False analogies differ from their source only in unobservable properties, so a zero-evaluation score cannot separate them; separation has to come from testing (section 11).

**Decoupling control.** With observations generated from a different family's structure than the one driving fitness, ARCHETYPE's within-transformation AUROC is 0.594 [0.578, 0.610] against 0.740 [0.731, 0.750] with real observations (difference +0.146 [0.132, 0.159] *).

**Structural transfer success** (transfer worlds): architecture built from accepted principles is useful in 0.21 [0.19, 0.24] of environments; built from frozen knowledge alone with zero evaluations: 0.11 [0.09, 0.14]; proposal has the same organization class as the optimum: 0.45 [0.43, 0.48]; missed-transfer rate (truly useful transformation not adopted): 0.38 [0.36, 0.41].

Decisions over all test environments: per principle {'ABSTAIN': 4501, 'TEST/ACCEPTED': 3188, 'REJECT': 1255, 'IGNORE': 5434, 'TEST/REJECTED': 3119, 'TRUST': 503}; per environment {'MODIFY': 1232, 'REUSE': 401, 'ABSTAIN': 163, 'BUILD_NEW': 4}.

**Abstention.** Coverage 0.750; risk when the learner decided 0.274; risk had it been forced to decide on the abstained cases 0.142; risk at full coverage 0.241. Risk-coverage curve (most confident first): 20%: 0.062, 40%: 0.102, 60%: 0.135, 80%: 0.187, 100%: 0.241.

## 9. Counterfactual results

Interventional pairs: same surface, exactly one latent property set low (0.1) vs high (0.9). A pair is *material* for a transformation when its noise-free effect changes by at least 0.03 (532 [524, 540] material pairs per seed). *Prediction*: the zero-evaluation score moves in the true direction. *Choice*: the transformation enters or leaves the final architecture exactly as it enters or leaves the noise-free optimum.

| agent | prediction, observable properties | prediction, hidden-only properties | choice, observable | choice, hidden-only | gap closure on interventional environments |
|---|---|---|---|---|---|
| B11 ARCHETYPE | 0.42 [0.41, 0.44] | 0.00 [0.00, 0.00] | 0.42 [0.40, 0.45] | 0.42 [0.39, 0.45] | 0.76 [0.75, 0.78] |
| archetype_no_structural_memory | n/a | n/a | 0.30 [0.28, 0.32] | 0.30 [0.28, 0.32] | 0.63 [0.60, 0.65] |
| archetype_no_counterfactual | 0.45 [0.44, 0.46] | 0.00 [0.00, 0.00] | 0.45 [0.42, 0.47] | 0.43 [0.40, 0.45] | 0.76 [0.74, 0.78] |
| B5 principle memory | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.43 [0.40, 0.45] | 0.47 [0.44, 0.50] | 0.84 [0.82, 0.85] |
| B2 search (screening) | n/a | n/a | 0.48 [0.45, 0.51] | 0.51 [0.48, 0.54] | 0.87 [0.86, 0.88] |
| B9 surface similarity | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.41 [0.39, 0.43] | 0.43 [0.41, 0.45] | 0.79 [0.77, 0.81] |

The five pairs named in the specification (mean change of the true effect from low to high; share of cases where each agent's prediction moved the right way):

| intervention -> transformation | true change | B11 ARCHETYPE | archetype_no_structural_memory | archetype_no_counterfactual | B5 principle memory | B2 search (screening) | B9 surface similarity |
|---|---|---|---|---|---|---|---|
| failure_cost->gate | 0.135 | 0.00 | n/a | 0.00 | 0.00 | n/a | 0.00 |
| parallelizability->parallelize | 0.083 | 0.98 | n/a | 0.99 | 0.00 | n/a | 0.00 |
| dependency_depth->decompose | 0.115 | 0.83 | n/a | 0.64 | 0.00 | n/a | 0.00 |
| observation_noise->replicate | 0.115 | 0.88 | n/a | 0.75 | 0.00 | n/a | 0.00 |
| delayed_feedback->decompose | 0.091 | 0.89 | n/a | 0.91 | 0.00 | n/a | 0.00 |

Structural memory vs the same agent without it on interventional environments: gap closure +0.134 [0.106, 0.160] *, choice accuracy +0.125 [0.101, 0.149] *.

## 10. Structural reconstruction events

A final architecture counts as a STRUCTURAL RECONSTRUCTION EVENT when (1) its role-level distance to every architecture observed in training is at least 0.1 (otherwise it is MEMORIZED TRANSFER), (2) every accepted principle's transformation is present and truly helps, and (3) it is useful. Events: **14**. Share of ARCHETYPE's final architectures in transfer worlds that are novel at role level: 0.06 [0.05, 0.08].

| family | event rate | surfaces with events | seeds with events | beats both searches on E2U | passes K5 |
|---|---|---|---|---|---|
| B00 | 0.01 | 1 | 1 | False | False |
| B01 | 0.00 | 0 | 0 | False | False |
| B02 | 0.00 | 0 | 0 | False | False |
| B03 | 0.00 | 0 | 0 | False | False |
| B04 | 0.00 | 0 | 0 | False | False |
| H00 | 0.04 | 3 | 3 | False | False |
| H01 | 0.10 | 3 | 7 | False | False |
| H02 | 0.00 | 0 | 0 | False | False |
| H03 | 0.00 | 0 | 0 | True | False |
| H04 | 0.00 | 0 | 0 | False | False |

Events meeting every condition of the breakthrough event log (spec §34): **0** (written to `breakthrough_events.jsonl`; all reconstruction events are in `reconstruction_events.jsonl`).

## 11. False-transfer results

False transfer: a trap transformation ends up, harmful, in the final phase-1 architecture of a false-analogy environment.

| agent | false-transfer rate | agent minus ARCHETYPE (paired) |
|---|---|---|
| B0 fixed | 0.09 [0.07, 0.11] | +0.08 [0.06, 0.09] * |
| B1 adaptive workflow | 0.03 [0.01, 0.04] | +0.01 [-0.00, 0.03] |
| B2 search (mutation) | 0.03 [0.01, 0.04] | +0.01 [-0.01, 0.02] |
| B2 search (screening) | 0.01 [0.00, 0.01] | -0.01 [-0.02, 0.00] |
| B3 task memory | 0.07 [0.05, 0.09] | +0.05 [0.03, 0.07] * |
| B4 architecture memory | 0.06 [0.04, 0.08] | +0.05 [0.03, 0.06] * |
| B5 principle memory | 0.01 [0.00, 0.01] | -0.01 [-0.02, 0.00] |
| B6 always adapt | 0.02 [0.01, 0.03] | +0.01 [-0.01, 0.02] |
| B7 never adapt | 0.27 [0.23, 0.30] | +0.25 [0.21, 0.29] * |
| B8 random transfer | 0.04 [0.02, 0.05] | +0.02 [0.01, 0.04] * |
| B9 surface similarity | 0.08 [0.06, 0.10] | +0.06 [0.04, 0.08] * |
| B10 latent oracle (analysis only) | 0.00 [0.00, 0.00] | -0.02 [-0.03, -0.01] * |
| B11 ARCHETYPE | 0.02 [0.01, 0.03] | - |
| archetype_no_structural_memory | 0.04 [0.03, 0.06] | +0.02 [0.01, 0.04] * |
| archetype_no_contraindications | 0.01 [0.00, 0.01] | -0.01 [-0.02, 0.00] |
| archetype_no_transfer_confidence | 0.10 [0.08, 0.13] | +0.09 [0.06, 0.11] * |
| archetype_no_counterfactual | 0.01 [0.00, 0.01] | -0.01 [-0.02, 0.00] |
| archetype_no_economics | 0.02 [0.01, 0.03] | +0.00 [-0.01, 0.01] |
| archetype_no_regime_detection | 0.02 [0.01, 0.03] | -0.00 [-0.01, 0.01] |
| archetype_no_structural_analogy | 0.01 [0.00, 0.01] | -0.01 [-0.02, 0.00] |
| archetype_no_reconstruction | 0.10 [0.07, 0.12] | +0.08 [0.06, 0.11] * |

At decision level, ARCHETYPE adopted 0.10 [0.07, 0.12] of trap transformations (TRUST, or TEST followed by acceptance).

## 12. Ablations

Each row removes one component. Deltas are ablated minus full, paired by seed. For E2U and false transfer a negative delta means the removal helped; for gap closure a positive delta means the removal helped.

| ablation | E2U transfer | E2U false | gap transfer | gap false | false-transfer rate | evaluations used | phase-2 gap | evidence against the component |
|---|---|---|---|---|---|---|---|---|
| without structural_memory | +5.5 [4.5, 6.6] * | +5.6 [4.3, 6.7] * | -0.133 [-0.154, -0.111] * | -0.211 [-0.239, -0.184] * | +0.024 [0.006, 0.043] * | -2.5 [-3.0, -2.0] * | -0.257 [-0.279, -0.236] * | no |
| without contraindications | +1.5 [0.6, 2.5] * | +2.7 [1.5, 3.9] * | +0.043 [0.023, 0.062] * | +0.034 [0.010, 0.057] * | -0.011 [-0.022, 0.002] | +6.0 [5.3, 6.6] * | +0.008 [-0.011, 0.026] | mixed: improves gap_transfer, gap_false |
| without transfer_confidence | +1.6 [0.1, 3.1] * | +3.1 [1.3, 4.7] * | -0.088 [-0.116, -0.063] * | -0.173 [-0.209, -0.135] * | +0.088 [0.062, 0.114] * | -3.4 [-3.9, -2.9] * | -0.157 [-0.186, -0.128] * | no |
| without counterfactual | +0.2 [-1.0, 1.4] | +0.5 [-1.1, 2.1] | -0.006 [-0.026, 0.015] | +0.004 [-0.037, 0.044] | -0.007 [-0.019, 0.005] | +0.2 [-0.3, 0.7] | -0.016 [-0.045, 0.011] | no |
| without economics | +0.1 [-0.8, 1.1] | +0.4 [-0.9, 1.6] | +0.083 [0.063, 0.102] * | +0.100 [0.076, 0.127] * | +0.004 [-0.006, 0.014] | +20.0 [19.6, 20.5] * | +0.025 [0.006, 0.044] * | YES: gap_transfer, gap_false, phase2_gap |
| without regime_detection | +0.2 [-0.8, 1.1] | -0.3 [-2.0, 1.5] | -0.002 [-0.020, 0.018] | +0.023 [-0.011, 0.058] | -0.000 [-0.012, 0.012] | +0.2 [-0.3, 0.7] | -0.134 [-0.158, -0.111] * | no |
| without structural_analogy | +2.4 [1.5, 3.2] * | -0.5 [-1.7, 1.0] | -0.022 [-0.040, -0.003] * | +0.042 [0.011, 0.068] * | -0.008 [-0.019, 0.003] | +2.0 [1.1, 2.8] * | -0.002 [-0.023, 0.018] | mixed: improves gap_false |
| without reconstruction | +1.2 [-0.0, 2.4] | +5.5 [4.1, 6.8] * | -0.085 [-0.105, -0.065] * | -0.219 [-0.257, -0.182] * | +0.080 [0.057, 0.105] * | -3.8 [-4.3, -3.3] * | -0.182 [-0.206, -0.155] * | no |

Regime shift (phase 2):

| agent | gap after a shift | gap of the kept incumbent before adapting | evaluations when shifted | evaluations when nothing changed | detection rate | false-alarm rate |
|---|---|---|---|---|---|---|
| B0 fixed | 0.28 [0.25, 0.31] | 0.28 [0.25, 0.31] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | - | - |
| B1 adaptive workflow | 0.41 [0.38, 0.44] | 0.37 [0.33, 0.40] | 1.9 [1.8, 2.0] | 1.2 [1.1, 1.2] | - | - |
| B2 search (mutation) | 0.45 [0.41, 0.49] | 0.36 [0.31, 0.41] | 5.7 [5.2, 6.2] | 1.5 [1.4, 1.7] | - | - |
| B2 search (screening) | 0.55 [0.51, 0.58] | 0.47 [0.43, 0.51] | 5.7 [5.2, 6.2] | 1.7 [1.5, 1.9] | - | - |
| B3 task memory | 0.48 [0.44, 0.52] | 0.40 [0.35, 0.45] | 5.5 [5.0, 5.9] | 1.5 [1.3, 1.7] | - | - |
| B4 architecture memory | 0.48 [0.44, 0.51] | 0.39 [0.34, 0.44] | 5.9 [5.4, 6.3] | 1.6 [1.4, 1.9] | - | - |
| B5 principle memory | 0.53 [0.49, 0.56] | 0.46 [0.43, 0.50] | 5.7 [5.2, 6.2] | 1.5 [1.3, 1.6] | - | - |
| B6 always adapt | 0.61 [0.58, 0.64] | 0.37 [0.32, 0.41] | 20.0 [20.0, 20.0] | 20.0 [20.0, 20.0] | - | - |
| B7 never adapt | -0.22 [-0.29, -0.14] | -0.22 [-0.29, -0.14] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | - | - |
| B8 random transfer | 0.44 [0.42, 0.47] | 0.35 [0.32, 0.38] | 5.7 [5.2, 6.2] | 1.4 [1.3, 1.6] | - | - |
| B9 surface similarity | 0.47 [0.43, 0.51] | 0.39 [0.35, 0.43] | 5.8 [5.3, 6.3] | 1.7 [1.4, 1.9] | - | - |
| B10 latent oracle (analysis only) | 1.00 [1.00, 1.00] | 0.58 [0.54, 0.62] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | - | - |
| B11 ARCHETYPE | 0.70 [0.67, 0.72] | 0.43 [0.39, 0.47] | 13.5 [13.0, 14.0] | 8.2 [7.3, 9.2] | 0.76 [0.73, 0.79] | 0.44 [0.39, 0.50] |
| archetype_no_structural_memory | 0.39 [0.35, 0.43] | 0.30 [0.25, 0.34] | 4.5 [4.0, 4.9] | 1.4 [1.2, 1.6] | 0.22 [0.19, 0.25] | 0.03 [0.02, 0.04] |
| archetype_no_contraindications | 0.69 [0.67, 0.72] | 0.44 [0.41, 0.48] | 15.1 [14.5, 15.7] | 9.1 [8.0, 10.2] | 0.75 [0.71, 0.78] | 0.43 [0.37, 0.49] |
| archetype_no_transfer_confidence | 0.55 [0.52, 0.58] | 0.33 [0.29, 0.36] | 11.4 [10.9, 11.9] | 6.3 [5.5, 7.2] | 0.75 [0.72, 0.79] | 0.40 [0.33, 0.46] |
| archetype_no_counterfactual | 0.67 [0.65, 0.69] | 0.42 [0.39, 0.45] | 13.9 [13.4, 14.4] | 7.5 [6.6, 8.3] | 0.77 [0.74, 0.80] | 0.38 [0.33, 0.43] |
| archetype_no_economics | 0.70 [0.67, 0.72] | 0.44 [0.40, 0.48] | 15.6 [15.0, 16.2] | 8.5 [7.5, 9.5] | 0.77 [0.74, 0.80] | 0.39 [0.34, 0.45] |
| archetype_no_regime_detection | 0.42 [0.38, 0.46] | 0.42 [0.38, 0.46] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| archetype_no_structural_analogy | 0.70 [0.68, 0.72] | 0.46 [0.41, 0.50] | 14.2 [13.7, 14.8] | 8.3 [7.3, 9.3] | 0.76 [0.73, 0.79] | 0.42 [0.36, 0.48] |
| archetype_no_reconstruction | 0.50 [0.47, 0.53] | 0.28 [0.23, 0.32] | 11.0 [10.6, 11.5] | 6.2 [5.4, 7.0] | 0.71 [0.68, 0.75] | 0.37 [0.32, 0.42] |

## 13. Statistical analysis

Seeds: 30. Paired comparisons by seed with 2000 bootstrap resamples; a comparison is called significant only when its 95% CI excludes zero. No correction for multiple comparisons is applied to the descriptive tables; the registered criteria are the fixed set below. Family-level criteria use the mean over the three surfaces of the family within a seed. Censoring: E2U is set to budget + 1 when an agent never becomes useful, which compresses differences among agents that often fail.

## 14. Failure cases

- Transfer families where ARCHETYPE needed significantly MORE evaluations than a search baseline: ['B02', 'B04', 'H04'].
- Transformations whose usefulness ARCHETYPE could not predict (AUROC below 0.6): ['recall'].
- Components whose removal improved results (evidence against the component): ['economics'].
- Hidden-only interventions: zero-evaluation prediction accuracy 0.00 [0.00, 0.00]. By construction the frozen learner sees no difference between the two environments of such a pair.
- Failed kill criteria: K2 (significant useful-evaluation reduction vs both searches on >= 2 unseen transfer families), K4 (counterfactual interventions change the predicted architectural preference in the true direction), K5 (a structurally reconstructed (novel) architecture provides measurable benefit), K6 (architecture search is NOT equal or better everywhere), K7 (results survive randomization of superficial cues (fully scrambled surfaces)).

## 15. Reproducibility

- Run commit(s): ['59990e9ecacdcd639d658699c98f2b30bd1eb4c7']; working tree dirty during the run: False; configuration hash(es): ['4b869c09c9f4a683']; executor: `inprocess-simulator`; versions: {'archetype': 'archetype-0.1', 'ir': 'archetype-ir-0.1', 'fitness': 'archetype-fitness-0.1', 'primitive_grammar': 'archetype-primitives-0.1', 'learner': 'archetype-learner-0.1'}.
- Registration: commit bc514ebee35f, config hash 4b869c09c9f4a683; code identical to the registered code: True; run made from a clean commit: True.
- Development seeds 0-9 were used to build and calibrate; they are not evidence. Registered seeds: 1000-1029.
- Every seed shard records seed, genome hashes, surface seeds, configuration, timestamps and a record hash; `python -m archetype.experiments.replay <shard>` re-executes it and compares the hash.
- Commands: `python -m archetype.experiments.sanity`, `python -m archetype.experiments.registration`, `python -m archetype.experiments.run --name registered --seeds $(seq 1000 1029) --workers 8`, `python -m archetype.reports.write_report results/archetype/registered`.
- Sanity experiment (3 seeds, before registration): passed, 19 of 19 checks.

## 16. Kill criteria

| id | criterion | result | evidence |
|---|---|---|---|
| K1 | structural transfer prediction outperforms surface-similarity transfer | **PASS** | within-transformation AUROC archetype 0.7399583535633496, delta vs surface 0.22238742589138297 CI [0.21077686413649055, 0.23524725132847843]; pooled delta 0.23603814840316104 CI [0.2249812373960701, 0.2474605923088654]; threshold AUROC >= 0.65 |
| K2 | significant useful-evaluation reduction vs both searches on >= 2 unseen transfer families | **FAIL** | 1 of 10 transfer families: ['H03'] |
| K3 | false-transfer rate stays low on false-analogy environments | **PASS** | false-transfer rate 0.016086134745555033 (threshold <= 0.2); vs search_screen delta -0.009688005767715913 CI [-0.02116438499771833, 0.0020182324385222936] |
| K4 | counterfactual interventions change the predicted architectural preference in the true direction | **FAIL** | observable-property pairs: accuracy 0.4234000688191417 CI [0.40950393498312193, 0.4382704172677491] (threshold >= 0.6, CI above 0.5); hidden-only pairs: 0.0; choice-level all: 0.42153144679974397 |
| K5 | a structurally reconstructed (novel) architecture provides measurable benefit | **FAIL** | families passing: []; reconstruction events: 14; share of final architectures that are novel: 0.06222222222222222 |
| K6 | architecture search is NOT equal or better everywhere | **FAIL** | pooled transfer reduction vs search_screen -2.3122222222222217 CI [-3.1922222222222216, -1.5322222222222217]; vs search 3.8311111111111114 CI [2.651111111111111, 5.067777777777778]; families won 1; no family won: False |
| K7 | results survive randomization of superficial cues (fully scrambled surfaces) | **FAIL** | scrambled surfaces: within-AUROC delta vs surface 0.2338984537167307 CI [0.2173733523370907, 0.2524719963240377]; e2u reduction vs search_screen -2.2633333333333336 CI [-3.936666666666667, -0.5933333333333337] |
| K8 | structural memory does NOT improve apparent transfer while hurting controlled counterfactuals | **PASS** | e2u reduction from memory (transfer) 5.526666666666667 CI [4.505555555555556, 6.566666666666667]; memory minus cold gap on interventional environments 0.1336613777777778 CI [0.10644026666666677, 0.1598405000000001] |

| id | success condition | holds |
|---|---|---|
| S1 | predicts when architectural transfer will be useful | yes |
| S2 | prediction survives changed vocabulary / task representation | yes |
| S3 | better than architecture search in at least 2 of 3 unseen transfer environments | no |
| S4 | at least one structurally reconstructed architecture not present in training | yes |
| S5 | the reconstructed architecture provides measurable benefit | no |
| S6 | counterfactual interventions change preference in the predicted direction | no |
| S7 | avoids harmful transfer to false-analogy environments | yes |
| S8 | survives removal of superficial similarity signals | no |
| S9 | survives held-out environment families | no |
| S10 | survives 30+ seeds | yes |

## 17. Final verdict

**NO_DISTINCT_CAPABILITY**

> Did the system learn a transferable relationship between environmental structure and computational organization that cannot be explained by task memorization, architecture copying, surface similarity, or ordinary architecture search?

**NO.**

Demonstrated in this run: the frozen learner's zero-evaluation scores predict which architectural transformations help in unseen environments better than surface similarity does, including on fully scrambled surfaces; a low rate of harmful transfer into false-analogy environments.
Not demonstrated: significant useful-evaluation reduction vs both searches on >= 2 unseen transfer families; counterfactual interventions change the predicted architectural preference in the true direction; a structurally reconstructed (novel) architecture provides measurable benefit; architecture search is NOT equal or better everywhere; results survive randomization of superficial cues (fully scrambled surfaces).

No breakthrough is claimed. Thresholds, metrics, learner, environments and search budgets were fixed before this run and were not changed afterwards.

Whatever the verdict, it concerns a planted relationship in a simulated laboratory (section 1).
