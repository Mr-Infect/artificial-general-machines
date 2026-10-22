"""Deterministic replay: re-execute a stored seed job from its recorded configuration and compare record hashes.

    python -m archetype.experiments.replay results/archetype/<run>/seed_<n>.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from archetype.experiments.protocol import run_seed


def replay(path: str) -> dict:
    stored = json.loads(Path(path).read_text())
    again = run_seed(stored["seed"], stored["config"])
    return {"seed": stored["seed"], "stored": stored["record_hash"], "replayed": again["record_hash"], "identical": stored["record_hash"] == again["record_hash"]}


if __name__ == "__main__":
    r = replay(sys.argv[1])
    print(json.dumps(r))
    sys.exit(0 if r["identical"] else 1)
