"""The acquisition operation (url-retrieval design §6).

One operation intent, then per resource a URL look and an optional managed
materialization, then one closing transaction carrying the dataset and the
act-report. The cooperative stop (decision 5) skips every resource after the
first that did not complete; a stop forbids the mint (decision 10).
"""

from __future__ import annotations

import secrets
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
from beliefs.errors import AcquisitionRefused, MalformedRecord, StoreWriteRefused
from beliefs.holdings.boundary import ActContext, InconclusiveLook, look, write
from beliefs.holdings.records import HoldingsObservation, StoreLocator, UrlLocator, require_canonical_digest
from beliefs.holdings.transport import RetrievalBounds, UrlSeam, refuse_scratch_root
from beliefs.report import (
    ActReport,
    ByteLocatorUntested,
    DeclarationPinEntry,
    Entry,
    LocatorEntry,
    ManagedMutationEntry,
    OperationIntent,
    PinnedDeclaration,
    PublishedObservation,
    RetrievalFailed,
)
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed
from beliefs.world.anchors import parse_store_genesis

__all__ = ["SKIPPED_AFTER_STOP", "AcquisitionOutcome", "AcquisitionRequest", "ResourceRequest", "Stop", "acquire"]

SKIPPED_AFTER_STOP = "skipped-after-stop"
LOCATOR_SCHEMES = ("accession", "url", "instrument")
"""The empirical-observation facet's declared schemes (CONTRACT.yaml); the profile validates again at the write."""
PROBE_DIGEST = "sha256:" + "0" * 64
PROBE_REPORT = "act-report:" + "0" * 64
"""Placeholders the pre-intent shape check builds the dataset with; the shape check resolves neither."""


@sealed
@final
@dataclass(frozen=True)
class ResourceRequest:
    name: str
    url: UrlLocator
    expected: str | None = None
    materialize: StoreLocator | None = None

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise MalformedRecord("a resource request names its resource")
        if type(self.url) is not UrlLocator:
            raise MalformedRecord("a resource request retrieves a UrlLocator")
        if self.expected is not None:
            require_canonical_digest(self.expected, "a resource request's expected digest")
            if self.expected.split(":", 1)[0] != "sha256":
                raise MalformedRecord("an expected digest must use the instrument's algorithm, sha256")
        if self.materialize is not None and type(self.materialize) is not StoreLocator:
            raise MalformedRecord("a materialization destination is a StoreLocator")


@sealed
@final
@dataclass(frozen=True)
class AcquisitionRequest:
    title: str
    locator: str
    resources: tuple[ResourceRequest, ...]
    bounds: RetrievalBounds
    domain_facets: Mapping[str, Mapping[str, object]] | None = None

    def __post_init__(self) -> None:
        if type(self.title) is not str or not self.title:
            raise MalformedRecord("an acquisition request titles its dataset")
        scheme, separator, rest = self.locator.partition(":") if type(self.locator) is str else ("", "", "")
        if separator != ":" or not rest or scheme not in LOCATOR_SCHEMES:
            raise MalformedRecord(f"an acquisition's locator is `<scheme>:<rest>` with scheme in {LOCATOR_SCHEMES}")
        if type(self.resources) is not tuple or not self.resources or any(type(r) is not ResourceRequest for r in self.resources):
            raise MalformedRecord("an acquisition request names at least one ResourceRequest")
        names = [resource.name for resource in self.resources]
        if len(names) != len(set(names)):
            raise MalformedRecord("resource names are unique within one request")
        if type(self.bounds) is not RetrievalBounds:
            raise MalformedRecord("an acquisition request carries RetrievalBounds")
        if self.domain_facets is not None and (
            not isinstance(self.domain_facets, Mapping)
            or any(
                type(key) is not str or "/" not in key or not isinstance(payload, Mapping) or any(type(k) is not str for k in payload)
                for key, payload in self.domain_facets.items()
            )
        ):
            raise MalformedRecord("domain_facets maps namespaced `<namespace>/<name>` keys to mappings with string keys")


@sealed
@final
@dataclass(frozen=True)
class Stop:
    resource: str
    phase: str
    reason: str


@sealed
@final
@dataclass(frozen=True)
class AcquisitionOutcome:
    report: ActReport
    report_ref: str
    dataset: Node | None
    entries: tuple[Entry, ...]
    stop: Stop | None


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def acquire(
    ctx: ActContext,
    writer: CorpusWriter,
    request: AcquisitionRequest,
    *,
    seam: UrlSeam,
    scratch: Path,
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> AcquisitionOutcome:
    """`hold` is the caller's outer lock for the close — the session route passes
    the one `ScopedWriter._act` takes first — entered before the root lock and
    never around a request (decision 15; the session's session-then-root order)."""
    heads: dict[str, tuple[HoldingsObservation, ...]] = {} if standing is None else dict(standing)
    if type(request) is not AcquisitionRequest:
        raise MalformedRecord("acquire takes an AcquisitionRequest")
    # 1. Checks, before any effect (spec §6 step 1).
    ctx.authority.require("holdings", ("holdings-observation",))
    ctx.authority.require("corpus-write", ("dataset", "act-report"))
    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():
        raise AcquisitionRefused("the writer's root is not the act context's observer root; an acquisition publishes in one root")
    if port is None and writer._operation_port is None:
        raise AcquisitionRefused("this corpus has no operation port; acquisition is a boundary operation")
    refuse_scratch_root(scratch, (ctx.observer_root, ctx.store_root))
    if any(resource.materialize is not None for resource in request.resources):
        store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
        for resource in request.resources:
            if resource.materialize is not None and resource.materialize.store_id != store_id:
                raise AcquisitionRefused(f"{resource.name}: its destination names store {resource.materialize.store_id}, not the bound {store_id}")
    writer._refuse_dataset_shape(  # the request-only metadata, before any effect
        stored.dataset_node(
            title=request.title,
            resources=[{"name": r.name, "digest": r.expected or PROBE_DIGEST} for r in request.resources],
            empirical_observation={"locator": request.locator, "attested_by": ctx.actor, "retrieval": PROBE_REPORT},
            domain_facets=request.domain_facets,
        )
    )
    # 2. Open.
    intent = OperationIntent("acquisition", secrets.token_hex(16), ctx.actor)
    opened_at = _now()
    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)
    # 3. Resources, in order, until the cooperative stop.
    entries: list[Entry] = []
    digests: dict[str, str] = {}
    published: set[str] = set()
    stop: Stop | None = None
    inputs = request.bounds.instrument_inputs()
    for resource in request.resources:
        subject = resource.url.canonical()
        if stop is not None:
            entries.append(LocatorEntry(subject, ByteLocatorUntested(SKIPPED_AFTER_STOP), inputs))
            continue
        result = look(
            ctx, resource.url, bounds=request.bounds, seam=seam, scratch=scratch,
            expected=resource.expected, standing=heads.get(subject) or (),
        )
        if isinstance(result, InconclusiveLook):
            outcome = ByteLocatorUntested(result.reason) if result.report == "byte-locator-untested" else RetrievalFailed(result.reason)
            entries.append(LocatorEntry(subject, outcome, inputs))
            stop = Stop(resource.name, "look", result.reason)
            continue
        entries.append(LocatorEntry(subject, PublishedObservation(result.ref), inputs))
        published.add(result.ref)
        digests[resource.name] = result.retrieved.digest
        try:
            if resource.materialize is not None:
                destination = resource.materialize
                try:
                    materialized = write(
                        ctx, destination, result.retrieved.path.read_bytes(), expected=result.retrieved.digest,
                        standing=heads.get(destination.canonical()) or (),
                    )
                except StoreWriteRefused as refused:
                    stop = Stop(resource.name, "materialize", str(refused))
                    continue
                ref = f"holdings-observation:{materialized.record.identity()}"
                entries.append(ManagedMutationEntry(destination.canonical(), PublishedObservation(ref)))
                published.add(ref)
        finally:
            result.retrieved.path.unlink(missing_ok=True)
    # 4. Close.
    expectations_hold = all(r.expected is None or digests.get(r.name) == r.expected for r in request.resources)
    mint = stop is None and expectations_hold
    address: str | None = None
    if mint:
        declaration = DatasetDeclaration(tuple(ResourceDeclaration(r.name, digests[r.name]) for r in request.resources))
        address = dataset_address(declaration)
        assert address is not None  # every resource found and pinned sha256
    closed_at = _now()
    dataset: Node | None = None
    outer = nullcontext() if hold is None else hold()
    with outer, writer._operation:  # session (the caller's hold), then root: `_act`'s order
        writer._reconstruct()  # the looks published through the holdings seam, past this writer's cached index
        for ref in sorted(published):
            if writer.read_view.resolve(ref) is None:
                raise AcquisitionRefused(f"{ref}: the report would reference an observation no act published")
        held = address is not None and writer.read_view.resolve(address) is not None
        report_entries = tuple(entries) + ((DeclarationPinEntry(address, PinnedDeclaration(address)),) if mint and address is not None and not held else ())
        report = boundary_values._mint_acquisition_report(
            intent, observer=ctx.observer, instrument=ctx.instrument, opened_at=opened_at, closed_at=closed_at,
            entries=report_entries,
        )
        report_node = stored.act_report_node(report)
        operations = []
        if mint and not held:
            assert address is not None
            dataset = stored.dataset_node(
                title=request.title,
                resources=[{"name": r.name, "digest": digests[r.name]} for r in request.resources],
                empirical_observation={"locator": request.locator, "attested_by": ctx.actor, "retrieval": report_node.id},
                domain_facets=request.domain_facets,
            )
            writer._refuse_acquired_dataset(dataset, report_node)
            operations.append(writer._create_op(dataset))
        operations.append(writer._create_op(report_node))
        writer._publish_operation_report(report, intent_digest, operations=tuple(operations), port=port)
    return AcquisitionOutcome(report, report_node.id, dataset, report_entries, stop)
