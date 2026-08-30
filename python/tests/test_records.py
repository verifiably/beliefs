"""Record values: the closed relation signatures, and the facet's digests.

G1's refusal half lives here: an `assesses` edge from a source-assertion is
refused **in the typed constructor** — the slice has no other authoring surface
to refuse at (cut 2 §4.1). The value/digest halves are `test_belief.py`'s.
"""

import pytest

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
        assert assessment().identity() == assessment(estimate="0.4").identity()
        assert assessment().identity() != assessment(run="run-2").identity()

    @pytest.mark.parametrize("field", ["estimate", "uncertainty", "estimand", "applicability"])
    def test_each_optional_field_moves_the_facet_digest(self, field):
        assert assessment().facet_digest() != assessment(**{field: "x"}).facet_digest()

    def test_absent_and_empty_differ(self):
        assert assessment().facet_digest() != assessment(estimate="").facet_digest()

    def test_the_outcome_moves_it_too(self):
        assert assessment().facet_digest() != assessment(outcome="refuted").facet_digest()


class TestARunIsAValueNotABoundary:
    def test_a_run_holds_role_typed_inputs(self):
        dataset = DatasetDeclaration(resources=(ResourceDeclaration(name="r", digest=D1),))
        run = RunValue(ref="run-1", spec="spec-1", inputs=(RunInput(role="observes", dataset=dataset),))
        assert run.inputs[0].role == "observes"
