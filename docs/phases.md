# Development phases (Section 18) — status for v0.1

| phase | scope | status |
|---|---|---|
| 1 | host validation, repository, Python environment | `scripts/validate_host.py`, layout, `.env.example`, `requirements.txt` |
| 2 | Architecture IR + compiler | `architecture/`, `compiler/` |
| 3 | sandbox | `sandbox/`, `runtime/executor.py` |
| 4 | exercise environment | `environments/synthetic.py` (network, scientific), `environments/scoring.py` |
| 5 | baseline agents | `baselines/` B0–B3 |
| 6 | telemetry | `telemetry/`, SQLite `telemetry` + `environment_events` |
| 7 | adaptation economics | `runtime/economics.py`, `adaptation_decisions` table |
| 8 | structural memory | `memory/structural.py`, `architectural_patterns` table |
| 9 | AGM controller | **bounded prototype only** (`baselines/agm.py`): no self-modification, no open-ended invention |
| 10 | cross-domain experiments | `experiments/manifests/cross_domain_transfer_001.yaml`, suite report |

## Next steps that would improve measurement before adding features

* More seeds per condition (the suite report's CIs are only as good as `repeats`).
* A held-out-domain (Domain C) to test whether transfer generalizes beyond the pair it was tuned on.
* Host-side cgroup sampling of container memory to cross-check the in-container RSS measurement.
* An IR proposer interface backed by an LLM that can only emit IR (Section 4), evaluated as another agent.
