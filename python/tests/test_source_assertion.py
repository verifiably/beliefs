"""Unit tests for the typed source-assertion value, canonical facet, and record-local check."""

from __future__ import annotations

import copy
from typing import cast

import authority
import pytest
from nodes.core.relations import Relation

from beliefs.errors import MalformedRecord, SignatureRefused, SubclassRefused
from beliefs.identity import v1
from beliefs.reservation import UNREAD
from beliefs.source_assertion import (
    ANCHORED_IN,
    EXTENTS,
    SIGNS,
    SOURCE_ASSERTION_DOMAIN,
    Bearing,
    Reading,
    Representation,
    SourceAssertion,
    Span,
    source_assertion_from_stored,
    source_assertion_refusal,
)


def _value(**changes: object) -> SourceAssertion:
    fields: dict[str, object] = {
        "source": "source:" + "1" * 64,
        "sha256": "a" * 64,
        "media_type": "application/pdf",
        "extent": "full",
        "quote": "PHF19 is overexpressed",
        "locator": "Results, para 2",
        "extracted_by": authority.ACTOR,
        "attributed_to": None,
        "sign": "asserts",
        "proposition": "proposition:ab",
        "recorded_by": authority.ACTOR,
    }
    unknown = set(changes) - set(fields)
    if unknown:
        raise ValueError(f"unknown _value fields: {sorted(unknown)}")
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


def test_constants_match_the_spec():
    assert SIGNS == ("asserts", "denies", "hypothesizes")
    assert EXTENTS == ("full", "abstract")
    assert SOURCE_ASSERTION_DOMAIN == "science.source-assertion.v1"
    assert ANCHORED_IN == "anchored_in"


def test_the_facet_is_the_spec_shape_and_omits_an_absent_annotator():
    facet = _value().facet()
    assert list(facet) == ["read", "bears_on", "recorded_by"]
    read = cast(dict[str, object], facet["read"])
    assert list(read) == ["representation", "span", "extracted_by"]
    representation = cast(dict[str, object], read["representation"])
    span = cast(dict[str, object], read["span"])
    bears_on = cast(dict[str, object], facet["bears_on"])
    assert list(representation) == ["sha256", "media_type", "extent"]
    assert list(span) == ["quote", "locator"]
    assert list(bears_on) == ["sign", "proposition"]
    assert representation == {"sha256": "a" * 64, "media_type": "application/pdf", "extent": "full"}
    assert span == {"quote": "PHF19 is overexpressed", "locator": "Results, para 2"}
    assert bears_on == {"sign": "asserts", "proposition": "proposition:ab"}
    assert facet["recorded_by"] == authority.ACTOR
    annotated = _value(attributed_to="MSigDB curators").facet()
    annotated_read = cast(dict[str, object], annotated["read"])
    assert list(annotated_read) == ["representation", "span", "extracted_by", "attributed_to"]
    assert annotated_read["attributed_to"] == "MSigDB curators"


def test_identity_covers_read_and_bears_on_only():
    base = _value()
    assert base.id == "source-assertion:" + v1.digest(
        SOURCE_ASSERTION_DOMAIN, {"read": base.facet()["read"], "bears_on": base.facet()["bears_on"]}
    )
    assert _value(source="source:" + "2" * 64).id == base.id
    assert _value(recorded_by="session:" + "b" * 32).id == base.id
    assert _value(extracted_by="model:claude-opus-5-5").id != base.id


def test_relations_are_the_one_anchored_in_edge():
    v = _value()
    assert v.relations() == [Relation(source=v.id, predicate="anchored_in", target=v.source)]


def test_round_trip_through_the_stored_form():
    v = _value(attributed_to="MSigDB curators")
    assert source_assertion_from_stored(v.facet(), v.relations()) == v
    assert SourceAssertion.from_stored(v.facet(), v.relations()) == v
    bare = _value()
    assert source_assertion_from_stored(bare.facet(), bare.relations()) == bare


@pytest.mark.parametrize("sign", ["assesses", "supports", ""])
def test_a_sign_outside_the_closed_set_is_a_signature_refusal(sign):
    with pytest.raises(SignatureRefused):
        Bearing(sign=sign, proposition="proposition:ab")


def test_a_stored_sign_outside_the_closed_set_is_malformed():
    v = _value()
    facet = copy.deepcopy(v.facet())
    bears_on = cast(dict[str, object], facet["bears_on"])
    bears_on["sign"] = "assesses"
    with pytest.raises(MalformedRecord):
        source_assertion_from_stored(facet, v.relations())


@pytest.mark.parametrize(
    "field", ["quote", "locator", "media_type", "attributed_to", "extracted_by", "recorded_by", "source", "proposition"]
)
def test_a_decomposed_string_is_malformed_in_every_text_field(field):
    prefix = f"{field}:" if field in {"source", "proposition"} else ""
    with pytest.raises(MalformedRecord):
        _value(**{field: prefix + "cafe\u0301"})
    constructed = _value(**{field: prefix + "caf\u00e9"})
    assert source_assertion_from_stored(constructed.facet(), constructed.relations()) == constructed


def _drop_recorded_by(facet: dict[str, object]) -> dict[str, object]:
    del facet["recorded_by"]
    return facet


def _add_unknown_key(facet: dict[str, object]) -> dict[str, object]:
    facet["extra"] = "unexpected"
    return facet


def _wrong_type_sign(facet: dict[str, object]) -> dict[str, object]:
    cast(dict[str, object], facet["bears_on"])["sign"] = 123
    return facet


def _extent_skimmed(facet: dict[str, object]) -> dict[str, object]:
    cast(dict[str, object], cast(dict[str, object], facet["read"])["representation"])["extent"] = "skimmed"
    return facet


def _sha256_uppercase(facet: dict[str, object]) -> dict[str, object]:
    cast(dict[str, object], cast(dict[str, object], facet["read"])["representation"])["sha256"] = "A" * 64
    return facet


def _empty_quote(facet: dict[str, object]) -> dict[str, object]:
    cast(dict[str, object], cast(dict[str, object], facet["read"])["span"])["quote"] = ""
    return facet


def _empty_actor(facet: dict[str, object]) -> dict[str, object]:
    facet["recorded_by"] = ""
    return facet


def _non_dict_span(facet: dict[str, object]) -> dict[str, object]:
    cast(dict[str, object], facet["read"])["span"] = ["PHF19 is overexpressed", "Results, para 2"]
    return facet


_FACET_MUTATIONS = [
    ("missing key", _drop_recorded_by),
    ("unknown key", _add_unknown_key),
    ("wrong type", _wrong_type_sign),
    ("extent skimmed", _extent_skimmed),
    ("sha256 upper-case", _sha256_uppercase),
    ("empty quote", _empty_quote),
    ("actor ''", _empty_actor),
    ("non-canonical", _non_dict_span),
]


@pytest.mark.parametrize("mutate", [fn for _, fn in _FACET_MUTATIONS], ids=[name for name, _ in _FACET_MUTATIONS])
def test_a_malformed_stored_facet_is_refused(mutate):
    v = _value()
    facet = mutate(copy.deepcopy(v.facet()))
    with pytest.raises(MalformedRecord):
        source_assertion_from_stored(facet, v.relations())


def test_additional_stored_facet_and_constructor_malformed_cases():
    v = _value()
    with pytest.raises(MalformedRecord):
        source_assertion_from_stored(["not", "a", "dict"], v.relations())

    null_annotator = copy.deepcopy(v.facet())
    cast(dict[str, object], null_annotator["read"])["attributed_to"] = None
    with pytest.raises(MalformedRecord):
        source_assertion_from_stored(null_annotator, v.relations())

    with pytest.raises(MalformedRecord):
        Bearing(sign=123, proposition="proposition:ab")  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord):
        _value(attributed_to="")
    with pytest.raises(MalformedRecord):
        _value(quote="\ud800")
    with pytest.raises(MalformedRecord):
        _value(source="source:\ud800")
    with pytest.raises(MalformedRecord):
        _value(source="source:")
    with pytest.raises(MalformedRecord):
        _value(proposition="proposition:")
    with pytest.raises(MalformedRecord):
        _value(proposition="dataset:ab")
    with pytest.raises(MalformedRecord):
        Reading(representation="not-rep", span=v.read.span, extracted_by=authority.ACTOR)  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord):
        Reading(representation=v.read.representation, span="not-span", extracted_by=authority.ACTOR)  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord):
        SourceAssertion(source=v.source, read="not-read", bears_on=v.bears_on, recorded_by=authority.ACTOR)  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord):
        SourceAssertion(source=v.source, read=v.read, bears_on="not-bearing", recorded_by=authority.ACTOR)  # type: ignore[arg-type]


def test_the_value_types_are_sealed_against_subclassing():
    for cls in (Representation, Span, Reading, Bearing, SourceAssertion):
        with pytest.raises(SubclassRefused):
            type("Sub", (cls,), {})


@pytest.mark.parametrize(
    "edges", ["none", "two anchored_in", "anchored_in from another record", "anchored_in to a dataset"]
)
def test_the_anchor_edge_must_be_exactly_one_from_the_record_to_a_source(edges):
    v = _value()
    if edges == "none":
        relations: list[Relation] = []
    elif edges == "two anchored_in":
        relations = [*v.relations(), Relation(source=v.id, predicate="anchored_in", target="source:" + "2" * 64)]
    elif edges == "anchored_in from another record":
        relations = [Relation(source="source-assertion:" + "9" * 64, predicate="anchored_in", target=v.source)]
    else:
        relations = [Relation(source=v.id, predicate="anchored_in", target="dataset:" + "1" * 64)]
    with pytest.raises(MalformedRecord):
        source_assertion_from_stored(v.facet(), relations)


def test_stored_decoder_allows_extra_non_anchor_edges_and_rejects_non_relation_entries():
    v = _value()
    extra = [*v.relations(), Relation(source=v.id, predicate="assesses", target="proposition:ab")]
    assert source_assertion_from_stored(v.facet(), extra) == v
    with pytest.raises(MalformedRecord):
        source_assertion_from_stored(v.facet(), [*v.relations(), "not-a-relation"])  # type: ignore[list-item]


def test_an_extra_edge_is_an_edge_mismatch_and_refs_resolve_by_kind():
    v = _value()
    kinds = {v.source: "source", "proposition:ab": "proposition"}
    assert source_assertion_refusal(v, v.relations(), kind_of=kinds.get) is None
    extra = [*v.relations(), Relation(source=v.id, predicate="assesses", target="proposition:ab")]
    extra_refusal = source_assertion_refusal(v, extra, kind_of=kinds.get)
    assert extra_refusal is not None and extra_refusal.code == "source-assertion-edge-mismatch"
    doubled = [*v.relations(), *v.relations()]
    doubled_refusal = source_assertion_refusal(v, doubled, kind_of=kinds.get)
    assert doubled_refusal is not None and doubled_refusal.code == "source-assertion-edge-mismatch"
    cases = {
        "source absent": ({"proposition:ab": "proposition"}, "source", "resolves to no record"),
        "source another kind": ({v.source: "dataset", "proposition:ab": "proposition"}, "source", "is a dataset"),
        "proposition absent": ({v.source: "source"}, "proposition", "resolves to no record"),
        "proposition another kind": ({v.source: "source", "proposition:ab": "dataset"}, "proposition", "is a dataset"),
    }
    for kinds_here, slot, says in cases.values():
        refusal = source_assertion_refusal(v, v.relations(), kind_of=kinds_here.get)
        assert refusal is not None
        assert refusal.code == "source-assertion-ref-unresolved"
        assert f"the {slot} " in refusal.detail and says in refusal.detail
    assert source_assertion_refusal(v, v.relations(), kind_of=lambda ref: UNREAD) is None
    unread_source_absent_prop = source_assertion_refusal(
        v, v.relations(), kind_of=lambda ref: UNREAD if ref == v.source else None
    )
    assert unread_source_absent_prop is not None
    assert unread_source_absent_prop.code == "source-assertion-ref-unresolved"
    assert "the proposition " in unread_source_absent_prop.detail
