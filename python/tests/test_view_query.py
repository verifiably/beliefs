import pytest
from coordination_fixtures import raw_coordination_node

from beliefs.errors import MalformedRecord, SelectionRefused
from beliefs.view_query import Kinds, parse_view_query, stored_query

A = "a" * 32
C = "c" * 32
D = "d" * 32
KINDS_QUERY = {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": ["dataset"]}]}]}


def test_empty_outer_clauses_are_valid_and_canonical():
    query = parse_view_query({"version": "science.view-query.v1", "clauses": []})
    assert query.projection() == {"version": "science.view-query.v1", "clauses": []}


def test_every_v1_predicate_parses_without_resolving_addresses():
    value = {
        "version": "science.view-query.v1",
        "clauses": [
            {
                "all": [
                    {"kinds": ["dataset", "proposition"]},
                    {"references-term": "biology/gene-1"},
                    {
                        "closure": {
                            "anchor": "dataset:not-yet-held",
                            "predicates": ["reads"],
                            "direction": "both",
                        }
                    },
                    {"addresses": ["proposition:not-yet-held"]},
                ]
            }
        ],
    }
    query = parse_view_query(value)
    assert query.world_kinds() == frozenset({"dataset", "proposition"})
    assert query.relations() == frozenset({"reads"})
    assert query.addresses() == ("dataset:not-yet-held", "proposition:not-yet-held")


def test_reordering_set_like_members_does_not_move_the_canonical_projection():
    first = {
        "version": "science.view-query.v1",
        "clauses": [
            {
                "all": [
                    {"kinds": ["dataset", "proposition"]},
                    {"addresses": ["dataset:b", "dataset:a"]},
                ]
            }
        ],
    }
    second = {
        "version": "science.view-query.v1",
        "clauses": [
            {
                "all": [
                    {"addresses": ["dataset:a", "dataset:b"]},
                    {"kinds": ["proposition", "dataset"]},
                ]
            }
        ],
    }
    assert parse_view_query(first).projection() == parse_view_query(second).projection()


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"version": "science.view-query.v2", "clauses": []},
        {"version": "science.view-query.v1", "clauses": [], "extra": True},
        {"version": "science.view-query.v1", "clauses": [{"all": []}]},
        {"version": "science.view-query.v1", "clauses": [{"any": [{"kinds": ["dataset"]}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"unknown": "x"}]}]},
        {"version": "science.view-query.v1", "clauses": [{"all": [{"kinds": []}]}]},
        {
            "version": "science.view-query.v1",
            "clauses": [
                {
                    "all": [
                        {
                            "closure": {
                                "anchor": "dataset:x",
                                "predicates": [],
                                "direction": "out",
                            }
                        }
                    ]
                }
            ],
        },
        {
            "version": "science.view-query.v1",
            "clauses": [
                {
                    "all": [
                        {
                            "closure": {
                                "anchor": "dataset:x",
                                "predicates": ["reads"],
                                "direction": "sideways",
                            }
                        }
                    ]
                }
            ],
        },
        {
            "version": "science.view-query.v1",
            "clauses": [{"all": [{"addresses": ["coord:" + "a" * 32]}]}],
        },
        {
            "version": "science.view-query.v1",
            "clauses": [{"all": [{"addresses": ["note:x"]}]}],
        },
    ],
)
def test_the_v1_grammar_is_closed(value):
    with pytest.raises(ValueError, match="view query"):
        parse_view_query(value)


def test_stored_query_reads_a_view_revisions_query():
    topic = raw_coordination_node("topic", A, C, local=D, query=KINDS_QUERY)
    query = stored_query(topic)
    assert query.clauses[0].predicates == (Kinds(("dataset",)),)
    assert query.projection() == KINDS_QUERY


def test_stored_query_refuses_a_non_view_kind_and_a_missing_query():
    task = raw_coordination_node("task", A, C, local=D)
    with pytest.raises(MalformedRecord, match="not a view revision"):
        stored_query(task)
    topic = raw_coordination_node("topic", A, C, local=D)
    del topic.facets["coordination"]["query"]
    with pytest.raises(MalformedRecord, match="carries a query"):
        stored_query(topic)


def test_stored_query_reports_a_corrupt_stored_query_as_the_record():
    topic = raw_coordination_node("topic", A, C, local=D, query={"version": "science.view-query.v9", "clauses": []})
    with pytest.raises(MalformedRecord, match=f"{topic.id}: stored view query does not parse"):
        stored_query(topic)


def test_selection_refused_carries_a_closed_reason_and_sorted_references():
    refused = SelectionRefused("address-not-present", refs=["dataset:b", "dataset:a"], corpus_ids=["b" * 32])
    assert (refused.reason, refused.refs, refused.corpus_ids) == (
        "address-not-present",
        ("dataset:a", "dataset:b"),
        ("b" * 32,),
    )
    assert "dataset:a, dataset:b" in str(refused) and ("b" * 32) in str(refused)
    with pytest.raises(ValueError, match="not a selection refusal reason"):
        SelectionRefused("absent", refs=["x"])
