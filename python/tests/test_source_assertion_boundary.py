"""The source-assertion write boundary: one `anchored_in` edge, resolved endpoints, NFC strings, and bound actor."""

from __future__ import annotations

from typing import cast

import pytest
from authority import ACTOR, FULL
from fixtures_cut4 import raw_write
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    ActorMismatch,
    CollisionRefused,
    MalformedRecord,
    RecordAlreadyMinted,
    ReviseKindImmutable,
    SourceAssertionRefused,
    ValidationRefused,
)
from beliefs.projection import project_claim
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span

GENE = "biology/gene"
AFFECTS = "biology/affects"


@pytest.fixture()
def writer(tmp_path):
    root = tmp_path / "corpus"
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    w = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    w.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return w


@pytest.fixture()
def source(writer) -> Node:
    return writer.add(stored.source_node(title="s", identifiers={"doi": "10.1000/xyz"}))


@pytest.fixture()
def proposition(writer) -> Node:
    claim = build_claim(
        WITH_BIOLOGY,
        operator=AFFECTS,
        roles={"cause": Referent(GENE, "EX:a"), "effect": Referent(GENE, "EX:b")},
        layer="causal",
        polarity="positive",
    )
    return writer.add(stored.proposition_node("ab", title="ab", claim=project_claim(claim)))


def _assertion(source: Node, proposition: Node, /, **changes: object) -> SourceAssertion:
    fields: dict[str, object] = {
        "source": source.id,
        "sha256": "a" * 64,
        "media_type": "application/pdf",
        "extent": "full",
        "quote": "PHF19 is overexpressed",
        "locator": "Results, para 2",
        "extracted_by": ACTOR,
        "attributed_to": None,
        "sign": "asserts",
        "proposition": proposition.id,
        "recorded_by": ACTOR,
    }
    unknown = set(changes) - set(fields)
    if unknown:
        raise ValueError(f"unknown _assertion fields: {sorted(unknown)}")
    fields.update(changes)
    return SourceAssertion(
        source=cast(str, fields["source"]),
        read=Reading(
            representation=Representation(
                sha256=cast(str, fields["sha256"]),
                media_type=cast(str, fields["media_type"]),
                extent=cast(str, fields["extent"]),
            ),
            span=Span(
                quote=cast(str, fields["quote"]),
                locator=cast(str, fields["locator"]),
            ),
            extracted_by=cast(str, fields["extracted_by"]),
            attributed_to=cast(str | None, fields["attributed_to"]),
        ),
        bears_on=Bearing(
            sign=cast(str, fields["sign"]),
            proposition=cast(str, fields["proposition"]),
        ),
        recorded_by=cast(str, fields["recorded_by"]),
    )


def test_add_mints_an_assertion_whose_one_edge_is_anchored_in(writer, source, proposition):
    value = _assertion(source, proposition)
    minted = writer.add(stored.source_assertion_node(value, title="t"))
    assert minted.id == value.id
    back = writer.read_view.get(value.id)
    assert [(r.predicate, r.target) for r in back.relations] == [("anchored_in", source.id)]
    assert stored.source_assertion_value(back) == value


def test_builder_and_reader_enforce_types_and_preserve_body(source, proposition):
    value = _assertion(source, proposition)
    node = stored.source_assertion_node(value, title="t", body="paraphrase")
    assert node.body == "paraphrase"
    assert stored.source_assertion_value(node) == value
    with pytest.raises(MalformedRecord):
        stored.source_assertion_node("not-an-assertion", title="t")  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord, match=stored.SOURCE_ASSERTION_FACET):
        stored.source_assertion_value(node.model_copy(update={"facets": {}}))


def test_add_refuses_an_assesses_edge_by_the_kinds_own_rule_before_eligibility(writer, source, proposition):
    value = _assertion(source, proposition)
    node = stored.source_assertion_node(value, title="t")
    with_assesses = stored.stamp_semantic_identity(
        node.model_copy(
            update={
                "relations": [*node.relations, Relation(source=value.id, predicate="assesses", target=proposition.id)]
            }
        )
    )
    with pytest.raises(SourceAssertionRefused) as caught:
        writer.add(with_assesses)
    assert caught.value.code == "source-assertion-edge-mismatch"


def test_add_refuses_an_undeclared_and_a_declared_extra_edge(writer, source, proposition):
    value = _assertion(source, proposition)
    node = stored.source_assertion_node(value, title="t")
    for predicate in ("frobs", "member_of"):
        with_extra = stored.stamp_semantic_identity(
            node.model_copy(
                update={
                    "relations": [
                        *node.relations,
                        Relation(source=value.id, predicate=predicate, target=proposition.id),
                    ]
                }
            )
        )
        with pytest.raises(SourceAssertionRefused) as caught:
            writer.add(with_extra)
        assert caught.value.code == "source-assertion-edge-mismatch"


@pytest.mark.parametrize("missing", ["source", "proposition"])
def test_add_refuses_an_unresolved_reference(missing, writer, source, proposition):
    changes: dict[str, object] = (
        {"source": "source:" + "9" * 64} if missing == "source" else {"proposition": "proposition:nowhere"}
    )
    value = _assertion(source, proposition, **changes)
    with pytest.raises(SourceAssertionRefused) as caught:
        writer.add(stored.source_assertion_node(value, title="t"))
    assert caught.value.code == "source-assertion-ref-unresolved"
    assert f"the {missing} " in str(caught.value)
    assert "resolves to no record" in str(caught.value)


@pytest.mark.parametrize("slot", ["source", "proposition"])
def test_add_refuses_a_reference_resolving_to_another_kind(slot, writer, source, proposition):
    alias = "source:" + "8" * 64 if slot == "source" else "proposition:alias"
    dataset = stored.dataset_node(title="d", resources=[{"name": "r", "digest": "sha256:" + "d" * 64}])
    raw_write(writer.root, stored.stamp_semantic_identity(dataset.model_copy(update={"deprecated_ids": [alias]})))
    writer._reconstruct()

    changes: dict[str, object] = {"source": alias} if slot == "source" else {"proposition": alias}
    value = _assertion(source, proposition, **changes)
    with pytest.raises(SourceAssertionRefused) as caught:
        writer.add(stored.source_assertion_node(value, title="t"))
    assert caught.value.code == "source-assertion-ref-unresolved"
    assert f"the {slot} " in str(caught.value)
    assert "is a dataset" in str(caught.value)


def test_add_refuses_a_facetless_record_as_validation(writer):
    node = Node(id="source-assertion:" + "0" * 64, kind="source-assertion", title="t", facets={}, relations=[])
    with pytest.raises(ValidationRefused, match="facet-missing"):
        writer.add(node)


@pytest.mark.parametrize("damage", ["missing key", "unknown key", "wrong type", "wrong id", "stored sign assesses"])
def test_add_refuses_a_malformed_facet(damage, writer, source, proposition):
    value = _assertion(source, proposition)
    node = stored.source_assertion_node(value, title="t").model_copy(deep=True)
    facet = cast(dict[str, object], node.facets[stored.SOURCE_ASSERTION_FACET])
    if damage == "missing key":
        del facet["recorded_by"]
        damaged = stored.stamp_semantic_identity(node)
    elif damage == "unknown key":
        facet["extra"] = "unexpected"
        damaged = stored.stamp_semantic_identity(node)
    elif damage == "wrong type":
        cast(dict[str, object], facet["bears_on"])["sign"] = 123
        damaged = stored.stamp_semantic_identity(node)
    elif damage == "wrong id":
        damaged = stored.stamp_semantic_identity(node.model_copy(update={"id": "source-assertion:" + "9" * 64}))
    else:
        cast(dict[str, object], facet["bears_on"])["sign"] = "assesses"
        damaged = stored.stamp_semantic_identity(node)

    with pytest.raises(SourceAssertionRefused) as caught:
        writer.add(damaged)
    assert caught.value.code == "source-assertion-malformed"
    if damage == "wrong id":
        assert "does not recompute" in str(caught.value)


@pytest.mark.parametrize("field", ["quote", "locator", "source"])
def test_add_refuses_a_decomposed_quote(field, writer, source, proposition):
    value = _assertion(source, proposition)
    node = stored.source_assertion_node(value, title="t").model_copy(deep=True)
    if field in ("quote", "locator"):
        facet = cast(dict[str, object], node.facets[stored.SOURCE_ASSERTION_FACET])
        span = cast(dict[str, object], cast(dict[str, object], facet["read"])["span"])
        span[field] = "cafe\u0301"
        damaged = stored.stamp_semantic_identity(node)
    else:
        damaged = stored.stamp_semantic_identity(
            node.model_copy(
                update={
                    "relations": [Relation(source=node.id, predicate=stored.ANCHORED_IN, target="source:cafe\u0301")]
                }
            )
        )

    with pytest.raises(SourceAssertionRefused) as caught:
        writer.add(damaged)
    assert caught.value.code == "source-assertion-malformed"
    assert "Unicode NFC" in str(caught.value)


def test_add_refuses_another_actor_as_recorder(writer, source, proposition):
    value = _assertion(source, proposition, recorded_by="someone-else")
    node = stored.source_assertion_node(value, title="t")
    with pytest.raises(ActorMismatch):
        writer.add(node)
    writer.import_bundle([node], observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert writer.read_view.holds(value.id)


def test_reminting_the_same_extraction_is_refused(writer, source, proposition):
    value = _assertion(source, proposition)
    first = stored.source_assertion_node(value, title="t")
    writer.add(first)
    assert writer.read_view.holds(value.id) is True
    with pytest.raises(RecordAlreadyMinted):
        writer.add(first)
    second = stored.source_assertion_node(value, title="t")
    assert second.uid != first.uid and second.id == first.id
    with pytest.raises(CollisionRefused):
        writer.add(second)


def test_a_second_extractor_makes_a_second_record(writer, source, proposition):
    first = _assertion(source, proposition, extracted_by=ACTOR)
    second = _assertion(source, proposition, extracted_by="model:claude-opus-5-5")
    assert first.id != second.id
    writer.add(stored.source_assertion_node(first, title="t1"))
    writer.add(stored.source_assertion_node(second, title="t2"))
    assert writer.read_view.holds(first.id)
    assert writer.read_view.holds(second.id)


def test_revise_refuses_the_kind(writer, source, proposition):
    minted = writer.add(stored.source_assertion_node(_assertion(source, proposition), title="t"))
    with pytest.raises(ReviseKindImmutable):
        writer.revise(minted.model_copy(update={"body": "revised paraphrase"}))


def test_replacement_preflight_refuses_an_extra_edge(writer, source, proposition):
    value = _assertion(source, proposition)
    minted = writer.add(stored.source_assertion_node(value, title="t"))
    with_assesses = stored.stamp_semantic_identity(
        minted.model_copy(
            update={
                "relations": [*minted.relations, Relation(source=value.id, predicate="assesses", target=proposition.id)]
            }
        )
    )
    with pytest.raises(SourceAssertionRefused) as caught:
        writer._preflight_replace_locked(with_assesses, provenance=True)
    assert caught.value.code == "source-assertion-edge-mismatch"
