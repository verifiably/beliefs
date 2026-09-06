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


def test_equal_routes_retain_one_canonical_mapping_independent_of_operand_order():
    composed = {
        "identity": "route:cafe\u0301",
        "run": "run:cafe\u0301",
        "ancestor": "dataset:cafe\u0301",
        "transforms": ["dataset:cafe\u0301"],
    }
    canonical = {
        "ancestor": "dataset:café",
        "identity": "route:café",
        "run": "run:café",
        "transforms": ["dataset:café"],
    }
    first = _dataset("same", {"tag": "single", "routes": [composed]})
    second = _dataset("same", {"routes": [canonical], "tag": "single"})

    forward = stored.union_lineage_bases(first, second)
    reverse = stored.union_lineage_bases(second, first)

    assert forward == reverse
    assert forward[stored.LINEAGE_BASIS_FACET] == {
        "tag": "single",
        "routes": [canonical],
    }
    assert list(forward[stored.LINEAGE_BASIS_FACET]["routes"][0]) == [
        "ancestor",
        "identity",
        "run",
        "transforms",
    ]


# --- V2: the one place a kind prefix is added or removed (design §3.1) --------
from beliefs.runrecord import run_ref
from beliefs.stored import local_id, typed_ref


def test_v2_typed_ref_and_local_id_are_inverse_and_agree_with_run_ref():
    address = "a" * 64
    assert typed_ref("run", address) == run_ref(address) == f"run:{address}"
    assert local_id("run", f"run:{address}") == address
    assert typed_ref("assessment", "a1") == "assessment:a1"
    assert local_id("verification", "verification:v-1") == "v-1"


@pytest.mark.parametrize(
    "call",
    [
        lambda: typed_ref("run", "run:abc"),
        lambda: typed_ref("run", ""),
        lambda: typed_ref("not-a-kind", "abc"),
        lambda: local_id("run", "abc"),
        lambda: local_id("run", "run:"),
        lambda: local_id("run", "assessment:abc"),
        lambda: local_id("run", None),  # type: ignore[arg-type]
    ],
)
def test_v2_the_helper_pair_refuses_the_wrong_shape(call):
    with pytest.raises(MalformedRecord):
        call()


def test_v2_assessment_value_hands_back_the_bare_run_and_refuses_an_untyped_one():
    from beliefs import stored

    node = stored.assessment_node(
        "a1", title="a1", spec="s", run="run:r1", proposition="proposition:p", outcome="supported",
        interpretation_rule="rule-1",
    )
    assert stored.assessment_value(node).run == "r1"
    node.facets[stored.ASSESSMENT_FACET]["run"] = "r1"
    with pytest.raises(MalformedRecord):
        stored.assessment_value(node)
    del node.facets[stored.ASSESSMENT_FACET]["run"]
    with pytest.raises(MalformedRecord):
        stored.assessment_value(node)
