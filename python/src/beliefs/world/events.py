"""The event domain of the event-level relation.

Spec: `docs/superpowers/specs/2026-09-21-event-level-l8-design.md` §3. An
**event** is one entry of one corpus chain; its **moment** is the position in
that chain at which it happened — an intent, a genesis or a committed
settlement at its own position, a registration at its committed settlement's,
and a pending or rolled-back registration nowhere. A cut's **placement** of a
chain is where its captured head sits in the live chain, and it exists only
when the captured genesis is the live genesis and the head is an entry of it.
The functions here are pure over already-inspected views; locks, seams and
epochs are `world/verify.py`'s.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from beliefs.errors import EventUnknown
from beliefs.world.logmodel import (
    GenesisEntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

__all__ = ["Event", "Order", "Placement", "contains", "excludes", "moment", "place"]


@dataclass(frozen=True)
class Event:
    """One entry of one corpus chain, named by the corpus and the entry digest."""

    corpus_id: str
    digest: str


Order: TypeAlias = Literal["a-precedes-b", "b-precedes-a", "unordered"]


def moment(view: WellFormedView, digest: str) -> int | None:
    """Where the event named by `digest` happened in `view`, or `None` where it
    has not (yet) happened.

    A registration's moment is its **committed** settlement: the transition
    happened when it committed, not when it was declared. A well-formed chain
    settles a registration at most once (the duplicate is L2's malformed arm,
    classified before this is reached), so the settlement is a lookup by
    `registration` digest, never "the next settlement".
    """
    positions = {entry.digest: index for index, entry in enumerate(view.entries)}
    if digest not in positions:
        raise EventUnknown(f"{digest}: no entry of this chain carries that digest")
    entry = view.entries[positions[digest]]
    if type(entry) is GenesisEntryView or type(entry) is IntentEntryView:
        return positions[digest]
    if type(entry) is SettledEntryView:
        return positions[digest] if entry.committed else None
    assert type(entry) is RegisteredEntryView
    for index, candidate in enumerate(view.entries):
        if type(candidate) is SettledEntryView and candidate.registration == digest:
            return index if candidate.committed else None
    return None


@dataclass(frozen=True)
class Placement:
    """One cut's reading of one chain: the captured head's position in the live chain."""

    head: int


def place(view: WellFormedView, *, genesis_digest: str, head_digest: str) -> Placement | None:
    """Where a captured `(genesis_digest, head_digest)` sits in `view`, or
    `None` where the capture speaks about no prefix of this chain: the genesis
    differs (the chain was replaced), or the head is no entry of it (the chain
    was truncated behind the capture, or replaced). A `None` placement
    establishes neither presence nor exclusion (spec decision 6)."""
    if genesis_digest != view.genesis.digest:
        return None
    for index, entry in enumerate(view.entries):
        if entry.digest == head_digest:
            return Placement(head=index)
    return None


def contains(placement: Placement, moment: int) -> bool:
    """The cut's captured head is at or after the moment: the event had happened."""
    return moment <= placement.head


def excludes(placement: Placement, moment: int) -> bool:
    """The cut's captured head is before the moment: the event had not happened."""
    return not contains(placement, moment)
