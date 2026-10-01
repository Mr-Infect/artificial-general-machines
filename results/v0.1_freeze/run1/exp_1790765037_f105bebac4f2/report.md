# Experiment report: cross_domain_001_domain_a_network

- id: `exp_1790765037_f105bebac4f2`  seed: 100  executor: docker  git: `5f0c37881a8f`  manifest: `8da92a6e1ad2838f`
- task: anomaly_detection / network (n=2000, noise=0.1, anomaly_rate=0.03)
- target quality: 0.85  executions: 38 (candidate evaluations: 18)

This report lists measurements. It does not declare any agent successful.

## Aggregate metrics per agent

| metric | fixed | adaptive | search | agm_cold |
|---|---|---|---|---|
| quality_mean | 0.1778 | 0.9311 | 0.9533 | 0.9533 |
| quality_min | 0 | 0.8333 | 0.8333 | 0.8333 |
| quality_final | 0 | 0.8333 | 0.8333 | 0.8333 |
| time_to_target_logical_s | 0 | 0 | 0 | 0 |
| time_to_target_wall_s | 0.3516 | 0.297 | 6.354 | 1.18 |
| search_time_s | 1.212e-05 | 0.008167 | 13.39 | 1.849 |
| architecture_evaluations | 0 | 0 | 16 | 2 |
| model_calls | 1 | 5 | 21 | 7 |
| tokens | 480 | 2400 | 30000 | 3600 |
| cpu_time_s | 0.1677 | 0.7027 | 3.268 | 0.9883 |
| max_memory_mb | 12.47 | 12.75 | 12.75 | 13 |
| execution_cost | 0.0005 | 0.0025 | 0.0025 | 0.0025 |
| adaptation_cost | 0 | 0 | 0.029 | 0.001 |
| total_cost | 0.0005 | 0.0025 | 0.0315 | 0.0035 |
| constraint_violations | 4 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.2 |
| distinct_architectures | 1 | 2 | 2 | 1 |
| wall_used_s | 0.3517 | 1.677 | 14.1 | 3.363 |

## Resource-normalized comparison

| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |
|---|---|---|---|---|
| fixed | 355.6 | 1.06 | 0 | 3.445e-05 |
| adaptive | 372.4 | 1.325 | 0 | 0.004871 |
| search | 30.26 | 0.2917 | 0.9206 | 0.9494 |
| agm_cold | 272.4 | 0.9646 | 0.2857 | 0.5499 |

Pareto front (min total_cost, max quality_mean): fixed, adaptive, agm_cold
Pareto front (min cpu_time_s, max quality_mean): fixed, adaptive, agm_cold

## Quality per step

| agent | t=0 | t=10 | t=20 | t=30 | t=40 |
|---|---|---|---|---|---|
| fixed | 0.8889 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) |
| adaptive | 0.8889 (standard) | 0.9333 (lightweight) | 1 (lightweight) | 1 (lightweight) | 0.8333 (lightweight) |
| search | 1 (search) | 0.9333 (search) | 1 (search) | 1 (search) | 0.8333 (search) |
| agm_cold | 1 (syn_anom_direc) | 0.9333 (syn_anom_direc) | 1 (syn_anom_direc) | 1 (syn_anom_direc) | 0.8333 (syn_anom_direc) |

## Environment transitions

- t=10: memory_reduction {'memory_mb': 80} → memory=80MB cpu=1.0 network=True latency=2000ms priority=1 caps=27
- t=20: network_loss {} → memory=80MB cpu=1.0 network=False latency=2000ms priority=1 caps=27
- t=20: capability_removal {'capabilities': ['model:large_reasoner', 'tool:search']} → memory=80MB cpu=1.0 network=False latency=2000ms priority=1 caps=25
- t=30: latency_reduction {'latency_ms': 800} → memory=80MB cpu=1.0 network=False latency=800ms priority=1 caps=25
- t=40: priority_increase {'priority': 3} → memory=80MB cpu=1.0 network=False latency=800ms priority=3 caps=25

## Adaptation decisions

| agent | step | outcome | expected_quality | expected_improvement | search_cost | validation_cost | budget_remaining | deadline_remaining_s | rationale |
|---|---|---|---|---|---|---|---|---|---|
| agm_cold | 0 | ADAPT | 0 | 0.85 | 0.003 | 0.0005 | 0.25 | 120 | current architecture invalid under environment (cost_ratio=0.014, time_ratio=0.025, priority_weight=1.00) |
| agm_cold | 1 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.249 | 118.8 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.019, priority_weight=1.00) |
| agm_cold | 2 | ADAPT | 0.9333 | 0.06667 | 0.003 | 0.0005 | 0.2485 | 118.5 | benefit 0.067 > price 0.031 (cost_ratio=0.014, time_ratio=0.017, priority_weight=1.00) |
| agm_cold | 3 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.2475 | 117.4 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.016, priority_weight=1.00) |
| agm_cold | 4 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.247 | 117 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.017, priority_weight=1.50) |

## Failed or violating executions

| agent | step | purpose | arch | exit | violation | quality | stderr |
|---|---|---|---|---|---|---|---|
| fixed | 1 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 2 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 3 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 4 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |

All executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.
