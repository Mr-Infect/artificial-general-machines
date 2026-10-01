# Experiment report: cross_domain_001_domain_b_scientific

- id: `exp_1790765137_917b5b7decc3`  seed: 202  executor: docker  git: `5f0c37881a8f`  manifest: `348ca2f50abd2828`
- task: scientific_verification / scientific (n=2000, noise=0.1, anomaly_rate=0.03)
- target quality: 0.8  executions: 67 (candidate evaluations: 42)

This report lists measurements. It does not declare any agent successful.

## Aggregate metrics per agent

| metric | fixed | adaptive | search | agm_cold | agm_memory |
|---|---|---|---|---|---|
| quality_mean | 0.1793 | 0.6677 | 0.7134 | 0.711 | 0.6667 |
| quality_min | 0 | 0.4 | 0.4706 | 0.4 | 0.4 |
| quality_final | 0 | 0.4 | 0.5 | 0.4 | 0.4 |
| time_to_target_logical_s | 0 | 0 | 0 | 0 | 0 |
| time_to_target_wall_s | 0.3159 | 0.2986 | 6.614 | 4.926 | 4.839 |
| search_time_s | 8.503e-06 | 0.007722 | 17.06 | 7.765 | 9.915 |
| architecture_evaluations | 0 | 0 | 21 | 9 | 12 |
| model_calls | 1 | 5 | 26 | 14 | 17 |
| tokens | 480 | 2400 | 29400 | 7800 | 9600 |
| cpu_time_s | 0.1499 | 0.7273 | 4.08 | 2.059 | 2.433 |
| max_memory_mb | 12.62 | 13 | 12.88 | 12.88 | 13.12 |
| execution_cost | 0.0005 | 0.0025 | 0.006 | 0.0025 | 0.0025 |
| adaptation_cost | 0 | 0 | 0.0245 | 0.0045 | 0.006 |
| total_cost | 0.0005 | 0.0025 | 0.0305 | 0.007 | 0.0085 |
| constraint_violations | 4 | 0 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.2125 | 0.04583 |
| distinct_architectures | 1 | 2 | 3 | 2 | 2 |
| wall_used_s | 0.3159 | 1.862 | 17.64 | 8.936 | 10.88 |

## Resource-normalized comparison

| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |
|---|---|---|---|---|
| fixed | 358.6 | 1.196 | 0 | 2.691e-05 |
| adaptive | 267.1 | 0.918 | 0 | 0.004148 |
| search | 23.39 | 0.1748 | 0.8033 | 0.9671 |
| agm_cold | 101.6 | 0.3454 | 0.6429 | 0.869 |
| agm_memory | 78.43 | 0.274 | 0.7059 | 0.9113 |

Pareto front (min total_cost, max quality_mean): fixed, adaptive, agm_cold, search
Pareto front (min cpu_time_s, max quality_mean): fixed, adaptive, agm_cold, search

## Quality per step

| agent | t=0 | t=10 | t=20 | t=30 | t=40 |
|---|---|---|---|---|---|
| fixed | 0.8966 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) |
| adaptive | 0.9677 (verified) | 0.5 (lightweight) | 0.4706 (lightweight) | 1 (lightweight) | 0.4 (lightweight) |
| search | 0.9677 (search) | 0.6286 (search) | 0.4706 (search) | 1 (search) | 0.5 (search) |
| agm_cold | 0.9677 (syn_anom+cons+) | 0.6875 (syn_anom+cons+) | 0.5 (syn_anom+cons+) | 1 (syn_anom+cons+) | 0.4 (syn_anom+cons+) |
| agm_memory | 0.9333 (mem_87d1f5) | 0.5 (mem_87d1f5) | 0.5 (syn_anom+cons+) | 1 (syn_anom+cons+) | 0.4 (syn_anom+cons+) |

## Environment transitions

- t=10: memory_reduction {'memory_mb': 80} → memory=80MB cpu=1.0 network=True latency=2000ms priority=1 caps=27
- t=20: network_loss {} → memory=80MB cpu=1.0 network=False latency=2000ms priority=1 caps=27
- t=20: capability_removal {'capabilities': ['model:large_reasoner', 'tool:search']} → memory=80MB cpu=1.0 network=False latency=2000ms priority=1 caps=25
- t=30: latency_reduction {'latency_ms': 800} → memory=80MB cpu=1.0 network=False latency=800ms priority=1 caps=25
- t=40: priority_increase {'priority': 3} → memory=80MB cpu=1.0 network=False latency=800ms priority=3 caps=25

## Adaptation decisions

| agent | step | outcome | expected_quality | expected_improvement | search_cost | validation_cost | budget_remaining | deadline_remaining_s | rationale |
|---|---|---|---|---|---|---|---|---|---|
| agm_cold | 0 | ADAPT | 0 | 0.8 | 0.003 | 0.0005 | 0.25 | 120 | current architecture invalid under environment (cost_ratio=0.014, time_ratio=0.025, priority_weight=1.00) |
| agm_memory | 0 | ADAPT | 0 | 0.8 | 0.003 | 0.0005 | 0.25 | 120 | current architecture invalid under environment (cost_ratio=0.014, time_ratio=0.025, priority_weight=1.00) |
| agm_cold | 1 | ADAPT | 0 | 0.8 | 0.0005 | 0.0005 | 0.2465 | 115.1 | current architecture invalid under environment (cost_ratio=0.004, time_ratio=0.003, priority_weight=1.00) |
| agm_memory | 1 | DO_NOT_ADAPT | 0.9333 | -0.3126 | 0.002 | 0.0005 | 0.2465 | 115.2 | target met; expected improvement negligible (cost_ratio=0.010, time_ratio=0.014, priority_weight=1.00) |
| agm_cold | 2 | ADAPT | 0.6875 | 0.1125 | 0.001 | 0.0005 | 0.2455 | 113.8 | benefit 0.113 > price 0.012 (cost_ratio=0.006, time_ratio=0.006, priority_weight=1.00) |
| agm_memory | 2 | ADAPT | 0.5 | 0.3 | 0.002 | 0.0005 | 0.246 | 114.8 | benefit 0.300 > price 0.021 (cost_ratio=0.010, time_ratio=0.011, priority_weight=1.00) |
| agm_cold | 3 | ADAPT | 0.5 | 0.1897 | 0 | 0 | 0.244 | 111.8 | benefit 0.190 > price 0.000 (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.00) |
| agm_memory | 3 | ADAPT | 0.5 | 0.3 | 0.001 | 0.0005 | 0.2435 | 111.4 | benefit 0.300 > price 0.012 (cost_ratio=0.006, time_ratio=0.005, priority_weight=1.00) |
| agm_cold | 4 | DO_NOT_ADAPT | 1 | -0.3103 | 0 | 0 | 0.2435 | 111.4 | target met; expected improvement negligible (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.50) |
| agm_memory | 4 | DO_NOT_ADAPT | 1 | -0.3103 | 0 | 0 | 0.242 | 109.5 | target met; expected improvement negligible (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.50) |

## Transfer measurements (memory vs cold)

- agm_memory: delta_quality_mean=-0.04438, delta_quality_first_step=-0.03441, delta_time_to_target_logical_s=0, delta_architecture_evaluations=3, delta_adaptation_cost=0.0015, delta_total_cost=0.0015, cold_reached_target=True, memory_reached_target=True

## Failed or violating executions

| agent | step | purpose | arch | exit | violation | quality | stderr |
|---|---|---|---|---|---|---|---|
| fixed | 1 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 2 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 3 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 4 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |

All executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.
