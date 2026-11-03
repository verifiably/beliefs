"""The failing test for the one-identity change, written before the fix.

One identity: the assessment identity a stored assessment reads back is the
identity its run derives, so a verification derived over an original and a
replayed run of that assessment is admitted by the gate's own clause and
checked without contradiction by the audit. On the tree before the fix
this fails at the first assertion: `stored.assessment_value`
hands back the typed `run:` ref and digests it, while the derivation digests
the bare closure address.
"""

from __future__ import annotations

import pytest
from test_evaluation import CLAIM_FACET
from test_relocation import _writer
from verification_fixtures import publish_corpus

from beliefs import stored
from beliefs.admission import Admitted
from beliefs.audit import check_verification
from beliefs.belief import Belief
from beliefs.verification import ADMITTED, lifecycle_state
from beliefs.verify import admission_record


@pytest.fixture()
def writer(tmp_path):
    return _writer(tmp_path / "corpus")


def test_one_identity_admits_over_the_corpus_and_audits_clean(writer):
    published = publish_corpus(writer, claim=CLAIM_FACET)
    original, assessment = published.original, published.assessment
    derived, verification, evidence = published.derived_value, published.derived, published.evidence
    record = admission_record(verification)
    from beliefs.verify import publication_node

    stored_node = writer.add(publication_node(verification, assessment_ref=assessment.id))
    view = writer.read_view

    stored_identity = stored.assessment_reference(view.get(assessment.id)).identity()
    assert stored_identity == derived.identity() == record.assessment, (
        "one spelling for the run member: the stored assessment reads back the identity its run derives"
    )
    verifications = (stored.verification_value(view.get(stored_node.id)),)
    assert lifecycle_state(tuple(v for v in verifications if v.assessment == stored_identity)) == ADMITTED
    outcome = check_verification(view, view.get(stored_node.id), evidence=evidence)
    assert outcome.checked and outcome.contradiction is None

    # The full flow: gather -> admit over the corpus, the gate's every clause.
    from verification_fixtures import admission_over

    verdict, belief = admission_over(writer, published.proposition.id, original)
    assert isinstance(verdict, Admitted), verdict
    assert isinstance(belief, Belief), belief
