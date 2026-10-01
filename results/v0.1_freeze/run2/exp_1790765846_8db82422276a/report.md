# Experiment report: cross_domain_001_domain_b_scientific

- id: `exp_1790765846_8db82422276a`  seed: 201  executor: docker  git: `5f0c37881a8f`  manifest: `9dabdebf2810d8cc`
- task: scientific_verification / scientific (n=2000, noise=0.1, anomaly_rate=0.03)
- target quality: 0.8  executions: 61 (candidate evaluations: 36)

This report lists measurements. It does not declare any agent successful.

## Aggregate metrics per agent

| metric | fixed | adaptive | search | agm_cold | agm_memory |
|---|---|---|---|---|---|
| quality_mean | 0.08 | 0.7372 | 0.8681 | 0.847 | 0.847 |
| quality_min | 0 | 0.6471 | 0.6667 | 0.6667 | 0.6667 |
| quality_final | 0 | 0.7692 | 1 | 0.9333 | 0.9333 |
| time_to_target_logical_s | — | 20 | 10 | 10 | 10 |
| time_to_target_wall_s | — | 0.9915 | 13.17 | 7.056 | 7.548 |
| search_time_s | 1.312e-05 | 0.01081 | 13.39 | 7.715 | 8.143 |
| architecture_evaluations | 0 | 0 | 16 | 10 | 10 |
| model_calls | 1 | 5 | 21 | 15 | 15 |
| tokens | 480 | 2400 | 23400 | 8400 | 8400 |
| cpu_time_s | 0.1474 | 0.6949 | 3.331 | 2.068 | 2.161 |
| max_memory_mb | 13.12 | 12.88 | 12.88 | 13 | 13.22 |
| execution_cost | 0.0005 | 0.0025 | 0.006 | 0.0025 | 0.0025 |
| adaptation_cost | 0 | 0 | 0.0185 | 0.005 | 0.005 |
| total_cost | 0.0005 | 0.0025 | 0.0245 | 0.0075 | 0.0075 |
| constraint_violations | 4 | 0 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.225 | 0.025 |
| distinct_architectures | 1 | 2 | 2 | 3 | 3 |
| wall_used_s | 0.3071 | 1.725 | 14.12 | 8.915 | 9.282 |

## Resource-normalized comparison

| agent | quality/$ | quality/cpu-s | adaptation overhead (cost) | adaptation overhead (time) |
|---|---|---|---|---|
| fixed | 160 | 0.5428 | 0 | 4.272e-05 |
| adaptive | 294.9 | 1.061 | 0 | 0.006268 |
| search | 35.43 | 0.2606 | 0.7551 | 0.9488 |
| agm_cold | 112.9 | 0.4095 | 0.6667 | 0.8655 |
| agm_memory | 112.9 | 0.392 | 0.6667 | 0.8773 |

Pareto front (min total_cost, max quality_mean): fixed, adaptive, agm_cold, agm_memory, search
Pareto front (min cpu_time_s, max quality_mean): fixed, adaptive, agm_cold, search

## Quality per step

| agent | t=0 | t=10 | t=20 | t=30 | t=40 |
|---|---|---|---|---|---|
| fixed | 0.4 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) | 0 (fixed_fixed) |
| adaptive | 0.6667 (verified) | 0.7143 (lightweight) | 0.8889 (lightweight) | 0.6471 (lightweight) | 0.7692 (lightweight) |
| search | 0.6667 (search) | 1 (search) | 0.9091 (search) | 0.7647 (search) | 1 (search) |
| agm_cold | 0.6667 (syn_cons_direc) | 1 (local) | 0.9474 (local) | 0.6875 (local) | 0.9333 (local) |
| agm_memory | 0.6667 (mem_5d0255) | 1 (local) | 0.9474 (local) | 0.6875 (local) | 0.9333 (local) |

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
| agm_cold | 1 | ADAPT | 0.6667 | 0.1333 | 0.0015 | 0.0005 | 0.2465 | 115.4 | benefit 0.133 > price 0.016 (cost_ratio=0.008, time_ratio=0.008, priority_weight=1.00) |
| agm_memory | 1 | ADAPT | 0.6667 | 0.1333 | 0.0015 | 0.0005 | 0.2465 | 115.1 | benefit 0.133 > price 0.016 (cost_ratio=0.008, time_ratio=0.007, priority_weight=1.00) |
| agm_cold | 2 | DO_NOT_ADAPT | 1 | -0.5556 | 0.0005 | 0.0005 | 0.2445 | 112.9 | target met; expected improvement negligible (cost_ratio=0.004, time_ratio=0.003, priority_weight=1.00) |
| agm_memory | 2 | DO_NOT_ADAPT | 1 | -0.5556 | 0.0005 | 0.0005 | 0.2445 | 112.5 | target met; expected improvement negligible (cost_ratio=0.004, time_ratio=0.003, priority_weight=1.00) |
| agm_cold | 3 | DO_NOT_ADAPT | 0.9474 | -0.5029 | 0.0005 | 0.0005 | 0.244 | 112.6 | target met; expected improvement negligible (cost_ratio=0.004, time_ratio=0.003, priority_weight=1.00) |
| agm_memory | 3 | DO_NOT_ADAPT | 0.9474 | -0.5029 | 0.0005 | 0.0005 | 0.244 | 112.1 | target met; expected improvement negligible (cost_ratio=0.004, time_ratio=0.003, priority_weight=1.00) |
| agm_cold | 4 | ADAPT | 0.6875 | 0.1125 | 0.0005 | 0.0005 | 0.2435 | 112.2 | benefit 0.169 > price 0.007 (cost_ratio=0.004, time_ratio=0.003, priority_weight=1.50) |
| agm_memory | 4 | ADAPT | 0.6875 | 0.1125 | 0.0005 | 0.0005 | 0.2435 | 111.7 | benefit 0.169 > price 0.007 (cost_ratio=0.004, time_ratio=0.003, priority_weight=1.50) |

## Transfer measurements (memory vs cold)

- agm_memory: delta_quality_mean=0, delta_quality_first_step=0, delta_time_to_target_logical_s=0, delta_architecture_evaluations=0, delta_adaptation_cost=0, delta_total_cost=0, cold_reached_target=True, memory_reached_target=True

## Failed or violating executions

| agent | step | purpose | arch | exit | violation | quality | stderr |
|---|---|---|---|---|---|---|---|
| fixed | 1 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 2 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 3 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |
| fixed | 4 | task | 2cf46e3a49f036de | -1 | architecture_invalid_for_environment | 0 | memory_estimate_exceeds_limit:82>80 |

All executions, candidate evaluations and telemetry are inspectable in SQLite and under results/<experiment_id>/.
