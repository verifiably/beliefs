from __future__ import annotations

import pytest

from beliefs import stored
from beliefs.errors import MalformedRecord

PINNED = [{"name": "data", "digest": "sha256:" + "ab" * 32}]


def _dataset(slug: str, basis=None):
    return stored.dataset_node(slug, title=slug, resources=PINNED, basis=basis)


def _route(identity: str) -> dict[str, object]:
    return {
        "identity": identity,
        "run": f"run:{identity}",
        "ancestor": f"dataset:{identity}",
        "transforms": [f"dataset:{identity}"],
    }


def test_union_lineage_bases_keeps_a_single_tag_for_equal_bases():
    basis = {"tag": "single", "routes": [_route("a")]}

    facets = stored.union_lineage_bases(_dataset("kept", basis), _dataset("other", basis))

    assert facets[stored.LINEAGE_BASIS_FACET] == basis


def test_union_lineage_bases_makes_a_sorted_conflict_for_differing_routes():
    facets = stored.union_lineage_bases(
        _dataset("kept", {"tag": "single", "routes": [_route("z")]}),
        _dataset("other", {"tag": "single", "routes": [_route("a")]}),
    )

    assert facets[stored.LINEAGE_BASIS_FACET] == {
        "tag": "conflict",
        "routes": [_route("a"), _route("z")],
    }


def test_union_lineage_bases_unions_two_conflicts():
    facets = stored.union_lineage_bases(
        _dataset(
            "kept",
            {"tag": "conflict", "routes": [_route("a"), _route("c")]},
        ),
        _dataset(
            "other",
            {"tag": "conflict", "routes": [_route("b"), _route("c")]},
        ),
    )

    assert facets[stored.LINEAGE_BASIS_FACET] == {
        "tag": "conflict",
        "routes": [_route("a"), _route("b"), _route("c")],
    }


def test_a_conflict_with_fewer_than_two_routes_is_unconstructible():
    malformed = _dataset(
        "other", {"tag": "conflict", "routes": [_route("only")]}
    )

    with pytest.raises(MalformedRecord, match="conflict"):
        stored.union_lineage_bases(_dataset("kept"), malformed)
