"""A supplied operation port is bound to its writer (act-report-remainder design decision 13)."""

from __future__ import annotations

import secrets

import pytest
from authority import FULL, narrowed
from profiles import WITH_BIOLOGY
from test_operation_writes import RecordingPort, writer_over

from beliefs import boundary as boundary_values
from beliefs.errors import PortMismatch
from beliefs.report import LocatorEntry, OperationIntent, RetrievalFailed


def _report(writer, token: str):
    now = "2026-09-22T00:00:00Z"
    return boundary_values._mint_acquisition_report(
        OperationIntent("acquisition", token, writer.authority.actor), observer="o", instrument="i",
        opened_at=now, closed_at=now,
        entries=(LocatorEntry("url:https://example.org/a", RetrievalFailed("status 500"), ()),),
    )


class BiologyPort(RecordingPort):
    def __init__(self, authority, root) -> None:
        super().__init__(authority, root)
        self.profile = WITH_BIOLOGY


def test_none_returns_the_writers_own_port(tmp_path):
    writer, port = writer_over(tmp_path)
    assert writer._require_bound_port(None) is port


def test_a_fresh_port_on_the_same_root_authority_and_profile_is_bound(tmp_path):
    writer, port = writer_over(tmp_path)
    fresh = RecordingPort(FULL, tmp_path)
    assert writer._require_bound_port(port) is port
    assert writer._require_bound_port(fresh) is fresh


@pytest.mark.parametrize("spoil", ["root", "authority", "profile"])
def test_a_port_bound_elsewhere_refuses_before_either_primitive_touches_a_port(tmp_path, spoil):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    writer, own = writer_over(tmp_path / "a")
    if spoil == "root":
        port = RecordingPort(FULL, tmp_path / "b")
    elif spoil == "authority":
        port = RecordingPort(narrowed(kinds=("act-report",), families=("corpus-write",)), tmp_path / "a")
    else:
        port = BiologyPort(FULL, tmp_path / "a")
    token = secrets.token_hex(16)
    with pytest.raises(PortMismatch):
        writer._append_operation_intent("acquisition", token, writer.authority.actor, port=port)
    with pytest.raises(PortMismatch):
        writer._publish_operation_report(_report(writer, token), "0" * 64, port=port)
    assert own.calls == [] and port.calls == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())
