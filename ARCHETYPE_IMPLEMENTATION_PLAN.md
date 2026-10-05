# ARCHETYPE — implementation plan

*Learning the relationship between environment structure and computational organization.*

This is a new experimental phase on the existing laboratory. It is **not** AGM v0.4 and does not
reinterpret the AGM result: AGM v0.1–v0.3 concluded with verdict FAIL and that stands
(`docs/V0.3_RESEARCH_REPORT.md`). ARCHETYPE asks a narrower question (Hypothesis H, spec §0) and is
built so that it can fail.

Path note: the spec names `/home/cool/AGM-Laboratory/archetype/`. That path does not exist on this
host; the repository is `/home/ghost/artificial-general-machines`, so the module lives at
`archetype/` in this repository.

---

## 1. Inspection of the existing repository

### 1.1 Structure (tracked code, ~9.5k lines of Python)

```
architecture/   ir.py (ArchitectureIR, canonical hash, lineage), validate.py, distance.py (8-component distance, novelty levels)
compiler/       compile.py (IR -> sandbox execution spec + cost estimates)
sandbox/        runner.py (interprets compiled specs on data), Dockerfile
runtime/        executor.py (ProcessExecutor, DockerExecutor), economics.py, economics_v2.py
core/           models.py, ids.py, registry.py (CapabilityRegistry), db.py (SQLite, WAL, backup-API copies), api.py
environments/   synthetic.py, planning.py, regimes.py (hidden regimes, twins, false analogies), profile.py, scoring.py
baselines/      base.py (Agent, AgentContext), fixed, adaptive, search, self_evolving, agm, agm_v2, agm_v3, llm_proposer
memory/         structural.py, principles.py (ArchitecturalPrinciple, extraction, applicability decision), merge.py
observability/  events.py (EventLog, replay), api.py + static dashboard
telemetry/      telemetry.py
experiments/    manifest.py, run.py (ExperimentRunner), bundle.py, analysis.py, analysis_v03.py, report.py
scripts/        30-seed drivers (v0.2, v0.3), report writers, host validation
tests/          33 tests (all pass on this host)
```

### 1.2 Reusable infrastructure, and what is actually reused

| existing piece | reuse in ARCHETYPE |
|---|---|
| `experiments.analysis.describe / paired / ci_excludes_zero` (bootstrap 95% CI, paired deltas by seed, Cohen's d, sign counts) | **imported directly**; all ARCHETYPE statistics go through them |
| `experiments.manifest.manifest_hash`, `experiments.run.git_commit` | **imported directly** for provenance |
| `core.ids.new_id` | imported |
| driver pattern of `scripts/run_v03_experiments.py` (one job per seed, multiprocessing pool, resumable, single-instance lock, per-job output shard, driver log) | **same pattern**; shards are per-job files so workers never share a SQLite writer (the v0.3 locking lesson) |
| SQLite conventions of `core/db.py` (WAL, busy timeout) | same conventions in a separate `results/archetype/archetype.sqlite`; AGM tables are not touched |
| conventions of `architecture/ir.py` (Pydantic, canonical JSON, `sha256[:16]` hash, lineage) and `architecture/distance.py` (separately reported distance components, no single arbitrary novelty score) | **conventions reused, code new** (see 1.3) |
| agent protocol of `baselines/base.py` (agents never touch the evaluator; every candidate evaluation goes through one counted, charged callback) | **same protocol**, new context class |
| principle status / evidence idea of `memory/principles.py`; TRUST/TEST/IGNORE/REJECT decision of AGM v0.3 | idea reused, representation new (spec §8, §28 need antecedent relations, contraindications, RETIRED) |
| pre-registration procedure of v0.3 (`docs/v0.3_design.md` + `registration.json` at a commit, verdict rule in code before the run) | **same procedure** |

### 1.3 Existing abstractions that cannot carry this experiment (and why new code is needed)

- **Architecture IR.** `ArchitectureIR` is a fixed stage layout (perception → reasoning → memory →
  verification) with enumerated types. It cannot express planner → parallel workers → aggregator,
  hypothesis → critic → revision loops, redundant consensus, hierarchical decomposition or
  conditional branching as *structure*. Spec §3.2 forbids reducing these to a parameter. ARCHETYPE
  therefore adds a compositional IR (`archetype/architecture/graph.py`) with the same conventions.
  The existing IR, compiler and sandbox runner are left untouched.
- **Environments.** Existing domains compute a real score from data with a fixed pipeline
  interpreter; there is no latent genome and no way to intervene on one property. Spec §4, §22, §23
  require a genome-driven generator and a hidden fitness function, which is new.
- **Sandbox.** `sandbox/runner.py` interprets only the old IR. ARCHETYPE architectures are pure data
  scored by a hidden fitness simulator; no generated code runs. Evaluations run in-process inside
  worker processes (≈1.5 M evaluations in the full run; one subprocess per evaluation is not
  feasible). Every record states `executor: inprocess-simulator`. This is a deliberate deviation
  from "Docker/process execution" and is listed in the limitations.
- **Experiment runner.** `experiments/run.py` is bound to the old IR/DB schema; ARCHETYPE gets its
  own runner following the same loop (shared environment per seed, identical budgets, counted
  evaluations, provenance).

### 1.4 Things in the existing lab that would violate the ARCHETYPE anti-cheating rules

These are the reasons the existing agents and environments are **not** reused as-is:

1. `core/registry.py` exposes `params.role` and `params.domains` for every component, and
   `memory/principles.py::instantiate` maps principles through those role labels. That is a manually
   supplied cross-domain mapping (forbidden by §20).
2. `AgentContext.domain` / `task["domain"]` hands the domain name to the agent.
3. `environments/regimes.py::_twin_transform` renames features, but twins keep the same role labels
   and the same registry, so "blind" transfer in v0.3 still had a role dictionary.
4. Regime names and schedules are stored in the same dataset dict that payloads are cut from
   (kept away from agents by convention only).
5. Memory rows store `source_domain` names that an agent can read back.

ARCHETYPE enforces the boundary structurally (§5 below) and tests it.

---

## 2. What ARCHETYPE is, in one page

```
EnvironmentGenome (hidden, 15 properties in [0,1])
        │  evaluator only
        ├──► hidden fitness(genome, role-graph of architecture) + noise ──► score (surface scale)
        │
        └──► surface realization (randomized): observation channels, task spec, primitive inventory
                         │  learner-visible
                         ▼
   agent ── builds composition trees from local primitives ── evaluate(arch) ── counted, charged
```

- **Training world**: 10 structural families × 3 surfaces. Agents explore with a generous budget.
  ARCHETYPE additionally runs counterfactual experiments through anonymous intervention knobs.
- **Freeze**: learned memory is serialized and hashed; no learning-rule or memory writes afterwards
  except per-environment working state.
- **Transfer world**: 10 structural families × 3 surfaces. 5 *isomorphic* families (same latent
  region as a training family; unseen vocabulary themes, shapes, scales, primitive inventories) and
  5 *compositional hold-out* families (factor combinations never seen in training, spec §32).
- **False-analogy world**: 10 families × 3 surfaces. Each is matched to a training family: same
  vocabulary theme, same shapes, same *observable* latent properties, but hidden-only properties
  changed so that the organization that was best in the matched training family is harmful.
- **Interventional pairs**: for the frozen learner, environment pairs that differ in exactly one
  latent property (spec §11, §12).

### 2.1 The hardest honesty point (stated before any result exists)

The relationship between environment structure and organization is **planted by the experimenter**
in the hidden fitness function, and the same author writes the generator and the learner. A positive
result therefore can only mean: *a simple interpretable learner can recover a planted
structure→organization relation and carry it across surface randomization, compositional hold-outs
and false analogies, better than search / memory / surface matching*. It cannot show that such
relations exist in natural task environments. The report must say this in the executive summary
regardless of verdict. Mitigations: the learner's observation encoder is a generic battery of
descriptive statistics (not one estimator per latent), several latent properties have no
observational proxy at all, and the fitness function has interactions and noise.

---

## 3. Design

### 3.1 Latent structure (`archetype/latent_structure/`)

`EnvironmentGenome`: `dependency_depth, branching_factor, observation_noise, temporal_correlation,
state_volatility, verification_cost, action_reversibility, resource_constraint, adversariality,
delayed_feedback, information_decay, parallelizability, coupling, uncertainty, failure_cost`.
Canonical hash; `intervene(property, value)`; `distance(a, b)`.

Two classes of property:
- **observable-proxy** (leave statistical traces in observation channels): dependency_depth,
  branching_factor, parallelizability, observation_noise, temporal_correlation, state_volatility,
  resource_constraint, verification_cost, delayed_feedback, action_reversibility.
- **hidden-only** (no trace in observations; only visible through evaluation outcomes): coupling,
  adversariality, information_decay, uncertainty, failure_cost.

`families.py`: structural *factors* (each pins 2–3 properties) and families as factor pairs.
Training families use 10 pairs; compositional hold-out families use 5 pairs absent from training;
isomorphic families reuse 5 training pairs; false-analogy families copy the observable properties of
a training family and flip hidden-only ones. Unpinned properties are sampled per seed. In the
training world some hidden-only properties are deliberately *confounded* with observable ones (e.g.
wide dependency graphs always come with low coupling); false analogies break that confounding.

### 3.2 Architecture space (`archetype/architecture/`)

`graph.py` — compositional IR, canonicalized and hashed like the existing IR:
`unit(p) | serial[...] | parallel[...]+merge | conditional(router)[...] | loop(body, gate, n) |
hierarchy(decomposer, body, depth)`; constraints: max depth, max branching, max nodes.
Well over 1000 valid configurations per environment (counted in a test).

`primitives.py` — each environment has its own inventory (8–12 primitives, random names, 1–2 grades
per function, sometimes combined-function primitives, sometimes a function missing). Learner-visible
per primitive: random name, **interface signature** (fan-out arity, fan-in, gates, stateful,
selects, tunes), cost/latency/memory in a randomized currency scale. Evaluator-only: abstract role
set, strength.

`roles.py` (evaluator only) — `ArchitectureGraph`: the tree normalized to abstract roles
(decomposition, execution, aggregation, verification, memory, control, adaptation); organization
classifier for the ten organizations ARCH_1…ARCH_10; role-level structural distance with separately
reported components; novelty relative to a reference set; `MEMORIZED_TRANSFER` threshold.

`generate.py` — random valid trees and mutation operators (shared by every searching agent).

*Design limitation, flagged now:* primitives carry an interface signature, which is the one fixed
shared language of the lab (like a tool schema). Without it no agent, including plain search, could
form valid compositions. Recovering a primitive's function from its signature is therefore **not**
what the experiment tests; what is tested is the mapping environment-structure → organization.

### 3.3 Hidden fitness (`archetype/latent_structure/fitness.py`)

Mechanistic-style terms with interactions, all hidden: error compounding with dependency depth and
its relief by decomposition; consensus gain shrinking with coupling; verification value scaling with
noise × failure cost × adversariality and paying verification cost; critic loops needing immediate
feedback; memory helping under temporal correlation and hurting under decay × volatility; parallel
speed-up under parallelizability with interference under coupling; branching under volatility;
explore/exploit under uncertainty × reversibility; resource penalties; stochastic evaluation noise
and failure events. Outputs per evaluation: score (surface scale and direction), cost, latency,
memory, failed flag, structural-operation count.

**Architectures are not executed on the observation data.** Fitness is simulated from the genome as
spec §23 requires. The "task" (anomaly detection, experiment repetition, scheduling …) is a surface.

### 3.4 Surface realization (`archetype/environments/`)

`surface.py` randomizes: vocabulary theme and tokens, feature names, feature order, affine numeric
ranges and signs, series length and width, item ids, task label and output label, score scale and
direction, primitive names and order, cost currency. Channels (fixed kinds, randomized content):
`series` (signal driven by noise / temporal correlation / volatility), `relations` (a work-item
dependency graph: depth, branching, width), `episodes` (action/outcome log: feedback lag, undo
fraction), `limits` (budget, price sheet). Hidden-only properties influence none of them.

`world.py` — `Environment` (evaluator side, owns genome + fitness) and `LearnerView` (the only object
an agent receives: observations, task spec, primitives, `evaluate()`, budget). The third surface
realization of every family is fully token-scrambled (random hex vocabulary) for K7.

### 3.5 Learner (`archetype/learner/`, `archetype/memory/`, `archetype/transfer/`)

Interpretable, no neural network, no LLM:

1. **Observation encoder** — generic battery of ~30 scale/sign/order-invariant statistics over the
   channels (moments, autocorrelations at several lags, difference outliers, cross-correlations,
   graph depth/degree/width statistics, lag and undo statistics, relative prices).
2. **Experience** — in training environments: base architecture, paired add/remove tests of each
   *architectural transformation* (add staged gate, parallelize with fan-in, redundant consensus,
   decompose / deepen hierarchy, prepend memory, wrap in critic loop, add router, add tuner, change
   executor grade), plus search. Rows: (features, transformation, Δquality, Δcost, opaque token).
3. **Relation model** — per transformation, a shallow regression tree (depth ≤ 3) over features;
   each leaf becomes a `Principle` (antecedent = conjunction of threshold relations, predicted
   transformation, expected Δquality/Δcost, confidence from a Beta posterior, support, contradiction
   count, applicability range, contraindications, opaque sources, transfer and counterfactual
   history, status HYPOTHESIS/SUPPORTED/CONDITIONAL/CONTRADICTED/RETIRED). Negative leaves become
   contraindications of sibling principles.
4. **Counterfactual learning (training only)** — for each principle, request interventions through
   anonymous knobs on a supporting environment, re-encode, predict, measure. Wrong prediction with a
   feature change → refine conditions (CONDITIONAL). Wrong prediction with *no* feature change →
   mark the principle hidden-sensitive (must be TESTed, never TRUSTed). Repeated failure → trust
   decay → RETIRED (forgetting; memory precision is measured).
5. **Transfer confidence** — P(transformation helps | features) from posterior × antecedent margin;
   decisions per principle TRUST / TEST / REJECT / IGNORE and per environment REUSE / MODIFY /
   BUILD_NEW / ABSTAIN. "Always reuse" is impossible by construction: REUSE requires a matched
   principle above the confidence threshold.
6. **Architecture constructor** — builds a composition tree from *local* primitives by signature
   (reconstruction; training architectures are never stored as trees of training primitives in a
   form that could be instantiated by name).
7. **Economics** — stop when expected gain of the next evaluation is below its cost.
8. **Regime detection** — feature shift or incumbent score drop between phases triggers re-inference.

Each of the nine ablations (§16) switches off exactly one of these.

### 3.6 Baselines (`archetype/baselines/`)

B0 fixed, B1 adaptive workflow (presets, degradation-triggered), B2 architecture search (random +
local mutation over the same grammar, same budget), B3 task memory (keyed by task label/surface),
B4 architecture memory (signature-level patterns of best training architectures, tried first),
B5 principle memory (AGM-style unconditional principles, no contraindications, no counterfactuals),
B6 always adapt, B7 never adapt, B8 random structural transfer, B9 surface-similarity transfer
(nearest training environment by names/shapes/raw ranges/labels), B10 latent oracle (reads the
genome; analysis only, excluded from all criteria), B11 ARCHETYPE.

All memory baselines train on the same training environments with the same exploration budget.
ARCHETYPE's cold fallback uses the same search code as B2.

### 3.7 Run protocol and metrics (`archetype/experiments/`, `archetype/metrics/`)

Per (seed, environment, agent): phase 1 with a fixed evaluation budget; in half of the environments
a hidden shift of one latent property; phase 2 with a smaller budget. After every evaluation the
agent declares an incumbent; the evaluator records its noise-free utility (never shown to agents).

- reference optimum per environment from an evaluator-side reference search (noise-free);
  *useful* = incumbent closes ≥ 80% of the gap between single-pass and the reference optimum;
- **evaluations-to-useful** (censored at budget + 1), **useful-evaluation reduction** vs B2 and vs
  ARCHETYPE-without-structural-memory, paired by seed;
- structural transfer success, false-transfer rate, missed-transfer rate, reconstruction success,
  counterfactual prediction accuracy, structural-analogy AUROC/AUPRC/calibration (learner confidence
  vs noise-free truth; compared with surface similarity), adaptation cost, quality, novelty;
- selective risk / coverage for ABSTAIN; memory precision; secondary metrics of §17;
- latent distance vs learner-predicted transferability vs surface distance.

Statistics: unit of analysis is the seed; bootstrap 95% CIs and paired deltas via the existing
`experiments.analysis` functions; nothing is collapsed into one score.

### 3.8 Provenance and replay

Every job records: git commit + dirty flag, seed, genome hash, surface seed, primitive-grammar
version, learner version, full configuration and its hash, timestamp, executor, budgets. All
randomness derives from `(seed, family, surface, agent)` strings through SHA-256, so any job can be
re-executed and compared by record hash (`python -m archetype.experiments.replay <job>`); a test
asserts bit-identical replay.

---

## 4. Anti-cheating enforcement

- Agents receive only `LearnerView`. The `Environment` lives in the harness; `evaluate` is a closure.
- Test: serialize everything reachable from a `LearnerView` and assert that no genome property name,
  no genome value, no family id, no role name and no organization label appears.
- Test: modules under `archetype/learner`, `archetype/transfer`, `archetype/memory` and all baselines
  except the oracle do not import `archetype.latent_structure` or `archetype.architecture.roles`.
- Memory stores opaque random tokens for source environments, never family ids or themes.
- Sanity-run leakage probe: a classifier from learner-visible *names/tokens* to family must be at
  chance on scrambled surfaces; shuffling genome↔surface assignment must destroy ARCHETYPE's benefit.
- B10 (oracle) is the only consumer of the genome and is excluded from every criterion.

## 5. Development discipline

- **Development seeds** (0–9) are used for building, calibrating the *environment* (so that no single
  architecture is near-optimal everywhere, search is neither trivial nor hopeless, false analogies
  are really harmful) and for the 3-seed sanity run.
- **Registered seeds** (1000–1029) are never run before registration.
- Order: phases 1–11 of spec §41 → 3-seed sanity (3 families, 1 transfer, 1 false analogy) → stop if
  leakage / trivial selection / broken transfer → freeze (commit) → write
  `docs/archetype_registration.md` + `archetype/reports/registration.json` with hypotheses, metrics,
  thresholds, K1–K8, S1–S10 and the verdict rule in code → commit → 30-seed run → report.
- After registration: no change to thresholds, metrics, learner, environments or search budget. Bugs
  that invalidate measurements are fixed in the open, recorded in the report, and affected jobs are
  re-run from scratch; anything else stays as measured.
- Verdict ∈ {BREAKTHROUGH_CANDIDATE, PARTIAL_SUPPORT, NO_DISTINCT_CAPABILITY, INCONCLUSIVE}. A
  BREAKTHROUGH_CANDIDATE automatically triggers the replication of §35 (30 new seeds, 3 new surface
  realizations, 1 new false-analogy family) before it is reported as such.

## 6. Module layout

```
archetype/
  latent_structure/  genome.py  families.py  fitness.py
  architecture/      graph.py  primitives.py  generate.py  roles.py (evaluator only)
  environments/      surface.py  world.py
  learner/           encoder.py  transformations.py  relation.py  archetype_agent.py
  memory/            principles.py  (store, forgetting, precision)
  transfer/          decisions.py  constructor.py
  baselines/         base.py  simple.py  memory_agents.py  transfer_agents.py  oracle.py
  experiments/       protocol.py  run.py  driver.py  sanity.py  interventions.py  replay.py  registration.py
  metrics/           core.py  analysis.py
  reports/           write_report.py  (outputs: archetype_final.md, breakthrough_events.jsonl, registration.json)
  tests/
```

Changes outside `archetype/`: `pyproject.toml` test path (so plain `pytest` runs both suites),
`.gitignore` (raw ARCHETYPE results untracked), this plan, the registration document.

## 7. Known limitations (written before any run)

1. Planted structure and a single author for generator and learner (§2.1).
2. Simulated fitness; architectures do not process data.
3. Interface signatures make primitive function recoverable for every agent.
4. In-process execution instead of the Docker/process sandbox.
5. Channel kinds (`series`, `relations`, `episodes`, `limits`) are a fixed sensor API.
6. Development seeds were seen by the developer; only registered seeds count as evidence.
