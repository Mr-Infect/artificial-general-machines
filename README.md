# Artificial General Machines

### A pre-registered falsification study of architectural self-determination, and what its failure taught us

> **Status: concluded. Verdict of the final experiment: FAIL.**
> Three rounds of increasingly hostile experiments (3 seeds, then 30 seeds, then 30 seeds under hidden regime changes with blind and false-analogy transfer) did not find a measurable capability that separates an "Artificial General Machine" from architecture search plus memory plus heuristics. This repository publishes the instrument, every analysis table, the plots, the pre-registration, and the negative result exactly as it was measured. Nothing was tuned after the fact to make the machine look better.

---

## Table of contents

1. [The idea in one paragraph](#1-the-idea-in-one-paragraph)
2. [The hypothesis](#2-the-hypothesis)
3. [Why build a laboratory instead of a demo](#3-why-build-a-laboratory-instead-of-a-demo)
4. [The instrument](#4-the-instrument)
5. [Round one, v0.1: does structural memory help across domains?](#5-round-one-v01-does-structural-memory-help-across-domains)
6. [Round two, v0.2: are there transferable principles at all?](#6-round-two-v02-are-there-transferable-principles-at-all)
7. [Round three, v0.3: the kill experiment](#7-round-three-v03-the-kill-experiment)
8. [Results of v0.3 in detail](#8-results-of-v03-in-detail)
9. [What the machine actually told us](#9-what-the-machine-actually-told-us)
10. [Why it failed: five candidate explanations](#10-why-it-failed-five-candidate-explanations)
11. [The mysteries this experiment touches](#11-the-mysteries-this-experiment-touches)
12. [New questions, and the answers the data already gives](#12-new-questions-and-the-answers-the-data-already-gives)
13. [Future scope: the one experiment worth running next](#13-future-scope-the-one-experiment-worth-running-next)
14. [What was observed and what was not demonstrated](#14-what-was-observed-and-what-was-not-demonstrated)
15. [Repository structure](#15-repository-structure)
16. [Reproducing everything](#16-reproducing-everything)
17. [Honesty notes and limitations](#17-honesty-notes-and-limitations)
18. [Citation and license](#18-citation-and-license)

---

## 1. The idea in one paragraph

Modern AI systems are built around a fixed computational organization: a model, a set of tools, a workflow, a verification step, a memory. Humans then tune that organization by hand or by search. The **Artificial General Machine (AGM)** hypothesis asked whether the *organization itself* could become something a machine learns: a machine that recognizes when its current architecture has become inappropriate for its environment, infers what kind of organization is now needed, decides whether changing itself is worth the cost, constructs and evaluates a different architecture, and carries that structural understanding into an unfamiliar problem. Not a bigger model. Not a better workflow found by search. A machine whose object of learning is *how computation should be organized*.

This repository is the attempt to find out whether that capability exists in a measurable form. It does not.

## 2. The hypothesis

The hypothesis evolved as the experiments grew stricter, but its core never changed.

**v0.1 (architectural self-determination).** An agent that can reorganize its own architecture from a registry of primitives, guided by structural memory of what worked before, should adapt to a new domain better than a fixed agent, a preset-switching adaptive agent, a random/greedy architecture search, or a self-evolving (mutation-based) agent, when all of them run on identical data, limits and scoring.

**v0.2 (transferable principles).** Beyond remembering architectures, the machine should extract *principles* of computational organization (structural pattern + conditions under which it was useful + epistemic status), test them, and reuse them to reduce the cost of adapting to a genuinely different domain.

**v0.3 (the full claim, pre-registered).**
> AGM learns structural relationships between environmental conditions and computational organization (conditions → architectural choice → outcome → confidence → applicability → epistemic status), detects regime changes from observations alone, adapts only when economically justified, constructs materially different architectures, and transfers this knowledge to environments with different surface representation but the same structural relationships, and does *not* transfer it to environments with similar surface but different structure.

The v0.3 hypothesis was registered in [docs/v0.3_design.md](docs/v0.3_design.md) together with seven kill criteria and a fixed verdict rule *before* any run. The registration commit is recorded in [results/v03/registration.json](results/v03/registration.json).

## 3. Why build a laboratory instead of a demo

It is easy to build an agent that rewrites its own architecture and to show a video of it doing something impressive. It is hard to show that the rewriting *is the reason* for the result and not an artifact of search, memory, or the environment being easy. From the first day the project was therefore specified as a scientific instrument:

- **Identical conditions.** Every compared agent sees the same data, the same seed, the same environment schedule, the same resource limits, the same sandbox runner and the same scoring. Comparisons are paired by seed.
- **Baselines that steal the credit.** Fixed, adaptive (preset switching), search (same primitive space as AGM), self-evolving (mutation), and later task-memory and architecture-memory agents, always-adapt and never-adapt ablations. If any of them explains the result, the AGM gets no credit.
- **Hidden ground truth.** The agent never sees regime labels; the lab records the hidden truth separately for post-hoc analysis only.
- **Raw measurements, not a score.** Mean, median, standard deviation, bootstrap 95% confidence intervals, Cohen's d on paired differences, win/loss/tie counts, failure counts and missing counts for every comparison. Nothing is collapsed into a single number.
- **Never declare success in code.** No code path in this repository is allowed to print "AGM succeeded". The analysis prints the pre-registered criteria and what the data did to them.
- **Sandboxed execution.** Generated architectures run in a locked-down Docker container (no network, read-only filesystem, memory and CPU limits, no host access). A process executor exists for Docker-less hosts and long programs; every experiment records which executor produced it.
- **Full provenance and replay.** Git commit, manifest hash, seed, registry hash, environment, every event in order. Any run can be replayed step by step in the observability dashboard.

## 4. The instrument

```
                   experiment manifest (YAML)
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      environment         agents (14)       capability registry
   (domain + hidden    fixed · adaptive ·   components with roles,
    regime schedule)   search · memory ·    cost classes, domains
            │          AGM + ablations            │
            │                 │                   │
            │        Architecture IR (Pydantic, canonical hash,
            │        lineage, structural distance, novelty level)
            │                 │
            │            compiler → execution spec + cost estimates
            │                 │
            └──────► sandbox runner (Docker or process) ◄───────┘
                              │
                 telemetry · events · SQLite · raw_events.jsonl
                              │
          analysis (paired stats, kill criteria) → report.md → dashboard
```

**Domains.** Three synthetic but structurally different domains were built so that the *right* architecture differs between them:

| domain | task | what a good architecture needs |
|---|---|---|
| A, network | anomaly detection in telemetry batches | cheap statistical filter, stratified handling, verification only under noise |
| B, scientific | verification of hypotheses against noisy measurements | reasoning depth, verification cost trade-off |
| C, planning | resource-constrained scheduling scored against an oracle plan | a planner component, hierarchical structure under tight capacity |

**Regimes (v0.3).** Each run of 9 steps passes through three hidden computational regimes in seeded random order (calm, turbulent, starved in training; three held-out combinations H1–H3 in transfer). A regime changes the data-generating process (noise, volatility, anomaly rate) and the resource constraints (memory, CPU, verification cost, availability of the expensive model, failure penalty). Constraint changes are observable through telemetry; the data regime is not labelled and must be inferred.

**Twins and false analogies (v0.3).**
- **Blind transfer Y.** Twins of each domain with renamed features and components, permuted feature order and affine-transformed numerical ranges. Same hidden structure, different vocabulary. A machine that learned *structure* should benefit here.
- **False analogy Z.** Environments with *identical* vocabulary to a training domain but different structure (rule violations only; slow drift only; exact capacity with slack deadlines). A machine that learned structure should *refuse* to apply its prior here.

**The AGM.** The v0.3 machine has a regime detector (constraint changes plus quality drop plus observation shift), a principle memory with positive and negative principles, an applicability decision for every retrieved principle (TRUST / TEST / IGNORE / REJECT / ADAPT, derived from status, confidence and conditions, never from the environment name), an economics module (gain = improvement + resource benefit + risk reduction; cost = money + time + failure risk; settled against actual cost to give a decision error), a synthesis step over the full primitive space, and architecture memory. Each of these can be switched off, which gives the ablations.

## 5. Round one, v0.1: does structural memory help across domains?

Three seeds, domains A and B, five agents. The AGM with structural memory from domain A was compared against the same AGM cold-started on domain B.

**Result: no benefit, slight harm.** Memory changed quality on domain B by −0.015 (95% CI [−0.044, 0]) over three seeds. The frozen runs are in `results/v0.1_freeze/` and were reproduced bit-for-bit twice before v0.2 began (tag `agm-v0.1-freeze`).

The question at that point was whether three seeds were simply too few. v0.2 was built to answer that and to ask something more precise.

## 6. Round two, v0.2: are there transferable principles at all?

v0.2 added a third domain, an explicit principle representation with epistemic states (UNTESTED, SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, INCONCLUSIVE), rule-based extraction (six positive templates, no language model), principle validation under conditions that did not produce them, a strengthened economics with decision error, an eight-component architecture distance and five novelty levels, a real-time observability platform, and a 30-seed program with a full 3×3 transfer matrix and ablations. 330 experiments in all.

**Headline numbers (30 seeds, paired by seed, bootstrap 95% CIs).**

| transfer direction | Δ adaptation cost, memory − cold | significant? | principle tests (supported / contradicted / inconclusive) |
|---|---|---|---|
| B → A | +0.0011 | worse | 3 / 73 / 4 |
| C → A | +0.0003 | worse | 0 / 26 / 6 |
| A → B | 0 | none | 5 / 24 / 5 |
| C → B | −0.0003 | **better** | 11 / 15 / 7 |
| A → C | +0.0004 | worse | 0 / 30 / 0 |
| B → C | +0.0002 | worse | 6 / 13 / 5 |

- The 30-seed repeat of the v0.1 comparison measured Δ quality −0.004 [−0.011, 0] with 28 of 30 pairs tied: the v0.1 negative result was not noise hiding a benefit.
- Transferred memory reduced adaptation cost in **one** of six directions and increased it significantly in four.
- Across all cells, 181 principle tests came back contradicted, 27 inconclusive and 25 supported.
- Removing principle memory and keeping only architecture memory was *cheaper* in domains A and C.
- Economics: the economic mode did produce DO_NOT_ADAPT decisions (20% in A, 7% in B, under 1% in C), always-adapt spent more evaluations without higher quality, never-adapt was cheapest. The machine's mean decision error in domain A (realized minus expected net value) was −0.12 quality units: it systematically overestimated the value of adapting.

The pre-registered v0.2 criteria were met by the letter (criterion D required a significant cost reduction in *any* cell, and one cell delivered). The research report ([docs/V0.2_RESEARCH_REPORT.md](docs/V0.2_RESEARCH_REPORT.md)) therefore answers the question as **"weak and direction-dependent; not a general capability"**, states that the criterion was too lenient, keeps it unchanged, and tightens it for v0.3. That is the only time a criterion was judged lenient, and the judgment was made in the direction of *more* severity.

## 7. Round three, v0.3: the kill experiment

v0.3 was designed to give the hypothesis its best chance and, at the same time, every opportunity to die. Everything was registered in advance ([docs/v0.3_design.md](docs/v0.3_design.md)).

**Per seed:** three training runs (network, scientific, planning) in exploration mode write one memory file. Then six transfer runs (three blind twins Y, three false analogies Z) under held-out regime combinations, with **fourteen agents** on identical data, identical budgets (6 candidate evaluations per step), identical scoring and sandbox:

`fixed · adaptive · search · task_memory · architecture_memory · always_adapt · never_adapt · agm_cold · agm_full · agm_no_principle · agm_no_archmem · agm_no_negative · agm_no_economics · agm_no_regime`

30 seeds. 270 experiments. 0% missing. One executor (process) for all agents. About three hours on a 4-core, 8 GB machine.

**Kill criteria, fixed before the run.**

| id | what it tests | pass threshold |
|---|---|---|
| K1 regime detection | detects true transitions without labels | detection ≥ 0.7 within 2 steps, false alarms ≤ 0.3 per non-transition step |
| K2 architectural response | reorganizes when requirements change | reaches the new regime's target within 3 steps in ≥ 60% of needed cases, with a structural change in ≥ 50% of those |
| K3 economic adaptation | sometimes correctly refuses to adapt | DO_NOT_ADAPT share in [0.1, 0.9] and accuracy ≥ 0.7 |
| K4 blind structural transfer | training knowledge helps in twins | significant reduction in evaluations-to-useful (agm_full − agm_cold) in ≥ 2 of 3 Y environments, none significantly worse |
| K5 negative-transfer avoidance | does not apply priors to false analogies | not significantly worse than cold in any Z environment, and REJECT/IGNORE rate in Z higher than in Y |
| K6 baseline separation | not explainable by search or memory alone | beats both search and architecture_memory on evaluations-to-useful in ≥ 2 of 3 Y environments |
| K7 generalization | survives held-out seeds | K4 holds on seeds 15–29 alone |

**Verdict rule:** SUPPORT if all pass; PARTIAL SUPPORT if K1–K3 pass and K4 or K6 passes without K5 failing; FAIL if K4 and K6 both fail or K5 fails; INCONCLUSIVE otherwise. "These rules are not to be changed after the run."

## 8. Results of v0.3 in detail

Full tables: [results/v03/report.md](results/v03/report.md) (20 sections) and [results/v03/analysis/analysis.md](results/v03/analysis/analysis.md) (every paired comparison). Plots: [results/v03/plots/](results/v03/plots/).

### 8.1 Kill criteria

| id | result | evidence |
|---|---|---|
| K1 | **PASS** | detection rate 1.0 within 2 steps; false-alarm rate 0.084 |
| K2 | FAIL | 131 transitions needed a response; 62 (47%) reached the new target within 3 steps; of those, 20 (32%) did so with a structural change |
| K3 | FAIL | DO_NOT_ADAPT share 0.057 (below the 0.1 floor); accuracy 0.69 |
| K4 | FAIL | no Y environment improved; lab_assay and allocation got significantly *worse* |
| K5 | FAIL | no Z environment significantly worse than cold, but REJECT+IGNORE rate in Z (0.568) was not higher than in Y (0.571) |
| K6 | FAIL | agm_full beat both search and architecture_memory in 0 of 3 Y environments |
| K7 | FAIL | on seeds 15–29 alone: better in none, worse in allocation |

**Verdict: FAIL** (K4 and K6 both fail; K5 fails).

### 8.2 Blind transfer, Y (what the hypothesis most needed)

Means over 30 seeds. Lower evaluations-to-useful is better. Stars mark paired differences whose bootstrap 95% CI excludes zero.

| environment | agent | quality | evaluations-to-useful | adaptation cost (USD, simulated) |
|---|---|---|---|---|
| telemetry_grid (twin of network) | agm_cold | 0.726 | 3.67 | 0.0074 |
| | agm_full | **0.649** | 4.25 | 0.0085 |
| | search | 0.660 | 4.51 | 0.0133 |
| | architecture_memory | 0.729 | 3.44 | 0.0070 |
| lab_assay (twin of scientific) | agm_cold | 0.322 | 2.08 | 0.0089 |
| | agm_full | 0.377 | **3.21** | 0.0088 |
| | search | 0.387 | 3.10 | 0.0148 |
| | fixed | **0.410** | 0 | 0 |
| allocation (twin of planning) | agm_cold | 0.763 | 3.30 | 0.0079 |
| | agm_full | 0.746 | **4.58** | 0.0096 |
| | search | 0.705 | 6.60 | 0.0341 |
| | architecture_memory | 0.764 | 3.28 | 0.0079 |

Paired, agm_full − agm_cold:

- **telemetry_grid:** quality −0.078 [−0.134, −0.033]*, d = −0.54, 20 of 30 seeds worse. Evaluations-to-useful +0.49 (not significant).
- **lab_assay:** evaluations-to-useful +1.13 [+0.19, +2.27]*, d = 0.37. Quality +0.055 [+0.022, +0.089]*: the only place where warm memory raised quality, and it did so by spending *more* evaluations, not fewer. The fixed agent still had the highest quality of all fourteen agents here.
- **allocation:** evaluations-to-useful +1.38 [+0.44, +2.71]*, adaptation cost +0.0017*, time-to-regime-response +0.40 steps*, quality −0.016*. Worse on every primary metric.

Transfer outcome per seed (successful / harmful / tie): telemetry_grid 33% / 53% / 13%; lab_assay 27% / 40% / 33%; allocation 7% / 53% / 40%.

### 8.3 False analogy, Z (what the hypothesis needed to refuse)

| environment | agm_cold quality | agm_full quality | search quality | agm_full − cold, evaluations-to-useful |
|---|---|---|---|---|
| network_rules | 0.960 | 0.952 | 0.878 | −0.43 [−0.92, −0.06]* (better) |
| scientific_drift | 0.003 | 0.005 | 0.007 | +0.13 (n.s.) |
| planning_stable | 0.993 | 0.991 | 0.917 | −0.13 (n.s.) |

The AGM was *not* harmed in false-analogy environments. In network_rules it was even slightly faster. But it was not harmed because it recognised the false analogy: its REJECT+IGNORE rate was the same in Z as in Y. It was not harmed because the Z environments were easy. Every memory-based agent reached a near-ceiling quality there in one or two evaluations. (scientific_drift is a floor rather than a ceiling: no agent of any kind scored above 0.007, so the environment measured nothing. This is a defect in the environment, noted, not corrected after the fact.)

### 8.4 Ablations (variant − agm_full, Y environments)

| ablation | telemetry_grid | lab_assay | allocation |
|---|---|---|---|
| no principle memory | quality **+0.078*** | quality −0.055*, evaluations −1.13* | quality +0.016*, evaluations −1.38*, cost −0.0017* |
| no architecture memory | identical in every metric | identical | identical |
| no negative knowledge | evaluations −0.52 (n.s.) | ≈ 0 | evaluations −0.41* |
| no economics (always adapt) | cost +0.0004* | ≈ 0 | ≈ 0 |
| no regime detection | ≈ 0 | identical | ≈ 0 |

Three facts stand out:

1. **Removing principle memory helped in two of three twins.** The principle memory, the component that was supposed to carry structural understanding across vocabulary, was a net liability.
2. **Removing architecture memory changed nothing.** Across all 30 seeds and all three Y environments the agm_no_archmem run was tied with agm_full on every metric. The architecture memory was never the thing that decided.
3. **Removing regime detection changed almost nothing.** The constraint-only detector (agm_no_regime) also hit 100% detection. K1 passed because constraint changes are observable in telemetry, not because the machine inferred the data regime from observations. The pass is real but it is the easy half of the problem.

### 8.5 Economics and decisions

- DO_NOT_ADAPT share across all transfer runs: 5.7%. Unnecessary-adaptation rate per environment: 65% to 98%. The machine almost always chose to adapt, and most of the time it did not need to.
- Principle decisions by agm_full in telemetry_grid: TRUST 7, TEST 322, IGNORE 0, REJECT 1458, ADAPT 772. Over half of all retrieved principles were rejected outright; IGNORE was never selected in any environment; TRUST was selected 1 to 22 times per environment out of roughly 2,500 decisions.
- Principle tests in transfer: telemetry_grid 22 supported / 83 contradicted / 43 inconclusive; network_rules 8 / 107 / 0; scientific_drift 99 / 20 / 16 (in the environment where nothing could be measured).
- Training produced 24 principles per run in network, 22 in scientific, 6 in planning.

### 8.6 Regime response

Structural switches per run: 0.8 to 1.2 in twins, 0.1 to 0.6 in false analogies. Final structural distance from the initial architecture: 0.23 to 0.47 in twins. The machine *did* construct materially different architectures. Segments that never reached the regime target: 0.67 to 0.93 per run in twins. Constructing a different architecture and constructing the *right* one were different things.

## 9. What the machine actually told us

Strip away the hypothesis and look at what the instrument measured, in order of confidence:

1. **Regime detection from observable constraints is solved and trivial.** 100% detection, 8% false alarms, and the ablation shows the observation-based part added nothing on top of constraint changes.
2. **The machine reorganizes itself, often, and usually unnecessarily.** Roughly one structural switch per run, 65–98% of adaptations unnecessary, DO_NOT_ADAPT chosen 6% of the time with 69% accuracy.
3. **Memory of architectures is inert.** Switching it off changes nothing. Whatever the AGM does, it does from synthesis and principles, not from recalled architectures.
4. **Memory of principles is active and harmful on average.** It raises evaluations-to-useful and lowers quality in two of three blind twins, and the one twin where it raises quality (lab_assay) it does so at higher search cost, while a fixed agent still wins.
5. **The applicability decision cannot tell a twin from a false analogy.** REJECT+IGNORE rate 0.568 in Z versus 0.571 in Y. The machine rejected most of what it retrieved, everywhere, equally.
6. **Search alone is expensive but competitive; memory alone is cheap and competitive; AGM is neither best nor cheapest.** In every Y environment the agm_full result sits between search and architecture_memory on cost and below one of them on quality.
7. **Every result is paired, 30 seeds, zero failures, zero missing runs.** This is not a noisy result. The negative is clean.

The hypothesis predicted a specific signature: faster useful adaptation in twins, refusal in false analogies, and separation from search and memory. None of the three appeared.

## 10. Why it failed: five candidate explanations

These are explanations the data supports or cannot rule out. They are not excuses, and none of them was used to re-run anything.

**(a) Principles were extracted as correlations, not mechanisms.** The six extraction rules record "pattern P under conditions C scored well". They do not record *why*. A twin environment matches the conditions (same roles, same regime constraints) and triggers the principle, but the principle carries no test of whether the reason it worked still holds. 181 of 233 principle tests in v0.2 were contradicted; the v0.3 numbers are similar. A memory of correlations that are mostly wrong in new conditions is worse than no memory.

**(b) The applicability decision had no structural evidence to work with.** TRUST / TEST / IGNORE / REJECT / ADAPT were computed from epistemic status, confidence and condition match. Twins and false analogies produce the *same* condition match by construction (that was the point of the design). The decision mechanism was therefore blind to exactly the distinction it was supposed to make. The failure of K5 is the direct consequence: the machine had no signal that could separate same-structure from same-surface.

**(c) Economics overestimated the value of change.** Mean decision error of −0.12 quality units in v0.2, DO_NOT_ADAPT share 6% in v0.3. The gain model counted expected improvement from a candidate's validation score, which under regime noise is optimistic. The machine therefore kept paying for reorganisations that did not pay back.

**(d) The environments reward early convergence.** The cheapest valid architecture often already reached the regime target (the "ceiling" alternative explanation in the report). Where this holds, no prior can reduce evaluations-to-useful below what cold synthesis already achieves in two or three evaluations, and any prior that redirects the first evaluations elsewhere can only lose.

**(e) Roles are lab-provided labels.** Twins share component *roles* (filter, reasoner, verifier, planner) because the registry declares them. Transfer through roles is therefore partly transfer through a vocabulary the lab supplied. This made transfer easier, not harder, and the machine still did not benefit. If anything this strengthens the negative result.

What the data cannot distinguish is whether (a) and (b) are failures of this implementation or failures of the idea. That is the honest boundary of this study.

## 11. The mysteries this experiment touches

The experiments do not explain a major open problem in AI. They expose a mechanism that could be used to investigate several, and one connection in particular is worth stating.

There is a recurring puzzle in modern AI:

> **Why can the same underlying model behave extremely differently depending on how the computation around it is organized?**

Changing which tools are available, how subtasks are decomposed, whether agents run sequentially or in parallel, how much verification occurs, when memory is consulted, when computation is expanded, or when a system changes strategy can produce enormous differences even when the underlying model has not changed. The usual explanation is "we found a better architecture or workflow". This project probed a deeper possibility: **the organization of computation may itself be a learned variable.**

Five mysteries sit next to that possibility.

### 11.1 Why does scaling sometimes stop helping?

The default picture is: more parameters → more capability. But there are regimes where additional computation does not produce proportional gains. This framework suggests another factor:

```
capability = model capability × computational organization × environment fit
```

A powerful system with the wrong organization can perform worse than a smaller system with the right one. The Y results contain a miniature of exactly this: **agm_full had more architectural activity than agm_cold and lower quality.** More adaptation was not more intelligence.

### 11.2 Why does an AI sometimes get worse after learning?

The result that removing principle memory raised telemetry_grid quality by 0.078 is the kind of phenomenon that breaks the simple "more experience → better system" story. The chain the data suggests is:

```
experience → representation of previous structure → wrong analogy
           → wrong architectural decision → performance degradation
```

The general form: **knowledge is not inherently beneficial; it becomes harmful when the system cannot determine its domain of validity.** This is a research direction in its own right, and the laboratory measures it directly (the no_principle ablation is the instrument).

### 11.3 Why is transfer so difficult?

Humans are good at "this reminds me of something I have seen". The hard part is not recognizing similarity; it is knowing *that this similarity is relevant*. The Y/Z design isolates exactly that: the machine could reuse principles but could not determine when reuse was justified. The missing concept is **structural analogy selection**: not "have I seen something similar?" but "does the relationship between components in my previous problem remain valid here?" That question, not architecture generation, is what K5 measured, and it is where the machine was blind.

### 11.4 Why do agents overthink?

The economics ablation is a computation-allocation problem in miniature:

```
never adapt   → cheap, sometimes inadequate (quality −0.046* in telemetry_grid)
always adapt  → expensive, not better (cost +0.0004*, quality ≈ 0)
AGM economic  → chose to adapt 94% of the time; 65–98% of those were unnecessary
```

An intelligent system has to decide not only *what answer to produce* but *how much computation to reorganize before producing it*. That connects to test-time compute, reasoning budgets, tool selection, planning depth, verification and agentic loops. The deeper question: **can intelligence include deciding how much intelligence to deploy?** The machine built here could not; its decision error was consistently optimistic.

### 11.5 Why do different problems need different architectures?

Current research searches for good architectures, workflows and agent organizations. The deeper question is whether there is a **general principle relating environment structure to computational organization**:

```
environment → structural properties → computational requirements → architecture → performance
```

rather than

```
try architecture 1, try architecture 2, try architecture 3, ...
```

If such principles exist, architecture search is only the surface phenomenon. v0.3 did not find them. It found something more uncomfortable: a system can detect environmental change, manipulate architectures, remember principles and perform transfer experiments, and **those mechanisms do not automatically produce useful architectural intelligence.**

Perhaps the missing capability is not architecture *generation* but **architecture epistemology**: knowing *why* an architecture should work, *where* that reasoning applies, and *when* it should be abandoned.

```
                 COMPUTATION
                     │
                     ▼
               ARCHITECTURE
              ↗           ↖
             /             \
            ▼               ▼
      ENVIRONMENT ──── EXPERIENCE
```

The AGM built here treated these as things to manipulate. The open question is whether a system can learn the **relationships between them**: "when environmental property X occurs, organization Y tends to be useful, unless condition Z is present." That is not an architecture. That is a theory of computational organization, learned by the machine. This project did not discover it. It built the instrument that could tell you if someone did.

## 12. New questions, and the answers the data already gives

The failure sharpens the question set. For each, the answer this repository can already give, and what remains open.

**Q1. Is the problem the memory, or the use of the memory?**
*Answered, partially.* Architecture memory is inert (no_archmem identical to full). Principle memory is active and harmful on average. So the *content* of principle memory is what matters, and its content is mostly contradicted correlations. Open: whether a mechanistic principle representation (one that stores the reason, not the outcome) would flip the sign.

**Q2. Can a machine distinguish a twin from a false analogy using only what it observes?**
*Answered: not with condition matching.* REJECT+IGNORE rate was identical in Y and Z. Open: whether an explicit *probe* step (spend one evaluation testing the structural assumption behind a principle before trusting it) separates them. The TEST decision exists in the code but was treated as a weak TRUST, not as an experiment with a falsifiable prediction.

**Q3. Does regime detection need anything beyond observable constraints?**
*Answered: not in these environments.* The observation-based part added nothing (no_regime ablation tied). Open: environments where the data regime changes while constraints do not. Those were not built.

**Q4. Is adaptation worth it at all in these environments?**
*Answered: rarely.* never_adapt was cheapest everywhere and lost quality mainly where the regime genuinely required a change (telemetry_grid −0.046*, planning_stable −0.019*; elsewhere under 0.003). The economically correct policy in most segments was to do nothing, and the machine did not find it. Open: a gain model calibrated against realized outcomes rather than validation scores; the decision-error signal is recorded and could drive it.

**Q5. Why did search beat AGM on quality in two twins while costing three times more?**
*Answered by the numbers.* Search explores more widely with the same budget per step and never carries a prior that redirects its first evaluations. In allocation the AGM beat search on quality (+0.041*) and cost, which is the only Y cell where the AGM's narrow synthesis was an advantage. Open: whether the AGM's synthesis space (same primitives, different ordering) rather than its memory is what differed.

**Q6. Would a language model as architecture proposer change the result?**
*Not tested, by design.* The spec required the primary experiment to run without any LLM so that no result could be attributed to a model's prior knowledge of good architectures. An LLM proposer exists in the code (`baselines/llm_proposer.py`, validated with a stub backend, never run with a real model). It is the natural next ablation, but it answers a different question: "can a pre-trained model's knowledge of architectures help?" rather than "can a machine learn principles from its own experience?"

**Q7. Was the hypothesis falsified or was the implementation inadequate?**
*Cannot be separated by this data.* Three implementations (v0.1 structural memory, v0.2 principles, v0.3 principles + negatives + applicability + economics + regimes) each failed in the same direction. That is evidence against the idea as formulated, but a stronger implementation of the applicability decision could reopen it. Section 13 states what that experiment would have to be.

## 13. Future scope: the one experiment worth running next

Do not run another benchmark. The valuable next experiment is a single, harder, cleaner test:

> Construct one experiment where the machine learns a structural rule in environment A, encounters a completely different-looking environment B, and successfully reconstructs the correct computational organization **without sharing vocabulary, task representation, architecture, or primitives.**

Concretely, what v0.3 did not do and what such an experiment must do:

1. **Different primitives.** The twins in v0.3 shared the capability registry and its role labels. B must have its own registry, with no role names in common; roles must be *inferred* from behaviour (what a component consumes and produces and how its cost responds to load), not read from a label.
2. **Different task representation.** Not a renamed anomaly task but a task whose inputs and outputs have a different shape, and whose only commonality with A is the *relationship* between environmental pressure and the organization that handles it (for example: "when verification cost rises sharply, a cheap pre-filter before the expensive step becomes necessary").
3. **A principle representation that stores the mechanism.** Something like "a cheap filter before an expensive component is useful when the expensive component's cost is dominated by the volume it receives", with a test the machine can run in B to confirm the premise before trusting the conclusion.
4. **TEST as an experiment, not a weak TRUST.** Each retrieved principle makes a prediction; the machine spends one evaluation to check it; the result updates the principle's status *and* decides applicability. K5 should be re-stated as: "the probe rejects principles in Z significantly more often than in Y".
5. **Environments where data regimes change while constraints do not,** so that regime detection has to use observations.
6. **A calibrated economics,** with the gain model trained on realized decision error from earlier runs rather than on validation scores.
7. **The same kill criteria, same statistics, same honesty.** If K4, K5 and K6 all pass under conditions 1 to 3, that would be the first evidence that architectural self-determination is a capability and not a search. If they fail again, the hypothesis should be retired.

The instrument in this repository already supports 3 to 7 with modest changes and would need a new registry and environment for 1 and 2.

## 14. What was observed and what was not demonstrated

**Observed**
- Regime detection from observable constraints works (100% detection, 8% false alarms).
- Structural adaptation occurs (about one structural switch per run; final distance 0.23–0.47).
- Transfer occurs mechanically (principles retrieved, instantiated, evaluated in twins).
- Architectural memory can hurt (principle memory lowered quality in two of three twins).
- Adaptation has a measurable economic cost and the machine overpays for it (65–98% unnecessary).
- Blind transfer is unreliable (successful in 7–33% of seeds; harmful in 40–53%).

**Not demonstrated**
- A general law connecting environment to architecture.
- Reliable structural analogy (twin vs false analogy indistinguishable to the machine).
- Reliable architectural self-selection (47% reach the new target within 3 steps; 32% of those by structural change).
- Transferable architectural principles (no Y environment improved; two got worse).
- Separation from search plus memory (0 of 3 environments).
- A new form of machine intelligence.

## 15. Repository structure

```
.
├── README.md                     this document
├── LICENSE, CITATION.cff
├── pyproject.toml, requirements.txt, docker-compose.yml, .env.example
├── architecture/                 Architecture IR: schema, validation, canonical hash, lineage,
│                                 8-component structural distance, 5 novelty levels
├── compiler/                     IR → sandbox execution spec with cost/memory/latency estimates
├── sandbox/                      generic runner that interprets compiled specs; Dockerfile
├── runtime/                      Docker and process executors; adaptation economics v1 and v2
├── core/                         entities, ids, capability registry, SQLite layer (WAL), inspection API
├── environments/                 network, scientific, planning domains; regimes.py (hidden regimes,
│                                 twins, false analogies, held-out combinations)
├── baselines/                    fixed, adaptive, search, self_evolving, agm (v0.1), agm_v2, agm_v3,
│                                 llm_proposer (never run with a real model)
├── memory/                       structural pattern memory; principles.py (representation, extraction
│                                 rules, evaluator, applicability decision, negative knowledge)
├── observability/                event model (28 types), event log, replay, FastAPI + WebSocket
│                                 dashboard "AGM Architecture Observatory"
├── telemetry/                    JSONL + SQLite telemetry (the only thing agents observe)
├── experiments/                  manifests, runner, analysis (v0.2), analysis_v03 (kill criteria), report
├── scripts/                      host validation, sandbox build, 30-seed drivers for v0.2 and v0.3,
│                                 report writers
├── configs/                      capability registry, adaptive presets, search space
├── tests/                        33 pytest tests (IR, sandbox, environments, economics, principles,
│                                 events, observatory, planning, LLM proposer stub, v0.3)
├── docs/
│   ├── v0.3_design.md            pre-registered design, hypothesis, kill criteria, verdict rule
│   ├── V0.3_RESEARCH_REPORT.md   final report (same content as results/v03/report.md)
│   ├── V0.2_RESEARCH_REPORT.md   v0.2 report and the "weak and direction-dependent" answer
│   ├── v0.2_analysis.md, v0.2_baseline.md, v0.2_experiments.md, v0.2_interim_observations.txt
│   ├── architecture.md, architecture_ir.md, baselines.md, principles.md, sandbox.md,
│   │   observability.md, experiments.md, domain_planning.md, phases.md
└── results/                      see results/README.md: reports, analysis tables, plots, all
                                  manifests, registration, logs, one sample bundle per experiment
                                  (raw run bundles and databases, ~28 GB, are not tracked)
```

## 16. Reproducing everything

Requirements: Python 3.10+, 8 GB RAM, Docker optional (the published programs used the process executor; the choice is recorded in every provenance file).

```bash
git clone https://github.com/Mr-Infect/artifical-general-machines.git
cd artifical-general-machines
pip install -r requirements.txt
cp .env.example .env
python3 -m pytest -p no:warnings
```

Single experiment and the inspection API:

```bash
python3 -m experiments.run experiments/manifests/example.yaml
uvicorn core.api:app --port 8000
```

Live dashboard (replays any run, shows every event with a human-readable explanation):

```bash
uvicorn observability.api:app --host 0.0.0.0 --port 8100
```

The v0.2 program (330 experiments, about 5 hours on 4 cores; resumable):

```bash
nohup python3 scripts/run_v02_experiments.py --seeds 30 --workers 4 --executor process --resume >> results/v02_program.log 2>&1 &
python3 -m experiments.analysis && python3 scripts/write_research_report.py
```

The v0.3 program (270 experiments, about 3 hours; resumable; single-instance lock):

```bash
nohup python3 scripts/run_v03_experiments.py --seeds 30 --workers 4 --executor process --resume >> results/v03_program.log 2>&1 &
python3 -m experiments.analysis_v03 && python3 scripts/write_v03_report.py
```

Seeds, regime schedules, hidden truths and manifests are deterministic. Git tags: `agm-v0.1-freeze`, `agm-v0.2`, `agm-v0.3`.

## 17. Honesty notes and limitations

- **No criterion was loosened after a run.** One was judged too lenient (v0.2 criterion D) and was *tightened* for v0.3. The v0.3 rules were registered before the run and applied unchanged.
- **One environment measured nothing.** scientific_drift scored every agent near zero; it is a floor effect and a defect in that environment. It is reported as is.
- **Regime detection is partly trivial.** The constraint half of a regime change is directly observable; the pass on K1 should be read with the no_regime ablation beside it.
- **Simulated costs.** Model costs are simulated compute profiles, not API calls. All agents share them.
- **Process executor.** The 30-seed programs ran without container isolation for throughput; the Docker executor is implemented and tested, and every record states which executor produced it.
- **No language model anywhere in the primary experiments.** By design.
- **Bounded architecture space.** Agents compose primitives from a registry; they do not write code. "Novelty" is structural novelty within that space.
- **The instrument had bugs during the programs** (SQLite locking under dashboard reads, WAL copies, a double-launched driver). Each was fixed in code, the affected jobs were re-run from scratch, and the fixes are in the commit history. No result in the published tables comes from a corrupted run.
- **This repository was built with an AI coding assistant (Claude).** The hypothesis, the experimental programme, the decision to pre-register and to publish the negative result are the author's.

## 18. Citation and license

MIT License. See [CITATION.cff](CITATION.cff).

```
Mr-Infect (2026). Artificial General Machines: a falsification study of architectural
self-determination. https://github.com/Mr-Infect/artifical-general-machines
```

The research attempted to establish a new machine paradigm, designed increasingly hostile falsification experiments, and the machine itself told us the distinction was not there. That answer is published here in full.
