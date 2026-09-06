"""Cut 19's durable arms (design §9.2): the attended session over registered,
adopted roots on the certified volume, through the real DurableOperationPort."""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import secrets
import shutil
import threading
from pathlib import Path
from typing import Any

import pytest
from authority import ACTOR, FULL
from coordination_fixtures import content_for, coordination_profile, pins_for
from fixtures_cut6 import PINS
from nodes.core.node import Node
from test_durable_families import proposition
from test_retract import mint_eligible_assessment

from beliefs import root as science_root
from beliefs import stored
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.corpus import OperationWrites, _operation_lock_for, corpus_check
from beliefs.errors import (
    ActorMismatch,
    PermitExceeded,
    PermitFact,
    PlanRefused,
    SessionClosed,
    SessionProtocolError,
    SessionRefused,
    WriteRefused,
)
from beliefs.intents.reduce import qualify_chain
from beliefs.intents.shapes import DecodedIntent, decode_intent
from beliefs.permit import RequiredCapabilities
from beliefs.report import CLOSED, OperationIntent, Registration, completion
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.session import ScopedWriter, WriterSession, open_attended_session, open_ledger_reader
from beliefs.session.ledger import ledger_path
from beliefs.world import WorldConfig
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView, WellFormedView
from beliefs.world.records import RECORD_CEILING

PROPOSITIONS = RequiredCapabilities.for_kinds({"proposition"}, {})
ORDINARY = RequiredCapabilities.for_kinds({"proposition", "retraction"}, {})
SOURCES = RequiredCapabilities.for_kinds({"source"}, {})
WIDE = RequiredCapabilities.for_kinds({"proposition", "retraction", "act-report"}, {"act-report": "corpus-write"})
DIGEST = "d" * 64

_TRACKED: list[Path] = []
"""Every directory this module makes on the certified volume, swept per test.

The `work_directory` fixture is session-scoped and deliberately never removed —
concurrent acceptance processes share it — so each root here is its own to
clean, exactly as `durable_root` cleans its own.
"""


def _track(path: Path) -> Path:
    _TRACKED.append(path)
    return path


@pytest.fixture(autouse=True)
def _swept():
    yield
    for path in _TRACKED:
        shutil.rmtree(path, ignore_errors=True)
        shutil.rmtree(metadata_root_for(path), ignore_errors=True)
    _TRACKED.clear()


def adopted(work_directory: Path, name: str, pins=PINS) -> Path:
    root = _track(work_directory / f"{name}-{secrets.token_hex(4)}")
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL).adopt_manifest(profile=pins)
    return root


def session_retraction(target: Node, ground: str, actor: str) -> Node:
    """A well-formed retraction of an eligible target, stamped for the given actor
    (the shared `retraction_for` hardcodes the test actor, which `retract` refuses
    for a session-bound writer)."""
    identity = stored.stored_semantic_hash(target)
    assert identity is not None
    return stored.retraction_node(
        title="retraction",
        target=stored.NodeTarget(target.id, target.id, identity),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=(ground,),
        actor=actor,
        event_token=secrets.token_hex(8),
    )


def config_for(work_directory: Path, root: Path) -> WorldConfig:
    return WorldConfig(work_directory / "world", secrets.token_hex(16), (root,))


def attended(work_directory: Path, root: Path, **kwargs: Any) -> tuple[WriterSession, Path]:
    ops = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    return open_attended_session(config_for(work_directory, root), ops, **kwargs), ops


def chain(root: Path) -> WellFormedView:
    view = science_root.log_seam().inspect_detached(root)
    assert type(view) is WellFormedView
    return view


def operation_of(entry: IntentEntryView) -> OperationIntent:
    decoded = decode_intent(entry.digest, entry.payload)
    assert type(decoded) is DecodedIntent
    value = decoded.value
    assert type(value) is OperationIntent
    return value


def intents(root: Path) -> list[OperationIntent]:
    return [operation_of(e) for e in chain(root).entries if type(e) is IntentEntryView]


def registrations(root: Path) -> list[RegisteredEntryView]:
    return [e for e in chain(root).entries if type(e) is RegisteredEntryView]


def pending_registrations(root: Path) -> list[str]:
    """Registrations the detached view holds without a settlement, plus the view's own pending digests."""
    view = chain(root)
    settled = {s.registration for s in view.entries if type(s) is SettledEntryView}
    unsettled = [e.digest for e in view.entries if type(e) is RegisteredEntryView and e.digest not in settled]
    return unsettled + [digest for _, digest in view.pending]


def intents_of_chain(view: WellFormedView) -> list[str]:
    return [e.digest for e in view.entries if type(e) is IntentEntryView]


def tree_hash(*roots: Path) -> str:
    digest = hashlib.sha256()
    for root in roots:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture()
def session_rig(work_directory):
    root = adopted(work_directory, "corpus")
    session, ops = attended(work_directory, root)
    try:
        yield session, root, ops
    finally:
        # `close` is idempotent (J9) and no arm here faults the ledger, so the
        # teardown closes outright rather than swallowing whatever it raises.
        session.close()


def fresh(session: WriterSession, invocation: str, required: RequiredCapabilities = PROPOSITIONS) -> ScopedWriter:
    writer = session.scoped(required, invocation)
    session.claim_invocation(invocation, "mint", DIGEST)
    return writer


def triple(entries, offset: int) -> tuple[IntentEntryView, RegisteredEntryView, SettledEntryView]:
    intent, registration, settlement = entries[offset], entries[offset + 1], entries[offset + 2]
    assert type(intent) is IntentEntryView
    assert type(registration) is RegisteredEntryView
    assert type(settlement) is SettledEntryView
    return intent, registration, settlement


# --- J1 ---------------------------------------------------------------------------
def test_j1_each_scoped_write_is_one_intent_and_one_fulfilling_registration(session_rig, work_directory):
    session, root, _ = session_rig
    # An eligible retraction target (assessment) minted through the library path: a proposition is not retractable.
    target = mint_eligible_assessment(open_corpus(root, authority=FULL))
    before = len(chain(root).entries)
    w = fresh(session, "A", ORDINARY)
    w.add(proposition("q1"))
    q2 = w.add(proposition("q2"))
    w.revise(q2.model_copy(update={"title": "renamed"}))
    w.supersede(proposition("q3", "inhibits"), of="proposition:q1")
    w.retract(session_retraction(target, "proposition:q3", session.actor))
    w.delete("proposition:q3")
    entries = chain(root).entries[before:]
    kinds = [type(e).__name__ for e in entries]
    assert kinds == ["IntentEntryView", "RegisteredEntryView", "SettledEntryView"] * 6
    for offset in range(0, len(entries), 3):
        intent_entry, registration, settlement = triple(entries, offset)
        decoded = operation_of(intent_entry)
        assert decoded.kind == "corpus-write" and decoded.actor == session.actor
        assert registration.fulfills == intent_entry.digest and settlement.committed
    rows, _findings = qualify_chain(chain(root).entries, records={}, state_facts=science_root.log_seam().state_facts)
    operations = [row for row in rows if row.shape == "operation"]
    assert len(operations) == 6 and {row.status for row in operations} == {"matched"}
    for offset in range(0, len(entries), 3):
        intent_entry, registration, _settlement = triple(entries, offset)
        decoded = operation_of(intent_entry)
        fulfillment = Registration(intent_token=decoded.event_token, pointer=registration.digest)
        assert completion(decoded, (fulfillment,), held={}) == CLOSED
    # Negative: the same methods through the ordinary CorpusWriter append no intent.
    twin = adopted(work_directory, "ordinary")
    library = open_corpus(twin, authority=FULL)
    twin_target = mint_eligible_assessment(library)
    library.add(proposition("q1"))
    r2 = library.add(proposition("q2"))
    library.revise(r2.model_copy(update={"title": "renamed"}))
    library.supersede(proposition("q3", "inhibits"), of="proposition:q1")
    library.retract(session_retraction(twin_target, "proposition:q3", ACTOR))
    library.delete("proposition:q3")
    assert intents(twin) == []


def test_j1_refusals_append_nothing_of_their_own(session_rig):
    session, root, _ = session_rig
    settled_head = chain(root).tip  # the probe: a settled, non-writing read
    w = fresh(session, "A", PROPOSITIONS)
    source = stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s"})
    huge = proposition("big").model_copy(update={"body": "x" * (RECORD_CEILING + 1)})
    for exception, call in (
        (PermitExceeded, lambda: w.add(source)),
        (PlanRefused, lambda: w.add(huge)),
    ):
        with pytest.raises(exception):
            call()
        assert chain(root).tip == settled_head
    # Under a requirement that names every kind these records carry, the refusal is the body's:
    # the operation twin raises the exact class the ordinary `add` raises for the same record,
    # and it is not the permit's — `WriteRefused` alone would be satisfied by `PermitExceeded`.
    wide = fresh(session, "B", WIDE)
    malformed = proposition("p1").model_copy(update={"kind": "act-report"})
    with pytest.raises(WriteRefused) as ordinary_malformed:
        open_corpus(root, authority=FULL).add(malformed)
    with pytest.raises(WriteRefused) as operation_malformed:
        wide.add(malformed)
    assert type(operation_malformed.value) is type(ordinary_malformed.value)
    assert not isinstance(operation_malformed.value, PermitExceeded)
    assert chain(root).tip == settled_head
    assert intents(root) == []  # no intent decodes to any refused call
    target = mint_eligible_assessment(open_corpus(root, authority=FULL))
    session_head = chain(root).tip
    retraction = session_retraction(target, "proposition:p0", session.actor)
    with pytest.raises(WriteRefused) as ordinary:  # a retraction enters through retract, not add — both paths
        open_corpus(root, authority=FULL).add(retraction)
    with pytest.raises(WriteRefused) as operation:
        wide.add(retraction)
    assert type(operation.value) is type(ordinary.value)
    assert not isinstance(operation.value, PermitExceeded)
    assert chain(root).tip == session_head
    # Each of the seven refused under a permit lacking its kind: the kernel's own `require`
    # runs before the body, so an argument that would refuse later never gets there.
    lacking = fresh(session, "C", SOURCES)
    for call in (
        lambda: lacking.add(proposition("nope")),
        lambda: lacking.retract(retraction),
        lambda: lacking.supersede(proposition("nope-2", "inhibits"), of="proposition:p1"),
        lambda: lacking.revise(proposition("nope-3")),
        lambda: lacking.delete("proposition:p1"),
        lambda: lacking.mint_coordination("project", content=content_for("project")),
        lambda: lacking.revise_coordination(
            "project", CoordinationAddress("0" * 32), predecessors=["0" * 32], content=content_for("project")
        ),
    ):
        with pytest.raises(PermitExceeded):
            call()
        assert chain(root).tip == session_head
    assert intents(root) == []


def test_j1_coordination_writes_commit_as_operations(work_directory, base_contract):
    from beliefs.corpus import CoordinationResolver
    from beliefs.errors import CoordinationUnavailable

    profile = coordination_profile(base_contract)
    root = adopted(work_directory, "coord", pins=pins_for(profile))
    session, _ = attended(work_directory, root, coordination=profile)
    before = len(chain(root).entries)
    w = fresh(session, "A", RequiredCapabilities.coordination())
    project = w.mint_coordination("project", content=content_for("project", name="first"))
    address = coordination_revision(project).address
    revised = w.revise_coordination(
        "project", address, predecessors=[project.uid], content=content_for("project", name="second")
    )
    entries = chain(root).entries[before:]
    assert [type(e).__name__ for e in entries] == ["IntentEntryView", "RegisteredEntryView", "SettledEntryView"] * 2
    for offset in range(0, len(entries), 3):
        intent_entry, registration, settlement = triple(entries, offset)
        decoded = operation_of(intent_entry)
        assert decoded.kind == "corpus-write" and decoded.actor == session.actor
        assert registration.fulfills == intent_entry.digest and settlement.committed
    assert [act.record_ids for act in session.invocation_acts("A")] == [
        ((project.uid, project.id),),
        ((revised.uid, revised.id),),
    ]
    session.close()
    # Negative: the two coordination methods through the ordinary CorpusWriter append no intent.
    library = open_corpus(root, authority=FULL, coordination_resolver=CoordinationResolver({root: profile}))
    minted = len(intents(root))
    other = library.mint_coordination("project", content=content_for("project", name="third"))
    library.revise_coordination(
        "project",
        coordination_revision(other).address,
        predecessors=[other.uid],
        content=content_for("project", name="fourth"),
    )
    assert len(intents(root)) == minted
    # Negative: without the launcher's profile the two methods refuse at the act, as an unmounted writer does.
    plain, _ = attended(work_directory, adopted(work_directory, "coord-plain", pins=pins_for(profile)))
    unmounted = fresh(plain, "A", RequiredCapabilities.coordination())
    with pytest.raises(CoordinationUnavailable):
        unmounted.mint_coordination("project", content=content_for("project"))
    with pytest.raises(CoordinationUnavailable):
        unmounted.revise_coordination(
            "project", address, predecessors=[project.uid], content=content_for("project")
        )
    plain.close()


# --- J3 -----------------------------------------------------------------------------
def test_j3_the_act_time_refusal_is_the_kernels_under_a_full_permit_session(session_rig):
    session, root, _ = session_rig
    head = chain(root).tip
    w = fresh(session, "A")
    source = stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s"})
    with pytest.raises(PermitExceeded) as caught:
        w.add(source)
    assert caught.value.requirement == PermitFact("kind", "source") and caught.value.capability.kinds == ("proposition",)
    assert session.invocation_acts("A") == () and chain(root).tip == head
    with pytest.raises(PermitExceeded) as coordination:
        fresh(session, "B", RequiredCapabilities.coordination()).add(proposition("p"))
    assert coordination.value.requirement == PermitFact("kind", "proposition")
    assert session.invocation_acts("B") == ()
    # Negative: the same acts under a requirement that names them are minted.
    minting = fresh(session, "C", SOURCES)
    assert minting.add(source).kind == "source"
    assert len(session.invocation_acts("C")) == 1
    assert fresh(session, "D", PROPOSITIONS).add(proposition("p")).kind == "proposition"


# --- J4 -----------------------------------------------------------------------------
def test_j4_every_intent_carries_the_session_actor(session_rig):
    session, root, _ = session_rig
    target = mint_eligible_assessment(open_corpus(root, authority=FULL))
    w = fresh(session, "A", ORDINARY)
    w.add(proposition("q1"))
    foreign = session_retraction(target, "proposition:q1", "someone-else")
    head = chain(root).tip
    with pytest.raises(ActorMismatch):
        w.retract(foreign)
    assert chain(root).tip == head
    w.retract(session_retraction(target, "proposition:q1", session.actor))
    assert {i.actor for i in intents(root)} == {session.actor}
    # No session or scoped method accepts an actor: the actor is `Authority.actor`, always.
    for owner in (WriterSession, ScopedWriter, OperationWrites):
        for name, member in inspect.getmembers(owner, inspect.isfunction):
            assert "actor" not in inspect.signature(member).parameters, f"{owner.__name__}.{name}"


# --- J5 -----------------------------------------------------------------------------
def test_j5_the_act_line_carries_the_chain_registration_and_is_fsynced_under_the_lock(session_rig, monkeypatch):
    session, root, ops = session_rig
    ledger_file = ledger_path(ops, session.session_id)
    lock = _operation_lock_for(root)
    holders: list[tuple[object, bool]] = []
    sizes: list[int] = []
    fsyncs: list[int] = []
    real_record = session._record_act
    real_fsync = os.fsync

    def recording(invocation, commit):
        # The row's evidence: the append happens while this thread still holds the lock the commit held.
        holders.append((lock._holder, lock._writer_owner == threading.get_ident()))
        sizes.append(ledger_file.stat().st_size)
        return real_record(invocation, commit)

    def counting(fd):
        fsyncs.append(fd)
        return real_fsync(fd)

    monkeypatch.setattr(session, "_record_act", recording)
    monkeypatch.setattr(os, "fsync", counting)
    assert lock._holder is None  # the observation below is a reading, not a constant
    w = fresh(session, "A")
    node = w.add(proposition("p1"))
    assert holders == [("writer", True)]
    assert ledger_file.stat().st_size > sizes[0]
    # §7 J5 reads the ledger *back*: the assertions below are off the persisted line, so a
    # durable `act` carrying an `entry` the chain does not hold fails here whatever the
    # in-memory index says. The index is asserted alongside, never instead.
    (persisted,) = open_ledger_reader(ops, session.session_id).acts()
    (act,) = session.invocation_acts("A")
    registration = next(e for e in registrations(root) if e.fulfills == persisted.intent)
    assert persisted.entry == registration.digest and persisted.record_ids == ((node.uid, node.id),)
    assert (act.entry, act.intent, act.record_ids) == (persisted.entry, persisted.intent, persisted.record_ids)
    assert ledger_file.read_bytes().endswith(b"\n")
    assert session._ledger._file.fileno() in fsyncs
    w.delete("proposition:p1")
    deleted = open_ledger_reader(ops, session.session_id).acts()[-1]
    assert deleted.record_ids == () and session.invocation_acts("A")[-1].record_ids == ()
    assert deleted.entry == next(e for e in registrations(root) if e.fulfills == deleted.intent).digest
    assert holders[-1] == ("writer", True)


# --- J9 -----------------------------------------------------------------------------
def test_j9_lifecycle_and_the_refusing_configurations(work_directory):
    root = adopted(work_directory, "corpus")
    # `attended` mints the world config inside itself, and J9 compares the world id the
    # `session-open` line carries against the config's *exactly*, so this arm builds the
    # config and hands it to the constructor rather than going through the helper.
    config = config_for(work_directory, root)
    ops = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    session = open_attended_session(config, ops)
    reader = open_ledger_reader(ops, session.session_id)
    assert reader.actor == session.actor == f"session:{session.session_id}"
    assert reader.world_id == config.world_id and reader.closed is False
    # The whole `session-open` line, permit summary included, read off the file.
    opened = json.loads(ledger_path(ops, session.session_id).read_bytes().splitlines()[0])
    ceiling = FULL.permit.summary()  # the attended constructor's ceiling is the full permit
    assert opened["line"] == "session-open" and opened["session"] == session.session_id
    assert opened["actor"] == session.actor and opened["world"] == config.world_id
    assert opened["permit"] == {
        "kinds": list(ceiling.kinds),
        "act_families": list(ceiling.act_families),
        "ungoverned": ceiling.ungoverned,
    }
    session.claim_invocation("A", "mint", DIGEST)
    session.close()
    session.close()
    reader = open_ledger_reader(ops, session.session_id)
    assert reader.closed is True and reader.open_invocations == ("A",)
    assert ledger_path(ops, session.session_id).read_bytes().count(b'"session-close"') == 1
    for call in (
        lambda: session.scoped(PROPOSITIONS, "B"),
        lambda: session.claim_invocation("B", "mint", DIGEST),
        lambda: session.invocation_acts("A"),
        lambda: session.close_invocation("A", {"done": []}),
    ):
        with pytest.raises(SessionClosed):
            call()
    # Refusing configurations, no sessions/ entry created.
    registered_no_manifest = _track(work_directory / f"unadopted-{secrets.token_hex(4)}")
    init_corpus_root(registered_no_manifest, authority=FULL)
    plain = _track(work_directory / f"plain-{secrets.token_hex(4)}")
    plain.mkdir()
    missing = work_directory / f"missing-{secrets.token_hex(4)}"
    other = adopted(work_directory, "other")
    chainless = adopted(work_directory, "chainless")
    shutil.rmtree(chainless / ".#~chain")  # the chain lives under the root; removing it is AbsentView
    for description, roots in (
        ("zero roots", ()),
        ("two roots", (root, other)),
        ("missing root", (missing,)),
        ("existing, never registered", (plain,)),
        ("registered, no manifest", (registered_no_manifest,)),
    ):
        ops2 = _track(work_directory / f"ops-{secrets.token_hex(4)}")
        with pytest.raises(SessionRefused):
            open_attended_session(WorldConfig(work_directory / "w", secrets.token_hex(16), roots), ops2)
        assert not (ops2 / "sessions").exists(), description
    ops3 = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    with pytest.raises(SessionRefused):
        open_attended_session(WorldConfig(work_directory / "w", secrets.token_hex(16), (chainless,)), ops3)
    assert not (ops3 / "sessions").exists()
    # An unreadable prior ledger — a directory where the file should be — is a finding, never a refusal to open.
    ops4 = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    (ops4 / "sessions" / ("9" * 32) / "ledger.v1").mkdir(parents=True)
    (ops4 / "sessions" / ("8" * 32)).mkdir(parents=True)  # a directory with no ledger at all
    opened = open_attended_session(config_for(work_directory, root), ops4)
    codes = {(f.code, f.ref) for f in opened.findings}
    assert ("session-ledger-malformed", "9" * 32) in codes and ("session-ledger-missing", "8" * 32) in codes
    opened.close()


# --- J10 ----------------------------------------------------------------------------
def test_j10_a_session_write_is_indistinguishable_on_ordinary_read(work_directory):
    twin_a = adopted(work_directory, "twin-a")
    twin_b = adopted(work_directory, "twin-b")
    session, _ops = attended(work_directory, twin_a)
    node = proposition("p1")
    fresh(session, "A").add(node)
    open_corpus(twin_b, authority=FULL).add(node)
    a = {p.relative_to(twin_a).as_posix(): p.read_bytes() for p in twin_a.rglob("*.md")}
    b = {p.relative_to(twin_b).as_posix(): p.read_bytes() for p in twin_b.rglob("*.md")}
    assert a == b and a
    assert corpus_check(open_corpus(twin_a, authority=FULL).read_view) == corpus_check(
        open_corpus(twin_b, authority=FULL).read_view
    )
    assert inventory(twin_a) == inventory(twin_b)
    fresh(session, "B").delete("proposition:p1")
    (twin_b / "proposition" / "p1.md").unlink()
    assert {p.name for p in twin_a.rglob("*.md")} == {p.name for p in twin_b.rglob("*.md")}
    assert inventory(twin_a) == inventory(twin_b) == []
    assert corpus_check(open_corpus(twin_a, authority=FULL).read_view) == corpus_check(
        open_corpus(twin_b, authority=FULL).read_view
    )
    # Negative: the chains differ by exactly what the session added — two intents, and the
    # delete's registration and settlement that a raw unlink never appends.
    assert len(chain(twin_a).entries) == len(chain(twin_b).entries) + 4
    assert len(intents(twin_a)) == 2 and intents(twin_b) == []
    session.close()


def inventory(root: Path) -> list[str]:
    return sorted(node.id for node in open_corpus(root, authority=FULL).read_view.iter_stored())


# --- J11 ----------------------------------------------------------------------------
def test_j11_a_writer_is_bound_to_one_invocation_durably(session_rig):
    session, root, ops = session_rig

    def ledgered(invocation: str) -> list[str]:
        """The act lines the *file* holds for one invocation, read through a fresh reader."""
        return [act.invocation for act in open_ledger_reader(ops, session.session_id).acts() if act.invocation == invocation]

    a = session.scoped(PROPOSITIONS, "A")
    head = chain(root).tip
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p0"))
    assert chain(root).tip == head
    session.claim_invocation("A", "mint", DIGEST)
    a.add(proposition("p1"))
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p2"))
    b = session.scoped(RequiredCapabilities.for_kinds({"proposition"}, {}), "B")
    session.claim_invocation("B", "mint", DIGEST)
    head = chain(root).tip
    with pytest.raises(SessionProtocolError):
        a.add(proposition("p3"))
    assert chain(root).tip == head and session.invocation_acts("B") == () and ledgered("B") == []
    b.add(proposition("p3"))
    assert ledgered("B") == ["B"]
    session.claim_invocation("C", "mint", DIGEST)
    with pytest.raises(SessionProtocolError):
        b.add(proposition("p4"))
    # Negative: two writers scoped for one id under one claim both act, and every act ledgers under that id.
    one, two = session.scoped(PROPOSITIONS, "D"), session.scoped(PROPOSITIONS, "D")
    session.claim_invocation("D", "mint", DIGEST)
    one.add(proposition("p5"))
    two.add(proposition("p6"))
    assert [act.invocation for act in session.invocation_acts("D")] == ["D", "D"]
    assert ledgered("D") == ["D", "D"]  # durably, off the file the writer fsynced
