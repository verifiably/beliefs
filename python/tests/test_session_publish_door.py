"""The publish act's preview and its session door (sharing design §2
decisions 6, 7, 9, 10 and 12, §4.4, §4.7, §6 "The preview" and "The publish
door, end to end").

The preview section runs `publication_preview` over Task 5's published-source
world on the certified volume: it returns exactly what a subsequent `publish`
freezes, pins a subordinate view, refuses as the act refuses, and needs no
authority. Its v3 case reuses the attribution module's wrapper fixture.

The door section opens an attended session over the same world, writing the
written root, and runs `ScopedWriter.publish` and `resume_publish`: the
binding and the act reports reach the ledger as `act` lines matching the
chain, and a stale, closed, under-permitted or resolver-less writer refuses
before any effect. Crashes are injected at step boundaries as the publish
acceptance modules inject them (`crash` below mirrors theirs)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from authority import FULL
from coordination_fixtures import EMPTY_QUERY, content_for, raw_coordination_node
from session_doors_fixture import KINDS, PUBLISHES, V2, Clock, publish_locally, published_source
from test_publication_attribution import wrapper_fixture
from test_session_writer import make_session
from transport_fake import DirectoryTransport

import beliefs.publish as act
import beliefs.session.writer as session_writer
from beliefs import root as science_root
from beliefs import stored
from beliefs.coordination import CoordinationAddress, coordination_revision
from beliefs.corpus import ReadView
from beliefs.errors import (
    CoordinationUnavailable,
    PermitExceeded,
    PermitFact,
    PublicationRefused,
    SessionClosed,
    SessionProtocolError,
)
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities
from beliefs.publication import BINDING_KIND, MARKER_KIND
from beliefs.publication_doors import attempt_reading
from beliefs.publish import PublicationPreview, Published, PublishRefused, publication_preview
from beliefs.publish_request import decode_request, decode_snapshot
from beliefs.root import moment_seam, open_corpus, open_world, open_world_read
from beliefs.session import ScopedWriter, WriterSession, open_attended_session, reconcile_sessions
from beliefs.world import load_manifest
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView

# --- the preview ------------------------------------------------------------------


def _preview(s: SimpleNamespace, view: CoordinationAddress) -> PublicationPreview:
    """The dry run through the read door: no permit at all."""
    return publication_preview(open_world_read(s.config), s.resolver, view, own_pins=load_manifest(s.written).profile)


def _act(s: SimpleNamespace, view: CoordinationAddress) -> object:
    """The local act over `view` under exactly the publication permit."""
    writer = open_corpus(s.written, authority=PUBLISHES, profile=V2, coordination_resolver=s.resolver)
    return act.publish(
        writer,
        s.resolver,
        open_world(s.config, authority=PUBLISHES),
        view=view,
        destination=s.destination,
        operations_root=s.ops,
        staging_profile=V2,
        clock=Clock(),
        seam=moment_seam(),
    )


def _mint(s: SimpleNamespace, kind: str, *, query: dict, project: CoordinationAddress | None = None):
    """A new coordination record in the written root, as its address pinned to its revision."""
    writer = open_corpus(s.written, authority=FULL, profile=V2, coordination_resolver=s.resolver)
    content = content_for(kind, query=query)
    if project is None:
        node = writer.mint_coordination(kind, content=content)
    else:
        node = writer.mint_coordination(kind, project=project, content=content)
    return coordination_revision(node).address.pinned(node.uid)


def _files(root: Path) -> list[tuple[Path, bytes]]:
    return sorted((p.relative_to(root), p.read_bytes()) for p in root.rglob("*") if p.is_file())


def test_the_preview_returns_what_publish_freezes(certified_work):
    s = published_source(certified_work)
    preview = _preview(s, s.view)
    published = publish_locally(s)
    op = s.ops / "publish" / published.event_token
    snapshot = decode_snapshot((op / "selection.v1").read_bytes())
    request = decode_request((op / "request.v1").read_bytes())
    assert (snapshot.records, snapshot.attributions) == (preview.records, preview.attributions)
    assert (request.epoch, request.world_id, request.pins, request.view) == (
        preview.epoch,
        preview.world_id,
        preview.pins,
        preview.view,
    )
    assert preview.view.unpinned() == s.view and preview.view.revision is not None
    assert preview.attributions is None  # the written root pins coordination v2
    assert preview.selected == tuple(address for address, _ in preview.records) != ()
    assert preview.contributing == (s.alpha_id,)


def test_the_preview_of_a_subordinate_view_pins_it(certified_work):
    """Review Focus 5: a question under the project previews pinned to its revision,
    and the act freezes that pinned subordinate view."""
    s = published_source(certified_work)
    question = _mint(s, "question", query=KINDS, project=s.view.unpinned())
    preview = _preview(s, question.unpinned())
    assert preview.view == question
    assert preview.view.local is not None and preview.view.revision is not None
    published = _act(s, question.unpinned())
    assert type(published) is Published
    request = decode_request((s.ops / "publish" / published.event_token / "request.v1").read_bytes())
    assert request.view == preview.view


@pytest.mark.parametrize("case", ["view-unresolved", "empty-selection"])
def test_the_preview_refuses_as_publish_does(certified_work, case):
    s = published_source(certified_work)
    view = CoordinationAddress("1" * 32) if case == "view-unresolved" else _mint(s, "project", query=EMPTY_QUERY)
    with pytest.raises(PublicationRefused) as previewed:
        _preview(s, view)
    with pytest.raises(PublicationRefused) as acted:
        _act(s, view)
    assert previewed.value.reason == acted.value.reason == case
    assert str(previewed.value) == str(acted.value)
    assert not (s.ops / "publish").exists()


def test_the_preview_needs_no_authority(certified_work):
    s = published_source(certified_work)
    before = _files(s.base)
    preview = _preview(s, s.view)
    assert type(preview) is PublicationPreview and preview.records
    assert not (s.ops / "publish").exists()
    assert _files(s.base) == before


def test_the_v3_preview_attributions_are_what_publish_freezes(tmp_path: Path, monkeypatch):
    """Ruling R4: under a v3 coordination pin the preview's attribution entries are the
    ones the act freezes into its snapshot (the attribution module's wrapper fixture,
    with the intent stood in and the steps after the freeze stopped)."""
    s = wrapper_fixture(tmp_path, monkeypatch, writer_version=3)
    token = "1" * 32
    frozen: list[Any] = []
    project = raw_coordination_node("project", "f" * 32, "d" * 32)  # the wrapper fixture's view

    def opening(writer, resolver, *, expected_view, **kwargs):
        return SimpleNamespace(intent=SimpleNamespace(event_token=token, view=expected_view))

    monkeypatch.setattr(act, "_open_publication", opening)
    monkeypatch.setattr(act, "_run", lambda attempt: frozen.append(attempt) or "stopped")
    resolver = SimpleNamespace(mounted=lambda: (s.writer.root,), resolve=lambda address: project)
    preview = publication_preview(
        cast(Any, s.world),
        cast(Any, resolver),
        coordination_revision(project).address,
        own_pins=load_manifest(s.writer.root).profile,
    )
    assert preview.attributions is not None and len(preview.attributions) == 2
    assert s.run() == "stopped"
    snapshot = decode_snapshot((s.ops / "publish" / token / "selection.v1").read_bytes())
    assert snapshot.attributions == preview.attributions == frozen[0].snapshot.attributions
    assert snapshot.records == preview.records
    assert (frozen[0].request.pins, frozen[0].request.epoch) == (preview.pins, preview.epoch)


# --- the door ---------------------------------------------------------------------

DIGEST = "d" * 64
REMOTE = Destination.remote("https://remote.test/pub")
REFUSAL = {"refusal": {"code": "crashed", "message": "the act died at a step boundary", "data": {}}}


class Crash(Exception):
    """A process death at a step boundary: in-memory state is discarded after it."""


def crash(monkeypatch, name: str, *, before: bool = False, on_call: int = 1) -> None:
    """Replace the act's step `name` with one that dies before or after its
    `on_call`th call (the publish acceptance modules' helper, mirrored: the
    portable suite does not import `tests/acceptance`)."""
    original = getattr(act, name)
    calls = {"n": 0}

    def crashing(*args, **kwargs):
        calls["n"] += 1
        if before and calls["n"] == on_call:
            raise Crash(name)
        result = original(*args, **kwargs)
        if not before and calls["n"] == on_call:
            raise Crash(name)
        return result

    monkeypatch.setattr(act, name, crashing)


def publishing_session(
    s: SimpleNamespace, *, required: RequiredCapabilities | None = None, mounted: bool = True
) -> tuple[WriterSession, ScopedWriter]:
    """An attended session over the source world writing its written root,
    invocation `A` claimed and scoped to the publication permit (or `required`)."""
    session = open_attended_session(
        s.config, s.ops / "sessions-root", write_root=s.written, profile=s.profile, mounts=s.mounts if mounted else None
    )
    session.claim_invocation("A", "publish", DIGEST)
    return session, session.scoped(RequiredCapabilities.publishes() if required is None else required, "A")


def _door_publish(writer: ScopedWriter, s: SimpleNamespace, **changes: Any) -> object:
    arguments: dict[str, Any] = {
        "view": s.view,
        "destination": s.destination,
        "operations_root": s.ops,
        "staging_profile": s.profile,
    }
    arguments.update(changes)
    return writer.publish(**arguments)


def _door_resume(writer: ScopedWriter, s: SimpleNamespace, token: str, **changes: Any) -> object:
    arguments: dict[str, Any] = {"event_token": token, "operations_root": s.ops, "staging_profile": s.profile}
    arguments.update(changes)
    return writer.resume_publish(**arguments)


def _chain(s: SimpleNamespace) -> WellFormedView:
    view = science_root.log_seam().inspect_detached(s.written)
    assert type(view) is WellFormedView
    return view


def _publish_tokens(s: SimpleNamespace) -> list[str]:
    """Every publish intent's token on the written chain, in chain order."""
    payloads = [json.loads(e.payload) for e in _chain(s).entries if type(e) is IntentEntryView]
    return [p["event_token"] for p in payloads if p.get("domain") == "science.publish-intent.v1"]


def _registered(s: SimpleNamespace, fulfills: str) -> list[str]:
    return [e.digest for e in _chain(s).entries if type(e) is RegisteredEntryView and e.fulfills == fulfills]


def _written(s: SimpleNamespace, kind: str) -> set[tuple[str, str]]:
    return {(node.uid, node.id) for node in ReadView.opened_at(s.written).iter_stored() if node.kind == kind}


def _intent_digest(s: SimpleNamespace, token: str) -> str:
    reader = open_corpus(s.written, authority=FULL, profile=V2, coordination_resolver=s.resolver)
    reading = attempt_reading(reader, token, moment_seam())
    assert reading is not None
    return reading.opened.digest


def test_a_local_publish_through_the_door_ledgers_the_binding_and_report(certified_work):
    s = published_source(certified_work)
    session, writer = publishing_session(s)
    outcome = _door_publish(writer, s)
    assert type(outcome) is Published
    (act_line,) = session.invocation_acts("A")
    assert act_line.intent == _intent_digest(s, outcome.event_token)
    (binding,) = _written(s, BINDING_KIND)
    (report,) = _written(s, "act-report")
    assert binding[0] == outcome.binding
    assert set(act_line.record_ids) == {binding, report} and len(act_line.record_ids) == 2
    assert _registered(s, act_line.intent) == [act_line.entry]
    assert act_line.corpus == s.written_id
    session.close_invocation("A", {"done": [list(p) for p in act_line.record_ids]})
    session.close()
    assert reconcile_sessions(s.config, s.ops / "sessions-root") == ()


def test_a_refused_publish_ledgers_the_refusal_report(certified_work, monkeypatch):
    """A sibling another writer left at the export path → `export-collision`: the
    refusal report alone reaches the write root, and the ledger names it."""
    s = published_source(certified_work)
    session, writer = publishing_session(s)
    original = act._write_sibling

    def colliding(a, corpus_id, artifact):
        (s.dest / f"{corpus_id}.head-artifact.v1").write_bytes(b"someone else's artifact")
        return original(a, corpus_id, artifact)

    monkeypatch.setattr(act, "_write_sibling", colliding)
    outcome = _door_publish(writer, s)
    (token,) = _publish_tokens(s)
    assert outcome == PublishRefused(token, "export-collision")
    (act_line,) = session.invocation_acts("A")
    assert act_line.record_ids == tuple(_written(s, "act-report"))
    assert act_line.intent == _intent_digest(s, token) and _registered(s, act_line.intent) == [act_line.entry]
    assert _written(s, BINDING_KIND) == set()
    session.close_invocation("A", {"done": [list(p) for p in act_line.record_ids]})
    session.close()
    assert reconcile_sessions(s.config, s.ops / "sessions-root") == ()


def test_resume_in_a_second_invocation_ledgers_under_it(certified_work, monkeypatch):
    s = published_source(certified_work)
    session, writer = publishing_session(s)
    crash(monkeypatch, "_replicate", before=True)
    with pytest.raises(Crash):
        _door_publish(writer, s)
    monkeypatch.undo()
    (token,) = _publish_tokens(s)
    assert session.invocation_acts("A") == ()  # the intent is not an act; nothing reached the write root yet
    session.close_invocation("A", REFUSAL)
    session.claim_invocation("B", "publish", "e" * 64)
    writer_b = session.scoped(RequiredCapabilities.publishes(), "B")
    outcome = _door_resume(writer_b, s, token)
    assert type(outcome) is Published and outcome.event_token == token
    (act_line,) = session.invocation_acts("B")
    assert act_line.invocation == "B" and act_line.intent == _intent_digest(s, token)
    assert outcome.binding in {uid for uid, _ in act_line.record_ids}
    assert set(act_line.record_ids) == _written(s, BINDING_KIND) | _written(s, "act-report")
    assert _registered(s, act_line.intent) == [act_line.entry]
    assert session.invocation_acts("A") == ()
    session.close_invocation("B", {"done": [list(p) for p in act_line.record_ids]})
    session.close()
    assert reconcile_sessions(s.config, s.ops / "sessions-root") == ()


def _left_remote(s: SimpleNamespace, monkeypatch, left: str) -> tuple[WriterSession, ScopedWriter, str]:
    """A remote attempt through invocation A, stopped by a crash: `marked` — the
    transport mark written and nothing pushed; `bound-undiscarded` — bound, with
    staging and its world still on disk."""
    (s.base / "remote").mkdir()
    s.transport = DirectoryTransport(s.base / "remote")
    s.destination = REMOTE
    session, writer = publishing_session(s)
    crash(monkeypatch, "_push" if left == "marked" else "_discard", before=True)
    with pytest.raises(Crash):
        _door_publish(writer, s, transport=s.transport)
    monkeypatch.undo()
    (token,) = _publish_tokens(s)
    op = s.ops / "publish" / token
    assert (op / "transport.v1").is_file()
    if left == "marked":
        assert s.transport.pushes == 0 and session.invocation_acts("A") == ()
    else:
        assert s.transport.pushes == 1 and len(session.invocation_acts("A")) == 1
        assert (op / "staging").is_dir() and (op / "world").is_dir()
    return session, writer, token


def _assert_untouched(s: SimpleNamespace, token: str, left: str, pushes: int, before: list) -> None:
    op = s.ops / "publish" / token
    assert s.transport.pushes == pushes
    assert _files(s.ops / "publish") == before
    if left == "bound-undiscarded":
        assert (op / "staging").is_dir() and (op / "world").is_dir()


@pytest.mark.parametrize("left", ["marked", "bound-undiscarded"])
def test_a_stale_writer_refuses_before_any_effect_with_a_transport_spy(certified_work, monkeypatch, left):
    s = published_source(certified_work)
    session, writer, token = _left_remote(s, monkeypatch, left)
    session.close_invocation("A", REFUSAL)
    pushes, before, acts = s.transport.pushes, _files(s.ops / "publish"), session.invocation_acts("A")
    with pytest.raises(SessionProtocolError):
        _door_publish(writer, s, transport=s.transport)
    with pytest.raises(SessionProtocolError):
        _door_resume(writer, s, token, transport=s.transport)
    _assert_untouched(s, token, left, pushes, before)
    assert session.invocation_acts("A") == acts


@pytest.mark.parametrize("left", ["marked", "bound-undiscarded"])
def test_a_closed_session_writer_refuses_session_closed(certified_work, monkeypatch, left):
    s = published_source(certified_work)
    session, writer, token = _left_remote(s, monkeypatch, left)
    session.close()
    pushes, before = s.transport.pushes, _files(s.ops / "publish")
    with pytest.raises(SessionClosed):
        _door_publish(writer, s, transport=s.transport)
    with pytest.raises(SessionClosed):
        _door_resume(writer, s, token, transport=s.transport)
    _assert_untouched(s, token, left, pushes, before)


def test_a_coordination_scoped_writer_refuses_the_permit_before_the_world_is_opened(certified_work, monkeypatch):
    s = published_source(certified_work)
    session, writer = publishing_session(s, required=RequiredCapabilities.coordination())

    def opened(*args, **kwargs):
        raise AssertionError("opened")

    monkeypatch.setattr(session_writer, "open_world", opened)
    with pytest.raises(PermitExceeded) as publishing:
        _door_publish(writer, s)
    with pytest.raises(PermitExceeded) as resuming:
        _door_resume(writer, s, "1" * 32)
    assert publishing.value.requirement == resuming.value.requirement == PermitFact("family", "publish")
    assert session.invocation_acts("A") == () and _publish_tokens(s) == []
    assert not (s.ops / "publish").exists()


def test_a_session_without_a_resolver_refuses_coordination_unavailable(certified_work):
    s = published_source(certified_work)
    session, writer = publishing_session(s, mounted=False)
    with pytest.raises(CoordinationUnavailable, match="no coordination resolver"):
        _door_publish(writer, s)
    with pytest.raises(CoordinationUnavailable, match="no coordination resolver"):
        _door_resume(writer, s, "1" * 32)
    assert session.invocation_acts("A") == () and _publish_tokens(s) == []
    assert not (s.ops / "publish").exists()


def test_a_session_without_a_world_configuration_refuses_both_publish_doors(tmp_path):
    """Decision 6: the doors open their world from the session's configuration;
    a session opened without one has no world to publish from."""
    session, _ = make_session(tmp_path, coordination_resolver=cast(Any, SimpleNamespace()))
    session.claim_invocation("A", "publish", DIGEST)
    writer = session.scoped(RequiredCapabilities.publishes(), "A")
    with pytest.raises(SessionProtocolError, match="no world configuration; the admit and publish doors have no world"):
        writer.publish(
            view=CoordinationAddress("1" * 32),
            destination=Destination.local(str(tmp_path)),
            operations_root=tmp_path,
            staging_profile=V2,
        )
    with pytest.raises(SessionProtocolError, match="no world configuration; the admit and publish doors have no world"):
        writer.resume_publish(event_token="1" * 32, operations_root=tmp_path, staging_profile=V2)
    assert session.invocation_acts("A") == ()


def test_an_operations_root_inside_a_mount_is_unusable_from_the_act(certified_work):
    """Review Focus 4: the act's own root rule refuses after the door's entry
    checks and its world open: no intent on the chain and no act line."""
    s = published_source(certified_work)
    session, writer = publishing_session(s)
    inside = s.alpha / "ops"
    inside.mkdir()
    with pytest.raises(PublicationRefused) as refused:
        _door_publish(writer, s, operations_root=inside)
    assert refused.value.reason == "operations-root-unusable"
    assert session.invocation_acts("A") == () and _publish_tokens(s) == []
    assert session.current_invocation == "A"


def test_a_subordinate_view_publishes_through_the_door(certified_work):
    """Review Focus 5: a question under the project publishes through the door;
    the request and the marker carry the question pinned to its revision."""
    s = published_source(certified_work)
    question = _mint(s, "question", query=KINDS, project=s.view.unpinned())
    session, writer = publishing_session(s)
    outcome = _door_publish(writer, s, view=question.unpinned())
    assert type(outcome) is Published
    request = decode_request((s.ops / "publish" / outcome.event_token / "request.v1").read_bytes())
    assert request.view == question and question.local is not None
    export = s.dest / outcome.corpus_id
    (marker,) = (n for n in ReadView.opened_at(export).iter_stored() if n.kind == MARKER_KIND)
    assert marker.facets[stored.COORDINATION_FACET]["published_from"]["view"] == str(question)
    (act_line,) = session.invocation_acts("A")
    assert act_line.intent == _intent_digest(s, outcome.event_token)
    assert set(act_line.record_ids) == _written(s, BINDING_KIND) | _written(s, "act-report")


def test_the_door_opens_the_publication_inside_the_closing_hold(certified_work, monkeypatch):
    """Ruling R15 (decision 9): step 0's intent is appended inside the session's
    `_closing_hold` — entered before `_open_publication`, exited after it — and
    steps 1-9 run outside it."""
    s = published_source(certified_work)
    session, writer = publishing_session(s)
    events: list[str] = []
    hold, opening, running = ScopedWriter._closing_hold, act._open_publication, act._run

    @contextmanager
    def spying_hold(self) -> Iterator[None]:
        events.append("enter")
        with hold(self):
            yield
        events.append("exit")

    def spying_open(*args, **kwargs):
        events.append("open")
        return opening(*args, **kwargs)

    def spying_run(*args, **kwargs):
        events.append("run")
        return running(*args, **kwargs)

    monkeypatch.setattr(ScopedWriter, "_closing_hold", spying_hold)
    monkeypatch.setattr(act, "_open_publication", spying_open)
    monkeypatch.setattr(act, "_run", spying_run)
    assert type(_door_publish(writer, s)) is Published
    assert events == ["enter", "open", "exit", "run"]
    assert len(session.invocation_acts("A")) == 1


@pytest.mark.parametrize("scenario", ["forward", "closed", "stale", "permit", "resolver"])
def test_y17_w_scoped_ownership(certified_work, monkeypatch, scenario):
    s = published_source(certified_work)
    session, writer = publishing_session(
        s,
        required=RequiredCapabilities.coordination() if scenario == "permit" else None,
        mounted=scenario != "resolver",
    )
    own = frozenset({s.alpha_id, s.written_id})
    try:
        if scenario == "forward":

            def publish_spy(*args, own_corpora=frozenset(), **kwargs):
                assert own_corpora is own
                return "forwarded"

            monkeypatch.setattr(act, "publish", publish_spy)
            assert _door_publish(writer, s, own_corpora=own) == "forwarded"
        else:
            if scenario == "closed":
                session.close()
            elif scenario == "stale":
                session.close_invocation("A", REFUSAL)
            monkeypatch.setattr(
                session_writer, "open_world", lambda *a, **kw: pytest.fail("world opened before preflight")
            )
            error = {
                "closed": SessionClosed,
                "stale": SessionProtocolError,
                "permit": PermitExceeded,
                "resolver": CoordinationUnavailable,
            }[scenario]
            with pytest.raises(error):
                _door_publish(writer, s, own_corpora=["malformed"])
            assert not (s.ops / "publish").exists()
    finally:
        session.close()
