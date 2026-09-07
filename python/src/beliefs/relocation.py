"""The two-root world-changing operations: `move` and `consolidate`.

This module **composes** two `CorpusWriter`s and subclasses neither: an
operation over two corpus roots cannot honestly be a method on an object bound
to one. `atoms` §12.2 keys an engine root on a corpus root, so two corpora are
two chains and two operation ports — these operations are never one
transaction, and the design's §3.5 enumerates every durable prefix instead of
pretending otherwise.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from nodes.core.node import Node
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.corpus import EXCLUDED_MUTATION_KINDS as EXCLUDED_KINDS
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    ActorMismatch,
    AddressDisagreement,
    ContractPinDisagreement,
    DuplicateLocation,
    RelocationKindExcluded,
    RelocationRefused,
    RelocationTargetMissing,
    SameRootRefused,
)
from beliefs.report import ActReport, Consolidated, Moved, OperationIntent


@contextmanager
def _both_locks(first: CorpusWriter, second: CorpusWriter) -> Iterator[None]:
    """Both roots' operation locks, each distinct root once, in sorted order."""
    roots = {str(Path(writer.root).resolve()): writer for writer in (first, second)}
    with ExitStack() as stack:
        for key in sorted(roots):
            stack.enter_context(roots[key]._operation)
        yield


def _refuse_same_root(first: CorpusWriter, second: CorpusWriter) -> None:
    if Path(first.root).resolve() == Path(second.root).resolve():
        raise SameRootRefused(f"both positions resolve to corpus root {first.root}")


def _refuse_actor_disagreement(first: CorpusWriter, second: CorpusWriter) -> None:
    if first.authority.actor != second.authority.actor:
        raise ActorMismatch(
            f"the two writers bind different actors: {first.authority.actor!r} and {second.authority.actor!r}"
        )


def _refuse_excluded_kind(node: Node) -> None:
    if node.kind in EXCLUDED_KINDS:
        raise RelocationKindExcluded(f"{node.id}: kind {node.kind!r} is excluded from relocation")


def _refuse_contract_disagreement(
    node: Node, source: CorpusWriter, destination: CorpusWriter
) -> None:
    source_pins = source.manifest_pins()
    destination_pins = destination.manifest_pins()
    if source_pins.science_contract != destination_pins.science_contract:
        raise ContractPinDisagreement(
            f"{node.id}: source and destination pin different science contracts"
        )
    for namespace in sorted(stored.used_facet_namespaces(node)):
        if (
            namespace not in source_pins.domains
            or destination_pins.domains.get(namespace) != source_pins.domains[namespace]
        ):
            raise ContractPinDisagreement(
                f"{node.id}: source and destination disagree on used namespace {namespace!r}"
            )


def move(
    source: CorpusWriter,
    destination: CorpusWriter,
    ref: str,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
) -> tuple[Node, ActReport, ActReport]:
    """Move one record destination-first and report once in each root."""
    _refuse_actor_disagreement(source, destination)
    with _both_locks(source, destination):
        source._require_pins_agree()
        destination._require_pins_agree()
        _refuse_same_root(source, destination)
        resolved = source.read_view.resolve(ref)
        if resolved is None:
            raise RelocationTargetMissing(f"{ref!r}: source holds no resolving record")
        node = source.read_view.get(resolved)
        _refuse_excluded_kind(node)
        _refuse_contract_disagreement(node, source, destination)
        if destination.read_view.resolve(node.id) == node.id:
            raise DuplicateLocation(
                f"{node.id}: destination already holds this canonical address"
            )
        destination._preflight_add_locked(node, provenance=True)
        for position, writer in (("source", source), ("destination", destination)):
            if writer._operation_port is None:
                raise RelocationRefused(
                    f"{position} corpus has no operation port; move is a boundary operation"
                )

        token = secrets.token_hex(16)
        destination.authority.require("corpus-write", (node.kind, "act-report"))
        source.authority.require("corpus-write", (node.kind, "act-report"))
        intent = OperationIntent("move", token, source.authority.actor)
        outcome = Moved(source.corpus_id, destination.corpus_id, node.id)
        report_fields = {
            "subject": node.id,
            "observer": observer,
            "instrument": instrument,
            "opened_at": opened_at,
            "closed_at": closed_at,
            "outcome": outcome,
        }
        destination_report = destination._relocation_report(intent, **report_fields)
        source_report = source._relocation_report(intent, **report_fields)
        destination_report_op = destination._create_op(
            stored.act_report_node(destination_report)
        )
        source_report_op = source._create_op(stored.act_report_node(source_report))

        destination_intent = destination._append_operation_intent(
            intent.kind, intent.event_token, intent.actor
        )
        source_intent = source._append_operation_intent(
            intent.kind, intent.event_token, intent.actor
        )
        moved = destination._add_locked(node, provenance=True)
        source._delete_locked(node.id)
        destination._publish_operation_report(
            destination_report,
            destination_intent,
            operation=destination_report_op,
        )
        source._publish_operation_report(
            source_report,
            source_intent,
            operation=source_report_op,
        )
        return moved, destination_report, source_report


def _relation_key(relation: Relation) -> tuple[str, str, str]:
    return relation.source, relation.predicate, relation.target


def _reconcile(survivor: Node, loser: Node) -> Node:
    relations: dict[tuple[str, str, str], Relation] = {}
    for relation in (*survivor.relations, *loser.relations):
        relations.setdefault(_relation_key(relation), relation)
    unstamped = survivor.model_copy(
        update={
            "relations": [relations[key] for key in sorted(relations)],
            "deprecated_ids": sorted(
                {*survivor.deprecated_ids, *loser.deprecated_ids}
            ),
            "facets": stored.union_lineage_bases(survivor, loser),
        }
    )
    return (
        stored.stamp_semantic_identity(unstamped)
        if unstamped.kind in stored.SEMANTIC_DOMAINS
        else unstamped
    )


def consolidate(
    keep: tuple[CorpusWriter, str],
    other: tuple[CorpusWriter, str],
    *,
    rationale: str,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
) -> tuple[Node, ActReport, ActReport]:
    """Consolidate one duplicate location into `keep` and report in both roots."""
    keep_writer, keep_ref = keep
    other_writer, other_ref = other
    _refuse_actor_disagreement(keep_writer, other_writer)
    with _both_locks(keep_writer, other_writer):
        keep_writer._require_pins_agree()
        other_writer._require_pins_agree()
        _refuse_same_root(keep_writer, other_writer)
        keep_id = keep_writer.read_view.resolve(keep_ref)
        if keep_id is None:
            raise RelocationTargetMissing(
                f"{keep_ref!r}: keep corpus holds no resolving record"
            )
        other_id = other_writer.read_view.resolve(other_ref)
        if other_id is None:
            raise RelocationTargetMissing(
                f"{other_ref!r}: other corpus holds no resolving record"
            )
        keep_node = keep_writer.read_view.get(keep_id)
        other_node = other_writer.read_view.get(other_id)
        _refuse_excluded_kind(keep_node)
        _refuse_excluded_kind(other_node)
        if keep_node.id != other_node.id:
            raise AddressDisagreement(
                f"{keep_node.id} and {other_node.id}: consolidation requires one canonical address"
            )
        _refuse_contract_disagreement(other_node, other_writer, keep_writer)
        merged = _reconcile(keep_node, other_node)
        keep_writer._preflight_replace_locked(merged, provenance=True)
        for position, writer in (("keep", keep_writer), ("other", other_writer)):
            if writer._operation_port is None:
                raise RelocationRefused(
                    f"{position} corpus has no operation port; consolidate is a boundary operation"
                )

        keep_writer.authority.require("corpus-write", (merged.kind, "act-report"))
        other_writer.authority.require("corpus-write", (other_node.kind, "act-report"))
        intent = OperationIntent("consolidate", secrets.token_hex(16), keep_writer.authority.actor)
        outcome = Consolidated(
            keep_writer.corpus_id,
            keep_node.id,
            other_writer.corpus_id,
            other_node.id,
            () if keep_node.uid == other_node.uid else (other_node.uid,),
            rationale,
        )
        report_fields = {
            "subject": keep_node.id,
            "observer": observer,
            "instrument": instrument,
            "opened_at": opened_at,
            "closed_at": closed_at,
            "outcome": outcome,
        }
        keep_report = keep_writer._relocation_report(intent, **report_fields)
        other_report = other_writer._relocation_report(intent, **report_fields)
        keep_report_op = keep_writer._create_op(stored.act_report_node(keep_report))
        other_report_op = other_writer._create_op(stored.act_report_node(other_report))

        keep_intent = keep_writer._append_operation_intent(
            intent.kind, intent.event_token, intent.actor
        )
        other_intent = other_writer._append_operation_intent(
            intent.kind, intent.event_token, intent.actor
        )
        survivor = keep_writer._replace_locked(merged, provenance=True)
        other_writer._delete_locked(other_node.id)
        keep_writer._publish_operation_report(
            keep_report, keep_intent, operation=keep_report_op
        )
        other_writer._publish_operation_report(
            other_report, other_intent, operation=other_report_op
        )
        return survivor, keep_report, other_report
