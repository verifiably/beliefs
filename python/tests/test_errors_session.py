from beliefs.errors import (
    LedgerMalformed,
    OperationPortMissing,
    PlanRefused,
    ScienceError,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
    SessionRefused,
    WriteRefused,
)


def test_the_session_errors_have_their_designed_bases():
    assert issubclass(PlanRefused, WriteRefused)
    assert issubclass(OperationPortMissing, WriteRefused)
    for hard in (SessionRefused, SessionClosed, SessionProtocolError, SessionLedgerFailed, LedgerMalformed):
        assert issubclass(hard, ScienceError) and not issubclass(hard, WriteRefused)
