# Experiment report: cross_domain_001_domain_a_network

- id: `exp_1790765789_29f743279df1`  seed: 101  executor: docker  git: `5f0c37881a8f`  manifest: `96daa220129fad11`
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
| time_to_target_wall_s | — | 0.643 | 6.497 | 1.1 |
| search_time_s | 1.061e-05 | 0.00735 | 6.648 | 1.771 |
| architecture_evaluations | 0 | 0 | 8 | 2 |
| model_calls | 1 | 5 | 13 | 7 |
| tokens | 480 | 2400 | 16200 | 3600 |
| cpu_time_s | 0.1656 | 0.7604 | 2.158 | 1.024 |
| max_memory_mb | 12.75 | 13 | 12.88 | 13 |
| execution_cost | 0.0005 | 0.0025 | 0.0025 | 0.0025 |
| adaptation_cost | 0 | 0 | 0.0145 | 0.001 |
| total_cost | 0.0005 | 0.0025 | 0.017 | 0.0035 |
| constraint_violations | 4 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.2 |
| distinct_architectures | 1 | 2 | 1 | 1 |
| wall_used_s | 0.3295 | 1.636 | 7.759 | 3.469 |

## Resource-normalized comparison

| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |
|---|---|---|---|---|
| fixed | 320 | 0.9661 | 0 | 3.219e-05 |
| adaptive | 384 | 1.262 | 0 | 0.004491 |
| search | 57.14 | 0.4501 | 0.8529 | 0.8569 |
| agm_cold | 277.6 | 0.9487 | 0.2857 | 0.5105 |

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
| agm_cold | 1 | ADAPT | 0.8571 | 0.1429 | 0.003 | 0.0005 | 0.249 | 118.9 | benefit 0.143 > price 0.029 (cost_ratio=0.014, time_ratio=0.015, priority_weight=1.00) |
| agm_cold | 2 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.248 | 117.8 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.016, priority_weight=1.00) |
| agm_cold | 3 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.2475 | 117.3 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.021, priority_weight=1.00) |
| agm_cold | 4 | DO_NOT_ADAPT | 1 | 0 | 0.003 | 0.0005 | 0.247 | 116.9 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.020, priority_weight=1.50) |

## Failed or violating executions

| agent | step | purpose | arch | exit | violation | quality | stderr |
|---|---|---|---|---|---|---|---|
| fixed | 1 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 2 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 3 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 4 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |

All executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.
