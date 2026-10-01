# Experiment report: v03_train_network

## Hypothesis

v0.3 training run in network with the training regime library; AGM v0.3 in exploration mode writes memory.

## Experimental conditions

- id `exp_1790781786_2ba8eaf9d0b3`, seed 10003, executor process, git `32e0a66326c4`, manifest `6c0ad9fec75cfcc7`
- task {'type': 'anomaly_detection', 'domain': 'network', 'dataset_size': 3000, 'noise': 0.1, 'anomaly_rate': 0.03, 'verification_required': False, 'priority': 1}
- environment {'cpu': 1.0, 'memory_mb': 512, 'latency_ms': 2000, 'network': False, 'privacy': 'local_only', 'energy_budget': 1.0, 'available_capabilities': 'all', 'verification_cost_factor': 1.0}
- events []
- objective quality ≥ 0.0; budget {'max_seconds': 600.0, 'max_cost': 1.0, 'step_timeout_s': 30.0}

## Baselines

- agm_train: {"type": "agm_v3", "max_evaluations": 6, "explore_all": true, "memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/train_3.sqlite"}, "principle_memory": {"read": true, "write": true, "db": "/home/cool/AGM-Laboratory/results/v03/memory/train_3.sqlite"}}

## Results

| metric | agm_train |
|---|---|
| quality_mean | 0.832 |
| quality_min | 0 |
| quality_final | 0.9412 |
| time_to_target_logical_s | 30 |
| architecture_evaluations | 36 |
| adaptation_cost | 0.018 |
| execution_cost | 0.0045 |
| total_cost | 0.0225 |
| cpu_time_s | 2.59 |
| max_memory_mb | 59.97 |
| constraint_violations | 0 |
| failures | 0 |
| novelty_mean | 0.1111 |
| distinct_architectures | 1 |

## Statistical analysis

Single seed: no confidence intervals at this level. Cross-seed statistics (mean, median, sd, bootstrap CI, paired deltas, effect sizes) are produced by `python -m experiments.analysis`.

## Architecture changes

- agm_train: A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00) → A-001 (Δprev 0.00)

## Transfer results

- cross-domain principle instantiations attempted: 0; completed with a recorded test: 0; principle reuse per agent: {'agm_train': 0}

## Adaptation economics

- agm_train: decisions {'ADAPT': 12, 'DO_NOT_ADAPT': 6}; mean decision error -0.147

## Failures

- failed/refused/violating executions: 0
- rejected architectures: {'agm_train': 1960}
- contradicted principles: {'agm_train': 0}

## Counterexamples

- lowest per-step quality per agent: agm_train 0.000

## Interpretation

- Pareto (quality ↑, latency ↓, memory ↓, adaptation cost ↓, evaluations ↓, failure rate ↓): non-dominated = ['agm_train']; dominated = []
- resource-normalized (quality per adaptation cost; distinct from raw quality): {'agm_train': '46.22'}

## Limitations

- One seed; simulated model costs; synthetic domains; the sandbox measures in-container RSS, not cgroup memory.

## Conclusion

- Agents that reached the target quality 0.0 at some step: ['agm_train']. Agents with zero failures: ['agm_train'].
- This is one run. No agent is declared successful here; success criteria are evaluated across seeds in the v0.2 research report.
