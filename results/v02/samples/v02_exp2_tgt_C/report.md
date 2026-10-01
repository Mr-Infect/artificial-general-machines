# Experiment report: v02_exp2_tgt_C

## Hypothesis

Exp 2/3/4/5/7 target run in domain C: cold vs transferred memory (from each other domain and merged), memory-mode and economics ablations, AGM v0.1 with warm architecture memory.

## Experimental conditions

- id `exp_1790770106_d09ce7afe68a`, seed 4201, executor process, git `cad9294d4e82`, manifest `eb8ac1f11a817b57`
- task {'type': 'resource_planning', 'domain': 'planning', 'dataset_size': 2000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': True, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events [{'t': 10.0, 'type': 'memory_reduction', 'params': {'memory_mb': 80}}, {'t': 20.0, 'type': 'network_loss', 'params': {}}, {'t': 20.0, 'type': 'capability_removal', 'params': {'capabilities': ['model:large_reasoner', 'tool:search', 'component:lookahead_planner']}}, {'t': 30.0, 'type': 'latency_reduction', 'params': {'latency_ms': 800}}, {'t': 40.0, 'type': 'priority_increase', 'params': {'priority': 3}}]
- objective quality ≥ 0.0; budget {'max_seconds': 120.0, 'max_cost': 0.25, 'step_timeout_s': 30.0}

## Baselines

- v2_cold: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "economic", "explore_all": false}
- v2_from_A: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_A_to_C_1.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_A_to_C_1.sqlite"}}
- v2_from_B: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_B_to_C_1.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_B_to_C_1.sqlite"}}
- v2_warm_full: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_full.sqlite"}}
- v2_warm_architecture: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_architecture.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_architecture.sqlite"}}
- v2_warm_principle: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "principle", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_principle.sqlite"}}
- v2_warm_task: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_task.sqlite"}}
- v2_always_adapt: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "always_adapt", "explore_all": false}
- v2_never_adapt: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "never_adapt", "explore_all": false}
- v1_warm_architecture: {"type": "agm", "max_evaluations": 6, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_C_1_v1.sqlite"}}

## Results

| metric | v2_cold | v2_from_A | v2_from_B | v2_warm_full | v2_warm_architecture | v2_warm_principle | v2_warm_task | v2_always_adapt | v2_never_adapt | v1_warm_architecture |
|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.7587 | 0.7587 | 0.7587 | 0.7587 | 0.7587 | 0.7587 | 0.7587 | 0.7587 | 0.7587 | 0.7587 |
| quality_min | 0.6616 | 0.6616 | 0.6616 | 0.6616 | 0.6616 | 0.6616 | 0.6616 | 0.6616 | 0.6616 | 0.6616 |
| quality_final | 0.8064 | 0.8064 | 0.8064 | 0.8064 | 0.8064 | 0.8064 | 0.8064 | 0.8064 | 0.8064 | 0.8064 |
| time_to_target_logical_s | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| architecture_evaluations | 27 | 28 | 28 | 29 | 27 | 29 | 27 | 27 | 9 | 8 |
| adaptation_cost | 0.0135 | 0.014 | 0.014 | 0.0145 | 0.0135 | 0.0145 | 0.0135 | 0.0135 | 0.0045 | 0.004 |
| execution_cost | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 |
| total_cost | 0.016 | 0.0165 | 0.0165 | 0.017 | 0.016 | 0.017 | 0.016 | 0.016 | 0.007 | 0.0065 |
| cpu_time_s | 1.354 | 1.399 | 1.442 | 1.358 | 1.255 | 1.461 | 1.388 | 1.267 | 0.561 | 0.5168 |
| max_memory_mb | 131.5 | 131.5 | 131.5 | 131.5 | 131.5 | 131.5 | 131.5 | 131.5 | 131.5 | 131.5 |
| constraint_violations | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0.2125 | 0.025 | 0.0625 | 0.025 | 0.025 | 0.025 | 0.025 | 0.2125 | 0.2125 | 0.025 |
| distinct_architectures | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- v2_cold: A-003 (Δprev 0.00) → A-001 (Δprev 0.30) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_from_A: A-004 (Δprev 0.00) → A-002 (Δprev 0.30) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- v2_from_B: A-004 (Δprev 0.00) → A-002 (Δprev 0.30) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- v2_warm_full: A-005 (Δprev 0.00) → A-003 (Δprev 0.30) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00)
- v2_warm_architecture: A-003 (Δprev 0.00) → A-001 (Δprev 0.30) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_warm_principle: A-005 (Δprev 0.00) → A-003 (Δprev 0.30) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00)
- v2_warm_task: A-003 (Δprev 0.00) → A-001 (Δprev 0.30) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_always_adapt: A-003 (Δprev 0.00) → A-001 (Δprev 0.30) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_never_adapt: A-003 (Δprev 0.00) → A-001 (Δprev 0.30) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v1_warm_architecture: A-003 (Δprev 0.00) → A-001 (Δprev 0.30) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 30; completed with a recorded test: 9; principle reuse per agent: {'v2_cold': 0, 'v2_from_A': 1, 'v2_from_B': 2, 'v2_warm_full': 3, 'v2_warm_architecture': 0, 'v2_warm_principle': 3, 'v2_warm_task': 0, 'v2_always_adapt': 0, 'v2_never_adapt': 0, 'v1_warm_architecture': None}

## Adaptation economics

- v2_cold: decisions {'ADAPT': 10}; mean decision error -0.1076
- v2_from_A: decisions {'ADAPT': 10}; mean decision error -0.1062
- v2_from_B: decisions {'ADAPT': 10}; mean decision error -0.1106
- v2_warm_full: decisions {'ADAPT': 10}; mean decision error -0.1099
- v2_warm_architecture: decisions {'ADAPT': 10}; mean decision error -0.106
- v2_warm_principle: decisions {'ADAPT': 10}; mean decision error -0.111
- v2_warm_task: decisions {'ADAPT': 10}; mean decision error -0.1089
- v2_always_adapt: decisions {'ADAPT': 10}; mean decision error -0.1067
- v2_never_adapt: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.09243

## Failures

- failed/refused/violating executions: 243
  - v2_cold step 1 candidate_evaluation 5794dd0dc20065bd: memory_limit_exceeded:131>80
  - v2_cold step 1 candidate_evaluation de57420906cd01f2: memory_limit_exceeded:131>80
  - v2_cold step 1 candidate_evaluation 3f1ec0961a0481b0: memory_limit_exceeded:131>80
  - v2_cold step 1 candidate_evaluation bfa2536b6df9e14d: memory_limit_exceeded:131>80
  - v2_cold step 1 candidate_evaluation a1c035998e3d5b77: memory_limit_exceeded:131>80
  - v2_cold step 1 candidate_evaluation 4c9be35575d29ef7: memory_limit_exceeded:131>80
  - v2_cold step 1 task d423cf5ea73f7153: memory_limit_exceeded:131>80
  - v2_from_A step 1 candidate_evaluation 5794dd0dc20065bd: memory_limit_exceeded:131>80
  - v2_from_A step 1 candidate_evaluation 3f1ec0961a0481b0: memory_limit_exceeded:131>80
  - v2_from_A step 1 candidate_evaluation bfa2536b6df9e14d: memory_limit_exceeded:131>80
  - v2_from_A step 1 candidate_evaluation a1c035998e3d5b77: memory_limit_exceeded:131>80
  - v2_from_A step 1 candidate_evaluation 4c9be35575d29ef7: memory_limit_exceeded:131>80
  - v2_from_A step 1 candidate_evaluation 6a7f9704b56583a7: memory_limit_exceeded:131>80
  - v2_from_A step 1 task d423cf5ea73f7153: memory_limit_exceeded:131>80
  - v2_from_B step 1 candidate_evaluation 3adaa84ac717db89: memory_limit_exceeded:131>80
  - v2_from_B step 1 candidate_evaluation 5794dd0dc20065bd: memory_limit_exceeded:131>80
  - v2_from_B step 1 candidate_evaluation de57420906cd01f2: memory_limit_exceeded:131>80
  - v2_from_B step 1 candidate_evaluation 3f1ec0961a0481b0: memory_limit_exceeded:131>80
  - v2_from_B step 1 candidate_evaluation bfa2536b6df9e14d: memory_limit_exceeded:131>80
  - v2_from_B step 1 candidate_evaluation a1c035998e3d5b77: memory_limit_exceeded:131>80
- rejected architectures: {'v2_cold': 426, 'v2_from_A': 426, 'v2_from_B': 430, 'v2_warm_full': 430, 'v2_warm_architecture': 426, 'v2_warm_principle': 430, 'v2_warm_task': 426, 'v2_always_adapt': 426, 'v2_never_adapt': 429, 'v1_warm_architecture': 0}
- contradicted principles: {'v2_cold': 0, 'v2_from_A': 1, 'v2_from_B': 1, 'v2_warm_full': 2, 'v2_warm_architecture': 0, 'v2_warm_principle': 2, 'v2_warm_task': 0, 'v2_always_adapt': 0, 'v2_never_adapt': 0, 'v1_warm_architecture': 0}

## Counterexamples

- lowest per-step quality per agent: v2_cold 0.662, v2_from_A 0.662, v2_from_B 0.662, v2_warm_full 0.662, v2_warm_architecture 0.662, v2_warm_principle 0.662, v2_warm_task 0.662, v2_always_adapt 0.662, v2_never_adapt 0.662, v1_warm_architecture 0.662

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['v2_warm_architecture', 'v2_never_adapt', 'v1_warm_architecture']; dominated = ['v2_cold', 'v2_from_A', 'v2_from_B', 'v2_warm_full', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'v2_cold': '56.2', 'v2_from_A': '54.2', 'v2_from_B': '54.2', 'v2_warm_full': '52.33', 'v2_warm_architecture': '56.2', 'v2_warm_principle': '52.33', 'v2_warm_task': '56.2', 'v2_always_adapt': '56.2', 'v2_never_adapt': '168.6', 'v1_warm_architecture': '189.7'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['v2_cold', 'v2_from_A', 'v2_from_B', 'v2_warm_full', 'v2_warm_architecture', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt', 'v2_never_adapt', 'v1_warm_architecture']. Agents with zero failures: ['v2_cold', 'v2_from_A', 'v2_from_B', 'v2_warm_full', 'v2_warm_architecture', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt', 'v2_never_adapt', 'v1_warm_architecture'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
