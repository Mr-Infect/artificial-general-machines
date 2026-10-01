# Experiment report: v03_Y_lab_assay

## Hypothesis

v0.3 blind-transfer environment lab_assay with held-out regime combinations; all agents, memory from the training runs of the same seed.

## Experimental conditions

- id `exp_1790782598_4650bc0cb1af`, seed 20102, executor process, git `32e0a66326c4`, manifest `d49d1734ea6d8b8d`
- task {'type': 'scientific_verification', 'domain': 'lab_assay', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': True, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["flux_zscore", "robust_flux", "flux_delta"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive", "library": "roles"}
- search: {"type": "search", "space": "auto", "max_evaluations": 6}
- task_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_task.sqlite"}}
- architecture_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_arch.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_arch.sqlite"}}
- always_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt"}
- never_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "never_adapt"}
- agm_cold: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false}
- agm_full: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_full.sqlite"}}
- agm_no_principle: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_principles": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_principle.sqlite"}}
- agm_no_archmem: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_archmem": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_archmem.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_archmem.sqlite"}}
- agm_no_negative: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_negative": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_negative.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_negative.sqlite"}}
- agm_no_economics: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_economics.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_economics.sqlite"}}
- agm_no_regime: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "regime_detection": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_regime.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/lab_assay_2_no_regime.sqlite"}}

## Results

| metric | fixed | adaptive | search | task_memory | architecture_memory | always_adapt | never_adapt | agm_cold | agm_full | agm_no_principle | agm_no_archmem | agm_no_negative | agm_no_economics | agm_no_regime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.4418 | 0.3701 | 0.3716 | 0.3095 | 0.3095 | 0.3095 | 0.3391 | 0.3095 | 0.3704 | 0.3095 | 0.3704 | 0.3598 | 0.3704 | 0.3704 |
| quality_min | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| quality_final | 0.6667 | 0.4167 | 0.4444 | 0.6667 | 0.6667 | 0.6667 | 0.4762 | 0.6667 | 0.4286 | 0.6667 | 0.4286 | 0.4286 | 0.4286 | 0.4286 |
| time_to_target_logical_s | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| architecture_evaluations | 0 | 0 | 18 | 9 | 9 | 9 | 1 | 9 | 17 | 9 | 17 | 17 | 17 | 17 |
| adaptation_cost | 0 | 0 | 0.009 | 0.0045 | 0.0045 | 0.0045 | 0.0005 | 0.0045 | 0.0085 | 0.0045 | 0.0085 | 0.0085 | 0.0085 | 0.0085 |
| execution_cost | 0.0045 | 0.008 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 |
| total_cost | 0.0045 | 0.008 | 0.0135 | 0.009 | 0.009 | 0.009 | 0.005 | 0.009 | 0.013 | 0.009 | 0.013 | 0.013 | 0.013 | 0.013 |
| cpu_time_s | 0.7 | 0.7695 | 1.74 | 0.9156 | 0.9522 | 0.9952 | 0.4609 | 0.9553 | 1.481 | 1.043 | 1.453 | 1.435 | 1.481 | 1.501 |
| max_memory_mb | 273.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 | 272.7 |
| constraint_violations | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 6 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0.1699 | 0.1418 | 0.01389 | 0.01389 | 0.1181 | 0.1111 | 0.1181 | 0.03472 | 0.01389 | 0.03472 | 0.03472 | 0.03472 | 0.03472 |
| distinct_architectures | 1 | 4 | 3 | 2 | 2 | 2 | 1 | 2 | 3 | 2 | 3 | 3 | 3 | 3 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-003 (Δprev 0.24) → A-004 (Δprev 0.64) → A-003 (Δprev 0.64) → A-003 (Δprev 0.00)
- search: A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-005 (Δprev 0.00) → A-007 (Δprev 0.43) → A-007 (Δprev 0.00) → A-014 (Δprev 0.40) → A-014 (Δprev 0.00)
- task_memory: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-004 (Δprev 0.30) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- architecture_memory: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-004 (Δprev 0.30) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- always_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-004 (Δprev 0.30) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- never_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- agm_cold: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-004 (Δprev 0.30) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- agm_full: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-002 (Δprev 0.60) → A-002 (Δprev 0.00) → A-013 (Δprev 0.45) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00)
- agm_no_principle: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-004 (Δprev 0.30) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00) → A-004 (Δprev 0.00)
- agm_no_archmem: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-002 (Δprev 0.60) → A-002 (Δprev 0.00) → A-013 (Δprev 0.45) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00)
- agm_no_negative: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-004 (Δprev 0.60) → A-004 (Δprev 0.00) → A-012 (Δprev 0.75) → A-012 (Δprev 0.00) → A-012 (Δprev 0.00) → A-012 (Δprev 0.00)
- agm_no_economics: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-002 (Δprev 0.60) → A-002 (Δprev 0.00) → A-013 (Δprev 0.45) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00)
- agm_no_regime: A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-003 (Δprev 0.00) → A-002 (Δprev 0.60) → A-002 (Δprev 0.00) → A-013 (Δprev 0.45) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00) → A-013 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 168; completed with a recorded test: 28; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 6, 'agm_no_principle': 0, 'agm_no_archmem': 6, 'agm_no_negative': 6, 'agm_no_economics': 6, 'agm_no_regime': 6}

## Adaptation economics

- task_memory: decisions {'ADAPT': 18}; mean decision error -0.5438
- architecture_memory: decisions {'ADAPT': 18}; mean decision error -0.5431
- always_adapt: decisions {'ADAPT': 18}; mean decision error -0.5217
- never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 16}; mean decision error -0.3656
- agm_cold: decisions {'ADAPT': 18}; mean decision error -0.5219
- agm_full: decisions {'ADAPT': 18}; mean decision error -0.5706
- agm_no_principle: decisions {'ADAPT': 18}; mean decision error -0.5229
- agm_no_archmem: decisions {'ADAPT': 18}; mean decision error -0.5693
- agm_no_negative: decisions {'ADAPT': 18}; mean decision error -0.5536
- agm_no_economics: decisions {'ADAPT': 18}; mean decision error -0.5693
- agm_no_regime: decisions {'ADAPT': 18}; mean decision error -0.5694

## Failures

- failed/refused/violating executions: 197
  - fixed step 0 task 77690943b9566086: memory_limit_exceeded:274>100
  - adaptive step 0 task 7b2ba91f0754b273: memory_limit_exceeded:273>100
  - search step 0 candidate_evaluation 8d3dbc7a764b4b80: memory_limit_exceeded:273>100
  - search step 0 candidate_evaluation f77dd5ab99cad9f1: memory_limit_exceeded:273>100
  - search step 0 candidate_evaluation 7b2ba91f0754b273: memory_limit_exceeded:273>100
  - search step 0 candidate_evaluation 815a70cafcdb5ee7: memory_limit_exceeded:273>100
  - search step 0 candidate_evaluation ca82ff520797bb07: memory_limit_exceeded:273>100
  - search step 0 candidate_evaluation a591544c495878cd: memory_limit_exceeded:273>100
  - search step 0 task ca82ff520797bb07: memory_limit_exceeded:273>100
  - task_memory step 0 candidate_evaluation 98144ce95b9ea647: memory_limit_exceeded:273>100
  - task_memory step 0 task 98144ce95b9ea647: memory_limit_exceeded:273>100
  - architecture_memory step 0 candidate_evaluation 98144ce95b9ea647: memory_limit_exceeded:273>100
  - architecture_memory step 0 task 98144ce95b9ea647: memory_limit_exceeded:273>100
  - always_adapt step 0 candidate_evaluation 98144ce95b9ea647: memory_limit_exceeded:273>100
  - always_adapt step 0 task 98144ce95b9ea647: memory_limit_exceeded:273>100
  - never_adapt step 0 candidate_evaluation 98144ce95b9ea647: memory_limit_exceeded:273>100
  - never_adapt step 0 task 98144ce95b9ea647: memory_limit_exceeded:273>100
  - agm_cold step 0 candidate_evaluation 98144ce95b9ea647: memory_limit_exceeded:273>100
  - agm_cold step 0 task 98144ce95b9ea647: memory_limit_exceeded:273>100
  - agm_full step 0 candidate_evaluation 906faec010d97a33: memory_limit_exceeded:273>100
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 1594, 'architecture_memory': 1594, 'always_adapt': 1594, 'never_adapt': 1602, 'agm_cold': 1594, 'agm_full': 1630, 'agm_no_principle': 1594, 'agm_no_archmem': 1630, 'agm_no_negative': 1603, 'agm_no_economics': 1630, 'agm_no_regime': 1630}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 0, 'agm_no_principle': 0, 'agm_no_archmem': 0, 'agm_no_negative': 0, 'agm_no_economics': 0, 'agm_no_regime': 0}

## Counterexamples

- lowest per-step quality per agent: fixed 0.000, adaptive 0.000, search 0.000, task_memory 0.000, architecture_memory 0.000, always_adapt 0.000, never_adapt 0.000, agm_cold 0.000, agm_full 0.000, agm_no_principle 0.000, agm_no_archmem 0.000, agm_no_negative 0.000, agm_no_economics 0.000, agm_no_regime 0.000

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['fixed', 'adaptive', 'search', 'never_adapt', 'agm_no_negative', 'agm_no_economics']; dominated = ['task_memory', 'architecture_memory', 'always_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_regime']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '41.29', 'task_memory': '68.78', 'architecture_memory': '68.78', 'always_adapt': '68.78', 'never_adapt': '678.2', 'agm_cold': '68.78', 'agm_full': '43.57', 'agm_no_principle': '68.78', 'agm_no_archmem': '43.57', 'agm_no_negative': '42.33', 'agm_no_economics': '43.57', 'agm_no_regime': '43.57'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']. Agents with zero failures: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
