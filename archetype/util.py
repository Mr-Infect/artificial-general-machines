"""Deterministic randomness and small numeric helpers shared by evaluator and agents (no hidden state)."""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any


def seed_for(*parts: Any) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:16], 16)


def rng_for(*parts: Any) -> random.Random:
    """Every random stream in ARCHETYPE derives from a string key, so any job can be replayed exactly."""
    return random.Random(seed_for(*parts))


def stable_hash(obj: Any, n: int = 16) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:n]


def clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x
