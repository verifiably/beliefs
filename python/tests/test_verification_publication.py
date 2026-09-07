"""V3 (design §8): admission is evaluated over records read back, and the
belief moves with the verification record. V7's gather arm sits in
`test_evaluation.py` beside the gather fixture; nothing here is imported
back into `test_evaluation`."""

from __future__ import annotations

import pytest
from test_audit import writer  # noqa: F401 - the fixture
from test_evaluation import CLAIM_FACET, OTHER_GENE, PHENO
from verification_fixtures import admission_over, evaluation_kwargs, publish_corpus

from beliefs import stored
from beliefs.belief import Belief, NoBelief, Refused
from beliefs.evaluation import gather
from beliefs.runrecord import run_ref
from beliefs.verification import INVALIDATED, active, lifecycle_state
from beliefs.verify import _mint_verification, publication_node


def _gathered(writer, proposition_ref):  # noqa: F811 - the imported fixture, used here by parameter name
    view = writer.read_view
    return gather(view, proposition_ref, **{k: v for k, v in evaluation_kwargs(view).items() if k != "availability"})


def test_v3_the_belief_moves_with_the_verification_record(writer):  # noqa: F811 - the imported fixture
    published = publish_corpus(writer, claim=CLAIM_FACET)
    _, before = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(before, NoBelief) and before.reason == "no-eligible-assessment"
    node = writer.add(publication_node(published.derived, assessment_ref=published.assessment.id))
    _, belief = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(belief, Belief)
    writer.delete(node.id)
    _, after = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(after, NoBelief) and after.reason == "no-eligible-assessment"


def test_v3_a_superseding_failed_verification_invalidates_and_retires_its_predecessor(writer):  # noqa: F811
    published = publish_corpus(writer, claim=CLAIM_FACET, publish=True)
    derived = published.derived
    failed = _mint_verification(  # the private mint: `build_verification` never sets `supersedes`
        original=derived.original, replayed=derived.replayed, assessment=derived.assessment, rule=derived.rule,
        report=derived.report, scope_rule=derived.scope_rule, scope=derived.scope, verdict="failed",
        supersedes=derived.identity(),
    )
    successor = writer.add(publication_node(failed, assessment_ref=published.assessment.id))
    inputs = _gathered(writer, published.proposition.id)
    assert lifecycle_state(inputs.verifications) == INVALIDATED
    assert {v.ref for v in active(inputs.verifications)} == {successor.id}  # [R10] the predecessor leaves the active set
    _, belief = admission_over(writer, published.proposition.id, published.original)
    assert isinstance(belief, NoBelief)


def test_v3_negatives_another_proposition_is_never_gathered_and_a_twin_target_admits(writer):  # noqa: F811
    published = publish_corpus(writer, claim=CLAIM_FACET)
    value = stored.assessment_value(published.assessment)
    # A genuine twin (decision 17) agrees on the whole facet, not only the
    # identity's three fields — ruling P8 refuses an identity-equal pair
    # whose facets disagree, so the optionals travel with the twin too.
    optional = {n: getattr(value, n) for n in ("estimate", "uncertainty", "estimand", "applicability") if getattr(value, n) is not None}
    twin = writer.add(
        stored.assessment_node(
            "a-p-twin", title="twin", spec=value.spec, run=run_ref(published.original.address()),
            proposition=published.proposition.id, outcome=value.outcome, interpretation_rule=value.interpretation_rule,
            **optional,
        )
    )
    assert stored.assessment_value(twin).identity() == value.identity()
    assert stored.assessment_value(twin).facet_digest() == value.facet_digest()
    writer.add(publication_node(published.derived, assessment_ref=twin.id))  # decision 17: the twin is a valid target
    _, belief = admission_over(writer, published.proposition.id, published.original)  # [R5] admission is over the identity
    assert isinstance(belief, Belief)
    other = writer.add(stored.proposition_node("q", title="q", claim={**CLAIM_FACET, "args": [OTHER_GENE, PHENO]}))
    inputs = _gathered(writer, other.id)
    assert inputs.verifications == () and inputs.assessments == ()


@pytest.mark.parametrize("disagreeing_outcome", ["refuted", "inconclusive"])
def test_v3_twins_that_disagree_on_outcome_are_refused_not_silently_resolved(writer, disagreeing_outcome):  # noqa: F811
    """Ruling P8: `identity()` digests only `(spec, run, proposition)` —
    `outcome` is a free write-path parameter with no cross-check, so a shared
    identity does not by itself mean two records assert the same fact. A
    disagreeing twin is a corpus contradiction, refused loudly rather than
    silently resolved by whichever record the corpus file order put first (the
    agreeing twin above still admits).

    `inconclusive` is the case that made the guard's original placement wrong:
    it disagrees *across* the directional boundary, so a guard reading only the
    directional records never saw the pair at all and the belief computed from
    the survivor alone."""
    published = publish_corpus(writer, claim=CLAIM_FACET)
    value = stored.assessment_value(published.assessment)
    assert disagreeing_outcome != value.outcome, "the twin must actually disagree"
    twin = writer.add(
        stored.assessment_node(
            "a-p-disagreeing-twin", title="disagreeing twin", spec=value.spec, run=run_ref(published.original.address()),
            proposition=published.proposition.id, outcome=disagreeing_outcome, interpretation_rule=value.interpretation_rule,
        )
    )
    assert stored.assessment_value(twin).identity() == value.identity()
    assert stored.assessment_value(twin).facet_digest() != value.facet_digest()
    writer.add(publication_node(published.derived, assessment_ref=twin.id))
    _, answer = admission_over(writer, published.proposition.id, published.original)
    # `evaluate` stays total: the contradiction is an answer, as loud as
    # step 2's `consulted-contracts-disagree`, and never a Belief.
    assert isinstance(answer, Refused), answer
    assert answer.reason.startswith("assessment-identity-contradicted")
    assert value.identity() in answer.reason
