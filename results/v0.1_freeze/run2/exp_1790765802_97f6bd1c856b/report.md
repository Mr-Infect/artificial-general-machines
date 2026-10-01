# Experiment report: cross_domain_001_domain_a_network

- id: `exp_1790765802_97f6bd1c856b`  seed: 102  executor: docker  git: `5f0c37881a8f`  manifest: `ccf71bbd3fa01517`
- task: anomaly_detection / network (n=2000, noise=0.1, anomaly_rate=0.03)
- target quality: 0.85  executions: 30 (candidate evaluations: 10)

This report lists measurements. It does not declare any agent successful.

## Aggregate metrics per agent

| metric | fixed | adaptive | search | agm_cold |
|---|---|---|---|---|
| quality_mean | 0.1684 | 0.9163 | 0.8512 | 0.9479 |
| quality_min | 0 | 0.8421 | 0.6154 | 0.8571 |
| quality_final | 0 | 0.9412 | 1 | 0.9412 |
| time_to_target_logical_s | — | 10 | 10 | 0 |
| time_to_target_wall_s | — | 0.6276 | 6.668 | 1.068 |
| search_time_s | 1.96e-05 | 0.01005 | 6.5 | 1.665 |
| architecture_evaluations | 0 | 0 | 8 | 2 |
| model_calls | 1 | 5 | 13 | 7 |
| tokens | 480 | 2400 | 16200 | 3600 |
| cpu_time_s | 0.1461 | 0.7166 | 2.006 | 0.9814 |
| max_memory_mb | 12.62 | 13 | 13 | 13 |
| execution_cost | 0.0005 | 0.0025 | 0.0025 | 0.0025 |
| adaptation_cost | 0 | 0 | 0.0145 | 0.001 |
| total_cost | 0.0005 | 0.0025 | 0.017 | 0.0035 |
| constraint_violations | 4 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.2 |
| distinct_architectures | 1 | 2 | 1 | 1 |
| wall_used_s | 0.3217 | 1.737 | 7.702 | 3.319 |

## Resource-normalized comparison

| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |
|---|---|---|---|---|
| fixed | 336.8 | 1.153 | 0 | 6.093e-05 |
| adaptive | 366.5 | 1.279 | 0 | 0.005787 |
| search | 50.07 | 0.4242 | 0.8529 | 0.8439 |
| agm_cold | 270.8 | 0.9659 | 0.2857 | 0.5016 |

Pareto front (min total_cost, max quality_mean): fixed, adaptive, agm_cold
Pareto front (min cpu_time_s, max quality_mean): fixed, adaptive, agm_cold

## Quality per step

| agent | t=0 | t=10 | t=20 | t=30 | t=40 |
|---|---|---|---|---|---|
| fixed | 0.8421 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) |
| adaptive | 0.8421 (standard) | 1 (lightweight) | 0.8571 (lightweight) | 0.9412 (lightweight) | 0.9412 (lightweight) |
| search | 0.6154 (search) | 1 (search) | 0.9 (search) | 0.7407 (search) | 1 (search) |
| agm_cold | 1 (syn_anom_direc) | 1 (syn_anom_direc) | 0.8571 (syn_anom_direc) | 0.9412 (syn_anom_direc) | 0.9412 (syn_anom_direc) |

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
| agm_cold | 1 | DO_NOT_ADAPT | 1 | -0.06667 | 0.003 | 0.0005 | 0.249 | 118.9 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.019, priority_weight=1.00) |
| agm_cold | 2 | DO_NOT_ADAPT | 1 | -0.06667 | 0.003 | 0.0005 | 0.2485 | 118.5 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.018, priority_weight=1.00) |
| agm_cold | 3 | ADAPT | 0.8571 | 0.07619 | 0.003 | 0.0005 | 0.248 | 118.1 | benefit 0.076 > price 0.034 (cost_ratio=0.014, time_ratio=0.020, priority_weight=1.00) |
| agm_cold | 4 | DO_NOT_ADAPT | 0.9412 | -0.007843 | 0.003 | 0.0005 | 0.247 | 117 | target met; expected improvement negligible (cost_ratio=0.014, time_ratio=0.016, priority_weight=1.50) |

## Failed or violating executions

| agent | step | purpose | arch | exit | violation | quality | stderr |
|---|---|---|---|---|---|---|---|
| fixed | 1 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 2 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 3 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 4 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |

All executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.
