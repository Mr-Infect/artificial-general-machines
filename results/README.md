# Results directory

The full results tree of the three experimental programs is about 28 GB (per-run event logs,
SQLite databases and memory files). It is not tracked. What is tracked:

| path | contents |
|---|---|
| `v0.1_freeze/` | the two bit-for-bit identical v0.1 benchmark runs (3 seeds) that were frozen before v0.2 |
| `v02_observations.txt` | plain-text interim observations written while the v0.2 program was running |
| `v02/analysis/` | v0.2 analysis tables (`analysis.md`, `analysis.json`), 330 experiments, 30 seeds |
| `v02/manifests/`, `v02/samples/` | every v0.2 experiment manifest; one small sample bundle per experiment type |
| `v03/report.md` | the generated v0.3 report (20 mandated sections, verdict FAIL) |
| `v03/analysis/` | v0.3 analysis tables: all paired comparisons, kill criteria, per-environment metrics |
| `v03/plots/` | SVG plots per environment: quality, evaluations-to-useful, adaptation cost |
| `v03/manifests/`, `v03/samples/` | all 270 manifests; one sample bundle per experiment type (manifest, hidden truth, metrics, Pareto, transfer, provenance, report) |
| `v03/registration.json`, `v03/driver_log.jsonl`, `v03_program.log` | pre-registration record and the driver's job log |

Regenerate everything from the code with the commands in the top-level README (about 3 hours
for v0.3 and 5 hours for v0.2 on a 4-core machine).
