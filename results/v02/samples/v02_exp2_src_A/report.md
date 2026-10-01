# Experiment report: v02_exp2_src_A

## Hypothesis

Exp 2 source run in domain A: AGM v0.2 in exploration mode (evaluates up to 8 candidates per step regardless of early target) writes patterns and principles.

## Experimental conditions

- id `exp_1790769628_146f1611a0cc`, seed 3001, executor process, git `d07b0f410b21`, manifest `4fdab23a2b905ed0`
- task {'type': 'anomaly_detection', 'domain': 'network', 'dataset_size': 2000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': True, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events [{'t': 10.0, 'type': 'memory_reduction', 'params': {'memory_mb': 80}}, {'t': 20.0, 'type': 'network_loss', 'params': {}}, {'t': 20.0, 'type': 'capability_removal', 'params': {'capabilities': ['model:large_reasoner', 'tool:search', 'component:lookahead_planner']}}, {'t': 30.0, 'type': 'latency_reduction', 'params': {'latency_ms': 800}}, {'t': 40.0, 'type': 'priority_increase', 'params': {'priority': 3}}]
- objective quality ≥ 0.0; budget {'max_seconds': 120.0, 'max_cost': 0.25, 'step_timeout_s': 30.0}

## Baselines

- agm_v2_src: {"type": "agm_v2", "max_evaluations": 8, "memory_mode": "full", "economics_mode": "economic", "explore_all": true, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_src_A_1.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v02/memory/exp2_src_A_1.sqlite"}}

## Results

| metric | agm_v2_src |
|---|---|
| quality_mean | 0.9852 |
| quality_min | 0.963 |
| quality_final | 0.963 |
| time_to_target_logical_s | 0 |
| architecture_evaluations | 16 |
| adaptation_cost | 0.008 |
| execution_cost | 0.0025 |
| total_cost | 0.0105 |
| cpu_time_s | 1.123 |
| max_memory_mb | 53.1 |
| constraint_violations | 0 |
| failures | 0 |
| novelty_mean | 0.2 |
| distinct_architectures | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- agm_v2_src: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 0; completed with a recorded test: 0; principle reuse per agent: {'agm_v2_src': 0}

## Adaptation economics

- agm_v2_src: decisions {'ADAPT': 4, 'DO_NOT_ADAPT': 6}; mean decision error -0.02743

## Failures

- failed/refused/violating executions: 0
- rejected architectures: {'agm_v2_src': 527}
- contradicted principles: {'agm_v2_src': 0}

## Counterexamples

- lowest per-step quality per agent: agm_v2_src 0.963

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['agm_v2_src']; dominated = []
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'agm_v2_src': '123.1'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['agm_v2_src']. Agents with zero failures: ['agm_v2_src'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
