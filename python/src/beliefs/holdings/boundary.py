"""The holdings recheck boundary."""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from nodes.core.errors import ExecutionError
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import CreateOp

from beliefs import stored
from beliefs.errors import MalformedRecord, StoreIdMismatch, StoreWriteRefused
from beliefs.holdings.records import (
    Absent,
    Found,
    HoldingsObservation,
    Incomplete,
    Locator,
    StoreLocator,
    StoreTreeLocator,
    UrlLocator,
    holdings_observation,
    require_canonical_digest,
)
from beliefs.holdings.seam import (
    AbsentStateView,
    FileStateView,
    NonRegularStateView,
    PathObservedView,
    PathReadView,
    PathStateView,
    ReadNotAttemptedView,
    ReadUnestablishedView,
    StoreActSeam,
    StoreOutcomeView,
)
from beliefs.holdings.transport import (
    Failed,
    NotAttempted,
    RetrievalBounds,
    Retrieved,
    UrlSeam,
    refuse_scratch_root,
    retrieve,
)
from beliefs.permit import Authority, require_actor
from beliefs.profile import ProfileSpec
from beliefs.tree import Tree, object_path, parse_tree_file, tree_digest, tree_file_bytes
from beliefs.world.anchors import parse_store_genesis

HOLDINGS_INTENT_DOMAIN = "science.holdings-intent.v1"
ACT_KINDS = ("re-check", "write", "delete", "move-source", "move-destination", "tree-write")
TREE_KINDS = ("re-check", "tree-write")


def intent_payload(*, location: Locator, act_kind: str, event_token: str, actor: str) -> bytes:
    if act_kind not in ACT_KINDS:
        raise MalformedRecord(f"holdings intent kind {act_kind!r} is not admitted")
    if not isinstance(event_token, str) or not event_token:
        raise MalformedRecord("a holdings intent event_token must be a non-empty string")
    require_actor(actor)
    if isinstance(location, StoreTreeLocator):
        if act_kind not in TREE_KINDS:
            raise MalformedRecord(f"holdings intent kind {act_kind!r} does not pair with a store-tree location")
        location_facet = {"type": "store-tree", "store_id": location.store_id, "tree": location.tree}
    else:
        if act_kind == "tree-write":
            raise MalformedRecord("a tree-write intent pairs only with a store-tree location")
        location_facet = (
            {"type": "url", "url": location.url}
            if isinstance(location, UrlLocator)
            else {"relative_path": location.relative_path, "store_id": location.store_id, "type": "store"}
        )
    return json.dumps(
        {
            "actor": actor,
            "domain": HOLDINGS_INTENT_DOMAIN,
            "event_token": event_token,
            "kind": act_kind,
            "location": location_facet,
        },
        sort_keys=True,
        separators=(",", ":"),
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
class PublishedLook:
    record: HoldingsObservation
    ref: str
    retrieved: Retrieved


@dataclass(frozen=True)
class InconclusiveLook:
    report: str
    reason: str


def look(
    ctx: ActContext,
    location: UrlLocator,
    *,
    bounds: RetrievalBounds,
    seam: UrlSeam,
    scratch: Path,
    expected: str | None = None,
    standing: tuple[HoldingsObservation, ...] = (),
) -> PublishedLook | InconclusiveLook:
    """The URL pure look: a `re-check` intent for the
    registration, the request with nothing held, then a published `found` or an
    inconclusive attempt that mints nothing. The caller deletes `retrieved.path`
    on a `PublishedLook`; every other exit leaves no file."""
    ctx.authority.require("holdings", ("holdings-observation",))
    if type(location) is not UrlLocator:
        raise MalformedRecord("a URL look takes a UrlLocator")
    if expected is not None:
        require_canonical_digest(expected, "a holdings observation's expected digest")
        if expected.split(":", 1)[0] != "sha256":
            raise MalformedRecord("a found observation's expected digest must use the found digest's algorithm")
    refuse_scratch_root(scratch, (ctx.observer_root, ctx.store_root))
    token, intent = _append(ctx, location, "re-check")
    result = retrieve(location, bounds, seam, scratch)
    if isinstance(result, NotAttempted):
        return InconclusiveLook("byte-locator-untested", result.reason)
    if isinstance(result, Failed):
        return InconclusiveLook("retrieval-failed", result.reason)
    try:  # from `Retrieved` to the caller's ownership: construction refusals included
        record = holdings_observation(
            location=location,
            outcome=Found(result.digest),
            expected=expected,
            observer=ctx.observer,
            instrument=ctx.instrument,
            event_token=token,
            observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            supersedes=standing,
        )
        published = _publish_record(ctx, record, intent)
    except BaseException:
        result.path.unlink(missing_ok=True)  # ownership never reached the caller
        raise
    return PublishedLook(published.record, f"holdings-observation:{record.identity()}", result)


@dataclass(frozen=True)
class ActContext:
    observer_root: Path
    store_root: Path
    observer: str
    instrument: str
    authority: Authority
    seam: StoreActSeam
    profile: ProfileSpec

    def __post_init__(self) -> None:
        if not isinstance(self.profile, ProfileSpec):
            raise TypeError("an act context binds a compiled ProfileSpec")
        if type(self.authority) is not Authority:
            raise TypeError("an act context binds an Authority")

    @property
    def actor(self) -> str:
        """The bound actor — a read, never a field."""
        return self.authority.actor


def _publish_record(ctx: ActContext, record: HoldingsObservation, intent: str) -> PublishedObservation:
    """Publish under the corpus lock after checking the held profile's pins."""
    ctx.authority.require("holdings", ("holdings-observation",))
    from beliefs.corpus import require_pins_agree

    node = stored.holdings_observation_node(record)
    plan = (CreateOp(f"holdings-observation/{record.identity()}.md", node_to_markdown(node).encode("utf-8")),)
    with ctx.seam.corpus_lock(ctx.observer_root):
        require_pins_agree(ctx.observer_root, ctx.profile)
        ctx.seam.publish_fulfilling(ctx.observer_root, plan, intent)
    return PublishedObservation(record)


def _publish(
    ctx: ActContext,
    location: StoreLocator | StoreTreeLocator,
    outcome: Found | Absent,
    token: str,
    intent: str,
    standing: tuple[HoldingsObservation, ...],
    *,
    expected: str | None = None,
) -> PublishedObservation:
    ctx.authority.require("holdings", ("holdings-observation",))
    record = holdings_observation(
        location=location,
        outcome=outcome,
        expected=expected,
        observer=ctx.observer,
        instrument=ctx.instrument,
        event_token=token,
        observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        supersedes=standing,
    )
    return _publish_record(ctx, record, intent)


def recheck(ctx: ActContext, location: StoreLocator, *, standing: tuple[HoldingsObservation, ...] = ()) -> ActResult:
    ctx.authority.require("holdings", ("holdings-observation",))
    token, intent = _append(ctx, location, "re-check")
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
    return _publish(
        ctx,
        location,
        Found(view.state.content_hash) if isinstance(view.state, FileStateView) else Absent(),
        token,
        intent,
        standing,
    )


def _final(outcome: StoreOutcomeView, path: str) -> FileStateView | AbsentStateView | NonRegularStateView:
    for final_path, state in outcome.final_states:
        if final_path == path:
            return state
    raise RuntimeError(f"store outcome lacks final state for {path!r}")


def _bind(ctx: ActContext, location: StoreLocator | StoreTreeLocator) -> None:
    store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
    if store_id != location.store_id:
        raise StoreIdMismatch(f"store root names {store_id}, not {location.store_id}")


def _append(ctx: ActContext, location: Locator, kind: str) -> tuple[str, str]:
    ctx.authority.require("holdings", ("holdings-observation",))
    token = secrets.token_hex(16)
    from beliefs.corpus import require_pins_agree

    with ctx.seam.corpus_lock(ctx.observer_root):
        require_pins_agree(ctx.observer_root, ctx.profile)
        intent = ctx.seam.append_intent(
            ctx.observer_root, intent_payload(location=location, act_kind=kind, event_token=token, actor=ctx.actor)
        )
    return token, intent


def write(
    ctx: ActContext,
    location: StoreLocator,
    content: bytes,
    *,
    expected: str | None = None,
    standing: tuple[HoldingsObservation, ...] = (),
) -> PublishedObservation:
    ctx.authority.require("holdings", ("holdings-observation",))
    if expected is not None:
        require_canonical_digest(expected, "a holdings observation's expected digest")
        if expected.split(":", 1)[0] != "sha256":
            raise MalformedRecord("a found observation's expected digest must use the found digest's algorithm")
    token, intent = _append(ctx, location, "write")
    _bind(ctx, location)
    try:
        outcome = ctx.seam.store_write(ctx.store_root, location.relative_path, content, intent)
    except ExecutionError as caught:
        if ctx.seam.store_refusal(caught):
            raise StoreWriteRefused(location.canonical(), str(caught)) from caught
        raise
    state = _final(outcome, location.relative_path)
    if not isinstance(state, FileStateView):
        raise TypeError(f"store write did not establish a file at {location.relative_path!r}")
    record = holdings_observation(
        location=location,
        outcome=Found(state.content_hash),
        expected=expected,
        observer=ctx.observer,
        instrument=ctx.instrument,
        event_token=token,
        observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        supersedes=standing,
    )
    return _publish_record(ctx, record, intent)


def delete(
    ctx: ActContext, location: StoreLocator, *, standing: tuple[HoldingsObservation, ...] = ()
) -> PublishedObservation:
    ctx.authority.require("holdings", ("holdings-observation",))
    token, intent = _append(ctx, location, "delete")
    _bind(ctx, location)
    state = _final(ctx.seam.store_delete(ctx.store_root, location.relative_path, intent), location.relative_path)
    if not isinstance(state, AbsentStateView):
        raise TypeError(f"store delete did not establish absence at {location.relative_path!r}")
    return _publish(ctx, location, Absent(), token, intent, standing)


def move(
    ctx: ActContext,
    source: StoreLocator,
    destination: StoreLocator,
    *,
    standing_source: tuple[HoldingsObservation, ...] = (),
    standing_destination: tuple[HoldingsObservation, ...] = (),
) -> tuple[PublishedObservation, PublishedObservation]:
    ctx.authority.require("holdings", ("holdings-observation",))
    source_token, source_intent = _append(ctx, source, "move-source")
    destination_token, destination_intent = _append(ctx, destination, "move-destination")
    _bind(ctx, source)
    _bind(ctx, destination)
    outcome = ctx.seam.store_move(ctx.store_root, source.relative_path, destination.relative_path, source_intent)
    source_state = _final(outcome, source.relative_path)
    destination_state = _final(outcome, destination.relative_path)
    if not isinstance(source_state, AbsentStateView) or not isinstance(destination_state, FileStateView):
        raise TypeError("store move did not establish absent source and file destination")
    return (
        _publish(ctx, source, Absent(), source_token, source_intent, standing_source),
        _publish(
            ctx,
            destination,
            Found(destination_state.content_hash),
            destination_token,
            destination_intent,
            standing_destination,
        ),
    )


def _require_object(location: StoreTreeLocator, path: str, digest: str, size: int, state: object) -> None:
    """The object at `path` is a regular file of exactly this digest and size, or the act refuses."""
    if not isinstance(state, FileStateView) or state.content_hash != digest or state.byte_len != size:
        raise StoreWriteRefused(location.canonical(), f"{path} does not hold the declared object")


def _place_object(
    ctx: ActContext,
    location: StoreTreeLocator,
    digest: str,
    size: int,
    read_content: Callable[[], bytes],
    intent: str,
) -> None:
    """Make `objects/sha256/..` hold `digest`: reuse a matching object, create an absent one.

    `read_content` is called only when the object is absent, so a reused object
    never loads its bytes. A routine refusal from the create proves nothing (a
    concurrent create or a directory at the path refuses alike), so the object is
    read again and counts only when it matches."""
    ctx.authority.require("holdings", ("holdings-observation",))
    path = object_path(digest)
    view = ctx.seam.read_path(ctx.store_root, path)
    if not isinstance(view, PathObservedView):
        raise StoreWriteRefused(location.canonical(), f"{path} could not be read: {view.detail}")
    if not isinstance(view.state, AbsentStateView):
        _require_object(location, path, digest, size, view.state)
        return
    content = read_content()
    if f"sha256:{sha256(content).hexdigest()}" != digest or len(content) != size:
        raise MalformedRecord(f"the bytes for {path} do not match their declared digest and size")
    try:
        outcome = ctx.seam.store_create(ctx.store_root, path, content, intent)
    except ExecutionError as caught:
        if not ctx.seam.store_refusal(caught):
            raise
        again = ctx.seam.read_path(ctx.store_root, path)
        if not isinstance(again, PathObservedView):
            raise StoreWriteRefused(location.canonical(), str(caught)) from caught
        try:
            _require_object(location, path, digest, size, again.state)
        except StoreWriteRefused as refused:
            raise StoreWriteRefused(location.canonical(), str(caught)) from refused
        return
    _require_object(location, path, digest, size, _final(outcome, path))


def tree_write(
    ctx: ActContext,
    location: StoreTreeLocator,
    tree: Tree,
    members: Mapping[str, Path],
    *,
    standing: tuple[HoldingsObservation, ...] = (),
) -> PublishedObservation:
    """Write a tree into the store: every member object, then the tree file, then one `found`.

    Holds one member's bytes in memory at a time. A failure part-way leaves whole
    objects (each is created whole or not at all) and an unmatched intent."""
    ctx.authority.require("holdings", ("holdings-observation",))
    if location.digest() != tree_digest(tree):
        raise MalformedRecord("the store-tree location does not name this tree")
    if set(members) != {member.path for member in tree.members}:
        raise MalformedRecord("the member sources must be exactly the tree's paths")
    token, intent = _append(ctx, location, "tree-write")
    _bind(ctx, location)
    for member in tree.members:
        source = members[member.path]
        _place_object(ctx, location, member.digest, member.size, source.read_bytes, intent)
    file_bytes = tree_file_bytes(tree)
    _place_object(ctx, location, f"sha256:{location.tree}", len(file_bytes), lambda: file_bytes, intent)
    return _publish(ctx, location, Found(location.digest()), token, intent, standing, expected=location.digest())


def recheck_tree(
    ctx: ActContext, location: StoreTreeLocator, *, standing: tuple[HoldingsObservation, ...] = ()
) -> ActResult:
    """Observe whether the store still holds the tree: its tree file and every member object."""
    ctx.authority.require("holdings", ("holdings-observation",))
    token, intent = _append(ctx, location, "re-check")
    file_path = object_path(location.digest())
    view = ctx.seam.read_path(ctx.store_root, file_path)
    inconclusive = _inconclusive(view)
    if inconclusive is not None:
        return inconclusive
    assert isinstance(view, PathObservedView)
    _bind(ctx, location)
    if isinstance(view.state, AbsentStateView):
        return _publish(ctx, location, Absent(Incomplete(1, 0)), token, intent, standing)
    tree = _held_tree(ctx, location, view.state, file_path)
    if tree is None:
        return _publish(ctx, location, Absent(Incomplete(0, 1)), token, intent, standing)
    missing = mismatched = 0
    for member in tree.members:
        member_view = ctx.seam.read_path(ctx.store_root, object_path(member.digest))
        inconclusive = _inconclusive(member_view)
        if inconclusive is not None:
            return inconclusive
        assert isinstance(member_view, PathObservedView)
        state = member_view.state
        if isinstance(state, AbsentStateView):
            missing += 1
        elif (
            not isinstance(state, FileStateView) or state.content_hash != member.digest or state.byte_len != member.size
        ):
            mismatched += 1
    outcome = Found(location.digest()) if missing + mismatched == 0 else Absent(Incomplete(missing, mismatched))
    return _publish(ctx, location, outcome, token, intent, standing)


def _inconclusive(view: PathReadView) -> InconclusiveAttempt | None:
    if isinstance(view, ReadNotAttemptedView):
        return InconclusiveAttempt("byte-locator-untested", view.reason, view.detail)
    if isinstance(view, ReadUnestablishedView):
        return InconclusiveAttempt("retrieval-failed", view.reason, view.detail)
    return None


def _held_tree(ctx: ActContext, location: StoreTreeLocator, state: PathStateView, file_path: str) -> Tree | None:
    """The tree the store's tree file declares, or `None` when it holds other bytes or does not parse."""
    if not isinstance(state, FileStateView) or state.content_hash != f"sha256:{location.tree}":
        return None
    data = (ctx.store_root / file_path).read_bytes()
    if sha256(data).hexdigest() != location.tree:
        return None
    try:
        return parse_tree_file(data)
    except MalformedRecord:
        return None
