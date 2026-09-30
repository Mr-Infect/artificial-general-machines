# Experiments, provenance, reports

## Manifest

```yaml
experiment:
  name: cross_domain_transfer_001
  seed: 42
  repeats: 3                         # seeds 42, 43, 44
  task: {type: anomaly_detection, domain: network, dataset_size: 2000, noise: 0.1, anomaly_rate: 0.03}
  environment: {cpu: 1, memory_mb: 512, latency_ms: 2000, network: true, available_capabilities: all}
  objective: {quality_threshold: 0.85}
  budget: {max_seconds: 120, max_cost: 0.25, step_timeout_s: 30}
  schedule: {steps: 5, step_seconds: 10, validation_fraction: 0.2}
  events:
    - {t: 10, type: memory_reduction, params: {memory_mb: 120}}
    - {t: 20, type: network_loss}
    - {t: 20, type: capability_removal, params: {capabilities: [model:large_reasoner]}}
    - {t: 30, type: latency_reduction, params: {latency_ms: 800}}
    - {t: 40, type: priority_increase, params: {priority: 3}}
  agents:
    - {name: fixed, type: fixed}
    - {name: adaptive, type: adaptive}
    - {name: search, type: search, max_evaluations: 8}
    - {name: self_evolving, type: self_evolving, mutations_per_step: 2}
    - {name: agm_cold, type: agm, memory: {read: false, write: true}}
    - {name: agm_memory, type: agm, memory: {read: true, write: true}}
```

A `suite:` manifest lists experiments that share a `memory_db`; that is how Domain A experience
becomes available to `agm_memory` in Domain B.

Event types: memory_reduction, cpu_reduction, network_loss, network_restore, latency_reduction,
capability_removal, capability_addition, deadline_reduction, priority_increase, cost_budget_reduction.

## Provenance (`results/<id>/provenance.json`)

git commit + dirty flag, manifest and its hash, seed, dataset id, split sizes, executor, sandbox
image id, registry keys, simulated model configuration, python version, host sample, timestamps,
per-agent summaries. Every IR executed is in the `architectures` table.

## Replay

`python -m experiments.run --replay <experiment_id>` re-runs from the stored manifest and compares
`(architecture_hash, predictions_sha)` per agent-step. Deterministic given the seed except where an
agent's choice depends on measured wall time (deadline pressure); divergences are listed.

## Metrics

Per step: quality, accuracy, latency_ms, cpu_time_s, memory_mb, cost, violations, failed, novelty.
Per agent: quality mean/min/final, steps at target, time to target (logical and wall), search time,
architecture evaluations, model calls, tokens, cpu time, max memory, execution/adaptation/total
cost, constraint violations, failures, novelty, distinct architectures, memory reads/writes.

Quality is F1 on batches that contain anomalies and specificity on batches that contain none.

## Reports

`report.md` per experiment: aggregate table, resource-normalized comparison (quality per $, per
CPU-second, adaptation overhead), Pareto fronts, per-step quality with the architecture used,
environment transitions, every adaptation decision with its inputs, transfer deltas (agents named
`X_memory` vs `X_cold`), and all failed or violating executions.

`python -m experiments.report --suite <tag>`: means with bootstrap 95% CIs over seeds, target-reached
fractions, and paired memory−cold deltas. With one seed the CI collapses to the mean and the report says so.
