"""The successor-admission act's one named refusal (spec §5)."""

import pytest

from beliefs.errors import AdmissionEvidenceRefused, ScienceError


def test_it_is_a_science_error_carrying_reason_and_ref() -> None:
    refused = AdmissionEvidenceRefused("verification unreadable", "verification/v1.md")
    assert isinstance(refused, ScienceError)
    assert refused.reason == "verification unreadable"
    assert refused.ref == "verification/v1.md"
    assert str(refused) == "verification unreadable: verification/v1.md"


def test_both_arguments_are_required() -> None:
    with pytest.raises(TypeError):
        AdmissionEvidenceRefused("root unreadable")  # type: ignore[call-arg]
