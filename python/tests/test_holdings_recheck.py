"""The re-check operation — portable, over a recording port and a scripted store seam."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from pathlib import Path

import pytest
from authority import FULL, narrowed
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE
from test_audit_operation import Ordered, _held
from test_operation_writes import RecordingPort, intents_of, writer_over

from beliefs import boundary as boundary_values
from beliefs import stored
from beliefs.corpus import CorpusWriter, _operation_lock_for
from beliefs.errors import MalformedRecord, PermitExceeded, PortMismatch, RecheckRefused
from beliefs.holdings.boundary import ActContext, InconclusiveAttempt
from beliefs.holdings.recheck import RecheckOutcome, recheck_locations
from beliefs.holdings.records import Found, StoreLocator, holdings_observation
from beliefs.holdings.seam import (
    FileStateView,
    PathObservedView,
    PathReadView,
    ReadNotAttemptedView,
    ReadUnestablishedView,
    StoreActSeam,
)
from beliefs.report import (
    CLOSED,
    ByteLocatorUntested,
    LocatorEntry,
    OperationIntent,
    PublishedObservation,
    Registration,
    RetrievalFailed,
    completion,
)

STORE_ID = "1" * 32
GENESIS = b'{"domain":"science.store-root.v1","store_id":"' + STORE_ID.encode() + b'"}'
FOUND = PathObservedView(FileStateView("sha256:" + "a" * 64, 1))


@dataclass
class ScriptedStore:
    """A store seam over the observer root's plain executor: holdings intents counted, publications on disk, reads scripted per path."""

    root: Path
    views: dict[str, PathReadView] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    intents: list[bytes] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)

    def build(self) -> StoreActSeam:
        executor = DefaultExecutor(self.root)

        @contextmanager
        def corpus_lock(root):
            with _operation_lock_for(root):
                yield

        def append_intent(_root, payload):
            self.intents.append(payload)
            self.events.append("holdings-intent")
            return sha256(payload).hexdigest()

        def publish_fulfilling(_root, plan, _intent):
            executor.execute(list(plan))
            self.events.append("published")
            return "2" * 64

        def read_path(_root, path):
            self.reads.append(path)
            self.events.append("read")
            return self.views.get(path, FOUND)

        def unused(*_):
            raise AssertionError("not reached")

        return StoreActSeam(
            corpus_lock,
            append_intent,
            publish_fulfilling,
            read_path,
            unused,
            unused,
            unused,
            lambda _root: GENESIS,
            lambda _caught: False,
            unused,
        )


def portable(tmp_path, views=None):
    observer_root, store_root = tmp_path / "observer", tmp_path / "store"
    observer_root.mkdir(parents=True)
    store_root.mkdir(parents=True)
    seam = ScriptedStore(observer_root, {} if views is None else views)
    ctx = ActContext(observer_root, store_root, "observer", "instrument", FULL, seam.build(), profile=BASE)
    port = Ordered(FULL, observer_root, seam.events)
    writer = CorpusWriter(observer_root, DefaultExecutor, authority=FULL, operation_port=port, profile=BASE)
    return ctx, seam, writer, port


def location(name: str) -> StoreLocator:
    return StoreLocator(STORE_ID, name)


def test_two_locations_close_through_one_report_after_one_operation_intent(tmp_path):
    ctx, seam, writer, port = portable(tmp_path)
    a, b = location("a.bin"), location("b.bin")
    outcome = recheck_locations(ctx, writer, (a, b))
    assert isinstance(outcome, RecheckOutcome)
    assert seam.events == [
        "appended",
        "holdings-intent",
        "read",
        "published",
        "holdings-intent",
        "read",
        "published",
        "closed",
    ]
    (intent,) = intents_of(port)
    assert intent == OperationIntent("re-check", outcome.report.event_token, FULL.actor)
    assert len(seam.intents) == 2 and all(json.loads(i)["kind"] == "re-check" for i in seam.intents)
    assert [e.subject for e in outcome.entries] == [a.canonical(), b.canonical()]
    assert all(
        type(e) is LocatorEntry and type(e.outcome) is PublishedObservation and e.instrument_inputs == ()
        for e in outcome.entries
    )
    for entry in outcome.entries:
        assert isinstance(entry.outcome, PublishedObservation)
        assert writer.read_view.holds(entry.outcome.ref)
    assert writer.read_view.holds(outcome.report_ref)
    ((_plan, fulfills),) = [payload for kind, payload in port.calls if kind == "execute_fulfilling"]
    assert fulfills == "1" * 60 + "0001"
    assert (
        completion(
            intent, (Registration(intent.event_token, outcome.report_ref),), {outcome.report_ref: outcome.report}
        )
        == CLOSED
    )
    assert outcome.report.entries == outcome.entries


def test_an_inconclusive_location_is_an_entry_with_the_reason_only_and_the_operation_still_closes(tmp_path):
    views = {
        "b.bin": ReadNotAttemptedView(
            reason="lease-refused", lifecycle_state=None, detail="/secret/path must not enter the record"
        )
    }
    ctx, seam, writer, _ = portable(tmp_path, views)
    a, b = location("a.bin"), location("b.bin")
    outcome = recheck_locations(ctx, writer, (a, b))
    assert type(outcome.entries[0].outcome) is PublishedObservation
    assert outcome.entries[1] == LocatorEntry(b.canonical(), ByteLocatorUntested("lease-refused"))
    assert isinstance(outcome.results[1], InconclusiveAttempt)
    assert "/secret/path" not in json.dumps(stored.act_report_facet(writer.read_view.get(outcome.report_ref)))
    assert seam.events[-1] == "closed"


def test_an_unestablished_read_spells_retrieval_failed(tmp_path):
    ctx, _, writer, _ = portable(tmp_path, {"a.bin": ReadUnestablishedView(reason="io-error", detail="d")})
    a = location("a.bin")
    outcome = recheck_locations(ctx, writer, (a,))
    assert outcome.entries == (LocatorEntry(a.canonical(), RetrievalFailed("io-error")),)


def test_a_standing_head_is_superseded_by_the_new_observation(tmp_path):
    ctx, _, writer, _ = portable(tmp_path)
    a = location("a.bin")
    first = recheck_locations(ctx, writer, (a,))
    first_outcome = first.entries[0].outcome
    assert isinstance(first_outcome, PublishedObservation)
    head = stored.holdings_observation_value(writer.read_view.get(first_outcome.ref))
    second = recheck_locations(ctx, writer, (a,), standing={a.canonical(): (head,)})
    second_outcome = second.entries[0].outcome
    assert isinstance(second_outcome, PublishedObservation)
    new = stored.holdings_observation_value(writer.read_view.get(second_outcome.ref))
    assert new.supersedes == (head.identity(),)


@pytest.mark.parametrize(
    ("spoil", "refusal"),
    [
        ("not-a-tuple", MalformedRecord),
        ("empty", MalformedRecord),
        ("duplicate", RecheckRefused),
        ("foreign-store", RecheckRefused),
        ("wrong-root", RecheckRefused),
        ("no-port", RecheckRefused),
        ("foreign-root-port", PortMismatch),
        ("empty-instrument", RecheckRefused),
        ("unencodable-observer", RecheckRefused),
        ("standing-elsewhere", RecheckRefused),
        ("standing-unrequested", RecheckRefused),
        ("no-holdings-permit", PermitExceeded),
    ],
)
def test_every_pre_intent_refusal_appends_no_intent_of_either_grain_and_reads_nothing(tmp_path, spoil, refusal):
    ctx, seam, writer, port = portable(tmp_path)
    a = location("a.bin")
    locations: object = (a,)
    kwargs: dict = {}
    ports: list[RecordingPort] = [port]
    if spoil == "not-a-tuple":
        locations = [a]
    elif spoil == "empty":
        locations = ()
    elif spoil == "duplicate":
        locations = (a, StoreLocator(STORE_ID, "a.bin"))
    elif spoil == "foreign-store":
        locations = (a, StoreLocator("f" * 32, "x.bin"))
    elif spoil == "wrong-root":
        (tmp_path / "other").mkdir()
        writer, other_port = writer_over(tmp_path / "other")
        ports.append(other_port)
    elif spoil == "no-port":
        writer = CorpusWriter(ctx.observer_root, DefaultExecutor, authority=FULL, profile=BASE)
    elif spoil == "foreign-root-port":
        (tmp_path / "other").mkdir()
        kwargs["port"] = RecordingPort(FULL, tmp_path / "other")
        ports.append(kwargs["port"])
    elif spoil == "empty-instrument":
        ctx = replace(ctx, instrument="")
    elif spoil == "unencodable-observer":
        ctx = replace(ctx, observer="\udcff")
    elif spoil == "standing-elsewhere":
        elsewhere = holdings_observation(
            location=location("b.bin"),
            outcome=Found("sha256:" + "0" * 64),
            observer="o",
            instrument="i",
            event_token="t",
            observed_at="2026-09-22T00:00:00Z",
        )
        kwargs["standing"] = {a.canonical(): (elsewhere,)}
    elif spoil == "standing-unrequested":
        kwargs["standing"] = {location("b.bin").canonical(): ()}
    elif spoil == "no-holdings-permit":
        ctx = replace(ctx, authority=narrowed(kinds=("act-report",), families=("corpus-write",)))
    with pytest.raises(refusal):
        recheck_locations(ctx, writer, locations, **kwargs)  # type: ignore[arg-type]
    assert all(p.calls == [] for p in ports)
    assert seam.intents == [] and seam.reads == [] and seam.events == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_no_lock_is_held_across_the_acts_and_the_hold_enters_before_the_root_lock_at_the_close(tmp_path):
    ctx, _seam, writer, _ = portable(tmp_path)
    a = location("a.bin")
    events: list[str] = []
    lock = _operation_lock_for(ctx.observer_root)
    inner = ctx.seam.read_path

    def reading(root: Path, path: str) -> PathReadView:
        events.append("read:" + ("held" if _held(lock) else "free"))
        return inner(root, path)

    class Hold:
        def __enter__(self):
            events.append("hold-enter:" + ("held" if _held(lock) else "free"))
            return self

        def __exit__(self, *_exc):
            events.append("hold-exit:" + ("held" if _held(lock) else "free"))

    ctx = replace(ctx, seam=replace(ctx.seam, read_path=reading))
    recheck_locations(ctx, writer, (a,), hold=Hold)
    assert events == ["read:free", "hold-enter:free", "hold-exit:free"]


def test_the_close_rebuilds_the_view_and_refuses_a_ref_no_act_published(tmp_path, monkeypatch):
    ctx, _, writer, port = portable(tmp_path)
    monkeypatch.setattr(writer, "_reconstruct", lambda: None)  # the act published past this writer's cached index
    with pytest.raises(RecheckRefused, match="no act published"):
        recheck_locations(ctx, writer, (location("a.bin"),))
    assert [kind for kind, _ in port.calls] == ["append_intent"]  # the intent stands; nothing fulfilled it


def test_the_mint_helper_refuses_the_wrong_intent_kind_and_the_wrong_entry_kind():
    from beliefs.report import EvaluationFinding, SubjectEvaluationEntry

    now = "2026-09-22T00:00:00Z"
    entry = LocatorEntry(location("x.bin").canonical(), RetrievalFailed("x"))
    with pytest.raises(MalformedRecord, match="re-check operation intent"):
        boundary_values._mint_recheck_report(
            OperationIntent("audit", "t", "alice"),
            observer="o",
            instrument="i",
            opened_at=now,
            closed_at=now,
            entries=(entry,),
        )
    with pytest.raises(MalformedRecord, match="locator entries only"):
        boundary_values._mint_recheck_report(
            OperationIntent("re-check", "t", "alice"),
            observer="o",
            instrument="i",
            opened_at=now,
            closed_at=now,
            entries=(SubjectEvaluationEntry("proposition:" + "a" * 64, EvaluationFinding("{}")),),
        )
    report = boundary_values._mint_recheck_report(
        OperationIntent("re-check", "t", "alice"),
        observer="o",
        instrument="i",
        opened_at=now,
        closed_at=now,
        entries=(entry,),
    )
    assert report.operation == "re-check" and report.entries == (entry,)


def _tree_locator_and_file(store_root: Path, members: dict[str, bytes]):
    """A tree over `members` with its tree file laid in the store root; returns (locator, tree)."""
    from beliefs.holdings.records import StoreTreeLocator
    from beliefs.tree import TreeMember, make_tree, object_path, tree_digest, tree_file_bytes

    tree = make_tree(
        TreeMember(name, "sha256:" + sha256(data).hexdigest(), len(data)) for name, data in members.items()
    )
    laid = store_root / object_path(tree_digest(tree))
    laid.parent.mkdir(parents=True)
    laid.write_bytes(tree_file_bytes(tree))
    return StoreTreeLocator(STORE_ID, tree_digest(tree).split(":", 1)[1]), tree


def _views_for(tree, *, tree_file_view=None, member_view=None):
    from beliefs.tree import object_path, tree_digest

    views = {
        object_path(tree_digest(tree)): tree_file_view
        or PathObservedView(FileStateView("sha256:" + tree_digest(tree).split(":", 1)[1], len(b"x")))
    }
    for member in tree.members:
        views[object_path(member.digest)] = member_view or PathObservedView(FileStateView(member.digest, member.size))
    return views


def test_recheck_locations_dispatches_a_store_tree_location(tmp_path):
    from beliefs.holdings.records import Absent, Incomplete

    locator, tree = _tree_locator_and_file(tmp_path / "scratch", {"a.txt": b"alpha", "b.txt": b"beta"})
    views = _views_for(tree)
    ctx, seam, writer, _ = portable(tmp_path / "p", views)
    from beliefs.tree import object_path, tree_digest, tree_file_bytes

    laid = ctx.store_root / object_path(tree_digest(tree))
    laid.parent.mkdir(parents=True)
    laid.write_bytes(tree_file_bytes(tree))
    plain = location("plain.bin")

    outcome = recheck_locations(ctx, writer, (plain, locator))

    assert [e.subject for e in outcome.entries] == [plain.canonical(), locator.canonical()]
    tree_result = outcome.results[1]
    assert not isinstance(tree_result, InconclusiveAttempt)
    assert tree_result.record.outcome == Found(tree_digest(tree))
    assert json.loads(seam.intents[1])["kind"] == "re-check"
    assert json.loads(seam.intents[1])["location"]["type"] == "store-tree"

    gone = {**views, object_path(tree.members[0].digest): PathObservedView(FileStateView("sha256:" + "0" * 64, 5))}
    seam.views.update(gone)
    second = recheck_locations(ctx, writer, (locator,))
    assert second.results[0].record.outcome == Absent(Incomplete(0, 1))  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("which", "view", "report"),
    [
        (
            "tree-file",
            ReadNotAttemptedView(reason="lease-refused", lifecycle_state=None, detail="d"),
            "byte-locator-untested",
        ),
        ("tree-file", ReadUnestablishedView(reason="io-error", detail="d"), "retrieval-failed"),
        ("member", ReadUnestablishedView(reason="io-error", detail="d"), "retrieval-failed"),
    ],
)
def test_an_unreadable_tree_object_is_inconclusive(tmp_path, which, view, report):
    from beliefs.tree import object_path, tree_digest, tree_file_bytes

    ctx, seam, writer, _ = portable(tmp_path / "p")
    locator, tree = _tree_locator_and_file(tmp_path / "scratch", {"a.txt": b"alpha"})
    laid = ctx.store_root / object_path(tree_digest(tree))
    laid.parent.mkdir(parents=True)
    laid.write_bytes(tree_file_bytes(tree))
    views = _views_for(tree)
    key = object_path(tree_digest(tree)) if which == "tree-file" else object_path(tree.members[0].digest)
    views[key] = view
    seam.views.update(views)

    outcome = recheck_locations(ctx, writer, (locator,))

    (result,) = outcome.results
    assert isinstance(result, InconclusiveAttempt)
    assert (result.report, result.reason) == (report, view.reason)
    assert not (ctx.observer_root / "holdings-observation").exists()
