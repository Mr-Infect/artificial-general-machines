# Architecture IR (v0.1)

```yaml
ir_version: "0.1"
name: example
architecture:
  input:        {type: stream, batch_size: 200}
  perception:   {mode: parallel, components: [statistical_detector, anomaly_detector], window: 50}
  reasoning:    {type: hierarchical, model: small_reasoner, threshold: 0.5, iterations: 1}
  memory:       {type: episodic, capacity: 500}
  verification: {type: rule_based, model: null, strictness: 0.5}
  tools:        [python]
  output:       {confidence: true}
parent_hash: null     # set by ArchitectureIR.derive()
lineage: []           # ancestor hashes
metadata: {}          # free-form; does not affect the hash
```

* **Schema validation**: Pydantic (`architecture/ir.py`), literal enumerations for every choice.
* **Registry validation**: every component/model/tool must exist (`architecture/validate.py`).
* **Environment validation**: required capabilities must be available *now*, network-requiring
  capabilities need network, the compiled memory estimate must fit the current limit, `local_only`
  privacy forbids the search tool. This is what makes environmental events invalidate architectures.
* **Hash**: sha256 of the canonical JSON of `ir_version` + `architecture`; `name`, `metadata`,
  `lineage` do not contribute.
* **Comparison**: `compare(a, b)` gives a field-level diff and a distance in [0, 1] (Jaccard for
  list fields); `novelty(candidate, known)` is the minimum distance to a set.
* **Versioning**: `ir.derive(**{"reasoning.model": "large_reasoner"})` produces a child with
  `parent_hash` and `lineage`; every hash seen in an experiment is stored in `architectures`.

## Compilation

`compile_ir(ir, registry, limits)` produces a `CompiledSpec`: the resolved pipeline, the cost
profile of each required capability (so the sandbox accounts model calls, tokens and simulated
money consistently), the limits, and static estimates (memory, cost per batch, latency, CPU weight)
used by environment validation and adaptation economics.
