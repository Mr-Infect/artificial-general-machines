# Experiment report: cross_domain_001_domain_b_scientific

- id: `exp_1790765081_d2c490e94aab`  seed: 200  executor: docker  git: `5f0c37881a8f`  manifest: `b121d7e83f96f149`
- task: scientific_verification / scientific (n=2000, noise=0.1, anomaly_rate=0.03)
- target quality: 0.8  executions: 69 (candidate evaluations: 44)

This report lists measurements. It does not declare any agent successful.

## Aggregate metrics per agent

| metric | fixed | adaptive | search | agm_cold | agm_memory |
|---|---|---|---|---|---|
| quality_mean | 0.1217 | 0.5682 | 0.5579 | 0.4994 | 0.4994 |
| quality_min | 0 | 0.3846 | 0.3333 | 0.3529 | 0.3529 |
| quality_final | 0 | 0.4444 | 0.4444 | 0.3529 | 0.3529 |
| time_to_target_logical_s | — | — | — | — | — |
| time_to_target_wall_s | — | — | — | — | — |
| search_time_s | 1.391e-05 | 0.007025 | 21.52 | 7.403 | 7.429 |
| architecture_evaluations | 0 | 0 | 26 | 9 | 9 |
| model_calls | 1 | 5 | 31 | 14 | 14 |
| tokens | 480 | 2400 | 29400 | 7800 | 7800 |
| cpu_time_s | 0.1454 | 0.6539 | 4.886 | 1.981 | 1.973 |
| max_memory_mb | 13.12 | 12.75 | 13 | 12.88 | 13 |
| execution_cost | 0.0005 | 0.0025 | 0.006 | 0.0025 | 0.0025 |
| adaptation_cost | 0 | 0 | 0.0235 | 0.0045 | 0.0045 |
| total_cost | 0.0005 | 0.0025 | 0.0295 | 0.007 | 0.007 |
| constraint_violations | 4 | 0 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.2 | 0.0125 |
| distinct_architectures | 1 | 2 | 4 | 1 | 1 |
| wall_used_s | 0.3039 | 1.591 | 21.8 | 8.653 | 8.57 |

## Resource-normalized comparison

| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |
|---|---|---|---|---|
| fixed | 243.5 | 0.8373 | 0 | 4.578e-05 |
| adaptive | 227.3 | 0.869 | 0 | 0.004417 |
| search | 18.91 | 0.1142 | 0.7966 | 0.9874 |
| agm_cold | 71.34 | 0.2521 | 0.6429 | 0.8555 |
| agm_memory | 71.34 | 0.2531 | 0.6429 | 0.8669 |

Pareto front (min total_cost, max quality_mean): fixed, adaptive
Pareto front (min cpu_time_s, max quality_mean): fixed, adaptive

## Quality per step

| agent | t=0 | t=10 | t=20 | t=30 | t=40 |
|---|---|---|---|---|---|
| fixed | 0.6087 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) |
| adaptive | 0.75 (verified) | 0.7619 (lightweight) | 0.5 (lightweight) | 0.3846 (lightweight) | 0.4444 (lightweight) |
| search | 0.75 (search) | 0.7619 (search) | 0.5 (search) | 0.3333 (search) | 0.4444 (search) |
| agm_cold | 0.6957 (syn_cons_direc) | 0.375 (syn_cons_direc) | 0.3636 (syn_cons_direc) | 0.7097 (syn_cons_direc) | 0.3529 (syn_cons_direc) |
| agm_memory | 0.6957 (syn_cons_direc) | 0.375 (syn_cons_direc) | 0.3636 (syn_cons_direc) | 0.7097 (syn_cons_direc) | 0.3529 (syn_cons_direc) |

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
| agm_cold | 1 | ADAPT | 0.6957 | 0.1043 | 0.0015 | 0.0005 | 0.2465 | 115.2 | benefit 0.104 > price 0.015 (cost_ratio=0.008, time_ratio=0.007, priority_weight=1.00) |
| agm_memory | 1 | ADAPT | 0.6957 | 0.1043 | 0.0015 | 0.0005 | 0.2465 | 115.2 | benefit 0.104 > price 0.017 (cost_ratio=0.008, time_ratio=0.009, priority_weight=1.00) |
| agm_cold | 2 | DO_NOT_ADAPT | 0.375 | -0.2417 | 0 | 0 | 0.2445 | 112.5 | benefit 0.000 <= half of price 0.000 (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.00) |
| agm_memory | 2 | DO_NOT_ADAPT | 0.375 | -0.2417 | 0 | 0 | 0.2445 | 112.5 | benefit 0.000 <= half of price 0.000 (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.00) |
| agm_cold | 3 | DO_NOT_ADAPT | 0.3636 | -0.2303 | 0 | 0 | 0.244 | 112.1 | benefit 0.000 <= half of price 0.000 (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.00) |
| agm_memory | 3 | DO_NOT_ADAPT | 0.3636 | -0.2303 | 0 | 0 | 0.244 | 112.2 | benefit 0.000 <= half of price 0.000 (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.00) |
| agm_cold | 4 | DO_NOT_ADAPT | 0.7097 | -0.5763 | 0 | 0 | 0.2435 | 111.8 | benefit 0.000 <= half of price 0.000 (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.50) |
| agm_memory | 4 | DO_NOT_ADAPT | 0.7097 | -0.5763 | 0 | 0 | 0.2435 | 111.8 | benefit 0.000 <= half of price 0.000 (cost_ratio=0.000, time_ratio=0.000, priority_weight=1.50) |

## Transfer measurements (memory vs cold)

- agm_memory: delta_quality_mean=0, delta_quality_first_step=0, delta_time_to_target_logical_s=—, delta_architecture_evaluations=0, delta_adaptation_cost=0, delta_total_cost=0, cold_reached_target=False, memory_reached_target=False

## Failed or violating executions

| agent | step | purpose | arch | exit | violation | quality | stderr |
|---|---|---|---|---|---|---|---|
| fixed | 1 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 2 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 3 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 4 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |

All executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.
