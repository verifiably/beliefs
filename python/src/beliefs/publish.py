"""The publish act, local (publish-act-local design; layer design §6.1): step 0
selects, refuses, appends the intent and freezes the snapshot and the request;
steps 1–6 stage, admit, export and reveal; step 8 binds; step 9 discards. A
retry reinvokes the same sequence from the request (§9). Every lifecycle call
goes through `root.py`'s wrappers; this module imports nothing of `atoms`."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused, MomentSeam
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.durable import ensure_directory, write_create_only
from beliefs.errors import CreateOnlyCollision, MalformedRecord, PublicationRefused, ValidationRefused
from beliefs.intents.publish import Destination
from beliefs.profile import ProfileSpec
from beliefs.publication import BINDING_KIND, MARKER_KIND, binding_address, binding_uid, marker_record, marker_uid
from beliefs.publication_doors import (
    OpenedPublication,
    _bind_publication,
    _open_publication,
    _refuse_publication,
    attempt_reading,
)
from beliefs.publish_request import (
    PublishRequest,
    Snapshot,
    closure_missing,
    decode_request,
    decode_snapshot,
    derive_pins,
    encode_request,
    encode_snapshot,
    pins_of,
    require_usable,
    staging_world_id_for,
)
from beliefs.report import (
    Entry,
    ExportCollision,
    Exported,
    PublicationExportEntry,
    PublicationRequestEntry,
    PublicationRevealEntry,
    PublicationStagingEntry,
    RequestCorrupt,
    Revealed,
    RevealRefused,
    Staged,
    StagingCorrupt,
    outcome_type,
)
from beliefs.root import (
    export_head_artifact,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    open_corpus,
    open_world,
    read_serviceable,
    replicate_export,
    restore_root,
)
from beliefs.runrecord import OperationPort
from beliefs.view_query import stored_query
from beliefs.world import Fresh, WorldConfig, load_manifest
from beliefs.world.anchors import CorpusSubject
from beliefs.world.read import current_epoch
from beliefs.world.registry import World
from beliefs.world.selection import evaluate_query
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from beliefs.world.view import open_world_view

__all__ = ["PublishRefused", "PublishUnresolved", "Published", "pending_publishes", "publish", "resume_publish"]


@dataclass(frozen=True)
class Published:
    event_token: str
    corpus_id: str
    marker: str
    binding: str
    artifact: str


@dataclass(frozen=True)
class PublishRefused:
    event_token: str
    outcome: str  # the report's last outcome type


@dataclass(frozen=True)
class PublishUnresolved:
    event_token: str
    reason: str  # "no-request" | "indeterminate" | "binding-without-report"


PublishOutcome = Published | PublishRefused | PublishUnresolved


@dataclass(frozen=True)
class _Attempt:
    writer: CorpusWriter
    resolver: CoordinationResolver
    opened: OpenedPublication
    request: PublishRequest
    snapshot: Snapshot
    op: Path
    staging_profile: ProfileSpec
    clock: Callable[[], str]
    seam: MomentSeam
    port: OperationPort | None

    @property
    def token(self) -> str:
        return self.opened.intent.event_token

    @property
    def subject(self) -> str:
        return str(binding_address(self.opened.intent.view, self.opened.intent.destination))


@dataclass(frozen=True)
class _Population:
    present: int
    complete: bool


def _require_publishes(writer: CorpusWriter) -> None:
    writer.authority.require("publish", (BINDING_KIND, MARKER_KIND))
    writer.authority.require("corpus-write", ("act-report", *stored.WORLD_KINDS))
    writer.authority.require("lifecycle")
    writer.authority.require("registry")


def _op_dir(operations_root: Path, event_token: str) -> Path:
    return operations_root / "publish" / event_token


# --- step 0 ------------------------------------------------------------------


def publish(
    writer: CorpusWriter,
    resolver: CoordinationResolver,
    world: World,
    *,
    view: CoordinationAddress,
    destination: Destination,
    operations_root: Path,
    staging_profile: ProfileSpec,
    clock: Callable[[], str],
    seam: MomentSeam,
    port: OperationPort | None = None,
) -> PublishOutcome:
    """Publish `view` to a local `destination` (spec §3–§8)."""
    _require_publishes(writer)
    if destination.type != "local":
        raise ValidationRefused("remote destinations arrive in cut 41")
    forbidden = (*resolver.mounted(), *world.config.corpus_roots, world.config.world_root)
    operations_root, resolved_destination = require_usable(operations_root, destination, forbidden=forbidden)
    # spec §4.1 item 7: the resolved path is the destination the intent and the request freeze
    destination = Destination.local(str(resolved_destination))
    resolved = resolver.resolve(view.unpinned())
    if resolved is None:
        raise PublicationRefused("view-unresolved")
    if type(resolved) is CoordinationRefused:
        raise PublicationRefused("divergent-view", tips=resolved.tips)
    assert type(resolved) is Node
    pinned = view.unpinned().pinned(resolved.uid)
    query = stored_query(resolved)
    published = current_epoch(world)
    read = open_world_view(world, published)
    selection = evaluate_query(read, query)
    if not selection.complete:
        absent = {*selection.absent, *(step.corpus_id for step in selection.unresolved if step.corpus_id is not None)}
        raise PublicationRefused("selection-incomplete", corpus_ids=tuple(sorted(absent)))
    if not selection.selected:
        raise PublicationRefused("empty-selection")
    if missing := closure_missing(read, selection.selected):
        raise PublicationRefused("closure-incomplete", refs=missing)
    pins = derive_pins(
        {corpus_id: read.captured_manifest(corpus_id).profile for corpus_id in selection.contributing},
        load_manifest(writer.root).profile,
    )
    if pins_of(staging_profile) != pins:
        raise PublicationRefused("profile-disagrees")
    records = tuple((address, node_to_markdown(read.get(address))) for address in selection.selected)
    opened = _open_publication(
        writer, resolver, view=view.unpinned(), destination=destination, clock=clock, seam=seam, port=port, expected_view=pinned,
    )
    token = opened.intent.event_token
    snapshot = Snapshot(token, records)
    request = PublishRequest(
        event_token=token,
        view=opened.intent.view,
        destination=destination,
        epoch=published.packaging_identity,
        world_id=world.config.world_id,
        pins=pins,
        selection=snapshot.identity(),
        staging_world_id=staging_world_id_for(token),
    )
    op = _op_dir(operations_root, token)
    ensure_directory(op)
    write_create_only(op / "selection.v1", encode_snapshot(snapshot))
    write_create_only(op / "request.v1", encode_request(request))
    attempt = _Attempt(writer, resolver, opened, request, snapshot, op, staging_profile, clock, seam, port)
    return _run(attempt)


# --- steps 1–9 -----------------------------------------------------------------


def _initialize(a: _Attempt) -> tuple[CorpusWriter, World, str] | StagingCorrupt:
    """Step 1, reinvoked on every retry: each initializer's predicate decides."""
    staging, world_root = a.op / "staging", a.op / "world"
    init_corpus_root(staging, authority=a.writer.authority)
    staging_writer = open_corpus(staging, authority=a.writer.authority, profile=a.staging_profile)
    if (staging / "corpus.yaml").exists():
        manifest = load_manifest(staging)
        if manifest.profile != a.request.pins:
            return StagingCorrupt(manifest.corpus_id, "pins-foreign", ())
    else:
        staging_writer.adopt_manifest(profile=a.request.pins)
    corpus_id = load_manifest(staging).corpus_id
    config = WorldConfig(world_root, a.request.staging_world_id, (staging,))
    init_world_root(config, authority=a.writer.authority)
    return staging_writer, open_world(config, authority=a.writer.authority), corpus_id


def _expected_marker(a: _Attempt) -> Node:
    return marker_record(
        a.opened.intent, world_id=a.request.world_id, epoch=a.request.epoch, selection=tuple(i for i, _ in a.snapshot.records),
    )


def _population(staging: CorpusWriter, corpus_id: str, snapshot: Snapshot, marker: Node) -> _Population | StagingCorrupt:
    """Spec §5's classification: a true prefix, complete, or corrupt."""
    root = Path(staging.root)
    present = {node.id: (root / staging._relative_path(node)).read_bytes() for node in ReadView.opened_at(root).iter_stored()}
    order = [record_id for record_id, _ in snapshot.records]
    extras = sorted(set(present) - set(order) - {marker.id})
    if extras:
        return StagingCorrupt(corpus_id, "extra", (extras[0],))
    n = 0
    for record_id, text in snapshot.records:
        if record_id not in present:
            break
        if present[record_id] != text.encode("utf-8"):
            return StagingCorrupt(corpus_id, "bytes", (record_id,))
        n += 1
    if any(record_id in present for record_id in order[n:]):
        return StagingCorrupt(corpus_id, "hole", (order[n],))
    if marker.id in present:
        if n != len(order) or present[marker.id] != node_to_markdown(marker).encode("utf-8"):
            return StagingCorrupt(corpus_id, "marker", (marker.id,))
        return _Population(n, True)
    return _Population(n, complete=False)


def _populate(a: _Attempt, staging: CorpusWriter, corpus_id: str) -> StagingCorrupt | None:
    """Step 2: continue a true prefix, write the marker last."""
    marker = _expected_marker(a)
    state = _population(staging, corpus_id, a.snapshot, marker)
    if type(state) is StagingCorrupt:
        return state
    assert type(state) is _Population
    if not state.complete:
        for _, text in a.snapshot.records[state.present :]:
            staging._stage_record(text)
        staging._stage_marker(marker)
    again = _population(staging, corpus_id, a.snapshot, marker)
    return again if type(again) is StagingCorrupt else None


def _admit_and_export(a: _Attempt, world: World, corpus_id: str) -> bytes:
    """Step 3: the admission reinvoked (its predicate converges), then the export."""
    world.admit(a.op / "staging", provenance=Fresh())
    return export_head_artifact(world, CorpusSubject(corpus_id))


def _export_root(a: _Attempt, corpus_id: str) -> Path:
    return Path(a.request.destination.locator) / corpus_id


def _sibling(a: _Attempt, corpus_id: str) -> Path:
    return Path(a.request.destination.locator) / f"{corpus_id}.head-artifact.v1"


def _write_sibling(a: _Attempt, corpus_id: str, artifact: bytes) -> ExportCollision | None:
    """Step 5: the create-only sibling."""
    sibling = _sibling(a, corpus_id)
    try:
        write_create_only(sibling, artifact)
    except CreateOnlyCollision:
        return ExportCollision(corpus_id, sibling.name)
    return None


def _serviceable(root: Path) -> bool:
    return root.exists() and read_serviceable(root)


def _replicate(a: _Attempt, corpus_id: str) -> None:
    """Step 6, first half: the exact replication, reinvoked on every retry
    whatever the export root's state (spec §6 step 6): its retained-operation
    check, not the root's serviceability, proves the root is this attempt's. A
    foreign occupant refuses, and the refusal propagates (spec §16 item 6)."""
    replicate_export(a.op / "staging", _export_root(a, corpus_id), authority=a.writer.authority)


def _restore(a: _Attempt, corpus_id: str) -> str:
    """Step 6, second half: the reveal — `restore_root` against the sibling read
    back. Called only after `_replicate` has proven the root is this attempt's."""
    export = _export_root(a, corpus_id)
    if _serviceable(export):
        return "validated"
    observers = ObserverSet((ArtifactCarrier.from_bytes(_sibling(a, corpus_id).read_bytes()),))
    report = restore_root(export, CorpusSubject(corpus_id), observers, authority=a.writer.authority)
    if _serviceable(export):
        return "validated"
    if report.outcome == "validated":
        raise MalformedRecord(f"{export}: restore validated but granted nothing")  # the engine's to explain, not a verdict
    return report.outcome


def _bind(a: _Attempt, corpus_id: str, artifact_identity: str, entries: tuple[Entry, ...]):
    """Step 8: the binding door, carrying the lifecycle entries."""
    return _bind_publication(
        a.writer, a.resolver, a.opened, corpus_id=corpus_id, marker=marker_uid(a.token), artifact=artifact_identity,
        remotely_revealed=False, clock=a.clock, seam=a.seam, port=a.port,
        lifecycle=entries,
    )


def _discard(op: Path) -> None:
    """Step 9: staging and its world go; the request and the snapshot stay."""
    for path in (op / "staging", op / "world"):
        for target in (path, metadata_root_for(path)):
            if target.exists():
                shutil.rmtree(target)


def _refused(a: _Attempt, entries: tuple[Entry, ...]) -> PublishRefused:
    report = _refuse_publication(a.writer, a.opened, entries, clock=a.clock, port=a.port)
    return PublishRefused(a.token, outcome_type(report.entries[-1].outcome))


def _run(a: _Attempt) -> PublishOutcome:
    """Steps 1–9, reinvoked identically on every retry (spec §2 decision 8)."""
    initialized = _initialize(a)
    if type(initialized) is StagingCorrupt:
        return _refused(a, (PublicationStagingEntry(a.subject, initialized),))
    staging, world, corpus_id = initialized
    corrupt = _populate(a, staging, corpus_id)
    if corrupt is not None:
        return _refused(a, (PublicationStagingEntry(a.subject, corrupt),))
    entries: list[Entry] = [PublicationStagingEntry(a.subject, Staged(corpus_id, len(a.snapshot.records)))]
    artifact = _admit_and_export(a, world, corpus_id)
    collision = _write_sibling(a, corpus_id, artifact)
    if collision is not None:
        return _refused(a, (*entries, PublicationExportEntry(a.subject, collision)))
    artifact_identity = sha256(artifact).hexdigest()
    entries.append(PublicationExportEntry(a.subject, Exported(corpus_id, artifact_identity)))
    _replicate(a, corpus_id)
    verdict = _restore(a, corpus_id)
    if verdict != "validated":
        return _refused(a, (*entries, PublicationRevealEntry(a.subject, RevealRefused(corpus_id, verdict))))
    entries.append(PublicationRevealEntry(a.subject, Revealed(corpus_id)))
    outcome = _bind(a, corpus_id, artifact_identity, tuple(entries))
    if outcome.binding is None:
        return PublishRefused(a.token, outcome_type(outcome.report.entries[-1].outcome))
    _discard(a.op)
    return Published(a.token, corpus_id, marker_uid(a.token), outcome.binding.uid, artifact_identity)


# --- resumption (§9) --------------------------------------------------------------


def _binding_present(writer: CorpusWriter, opened: OpenedPublication) -> bool:
    address = binding_address(opened.intent.view, opened.intent.destination)
    binding_id = f"{BINDING_KIND}:{address.project}.{address.local}.{binding_uid(opened.intent.event_token)}"
    return writer._corpus.store.path_for(binding_id).exists()


def _load(op: Path, opened: OpenedPublication) -> tuple[PublishRequest, Snapshot] | RequestCorrupt:
    try:
        request = decode_request((op / "request.v1").read_bytes())
    except MalformedRecord:
        return RequestCorrupt("undecodable")
    intent = opened.intent
    if request.event_token != intent.event_token or request.view != intent.view or request.destination != intent.destination:
        return RequestCorrupt("intent-disagrees")
    if not (op / "selection.v1").is_file():
        return RequestCorrupt("snapshot-missing")
    try:
        snapshot = decode_snapshot((op / "selection.v1").read_bytes())
    except MalformedRecord:
        return RequestCorrupt("snapshot-undecodable")
    if snapshot.identity() != request.selection or snapshot.event_token != intent.event_token:
        return RequestCorrupt("snapshot-mismatch")
    return request, snapshot


def resume_publish(
    writer: CorpusWriter,
    resolver: CoordinationResolver,
    *,
    event_token: str,
    operations_root: Path,
    staging_profile: ProfileSpec,
    clock: Callable[[], str],
    seam: MomentSeam,
    port: OperationPort | None = None,
) -> PublishOutcome:
    """Resume one attempt from its request (spec §9)."""
    _require_publishes(writer)
    reading = attempt_reading(writer, event_token, seam)
    if reading is None:
        raise ValidationRefused(f"no publish intent carries token {event_token}")
    if writer.authority.actor != reading.opened.intent.actor:
        raise ValidationRefused("a publish resumes only under its intent's actor")
    op = _op_dir(Path(operations_root).resolve(), event_token)
    present = _binding_present(writer, reading.opened)
    if reading.reading == "indeterminate":
        return PublishUnresolved(event_token, "indeterminate")
    if reading.reading == "closed":
        if not present:
            assert reading.outcome is not None
            return PublishRefused(event_token, reading.outcome)
        request = decode_request((op / "request.v1").read_bytes())
        _discard(op)
        return _published_from_disk(writer, reading.opened, request)
    if present:
        return PublishUnresolved(event_token, "binding-without-report")
    if not (op / "request.v1").is_file():
        return PublishUnresolved(event_token, "no-request")
    loaded = _load(op, reading.opened)
    if type(loaded) is RequestCorrupt:
        report = _refuse_publication(writer, reading.opened, (PublicationRequestEntry(
            str(binding_address(reading.opened.intent.view, reading.opened.intent.destination)), loaded),), clock=clock, port=port)
        return PublishRefused(event_token, outcome_type(report.entries[-1].outcome))
    request, snapshot = loaded
    if pins_of(staging_profile) != request.pins:
        raise ValidationRefused("a publish resumes only under a staging profile holding its request's pins")
    return _run(_Attempt(writer, resolver, reading.opened, request, snapshot, op, staging_profile, clock, seam, port))


def _published_from_disk(writer: CorpusWriter, opened: OpenedPublication, request: PublishRequest) -> Published:
    """A done attempt's outcome, read back from its binding revision."""
    address = binding_address(opened.intent.view, opened.intent.destination)
    binding_id = f"{BINDING_KIND}:{address.project}.{address.local}.{binding_uid(opened.intent.event_token)}"
    facet = writer.read_view.get(binding_id).facets[stored.COORDINATION_FACET]
    return Published(opened.intent.event_token, facet["corpus_id"], facet["marker"], binding_uid(opened.intent.event_token), facet["artifact"])


def pending_publishes(writer: CorpusWriter, *, operations_root: Path, seam: MomentSeam) -> tuple[str, ...]:
    """Every request under the operations root whose intent is `unfinished`,
    ascending by token (spec §3)."""
    root = Path(operations_root).resolve() / "publish"
    tokens: list[str] = []
    for request in sorted(root.glob("*/request.v1")) if root.is_dir() else ():
        token = request.parent.name
        reading = attempt_reading(writer, token, seam)
        if reading is not None and reading.reading == "unfinished":
            tokens.append(token)
    return tuple(tokens)
