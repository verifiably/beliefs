"""The two-root world-changing operations: `move` and `consolidate`.

This module **composes** two `CorpusWriter`s and subclasses neither: an
operation over two corpus roots cannot honestly be a method on an object bound
to one. `atoms` §12.2 keys an engine root on a corpus root, so two corpora are
two chains and two operation ports — these operations are never one
transaction, and the design's §3.5 enumerates every durable prefix instead of
pretending otherwise.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from nodes.core.node import Node

from beliefs import stored
from beliefs.coordination import COORDINATION_KINDS
from beliefs.corpus import CorpusWriter
from beliefs.errors import ContractPinDisagreement, RelocationKindExcluded, SameRootRefused

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
