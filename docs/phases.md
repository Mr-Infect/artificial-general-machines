# Development phases — status for v0.2

## v0.1 (frozen at tag `agm-v0.1-freeze`)

| phase | scope | status |
|---|---|---|
| 1 | host validation, repository, Python environment | done |
| 2 | Architecture IR + compiler | done |
| 3 | sandbox | done (Docker; process executor for tests/programs) |
| 4 | exercise environment | done (network, scientific) |
| 5 | baseline agents | done (B0–B3) |
| 6 | telemetry | done |
| 7 | adaptation economics | done (v1) |
| 8 | structural memory | done (patterns) |
| 9 | AGM controller | bounded prototype only |
| 10 | cross-domain experiments | done, 3 seeds, negative transfer result |

## v0.2 (spec section 36 order)

| phase | scope | status |
|---|---|---|
| 1 | freeze v0.1 | done: tag, `docs/v0.2_baseline.md`, benchmark reproduced twice bit-for-bit |
| 2 | architectural principle representation | done: `memory/principles.py` |
| 3 | principle extraction | done: rule-based, 6 rules, hypotheses only |
| 4 | third domain | done: planning, `docs/domain_planning.md` |
| 5 | observability event model | done: 25 event types, replayable, `events` table + `raw_events.jsonl` |
| 6 | live dashboard | done: AGM Architecture Observatory, live/demo labelled |
| 7 | replay | done: ReplayController with play/pause/step/speed/jump, state at any event |
| 8 | 30-seed baseline | run by `scripts/run_v02_experiments.py` (exp1) |
| 9 | transfer matrix | same program (exp2 sources/targets) |
| 10 | principle ablation | same target runs (memory modes) |
| 11 | memory ablation | same |
| 12 | adaptation economics ablation | same (economic / always / never) |
| 13 | architecture distance analysis | `experiments/analysis.py` (exp6) |
| 14 | LLM architecture proposer | interface + validation pipeline implemented (`baselines/llm_proposer.py`), **not run** (no API key on the host; by design last) |
