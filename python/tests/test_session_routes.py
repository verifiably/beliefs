"""The invocation-scoped run and holdings routes."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from authority import FULL
from fixtures_cut3 import run_assessment, run_production
from holdings_transport_fixtures import Scripted, scripted_seam
from nodes.core.errors import ExecutionError
from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.write_plan import CreateOp, DeleteOp
from profiles import BASE, pins_for
from test_boundary import _assessment
from test_operation_writes import proposition
from test_session_writer import CORPUS, DIGEST, make_session

from beliefs import root as science_root
from beliefs.boundary import RunMinted, RunRefused
from beliefs.corpus import _operation_lock_for
from beliefs.errors import SessionLedgerFailed, SessionProtocolError, StoreWriteRefused
from beliefs.holdings.acquire import AcquisitionRequest, ResourceRequest
from beliefs.holdings.boundary import ActContext, delete, move, recheck, tree_write, write
from beliefs.holdings.records import StoreLocator, StoreTreeLocator, url_locator
from beliefs.holdings.seam import (
    AbsentStateView,
    FileStateView,
    PathObservedView,
    StoreActSeam,
    StoreOutcomeView,
)
from beliefs.holdings.transport import RetrievalBounds
from beliefs.permit import RequiredCapabilities
from beliefs.report import PublishedObservation
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus
from beliefs.runrecord import GuardedCommit
from beliefs.session import open_attended_session, open_ledger_reader, reconcile_sessions
from beliefs.session.routes import plan_records
from beliefs.world.logmodel import RegisteredEntryView, SettledEntryView, WellFormedView
from beliefs.world.registry import WorldConfig

RUNS = RequiredCapabilities.for_kinds({"run", "dataset", "act-report"}, {"run": "run", "act-report": "run"})
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


def test_execute_is_refused_before_the_inner_port(tmp_path):
    _session, _writer, port, inner = _run_port(tmp_path)
    with pytest.raises(SessionProtocolError, match="fulfilling"):
        port.execute(_plan(proposition("p")))
    assert inner.calls == []


# --- the guarded ledgered commit ----------


def test_the_guarded_form_ledgers_the_primary_plan_when_the_guard_passes(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    node = proposition("p")
    fulfills = port.append_intent(b"intent")
    commit = port.execute_fulfilling_guarded(_plan(node), fulfills, guard=lambda _v: None, fallback=lambda _r: ())
    assert type(commit) is GuardedCommit
    (act,) = session.invocation_acts("A")
    assert commit.reason is None
    assert (act.intent, act.entry, act.record_ids) == (fulfills, commit.entry, ((node.uid, node.id),))
    assert inner.calls[-1] == ("execute_fulfilling", (_plan(node), fulfills))


def test_the_guarded_form_ledgers_the_fallback_plan_when_the_guard_refuses(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    node, other = proposition("p"), proposition("q")
    fulfills = port.append_intent(b"intent")
    reasons: list[str] = []

    def fallback(reason: str):
        reasons.append(reason)
        return _plan(other)

    commit = port.execute_fulfilling_guarded(_plan(node), fulfills, guard=lambda _v: "stale", fallback=fallback)
    (act,) = session.invocation_acts("A")
    assert commit.reason == "stale" and reasons == ["stale"]
    assert (act.intent, act.entry, act.record_ids) == (fulfills, commit.entry, ((other.uid, other.id),))
    assert inner.calls[-1] == ("execute_fulfilling", (_plan(other), fulfills))


def test_a_non_current_invocation_refuses_the_guarded_form_before_the_inner_port(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    session.close_invocation("A", {"done": []})
    guarded: list[object] = []
    with pytest.raises(SessionProtocolError, match="current invocation"):
        port.execute_fulfilling_guarded(
            _plan(proposition("p")), INTENT, guard=lambda view: guarded.append(view), fallback=lambda _r: ()
        )
    assert inner.calls == [] and guarded == []
    assert session.invocation_acts("A") == ()


def test_a_non_create_primary_plan_is_refused_before_the_inner_port(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    guarded: list[object] = []
    with pytest.raises(SessionProtocolError, match="creates only"):
        port.execute_fulfilling_guarded(
            (DeleteOp("x.md", expected_digest="a" * 64),),
            INTENT,
            guard=lambda view: guarded.append(view),
            fallback=lambda _r: (),
        )
    assert inner.calls == [] and guarded == []
    assert session.invocation_acts("A") == () and session.current_invocation == "A"


def test_a_non_create_fallback_plan_is_refused_before_it_commits(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    fulfills = port.append_intent(b"intent")
    with pytest.raises(SessionProtocolError, match="creates only"):
        port.execute_fulfilling_guarded(
            _plan(proposition("p")),
            fulfills,
            guard=lambda _v: "r",
            fallback=lambda _r: [DeleteOp("x.md", expected_digest="a" * 64)],
        )
    assert "execute_fulfilling" not in [kind for kind, _ in inner.calls]
    assert session.invocation_acts("A") == () and session.current_invocation == "A"


def test_a_raising_guard_commits_and_ledgers_nothing(tmp_path):
    session, _writer, port, inner = _run_port(tmp_path)
    fulfills = port.append_intent(b"intent")

    def guard(_view):
        raise RuntimeError("the guard failed")

    with pytest.raises(RuntimeError, match="the guard failed"):
        port.execute_fulfilling_guarded(_plan(proposition("p")), fulfills, guard=guard, fallback=lambda _r: ())
    assert "execute_fulfilling" not in [kind for kind, _ in inner.calls]
    assert session.invocation_acts("A") == () and session.current_invocation == "A"


def durable_session(work: Path):
    """A durable attended session over one adopted corpus root, invocation "A"
    claimed and scoped to RUNS, and its ledgered operation port."""
    root = work / "corpus"
    init_corpus_root(root, authority=FULL)
    open_corpus(root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
    config = WorldConfig(work / "world", "e" * 32, (root,))
    init_world_root(config, authority=FULL)
    session = open_attended_session(config, work / "ops", write_root=root, profile=BASE, mounts={root: BASE})
    session.claim_invocation("A", "run", DIGEST)
    writer = session.scoped(RUNS, "A")
    return session, writer, writer.operation_port()


def _registrations(root: Path) -> list[RegisteredEntryView]:
    view = science_root.log_seam().inspect_detached(root)
    assert type(view) is WellFormedView
    return [entry for entry in view.entries if type(entry) is RegisteredEntryView]


def _registered(root: Path, fulfills: str) -> list[RegisteredEntryView]:
    return [entry for entry in _registrations(root) if entry.fulfills == fulfills]


def _record_path(root: Path, node) -> Path:
    return root / node.kind / f"{node.id.split(':', 1)[1]}.md"


def test_a_production_run_through_the_session_port_commits_and_ledgers(certified_work):
    session, _writer, port = durable_session(certified_work)
    root = session.corpus_root
    result = run_production(certified_work / "work", port=port)
    assert type(result) is RunMinted
    registrations = [entry for entry in _registrations(root) if entry.fulfills is not None]
    (act,) = session.invocation_acts("A")
    assert [(r.digest, r.fulfills) for r in registrations] == [(act.entry, act.intent)]
    from nodes.core.paths import path_for_node_id

    from beliefs.production import mint_dataset

    run_node = node_from_markdown((root / "run" / f"{result.run.address()}.md").read_text())
    minted = mint_dataset(result.run, existing_bases={})
    dataset_node = node_from_markdown((root / path_for_node_id(minted.address)).read_text())
    assert act.record_ids == ((run_node.uid, run_node.id), (dataset_node.uid, dataset_node.id))
    session.close_invocation("A", {"done": [list(pair) for pair in act.record_ids]})
    session.close()
    config = WorldConfig(certified_work / "world", "e" * 32, (root,))
    assert reconcile_sessions(config, certified_work / "ops") == ()


def test_the_ledgered_guarded_commit_over_the_durable_port_ledgers_the_primary_plan(certified_work):
    session, _writer, port = durable_session(certified_work)
    root = session.corpus_root
    node = proposition("p")
    fulfills = port.append_intent(b"intent")
    commit = port.execute_fulfilling_guarded(_plan(node), fulfills, guard=lambda _v: None, fallback=lambda _r: ())
    assert [entry.digest for entry in _registered(root, fulfills)] == [commit.entry] and commit.reason is None
    (act,) = session.invocation_acts("A")
    assert (act.entry, act.intent, act.record_ids) == (commit.entry, fulfills, ((node.uid, node.id),))
    assert _record_path(root, node).exists()


def test_the_ledgered_guarded_commit_over_the_durable_port_ledgers_the_fallback_plan(certified_work):
    session, _writer, port = durable_session(certified_work)
    root = session.corpus_root
    node, other = proposition("p"), proposition("q")
    fulfills = port.append_intent(b"intent")
    commit = port.execute_fulfilling_guarded(
        _plan(node), fulfills, guard=lambda _v: "stale", fallback=lambda _r: _plan(other)
    )
    assert [entry.digest for entry in _registered(root, fulfills)] == [commit.entry] and commit.reason == "stale"
    (act,) = session.invocation_acts("A")
    assert (act.entry, act.intent, act.record_ids) == (commit.entry, fulfills, ((other.uid, other.id),))
    assert _record_path(root, other).exists() and not _record_path(root, node).exists()


def test_an_invalid_fallback_over_the_durable_port_commits_registers_and_ledgers_nothing(certified_work):
    session, _writer, port = durable_session(certified_work)
    root = session.corpus_root
    node = proposition("p")
    fulfills = port.append_intent(b"intent")
    with pytest.raises(SessionProtocolError, match="creates only"):
        port.execute_fulfilling_guarded(
            _plan(node),
            fulfills,
            guard=lambda _v: "stale",
            fallback=lambda _r: [DeleteOp(f"{node.kind}/x.md", expected_digest="a" * 64)],
        )
    assert _registered(root, fulfills) == []
    assert not _record_path(root, node).exists() and not (root / node.kind / "x.md").exists()
    assert session.invocation_acts("A") == () and session.current_invocation == "A"


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


# --- the holdings route ---------------------------------------------
HOLDINGS = RequiredCapabilities.for_kinds({"holdings-observation"}, {})
STORE_ID = "1" * 32
GENESIS = b'{"domain":"science.store-root.v1","store_id":"' + STORE_ID.encode() + b'"}'
STATE = FileStateView("sha256:" + "a" * 64, 1)


def _state_of(content: bytes) -> FileStateView:
    return FileStateView("sha256:" + sha256(content).hexdigest(), len(content))


@dataclass
class FakeSeam:
    """A holdings seam over no engine. Each intent is its payload's digest, so two
    intents differ; each store call returns a fresh registration digest, recorded
    in `entries`; `raises`, when set, is raised by every store call instead."""

    root: Path
    lock: TracingLock | None = None
    on_corpus_lock: Any = None
    raises: BaseException | None = None
    reached: list[str] = field(default_factory=list)
    events: list[tuple[object, ...]] = field(default_factory=list)
    published: list[tuple[object, ...]] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    entries: list[str] = field(default_factory=list)
    created: set[str] = field(default_factory=set)
    entered: int = 0

    def _touch(self, name: str) -> None:
        if self.lock is not None:
            assert self.lock.held_by_me(), f"{name} entered without the session lock"
        self.reached.append(name)

    def _store(self, name: str, final_states) -> StoreOutcomeView:
        self._touch(name)
        self.events.append((name,))
        if self.raises is not None:
            raise self.raises
        entry = sha256(f"{name}:{len(self.entries)}".encode()).hexdigest()
        self.entries.append(entry)
        return StoreOutcomeView("tx", tuple(final_states), entry)

    def build(self) -> StoreActSeam:
        @contextmanager
        def corpus_lock(root):
            self._touch("corpus_lock")
            with _operation_lock_for(root):
                self.entered += 1
                self.events.append(("corpus_lock-enter", Path(root), self.lock is None or self.lock.held_by_me()))
                if self.on_corpus_lock is not None:
                    self.on_corpus_lock(self.entered)
                yield
                self.events.append(("corpus_lock-exit", Path(root)))

        def append_intent(_root, payload):
            self._touch("append_intent")
            digest = sha256(payload).hexdigest()
            self.intents.append(digest)
            return digest

        def publish_fulfilling(_root, plan, _intent):
            self._touch("publish_fulfilling")
            self.published.append(tuple(plan))
            return "2" * 64

        def read_path(_root, path):
            self._touch("read_path")
            if path.startswith("objects/") and path not in self.created:
                return PathObservedView(AbsentStateView())
            return PathObservedView(STATE)

        def store_write(_root, path, content, _intent):
            return self._store("store_write", ((path, _state_of(content)),))

        def store_delete(_root, path, _intent):
            return self._store("store_delete", ((path, AbsentStateView()),))

        def store_move(_root, source, destination, _intent):
            return self._store("store_move", ((source, AbsentStateView()), (destination, STATE)))

        def store_create(_root, path, content, _intent):
            outcome = self._store("store_create", ((path, _state_of(content)),))
            self.created.add(path)
            return outcome

        def store_genesis(_root):
            self._touch("store_genesis")
            return GENESIS

        return StoreActSeam(
            corpus_lock,
            append_intent,
            publish_fulfilling,
            read_path,
            store_write,
            store_delete,
            store_move,
            store_genesis,
            lambda caught: isinstance(caught, ExecutionError) and caught.applied == 0,
            store_create,
        )


BOTH = RequiredCapabilities.for_kinds({"holdings-observation", "proposition"}, {})


def _holdings(tmp_path: Path, seam: FakeSeam, scope: RequiredCapabilities = HOLDINGS):
    session, ports = make_session(
        tmp_path, store_root=tmp_path / "store", store_id=STORE_ID, holdings_seam=seam.build()
    )
    session.claim_invocation("A", "hold", DIGEST)
    writer = session.scoped(scope, "A")
    return session, writer, writer.holdings_context(instrument="test"), ports[-1]


def test_the_ledgered_port_forwards_its_inner_ports_root(tmp_path):
    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(BOTH, "A")
    assert scoped.operation_port().root == ports[-1].root
    session.close_invocation("A", {"done": []})
    session.close()


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
    (_stored, act) = open_ledger_reader(session.operations_root, session.session_id).acts()
    ((intent,),) = (seam.intents,)
    assert (act.corpus, act.intent, act.entry, act.record_ids) == (CORPUS, intent, "2" * 64, (pair,))
    assert seam.reached == [
        "corpus_lock",
        "append_intent",
        "store_genesis",
        "corpus_lock",
        "store_write",
        "corpus_lock",
        "publish_fulfilling",
    ]


def test_ledgered_seam_guards_store_create(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    ctx.seam.store_create(tmp_path / "store", "objects/sha256/aa/aa", b"x", "f" * 64)
    assert seam.reached == ["corpus_lock", "store_create"]
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        ctx.seam.store_create(tmp_path / "store", "objects/sha256/aa/aa", b"x", "f" * 64)
    assert seam.reached == ["corpus_lock", "store_create"]
    assert not session._ledger.failed


# --- ledgered store registrations ------------------------------------------


def _ledger_acts(session):
    return open_ledger_reader(session.operations_root, session.session_id).acts()


def test_each_store_call_ledgers_one_act_on_the_store_chain(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    delete(ctx, StoreLocator(STORE_ID, "p.bin"))
    move(ctx, StoreLocator(STORE_ID, "q.bin"), StoreLocator(STORE_ID, "r.bin"))
    write_intent, delete_intent, source_intent, destination_intent = seam.intents
    assert len({write_intent, delete_intent, source_intent, destination_intent}) == 4
    written, deleted, moved = seam.entries
    session.close_invocation("A", {"done": []})
    session.close()
    acts = _ledger_acts(session)
    assert [(act.corpus, act.entry, act.intent, act.record_ids) for act in acts if act.corpus == STORE_ID] == [
        (STORE_ID, written, write_intent, ()),
        (STORE_ID, deleted, delete_intent, ()),
        (STORE_ID, moved, source_intent, ()),
    ]
    # Each store line comes before the corpus line of its act's publication.
    assert [(act.corpus, act.intent) for act in acts] == [
        (STORE_ID, write_intent),
        (CORPUS, write_intent),
        (STORE_ID, delete_intent),
        (CORPUS, delete_intent),
        (STORE_ID, source_intent),
        (CORPUS, source_intent),
        (CORPUS, destination_intent),
    ]


def _two_member_tree(tmp_path: Path):
    """A two-member tree, its member sources laid under `tmp_path`, and its locator."""
    from beliefs.tree import TreeMember, make_tree, tree_digest

    contents = {"a.txt": b"alpha", "d/b.txt": b"beta"}
    sources = {}
    for name, data in contents.items():
        source = tmp_path / "src" / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(data)
        sources[name] = source
    tree = make_tree(
        tuple(TreeMember(name, _state_of(data).content_hash, len(data)) for name, data in contents.items())
    )
    return tree, sources, StoreTreeLocator(STORE_ID, tree_digest(tree).split(":", 1)[1])


def test_a_tree_write_ledgers_every_create_under_its_one_intent(tmp_path):
    tree, sources, location = _two_member_tree(tmp_path)
    seam = FakeSeam(tmp_path / "corpus")
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    tree_write(ctx, location, tree, sources)
    ((intent,),) = (seam.intents,)
    assert seam.reached.count("store_create") == 3  # two members, then the tree file
    acts = session.invocation_acts("A")
    assert [(act.corpus, act.entry, act.intent, act.record_ids) for act in acts] == [
        *((STORE_ID, entry, intent, ()) for entry in seam.entries),
        (CORPUS, "2" * 64, intent, (_published_pair(seam),)),
    ]


def test_a_tree_write_create_refusal_fails_the_session_with_ledger_failed(tmp_path):
    """Under a session the create's routine refusal fails the ledger inside the
    wrapper, so the boundary's read-again of the object is refused by the failed
    session: the act raises `SessionLedgerFailed`, never `StoreWriteRefused`."""
    tree, sources, location = _two_member_tree(tmp_path)
    seam = FakeSeam(tmp_path / "corpus", raises=ExecutionError("refused", index=None, applied=0))
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    with pytest.raises(SessionLedgerFailed):
        tree_write(ctx, location, tree, sources)
    assert seam.reached.count("store_create") == 1  # the first create; nothing after it
    assert seam.reached[-1] == "store_create"  # the object is never read again
    assert _ledger_acts(session) == ()
    assert session._ledger.failed is True


def test_an_engine_refusal_fails_the_ledger(tmp_path):
    seam = FakeSeam(tmp_path / "corpus", raises=ExecutionError("refused", index=None, applied=0))
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    with pytest.raises(StoreWriteRefused):  # the boundary still reports a routine refusal as one
        write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    assert _ledger_acts(session) == ()
    assert session._ledger.failed is True
    with pytest.raises(SessionLedgerFailed):
        session.close_invocation("A", {"done": []})


def test_an_uncertain_store_failure_fails_the_ledger(tmp_path):
    seam = FakeSeam(tmp_path / "corpus", raises=ExecutionError("unproved", index=None, applied=None))
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    with pytest.raises(ExecutionError, match="unproved"):
        write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    assert _ledger_acts(session) == ()
    assert session._ledger.failed is True
    with pytest.raises(SessionLedgerFailed):
        session.close_invocation("A", {"done": []})


def test_a_store_argument_refusal_keeps_the_session_live(tmp_path):
    seam = FakeSeam(tmp_path / "corpus", raises=StoreWriteRefused("p.bin", "a malformed path"))
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    with pytest.raises(StoreWriteRefused, match="a malformed path"):
        write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    assert session._ledger.failed is False
    assert session.invocation_acts("A") == ()
    seam.raises = None
    write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    (entry,) = seam.entries
    assert [(act.corpus, act.entry) for act in session.invocation_acts("A")] == [
        (STORE_ID, entry),
        (CORPUS, "2" * 64),
    ]
    session.close_invocation("A", {"done": []})
    session.close()


def test_a_store_call_on_another_root_is_refused_before_the_store(tmp_path):
    seam = FakeSeam(tmp_path / "corpus")
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    with pytest.raises(SessionProtocolError, match="store root"):
        ctx.seam.store_write(tmp_path / "elsewhere", "p.bin", b"x", "f" * 64)
    assert seam.reached == [] and session._ledger.failed is False
    assert session.invocation_acts("A") == ()


def test_a_store_act_holds_the_store_roots_operation_lock_through_its_line(tmp_path, monkeypatch):
    lock = TracingLock()
    seam = FakeSeam(tmp_path / "corpus", lock=lock)
    session, _writer, ctx, _ = _holdings(tmp_path, seam)
    session._lock = lock  # type: ignore[assignment]
    append = session._ledger.append

    def recording(line):
        seam.events.append(("append", line["line"], line.get("corpus"), lock.held_by_me()))
        append(line)

    monkeypatch.setattr(session._ledger, "append", recording)
    write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes")
    store = tmp_path / "store"
    start = seam.events.index(("corpus_lock-enter", store, True))
    end = seam.events.index(("corpus_lock-exit", store))
    assert seam.events[start : end + 1] == [
        ("corpus_lock-enter", store, True),  # the session lock is already held
        ("store_write",),
        ("append", "act", STORE_ID, True),
        ("corpus_lock-exit", store),
    ]
    # The observer root's lock was taken and released before the store call: one
    # operation lock at a time.
    before = seam.events[:start]
    observer_enters = [e for e in before if e[:2] == ("corpus_lock-enter", session.corpus_root)]
    observer_exits = [e for e in before if e == ("corpus_lock-exit", session.corpus_root)]
    assert len(observer_enters) == len(observer_exits) == 1


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
        if entered == 3:  # the intent's lock, the store root's, then the publication's
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

    a = threading.Thread(
        name="A", target=run, args=(lambda: write(ctx, StoreLocator(STORE_ID, "p.bin"), b"bytes"),), daemon=True
    )
    b = threading.Thread(name="B", target=run, args=(lambda: writer.add(proposition("p")),), daemon=True)
    a.start()
    assert a_in_publication.wait(5)
    b.start()
    a.join(5)
    b.join(5)
    assert not a.is_alive() and not b.is_alive(), "deadlock: the lock order is not session then corpus"
    assert failures == []
    assert ("B", "held-by-another") in lock.attempts


# --- the session acquisition route -----------------------

ACQUIRES = RequiredCapabilities.for_kinds(
    {"holdings-observation", "dataset", "act-report"}, {"act-report": "corpus-write"}
)


def _acquisition_request():
    return AcquisitionRequest(
        title="t",
        locator="url:https://example.org/dataset",
        resources=(ResourceRequest("a", url_locator("https://example.org/a")),),
        bounds=RetrievalBounds(5.0, 1 << 20, 3),
    )


def _durable_session(certified_work):
    corpus_root, store_root = certified_work / "corpus", certified_work / "store"
    init_corpus_root(corpus_root, authority=FULL)
    open_corpus(corpus_root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
    init_store_root(store_root, authority=FULL)
    config = WorldConfig(certified_work / "world", "a" * 32, (corpus_root,))
    return open_attended_session(
        config, certified_work / "ops", write_root=corpus_root, profile=BASE, store_root=store_root
    )


def test_acquire_through_a_session_ledgers_every_commit(certified_work, tmp_path):
    session = _durable_session(certified_work)
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES, "A")
    transport, log = scripted_seam({"/a": Scripted(200, {"Content-Length": "1"}, (b"x",))})
    outcome = scoped.acquire(_acquisition_request(), instrument="inst", scratch=tmp_path / "scratch", seam=transport)
    assert outcome.dataset is not None and len(log.requests) == 1
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert len(acts) == 2  # the look's fulfilling publication and the closing transaction
    assert {pair[1] for act in acts for pair in act.record_ids} >= {outcome.report_ref, outcome.dataset.id}


def test_seal_route_ledgers_its_acts(certified_work, tmp_path):
    from test_holdings_seal import MEMBERS, fetched_log, request_for

    session = _durable_session(certified_work)
    session.claim_invocation("A", "seal-acquisition", DIGEST)
    scoped = session.scoped(ACQUIRES, "A")
    outcome = scoped.seal_acquisition(request_for(tmp_path / "work", MEMBERS, fetched_log(MEMBERS)), instrument="inst")
    assert outcome.dataset is not None
    assert outcome.report.instrument == "inst" and outcome.report.observer == session.actor
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    corpus_acts = [act for act in acts if act.corpus == session.corpus_id]
    store_acts = [act for act in acts if act.corpus == scoped.store_id]
    assert len(corpus_acts) == 3  # the log write's publication, the tree write's publication, the closing transaction
    assert len(store_acts) == 5  # the log write, then three member objects and the tree file
    assert len(acts) == len(corpus_acts) + len(store_acts)
    assert {pair[1] for act in acts for pair in act.record_ids} >= {outcome.report_ref, outcome.dataset.id}


AUDITS = RequiredCapabilities.for_kinds({"act-report"}, {"act-report": "corpus-write"})
RECHECKS = RequiredCapabilities.for_kinds({"holdings-observation", "act-report"}, {"act-report": "corpus-write"})


def test_audit_through_a_session_ledgers_its_one_commit_and_names_the_session_actor(certified_work):
    from beliefs.audit import NO_EVIDENCE

    session = _durable_session(certified_work)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(AUDITS, "A")
    outcome = scoped.audit(instrument="inst", evidence=NO_EVIDENCE)
    assert outcome.report.observer == session.actor and outcome.report.actor == session.actor
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert len(acts) == 1
    assert {pair[1] for act in acts for pair in act.record_ids} == {outcome.report_ref}


def test_recheck_through_a_session_ledgers_every_commit(certified_work):
    session = _durable_session(certified_work)
    session.claim_invocation("A", "recheck", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    ctx = scoped.holdings_context(instrument="inst")
    location = StoreLocator(scoped.store_id, "a.bin")
    write(ctx, location, b"alpha")
    outcome = scoped.recheck((location,), instrument="inst")
    assert outcome.report.observer == session.actor
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    # The write's store registration and its publication, the re-check's publication, the closing transaction.
    assert [act.corpus for act in acts] == [scoped.store_id, session.corpus_id, session.corpus_id, session.corpus_id]
    stored, published = acts[0], acts[1]
    assert session.store_root is not None
    assert [entry.digest for entry in _registrations(session.store_root)] == [stored.entry]
    assert (stored.intent, stored.record_ids) == (published.intent, ())
    assert isinstance(outcome.entries[0].outcome, PublishedObservation)
    assert {pair[1] for act in acts for pair in act.record_ids} >= {outcome.report_ref, outcome.entries[0].outcome.ref}


def test_an_effect_time_rollback_fails_the_ledger_and_leaves_its_registration(certified_work, monkeypatch):
    """The engine registers before it applies effects; an effect that meets drift
    rolls back and settles the registration as not committed. A routine refusal
    therefore does not prove nothing registered, so the session ledger fails."""
    from atoms.coordinator import execute as engine_execute
    from atoms.coordinator.effects.common import EffectMismatch

    session = _durable_session(certified_work)
    session.claim_invocation("A", "write", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    ctx = scoped.holdings_context(instrument="inst")
    store_root = session.store_root
    assert store_root is not None
    before = science_root.log_seam().inspect_detached(store_root)
    assert type(before) is WellFormedView
    real = engine_execute._apply_effect
    calls: list[object] = []

    def mismatching(lease, approved, table, effect):
        calls.append(effect)
        if len(calls) == 1:
            raise EffectMismatch("create", "op-0")
        return real(lease, approved, table, effect)

    monkeypatch.setattr(engine_execute, "_apply_effect", mismatching)
    with pytest.raises(StoreWriteRefused):
        write(ctx, StoreLocator(scoped.store_id, "a.bin"), b"alpha")
    assert len(calls) == 1
    after = science_root.log_seam().inspect_detached(store_root)
    assert type(after) is WellFormedView
    added = after.entries[len(before.entries) :]
    (registered,) = [entry for entry in added if type(entry) is RegisteredEntryView]
    (settled,) = [entry for entry in added if type(entry) is SettledEntryView]
    assert (settled.registration, settled.committed) == (registered.digest, False)
    assert len(added) == 2
    assert open_ledger_reader(session.operations_root, session.session_id).acts() == ()
    assert session._ledger.failed is True
    with pytest.raises(SessionLedgerFailed):
        session.close_invocation("A", {"done": []})


def test_a_store_less_session_audits_and_cannot_recheck(certified_work):
    from beliefs.audit import NO_EVIDENCE

    corpus_root = certified_work / "corpus"
    init_corpus_root(corpus_root, authority=FULL)
    open_corpus(corpus_root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
    config = WorldConfig(certified_work / "world", "a" * 32, (corpus_root,))
    session = open_attended_session(config, certified_work / "ops", write_root=corpus_root, profile=BASE)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    assert scoped.audit(instrument="inst", evidence=NO_EVIDENCE).entries == ()
    with pytest.raises(SessionProtocolError, match="no store root"):
        scoped.recheck((StoreLocator("a" * 32, "a.bin"),), instrument="inst")
    session.close_invocation("A", {"done": []})
    session.close()


def test_the_routes_refuse_after_the_invocation_closes(certified_work):
    from beliefs.audit import NO_EVIDENCE

    session = _durable_session(certified_work)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    session.close_invocation("A", {"done": []})
    with pytest.raises(SessionProtocolError):
        scoped.audit(instrument="inst", evidence=NO_EVIDENCE)
    with pytest.raises(SessionProtocolError):
        scoped.recheck((StoreLocator(scoped.store_id, "a.bin"),), instrument="inst")
    session.close()


ACQUIRES_AND_ADDS = RequiredCapabilities.for_kinds(
    {"holdings-observation", "dataset", "act-report", "proposition"}, {"act-report": "corpus-write"}
)


def test_the_close_takes_the_session_lock_before_the_root_lock_and_a_concurrent_act_completes(
    certified_work, tmp_path, monkeypatch
):
    """Session, then root, is the only order `_act` takes; the close takes the same
    one, and holds neither around the request — so an act on another thread
    completes while the acquisition is open, and the close never waits on a
    thread that waits on it."""
    from beliefs import corpus as corpus_module

    session = _durable_session(certified_work)
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES_AND_ADDS, "A")
    owned: list[bool] = []
    real_enter = corpus_module._SettlingHold.__enter__

    def probing(self):
        owned.append(session._lock._is_owned())  # type: ignore[attr-defined]
        return real_enter(self)

    monkeypatch.setattr(corpus_module._SettlingHold, "__enter__", probing)
    transport, _ = scripted_seam({"/a": Scripted(200, {"Content-Length": "1"}, (b"x",))})
    opened, added = threading.Event(), threading.Event()

    def gated_connect(approved, timeout):
        opened.set()  # the operation intent is open and the request is about to go out
        assert added.wait(30), "the concurrent add did not complete while the request was open"
        return transport.connect(approved, timeout)

    def add_while_open():
        assert opened.wait(30)
        scoped.add(proposition("p"))
        added.set()

    partner = threading.Thread(target=add_while_open, daemon=True)
    partner.start()
    outcome = scoped.acquire(
        _acquisition_request(),
        instrument="inst",
        scratch=tmp_path / "scratch",
        seam=replace(transport, connect=gated_connect),
    )
    partner.join(30)
    assert not partner.is_alive() and outcome.dataset is not None
    assert owned and all(owned)  # every root-lock entry under the session saw the session lock owned first
    session.close_invocation("A", {"done": []})
    session.close()
    assert (
        len(open_ledger_reader(session.operations_root, session.session_id).acts()) == 3
    )  # the add, the look, the close


def test_acquire_on_a_store_less_session_refuses_before_any_intent(tmp_path):
    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES, "A")
    transport, log = scripted_seam({})
    with pytest.raises(SessionProtocolError, match="no store"):
        scoped.acquire(_acquisition_request(), instrument="inst", scratch=tmp_path / "scratch", seam=transport)
    assert ports[-1].calls == [] and log.requests == []
