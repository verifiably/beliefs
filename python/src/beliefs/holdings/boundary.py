"""The holdings recheck boundary."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import CreateOp

from beliefs import stored
from beliefs.errors import MalformedRecord, StoreIdMismatch
from beliefs.holdings.records import (
    Absent,
    Found,
    HoldingsObservation,
    StoreLocator,
    holdings_observation,
    require_canonical_digest,
)
from beliefs.holdings.seam import (
    AbsentStateView,
    FileStateView,
    NonRegularStateView,
    ReadNotAttemptedView,
    ReadUnestablishedView,
    StoreActSeam,
    StoreOutcomeView,
)
from beliefs.world.anchors import parse_store_genesis

HOLDINGS_INTENT_DOMAIN = "science.holdings-intent.v1"
ACT_KINDS = ("re-check", "write", "delete", "move-source", "move-destination")


def intent_payload(*, location: StoreLocator, act_kind: str, event_token: str, actor: str) -> bytes:
    if act_kind not in ACT_KINDS:
        raise MalformedRecord(f"holdings intent kind {act_kind!r} is not admitted")
    if not isinstance(event_token, str) or not event_token:
        raise MalformedRecord("a holdings intent event_token must be a non-empty string")
    if not isinstance(actor, str) or not actor:
        raise MalformedRecord("a holdings intent actor must be a non-empty string")
    return json.dumps(
        {"actor": actor, "domain": HOLDINGS_INTENT_DOMAIN, "event_token": event_token, "kind": act_kind,
         "location": {"relative_path": location.relative_path, "store_id": location.store_id, "type": "store"}},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


@dataclass(frozen=True)
class PublishedObservation:
    record: HoldingsObservation


@dataclass(frozen=True)
class InconclusiveAttempt:
    report: str
    reason: str
    detail: str


ActResult = PublishedObservation | InconclusiveAttempt


@dataclass(frozen=True)
class ActContext:
    observer_root: Path
    store_root: Path
    observer: str
    instrument: str
    actor: str
    seam: StoreActSeam


def _publish(ctx: ActContext, location: StoreLocator, outcome: Found | Absent, token: str, intent: str,
             standing: tuple[HoldingsObservation, ...]) -> PublishedObservation:
    record = holdings_observation(location=location, outcome=outcome, observer=ctx.observer, instrument=ctx.instrument,
                                  event_token=token, observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                  supersedes=standing)
    node = stored.holdings_observation_node(record)
    ctx.seam.publish_fulfilling(ctx.observer_root, (CreateOp(f"holdings-observation/{record.identity()}.md",
                                                             node_to_markdown(node).encode("utf-8")),), intent)
    return PublishedObservation(record)


def recheck(ctx: ActContext, location: StoreLocator, *, standing: tuple[HoldingsObservation, ...] = ()) -> ActResult:
    token = secrets.token_hex(16)
    intent = ctx.seam.append_intent(ctx.observer_root, intent_payload(location=location, act_kind="re-check",
                                                                        event_token=token, actor=ctx.actor))
    view = ctx.seam.read_path(ctx.store_root, location.relative_path)
    if isinstance(view, ReadNotAttemptedView):
        return InconclusiveAttempt("byte-locator-untested", view.reason, view.detail)
    if isinstance(view, ReadUnestablishedView):
        return InconclusiveAttempt("retrieval-failed", view.reason, view.detail)
    if isinstance(view.state, NonRegularStateView):
        return InconclusiveAttempt("retrieval-failed", "established-neither", view.state.kind)
    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
    if store_id != location.store_id:
        raise StoreIdMismatch(f"store root names {store_id}, not {location.store_id}")
    return _publish(ctx, location, Found(view.state.content_hash) if isinstance(view.state, FileStateView) else Absent(),
                    token, intent, standing)


def _final(outcome: StoreOutcomeView, path: str) -> FileStateView | AbsentStateView | NonRegularStateView:
    for final_path, state in outcome.final_states:
        if final_path == path:
            return state
    raise RuntimeError(f"store outcome lacks final state for {path!r}")


def _bind(ctx: ActContext, location: StoreLocator) -> None:
    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
    if store_id != location.store_id:
        raise StoreIdMismatch(f"store root names {store_id}, not {location.store_id}")


def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:
    token = secrets.token_hex(16)
    return token, ctx.seam.append_intent(
        ctx.observer_root, intent_payload(location=location, act_kind=kind, event_token=token, actor=ctx.actor)
    )


def write(ctx: ActContext, location: StoreLocator, content: bytes, *, expected: str | None = None,
          standing: tuple[HoldingsObservation, ...] = ()) -> PublishedObservation:
    if expected is not None:
        require_canonical_digest(expected, "a holdings observation's expected digest")
        if expected.split(":", 1)[0] != "sha256":
            raise MalformedRecord("a found observation's expected digest must use the found digest's algorithm")
    token, intent = _append(ctx, location, "write")
    _bind(ctx, location)
    state = _final(ctx.seam.store_write(ctx.store_root, location.relative_path, content), location.relative_path)
    if not isinstance(state, FileStateView):
        raise TypeError(f"store write did not establish a file at {location.relative_path!r}")
    record = holdings_observation(location=location, outcome=Found(state.content_hash), expected=expected,
                                  observer=ctx.observer, instrument=ctx.instrument, event_token=token,
                                  observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), supersedes=standing)
    node = stored.holdings_observation_node(record)
    ctx.seam.publish_fulfilling(ctx.observer_root, (CreateOp(f"holdings-observation/{record.identity()}.md",
                                                             node_to_markdown(node).encode("utf-8")),), intent)
    return PublishedObservation(record)


def delete(ctx: ActContext, location: StoreLocator, *, standing: tuple[HoldingsObservation, ...] = ()) -> PublishedObservation:
    token, intent = _append(ctx, location, "delete")
    _bind(ctx, location)
    state = _final(ctx.seam.store_delete(ctx.store_root, location.relative_path), location.relative_path)
    if not isinstance(state, AbsentStateView):
        raise TypeError(f"store delete did not establish absence at {location.relative_path!r}")
    return _publish(ctx, location, Absent(), token, intent, standing)


def move(ctx: ActContext, source: StoreLocator, destination: StoreLocator, *,
         standing_source: tuple[HoldingsObservation, ...] = (),
         standing_destination: tuple[HoldingsObservation, ...] = ()) -> tuple[PublishedObservation, PublishedObservation]:
    source_token, source_intent = _append(ctx, source, "move-source")
    destination_token, destination_intent = _append(ctx, destination, "move-destination")
    _bind(ctx, source)
    _bind(ctx, destination)
    outcome = ctx.seam.store_move(ctx.store_root, source.relative_path, destination.relative_path)
    source_state = _final(outcome, source.relative_path)
    destination_state = _final(outcome, destination.relative_path)
    if not isinstance(source_state, AbsentStateView) or not isinstance(destination_state, FileStateView):
        raise TypeError("store move did not establish absent source and file destination")
    return (
        _publish(ctx, source, Absent(), source_token, source_intent, standing_source),
        _publish(ctx, destination, Found(destination_state.content_hash), destination_token, destination_intent,
                 standing_destination),
    )
