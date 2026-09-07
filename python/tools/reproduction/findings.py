"""`findings.jsonl`: one line per finding, under the design's closed classes (§7)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from reproduction import paths

CLASSES = frozenset({"closed", "design-gap", "corpus-work", "defect", "host"})


def record(step: int, cls: str, reason: str, filed: str = "unfiled") -> None:
    if cls not in CLASSES:
        raise ValueError(f"finding class {cls!r} is not one of {sorted(CLASSES)}")
    paths.FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    with paths.FINDINGS.open("a") as out:
        out.write(
            json.dumps(
                {
                    "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "step": step,
                    "class": cls,
                    "reason": reason,
                    "filed": filed,
                },
                sort_keys=True,
            )
            + "\n"
        )
