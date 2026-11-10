"""The exposure-event write boundary: edges mirror the facet, refs resolve, the actor is the bound one."""

from __future__ import annotations

from dataclasses import replace

import pytest
from authority import ACTOR, FULL
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder
from test_reservation import _event

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    ActorMismatch,
    DeletionKindExcluded,
    MalformedRecord,
    RecordAlreadyMinted,
    ReservationRefused,
    ReviseOutsideAllowlist,
)
from beliefs.identity import v1
from beliefs.projection import project_claim
from beliefs.reservation import EXPOSURE_EVENT_DOMAIN, TermUnit

GENE = "biology/gene"
AFFECTS = "biology/affects"
_D = "a" * 64


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


def _unit() -> TermUnit:
    return TermUnit(GENE, "EX:a")


def _read(source: Node, **overrides: object):
    return _event(subjects=(source.id,), units=(_unit(),), observer=ACTOR, recorded_by=ACTOR, evidence=(), **overrides)


def test_add_mints_an_exposure_event_whose_edges_mirror_its_facet(writer, source, proposition):
    dataset = writer.add(stored.dataset_node(title="d", resources=[{"name": "r", "digest": "sha256:" + _D}]))
    value = replace(
        _read(source, propositions=(proposition.id,)),
        subjects=tuple(sorted((dataset.id, source.id))),
    )
    minted = writer.add(stored.exposure_event_node(value, title="t"))
    assert minted.id == value.id
    assert [(r.predicate, r.target) for r in writer.read_view.get(value.id).relations] == [
        *(("exposes", ref) for ref in sorted((dataset.id, source.id))),
        ("concerns", proposition.id),
    ]


def test_an_edge_the_facet_does_not_name_or_a_missing_edge_is_refused(writer, source, proposition):
    value = _read(source)
    node = stored.exposure_event_node(value, title="t")
    extra = Relation(source=node.id, predicate="concerns", target=proposition.id)
    with pytest.raises(ReservationRefused) as caught:
        writer.add(node.model_copy(update={"relations": [*node.relations, extra]}))
    assert caught.value.code == "exposure-edge-mismatch"
    with pytest.raises(ReservationRefused) as caught:
        writer.add(node.model_copy(update={"relations": []}))
    assert caught.value.code == "exposure-edge-mismatch"


def test_an_unresolved_subject_is_refused(writer):
    value = _event(units=(_unit(),), observer=ACTOR, recorded_by=ACTOR, evidence=())
    with pytest.raises(ReservationRefused) as caught:
        writer.add(stored.exposure_event_node(value, title="t"))
    assert caught.value.code == "exposure-ref-unresolved"


def test_a_subject_of_the_wrong_kind_is_refused(writer, proposition):
    value = _event(
        subjects=("dataset:" + proposition.id.partition(":")[2],),
        units=(_unit(),),
        observer=ACTOR,
        recorded_by=ACTOR,
        evidence=(),
    )
    with pytest.raises(ReservationRefused) as caught:
        writer.add(stored.exposure_event_node(value, title="t"))
    assert caught.value.code == "exposure-ref-unresolved"


def test_a_concerned_proposition_of_the_wrong_kind_is_refused(writer, source):
    value = _read(source)
    value = replace(value, propositions=(f"proposition:{source.id.partition(':')[2]}",))
    with pytest.raises(ReservationRefused) as caught:
        writer.add(stored.exposure_event_node(value, title="t"))
    assert caught.value.code == "exposure-ref-unresolved"


def test_an_evidence_run_that_does_not_resolve_is_refused(writer, source):
    value = replace(_read(source), evidence=("run:never-stored",))
    with pytest.raises(ReservationRefused) as caught:
        writer.add(stored.exposure_event_node(value, title="t"))
    assert caught.value.code == "exposure-ref-unresolved"


def test_a_resolving_evidence_run_is_admitted(writer, source):
    run = writer.add(stored.run_node("r1", title="r1", spec="s"))
    value = replace(_read(source), evidence=(run.id, "task:x-1"))
    assert writer.add(stored.exposure_event_node(value, title="t")).id == value.id


def test_recorded_by_must_be_the_bound_actor_except_on_import(writer, source):
    value = replace(_read(source), recorded_by="someone-else")
    node = stored.exposure_event_node(value, title="t")
    with pytest.raises(ActorMismatch):
        writer.add(node)
    writer.import_bundle([node], observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert writer.read_view.holds(value.id)


def test_an_undeclared_unit_sort_is_refused(writer, source):
    value = replace(_read(source), units=(TermUnit("mm/cohort", "x"),))
    with pytest.raises(ReservationRefused) as caught:
        writer.add(stored.exposure_event_node(value, title="t"))
    assert caught.value.code == "exposure-unit-sort-undeclared"


def test_an_exposure_event_cannot_be_deleted(writer, source):
    minted = writer.add(stored.exposure_event_node(_read(source), title="t"))
    with pytest.raises(DeletionKindExcluded, match="append-only"):
        writer.delete(minted.id)


def test_revise_changes_prose_only(writer, source):
    value = _read(source)
    minted = writer.add(stored.exposure_event_node(value, title="t"))
    revised = writer.revise(minted.model_copy(update={"body": "more"}))
    assert revised.body == "more"
    changed = stored.exposure_event_node(replace(value, account="other"), title="t").model_copy(
        update={"uid": minted.uid, "id": minted.id}
    )
    with pytest.raises(ReviseOutsideAllowlist):
        writer.revise(changed)


def test_the_same_look_twice_is_one_record(writer, source):
    node = stored.exposure_event_node(_read(source), title="t")
    writer.add(node)
    with pytest.raises(RecordAlreadyMinted):
        writer.add(node)


def test_a_disallowed_world_kind_scheme_in_evidence_is_refused(writer, source):
    node = stored.exposure_event_node(_read(source), title="t").model_copy(deep=True)
    facet = node.facets[stored.EXPOSURE_EVENT_FACET]
    facet["evidence"] = ["assessment:" + _D]
    readdressed = "exposure-event:" + v1.digest(EXPOSURE_EVENT_DOMAIN, facet)
    relations = [Relation(source=readdressed, predicate=r.predicate, target=r.target) for r in node.relations]
    stamped = stored.stamp_semantic_identity(node.model_copy(update={"id": readdressed, "relations": relations}))
    with pytest.raises(MalformedRecord, match="assessment"):
        writer.add(stamped)
