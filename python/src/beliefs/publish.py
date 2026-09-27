"""The publish act (publish-act-local and publish-act-remote designs): step 0
selects, refuses, appends the intent and freezes the snapshot and the request;
steps 1–6 stage, admit, export and reveal; step 7 transports remotely;
step 8 binds; step 9 discards. A retry resumes from the request or, after the
remote reveal, from its transport mark. Every lifecycle call goes through
`root.py`'s wrappers; this module imports nothing of `atoms`."""

from __future__ import annotations

import shutil
import stat
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from nodes.core.errors import CollisionError, NodesError, PlacementError
from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.frontmatter import node_from_bytes, node_from_markdown, node_to_markdown
from nodes.core.node import Node
from nodes.core.paths import path_for_node_id

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused, MomentSeam
from beliefs.corpus import CoordinationResolver, CorpusWriter, ReadView
from beliefs.durable import ensure_directory, write_create_only
from beliefs.errors import CreateOnlyCollision, MalformedRecord, PublicationRefused, ScienceError, ValidationRefused
from beliefs.intents.publish import Destination
from beliefs.profile import ProfileSpec
from beliefs.publication import (
    BINDING_KIND,
    MARKER_KIND,
    binding_address,
    binding_uid,
    marker_address,
    marker_consistent,
    marker_record,
    marker_uid,
    publication_content_malformed,
)
from beliefs.publication_doors import (
    OpenedPublication,
    _bind_publication,
    _open_publication,
    _refuse_publication,
    attempt_reading,
    unfinished_attempts,
)
from beliefs.publish_request import (
    PublishRequest,
    Snapshot,
    TransportMark,
    closure_missing,
    decode_mark,
    decode_request,
    decode_snapshot,
    derive_pins,
    encode_mark,
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
    PublicationTransportEntry,
    RequestCorrupt,
    Revealed,
    RevealRefused,
    Staged,
    StagingCorrupt,
    Transported,
    TransportIncomplete,
    outcome_type,
)
from beliefs.root import (
    evaluate_copy,
    export_chain_head,
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
from beliefs.transport import Transport, TransportAbandoned, listing_identity, local_listing, transport_files
from beliefs.view_query import stored_query
from beliefs.world import Fresh, WorldConfig, load_manifest
from beliefs.world.anchors import CorpusSubject, decode_head_artifact
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
    reason: str  # "no-request" | "indeterminate" | "binding-without-report" | "transport-mark-corrupt"


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
    transport: Transport | None

    @property
    def token(self) -> str:
        return self.opened.intent.event_token

    @property
    def subject(self) -> str:
        return str(binding_address(self.opened.intent.view, self.opened.intent.destination))

    def remote(self) -> _Remote:
        """Steps 7–9's view of this attempt (decision 5)."""
        assert self.transport is not None
        return _Remote(self.writer, self.resolver, self.opened, self.op, self.clock, self.seam, self.port, self.transport)


@dataclass(frozen=True)
class _Population:
    present: int
    complete: bool


@dataclass(frozen=True)
class _Remote:
    """Steps 7–9 of a remote attempt (remote decision 5): the mark, never the
    request or the snapshot."""

    writer: CorpusWriter
    resolver: CoordinationResolver
    opened: OpenedPublication
    op: Path
    clock: Callable[[], str]
    seam: MomentSeam
    port: OperationPort | None
    transport: Transport

    @property
    def token(self) -> str:
        return self.opened.intent.event_token

    @property
    def subject(self) -> str:
        return str(binding_address(self.opened.intent.view, self.opened.intent.destination))


def _require_transport(destination: Destination, transport: Transport | None) -> None:
    """Remote §3.2: a remote destination needs a transport and a local one takes none."""
    if destination.type == "remote" and transport is None:
        raise ValidationRefused("a remote destination needs a transport")
    if destination.type == "local" and transport is not None:
        raise ValidationRefused("a local destination takes no transport")


def _require_publishes(writer: CorpusWriter) -> None:
    writer.authority.require("publish", (BINDING_KIND, MARKER_KIND))
    writer.authority.require("corpus-write", ("act-report", *stored.WORLD_KINDS))
    writer.authority.require("lifecycle")
    writer.authority.require("registry")


def _op_dir(operations_root: Path, event_token: str) -> Path:
    return operations_root / "publish" / event_token


def _mark_nonregular(op: Path) -> bool:
    """Only an absent entry is unmarked; never follow a damaged mark's symlink."""
    try:
        return not stat.S_ISREG((op / "transport.v1").lstat().st_mode)
    except FileNotFoundError:
        return False
    except OSError:
        return True


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
    transport: Transport | None = None,
) -> PublishOutcome:
    """Publish `view` to `destination` (local and remote specs §3–§8)."""
    _require_publishes(writer)
    _require_transport(destination, transport)
    forbidden = (*resolver.mounted(), *world.config.corpus_roots, world.config.world_root)
    # local §4.1 item 7, remote §4.1: the returned destination is the one the intent and the request freeze
    operations_root, destination = require_usable(operations_root, destination, forbidden=forbidden)
    if destination.type == "remote":
        # remote §4.1, decision 6: a stranded attempt that may have shared its marker blocks the pair
        blocking = tuple(token for token in unfinished_attempts(writer, view, destination, seam) if (_op_dir(operations_root, token) / "transport.v1").is_file())
        blocking = tuple(sorted(set(blocking) | {token for token in unfinished_attempts(writer, view, destination, seam) if _mark_nonregular(_op_dir(operations_root, token))}))
        if blocking:
            raise PublicationRefused("publish-unfinished", tokens=blocking)
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
    _require_snapshot_records(read, records)
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
    attempt = _Attempt(writer, resolver, opened, request, snapshot, op, staging_profile, clock, seam, port, transport)
    return _run(attempt)


class _Captured(Protocol):
    """What the pre-intent check reads of a world view: its captured records."""

    def get(self, ref: str) -> Node: ...


_PROBE_TOKEN = "0" * 32
"""A well-formed stand-in token: the pre-intent check runs the snapshot's own rule
before the real token exists, and the rule does not read the token's value."""


def _require_snapshot_records(read: _Captured, records: tuple[tuple[str, str], ...]) -> None:
    """Spec §4.3, asserted before the intent (§4.1 item 8): the records satisfy the
    snapshot's own rule (each parses, carries its id and is its canonical
    rendering), and each re-parses to the record the view captured. It holds by
    construction; a failure is a malformed record and nothing is written."""
    Snapshot(_PROBE_TOKEN, records)
    for address, text in records:
        if node_from_markdown(text) != read.get(address):
            raise MalformedRecord(f"{address}: its snapshot text does not re-parse to the record the view captured")


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
    """Spec §5's classification: a true prefix, complete, or corrupt. A staging
    store `nodes` refuses to read — bytes that do not parse, a record off its
    mapped path, a duplicate uid — is neither a prefix nor complete: `bytes`,
    naming no record, since none can be read to name (Y7)."""
    root = Path(staging.root)
    try:
        present = {node.id: (root / staging._relative_path(node)).read_bytes() for node in ReadView.opened_at(root).iter_stored()}
    except (NodesValidationError, PlacementError, CollisionError):
        return StagingCorrupt(corpus_id, "bytes", ())
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
    if a.request.destination.type == "remote":
        return _remote_export(a.op, corpus_id)  # remote decision 7
    return Path(a.request.destination.locator) / corpus_id


def _sibling(a: _Attempt, corpus_id: str) -> Path:
    if a.request.destination.type == "remote":
        return _remote_sibling(a.op, corpus_id)
    return Path(a.request.destination.locator) / f"{corpus_id}.head-artifact.v1"


def _remote_export(op: Path, corpus_id: str) -> Path:
    return op / "export" / corpus_id


def _remote_sibling(op: Path, corpus_id: str) -> Path:
    return op / "export" / f"{corpus_id}.head-artifact.v1"


def _write_sibling(a: _Attempt, corpus_id: str, artifact: bytes) -> ExportCollision | None:
    """Step 5: the create-only sibling."""
    sibling = _sibling(a, corpus_id)
    ensure_directory(sibling.parent)
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


def _bind(a: _Attempt | _Remote, corpus_id: str, artifact_identity: str, entries: tuple[Entry, ...], *, remote: bool = False):
    """Step 8: the binding door, carrying the lifecycle entries. A remote reveal
    refused here is an orphan (remote §4.4)."""
    return _bind_publication(
        a.writer, a.resolver, a.opened, corpus_id=corpus_id, marker=marker_uid(a.token), artifact=artifact_identity,
        remotely_revealed=remote, clock=a.clock, seam=a.seam, port=a.port,
        lifecycle=entries,
    )


def _discard(op: Path) -> None:
    """Step 9: staging and its world go; the request and the snapshot stay."""
    for path in (op / "staging", op / "world"):
        for target in (path, metadata_root_for(path)):
            if target.exists():
                shutil.rmtree(target)


def _refused(a: _Attempt | _Remote, entries: tuple[Entry, ...]) -> PublishRefused:
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
    if a.request.destination.type == "remote":
        return _transport_and_bind(a.remote(), _mark(a, corpus_id, artifact_identity), tuple(entries))
    outcome = _bind(a, corpus_id, artifact_identity, tuple(entries))
    if outcome.binding is None:
        return PublishRefused(a.token, outcome_type(outcome.report.entries[-1].outcome))
    _discard(a.op)
    return Published(a.token, corpus_id, marker_uid(a.token), outcome.binding.uid, artifact_identity)


# --- the remote steps (remote §4.2–§4.4) ------------------------------------------


def _mark(a: _Attempt, corpus_id: str, artifact_identity: str) -> TransportMark:
    """The durable record that a remote reveal may begin (decision 2): create-only,
    after step 6 validates and before the first `push`."""
    transport_files(a.op / "export", corpus_id)  # §3.1: refuse an invalid layout before the mark
    mark = TransportMark(a.token, a.request.destination, corpus_id, marker_uid(a.token), artifact_identity, len(a.snapshot.records))
    write_create_only(a.op / "transport.v1", encode_mark(mark))
    return mark


def _push(r: _Remote, files: Mapping[str, Path]) -> TransportAbandoned | None:
    """Step 7's upload through the seam: idempotent, reinvoked whole on every retry (§14 item 5)."""
    return r.transport.push(r.opened.intent.destination, files)


def _verify(r: _Remote, corpus_id: str) -> dict[str, str]:
    """Step 7's read-back: the remote's enumeration of the publication's whole namespace."""
    return dict(r.transport.listing(r.opened.intent.destination, corpus_id))


def _listing_or_none(files: Mapping[str, Path]) -> dict[str, str] | None:
    try:
        return local_listing(files)
    except OSError:
        return None  # a file the act cannot read is damage (planning note)


def _evaluate_export(r: _Remote, mark: TransportMark) -> str:
    """§4.3 step 2: the recipient's evaluation of the retained export against its
    own sibling, granting nothing; `"unreadable"` when it cannot be judged."""
    try:
        observers = ObserverSet((ArtifactCarrier.from_bytes(_remote_sibling(r.op, mark.corpus_id).read_bytes()),))
    except (OSError, ScienceError):
        return "unreadable"  # a sibling gone or undecodable since the mark: damage, like any other
    return evaluate_copy(_remote_export(r.op, mark.corpus_id), CorpusSubject(mark.corpus_id), observers)


def _export_damaged(r: _Remote, mark: TransportMark) -> bool:
    """The one place the export's content is judged, on a fresh run and on a resume."""
    return _evaluate_export(r, mark) != "validated"


def _transport(r: _Remote, mark: TransportMark) -> Transported | TransportIncomplete:
    """Step 7 (§4.3): upload exactly the bytes the evaluation judged, then verify
    by the remote's own listing. The act, not the seam, decides."""
    damaged = TransportIncomplete(mark.corpus_id, mark.marker, "export-damaged")
    try:
        files = transport_files(r.op / "export", mark.corpus_id)
    except (OSError, MalformedRecord):
        return damaged
    before = _listing_or_none(files)
    if before is None or _export_damaged(r, mark):
        return damaged
    expected = _listing_or_none(files)
    if expected is None or expected != before:
        return damaged
    if type(_push(r, files)) is TransportAbandoned:
        return TransportIncomplete(mark.corpus_id, mark.marker, "abandoned")
    listing = _verify(r, mark.corpus_id)
    if listing != expected:
        return TransportIncomplete(mark.corpus_id, mark.marker, "listing-mismatch")
    return Transported(mark.corpus_id, listing_identity(expected))


def _transport_and_bind(r: _Remote, mark: TransportMark, entries: tuple[Entry, ...]) -> PublishOutcome:
    """Steps 7, 8 and 9 from the mark. An incomplete transport writes its report
    alone and carries its orphan (decision 4)."""
    transported = _transport(r, mark)
    if type(transported) is TransportIncomplete:
        return _refused(r, (*entries, PublicationTransportEntry(r.subject, transported)))
    assert type(transported) is Transported
    entries = (*entries, PublicationTransportEntry(r.subject, transported))
    outcome = _bind(r, mark.corpus_id, mark.artifact, entries, remote=True)
    if outcome.binding is None:
        return PublishRefused(r.token, outcome_type(outcome.report.entries[-1].outcome))
    _discard(r.op)
    return Published(r.token, mark.corpus_id, mark.marker, outcome.binding.uid, mark.artifact)


def _marker_path(r: _Remote, mark: TransportMark) -> Path:
    """The export's marker file, by name: its id follows from the intent and the mark's uid."""
    address = marker_address(r.opened.intent.view, r.opened.intent.destination)
    return _remote_export(r.op, mark.corpus_id) / path_for_node_id(f"{MARKER_KIND}:{address.project}.{address.local}.{mark.marker}")


def _export_agrees(r: _Remote, mark: TransportMark) -> bool:
    """§4.2 as identity only (planning note): the export's manifest names the
    mark's corpus, the sibling is the mark's artifact and names that corpus and
    the export's chain head, and the export holds one `publication` file, the
    mark's marker by name. No record's content is read here, so a damaged
    selected record reaches the evaluation and closes as `export-damaged`."""
    export, sibling = _remote_export(r.op, mark.corpus_id), _remote_sibling(r.op, mark.corpus_id)
    try:
        if not _serviceable(export) or load_manifest(export).corpus_id != mark.corpus_id:
            return False
        data = sibling.read_bytes()
        if sha256(data).hexdigest() != mark.artifact:
            return False
        artifact = decode_head_artifact(data)
    except (OSError, ValueError, ScienceError):  # file I/O, the artifact decoder, the manifest
        return False
    head = export_chain_head(export)
    if head is None or artifact.subject != CorpusSubject(mark.corpus_id) or (artifact.genesis, artifact.head) != head:
        return False
    marker = _marker_path(r, mark)
    kind_directory = export / marker.relative_to(export).parts[0]
    held = sorted(path for path in kind_directory.rglob("*") if path.is_file()) if kind_directory.is_dir() else []
    return held == [marker]


def _mark_corrupt(r: _Remote, mark: TransportMark) -> bool:
    """§4.2: the mark agrees with its intent, then with its export's identity."""
    intent = r.opened.intent
    if mark.event_token != intent.event_token or mark.destination != intent.destination or mark.marker != marker_uid(intent.event_token):
        return True
    return not _export_agrees(r, mark)


def _marker_agrees(r: _Remote, mark: TransportMark) -> bool:
    """After the export evaluated `validated`: its marker is well formed and
    consistent, is the mark's, and selects `mark.records` records."""
    try:
        node = node_from_bytes(_marker_path(r, mark).read_bytes())
    except (OSError, NodesError):
        return False
    if node.kind != MARKER_KIND or publication_content_malformed(node) or not marker_consistent(node) or node.uid != mark.marker:
        return False
    return len(node.facets[stored.COORDINATION_FACET]["selection"]) == mark.records


def _resume_from_mark(r: _Remote) -> PublishOutcome:
    """Decision 5: steps 7–9 from the mark alone. Identity first (a failure is
    `transport-mark-corrupt`); then the export's content (a failure closes the
    attempt `export-damaged` with its orphan, pushing nothing); then the marker's
    content, trusted only once the evaluation validated it."""
    try:
        mark = decode_mark((r.op / "transport.v1").read_bytes())
    except (OSError, MalformedRecord):
        return PublishUnresolved(r.token, "transport-mark-corrupt")
    if _mark_corrupt(r, mark):
        return PublishUnresolved(r.token, "transport-mark-corrupt")
    entries = (
        PublicationStagingEntry(r.subject, Staged(mark.corpus_id, mark.records)),
        PublicationExportEntry(r.subject, Exported(mark.corpus_id, mark.artifact)),
        PublicationRevealEntry(r.subject, Revealed(mark.corpus_id)),
    )
    if _export_damaged(r, mark):
        return _refused(r, (*entries, PublicationTransportEntry(r.subject, TransportIncomplete(mark.corpus_id, mark.marker, "export-damaged"))))
    if not _marker_agrees(r, mark):
        return PublishUnresolved(r.token, "transport-mark-corrupt")
    return _transport_and_bind(r, mark, entries)


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
    transport: Transport | None = None,
) -> PublishOutcome:
    """Resume from its request, or a remote transport mark (local §9, remote §4.2)."""
    _require_publishes(writer)
    reading = attempt_reading(writer, event_token, seam)
    if reading is None:
        raise ValidationRefused(f"no publish intent carries token {event_token}")
    if writer.authority.actor != reading.opened.intent.actor:
        raise ValidationRefused("a publish resumes only under its intent's actor")
    _require_transport(reading.opened.intent.destination, transport)
    op = _op_dir(Path(operations_root).resolve(), event_token)
    present = _binding_present(writer, reading.opened)
    if reading.reading == "indeterminate":
        return PublishUnresolved(event_token, "indeterminate")
    if reading.reading == "closed":
        if not present:
            assert reading.outcome is not None
            return PublishRefused(event_token, reading.outcome)
        _discard(op)
        return _published_from_disk(writer, reading.opened)
    if present:
        return PublishUnresolved(event_token, "binding-without-report")
    if _mark_nonregular(op):
        return PublishUnresolved(event_token, "transport-mark-corrupt")
    if (op / "transport.v1").is_file():
        assert transport is not None  # the seam rule above: a mark exists only for a remote intent
        return _resume_from_mark(_Remote(writer, resolver, reading.opened, op, clock, seam, port, transport))
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
    return _run(_Attempt(writer, resolver, reading.opened, request, snapshot, op, staging_profile, clock, seam, port, transport))


def _published_from_disk(writer: CorpusWriter, opened: OpenedPublication) -> Published:
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
