"""Marker-required arrival and recipient tip reading share one layout rule."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nodes.core.errors import CollisionError, PlacementError
from nodes.core.errors import ValidationError as NodesValidationError
from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.corpus import ReadView
from beliefs.errors import PublicationArrivalRefused, PublicationReadingRefused
from beliefs.intents.publish import Destination
from beliefs.publication import (
    BINDING_KIND,
    MARKER_KIND,
    _marker_release_malformed,
    marker_address,
    marker_consistent,
    publication_content_malformed,
)
from beliefs.root import admit_arrival
from beliefs.world import ReplicaOf, load_manifest

__all__ = ["CurrentPublication", "DivergentPublication", "admit_publication", "publication_tip", "require_publication_layout"]

_CAPTURE_DAMAGE = (OSError, NodesValidationError, PlacementError, CollisionError)


@dataclass(frozen=True)
class CurrentPublication:
    corpus_id: str
    marker: str


@dataclass(frozen=True)
class DivergentPublication:
    tips: tuple[tuple[str, str], ...]


def require_publication_layout(records: tuple[Node, ...]) -> None:
    """Require the publication layout before admitting or reading a held root."""
    markers = [node for node in records if node.kind == MARKER_KIND]
    if not markers:
        raise PublicationArrivalRefused("marker-absent")
    if len(markers) > 1:
        raise PublicationArrivalRefused("marker-duplicated")
    (marker,) = markers
    if publication_content_malformed(marker):
        raise PublicationArrivalRefused("marker-malformed")
    if not marker_consistent(marker):
        raise PublicationArrivalRefused("marker-inconsistent")
    if any(node.kind == BINDING_KIND for node in records):
        raise PublicationArrivalRefused("binding-present")
    held = sorted(node.id for node in records if node.kind != MARKER_KIND)
    selection = list(marker.facets[stored.COORDINATION_FACET]["selection"])
    if held != selection:
        first = min(set(held) ^ set(selection))
        raise PublicationArrivalRefused("selection-mismatch", refs=(first,))


def admit_publication(world, root: Path, observers):
    """Check publication layout before admitting a replica of the same root."""
    root = Path(root).resolve()
    records = tuple(ReadView.opened_at(root).iter_stored())
    require_publication_layout(records)
    manifest = load_manifest(root)
    (marker,) = (node for node in records if node.kind == MARKER_KIND)
    if _marker_release_malformed(marker, manifest.profile.domains.get("coordination")):
        raise PublicationArrivalRefused("marker-malformed")
    return admit_arrival(world, root, ReplicaOf(manifest.corpus_id), observers)


def _held_records(root: Path, corpus_id: str) -> tuple[Node, ...]:
    try:
        return tuple(ReadView.opened_at(root).iter_stored())
    except _CAPTURE_DAMAGE as caught:
        raise PublicationReadingRefused("capture-damaged", corpus_id) from caught


def publication_tip(
    roots: tuple[Path, ...], view: CoordinationAddress, destination: Destination
) -> CurrentPublication | DivergentPublication | None:
    """Read one publication tip, or sibling tips, across held roots."""
    if type(roots) is not tuple or any(not isinstance(root, Path) for root in roots):
        raise TypeError("publication_tip reads an exact tuple of held corpus roots")
    resolved = tuple(root.resolve() for root in roots)
    if len(set(resolved)) != len(resolved):
        raise ValueError("a held root is named twice")
    address = marker_address(view.unpinned(), destination)
    held: list[tuple[str, Node]] = []
    seen: set[str] = set()
    for root in resolved:
        manifest = load_manifest(root)
        corpus_id = manifest.corpus_id
        records = _held_records(root, corpus_id)
        if not any(node.kind == MARKER_KIND for node in records):
            continue
        try:
            require_publication_layout(records)
            (marker,) = (node for node in records if node.kind == MARKER_KIND)
            if _marker_release_malformed(marker, manifest.profile.domains.get("coordination")):
                raise PublicationArrivalRefused("marker-malformed")
        except PublicationArrivalRefused as refused:
            raise PublicationReadingRefused(refused.reason, corpus_id, refused.refs) from refused
        (marker,) = (node for node in records if node.kind == MARKER_KIND)
        if coordination_revision(marker).address != address:
            continue
        if marker.uid in seen:
            raise PublicationReadingRefused("marker-duplicated", None, (marker.uid,))
        seen.add(marker.uid)
        held.append((corpus_id, marker))
    if not held:
        return None
    present = {(corpus_id, marker.uid) for corpus_id, marker in held}
    superseded = {
        (str(pair[0]), str(pair[1]))
        for _, marker in held
        for pair in marker.facets[stored.COORDINATION_FACET]["supersedes_markers"]
    }
    tips = tuple(sorted(present - superseded))
    if not tips:
        raise PublicationReadingRefused("supersession-cycle", None, tuple(sorted(uid for _, uid in present)))
    if len(tips) == 1:
        return CurrentPublication(*tips[0])
    return DivergentPublication(tips)
