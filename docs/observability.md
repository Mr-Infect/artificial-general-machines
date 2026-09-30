# Observability: event model, Observatory, replay

## Event model (`observability/events.py`)

A run is one (experiment, agent) pair: `run_id = <experiment_id>.<agent>`. Every important action
emits an `Event` with `run_id, experiment_id, agent, seq, timestamp, step, logical_time_s,
event_type, domain, environment_state, constraints, candidate_architectures, selected_architecture
(readable alias A-001…), architecture_hash, reason, expected_gain, estimated_cost, actual_cost,
payload`. Sequence numbers are per run and contiguous, so `verify_ordering` can check replayability
and `fold_state(events, upto)` recomputes the complete machine state after any event.

Events are appended to `results/<experiment_id>/raw_events.jsonl` and mirrored to the `events`
table. The 25 event types of the specification are all emitted: the runner emits RUN_STARTED,
ENVIRONMENT_OBSERVED, CONSTRAINT_CHANGED, VALIDATION_*, COMPILATION_STARTED, EXECUTION_*,
RESOURCE_LIMIT_HIT, RESULT_EVALUATED, RUN_COMPLETED for every agent; the AGM v0.2 agent emits
CAPABILITY_REQUIREMENT_INFERRED, MEMORY_RETRIEVED, PRINCIPLE_RETRIEVED, ARCHITECTURE_GENERATED /
REJECTED / SELECTED, ADAPTATION_DECISION, DO_NOT_ADAPT, PRINCIPLE_CREATED / SUPPORTED /
CONTRADICTED, TRANSFER_ATTEMPTED / COMPLETED. Other agents' selections are emitted by the runner.

Nothing here observes "thought": these are records written by the code that made each decision.

## AGM Architecture Observatory (`observability/api.py`, `observability/static/`)

```bash
uvicorn observability.api:app --host 127.0.0.1 --port 8100
```

Panels A–I of the specification: environment, current architecture (id, parent, lineage,
distances, components, topology, resource estimate), decision pipeline with the active stage,
candidate table (distance, estimated quality/cost/latency, status and reason), chronological
decision trace, resource graph (CPU, memory, latency, evaluations, adaptation cost), lineage graph
with node selection (diff vs parent, performance, environment, reason, parent/children,
experiment), memory panel (retrieved / new / supported / contradicted principles, transfer
candidates, confidence), experiment panel.

**Live mode** tails the `events` table over a WebSocket (`/ws/runs/{id}`, 0.5 s polling); the
numbers on screen are the ones the runner just wrote. **Demo mode** replays a stored run. Both are
labelled in the header. There are no synthetic numbers anywhere in the client.

## Replay controller

Play / pause / step forward / step backward / 0.5× 1× 10× / jump to seq / click on the trace or
the progress bar. Selecting an event folds the recorded events up to that point into the complete
state (the JS fold mirrors `fold_state`; `/runs/{id}/state?at=<seq>` gives the server-side version
for cross-checking).

## Human-readable explanation

`/runs/{id}/explanations` derives Observed / Retrieved / Considered / Rejected / Selected /
Expected / Actual / What was learned per step strictly from recorded events (`explanations()`).

## API

`GET /runs`, `/runs/{id}`, `/runs/{id}/events?after=`, `/runs/{id}/state?at=`,
`/runs/{id}/explanations`, `/runs/{id}/architectures`, `/runs/{id}/lineage`, `/runs/{id}/principles`,
`/runs/{id}/transfer`, `/architectures/{hash}`, `/architectures/{hash}/lineage`,
`/architectures/{hash}/diff/{other}`, `/experiments/{id}/pareto`, `WS /ws/runs/{id}`.
All accept `db_path=` to point at another SQLite file (the experiment program uses per-worker files).
