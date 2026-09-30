"""Unique identifiers for experiments, executions and other entities."""
import uuid
import time


def new_id(prefix: str) -> str:
    """Return a time-prefixed unique id such as ``exp_1700000000_9f3c...``.

    The timestamp keeps ids sortable in the database; the uuid guarantees uniqueness.
    """
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:12]}"
