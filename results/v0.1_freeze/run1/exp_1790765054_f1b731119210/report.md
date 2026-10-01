# Experiment report: cross_domain_001_domain_a_network

- id: `exp_1790765054_f1b731119210`  seed: 101  executor: docker  git: `5f0c37881a8f`  manifest: `96daa220129fad11`
- task: anomaly_detection / network (n=2000, noise=0.1, anomaly_rate=0.03)
- target quality: 0.85  executions: 30 (candidate evaluations: 10)

This report lists measurements. It does not declare any agent successful.

## Aggregate metrics per agent

| metric | fixed | adaptive | search | agm_cold |
|---|---|---|---|---|
| quality_mean | 0.16 | 0.96 | 0.9714 | 0.9714 |
| quality_min | 0 | 0.8 | 0.8571 | 0.8571 |
| quality_final | 0 | 1 | 1 | 1 |
| time_to_target_logical_s | — | 10 | 0 | 0 |
| time_to_target_wall_s | — | 0.8 | 6.679 | 1.125 |
| search_time_s | 1.241e-05 | 0.008631 | 6.888 | 1.905 |
| architecture_evaluations | 0 | 0 | 8 | 2 |
| model_calls | 1 | 5 | 13 | 7 |
| tokens | 480 | 2400 | 16200 | 3600 |
| cpu_time_s | 0.1515 | 0.7587 | 2.12 | 0.9976 |
| max_memory_mb | 13.25 | 13 | 12.88 | 12.88 |
| execution_cost | 0.0005 | 0.0025 | 0.0025 | 0.0025 |
| adaptation_cost | 0 | 0 | 0.0145 | 0.001 |
| total_cost | 0.0005 | 0.0025 | 0.017 | 0.0035 |
| constraint_violations | 4 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.2 |
| distinct_architectures | 1 | 2 | 1 | 1 |
| wall_used_s | 0.3762 | 1.79 | 7.986 | 3.523 |

## Resource-normalized comparison

| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |
|---|---|---|---|---|
| fixed | 320 | 1.056 | 0 | 3.298e-05 |
| adaptive | 384 | 1.265 | 0 | 0.004822 |
| search | 57.14 | 0.4583 | 0.8529 | 0.8625 |
| agm_cold | 277.6 | 0.9737 | 0.2857 | 0.5407 |

Pareto front (min total_cost, max quality_mean): fixed, adaptive, agm_cold
Pareto front (min cpu_time_s, max quality_mean): fixed, adaptive, agm_cold

## Quality per step

| agent | t=0 | t=10 | t=20 | t=30 | t=40 |
|---|---|---|---|---|---|
| fixed | 0.8 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) |
| adaptive | 0.8 (standard) | 1 (lightweight) | 1 (lightweight) | 1 (lightweight) | 1 (lightweight) |
| search | 0.8571 (search) | 1 (search) | 1 (search) | 1 (search) | 1 (search) |
| agm_cold | 0.8571 (syn_anom_direc) | 1 (syn_anom_direc) | 1 (syn_anom_direc) | 1 (syn_anom_direc) | 1 (syn_anom_direc) |

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
| agm_cold | 1 | ADAPT | 0.8571 | 0.1429 | 0.003 | 0.0005 | 0.249 | 118.9 | benefit 0.143 > price 0.030 (cost_ratio=0.014, time_ratio=0.016, priority_weight=1.00) |
| agm_cold | 2 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.248 | 117.6 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.018, priority_weight=1.00) |
| agm_cold | 3 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.2475 | 117.2 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.017, priority_weight=1.00) |
| agm_cold | 4 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.247 | 116.8 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.019, priority_weight=1.50) |

## Failed or violating executions

| agent | step | purpose | arch | exit | violation | quality | stderr |
|---|---|---|---|---|---|---|---|
| fixed | 1 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 2 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 3 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 4 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |

All executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.
