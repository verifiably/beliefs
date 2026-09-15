"""Record values: the closed relation signatures, and the facet's digests.

G1's refusal half lives here: an `assesses` edge from a source-assertion is
refused **in the typed constructor** — the slice has no other authoring surface
to refuse at (cut 2 §4.1). The value/digest halves are `test_belief.py`'s.
"""

import pytest
from fixtures_cut3 import typed_applicability, typed_estimand

from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
from beliefs.errors import MalformedRecord, SignatureRefused
from beliefs.record import (
    AssessmentValue,
    RunInput,
    RunValue,
    SourceAssertion,
)

D1 = "sha256:" + "11" * 32


def assessment(**overrides) -> AssessmentValue:
    fields = {
        "spec": "spec-1",
        "run": "run-1",
        "proposition": "prop-1",
        "outcome": "supported",
        "interpretation_rule": "rule-1",
        "estimand": typed_estimand(),
        "applicability": typed_applicability(),
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
        # Verification state is never an outcome (kernel §4.2.1's facet table).
        with pytest.raises(MalformedRecord):
            assessment(outcome="verified")


class TestTheFacetDigest:
    def test_identity_is_spec_run_proposition(self):
        from decimal import Decimal

        assert assessment().identity() == assessment(estimate=Decimal("0.4")).identity()
        assert assessment().identity() != assessment(run="run-2").identity()

    def test_each_typed_member_moves_the_facet_digest(self):
        from decimal import Decimal

        from fixtures_cut3 import typed_applicability, typed_estimand

        from beliefs.claim import Qualifier, Referent
        from beliefs.estimand import Interval, StandardError

        base = assessment()
        assert base.facet_digest() != assessment(estimate=Decimal("0.4")).facet_digest()
        assert assessment(estimate=Decimal("0.4")).facet_digest() != assessment(estimate=Decimal("0.4"), uncertainty=Interval(Decimal("0.1"), Decimal("0.7"), Decimal("0.95"))).facet_digest()
        assert assessment(estimate=Decimal("0.4"), uncertainty=StandardError(Decimal("0.1"))).facet_digest() != assessment(estimate=Decimal("0.4")).facet_digest()
        assert base.facet_digest() != assessment(estimand=typed_estimand(reference=Decimal(1))).facet_digest()
        adults = typed_applicability({"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))})
        assert base.facet_digest() != assessment(applicability=adults).facet_digest()

    def test_typed_projection_carries_estimand_and_applicability_always_and_the_optionals_only_when_present(self):
        from decimal import Decimal

        from beliefs.estimand import StandardError

        assert set(assessment().typed_projection()) == {"estimand", "applicability"}
        assert set(assessment(estimate=Decimal("0.4")).typed_projection()) == {"estimand", "applicability", "estimate"}
        assert set(
            assessment(estimate=Decimal("0.4"), uncertainty=StandardError(Decimal("0.1"))).typed_projection()
        ) == {"estimand", "applicability", "estimate", "uncertainty"}

    def test_a_string_member_is_refused(self):
        with pytest.raises(MalformedRecord):
            assessment(estimate="0.4")
        with pytest.raises(MalformedRecord):
            assessment(estimand="the effect of x on y")

    def test_the_numerical_invariants_hold_at_construction(self):
        from decimal import Decimal

        from beliefs.estimand import Interval, StandardError

        with pytest.raises(MalformedRecord, match="non-negative"):
            assessment(estimate=Decimal("0.4"), uncertainty=StandardError(Decimal("-0.1")))
        with pytest.raises(MalformedRecord, match="excludes"):
            assessment(estimate=Decimal("0.4"), uncertainty=Interval(Decimal("0.5"), Decimal("0.7"), Decimal("0.95")))
        with pytest.raises(MalformedRecord, match="no estimate"):
            assessment(uncertainty=StandardError(Decimal("0.1")))

    def test_the_outcome_moves_it_too(self):
        assert assessment().facet_digest() != assessment(outcome="refuted").facet_digest()


class TestTheStoredReaderRefusesWhatTheConstructorWould:
    """`stored.assessment_value` decodes the `typed` member and constructs an
    `AssessmentValue` through the ordinary constructor — so a stored record
    cannot carry a negative standard error or a prose estimand any more than
    a derived one can (estimand-typing §6, decision 10)."""

    def test_a_negative_stored_standard_error_reads_as_malformed_never_a_value(self):
        from decimal import Decimal
        from typing import cast

        from fixtures_cut3 import TESTING_PROFILE

        from beliefs import stored
        from beliefs.identity import v1

        node = stored.assessment_node(
            "a1", title="a1", spec="spec-1", run="run:run-1", proposition="prop-1",
            outcome="supported", interpretation_rule="rule-1",
            estimand=typed_estimand(), applicability=typed_applicability(), estimate=Decimal("0.4"),
        )
        typed = cast(dict, v1.decode(node.facets[stored.ASSESSMENT_FACET]["typed"].encode("utf-8")))
        typed["uncertainty"] = {"kind": "standard-error", "value": Decimal("-0.1")}
        node.facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(typed).decode("utf-8")
        with pytest.raises(MalformedRecord, match="non-negative"):
            stored.assessment_value(node, profile=TESTING_PROFILE)

    def test_an_unrecognized_stored_uncertainty_kind_reads_as_malformed_never_a_value(self):
        from decimal import Decimal
        from typing import cast

        from fixtures_cut3 import TESTING_PROFILE

        from beliefs import stored
        from beliefs.identity import v1

        # The shared decoder's shape refusal (`estimand.uncertainty_from_mapping`)
        # translates to `MalformedRecord` here, exactly as the negative standard
        # error above does — the same `UncertaintyRefused`, two call sites, one
        # decoder (the concern `uncertainty_from_mapping` exists to close).
        node = stored.assessment_node(
            "a1", title="a1", spec="spec-1", run="run:run-1", proposition="prop-1",
            outcome="supported", interpretation_rule="rule-1",
            estimand=typed_estimand(), applicability=typed_applicability(), estimate=Decimal("0.4"),
        )
        typed = cast(dict, v1.decode(node.facets[stored.ASSESSMENT_FACET]["typed"].encode("utf-8")))
        typed["uncertainty"] = {"kind": "confidence-band", "value": Decimal("0.1")}
        node.facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(typed).decode("utf-8")
        with pytest.raises(MalformedRecord, match="neither interval nor standard-error"):
            stored.assessment_value(node, profile=TESTING_PROFILE)

    def test_a_pre_grammar_facet_is_refused_by_name_never_coerced(self):
        from fixtures_cut3 import TESTING_PROFILE

        from beliefs import stored
        from beliefs.errors import PreGrammarAssessment

        node = stored.assessment_node(
            "a1", title="a1", spec="spec-1", run="run:run-1", proposition="prop-1",
            outcome="supported", interpretation_rule="rule-1",
            estimand=typed_estimand(), applicability=typed_applicability(),
        )
        del node.facets[stored.ASSESSMENT_FACET]["typed"]
        node.facets[stored.ASSESSMENT_FACET]["estimand"] = "the effect of x on y"
        with pytest.raises(PreGrammarAssessment):
            stored.assessment_value(node, profile=TESTING_PROFILE)


class TestARunIsAValueNotABoundary:
    def test_a_run_holds_role_typed_inputs(self):
        dataset = DatasetDeclaration(resources=(ResourceDeclaration(name="r", digest=D1),))
        run = RunValue(ref="run-1", spec="spec-1", inputs=(RunInput(role="observes", dataset=dataset),))
        assert run.inputs[0].role == "observes"
