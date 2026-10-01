# Experiment report: v03_Y_allocation

## Hypothesis

v0.3 blind-transfer environment allocation with held-out regime combinations; all agents, memory from the training runs of the same seed.

## Experimental conditions

- id `exp_1790783003_b8ee03055f1b`, seed 20202, executor process, git `32e0a66326c4`, manifest `a28d0ce2edf2a3b5`
- task {'type': 'resource_planning', 'domain': 'allocation', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["request_ranker", "risk_weighting", "admission_check"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive", "library": "roles"}
- search: {"type": "search", "space": "auto", "max_evaluations": 6}
- task_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_task.sqlite"}}
- architecture_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_arch.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_arch.sqlite"}}
- always_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt"}
- never_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "never_adapt"}
- agm_cold: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false}
- agm_full: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_full.sqlite"}}
- agm_no_principle: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_principles": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_principle.sqlite"}}
- agm_no_archmem: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_archmem": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_archmem.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_archmem.sqlite"}}
- agm_no_negative: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_negative": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_negative.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_negative.sqlite"}}
- agm_no_economics: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_economics.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_economics.sqlite"}}
- agm_no_regime: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "regime_detection": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_regime.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/allocation_2_no_regime.sqlite"}}

## Results

| metric | fixed | adaptive | search | task_memory | architecture_memory | always_adapt | never_adapt | agm_cold | agm_full | agm_no_principle | agm_no_archmem | agm_no_negative | agm_no_economics | agm_no_regime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.724 | 0.5562 | 0.7142 | 0.7964 | 0.7964 | 0.7298 | 0.7964 | 0.7964 | 0.7411 | 0.7964 | 0.7411 | 0.7522 | 0.7411 | 0.7411 |
| quality_min | 0.6141 | 0.388 | 0.6117 | 0.7135 | 0.7135 | 0.6031 | 0.7135 | 0.7135 | 0.6031 | 0.7135 | 0.6031 | 0.6976 | 0.6031 | 0.6031 |
| quality_final | 0.708 | 0.495 | 0.6999 | 0.7185 | 0.7185 | 0.6974 | 0.7185 | 0.7185 | 0.6974 | 0.7185 | 0.6974 | 0.7007 | 0.6974 | 0.6974 |
| time_to_target_logical_s | — | — | — | 0 | 0 | 0 | 0 | 0 | — | 0 | — | 0 | — | — |
| architecture_evaluations | 0 | 0 | 25 | 23 | 23 | 33 | 6 | 23 | 33 | 23 | 33 | 33 | 33 | 33 |
| adaptation_cost | 0 | 0 | 0.0425 | 0.0115 | 0.0115 | 0.0165 | 0.003 | 0.0115 | 0.0165 | 0.0115 | 0.0165 | 0.0165 | 0.0165 | 0.0165 |
| execution_cost | 0.0045 | 0.0045 | 0.0195 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 |
| total_cost | 0.0045 | 0.0045 | 0.062 | 0.016 | 0.016 | 0.021 | 0.0075 | 0.016 | 0.021 | 0.016 | 0.021 | 0.021 | 0.021 | 0.021 |
| cpu_time_s | 0.4417 | 0.44 | 2.328 | 1.812 | 1.746 | 2.203 | 0.8841 | 1.861 | 2.293 | 1.843 | 2.25 | 2.24 | 2.315 | 2.241 |
| max_memory_mb | 285.8 | 268 | 268 | 268 | 268 | 268 | 268 | 268 | 268 | 268 | 268 | 268 | 268 | 268 |
| constraint_violations | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0.1418 | 0.1586 | 0.03472 | 0.03472 | 0.1713 | 0.1111 | 0.1389 | 0.03935 | 0.03472 | 0.03935 | 0.02778 | 0.03935 | 0.03935 |
| distinct_architectures | 1 | 3 | 4 | 5 | 5 | 5 | 1 | 5 | 4 | 5 | 4 | 3 | 4 | 4 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-003 (Δprev 0.60) → A-002 (Δprev 0.60) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- search: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-011 (Δprev 0.63) → A-011 (Δprev 0.00) → A-012 (Δprev 0.45) → A-012 (Δprev 0.00) → A-012 (Δprev 0.00) → A-012 (Δprev 0.00) → A-013 (Δprev 0.50)
- task_memory: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-258 (Δprev 0.00) → A-260 (Δprev 0.00) → A-261 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00)
- architecture_memory: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-258 (Δprev 0.00) → A-260 (Δprev 0.00) → A-261 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00)
- always_adapt: A-003 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-017 (Δprev 0.45) → A-022 (Δprev 0.90) → A-032 (Δprev 0.35) → A-032 (Δprev 0.00) → A-032 (Δprev 0.00) → A-032 (Δprev 0.00)
- never_adapt: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00)
- agm_cold: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-258 (Δprev 0.00) → A-260 (Δprev 0.00) → A-261 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00)
- agm_full: A-001 (Δprev 0.00) → A-008 (Δprev 0.75) → A-008 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-033 (Δprev 0.75) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00)
- agm_no_principle: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-258 (Δprev 0.00) → A-260 (Δprev 0.00) → A-261 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00) → A-262 (Δprev 0.00)
- agm_no_archmem: A-001 (Δprev 0.00) → A-008 (Δprev 0.75) → A-008 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-033 (Δprev 0.75) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00)
- agm_no_negative: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-260 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00)
- agm_no_economics: A-001 (Δprev 0.00) → A-008 (Δprev 0.75) → A-008 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-033 (Δprev 0.75) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00)
- agm_no_regime: A-001 (Δprev 0.00) → A-008 (Δprev 0.75) → A-008 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-033 (Δprev 0.75) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00) → A-033 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 135; completed with a recorded test: 18; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 4, 'agm_no_principle': 0, 'agm_no_archmem': 4, 'agm_no_negative': 6, 'agm_no_economics': 4, 'agm_no_regime': 4}

## Adaptation economics

- task_memory: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.09436
- architecture_memory: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.0916
- always_adapt: decisions {'ADAPT': 18}; mean decision error -0.1465
- never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 16}; mean decision error -0.07225
- agm_cold: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.08889
- agm_full: decisions {'ADAPT': 16, 'PARTIAL_ADAPT': 2}; mean decision error -0.1314
- agm_no_principle: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.08919
- agm_no_archmem: decisions {'ADAPT': 16, 'PARTIAL_ADAPT': 2}; mean decision error -0.1314
- agm_no_negative: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.1098
- agm_no_economics: decisions {'ADAPT': 18}; mean decision error -0.1314
- agm_no_regime: decisions {'ADAPT': 16, 'PARTIAL_ADAPT': 2}; mean decision error -0.1315

## Failures

- failed/refused/violating executions: 337
  - fixed step 2 task f7a52bbb964cabb4: memory_limit_exceeded:286>100
  - adaptive step 2 task bce5d1ac98131d62: memory_limit_exceeded:268>100
  - search step 2 candidate_evaluation 514271c061a736d2: memory_limit_exceeded:268>100
  - search step 2 candidate_evaluation e1a1e72007899f6a: memory_limit_exceeded:268>100
  - search step 2 candidate_evaluation 4646a302124cf5fc: memory_limit_exceeded:268>100
  - search step 2 candidate_evaluation 751f5a94efec7950: memory_limit_exceeded:268>100
  - search step 2 candidate_evaluation c60821918c7de34a: memory_limit_exceeded:268>100
  - search step 2 task c60821918c7de34a: memory_limit_exceeded:268>100
  - task_memory step 2 candidate_evaluation 124842ea805d6c54: memory_limit_exceeded:268>100
  - task_memory step 2 candidate_evaluation d7b62163d4656125: memory_limit_exceeded:268>100
  - task_memory step 2 candidate_evaluation 731baed6518c2219: memory_limit_exceeded:268>100
  - task_memory step 2 candidate_evaluation eb91b0ffd13686fd: memory_limit_exceeded:268>100
  - task_memory step 2 candidate_evaluation 8f8cd749114a6d8d: memory_limit_exceeded:268>100
  - task_memory step 2 candidate_evaluation ed315c8d535274e8: memory_limit_exceeded:268>100
  - task_memory step 2 task 124842ea805d6c54: memory_limit_exceeded:268>100
  - architecture_memory step 2 candidate_evaluation 124842ea805d6c54: memory_limit_exceeded:268>100
  - architecture_memory step 2 candidate_evaluation d7b62163d4656125: memory_limit_exceeded:268>100
  - architecture_memory step 2 candidate_evaluation 731baed6518c2219: memory_limit_exceeded:268>100
  - architecture_memory step 2 candidate_evaluation eb91b0ffd13686fd: memory_limit_exceeded:268>100
  - architecture_memory step 2 candidate_evaluation 8f8cd749114a6d8d: memory_limit_exceeded:268>100
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 1316, 'architecture_memory': 1316, 'always_adapt': 1312, 'never_adapt': 1321, 'agm_cold': 1316, 'agm_full': 1349, 'agm_no_principle': 1316, 'agm_no_archmem': 1349, 'agm_no_negative': 1323, 'agm_no_economics': 1349, 'agm_no_regime': 1349}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 0, 'agm_no_principle': 0, 'agm_no_archmem': 0, 'agm_no_negative': 3, 'agm_no_economics': 0, 'agm_no_regime': 0}

## Counterexamples

- lowest per-step quality per agent: fixed 0.614, adaptive 0.388, search 0.612, task_memory 0.713, architecture_memory 0.713, always_adapt 0.603, never_adapt 0.713, agm_cold 0.713, agm_full 0.603, agm_no_principle 0.713, agm_no_archmem 0.603, agm_no_negative 0.698, agm_no_economics 0.603, agm_no_regime 0.603

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['fixed', 'adaptive', 'task_memory', 'never_adapt', 'agm_no_negative', 'agm_no_regime']; dominated = ['search', 'architecture_memory', 'always_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_economics']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '16.8', 'task_memory': '69.25', 'architecture_memory': '69.25', 'always_adapt': '44.23', 'never_adapt': '265.5', 'agm_cold': '69.25', 'agm_full': '44.92', 'agm_no_principle': '69.25', 'agm_no_archmem': '44.92', 'agm_no_negative': '45.59', 'agm_no_economics': '44.92', 'agm_no_regime': '44.92'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_no_principle', 'agm_no_negative']. Agents with zero failures: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
