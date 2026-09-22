"""The re-check operation (act-report-remainder design §4).

One operation intent, then per location the `recheck` act as built — its own
holdings intent, its own observation — then one closing transaction carrying
the act-report: one locator entry per location, in request order. No
cooperative stop: the close mints nothing that depends on any location
(decision 5). Nothing is held across the acts; the close takes the caller's
hold and then the root lock, the view rebuilt before any ref resolves
(decision 6). Every check the acts would make late is made before the
intent (decision 14).
"""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import final

from beliefs import boundary as boundary_values
from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import LoneSurrogate, MalformedRecord, RecheckRefused
from beliefs.holdings.boundary import ActContext, ActResult, InconclusiveAttempt, recheck
from beliefs.holdings.records import HoldingsObservation, StoreLocator
from beliefs.identity import v1
from beliefs.report import (
    ActReport,
    ByteLocatorUntested,
    LocatorEntry,
    OperationIntent,
    PublishedObservation,
    RetrievalFailed,
)
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed
from beliefs.world.anchors import parse_store_genesis

__all__ = ["RecheckOutcome", "recheck_locations"]


@sealed
@final
@dataclass(frozen=True)
class RecheckOutcome:
    report: ActReport
    report_ref: str
    entries: tuple[LocatorEntry, ...]
    results: tuple[ActResult, ...]


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_identity_text(value: object, name: str) -> None:
    """`holdings_observation`'s rule for observer and instrument, made before
    the intent rather than after the read (decision 14)."""
    if type(value) is not str or not value:
        raise RecheckRefused(f"a re-check's {name} must be a non-empty string")
    try:
        v1.encode(value)
    except LoneSurrogate as caught:
        raise RecheckRefused(f"a re-check's {name} must encode as identity text") from caught


def recheck_locations(
    ctx: ActContext,
    writer: CorpusWriter,
    locations: tuple[StoreLocator, ...],
    *,
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> RecheckOutcome:
    """`hold` is the caller's outer lock for the close — the session route
    passes the one `ScopedWriter._act` takes first — entered before the root
    lock and never around an act (decision 6)."""
    # 1. Checks, before any effect (§4 step 1).
    if type(locations) is not tuple or not locations or any(type(location) is not StoreLocator for location in locations):
        raise MalformedRecord("recheck_locations takes a non-empty tuple of StoreLocator values")
    canonicals = [location.canonical() for location in locations]
    if len(set(canonicals)) != len(canonicals):
        raise RecheckRefused("re-check locations are unique by canonical spelling")
    heads: dict[str, tuple[HoldingsObservation, ...]] = {} if standing is None else dict(standing)
    for key, predecessors in heads.items():
        if key not in canonicals:
            raise RecheckRefused(f"{key}: standing names a location this re-check does not request")
        if type(predecessors) is not tuple or any(
            type(predecessor) is not HoldingsObservation or predecessor.location.canonical() != key for predecessor in predecessors
        ):
            raise RecheckRefused(f"{key}: standing holds only HoldingsObservation values at that canonical location")
    ctx.authority.require("holdings", ("holdings-observation",))
    ctx.authority.require("corpus-write", ("act-report",))
    _require_identity_text(ctx.observer, "observer")
    _require_identity_text(ctx.instrument, "instrument")
    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():
        raise RecheckRefused("the writer's root is not the act context's observer root; a re-check publishes in one root")
    if port is None and writer._operation_port is None:
        raise RecheckRefused("this corpus has no operation port; re-check is a boundary operation")
    writer._require_bound_port(port)
    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
    for location in locations:
        if location.store_id != store_id:
            raise RecheckRefused(f"{location.canonical()}: names store {location.store_id}, not the bound {store_id}")
    # 2. Open.
    intent = OperationIntent("re-check", secrets.token_hex(16), ctx.actor)
    opened_at = _now()
    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)
    # 3. Acts, in request order, nothing held across them.
    entries: list[LocatorEntry] = []
    results: list[ActResult] = []
    published: list[str] = []
    for location, canonical in zip(locations, canonicals, strict=True):
        result = recheck(ctx, location, standing=heads.get(canonical, ()))
        results.append(result)
        if isinstance(result, InconclusiveAttempt):
            outcome = ByteLocatorUntested(result.reason) if result.report == "byte-locator-untested" else RetrievalFailed(result.reason)
            entries.append(LocatorEntry(canonical, outcome))
            continue
        ref = f"holdings-observation:{result.record.identity()}"
        published.append(ref)
        entries.append(LocatorEntry(canonical, PublishedObservation(ref)))
    # 4. Close.
    closed_at = _now()
    outer = nullcontext() if hold is None else hold()
    with outer, writer._operation:  # the caller's hold, then the root: `_act`'s order
        writer._reconstruct()  # the acts published through the holdings seam, past this writer's cached index
        for ref in published:
            if writer.read_view.resolve(ref) is None:
                raise RecheckRefused(f"{ref}: the report would reference an observation no act published")
        report = boundary_values._mint_recheck_report(
            intent, observer=ctx.observer, instrument=ctx.instrument, opened_at=opened_at, closed_at=closed_at,
            entries=tuple(entries),
        )
        report_ref = stored.act_report_node(report).id
        writer._publish_operation_report(report, intent_digest, port=port)
    return RecheckOutcome(report, report_ref, tuple(entries), tuple(results))
