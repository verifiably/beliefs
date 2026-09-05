"""J3, J6 and J11 portably: a WriterSession built from parts over the in-memory
executor and a synthetic-digest port (design §13 item 2)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pytest
from nodes.core.write_plan import DefaultExecutor
from test_operation_writes import RecordingPort, proposition

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    PermitExceeded,
    PermitFact,
    PlanRefused,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
)
from beliefs.permit import Authority, RequiredCapabilities, WritePermit
from beliefs.session import (
    Claim,
    ClaimDone,
    ClaimFresh,
    ClaimMismatch,
    ClaimOpen,
    KernelRefusalValue,
    ScopedWriter,
    WriterSession,
    open_ledger_reader,
)
from beliefs.session.ledger import LedgerWriter, ledger_path
from beliefs.world.records import RECORD_CEILING

SESSION = "a" * 32
WORLD = "b" * 32
CORPUS = "c" * 32
DIGEST = "d" * 64


def make_session(
    tmp_path: Path, ceiling: WritePermit | None = None
) -> tuple[WriterSession, list[RecordingPort]]:
    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    operations_root = tmp_path / "ops"
    path = ledger_path(operations_root, SESSION)
    path.parent.mkdir(parents=True)
    ports: list[RecordingPort] = []

    def writer_factory(authority: Authority) -> CorpusWriter:
        port = RecordingPort(authority, corpus_root)
        ports.append(port)
        return CorpusWriter(corpus_root, DefaultExecutor, authority=authority, operation_port=port)

    ledger = LedgerWriter(path)
    session = WriterSession(
        session_id=SESSION, world_id=WORLD, corpus_root=corpus_root, corpus_id=CORPUS,
        operations_root=operations_root, ledger=ledger, writer_factory=writer_factory,
        ceiling=WritePermit.full() if ceiling is None else ceiling,
    )
    return session, ports


def replayed(claim: Claim) -> Any:
    """The outcome a `ClaimDone` replays, read untyped by the mutation arms."""
    assert type(claim) is ClaimDone
    return claim.outcome


PROPOSITIONS = RequiredCapabilities.for_kinds({"proposition"}, {})


# --- J6: the claim table ---------------------------------------------------------
def test_the_claim_table(tmp_path):
    session, _ = make_session(tmp_path)
    assert type(session.claim_invocation("A", "mint", DIGEST)) is ClaimFresh
    assert session.current_invocation == "A"
    assert type(session.claim_invocation("A", "mint", DIGEST)) is ClaimOpen
    assert type(session.claim_invocation("A", "mint", "e" * 64)) is ClaimMismatch
    assert type(session.claim_invocation("A", "other", DIGEST)) is ClaimMismatch
    session.close_invocation("A", {"done": [["u1", "proposition:p1"]]})
    done = session.claim_invocation("A", "mint", DIGEST)
    assert type(done) is ClaimDone and done.outcome == {"done": [["u1", "proposition:p1"]]}
    assert type(session.claim_invocation("A", "mint", "e" * 64)) is ClaimMismatch
    assert session.current_invocation is None


def test_a_refusal_outcome_replays_whole_and_detached_from_every_caller(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("F", "over", DIGEST)
    nested = {"requirement": {"dimension": "kind", "name": "source"}}
    envelope = {"refusal": {"code": "permit-exceeded", "message": "kind source", "data": nested}}
    session.close_invocation("F", envelope)
    nested["requirement"]["name"] = "MUTATED-INPUT"  # the caller keeps mutating what it passed in
    first = replayed(session.claim_invocation("F", "over", DIGEST))
    assert first["refusal"]["data"]["requirement"]["name"] == "source"
    first["refusal"]["data"]["requirement"]["name"] = "MUTATED-OUTPUT"  # and what it got back
    again = replayed(session.claim_invocation("F", "over", DIGEST))
    assert again["refusal"]["data"]["requirement"]["name"] == "source"
    session.claim_invocation("G", "mint", DIGEST)
    session.close_invocation("G", {"done": [["u1", "proposition:p1"]]})
    replayed(session.claim_invocation("G", "mint", DIGEST))["done"].clear()
    assert replayed(session.claim_invocation("G", "mint", DIGEST)) == {"done": [["u1", "proposition:p1"]]}
    record = open_ledger_reader(session.operations_root, SESSION).invocation("G")
    assert record is not None and record.outcome == {"done": [["u1", "proposition:p1"]]}


def test_an_abandoned_invocation_stays_open_and_never_blocks_a_fresh_claim(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    assert type(session.claim_invocation("B", "mint", DIGEST)) is ClaimFresh
    assert session.current_invocation == "B"
    assert type(session.claim_invocation("A", "mint", DIGEST)) is ClaimOpen
    with pytest.raises(SessionProtocolError):
        session.close_invocation("A", {"done": []})
    session.close_invocation("B", {"done": []})
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert reader.open_invocations == ("A",)


def test_a_malformed_outcome_is_refused_and_the_invocation_stays_current(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(ValueError):
        session.close_invocation("A", {"done": [["u"]]})
    assert session.current_invocation == "A"


def test_claims_are_validated(tmp_path):
    session, _ = make_session(tmp_path)
    for bad in [("bad id!", "mint", DIGEST), ("A", "", DIGEST), ("A", "mint", "short")]:
        with pytest.raises(ValueError):
            session.claim_invocation(*bad)


def test_eight_threads_claiming_one_fresh_id_under_a_lock_see_one_fresh(tmp_path):
    session, _ = make_session(tmp_path)
    lock = threading.Lock()
    results = []

    def go():
        with lock:
            claim = session.claim_invocation("C", "mint", DIGEST)
            if type(claim) is ClaimFresh:
                session.close_invocation("C", {"done": []})
            results.append(type(claim))

    threads = [threading.Thread(target=go) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(ClaimFresh) == 1 and results.count(ClaimDone) == 7


# --- J3: scoped is a real writer bound to the requirement -----------------------
def test_scoped_refuses_an_uncovered_requirement_before_any_writer_exists(tmp_path):
    session, ports = make_session(tmp_path, ceiling=WritePermit(frozenset({"source"}), frozenset({"corpus-write"})))
    with pytest.raises(PermitExceeded) as caught:
        session.scoped(PROPOSITIONS, "A")
    assert caught.value.requirement == PermitFact("kind", "proposition")
    assert caught.value.capability.kinds == ("source",)
    assert ports == []


def test_the_act_time_refusal_comes_from_the_kernel_with_the_requirements_summary(tmp_path):
    session, _ = make_session(tmp_path)
    writer = session.scoped(PROPOSITIONS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(PermitExceeded) as caught:
        writer.add(stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s1"}))
    assert caught.value.capability.kinds == ("proposition",)
    assert session.invocation_acts("A") == ()


def test_scoped_type_checks_its_arguments(tmp_path):
    session, _ = make_session(tmp_path)
    with pytest.raises(TypeError):
        session.scoped(WritePermit.full(), "A")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        session.scoped(PROPOSITIONS, "not valid!")


# --- J11: bound to one invocation -----------------------------------------------
def test_a_scoped_writer_acts_only_under_its_own_current_invocation(tmp_path):
    session, _ = make_session(tmp_path)
    a = session.scoped(PROPOSITIONS, "A")
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p0"))
    session.claim_invocation("A", "mint", DIGEST)
    node = a.add(proposition("p1"))
    assert node.id == "proposition:p1"
    (act,) = session.invocation_acts("A")
    assert act.record_ids == ((node.uid, node.id),) and act.corpus == CORPUS
    session.close_invocation("A", {"done": [[node.uid, node.id]]})
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p2"))
    b = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "B")
    session.claim_invocation("B", "mint", DIGEST)
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p3"))
    assert session.invocation_acts("B") == ()
    assert b.add(proposition("p3")).id == "proposition:p3"
    session.claim_invocation("C", "mint", DIGEST)  # B abandoned
    with pytest.raises(SessionProtocolError):
        b.add(proposition("p4"))


def test_two_writers_scoped_for_one_id_both_act_under_that_id(tmp_path):
    session, _ = make_session(tmp_path)
    one, two = session.scoped(PROPOSITIONS, "A"), session.scoped(PROPOSITIONS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    one.add(proposition("p1"))
    two.add(proposition("p2"))
    assert [act.invocation for act in session.invocation_acts("A")] == ["A", "A"]


def test_delete_ledgers_an_empty_record_list(tmp_path):
    session, _ = make_session(tmp_path)
    w = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "A")
    session.claim_invocation("A", "mint", DIGEST)
    w.add(proposition("p1"))
    assert w.delete("proposition:p1") is None
    assert session.invocation_acts("A")[-1].record_ids == ()


def test_the_scoped_writer_exposes_only_the_seven_methods_and_its_invocation(tmp_path):
    public = {name for name in dir(ScopedWriter) if not name.startswith("_")}
    assert public == {"add", "retract", "supersede", "revise", "delete", "mint_coordination", "revise_coordination", "invocation_id"}


# --- refusal shapes -----------------------------------------------------------------
def test_an_over_ceiling_record_through_the_scoped_writer_is_plan_refused(tmp_path):
    session, _ = make_session(tmp_path)
    w = session.scoped(PROPOSITIONS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    with pytest.raises(PlanRefused):
        w.add(proposition("p1").model_copy(update={"body": "x" * (RECORD_CEILING + 1)}))
    assert session.invocation_acts("A") == ()


def test_kernel_refusal_value_wraps_a_value_and_exposes_it():
    class Refusal:
        reason = "recipe-mismatch"

    value = Refusal()
    caught = KernelRefusalValue(value)
    assert caught.value is value and "recipe-mismatch" in str(caught)


# --- J9 lifecycle, portable half -----------------------------------------------------
def test_close_is_idempotent_and_every_later_call_is_session_closed(tmp_path):
    session, _ = make_session(tmp_path)
    session.close()
    session.close()
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert reader.closed is True
    for call in (
        lambda: session.scoped(PROPOSITIONS, "A"),
        lambda: session.claim_invocation("A", "mint", DIGEST),
        lambda: session.close_invocation("A", {"done": []}),
        lambda: session.invocation_acts("A"),
    ):
        with pytest.raises(SessionClosed):
            call()


def test_a_ledger_failure_ends_the_session(tmp_path, monkeypatch):
    import os

    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    monkeypatch.setattr(os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("gone")))
    with pytest.raises(SessionLedgerFailed):
        session.close_invocation("A", {"done": []})
    monkeypatch.undo()
    for call in (
        lambda: session.claim_invocation("B", "mint", DIGEST),
        lambda: session.scoped(PROPOSITIONS, "B"),
        lambda: session.invocation_acts("A"),
        session.close,
    ):
        with pytest.raises(SessionLedgerFailed):
            call()
    assert session.current_invocation == "A"  # the index never learned the close
