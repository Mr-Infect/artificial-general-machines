"""Capability registry (Section 5), loaded from configs/capabilities.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

from core.models import Capability

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "configs" / "capabilities.yaml"

KIND_MAP = {
    "models": "model",
    "reasoning": "reasoning",
    "memory": "memory",
    "verification": "verification",
    "tools": "tool",
    "components": "component",
}


class CapabilityRegistry:
    def __init__(self, capabilities: Iterable[Capability]):
        self._caps: Dict[str, Capability] = {}
        for c in capabilities:
            self.register(c)

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "CapabilityRegistry":
        raw = yaml.safe_load(Path(path).read_text())
        caps: List[Capability] = []
        for section, kind in KIND_MAP.items():
            for name, spec in (raw.get(section) or {}).items():
                spec = dict(spec or {})
                caps.append(Capability(name=name, kind=kind, **spec))
        return cls(caps)

    def register(self, cap: Capability) -> None:
        key = f"{cap.kind}:{cap.name}"
        if key in self._caps:
            raise ValueError(f"duplicate capability {key}")
        self._caps[key] = cap

    def get(self, kind: str, name: str) -> Optional[Capability]:
        return self._caps.get(f"{kind}:{name}")

    def has(self, kind: str, name: str) -> bool:
        return f"{kind}:{name}" in self._caps

    def names(self, kind: str) -> List[str]:
        return sorted(c.name for c in self._caps.values() if c.kind == kind)

    def all(self) -> List[Capability]:
        return list(self._caps.values())

    def all_keys(self) -> List[str]:
        return sorted(self._caps)
