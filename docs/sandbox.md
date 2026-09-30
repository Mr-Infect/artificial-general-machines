# Sandbox

`sandbox/runner.py` is a stdlib-only interpreter for compiled specs. The Docker image is
`python:3.10-slim` plus that one file, tagged by the content hash of the runner and Dockerfile so
changes rebuild automatically. The experiment's provenance records the image id.

Container flags: `--network none --cpus N --memory Mm --memory-swap Mm --pids-limit 64
--cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp:noexec,nosuid,size=32m
--user 65534:65534`. Input is piped over stdin; nothing is mounted; no Docker socket.

Each run returns stdout, stderr, exit code, runtime, CPU time (from `getrusage` inside the
container), max RSS, timeout flag, resource violation (`timeout`, `memory_limit_exceeded:*`,
`architecture_invalid_for_environment`) and the result artifact (predictions, confidences,
accounting, carried state).

`ProcessExecutor` runs the same runner locally. It enforces only the CPU-time timeout and flags
memory overruns after the fact; it is for tests and Docker-less hosts.

## Components available to the runner

| kind | names |
|---|---|
| perception | statistical_detector (rolling z), anomaly_detector (MAD), rate_detector (first difference), range_validator (declared ranges), consistency_checker (cross-feature relations) |
| reasoning | direct, sequential, parallel, hierarchical (ambiguous band refined by the model), iterative (threshold adjusted toward expected contamination) |
| models | small_reasoner (mean combiner), large_reasoner (multi-scale, consistency-weighted; ~4× CPU), classifier, embedding_model (used by vector memory) |
| memory | none, episodic (carried stats), vector (nearest past anomaly boosts), graph (co-flag edges) |
| verification | none, rule_based (agreement), model_based (re-score with a model), execution_based (re-run with another window) |

Costs, latencies and token counts are the registry's simulated profiles (`configs/capabilities.yaml`).
