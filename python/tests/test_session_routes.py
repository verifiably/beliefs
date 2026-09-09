"""The invocation-scoped run and holdings routes (session-routes design §4)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import CreateOp, DeleteOp
from test_operation_writes import proposition
from test_session_writer import DIGEST, make_session

from beliefs.errors import PermitExceeded, SessionProtocolError
from beliefs.permit import RequiredCapabilities
from beliefs.session import open_ledger_reader
from beliefs.session.routes import plan_records

RUNS = RequiredCapabilities.for_kinds({"run", "act-report"}, {"run": "run", "act-report": "run"})
INTENT = "1" * 64


class TracingLock:
    """A re-entrant lock that reports attempts blocked by another thread."""

    def __init__(self, on_attempt=None) -> None:
        self._inner = threading.RLock()
        self._holder: int | None = None
        self._depth = 0
        self.attempts: list[tuple[str, str]] = []
        self._on_attempt = on_attempt

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        name = threading.current_thread().name
        if self._inner.acquire(blocking=False):
            outcome = "owned"
        else:
            outcome = "held-by-another"
        self.attempts.append((name, outcome))
        if self._on_attempt is not None:
            self._on_attempt(name, outcome)
        if outcome == "held-by-another" and not self._inner.acquire(blocking, timeout):
            return False
        self._holder = threading.get_ident()
        self._depth += 1
        return True

    def release(self) -> None:
        self._depth -= 1
        if self._depth == 0:
            self._holder = None
        self._inner.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc) -> None:
        self.release()

    def held_by_me(self) -> bool:
        return self._holder == threading.get_ident()


def _plan(*nodes) -> tuple[CreateOp, ...]:
    return tuple(CreateOp(f"{n.kind}/{n.id.split(':', 1)[1]}.md", node_to_markdown(n).encode()) for n in nodes)


def test_plan_records_reads_uid_and_id_from_each_create(tmp_path):
    a, b = proposition("one"), proposition("two")
    assert plan_records(_plan(a, b)) == ((a.uid, a.id), (b.uid, b.id))


def test_plan_records_refuses_any_other_op():
    with pytest.raises(SessionProtocolError, match="creates only"):
        plan_records((DeleteOp("x.md", expected_digest="a" * 64),))


def _run_port(tmp_path: Path):
    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "run", DIGEST)
    writer = session.scoped(RUNS, "A")
    return session, writer, writer.operation_port(), ports[-1]


def test_execute_fulfilling_ledgers_an_act_with_the_plan_records(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    node = proposition("p")
    fulfills = port.append_intent(b"intent")
    entry = port.execute_fulfilling(_plan(node), fulfills)
    session.close_invocation("A", {"done": [[node.uid, node.id]]})
    session.close()

    (act,) = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert (act.intent, act.entry, act.record_ids) == (fulfills, entry, ((node.uid, node.id),))
    assert [kind for kind, _ in inner.calls] == ["append_intent", "execute_fulfilling"]


def test_execute_and_the_guarded_form_are_refused_before_the_inner_port(tmp_path):
    _session, _writer, port, inner = _run_port(tmp_path)
    with pytest.raises(SessionProtocolError, match="fulfilling"):
        port.execute(_plan(proposition("p")))
    with pytest.raises(SessionProtocolError, match="guarded"):
        port.execute_fulfilling_guarded(
            _plan(proposition("p")), INTENT, guard=lambda _v: None, fallback=lambda _reason: ()
        )
    assert inner.calls == []


def test_a_non_create_plan_is_refused_before_the_inner_port(tmp_path):
    _session, _writer, port, inner = _run_port(tmp_path)
    with pytest.raises(SessionProtocolError, match="creates only"):
        port.execute_fulfilling((DeleteOp("x.md", expected_digest="a" * 64),), INTENT)
    assert inner.calls == []


def test_a_closed_invocation_refuses_both_port_steps(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        port.append_intent(b"intent")
    with pytest.raises(SessionProtocolError):
        port.execute_fulfilling(_plan(proposition("p")), INTENT)
    assert inner.calls == []


def test_close_waits_while_append_intent_holds_the_session_lock(tmp_path, monkeypatch):
    session, _writer, port, inner = _run_port(tmp_path)
    appending, release, close_waiting = threading.Event(), threading.Event(), threading.Event()
    order: list[str] = []

    def on_attempt(name: str, outcome: str) -> None:
        if name == "close" and outcome == "held-by-another":
            close_waiting.set()

    monkeypatch.setattr(session, "_lock", TracingLock(on_attempt))
    append_intent = inner.append_intent

    def blocking_append(payload: bytes) -> str:
        appending.set()
        assert release.wait(10)
        digest = append_intent(payload)
        order.append("append")
        return digest

    monkeypatch.setattr(inner, "append_intent", blocking_append)

    def append() -> None:
        port.append_intent(b"intent")

    def close() -> None:
        assert appending.wait(10)
        session.close_invocation("A", {"done": []})
        order.append("close")

    appender = threading.Thread(target=append, name="append")
    closer = threading.Thread(target=close, name="close")
    appender.start()
    assert appending.wait(10)
    closer.start()
    assert close_waiting.wait(10)
    assert closer.is_alive()
    release.set()
    appender.join(10)
    closer.join(10)

    assert not appender.is_alive() and not closer.is_alive()
    assert order == ["append", "close"]


def test_the_port_carries_the_scoped_authority_and_profile(tmp_path):
    _session, writer, port, inner = _run_port(tmp_path)
    assert port.authority is inner.authority
    assert port.authority.actor == writer.actor
    assert port.profile is inner.profile


def test_a_permit_below_run_is_refused_by_the_boundary_before_any_intent(tmp_path):
    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "run", DIGEST)
    port = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "A").operation_port()
    with pytest.raises(PermitExceeded):
        port.authority.require("run", ("run", "act-report"))
    assert ports[-1].calls == []
