"""The seal: a run session refuses new acts and phases, drains the holds already
begun, and names each written chain's tip from a detached read."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from profiles import BASE
from test_operation_writes import proposition
from test_run_session import CEILING
from test_session_claim import _one_corpus, _store
from test_session_routes import STORE_ID, FakeSeam, TracingLock, _plan, _registered
from test_session_writer import DIGEST, PROPOSITIONS, make_session

from beliefs.errors import (
    ScienceError,
    SealTimeout,
    SealTipsUnavailable,
    SessionClosed,
    SessionProtocolError,
    SessionSealed,
)
from beliefs.holdings.boundary import write
from beliefs.holdings.records import StoreLocator
from beliefs.permit import RequiredCapabilities
from beliefs.root import log_seam
from beliefs.session import open_ledger_reader, open_run_session
from beliefs.session import writer as writer_module
from beliefs.session.writer import ChainTip, SealedTips, WriterSession
from beliefs.world.logmodel import AbsentView, GenesisEntryView, SettledEntryView, WellFormedView

AUDITS = RequiredCapabilities.for_kinds({"act-report"}, {"act-report": "corpus-write"})
HOLDINGS = RequiredCapabilities.for_kinds({"holdings-observation"}, {})
GENESIS_DIGEST = "0" * 64
_GENESIS = GenesisEntryView(GENESIS_DIGEST, b"{}", ())
STUB_VIEW = WellFormedView(_GENESIS, (_GENESIS,), GENESIS_DIGEST, ())
WAIT = 30


# --- helpers ------------------------------------------------------------------
class _Run(threading.Thread):
    """A named thread that keeps its target's result or exception."""

    def __init__(self, name: str, target: Callable[[], Any]) -> None:
        super().__init__(name=name, daemon=True)
        self._target_call = target
        self.result: Any = None
        self.raised: BaseException | None = None

    def run(self) -> None:
        try:
            self.result = self._target_call()
        except BaseException as caught:  # noqa: BLE001 - the outcome is the assertion
            self.raised = caught


def _stub_views(monkeypatch, views: dict[Path, object] | None = None) -> None:
    """Every detached read the seal takes answers `STUB_VIEW`, or the view
    `views` names for that root."""
    chosen = {} if views is None else views

    def inspect(root: Path) -> object:
        return chosen.get(Path(root), STUB_VIEW)

    monkeypatch.setattr(writer_module, "log_seam", lambda: SimpleNamespace(inspect_detached=inspect))


def _seal_waits(session: WriterSession, monkeypatch) -> threading.Event:
    """Swap the session lock for a tracing one; the event is set once the seal
    thread finds the lock held by another."""
    waiting = threading.Event()

    def on_attempt(name: str, outcome: str) -> None:
        if name == "seal" and outcome == "held-by-another":
            waiting.set()

    monkeypatch.setattr(session, "_lock", TracingLock(on_attempt))
    return waiting


def _block_record_act(session: WriterSession, monkeypatch) -> tuple[threading.Event, threading.Event]:
    """A scoped act blocks after its commit, inside the session and root locks,
    until released."""
    inside, release = threading.Event(), threading.Event()
    real = session._record_act

    def blocked(invocation, commit) -> None:
        inside.set()
        assert release.wait(WAIT)
        real(invocation, commit)

    monkeypatch.setattr(session, "_record_act", blocked)
    return inside, release


def _run_session(work: Path, *, store: bool = False) -> WriterSession:
    config, root = _one_corpus(work)
    return open_run_session(
        config, work / "ops", write_root=root, profile=BASE, ceiling=CEILING, store_root=_store(work) if store else None
    )


def _detached_tip(chain_id: str, root: Path) -> ChainTip:
    view = log_seam().inspect_detached(root)
    assert type(view) is WellFormedView
    return ChainTip(chain_id, view.genesis.digest, view.tip)


# --- draining and cutting -----------------------------------------------------
def test_a_scoped_act_in_flight_drains_into_the_sealed_tip(certified_work, monkeypatch):
    session = _run_session(certified_work)
    root = session.corpus_root
    try:
        session.claim_invocation("A", "mint", DIGEST)
        writer = session.scoped(PROPOSITIONS, "A")
        seal_waiting = _seal_waits(session, monkeypatch)
        inside, release = _block_record_act(session, monkeypatch)
        act = _Run("act", lambda: writer.add(proposition("p")))
        act.start()
        assert inside.wait(WAIT)
        sealer = _Run("seal", lambda: session.seal(WAIT))
        sealer.start()
        assert seal_waiting.wait(WAIT)
        assert sealer.is_alive()
        release.set()
        act.join(WAIT)
        sealer.join(WAIT)
        assert act.raised is None and sealer.raised is None
        (line,) = session.invocation_acts("A")
        view = log_seam().inspect_detached(root)
        assert type(view) is WellFormedView
        settled = view.entries[-1]
        assert type(settled) is SettledEntryView and settled.registration == line.entry
        assert sealer.result == SealedTips(ChainTip(session.corpus_id, view.genesis.digest, view.tip), None)
        session.close_invocation("A", {"done": []})
    finally:
        session.close()
    (ledgered,) = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert ledgered.entry == line.entry


def test_a_route_fulfil_after_the_seal_is_refused(certified_work):
    session = _run_session(certified_work)
    root = session.corpus_root
    try:
        session.claim_invocation("A", "run", DIGEST)
        port = session.scoped(PROPOSITIONS, "A").operation_port()
        fulfills = port.append_intent(b"intent")
        tips = session.seal(WAIT)
        assert tips.corpus == _detached_tip(session.corpus_id, root)
        with pytest.raises(SessionSealed):
            port.execute_fulfilling(_plan(proposition("p")), fulfills)
        assert _registered(root, fulfills) == []
        assert session.invocation_acts("A") == ()
        assert _detached_tip(session.corpus_id, root) == tips.corpus
    finally:
        session.close()


def test_a_holdings_write_sealed_between_store_and_publish(tmp_path, monkeypatch):
    _stub_views(monkeypatch)
    seam = FakeSeam(tmp_path / "corpus")
    built = seam.build()
    stored, release = threading.Event(), threading.Event()

    def blocking_store_write(root, path, content, intent):
        outcome = built.store_write(root, path, content, intent)
        stored.set()
        assert release.wait(WAIT)
        return outcome

    session, _ = make_session(
        tmp_path,
        store_root=tmp_path / "store",
        store_id=STORE_ID,
        holdings_seam=replace(built, store_write=blocking_store_write),
        run=True,
    )
    session.claim_invocation("A", "hold", DIGEST)
    ctx = session.scoped(HOLDINGS, "A").holdings_context(instrument="test")
    seal_waiting = _seal_waits(session, monkeypatch)
    act = _Run("act", lambda: write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes"))
    act.start()
    assert stored.wait(WAIT)
    sealer = _Run("seal", lambda: session.seal(WAIT))
    sealer.start()
    assert seal_waiting.wait(WAIT)
    release.set()
    act.join(WAIT)
    sealer.join(WAIT)
    assert sealer.raised is None and type(sealer.result) is SealedTips
    assert type(act.raised) is SessionSealed
    (entry,) = seam.entries
    (intent,) = seam.intents
    (line,) = session.invocation_acts("A")
    assert (line.corpus, line.entry, line.intent, line.record_ids) == (STORE_ID, entry, intent, ())
    assert "publish_fulfilling" not in seam.reached and seam.published == []
    assert not session._ledger.failed
    session.close_invocation("A", {"done": []})
    session.close()


def test_an_audit_in_flight_drains_whole(certified_work, monkeypatch):
    from beliefs import audit_operation
    from beliefs.audit import NO_EVIDENCE

    session = _run_session(certified_work)
    root = session.corpus_root
    try:
        session.claim_invocation("A", "audit", DIGEST)
        scoped = session.scoped(AUDITS, "A")
        seal_waiting = _seal_waits(session, monkeypatch)
        inside, release = threading.Event(), threading.Event()
        real = audit_operation.audit_corpus

        def blocked(*args, **kwargs):
            inside.set()
            assert release.wait(WAIT)
            return real(*args, **kwargs)

        monkeypatch.setattr(audit_operation, "audit_corpus", blocked)
        auditor = _Run("audit", lambda: scoped.audit(instrument="inst", evidence=NO_EVIDENCE))
        auditor.start()
        assert inside.wait(WAIT)  # the intent is appended; the fulfilment is still to come
        sealer = _Run("seal", lambda: session.seal(WAIT))
        sealer.start()
        assert seal_waiting.wait(WAIT)
        release.set()
        auditor.join(WAIT)
        sealer.join(WAIT)
        assert auditor.raised is None and sealer.raised is None
        (line,) = session.invocation_acts("A")
        assert [entry.digest for entry in _registered(root, line.intent)] == [line.entry]
        assert line.record_ids[0][1] == auditor.result.report_ref
        assert sealer.result.corpus == _detached_tip(session.corpus_id, root)
        session.close_invocation("A", {"done": []})
    finally:
        session.close()


def test_a_held_act_past_the_timeout_gives_seal_timeout(tmp_path, monkeypatch):
    _stub_views(monkeypatch)
    session, _ = make_session(tmp_path, run=True)
    session.claim_invocation("A", "mint", DIGEST)
    writer = session.scoped(PROPOSITIONS, "A")
    inside, release = _block_record_act(session, monkeypatch)
    act = _Run("act", lambda: writer.add(proposition("p")))
    act.start()
    assert inside.wait(WAIT)
    with pytest.raises(SealTimeout):
        session.seal(0.2)
    assert session._sealed is True
    release.set()
    act.join(WAIT)
    assert act.raised is None and len(session.invocation_acts("A")) == 1
    assert session.seal(WAIT) == SealedTips(ChainTip(session.corpus_id, GENESIS_DIGEST, GENESIS_DIGEST), None)
    with pytest.raises(SessionSealed):
        writer.add(proposition("q"))
    session.close_invocation("A", {"done": []})
    session.close()


# --- after the seal -------------------------------------------------------------
def test_after_the_seal(tmp_path, monkeypatch):
    _stub_views(monkeypatch)
    session, ports = make_session(tmp_path, run=True)
    session.claim_invocation("A", "mint", DIGEST)
    writer = session.scoped(PROPOSITIONS, "A")
    session.seal(WAIT)
    assert issubclass(SessionSealed, ScienceError) and not issubclass(SessionSealed, SessionClosed)
    with pytest.raises(SessionSealed):
        session.claim_invocation("B", "mint", DIGEST)
    with pytest.raises(SessionSealed):
        session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(SessionSealed):
        session.select_project("A", None)
    with pytest.raises(SessionSealed):
        writer.add(proposition("p"))
    assert ports[-1].calls == []
    assert session.invocation_acts("A") == ()
    assert session.invocation_selection("A") is None
    assert session.invocation_sharing("A") == ()
    session.close_invocation("A", {"done": []})
    session.close()
    lines = open_ledger_reader(session.operations_root, session.session_id)
    assert lines.acts() == ()


@pytest.mark.parametrize(
    ("chain", "view", "reason"),
    [
        ("corpus", replace(STUB_VIEW, pending=(("tx", "e" * 64),)), "pending"),
        ("store", replace(STUB_VIEW, pending=(("tx", "e" * 64),)), "pending"),
        ("corpus", AbsentView(), "chain-absent"),
    ],
)
def test_pending_on_a_written_chain_refuses_the_seal(tmp_path, monkeypatch, chain, view, reason):
    session, _ = make_session(
        tmp_path, store_root=tmp_path / "store", store_id=STORE_ID, holdings_seam=FakeSeam(tmp_path).build(), run=True
    )
    root = session.corpus_root if chain == "corpus" else session.store_root
    assert root is not None
    _stub_views(monkeypatch, {root: view})
    with pytest.raises(SealTipsUnavailable) as refused:
        session.seal(WAIT)
    assert (refused.value.root, refused.value.reason) == (root, reason)
    session.close()


def test_seal_on_an_attended_session_is_a_protocol_error(tmp_path, monkeypatch):
    _stub_views(monkeypatch)
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(SessionProtocolError, match="run session"):
        session.seal(WAIT)
    assert session._sealed is False
    session.scoped(PROPOSITIONS, "A").add(proposition("p"))
    assert len(session.invocation_acts("A")) == 1
    session.close_invocation("A", {"done": []})
    session.close()


def test_two_seals_return_the_same_tips(certified_work):
    session = _run_session(certified_work, store=True)
    store_root, store_id = session.store_root, session.store_id
    assert store_root is not None and store_id is not None
    try:
        session.claim_invocation("A", "mint", DIGEST)
        session.scoped(PROPOSITIONS, "A").add(proposition("p"))
        first = session.seal(WAIT)
        assert first == SealedTips(
            _detached_tip(session.corpus_id, session.corpus_root), _detached_tip(store_id, store_root)
        )
        assert session.seal(WAIT) == first
        session.close_invocation("A", {"done": []})
    finally:
        session.close()


def test_a_run_session_without_a_store_seals_with_store_none(certified_work):
    session = _run_session(certified_work)
    try:
        tips = session.seal(WAIT)
        assert tips == SealedTips(_detached_tip(session.corpus_id, session.corpus_root), None)
    finally:
        session.close()


# --- negative -------------------------------------------------------------------
def test_an_unsealed_sessions_next_act_lands(tmp_path):
    session, _ = make_session(tmp_path, run=True)
    session.claim_invocation("A", "mint", DIGEST)
    writer = session.scoped(PROPOSITIONS, "A")
    writer.add(proposition("p"))
    writer.add(proposition("q"))
    assert session._sealed is False
    assert len(session.invocation_acts("A")) == 2
    session.close_invocation("A", {"done": []})
    session.close()
