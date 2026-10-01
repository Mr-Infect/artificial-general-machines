# Experiment report: v03_train_planning

## Hypothesis

v0.3 training run in planning with the training regime library; AGM v0.3 in exploration mode writes memory.

## Experimental conditions

- id `exp_1790781900_0852c2e3c527`, seed 10201, executor process, git `32e0a66326c4`, manifest `0bfb8d3cb4c9cccd`
- task {'type': 'resource_planning', 'domain': 'planning', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- agm_train: {"type": "agm_v3", "max_evaluations": 6, "explore_all": true, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/train_1.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/train_1.sqlite"}}

## Results

| metric | agm_train |
|---|---|
| quality_mean | 0.7419 |
| quality_min | 0.6525 |
| quality_final | 0.6525 |
| time_to_target_logical_s | 20 |
| architecture_evaluations | 42 |
| adaptation_cost | 0.021 |
| execution_cost | 0.0045 |
| total_cost | 0.0255 |
| cpu_time_s | 2.229 |
| max_memory_mb | 80.86 |
| constraint_violations | 0 |
| failures | 0 |
| novelty_mean | 0.03472 |
| distinct_architectures | 3 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- agm_train: A-006 (Δprev 0.00) → A-008 (Δprev 0.45) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-008 (Δprev 0.00) → A-260 (Δprev 0.60) → A-260 (Δprev 0.00) → A-260 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 2; completed with a recorded test: 2; principle reuse per agent: {'agm_train': 5}

## Adaptation economics

- agm_train: decisions {'ADAPT': 14, 'DO_NOT_ADAPT': 4}; mean decision error -0.04108

## Failures

- failed/refused/violating executions: 0
- rejected architectures: {'agm_train': 1787}
- contradicted principles: {'agm_train': 1}

## Counterexamples

- lowest per-step quality per agent: agm_train 0.653

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['agm_train']; dominated = []
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'agm_train': '35.33'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['agm_train']. Agents with zero failures: ['agm_train'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
