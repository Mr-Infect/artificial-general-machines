# Experiment report: v02_exp2_tgt_A

## Hypothesis

Exp 2/3/4/5/7 target run in domain A: cold vs transferred memory (from each other domain and merged), memory-mode and economics ablations, AGM v0.1 with warm architecture memory.

## Experimental conditions

- id `exp_1790769753_6adb99a64c61`, seed 4000, executor process, git `cad9294d4e82`, manifest `954ca28ca2b3a6f0`
- task {'type': 'anomaly_detection', 'domain': 'network', 'dataset_size': 2000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': True, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events [{'t': 10.0, 'type': 'memory_reduction', 'params': {'memory_mb': 80}}, {'t': 20.0, 'type': 'network_loss', 'params': {}}, {'t': 20.0, 'type': 'capability_removal', 'params': {'capabilities': ['model:large_reasoner', 'tool:search', 'component:lookahead_planner']}}, {'t': 30.0, 'type': 'latency_reduction', 'params': {'latency_ms': 800}}, {'t': 40.0, 'type': 'priority_increase', 'params': {'priority': 3}}]
- objective quality ≥ 0.0; budget {'max_seconds': 120.0, 'max_cost': 0.25, 'step_timeout_s': 30.0}

## Baselines

- v2_cold: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "economic", "explore_all": false}
- v2_from_B: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_B_to_A_0.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_B_to_A_0.sqlite"}}
- v2_from_C: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_C_to_A_0.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_from_C_to_A_0.sqlite"}}
- v2_warm_full: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "full", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_full.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_full.sqlite"}}
- v2_warm_architecture: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "architecture", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_architecture.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_architecture.sqlite"}}
- v2_warm_principle: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "principle", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_principle.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_principle.sqlite"}}
- v2_warm_task: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "task", "economics_mode": "economic", "explore_all": false, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_task.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_task.sqlite"}}
- v2_always_adapt: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "always_adapt", "explore_all": false}
- v2_never_adapt: {"type": "agm_v2", "max_evaluations": 6, "memory_mode": "none", "economics_mode": "never_adapt", "explore_all": false}
- v1_warm_architecture: {"type": "agm", "max_evaluations": 6, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_warm_A_0_v1.sqlite"}}

## Results

| metric | v2_cold | v2_from_B | v2_from_C | v2_warm_full | v2_warm_architecture | v2_warm_principle | v2_warm_task | v2_always_adapt | v2_never_adapt | v1_warm_architecture |
|---|---|---|---|---|---|---|---|---|---|---|
| quality_mean | 0.981 | 0.981 | 0.981 | 0.981 | 0.981 | 0.981 | 0.981 | 0.981 | 0.981 | 0.981 |
| quality_min | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 |
| quality_final | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 | 0.9524 |
| time_to_target_logical_s | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| architecture_evaluations | 2 | 3 | 2 | 3 | 3 | 3 | 2 | 5 | 1 | 3 |
| adaptation_cost | 0.001 | 0.0015 | 0.001 | 0.0015 | 0.0015 | 0.0015 | 0.001 | 0.0025 | 0.0005 | 0.0015 |
| execution_cost | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 | 0.0025 |
| total_cost | 0.0035 | 0.004 | 0.0035 | 0.004 | 0.004 | 0.004 | 0.0035 | 0.005 | 0.003 | 0.004 |
| cpu_time_s | 0.3746 | 0.3834 | 0.3627 | 0.3766 | 0.3826 | 0.3949 | 0.3378 | 0.486 | 0.3147 | 0.3612 |
| max_memory_mb | 66.73 | 66.73 | 66.73 | 66.73 | 66.73 | 66.73 | 66.73 | 66.73 | 66.73 | 66.73 |
| constraint_violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| novelty_mean | 0.2 | 0.0125 | 0.0125 | 0.0125 | 0.0125 | 0.0125 | 0.0125 | 0.2 | 0.2 | 0.0125 |
| distinct_architectures | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- v2_cold: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_from_B: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- v2_from_C: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_warm_full: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- v2_warm_architecture: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- v2_warm_principle: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)
- v2_warm_task: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_always_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v2_never_adapt: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)
- v1_warm_architecture: A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00) → A-002 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 30; completed with a recorded test: 6; principle reuse per agent: {'v2_cold': 0, 'v2_from_B': 2, 'v2_from_C': 0, 'v2_warm_full': 2, 'v2_warm_architecture': 0, 'v2_warm_principle': 2, 'v2_warm_task': 0, 'v2_always_adapt': 0, 'v2_never_adapt': 0, 'v1_warm_architecture': None}

## Adaptation economics

- v2_cold: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.01425
- v2_from_B: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.01776
- v2_from_C: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.01506
- v2_warm_full: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.01555
- v2_warm_architecture: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.01332
- v2_warm_principle: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.01316
- v2_warm_task: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.01358
- v2_always_adapt: decisions {'ADAPT': 10}; mean decision error -0.01349
- v2_never_adapt: decisions {'ADAPT': 2, 'DO_NOT_ADAPT': 8}; mean decision error -0.01219

## Failures

- failed/refused/violating executions: 0
- rejected architectures: {'v2_cold': 527, 'v2_from_B': 527, 'v2_from_C': 527, 'v2_warm_full': 527, 'v2_warm_architecture': 527, 'v2_warm_principle': 527, 'v2_warm_task': 527, 'v2_always_adapt': 524, 'v2_never_adapt': 528, 'v1_warm_architecture': 0}
- contradicted principles: {'v2_cold': 0, 'v2_from_B': 2, 'v2_from_C': 0, 'v2_warm_full': 2, 'v2_warm_architecture': 0, 'v2_warm_principle': 2, 'v2_warm_task': 0, 'v2_always_adapt': 0, 'v2_never_adapt': 0, 'v1_warm_architecture': 0}

## Counterexamples

- lowest per-step quality per agent: v2_cold 0.952, v2_from_B 0.952, v2_from_C 0.952, v2_warm_full 0.952, v2_warm_architecture 0.952, v2_warm_principle 0.952, v2_warm_task 0.952, v2_always_adapt 0.952, v2_never_adapt 0.952, v1_warm_architecture 0.952

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['v2_warm_full', 'v2_warm_task', 'v2_never_adapt']; dominated = ['v2_cold', 'v2_from_B', 'v2_from_C', 'v2_warm_architecture', 'v2_warm_principle', 'v2_always_adapt', 'v1_warm_architecture']
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'v2_cold': '981', 'v2_from_B': '654', 'v2_from_C': '981', 'v2_warm_full': '654', 'v2_warm_architecture': '654', 'v2_warm_principle': '654', 'v2_warm_task': '981', 'v2_always_adapt': '392.4', 'v2_never_adapt': '1962', 'v1_warm_architecture': '654'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['v2_cold', 'v2_from_B', 'v2_from_C', 'v2_warm_full', 'v2_warm_architecture', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt', 'v2_never_adapt', 'v1_warm_architecture']. Agents with zero failures: ['v2_cold', 'v2_from_B', 'v2_from_C', 'v2_warm_full', 'v2_warm_architecture', 'v2_warm_principle', 'v2_warm_task', 'v2_always_adapt', 'v2_never_adapt', 'v1_warm_architecture'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
