"""Conformance cut 42 — the publish act, remote (publish-act-remote design §11.2).
Fourteen declaration units over real roots on the certified volume, each run
under exactly the publication permit, over cut 40's fixture with a
directory-backed transport at `https://remote.test/pub`.

Crashes are injected at step boundaries by monkeypatching the act's named step
functions (cut 40's, plus `_mark`, `_push`, `_verify`); a fresh `resume_publish`
then reads only disk."""

from __future__ import annotations

import os
import shutil
import stat
from dataclasses import replace
from itertools import count
from pathlib import Path

import pytest
from coordination_fixtures import raw_add
from nodes.core.paths import path_for_node_id
from test_publish_act_acceptance import (  # noqa: F401 — `source` is a fixture
    SETUP,
    V2,
    Clock,
    Crash,
    _binding_files,
    _ops_tree,
    _publish_reports,
    chain_tip,
    crash,
    fresh_writer,
    run,
    source,
    token_of_last_intent,
)
from test_world_receipts import hold_shipped
from transport_fake import DirectoryTransport, TransportFault

from beliefs import publish as act
from beliefs import stored
from beliefs.corpus import CorpusWriter, ReadView
from beliefs.errors import AddressMapConflict, PublicationArrivalRefused, PublicationReadingRefused, PublicationRefused
from beliefs.intents.publish import Destination
from beliefs.publication import MARKER_KIND, marker_uid
from beliefs.publication_arrival import CurrentPublication, DivergentPublication, admit_publication, publication_tip
from beliefs.publication_doors import attempt_reading
from beliefs.publish import Published, PublishRefused, PublishUnresolved, resume_publish
from beliefs.publish_request import decode_mark, encode_mark
from beliefs.root import LifecycleState, init_world_root, moment_seam, open_world, read_lifecycle_state, restore_root
from beliefs.world import WorldConfig, epoch
from beliefs.world.anchors import CorpusSubject
from beliefs.world.verify import ArtifactCarrier, ObserverSet

REMOTE = Destination.remote("https://remote.test/pub")
_counter = count()


@pytest.fixture()
def remote(source):  # noqa: F811 — imported pytest fixture
    """Cut 40's source world, publishing to the fake remote."""
    (source.base / "remote").mkdir()
    source.transport = DirectoryTransport(source.base / "remote")
    source.destination = REMOTE
    return source


def publish_remote(s, **changes):
    return run(s, transport=s.transport, **changes)


def resume_remote(s, token: str, transport=None):
    return resume_publish(
        fresh_writer(s), s.resolver, event_token=token, operations_root=s.ops, staging_profile=V2,
        clock=Clock(), seam=moment_seam(), transport=transport or s.transport,
    )


def op_dir(s, token: str) -> Path:
    return s.ops / "publish" / token


def mark_of(s, token: str):
    return decode_mark((op_dir(s, token) / "transport.v1").read_bytes())


def export_of(s, token: str, corpus_id: str) -> Path:
    return op_dir(s, token) / "export" / corpus_id


def marker_node(root: Path):
    (marker,) = [n for n in ReadView.opened_at(root).iter_stored() if n.kind == MARKER_KIND]
    return marker


def supersedes(s, outcome: Published) -> set[tuple[str, str]]:
    """The published marker's `supersedes_markers`, read from its retained export root."""
    facet = marker_node(export_of(s, outcome.event_token, outcome.corpus_id)).facets[stored.COORDINATION_FACET]
    return {(str(c), str(m)) for c, m in facet["supersedes_markers"]}


def writable(root: Path) -> None:
    """Lift write permission on a root's tree (Task 0's DAMAGE_WRITABLE)."""
    for path in (root, *root.rglob("*")):
        if not path.is_symlink():
            os.chmod(path, stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)


def kinds(report) -> list[str]:
    return [e["kind"] for e in report["entries"]]


REMOTE_LIFECYCLE = ["publication-staging", "publication-export", "publication-reveal", "publication-transport"]


def recipient_copy(s, outcome: Published) -> tuple[Path, ObserverSet]:
    """A recipient's restored raw copy of a remote publication (decision 10)."""
    into = s.base / f"recipient-copy-{next(_counter)}"
    s.roots.append(into / outcome.corpus_id)
    root, sibling = s.transport.materialize(REMOTE, outcome.corpus_id, into)
    observers = ObserverSet((ArtifactCarrier.from_bytes(sibling),))
    assert restore_root(root, CorpusSubject(outcome.corpus_id), observers, authority=SETUP).outcome == "validated"
    return root, observers


def recipient_world(s, roots: tuple[Path, ...]):
    world_root = s.base / f"recipient-{next(_counter)}"
    s.roots.append(world_root)
    config = WorldConfig(world_root, "c" * 32, roots)
    init_world_root(config, authority=SETUP)
    return open_world(config, authority=SETUP)


# --- Y11 ------------------------------------------------------------------------


@pytest.mark.parametrize("fault", ["altered", "extra"])
def test_y11_a_a_listing_that_disagrees_is_transport_incomplete_durably(remote, fault):
    """Y11-a: a file altered, or an extra file added, at the remote after `push` → listing-mismatch."""

    def after_push(target: Path) -> None:
        (corpus_dir,) = [p for p in target.iterdir() if p.is_dir()]
        if fault == "altered":
            victim = next(p for p in sorted(corpus_dir.rglob("*")) if p.is_file())
            victim.write_bytes(victim.read_bytes() + b"\n")
        else:
            (corpus_dir / "extra").write_bytes(b"extra")

    remote.transport.after_push = after_push
    outcome = publish_remote(remote)
    assert outcome == PublishRefused(outcome.event_token, "transport-incomplete")
    (report,) = _publish_reports(remote, outcome.event_token)
    assert kinds(report) == REMOTE_LIFECYCLE and report["entries"][-1]["outcome"]["reason"] == "listing-mismatch"
    assert _binding_files(remote) == []
    reading = attempt_reading(fresh_writer(remote), outcome.event_token, moment_seam())
    assert reading is not None and reading.reading == "closed"


# --- Y12 ------------------------------------------------------------------------


def test_y12_a_a_crash_inside_push_leaves_the_mark_and_blocks_the_next_publish_durably(remote):
    """Y12-a: the mark is on disk before the first byte leaves."""
    remote.transport.fail_after_files = 1
    with pytest.raises(TransportFault):
        publish_remote(remote)
    token = token_of_last_intent(remote)
    assert (op_dir(remote, token) / "transport.v1").is_file()
    remote.transport.fail_after_files = None
    tip, ops = chain_tip(remote), _ops_tree(remote)
    with pytest.raises(PublicationRefused) as refused:
        publish_remote(remote)
    assert refused.value.reason == "publish-unfinished" and refused.value.tokens == (token,)
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops


def test_y12_b_a_resume_after_the_mark_never_rereads_staging_durably(remote, monkeypatch):
    """Y12-b: an extra record raw-written into staging after the mark is never seen."""
    crash(monkeypatch, "_verify", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    raw_add(op_dir(remote, token) / "staging", stored.run_node("zz", title="zz", spec="s", produces=[]))
    staged: list[str] = []
    original = CorpusWriter._stage_record
    monkeypatch.setattr(CorpusWriter, "_stage_record", lambda self, text: staged.append(text) or original(self, text))
    outcome = resume_remote(remote, token)
    assert type(outcome) is Published and staged == []


@pytest.mark.parametrize("field", ["corpus_id", "artifact"])
def test_y12_c_a_mark_disagreeing_with_its_export_fails_closed_durably(remote, monkeypatch, field):
    """Y12-c: a mark rewritten with another corpus_id or artifact → transport-mark-corrupt, nothing written."""
    crash(monkeypatch, "_push", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    path = op_dir(remote, token) / "transport.v1"
    path.write_bytes(encode_mark(replace(mark_of(remote, token), **{field: "7" * (32 if field == "corpus_id" else 64)})))
    tip, ops = chain_tip(remote), _ops_tree(remote)
    assert resume_remote(remote, token) == PublishUnresolved(token, "transport-mark-corrupt")
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops


# --- Y13 ------------------------------------------------------------------------


def test_y13_a_an_abandoned_transport_is_an_orphan_the_next_publish_supersedes_durably(remote):
    """Y13-a: the fake abandons; the next publish binds and its marker supersedes the abandoned pair."""
    remote.transport.abandon = True
    abandoned = publish_remote(remote)
    assert abandoned == PublishRefused(abandoned.event_token, "transport-incomplete")
    pair = (mark_of(remote, abandoned.event_token).corpus_id, marker_uid(abandoned.event_token))
    remote.transport.abandon = False
    bound = publish_remote(remote)
    assert type(bound) is Published and pair in supersedes(remote, bound)


def test_y13_b_an_orphan_named_by_an_abandoned_attempt_is_not_retired_durably(remote):
    """Y13-b: O abandons; T, naming O, abandons; N supersedes both."""
    remote.transport.abandon = True
    o = publish_remote(remote)
    t = publish_remote(remote)
    o_pair = (mark_of(remote, o.event_token).corpus_id, marker_uid(o.event_token))
    t_pair = (mark_of(remote, t.event_token).corpus_id, marker_uid(t.event_token))
    reading = attempt_reading(fresh_writer(remote), t.event_token, moment_seam())
    assert reading is not None and o_pair in reading.opened.intent.marker_tips
    remote.transport.abandon = False
    n = publish_remote(remote)
    assert type(n) is Published and {o_pair, t_pair} <= supersedes(remote, n)


@pytest.mark.parametrize("damage", ["deleted", "altered", "unreadable", "undecodable"])
def test_y13_c_an_export_damaged_after_the_mark_closes_as_an_orphan_durably(remote, monkeypatch, damage):
    """Y13-c: a selected record deleted from, altered in, made unreadable in or
    replaced by undecodable bytes in the serviceable export after the mark → the
    resume refuses `export-damaged` without pushing (never `transport-mark-corrupt`),
    and the next publish supersedes the orphan."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    crash(monkeypatch, "_push", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    mark = mark_of(remote, token)
    export = export_of(remote, token, mark.corpus_id)
    selected = marker_node(export).facets[stored.COORDINATION_FACET]["selection"][0]
    writable(export)
    record = export / path_for_node_id(selected)
    if damage == "deleted":
        record.unlink()
    elif damage == "altered":
        data = record.read_bytes()
        record.write_bytes(data[:-2] + bytes([data[-2] ^ 1]) + data[-1:])  # one byte flipped inside the content
    elif damage == "unreadable":
        record.chmod(0)
    else:
        record.write_bytes(b"\x00\xffnot a record")
    pushes = remote.transport.pushes
    assert resume_remote(remote, token) == PublishRefused(token, "transport-incomplete")
    assert remote.transport.pushes == pushes
    (report,) = _publish_reports(remote, token)
    assert kinds(report) == REMOTE_LIFECYCLE and report["entries"][-1]["outcome"]["reason"] == "export-damaged"
    after = publish_remote(remote)
    assert type(after) is Published and (mark.corpus_id, marker_uid(token)) in supersedes(remote, after)


# --- Y14 ------------------------------------------------------------------------


def test_y14_a_a_stranded_marked_attempt_blocks_until_resumed_durably(remote, monkeypatch):
    """Y14-a (Ruling 12): step 8 raises before any effect after a verified
    transport; the next publish refuses until the attempt is resumed."""
    crash(monkeypatch, "_bind", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    reading = attempt_reading(fresh_writer(remote), token, moment_seam())
    assert reading is not None and reading.reading == "unfinished"
    tip, ops = chain_tip(remote), _ops_tree(remote)
    with pytest.raises(PublicationRefused) as refused:
        publish_remote(remote)
    assert refused.value.reason == "publish-unfinished" and refused.value.tokens == (token,)
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops
    resumed = resume_remote(remote, token)
    assert type(resumed) is Published
    after = publish_remote(remote)
    assert type(after) is Published and (resumed.corpus_id, resumed.marker) in supersedes(remote, after)


def test_y14_b_an_attempt_without_a_mark_never_blocks_durably(remote, monkeypatch):
    """Y14-b: a request and no mark → the next publish binds."""
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    stranded = token_of_last_intent(remote)
    assert (op_dir(remote, stranded) / "request.v1").is_file() and not (op_dir(remote, stranded) / "transport.v1").exists()
    assert type(publish_remote(remote)) is Published


# --- Y15 ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "step, before",
    [("_mark", False), ("_push", True), ("_push", False), ("_verify", True), ("_verify", False), ("_bind", True)],
    ids=["after-mark", "before-push", "after-push", "before-verify", "after-verify", "before-bind"],
)
def test_y15_a_a_crash_at_every_remote_step_resumes_to_one_binding_and_one_report_durably(remote, monkeypatch, step, before):
    """Y15-a: crash, resume → Published; one binding, one report of the whole
    remote lifecycle; step 9 keeps the export root, the mark, the request and the snapshot."""
    crash(monkeypatch, step, before=before)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    outcome = resume_remote(remote, token)
    assert type(outcome) is Published
    (report,) = _publish_reports(remote, token)
    assert kinds(report) == [*REMOTE_LIFECYCLE, "publication-binding"]
    assert len(_binding_files(remote)) == 1
    op = op_dir(remote, token)
    assert read_lifecycle_state(export_of(remote, token, outcome.corpus_id)) is LifecycleState.READ_ONLY_SERVICEABLE
    assert all((op / name).is_file() for name in ("transport.v1", "request.v1", "selection.v1"))
    assert not (op / "staging").exists() and not (op / "world").exists()


def test_y15_b_a_remote_step_8_refusal_is_an_orphan_the_next_publish_names_durably(remote):
    """Y15-b: cut 39's W17-p-a race through the act. P binds; A's port runs a whole
    remote publish B, superseding P, inside `append_intent` after A's tip read;
    A transports, then refuses `predecessor-not-standing` with `remotely_revealed`."""
    p = publish_remote(remote)
    assert type(p) is Published
    inner = remote.writer._operation_port
    superseding: list[object] = []

    class SecondWriter:
        def append_intent(self, payload):
            if not superseding:
                superseding.append(publish_remote(remote))  # B supersedes P before A's intent lands
            return inner.append_intent(payload)

        def __getattr__(self, name):
            return getattr(inner, name)

    a = publish_remote(remote, port=SecondWriter())
    (b,) = superseding
    assert type(b) is Published
    assert a == PublishRefused(a.event_token, "predecessor-not-standing")
    reading = attempt_reading(fresh_writer(remote), a.event_token, moment_seam())
    assert reading is not None and reading.opened.intent.binding_tips == (p.binding,)
    (report,) = _publish_reports(remote, a.event_token)
    last = report["entries"][-1]["outcome"]
    assert last["remotely_revealed"] is True and last["tips"] == [b.binding]
    a_pair = (mark_of(remote, a.event_token).corpus_id, marker_uid(a.event_token))
    after = publish_remote(remote)
    assert type(after) is Published
    reading = attempt_reading(fresh_writer(remote), after.event_token, moment_seam())
    assert reading is not None and a_pair in reading.opened.intent.marker_tips


# --- Y16 ------------------------------------------------------------------------


def test_y16_a_a_recipient_restores_admits_and_reads_the_current_publication_durably(remote):
    """Y16-a: materialize, restore against the transported artifact, admit, read the tip;
    the same copy missing one file restores to a non-validated verdict and is refused."""
    outcome = publish_remote(remote)
    assert type(outcome) is Published
    root, observers = recipient_copy(remote, outcome)
    admit_publication(recipient_world(remote, (root,)), root, observers)
    assert publication_tip((root,), remote.view, REMOTE) == CurrentPublication(outcome.corpus_id, outcome.marker)
    into = remote.base / f"recipient-partial-{next(_counter)}"
    remote.roots.append(into / outcome.corpus_id)
    partial, sibling = remote.transport.materialize(REMOTE, outcome.corpus_id, into)
    selected = marker_node(partial).facets[stored.COORDINATION_FACET]["selection"][0]
    writable(partial)
    (partial / path_for_node_id(selected)).unlink()
    verdict = restore_root(partial, CorpusSubject(outcome.corpus_id), ObserverSet((ArtifactCarrier.from_bytes(sibling),)), authority=SETUP)
    assert verdict.outcome != "validated"
    with pytest.raises(PublicationArrivalRefused):
        admit_publication(recipient_world(remote, (partial,)), partial, observers)


def test_y16_b_sibling_publications_are_divergent_until_one_supersedes_both_durably(remote, monkeypatch):
    """Y16-b: A crashed before its mark, B bound, A resumed and bound as a sibling.
    Both select the same records; the recipient's epoch refuses duplicate-location,
    and `publication_tip` reads them side by side as divergent until C."""
    crash(monkeypatch, "_initialize")
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    a_token = token_of_last_intent(remote)
    b = publish_remote(remote)
    a = resume_remote(remote, a_token)
    assert type(a) is Published and type(b) is Published
    (a_root, a_obs), (b_root, b_obs) = recipient_copy(remote, a), recipient_copy(remote, b)
    world = recipient_world(remote, (a_root, b_root))
    admit_publication(world, a_root, a_obs)
    admit_publication(world, b_root, b_obs)
    with pytest.raises(AddressMapConflict) as conflict:
        epoch.build_epoch(world, coverage=frozenset({a.corpus_id, b.corpus_id}), bindings=hold_shipped(world))
    assert conflict.value.finding.code == "duplicate-location"
    divergent = publication_tip((a_root, b_root), remote.view, REMOTE)
    assert divergent == DivergentPublication(tuple(sorted([(a.corpus_id, a.marker), (b.corpus_id, b.marker)])))
    c = publish_remote(remote)
    assert type(c) is Published and {(a.corpus_id, a.marker), (b.corpus_id, b.marker)} <= supersedes(remote, c)
    c_root, _ = recipient_copy(remote, c)
    assert publication_tip((a_root, b_root, c_root), remote.view, REMOTE) == CurrentPublication(c.corpus_id, c.marker)


def test_y16_c_a_held_root_with_an_unreadable_record_file_refuses_capture_damaged_durably(remote):
    """Y16-c (the round-3 reviewer's probe): an unreadable extra record file in a
    held root refuses `capture-damaged`, and arrival of the same bytes refuses too."""
    if os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    outcome = publish_remote(remote)
    assert type(outcome) is Published
    root, observers = recipient_copy(remote, outcome)
    admit_publication(recipient_world(remote, (root,)), root, observers)
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    writable(root)
    raw_add(root, extra)
    path = root / path_for_node_id(extra.id)
    path.chmod(0)
    try:
        with pytest.raises(PublicationReadingRefused) as refused:
            publication_tip((root,), remote.view, REMOTE)
        assert refused.value.reason == "capture-damaged" and refused.value.corpus_id == outcome.corpus_id
        with pytest.raises(PermissionError):
            admit_publication(recipient_world(remote, (root,)), root, observers)
    finally:
        path.chmod(0o644)


# --- beyond the units -------------------------------------------------------------


@pytest.mark.parametrize("check", ["serviceable", "sibling", "chain", "chain-deleted", "marker"])
def test_each_export_check_failing_alone_is_transport_mark_corrupt_durably(remote, monkeypatch, check):
    """§11.1: each of §4.2's checks failing alone → transport-mark-corrupt, nothing written.
    The marker case is the content check, which runs after the evaluation validates."""
    crash(monkeypatch, "_push", before=True)
    with pytest.raises(Crash):
        publish_remote(remote)
    monkeypatch.undo()
    token = token_of_last_intent(remote)
    if check == "serviceable":
        monkeypatch.setattr(act, "read_serviceable", lambda _root: False)
    elif check == "sibling":
        real = act.decode_head_artifact
        monkeypatch.setattr(act, "decode_head_artifact", lambda data: replace(real(data), head="0" * 64))
    elif check == "chain":
        monkeypatch.setattr(act, "export_chain_head", lambda _root: None)
    elif check == "chain-deleted":
        export = export_of(remote, token, mark_of(remote, token).corpus_id)
        writable(export)
        shutil.rmtree(export / ".#~chain")  # Task 0's CHAIN_DIR
    else:
        path = op_dir(remote, token) / "transport.v1"
        mark = mark_of(remote, token)
        path.write_bytes(encode_mark(replace(mark, records=mark.records + 1)))
    tip, ops = chain_tip(remote), _ops_tree(remote)
    assert resume_remote(remote, token) == PublishUnresolved(token, "transport-mark-corrupt")
    assert chain_tip(remote) == tip and _ops_tree(remote) == ops


def test_a_push_that_always_raises_writes_nothing_and_keeps_blocking_durably(remote):
    """Review Focus 3: a remote that raises on every push never closes the attempt;
    each resume propagates, writes nothing, and the pair stays blocked."""
    remote.transport.fail_after_files = 0
    with pytest.raises(TransportFault):
        publish_remote(remote)
    token = token_of_last_intent(remote)
    tip = chain_tip(remote)
    for _ in range(2):
        with pytest.raises(TransportFault):
            resume_remote(remote, token)
        assert chain_tip(remote) == tip and _publish_reports(remote, token) == []
    with pytest.raises(PublicationRefused) as refused:
        publish_remote(remote)
    assert refused.value.tokens == (token,)


def test_a_transport_incomplete_attempt_is_never_resumed_durably(remote):
    """§6's last row: closed by transport-incomplete → PublishRefused, and nothing is pushed again."""
    remote.transport.abandon = True
    abandoned = publish_remote(remote)
    remote.transport.abandon = False
    pushes, tip = remote.transport.pushes, chain_tip(remote)
    assert resume_remote(remote, abandoned.event_token) == PublishRefused(abandoned.event_token, "transport-incomplete")
    assert remote.transport.pushes == pushes and chain_tip(remote) == tip


@pytest.mark.parametrize("damage", ["directory", "dangling", "symlink", "unreadable", "fifo"])
def test_a_damaged_mark_blocks_and_never_resumes_the_request(remote, damage):
    """An extant mark keeps the token unfinished even with a corrupt request."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    remote.transport.fail_after_files = 1
    with pytest.raises(TransportFault):
        publish_remote(remote)
    token = token_of_last_intent(remote)
    op = op_dir(remote, token)
    mark = op / "transport.v1"
    data = mark.read_bytes()
    mark.unlink()
    if damage == "directory":
        mark.mkdir()
    elif damage in ("dangling", "symlink"):
        target = op / "mark-target"
        if damage == "symlink":
            target.write_bytes(data)
        mark.symlink_to(target)
    elif damage == "fifo":
        os.mkfifo(mark)
    else:
        mark.write_bytes(data)
        mark.chmod(0)
    (op / "request.v1").write_bytes(b"corrupt request")
    remote.transport.fail_after_files = None
    tip = chain_tip(remote)
    try:
        with pytest.raises(PublicationRefused) as refused:
            publish_remote(remote)
        assert refused.value.reason == "publish-unfinished" and refused.value.tokens == (token,)
        assert resume_remote(remote, token) == PublishUnresolved(token, "transport-mark-corrupt")
        reading = attempt_reading(fresh_writer(remote), token, moment_seam())
        assert reading is not None and reading.reading == "unfinished"
        assert chain_tip(remote) == tip and _publish_reports(remote, token) == []
    finally:
        if damage == "unreadable":
            mark.chmod(0o644)
