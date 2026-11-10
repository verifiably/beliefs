"""Classification rules retain normative prose and optional provenance."""

from dataclasses import replace

import pytest
from test_procedure import DIGEST, OBS, node_for

from beliefs.classification_rule import ClassificationRule, rule_from_stored, rule_identity, rule_projection
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.procedure import External, Implementation


def rule(**changes):
    return ClassificationRule(
        **(
            {
                "classes": "testing/class",
                "reads": (OBS,),
                "definition": "Width is 360 degrees",
                "external": None,
                "implementation": None,
                "annotator": None,
            }
            | changes
        )
    )


def test_identity_is_content_addressed():
    value = rule()
    assert rule_identity(value) == rule_identity(rule())
    assert rule_identity(value) == "classification-rule:" + v1.digest(
        "science.classification-rule.v1", rule_projection(value)
    )
    assert rule_identity(value) != rule_identity(replace(value, definition="Other"))


@pytest.mark.parametrize(
    "extras",
    [
        {},
        {
            "external": External("uri", "contextual"),
            "implementation": Implementation("code", DIGEST),
            "annotator": "team",
        },
    ],
)
def test_projection_has_no_nulls_and_round_trips(extras):
    value = rule(**extras)
    facet = rule_projection(value)
    v1.encode(facet)
    assert rule_from_stored(node_for("classification-rule", rule_identity(value), facet)) == value


def test_from_stored_refuses_a_non_canonical_facet_and_a_wrong_id():
    value = rule()
    facet = rule_projection(value)
    for bad in (facet | {"annotator": None}, facet | {"extra": "x"}, facet | {"reads": [{"bad": "value"}]}):
        with pytest.raises(MalformedRecord):
            rule_from_stored(node_for("classification-rule", rule_identity(value), bad))
    with pytest.raises(MalformedRecord):
        rule_from_stored(node_for("classification-rule", "classification-rule:" + "a" * 64, facet))


@pytest.mark.parametrize(
    "changes",
    [
        {"classes": "bad"},
        {"reads": ("bad",)},
        {"definition": ""},
        {"annotator": 1},
        {"external": {}},
        {"implementation": {}},
    ],
)
def test_field_grammar(changes):
    with pytest.raises(MalformedRecord):
        rule(**changes)
