"""The proposition successor write path."""

from __future__ import annotations

from typing import ClassVar

import pytest
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, DefaultExecutor

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    FamilyKindUnsupported,
    RecordAlreadyMinted,
    RelocationTargetMissing,
    SupersedeIdentityUnchanged,
    ValidationRefused,
    WriteRefused,
)


class Recorder:
    """Apply each recorded plan so the real writer remains readable."""

    plans: ClassVar[list[list]] = []

    def __init__(self, root):
        self._inner = DefaultExecutor(root)

    def execute(self, plan) -> None:
        Recorder.plans.append(list(plan))
        self._inner.execute(plan)


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    Recorder.plans = []
    return CorpusWriter(tmp_path, Recorder)


def prop(slug: str, claim_op: str = "affects") -> Node:
    return stored.proposition_node(slug, title=slug, claim={"op": claim_op})


def test_supersede_mints_a_successor_and_one_owned_edge(writer):
    old = writer.add(prop("in-adults"))
    predecessor = writer.read_view.get(old.id).model_dump(mode="json")

    new = writer.supersede(prop("in-all-humans", claim_op="causes"), of=old.id)

    assert new.relations == [
        stored.Relation(source=new.id, predicate=stored.SUPERSEDES, target=old.id)
    ]
    assert all(isinstance(op, CreateOp) for op in Recorder.plans[-1])
    assert writer.read_view.get(old.id).model_dump(mode="json") == predecessor


def test_supersede_uses_relocation_missing_for_an_absent_predecessor(writer):
    with pytest.raises(RelocationTargetMissing):
        writer.supersede(prop("s"), of="proposition:absent")


def test_supersede_refuses_a_stale_successor_stamp_before_execution(writer):
    old = writer.add(prop("old"))
    successor = prop("new", claim_op="causes")
    successor.facets[stored.PROPOSITION_FACET]["op"] = "prevents"

    with pytest.raises(ValidationRefused, match="semantic-identity stamp"):
        writer.supersede(successor, of=old.id)

    assert len(Recorder.plans) == 1


def test_supersede_refuses_an_unsupported_predecessor_kind(writer):
    source = writer.add(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}))

    with pytest.raises(FamilyKindUnsupported):
        writer.supersede(prop("p"), of=source.id)


def test_supersede_refuses_an_unsupported_successor_kind(writer):
    old = writer.add(prop("p"))

    with pytest.raises(FamilyKindUnsupported):
        writer.supersede(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}), of=old.id)


def test_supersede_refuses_a_fresh_pair_before_a_caller_authored_edge(writer):
    old = writer.add(prop("old"))
    minted = writer.add(prop("new", claim_op="causes"))
    candidate = minted.model_copy(
        update={
            "relations": [
                stored.Relation(source=minted.id, predicate=stored.SUPERSEDES, target=old.id)
            ]
        }
    )

    with pytest.raises(RecordAlreadyMinted):
        writer.supersede(candidate, of=old.id)


def test_supersede_refuses_a_caller_authored_edge_before_equal_identity(writer):
    old = writer.add(prop("p"))
    candidate = prop("p-copy")
    candidate = candidate.model_copy(
        update={
            "relations": [
                stored.Relation(source=candidate.id, predicate=stored.SUPERSEDES, target=old.id)
            ]
        }
    )

    with pytest.raises(ValidationRefused):
        writer.supersede(candidate, of=old.id)


def test_supersede_refuses_an_unvalidated_relation_shape(writer):
    old = writer.add(prop("old"))
    candidate = prop("new", claim_op="causes").model_copy(
        update={"relations": [{"source": "proposition:new", "predicate": "cites", "target": old.id}]}
    )

    with pytest.raises(ValidationRefused):
        writer.supersede(candidate, of=old.id)


def test_supersede_refuses_an_unencodable_covered_facet_value(writer):
    old = writer.add(prop("old"))
    candidate = prop("new", claim_op="causes").model_copy(
        update={"facets": {stored.PROPOSITION_FACET: {"op": 0.1}}}
    )

    with pytest.raises(ValidationRefused):
        writer.supersede(candidate, of=old.id)


def test_supersede_refuses_an_equal_semantic_identity(writer):
    old = writer.add(prop("p"))

    with pytest.raises(SupersedeIdentityUnchanged):
        writer.supersede(prop("p-copy"), of=old.id)


def test_supersede_errors_are_write_refusals():
    for refusal in (RelocationTargetMissing, SupersedeIdentityUnchanged, FamilyKindUnsupported):
        assert issubclass(refusal, WriteRefused)
