"""Publication records (publication-records design §3–§4, decisions 5 and 6; row Y2)."""

import pytest
from nodes.core.frontmatter import node_to_markdown
from test_publish_intent import intent

from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.errors import MalformedRecord
from beliefs.intents.publish import Destination
from beliefs.publication import (
    binding_address,
    binding_record,
    marker_address,
    marker_consistent,
    marker_record,
    publication_content_malformed,
)

VIEW = CoordinationAddress("a" * 32, "b" * 32)
HERE = Destination.local("/srv/published/mm30")
PINNED_ELSEWHERE = "coord:" + "c" * 32 + "/" + "d" * 32 + "@" + "e" * 32


def test_the_two_addresses_differ_and_share_the_project():
    binding, marker = binding_address(VIEW, HERE), marker_address(VIEW, HERE)
    assert binding != marker and binding.project == marker.project == VIEW.project


def test_two_spellings_of_one_directory_are_one_address():
    assert binding_address(VIEW, Destination.local("/srv/published/./mm30")) == binding_address(VIEW, HERE)


def test_a_project_view_has_addresses_too():
    assert binding_address(CoordinationAddress("a" * 32), HERE).local is not None


def test_both_records_are_byte_functions_of_their_inputs():
    value = intent()
    first = binding_record(value, corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64)
    second = binding_record(value, corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64)
    assert node_to_markdown(first) == node_to_markdown(second)
    facet = first.facets["coordination"]
    assert coordination_revision(first).predecessors == tuple(
        f"publication-binding:{facet['project']}.{facet['local']}.{tip}" for tip in value.binding_tips
    )
    marker = marker_record(value, world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1", "proposition:p2"))
    assert node_to_markdown(marker) == node_to_markdown(
        marker_record(value, world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1", "proposition:p2"))
    )
    assert marker.relations == []
    assert not publication_content_malformed(marker) and not publication_content_malformed(first)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda n: n.facets["coordination"].__setitem__("event_token", "0" * 32),
        lambda n: n.facets["coordination"].__setitem__("destination", {"type": "local", "locator": "/elsewhere"}),
        lambda n: n.facets["coordination"]["published_from"].__setitem__("view", PINNED_ELSEWHERE),
    ],
    ids=["token", "destination", "view"],
)
def test_marker_consistency_is_self_contained(mutate):
    marker = marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1",))
    assert marker_consistent(marker)
    mutate(marker)
    assert not marker_consistent(marker)


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", "other"),
        ("body", "text"),
        ("event_token", "short"),
        ("corpus_id", "x"),
        ("marker", "x"),
        ("artifact", "x"),
        ("view", "coord:" + "a" * 32),
        ("destination", {"type": "local", "locator": "rel"}),
    ],
)
def test_every_binding_field_rule_refuses(field, value):
    node = binding_record(intent(), corpus_id="e" * 32, marker="f" * 32, artifact="9" * 64)
    if field in {"name", "body"}:
        node = node.model_copy(update={"title" if field == "name" else "body": value})
    else:
        node.facets["coordination"][field] = value
    assert publication_content_malformed(node)


@pytest.mark.parametrize("selection", [[{}], ["proposition:p1", 1]], ids=["mapping-member", "mixed-str-int"])
def test_malformed_selection_members_are_malformed_not_type_errors(selection):
    """User review 2: `_selection` validates each member before comparing orders."""
    marker = marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1",))
    marker.facets["coordination"]["selection"] = selection
    assert publication_content_malformed(marker)


@pytest.mark.parametrize(
    "pairs", [[{}], [["e" * 32, "f" * 32], ["a" * 32, 1]]], ids=["mapping-member", "mixed-str-int"]
)
def test_malformed_supersedes_markers_are_malformed_not_type_errors(pairs):
    marker = marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1",))
    marker.facets["coordination"]["supersedes_markers"] = pairs
    assert publication_content_malformed(marker)


def test_an_invalid_record_id_is_refused_by_the_factory_the_rule_and_the_check():
    """User review, finding 4: `selection` members are world record ids, not any sorted strings."""
    with pytest.raises(MalformedRecord):
        marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("not a record id",))
    with pytest.raises(MalformedRecord):  # a coordination kind is not a world record
        marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("task:" + "a" * 32,))
    marker = marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1",))
    marker.facets["coordination"]["selection"] = ["not a record id"]
    assert publication_content_malformed(marker) and not marker_consistent(marker)


@pytest.mark.parametrize(
    "field, value",
    [
        ("selection", []),
        ("selection", ["proposition:b", "proposition:a"]),
        ("selection", ["b"]),
        ("supersedes_markers", [["b" * 32, "c" * 32], ["a" * 32, "c" * 32]]),
        ("published_from", {"world_id": "7" * 32}),
    ],
)
def test_every_marker_field_rule_refuses(field, value):
    node = marker_record(intent(), world_id="7" * 32, epoch="6" * 64, selection=("proposition:p1",))
    node.facets["coordination"][field] = value
    assert publication_content_malformed(node)
