"""Referent mappings establish typed correspondence without applying it."""

from dataclasses import replace
from typing import cast

import pytest
from test_procedure import DIGEST, node_for

from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.referent_mapping import ReferentMapping, mapping_from_stored, mapping_identity, mapping_projection


def mapping(**changes):
    return ReferentMapping(
        **(
            {
                "source_sort": "testing/transcript",
                "target_sort": "testing/gene",
                "reference": {"name": "annotation", "release": "1"},
                "cardinality": "many-to-one",
                "aggregation": None,
                "members": None,
            }
            | changes
        )
    )


def test_identity_is_content_addressed():
    value = mapping()
    assert mapping_identity(value) == mapping_identity(mapping())
    assert mapping_identity(value) == "referent-mapping:" + v1.digest(
        "science.referent-mapping.v1", mapping_projection(value)
    )
    assert mapping_identity(value) != mapping_identity(replace(value, cardinality="one-to-one"))


@pytest.mark.parametrize("extras", [{}, {"aggregation": "testing/sum", "members": DIGEST}])
def test_projection_has_no_nulls_and_round_trips(extras):
    value = mapping(**extras)
    facet = mapping_projection(value)
    v1.encode(facet)
    assert mapping_from_stored(node_for("referent-mapping", mapping_identity(value), facet)) == value
    with pytest.raises(TypeError):
        cast(dict[str, str], value.reference)["x"] = "1"


def test_from_stored_refuses_a_non_canonical_facet_and_a_wrong_id():
    value = mapping()
    facet = mapping_projection(value)
    for bad in (facet | {"members": None}, facet | {"extra": "x"}, facet | {"reference": {"name": 2}}):
        with pytest.raises(MalformedRecord):
            mapping_from_stored(node_for("referent-mapping", mapping_identity(value), bad))
    with pytest.raises(MalformedRecord):
        mapping_from_stored(node_for("referent-mapping", "referent-mapping:" + "a" * 64, facet))


@pytest.mark.parametrize(
    "changes",
    [
        {"source_sort": "bad"},
        {"target_sort": "bad"},
        {"cardinality": "many"},
        {"reference": {"name": 1}},
        {"aggregation": "sum"},
        {"members": "sha256:abc"},
    ],
)
def test_field_grammar(changes):
    with pytest.raises(MalformedRecord):
        mapping(**changes)


def test_joins_either_direction():
    assert mapping().joins("testing/transcript", "testing/gene")
    assert mapping().joins("testing/gene", "testing/transcript")
    assert not mapping().joins("testing/transcript", "testing/protein")
