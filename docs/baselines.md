# Baselines and the bounded AGM prototype

| id | agent | what it may do | sandbox evaluations |
|---|---|---|---|
| B0 | `fixed` | one IR, forever | none |
| B1 | `adaptive` | pick among presets in `configs/adaptive_library.yaml` by rules over telemetry | none |
| B2 | `search` | evaluate up to `max_evaluations` valid points of `configs/architecture_space.yaml` on the validation slice; re-search when invalid or after `patience` misses | yes |
| B3 | `self_evolving` | mutate its own IR (never code) and hill-climb on validation quality | yes |
| B4 | `agm` | see below | yes, gated by adaptation economics |

## B4 components

* **Environment model**: the telemetry snapshot (observable profile, recent quality, recent violations, budgets).
* **Objective model**: target quality, priority, remaining cost and deadline.
* **Capability model**: registry ∩ currently available capabilities (network-requiring tools drop without network).
* **Architecture synthesis** (bounded): candidates from (1) structural-memory patterns adapted to the
  current capability model, (2) heuristic templates over available components/models/verification,
  (3) local threshold variations of the current architecture. All candidates pass the same validation.
* **Adaptation economics** (`runtime/economics.py`): ADAPT / PARTIAL_ADAPT / DO_NOT_ADAPT / TERMINATE
  from expected quality, expected improvement, search/synthesis/validation/execution cost, deadline and
  budget. Every decision and its inputs are stored in `adaptation_decisions`.
* **Structural memory** (`memory/structural.py`): after each step a pattern is stored with the
  environment signature, task characteristics, IR, resources, quality, latency, failures, constraints,
  adaptation cost, success/failure conditions. Retrieval is by environment + task similarity weighted by
  quality; retrievals from other experiments are marked with `transfer_history`.
* **Architectural transfer**: memory persists in a SQLite file named by the manifest; `agm_memory` in
  Domain B reads what `agm_cold` wrote in Domain A. The benchmark measures whether that helps.

Nothing in B4 modifies code, leaves the registry, or receives information the other agents do not.
