"""The confined boundary's refusals carry stable reasons; the message is diagnostic."""

from beliefs.boundary import RunRefused
from beliefs.errors import (
    BoundaryPolicyUnsupported,
    ClosureMutated,
    ClosureUnsupported,
    ConfinementNotEstablished,
    ConfinementRefusal,
    ConfinementUnavailable,
    NotAnAssessmentVerification,
    RecordError,
    ScienceError,
    SnapshotMismatch,
)

REFUSALS = (
    ConfinementUnavailable,
    BoundaryPolicyUnsupported,
    ClosureUnsupported,
    SnapshotMismatch,
    ClosureMutated,
    ConfinementNotEstablished,
)


def test_every_confinement_refusal_carries_a_distinct_stable_reason():
    assert [cls.reason for cls in REFUSALS] == [
        "confinement-unavailable",
        "boundary-policy-unsupported",
        "closure-unsupported",
        "snapshot-mismatch",
        "closure-mutated",
        "confinement-not-established",
    ]
    assert all(issubclass(cls, ConfinementRefusal) for cls in REFUSALS)
    assert issubclass(ConfinementRefusal, ScienceError)
    assert "reason" not in vars(ConfinementRefusal)


def test_the_message_is_diagnostic_and_never_the_reason():
    error = ClosureMutated("bundle fingerprint moved between the bind and exit")
    assert error.reason == "closure-mutated"
    assert str(error) == "bundle fingerprint moved between the bind and exit"


def test_not_an_assessment_verification_is_a_record_error():
    assert issubclass(NotAnAssessmentVerification, RecordError)


def test_run_refused_carries_an_in_memory_detail_defaulting_to_empty():
    refused = RunRefused("closure-mutated", None, None, None)
    assert refused.detail == ""
    detailed = RunRefused("closure-mutated", None, None, None, detail="bundle moved")
    assert detailed.detail == "bundle moved"
