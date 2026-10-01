# Experiment report: v02_exp2_tgt_B

## Hypothesis

Exp 2/3/4/5/7 target run in domain B: cold vs transferred memory (from each other domain and merged), memory-mode and economics ablations, AGM v0.1 with warm architecture memory.

## Experimental conditions

- id `exp_1790769921_cd06b7a861c9`, seed 4100, executor process, git `cad9294d4e82`, manifest `6881eb4dc2ef70c4`
- task {'type': 'scientific_verification', 'domain': 'scientific', 'dataset_size': 2000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': True, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': True, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events [{'t': 10.0, 'type': 'memory_reduction', 'params': {'memory_mb': 80}}, {'t': 20.0, 'type': 'network_loss', 'params': {}}, {'t': 20.0, 'type': 'capability_removal', 'params': {'capabilities': ['model:large_reasoner', 'tool:search', 'component:lookahead_planner']}}, {'t': 30.0, 'type': 'latency_reduction', 'params': {'latency_ms': 800}}, {'t': 40.0, 'type': 'priority_increase', 'params': {'priority': 3}}]
- objective quality ≥ 0.0; budget {'max_seconds': 120.0, 'max_cost': 0.25, 'step_timeout_s': 30.0}

## Baselines

- v2_cold: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "economic", "explore_all": false}
- v2_from_A: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_A_to_B_0.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_A_to_B_0.sqlite"}}
- v2_from_C: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_C_to_B_0.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_C_to_B_0.sqlite"}}
- v2_warm_full: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_full.sqlite"}}
- v2_warm_architecture: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_architecture.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_architecture.sqlite"}}
- v2_warm_principle: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "principle", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_principle.sqlite"}}
- v2_warm_task: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_task.sqlite"}}
- v2_always_adapt: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "always_adapt", "explore_all": false}
- v2_never_adapt: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "never_adapt", "explore_all": false}
- v1_warm_architecture: {"type": "agm", "max_evaluations": 6, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_B_0_v1.sqlite"}}

## Results

| metric | v2_cold | v2_from_A | v2_from_C | v2_warm_full | v2_warm_architecture | v2_warm_principle | v2_warm_task | v2_always_adapt | v2_never_adapt | v1_warm_architecture |
|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.6251 | 0.6251 | 0.6251 | 0.6251 | 0.6251 | 0.6251 | 0.6251 | 0.6251 | 0.6251 | 0.6251 |
| quality_min | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 |
| quality_final | 0.6364 | 0.6364 | 0.6364 | 0.6364 | 0.6364 | 0.6364 | 0.6364 | 0.6364 | 0.6364 | 0.6364 |
| time_to_target_logical_s | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 20 |
| architecture_evaluations | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 6 | 9 |
| adaptation_cost | 0.015 | 0.015 | 0.015 | 0.015 | 0.015 | 0.015 | 0.015 | 0.015 | 0.003 | 0.0045 |
| execution_cost | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 |
| total_cost | 0.0175 | 0.0175 | 0.0175 | 0.0175 | 0.0175 | 0.0175 | 0.0175 | 0.0175 | 0.0055 | 0.007 |
| cpu_time_s | 2.114 | 2.008 | 2.034 | 2.077 | 1.976 | 2.029 | 2.01 | 2.104 | 0.5757 | 0.7311 |
| max_memory_mb | 125.9 | 125.9 | 124.9 | 124.9 | 124.9 | 124.9 | 124.9 | 124.9 | 124.9 | 124.9 |
| constraint_violations | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0.2 | 0 | 0.0125 | 0 | 0 | 0 | 0 | 0.2 | 0.2 | 0 |
| distinct_architectures | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- v2_cold: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_from_A: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_from_C: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_warm_full: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_warm_architecture: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_warm_principle: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_warm_task: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_always_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_never_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v1_warm_architecture: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 0; completed with a recorded test: 0; principle reuse per agent: {'v2_cold': 0, 'v2_from_A': 0, 'v2_from_C': 0, 'v2_warm_full': 0, 'v2_warm_architecture': 0, 'v2_warm_principle': 0, 'v2_warm_task': 0, 'v2_always_adapt': 0, 'v2_never_adapt': 0, 'v1_warm_architecture': None}

## Adaptation economics

- v2_cold: decisions {'ADAPT': 10}; mean decision error -0.2829
- v2_from_A: decisions {'ADAPT': 10}; mean decision error -0.2778
- v2_from_C: decisions {'ADAPT': 10}; mean decision error -0.2771
- v2_warm_full: decisions {'ADAPT': 10}; mean decision error -0.2777
- v2_warm_architecture: decisions {'ADAPT': 10}; mean decision error -0.2776
- v2_warm_principle: decisions {'ADAPT': 10}; mean decision error -0.2786
- v2_warm_task: decisions {'ADAPT': 10}; mean decision error -0.2778
- v2_always_adapt: decisions {'ADAPT': 10}; mean decision error -0.2718
- v2_never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 8}; mean decision error -0.2539

## Failures

- failed/refused/violating executions: 235
  - v2_cold step 1 candidate_evaluation e57f8da0b84cc1be: memory_limit_exceeded:126>80
  - v2_cold step 1 candidate_evaluation 19544cf3f8c29d84: memory_limit_exceeded:126>80
  - v2_cold step 1 candidate_evaluation 720400dc4dabaec9: memory_limit_exceeded:126>80
  - v2_cold step 1 candidate_evaluation e3a7d7c45825ade2: memory_limit_exceeded:126>80
  - v2_cold step 1 candidate_evaluation ee9196401165483b: memory_limit_exceeded:126>80
  - v2_cold step 1 candidate_evaluation c9f23cf55c320997: memory_limit_exceeded:126>80
  - v2_cold step 1 task 4c11ce0f07f705d9: memory_limit_exceeded:126>80
  - v2_from_A step 1 candidate_evaluation e57f8da0b84cc1be: memory_limit_exceeded:126>80
  - v2_from_A step 1 candidate_evaluation 19544cf3f8c29d84: memory_limit_exceeded:126>80
  - v2_from_A step 1 candidate_evaluation 720400dc4dabaec9: memory_limit_exceeded:126>80
  - v2_from_A step 1 candidate_evaluation e3a7d7c45825ade2: memory_limit_exceeded:126>80
  - v2_from_A step 1 candidate_evaluation ee9196401165483b: memory_limit_exceeded:126>80
  - v2_from_A step 1 candidate_evaluation c9f23cf55c320997: memory_limit_exceeded:126>80
  - v2_from_A step 1 task 4c11ce0f07f705d9: memory_limit_exceeded:126>80
  - v2_from_C step 1 candidate_evaluation e57f8da0b84cc1be: memory_limit_exceeded:125>80
  - v2_from_C step 1 candidate_evaluation 19544cf3f8c29d84: memory_limit_exceeded:125>80
  - v2_from_C step 1 candidate_evaluation 720400dc4dabaec9: memory_limit_exceeded:125>80
  - v2_from_C step 1 candidate_evaluation e3a7d7c45825ade2: memory_limit_exceeded:125>80
  - v2_from_C step 1 candidate_evaluation ee9196401165483b: memory_limit_exceeded:125>80
  - v2_from_C step 1 candidate_evaluation c9f23cf55c320997: memory_limit_exceeded:125>80
- rejected architectures: {'v2_cold': 524, 'v2_from_A': 524, 'v2_from_C': 524, 'v2_warm_full': 524, 'v2_warm_architecture': 524, 'v2_warm_principle': 524, 'v2_warm_task': 524, 'v2_always_adapt': 524, 'v2_never_adapt': 528, 'v1_warm_architecture': 0}
- contradicted principles: {'v2_cold': 0, 'v2_from_A': 0, 'v2_from_C': 0, 'v2_warm_full': 0, 'v2_warm_architecture': 0, 'v2_warm_principle': 0, 'v2_warm_task': 0, 'v2_always_adapt': 0, 'v2_never_adapt': 0, 'v1_warm_architecture': 0}

## Counterexamples

- lowest per-step quality per agent: v2_cold 0.200, v2_from_A 0.200, v2_from_C 0.200, v2_warm_full 0.200, v2_warm_architecture 0.200, v2_warm_principle 0.200, v2_warm_task 0.200, v2_always_adapt 0.200, v2_never_adapt 0.200, v1_warm_architecture 0.200

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['v2_from_A', 'v2_warm_architecture', 'v2_never_adapt', 'v1_warm_architecture']; dominated = ['v2_cold', 'v2_from_C', 'v2_warm_full', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'v2_cold': '41.67', 'v2_from_A': '41.67', 'v2_from_C': '41.67', 'v2_warm_full': '41.67', 'v2_warm_architecture': '41.67', 'v2_warm_principle': '41.67', 'v2_warm_task': '41.67', 'v2_always_adapt': '41.67', 'v2_never_adapt': '208.4', 'v1_warm_architecture': '138.9'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['v2_cold', 'v2_from_A', 'v2_from_C', 'v2_warm_full', 'v2_warm_architecture', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt', 'v2_never_adapt', 'v1_warm_architecture']. Agents with zero failures: ['v2_cold', 'v2_from_A', 'v2_from_C', 'v2_warm_full', 'v2_warm_architecture', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt', 'v2_never_adapt', 'v1_warm_architecture'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
