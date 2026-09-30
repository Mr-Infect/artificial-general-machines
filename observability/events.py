"""Formal event model for the AGM event stream (v0.2, spec sections 14-15, 18).

Every important action of the runner or an agent produces one ``Event``. Events
are appended, in order, to ``results/<experiment_id>/raw_events.jsonl`` and to
the SQLite ``events`` table. A run is one (experiment, agent) pair:
``run_id = "<experiment_id>.<agent>"``. Sequence numbers are per run, so a run's
events can be replayed exactly and the machine state at any point can be
recomputed by ``fold_state``.

Nothing here observes "thought": these are explicit machine-state and decision
records emitted by the code that made the decision.
"""
from __future__ import annotations

import json
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.db import Database, EventRow, utcnow

EVENT_SCHEMA_VERSION = "0.2"


class EventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    ENVIRONMENT_OBSERVED = "ENVIRONMENT_OBSERVED"
    CONSTRAINT_CHANGED = "CONSTRAINT_CHANGED"
    CAPABILITY_REQUIREMENT_INFERRED = "CAPABILITY_REQUIREMENT_INFERRED"
    MEMORY_RETRIEVED = "MEMORY_RETRIEVED"
    PRINCIPLE_RETRIEVED = "PRINCIPLE_RETRIEVED"
    ARCHITECTURE_GENERATED = "ARCHITECTURE_GENERATED"
    ARCHITECTURE_REJECTED = "ARCHITECTURE_REJECTED"
    ARCHITECTURE_SELECTED = "ARCHITECTURE_SELECTED"
    ADAPTATION_DECISION = "ADAPTATION_DECISION"
    DO_NOT_ADAPT = "DO_NOT_ADAPT"
    VALIDATION_STARTED = "VALIDATION_STARTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    COMPILATION_STARTED = "COMPILATION_STARTED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    RESOURCE_LIMIT_HIT = "RESOURCE_LIMIT_HIT"
    RESULT_EVALUATED = "RESULT_EVALUATED"
    PRINCIPLE_CREATED = "PRINCIPLE_CREATED"
    PRINCIPLE_SUPPORTED = "PRINCIPLE_SUPPORTED"
    PRINCIPLE_CONTRADICTED = "PRINCIPLE_CONTRADICTED"
    TRANSFER_ATTEMPTED = "TRANSFER_ATTEMPTED"
    TRANSFER_COMPLETED = "TRANSFER_COMPLETED"
    RUN_COMPLETED = "RUN_COMPLETED"


# The decision-pipeline stage each event type activates on the dashboard.
STAGE_OF = {
    EventType.RUN_STARTED: "OBSERVE", EventType.ENVIRONMENT_OBSERVED: "OBSERVE", EventType.CONSTRAINT_CHANGED: "OBSERVE",
    EventType.CAPABILITY_REQUIREMENT_INFERRED: "REQUIREMENTS",
    EventType.MEMORY_RETRIEVED: "MEMORY", EventType.PRINCIPLE_RETRIEVED: "MEMORY",
    EventType.ARCHITECTURE_GENERATED: "CANDIDATES", EventType.ARCHITECTURE_REJECTED: "ECONOMICS",
    EventType.ADAPTATION_DECISION: "ECONOMICS", EventType.DO_NOT_ADAPT: "DECIDE", EventType.ARCHITECTURE_SELECTED: "DECIDE",
    EventType.VALIDATION_STARTED: "VALIDATE", EventType.VALIDATION_FAILED: "VALIDATE", EventType.COMPILATION_STARTED: "VALIDATE",
    EventType.EXECUTION_STARTED: "EXECUTE", EventType.EXECUTION_COMPLETED: "EXECUTE", EventType.EXECUTION_FAILED: "EXECUTE",
    EventType.RESOURCE_LIMIT_HIT: "EXECUTE", EventType.RESULT_EVALUATED: "EVALUATE",
    EventType.PRINCIPLE_CREATED: "LEARN", EventType.PRINCIPLE_SUPPORTED: "LEARN", EventType.PRINCIPLE_CONTRADICTED: "LEARN",
    EventType.TRANSFER_ATTEMPTED: "MEMORY", EventType.TRANSFER_COMPLETED: "LEARN", EventType.RUN_COMPLETED: "LEARN",
}
PIPELINE = ["OBSERVE", "UNDERSTAND", "REQUIREMENTS", "MEMORY", "CANDIDATES", "ECONOMICS", "DECIDE", "VALIDATE", "EXECUTE", "EVALUATE", "LEARN"]


class Event(BaseModel):
    schema_version: str = EVENT_SCHEMA_VERSION
    run_id: str
    experiment_id: str
    agent: str
    seq: int
    timestamp: str
    step: Optional[int] = None
    logical_time_s: Optional[float] = None
    event_type: EventType
    domain: Optional[str] = None
    environment_state: Dict[str, Any] = Field(default_factory=dict)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    candidate_architectures: List[Dict[str, Any]] = Field(default_factory=list)
    selected_architecture: Optional[str] = None      # readable alias, e.g. A-021
    architecture_hash: Optional[str] = None
    reason: Optional[str] = None
    expected_gain: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

    @property
    def stage(self) -> str:
        return STAGE_OF.get(self.event_type, "OBSERVE")


class EventLog:
    """Per-run append-only log. Thread-safe within a process."""

    def __init__(self, db: Database, experiment_id: str, agent: str, results_dir: Path, domain: Optional[str] = None):
        self.db = db
        self.experiment_id = experiment_id
        self.agent = agent
        self.run_id = f"{experiment_id}.{agent}"
        self.domain = domain
        self.seq = -1
        self.step: Optional[int] = None
        self.logical_time_s: Optional[float] = None
        self.env_state: Dict[str, Any] = {}
        self.aliases: Dict[str, str] = {}
        self._lock = threading.Lock()
        results_dir.mkdir(parents=True, exist_ok=True)
        self._fh = (results_dir / "raw_events.jsonl").open("a")
        self.events: List[Event] = []

    def alias(self, architecture_hash: str) -> str:
        if architecture_hash not in self.aliases:
            self.aliases[architecture_hash] = f"A-{len(self.aliases) + 1:03d}"
        return self.aliases[architecture_hash]

    def set_context(self, step: Optional[int], logical_time_s: Optional[float], env_state: Optional[Dict[str, Any]] = None) -> None:
        self.step, self.logical_time_s = step, logical_time_s
        if env_state is not None:
            self.env_state = env_state

    def emit(self, event_type: EventType | str, **fields: Any) -> Event:
        with self._lock:
            self.seq += 1
            et = EventType(event_type)
            if "architecture_hash" in fields and fields["architecture_hash"] and not fields.get("selected_architecture"):
                fields["selected_architecture"] = self.alias(fields["architecture_hash"])
            for c in fields.get("candidate_architectures", []) or []:
                if c.get("hash") and not c.get("alias"):
                    c["alias"] = self.alias(c["hash"])
            ev = Event(run_id=self.run_id, experiment_id=self.experiment_id, agent=self.agent, seq=self.seq, timestamp=utcnow(),
                       step=fields.pop("step", self.step), logical_time_s=fields.pop("logical_time_s", self.logical_time_s),
                       event_type=et, domain=fields.pop("domain", self.domain),
                       environment_state=fields.pop("environment_state", self.env_state), **fields)
            line = ev.model_dump_json()
            self._fh.write(line + "\n")
            self._fh.flush()
            self.db.add(EventRow(run_id=self.run_id, experiment_id=self.experiment_id, agent=self.agent, seq=self.seq, step=ev.step,
                                 timestamp=ev.timestamp, event_type=et.value, json=line))
            self.events.append(ev)
            return ev

    def close(self) -> None:
        self._fh.close()


def load_events(path: Path, run_id: Optional[str] = None) -> List[Event]:
    out = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        ev = Event.model_validate_json(line)
        if run_id is None or ev.run_id == run_id:
            out.append(ev)
    out.sort(key=lambda e: (e.run_id, e.seq))
    return out


def verify_ordering(events: List[Event]) -> List[str]:
    """Replayability check: per run, seq must be contiguous from 0 and timestamps non-decreasing."""
    problems = []
    by_run: Dict[str, List[Event]] = {}
    for e in events:
        by_run.setdefault(e.run_id, []).append(e)
    for run, evs in by_run.items():
        evs.sort(key=lambda e: e.seq)
        for i, e in enumerate(evs):
            if e.seq != i:
                problems.append(f"{run}: seq gap at {i} (found {e.seq})")
                break
        for a, b in zip(evs, evs[1:]):
            if b.timestamp < a.timestamp:
                problems.append(f"{run}: timestamp regression at seq {b.seq}")
                break
        if evs and evs[0].event_type != EventType.RUN_STARTED:
            problems.append(f"{run}: first event is {evs[0].event_type.value}, not RUN_STARTED")
    return problems


def fold_state(events: List[Event], upto: Optional[int] = None) -> Dict[str, Any]:
    """Recompute the complete observable machine state after event index ``upto`` (inclusive).

    This is the single definition of "state at a point in time" used by the API, the replay
    controller and the explanations; the JS dashboard mirrors it.
    """
    st: Dict[str, Any] = {
        "run_id": None, "experiment_id": None, "agent": None, "domain": None, "step": None, "logical_time_s": None,
        "stage": "OBSERVE", "environment": {}, "constraints": {}, "objective": {}, "current_architecture": None,
        "architectures": {}, "candidates": [], "decisions": [], "last_decision": None, "principles": {"retrieved": [], "created": [],
        "supported": [], "contradicted": [], "transfer_candidates": []}, "memory_retrievals": [], "executions": [], "evaluations": [],
        "failures": [], "resource_series": [], "counters": {"architecture_evaluations": 0, "adaptation_cost": 0.0, "execution_cost": 0.0,
        "failures": 0, "do_not_adapt": 0, "adapt": 0}, "trace": [], "completed": False, "last_seq": -1,
    }
    seq_events = events if upto is None else events[: upto + 1]
    for e in seq_events:
        st["run_id"], st["experiment_id"], st["agent"] = e.run_id, e.experiment_id, e.agent
        st["domain"] = e.domain or st["domain"]
        if e.step is not None:
            st["step"] = e.step
        if e.logical_time_s is not None:
            st["logical_time_s"] = e.logical_time_s
        if e.environment_state:
            st["environment"] = e.environment_state
        st["stage"] = e.stage
        st["last_seq"] = e.seq
        p = e.payload
        t = e.event_type
        st["trace"].append({"seq": e.seq, "t": e.timestamp, "type": t.value, "summary": summarize(e)})
        if t == EventType.RUN_STARTED:
            st["objective"] = p.get("objective", {})
            st["constraints"] = p.get("constraints", {})
        elif t == EventType.CONSTRAINT_CHANGED:
            st["constraints"] = p.get("after", st["constraints"])
        elif t == EventType.ENVIRONMENT_OBSERVED:
            st["candidates"] = []
            st["principles"]["retrieved"] = []
            st["memory_retrievals"] = []
        elif t == EventType.MEMORY_RETRIEVED:
            st["memory_retrievals"].append(p)
        elif t == EventType.PRINCIPLE_RETRIEVED:
            st["principles"]["retrieved"] = p.get("principles", [])
            st["principles"]["transfer_candidates"] = [q for q in p.get("principles", []) if q.get("source_domains") and st["domain"] not in q.get("source_domains", [])]
        elif t == EventType.ARCHITECTURE_GENERATED:
            for c in e.candidate_architectures:
                c = dict(c); c.setdefault("status", "generated")
                st["candidates"].append(c)
                st["architectures"].setdefault(c.get("hash"), {"alias": c.get("alias"), "hash": c.get("hash"), "name": c.get("name"),
                                                               "parent_hash": c.get("parent_hash"), "source": c.get("source"),
                                                               "created_step": e.step, "reason": c.get("reason"), "performance": []})
        elif t == EventType.ARCHITECTURE_REJECTED:
            for c in st["candidates"]:
                if c.get("hash") == e.architecture_hash:
                    c["status"], c["reason"] = "rejected", e.reason
        elif t == EventType.ARCHITECTURE_SELECTED:
            for c in st["candidates"]:
                if c.get("hash") == e.architecture_hash:
                    c["status"], c["reason"] = "selected", e.reason
            st["current_architecture"] = {"alias": e.selected_architecture, "hash": e.architecture_hash, **p}
            st["architectures"].setdefault(e.architecture_hash, {"alias": e.selected_architecture, "hash": e.architecture_hash,
                                                                 "name": p.get("name"), "parent_hash": p.get("parent_hash"), "source": p.get("source"),
                                                                 "created_step": e.step, "reason": e.reason, "performance": []})
        elif t in (EventType.ADAPTATION_DECISION, EventType.DO_NOT_ADAPT):
            d = {"seq": e.seq, "step": e.step, "outcome": p.get("outcome"), "reason": e.reason, "expected_gain": e.expected_gain,
                 "estimated_cost": e.estimated_cost, "actual_cost": e.actual_cost, **p}
            st["decisions"].append(d)
            st["last_decision"] = d
            if p.get("outcome") == "DO_NOT_ADAPT":
                st["counters"]["do_not_adapt"] += 1
            elif p.get("outcome") in ("ADAPT", "PARTIAL_ADAPT"):
                st["counters"]["adapt"] += 1
        elif t == EventType.VALIDATION_FAILED:
            st["failures"].append({"seq": e.seq, "step": e.step, "kind": "validation", "architecture": e.selected_architecture, "reason": e.reason})
        elif t in (EventType.EXECUTION_COMPLETED, EventType.EXECUTION_FAILED):
            rec = {"seq": e.seq, "step": e.step, "architecture": e.selected_architecture, "hash": e.architecture_hash, "purpose": p.get("purpose"),
                   "ok": t == EventType.EXECUTION_COMPLETED, **{k: p.get(k) for k in ("runtime_s", "cpu_time_s", "max_memory_mb", "cost", "violation")}}
            st["executions"].append(rec)
            if p.get("purpose") == "candidate_evaluation":
                st["counters"]["architecture_evaluations"] += 1
                st["counters"]["adaptation_cost"] += float(p.get("cost") or 0.0)
            else:
                st["counters"]["execution_cost"] += float(p.get("cost") or 0.0)
            st["resource_series"].append({"seq": e.seq, "step": e.step, "cpu_time_s": p.get("cpu_time_s"), "max_memory_mb": p.get("max_memory_mb"),
                                          "latency_ms": (p.get("runtime_s") or 0) * 1000, "architecture_evaluations": st["counters"]["architecture_evaluations"],
                                          "adaptation_cost": st["counters"]["adaptation_cost"]})
            if t == EventType.EXECUTION_FAILED:
                st["counters"]["failures"] += 1
                st["failures"].append({"seq": e.seq, "step": e.step, "kind": "execution", "architecture": e.selected_architecture, "reason": e.reason})
        elif t == EventType.RESOURCE_LIMIT_HIT:
            st["failures"].append({"seq": e.seq, "step": e.step, "kind": "resource", "architecture": e.selected_architecture, "reason": e.reason})
        elif t == EventType.RESULT_EVALUATED:
            st["evaluations"].append({"seq": e.seq, "step": e.step, "architecture": e.selected_architecture, **p})
            if e.architecture_hash in st["architectures"]:
                st["architectures"][e.architecture_hash]["performance"].append({"step": e.step, "purpose": p.get("purpose"), "quality": p.get("quality")})
        elif t == EventType.PRINCIPLE_CREATED:
            st["principles"]["created"].append(p)
        elif t == EventType.PRINCIPLE_SUPPORTED:
            st["principles"]["supported"].append(p)
        elif t == EventType.PRINCIPLE_CONTRADICTED:
            st["principles"]["contradicted"].append(p)
        elif t == EventType.RUN_COMPLETED:
            st["completed"] = True
            st["summary"] = p
    return st


def summarize(e: Event) -> str:
    p = e.payload
    t = e.event_type
    a = e.selected_architecture or ""
    if t == EventType.CONSTRAINT_CHANGED:
        return f"{p.get('event', {}).get('type', 'constraint changed')} {p.get('event', {}).get('params', '')}"
    if t == EventType.ARCHITECTURE_GENERATED:
        return f"generated {len(e.candidate_architectures)} candidate(s): " + ", ".join(c.get("alias", "?") for c in e.candidate_architectures)
    if t == EventType.ARCHITECTURE_REJECTED:
        return f"rejected {a} — {e.reason}"
    if t == EventType.ARCHITECTURE_SELECTED:
        return f"selected {a} — {e.reason}"
    if t in (EventType.ADAPTATION_DECISION, EventType.DO_NOT_ADAPT):
        return f"{p.get('outcome')} — {e.reason}"
    if t == EventType.EXECUTION_COMPLETED:
        return f"execution of {a} completed ({p.get('purpose')}, {float(p.get('runtime_s') or 0):.2f}s)"
    if t == EventType.EXECUTION_FAILED:
        return f"execution of {a} failed — {e.reason}"
    if t == EventType.RESULT_EVALUATED:
        return f"{a} quality {float(p.get('quality') or 0):.3f} ({p.get('purpose')})"
    if t in (EventType.PRINCIPLE_CREATED, EventType.PRINCIPLE_SUPPORTED, EventType.PRINCIPLE_CONTRADICTED, EventType.PRINCIPLE_RETRIEVED):
        ids = p.get("principle_id") or ",".join(q.get("id", "?") for q in p.get("principles", []))
        return f"{t.value.lower().replace('_', ' ')} {ids}"
    if t == EventType.MEMORY_RETRIEVED:
        return f"memory retrieved {p.get('n', 0)} pattern(s)"
    if t == EventType.VALIDATION_FAILED:
        return f"validation of {a} failed — {e.reason}"
    if t == EventType.ENVIRONMENT_OBSERVED:
        env = e.environment_state
        return f"observed env: memory {env.get('memory_mb')}MB cpu {env.get('cpu')} network {env.get('network')} priority {env.get('priority')}"
    return e.reason or t.value.lower().replace("_", " ")


def explanations(events: List[Event]) -> List[Dict[str, Any]]:
    """Human-readable per-step explanation derived strictly from recorded events."""
    by_step: Dict[int, List[Event]] = {}
    for e in events:
        if e.step is not None:
            by_step.setdefault(e.step, []).append(e)
    out = []
    for step in sorted(by_step):
        evs = by_step[step]
        def pick(t):
            return [e for e in evs if e.event_type == t]
        observed = [summarize(e) for e in pick(EventType.ENVIRONMENT_OBSERVED) + pick(EventType.CONSTRAINT_CHANGED)]
        retrieved = [summarize(e) for e in pick(EventType.MEMORY_RETRIEVED) + pick(EventType.PRINCIPLE_RETRIEVED)]
        considered = [f"{c.get('alias')} ({c.get('name')}, source {c.get('source')}, est. cost {c.get('estimated_cost')})"
                      for e in pick(EventType.ARCHITECTURE_GENERATED) for c in e.candidate_architectures]
        rejected = [summarize(e) for e in pick(EventType.ARCHITECTURE_REJECTED)]
        selected = [summarize(e) for e in pick(EventType.ARCHITECTURE_SELECTED)]
        decisions = pick(EventType.ADAPTATION_DECISION) + pick(EventType.DO_NOT_ADAPT)
        expected = [f"{d.payload.get('outcome')}: expected gain {d.expected_gain}, estimated adaptation cost {d.estimated_cost} — {d.reason}" for d in decisions]
        actual = [f"{summarize(e)}" for e in pick(EventType.RESULT_EVALUATED) if e.payload.get("purpose") == "task"]
        actual += [f"actual adaptation cost {d.actual_cost} (decision error {d.payload.get('decision_error')})" for d in decisions if d.actual_cost is not None]
        learned = [summarize(e) for e in pick(EventType.PRINCIPLE_CREATED) + pick(EventType.PRINCIPLE_SUPPORTED) + pick(EventType.PRINCIPLE_CONTRADICTED)]
        out.append({"step": step, "observed": observed, "retrieved": retrieved, "considered": considered, "rejected": rejected,
                    "selected": selected, "expected": expected, "actual": actual, "learned": learned})
    return out
