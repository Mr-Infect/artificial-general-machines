# Experiment report: v03_Y_telemetry_grid

## Hypothesis

v0.3 blind-transfer environment telemetry_grid with held-out regime combinations; all agents, memory from the training runs of the same seed.

## Experimental conditions

- id `exp_1790782189_a1fa96a074d8`, seed 20001, executor process, git `32e0a66326c4`, manifest `a60cb3cbc32e1c08`
- task {'type': 'anomaly_detection', 'domain': 'telemetry_grid', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["flux_zscore", "robust_flux", "flux_delta"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive", "library": "roles"}
- search: {"type": "search", "space": "auto", "max_evaluations": 6}
- task_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_task.sqlite"}}
- architecture_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_arch.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_arch.sqlite"}}
- always_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt"}
- never_adapt: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "never_adapt"}
- agm_cold: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false}
- agm_full: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_full.sqlite"}}
- agm_no_principle: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_principles": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_principle.sqlite"}}
- agm_no_archmem: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_archmem": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_archmem.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_archmem.sqlite"}}
- agm_no_negative: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "use_negative": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_negative.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_negative.sqlite"}}
- agm_no_economics: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "economics_mode": "always_adapt", "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_economics.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_economics.sqlite"}}
- agm_no_regime: {"type": "agm_v3", "max_evaluations": 6, "explore_all": false, "regime_detection": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_regime.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/telemetry_grid_1_no_regime.sqlite"}}

## Results

| metric | fixed | adaptive | search | task_memory | architecture_memory | always_adapt | never_adapt | agm_cold | agm_full | agm_no_principle | agm_no_archmem | agm_no_negative | agm_no_economics | agm_no_regime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.4705 | 0.4899 | 0.3154 | 0.3859 | 0.3859 | 0.3859 | 0.2636 | 0.3859 | 0.4026 | 0.3859 | 0.4026 | 0.4481 | 0.4026 | 0.4026 |
| quality_min | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| quality_final | 0.8889 | 1 | 1 | 0.6154 | 0.6154 | 0.6154 | 0.4615 | 0.6154 | 1 | 0.6154 | 1 | 1 | 1 | 1 |
| time_to_target_logical_s | — | 70 | 80 | — | — | — | — | — | 70 | — | 70 | 30 | 70 | 70 |
| architecture_evaluations | 0 | 0 | 29 | 23 | 23 | 23 | 6 | 23 | 41 | 23 | 41 | 47 | 41 | 35 |
| adaptation_cost | 0 | 0 | 0.0425 | 0.0115 | 0.0115 | 0.0115 | 0.003 | 0.0115 | 0.0205 | 0.0115 | 0.0205 | 0.0235 | 0.0205 | 0.0175 |
| execution_cost | 0.0045 | 0.008 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 | 0.0045 |
| total_cost | 0.0045 | 0.008 | 0.047 | 0.016 | 0.016 | 0.016 | 0.0075 | 0.016 | 0.025 | 0.016 | 0.025 | 0.028 | 0.025 | 0.022 |
| cpu_time_s | 0.5703 | 0.6382 | 2.861 | 1.69 | 1.751 | 1.7 | 0.859 | 1.75 | 2.78 | 1.731 | 2.643 | 3.117 | 2.711 | 2.167 |
| max_memory_mb | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 | 88.53 |
| constraint_violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0.1699 | 0.1667 | 0.02778 | 0.02778 | 0.1319 | 0.1111 | 0.1319 | 0.02778 | 0.02778 | 0.02778 | 0.01852 | 0.02778 | 0.02778 |
| distinct_architectures | 1 | 4 | 5 | 3 | 3 | 3 | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-003 (Δprev 0.24) → A-004 (Δprev 0.64) → A-002 (Δprev 0.40) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-001 (Δprev 0.65) → A-001 (Δprev 0.00)
- search: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-008 (Δprev 0.35) → A-008 (Δprev 0.00) → A-013 (Δprev 0.58) → A-013 (Δprev 0.00) → A-014 (Δprev 0.75) → A-014 (Δprev 0.00) → A-024 (Δprev 0.60)
- task_memory: A-002 (Δprev 0.00) → A-137 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00)
- architecture_memory: A-002 (Δprev 0.00) → A-137 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00)
- always_adapt: A-002 (Δprev 0.00) → A-137 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00)
- never_adapt: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- agm_cold: A-002 (Δprev 0.00) → A-137 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00)
- agm_full: A-001 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-020 (Δprev 0.60) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00)
- agm_no_principle: A-002 (Δprev 0.00) → A-137 (Δprev 0.00) → A-014 (Δprev 0.45) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00) → A-014 (Δprev 0.00)
- agm_no_archmem: A-001 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-020 (Δprev 0.60) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00)
- agm_no_negative: A-001 (Δprev 0.00) → A-008 (Δprev 0.75) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-040 (Δprev 0.60)
- agm_no_economics: A-001 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-020 (Δprev 0.60) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00)
- agm_no_regime: A-001 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-138 (Δprev 0.00) → A-020 (Δprev 0.60) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00) → A-020 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 112; completed with a recorded test: 28; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 10, 'agm_no_principle': 0, 'agm_no_archmem': 10, 'agm_no_negative': 7, 'agm_no_economics': 10, 'agm_no_regime': 10}

## Adaptation economics

- task_memory: decisions {'ADAPT': 18}; mean decision error -0.5577
- architecture_memory: decisions {'ADAPT': 18}; mean decision error -0.5573
- always_adapt: decisions {'ADAPT': 18}; mean decision error -0.5573
- never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 16}; mean decision error -0.6471
- agm_cold: decisions {'ADAPT': 18}; mean decision error -0.557
- agm_full: decisions {'ADAPT': 18}; mean decision error -0.5146
- agm_no_principle: decisions {'ADAPT': 18}; mean decision error -0.5573
- agm_no_archmem: decisions {'ADAPT': 18}; mean decision error -0.5133
- agm_no_negative: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.4688
- agm_no_economics: decisions {'ADAPT': 18}; mean decision error -0.5154
- agm_no_regime: decisions {'ADAPT': 16, 'DO_NOT_ADAPT': 2}; mean decision error -0.5116

## Failures

- failed/refused/violating executions: 0
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 1714, 'architecture_memory': 1714, 'always_adapt': 1714, 'never_adapt': 1723, 'agm_cold': 1714, 'agm_full': 1776, 'agm_no_principle': 1714, 'agm_no_archmem': 1776, 'agm_no_negative': 1728, 'agm_no_economics': 1776, 'agm_no_regime': 1777}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'task_memory': 0, 'architecture_memory': 0, 'always_adapt': 0, 'never_adapt': 0, 'agm_cold': 0, 'agm_full': 5, 'agm_no_principle': 0, 'agm_no_archmem': 5, 'agm_no_negative': 3, 'agm_no_economics': 5, 'agm_no_regime': 5}

## Counterexamples

- lowest per-step quality per agent: fixed 0.000, adaptive 0.000, search 0.000, task_memory 0.000, architecture_memory 0.000, always_adapt 0.000, never_adapt 0.000, agm_cold 0.000, agm_full 0.000, agm_no_principle 0.000, agm_no_archmem 0.000, agm_no_negative 0.000, agm_no_economics 0.000, agm_no_regime 0.000

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['fixed', 'adaptive', 'never_adapt', 'agm_no_principle', 'agm_no_negative', 'agm_no_regime']; dominated = ['search', 'task_memory', 'architecture_memory', 'always_adapt', 'agm_cold', 'agm_full', 'agm_no_archmem', 'agm_no_economics']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '7.421', 'task_memory': '33.56', 'architecture_memory': '33.56', 'always_adapt': '33.56', 'never_adapt': '87.88', 'agm_cold': '33.56', 'agm_full': '19.64', 'agm_no_principle': '33.56', 'agm_no_archmem': '19.64', 'agm_no_negative': '19.07', 'agm_no_economics': '19.64', 'agm_no_regime': '23.01'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['adaptive', 'search', 'agm_full', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime']. Agents with zero failures: ['fixed', 'adaptive', 'search', 'task_memory', 'architecture_memory', 'always_adapt', 'never_adapt', 'agm_cold', 'agm_full', 'agm_no_principle', 'agm_no_archmem', 'agm_no_negative', 'agm_no_economics', 'agm_no_regime'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
