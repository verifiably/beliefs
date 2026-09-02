import pytest

from beliefs.view_query import parse_view_query


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
