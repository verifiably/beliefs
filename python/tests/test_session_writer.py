"""J3, J6 and J11 portably: a WriterSession built from parts over the in-memory
executor and a synthetic-digest port (design §13 item 2)."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

import pytest
from authority import FULL, narrowed
from coordination_fixtures import coordination_profile, mounted_root, raw_add, raw_coordination_node
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder
from test_operation_writes import RecordingPort, proposition

from beliefs import session as session_module
from beliefs import stored
from beliefs.coordination import CoordinationAddress
from beliefs.corpus import CoordinationResolver, CorpusWriter
from beliefs.errors import (
    CoordinationUnavailable,
    PermitExceeded,
    PermitFact,
    PlanRefused,
    ProjectNotResolvable,
    RetractionTargetUnresolvable,
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
from beliefs.session.ledger import LedgerWriter, SelectLine, ledger_path
from beliefs.world.records import RECORD_CEILING

SESSION = "a" * 32
WORLD = "b" * 32
CORPUS = "c" * 32
DIGEST = "d" * 64


def make_session(
    tmp_path: Path,
    ceiling: WritePermit | None = None,
    *,
    store_root: Path | None = None,
    store_id: str | None = None,
    holdings_seam: Any = None,
    coordination_resolver: CoordinationResolver | None = None,
    project: CoordinationAddress | None = None,
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
        return CorpusWriter(corpus_root, DefaultExecutor, authority=authority, operation_port=port, profile=BASE)

    ledger = LedgerWriter(path)
    session = WriterSession(
        session_id=SESSION, world_id=WORLD, corpus_root=corpus_root, corpus_id=CORPUS,
        operations_root=operations_root, ledger=ledger, writer_factory=writer_factory,
        ceiling=WritePermit.full() if ceiling is None else ceiling,
        profile=BASE, store_root=store_root, store_id=store_id, holdings_seam=holdings_seam,
        coordination_resolver=coordination_resolver, project=project,
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
    session, ports = make_session(tmp_path, ceiling=narrowed(kinds={"source"}, families={"corpus-write"}).permit)
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
        writer.add(stored.source_node(title="s1", identifiers={"doi": "10.1234/s1"}))
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


def test_the_session_lock_spans_the_act_so_no_claim_interleaves_with_a_commit(tmp_path, monkeypatch):
    """§13 item 18: a claim arriving mid-commit waits, so the durable commit and
    its `act` line are one step. Without the session lock held across `perform`,
    the claiming thread would finish first and leave a committed registration
    with no `act` line in a session that stays live."""
    session, ports = make_session(tmp_path)
    writer = session.scoped(PROPOSITIONS, "A")
    session.claim_invocation("A", "mint", DIGEST)
    (port,) = ports
    committing, release = threading.Event(), threading.Event()
    submit = port.execute_fulfilling
    order: list[str] = []

    def blocking(plan, fulfills):
        committing.set()
        assert release.wait(10)
        return submit(plan, fulfills)

    monkeypatch.setattr(port, "execute_fulfilling", blocking)

    def act():
        writer.add(proposition("p1"))
        order.append("act")

    def claim():
        assert committing.wait(10)
        order.append("claim-arrives")
        session.claim_invocation("B", "mint", DIGEST)
        order.append("claim")

    acting, claiming = threading.Thread(target=act), threading.Thread(target=claim)
    acting.start()
    claiming.start()
    assert committing.wait(10)
    claiming.join(0.5)
    assert claiming.is_alive()  # blocked on the session lock the act holds
    release.set()
    acting.join(10)
    claiming.join(10)
    assert order == ["claim-arrives", "act", "claim"]
    assert len(session.invocation_acts("A")) == 1
    assert session.current_invocation == "B"


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


def test_the_scoped_writer_exposes_the_seventeen_methods_the_routes_and_its_invocation(tmp_path):
    public = {name for name in dir(ScopedWriter) if not name.startswith("_")}
    assert public == {
        "add", "retract", "attest_coreference", "correct_identifier", "supersede", "revise", "delete", "mint_coordination", "revise_coordination",
        "invocation_id", "actor", "store_id", "operation_port", "holdings_context", "acquire", "audit", "recheck",
    }


# --- the session's store and the facade's authority (session-routes design §3) ---
def test_the_facade_exposes_the_session_actor(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    writer = session.scoped(PROPOSITIONS, "A")
    assert writer.actor == session.actor == f"session:{SESSION}"


def test_store_id_without_a_store_is_a_protocol_error(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "mint", DIGEST)
    writer = session.scoped(PROPOSITIONS, "A")
    with pytest.raises(SessionProtocolError, match="no store"):
        _ = writer.store_id


def test_a_session_built_with_a_store_exposes_its_id(tmp_path):
    session, _ = make_session(tmp_path, store_root=tmp_path / "store", store_id="e" * 32)
    session.claim_invocation("A", "mint", DIGEST)
    assert session.scoped(PROPOSITIONS, "A").store_id == "e" * 32


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


def test_attended_session_refuses_an_uncompiled_profile_before_ledger_effects(tmp_path):
    from beliefs.session import open_attended_session
    from beliefs.world import WorldConfig

    config = WorldConfig(tmp_path / "world", WORLD, (tmp_path / "corpus",))
    before = tuple(tmp_path.rglob("*"))
    with pytest.raises(TypeError, match="compiled ProfileSpec"):
        open_attended_session(config, tmp_path / "ops", profile=None)  # pyright: ignore[reportArgumentType]
    assert tuple(tmp_path.rglob("*")) == before


# --- correction-remainder slice 2: the snapshot resolver reaches the writer --------
#
# `open_attended_session`'s own `writer_factory` closure passes `snapshot_resolver`
# straight through to the `CorpusWriter` it builds; a session opened without the
# port must refuse a snapshot-arm retraction exactly as a bare `CorpusWriter`
# does. Reaching that through the real session (not `make_session`'s bypass of
# `open_attended_session`) needs a registered corpus and a well-formed chain —
# both, ordinarily, the durable engine's, which is certified-volume-only. The
# durable seams (`log_seam`, `durable_executor_factory`, `durable_operation_port`)
# are swapped here for this module's own in-memory doubles so the test stays
# off the durable path entirely; nothing about the pass-through under test is a
# durable-engine behaviour.
def _attended(tmp_path, monkeypatch, *, resolver_for=lambda corpus_id: None, profile=WITH_BIOLOGY):
    """`resolver_for` is handed the adopted corpus's id, since a resolver keyed
    by it (`StubResolver`) can only be built once the corpus exists."""
    from beliefs.session import open_attended_session
    from beliefs.world import WorldConfig
    from beliefs.world.logmodel import GenesisEntryView, WellFormedView

    root = tmp_path / "corpus"
    root.mkdir()
    writer = CorpusWriter(
        root, DefaultExecutor, authority=FULL, profile=profile,
        operation_port=OperationRecorder(root, authority=FULL, profile=profile),
    )
    writer.adopt_manifest(profile=pins_for(profile))

    genesis = GenesisEntryView(digest="g" * 64, payload=b"", baseline=())

    class _StubLogSeam:
        def inspect_detached(self, _root):
            return WellFormedView(genesis=genesis, entries=(genesis,), tip=genesis.digest, pending=())

    def _stub_port(port_root, authority, *, profile):
        port = RecordingPort(authority, port_root)
        port.profile = profile
        return port

    monkeypatch.setattr(session_module, "log_seam", lambda: _StubLogSeam())
    monkeypatch.setattr(session_module, "durable_executor_factory", lambda: DefaultExecutor)
    monkeypatch.setattr(session_module, "durable_operation_port", _stub_port)

    config = WorldConfig(tmp_path / "world", WORLD, (root,))
    resolver = resolver_for(writer.corpus_id)
    return open_attended_session(config, tmp_path / "ops", profile=profile, snapshot_resolver=resolver)


def _session_snapshot_retraction(identity: str, actor: str):
    return stored.retraction_node(
        title="t1", target=stored.SnapshotTarget("producer", identity), reason="authored-error",
        rationale="the snapshot's coverage was too wide", grounds=("verification:v1",),
        actor=actor, event_token="t1",
    )


def test_attended_sessions_snapshot_resolver_reaches_the_writer(tmp_path, monkeypatch):
    from test_snapshot_retraction import S, StubResolver

    session = _attended(tmp_path, monkeypatch, resolver_for=lambda corpus_id: StubResolver({S: (corpus_id,)}))
    scoped = session.scoped(RequiredCapabilities.for_kinds({"retraction"}, {}), "A")
    session.claim_invocation("A", "mint", DIGEST)

    minted = scoped.retract(_session_snapshot_retraction(S, scoped.actor))

    assert minted.kind == "retraction"


def test_attended_session_without_a_snapshot_resolver_refuses_the_arm(tmp_path, monkeypatch):
    from test_snapshot_retraction import S

    session = _attended(tmp_path, monkeypatch)  # no snapshot_resolver
    scoped = session.scoped(RequiredCapabilities.for_kinds({"retraction"}, {}), "A")
    session.claim_invocation("A", "mint", DIGEST)

    with pytest.raises(RetractionTargetUnresolvable, match="reaches none"):
        scoped.retract(_session_snapshot_retraction(S, scoped.actor))


# --- selection (selection design §4.2) ------------------------------------------------
P, Q, D, L = ("1" * 32, "2" * 32, "3" * 32, "4" * 32)
R1, R2, R3, R4, R5 = ("5" * 32, "6" * 32, "7" * 32, "8" * 32, "9" * 32)


def projects_resolver(tmp_path: Path, base_contract) -> tuple[CoordinationResolver, Path]:
    """A resolver over one mounted root holding projects P@R1 and Q@R2."""
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path / "coordination", profile)
    raw_add(root, raw_coordination_node("project", P, R1), raw_coordination_node("project", Q, R2))
    return CoordinationResolver({root: profile}), root


def ledger_file(session: WriterSession) -> Path:
    return ledger_path(session.operations_root, SESSION)


def recorded_selection(session: WriterSession, invocation: str) -> SelectLine | None:
    record = open_ledger_reader(session.operations_root, SESSION).invocation(invocation)
    assert record is not None
    return record.selection


def test_select_project_ledgers_the_pinned_tip_and_the_index_learns_it(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    pinned = session.select_project("A", CoordinationAddress(P))
    assert pinned == CoordinationAddress(P, revision=R1)
    assert session.invocation_selection("A") == SelectLine("A", pinned)
    assert session.current_invocation == "A"  # selecting does not close the invocation
    session.close_invocation("A", {"done": []})
    session.claim_invocation("B", "project-select", DIGEST)
    assert session.select_project("B", None) is None
    assert session.invocation_selection("B") == SelectLine("B", None)
    session.close_invocation("B", {"done": []})
    session.claim_invocation("C", "mint", DIGEST)
    assert session.invocation_selection("C") is None
    assert session.invocation_selection("Z") is None
    assert recorded_selection(session, "A") == SelectLine("A", CoordinationAddress(P, revision=R1))
    assert recorded_selection(session, "B") == SelectLine("B", None)


def test_reselecting_the_standing_project_records_a_second_line(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    for invocation in ("A", "B"):
        session.claim_invocation(invocation, "project-select", DIGEST)
        assert session.select_project(invocation, CoordinationAddress(P)) == CoordinationAddress(P, revision=R1)
        session.close_invocation(invocation, {"done": []})
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert [record.selection for record in reader.invocations()] == [
        SelectLine("A", CoordinationAddress(P, revision=R1)),
        SelectLine("B", CoordinationAddress(P, revision=R1)),
    ]


def test_session_open_always_writes_the_project_key(tmp_path):
    session, _ = make_session(tmp_path, project=CoordinationAddress(P, revision=R1))
    head = json.loads(ledger_file(session).read_bytes().splitlines()[0])
    assert head["project"] == f"coord:{P}@{R1}"
    assert open_ledger_reader(session.operations_root, SESSION).initial_project == CoordinationAddress(P, revision=R1)
    (tmp_path / "unselected").mkdir()
    other, _ = make_session(tmp_path / "unselected")
    assert json.loads(ledger_file(other).read_bytes().splitlines()[0])["project"] is None


@pytest.mark.parametrize("project", [CoordinationAddress(P), CoordinationAddress(P, L, R1), f"coord:{P}@{R1}"])
def test_a_session_refuses_an_initial_project_that_is_not_pinned_to_a_project_revision(tmp_path, project):
    with pytest.raises(ValueError):
        make_session(tmp_path, project=project)  # pyright: ignore[reportArgumentType]


def test_select_project_refusals_append_nothing_and_leave_the_invocation_current(tmp_path, base_contract):
    resolver, root = projects_resolver(tmp_path, base_contract)
    raw_add(
        root,
        raw_coordination_node("project", D, R3),
        raw_coordination_node("project", D, R4),  # two standing tips: divergent
        raw_coordination_node("question", L, R5),  # a project-root address whose tip is not a project
    )
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    before = ledger_file(session).read_bytes()
    for address, refusal in (
        (CoordinationAddress("0" * 32), ProjectNotResolvable),
        (CoordinationAddress(D), ProjectNotResolvable),
        (CoordinationAddress(L), ProjectNotResolvable),
        (CoordinationAddress(P, L), ValueError),
        (CoordinationAddress(P, revision=R1), ValueError),
        (f"coord:{P}", ValueError),
    ):
        with pytest.raises(refusal) as caught:
            session.select_project("A", address)  # pyright: ignore[reportArgumentType]
        if address == CoordinationAddress(D):
            assert caught.value.tips == (R3, R4)  # pyright: ignore[reportAttributeAccessIssue]
        assert ledger_file(session).read_bytes() == before
        assert session.current_invocation == "A"
        assert session.invocation_selection("A") is None


def test_a_clear_needs_no_resolver_but_an_address_does(tmp_path):
    session, _ = make_session(tmp_path)
    session.claim_invocation("A", "project-select", DIGEST)
    with pytest.raises(CoordinationUnavailable):
        session.select_project("A", CoordinationAddress(P))
    assert session.select_project("A", None) is None


def test_a_later_revision_leaves_the_recorded_line_pinned(tmp_path, base_contract):
    resolver, root = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    session.select_project("A", CoordinationAddress(P))
    session.close_invocation("A", {"done": []})
    raw_add(root, raw_coordination_node("project", P, R5, supersedes=(f"project:{P}.{R1}",)))
    session.claim_invocation("B", "project-select", DIGEST)
    assert session.select_project("B", CoordinationAddress(P)) == CoordinationAddress(P, revision=R5)
    assert recorded_selection(session, "A") == SelectLine("A", CoordinationAddress(P, revision=R1))


def test_select_project_is_held_to_the_current_invocation_and_one_line(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    session.select_project("A", CoordinationAddress(P))
    before = ledger_file(session).read_bytes()
    with pytest.raises(SessionProtocolError):
        session.select_project("A", CoordinationAddress(Q))  # a second select in one invocation
    session.claim_invocation("B", "project-select", DIGEST)  # A is now abandoned
    with pytest.raises(SessionProtocolError):
        session.select_project("A", CoordinationAddress(Q))
    session.close_invocation("B", {"done": []})
    with pytest.raises(SessionProtocolError):
        session.select_project("B", CoordinationAddress(Q))  # no invocation is current
    after = ledger_file(session).read_bytes()
    assert after.startswith(before) and b'"line":"select"' not in after[len(before):]


def test_selection_calls_on_a_closed_session_are_session_closed(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    session.close()
    for call in (lambda: session.select_project("A", CoordinationAddress(P)), lambda: session.invocation_selection("A")):
        with pytest.raises(SessionClosed):
            call()


@pytest.mark.parametrize("fault", ["write", "flush", "fsync"])
def test_a_failed_select_append_leaves_the_index_unchanged_and_ends_the_session(tmp_path, base_contract, monkeypatch, fault):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver)
    session.claim_invocation("A", "project-select", DIGEST)
    handle = session._ledger._file

    def failing(*_args):
        raise OSError(f"{fault} failed")

    if fault == "write":
        real_write = handle.write
        monkeypatch.setattr(handle, "write", lambda data: real_write(data[:17]))  # a short write
    elif fault == "flush":
        monkeypatch.setattr(handle, "flush", failing)
    else:
        monkeypatch.setattr(os, "fsync", failing)
    with pytest.raises(SessionLedgerFailed):
        session.select_project("A", CoordinationAddress(P))
    monkeypatch.undo()
    assert session._index["A"].selection is None  # the index never learned the selection
    frozen = ledger_file(session).read_bytes()
    for call in (
        lambda: session.select_project("A", None),
        lambda: session.invocation_selection("A"),
        lambda: session.invocation_acts("A"),
        lambda: session.claim_invocation("B", "mint", DIGEST),
        lambda: session.close_invocation("A", {"done": []}),
        lambda: session.scoped(PROPOSITIONS, "A"),
        session.close,
    ):
        with pytest.raises(SessionLedgerFailed):
            call()
    assert ledger_file(session).read_bytes() == frozen  # nothing after the fault reaches the file


def test_every_act_is_attributed_to_the_selection_standing_when_it_ran(tmp_path, base_contract):
    resolver, _ = projects_resolver(tmp_path, base_contract)
    session, _ = make_session(tmp_path, coordination_resolver=resolver, project=CoordinationAddress(P, revision=R1))

    def mint(invocation: str, name: str) -> str:
        writer = session.scoped(PROPOSITIONS, invocation)
        return writer.add(proposition(name)).id

    session.claim_invocation("A", "mint", DIGEST)
    mint("A", "p1")
    session.select_project("A", CoordinationAddress(Q))  # act, then select, in one invocation
    mint("A", "p2")
    session.close_invocation("A", {"done": []})
    session.claim_invocation("B", "project-select", DIGEST)
    session.select_project("B", None)
    session.close_invocation("B", {"done": []})
    session.claim_invocation("C", "mint", DIGEST)
    mint("C", "p3")
    session.close_invocation("C", {"done": []})
    session.claim_invocation("F", "project-select", DIGEST)
    session.select_project("F", CoordinationAddress(P))
    session.claim_invocation("G", "mint", DIGEST)  # F is abandoned; its selection still stands (decision 4)
    mint("G", "p4")
    session.close_invocation("G", {"done": []})
    reader = open_ledger_reader(session.operations_root, SESSION)
    assert [(act.record_ids[0][1], project) for act, project in reader.attributed_acts()] == [
        ("proposition:p1", CoordinationAddress(P, revision=R1)),
        ("proposition:p2", CoordinationAddress(Q, revision=R2)),
        ("proposition:p3", None),
        ("proposition:p4", CoordinationAddress(P, revision=R1)),
    ]
