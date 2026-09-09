"""Cut 19's durable arms (design §9.2): the attended session over registered,
adopted roots on the certified volume, through the real DurableOperationPort."""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import os
import secrets
import shutil
import threading
from pathlib import Path
from typing import Any, cast

import pytest
from atoms.fs.backend import Backend
from authority import ACTOR, FULL
from coordination_fixtures import content_for, coordination_profile, pins_for
from fixtures_cut6 import PINS
from nodes.core.errors import ExecutionError
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, DefaultExecutor
from profiles import WITH_BIOLOGY
from session_faults import (
    PUBLISH_CALLS_BEFORE_RECORD,
    PUBLISH_PHASE,
    HaltingBackend,
    HaltingPort,
    TracingBackend,
)
from test_durable_families import proposition
from test_retract import PINNED, mint_eligible_assessment

from beliefs import root as science_root
from beliefs import session as session_module
from beliefs import stored
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.corpus import CorpusWriter, OperationWrites, _operation_lock_for, _root_state_for, corpus_check
from beliefs.errors import (
    ActorMismatch,
    ContractMismatch,
    ImportRefused,
    PermitExceeded,
    PermitFact,
    PlanRefused,
    RelocationTargetMissing,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
    SessionRefused,
    WriteRefused,
)
from beliefs.intents.reduce import qualify_chain
from beliefs.intents.shapes import DecodedIntent, decode_intent
from beliefs.permit import Authority, RequiredCapabilities
from beliefs.relocation import move
from beliefs.report import CLOSED, OperationIntent, Registration, completion
from beliefs.root import (
    PRODUCTION_STORAGE,
    DurableOperationPort,
    durable_executor_factory,
    init_corpus_root,
    metadata_root_for,
    open_corpus,
)
from beliefs.session import (
    ScopedWriter,
    WriterSession,
    open_attended_session,
    open_ledger_reader,
    reconcile_sessions,
)
from beliefs.session.ledger import LedgerWriter, ledger_path
from beliefs.world import WorldConfig, load_manifest
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView, WellFormedView
from beliefs.world.records import RECORD_CEILING

PROPOSITIONS = RequiredCapabilities.for_kinds({"proposition"}, {})
ORDINARY = RequiredCapabilities.for_kinds({"proposition", "retraction"}, {})
SOURCES = RequiredCapabilities.for_kinds({"source"}, {})
WIDE = RequiredCapabilities.for_kinds({"proposition", "retraction", "act-report"}, {"act-report": "corpus-write"})
ASSESSMENTS = RequiredCapabilities.for_kinds({"assessment", "retraction"}, {})
RETRACTABLE = RequiredCapabilities.for_kinds({"assessment", "proposition"}, {})
DIGEST = "d" * 64
OPENED_AT = "2026-09-05T00:00:00Z"
CLOSED_AT = "2026-09-05T00:00:01Z"

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


def adopted(work_directory: Path, name: str, pins=PINS, profile=WITH_BIOLOGY) -> Path:
    root = _track(work_directory / f"{name}-{secrets.token_hex(4)}")
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL, profile=profile).adopt_manifest(profile=pins)
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


def attended(work_directory: Path, root: Path, *, profile=WITH_BIOLOGY, **kwargs: Any) -> tuple[WriterSession, Path]:
    ops = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    return open_attended_session(config_for(work_directory, root), ops, profile=profile, **kwargs), ops


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
    target = mint_eligible_assessment(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY))
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
    library = open_corpus(twin, authority=FULL, profile=WITH_BIOLOGY)
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
        open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).add(malformed)
    with pytest.raises(WriteRefused) as operation_malformed:
        wide.add(malformed)
    assert type(operation_malformed.value) is type(ordinary_malformed.value)
    assert not isinstance(operation_malformed.value, PermitExceeded)
    assert chain(root).tip == settled_head
    assert intents(root) == []  # no intent decodes to any refused call
    target = mint_eligible_assessment(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY))
    session_head = chain(root).tip
    retraction = session_retraction(target, "proposition:p0", session.actor)
    with pytest.raises(WriteRefused) as ordinary:  # a retraction enters through retract, not add — both paths
        open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).add(retraction)
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
    root = adopted(work_directory, "coord", pins=pins_for(profile), profile=profile)
    session, _ = attended(work_directory, root, coordination=profile, profile=profile)
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
    library = open_corpus(root, authority=FULL, coordination_resolver=CoordinationResolver({root: profile}), profile=profile)
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
    plain, _ = attended(work_directory, adopted(work_directory, "coord-plain", pins=pins_for(profile), profile=profile), profile=profile)
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
    target = mint_eligible_assessment(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY))
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
    session = open_attended_session(config, ops, profile=WITH_BIOLOGY)
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
            open_attended_session(WorldConfig(work_directory / "w", secrets.token_hex(16), roots), ops2, profile=WITH_BIOLOGY)
        assert not (ops2 / "sessions").exists(), description
    ops3 = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    with pytest.raises(SessionRefused):
        open_attended_session(WorldConfig(work_directory / "w", secrets.token_hex(16), (chainless,)), ops3, profile=WITH_BIOLOGY)
    assert not (ops3 / "sessions").exists()
    # An unreadable prior ledger — a directory where the file should be — is a finding, never a refusal to open.
    ops4 = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    (ops4 / "sessions" / ("9" * 32) / "ledger.v1").mkdir(parents=True)
    (ops4 / "sessions" / ("8" * 32)).mkdir(parents=True)  # a directory with no ledger at all
    opened = open_attended_session(config_for(work_directory, root), ops4, profile=WITH_BIOLOGY)
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
    open_corpus(twin_b, authority=FULL, profile=WITH_BIOLOGY).add(node)
    a = {p.relative_to(twin_a).as_posix(): p.read_bytes() for p in twin_a.rglob("*.md")}
    b = {p.relative_to(twin_b).as_posix(): p.read_bytes() for p in twin_b.rglob("*.md")}
    assert a == b and a
    assert corpus_check(open_corpus(twin_a, authority=FULL, profile=WITH_BIOLOGY).read_view, profile=WITH_BIOLOGY) == corpus_check(
        open_corpus(twin_b, authority=FULL, profile=WITH_BIOLOGY).read_view
    , profile=WITH_BIOLOGY)
    assert inventory(twin_a) == inventory(twin_b)
    fresh(session, "B").delete("proposition:p1")
    (twin_b / "proposition" / "p1.md").unlink()
    assert {p.name for p in twin_a.rglob("*.md")} == {p.name for p in twin_b.rglob("*.md")}
    assert inventory(twin_a) == inventory(twin_b) == []
    assert corpus_check(open_corpus(twin_a, authority=FULL, profile=WITH_BIOLOGY).read_view, profile=WITH_BIOLOGY) == corpus_check(
        open_corpus(twin_b, authority=FULL, profile=WITH_BIOLOGY).read_view
    , profile=WITH_BIOLOGY)
    # Negative: the chains differ by exactly what the session added — two intents, and the
    # delete's registration and settlement that a raw unlink never appends.
    assert len(chain(twin_a).entries) == len(chain(twin_b).entries) + 4
    assert len(intents(twin_a)) == 2 and intents(twin_b) == []
    session.close()


def inventory(root: Path) -> list[str]:
    return sorted(node.id for node in open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).read_view.iter_stored())


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


def state_of(root: Path):
    return _root_state_for(root.resolve(), durable_executor_factory())


def assessment_grounds(root: Path) -> None:
    """The records an eligible assessment needs, minted through the library so the
    session's own write is the assessment alone."""
    library = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    library.add(
        stored.dataset_node("raw", title="raw", resources=PINNED, empirical_observation={"locator": "instrument:fixture", "attested_by": FULL.actor})
    )
    library.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=["dataset:raw"]))
    library.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))


def assessment(slug: str) -> Node:
    return stored.assessment_node(
        slug,
        title=slug,
        spec="analysis-spec:s1",
        run="run:r1",
        proposition="proposition:p1",
        outcome="supported",
        interpretation_rule="rule:threshold",
    )


def halting_session(work_directory: Path, root: Path) -> tuple[WriterSession, HaltingBackend, Path]:
    """A session whose scoped writers run over a halting backend; the factory's
    recovery runs over the real one."""
    backend = HaltingBackend(skip=PUBLISH_CALLS_BEFORE_RECORD)
    ops = _track(work_directory / f"ops-{secrets.token_hex(4)}")
    session_id = secrets.token_hex(16)
    path = ledger_path(ops, session_id)
    path.parent.mkdir(parents=True)

    def writer_factory(authority: Authority) -> CorpusWriter:
        port = HaltingPort(
            root,
            backend=backend,
            storage=PRODUCTION_STORAGE,
            metadata_root=metadata_root_for(root),
            authority=authority,
            profile=WITH_BIOLOGY,
        )
        return CorpusWriter(root, durable_executor_factory(), authority=authority, operation_port=port, profile=WITH_BIOLOGY)

    session = WriterSession(
        session_id=session_id,
        world_id="1" * 32,
        corpus_root=root,
        corpus_id=load_manifest(root).corpus_id,
        operations_root=ops,
        ledger=LedgerWriter(path),
        writer_factory=writer_factory,
    )
    return session, backend, ops


# --- J2 -------------------------------------------------------------------------------
def test_j2_a_failure_before_submission_leaves_an_intent_and_no_record(session_rig, monkeypatch):
    session, root, ops = session_rig
    w = fresh(session, "A")

    def refuse(**kwargs):
        raise ExecutionError("no submission", index=None, applied=0)

    monkeypatch.setattr(science_root, "_mapped_submit", refuse)
    before = len(chain(root).entries)
    with pytest.raises(ExecutionError):
        w.add(proposition("p1"))
    monkeypatch.undo()
    entries = chain(root).entries[before:]
    assert [type(e).__name__ for e in entries] == ["IntentEntryView"]
    assert not (root / "proposition" / "p1.md").exists()
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    (unknown,) = [f for f in findings if f.code == "session-outcome-unknown"]
    assert unknown.ref == entries[0].digest and "invocations=['A']" in unknown.detail
    # Negative: a failure in append_intent leaves nothing.
    monkeypatch.setattr(
        DurableOperationPort,
        "append_intent",
        lambda self, payload: (_ for _ in ()).throw(ExecutionError("no intent", index=None, applied=0)),
    )
    head = chain(root).tip
    with pytest.raises(ExecutionError):
        w.add(proposition("p2"))
    assert chain(root).tip == head


def test_j2_a_readback_failure_leaves_the_root_unresolved_and_the_registration_committed(session_rig, monkeypatch):
    session, root, ops = session_rig
    w = fresh(session, "A")
    monkeypatch.setattr(
        science_root,
        "_registration_for",
        lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)),
    )
    with pytest.raises(ExecutionError):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert (root / "proposition" / "p1.md").exists()
    (registration,) = [e for e in registrations(root) if e.fulfills is not None]
    assert state_of(root).unresolved is True
    assert session.invocation_acts("A") == ()
    assert open_ledger_reader(ops, session.session_id).acts() == ()
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    assert ("session-outcome-unknown", registration.digest) in [(f.code, f.ref) for f in findings]
    # The next write settles first and sees the record.
    w.add(proposition("p2"))
    assert state_of(root).unresolved is False
    assert open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).read_view.get("proposition:p1").id == "proposition:p1"


def test_j2_a_post_commit_rebuild_failure_on_delete_leaves_the_root_unresolved(session_rig, monkeypatch):
    """Session `add` updates the index incrementally and never rebuilds after commit; `delete`
    does (`_delete_locked` reconstructs after its execute). Fault that rebuild only."""
    session, root, ops = session_rig
    w = fresh(session, "A")
    w.add(proposition("p1"))  # settles the fresh root first, with the real rebuild
    original = CorpusWriter._reconstruct
    arm = {"on": True}

    def failing(self):
        if arm["on"]:
            arm["on"] = False
            raise RuntimeError("rebuild failed")
        return original(self)

    monkeypatch.setattr(CorpusWriter, "_reconstruct", failing)
    acts_before = session.invocation_acts("A")  # the add's act line; the faulted delete must add none
    ledgered_before = open_ledger_reader(ops, session.session_id).acts()
    with pytest.raises(ExecutionError, match="rebuild failed") as caught:  # normalized: the submission happened
        w.delete("proposition:p1")
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert not (root / "proposition" / "p1.md").exists()  # the delete committed
    assert state_of(root).unresolved is True and session.invocation_acts("A") == acts_before
    assert open_ledger_reader(ops, session.session_id).acts() == ledgered_before
    monkeypatch.undo()
    w.add(proposition("p2"))  # settles (recover, rebuild) first
    assert state_of(root).unresolved is False


def test_j2_a_post_commit_index_failure_on_add_leaves_the_root_unresolved(session_rig, monkeypatch):
    session, root, ops = session_rig
    w = fresh(session, "A")
    w.add(proposition("p0"))
    state = state_of(root)
    index_type = type(state.corpus.index)
    monkeypatch.setattr(index_type, "upsert", lambda self, node: (_ for _ in ()).throw(RuntimeError("index down")))
    with pytest.raises(ExecutionError, match="index down"):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert (root / "proposition" / "p1.md").exists()
    covered = {act.entry for act in open_ledger_reader(ops, session.session_id).acts()}
    (registration,) = [e for e in registrations(root) if e.fulfills is not None and e.digest not in covered]
    assert state.unresolved is True
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    assert ("session-outcome-unknown", registration.digest) in [(f.code, f.ref) for f in findings]
    w.add(proposition("p2"))  # settles first and sees p1
    assert state.unresolved is False and open_corpus(root, authority=FULL, profile=WITH_BIOLOGY).read_view.get("proposition:p1").id == "proposition:p1"


def test_j2_a_ledger_write_failure_after_commit_leaves_the_registration_uncovered(work_directory, monkeypatch):
    """J2's ledger clause proper: the append fails with **no bytes on disk**, so the
    committed registration is covered by no `act` line and reconciliation reports it."""
    # Not `session_rig`: this arm makes the ledger terminal, and the rig's teardown
    # closes outright — `close` on a failed ledger is `SessionLedgerFailed` (J9).
    root = adopted(work_directory, "ledger-write-fault")
    session, ops = attended(work_directory, root)
    w = fresh(session, "A")
    real_write = LedgerWriter._write

    def refusing(self, data):
        # Only the `act` append: `session-open` and `invocation-open` are already durable,
        # so the crashed session's ledger is readable and names its open invocation.
        if b'"line":"act"' in data:
            raise OSError("ledger write")
        return real_write(self, data)

    monkeypatch.setattr(LedgerWriter, "_write", refusing)
    ledger_file = ledger_path(ops, session.session_id)
    bytes_before = ledger_file.read_bytes()
    with pytest.raises(SessionLedgerFailed):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert ledger_file.read_bytes() == bytes_before  # nothing of the act line landed
    assert (root / "proposition" / "p1.md").exists()  # the record is durable
    (registration,) = [e for e in registrations(root) if e.fulfills is not None]
    settlement = {e.registration: e.committed for e in chain(root).entries if type(e) is SettledEntryView}
    assert settlement[registration.digest] is True  # the registration committed
    assert open_ledger_reader(ops, session.session_id).acts() == ()  # no act line covers it
    # No `exclude`: the crashed session is exactly what reconciliation must read.
    findings = reconcile_sessions(config_for(work_directory, root), ops)
    unknown = [f for f in findings if f.code == "session-outcome-unknown"]
    assert [f.ref for f in unknown] == [registration.digest]
    assert f"session={session.session_id}" in unknown[0].detail and "invocations=['A']" in unknown[0].detail
    assert {"session-unclosed"} <= {f.code for f in findings}
    for call in (
        lambda: session.claim_invocation("B", "mint", DIGEST),
        lambda: session.invocation_acts("A"),
        lambda: session.close(),
    ):
        with pytest.raises(SessionLedgerFailed):
            call()


def test_j2_a_ledger_fsync_failure_after_a_complete_act_line_ends_the_session(work_directory, monkeypatch):
    """The other half of the ledger clause: the write and flush succeeded and only the
    fsync raised, so the complete `act` line *is* on disk and covers the registration —
    what the arm proves is that the rebuild finished before the append and that the
    session is terminal all the same."""
    # Not `session_rig`: this arm makes the ledger terminal, and the rig's teardown
    # closes outright — `close` on a failed ledger is `SessionLedgerFailed` (J9).
    root = adopted(work_directory, "ledger-fault")
    session, ops = attended(work_directory, root)
    w = fresh(session, "A")
    real = os.fsync
    ledger_fd = session._ledger._file.fileno()
    monkeypatch.setattr(
        os, "fsync", lambda fd: (_ for _ in ()).throw(OSError("ledger fsync")) if fd == ledger_fd else real(fd)
    )
    with pytest.raises(SessionLedgerFailed):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert (root / "proposition" / "p1.md").exists()
    assert state_of(root).unresolved is False  # the rebuild completed before the append
    # The ledger — not the failed session's index — is the evidence, and here it covers the registration.
    (registration,) = [e for e in registrations(root) if e.fulfills is not None]
    reader = open_ledger_reader(ops, session.session_id)
    assert [act.entry for act in reader.acts()] == [registration.digest]
    findings = reconcile_sessions(config_for(work_directory, root), ops)
    assert registration.digest not in {f.ref for f in findings}
    assert {"session-unclosed"} <= {f.code for f in findings}
    for call in (lambda: session.claim_invocation("B", "mint", DIGEST), lambda: session.invocation_acts("A")):
        with pytest.raises(SessionLedgerFailed):
            call()


def test_j2_a_raced_precondition_is_an_execution_error(session_rig, monkeypatch):
    session, root, ops = session_rig
    w = fresh(session, "A")
    real = science_root._mapped_submit

    def race(**kwargs):
        (root / "proposition").mkdir(exist_ok=True)
        (root / "proposition" / "p1.md").write_bytes(b"raw")
        return real(**kwargs)

    monkeypatch.setattr(science_root, "_mapped_submit", race)
    with pytest.raises(ExecutionError):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert state_of(root).unresolved is True
    # §7: reconciliation, not the test, says whether a registration stands.
    findings = reconcile_sessions(config_for(ops.parent, root), ops)
    uncovered = [f for f in findings if f.code in ("session-outcome-unknown", "session-entry-pending")]
    assert [f.code for f in uncovered] == ["session-outcome-unknown"]
    assert uncovered[0].ref == intents_of_chain(chain(root))[-1]  # the intent's digest: no registration stands
    (root / "proposition" / "p1.md").unlink()
    w.add(proposition("p2"))  # settles, then commits


def test_j1_a_refusal_on_a_root_left_unresolved_moves_the_head_only_by_settlement(work_directory):
    """J1's last check, which needs J2's halting fixture: a refusal on a root left
    unresolved by a prior failed submission moves the head by recovery's settlement
    of that prior work and by nothing of the refused call's own."""
    root = adopted(work_directory, "unresolved-refusal")
    session, backend, _ops = halting_session(work_directory, root)
    w = fresh(session, "A")
    w.add(proposition("t"))
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        w.add(proposition("staged"))
    assert backend.halted and pending_registrations(root) and state_of(root).unresolved is True
    head = chain(root).tip
    before = len(chain(root).entries)
    # A permit-lacking refusal is judged before the settling hold: nothing moves at all.
    with pytest.raises(PermitExceeded):
        fresh(session, "B", SOURCES).add(proposition("nope"))
    assert chain(root).tip == head and state_of(root).unresolved is True
    assert pending_registrations(root)
    # A refusal the body makes settles first: the head moves by the prior work's settlement, and
    # by no intent and no registration of the refused call.
    huge = proposition("big").model_copy(update={"body": "x" * (RECORD_CEILING + 1)})
    with pytest.raises(PlanRefused):
        fresh(session, "C").add(huge)
    assert [type(e).__name__ for e in chain(root).entries[before:]] == ["SettledEntryView"]
    assert not pending_registrations(root) and state_of(root).unresolved is False
    session.close()


def test_j2_the_halting_backends_skip_count_names_the_records_publish(work_directory):
    """`PUBLISH_CALLS_BEFORE_RECORD` is an empirical count of the engine's publish
    sequence (§13 item 4), re-derived here through the instrument that fixed it, so a
    change in that sequence fails on the count rather than as a puzzling assertion
    inside the continuation arm."""
    root = adopted(work_directory, "traced")
    backend = TracingBackend()
    port = DurableOperationPort(
        root,
        backend=cast(Backend, backend),
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(root),
        authority=FULL,
     profile=WITH_BIOLOGY)
    # The kind directory has to exist already: a transaction that must create it publishes
    # it too, one publish *before* the record's, which is why every arm that arms the halt
    # writes a record of the same kind first.
    warm = port.append_intent(b"{}")
    port._execute_fulfilling([CreateOp(path="proposition/warm.md", content=b"warm")], warm)
    intent = port.append_intent(b"{}")
    backend.calls.clear()
    # `_execute_fulfilling` is exactly where `HaltingPort` arms, so this is the sequence
    # the skip count is counted against.
    port._execute_fulfilling([CreateOp(path="proposition/traced.md", content=b"traced")], intent)
    publishes = [name for name in backend.calls if name in PUBLISH_PHASE]
    # Four from the volume-certification probe, then the payload blob, the registration
    # leaf, the record's own publish, and the settlement: the record's is the skip count
    # plus one, and the settlement is the last.
    assert len(publishes) == PUBLISH_CALLS_BEFORE_RECORD + 2, publishes
    assert (root / "proposition" / "traced.md").read_bytes() == b"traced"
    # And the directory-creating shape is one publish longer, which the skip count would miss.
    fresh_root = adopted(work_directory, "traced-fresh")
    fresh_backend = TracingBackend()
    fresh_port = DurableOperationPort(
        fresh_root,
        backend=cast(Backend, fresh_backend),
        storage=PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(fresh_root),
        authority=FULL,
     profile=WITH_BIOLOGY)
    first = fresh_port.append_intent(b"{}")
    fresh_backend.calls.clear()
    fresh_port._execute_fulfilling([CreateOp(path="proposition/first.md", content=b"first")], first)
    assert len([name for name in fresh_backend.calls if name in PUBLISH_PHASE]) == PUBLISH_CALLS_BEFORE_RECORD + 3


def test_j2_continuation_after_unresolved_effects_recovers_before_the_prepare(work_directory):
    root = adopted(work_directory, "halting")
    assessment_grounds(root)
    session, backend, _ops = halting_session(work_directory, root)
    w = fresh(session, "A", ASSESSMENTS)
    w.add(assessment("t"))  # commits: the port arms only when a test asks
    backend.arm_next = True
    intents_before = len(intents(root))
    with pytest.raises(ExecutionError):
        w.add(assessment("staged"))
    assert backend.halted and state_of(root).unresolved is True
    assert len(intents(root)) == intents_before + 1  # the intent landed; it is the transaction that halted
    view = chain(root)
    assert pending_registrations(root), "the halt must leave a pending registration"
    assert any(
        r.fulfills == intents_of_chain(view)[-1] for r in view.entries if type(r) is RegisteredEntryView
    ), "the pending registration fulfills the new intent"
    # The engine unwinds its own staging on the way out but cannot publish its settlement, so what
    # stays staged is the chain entry itself — the bytes recovery resolves.
    stage = root / ".#~chain" / ".#~stage"
    assert stage.is_file(), "the staged settlement's bytes exist"
    assert not (root / "assessment" / "staged.md").exists()
    # Continuation through the same session: recovery first, then the prepare judges the settled state.
    session.close_invocation("A", {"done": []})
    w2 = fresh(session, "B", ASSESSMENTS)
    with pytest.raises(RelocationTargetMissing):
        w2.retract(session_retraction(assessment("staged"), "proposition:p1", session.actor))
    assert not (root / "assessment" / "staged.md").exists()
    assert not stage.exists()
    after = chain(root)
    assert not after.pending
    assert not pending_registrations(root)
    assert state_of(root).unresolved is False
    w2.add(assessment("fresh"))
    session.close()


def test_j2_a_fresh_process_settles_before_its_first_prepare(work_directory):
    import json
    import subprocess
    import sys

    root = adopted(work_directory, "cross-process")
    session, backend, ops = halting_session(work_directory, root)
    w = fresh(session, "A")
    w.add(proposition("t"))
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        w.add(proposition("staged"))
    assert pending_registrations(root), "the halt must leave a pending registration for the child to settle"
    # The child opens over the SAME operations root, so it reads this session's unclosed ledger,
    # reports the pending registration at open, and settles it before its first prepare.
    script = f"""
import json, secrets
from pathlib import Path
from test_durable_families import proposition
from beliefs import root as science_root
from beliefs.corpus import CorpusWriter
from beliefs.permit import RequiredCapabilities
from beliefs.session import open_attended_session
from beliefs.world import WorldConfig

root = Path({str(root)!r})
ops = Path({str(ops)!r})
order = []
real_settle = CorpusWriter._settle
real_prepare = CorpusWriter._refuse_family_kinds
CorpusWriter._settle = lambda self: (order.append("settle"), real_settle(self))[1]
CorpusWriter._refuse_family_kinds = lambda self, node, **k: (order.append("prepare"), real_prepare(self, node, **k))[1]
from profiles import WITH_BIOLOGY
session = open_attended_session(WorldConfig(root.parent / "w", secrets.token_hex(16), (root,)), ops, profile=WITH_BIOLOGY)
findings = sorted({{f.code for f in session.findings}})
w = session.scoped(RequiredCapabilities.for_kinds({{"proposition"}}, {{}}), "A")
session.claim_invocation("A", "mint", "d" * 64)
w.add(proposition("after"))
view = science_root.log_seam().inspect_detached(root)
settled = {{s.registration for s in view.entries if type(s).__name__ == "SettledEntryView"}}
pending = [e.digest for e in view.entries if type(e).__name__ == "RegisteredEntryView" and e.digest not in settled]
pending += [digest for _, digest in view.pending]
print(json.dumps({{
    "pending_after": pending,
    "findings": findings,
    "order": order[:2],
    "staged_gone": not (root / ".#~chain" / ".#~stage").exists(),
}}))
session.close()
"""
    tests = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(tests), str(tests / "acceptance")])},
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result["pending_after"] == []  # the child's first write settled it before its prepare
    # `add`'s first prepare is its `_refuse_family_kinds`; settlement precedes it.
    assert result["order"] == ["settle", "prepare"] and result["staged_gone"] is True
    assert "session-entry-pending" in result["findings"] and "session-unclosed" in result["findings"]
    session.close()


def test_j2_library_and_mixed_handles_settle_first(work_directory, monkeypatch):
    root = adopted(work_directory, "handles")
    session, _ops = attended(work_directory, root)
    w = fresh(session, "A", RETRACTABLE)
    target = mint_eligible_assessment(open_corpus(root, authority=FULL, profile=WITH_BIOLOGY))
    monkeypatch.setattr(
        science_root,
        "_registration_for",
        lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)),
    )
    with pytest.raises(ExecutionError):
        w.delete(target.id)  # committed; only the readback failed, so the index still holds it
    monkeypatch.undo()
    assert state_of(root).unresolved is True
    assert not (root / "assessment" / "a1.md").exists()
    order: list[str] = []
    real_settle = CorpusWriter._settle
    real_validate = CorpusWriter._validate_import_bundle
    real_preflight_add = CorpusWriter._preflight_add_locked
    monkeypatch.setattr(CorpusWriter, "_settle", lambda self: (order.append("settle"), real_settle(self))[1])
    monkeypatch.setattr(
        CorpusWriter,
        "_validate_import_bundle",
        lambda self, *a, **k: (order.append("validate"), real_validate(self, *a, **k))[1],
    )
    monkeypatch.setattr(
        CorpusWriter,
        "_preflight_add_locked",
        lambda self, node: (order.append("preflight-add"), real_preflight_add(self, node))[1],
    )
    library = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY)
    # Import: a member deriving from the deleted record — a retraction naming it as its target.
    # Settlement precedes validation, and the rebuilt index no longer resolves the target, so the
    # import is judged against disk and not against the stale index the failed delete left behind.
    bundle = [session_retraction(target, "proposition:p1", FULL.actor)]
    with pytest.raises(ImportRefused):
        library.import_bundle(bundle, observer="o", instrument="i", opened_at=OPENED_AT, closed_at=CLOSED_AT)
    assert order[:2] == ["settle", "validate"], order
    # The rebuilt index is what judged the member: the deleted record no longer resolves. The flag
    # is set again on the way out — a refused import publishes its own refusal report (§13 item 12).
    assert library.read_view.resolve(target.id) is None
    # Relocation continuation after the readback-failed delete: a real move of the deleted record.
    w.add(proposition("mover"))  # committed before the fault is armed
    real_registration_for = science_root._registration_for
    monkeypatch.setattr(
        science_root,
        "_registration_for",
        lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)),
    )
    with pytest.raises(ExecutionError):
        w.delete("proposition:mover")
    # Restored by name, not by `undo`: `undo` would also lift the three order recorders above.
    monkeypatch.setattr(science_root, "_registration_for", real_registration_for)
    assert state_of(root).unresolved is True
    order.clear()
    other = open_corpus(adopted(work_directory, "other"), authority=FULL, profile=WITH_BIOLOGY)
    with pytest.raises(RelocationTargetMissing):
        move(library, other, "proposition:mover", observer="o", instrument="i", opened_at=OPENED_AT, closed_at=CLOSED_AT)
    assert order[0] == "settle" and "preflight-add" not in order  # settled first; the missing source refused before any preflight
    # Mixed handle with staged effects: a portless durable writer over the same root recovers a halted
    # transaction through the factory's capability before its prepare.
    halted_root = adopted(work_directory, "halted-handle")
    halted, backend, _halted_ops = halting_session(work_directory, halted_root)
    hw = fresh(halted, "A")
    hw.add(proposition("t"))
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        hw.add(proposition("staged"))
    assert pending_registrations(halted_root), "the halt must leave a pending registration"
    order.clear()
    portless = CorpusWriter(halted_root, durable_executor_factory(), authority=FULL, profile=WITH_BIOLOGY)
    assert state_of(halted_root).recover == durable_executor_factory().recover
    portless.add(proposition("after"))
    assert order[0] == "settle" and not pending_registrations(halted_root) and state_of(halted_root).unresolved is False
    assert not (halted_root / ".#~chain" / ".#~stage").exists()
    never = _track(work_directory / f"never-{secrets.token_hex(4)}")
    never.mkdir()
    assert _root_state_for(never, DefaultExecutor).recover is None
    halted.close()
    session.close()


def test_j2_a_failed_recovery_refuses_the_write_before_any_prepare(session_rig, monkeypatch):
    session, root, _ops = session_rig
    w = fresh(session, "A")
    monkeypatch.setattr(
        science_root,
        "_registration_for",
        lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)),
    )
    with pytest.raises(ExecutionError):
        w.add(proposition("p1"))
    monkeypatch.undo()
    assert state_of(root).unresolved is True
    prepared: list[str] = []
    monkeypatch.setattr(CorpusWriter, "_refuse_family_kinds", lambda self, node, **k: prepared.append(node.id))
    # The root state captured the factory's bound `recover` when it was built (§13 item 3), so the
    # capability this root actually holds is the thing to fault, not the class it came from.
    monkeypatch.setattr(
        state_of(root),
        "recover",
        lambda target: (_ for _ in ()).throw(ExecutionError("engine down", index=None, applied=None)),
    )
    with pytest.raises(ExecutionError, match="engine down"):
        w.add(proposition("p2"))
    assert prepared == [] and state_of(root).unresolved is True
    monkeypatch.undo()
    w.add(proposition("p2"))
    assert state_of(root).unresolved is False


# --- J8 -------------------------------------------------------------------------------
def test_j8_reconciliation_over_the_real_root(work_directory, monkeypatch):
    root = adopted(work_directory, "reconcile")
    session, ops = attended(work_directory, root)
    fresh(session, "A").add(proposition("p1"))
    session.close_invocation("A", {"done": []})
    w = fresh(session, "B")
    monkeypatch.setattr(
        science_root,
        "_registration_for",
        lambda *a, **k: (_ for _ in ()).throw(ExecutionError("readback", index=None, applied=None)),
    )
    with pytest.raises(ExecutionError):
        w.add(proposition("p2"))
    monkeypatch.undo()
    config = config_for(work_directory, root)
    before = tree_hash(root, metadata_root_for(root), ops)
    findings = reconcile_sessions(config, ops)
    assert tree_hash(root, metadata_root_for(root), ops) == before
    assert findings == reconcile_sessions(config, ops)
    codes = {f.code for f in findings}
    assert "session-outcome-unknown" in codes and "session-unclosed" in codes
    later, _ops2 = attended(work_directory, root)  # a later endpoint over a *different* operations root
    assert {f.code for f in later.findings} == {"session-unknown"}  # this session's intents name a ledger it cannot see
    later.close()
    second = open_attended_session(config, ops, profile=WITH_BIOLOGY)
    assert second.findings == reconcile_sessions(config, ops, exclude=second.session_id)
    second.close()
    # Byte equality with an unsettled registration present (registered inspection would have resolved it).
    halted_root = adopted(work_directory, "halted")
    halted, backend, halted_ops = halting_session(work_directory, halted_root)
    hw = fresh(halted, "A")
    hw.add(proposition("t"))
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        hw.add(proposition("staged"))
    before = tree_hash(halted_root, metadata_root_for(halted_root), halted_ops)
    found = reconcile_sessions(config_for(work_directory, halted_root), halted_ops)
    assert tree_hash(halted_root, metadata_root_for(halted_root), halted_ops) == before
    assert {"session-entry-pending", "session-unclosed"} <= {f.code for f in found}
    halted.close()
    session.close()


def test_j8_reconciliation_is_lock_coherent_under_an_interleaved_write(work_directory):
    root = adopted(work_directory, "interleave")
    session, ops = attended(work_directory, root)
    w = fresh(session, "A")
    w.add(proposition("p1"))  # the record the interleaved write removes
    config = config_for(work_directory, root)
    inside = threading.Event()
    release = threading.Event()
    original = CorpusWriter._reconstruct

    def blocking(self):
        inside.set()
        release.wait(timeout=10)
        return original(self)

    # `delete` rebuilds after its execute (§13 item 15) and `add` does not, so the block sits
    # *inside* the commit: the registration is durable and the `act` line is not yet appended,
    # both under the root lock reconciliation must take.
    CorpusWriter._reconstruct = blocking
    try:
        thread = threading.Thread(target=lambda: w.delete("proposition:p1"))
        thread.start()
        assert inside.wait(timeout=10)
        done: list[tuple] = []
        reader = threading.Thread(target=lambda: done.append(reconcile_sessions(config, ops)))
        reader.start()
        reader.join(timeout=0.5)
        assert reader.is_alive(), "reconciliation must wait for the corpus lock"
        release.set()
        thread.join(timeout=10)
        reader.join(timeout=10)
        assert not thread.is_alive() and not reader.is_alive()
    finally:
        CorpusWriter._reconstruct = original
    (findings,) = done
    assert not [f for f in findings if f.code == "session-entry-foreign"]
    # The write is covered, not straddling the snapshot: its act line is on disk and no finding names it.
    covered = {act.entry for act in open_ledger_reader(ops, session.session_id).acts()}
    assert len(covered) == 2 and not [f for f in findings if f.ref in covered]
    session.close()


def test_j8_reconciliation_reads_chain_and_ledgers_under_one_hold(work_directory, monkeypatch):
    """The chain read and the ledger read both run on a thread that holds the root's operation lock
    as a writer, and the lock is held before the first and still at the second. Observed at the two
    read points themselves, not through a racing writer: an earlier form of this check let a writer
    loose after the chain read and waited a fixed half second for its durable commit to land, so
    under load an unheld lock still read as held (beliefs-d0ca64). The holder is the lock's own
    state, which is what "under one hold" means, and it is the same on every run."""
    root = adopted(work_directory, "one-hold")
    session, ops = attended(work_directory, root)
    fresh(session, "A").add(proposition("before"))  # a ledger with an act line, so the ledger read is real
    config = config_for(work_directory, root)
    lock = _operation_lock_for(root)
    seam = science_root.log_seam()
    real_inspect = seam.inspect_detached
    real_read_ledgers = session_module.read_ledger_evidence
    holds: list[tuple[str, bool]] = []

    def held_by_this_thread() -> bool:
        # The lock's holder and owner are the fact this arm is about; there is no other witness.
        with lock._condition:
            return lock._holder == "writer" and lock._writer_owner == threading.get_ident()

    def inspect_observed(target):
        holds.append(("chain", held_by_this_thread()))
        return real_inspect(target)

    def ledgers_observed(operations_root, session_id):
        holds.append(("ledgers", held_by_this_thread()))
        return real_read_ledgers(operations_root, session_id)

    # LogSeam is a frozen dataclass and log_seam() reads the module attribute at call time.
    monkeypatch.setattr(science_root, "_LOG_SEAM", dataclasses.replace(seam, inspect_detached=inspect_observed))
    monkeypatch.setattr(session_module, "read_ledger_evidence", ledgers_observed)
    findings = reconcile_sessions(config, ops)
    assert holds == [("chain", True), ("ledgers", True)], holds
    assert not held_by_this_thread(), "the hold is reconciliation's, released with it"
    assert not [f for f in findings if f.code in ("session-act-unverified", "session-entry-foreign")], findings
    assert [act.entry for act in open_ledger_reader(ops, session.session_id).acts()] == [
        e.digest for e in registrations(root) if e.fulfills is not None
    ]
    session.close()


@pytest.mark.parametrize("entry", ["ordinary", "session"])
def test_mismatching_pins_leave_durable_pending_recovery_untouched(work_directory, entry):
    root = adopted(work_directory, f"pin-before-recovery-{entry}")
    session, backend, ops = halting_session(work_directory, root)
    writer = fresh(session, "A")
    writer.add(proposition("first"))
    backend.arm_next = True
    with pytest.raises(ExecutionError):
        writer.add(proposition("pending"))
    assert backend.halted and state_of(root).unresolved
    pending = pending_registrations(root)
    assert pending and (root / ".#~chain" / ".#~stage").is_file()
    manifest = root / "corpus.yaml"
    original = manifest.read_bytes()
    manifest.write_bytes(original.replace(PINS.science_contract.encode(), ("science:" + "f" * 64).encode()))
    before = tree_hash(root, metadata_root_for(root), ops)
    target = open_corpus(root, authority=FULL, profile=WITH_BIOLOGY) if entry == "ordinary" else writer
    with pytest.raises(ContractMismatch):
        target.add(proposition("refused"))
    assert tree_hash(root, metadata_root_for(root), ops) == before
    assert pending_registrations(root) == pending and state_of(root).unresolved
    # With valid pins restored, the production factory really can settle the
    # staged transaction and continue through this same session.
    manifest.write_bytes(original)
    writer.add(proposition("after"))
    assert not pending_registrations(root) and not state_of(root).unresolved
    assert not (root / ".#~chain" / ".#~stage").exists()
    session.close()
