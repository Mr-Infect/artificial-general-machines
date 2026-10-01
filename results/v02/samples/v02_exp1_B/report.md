# Experiment report: v02_exp1_B

## Hypothesis

Exp 1 repeatability: Domain B with AGM v0.1 and v0.2, cold vs memory from Domain A (paired by seed).

## Experimental conditions

- id `exp_1790769693_aa5ccb52b303`, seed 2000, executor process, git `d07b0f410b21`, manifest `d312e6ef68774b5f`
- task {'type': 'scientific_verification', 'domain': 'scientific', 'dataset_size': 2000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': True, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': True, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events [{'t': 10.0, 'type': 'memory_reduction', 'params': {'memory_mb': 80}}, {'t': 20.0, 'type': 'network_loss', 'params': {}}, {'t': 20.0, 'type': 'capability_removal', 'params': {'capabilities': ['model:large_reasoner', 'tool:search', 'component:lookahead_planner']}}, {'t': 30.0, 'type': 'latency_reduction', 'params': {'latency_ms': 800}}, {'t': 40.0, 'type': 'priority_increase', 'params': {'priority': 3}}]
- objective quality ≥ 0.0; budget {'max_seconds': 120.0, 'max_cost': 0.25, 'step_timeout_s': 30.0}

## Baselines

- fixed: {"type": "fixed", "architecture": {"perception": {"mode": "parallel", "components": ["statistical_detector", "anomaly_detector", "rate_detector"]}, "reasoning": {"type": "parallel", "model": "small_reasoner", "threshold": 0.5}, "verification": {"type": "rule_based"}}}
- adaptive: {"type": "adaptive"}
- search: {"type": "search", "max_evaluations": 8}
- self_evolving: {"type": "self_evolving", "mutations_per_step": 2}
- agm_v1_cold: {"type": "agm", "max_evaluations": 6}
- agm_v1_memory: {"type": "agm", "max_evaluations": 6, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v1_A_0.sqlite"}}
- agm_v2_cold: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "economic", "explore_all": false}
- agm_v2_memory: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v2_A_0.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp1_v2_A_0.sqlite"}}

## Results

| metric | fixed | adaptive | search | self_evolving | agm_v1_cold | agm_v1_memory | agm_v2_cold | agm_v2_memory |
|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.08421 | 0.5178 | 0.6214 | 0.3265 | 0.401 | 0.401 | 0.401 | 0.401 |
| quality_min | 0 | 0 | 0.4 | 0 | 0 | 0 | 0 | 0 |
| quality_final | 0 | 0.64 | 0.7407 | 0.6897 | 0.6923 | 0.6923 | 0.6923 | 0.6923 |
| time_to_target_logical_s | — | — | — | — | — | — | — | — |
| architecture_evaluations | 0 | 0 | 27 | 6 | 6 | 6 | 6 | 6 |
| adaptation_cost | 0 | 0 | 0.0205 | 0.0018 | 0.003 | 0.003 | 0.003 | 0.003 |
| execution_cost | 0.0005 | 0.0025 | 0.0025 | 0.0008 | 0.0025 | 0.0025 | 0.0025 | 0.0025 |
| total_cost | 0.0005 | 0.0025 | 0.023 | 0.0026 | 0.0055 | 0.0055 | 0.0055 | 0.0055 |
| cpu_time_s | 0.06701 | 0.2489 | 2.324 | 0.771 | 0.5023 | 0.4708 | 0.506 | 0.4868 |
| max_memory_mb | 73.54 | 73.54 | 73.54 | 73.54 | 73.54 | 73.54 | 73.54 | 73.56 |
| constraint_violations | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| failures | 4 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| novelty_mean | 0 | 0 | 0 | 0.025 | 0.2 | 0.0125 | 0.2 | 0.0125 |
| distinct_architectures | 1 | 2 | 4 | 3 | 1 | 1 | 1 | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- fixed: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- adaptive: A-001 (Δprev 0.00) → A-002 (Δprev 0.65) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- search: A-003 (Δprev 0.00) → A-015 (Δprev 0.43) → A-019 (Δprev 0.35) → A-019 (Δprev 0.00) → A-025 (Δprev 0.30)
- self_evolving: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-004 (Δprev 0.00) → A-006 (Δprev 0.15) → A-006 (Δprev 0.00)
- agm_v1_cold: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- agm_v1_memory: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- agm_v2_cold: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- agm_v2_memory: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)

## Transfer results

- agm_v1_memory: delta_quality_mean=0, delta_quality_first_step=0, delta_time_to_target_logical_s=—, delta_architecture_evaluations=0, delta_adaptation_cost=0, delta_total_cost=0, cold_reached_target=False, memory_reached_target=False
- agm_v2_memory: delta_quality_mean=0, delta_quality_first_step=0, delta_time_to_target_logical_s=—, delta_architecture_evaluations=0, delta_adaptation_cost=0, delta_total_cost=0, cold_reached_target=False, memory_reached_target=False
- cross-domain principle instantiations attempted: 5; completed with a recorded test: 1; principle reuse per agent: {'fixed': None, 'adaptive': None, 'search': None, 'self_evolving': None, 'agm_v1_cold': None, 'agm_v1_memory': None, 'agm_v2_cold': 0, 'agm_v2_memory': 1}

## Adaptation economics

- agm_v2_cold: decisions {'ADAPT': 10}; mean decision error -0.7106
- agm_v2_memory: decisions {'ADAPT': 10}; mean decision error -0.7026

## Failures

- failed/refused/violating executions: 5
  - fixed step 1 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - self_evolving step 1 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - fixed step 2 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - fixed step 3 task 2cf46e3a49f036de: architecture_invalid_for_environment
  - fixed step 4 task 2cf46e3a49f036de: architecture_invalid_for_environment
- rejected architectures: {'fixed': 0, 'adaptive': 0, 'search': 0, 'self_evolving': 0, 'agm_v1_cold': 0, 'agm_v1_memory': 0, 'agm_v2_cold': 524, 'agm_v2_memory': 524}
- contradicted principles: {'fixed': 0, 'adaptive': 0, 'search': 0, 'self_evolving': 0, 'agm_v1_cold': 0, 'agm_v1_memory': 0, 'agm_v2_cold': 0, 'agm_v2_memory': 1}

## Counterexamples

- lowest per-step quality per agent: fixed 0.000, adaptive 0.000, search 0.400, self_evolving 0.000, agm_v1_cold 0.000, agm_v1_memory 0.000, agm_v2_cold 0.000, agm_v2_memory 0.000

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['fixed', 'adaptive', 'search', 'agm_v1_memory']; dominated = ['self_evolving', 'agm_v1_cold', 'agm_v2_cold', 'agm_v2_memory']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'fixed': '—', 'adaptive': '—', 'search': '30.31', 'self_evolving': '181.4', 'agm_v1_cold': '133.7', 'agm_v1_memory': '133.7', 'agm_v2_cold': '133.7', 'agm_v2_memory': '133.7'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: none. Agents with zero failures: ['adaptive', 'search', 'agm_v1_cold', 'agm_v1_memory', 'agm_v2_cold', 'agm_v2_memory'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
