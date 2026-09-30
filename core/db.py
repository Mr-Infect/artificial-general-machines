"""SQLite persistence via SQLAlchemy (Sections 3, 13, 15).

Every table keeps the full JSON of the entity so nothing is lost to schema
flattening; indexed columns exist for querying and reporting.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import time as _time

from sqlalchemy import (Column, Float, Integer, String, Text, create_engine, event,
                        select)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parent.parent
Base = declarative_base()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExperimentRow(Base):
    __tablename__ = "experiments"
    experiment_id = Column(String, primary_key=True)
    name = Column(String, index=True)
    manifest_hash = Column(String, index=True)
    git_commit = Column(String)
    seed = Column(Integer)
    status = Column(String)
    executor = Column(String)
    started_at = Column(String)
    finished_at = Column(String)
    json = Column(Text)


class ArchitectureRow(Base):
    __tablename__ = "architectures"
    architecture_hash = Column(String, primary_key=True)
    ir_version = Column(String)
    parent_hash = Column(String, nullable=True)
    first_seen_experiment = Column(String)
    json = Column(Text)


class ExecutionRow(Base):
    __tablename__ = "executions"
    execution_id = Column(String, primary_key=True)
    experiment_id = Column(String, index=True)
    agent = Column(String, index=True)
    step = Column(Integer)
    logical_time_s = Column(Float)
    architecture_hash = Column(String, index=True)
    purpose = Column(String)
    exit_code = Column(Integer)
    timed_out = Column(Integer)
    runtime_s = Column(Float)
    cpu_time_s = Column(Float)
    max_memory_mb = Column(Float)
    json = Column(Text)


class EvaluationRow(Base):
    __tablename__ = "evaluations"
    execution_id = Column(String, primary_key=True)
    experiment_id = Column(String, index=True)
    agent = Column(String, index=True)
    quality = Column(Float)
    f1 = Column(Float)
    failed = Column(Integer)
    violations = Column(Integer)
    json = Column(Text)


class MetricRow(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, index=True)
    agent = Column(String, index=True)
    step = Column(Integer, nullable=True)
    name = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)


class EnvEventRow(Base):
    __tablename__ = "environment_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, index=True)
    agent = Column(String, index=True)
    logical_time_s = Column(Float)
    wall_time = Column(String)
    event = Column(String)
    json = Column(Text)


class AdaptationDecisionRow(Base):
    __tablename__ = "adaptation_decisions"
    decision_id = Column(String, primary_key=True)
    experiment_id = Column(String, index=True)
    agent = Column(String, index=True)
    step = Column(Integer)
    outcome = Column(String)
    json = Column(Text)


class PatternRow(Base):
    __tablename__ = "architectural_patterns"
    pattern_id = Column(String, primary_key=True)
    architecture_hash = Column(String, index=True)
    source_experiment = Column(String, index=True)
    source_domain = Column(String, index=True)
    quality = Column(Float)
    json = Column(Text)


class PrincipleRow(Base):
    __tablename__ = "principles"
    principle_id = Column(String, primary_key=True)
    name = Column(String, index=True)
    status = Column(String, index=True)
    confidence = Column(Float)
    evidence_count = Column(Integer)
    updated_at = Column(String)
    json = Column(Text)


class EventRow(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, index=True)
    experiment_id = Column(String, index=True)
    agent = Column(String, index=True)
    seq = Column(Integer, index=True)
    step = Column(Integer)
    timestamp = Column(String)
    event_type = Column(String, index=True)
    json = Column(Text)


class TelemetryRow(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, index=True)
    agent = Column(String, index=True)
    logical_time_s = Column(Float)
    wall_time = Column(String)
    kind = Column(String, index=True)
    json = Column(Text)


def default_db_path() -> Path:
    p = os.environ.get("AGM_DB_PATH", "results/agm_lab.sqlite")
    path = Path(p)
    if not path.is_absolute():
        path = ROOT / path
    return path


class Database:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.path}", future=True, connect_args={"timeout": 30})

        @event.listens_for(self.engine, "connect")
        def _pragmas(dbapi_conn, _rec):   # WAL: readers never block writers (dashboard vs. experiment workers)
            try:
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL")
                cur.execute("PRAGMA synchronous=NORMAL")
                cur.execute("PRAGMA busy_timeout=30000")
                cur.close()
            except Exception:
                pass
        self._retry(lambda: Base.metadata.create_all(self.engine))
        self._session_factory = sessionmaker(bind=self.engine, future=True, expire_on_commit=False)

    def session(self) -> Session:
        return self._session_factory()

    @staticmethod
    def _retry(fn, attempts: int = 6):
        """Retry on 'database is locked' with backoff; experiment records must never be lost to contention."""
        delay = 0.5
        for i in range(attempts):
            try:
                return fn()
            except OperationalError as e:
                if "locked" not in str(e).lower() or i == attempts - 1:
                    raise
                _time.sleep(delay)
                delay = min(delay * 2, 8.0)

    # --- writers -----------------------------------------------------
    def add(self, row: Base) -> None:
        def _do():
            with self.session() as s:
                s.merge(row)
                s.commit()
        self._retry(_do)

    def add_all(self, rows: List[Base]) -> None:
        def _do():
            with self.session() as s:
                for r in rows:
                    s.merge(r)
                s.commit()
        self._retry(_do)

    def add_metric(self, experiment_id: str, agent: str, step: Optional[int], name: str, value: float, unit: str = "") -> None:
        self.add(MetricRow(experiment_id=experiment_id, agent=agent, step=step, name=name, value=float(value), unit=unit))

    # --- readers -----------------------------------------------------
    def experiments(self) -> List[Dict[str, Any]]:
        with self.session() as s:
            rows = s.execute(select(ExperimentRow).order_by(ExperimentRow.started_at)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        with self.session() as s:
            r = s.get(ExperimentRow, experiment_id)
            return json.loads(r.json) if r else None

    def executions(self, experiment_id: str, agent: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.session() as s:
            q = select(ExecutionRow).where(ExecutionRow.experiment_id == experiment_id)
            if agent:
                q = q.where(ExecutionRow.agent == agent)
            rows = s.execute(q.order_by(ExecutionRow.step)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        with self.session() as s:
            r = s.get(ExecutionRow, execution_id)
            return json.loads(r.json) if r else None

    def evaluations(self, experiment_id: str) -> List[Dict[str, Any]]:
        with self.session() as s:
            rows = s.execute(select(EvaluationRow).where(EvaluationRow.experiment_id == experiment_id)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def metrics(self, experiment_id: str) -> List[Dict[str, Any]]:
        with self.session() as s:
            rows = s.execute(select(MetricRow).where(MetricRow.experiment_id == experiment_id).order_by(MetricRow.id)).scalars().all()
            return [dict(experiment_id=r.experiment_id, agent=r.agent, step=r.step, name=r.name, value=r.value, unit=r.unit) for r in rows]

    def env_events(self, experiment_id: str) -> List[Dict[str, Any]]:
        with self.session() as s:
            rows = s.execute(select(EnvEventRow).where(EnvEventRow.experiment_id == experiment_id).order_by(EnvEventRow.id)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def decisions(self, experiment_id: str) -> List[Dict[str, Any]]:
        with self.session() as s:
            rows = s.execute(select(AdaptationDecisionRow).where(AdaptationDecisionRow.experiment_id == experiment_id).order_by(AdaptationDecisionRow.step)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def telemetry(self, experiment_id: str, agent: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.session() as s:
            q = select(TelemetryRow).where(TelemetryRow.experiment_id == experiment_id)
            if agent:
                q = q.where(TelemetryRow.agent == agent)
            rows = s.execute(q.order_by(TelemetryRow.id)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def patterns(self) -> List[Dict[str, Any]]:
        with self.session() as s:
            rows = s.execute(select(PatternRow)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def principles(self) -> List[Dict[str, Any]]:
        with self.session() as s:
            rows = s.execute(select(PrincipleRow)).scalars().all()
            return [json.loads(r.json) for r in rows]

    def events(self, run_id: str, after_seq: int = -1, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.session() as s:
            q = select(EventRow).where(EventRow.run_id == run_id, EventRow.seq > after_seq).order_by(EventRow.seq)
            if limit:
                q = q.limit(limit)
            return [json.loads(r.json) for r in s.execute(q).scalars().all()]

    def runs(self) -> List[Dict[str, Any]]:
        from sqlalchemy import func
        with self.session() as s:
            rows = s.execute(select(EventRow.run_id, EventRow.experiment_id, EventRow.agent, func.count(EventRow.id), func.max(EventRow.seq),
                                    func.min(EventRow.timestamp), func.max(EventRow.timestamp))
                             .group_by(EventRow.run_id).order_by(func.min(EventRow.timestamp))).all()
            return [dict(run_id=r[0], experiment_id=r[1], agent=r[2], n_events=r[3], last_seq=r[4], started=r[5], last_event=r[6]) for r in rows]

    def architecture(self, architecture_hash: str) -> Optional[Dict[str, Any]]:
        with self.session() as s:
            r = s.get(ArchitectureRow, architecture_hash)
            return json.loads(r.json) if r else None


def copy_database(src: Path, dst: Path) -> None:
    """Consistent copy of a SQLite database (includes WAL content). Plain file copies are NOT safe in WAL mode."""
    import sqlite3
    dst = Path(dst)
    if dst.exists():
        dst.unlink()
    for suffix in ("-wal", "-shm"):
        p = Path(str(dst) + suffix)
        if p.exists():
            p.unlink()
    with sqlite3.connect(str(src)) as a, sqlite3.connect(str(dst)) as b:
        a.backup(b)
