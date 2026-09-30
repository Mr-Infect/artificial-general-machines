# v0.2 analysis

Paired deltas are (variant − reference) over seeds; `*` marks a bootstrap 95% CI that excludes 0; d is Cohen's d on paired differences. Means are shown with median, sd, CI and n.

## Experiment 1 — repeatability (30 seeds, Domains A and B)

### Domain A (n=30)

| metric | adaptive | agm_v1_cold | agm_v2_cold | agm_v2_explore | fixed | search | self_evolving |
|---|---|---|---|---|---|---|---|
| quality_mean | 0.9165 (med 0.92, sd 0.043) [0.9, 0.931] n=30 | 0.9514 (med 0.964, sd 0.048) [0.933, 0.966] n=30 | 0.9476 (med 0.959, sd 0.046) [0.929, 0.962] n=30 | 0.9457 (med 0.959, sd 0.048) [0.927, 0.961] n=30 | 0.1704 (med 0.175, sd 0.019) [0.163, 0.176] n=30 | 0.9258 (med 0.953, sd 0.059) [0.903, 0.945] n=30 | 0.4898 (med 0.509, sd 0.29) [0.39, 0.592] n=30 |
| architecture_evaluations | 0 (med 0, sd 0) [0, 0] n=30 | 3.4 (med 3, sd 2.3) [2.67, 4.3] n=30 | 5.767 (med 4, sd 4.1) [4.57, 7.37] n=30 | 32.8 (med 32, sd 6.1) [30.7, 34.9] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 16.67 (med 16, sd 5.6) [14.8, 18.7] n=30 | 4.867 (med 5, sd 2) [4.17, 5.57] n=30 |
| adaptation_cost | 0 (med 0, sd 0) [0, 0] n=30 | 0.0017 (med 0.0015, sd 0.0011) [0.00133, 0.00215] n=30 | 0.002883 (med 0.002, sd 0.002) [0.00228, 0.00368] n=30 | 0.0164 (med 0.016, sd 0.003) [0.0153, 0.0175] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.02163 (med 0.0218, sd 0.0054) [0.0198, 0.0236] n=30 | 0.00287 (med 0.0028, sd 0.0017) [0.00231, 0.00349] n=30 |
| evaluations_to_target | — | — | 2.103 (med 1, sd 2.5) [1.24, 3.07] n=29 | 9.103 (med 8, sd 2.8) [8.28, 10.2] n=29 | — | — | — |
| failure_rate | 0 (med 0, sd 0) [0, 0] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.8 (med 0.8, sd 0) [0.8, 0.8] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.4267 (med 0.4, sd 0.33) [0.307, 0.54] n=30 |
| adaptation_overhead | 0 (med 0, sd 0) [0, 0] n=30 | 0.3687 (med 0.375, sd 0.14) [0.322, 0.419] n=30 | 0.4988 (med 0.444, sd 0.11) [0.463, 0.539] n=30 | 0.8632 (med 0.865, sd 0.031) [0.852, 0.873] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.8489 (med 0.853, sd 0.051) [0.83, 0.866] n=30 | 0.685 (med 0.686, sd 0.1) [0.647, 0.722] n=30 |
| target_reached_fraction | 0.90 | 1.00 | 1.00 | 1.00 | 0.17 | 0.97 | 0.40 |

### Domain B (n=30)

| metric | adaptive | agm_v1_cold | agm_v1_memory | agm_v2_cold | agm_v2_memory | fixed | search | self_evolving |
|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.6555 (med 0.656, sd 0.12) [0.615, 0.696] n=30 | 0.6587 (med 0.677, sd 0.17) [0.596, 0.716] n=30 | 0.6548 (med 0.667, sd 0.17) [0.59, 0.713] n=30 | 0.6587 (med 0.677, sd 0.17) [0.596, 0.716] n=30 | 0.6548 (med 0.667, sd 0.17) [0.59, 0.713] n=30 | 0.144 (med 0.158, sd 0.045) [0.127, 0.159] n=30 | 0.6687 (med 0.685, sd 0.16) [0.608, 0.723] n=30 | 0.4122 (med 0.466, sd 0.23) [0.334, 0.493] n=30 |
| architecture_evaluations | 0 (med 0, sd 0) [0, 0] n=30 | 6.767 (med 7.5, sd 2.4) [5.93, 7.57] n=30 | 6.733 (med 7.5, sd 2.4) [5.9, 7.57] n=30 | 13.9 (med 10, sd 10) [10.4, 17.5] n=30 | 13.6 (med 10, sd 9.5) [10.3, 17] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 17.53 (med 16, sd 5.4) [15.6, 19.5] n=30 | 4.967 (med 5.5, sd 2) [4.27, 5.67] n=30 |
| adaptation_cost | 0 (med 0, sd 0) [0, 0] n=30 | 0.003383 (med 0.00375, sd 0.0012) [0.00297, 0.00378] n=30 | 0.003367 (med 0.00375, sd 0.0012) [0.00295, 0.00378] n=30 | 0.00695 (med 0.005, sd 0.005) [0.0052, 0.00873] n=30 | 0.0068 (med 0.005, sd 0.0047) [0.00517, 0.00848] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.02323 (med 0.022, sd 0.0061) [0.0211, 0.0255] n=30 | 0.002507 (med 0.00185, sd 0.0015) [0.00199, 0.00304] n=30 |
| evaluations_to_target | — | — | — | 3.7 (med 2, sd 3.8) [2.25, 5.45] n=20 | 3.9 (med 2, sd 3.8) [2.4, 5.6] n=20 | — | — | — |
| failure_rate | 0 (med 0, sd 0) [0, 0] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.8 (med 0.8, sd 0) [0.8, 0.8] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.38 (med 0.3, sd 0.33) [0.267, 0.493] n=30 |
| adaptation_overhead | 0 (med 0, sd 0) [0, 0] n=30 | 0.5532 (med 0.599, sd 0.11) [0.511, 0.589] n=30 | 0.5523 (med 0.599, sd 0.11) [0.51, 0.588] n=30 | 0.6622 (med 0.667, sd 0.15) [0.61, 0.714] n=30 | 0.6633 (med 0.667, sd 0.14) [0.613, 0.713] n=30 | 0 (med 0, sd 0) [0, 0] n=30 | 0.8656 (med 0.878, sd 0.039) [0.851, 0.879] n=30 | 0.6735 (med 0.667, sd 0.09) [0.643, 0.707] n=30 |
| target_reached_fraction | 0.80 | 0.87 | 0.87 | 0.87 | 0.87 | 0.33 | 0.83 | 0.40 |

Paired memory − cold:

- AGM v1: quality_mean -0.003846 [-0.0108, +0] d=-0.22 (+0/−2/=28, n=30); architecture_evaluations -0.03333 [-0.1, +0] d=-0.18 (+0/−1/=29, n=30); adaptation_cost -1.667e-05 [-5e-05, +0] d=-0.18 (+0/−1/=29, n=30); evaluations_to_target — (pairs 0, both-missing 30); time_to_target_logical_s +0 [+0, +0] d=0.00 (+0/−0/=26, n=26); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- AGM v2: quality_mean -0.003846 [-0.0108, +0] d=-0.22 (+0/−2/=28, n=30); architecture_evaluations -0.3 [-1.17, +0.233] d=-0.13 (+2/−1/=27, n=30); adaptation_cost -0.00015 [-0.000583, +0.000117] d=-0.13 (+2/−1/=27, n=30); evaluations_to_target +0.2 [+0, +0.45] d=0.38 (+3/−0/=17, n=20); time_to_target_logical_s +0 [+0, +0] d=0.00 (+0/−0/=26, n=26); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)

## Experiment 2 — transfer matrix (AGM v0.2, memory from one source domain vs cold, paired)

| S→T | Δ adaptation cost | Δ evaluations | Δ evaluations-to-target | Δ quality | Δ failures | principle reuse (mean) | tests (kinds) | transferred-vs-cold final distance |
|---|---|---|---|---|---|---|---|---|
| B->A | +0.001133 [+0.000717, +0.00153]* d=1.00 (+22/−0/=8, n=30) | +2.267 [+1.43, +3.07]* d=1.00 (+22/−0/=8, n=30) | +2.333 [+1.5, +3.17]* d=0.99 (+22/−0/=8, n=30) | +0.003533 [-0.00493, +0.0145] d=0.13 (+2/−2/=26, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | 2.6666666666666665 | {'contradicted': 73, 'inconclusive': 4, 'supported': 3} | 0 (med 0, sd 0) [0, 0] n=30 identical 1.0 |
| C->A | +0.0003333 [+0.000217, +0.000467]* d=0.94 (+16/−0/=14, n=30) | +0.6667 [+0.433, +0.933]* d=0.94 (+16/−0/=14, n=30) | +0.6667 [+0.433, +0.933]* d=0.94 (+16/−0/=14, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | 1.0666666666666667 | {'contradicted': 26, 'inconclusive': 6} | 0 (med 0, sd 0) [0, 0] n=30 identical 1.0 |
| A->B | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0.04545 [+0, +0.136] d=0.21 (+1/−0/=21, n=22) | -0.002061 [-0.00526, +0] d=-0.26 (+0/−2/=28, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | 1.1333333333333333 | {'inconclusive': 5, 'contradicted': 24, 'supported': 5} | 0 (med 0, sd 0) [0, 0] n=30 identical 1.0 |
| C->B | -0.0003167 [-0.000633, -1.67e-05]* d=-0.35 (+2/−5/=23, n=30) | -0.6333 [-1.27, -0.0333]* d=-0.35 (+2/−5/=23, n=30) | -0.8636 [-1.73, -0.0909]* d=-0.43 (+2/−5/=15, n=22) | +0.007349 [+0, +0.0213] d=0.20 (+2/−0/=28, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | 1.2333333333333334 | {'contradicted': 15, 'inconclusive': 7, 'supported': 11} | 0.045 (med 0, sd 0.12) [0.01, 0.09] n=30 identical 0.8 |
| A->C | +0.0003833 [+0.000267, +0.000483]* d=1.35 (+23/−1/=6, n=30) | +0.7667 [+0.533, +0.967]* d=1.35 (+23/−1/=6, n=30) | +0.8276 [+0.69, +0.966]* d=2.15 (+24/−0/=5, n=29) | -0.002386 [-0.00564, -4.95e-05]* d=-0.29 (+3/−4/=23, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | 1.0333333333333334 | {'contradicted': 30} | 0.02333 (med 0, sd 0.073) [0, 0.05] n=30 identical 0.9 |
| B->C | +0.0002167 [+0.000133, +0.0003]* d=0.86 (+13/−0/=17, n=30) | +0.4333 [+0.267, +0.6]* d=0.86 (+13/−0/=17, n=30) | +0.4138 [+0.241, +0.586]* d=0.83 (+12/−0/=17, n=29) | -0.001821 [-0.00596, +0.00253] d=-0.15 (+1/−4/=25, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | 0.8333333333333334 | {'contradicted': 13, 'supported': 6, 'inconclusive': 5} | 0.06 (med 0, sd 0.18) [0, 0.12] n=30 identical 0.9 |

## Experiments 3 & 4 — principle and memory ablations (target domain, warm memory from the two other domains; variant − cold)

### Domain A

| variant | Δ adaptation cost | Δ evaluations | Δ evaluations-to-target | Δ quality | principle reuse |
|---|---|---|---|---|---|
| v2_warm_task | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) |
| v2_warm_architecture | +0.00055 [+0.0004, +0.000717]* d=1.24 (+21/−0/=9, n=30) | +1.1 [+0.8, +1.43]* d=1.24 (+21/−0/=9, n=30) | +1.167 [+0.867, +1.47]* d=1.33 (+22/−0/=8, n=30) | +0.004225 [+0, +0.0127] d=0.18 (+1/−0/=29, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) |
| v2_warm_principle | +0.0009167 [+0.0007, +0.00115]* d=1.42 (+26/−0/=4, n=30) | +1.833 [+1.4, +2.3]* d=1.42 (+26/−0/=4, n=30) | +1.9 [+1.4, +2.4]* d=1.36 (+26/−0/=4, n=30) | +0.006096 [+0, +0.0164] d=0.24 (+2/−0/=28, n=30) | +3.367 [+2.7, +4.03]* d=1.77 (+29/−0/=1, n=30) |
| v2_warm_full | +0.00125 [+0.00085, +0.00165]* d=1.13 (+23/−0/=7, n=30) | +2.5 [+1.7, +3.3]* d=1.13 (+23/−0/=7, n=30) | +2.6 [+1.77, +3.43]* d=1.10 (+23/−0/=7, n=30) | -0.001586 [-0.013, +0.0108] d=-0.05 (+2/−4/=24, n=30) | +3.267 [+2.6, +3.9]* d=1.71 (+29/−0/=1, n=30) |
| principle − architecture | +0.0003667 [+0.0002, +0.000517]* d=0.81 (+18/−2/=10, n=30) | +0.7333 [+0.4, +1.03]* d=0.81 (+18/−2/=10, n=30) | +0.7333 [+0.4, +1.03]* d=0.81 (+18/−2/=10, n=30) | +0.001871 [+0, +0.00561] d=0.18 (+1/−0/=29, n=30) | |
| full − architecture | +0.0007 [+0.000417, +0.000983]* d=0.87 (+17/−0/=13, n=30) | +1.4 [+0.833, +1.97]* d=0.87 (+17/−0/=13, n=30) | +1.433 [+0.867, +2.03]* d=0.87 (+17/−0/=13, n=30) | -0.005811 [-0.0149, +0.00216] d=-0.25 (+1/−4/=25, n=30) | |

### Domain B

| variant | Δ adaptation cost | Δ evaluations | Δ evaluations-to-target | Δ quality | principle reuse |
|---|---|---|---|---|---|
| v2_warm_task | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=22, n=22) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) |
| v2_warm_architecture | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0.04545 [+0, +0.136] d=0.21 (+1/−0/=21, n=22) | -0.002061 [-0.00526, +0] d=-0.26 (+0/−2/=28, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) |
| v2_warm_principle | -0.0003 [-0.0006, -1.67e-05]* d=-0.37 (+1/−5/=24, n=30) | -0.6 [-1.2, -0.0333]* d=-0.37 (+1/−5/=24, n=30) | -0.8182 [-1.64, -0.0909]* d=-0.44 (+1/−5/=16, n=22) | +0.007349 [+0, +0.0213] d=0.20 (+2/−0/=28, n=30) | +2.133 [+1.57, +2.77]* d=1.24 (+29/−0/=1, n=30) |
| v2_warm_full | -0.0002667 [-0.000567, -5.78e-20]* d=-0.33 (+2/−5/=23, n=30) | -0.5333 [-1.13, +0] d=-0.33 (+2/−5/=23, n=30) | -0.7273 [-1.5, -0.0455]* d=-0.40 (+2/−5/=15, n=22) | -0.0003956 [-0.00341, +0.00183] d=-0.05 (+1/−1/=28, n=30) | +2.1 [+1.57, +2.73]* d=1.26 (+29/−0/=1, n=30) |
| principle − architecture | -0.0003 [-0.0006, -1.67e-05]* d=-0.37 (+1/−5/=24, n=30) | -0.6 [-1.2, -0.0333]* d=-0.37 (+1/−5/=24, n=30) | -0.8636 [-1.64, -0.182]* d=-0.47 (+1/−6/=15, n=22) | +0.009411 [+0, +0.0243] d=0.25 (+3/−0/=27, n=30) | |
| full − architecture | -0.0002667 [-0.000567, -5.78e-20]* d=-0.33 (+2/−5/=23, n=30) | -0.5333 [-1.13, +0] d=-0.33 (+2/−5/=23, n=30) | -0.7727 [-1.55, -0.0909]* d=-0.44 (+1/−5/=16, n=22) | +0.001666 [+0, +0.005] d=0.18 (+1/−0/=29, n=30) | |

### Domain C

| variant | Δ adaptation cost | Δ evaluations | Δ evaluations-to-target | Δ quality | principle reuse |
|---|---|---|---|---|---|
| v2_warm_task | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=29, n=29) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) |
| v2_warm_architecture | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=29, n=29) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) | +0 [+0, +0] d=0.00 (+0/−0/=30, n=30) |
| v2_warm_principle | +0.0005167 [+0.000367, +0.000667]* d=1.22 (+22/−1/=7, n=30) | +1.033 [+0.733, +1.33]* d=1.22 (+22/−1/=7, n=30) | +1.069 [+0.828, +1.31]* d=1.52 (+23/−0/=6, n=29) | -0.00237 [-0.00675, +0.00211] d=-0.19 (+4/−6/=20, n=30) | +1.733 [+1.4, +2.1]* d=1.71 (+28/−0/=2, n=30) |
| v2_warm_full | +0.0005167 [+0.000367, +0.000667]* d=1.22 (+22/−1/=7, n=30) | +1.033 [+0.733, +1.33]* d=1.22 (+22/−1/=7, n=30) | +1.069 [+0.828, +1.31]* d=1.52 (+23/−0/=6, n=29) | -0.00237 [-0.00675, +0.00211] d=-0.19 (+4/−6/=20, n=30) | +1.733 [+1.4, +2.1]* d=1.71 (+28/−0/=2, n=30) |
| principle − architecture | +0.0005167 [+0.000367, +0.000667]* d=1.22 (+22/−1/=7, n=30) | +1.033 [+0.733, +1.33]* d=1.22 (+22/−1/=7, n=30) | +1.069 [+0.828, +1.31]* d=1.52 (+23/−0/=6, n=29) | -0.00237 [-0.00675, +0.00211] d=-0.19 (+4/−6/=20, n=30) | |
| full − architecture | +0.0005167 [+0.000367, +0.000667]* d=1.22 (+22/−1/=7, n=30) | +1.033 [+0.733, +1.33]* d=1.22 (+22/−1/=7, n=30) | +1.069 [+0.828, +1.31]* d=1.52 (+23/−0/=6, n=29) | -0.00237 [-0.00675, +0.00211] d=-0.19 (+4/−6/=20, n=30) | |

## Experiment 5 — adaptation economics ablation (variant − economic)

### Domain A

- decision outcome shares: {'v2_cold': {'ADAPT': 0.8, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.2, 'TERMINATE': 0.0}, 'v2_always_adapt': {'ADAPT': 1.0, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.0, 'TERMINATE': 0.0}, 'v2_never_adapt': {'ADAPT': 0.2, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.8, 'TERMINATE': 0.0}}
- v2_always_adapt: Δ evaluations +1 [+0.667, +1.37]* d=0.98 (+21/−0/=9, n=30); Δ adaptation cost +0.0005 [+0.000333, +0.000683]* d=0.98 (+21/−0/=9, n=30); Δ quality -0.002222 [-0.00667, +0] d=-0.18 (+0/−1/=29, n=30); Δ cpu +0.03215 [-4.19e-05, +0.064] d=0.37 (+21/−9/=0, n=30); Δ wall +6.361 [-5.58, +28.7] d=0.11 (+3/−27/=0, n=30); Δ failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- v2_never_adapt: Δ evaluations -3.033 [-3.37, -2.63]* d=-2.94 (+0/−29/=1, n=30); Δ adaptation cost -0.001517 [-0.00168, -0.00132]* d=-2.94 (+0/−29/=1, n=30); Δ quality +0.001905 [+0, +0.00571] d=0.18 (+1/−0/=29, n=30); Δ cpu -0.1414 [-0.167, -0.114]* d=-1.88 (+1/−29/=0, n=30); Δ wall -5.887 [-8.49, -3.51]* d=-0.84 (+2/−28/=0, n=30); Δ failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- wasted evaluations after target reached: {'v2_cold': '2.967 (med 3, sd 1) [2.57, 3.3] n=30', 'v2_always_adapt': '3.967 (med 4, sd 0.18) [3.9, 4] n=30', 'v2_never_adapt': '0 (med 0, sd 0) [0, 0] n=29'}
- mean decision error (realized − expected net value): {'v2_cold': '-0.1236 (med -0.109, sd 0.079) [-0.153, -0.0968] n=30', 'v2_always_adapt': '-0.141 (med -0.0975, sd 0.15) [-0.199, -0.0953] n=30', 'v2_never_adapt': '-0.1091 (med -0.0941, sd 0.077) [-0.138, -0.0829] n=30'}
- mean cost-estimate error (actual − estimated adaptation cost, quality units): {'v2_cold': '-0.0257 (med -0.0371, sd 0.022) [-0.0331, -0.018] n=30', 'v2_always_adapt': '-0.01069 (med -0.0423, sd 0.13) [-0.0381, 0.0385] n=30', 'v2_never_adapt': '-0.03744 (med -0.0444, sd 0.013) [-0.0418, -0.0325] n=30'}

### Domain B

- decision outcome shares: {'v2_cold': {'ADAPT': 0.93, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.07, 'TERMINATE': 0.0}, 'v2_always_adapt': {'ADAPT': 1.0, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.0, 'TERMINATE': 0.0}, 'v2_never_adapt': {'ADAPT': 0.29, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.71, 'TERMINATE': 0.0}}
- v2_always_adapt: Δ evaluations +0.7 [+0.233, +1.3]* d=0.46 (+10/−0/=20, n=30); Δ adaptation cost +0.00035 [+0.000117, +0.00065]* d=0.46 (+10/−0/=20, n=30); Δ quality -0.0002381 [-0.000714, +0] d=-0.18 (+0/−1/=29, n=30); Δ cpu +0.05542 [-0.00719, +0.132] d=0.28 (+19/−11/=0, n=30); Δ wall -3.179 [-5.56, -0.916]* d=-0.48 (+8/−22/=0, n=30); Δ failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- v2_never_adapt: Δ evaluations -7.633 [-10.3, -5.27]* d=-1.03 (+0/−30/=0, n=30); Δ adaptation cost -0.003817 [-0.00515, -0.00263]* d=-1.03 (+0/−30/=0, n=30); Δ quality -0.0007424 [-0.00164, +0] d=-0.32 (+0/−3/=27, n=30); Δ cpu -0.4623 [-0.639, -0.296]* d=-0.93 (+0/−30/=0, n=30); Δ wall -6.414 [-9.36, -4.04]* d=-0.82 (+5/−25/=0, n=30); Δ failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- wasted evaluations after target reached: {'v2_cold': '3.409 (med 4, sd 0.73) [3.09, 3.68] n=22', 'v2_always_adapt': '3.565 (med 4, sd 0.99) [3.13, 3.91] n=23', 'v2_never_adapt': '0.4444 (med 0, sd 0.51) [0.222, 0.667] n=18'}
- mean decision error (realized − expected net value): {'v2_cold': '-0.2222 (med -0.214, sd 0.2) [-0.294, -0.15] n=30', 'v2_always_adapt': '-0.2172 (med -0.211, sd 0.2) [-0.29, -0.146] n=30', 'v2_never_adapt': '-0.2078 (med -0.205, sd 0.21) [-0.283, -0.136] n=30'}
- mean cost-estimate error (actual − estimated adaptation cost, quality units): {'v2_cold': '-0.01868 (med -0.0296, sd 0.026) [-0.0271, -0.00885] n=30', 'v2_always_adapt': '-0.02414 (med -0.0341, sd 0.021) [-0.031, -0.0163] n=30', 'v2_never_adapt': '-0.0334 (med -0.0396, sd 0.016) [-0.0388, -0.0275] n=30'}

### Domain C

- decision outcome shares: {'v2_cold': {'ADAPT': 0.99, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.01, 'TERMINATE': 0.0}, 'v2_always_adapt': {'ADAPT': 1.0, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.0, 'TERMINATE': 0.0}, 'v2_never_adapt': {'ADAPT': 0.37, 'PARTIAL_ADAPT': 0.0, 'DO_NOT_ADAPT': 0.63, 'TERMINATE': 0.0}}
- v2_always_adapt: Δ evaluations +0.03333 [+0, +0.1] d=0.18 (+1/−0/=29, n=30); Δ adaptation cost +1.667e-05 [+0, +5e-05] d=0.18 (+1/−0/=29, n=30); Δ quality +0 [+0, +0] d=0.00 (+0/−0/=30, n=30); Δ cpu -0.02537 [-0.0876, +0.0436] d=-0.13 (+13/−17/=0, n=30); Δ wall -3.812 [-5.71, -2.07]* d=-0.74 (+6/−24/=0, n=30); Δ failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- v2_never_adapt: Δ evaluations -14.07 [-16, -11.9]* d=-2.37 (+0/−30/=0, n=30); Δ adaptation cost -0.007033 [-0.008, -0.00595]* d=-2.37 (+0/−30/=0, n=30); Δ quality -0.001422 [-0.00614, +0.00228] d=-0.12 (+4/−6/=20, n=30); Δ cpu -0.6487 [-0.758, -0.54]* d=-2.09 (+1/−29/=0, n=30); Δ wall -8.629 [-11.5, -6.18]* d=-1.12 (+0/−30/=0, n=30); Δ failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- wasted evaluations after target reached: {'v2_cold': '18.28 (med 24, sd 8.9) [15.1, 21.2] n=29', 'v2_always_adapt': '18.31 (med 24, sd 8.8) [15.1, 21.2] n=29', 'v2_never_adapt': '4.889 (med 6, sd 2.4) [4, 5.56] n=27'}
- mean decision error (realized − expected net value): {'v2_cold': '-0.1398 (med -0.137, sd 0.053) [-0.158, -0.122] n=30', 'v2_always_adapt': '-0.1328 (med -0.131, sd 0.053) [-0.152, -0.115] n=30', 'v2_never_adapt': '-0.1189 (med -0.108, sd 0.05) [-0.137, -0.102] n=30'}
- mean cost-estimate error (actual − estimated adaptation cost, quality units): {'v2_cold': '-0.01103 (med -0.0218, sd 0.025) [-0.0194, -0.00174] n=30', 'v2_always_adapt': '-0.01796 (med -0.0239, sd 0.018) [-0.0241, -0.0109] n=30', 'v2_never_adapt': '-0.03314 (med -0.0375, sd 0.012) [-0.0374, -0.0284] n=30'}

## Experiment 6 — architecture distance

| run:agent | final distance to initial | fraction final identical to initial | max distance | final novelty level vs prior memory | distance reached vs not | cross-domain selected fraction |
|---|---|---|---|---|---|---|
| v02_exp1_A:agm_v2_cold | 0 (med 0, sd 0) [0, 0] n=30 | 1.00 | 0 (med 0, sd 0) [0, 0] n=30 | {'None': 30} | 0 (med 0, sd 0) [0, 0] n=30 vs — | 0.00 |
| v02_exp1_A:agm_v2_explore | 0 (med 0, sd 0) [0, 0] n=30 | 1.00 | 0 (med 0, sd 0) [0, 0] n=30 | {'None': 24, 'A_parameter_variation': 6} | 0 (med 0, sd 0) [0, 0] n=30 vs — | 0.00 |
| v02_exp1_B:agm_v2_cold | 0.04 (med 0, sd 0.067) [0.02, 0.065] n=30 | 0.73 | 0.04 (med 0, sd 0.067) [0.02, 0.065] n=30 | {'None': 30} | 0.04615 (med 0, sd 0.071) [0.0173, 0.075] n=26 vs 0 (med 0, sd 0) [0, 0] n=4 | 0.00 |
| v02_exp1_B:agm_v2_memory | 0.05667 (med 0, sd 0.13) [0.02, 0.11] n=30 | 0.73 | 0.05667 (med 0, sd 0.13) [0.02, 0.11] n=30 | {'E_unseen_architectural_pattern': 21, 'None': 9} | 0.06538 (med 0, sd 0.14) [0.0231, 0.121] n=26 vs 0 (med 0, sd 0) [0, 0] n=4 | 0.31 |
| v02_exp2_tgt_A:v2_always_adapt | 0 (med 0, sd 0) [0, 0] n=30 | 1.00 | 0 (med 0, sd 0) [0, 0] n=30 | {'None': 30} | 0 (med 0, sd 0) [0, 0] n=29 vs 0 (med 0, sd 0) [0, 0] n=1 | 0.00 |
| v02_exp2_tgt_A:v2_cold | 0 (med 0, sd 0) [0, 0] n=30 | 1.00 | 0 (med 0, sd 0) [0, 0] n=30 | {'None': 30} | 0 (med 0, sd 0) [0, 0] n=29 vs 0 (med 0, sd 0) [0, 0] n=1 | 0.00 |
| v02_exp2_tgt_A:v2_from_B | 0.04 (med 0, sd 0.12) [0, 0.085] n=30 | 0.90 | 0.04 (med 0, sd 0.12) [0, 0.085] n=30 | {'E_unseen_architectural_pattern': 24, 'None': 6} | 0.04 (med 0, sd 0.12) [0, 0.085] n=30 vs — | 0.15 |
| v02_exp2_tgt_A:v2_from_C | 0 (med 0, sd 0) [0, 0] n=30 | 1.00 | 0 (med 0, sd 0) [0, 0] n=30 | {'E_unseen_architectural_pattern': 30} | 0 (med 0, sd 0) [0, 0] n=29 vs 0 (med 0, sd 0) [0, 0] n=1 | 0.10 |
| v02_exp2_tgt_A:v2_never_adapt | 0 (med 0, sd 0) [0, 0] n=30 | 1.00 | 0 (med 0, sd 0) [0, 0] n=30 | {'None': 30} | 0 (med 0, sd 0) [0, 0] n=29 vs 0 (med 0, sd 0) [0, 0] n=1 | 0.00 |
| v02_exp2_tgt_A:v2_warm_architecture | 0.01 (med 0, sd 0.055) [0, 0.03] n=30 | 0.97 | 0.01 (med 0, sd 0.055) [0, 0.03] n=30 | {'E_unseen_architectural_pattern': 24, 'None': 6} | 0.01 (med 0, sd 0.055) [0, 0.03] n=30 vs — | 0.00 |
| v02_exp2_tgt_A:v2_warm_full | 0.08167 (med 0, sd 0.2) [0.02, 0.158] n=30 | 0.83 | 0.08167 (med 0, sd 0.2) [0.02, 0.158] n=30 | {'E_unseen_architectural_pattern': 24, 'None': 6} | 0.08167 (med 0, sd 0.2) [0.02, 0.158] n=30 vs — | 0.19 |
| v02_exp2_tgt_A:v2_warm_principle | 0.01 (med 0, sd 0.055) [0, 0.03] n=30 | 0.97 | 0.01 (med 0, sd 0.055) [0, 0.03] n=30 | {'E_unseen_architectural_pattern': 24, 'None': 6} | 0.01 (med 0, sd 0.055) [0, 0.03] n=30 vs — | 0.17 |
| v02_exp2_tgt_A:v2_warm_task | 0 (med 0, sd 0) [0, 0] n=30 | 1.00 | 0 (med 0, sd 0) [0, 0] n=30 | {'E_unseen_architectural_pattern': 24, 'None': 6} | 0 (med 0, sd 0) [0, 0] n=29 vs 0 (med 0, sd 0) [0, 0] n=1 | 0.00 |
| v02_exp2_tgt_B:v2_always_adapt | 0.08 (med 0, sd 0.1) [0.045, 0.12] n=30 | 0.53 | 0.08 (med 0, sd 0.1) [0.045, 0.12] n=30 | {'None': 30} | 0.08333 (med 0, sd 0.1) [0.0444, 0.128] n=27 vs 0.05 (med 0, sd 0.087) [0, 0.15] n=3 | 0.00 |
| v02_exp2_tgt_B:v2_cold | 0.065 (med 0, sd 0.076) [0.04, 0.09] n=30 | 0.57 | 0.065 (med 0, sd 0.076) [0.04, 0.09] n=30 | {'None': 30} | 0.06667 (med 0, sd 0.076) [0.0389, 0.0944] n=27 vs 0.05 (med 0, sd 0.087) [0, 0.15] n=3 | 0.00 |
| v02_exp2_tgt_B:v2_from_A | 0.09833 (med 0, sd 0.17) [0.045, 0.163] n=30 | 0.57 | 0.09833 (med 0, sd 0.17) [0.045, 0.163] n=30 | {'None': 8, 'E_unseen_architectural_pattern': 22} | 0.1037 (med 0, sd 0.17) [0.0444, 0.174] n=27 vs 0.05 (med 0, sd 0.087) [0, 0.15] n=3 | 0.20 |
| v02_exp2_tgt_B:v2_from_C | 0.04 (med 0, sd 0.067) [0.015, 0.065] n=30 | 0.73 | 0.04 (med 0, sd 0.067) [0.015, 0.065] n=30 | {'E_unseen_architectural_pattern': 30} | 0.04444 (med 0, sd 0.07) [0.0222, 0.0722] n=27 vs 0 (med 0, sd 0) [0, 0] n=3 | 0.27 |
| v02_exp2_tgt_B:v2_never_adapt | 0.065 (med 0, sd 0.076) [0.04, 0.09] n=30 | 0.57 | 0.065 (med 0, sd 0.076) [0.04, 0.09] n=30 | {'None': 30} | 0.06667 (med 0, sd 0.076) [0.0389, 0.0944] n=27 vs 0.05 (med 0, sd 0.087) [0, 0.15] n=3 | 0.00 |
| v02_exp2_tgt_B:v2_warm_architecture | 0.09833 (med 0, sd 0.17) [0.045, 0.163] n=30 | 0.57 | 0.09833 (med 0, sd 0.17) [0.045, 0.163] n=30 | {'None': 8, 'E_unseen_architectural_pattern': 22} | 0.1037 (med 0, sd 0.17) [0.0444, 0.174] n=27 vs 0.05 (med 0, sd 0.087) [0, 0.15] n=3 | 0.00 |
| v02_exp2_tgt_B:v2_warm_full | 0.05667 (med 0, sd 0.13) [0.02, 0.11] n=30 | 0.73 | 0.05667 (med 0, sd 0.13) [0.02, 0.11] n=30 | {'None': 8, 'E_unseen_architectural_pattern': 22} | 0.06296 (med 0, sd 0.13) [0.0222, 0.122] n=27 vs 0 (med 0, sd 0) [0, 0] n=3 | 0.37 |
| v02_exp2_tgt_B:v2_warm_principle | 0.04 (med 0, sd 0.067) [0.015, 0.065] n=30 | 0.73 | 0.04 (med 0, sd 0.067) [0.015, 0.065] n=30 | {'None': 7, 'E_unseen_architectural_pattern': 23} | 0.04444 (med 0, sd 0.07) [0.0222, 0.0722] n=27 vs 0 (med 0, sd 0) [0, 0] n=3 | 0.40 |
| v02_exp2_tgt_B:v2_warm_task | 0.065 (med 0, sd 0.076) [0.04, 0.09] n=30 | 0.57 | 0.065 (med 0, sd 0.076) [0.04, 0.09] n=30 | {'None': 8, 'E_unseen_architectural_pattern': 22} | 0.06667 (med 0, sd 0.076) [0.0389, 0.0944] n=27 vs 0.05 (med 0, sd 0.087) [0, 0.15] n=3 | 0.00 |
| v02_exp2_tgt_C:v2_always_adapt | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'None': 30} | 0.366 (med 0.3, sd 0.21) [0.288, 0.45] n=25 vs 0.3 (med 0.3, sd 0.32) [0.06, 0.57] n=5 | 0.00 |
| v02_exp2_tgt_C:v2_cold | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'None': 30} | 0.366 (med 0.3, sd 0.21) [0.288, 0.45] n=25 vs 0.3 (med 0.3, sd 0.32) [0.06, 0.57] n=5 | 0.00 |
| v02_exp2_tgt_C:v2_from_A | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'E_unseen_architectural_pattern': 30} | 0.35 (med 0.3, sd 0.2) [0.275, 0.431] n=24 vs 0.375 (med 0.375, sd 0.34) [0.125, 0.625] n=6 | 0.00 |
| v02_exp2_tgt_C:v2_from_B | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'E_unseen_architectural_pattern': 30} | 0.35 (med 0.3, sd 0.2) [0.275, 0.431] n=24 vs 0.375 (med 0.375, sd 0.34) [0.125, 0.625] n=6 | 0.10 |
| v02_exp2_tgt_C:v2_never_adapt | 0.3 (med 0.3, sd 0.15) [0.245, 0.355] n=30 | 0.17 | 0.3 (med 0.3, sd 0.15) [0.245, 0.355] n=30 | {'None': 30} | 0.312 (med 0.3, sd 0.14) [0.258, 0.36] n=25 vs 0.24 (med 0.3, sd 0.23) [0.06, 0.42] n=5 | 0.00 |
| v02_exp2_tgt_C:v2_warm_architecture | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'E_unseen_architectural_pattern': 30} | 0.366 (med 0.3, sd 0.21) [0.288, 0.45] n=25 vs 0.3 (med 0.3, sd 0.32) [0.06, 0.57] n=5 | 0.00 |
| v02_exp2_tgt_C:v2_warm_full | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'E_unseen_architectural_pattern': 30} | 0.35 (med 0.3, sd 0.2) [0.275, 0.431] n=24 vs 0.375 (med 0.375, sd 0.34) [0.125, 0.625] n=6 | 0.10 |
| v02_exp2_tgt_C:v2_warm_principle | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'E_unseen_architectural_pattern': 30} | 0.35 (med 0.3, sd 0.2) [0.275, 0.431] n=24 vs 0.375 (med 0.375, sd 0.34) [0.125, 0.625] n=6 | 0.10 |
| v02_exp2_tgt_C:v2_warm_task | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | 0.17 | 0.355 (med 0.3, sd 0.23) [0.275, 0.435] n=30 | {'E_unseen_architectural_pattern': 30} | 0.366 (med 0.3, sd 0.21) [0.288, 0.45] n=25 vs 0.3 (med 0.3, sd 0.32) [0.06, 0.57] n=5 | 0.00 |

## Experiment 7 — cold vs warm (warm = memory from the two other domains; warm − cold)

- Domain A: evaluations_to_target +2.6 [+1.77, +3.43]* d=1.10 (+23/−0/=7, n=30); time_to_target_logical_s +2.069 [+0, +4.83] d=0.31 (+3/−0/=26, n=29); architecture_evaluations +2.5 [+1.7, +3.3]* d=1.13 (+23/−0/=7, n=30); adaptation_cost +0.00125 [+0.00085, +0.00165]* d=1.13 (+23/−0/=7, n=30); quality_mean -0.001586 [-0.013, +0.0108] d=-0.05 (+2/−4/=24, n=30); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30); cpu_time_s +0.1616 [+0.111, +0.215]* d=1.09 (+27/−3/=0, n=30); max_memory_mb -0.1677 [-0.504, +0.000521] d=-0.18 (+2/−1/=27, n=30)
- Domain B: evaluations_to_target -0.7273 [-1.5, -0.0455]* d=-0.40 (+2/−5/=15, n=22); time_to_target_logical_s -0.7407 [-2.22, +0] d=-0.19 (+0/−1/=26, n=27); architecture_evaluations -0.5333 [-1.13, +0] d=-0.33 (+2/−5/=23, n=30); adaptation_cost -0.0002667 [-0.000567, -5.78e-20]* d=-0.33 (+2/−5/=23, n=30); quality_mean -0.0003956 [-0.00341, +0.00183] d=-0.05 (+1/−1/=28, n=30); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30); cpu_time_s -0.01446 [-0.093, +0.0582] d=-0.07 (+19/−11/=0, n=30); max_memory_mb -1.696 [-4.89, -0.0328]* d=-0.20 (+1/−5/=24, n=30)
- Domain C: evaluations_to_target +1.069 [+0.828, +1.31]* d=1.52 (+23/−0/=6, n=29); time_to_target_logical_s +1.667 [+0, +4.58] d=0.26 (+2/−0/=22, n=24); architecture_evaluations +1.033 [+0.733, +1.33]* d=1.22 (+22/−1/=7, n=30); adaptation_cost +0.0005167 [+0.000367, +0.000667]* d=1.22 (+22/−1/=7, n=30); quality_mean -0.00237 [-0.00675, +0.00211] d=-0.19 (+4/−6/=20, n=30); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30); cpu_time_s +0.02744 [-0.0356, +0.0948] d=0.15 (+18/−12/=0, n=30); max_memory_mb -3.375 [-8.3, -0.0656]* d=-0.27 (+0/−5/=25, n=30)

## AGM v0.1 (architecture memory) vs AGM v0.2 (full memory), warm, paired

- Domain A: quality_mean -0.007715 [-0.0157, -0.00151]* d=-0.38 (+0/−5/=25, n=30); architecture_evaluations +3.233 [+2.6, +3.87]* d=1.73 (+27/−0/=3, n=30); adaptation_cost +0.001617 [+0.0013, +0.00193]* d=1.73 (+27/−0/=3, n=30); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- Domain B: quality_mean +0.001666 [+0, +0.005] d=0.18 (+1/−0/=29, n=30); architecture_evaluations +6.1 [+3.33, +9.07]* d=0.73 (+25/−3/=2, n=30); adaptation_cost +0.00305 [+0.00167, +0.00453]* d=0.73 (+25/−3/=2, n=30); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)
- Domain C: quality_mean -0.01174 [-0.0211, -0.00302]* d=-0.46 (+3/−11/=16, n=30); architecture_evaluations +16.23 [+13.4, +18.7]* d=2.18 (+29/−0/=1, n=30); adaptation_cost +0.008117 [+0.0067, +0.00935]* d=2.18 (+29/−0/=1, n=30); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30)

## Experiment 8 — held-out conditions (warm − cold)

- Domain A (n=30): quality_mean -0.001624 [-0.0197, +0.0175] d=-0.03 (+2/−2/=26, n=30); architecture_evaluations +2.067 [+1.43, +2.7]* d=1.16 (+23/−0/=7, n=30); adaptation_cost +0.001033 [+0.000717, +0.00135]* d=1.16 (+23/−0/=7, n=30); evaluations_to_target +2.138 [+1.52, +2.79]* d=1.21 (+23/−0/=6, n=29); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30); principle_reuse +2.467 [+2, +2.9]* d=1.89 (+29/−0/=1, n=30); principle tests {'contradicted': 60, 'supported': 7, 'inconclusive': 7}
- Domain B (n=30): quality_mean +0.002392 [-0.00176, +0.00895] d=0.14 (+3/−2/=25, n=30); architecture_evaluations +0.5 [+0.2, +0.833]* d=0.58 (+9/−0/=21, n=30); adaptation_cost +0.00025 [+0.0001, +0.000417]* d=0.58 (+9/−0/=21, n=30); evaluations_to_target +0.6667 [+0.333, +1]* d=0.72 (+11/−0/=16, n=27); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30); principle_reuse +2.233 [+1.77, +2.7]* d=1.62 (+29/−0/=1, n=30); principle tests {'contradicted': 61, 'inconclusive': 5, 'supported': 1}
- Domain C (n=30): quality_mean -0.001774 [-0.00469, +7.68e-05] d=-0.25 (+1/−4/=25, n=30); architecture_evaluations +0.7667 [-0.0333, +1.87] d=0.29 (+19/−2/=9, n=30); adaptation_cost +0.0003833 [-1.67e-05, +0.000933] d=0.29 (+19/−2/=9, n=30); evaluations_to_target +0.7778 [+0.593, +0.926]* d=1.84 (+21/−0/=6, n=27); failures +0 [+0, +0] d=0.00 (+0/−0/=30, n=30); principle_reuse +1.233 [+1, +1.53]* d=1.59 (+28/−0/=2, n=30); principle tests {'contradicted': 33, 'supported': 2}

## Principle inventory (all memory files)

- {'memory_files': 960, 'status_counts': {'INCONCLUSIVE': 526, 'PARTIALLY_SUPPORTED': 36, 'UNTESTED': 2173}, 'rule_counts': {'minimal_perception_under_tight_memory': 1112, 'cheap_filter_before_verification': 406, 'ensemble_perception_under_uncertainty': 302, 'rule_roles_for_verification_tasks': 532, 'expensive_analysis_only_when_affordable': 383}}

## Success criteria (pre-registered)

| id | criterion | evidence | met |
|---|---|---|---|
| A | Architectural principles can be extracted from experience. | 2735 principle records across memory files; status counts {'INCONCLUSIVE': 526, 'PARTIALLY_SUPPORTED': 36, 'UNTESTED': 2173} | yes |
| B | Principles can be experimentally validated (tested under new conditions with recorded outcomes). | 233 principle tests recorded in transfer targets; 36 principles reached a non-UNTESTED status | yes |
| C | Validated principles transfer to a genuinely different domain (principle-derived architectures instantiated and evaluated in the target). | principle reuse > 0 in 6/6 source→target cells: ['B->A', 'C->A', 'A->B', 'C->B', 'A->C', 'B->C'] | yes |
| D | Transfer reduces adaptation/search cost (paired Δ adaptation cost < 0 with 95% CI excluding 0, or Δ evaluations-to-target < 0 likewise). | cells with significant cost reduction: ['C->B']; with significant cost increase: ['B->A', 'C->A', 'A->C', 'B->C']; with significant evaluations-to-target reduction: ['C->B'] | yes |
| E | The machine decides not to adapt when adaptation is uneconomical (DO_NOT_ADAPT occurs; always-adapt spends more evaluations without higher quality). | DO_NOT_ADAPT share of decisions per domain {'A': 0.2, 'B': 0.06666666666666667, 'C': 0.006666666666666667}; Δ evaluations (always_adapt − economic) {'A': 1.0, 'B': 0.7, 'C': 0.03333333333333333}; Δ quality {'A': -0.002222222222222222, 'B': -0.00023809523809523725, 'C': 0.0} | yes |
| F | Useful transferred architectures are not merely memorized copies (structural distance between transferred and cold final architectures > 0 in some cells, and transferred architectures differ from source architectures). | cells where transferred final architecture differs structurally from the cold final: ['C->B', 'A->C', 'B->C']; fraction identical per cell: {'B->A': 1.0, 'C->A': 1.0, 'A->B': 1.0, 'C->B': 0.8, 'A->C': 0.9, 'B->C': 0.9} | yes |
| G | The benefit survives multiple random seeds (criterion D holds with n ≥ 30 paired seeds and CI excluding 0). | n_pairs per cell: {'B->A': 30, 'C->A': 30, 'A->B': 30, 'C->B': 30, 'A->C': 30, 'B->C': 30} | yes |

Criteria met: 7 of 7. All must hold for the v0.2 hypothesis to be considered supported.
