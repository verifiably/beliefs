"""The proposition prose revision path."""

from __future__ import annotations

from hashlib import sha256
from typing import ClassVar

import pytest
from authority import FULL
from nodes.core.node import NodeMetadata
from nodes.core.write_plan import DefaultExecutor, ReplaceOp

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    ReviseKindImmutable,
    ReviseOutsideAllowlist,
    RevisionTargetMissing,
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
    return CorpusWriter(tmp_path, Recorder, authority=FULL)


def prop(slug: str = "p"):
    return stored.proposition_node(slug, title="old", claim={"op": "affects"})


def test_revise_prose_in_place_no_mint(writer):
    old = writer.add(prop())
    old_digest = stored.stored_semantic_hash(old)
    edited = old.model_copy(update={"title": "new title", "body": "new body"})

    out = writer.revise(edited)

    assert (out.uid, out.id) == (old.uid, old.id)
    assert len(list(writer.read_view.iter_stored())) == 1
    (op,) = Recorder.plans[-1]
    assert isinstance(op, ReplaceOp)
    assert op.expected_digest == sha256(Recorder.plans[-2][0].content).hexdigest()
    got = writer.read_view.get(old.id)
    assert (got.title, got.body) == ("new title", "new body")
    assert stored.stored_semantic_hash(got) == old_digest


def test_revise_unrenderable_prose_refuses_before_execution(writer):
    old = writer.add(prop())

    with pytest.raises(ValidationRefused, match="losslessly renderable"):
        writer.revise(old.model_copy(update={"body": "\ud800"}))

    assert len(Recorder.plans) == 1


def test_revise_display_statement_add_change_remove(writer):
    current = writer.add(prop())
    digest = stored.stored_semantic_hash(current)

    for display_statement in ("first rendering", "better rendering", None):
        facets = dict(current.facets)
        if display_statement is None:
            facets.pop(stored.DISPLAY_FACET)
        else:
            facets[stored.DISPLAY_FACET] = {"display_statement": display_statement}
        current = writer.revise(current.model_copy(update={"facets": facets}))
        assert stored.display_statement(writer.read_view.get(current.id)) == display_statement
        assert stored.stored_semantic_hash(current) == digest

    assert all(isinstance(plan[0], ReplaceOp) and len(plan) == 1 for plan in Recorder.plans[1:])


def test_revise_refuses_semantic_field_change(writer):
    old = writer.add(prop())
    edited = old.model_copy(
        update={"facets": {**old.facets, stored.PROPOSITION_FACET: {"op": "causes"}}}
    )

    with pytest.raises(ReviseOutsideAllowlist):
        writer.revise(edited)


def test_revise_refuses_relation_change(writer):
    old = writer.add(prop())
    edited = old.model_copy(
        update={
            "relations": [
                stored.Relation(source=old.id, predicate="cites", target="source:elsewhere")
            ]
        }
    )

    with pytest.raises(ReviseOutsideAllowlist):
        writer.revise(edited)


def test_revise_refuses_other_node_field_changes(writer):
    old = writer.add(prop())

    for update in (
        {"metadata": NodeMetadata(version=2)},
        {"deprecated_ids": ["proposition:former"]},
    ):
        with pytest.raises(ReviseOutsideAllowlist):
            writer.revise(old.model_copy(update=update))


def test_revise_refuses_other_facet_and_stamp_changes(writer):
    old = writer.add(prop())
    for facets in (
        {**old.facets, "annotation": {"text": "new"}},
        {**old.facets, stored.SEMANTIC_IDENTITY_FACET: {"digest": "sha256:forged"}},
    ):
        with pytest.raises(ReviseOutsideAllowlist):
            writer.revise(old.model_copy(update={"facets": facets}))


def test_revise_refuses_missing_exact_target(writer):
    writer.add(prop("ghost"))

    with pytest.raises(RevisionTargetMissing):
        writer.revise(prop("ghost"))


def test_revise_refuses_non_proposition(writer):
    source = writer.add(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}))

    with pytest.raises(ReviseKindImmutable):
        writer.revise(source.model_copy(update={"title": "x"}))


def test_revise_wraps_an_unhashable_uid_as_validation_refused(writer):
    old = writer.add(prop())

    with pytest.raises(ValidationRefused):
        writer.revise(old.model_copy(update={"uid": []}))


def test_revise_wraps_non_iterable_relations_as_validation_refused(writer):
    old = writer.add(prop())

    with pytest.raises(ValidationRefused):
        writer.revise(old.model_copy(update={"relations": None}))


def test_revise_revalidates_a_forged_nested_model(writer):
    old = writer.add(prop())
    malformed = old.model_copy(update={"metadata": NodeMetadata.model_construct(version="bad")})

    with pytest.raises(ValidationRefused):
        writer.revise(malformed)

    assert writer.read_view.get(old.id).metadata == old.metadata
    assert len(Recorder.plans) == 1


def test_revise_refuses_malformed_public_shapes(writer):
    old = writer.add(prop())
    malformed_display = old.model_copy(
        update={"facets": {**old.facets, stored.DISPLAY_FACET: {"extra": "field"}}}
    )
    malformed_relation = old.model_copy(
        update={"relations": [{"source": old.id, "predicate": "cites", "target": "source:s"}]}
    )
    unencodable_semantics = old.model_copy(
        update={"facets": {**old.facets, stored.PROPOSITION_FACET: {"op": 0.1}}}
    )

    for candidate in (malformed_display, malformed_relation, unencodable_semantics):
        with pytest.raises(ValidationRefused):
            writer.revise(candidate)


def test_revise_errors_are_write_refusals():
    for refusal in (RevisionTargetMissing, ReviseKindImmutable, ReviseOutsideAllowlist):
        assert issubclass(refusal, WriteRefused)
