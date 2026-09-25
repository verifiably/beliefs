"""Live view-query evaluation for attention reads.

Live-query design (`docs/designs/2026-09-24-live-query-evaluation-design.md`).
`evaluate_live_query` denotes a `ViewQuery` over every corpus the world admits
with no terminal status, each captured inside its own operation-lock hold, and
returns a `LiveSelection` stamped with the states it captured. It reads no
epoch, builds none and writes nothing. The denotation is `selection._denoted`,
the one `evaluate_query` runs, so the two paths differ only in what they
capture and how they stamp it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.view_query import ViewQuery
from beliefs.world import registry
from beliefs.world.selection import Unresolved

__all__ = ["LIVE_SELECTION_VERSION", "CaptureStamp", "LiveSelection"]

LIVE_SELECTION_VERSION = "science.live-selection.v1"


@sealed
@final
@dataclass(frozen=True)
class CaptureStamp:
    """What a live answer is bound to: one world and the per-corpus states its
    capture read (decision 2). There is no packaging identity and there will
    not be one: a live selection names bytes it read, never a publication."""

    world_id: str
    coverage: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        registry._require_lower_hex(self.world_id, 32, "world_id")
        if type(self.coverage) is not tuple or any(type(pair) is not tuple or len(pair) != 2 for pair in self.coverage):
            raise TypeError("coverage must be an exact tuple of (corpus_id, corpus_state) pairs")
        for _, state in self.coverage:
            registry._require_lower_hex(state, 64, "corpus_state")
        ids = [corpus_id for corpus_id, _ in self.coverage]
        if ids != sorted(set(ids)):
            raise ValueError("coverage names each corpus once, in sorted order")


@sealed
@final
@dataclass(frozen=True)
class LiveSelection:
    """What a query denotes over one live capture (§3). It is not a
    `Selection`, so nothing typed for an epoch-bound answer accepts it."""

    stamp: CaptureStamp
    query: ViewQuery
    selected: tuple[str, ...]
    contributing: tuple[str, ...]
    absent: tuple[str, ...]
    unresolved: tuple[Unresolved, ...]

    @property
    def complete(self) -> bool:
        return not self.absent and all(step.state != "not-present" for step in self.unresolved)

    def projection(self) -> dict[str, object]:
        return {
            "version": LIVE_SELECTION_VERSION,
            "capture": {
                "world": self.stamp.world_id,
                "coverage": [[corpus_id, state] for corpus_id, state in self.stamp.coverage],
            },
            "query": self.query.projection(),
            "selected": list(self.selected),
            "contributing": list(self.contributing),
            "absent": list(self.absent),
            "unresolved": [step.projection() for step in self.unresolved],
        }

    def identity(self) -> str:
        return v1.digest(LIVE_SELECTION_VERSION, self.projection())
