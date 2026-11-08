"""Readers and constructors of exposure-event and reservation-assignment records."""

from __future__ import annotations

import copy

import pytest
from test_reservation import _assignment, _event, _mm_unmask_event, _sun_assignment_17, _sun_knowledge_event

from beliefs import stored
from beliefs.errors import MalformedRecord


def test_exposure_event_node_mirrors_every_kernel_reference_as_an_edge():
    value = _event(
        subjects=("dataset:" + "1" * 64, "source:" + "2" * 64),
        propositions=("proposition:" + "3" * 64,),
        evidence=("act-report:" + "4" * 64, "holdings-observation:" + "5" * 64, "run:" + "6" * 64, "task:sun-1"),
    )
    node = stored.exposure_event_node(value, title="t")
    assert [(r.predicate, r.target) for r in node.relations] == [
        ("exposes", "dataset:" + "1" * 64),
        ("exposes", "source:" + "2" * 64),
        ("concerns", "proposition:" + "3" * 64),
        ("attested-by", "act-report:" + "4" * 64),
        ("attested-by", "holdings-observation:" + "5" * 64),
        ("attested-by", "run:" + "6" * 64),
    ]
    assert stored.SEMANTIC_IDENTITY_FACET in node.facets
    assert not stored.semantic_hash_missing(node) and not stored.semantic_hash_disagrees(node)
    assert stored.exposure_event_value(node) == value


def test_the_node_carries_the_body():
    assert stored.exposure_event_node(_sun_knowledge_event(), title="t", body="b").body == "b"
    assert stored.reservation_assignment_node(_sun_assignment_17(), title="t", body="b").body == "b"


def test_a_reader_refuses_an_id_that_does_not_recompute():
    node = stored.exposure_event_node(_mm_unmask_event(), title="t").model_copy(
        update={"id": "exposure-event:" + "0" * 64}
    )
    with pytest.raises(MalformedRecord, match="address"):
        stored.exposure_event_value(node)
    anode = stored.reservation_assignment_node(_sun_assignment_17(), title="t").model_copy(
        update={"id": "reservation-assignment:" + "0" * 64}
    )
    with pytest.raises(MalformedRecord, match="address"):
        stored.reservation_assignment_value(anode)


def test_assignment_node_writes_every_kernel_edge_in_slot_order_and_never_supersedes():
    value = _assignment(
        events=("exposure-event:" + "1" * 64,),
        scope="proposition:" + "2" * 64,
        applies="reservation-assignment:" + "3" * 64,
        predecessor="reservation-assignment:" + "4" * 64,
        evidence=("exposure-event:" + "5" * 64, "task:sun-1"),
        flagged=("assessment:" + "6" * 64,),
        prior_runs=("commit:abc", "run:" + "7" * 64),
    )
    node = stored.reservation_assignment_node(value, title="t")
    assert [(r.predicate, r.target) for r in node.relations] == [
        ("considers", "exposure-event:" + "1" * 64),
        ("evidenced-by", "exposure-event:" + "5" * 64),
        ("flags", "assessment:" + "6" * 64),
        ("reports", "run:" + "7" * 64),
        ("concerns", "proposition:" + "2" * 64),
        ("applies", "reservation-assignment:" + "3" * 64),
    ]
    assert stored.SEMANTIC_IDENTITY_FACET in node.facets
    assert not stored.semantic_hash_missing(node) and not stored.semantic_hash_disagrees(node)
    assert stored.reservation_assignment_value(node) == value


def test_a_facet_that_does_not_round_trip_is_malformed():
    node = stored.exposure_event_node(_mm_unmask_event(), title="t")
    facets = copy.deepcopy(node.facets)
    facets[stored.EXPOSURE_EVENT_FACET]["extra"] = 1
    with pytest.raises(MalformedRecord, match=node.id):
        stored.exposure_event_value(node.model_copy(update={"facets": facets}))
    anode = stored.reservation_assignment_node(_sun_assignment_17(), title="t")
    afacets = copy.deepcopy(anode.facets)
    afacets[stored.RESERVATION_ASSIGNMENT_FACET]["extra"] = 1
    with pytest.raises(MalformedRecord, match=anode.id):
        stored.reservation_assignment_value(anode.model_copy(update={"facets": afacets}))


def test_a_present_but_empty_optional_key_is_refused_not_tidied():
    node = stored.exposure_event_node(_sun_knowledge_event(), title="t")
    assert "bound" not in node.facets[stored.EXPOSURE_EVENT_FACET]
    facets = copy.deepcopy(node.facets)
    facets[stored.EXPOSURE_EVENT_FACET]["bound"] = {}
    with pytest.raises(MalformedRecord, match=node.id):
        stored.exposure_event_value(node.model_copy(update={"facets": facets}))
    anode = stored.reservation_assignment_node(_sun_assignment_17(), title="t")
    assert "evidence" not in anode.facets[stored.RESERVATION_ASSIGNMENT_FACET]
    afacets = copy.deepcopy(anode.facets)
    afacets[stored.RESERVATION_ASSIGNMENT_FACET]["evidence"] = []
    with pytest.raises(MalformedRecord, match=anode.id):
        stored.reservation_assignment_value(anode.model_copy(update={"facets": afacets}))


def test_a_missing_facet_is_malformed():
    node = stored.exposure_event_node(_mm_unmask_event(), title="t").model_copy(update={"facets": {}})
    with pytest.raises(MalformedRecord, match=stored.EXPOSURE_EVENT_FACET):
        stored.exposure_event_value(node)
    anode = stored.reservation_assignment_node(_sun_assignment_17(), title="t").model_copy(update={"facets": {}})
    with pytest.raises(MalformedRecord, match=stored.RESERVATION_ASSIGNMENT_FACET):
        stored.reservation_assignment_value(anode)
