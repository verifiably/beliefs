"""The invocation-scoped run and holdings routes (session-routes design §4)."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fixtures_cut3 import run_assessment
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import CreateOp, DeleteOp
from test_boundary import _assessment
from test_operation_writes import proposition
from test_session_writer import DIGEST, make_session

from beliefs.boundary import RunRefused
from beliefs.corpus import _operation_lock_for
from beliefs.errors import SessionProtocolError
from beliefs.holdings.boundary import ActContext, recheck, write
from beliefs.holdings.records import StoreLocator
from beliefs.holdings.seam import FileStateView, PathObservedView, StoreActSeam, StoreOutcomeView
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
    refused = run_assessment(tmp_path, port=port)
    assert isinstance(refused, RunRefused) and refused.reason == "permit-exceeded"
    assert refused.report is None and refused.intent is None and refused.registration is None
    assert ports[-1].calls == []


def test_an_unheld_input_refusal_is_excluded_by_the_fulfilling_only_route(tmp_path):
    _session, _writer, port, inner = _run_port(tmp_path)
    with pytest.raises(SessionProtocolError, match="fulfilling writes"):
        _assessment(tmp_path, port, held_inputs={})
    assert inner.calls == []


# --- the holdings route (design §4.2) ---------------------------------------------
HOLDINGS = RequiredCapabilities.for_kinds({"holdings-observation"}, {})
STORE_ID = "1" * 32
GENESIS = b'{"domain":"science.store-root.v1","store_id":"' + STORE_ID.encode() + b'"}'
STATE = FileStateView("sha256:" + "a" * 64)


@dataclass
class FakeSeam:
    root: Path
    lock: TracingLock | None = None
    on_corpus_lock: Any = None
    reached: list[str] = field(default_factory=list)
    published: list[tuple[object, ...]] = field(default_factory=list)
    entered: int = 0

    def _touch(self, name: str) -> None:
        if self.lock is not None:
            assert self.lock.held_by_me(), f"{name} entered without the session lock"
        self.reached.append(name)

    def build(self) -> StoreActSeam:
        @contextmanager
        def corpus_lock(root):
            self._touch("corpus_lock")
            with _operation_lock_for(root):
                self.entered += 1
                if self.on_corpus_lock is not None:
                    self.on_corpus_lock(self.entered)
                yield

        def append_intent(_root, _payload):
            self._touch("append_intent")
            return INTENT

        def publish_fulfilling(_root, plan, _intent):
            self._touch("publish_fulfilling")
            self.published.append(tuple(plan))
            return "2" * 64

        def read_path(_root, _path):
            self._touch("read_path")
            return PathObservedView(STATE)

        def store_write(_root, path, _bytes):
            self._touch("store_write")
            return StoreOutcomeView("tx", ((path, STATE),))

        def store_genesis(_root):
            self._touch("store_genesis")
            return GENESIS

        def unused(*_):
            raise AssertionError("not reached")

        return StoreActSeam(corpus_lock, append_intent, publish_fulfilling, read_path, store_write, unused, unused, store_genesis)


BOTH = RequiredCapabilities.for_kinds({"holdings-observation", "proposition"}, {})


def _holdings(tmp_path: Path, seam: FakeSeam, scope: RequiredCapabilities = HOLDINGS):
    session, ports = make_session(tmp_path, store_root=tmp_path / "store", store_id=STORE_ID, holdings_seam=seam.build())
    session.claim_invocation("A", "hold", DIGEST)
    writer = session.scoped(scope, "A")
    return session, writer, writer.holdings_context(instrument="test"), ports[-1]


def _published_pair(seam: FakeSeam) -> tuple[str, str]:
    from nodes.core.frontmatter import node_from_markdown
    ((op,),) = seam.published
    node = node_from_markdown(op.content.decode("utf-8"))  # type: ignore[attr-defined]
    return node.uid, node.id


def test_holdings_context_without_a_store_is_a_protocol_error(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "hold", DIGEST)
    with pytest.raises(SessionProtocolError, match="no store"):
        session.scoped(HOLDINGS, "A").holdings_context(instrument="test")


def test_holdings_context_binds_the_session_and_the_scoped_authority(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, writer, ctx, _ = _holdings(tmp_path, seam)
    assert type(ctx) is ActContext
    assert (ctx.observer_root, ctx.store_root) == (session.corpus_root, tmp_path / "store")
    assert (ctx.observer, ctx.instrument, ctx.actor) == (session.actor, "test", writer.actor)
    assert ctx.authority is writer._authority and ctx.profile is session.profile


def test_a_holdings_write_ledgers_an_act_naming_the_observation(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    pair = _published_pair(seam)
    session.close_invocation("A", {"done": [list(pair)]})
    session.close()
    (act,) = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert (act.intent, act.entry, act.record_ids) == (INTENT, "2" * 64, (pair,))
    assert seam.reached == ["corpus_lock", "append_intent", "store_genesis", "store_write", "corpus_lock", "publish_fulfilling"]


def test_a_context_kept_past_its_invocation_reaches_no_member(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    with pytest.raises(SessionProtocolError):
        recheck(ctx, StoreLocator(STORE_ID, "p.bin"))
    assert seam.reached == []


def test_a_close_inside_the_intent_append_is_refused_at_the_genesis_read(tmp_path):
    holder: dict[str, Any] = {}
    seam = FakeSeam(tmp_path / "corpus")
    original = seam.build

    def build():
        from dataclasses import replace
        built = original()
        inner_append = built.append_intent

        def closing_append(root, payload):
            digest = inner_append(root, payload)
            holder["session"].close_invocation("A", {"done": []})
            return digest
        return replace(built, append_intent=closing_append)

    seam.build = build  # type: ignore[method-assign]
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    holder["session"] = session
    with pytest.raises(SessionProtocolError):
        write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    assert seam.reached == ["corpus_lock", "append_intent"]


def test_lock_order_is_session_then_corpus_everywhere(tmp_path):
    lock = TracingLock()
    seam = FakeSeam(tmp_path / "corpus", lock=lock)
    session, writer, ctx, _ = _holdings(tmp_path, seam, BOTH)
    session._lock = lock  # type: ignore[assignment]
    write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    writer.add(proposition("p"))
    assert {outcome for _, outcome in lock.attempts} == {"owned"}
    assert "publish_fulfilling" in seam.reached


def test_a_holdings_write_and_a_corpus_add_on_two_threads_both_complete(tmp_path):
    b_signalled, a_in_publication = threading.Event(), threading.Event()
    lock = TracingLock(on_attempt=lambda name, _outcome: b_signalled.set() if name == "B" else None)

    def on_corpus_lock(entered: int) -> None:
        if entered == 2:
            a_in_publication.set()
            assert b_signalled.wait(5), "B never attempted the session lock"

    seam = FakeSeam(tmp_path / "corpus", on_corpus_lock=on_corpus_lock)
    session, writer, ctx, _ = _holdings(tmp_path, seam, BOTH)
    session._lock = lock  # type: ignore[assignment]
    failures: list[BaseException] = []

    def run(fn):
        try:
            fn()
        except BaseException as caught:  # noqa: BLE001
            failures.append(caught)

    a = threading.Thread(name="A", target=run, args=(lambda: write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes"),), daemon=True)
    b = threading.Thread(name="B", target=run, args=(lambda: writer.add(proposition("p")),), daemon=True)
    a.start()
    assert a_in_publication.wait(5)
    b.start()
    a.join(5)
    b.join(5)
    assert not a.is_alive() and not b.is_alive(), "deadlock: the lock order is not session then corpus"
    assert failures == []
    assert ("B", "held-by-another") in lock.attempts
