"""Publication records (publication-records design §3–§4): the two addresses per
(view, destination), deterministic identities, the closed content rules, the
factories, and the self-contained marker check. Pure: no clock, no randomness,
no I/O — every byte is a function of the intent and the named arguments."""

from __future__ import annotations

import re

from nodes.core.errors import IdError
from nodes.core.ids import NodeId
from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.intents.publish import Destination, PublishIntent

__all__ = [
    "BINDING_KIND",
    "MARKER_KIND",
    "binding_address",
    "binding_record",
    "binding_uid",
    "marker_address",
    "marker_consistent",
    "marker_record",
    "marker_uid",
    "publication_content_malformed",
]

BINDING_KIND = "publication-binding"
MARKER_KIND = "publication"
_BINDING_ADDRESS_DOMAIN = "science.publication-binding-address.v1"
_MARKER_ADDRESS_DOMAIN = "science.publication-address.v1"
_BINDING_UID_DOMAIN = "science.publication-binding.v1"
_MARKER_UID_DOMAIN = "science.publication.v1"
_HEX32 = re.compile(r"[0-9a-f]{32}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_BINDING_FIELDS = frozenset(
    {"project", "local", "author", "at", "event_token", "view", "destination", "corpus_id", "marker", "artifact"}
)
_MARKER_FIELDS = frozenset(
    {"project", "local", "author", "at", "event_token", "published_from", "destination", "selection", "supersedes_markers"}
)


def _address(domain: str, view: CoordinationAddress, destination: Destination) -> CoordinationAddress:
    if type(view) is not CoordinationAddress or type(destination) is not Destination:
        raise MalformedRecord("an address derives from a CoordinationAddress and a Destination")
    unpinned = view.unpinned()
    local = v1.digest(domain, [unpinned.project, unpinned.local or "", destination.projection()])[:32]
    return CoordinationAddress(unpinned.project, local)


def binding_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress:
    return _address(_BINDING_ADDRESS_DOMAIN, view, destination)


def marker_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress:
    return _address(_MARKER_ADDRESS_DOMAIN, view, destination)


def binding_uid(event_token: str) -> str:
    return v1.digest(_BINDING_UID_DOMAIN, event_token)[:32]


def marker_uid(event_token: str) -> str:
    return v1.digest(_MARKER_UID_DOMAIN, event_token)[:32]


def _node(
    kind: str, address: CoordinationAddress, uid: str, facet: dict[str, object], predecessors: tuple[str, ...]
) -> Node:
    from beliefs.corpus import CorpusWriter

    content = {"name": kind, "body": "", **{name: value for name, value in facet.items() if name not in {"project", "local"}}}
    # `_coordination_node` reads only each predecessor's id, to build its supersedes edge
    predecessor_nodes = tuple(
        Node(id=f"{kind}:{address.project}.{address.local}.{tip}", uid=tip, kind=kind, title=kind, body="", facets={}, relations=[])
        for tip in predecessors
    )
    return CorpusWriter._coordination_node(kind, address, uid, content, predecessors=predecessor_nodes)


def binding_record(intent: PublishIntent, *, corpus_id: str, marker: str, artifact: str) -> Node:
    if type(intent) is not PublishIntent:
        raise MalformedRecord("a binding record derives from a PublishIntent")
    address = binding_address(intent.view, intent.destination)
    facet: dict[str, object] = {
        "author": intent.actor,
        "at": intent.at,
        "event_token": intent.event_token,
        "view": str(intent.view.unpinned()),
        "destination": intent.destination.projection(),
        "corpus_id": corpus_id,
        "marker": marker,
        "artifact": artifact,
    }
    node = _node(BINDING_KIND, address, binding_uid(intent.event_token), facet, intent.binding_tips)
    if publication_content_malformed(node):
        raise MalformedRecord("a binding's content is outside its closed rule")
    return node


def marker_record(intent: PublishIntent, *, world_id: str, epoch: str, selection: tuple[str, ...]) -> Node:
    if type(intent) is not PublishIntent:
        raise MalformedRecord("a marker record derives from a PublishIntent")
    if type(selection) is not tuple:  # before `list(...)`: None raises TypeError, a list or str would pass through
        raise MalformedRecord("a marker's selection is a tuple of world record ids")
    address = marker_address(intent.view, intent.destination)
    facet: dict[str, object] = {
        "author": intent.actor,
        "at": intent.at,
        "event_token": intent.event_token,
        "published_from": {"world_id": world_id, "epoch": epoch, "view": str(intent.view)},
        "destination": intent.destination.projection(),
        "selection": list(selection),
        "supersedes_markers": [list(pair) for pair in intent.marker_tips],
    }
    node = _node(MARKER_KIND, address, marker_uid(intent.event_token), facet, ())
    if publication_content_malformed(node):
        raise MalformedRecord("a marker's content is outside its closed rule")
    return node


def _world_record_id(value: object) -> bool:
    """A record id the publication can select: `nodes`' own id grammar
    (`NodeId.parse`, `kind:slug`) over a world kind — a publication selects
    world records, never coordination ones (spec §3, "record ids")."""
    if type(value) is not str:
        return False
    try:
        parsed = NodeId.parse(value)
    except IdError:
        return False
    return parsed.kind in stored.WORLD_KINDS


def _selection(value: object) -> bool:
    """Non-empty, strictly ascending, every member a world record id."""
    # members are validated before the order is compared: sorting mixed types raises TypeError
    return (
        type(value) is list
        and bool(value)
        and all(_world_record_id(member) for member in value)
        and value == sorted(set(value))
    )


def publication_content_malformed(node: Node) -> bool:
    """The closed per-kind rule beside `_validated_coordination_content` (spec §3)."""
    try:
        revision = coordination_revision(node)
    except MalformedRecord:
        return True
    facet = node.facets[stored.COORDINATION_FACET]
    if node.kind not in (BINDING_KIND, MARKER_KIND) or node.title != node.kind or node.body != "":
        return True
    if type(facet.get("event_token")) is not str or _HEX32.fullmatch(facet["event_token"]) is None:
        return True
    try:
        destination = Destination.from_projection(facet.get("destination"))
    except MalformedRecord:
        return True
    if node.kind == BINDING_KIND:
        if set(facet) != _BINDING_FIELDS or revision.address.local is None:
            return True
        try:
            view = CoordinationAddress.parse(facet["view"])
        except ValueError:
            return True
        return (
            view.revision is not None
            or any(type(facet[name]) is not str or _HEX32.fullmatch(facet[name]) is None for name in ("corpus_id", "marker"))
            or type(facet["artifact"]) is not str
            or _HEX64.fullmatch(facet["artifact"]) is None
            or binding_address(view, destination) != revision.address
            or node.uid != binding_uid(facet["event_token"])
        )
    if set(facet) != _MARKER_FIELDS or node.relations:
        return True
    source = facet["published_from"]
    if not isinstance(source, dict) or set(source) != {"world_id", "epoch", "view"}:
        return True
    try:
        view = CoordinationAddress.parse(source["view"])
    except ValueError:
        return True
    pairs = facet["supersedes_markers"]
    # every pair is validated before the list is sorted: ordering mixed types raises TypeError
    return (
        view.revision is None
        or type(source["world_id"]) is not str
        or _HEX32.fullmatch(source["world_id"]) is None
        or type(source["epoch"]) is not str
        or _HEX64.fullmatch(source["epoch"]) is None
        or not _selection(facet["selection"])
        or type(pairs) is not list
        or any(
            type(p) is not list or len(p) != 2 or any(type(m) is not str or _HEX32.fullmatch(m) is None for m in p)
            for p in pairs
        )
        or [list(p) for p in sorted({tuple(p) for p in pairs})] != pairs
        or node.uid != marker_uid(facet["event_token"])
        or marker_address(view, destination) != revision.address
    )


def marker_consistent(node: Node) -> bool:
    """Recompute the marker's uid, address and id from its own event token,
    view and destination (spec §4); `False` on any difference or any rule failure."""
    if node.kind != MARKER_KIND or publication_content_malformed(node):
        return False
    facet = node.facets[stored.COORDINATION_FACET]
    view = CoordinationAddress.parse(facet["published_from"]["view"])
    destination = Destination.from_projection(facet["destination"])
    address = marker_address(view, destination)
    uid = marker_uid(facet["event_token"])
    return (
        node.uid == uid
        and coordination_revision(node).address == address
        and node.id == f"{MARKER_KIND}:{address.project}.{address.local}.{uid}"
    )
