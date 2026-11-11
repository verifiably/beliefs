"""Record values: the closed relation signatures, and the facet's digests.

The refusal half lives here: an `assesses` edge from a source-assertion is
refused **in the typed constructor** — the slice has no other authoring surface
to refuse at. The value/digest halves are `test_belief.py`'s.
"""

from decimal import Decimal
from fractions import Fraction
from typing import cast

import pytest
from fixtures_cut3 import TESTING_PROFILE, typed_applicability, typed_estimand, typed_target

from beliefs import stored
from beliefs.applicability import ScopedRestriction
from beliefs.assessment_payload import Interval, StandardError
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
from beliefs.errors import MalformedRecord, PreGrammarAssessment, SignatureRefused
from beliefs.estimand import ValueReference
from beliefs.identity import v1
from beliefs.record import (
    AssessmentValue,
    RunInput,
    SourceAssertion,
)
from beliefs.restriction import IntervalRestriction

D1 = "sha256:" + "11" * 32


def assessment(**overrides) -> AssessmentValue:
    fields = {
        "spec": "spec-1",
        "run": "run-1",
        "proposition": "prop-1",
        "outcome": "supported",
        "interpretation_rule": "rule-1",
        "target": typed_target(),
    }
    fields.update(overrides)
    return AssessmentValue(**fields)


class TestClosedSignatures:
    def test_an_assesses_edge_from_a_source_assertion_is_refused(self):
        with pytest.raises(SignatureRefused):
            SourceAssertion(ref="s1", relation="assesses", proposition="prop-1", payload={})

    @pytest.mark.parametrize("relation", ["asserts", "denies", "hypothesizes"])
    def test_the_three_declared_relations_construct(self, relation):
        SourceAssertion(ref="s1", relation=relation, proposition="prop-1", payload={"quote": "…"})

    def test_a_run_input_role_outside_the_set_is_refused(self):
        dataset = DatasetDeclaration(resources=(ResourceDeclaration(name="r", digest=D1),))
        with pytest.raises(MalformedRecord):
            RunInput(role="consumes", dataset=dataset)

    def test_an_outcome_outside_the_set_is_refused(self):
        # Verification state is never an outcome.
        with pytest.raises(MalformedRecord):
            assessment(outcome="verified")


class TestTheFacetDigest:
    def test_identity_is_spec_run_proposition(self):
        assert assessment().identity() == assessment(estimates={"estimate": Decimal(".4")}).identity()
        assert assessment().identity() != assessment(run="run-2").identity()

    def test_every_typed_member_moves_the_digest(self):
        original = assessment()
        numerical = assessment(estimates={"estimate": Decimal(".4")})
        assert original.facet_digest() != numerical.facet_digest()
        assert (
            numerical.facet_digest()
            != assessment(
                estimates={"estimate": Decimal(".4")},
                uncertainty={"estimate": Interval(Decimal(0), Decimal(1), Decimal(".95"))},
            ).facet_digest()
        )
        assert (
            original.facet_digest()
            != assessment(
                target=typed_target(estimand=typed_estimand(reference=ValueReference(Decimal(1))))
            ).facet_digest()
        )
        scope = typed_applicability(
            {
                "testing/follow-up": ScopedRestriction(
                    "generic", IntervalRestriction("testing/hour", Fraction(1), None, True, False)
                )
            }
        )
        assert original.facet_digest() != assessment(target=typed_target(applicability=scope)).facet_digest()
        assert original.facet_digest() != assessment(outcome="refuted").facet_digest()

    def test_typed_projection_keeps_the_frozen_set_and_absent_payload(self):
        assert set(assessment().typed_projection()) == {"estimand", "applicability", "dependencies"}
        assert set(assessment(estimates={"estimate": Decimal(".4")}).typed_projection()) == {
            "estimand",
            "applicability",
            "dependencies",
            "estimates",
        }

    def test_constructor_refuses_untyped_target_and_numbers(self):
        with pytest.raises(MalformedRecord):
            assessment(target="prose")
        with pytest.raises(MalformedRecord):
            assessment(estimates={"estimate": ".4"})
        with pytest.raises(MalformedRecord):
            assessment(
                estimates={"estimate": Decimal(".4")},
                uncertainty={"estimate": Interval(Decimal(".5"), Decimal(".7"), Decimal(".95"))},
            )
        with pytest.raises(MalformedRecord):
            assessment(uncertainty={"estimate": StandardError(Decimal(".1"))})


def node():
    return stored.assessment_node(
        "a1",
        title="Assessment",
        spec="spec-1",
        run="run:run-1",
        proposition="prop-1",
        outcome="supported",
        interpretation_rule="rule-1",
        target=typed_target(),
        estimates={"estimate": Decimal(".4")},
    )


def test_stored_v2_roundtrip():
    value = stored.assessment_value(node(), profile=TESTING_PROFILE)
    assert value.target == typed_target() and value.estimates == {"estimate": Decimal(".4")}
    assert value.standing == "empirical"


@pytest.mark.parametrize(
    "uncertainty",
    [
        {"estimate": {"kind": "standard-error", "value": Decimal("-.1")}},
        {"estimate": {"kind": "unknown", "value": Decimal(".1")}},
        {"estimate": {"kind": "interval", "low": Decimal(".5"), "high": Decimal(".7"), "level": Decimal(".95")}},
    ],
)
def test_stored_reader_refuses_invalid_numerical_payload(uncertainty):
    value = node()
    typed = cast(dict, v1.decode(value.facets[stored.ASSESSMENT_FACET]["typed"].encode()))
    typed["uncertainty"] = uncertainty
    value.facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(typed).decode()
    with pytest.raises(MalformedRecord):
        stored.assessment_value(value, profile=TESTING_PROFILE)


def test_pre_grammar_facet_refuses_by_name():
    value = node()
    del value.facets[stored.ASSESSMENT_FACET]["standing"]
    with pytest.raises(PreGrammarAssessment):
        stored.assessment_value(value, profile=TESTING_PROFILE)
