"""Automatic replication of an apparent breakthrough (spec §35).

Triggered by the report writer only when the registered run's verdict is BREAKTHROUGH_CANDIDATE:
30 additional seeds, 3 new surface realizations of every family, and 1 new false-analogy family.
The result counts as a breakthrough candidate only if the replication reaches the same verdict.
"""
from __future__ import annotations

import json
import sys

from archetype.experiments import run as driver
from archetype.experiments.registration import REPLICATION_SEEDS
from archetype.metrics.analysis import analyze, load

CONFIG = {"surface_offset": 3, "extra_false_families": ["FX0"]}


def main(workers: int = 8) -> str:
    driver.main(["--name", "replication", "--seeds", *map(str, REPLICATION_SEEDS), "--workers", str(workers), "--resume", "--config", json.dumps(CONFIG)])
    res = analyze(load(str(driver.RESULTS / "replication")))
    (driver.RESULTS / "replication" / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    return res["criteria"]["verdict"]


if __name__ == "__main__":
    print("replication verdict:", main(int(sys.argv[1]) if len(sys.argv) > 1 else 8))
