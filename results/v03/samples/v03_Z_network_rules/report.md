# Experiment report: v03_Z_network_rules

## Hypothesis

v0.3 false-analogy environment network_rules with held-out regime combinations; all agents, memory from the training runs of the same seed.

## Experimental conditions

- id `exp_1790783389_ee41de583826`, seed 20302, executor process, git `32e0a66326c4`, manifest `e3cc521111cf155a`
- task {'type': 'anomaly_detection', 'domain': 'network_rules', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["statistical_detector", "anomaly_detector", "rate_detector"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive", "library": "roles"}
- search: {"type": "search", "space": "auto", "max_evaluations": 6}
- task_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_task.sqlite"}}
- architecture_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_arch.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_arch.sqlite"}}
- always_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt"}
- never_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "never_adapt"}
- agm_cold: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false}
- agm_full: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_full.sqlite"}}
- agm_no_principle: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_principles": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_principle.sqlite"}}
- agm_no_archmem: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_archmem": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_archmem.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_archmem.sqlite"}}
- agm_no_negative: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_negative": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_negative.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_negative.sqlite"}}
- agm_no_economics: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_economics.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_economics.sqlite"}}
- agm_no_regime: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "regime_detection": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_regime.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/network_rules_2_no_regime.sqlite"}}

## Results

| metric | fixed | adaptive | search | task_memory | architecture_memory | always_adapt | never_adapt | agm_cold | agm_full | agm_no_principle | agm_no_archmem | agm_no_negative | agm_no_economics | agm_no_regime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.7998 | 0.9312 | 0.9852 | 0.9667 | 0.9926 | 0.9203 | 0.9459 | 0.9852 | 0.9926 | 0.9459 | 0.9852 | 0.9459 | 0.9459 | 0.9926 |
| quality_min | 0.7692 | 0.7143 | 0.9333 | 0.8333 | 0.9333 | 0.6667 | 0.8235 | 0.9333 | 0.9333 | 0.8235 | 0.9333 | 0.8235 | 0.8235 | 0.9333 |
| quality_final | 0.7778 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| time_to_target_logical_s | — | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| architecture_evaluations | 0 | 0 | 12 | 16 | 15 | 15 | 6 | 17 | 19 | 13 | 18 | 17 | 17 | 19 |
| adaptation_cost | 0 | 0 | 0.0165 | 0.008 | 0.0075 | 0.0075 | 0.003 | 0.0085 | 0.0095 | 0.0065 | 0.009 | 0.0085 | 0.0085 | 0.0095 |
| execution_cost | 0.0045 | 0.0045 | 0.0115 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 |
| total_cost | 0.0045 | 0.0045 | 0.028 | 0.0125 | 0.012 | 0.012 | 0.0075 | 0.013 | 0.014 | 0.011 | 0.0135 | 0.013 | 0.013 | 0.014 |
| cpu_time_s | 0.6696 | 0.5824 | 2.134 | 1.56 | 1.417 | 1.4 | 0.9399 | 1.589 | 1.802 | 1.457 | 1.776 | 1.669 | 1.686 | 1.828 |
| max_memory_mb | 288.6 | 288.6 | 288.6 | 288.6 | 287.6 | 287.6 | 287.6 | 286.7 | 286.7 | 286.7 | 286.7 | 286.7 | 286.7 | 286.7 |
| constraint_violations | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0.1421 | 0.1424 | 0.01389 | 0.006944 | 0.1181 | 0.1111 | 0.125 | 0.006944 | 0.006944 | 0.006944 | 0.006944 | 0.006944 | 0.006944 |
| distinct_architectures | 1 | 3 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-003 (Δprev 0.65) → A-002 (Δprev 0.65) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- search: A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-009 (Δprev 0.70) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00)
- task_memory: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-010 (Δprev 0.45) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00)
- architecture_memory: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00)
- always_adapt: A-005 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00) → A-258 (Δprev 0.00)
- never_adapt: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00)
- agm_cold: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-010 (Δprev 0.45) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00)
- agm_full: A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00)
- agm_no_principle: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-007 (Δprev 0.30) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-007 (Δprev 0.00)
- agm_no_archmem: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-008 (Δprev 0.30) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00)
- agm_no_negative: A-007 (Δprev 0.00) → A-007 (Δprev 0.00) → A-010 (Δprev 0.30) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00) → A-010 (Δprev 0.00)
- agm_no_economics: A-009 (Δprev 0.00) → A-006 (Δprev 0.30) → A-006 (Δprev 0.00) → A-006 (Δprev 0.00) → A-006 (Δprev 0.00) → A-006 (Δprev 0.00) → A-006 (Δprev 0.00) → A-006 (Δprev 0.00) → A-006 (Δprev 0.00)
- agm_no_regime: A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-009 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 225; completed with a recorded test: 38; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 10, 'agm_no_principle': 0, 'agm_no_archmem': 6, 'agm_no_negative': 6, 'agm_no_economics': 6, 'agm_no_regime': 10}

## Adaptation economics

- task_memory: decisions {'ADAPT': 14, 'DO_NOT_ADAPT': 4}; mean decision error -0.07221
- architecture_memory: decisions {'ADAPT': 14, 'DO_NOT_ADAPT': 4}; mean decision error -0.04448
- always_adapt: decisions {'ADAPT': 18}; mean decision error -0.1172
- never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 16}; mean decision error -0.09118
- agm_cold: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.05347
- agm_full: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.04731
- agm_no_principle: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.09201
- agm_no_archmem: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.05452
- agm_no_negative: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.09447
- agm_no_economics: decisions {'ADAPT': 18}; mean decision error -0.09363
- agm_no_regime: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.04715

## Failures

- failed/refused/violating executions: 204
  - fixed step 2 task 2cf46e3a49f036de: memory_limit_exceeded:289>100
  - adaptive step 2 task 4c11ce0f07f705d9: memory_limit_exceeded:289>100
  - search step 2 candidate_evaluation 34a87c51471dac22: memory_limit_exceeded:289>100
  - search step 2 candidate_evaluation fa45a4be24697601: memory_limit_exceeded:289>100
  - search step 2 candidate_evaluation 4c11ce0f07f705d9: memory_limit_exceeded:289>100
  - search step 2 candidate_evaluation 7330b7ab4581c937: memory_limit_exceeded:289>100
  - search step 2 candidate_evaluation 8b1f4c9150503656: memory_limit_exceeded:289>100
  - search step 2 candidate_evaluation 9d8c1b5081d83410: memory_limit_exceeded:289>100
  - search step 2 task 4c11ce0f07f705d9: memory_limit_exceeded:289>100
  - task_memory step 2 task 2868724eec9f7f2d: memory_limit_exceeded:289>100
  - architecture_memory step 2 task 4c11ce0f07f705d9: memory_limit_exceeded:288>100
  - always_adapt step 2 candidate_evaluation f9340019763758ae: memory_limit_exceeded:288>100
  - always_adapt step 2 task 5432d8e50a4e2a6f: memory_limit_exceeded:288>100
  - never_adapt step 2 task 2868724eec9f7f2d: memory_limit_exceeded:288>100
  - agm_cold step 2 candidate_evaluation f9340019763758ae: memory_limit_exceeded:287>100
  - agm_cold step 2 candidate_evaluation be981f0c2cb269f3: memory_limit_exceeded:287>100
  - agm_cold step 2 candidate_evaluation 5432d8e50a4e2a6f: memory_limit_exceeded:287>100
  - agm_cold step 2 candidate_evaluation 6740a8ef2e312492: memory_limit_exceeded:287>100
  - agm_cold step 2 candidate_evaluation e3a7d7c45825ade2: memory_limit_exceeded:287>100
  - agm_cold step 2 task e3a7d7c45825ade2: memory_limit_exceeded:287>100
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 1475, 'architecture_memory': 1475, 'always_adapt': 1473, 'never_adapt': 1481, 'agm_cold': 1474, 'agm_full': 1548, 'agm_no_principle': 1474, 'agm_no_archmem': 1530, 'agm_no_negative': 1491, 'agm_no_economics': 1527, 'agm_no_regime': 1548}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 9, 'agm_no_principle': 0, 'agm_no_archmem': 6, 'agm_no_negative': 6, 'agm_no_economics': 6, 'agm_no_regime': 9}

## Counterexamples

- lowest per-step quality per agent: fixed 0.769, adaptive 0.714, search 0.933, task_memory 0.833, architecture_memory 0.933, always_adapt 0.667, never_adapt 0.824, agm_cold 0.933, agm_full 0.933, agm_no_principle 0.824, agm_no_archmem 0.933, agm_no_negative 0.824, agm_no_economics 0.824, agm_no_regime 0.933

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle']; dominated = ['fixed', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '59.71', 'task_memory': '120.8', 'architecture_memory': '132.3', 'always_adapt': '122.7', 'never_adapt': '315.3', 'agm_cold': '115.9', 'agm_full': '104.5', 'agm_no_principle': '145.5', 'agm_no_archmem': '109.5', 'agm_no_negative': '111.3', 'agm_no_economics': '111.3', 'agm_no_regime': '104.5'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']. Agents with zero failures: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
