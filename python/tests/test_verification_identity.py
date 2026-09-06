"""V2's failing test, written before conformance cut 21 froze (design §13).

One identity: the assessment identity a stored assessment reads back is the
identity its run derives, so a verification derived over an original and a
replayed run of that assessment is admitted by the gate's own clause and
checked without contradiction by the audit. On the tree the design was
written against this fails at the first assertion: `stored.assessment_value`
hands back the typed `run:` ref and digests it, while the derivation digests
the bare closure address (mm30 reproduction record §6, steps 6 and 8).
"""

from __future__ import annotations

import pytest
from fixtures_cut3 import spec_draft, spec_rules
from test_audit import (
    _interpretation_evidence,
    _verification_evidence,
    add_observed_datasets,
    assessment_closure,
    run_publication,
)
from test_relocation import _writer

from beliefs import stored
from beliefs.assess import build_assessment
from beliefs.audit import check_verification
from beliefs.record import AssessmentValue
from beliefs.runrecord import run_ref
from beliefs.spec import freeze
from beliefs.verification import ADMITTED, lifecycle_state
from beliefs.verify import AssessmentVerification, admission_record, build_verification


@pytest.fixture()
def writer(tmp_path):
    return _writer(tmp_path / "corpus")


def test_v2_one_identity_admits_over_the_corpus_and_audits_clean(writer):
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    original = assessment_closure(frozen, token="tok-original")
    replayed = assessment_closure(frozen, token="tok-replayed")
    add_observed_datasets(writer, original)
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    interpretation = _interpretation_evidence(frozen)
    derived = build_assessment(original, specs=interpretation.specs, implementations=interpretation.implementations)
    assert isinstance(derived, AssessmentValue), derived
    proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    # The reproduction driver's shape: the run as the typed corpus ref, so it resolves.
    assessment = writer.add(
        stored.assessment_node(
            "a1",
            title="a1",
            spec=frozen.identity,
            run=run_ref(original.address()),
            proposition=proposition.id,
            outcome=derived.outcome,
            interpretation_rule=derived.interpretation_rule,
        )
    )
    evidence = _verification_evidence(frozen)
    verification = build_verification(
        original,
        replayed,
        specs=evidence.specs,
        held_rules=evidence.held_rules,
        contract_identity="science:" + "c" * 64,
        epoch="epoch:" + "e" * 64,
    )
    assert isinstance(verification, AssessmentVerification)
    record = admission_record(verification)
    stored_node = writer.add(
        stored.verification_node(
            record.ref[:16],
            title="v",
            assessment=record.assessment,
            assessment_ref=assessment.id,
            scope=record.scope,
            verdict=record.verdict,
            derivation=(run_ref(original.address()), run_ref(replayed.address())),
        )
    )
    view = writer.read_view

    stored_identity = stored.assessment_value(view.get(assessment.id)).identity()
    assert stored_identity == derived.identity() == record.assessment, (
        "one spelling for the run member: the stored assessment reads back the identity its run derives"
    )
    verifications = (stored.verification_value(view.get(stored_node.id)),)
    assert lifecycle_state(tuple(v for v in verifications if v.assessment == stored_identity)) == ADMITTED
    outcome = check_verification(view, view.get(stored_node.id), evidence=evidence)
    assert outcome.checked and outcome.contradiction is None, outcome
