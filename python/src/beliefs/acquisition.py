"""The acquisition-boundary validity predicate and the bearer invariant
(facet-contracts design §2 items 1 and 14, §5.2).

One function decides whether a dataset's empirical-observation facet stands:
present, payload valid, no producer, no lineage basis, and `retrieval`
resolving to an acquisition report when present. Actor binding is a write
rule and is not here. The write seams, `corpus_check` and `eligibility_refusal`
all call it, so no seam can read a weaker predicate than another.
"""

from __future__ import annotations

from typing import Protocol

from nodes.core.node import Node

from beliefs import stored
from beliefs.errors import FacetPayloadRefused
from beliefs.facets import validate_payload
from beliefs.profile import ProfileSpec

__all__ = ["ProducerView", "bearer_refusal", "validity_refusal"]


class ProducerView(Protocol):
    def holds(self, ref: str) -> bool: ...
    def get(self, ref: str) -> Node: ...
    def resolve(self, ref: str) -> str | None: ...
    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]: ...


def validity_refusal(view: ProducerView, node: Node, profile: ProfileSpec) -> str | None:
    """`None` when `node` carries a valid acquisition-boundary declaration."""
    if stored.EMPIRICAL_OBSERVATION_FACET not in node.facets:
        return "no-empirical-observation-facet"
    payload = node.facets[stored.EMPIRICAL_OBSERVATION_FACET]
    try:
        validate_payload(profile.facets[stored.EMPIRICAL_OBSERVATION_FACET], payload, where=node.id)
    except FacetPayloadRefused as refused:
        return f"facet-payload-malformed: {refused}"
    if stored.LINEAGE_BASIS_FACET in node.facets:
        return "facet-bearer-produced: the dataset carries a lineage basis"
    producers = view.producers(node.id, aliases=tuple(node.deprecated_ids))
    if producers:
        return f"facet-bearer-produced: produced by {', '.join(producers)}"
    retrieval = payload.get("retrieval")
    if retrieval is not None:
        if not view.holds(retrieval):
            return f"facet-retrieval-unresolved: {retrieval}"
        facet = view.get(retrieval).facets.get("act-report")
        if not isinstance(facet, dict) or facet.get("operation") != "acquisition":
            return f"facet-retrieval-unresolved: {retrieval} is not an acquisition report"
    return None


def bearer_refusal(view: ProducerView, node: Node) -> str | None:
    """The resulting-state invariant for one proposed write, either half, keyed
    on the `produces` edge whatever its carrier's kind. The **candidate is part
    of the resulting state**: a facet-bearing dataset whose own `produces`
    names itself (by id, alias, or a target that resolves to it) is refused
    before the view is consulted at all."""
    own_names = {node.id, *node.deprecated_ids}
    bears = node.kind == "dataset" and stored.EMPIRICAL_OBSERVATION_FACET in node.facets
    for relation in node.relations:
        if relation.predicate != stored.PRODUCES:
            continue
        if bears and (relation.target in own_names or view.resolve(relation.target) == node.id):
            return f"{node.id}: carries the empirical-observation facet and produces itself"
        target = view.resolve(relation.target)
        if target is not None and stored.EMPIRICAL_OBSERVATION_FACET in view.get(target).facets:
            return f"{node.id}: produces {target}, which carries the empirical-observation facet"
    if bears:
        if stored.LINEAGE_BASIS_FACET in node.facets:
            return f"{node.id}: carries the empirical-observation facet and a lineage basis"
        producers = view.producers(node.id, aliases=tuple(node.deprecated_ids))
        if producers:
            return f"{node.id}: carries the empirical-observation facet and is produced by {', '.join(producers)}"
    return None
