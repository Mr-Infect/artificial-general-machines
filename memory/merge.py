"""Merge structural-pattern and principle memories from several SQLite files into one (warm-start
conditions built from more than one source domain). Rows are copied; principle records with the
same rule + structural pattern are merged so that evidence from several sources accumulates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from core.db import Database, PatternRow
from memory.principles import ArchitecturalPrinciple, PrincipleMemory


def merge_memory_dbs(sources: Iterable[Path], dest: Path) -> dict:
    dest = Path(dest)
    if dest.exists():
        dest.unlink()
    out = Database(dest)
    pm = PrincipleMemory(out)
    n_pat = n_prn = 0
    for src in sources:
        src = Path(src)
        if not src.exists():
            continue
        sdb = Database(src)
        for raw in sdb.patterns():
            out.add(PatternRow(pattern_id=raw["pattern_id"], architecture_hash=raw["architecture_hash"], source_experiment=raw["source_experiment"],
                               source_domain=raw["source_domain"], quality=raw["quality"], json=json.dumps(raw)))
            n_pat += 1
        for raw in sdb.principles():
            pm.merge(ArchitecturalPrinciple.model_validate(raw))
            n_prn += 1
    return {"dest": str(dest), "patterns": n_pat, "principles_in": n_prn, "principles_out": len(pm.all())}
