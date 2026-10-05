"""ARCHETYPE experiment driver (same pattern as scripts/run_v03_experiments.py).

    python -m archetype.experiments.run --name sanity --preset sanity --seeds 0 1 2 --workers 3
    python -m archetype.experiments.run --name registered --seeds $(seq 1000 1029) --workers 8 --resume

One job per seed, each writing its own shard (seed_<n>.json) so workers never share a database writer.
Resumable; single-instance lock per run directory; shards are ingested into SQLite (WAL) by the parent.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import traceback
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict

from archetype.experiments.protocol import DEFAULT_CONFIG, run_seed
from archetype.util import stable_hash
from experiments.run import git_commit

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "archetype"
PRESETS: Dict[str, Dict[str, Any]] = {
    "full": {},
    # spec §38: 3 seeds, 3 structural families, 1 transfer, 1 false analogy
    "sanity": {"train_families": ["T00", "T03", "T05"], "test_families": ["B00", "F00"], "intervention_families": ["B00"]},
}


def _job(args) -> Dict[str, Any]:
    seed, cfg, out, prov = args
    t0 = time.time()
    try:
        res = run_seed(seed, cfg, prov)
        tmp = out / f"seed_{seed}.json.tmp"
        tmp.write_text(json.dumps(res, default=str))
        os.replace(tmp, out / f"seed_{seed}.json")
        return {"seed": seed, "status": "ok", "seconds": round(time.time() - t0, 1), "record_hash": res["record_hash"]}
    except Exception:
        return {"seed": seed, "status": "error", "seconds": round(time.time() - t0, 1), "error": traceback.format_exc()[-2000:]}


def ingest(out: Path) -> None:
    """Shards -> SQLite (single writer, WAL), for inspection with ordinary tools."""
    db = sqlite3.connect(out / "archetype.sqlite", timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        DROP TABLE IF EXISTS jobs; DROP TABLE IF EXISTS environments; DROP TABLE IF EXISTS episodes; DROP TABLE IF EXISTS interventions;
        CREATE TABLE jobs(seed INTEGER PRIMARY KEY, record_hash TEXT, config_hash TEXT, provenance TEXT);
        CREATE TABLE environments(seed INTEGER, family TEXT, world TEXT, surface INTEGER, genome_hash TEXT, surface_seed TEXT, record TEXT);
        CREATE TABLE episodes(seed INTEGER, family TEXT, world TEXT, surface INTEGER, agent TEXT, e2u INTEGER, evaluations INTEGER, gap REAL, record TEXT);
        CREATE TABLE interventions(seed INTEGER, family TEXT, property TEXT, level TEXT, record TEXT);""")
    for p in sorted(out.glob("seed_*.json")):
        r = json.loads(p.read_text())
        db.execute("INSERT INTO jobs VALUES (?,?,?,?)", (r["seed"], r["record_hash"], r["config_hash"], json.dumps(r["provenance"])))
        db.executemany("INSERT INTO environments VALUES (?,?,?,?,?,?,?)", [(r["seed"], e["family"], e["world"], e["surface_index"], e["genome_hash"], e["surface_seed"], json.dumps(e)) for e in r["environments"]])
        db.executemany("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)", [(r["seed"], e["family"], e["world"], e["surface"], e["agent"], e["phase1"]["e2u"], e["phase1"]["evaluations"], e["phase1"]["final"]["gap"], json.dumps(e)) for e in r["episodes"]])
        db.executemany("INSERT INTO interventions VALUES (?,?,?,?,?)", [(r["seed"], e["family"], e["property"], e["level"], json.dumps(e)) for e in r["interventions"]])
    db.commit()
    db.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--preset", default="full", choices=sorted(PRESETS))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--config", default=None, help="JSON overrides of the protocol configuration")
    a = ap.parse_args(argv)
    out = RESULTS / a.name
    out.mkdir(parents=True, exist_ok=True)
    lock = out / "driver.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        print(f"another driver instance holds {lock}; refusing to start", file=sys.stderr)
        return 2
    try:
        cfg = {**DEFAULT_CONFIG, **PRESETS[a.preset], **(json.loads(a.config) if a.config else {})}
        prov = {"git": git_commit(), "run": a.name, "preset": a.preset, "config_hash": stable_hash(cfg)}
        (out / "manifest.json").write_text(json.dumps({"name": a.name, "seeds": a.seeds, "config": cfg, "provenance": prov}, indent=1))
        todo = [s for s in a.seeds if not (a.resume and (out / f"seed_{s}.json").exists())]
        print(f"[{a.name}] {len(todo)} of {len(a.seeds)} seeds to run, {a.workers} workers, commit {prov['git']['commit'][:12]} dirty={prov['git']['dirty']}", flush=True)
        failed = 0
        with Pool(a.workers) as pool, open(out / "driver_log.jsonl", "a") as log:
            for r in pool.imap_unordered(_job, [(s, cfg, out, prov) for s in todo]):
                log.write(json.dumps(r) + "\n")
                log.flush()
                failed += r["status"] != "ok"
                print(f"  seed {r['seed']}: {r['status']} in {r['seconds']}s" + (f"\n{r['error']}" if r["status"] != "ok" else ""), flush=True)
        ingest(out)
        print(f"[{a.name}] done, {failed} failed, results in {out}", flush=True)
        return 1 if failed else 0
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
