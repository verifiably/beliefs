"""Complete invented event preparation, persisted and reopened on the certified tuple."""

from fractions import Fraction

from authority import FULL
from profiles import pins_for
from series.test_event_preparation import complete_chain, preparation_chain
from series.test_event_preparation import preparation_profile as preparation_profile  # noqa: PLC0414

from beliefs import audit, stored
from beliefs.root import init_corpus_root, open_corpus


def test_event_preparation_durable_roundtrip(preparation_profile, certified_work):
    chain = preparation_chain(preparation_profile)
    corpus = certified_work / "corpus"
    init_corpus_root(corpus, authority=FULL)
    writer = open_corpus(corpus, authority=FULL, profile=chain.profile)
    writer.adopt_manifest(profile=pins_for(chain.profile))
    result = complete_chain(chain, certified_work, writer=writer)
    assert Fraction(result.emitted) == Fraction(7, 2)
    assert result.verification.verdict == "passed"
    reopened = open_corpus(corpus, authority=FULL, profile=chain.profile)
    node = reopened.read_view.get(result.assessment.id)
    assert stored.assessment_value(node, profile=chain.profile).target == result.spec.assessed_target
    checked = audit.check_assessment(reopened.read_view, node, profile=chain.profile, evidence=result.evidence)
    assert checked.checked and checked.contradiction is None
