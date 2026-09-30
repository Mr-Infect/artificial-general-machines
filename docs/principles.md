# Architectural principles (v0.2)

`memory/principles.py` replaces the v0.1 `environment → architecture` memory with

```
environmental conditions → architectural principle → rationale → applicability conditions
→ failure conditions → resource characteristics → candidate transfer domains
```

## Representation

`ArchitecturalPrinciple` is a plain Pydantic record, rendered as a readable card by `render()`:

| field | meaning |
|---|---|
| `structural_pattern` | constraints over abstract component *roles* (`broad_filter`, `robust_estimator`, `change_detector`, `rule_check`, `consistency_check`, `expensive_analyzer`) and IR fields (reasoning types, model cost class, memory/verification types, "cheap stage before verification"). Roles come from `configs/capabilities.yaml`, so the same pattern can be instantiated in any domain's vocabulary. |
| `preconditions`, `resource_conditions`, `objective_conditions`, `uncertainty_conditions` | readable, testable `Condition`s (`memory_mb <= 128`, `noise >= 0.1`, `verification_required == True`, ...) |
| `expected_effect` | metric → expectation, e.g. `quality: ">= target"`, `memory_mb: "lower estimate than alternatives"` |
| `evidence` | list of `Evidence` records, each with an epistemic `kind`: **observed** (the source measurement), **hypothesized** (the generalization), **supported**, **contradicted**, **inconclusive** |
| `status` | `UNTESTED`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INCONCLUSIVE` (derived, never set by hand) |
| `confidence` | `supports / (supports + contradictions + 1)`; never reaches 1.0 |
| `known_failures`, `supporting_experiments`, `contradicting_experiments`, `source_architectures`, `source_domains`, `candidate_transfer_domains` | provenance and transfer bookkeeping |

No embedding is used anywhere. Causality is never asserted: the `observed` evidence is a
comparison of measured validation results; the `hypothesized` evidence is the generalization the
rule proposes; only later tests under new conditions produce `supported`/`contradicted` evidence.

## Extraction (`extract_principles`)

Deterministic rules over one step's `DecisionRecord` (environment, task, selected architecture with
its measured validation result, rejected candidates with theirs, execution result, adaptation cost):

| rule | fires when |
|---|---|
| `cheap_filter_before_verification` | selected has a verification stage over cheap components and a rejected candidate without verification scored lower |
| `minimal_perception_under_tight_memory` | memory ≤ 128 MB, single component, cheap model, target met |
| `ensemble_perception_under_uncertainty` | ≥2 components, noise ≥ 0.1, best rejected single component scored lower |
| `cheap_model_suffices` | cheap model selected, a rejected expensive-model candidate did not score higher |
| `rule_roles_for_verification_tasks` | task requires verification, rule/consistency roles present, alternatives without them scored lower |
| `expensive_analysis_only_when_affordable` | expensive stage selected and beat cheap alternatives by ≥ 0.05 |

Conditions are bucketed from the observed environment (e.g. memory ≤ 128 vs ≥ 129) so that a
principle applies to a *range*, not to one point.

## Memory (`PrincipleMemory`)

Stored in the `principles` table. `merge` folds a new hypothesis into an existing principle with the
same rule and structural pattern (evidence accumulates, source domains widen). `retrieve(ctx)` ranks
principles by applicability (fraction of conditions that hold; unknown facts count half) ×
(0.5 + confidence); contradicted principles are penalized but never hidden.

## Instantiation (`instantiate`)

Builds an architecture satisfying the pattern from the *target* capability model, role by role. If
a required role has no component in the target domain the principle is not instantiable there, and
that is recorded rather than worked around.

## Validation (`PrincipleEvaluator`)

`record_test` compares a principle-derived architecture against the best non-principle alternative
evaluated under the same new conditions: Δquality ≥ −0.02 (and resource effect met, if promised) →
`supported`; Δ < −0.05 or execution failure → `contradicted`; in between → `inconclusive`. The
experiment that produced a principle can never validate it. Status policy: one supporting test is
`INCONCLUSIVE`; `SUPPORTED` needs ≥2 supports with contradictions ≤ supports/3; any mix is
`PARTIALLY_SUPPORTED`; ≥2 contradictions and no supports is `CONTRADICTED`.

`evaluate_offline` tests a principle across a list of conditions outside an experiment
(used by tests and `scripts/validate_principles.py`).
