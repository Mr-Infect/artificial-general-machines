"""Read-only inspection API (FastAPI). Every run is inspectable; nothing is hidden.

    uvicorn core.api:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException

from core.db import Database
from core.registry import CapabilityRegistry
from experiments.report import experiment_report, suite_report

app = FastAPI(title="AGM Research Laboratory", version="0.1", description="Read-only access to experiments, executions, telemetry and reports.")


def db() -> Database:
    return Database()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "db": str(db().path)}


@app.get("/capabilities")
def capabilities() -> List[Dict[str, Any]]:
    return [c.model_dump() for c in CapabilityRegistry.load().all()]


@app.get("/experiments")
def experiments() -> List[Dict[str, Any]]:
    return [{k: e.get(k) for k in ("experiment_id", "name", "seed", "status", "started_at", "finished_at", "git_commit", "manifest_hash", "executor")}
            for e in db().experiments()]


@app.get("/experiments/{experiment_id}")
def experiment(experiment_id: str) -> Dict[str, Any]:
    e = db().experiment(experiment_id)
    if not e:
        raise HTTPException(404, "unknown experiment")
    return e


@app.get("/experiments/{experiment_id}/report")
def report(experiment_id: str) -> Dict[str, Any]:
    try:
        return experiment_report(db(), experiment_id)
    except ValueError as ex:
        raise HTTPException(404, str(ex))


@app.get("/experiments/{experiment_id}/executions")
def executions(experiment_id: str, agent: Optional[str] = None) -> List[Dict[str, Any]]:
    return db().executions(experiment_id, agent)


@app.get("/experiments/{experiment_id}/metrics")
def metrics(experiment_id: str) -> List[Dict[str, Any]]:
    return db().metrics(experiment_id)


@app.get("/experiments/{experiment_id}/events")
def events(experiment_id: str) -> List[Dict[str, Any]]:
    return db().env_events(experiment_id)


@app.get("/experiments/{experiment_id}/decisions")
def decisions(experiment_id: str) -> List[Dict[str, Any]]:
    return db().decisions(experiment_id)


@app.get("/experiments/{experiment_id}/telemetry")
def telemetry(experiment_id: str, agent: Optional[str] = None) -> List[Dict[str, Any]]:
    return db().telemetry(experiment_id, agent)


@app.get("/executions/{execution_id}")
def execution(execution_id: str) -> Dict[str, Any]:
    e = db().execution(execution_id)
    if not e:
        raise HTTPException(404, "unknown execution")
    return e


@app.get("/architectures/{architecture_hash}")
def architecture(architecture_hash: str) -> Dict[str, Any]:
    a = db().architecture(architecture_hash)
    if not a:
        raise HTTPException(404, "unknown architecture")
    return a


@app.get("/patterns")
def patterns() -> List[Dict[str, Any]]:
    return db().patterns()


@app.get("/suite")
def suite(names: str) -> Dict[str, Any]:
    return suite_report(db(), names.split(","))
