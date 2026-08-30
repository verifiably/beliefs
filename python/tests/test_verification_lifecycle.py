"""G2c's selected arms: kernel §3.3's lifecycle table walked over values.

"Active" is exercised as *not superseded* only; the standing-retraction clause
of the amended definition is the C group's and is deferred (cut 2 §4.2). A walk
exercising the pre-amendment lifecycle while claiming the amended one is the
over-count that row exists to prevent — so this file claims exactly the
supersession half.
"""

import pytest

from beliefs.errors import MalformedRecord
from beliefs.verification import (
    ADMITTED,
    INVALIDATED,
    NOT_ADMITTED,
    SCOPES,
    VERDICTS,
    Verification,
    lifecycle_state,
)


def v(ref: str, scope: str, verdict: str, supersedes: str | None = None) -> Verification:
    return Verification(ref=ref, assessment="a1", scope=scope, verdict=verdict, supersedes=supersedes)


class TestTheTableIsTotal:
    def test_no_verifications_is_not_admitted(self):
        assert lifecycle_state(()) == NOT_ADMITTED

    @pytest.mark.parametrize("scope", SCOPES)
    @pytest.mark.parametrize("verdict", VERDICTS)
    def test_every_single_verification_lands_in_a_row(self, scope, verdict):
        # The final row is a complement, so the table is total by construction:
        # only (clean-environment, passed) admits; any failed invalidates; the
        # rest — including (independent-implementation, passed) and
        # (not-certified, passed), the holes an enumerated row once left —
        # are not admitted.
        state = lifecycle_state((v("v1", scope, verdict),))
        if verdict == "failed":
            assert state == INVALIDATED
        elif (scope, verdict) == ("clean-environment", "passed"):
            assert state == ADMITTED
        else:
            assert state == NOT_ADMITTED


class TestFailClosed:
    def test_a_passing_sibling_does_not_clear_an_active_failure(self):
        state = lifecycle_state((v("bad", "clean-environment", "failed"), v("good", "clean-environment", "passed")))
        assert state == INVALIDATED

    def test_recency_does_not_clear_either(self):
        # A later verification that does not name the failure it supersedes is
        # a sibling, whatever its date; precedence is explicit supersession.
        state = lifecycle_state((v("bad", "clean-environment", "failed"), v("later", "clean-environment", "passed")))
        assert state == INVALIDATED

    def test_an_addressed_resolution_clears(self):
        state = lifecycle_state(
            (
                v("bad", "clean-environment", "failed"),
                v("fix", "clean-environment", "passed", supersedes="bad"),
            )
        )
        assert state == ADMITTED

    def test_a_superseded_pass_admits_nothing(self):
        state = lifecycle_state(
            (
                v("old", "clean-environment", "passed"),
                v("newer", "same-environment", "inconclusive", supersedes="old"),
            )
        )
        assert state == NOT_ADMITTED

    def test_the_state_is_a_function_of_its_argument(self):
        # G8's in-slice sabotage is statefulness — a cross-call memory. Derive,
        # observe invalidation, then derive again from the smaller value: the
        # failure's deletion must return the assessment to admitted (§3.2's
        # undetectable-history limit, pinned rather than papered over).
        failed = (v("bad", "clean-environment", "failed"), v("good", "clean-environment", "passed"))
        assert lifecycle_state(failed) == INVALIDATED
        assert lifecycle_state((failed[1],)) == ADMITTED


class TestClosedSets:
    def test_a_scope_outside_the_set_is_refused(self):
        with pytest.raises(MalformedRecord):
            v("v1", "friendly-environment", "passed")

    def test_a_verdict_outside_the_set_is_refused(self):
        with pytest.raises(MalformedRecord):
            v("v1", "clean-environment", "mostly-passed")
