"""Pre-registration record (same procedure as AGM v0.3): written and committed BEFORE the evaluation run.

    python -m archetype.experiments.registration            # writes archetype/reports/registration.json

It pins the commit, the registered seeds, the protocol configuration, every threshold used by the kill
criteria, and content hashes of the files that define environments, learner, baselines and analysis. The
report writer refuses to call a run "registered" if any of these hashes differ from the run's code.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from archetype.architecture.roles import MEMORIZED_THRESHOLD
from archetype.experiments.protocol import DEFAULT_CONFIG
from archetype.metrics.analysis import HARM, HELP, TH, USEFUL_T
from archetype.metrics.reference import USEFUL_GAP
from archetype.transfer import decisions as D
from archetype.util import stable_hash
from experiments.run import git_commit

ROOT = Path(__file__).resolve().parents[2]
REGISTERED_SEEDS = list(range(1000, 1030))
REPLICATION_SEEDS = list(range(2000, 2030))
DEVELOPMENT_SEEDS = list(range(0, 10))
OUT = ROOT / "archetype" / "reports" / "registration.json"


def code_hashes() -> dict:
    files = sorted(p for p in (ROOT / "archetype").rglob("*.py") if "tests" not in p.parts and "reports" not in p.parts)
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in files}


def record() -> dict:
    return {"project": "ARCHETYPE", "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "git": git_commit(),
            "design_document": "docs/archetype_registration.md", "registered_seeds": REGISTERED_SEEDS, "replication_seeds": REPLICATION_SEEDS,
            "development_seeds_never_used_as_evidence": DEVELOPMENT_SEEDS, "config": DEFAULT_CONFIG, "config_hash": stable_hash(DEFAULT_CONFIG),
            "thresholds": {**TH, "useful_gap": USEFUL_GAP, "help_delta": HELP, "useful_transfer_delta": USEFUL_T, "harm_delta": HARM, "memorized_threshold": MEMORIZED_THRESHOLD,
                           "trust": D.TRUST_T, "test": D.TEST_T, "ignore": D.IGNORE_T, "patience": D.PATIENCE, "shift_sd": D.SHIFT_SD, "drop": D.DROP},
            "verdicts": ["BREAKTHROUGH_CANDIDATE", "PARTIAL_SUPPORT", "NO_DISTINCT_CAPABILITY", "INCONCLUSIVE"], "code_hashes": code_hashes()}


if __name__ == "__main__":
    r = record()
    OUT.write_text(json.dumps(r, indent=1))
    print(f"registration written: {OUT}  commit {r['git']['commit'][:12]} dirty={r['git']['dirty']}  code files {len(r['code_hashes'])}")
