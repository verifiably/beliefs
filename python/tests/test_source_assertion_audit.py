"""Source assertions under corpus and world audit: `_WHOLE_READERS`, `check_source_assertion`, and `WORLD_AUDIT_CODES`."""

from __future__ import annotations

from typing import cast

import pytest
from authority import ACTOR, FULL
from fixtures_cut3 import carry_registers
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder
from test_world_build import ALPHA, BETA
from test_world_receipts import corpora, hold_shipped, publish, world_over
from test_world_view import make_absent

from beliefs import audit, stored
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.claim import Referent, build_claim
from beliefs.corpus import CorpusWriter, corpus_check
from beliefs.projection import project_claim
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span
from beliefs.world.view import open_world_view

GENE = "biology/gene"
AFFECTS = "biology/affects"


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    root = tmp_path / "corpus"
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    w = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    w.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return carry_registers(w)


@pytest.fixture()
def source(writer: CorpusWriter) -> Node:
    return writer.add(stored.source_node(title="s", identifiers={"doi": "10.1000/xyz"}))


@pytest.fixture()
def proposition(writer: CorpusWriter) -> Node:
    return writer.add(_proposition_node())


def _proposition_node() -> Node:
    claim = build_claim(
        WITH_BIOLOGY,
        operator=AFFECTS,
        roles={"cause": Referent(GENE, "EX:a"), "effect": Referent(GENE, "EX:b")},
        layer="causal",
        polarity="positive",
    )
    return stored.proposition_node("ab", title="ab", claim=project_claim(claim))


def _assertion(source_id: str, proposition_id: str, /, **changes: object) -> SourceAssertion:
    fields: dict[str, object] = {
        "source": source_id,
        "sha256": "a" * 64,
        "media_type": "application/pdf",
        "extent": "full",
        "quote": "PHF19 is overexpressed",
        "locator": "Results, para 2",
        "extracted_by": ACTOR,
        "attributed_to": None,
        "sign": "asserts",
        "proposition": proposition_id,
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


def _raw(writer: CorpusWriter, node: Node) -> Node:
    raw_write(writer.root, stored.stamp_semantic_identity(node))
    return node


def _findings(writer: CorpusWriter):
    return audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile)


def _codes(writer: CorpusWriter) -> list[tuple[str, str]]:
    return sorted((f.code, f.ref) for f in _findings(writer))


def _world_of(tmp_path, placement):
    roots = corpora(tmp_path, placement)
    world = world_over(tmp_path, roots)
    return world, roots, publish(world, tuple(placement), hold_shipped(world))


def _owing_a_register(findings) -> tuple:
    """`findings` less the one `register-missing` warning a fixture world's corpus owes."""
    owed = [f for f in findings if f.code == "register-missing"]
    assert [(f.ref, f.detail) for f in owed] == [("corpus.yaml", "biology")]
    return tuple(f for f in findings if f.code != "register-missing")


def test_a_well_formed_assertion_audits_clean(writer, source, proposition):
    added = _assertion(source.id, proposition.id)
    writer.add(stored.source_assertion_node(added, title="t1"))
    # An imported assertion recorded by another actor must also audit clean: actor binding is write-time only.
    imported = _assertion(
        source.id,
        proposition.id,
        sign="denies",
        attributed_to="author:smith",
        recorded_by="someone-else",
    )
    writer.import_bundle(
        [stored.source_assertion_node(imported, title="t2")],
        observer="o",
        instrument="i",
        opened_at="T0",
        closed_at="T1",
    )

    assert _codes(writer) == []
    from beliefs.audit import check_source_assertion

    view = reopen(writer.root)
    for ref in (added.id, imported.id):
        outcome = check_source_assertion(view, view.get(ref), profile=WITH_BIOLOGY)
        assert outcome.checked is True and outcome.contradiction is None


@pytest.mark.parametrize("predicate", ["frobs", "member_of"])
def test_a_raw_extra_edge_is_reported_as_edge_mismatch(predicate, writer, source, proposition):
    value = _assertion(source.id, proposition.id)
    node = stored.source_assertion_node(value, title="t")
    with_extra = _raw(
        writer,
        node.model_copy(
            update={
                "relations": [*node.relations, Relation(source=value.id, predicate=predicate, target=proposition.id)]
            }
        ),
    )
    assert _codes(writer) == [("source-assertion-edge-mismatch", with_extra.id)]


def test_a_raw_assesses_edge_reports_eligibility_and_edge_mismatch(writer, source, proposition):
    value = _assertion(source.id, proposition.id)
    node = stored.source_assertion_node(value, title="t")
    with_assesses = _raw(
        writer,
        node.model_copy(
            update={
                "relations": [*node.relations, Relation(source=value.id, predicate="assesses", target=proposition.id)]
            }
        ),
    )
    assert _codes(writer) == sorted(
        [
            ("eligibility-unmet", with_assesses.id),
            ("source-assertion-edge-mismatch", with_assesses.id),
        ]
    )


def test_a_dangling_source_or_proposition_is_reported(writer, source, proposition):
    dangling_source = _raw(
        writer,
        stored.source_assertion_node(
            _assertion("source:" + "9" * 64, proposition.id, locator="dangling-source"),
            title="dangling-source",
        ),
    )
    dangling_prop = _raw(
        writer,
        stored.source_assertion_node(
            _assertion(source.id, "proposition:nowhere", locator="dangling-prop"),
            title="dangling-prop",
        ),
    )

    source_alias = "source:" + "8" * 64
    prop_alias = "proposition:alias"
    dataset = stored.dataset_node(title="d", resources=[{"name": "r", "digest": "sha256:" + "d" * 64}])
    _raw(writer, dataset.model_copy(update={"deprecated_ids": [source_alias, prop_alias]}))

    wrong_source = _raw(
        writer,
        stored.source_assertion_node(
            _assertion(source_alias, proposition.id, locator="wrong-source"),
            title="wrong-source",
        ),
    )
    wrong_prop = _raw(
        writer,
        stored.source_assertion_node(
            _assertion(source.id, prop_alias, locator="wrong-prop"),
            title="wrong-prop",
        ),
    )

    findings = _findings(writer)
    assert sorted((f.code, f.ref) for f in findings) == sorted(
        [
            ("source-assertion-ref-unresolved", dangling_source.id),
            ("source-assertion-ref-unresolved", dangling_prop.id),
            ("source-assertion-ref-unresolved", wrong_source.id),
            ("source-assertion-ref-unresolved", wrong_prop.id),
        ]
    )
    by_ref = {f.ref: f for f in findings}
    assert (
        "the source" in by_ref[dangling_source.id].detail
        and "resolves to no record" in by_ref[dangling_source.id].detail
    )
    assert (
        "the proposition" in by_ref[dangling_prop.id].detail
        and "resolves to no record" in by_ref[dangling_prop.id].detail
    )
    assert "the source" in by_ref[wrong_source.id].detail and "is a dataset" in by_ref[wrong_source.id].detail
    assert "the proposition" in by_ref[wrong_prop.id].detail and "is a dataset" in by_ref[wrong_prop.id].detail


def _malformed_node(source_id: str, proposition_id: str, damage: str, index: int) -> Node:
    value = _assertion(source_id, proposition_id, locator=f"Results, para {index}")
    node = stored.source_assertion_node(value, title=f"bad-{index}").model_copy(deep=True)
    facet = cast(dict[str, object], node.facets[stored.SOURCE_ASSERTION_FACET])
    if damage == "stored sign assesses":
        cast(dict[str, object], facet["bears_on"])["sign"] = "assesses"
    elif damage == "missing key":
        del facet["recorded_by"]
    elif damage == "unknown key":
        facet["extra"] = "unexpected"
    elif damage == "non-NFC quote":
        cast(dict[str, object], cast(dict[str, object], facet["read"])["span"])["quote"] = "cafe\u0301"
    elif damage == "missing anchored_in":
        node = node.model_copy(update={"relations": []})
    elif damage == "doubled anchored_in":
        extra = Relation(source=node.id, predicate=stored.ANCHORED_IN, target="source:" + "b" * 64)
        node = node.model_copy(update={"relations": [*node.relations, extra]})
    elif damage == "wrong id":
        node = node.model_copy(update={"id": "source-assertion:" + "9" * 64})
    else:
        raise ValueError(f"unknown damage: {damage!r}")
    return node


def test_a_malformed_facet_is_facet_payload_malformed_and_corpus_check_does_not_raise(writer, source, proposition):
    damages = (
        "stored sign assesses",
        "missing key",
        "unknown key",
        "non-NFC quote",
        "missing anchored_in",
        "doubled anchored_in",
        "wrong id",
    )
    bad_nodes = [
        _raw(writer, _malformed_node(source.id, proposition.id, damage, i)) for i, damage in enumerate(damages)
    ]

    view = reopen(writer.root)
    checked = corpus_check(view, writer.profile)
    audited = _findings(writer)
    expected = sorted(("facet-payload-malformed", node.id, stored.SOURCE_ASSERTION_FACET) for node in bad_nodes)
    assert sorted((f.code, f.ref, f.detail) for f in checked) == expected
    assert sorted((f.code, f.ref, f.detail) for f in audited) == expected


def test_world_audit_skips_a_source_held_in_an_absent_corpus(tmp_path):
    source = stored.source_node(title="s", identifiers={"doi": "10.1000/xyz"})
    proposition = _proposition_node()
    value = _assertion(source.id, proposition.id)
    assertion = stored.source_assertion_node(value, title="t")

    world, roots, published = _world_of(tmp_path, {ALPHA: (proposition, assertion), BETA: (source,)})
    present = audit.audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)
    assert _owing_a_register(present.corpora[ALPHA]) == () and _owing_a_register(present.corpora[BETA]) == ()

    make_absent(roots, BETA)
    absent = audit.audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    assert _owing_a_register(absent.corpora[ALPHA]) == ()
    assert [f.code for f in absent.corpora[BETA]] == ["corpus-absent"]
    view = open_world_view(world, published, on_damage="report")
    outcome = audit.check_source_assertion(view, view.get(value.id), profile=WITH_BIOLOGY)
    assert outcome.checked is False and outcome.contradiction is None
    assert source.id in outcome.reason and BETA in outcome.reason


def test_world_audit_reports_a_dangling_reference(tmp_path):
    source = stored.source_node(title="s", identifiers={"doi": "10.1000/xyz"})
    proposition = _proposition_node()
    valid = stored.source_assertion_node(_assertion(source.id, proposition.id, locator="valid"), title="valid")
    dangling_source = stored.source_assertion_node(
        _assertion("source:" + "9" * 64, proposition.id, locator="dangling-source"),
        title="dangling-source",
    )
    dangling_prop = stored.source_assertion_node(
        _assertion(source.id, "proposition:nowhere", locator="dangling-prop"),
        title="dangling-prop",
    )

    world, _roots, published = _world_of(
        tmp_path,
        {
            ALPHA: (source, dangling_source),
            BETA: (proposition, valid, dangling_prop),
        },
    )

    found = audit.audit_world(world, published, evidence=NO_EVIDENCE, profile=WITH_BIOLOGY)

    alpha_findings = _owing_a_register(found.corpora[ALPHA])
    beta_findings = _owing_a_register(found.corpora[BETA])
    assert [(f.code, f.ref) for f in alpha_findings] == [("source-assertion-ref-unresolved", dangling_source.id)]
    assert [(f.code, f.ref) for f in beta_findings] == [("source-assertion-ref-unresolved", dangling_prop.id)]
    assert "the source" in alpha_findings[0].detail
    assert "the proposition" in beta_findings[0].detail


def test_the_codes_are_world_audit_codes():
    assert {"source-assertion-edge-mismatch", "source-assertion-ref-unresolved"} <= audit.WORLD_AUDIT_CODES
    assert not {"source-assertion-edge-mismatch", "source-assertion-ref-unresolved"} & audit.MALFORMEDNESS_CODES
