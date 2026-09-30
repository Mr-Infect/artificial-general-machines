"""Telemetry (Section 6): the only channel through which agents observe the world.

Everything is appended to a JSONL file in the results directory and mirrored
into SQLite. ``snapshot()`` is what an agent receives: the observable
environment profile, its own recent resource usage, and remaining budgets.
It never includes the event schedule or ground-truth labels.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from core.db import Database, EnvEventRow, TelemetryRow, utcnow


class Telemetry:
    def __init__(self, db: Database, experiment_id: str, agent: str, results_dir: Path):
        self.db = db
        self.experiment_id = experiment_id
        self.agent = agent
        self.path = results_dir / f"telemetry_{agent}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("a")
        self.records: List[Dict[str, Any]] = []
        self.last_execution: Optional[Dict[str, Any]] = None
        self.history: List[Dict[str, Any]] = []

    def close(self) -> None:
        self._fh.close()

    def record(self, kind: str, logical_time_s: float, payload: Dict[str, Any]) -> None:
        rec = {"kind": kind, "t": logical_time_s, "wall": utcnow(), "agent": self.agent, **payload}
        self.records.append(rec)
        self._fh.write(json.dumps(rec) + "\n")
        self._fh.flush()
        self.db.add(TelemetryRow(experiment_id=self.experiment_id, agent=self.agent, logical_time_s=logical_time_s,
                                 wall_time=rec["wall"], kind=kind, json=json.dumps(rec)))

    def record_env_transition(self, logical_time_s: float, event: Dict[str, Any], before: Dict[str, Any], after: Dict[str, Any]) -> None:
        rec = {"t": logical_time_s, "event": event, "before": before, "after": after, "wall": utcnow(), "agent": self.agent}
        self.record("environment_transition", logical_time_s, {"event": event, "before": before, "after": after})
        self.db.add(EnvEventRow(experiment_id=self.experiment_id, agent=self.agent, logical_time_s=logical_time_s,
                                wall_time=rec["wall"], event=event.get("type", "?"), json=json.dumps(rec)))

    def record_execution(self, logical_time_s: float, summary: Dict[str, Any]) -> None:
        self.last_execution = summary
        self.history.append(summary)
        self.record("execution", logical_time_s, summary)

    @staticmethod
    def host_sample() -> Dict[str, float]:
        vm = psutil.virtual_memory()
        return {"host_cpu_percent": psutil.cpu_percent(interval=None), "host_mem_available_mb": vm.available / 2**20,
                "host_load_1m": psutil.getloadavg()[0]}

    def snapshot(self, env_observable: Dict[str, Any], budget: Dict[str, float]) -> Dict[str, Any]:
        recent = self.history[-5:]
        return {
            "environment": env_observable,
            "budget": dict(budget),
            "last_execution": self.last_execution,
            "recent_quality": [h.get("quality") for h in recent if h.get("quality") is not None],
            "recent_violations": [v for h in recent for v in h.get("violations", [])],
            "host": self.host_sample(),
        }
