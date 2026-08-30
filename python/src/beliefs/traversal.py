"""One algorithm, two adjacency adapters (substrate consolidation design §3).

The traversal `nodes` withdrew lives here, above its one-hop `outbound()` /
`inbound()` operations. It serves two callers whose *edges* have nothing in
common — a `supersedes` step is a stored `Relation` with a predicate and a
`directed` flag; a lineage step is a **facet** with neither — so the sharing
stops at the walk itself. What is shared is behaviour: **cycle-safe,
start-excluding, skip-and-report, sorted**, certified once because one function
performs both closures.

**The result is structured, and a bare list of reached ids could not satisfy
this contract.** The algorithm promises to *report* a step whose target does not
resolve, and the lineage caller must tell an absent **ancestor** from an absent
**producing run**. Neither survives a return type carrying only what resolved,
and for a facet-valued step there is no second source of truth to recover it
from — `nodes`' own `dangling()` is relations-only and cannot see one.

**Every unresolved entry says where it was stored.** A relation entry carries
the source node's live id and the position of the relation in that node's
stored list; without those, `X ─cites→ M` and `Y ─cites→ M` produce one
identical entry, two defects deduplicate into one, and the ordering has no
tie-break. A lineage entry carries the dataset, the route, and which position in
the route failed.

**Start-excluding.** The start never appears in `reached`, a cycle back to it
included. Callers that need it say so — substrate §5's inspected set is
`{observed root} ∪ closure`, the union written out, because deleting the root's
own immediate parent must still be seen.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Protocol, TypeAlias, final

from beliefs.sealed import sealed

__all__ = [
    "Adjacency",
    "LineageEntry",
    "Reach",
    "RelationEntry",
    "Step",
    "UnresolvedEntry",
    "closure",
]


@sealed
@final
@dataclass(frozen=True)
class RelationEntry:
    """An unresolved relation step, as the relation adapter saw it."""

    source: str
    """The live id of the node holding the relation."""

    position: int
    """The relation's position in that node's stored list — unique within it,
    which is what makes the ordering total."""

    predicate: str
    target: str

    @property
    def sort_key(self) -> tuple[object, ...]:
        return (self.source, self.position)


@sealed
@final
@dataclass(frozen=True)
class LineageEntry:
    """An unresolved lineage step, as the lineage adapter saw it."""

    dataset: str
    route: int
    position: str
    """`run` or `ancestor` — the distinction the relation adapter cannot
    express, and the one substrate §5 step 2 decides on."""

    target: str

    @property
    def sort_key(self) -> tuple[object, ...]:
        return (self.dataset, self.route, self.position)


UnresolvedEntry: TypeAlias = RelationEntry | LineageEntry


@sealed
@final
@dataclass(frozen=True)
class Step:
    """One adjacency step: the ref as stored, what it resolves to, and the
    entry that reports it when it resolves to nothing."""

    stored: str
    resolved: str | None
    entry: UnresolvedEntry
    follow: bool = True
    """Whether a resolved step is an edge of the closure. A lineage route's
    producing run is **checked and not followed**: its absence is a finding, and
    its presence is not an ancestor. Without this the walk would have to choose
    between reporting the run and keeping runs out of a dataset's closure."""


class Adjacency(Protocol):
    """What the walk consumes. Deliberately narrow: the walk knows nothing
    about predicates, directions, tags or facets — an adapter that needed the
    walk to know would be asking for a second algorithm."""

    def steps(self, ref: str) -> tuple[Step, ...]: ...


@sealed
@final
@dataclass(frozen=True)
class Reach:
    reached: tuple[str, ...]
    """Live ids, sorted, never including the start."""

    unresolved: tuple[UnresolvedEntry, ...]
    """Every step that reached nothing, in the adapter's own total order."""


def closure(start: str, adjacency: Adjacency) -> Reach:
    """Walk `adjacency` from `start` — cycle-safe, start-excluding,
    skip-and-report, sorted.

    An unresolvable step is **skipped and reported**, never fatal: a walk that
    stopped at the first dangling reference would report one defect and hide
    every other, and a walk that dropped it silently would report none.
    """
    seen = {start}
    reached: set[str] = set()
    unresolved: list[UnresolvedEntry] = []
    frontier = deque([start])
    while frontier:
        for step in adjacency.steps(frontier.popleft()):
            if step.resolved is None:
                unresolved.append(step.entry)
                continue
            if not step.follow:
                continue
            if step.resolved in seen:
                continue  # cycle-safe: one visit per node, however it is reached
            seen.add(step.resolved)
            reached.add(step.resolved)
            frontier.append(step.resolved)
    return Reach(
        reached=tuple(sorted(reached)),
        unresolved=tuple(sorted(unresolved, key=lambda entry: entry.sort_key)),
    )
