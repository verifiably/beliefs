"""Sealing an acquisition set.

A program fetches (or imports) a set of files into a work area and writes an
acquisition log; the seal verifies both and holds the set as one tree dataset.
One operation intent of kind `acquisition`, then a re-check of each location
the caller names unsettled, then the log (and, for an import, each source
journal) as ordinary holdings writes, then the `tree-write` act, then one
closing transaction carrying the dataset (unless its address is already held)
and the act report. Every check runs before the intent, and each member file
is hashed one at a time, in chunks, so no member is ever wholly in memory.
"""

from __future__ import annotations

import hashlib
import secrets
import stat
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import final

from nodes.core.node import Node

from beliefs import boundary as boundary_values
from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import AcquisitionRefused, MalformedRecord, WriteRefused
from beliefs.holdings.acquire import LOCATOR_SCHEMES, PROBE_REPORT
from beliefs.holdings.acquisition_log import log_summary, log_tree, parse_acquisition_log
from beliefs.holdings.boundary import ActContext, InconclusiveAttempt, recheck, recheck_tree, tree_write, write
from beliefs.holdings.records import HoldingsObservation, StoreLocator, StoreTreeLocator
from beliefs.holdings.transport import refuse_scratch_root
from beliefs.report import (
    AcquisitionSetEntry,
    ActReport,
    DeclarationPinEntry,
    Entry,
    ManagedMutationEntry,
    OperationIntent,
    PinnedDeclaration,
    PublishedObservation,
    SetSummary,
)
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed
from beliefs.tree import Tree, tree_digest
from beliefs.world.anchors import parse_store_genesis

__all__ = ["LOG_NAME", "SealOutcome", "SealRequest", "seal_acquisition"]

LOG_NAME = "acquisition-log.jsonl"
"""The log's name beside the set's source journals: each is stored at `<tree hex>/<set>/<name>`, where `<set>`
is the log header's set token, so every set that yields one tree keeps its own log."""
_ORIGINS = ("fetched", "imported")
_CHUNK = 1 << 20


@sealed
@final
@dataclass(frozen=True)
class SealRequest:
    """A work area to seal: `members` maps each tree path to its file, `log` is the
    acquisition log, and `source_journals` names an import's original journals by
    the names its log header gives them."""

    title: str
    locator: str
    tree_name: str
    members: Mapping[str, Path]
    log: Path
    origin: str
    fetched_by: str
    source_journals: tuple[tuple[str, Path], ...] = ()
    domain_facets: Mapping[str, Mapping[str, object]] | None = None

    def __post_init__(self) -> None:
        if type(self.title) is not str or not self.title:
            raise MalformedRecord("a seal request titles its dataset")
        scheme, separator, rest = self.locator.partition(":") if type(self.locator) is str else ("", "", "")
        if separator != ":" or not rest or scheme not in LOCATOR_SCHEMES:
            raise MalformedRecord(f"a seal's locator is `<scheme>:<rest>` with scheme in {LOCATOR_SCHEMES}")
        if type(self.tree_name) is not str or not self.tree_name:
            raise MalformedRecord("a seal request names its tree resource")
        if not isinstance(self.members, Mapping) or any(
            type(path) is not str or not isinstance(source, Path) for path, source in self.members.items()
        ):
            raise MalformedRecord("a seal request maps each tree path to a file Path")
        if not isinstance(self.log, Path):
            raise MalformedRecord("a seal request's log is a file Path")
        if self.origin not in _ORIGINS:
            raise MalformedRecord(f"a seal request's origin {self.origin!r} is outside {_ORIGINS}")
        if type(self.fetched_by) is not str or not self.fetched_by:
            raise MalformedRecord("a seal request names who fetched the bytes")
        if type(self.source_journals) is not tuple or any(
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or not row[0]
            or not isinstance(row[1], Path)
            for row in self.source_journals
        ):
            raise MalformedRecord("a seal request's source journals are (name, Path) pairs")
        names = [name for name, _ in self.source_journals]
        if len(names) != len(set(names)) or LOG_NAME in names:
            raise MalformedRecord(f"source journal names are unique and never {LOG_NAME!r}")
        if self.domain_facets is not None and (
            not isinstance(self.domain_facets, Mapping)
            or any(
                type(key) is not str
                or "/" not in key
                or not isinstance(payload, Mapping)
                or any(type(k) is not str for k in payload)
                for key, payload in self.domain_facets.items()
            )
        ):
            raise MalformedRecord(
                "domain_facets maps namespaced `<namespace>/<name>` keys to mappings with string keys"
            )


@sealed
@final
@dataclass(frozen=True)
class SealOutcome:
    report: ActReport
    report_ref: str
    dataset: Node | None
    """`None` when the dataset's address was already held: the seal never mints it twice."""
    address: str
    entries: tuple[Entry, ...]


@dataclass(frozen=True)
class _Plan:
    """Everything the checks established, before the intent."""

    tree: Tree
    location: StoreTreeLocator
    resources: tuple[tuple[StoreLocator, bytes, str], ...]
    """The log, then each source journal: its location, bytes and `sha256:` digest."""
    summary: SetSummary
    address: str
    heads: dict[str, tuple[HoldingsObservation, ...]]


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _digest(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _regular(path: Path) -> None:
    if not stat.S_ISREG(path.stat().st_mode):
        raise AcquisitionRefused(f"{path}: not a regular file")


def _read(path: Path) -> bytes:
    try:
        _regular(path)
        return path.read_bytes()
    except OSError as caught:
        raise AcquisitionRefused(f"{path}: could not be read: {caught}") from caught


def _hashed(path: Path) -> tuple[str, int]:
    """One file's `sha256:` digest and length, read in chunks."""
    digest = hashlib.sha256()
    size = 0
    try:
        _regular(path)
        with path.open("rb") as handle:
            while chunk := handle.read(_CHUNK):
                digest.update(chunk)
                size += len(chunk)
    except OSError as caught:
        raise AcquisitionRefused(f"{path}: could not be read: {caught}") from caught
    return f"sha256:{digest.hexdigest()}", size


def _heads(
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None,
    locations: tuple[StoreLocator | StoreTreeLocator, ...],
) -> dict[str, tuple[HoldingsObservation, ...]]:
    """The seal's head map, one entry per location it writes, seeded from `standing`;
    `standing` entries at other locations are not the seal's and are left unread."""
    supplied: Mapping[str, tuple[HoldingsObservation, ...]] = {} if standing is None else standing
    if not isinstance(supplied, Mapping):
        raise AcquisitionRefused("standing maps canonical locations to head observations")
    heads: dict[str, tuple[HoldingsObservation, ...]] = {}
    for location in locations:
        canonical = location.canonical()
        predecessors = supplied.get(canonical, ())
        if type(predecessors) is not tuple or any(
            type(predecessor) is not HoldingsObservation or predecessor.location.canonical() != canonical
            for predecessor in predecessors
        ):
            raise AcquisitionRefused(f"{canonical}: standing holds only HoldingsObservation values at that location")
        heads[canonical] = predecessors
    return heads


def _plan(
    ctx: ActContext,
    writer: CorpusWriter,
    request: SealRequest,
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None,
    unsettled: frozenset[str],
    port: OperationPort | None,
) -> _Plan:
    """Step 1 after the permits: every check, before any effect."""
    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():
        raise AcquisitionRefused(
            "the writer's root is not the act context's observer root; a seal publishes in one root"
        )
    if port is None and writer._operation_port is None:
        raise AcquisitionRefused("this corpus has no operation port; sealing is a boundary operation")
    if type(unsettled) is not frozenset or any(type(key) is not str for key in unsettled):
        raise AcquisitionRefused("unsettled is a frozenset of canonical locations")
    sources = (request.log, *request.members.values(), *(path for _, path in request.source_journals))
    for source in sources:
        try:
            refuse_scratch_root(source, (ctx.observer_root, ctx.store_root))
        except MalformedRecord as caught:
            raise AcquisitionRefused(f"the work area must lie outside the corpus and store roots: {caught}") from caught
    data = _read(request.log)
    try:
        log = parse_acquisition_log(data)
        tree = log_tree(log)
        summary = log_summary(log)
    except MalformedRecord as caught:
        raise AcquisitionRefused(f"{request.log}: {caught}") from caught
    if summary.log != _digest(data):
        raise AcquisitionRefused(f"{request.log}: the log is not its own canonical rendering")
    header = log.header
    if (header.origin, header.fetched_by) != (request.origin, request.fetched_by):
        raise AcquisitionRefused(
            f"the log header names origin {header.origin!r} and fetched_by {header.fetched_by!r}, "
            f"not the request's {request.origin!r} and {request.fetched_by!r}"
        )
    if [name for name, _ in header.source_journals] != [name for name, _ in request.source_journals]:
        raise AcquisitionRefused("the request's source journals are not the ones the log header names, in its order")
    if set(request.members) != {member.path for member in tree.members}:
        raise AcquisitionRefused("the member files are not exactly the paths of the log's fetched lines")
    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
    location = StoreTreeLocator(store_id, tree_digest(tree).split(":", 1)[1])
    try:
        set_directory = f"{location.tree}/{header.set}"  # per set: one tree may hold several sets' logs
        log_location = StoreLocator(store_id, f"{set_directory}/{LOG_NAME}")
        journal_locations = tuple(
            StoreLocator(store_id, f"{set_directory}/{name}") for name, _ in request.source_journals
        )
    except MalformedRecord as caught:
        raise AcquisitionRefused(f"a source journal's name is not a store path: {caught}") from caught
    heads = _heads(standing, (log_location, *journal_locations, location))
    address = dataset_address(DatasetDeclaration((ResourceDeclaration(request.tree_name, location.digest()),)))
    assert address is not None  # one resource, pinned by a `sha256-tree` digest
    try:
        writer._refuse_dataset_shape(  # the request-only metadata, before any effect
            stored.dataset_node(
                title=request.title,
                resources=[{"name": request.tree_name, "digest": location.digest()}],
                empirical_observation={"locator": request.locator, "attested_by": ctx.actor, "retrieval": PROBE_REPORT},
                domain_facets=request.domain_facets,
            )
        )
    except (WriteRefused, MalformedRecord) as caught:
        raise AcquisitionRefused(f"the dataset would be refused: {caught}") from caught
    resources = [(log_location, data, _digest(data))]
    for (name, recorded), (_, path), journal_location in zip(
        header.source_journals, request.source_journals, journal_locations, strict=True
    ):
        content = _read(path)
        if _digest(content) != recorded:
            raise AcquisitionRefused(f"{name}: the journal's bytes are not the digest the log header names")
        resources.append((journal_location, content, recorded))
    for member in tree.members:
        if _hashed(request.members[member.path]) != (member.digest, member.size):
            raise AcquisitionRefused(f"{member.path}: the work area's file is not the log's digest and size")
    return _Plan(tree, location, tuple(resources), summary, address, heads)


def _ref(record: HoldingsObservation) -> str:
    return f"holdings-observation:{record.identity()}"


def seal_acquisition(
    ctx: ActContext,
    writer: CorpusWriter,
    request: SealRequest,
    *,
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    unsettled: frozenset[str] = frozenset(),
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> SealOutcome:
    """Seal `request`'s work area as one tree dataset.

    Caller precondition: `standing` and `unsettled` come from one holdings
    reduction over the observer root, keyed by canonical location. `standing`
    gives the current heads at each location the seal writes (the log, each
    source journal and the store-tree location); `unsettled` gives the locations
    that reduction blocks as unsettled, and the seal re-checks those it writes
    before writing them. The seal does not establish that either is complete or
    current: a head left out stays unsuperseded beside the seal's observation, and
    an unsettled location left out stays blocked after the seal.

    Every check refuses with `AcquisitionRefused` (the permits with
    `PermitExceeded`) and writes nothing. An inconclusive repair re-check refuses
    after the intent, writes nothing more and leaves the intent unfinished.
    `hold` is the caller's outer lock for the close, entered before the root lock,
    as `acquire` takes it."""
    if type(request) is not SealRequest:
        raise MalformedRecord("seal_acquisition takes a SealRequest")
    # 1. Checks, before any effect.
    ctx.authority.require("holdings", ("holdings-observation",))
    ctx.authority.require("corpus-write", ("dataset", "act-report"))
    plan = _plan(ctx, writer, request, standing, unsettled, port)
    heads = dict(plan.heads)
    # 2. Open.
    intent = OperationIntent("acquisition", secrets.token_hex(16), ctx.actor)
    opened_at = _now()
    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)
    # 3. Settle: re-check each location the seal writes that the caller's reduction names unsettled.
    for location in (*(resource[0] for resource in plan.resources), plan.location):
        canonical = location.canonical()
        if canonical not in unsettled:
            continue
        if isinstance(location, StoreTreeLocator):
            result = recheck_tree(ctx, location, standing=heads[canonical])
        else:
            result = recheck(ctx, location, standing=heads[canonical])
        if isinstance(result, InconclusiveAttempt):
            raise AcquisitionRefused(
                f"{canonical}: the repair re-check was inconclusive ({result.reason}: {result.detail}); "
                "the location stays unsettled and the seal writes nothing more"
            )
        heads[canonical] = (result.record,)
    # 4. The log, then each source journal.
    mutations: list[Entry] = []
    published: list[str] = []
    for location, content, expected in plan.resources:
        written = write(ctx, location, content, expected=expected, standing=heads[location.canonical()])
        mutations.append(ManagedMutationEntry(location.canonical(), PublishedObservation(_ref(written.record))))
        published.append(_ref(written.record))
    # 5. The tree.
    tree_location = plan.location.canonical()
    held_tree = tree_write(ctx, plan.location, plan.tree, request.members, standing=heads[tree_location])
    published.append(_ref(held_tree.record))
    # 6. Close.
    closed_at = _now()
    dataset: Node | None = None
    outer = nullcontext() if hold is None else hold()
    with outer, writer._operation:  # session (the caller's hold), then root: `acquire`'s order
        writer._reconstruct()  # the acts published through the holdings seam, past this writer's cached index
        for ref in published:
            if writer.read_view.resolve(ref) is None:
                raise AcquisitionRefused(f"{ref}: the report would reference an observation no act published")
        held = writer.read_view.resolve(plan.address) is not None
        entries = (
            *mutations,
            ManagedMutationEntry(tree_location, PublishedObservation(_ref(held_tree.record))),
            AcquisitionSetEntry(tree_location, plan.summary),
            *(() if held else (DeclarationPinEntry(plan.address, PinnedDeclaration(plan.address)),)),
        )
        report = boundary_values._mint_acquisition_report(
            intent,
            observer=ctx.observer,
            instrument=ctx.instrument,
            opened_at=opened_at,
            closed_at=closed_at,
            entries=entries,
        )
        report_node = stored.act_report_node(report)
        operations = []
        if not held:
            dataset = stored.dataset_node(
                title=request.title,
                resources=[{"name": request.tree_name, "digest": plan.location.digest()}],
                empirical_observation={
                    "locator": request.locator,
                    "attested_by": ctx.actor,
                    "retrieval": report_node.id,
                },
                domain_facets=request.domain_facets,
            )
            writer._refuse_acquired_dataset(dataset, report_node)
            operations.append(writer._create_op(dataset))
        operations.append(writer._create_op(report_node))
        writer._publish_operation_report(report, intent_digest, operations=tuple(operations), port=port)
    return SealOutcome(report, report_node.id, dataset, plan.address, entries)
