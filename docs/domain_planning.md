# Domain C: resource-constrained planning

Implemented in `environments/planning.py`; executed by the planning branch of `sandbox/runner.py`
using the planning components declared in `configs/capabilities.yaml`. It reuses the Architecture IR
unchanged, but the computational vocabulary (candidate generation → filtering → feasibility /
forecasting → deferral planning → verification → commit) is different from the anomaly domains, and
the winning architectures are different (see the tuning table below).

## Task definition

A stream of jobs arrives over discrete ticks. The agent's architecture must decide, per batch of
arriving jobs, which jobs to commit (and, if it has a deferral-capable component, at which tick
before the deadline). Committed jobs consume resource capacity; when a tick's *realized* capacity is
exhausted the remaining committed jobs at that tick fail and incur a penalty.

## Environment variables (task and dataset)

| variable | meaning | manifest field |
|---|---|---|
| `dataset_size` | number of jobs | `task.dataset_size` |
| `noise` | scale of capacity bias/noise and per-job duration uncertainty | `task.noise` |
| `load` | mean demand relative to nominal capacity; `load = 1 + 10·anomaly_rate` so the existing manifest field is reused (0.03 → 1.3) | `task.anomaly_rate` |
| `seed` | dataset seed | `seed` |
| environment profile | CPU, memory, latency, network, capabilities, deadline, cost budget, priority, plus the same event schedule as the other domains | `environment`, `events` |

Every job record: `[tick, value, cost, est_duration, uncertainty, deadline]`. Hidden per job: the
true duration factor. Per tick: `nominal_capacity` (known) and `realized_capacity` (hidden for the
batch's ticks, revealed as history for earlier ticks).

## State transitions

Capacity follows regimes of 40–80 ticks; each regime has a level in [60, 140] units, a persistent
*bias* of realized vs. nominal in [−0.3, +0.1]·(1+noise), and a 30-tick sinusoidal modulation. Jobs
arrive at ~5 per tick with lognormal value, uniform cost × load, uniform estimate in [0.8, 1.2],
per-job uncertainty in [0.05, 0.6]·(0.5+noise), and deadlines 0–5 ticks after arrival. Realized
duration = estimate × (1 + N(0, uncertainty)).

Within an experiment the batch boundaries and environment events (memory reduction, capability
removal of `lookahead_planner`/`large_reasoner`, latency reduction, priority increase) create the
"changing resource availability" and "cost of adaptation" pressures; the capacity regimes create
"uncertain future state".

## Objective and scoring

`quality = clip(net_value / oracle_value, 0, 1)` per batch, where `net_value = Σ value(completed)
− 0.5·Σ value(failed)` from simulating the plan against hidden truth, and `oracle_value` is the
net value of a strong hidden-information plan (density-greedy with deferral inside the deadline
window plus an eviction-improvement pass; deterministic, not provably optimal, so quality can in
principle exceed 1 and is clipped). Precision/recall/F1 against the oracle's selection are recorded
as secondary metrics only.

Competing objectives: value vs. penalty (over-commitment), immediacy vs. deferral (deadlines), and
plan quality vs. compute/cost (the expensive components).

## Resource model

Components and their registry roles and costs:

| component | role | cost class | what it does |
|---|---|---|---|
| `priority_filter` | broad_filter | cheap | rank by value density |
| `risk_estimator` | robust_estimator | cheap | density discounted by duration uncertainty |
| `capacity_forecaster` | change_detector | cheap | estimates realized/nominal bias from history, fits jobs to the forecast |
| `feasibility_checker` | rule_check | cheap | fits jobs to nominal capacity in density order |
| `lookahead_planner` | expensive_analyzer | expensive (6× CPU, 24 MB) | deadline-aware multi-tick plan with deferral and improvement passes |

Reasoning types combine component scores as in the anomaly domains; `large_reasoner` re-plans at
three pessimism levels (≈4× CPU, 8× cost); `rule_based` verification trims to nominal capacity,
`execution_based` trims to a pessimistic capacity, `model_based` re-scores with the model. Episodic
memory carries the capacity-bias estimate across batches.

## Failure model

A committed job fails if its tick's realized capacity is exhausted before it runs, if it is assigned
outside `[arrival, deadline]`, or if its tick does not exist. Failed jobs cost 0.5 × value. Sandbox
failures (timeout, OOM, invalid architecture) are recorded exactly as in the other domains.

## Reproducibility

The dataset is a deterministic function of `(size, noise, load, seed)`; its id is the sha256 of that
tuple and it is cached in `datasets/planning_<id>.json`. The oracle plan and assignments are stored
with the dataset. The sandbox payload (`batch_payload`) is a pure function of the dataset and batch
range and never contains truth, labels, or realized capacities of the batch ticks.

## Reference tuning table (seed 1 / seed 2, noise 0.1, load 1.3, process executor)

| architecture | quality | cost |
|---|---|---|
| priority_filter only (threshold 0.5) | 0.607 / 0.519 | 0.0025 |
| feasibility_checker only | 0.760 / 0.683 | 0.0025 |
| priority+forecaster, episodic, execution_based | 0.744 / 0.744 | 0.0025 |
| forecaster+risk, episodic, rule_based | 0.790 / 0.721 | 0.0025 |
| priority+forecaster+lookahead, hierarchical large, episodic, execution_based | 0.793 / 0.729 | 0.0400 |
| priority+forecaster, iterative large ×2, episodic | 0.762 / 0.697 | 0.0600 |

The benchmark target for this domain is 0.75.
