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

from beliefs import stored
from beliefs.coordination import COORDINATION_KINDS
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    ContractPinDisagreement,
    DuplicateLocation,
    RelocationKindExcluded,
    RelocationRefused,
    RelocationTargetMissing,
    SameRootRefused,
)
from beliefs.report import ActReport, Moved, OperationIntent

EXCLUDED_KINDS = ("act-report", "holdings-observation", *COORDINATION_KINDS)


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
    actor: str,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
) -> tuple[Node, ActReport, ActReport]:
    """Move one record destination-first and report once in each root."""
    with _both_locks(source, destination):
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
        destination._preflight_add_locked(node)
        for position, writer in (("source", source), ("destination", destination)):
            if writer._operation_port is None:
                raise RelocationRefused(
                    f"{position} corpus has no operation port; move is a boundary operation"
                )

        token = secrets.token_hex(16)
        intent = OperationIntent("move", token, actor)
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
        moved = destination._add_locked(node)
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
