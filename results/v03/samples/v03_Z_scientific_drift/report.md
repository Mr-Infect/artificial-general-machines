# Experiment report: v03_Z_scientific_drift

## Hypothesis

v0.3 false-analogy environment scientific_drift with held-out regime combinations; all agents, memory from the training runs of the same seed.

## Experimental conditions

- id `exp_1790783789_b96aa94f6f39`, seed 20402, executor process, git `32e0a66326c4`, manifest `37c477797fd9d5e9`
- task {'type': 'scientific_verification', 'domain': 'scientific_drift', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': True, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["statistical_detector", "anomaly_detector", "rate_detector"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive", "library": "roles"}
- search: {"type": "search", "space": "auto", "max_evaluations": 6}
- task_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_task.sqlite"}}
- architecture_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_arch.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_arch.sqlite"}}
- always_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt"}
- never_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "never_adapt"}
- agm_cold: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false}
- agm_full: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_full.sqlite"}}
- agm_no_principle: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_principles": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_principle.sqlite"}}
- agm_no_archmem: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_archmem": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_archmem.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_archmem.sqlite"}}
- agm_no_negative: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_negative": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_negative.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_negative.sqlite"}}
- agm_no_economics: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_economics.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_economics.sqlite"}}
- agm_no_regime: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "regime_detection": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_regime.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/scientific_drift_2_no_regime.sqlite"}}

## Results

| metric | fixed | adaptive | search | task_memory | architecture_memory | always_adapt | never_adapt | agm_cold | agm_full | agm_no_principle | agm_no_archmem | agm_no_negative | agm_no_economics | agm_no_regime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0 | 0.005168 | 0.0158 | 0.005698 | 0.005698 | 0.005698 | 0.005698 | 0.005698 | 0.005698 | 0.005698 | 0.005698 | 0.005698 | 0.005698 | 0.005698 |
| quality_min | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| quality_final | 0 | 0.04651 | 0.09091 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| time_to_target_logical_s | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 | 30 |
| architecture_evaluations | 0 | 0 | 12 | 24 | 14 | 24 | 6 | 24 | 17 | 14 | 17 | 16 | 17 | 17 |
| adaptation_cost | 0 | 0 | 0.006 | 0.012 | 0.007 | 0.012 | 0.003 | 0.012 | 0.0085 | 0.007 | 0.0085 | 0.008 | 0.0085 | 0.0085 |
| execution_cost | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 |
| total_cost | 0.0045 | 0.0045 | 0.0105 | 0.0165 | 0.0115 | 0.0165 | 0.0075 | 0.0165 | 0.013 | 0.0115 | 0.013 | 0.0125 | 0.013 | 0.013 |
| cpu_time_s | 0.6449 | 0.5858 | 1.884 | 2.068 | 1.347 | 2.022 | 0.8902 | 1.893 | 1.77 | 1.473 | 1.561 | 1.569 | 1.712 | 1.67 |
| max_memory_mb | 295.1 | 295.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 | 294.1 |
| constraint_violations | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0.1421 | 0.1204 | 0.006944 | 0.01389 | 0.1111 | 0.1111 | 0.1111 | 0.006944 | 0.01389 | 0.01389 | 0.006944 | 0.006944 | 0.006944 |
| distinct_architectures | 1 | 3 | 2 | 1 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 2 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-003 (Δprev 0.24) → A-001 (Δprev 0.65) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-003 (Δprev 0.65) → A-003 (Δprev 0.00)
- search: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-010 (Δprev 0.30) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00)
- task_memory: A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- architecture_memory: A-006 (Δprev 0.00) → A-007 (Δprev 0.30) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00)
- always_adapt: A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- never_adapt: A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- agm_cold: A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- agm_full: A-007 (Δprev 0.00) → A-010 (Δprev 0.30) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00)
- agm_no_principle: A-006 (Δprev 0.00) → A-007 (Δprev 0.30) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00)
- agm_no_archmem: A-005 (Δprev 0.00) → A-008 (Δprev 0.30) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00)
- agm_no_negative: A-005 (Δprev 0.00) → A-009 (Δprev 0.30) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00)
- agm_no_economics: A-007 (Δprev 0.00) → A-010 (Δprev 0.30) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00)
- agm_no_regime: A-007 (Δprev 0.00) → A-010 (Δprev 0.30) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 219; completed with a recorded test: 22; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 4, 'agm_no_principle': 0, 'agm_no_archmem': 6, 'agm_no_negative': 4, 'agm_no_economics': 4, 'agm_no_regime': 4}

## Adaptation economics

- task_memory: decisions {'ADAPT': 18}; mean decision error -0.1342
- architecture_memory: decisions {'ADAPT': 18}; mean decision error -0.2216
- always_adapt: decisions {'ADAPT': 18}; mean decision error -0.1339
- never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 16}; mean decision error -0.1304
- agm_cold: decisions {'ADAPT': 18}; mean decision error -0.1336
- agm_full: decisions {'ADAPT': 18}; mean decision error -0.2352
- agm_no_principle: decisions {'ADAPT': 18}; mean decision error -0.2227
- agm_no_archmem: decisions {'ADAPT': 18}; mean decision error -0.2016
- agm_no_negative: decisions {'ADAPT': 18}; mean decision error -0.2622
- agm_no_economics: decisions {'ADAPT': 18}; mean decision error -0.2352
- agm_no_regime: decisions {'ADAPT': 18}; mean decision error -0.2352

## Failures

- failed/refused/violating executions: 280
  - fixed step 0 task 2cf46e3a49f036de: memory_limit_exceeded:295>100
  - adaptive step 0 task 4c11ce0f07f705d9: memory_limit_exceeded:295>100
  - search step 0 candidate_evaluation b3bc086de5d69ab9: memory_limit_exceeded:295>100
  - search step 0 candidate_evaluation ed9a8058fda2acce: memory_limit_exceeded:294>100
  - search step 0 candidate_evaluation 398f0b563e2392f9: memory_limit_exceeded:294>100
  - search step 0 candidate_evaluation 9476833ef580ecf9: memory_limit_exceeded:294>100
  - search step 0 candidate_evaluation 8fb34e1e5b6922e7: memory_limit_exceeded:294>100
  - search step 0 candidate_evaluation 4c11ce0f07f705d9: memory_limit_exceeded:294>100
  - search step 0 task 8fb34e1e5b6922e7: memory_limit_exceeded:294>100
  - task_memory step 0 candidate_evaluation 4c11ce0f07f705d9: memory_limit_exceeded:294>100
  - task_memory step 0 candidate_evaluation 662a48a0041be770: memory_limit_exceeded:294>100
  - task_memory step 0 candidate_evaluation 8d51da4468988bb6: memory_limit_exceeded:294>100
  - task_memory step 0 candidate_evaluation f1166591d0a381d3: memory_limit_exceeded:294>100
  - task_memory step 0 candidate_evaluation 2868724eec9f7f2d: memory_limit_exceeded:294>100
  - task_memory step 0 candidate_evaluation e57f8da0b84cc1be: memory_limit_exceeded:294>100
  - task_memory step 0 task f1166591d0a381d3: memory_limit_exceeded:294>100
  - architecture_memory step 0 candidate_evaluation 4c11ce0f07f705d9: memory_limit_exceeded:294>100
  - architecture_memory step 0 candidate_evaluation aad2e02f297ba0a5: memory_limit_exceeded:294>100
  - architecture_memory step 0 candidate_evaluation e9a71cf413884f1a: memory_limit_exceeded:294>100
  - architecture_memory step 0 candidate_evaluation 662a48a0041be770: memory_limit_exceeded:294>100
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 1473, 'architecture_memory': 1473, 'always_adapt': 1473, 'never_adapt': 1481, 'agm_cold': 1473, 'agm_full': 1508, 'agm_no_principle': 1473, 'agm_no_archmem': 1514, 'agm_no_negative': 1482, 'agm_no_economics': 1508, 'agm_no_regime': 1508}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 1, 'agm_no_principle': 0, 'agm_no_archmem': 6, 'agm_no_negative': 1, 'agm_no_economics': 1, 'agm_no_regime': 1}

## Counterexamples

- lowest per-step quality per agent: fixed 0.000, adaptive 0.000, search 0.000, task_memory 0.000, architecture_memory 0.000, always_adapt 0.000, never_adapt 0.000, agm_cold 0.000, agm_full 0.000, agm_no_principle 0.000, agm_no_archmem 0.000, agm_no_negative 0.000, agm_no_economics 0.000, agm_no_regime 0.000

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['adaptive', 'search', 'task_memory', 'architecture_memory', 'never_adapt']; dominated = ['fixed', 'always_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '2.633', 'task_memory': '0.4748', 'architecture_memory': '0.814', 'always_adapt': '0.4748', 'never_adapt': '1.899', 'agm_cold': '0.4748', 'agm_full': '0.6704', 'agm_no_principle': '0.814', 'agm_no_archmem': '0.6704', 'agm_no_negative': '0.7123', 'agm_no_economics': '0.6704', 'agm_no_regime': '0.6704'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']. Agents with zero failures: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
