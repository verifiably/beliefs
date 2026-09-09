"""A per-corpus coherent world capture bound to one epoch."""

from __future__ import annotations

import copy
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast, final

from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.structural_index import ResolvedEdge

from beliefs.corpus import ReadView, _producer_ids, _root_state_for, validated_node
from beliefs.errors import CaptureDrift, EpochUnknown, ManifestMalformed, RecordNotPresent, ResolutionRefused
from beliefs.sealed import sealed
from beliefs.world import epoch, registry
from beliefs.world.read import BoundStamp, Location, NotPresent, Resolved, Unknown, _address_map, _stamp

__all__ = ["DriftReport", "WorldReadView", "open_world_view"]

_MINT = object()


@final
@dataclass(frozen=True)
class DriftReport:
    corpus_id: str
    published_state: str
    captured_state: str
    unmapped: tuple[str, ...]


@sealed
@final
class WorldReadView:
    _stamp: BoundStamp
    _recorded: Mapping[str, tuple[str, str]]
    _held: Mapping[str, Mapping[str, Node]]
    _absent: tuple[str, ...]
    _drift: tuple[DriftReport, ...]
    _inbound: Mapping[tuple[str, str], tuple[ResolvedEdge, ...]]
    _producers: Mapping[tuple[str, str], tuple[str, ...]]
    _live: Mapping[str, ReadView]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ResolutionRefused("WorldReadView is opened, never constructed — use open_world_view(world, published)")

    @classmethod
    def _opened(
        cls,
        mint: object,
        *,
        stamp: BoundStamp,
        recorded: Mapping[str, tuple[str, str]],
        held: Mapping[str, Mapping[str, Node]],
        absent: tuple[str, ...],
        drift: tuple[DriftReport, ...],
        inbound: Mapping[tuple[str, str], tuple[ResolvedEdge, ...]],
        producers: Mapping[tuple[str, str], tuple[str, ...]],
        live: Mapping[str, ReadView],
    ) -> WorldReadView:
        if mint is not _MINT:
            raise ResolutionRefused("WorldReadView._opened is open_world_view's own route")
        view = object.__new__(cls)
        view._stamp = stamp
        view._recorded = recorded
        view._held = held
        view._absent = absent
        view._drift = drift
        view._inbound = inbound
        view._producers = producers
        view._live = live
        return view

    @property
    def stamp(self) -> BoundStamp:
        return self._stamp

    def absent(self) -> tuple[str, ...]:
        return self._absent

    def drift(self) -> tuple[DriftReport, ...]:
        return self._drift

    def locate(self, ref: str) -> Resolved | NotPresent | Unknown:
        entry = self._recorded.get(ref)
        if entry is None:
            return Unknown(self._stamp)
        corpus_id, uid = entry
        if corpus_id in self._absent:
            return NotPresent(self._stamp)
        return Resolved(Location(corpus_id, uid), self._stamp)

    def corpus_of(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        return None if entry is None else entry[0]

    def corpus_view(self, ref: str) -> ReadView:
        return self._live[self._located(ref).location.corpus_id]

    def published_producers(self, dataset: str) -> tuple[str, ...]:
        entry = self._recorded.get(dataset)
        return () if entry is None else self._producers.get(entry, ())

    def resolve(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        if entry is None or entry[0] in self._absent:
            return None
        return self._held[entry[0]][entry[1]].id

    def holds(self, ref: str) -> bool:
        return self.resolve(ref) is not None

    def get(self, ref: str) -> Node:
        located = self._located(ref)
        node = self._held[located.location.corpus_id][located.location.uid]
        return validated_node(node).model_copy(deep=True)

    def inbound(self, ref: str) -> list[ResolvedEdge]:
        entry = self._recorded.get(ref)
        if entry is None:
            return []
        return [
            ResolvedEdge(relation=copy.deepcopy(edge.relation), source_uid=edge.source_uid, target_uid=edge.target_uid)
            for edge in self._inbound.get(entry, ())
        ]

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        return _producer_ids(self, dataset, aliases=aliases)

    def iter_stored(self) -> Iterator[Node]:
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                yield self._held[corpus_id][uid].model_copy(deep=True)

    def live_id(self, uid: str) -> str:
        for records in self._held.values():
            if (node := records.get(uid)) is not None:
                return node.id
        raise KeyError(uid)

    def _located(self, ref: str) -> Resolved:
        located = self.locate(ref)
        if type(located) is Unknown:
            raise RefError(f"no node resolves ref {ref!r}")
        if type(located) is NotPresent:
            raise RecordNotPresent(ref, self._recorded[ref][0], self._stamp)
        return cast(Resolved, located)


def open_world_view(world: registry.World, published: epoch.Epoch) -> WorldReadView:
    stamp = _stamp(published)
    recorded = _address_map(published)
    covered = tuple(corpus_id for corpus_id, _ in published.coverage)
    published_states = dict(published.coverage)

    carriers: dict[str, Path] = {}
    with registry._locked_barrier(world) as world_root:
        if published.world_anchor.subject != world.config.world_id:
            raise EpochUnknown(
                f"{published.packaging_identity}: epoch belongs to world {published.world_anchor.subject}, "
                f"not {world.config.world_id}"
            )
        world._state.registry = registry._scan_registry(world_root)
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
    absent = tuple(corpus_id for corpus_id in covered if corpus_id not in carriers)

    captured: dict[str, dict[str, Node]] = {}
    states: dict[str, str] = {}
    live: dict[str, ReadView] = {}
    for corpus_id in sorted(carriers):
        carrier = carriers[corpus_id]
        state = _root_state_for(carrier, world._corpus_executor_factory)
        with state.lock.capture():
            before = registry.corpus_state_identity(carrier)
            view = ReadView.opened_at(carrier)
            view._require_base_pin()
            records = tuple(view.iter_stored())
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole open is discarded and nothing is served"
                )
        captured[corpus_id] = {node.uid: node for node in records}
        states[corpus_id] = before
        live[corpus_id] = view

    mapped: dict[str, set[str]] = {}
    for address, (corpus_id, uid) in recorded.items():
        mapped.setdefault(corpus_id, set()).add(uid)
        if corpus_id not in captured:
            continue
        node = captured[corpus_id].get(uid)
        if node is None or (address != node.id and address not in node.deprecated_ids):
            raise ResolutionRefused(
                f"{address}: {corpus_id}: {carriers[corpus_id]}: the present carrier does not hold uid {uid!r} "
                "under this address as the epoch mapped it; a carrier that disagrees with the publication is "
                "corruption and not an absence"
            )
        if recorded.get(node.id) != (corpus_id, uid):
            raise ResolutionRefused(
                f"{node.id}: {corpus_id}: {carriers[corpus_id]}: mapped uid {uid!r} has a live address the epoch "
                "did not map to that record; a new canonical address requires a new publication"
            )

    owners: dict[str, str] = {}
    for corpus_id in sorted(captured):
        for uid in captured[corpus_id]:
            if uid in owners:
                raise ResolutionRefused(
                    f"uid {uid!r} is held by both {owners[uid]} and {corpus_id}; world uid uniqueness is enforced "
                    "and its violation is corruption, not a record with two homes (W8b, the view's half)"
                )
            owners[uid] = corpus_id

    drift: list[DriftReport] = []
    held: dict[str, dict[str, Node]] = {}
    for corpus_id in sorted(captured):
        known = mapped.get(corpus_id, set())
        unmapped = tuple(sorted(uid for uid in captured[corpus_id] if uid not in known))
        if unmapped or states[corpus_id] != published_states[corpus_id]:
            drift.append(DriftReport(corpus_id, published_states[corpus_id], states[corpus_id], unmapped))
        held[corpus_id] = {uid: node for uid, node in captured[corpus_id].items() if uid in known}

    inbound: dict[tuple[str, str], list[ResolvedEdge]] = {}
    for records in held.values():
        for uid, node in records.items():
            for relation in node.relations:
                if (target := recorded.get(relation.target)) is not None:
                    inbound.setdefault(target, []).append(
                        ResolvedEdge(relation=relation, source_uid=uid, target_uid=target[1])
                    )

    producer_sets: dict[tuple[str, str], set[str]] = {}
    entries = cast(tuple[Mapping[str, object], ...], published.documents["producers-map.yaml"]["producers"])
    for entry in entries:
        if (located := recorded.get(cast(str, entry["dataset"]))) is not None:
            producer_sets.setdefault(located, set()).update(cast(list[str], entry["runs"]))

    return WorldReadView._opened(
        _MINT,
        stamp=stamp,
        recorded=recorded,
        held=held,
        absent=absent,
        drift=tuple(drift),
        inbound={key: tuple(edges) for key, edges in inbound.items()},
        producers={location: tuple(sorted(runs)) for location, runs in producer_sets.items()},
        live=live,
    )
