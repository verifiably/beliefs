"""Decode captured record bytes into evidence values the shapes match on."""

from __future__ import annotations

from typing import TypeAlias

from nodes.core.errors import NodesError
from nodes.core.frontmatter import node_from_markdown
from nodes.core.node import Node
from yaml import YAMLError

from science import runrecord, stored
from science.errors import (
    CanonicalTextRefused,
    IdentityError,
    MalformedRecord,
    RecordUndecodable,
)
from science.intents.shapes import (
    InertRecord,
    ObservationEvidence,
    ReportEvidence,
    RunEvidence,
)
from science.world.records import RECORD_NAMESPACES

__all__ = ["RecordEvidence", "decode_node", "decode_record", "record_layout_path"]


RecordEvidence: TypeAlias = RunEvidence | ReportEvidence | ObservationEvidence | InertRecord
"""What one captured record decodes to — the closed union `reduce_registration`
carries as its match (successor-admission design §4.4)."""


def record_layout_path(path: str) -> bool:
    return path.endswith(".md") and any(
        path.startswith(namespace + "/") for namespace in RECORD_NAMESPACES
    )


def decode_node(path: str, payload: bytes) -> Node:
    """The gate every captured record passes before any typed reader: the
    frontmatter parses, the semantic stamp is present and agrees, the id
    names this path, and the kind agrees with the id (spec §3.1;
    successor-admission design §4.4 step 1)."""
    try:
        node = node_from_markdown(payload.decode("utf-8"))
    except (UnicodeDecodeError, NodesError, YAMLError, ValueError) as caught:
        raise RecordUndecodable(f"{path}: {caught}") from caught
    try:
        if stored.semantic_hash_missing(node) or stored.semantic_hash_disagrees(node):
            raise RecordUndecodable(
                f"{path}: the semantic stamp does not agree with the stored fields"
            )
    except (IdentityError, MalformedRecord) as caught:
        raise RecordUndecodable(
            f"{path}: the semantic projection is not encodable: {caught}"
        ) from caught
    kind, _, slug = node.id.partition(":")
    if not slug or path != f"{kind}/{slug}.md":
        raise RecordUndecodable(
            f"{path}: the record id {node.id!r} does not name this path"
        )
    if node.kind != kind:
        raise RecordUndecodable(
            f"{path}: the record kind {node.kind!r} disagrees with its id"
        )
    return node


def decode_record(path: str, payload: bytes) -> RecordEvidence:
    node = decode_node(path, payload)
    if node.kind == "run":
        try:
            publication = runrecord.decode_run_record(node)
        except (MalformedRecord, CanonicalTextRefused) as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        if publication is None:
            return InertRecord()
        return RunEvidence(
            publication.shape,
            publication.spec_identity,
            publication.event_token,
        )
    if node.kind == "act-report":
        try:
            facet = stored.act_report_facet(node)
        except MalformedRecord as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        return ReportEvidence(str(facet["operation"]), str(facet["event_token"]))
    if node.kind == "holdings-observation":
        try:
            value = stored.holdings_observation_value(node)
        except MalformedRecord as caught:
            raise RecordUndecodable(f"{path}: {caught}") from caught
        if node.id != f"holdings-observation:{value.identity()}":
            raise RecordUndecodable(
                f"{path}: the observation id disagrees with its identity"
            )
        return ObservationEvidence(
            f"store:{value.location.store_id}:{value.location.relative_path}",
            value.event_token,
        )
    return InertRecord()
