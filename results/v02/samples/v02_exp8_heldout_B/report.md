# Experiment report: v02_exp8_heldout_B

## Hypothesis

Exp 8 held-out conditions in domain B (cpu 0.5, memory 100MB from t=0, noise 0.3, verification cost ×8): cold vs warm memory learned under standard conditions.

## Experimental conditions

- id `exp_1790770058_ec3ee63f9340`, seed 5101, executor process, git `cad9294d4e82`, manifest `339af067117c1b78`
- task {'type': 'scientific_verification', 'domain': 'scientific', 'dataset_size': 2000, 'noise': 0.3, 'anomaly_rate': 0.03, 'verification_required': True, 'priority': 1}
- environment {'cpu': 0.5, 'memory_mb': 100, 'latency_ms': 1500, 'network': True, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 8.0}
- events [{'t': 10.0, 'type': 'memory_reduction', 'params': {'memory_mb': 80}}, {'t': 20.0, 'type': 'network_loss', 'params': {}}, {'t': 20.0, 'type': 'capability_removal', 'params': {'capabilities': ['model:large_reasoner', 'tool:search', 'component:lookahead_planner']}}, {'t': 30.0, 'type': 'latency_reduction', 'params': {'latency_ms': 800}}, {'t': 40.0, 'type': 'priority_increase', 'params': {'priority': 3}}]
- objective quality ≥ 0.0; budget {'max_seconds': 120.0, 'max_cost': 0.25, 'step_timeout_s': 30.0}

## Baselines

- v2_cold: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "economic", "explore_all": false}
- v2_warm_full: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp8_warm_B_1.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp8_warm_B_1.sqlite"}}

## Results

| metric | v2_cold | v2_warm_full |
|---|---|---|
| quality_mean | 0.3522 | 0.3522 |
| quality_min | 0 | 0 |
| quality_final | 0.4516 | 0.4516 |
| time_to_target_logical_s | 10 | 10 |
| architecture_evaluations | 6 | 7 |
| adaptation_cost | 0.003 | 0.0035 |
| execution_cost | 0.0025 | 0.0025 |
| total_cost | 0.0055 | 0.006 |
| cpu_time_s | 0.5265 | 0.5667 |
| max_memory_mb | 132.5 | 132.5 |
| constraint_violations | 5 | 5 |
| failures | 0 | 0 |
| novelty_mean | 0.2 | 0.0125 |
| distinct_architectures | 1 | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- v2_cold: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- v2_warm_full: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 10; completed with a recorded test: 2; principle reuse per agent: {'v2_cold': 0, 'v2_warm_full': 2}

## Adaptation economics

- v2_cold: decisions {'ADAPT': 10}; mean decision error -0.1401
- v2_warm_full: decisions {'ADAPT': 10}; mean decision error -0.2457

## Failures

- failed/refused/violating executions: 23
  - v2_cold step 0 candidate_evaluation 4c11ce0f07f705d9: memory_limit_exceeded:132>100
  - v2_cold step 0 candidate_evaluation 662a48a0041be770: memory_limit_exceeded:132>100
  - v2_cold step 0 task 662a48a0041be770: memory_limit_exceeded:132>100
  - v2_warm_full step 0 candidate_evaluation 4c11ce0f07f705d9: memory_limit_exceeded:132>100
  - v2_warm_full step 0 candidate_evaluation f1166591d0a381d3: memory_limit_exceeded:132>100
  - v2_warm_full step 0 candidate_evaluation 662a48a0041be770: memory_limit_exceeded:132>100
  - v2_warm_full step 0 task 662a48a0041be770: memory_limit_exceeded:132>100
  - v2_cold step 1 candidate_evaluation 8d51da4468988bb6: memory_limit_exceeded:132>80
  - v2_cold step 1 task 662a48a0041be770: memory_limit_exceeded:132>80
  - v2_warm_full step 1 candidate_evaluation 8d51da4468988bb6: memory_limit_exceeded:132>80
  - v2_warm_full step 1 task 662a48a0041be770: memory_limit_exceeded:132>80
  - v2_cold step 2 candidate_evaluation f1166591d0a381d3: memory_limit_exceeded:132>80
  - v2_cold step 2 task 662a48a0041be770: memory_limit_exceeded:132>80
  - v2_warm_full step 2 candidate_evaluation 2868724eec9f7f2d: memory_limit_exceeded:132>80
  - v2_warm_full step 2 task 662a48a0041be770: memory_limit_exceeded:132>80
  - v2_cold step 3 candidate_evaluation 2868724eec9f7f2d: memory_limit_exceeded:132>80
  - v2_cold step 3 task 662a48a0041be770: memory_limit_exceeded:132>80
  - v2_warm_full step 3 candidate_evaluation e57f8da0b84cc1be: memory_limit_exceeded:132>80
  - v2_warm_full step 3 task 662a48a0041be770: memory_limit_exceeded:132>80
  - v2_cold step 4 candidate_evaluation e57f8da0b84cc1be: memory_limit_exceeded:132>80
- rejected architectures: {'v2_cold': 403, 'v2_warm_full': 403}
- contradicted principles: {'v2_cold': 0, 'v2_warm_full': 2}

## Counterexamples

- lowest per-step quality per agent: v2_cold 0.000, v2_warm_full 0.000

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['v2_cold']; dominated = ['v2_warm_full']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'v2_cold': '117.4', 'v2_warm_full': '100.6'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['v2_cold', 'v2_warm_full']. Agents with zero failures: ['v2_cold', 'v2_warm_full'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
