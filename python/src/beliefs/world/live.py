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

from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import final

from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.structural_index import ResolvedEdge

from beliefs import stored
from beliefs.corpus import ReadView, _operation_lock_for, validated_node
from beliefs.errors import (
    CaptureDrift,
    ContractMismatch,
    CorpusStateMalformed,
    ManifestMalformed,
    ResolutionRefused,
    SelectionRefused,
)
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.view_query import ViewQuery
from beliefs.world import derive, registry
from beliefs.world.selection import Unresolved, _denoted
from beliefs.world.view import LocatedState

__all__ = ["LIVE_SELECTION_VERSION", "CaptureStamp", "LiveSelection", "evaluate_live_query"]

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


@final
class _LiveCapture:
    """The capture `_denoted` reads on the live path (decision 9): publish's
    address map over the captured world records, those records by corpus and
    uid, and the inbound edges between them. It records no absent corpus's
    addresses (decision 4), so it never answers `not-present`."""

    def __init__(
        self,
        recorded: Mapping[str, tuple[str, str]],
        held: Mapping[str, Mapping[str, Node]],
        inbound: Mapping[tuple[str, str], tuple[ResolvedEdge, ...]],
    ) -> None:
        self._recorded = recorded
        self._held = held
        self._inbound = inbound

    def _located_state(self, ref: str) -> LocatedState:
        return "resolved" if ref in self._recorded else "unknown"

    def corpus_of(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        return None if entry is None else entry[0]

    def resolve(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        return None if entry is None else self._held[entry[0]][entry[1]].id

    def get(self, ref: str) -> Node:
        entry = self._recorded.get(ref)
        if entry is None:
            raise RefError(f"no node resolves ref {ref!r}")
        return validated_node(self._held[entry[0]][entry[1]]).model_copy(deep=True)

    def inbound(self, ref: str) -> list[ResolvedEdge]:
        entry = self._recorded.get(ref)
        if entry is None:
            return []
        return [
            ResolvedEdge(relation=deepcopy(edge.relation), source_uid=edge.source_uid, target_uid=edge.target_uid)
            for edge in self._inbound.get(entry, ())
        ]

    def live_id(self, uid: str) -> str:
        for records in self._held.values():
            if (node := records.get(uid)) is not None:
                return node.id
        raise KeyError(uid)

    def _mapped_records(self) -> Iterator[tuple[str, Node]]:
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                yield corpus_id, self._held[corpus_id][uid]


def evaluate_live_query(world: registry.World, query: ViewQuery) -> LiveSelection:
    """Denote `query` over every admitted corpus's current state (§3), or refuse."""
    if type(world) is not registry.World:
        raise TypeError(f"evaluate_live_query takes a registry.World, not {type(world).__name__}")
    if not isinstance(query, ViewQuery):
        raise TypeError(f"evaluate_live_query takes a parsed ViewQuery, not {type(query).__name__}")
    carriers, absent = _coverage(world)
    captured, states, damaged = _capture(carriers)
    if damaged:
        raise SelectionRefused("corpus-damaged", refs=damaged)
    recorded = _address_map(captured, states)
    _require_unmapped_uids_unique(captured)
    held = {
        corpus_id: {node.uid: node for node in records if node.kind in stored.WORLD_KINDS}
        for corpus_id, records in captured.items()
    }
    denoted = _denoted(_LiveCapture(recorded, held, _inbound(recorded, held)), query)
    return LiveSelection(
        stamp=CaptureStamp(world.config.world_id, tuple(sorted(states.items()))),
        query=query,
        selected=denoted.selected,
        contributing=denoted.contributing,
        absent=absent,
        unresolved=denoted.unresolved,
    )


def _coverage(world: registry.World) -> tuple[dict[str, Path], tuple[str, ...]]:
    """Decision 3: the registry's live admitted set, read under the world
    barrier and released before any capture, each corpus present or absent as
    `open_world_view` resolves it. No epoch is read."""
    carriers: dict[str, Path] = {}
    absent: list[str] = []
    with registry._locked_barrier(world) as world_root:
        world._state.registry = registry._scan_registry(world_root)
        covered = registry._live_corpus_ids(world._state.registry)
        for corpus_id in covered:
            try:
                status = registry._reduce_status(world.config, world._state.registry, corpus_id)
            except ManifestMalformed as caught:
                raise ResolutionRefused(
                    f"{corpus_id}: a configured root claims a manifest this world cannot read, so it can say "
                    f"neither that the corpus is here nor that it is absent: {caught}"
                ) from caught
            if any(finding.code == "duplicate-carrier" for finding in status.findings):
                raise ResolutionRefused(
                    f"{corpus_id}: more than one configured carrier claims this corpus, so which bytes "
                    "answer is a configuration question rather than a resolution"
                )
            if status.present:
                carriers[corpus_id] = registry._carrier_roots(world.config, corpus_id)[0]
            else:
                absent.append(corpus_id)
    return carriers, tuple(absent)


def _capture(carriers: Mapping[str, Path]) -> tuple[dict[str, tuple[Node, ...]], dict[str, str], list[str]]:
    """Decisions 5 and 8: one hold per present corpus, serial, in sorted
    order. Both state reads and the one enumeration happen inside the hold; a
    moved state discards the whole evaluation, and damage is collected so the
    refusal names every damaged corpus."""
    captured: dict[str, tuple[Node, ...]] = {}
    states: dict[str, str] = {}
    damaged: list[str] = []
    for corpus_id in sorted(carriers):
        carrier = carriers[corpus_id]
        with _operation_lock_for(carrier).capture():
            try:
                before = registry.corpus_state_identity(carrier)
                view = ReadView.opened_at(carrier)
                view._require_base_pin()
            except CorpusStateMalformed:
                damaged.append(corpus_id)
                continue
            except ContractMismatch:
                damaged.append(corpus_id)
                continue
            records = tuple(view.iter_stored())
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole live evaluation is discarded and nothing is returned"
                )
        captured[corpus_id] = records
        states[corpus_id] = before
    return captured, states, damaged


def _address_map(
    captured: Mapping[str, tuple[Node, ...]], states: Mapping[str, str]
) -> Mapping[str, tuple[str, str]]:
    """Decisions 6 and 7: publish's own `derive.address_map` over the captured
    world-kind records, so its `AddressMapConflict` — `uid-corruption` before
    `duplicate-location` — reaches the caller unchanged."""
    located = [
        (corpus_id, node) for corpus_id in sorted(captured) for node in captured[corpus_id] if node.kind in stored.WORLD_KINDS
    ]
    return derive.address_map(
        derive.Capture(
            tuple(
                derive.CapturedCorpus(
                    corpus_id,
                    states[corpus_id],
                    tuple(
                        derive.CapturedRecord(
                            address=node.id, uid=node.uid, kind=node.kind, deprecated_ids=tuple(node.deprecated_ids)
                        )
                        for owner, node in located
                        if owner == corpus_id
                    ),
                )
                for corpus_id in sorted(captured)
            )
        )
    )


def _require_unmapped_uids_unique(captured: Mapping[str, tuple[Node, ...]]) -> None:
    """Decision 7's scoped W8b check, run only after the map succeeded: a uid
    held in two corpora where a holder is a record the map excludes."""
    holders: dict[str, list[tuple[str, Node]]] = {}
    for corpus_id in sorted(captured):
        for node in captured[corpus_id]:
            holders.setdefault(node.uid, []).append((corpus_id, node))
    for uid in sorted(holders):
        corpora = sorted({corpus_id for corpus_id, _ in holders[uid]})
        if len(corpora) > 1 and any(node.kind not in stored.WORLD_KINDS for _, node in holders[uid]):
            raise ResolutionRefused(
                f"uid {uid!r} is held by both {corpora[0]} and {corpora[1]}; world uid uniqueness is enforced "
                "and its violation is corruption, not a record with two homes (W8b, the view's half)"
            )


def _inbound(
    recorded: Mapping[str, tuple[str, str]], held: Mapping[str, Mapping[str, Node]]
) -> dict[tuple[str, str], tuple[ResolvedEdge, ...]]:
    """Inbound edges between held records, constructed as `open_world_view` constructs them."""
    inbound: dict[tuple[str, str], list[ResolvedEdge]] = {}
    for records in held.values():
        for node in records.values():
            for relation in node.relations:
                if (target := recorded.get(relation.target)) is not None:
                    source = recorded.get(relation.source)
                    if source is None:
                        continue
                    source_uid = source[1] if source[1] in held.get(source[0], {}) else None
                    inbound.setdefault(target, []).append(
                        ResolvedEdge(relation=relation, source_uid=source_uid, target_uid=target[1])
                    )
    return {key: tuple(edges) for key, edges in inbound.items()}
