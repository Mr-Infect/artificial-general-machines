# Experiment report: v03_Z_planning_stable

## Hypothesis

v0.3 false-analogy environment planning_stable with held-out regime combinations; all agents, memory from the training runs of the same seed.

## Experimental conditions

- id `exp_1790784170_fe65f3c67b70`, seed 20502, executor process, git `32e0a66326c4`, manifest `4dd81165569a8732`
- task {'type': 'resource_planning', 'domain': 'planning_stable', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["priority_filter", "risk_estimator", "feasibility_checker"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive", "library": "roles"}
- search: {"type": "search", "space": "auto", "max_evaluations": 6}
- task_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_task.sqlite"}}
- architecture_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_arch.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_arch.sqlite"}}
- always_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt"}
- never_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "never_adapt"}
- agm_cold: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false}
- agm_full: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_full.sqlite"}}
- agm_no_principle: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_principles": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_principle.sqlite"}}
- agm_no_archmem: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_archmem": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_archmem.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_archmem.sqlite"}}
- agm_no_negative: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_negative": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_negative.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_negative.sqlite"}}
- agm_no_economics: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_economics.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_economics.sqlite"}}
- agm_no_regime: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "regime_detection": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_regime.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/planning_stable_2_no_regime.sqlite"}}

## Results

| metric | fixed | adaptive | search | task_memory | architecture_memory | always_adapt | never_adapt | agm_cold | agm_full | agm_no_principle | agm_no_archmem | agm_no_negative | agm_no_economics | agm_no_regime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.8647 | 0.672 | 0.8666 | 0.971 | 0.9854 | 0.971 | 0.8647 | 0.971 | 0.9998 | 0.9854 | 0.9089 | 0.9854 | 0.9998 | 0.9998 |
| quality_min | 0.8517 | 0.5163 | 0.8517 | 0.8702 | 0.8702 | 0.8702 | 0.8517 | 0.8702 | 0.9982 | 0.8702 | 0.8517 | 0.8702 | 0.9982 | 0.9982 |
| quality_final | 0.8718 | 0.6146 | 0.8894 | 0.9982 | 0.9982 | 0.9982 | 0.8718 | 0.9982 | 0.9982 | 0.9982 | 0.9982 | 0.9982 | 0.9982 | 0.9982 |
| time_to_target_logical_s | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 0 | 10 | 10 | 10 | 0 | 0 |
| architecture_evaluations | 0 | 0 | 23 | 9 | 9 | 9 | 1 | 9 | 9 | 9 | 10 | 9 | 9 | 9 |
| adaptation_cost | 0 | 0 | 0.0115 | 0.0045 | 0.0045 | 0.0045 | 0.0005 | 0.0045 | 0.0045 | 0.0045 | 0.005 | 0.0045 | 0.0045 | 0.0045 |
| execution_cost | 0.0045 | 0.012 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 |
| total_cost | 0.0045 | 0.012 | 0.016 | 0.009 | 0.009 | 0.009 | 0.005 | 0.009 | 0.009 | 0.009 | 0.0095 | 0.009 | 0.009 | 0.009 |
| cpu_time_s | 0.4219 | 0.5197 | 1.918 | 1.106 | 1.062 | 1.037 | 0.5353 | 1.045 | 1.11 | 1.138 | 1.072 | 1.107 | 1.107 | 1.179 |
| max_memory_mb | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 | 297.1 |
| constraint_violations | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0.1696 | 0.1358 | 0.006944 | 0 | 0.1181 | 0.1111 | 0.1181 | 0 | 0 | 0.006944 | 0 | 0 | 0 |
| distinct_architectures | 1 | 4 | 3 | 2 | 2 | 2 | 1 | 2 | 1 | 2 | 2 | 2 | 1 | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-001 (Δprev 0.65) → A-003 (Δprev 0.60) → A-004 (Δprev 0.68) → A-002 (Δprev 0.40) → A-001 (Δprev 0.65) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- search: A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-012 (Δprev 0.43) → A-012 (Δprev 0.00) → A-004 (Δprev 0.43) → A-004 (Δprev 0.00) → A-018 (Δprev 0.39)
- task_memory: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-003 (Δprev 0.30) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00)
- architecture_memory: A-001 (Δprev 0.00) → A-002 (Δprev 0.30) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- always_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-003 (Δprev 0.30) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00)
- never_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- agm_cold: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-003 (Δprev 0.30) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00)
- agm_full: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00)
- agm_no_principle: A-001 (Δprev 0.00) → A-002 (Δprev 0.30) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- agm_no_archmem: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-005 (Δprev 0.75) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00)
- agm_no_negative: A-001 (Δprev 0.00) → A-004 (Δprev 0.30) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- agm_no_economics: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00)
- agm_no_regime: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 142; completed with a recorded test: 15; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 3, 'agm_no_principle': 0, 'agm_no_archmem': 4, 'agm_no_negative': 3, 'agm_no_economics': 3, 'agm_no_regime': 3}

## Adaptation economics

- task_memory: decisions {'ADAPT': 18}; mean decision error -0.04851
- architecture_memory: decisions {'ADAPT': 18}; mean decision error -0.05122
- always_adapt: decisions {'ADAPT': 18}; mean decision error -0.04728
- never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 16}; mean decision error -0.09053
- agm_cold: decisions {'ADAPT': 18}; mean decision error -0.04744
- agm_full: decisions {'ADAPT': 18}; mean decision error -0.05614
- agm_no_principle: decisions {'ADAPT': 18}; mean decision error -0.05211
- agm_no_archmem: decisions {'ADAPT': 18}; mean decision error -0.06388
- agm_no_negative: decisions {'ADAPT': 18}; mean decision error -0.05227
- agm_no_economics: decisions {'ADAPT': 18}; mean decision error -0.05611
- agm_no_regime: decisions {'ADAPT': 18}; mean decision error -0.05632

## Failures

- failed/refused/violating executions: 163
  - fixed step 0 task 9bde56f584390dbb: memory_limit_exceeded:297>100
  - adaptive step 0 task de57420906cd01f2: memory_limit_exceeded:297>100
  - search step 0 candidate_evaluation edd4e85624c75ce9: memory_limit_exceeded:297>100
  - search step 0 candidate_evaluation f55fd133fa2d780e: memory_limit_exceeded:297>100
  - search step 0 candidate_evaluation b37587ec8fcccabd: memory_limit_exceeded:297>100
  - search step 0 candidate_evaluation ffd283a46b4807e2: memory_limit_exceeded:297>100
  - search step 0 candidate_evaluation a1c035998e3d5b77: memory_limit_exceeded:297>100
  - search step 0 candidate_evaluation 5fd1dace3d45b43c: memory_limit_exceeded:297>100
  - search step 0 task ffd283a46b4807e2: memory_limit_exceeded:297>100
  - task_memory step 0 candidate_evaluation d423cf5ea73f7153: memory_limit_exceeded:297>100
  - task_memory step 0 task d423cf5ea73f7153: memory_limit_exceeded:297>100
  - architecture_memory step 0 candidate_evaluation 5b587e37fd83dc90: memory_limit_exceeded:297>100
  - architecture_memory step 0 task 5b587e37fd83dc90: memory_limit_exceeded:297>100
  - always_adapt step 0 candidate_evaluation d423cf5ea73f7153: memory_limit_exceeded:297>100
  - always_adapt step 0 task d423cf5ea73f7153: memory_limit_exceeded:297>100
  - never_adapt step 0 candidate_evaluation d423cf5ea73f7153: memory_limit_exceeded:297>100
  - never_adapt step 0 task d423cf5ea73f7153: memory_limit_exceeded:297>100
  - agm_cold step 0 candidate_evaluation d423cf5ea73f7153: memory_limit_exceeded:297>100
  - agm_cold step 0 task d423cf5ea73f7153: memory_limit_exceeded:297>100
  - agm_full step 0 candidate_evaluation 3aaffea2fb6deaec: memory_limit_exceeded:297>100
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 1474, 'architecture_memory': 1474, 'always_adapt': 1474, 'never_adapt': 1482, 'agm_cold': 1474, 'agm_full': 1509, 'agm_no_principle': 1474, 'agm_no_archmem': 1509, 'agm_no_negative': 1486, 'agm_no_economics': 1509, 'agm_no_regime': 1509}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 3, 'agm_no_principle': 0, 'agm_no_archmem': 0, 'agm_no_negative': 2, 'agm_no_economics': 3, 'agm_no_regime': 3}

## Counterexamples

- lowest per-step quality per agent: fixed 0.852, adaptive 0.516, search 0.852, task_memory 0.870, architecture_memory 0.870, always_adapt 0.870, never_adapt 0.852, agm_cold 0.870, agm_full 0.998, agm_no_principle 0.870, agm_no_archmem 0.852, agm_no_negative 0.870, agm_no_economics 0.998, agm_no_regime 0.998

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['fixed', 'search', 'architecture_memory', 'always_adapt', 'agm_full']; dominated = ['adaptive', 'task_memory', 'never_adapt', 'agm_cold', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '75.36', 'task_memory': '215.8', 'architecture_memory': '219', 'always_adapt': '215.8', 'never_adapt': '1729', 'agm_cold': '215.8', 'agm_full': '222.2', 'agm_no_principle': '219', 'agm_no_archmem': '181.8', 'agm_no_negative': '219', 'agm_no_economics': '222.2', 'agm_no_regime': '222.2'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']. Agents with zero failures: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
