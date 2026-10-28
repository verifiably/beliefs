"""A per-corpus coherent world capture bound to one epoch."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
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
    _recorded: Mapping[str, derive.AddressEntry]
    _held: Mapping[str, Mapping[str, Node]]
    _absent: tuple[str, ...]
    _drift: tuple[DriftReport, ...]
    _damaged: tuple[DamageReport, ...]
    _damaged_ids: frozenset[str]
    _captured: Mapping[str, tuple[Node, ...]]
    _contents: Mapping[str, Mapping[str, str]]
    _manifests: Mapping[str, registry.CorpusManifest]
    _inbound: Mapping[str, tuple[ResolvedEdge, ...]]
    _producers: Mapping[str, tuple[str, ...]]
    _live: Mapping[str, ReadView]
    _retractions: RetractionEnumeration
    _retraction_discovery: Mapping[str, tuple[str, ...]]
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
        recorded: Mapping[str, derive.AddressEntry],
        held: Mapping[str, Mapping[str, Node]],
        absent: tuple[str, ...],
        drift: tuple[DriftReport, ...],
        damaged: tuple[DamageReport, ...],
        damaged_ids: frozenset[str],
        captured: Mapping[str, tuple[Node, ...]],
        contents: Mapping[str, Mapping[str, str]],
        manifests: Mapping[str, registry.CorpusManifest],
        inbound: Mapping[str, tuple[ResolvedEdge, ...]],
        producers: Mapping[str, tuple[str, ...]],
        live: Mapping[str, ReadView],
        retractions: RetractionEnumeration,
        retraction_discovery: Mapping[str, tuple[str, ...]],
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
        view._contents = contents
        view._manifests = manifests
        view._inbound = inbound
        view._producers = producers
        view._live = live
        view._retractions = retractions
        view._retraction_discovery = MappingProxyType(dict(retraction_discovery))
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

    def captured(self) -> tuple[str, ...]:
        """The captured corpus ids, sorted: present, readable, captured under
        their own holds (cut 48 §5.2). Not `registry.admissions`, which also
        lists corpora admitted after the epoch."""
        return tuple(sorted(self._held))

    def captured_records(self, corpus_id: str) -> tuple[Node, ...]:
        return tuple(node.model_copy(deep=True) for node in self._captured[corpus_id])

    def captured_manifest(self, corpus_id: str) -> registry.CorpusManifest:
        return self._manifests[corpus_id]

    def _captured_holders(self, entry: derive.AddressEntry) -> tuple[str, ...]:
        return tuple(holder for holder in entry.holders if holder in self._held)

    def locate(self, ref: str) -> Resolved | NotPresent | Unknown:
        self._refuse_damaged(ref)
        entry = self._recorded.get(ref)
        if entry is None:
            return Unknown(self._stamp)
        present = self._captured_holders(entry)
        if not present:
            return NotPresent(self._stamp)
        return Resolved(Location(present[0], entry.uid, present), self._stamp)

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
        """The record's canonical holder: the least captured holder, or the
        least recorded holder when none is captured (cut 48 §5.2). A label,
        never a choice of content: every captured holder's copy is the same
        record, and a caller whose answer depends on which holder reads
        `holders_of`."""
        entry = self._recorded.get(ref)
        if entry is None:
            return None
        present = self._captured_holders(entry)
        return present[0] if present else entry.holders[0]

    def holders_of(self, ref: str) -> tuple[str, ...]:
        """Every corpus the epoch records as holding the record, sorted; `()`
        for an address it never observed."""
        entry = self._recorded.get(ref)
        return () if entry is None else entry.holders

    def corpus_view(self, ref: str) -> ReadView:
        return self._live[self._located(ref).location.corpus_id]

    def published_producers(self, dataset: str) -> tuple[str, ...]:
        entry = self._recorded.get(dataset)
        return () if entry is None else self._producers.get(entry.uid, ())

    def retraction_enumeration(self) -> RetractionEnumeration:
        """The enumeration the bound epoch published — the evaluator's, never a caller's."""
        return self._retractions

    def producer_snapshot_identity(self) -> str:
        """The bound epoch's producer-snapshot subject identity."""
        return self._producer_snapshot

    def snapshot_standing(self, *, counts: Callable[[str, str], bool] | None = None) -> SnapshotStanding:
        """The live fold over the present covered corpora, over the same
        captured records this view serves (slice 2 §8) — never over `_live`:
        a `ReadView` resolves through the index built at its open and
        enumerates the store as it is now, and the two disagree after a
        write; never through the epoch's address map: a post-build record
        has no epoch address. Folded on the first read, not at the open, so
        a report-mode reader that never asks (`audit_world`) is not refused
        by a raw-written chain member; `gather` asks, and is."""
        if counts is not None:
            return snapshot_standing(self._captured_views, counts=counts)
        if self._snapshot_standing is None:
            self._snapshot_standing = snapshot_standing(self._captured_views)
        return self._snapshot_standing

    def _mapped_view(self, corpus_id: str) -> _CapturedCheckView:
        records = tuple(self._held[corpus_id].values())
        addresses = {
            ref: self._held[corpus_id][entry.uid].id
            for ref, entry in self._recorded.items()
            if corpus_id in entry.holders and entry.uid in self._held[corpus_id]
        }
        return _CapturedCheckView(records, addresses=addresses)

    def resolve(self, ref: str) -> str | None:
        self._refuse_damaged(ref)
        entry = self._recorded.get(ref)
        if entry is None:
            return None
        present = self._captured_holders(entry)
        if not present:
            return None
        return self._held[present[0]][entry.uid].id

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
            for edge in self._inbound.get(entry.uid, ())
        ]

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        return _producer_ids(self, dataset, aliases=aliases)

    def iter_stored(self) -> Iterator[Node]:
        for _holders, node in self._mapped_holders():
            yield node.model_copy(deep=True)

    def _mapped_records(self) -> Iterator[tuple[str, Node]]:
        """Yield retained records mapped to each captured holder, without copying:
        one `(corpus_id, node)` per holder, for callers that file something per corpus."""
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                yield corpus_id, self._held[corpus_id][uid]

    def _mapped_holders(self) -> Iterator[tuple[tuple[str, ...], Node]]:
        """Yield each retained record once with its captured holders, ordered by
        `(canonical holder, uid)`, without copying: for callers that decide
        something per record over its holders (cut 48 §5.2)."""
        seen: set[str] = set()
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                if uid in seen:
                    continue
                seen.add(uid)
                node = self._held[corpus_id][uid]
                entry = self._recorded.get(node.id)
                holders = self._captured_holders(entry) if entry is not None else (corpus_id,)
                yield holders, node

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
            raise RecordNotPresent(ref, self._recorded[ref].holders[0], self._stamp)
        return cast(Resolved, located)

    def _refuse_damaged(self, ref: str) -> None:
        """A damaged holder refuses the address, unless another holder was
        captured and every captured copy equals the content the epoch mapped
        (cut 48 §5.1): the damaged copy cannot be compared, so only the
        publication can vouch for the copies that can."""
        entry = self._recorded.get(ref)
        if entry is None:
            return
        damaged = [holder for holder in entry.holders if holder in self._damaged_ids]
        if not damaged:
            return
        present = self._captured_holders(entry)
        if (
            present
            and entry.content is not None
            and all(self._contents[holder][entry.uid] == entry.content for holder in present)
        ):
            return
        raise CorpusDamaged(ref, damaged[0], self._stamp)


def open_world_view(
    world: registry.World, published: epoch.Epoch, *, on_damage: Literal["refuse", "report"] = "refuse"
) -> WorldReadView:
    stamp = _stamp(published)
    enumeration = _carried_enumeration(published)
    discovery = _thawed(published.documents["retraction-discovery-map.yaml"])
    assert isinstance(discovery, Mapping)
    epoch._check_targets(cast(Mapping[object, object], discovery))
    retraction_discovery = {
        cast(str, entry["target"]): tuple(cast(list[str], entry["retractions"]))
        for entry in cast(list[Mapping[str, object]], discovery["targets"])
    }
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
    contents: dict[str, dict[str, str]] = {}
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
        contents[corpus_id] = {node.uid: registry.content_identity(node) for node in records}
        all_captured[corpus_id] = records
        states[corpus_id] = before
        live[corpus_id] = view
    damaged_ids = frozenset(report.corpus_id for report in damaged)
    # `live`'s keys are exactly the present, readable covered corpora (§8): the ones
    # captured inside their own hold, with the drift check, and not diverted to `damaged`.
    captured_views = {corpus_id: _CapturedCheckView(all_captured[corpus_id]) for corpus_id in live}

    mapped: dict[str, set[str]] = {}
    for address, entry in recorded.items():
        for corpus_id in entry.holders:
            mapped.setdefault(corpus_id, set()).add(entry.uid)
            if corpus_id not in captured:
                continue
            node = captured[corpus_id].get(entry.uid)
            if node is None or (address != node.id and address not in node.deprecated_ids):
                raise ResolutionRefused(
                    f"{address}: {corpus_id}: {carriers[corpus_id]}: the present carrier does not hold uid "
                    f"{entry.uid!r} under this address as the epoch mapped it; a carrier that disagrees with the "
                    "publication is corruption and not an absence"
                )
            live_entry = recorded.get(node.id)
            if live_entry is None or live_entry.uid != entry.uid or corpus_id not in live_entry.holders:
                raise ResolutionRefused(
                    f"{node.id}: {corpus_id}: {carriers[corpus_id]}: mapped uid {entry.uid!r} has a live address "
                    "the epoch did not map to that record; a new canonical address requires a new publication"
                )
    # Cut 48 §5.1: captured copies of one record must agree with each other. Agreement with the
    # epoch's content is not required — a single holder that moved is drift, and so are two that moved alike.
    checked: set[str] = set()
    for address, entry in sorted(recorded.items()):
        if entry.uid in checked:
            continue
        checked.add(entry.uid)
        present = [holder for holder in entry.holders if holder in captured]
        if len(present) > 1 and len({contents[holder][entry.uid] for holder in present}) > 1:
            raise ResolutionRefused(
                f"{address}: the captured holders {tuple(present)} disagree in content; the holders agreed when "
                "the epoch was built and no longer do, so this world cannot say which copy answers (rebuild to "
                "publish the conflict, or resolve it)"
            )

    # W8b, the view's half (cut 48 §5.1): a uid held by two captured corpora is admitted only where the
    # recorded map established those corpora as holders of one record.
    owners: dict[str, list[str]] = {}
    for corpus_id in sorted(captured):
        for uid in captured[corpus_id]:
            owners.setdefault(uid, []).append(corpus_id)
    for uid, corpora in owners.items():
        if len(corpora) < 2:
            continue
        entries = {recorded.get(captured[corpus_id][uid].id) for corpus_id in corpora}
        established = len(entries) == 1 and next(iter(entries)) is not None
        if not established or not set(corpora) <= set(cast(derive.AddressEntry, next(iter(entries))).holders):
            raise ResolutionRefused(
                f"uid {uid!r} is held by both {corpora[0]} and {corpora[1]}; world uid uniqueness is enforced "
                "and its violation is corruption, not a record with two homes (W8b, the view's half)"
            )

    drift: list[DriftReport] = []
    held: dict[str, dict[str, Node]] = {}
    for corpus_id in sorted(captured):
        known = mapped.get(corpus_id, set())
        unmapped = tuple(sorted(uid for uid in captured[corpus_id] if uid not in known))
        if unmapped or states[corpus_id] != published_states[corpus_id]:
            drift.append(DriftReport(corpus_id, published_states[corpus_id], states[corpus_id], unmapped))
        held[corpus_id] = {uid: node for uid, node in captured[corpus_id].items() if uid in known}

    def held_anywhere(entry: derive.AddressEntry) -> bool:
        return any(entry.uid in held.get(holder, {}) for holder in entry.holders)

    inbound: dict[str, list[ResolvedEdge]] = {}
    seen: set[str] = set()
    for corpus_id in sorted(held):
        for uid in sorted(held[corpus_id]):
            if uid in seen:
                continue
            seen.add(uid)
            node = held[corpus_id][uid]
            for relation in node.relations:
                if (target := recorded.get(relation.target)) is not None:
                    source = recorded.get(relation.source)
                    if source is None:
                        continue
                    source_uid = source.uid if held_anywhere(source) else None
                    inbound.setdefault(target.uid, []).append(
                        ResolvedEdge(relation=relation, source_uid=source_uid, target_uid=target.uid)
                    )

    producer_sets: dict[str, set[str]] = {}
    entries = cast(tuple[Mapping[str, object], ...], published.documents["producers-map.yaml"]["producers"])
    for entry in entries:
        if (located := recorded.get(cast(str, entry["dataset"]))) is not None:
            producer_sets.setdefault(located.uid, set()).update(cast(list[str], entry["runs"]))

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
        contents=contents,
        manifests=manifests,
        inbound={key: tuple(edges) for key, edges in inbound.items()},
        producers={uid: tuple(sorted(runs)) for uid, runs in producer_sets.items()},
        live=live,
        retractions=enumeration,
        retraction_discovery=retraction_discovery,
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
