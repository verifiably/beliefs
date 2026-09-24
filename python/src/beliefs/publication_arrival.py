"""Marker-required arrival (publish-act-local design §10; layer design §6.3): a
published corpus is admitted only through its marker, checked before any write,
then through cut 8's arrival act."""

from __future__ import annotations

from pathlib import Path

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import PublicationArrivalRefused
from beliefs.publication import BINDING_KIND, MARKER_KIND, marker_consistent, publication_content_malformed
from beliefs.root import admit_arrival
from beliefs.world import ReplicaOf, load_manifest

__all__ = ["admit_publication"]


def admit_publication(world, root: Path, observers):
    """Refuse, before `admit_arrival` writes anything, a root with no marker, two
    markers, a malformed or inconsistent marker, a binding, or records other
    than the marker's selection; then admit it as a replica of itself."""
    root = Path(root).resolve()
    records = tuple(ReadView.opened_at(root).iter_stored())
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
    return admit_arrival(world, root, ReplicaOf(load_manifest(root).corpus_id), observers)
