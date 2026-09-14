"""View-query evaluation over the world read view.

World resolution slice 4 §3. `evaluate_query` is a pure function of an open
`WorldReadView` and a parsed `ViewQuery`: it opens nothing, names no
`current`, reads no coordination record and consults no profile. It refuses
a damaged or drifted capture at entry, locates every address the query
names before denoting anything, and reports absence and dangling steps on
the selection instead of folding them into it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, final

from nodes.core.node import Node

from beliefs.corpus import validated_node
from beliefs.errors import SelectionRefused
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.view_query import Addresses, Closure, Kinds, Predicate, ReferencesTerm, ViewQuery
from beliefs.world.read import BoundStamp, NotPresent, Unknown
from beliefs.world.view import WorldReadView

__all__ = ["SELECTION_VERSION", "Selection", "Unresolved", "evaluate_query"]

SELECTION_VERSION = "science.view-selection.v1"

UnresolvedState = Literal["not-present", "unknown"]


@final
@dataclass(frozen=True)
class Unresolved:
    """One closure step that reached nothing, with the state `locate` gave
    its target and, for `not-present`, the absent corpus."""

    source: str
    predicate: str
    target: str
    state: UnresolvedState
    corpus_id: str | None

    def __post_init__(self) -> None:
        if self.state not in ("not-present", "unknown"):
            raise ValueError(f"{self.state!r} is not an unresolved state")
        if (self.corpus_id is None) != (self.state == "unknown"):
            raise ValueError("a not-present step names its corpus and an unknown one names none")

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.source, self.predicate, self.target)

    def projection(self) -> dict[str, object]:
        return {
            "source": self.source,
            "predicate": self.predicate,
            "target": self.target,
            "state": self.state,
            "corpus_id": [] if self.corpus_id is None else [self.corpus_id],
        }


@sealed
@final
@dataclass(frozen=True)
class Selection:
    """What a query denotes at one publication (§3.1). `complete` is derived
    and not a projection member: a member could disagree with the two it is
    computed from."""

    stamp: BoundStamp
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
            "version": SELECTION_VERSION,
            "epoch": self.stamp.packaging_identity,
            "query": self.query.projection(),
            "selected": list(self.selected),
            "contributing": list(self.contributing),
            "absent": list(self.absent),
            "unresolved": [step.projection() for step in self.unresolved],
        }

    def identity(self) -> str:
        return v1.digest(SELECTION_VERSION, self.projection())


Held = Mapping[str, tuple[str, Node]]
"""Live address -> (corpus_id, retained record), one enumeration of the capture."""


def evaluate_query(view: WorldReadView, query: ViewQuery) -> Selection:
    """Denote `query` over `view` (§3.2), or refuse."""
    if type(view) is not WorldReadView:
        raise TypeError(
            f"evaluate_query takes a WorldReadView, not {type(view).__name__}: a corpus-local selection is the "
            "fb-2026-07-30-019 defect W7 exists to refuse"
        )
    if not isinstance(query, ViewQuery):
        raise TypeError(f"evaluate_query takes a parsed ViewQuery, not {type(query).__name__}")
    if view.damaged():
        raise SelectionRefused("corpus-damaged", refs=[report.corpus_id for report in view.damaged()])
    moved = [report.corpus_id for report in view.drift() if report.captured_state != report.published_state]
    if moved:
        # A report whose states agree lists records outside the world map by
        # construction (coordination and prose kinds); only a moved state refuses.
        raise SelectionRefused("corpus-drifted", refs=moved)
    _require_located(view, query.addresses())

    held: dict[str, tuple[str, Node]] = {node.id: (corpus_id, node) for corpus_id, node in view._mapped_records()}
    unresolved: dict[tuple[str, str, str], Unresolved] = {}
    selected: set[str] = set()
    for clause in query.clauses:
        members: set[str] | None = None
        for predicate in clause.predicates:
            denoted = _denote(view, predicate, held, unresolved)
            members = denoted if members is None else members & denoted
        selected |= members or set()

    for address in selected:
        validated_node(held[address][1])
    contributing = sorted({held[address][0] for address in selected})
    return Selection(
        stamp=view.stamp,
        query=query,
        selected=tuple(sorted(selected)),
        contributing=tuple(contributing),
        absent=view.absent(),
        unresolved=tuple(sorted(unresolved.values(), key=lambda step: step.sort_key)),
    )


def _require_located(view: WorldReadView, addresses: tuple[str, ...]) -> None:
    """Every address the query names resolves, or the evaluation refuses
    naming each offender of the worst state; unknown and not-present never
    share one refusal (W6)."""
    unknown: list[str] = []
    not_present: list[tuple[str, str]] = []
    for address in addresses:
        located = view.locate(address)
        if type(located) is Unknown:
            unknown.append(address)
        elif type(located) is NotPresent:
            corpus_id = view.corpus_of(address)
            assert corpus_id is not None
            not_present.append((address, corpus_id))
    if unknown:
        raise SelectionRefused("address-unknown", refs=unknown)
    if not_present:
        raise SelectionRefused(
            "address-not-present",
            refs=[address for address, _ in not_present],
            corpus_ids=[corpus_id for _, corpus_id in not_present],
        )


def _denote(
    view: WorldReadView,
    predicate: Predicate,
    held: Held,
    unresolved: dict[tuple[str, str, str], Unresolved],
) -> set[str]:
    if isinstance(predicate, Kinds):
        kinds = set(predicate.values)
        return {address for address, (_, node) in held.items() if node.kind in kinds}
    if isinstance(predicate, Addresses):
        resolved: set[str] = set()
        for address in predicate.values:
            live = view.resolve(address)
            assert live is not None, address  # _require_located ran
            resolved.add(live)
        return resolved
    if isinstance(predicate, ReferencesTerm):
        raise NotImplementedError("references-term lands in Task 4")
    if isinstance(predicate, Closure):
        raise NotImplementedError("closure lands in Task 5")
    raise TypeError(f"{type(predicate).__name__} is not a v1 predicate")

