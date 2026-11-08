"""Readers and constructors of exposure-event and reservation-assignment records."""

from __future__ import annotations

import copy

import pytest
from test_reservation import _mm_unmask_event, _sun_assignment_17, _sun_knowledge_event

from beliefs import stored
from beliefs.errors import MalformedRecord


def test_exposure_event_node_mirrors_every_kernel_reference_as_an_edge():
    node = stored.exposure_event_node(_mm_unmask_event(), title="t")
    assert [(r.predicate, r.target) for r in node.relations] == [("exposes", "source:" + "1" * 64)]
    assert stored.exposure_event_value(node) == _mm_unmask_event()


def test_the_node_carries_the_body():
    assert stored.exposure_event_node(_sun_knowledge_event(), title="t", body="b").body == "b"


def test_a_reader_refuses_an_id_that_does_not_recompute():
    node = stored.exposure_event_node(_mm_unmask_event(), title="t").model_copy(
        update={"id": "exposure-event:" + "0" * 64}
    )
    with pytest.raises(MalformedRecord, match="address"):
        stored.exposure_event_value(node)


def test_assignment_node_writes_considers_edges_and_never_supersedes():
    value = _sun_assignment_17()
    node = stored.reservation_assignment_node(value, title="t")
    predicates = {r.predicate for r in node.relations}
    assert predicates <= {"considers", "evidenced-by", "flags", "reports", "concerns", "applies"}
    assert "considers" in predicates and "supersedes" not in predicates
    assert stored.reservation_assignment_value(node) == value


def test_a_facet_that_does_not_round_trip_is_malformed():
    node = stored.exposure_event_node(_mm_unmask_event(), title="t")
    facets = copy.deepcopy(node.facets)
    facets[stored.EXPOSURE_EVENT_FACET]["extra"] = 1
    with pytest.raises(MalformedRecord, match=node.id):
        stored.exposure_event_value(node.model_copy(update={"facets": facets}))


def test_a_present_but_empty_optional_key_is_refused_not_tidied():
    node = stored.exposure_event_node(_sun_knowledge_event(), title="t")
    assert "bound" not in node.facets[stored.EXPOSURE_EVENT_FACET]
    facets = copy.deepcopy(node.facets)
    facets[stored.EXPOSURE_EVENT_FACET]["bound"] = {}
    with pytest.raises(MalformedRecord, match=node.id):
        stored.exposure_event_value(node.model_copy(update={"facets": facets}))


def test_a_missing_facet_is_malformed():
    node = stored.exposure_event_node(_mm_unmask_event(), title="t").model_copy(update={"facets": {}})
    with pytest.raises(MalformedRecord, match="facet"):
        stored.exposure_event_value(node)
    anode = stored.reservation_assignment_node(_sun_assignment_17(), title="t").model_copy(update={"facets": {}})
    with pytest.raises(MalformedRecord, match="facet"):
        stored.reservation_assignment_value(anode)
