# Laboratory architecture

```
manifest (YAML) ──► ExperimentRunner ──► per agent, per step:
                        │                  1. DynamicEnvironment.advance(t)  → transitions recorded
                        │                  2. Telemetry.snapshot()           → the agent's only view
                        │                  3. agent.select_architecture(ctx) → Architecture IR
                        │                  4. validate (schema, registry, current environment)
                        │                  5. compile_ir → CompiledSpec (data only)
                        │                  6. executor.run(spec, batch)      → Docker sandbox
                        │                  7. score(predictions, labels)    → Evaluation
                        │                  8. persist Execution/Evaluation/Metrics; agent.observe()
                        └──► provenance.json, report.md/json, telemetry_*.jsonl, SQLite
```

## Trust boundaries

* Agents never see labels, the event schedule, or the dataset; they receive `AgentContext` with a
  telemetry snapshot and can ask the harness to evaluate a candidate on the shared validation slice.
  Every such evaluation is counted as an *architecture evaluation* and its cost charged as adaptation cost.
* The sandbox receives only records (no labels), the compiled spec and the carried memory state, via stdin.
  It has no network, no host filesystem, no capabilities, a read-only root, a PID limit and hard
  CPU/memory/timeout limits. It returns JSON on stdout.
* No generated code is executed anywhere. The IR is interpreted by a fixed runner.

## Fairness across baselines

Same dataset (seeded), same validation slice, same environment schedule, same sandbox limits, same
scoring, same registry. Agents differ only in how they choose an IR.

## Time

Logical time advances `step_seconds` per step; the event schedule is expressed in logical seconds
(Section 12's t=0,10,20,30,40). Wall time consumed by sandbox runs and agent deliberation is
accumulated separately and compared against the deadline; both are recorded.
