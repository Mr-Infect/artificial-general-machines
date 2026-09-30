"""AGM Architecture Observatory: service + API + WebSocket stream (v0.2, spec sections 14-20).

    uvicorn observability.api:app --host 127.0.0.1 --port 8100

Live mode: the WebSocket tails the ``events`` table of the database the running
experiment writes to (SQLite polling every 0.5 s), so what the dashboard shows
is exactly what the runner recorded. Demo mode: the client fetches a completed
run's events and replays them with the ReplayController. Nothing is generated
client-side except the fold of recorded events into state.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from architecture.distance import architecture_distance, novelty_levels
from architecture.ir import ArchitectureIR, compare
from core.db import Database
from core.registry import CapabilityRegistry
from experiments.report import experiment_report, pareto_front
from observability.events import Event, explanations, fold_state

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="AGM Architecture Observatory", version="0.2")
_registry = CapabilityRegistry.load()


_DB_CACHE: Dict[str, Database] = {}
_RUNS_CACHE: Dict[str, Any] = {"t": 0.0, "value": None}


def db(path: Optional[str] = None) -> Database:
    key = str(Path(path)) if path else "__default__"
    if key not in _DB_CACHE:
        _DB_CACHE[key] = Database(Path(path)) if path else Database()
    return _DB_CACHE[key]


def _events(run_id: str, path: Optional[str] = None) -> List[Event]:
    return [Event.model_validate(d) for d in db(path).events(run_id)]


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "db": str(db().path), "mode_note": "live = tails the events table; demo = replays a stored run"}


def all_db_paths() -> List[Path]:
    """Default database plus every program/worker database under results/ (AGM_OBS_DB_GLOB overrides)."""
    import glob as _glob
    pattern = os.environ.get("AGM_OBS_DB_GLOB", str(ROOT / "results" / "**" / "*.sqlite"))
    paths = {Path(p) for p in _glob.glob(pattern, recursive=True) if "memory" not in Path(p).parts and not Path(p).name.startswith("exp2_")}
    paths.add(db().path)
    return sorted(p for p in paths if p.exists())


@app.get("/runs")
def runs(db_path: Optional[str] = None):
    import time as _t
    if not db_path and _RUNS_CACHE["value"] is not None and _t.time() - _RUNS_CACHE["t"] < 20:
        return _RUNS_CACHE["value"]
    out = []
    for path in ([Path(db_path)] if db_path else all_db_paths()):
        try:
            d = Database(path)
            exps = {e["experiment_id"]: e for e in d.experiments()}
            for r in d.runs():
                e = exps.get(r["experiment_id"], {})
                m = e.get("manifest", {})
                out.append({**r, "db_path": str(path), "experiment": e.get("name"), "status": e.get("status") or "running", "seed": e.get("seed"),
                            "domain": m.get("task", {}).get("domain"), "steps": m.get("schedule", {}).get("steps"), "summary": (e.get("summary") or {}).get(r["agent"])})
        except Exception:
            continue
    out.sort(key=lambda r: r["started"] or "")
    if not db_path:
        _RUNS_CACHE["t"], _RUNS_CACHE["value"] = _t.time(), out
    return out


@app.get("/runs/{run_id}")
def run(run_id: str, db_path: Optional[str] = None):
    evs = _events(run_id, db_path)
    if not evs:
        raise HTTPException(404, "unknown run")
    st = fold_state(evs)
    exp = db(db_path).experiment(evs[0].experiment_id) or {}
    return {"run_id": run_id, "experiment": {k: exp.get(k) for k in ("experiment_id", "name", "seed", "status", "git_commit", "manifest_hash", "executor")},
            "manifest": exp.get("manifest"), "n_events": len(evs), "state": st}


@app.get("/runs/{run_id}/events")
def run_events(run_id: str, after: int = -1, limit: Optional[int] = None, db_path: Optional[str] = None):
    evs = db(db_path).events(run_id, after_seq=after, limit=limit)
    if not evs and after < 0:
        raise HTTPException(404, "unknown run")
    return evs


@app.get("/runs/{run_id}/state")
def run_state(run_id: str, at: Optional[int] = None, db_path: Optional[str] = None):
    """Complete machine state after event index ``at`` (replay support)."""
    evs = _events(run_id, db_path)
    if not evs:
        raise HTTPException(404, "unknown run")
    return fold_state(evs, upto=at)


@app.get("/runs/{run_id}/explanations")
def run_explanations(run_id: str, db_path: Optional[str] = None):
    evs = _events(run_id, db_path)
    if not evs:
        raise HTTPException(404, "unknown run")
    return explanations(evs)


@app.get("/runs/{run_id}/architectures")
def run_architectures(run_id: str, db_path: Optional[str] = None):
    evs = _events(run_id, db_path)
    if not evs:
        raise HTTPException(404, "unknown run")
    st = fold_state(evs)
    d = db(db_path)
    out = []
    for h, a in st["architectures"].items():
        row = d.architecture(h) or {}
        out.append({**a, "ir": row, "children": [b["alias"] for b in st["architectures"].values() if b.get("parent_hash") == h]})
    return out


@app.get("/runs/{run_id}/lineage")
def run_lineage(run_id: str, db_path: Optional[str] = None):
    evs = _events(run_id, db_path)
    if not evs:
        raise HTTPException(404, "unknown run")
    st = fold_state(evs)
    nodes = [{"id": h, "alias": a["alias"], "name": a.get("name"), "parent": a.get("parent_hash"), "source": a.get("source"),
              "created_step": a.get("created_step"), "reason": a.get("reason"), "performance": a.get("performance"),
              "executed": any(x["hash"] == h for x in st["executions"])} for h, a in st["architectures"].items()]
    edges = [{"from": n["parent"], "to": n["id"]} for n in nodes if n["parent"] and n["parent"] in st["architectures"]]
    return {"nodes": nodes, "edges": edges, "current": (st["current_architecture"] or {}).get("hash")}


@app.get("/runs/{run_id}/principles")
def run_principles(run_id: str, db_path: Optional[str] = None):
    evs = _events(run_id, db_path)
    if not evs:
        raise HTTPException(404, "unknown run")
    return fold_state(evs)["principles"]


@app.get("/runs/{run_id}/transfer")
def run_transfer(run_id: str, db_path: Optional[str] = None):
    evs = _events(run_id, db_path)
    if not evs:
        raise HTTPException(404, "unknown run")
    st = fold_state(evs)
    return {"attempted": [e.payload for e in evs if e.event_type.value == "TRANSFER_ATTEMPTED"],
            "completed": [e.payload for e in evs if e.event_type.value == "TRANSFER_COMPLETED"],
            "summary": (st.get("summary") or {}).get("agent_extra", {}).get("transfers")}


@app.get("/architectures/{architecture_hash}")
def architecture(architecture_hash: str, db_path: Optional[str] = None):
    a = db(db_path).architecture(architecture_hash)
    if not a:
        raise HTTPException(404, "unknown architecture")
    return a


@app.get("/architectures/{architecture_hash}/lineage")
def architecture_lineage(architecture_hash: str, db_path: Optional[str] = None):
    d = db(db_path)
    a = d.architecture(architecture_hash)
    if not a:
        raise HTTPException(404, "unknown architecture")
    chain = [a]
    seen = {architecture_hash}
    while chain[-1].get("parent_hash") and chain[-1]["parent_hash"] not in seen:
        p = d.architecture(chain[-1]["parent_hash"])
        if not p:
            break
        seen.add(chain[-1]["parent_hash"])
        chain.append(p)
    return {"hash": architecture_hash, "ancestors": [ArchitectureIR.from_dict(c).hash() for c in chain[1:]], "lineage_field": a.get("lineage", [])}


@app.get("/architectures/{architecture_hash}/diff/{other_hash}")
def architecture_diff(architecture_hash: str, other_hash: str, db_path: Optional[str] = None):
    d = db(db_path)
    a, b = d.architecture(architecture_hash), d.architecture(other_hash)
    if not a or not b:
        raise HTTPException(404, "unknown architecture")
    ia, ib = ArchitectureIR.from_dict(a), ArchitectureIR.from_dict(b)
    return {"diff": compare(ia, ib), "distance": architecture_distance(ia, ib, _registry), "novelty_of_a_vs_b": novelty_levels(ia, [ib], _registry)}


@app.get("/experiments/{experiment_id}/pareto")
def experiment_pareto(experiment_id: str, db_path: Optional[str] = None):
    try:
        r = experiment_report(db(db_path), experiment_id)
    except ValueError as ex:
        raise HTTPException(404, str(ex))
    agents = r["agents"]
    objectives = {"quality_mean": True, "latency_ms": False, "max_memory_mb": False, "adaptation_cost": False, "architecture_evaluations": False, "failure_rate": False}
    pts = {}
    for a, s in agents.items():
        steps = r["per_step"].get(a, [])
        pts[a] = {"quality_mean": s["quality_mean"], "latency_ms": sum(x["runtime_s"] for x in steps) / max(1, len(steps)) * 1000,
                  "max_memory_mb": s["max_memory_mb"], "adaptation_cost": s["adaptation_cost"], "architecture_evaluations": s["architecture_evaluations"],
                  "failure_rate": s["failures"] / max(1, len(steps))}
    def dominates(p, q):
        better_or_eq = all((p[k] >= q[k]) if mx else (p[k] <= q[k]) for k, mx in objectives.items())
        strictly = any((p[k] > q[k]) if mx else (p[k] < q[k]) for k, mx in objectives.items())
        return better_or_eq and strictly
    classification = {a: ("dominated" if any(dominates(pts[b], pts[a]) for b in pts if b != a) else "non-dominated") for a in pts}
    normalized = {a: {"quality_per_adaptation_cost": (pts[a]["quality_mean"] / pts[a]["adaptation_cost"]) if pts[a]["adaptation_cost"] > 0 else None,
                      "quality_per_evaluation": (pts[a]["quality_mean"] / pts[a]["architecture_evaluations"]) if pts[a]["architecture_evaluations"] > 0 else None} for a in pts}
    return {"objectives": objectives, "points": pts, "classification": classification, "frontier": [a for a, c in classification.items() if c == "non-dominated"],
            "pareto_cost_quality": pareto_front({a: (agents[a]["total_cost"], agents[a]["quality_mean"]) for a in agents}), "resource_normalized": normalized,
            "note": "raw quality and resource-normalized measures are reported separately and never combined into one score"}


@app.websocket("/ws/runs/{run_id}")
async def ws_run(ws: WebSocket, run_id: str):
    """Streams events as the runner records them (live mode). Query: after=<seq>, db_path=<path>."""
    await ws.accept()
    after = int(ws.query_params.get("after", -1))
    path = ws.query_params.get("db_path")
    try:
        idle = 0
        while True:
            evs = db(path).events(run_id, after_seq=after)
            if evs:
                for e in evs:
                    await ws.send_text(json.dumps(e))
                    after = e["seq"]
                idle = 0
                if evs[-1]["event_type"] == "RUN_COMPLETED":
                    await ws.send_text(json.dumps({"event_type": "_STREAM_END", "run_id": run_id, "seq": after}))
            else:
                idle += 1
                if idle % 20 == 0:
                    await ws.send_text(json.dumps({"event_type": "_HEARTBEAT", "run_id": run_id, "seq": after}))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return


app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
