"""A per-corpus coherent world capture bound to one epoch."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast, final

from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.structural_index import ResolvedEdge

from beliefs.closure import RetractionEnumeration
from beliefs.corpus import (
    Finding,
    ReadView,
    SnapshotStanding,
    _CapturedCheckView,
    _collecting_view,
    _operation_lock_for,
    _producer_ids,
    snapshot_standing,
    validated_node,
)
from beliefs.errors import (
    CaptureDrift,
    ContractMismatch,
    CorpusDamaged,
    CorpusStateMalformed,
    EpochMalformed,
    EpochUnknown,
    ManifestMalformed,
    RecordNotPresent,
    ResolutionRefused,
)
from beliefs.sealed import sealed
from beliefs.world import derive, epoch, registry
from beliefs.world.read import BoundStamp, Location, NotPresent, Resolved, Unknown, _address_map, _stamp, _thawed

__all__ = ["DamageReport", "DriftReport", "WorldReadView", "open_world_view"]

_MINT = object()

LocatedState = Literal["resolved", "not-present", "unknown"]
"""`locate`'s answer as the three states the query evaluator reads (live-query design decision 9)."""


@final
@dataclass(frozen=True)
class DriftReport:
    corpus_id: str
    published_state: str
    captured_state: str
    unmapped: tuple[str, ...]


@final
@dataclass(frozen=True)
class DamageReport:
    corpus_id: str
    carrier: Path
    cause: Literal["construction", "base-pin"]
    findings: tuple[Finding, ...]


@sealed
@final
class WorldReadView:
    _stamp: BoundStamp
    _recorded: Mapping[str, tuple[str, str]]
    _held: Mapping[str, Mapping[str, Node]]
    _absent: tuple[str, ...]
    _drift: tuple[DriftReport, ...]
    _damaged: tuple[DamageReport, ...]
    _damaged_ids: frozenset[str]
    _captured: Mapping[str, tuple[Node, ...]]
    _manifests: Mapping[str, registry.CorpusManifest]
    _inbound: Mapping[tuple[str, str], tuple[ResolvedEdge, ...]]
    _producers: Mapping[tuple[str, str], tuple[str, ...]]
    _live: Mapping[str, ReadView]
    _retractions: RetractionEnumeration
    _producer_snapshot: str
    _captured_views: Mapping[str, _CapturedCheckView]
    _snapshot_standing: SnapshotStanding | None

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
        damaged: tuple[DamageReport, ...],
        damaged_ids: frozenset[str],
        captured: Mapping[str, tuple[Node, ...]],
        manifests: Mapping[str, registry.CorpusManifest],
        inbound: Mapping[tuple[str, str], tuple[ResolvedEdge, ...]],
        producers: Mapping[tuple[str, str], tuple[str, ...]],
        live: Mapping[str, ReadView],
        retractions: RetractionEnumeration,
        producer_snapshot: str,
        captured_views: Mapping[str, _CapturedCheckView],
    ) -> WorldReadView:
        if mint is not _MINT:
            raise ResolutionRefused("WorldReadView._opened is open_world_view's own route")
        view = object.__new__(cls)
        view._stamp = stamp
        view._recorded = recorded
        view._held = held
        view._absent = absent
        view._drift = drift
        view._damaged = damaged
        view._damaged_ids = damaged_ids
        view._captured = captured
        view._manifests = manifests
        view._inbound = inbound
        view._producers = producers
        view._live = live
        view._retractions = retractions
        view._producer_snapshot = producer_snapshot
        view._captured_views = captured_views
        view._snapshot_standing = None
        return view

    @property
    def stamp(self) -> BoundStamp:
        return self._stamp

    def absent(self) -> tuple[str, ...]:
        return self._absent

    def drift(self) -> tuple[DriftReport, ...]:
        return self._drift

    def damaged(self) -> tuple[DamageReport, ...]:
        return self._damaged

    def captured_records(self, corpus_id: str) -> tuple[Node, ...]:
        return tuple(node.model_copy(deep=True) for node in self._captured[corpus_id])

    def captured_manifest(self, corpus_id: str) -> registry.CorpusManifest:
        return self._manifests[corpus_id]

    def locate(self, ref: str) -> Resolved | NotPresent | Unknown:
        self._refuse_damaged(ref)
        entry = self._recorded.get(ref)
        if entry is None:
            return Unknown(self._stamp)
        corpus_id, uid = entry
        if corpus_id in self._absent:
            return NotPresent(self._stamp)
        return Resolved(Location(corpus_id, uid), self._stamp)

    def _located_state(self, ref: str) -> LocatedState:
        """`locate`'s answer as the evaluator's three states; damage refuses
        exactly as `locate` refuses it."""
        located = self.locate(ref)
        if type(located) is Unknown:
            return "unknown"
        if type(located) is NotPresent:
            return "not-present"
        return "resolved"

    def corpus_of(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        return None if entry is None else entry[0]

    def corpus_view(self, ref: str) -> ReadView:
        return self._live[self._located(ref).location.corpus_id]

    def published_producers(self, dataset: str) -> tuple[str, ...]:
        entry = self._recorded.get(dataset)
        return () if entry is None else self._producers.get(entry, ())

    def retraction_enumeration(self) -> RetractionEnumeration:
        """The enumeration the bound epoch published — the evaluator's, never a caller's."""
        return self._retractions

    def producer_snapshot_identity(self) -> str:
        """The bound epoch's producer-snapshot subject identity."""
        return self._producer_snapshot

    def snapshot_standing(self) -> SnapshotStanding:
        """The live fold over the present covered corpora, over the same
        captured records this view serves (slice 2 §8) — never over `_live`:
        a `ReadView` resolves through the index built at its open and
        enumerates the store as it is now, and the two disagree after a
        write; never through the epoch's address map: a post-build record
        has no epoch address. Folded on the first read, not at the open, so
        a report-mode reader that never asks (`audit_world`) is not refused
        by a raw-written chain member; `gather` asks, and is."""
        if self._snapshot_standing is None:
            self._snapshot_standing = snapshot_standing(self._captured_views)
        return self._snapshot_standing

    def resolve(self, ref: str) -> str | None:
        self._refuse_damaged(ref)
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
        self._refuse_damaged(ref)
        entry = self._recorded.get(ref)
        if entry is None:
            return []
        return [
            ResolvedEdge(relation=deepcopy(edge.relation), source_uid=edge.source_uid, target_uid=edge.target_uid)
            for edge in self._inbound.get(entry, ())
        ]

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        return _producer_ids(self, dataset, aliases=aliases)

    def iter_stored(self) -> Iterator[Node]:
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                yield self._held[corpus_id][uid].model_copy(deep=True)

    def _mapped_records(self) -> Iterator[tuple[str, Node]]:
        """Yield retained records mapped to their present corpus, without copying."""
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                yield corpus_id, self._held[corpus_id][uid]

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

    def _refuse_damaged(self, ref: str) -> None:
        entry = self._recorded.get(ref)
        if entry is not None and entry[0] in self._damaged_ids:
            raise CorpusDamaged(ref, entry[0], self._stamp)


def open_world_view(
    world: registry.World, published: epoch.Epoch, *, on_damage: Literal["refuse", "report"] = "refuse"
) -> WorldReadView:
    stamp = _stamp(published)
    enumeration = _carried_enumeration(published)
    producer_identity = published.receipts["producer-receipt.yaml"].subject_identity
    if producer_identity is None:
        raise EpochMalformed(f"{published.packaging_identity}: the producer receipt names no subject identity")
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
    manifests: dict[str, registry.CorpusManifest] = {}
    all_captured: dict[str, tuple[Node, ...]] = {}
    damaged: list[DamageReport] = []
    for corpus_id in sorted(carriers):
        carrier = carriers[corpus_id]
        with _operation_lock_for(carrier).capture():
            manifests[corpus_id] = registry.load_manifest(carrier)
            try:
                before = registry.corpus_state_identity(carrier)
                view = ReadView.opened_at(carrier)
                view._require_base_pin()
            except CorpusStateMalformed:
                if on_damage == "refuse":
                    raise
                remainder, findings = _collecting_view(carrier)
                damaged.append(DamageReport(corpus_id, carrier, "construction", findings))
                all_captured[corpus_id] = remainder
                continue
            except ContractMismatch:
                if on_damage == "refuse":
                    raise
                damaged.append(DamageReport(corpus_id, carrier, "base-pin", ()))
                all_captured[corpus_id] = ()
                continue
            records = tuple(view.iter_stored())
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole open is discarded and nothing is served"
                )
        captured[corpus_id] = {node.uid: node for node in records}
        all_captured[corpus_id] = records
        states[corpus_id] = before
        live[corpus_id] = view
    damaged_ids = frozenset(report.corpus_id for report in damaged)
    # `live`'s keys are exactly the present, readable covered corpora (§8): the ones
    # captured inside their own hold, with the drift check, and not diverted to `damaged`.
    captured_views = {corpus_id: _CapturedCheckView(all_captured[corpus_id]) for corpus_id in live}

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
                    source = recorded.get(relation.source)
                    if source is None:
                        continue
                    source_uid = source[1] if source[1] in held.get(source[0], {}) else None
                    inbound.setdefault(target, []).append(
                        ResolvedEdge(relation=relation, source_uid=source_uid, target_uid=target[1])
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
        damaged=tuple(damaged),
        damaged_ids=damaged_ids,
        captured=all_captured,
        manifests=manifests,
        inbound={key: tuple(edges) for key, edges in inbound.items()},
        producers={location: tuple(sorted(runs)) for location, runs in producer_sets.items()},
        live=live,
        retractions=enumeration,
        producer_snapshot=producer_identity,
        captured_views=captured_views,
    )


def _carried_enumeration(published: epoch.Epoch) -> RetractionEnumeration:
    """Parse the receipt's §7.6 enumeration and check it against its named subject."""
    receipt = published.receipts["retraction-receipt.yaml"]
    carried = receipt.document.get("enumeration")
    if not isinstance(carried, Mapping):
        raise EpochMalformed(f"{published.packaging_identity}: retraction-receipt.yaml carries no enumeration mapping")
    try:
        enumeration = derive.retraction_enumeration(_thawed(carried))
    except Exception as caught:
        raise EpochMalformed(
            f"{published.packaging_identity}: the carried enumeration is not §7.6's projection: {caught}"
        ) from caught
    identity = derive.retraction_enumeration_identity(enumeration)
    if identity != receipt.subject_identity:
        raise EpochMalformed(
            f"{published.packaging_identity}: the carried enumeration does not digest to the subject the receipt "
            f"names ({identity} != {receipt.subject_identity})"
        )
    return enumeration
