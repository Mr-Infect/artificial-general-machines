# Experiment report: v02_exp1_A

## Hypothesis

Exp 1 repeatability: Domain A source run (AGM variants write memory).

## Experimental conditions

- id `exp_1790769628_31a8c8262f0f`, seed 1001, executor process, git `d07b0f410b21`, manifest `e303c7e2df301430`
- task {'type': 'anomaly_detection', 'domain': 'network', 'dataset_size': 2000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': True, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events [{'t': 10.0, 'type': 'memory_reduction', 'params': {'memory_mb': 80}}, {'t': 20.0, 'type': 'network_loss', 'params': {}}, {'t': 20.0, 'type': 'capability_removal', 'params': {'capabilities': ['model:large_reasoner', 'tool:search', 'component:lookahead_planner']}}, {'t': 30.0, 'type': 'latency_reduction', 'params': {'latency_ms': 800}}, {'t': 40.0, 'type': 'priority_increase', 'params': {'priority': 3}}]
- objective quality ≥ 0.0; budget {'max_seconds': 120.0, 'max_cost': 0.25, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["statistical_detector", "anomaly_detector", "rate_detector"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive"}
- search: {"type": "search", "max_evaluations": 8}
- self_evolving: {"type": "self_evolving", "mutations_per_step": 2}
- agm_v1_cold: {"type": "agm", "max_evaluations": 6, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v1_A_1.sqlite"}}
- agm_v2_cold: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v2_A_1.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v2_A_1.sqlite"}}
- agm_v2_explore: {"type": "agm_v2", "max_evaluations": 8, "memory_mode": "full", "economics_mode": "economic", "explore_all": true, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v2_A_1.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v2_A_1.sqlite"}}

## Results

| metric | fixed | adaptive | search | self_evolving | agm_v1_cold | agm_v2_cold | agm_v2_explore |
|---|---|---|---|---|---|---|---|
| quality_mean | 0.16 | 0.8829 | 0.8826 | 0.16 | 0.9588 | 0.9588 | 0.9588 |
| quality_min | 0 | 0.7619 | 0.7826 | 0 | 0.9333 | 0.9333 | 0.9333 |
| quality_final | 0 | 0.9565 | 0.8148 | 0 | 0.9565 | 0.9565 | 0.9565 |
| time_to_target_logical_s | — | — | — | — | 20 | 20 | 20 |
| architecture_evaluations | 0 | 0 | 26 | 3 | 4 | 4 | 32 |
| adaptation_cost | 0 | 0 | 0.027 | 0.0026 | 0.002 | 0.002 | 0.016 |
| execution_cost | 0.0005 | 0.0025 | 0.0025 | 0.0005 | 0.0025 | 0.0025 | 0.0025 |
| total_cost | 0.0005 | 0.0025 | 0.0295 | 0.0031 | 0.0045 | 0.0045 | 0.0185 |
| cpu_time_s | 0.08506 | 0.2659 | 2.504 | 0.3584 | 0.4148 | 0.4072 | 2.143 |
| max_memory_mb | 45.18 | 45.8 | 48.66 | 48.73 | 49.69 | 53.04 | 54.12 |
| constraint_violations | 4 | 0 | 0 | 4 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 4 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0 | 0.2 | 0.2 | 0 |
| distinct_architectures | 1 | 3 | 4 | 1 | 1 | 1 | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-003 (Δprev 0.65) → A-002 (Δprev 0.65) → A-002 (Δprev 0.00)
- search: A-007 (Δprev 0.00) → A-011 (Δprev 0.65) → A-017 (Δprev 0.60) → A-017 (Δprev 0.00) → A-016 (Δprev 0.43)
- self_evolving: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- agm_v1_cold: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- agm_v2_cold: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- agm_v2_explore: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 0; completed with a recorded test: 0; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'self_evolving': None, 'agm_v1_cold': None, 'agm_v2_cold': 0, 'agm_v2_explore': 0}

## Adaptation economics

- agm_v2_cold: decisions {'ADAPT': 8, 'DO_NOT_ADAPT': 2}; mean decision error -0.04876
- agm_v2_explore: decisions {'ADAPT': 8, 'DO_NOT_ADAPT': 2}; mean decision error -0.05931

## Failures

- failed/refused/violating executions: 8
  - fixed step 1 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - self_evolving step 1 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - fixed step 2 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - self_evolving step 2 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - fixed step 3 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - self_evolving step 3 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - fixed step 4 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - self_evolving step 4 task 2cf46e3a49f036de: architecture_invalid_for_environment
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'self_evolving': 0, 'agm_v1_cold': 0, 'agm_v2_cold': 525, 'agm_v2_explore': 525}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'self_evolving': 0, 'agm_v1_cold': 0, 'agm_v2_cold': 0, 'agm_v2_explore': 0}

## Counterexamples

- lowest per-step quality per agent: fixed 0.000, adaptive 0.762, search 0.783, self_evolving 0.000, agm_v1_cold 0.933, agm_v2_cold 0.933, agm_v2_explore 0.933

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['fixed', 'adaptive', 'self_evolving', 'agm_v1_cold']; dominated = ['search', 'agm_v2_cold', 'agm_v2_explore']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '32.69', 'self_evolving': '61.54', 'agm_v1_cold': '479.4', 'agm_v2_cold': '479.4', 'agm_v2_explore': '59.92'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['agm_v1_cold', 'agm_v2_cold', 'agm_v2_explore']. Agents with zero failures: ['adaptive', 'search', 'agm_v1_cold', 'agm_v2_cold', 'agm_v2_explore'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
