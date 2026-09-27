"""The act's classifier (publish-act-local design §5). Its flows and resume
refusals are Task 8's acceptance module; these tests read raw staging files."""

from __future__ import annotations

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile
from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_publish_intent import intent

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import MalformedRecord
from beliefs.publication import marker_record
from beliefs.publish import _Population, _population, _require_snapshot_records
from beliefs.publish_request import Snapshot
from beliefs.report import StagingCorrupt

PINNED = [{"name": "matrix", "digest": "sha256:" + "1" * 64}]
"""A dataset needs at least one accepted digest to mint an id (`test_publish_request.py`)."""


def _nodes():
    d = stored.dataset_node(title="d", resources=PINNED)
    r = stored.run_node("r", title="r", spec="s", produces=[d.id])
    s = stored.run_node("s", title="s", spec="s", produces=[])
    return sorted((d, r, s), key=lambda n: n.id)


@pytest.fixture()
def staging(tmp_path):
    profile = coordination_profile(None, version=2)
    # `DefaultExecutor` itself is the factory: a root's writers share one executor factory
    writer = CorpusWriter(tmp_path / "staging", DefaultExecutor, authority=FULL, profile=profile)
    manifest = writer.adopt_manifest(profile=pins_for(profile))
    nodes = _nodes()
    snapshot = Snapshot("e" * 32, tuple((n.id, node_to_markdown(n)) for n in nodes))
    marker = marker_record(
        intent(event_token="e" * 32), world_id="d" * 32, epoch="f" * 64, selection=tuple(n.id for n in nodes)
    )
    return writer, manifest.corpus_id, snapshot, marker, {n.id: n for n in nodes}


def test_an_empty_staging_is_a_prefix_of_zero(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    assert _population(writer, corpus_id, snapshot, marker) == _Population(0, False)


def test_a_true_prefix_resumes_at_its_length(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    writer._stage_record(snapshot.records[0][1])
    assert _population(writer, corpus_id, snapshot, marker) == _Population(1, False)


def test_complete_requires_the_marker_byte_equal(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    for _, text in snapshot.records:
        writer._stage_record(text)
    writer._stage_marker(marker)
    assert _population(writer, corpus_id, snapshot, marker) == _Population(3, True)


def test_every_record_without_the_marker_is_still_a_prefix(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    for _, text in snapshot.records:
        writer._stage_record(text)
    assert _population(writer, corpus_id, snapshot, marker) == _Population(3, False)


def test_a_hole_is_corrupt(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    writer._stage_record(snapshot.records[1][1])
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "hole", (snapshot.records[0][0],))


def test_an_extra_record_is_corrupt(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    writer._stage_record(node_to_markdown(extra))
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "extra", (extra.id,))


def test_a_byte_mismatch_is_corrupt(staging):
    writer, corpus_id, snapshot, marker, by_id = staging
    first = snapshot.records[0][0]
    writer._stage_record(snapshot.records[0][1])
    path = writer.root / writer._relative_path(by_id[first])
    path.chmod(0o644)
    path.write_text(path.read_text() + "\n")
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "bytes", (first,))


def test_a_marker_present_early_is_corrupt(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    writer._stage_marker(marker)
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "marker", (marker.id,))


def test_a_marker_unequal_to_the_expected_one_is_corrupt(staging):
    writer, corpus_id, snapshot, marker, _ = staging
    for _, text in snapshot.records:
        writer._stage_record(text)
    other = marker_record(
        intent(event_token="e" * 32), world_id="c" * 32, epoch="f" * 64, selection=tuple(i for i, _ in snapshot.records)
    )
    assert other.id == marker.id
    writer._stage_marker(other)
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "marker", (marker.id,))


@pytest.mark.parametrize(
    ("relative", "content"),
    [
        ("run/zz.md", b"not a record at all\n"),  # frontmatter missing
        ("zz.md", b"\xff\xfegarbage"),  # not UTF-8, outside any kind directory
        ("run/misfiled.md", None),  # a snapshot record off its mapped path
    ],
    ids=["garbage", "not-utf8", "misfiled"],
)
def test_an_unreadable_staging_file_is_corrupt_bytes(staging, relative, content):
    """Spec §5, Y7: a staging store `nodes` refuses to read is a terminal
    `staging-corrupt`, never a raw exception that leaves the attempt unfinished."""
    writer, corpus_id, snapshot, marker, _ = staging
    writer._stage_record(snapshot.records[0][1])
    path = writer.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(snapshot.records[1][1].encode("utf-8") if content is None else content)
    assert _population(writer, corpus_id, snapshot, marker) == StagingCorrupt(corpus_id, "bytes", ())


class _View:
    """`get` over a dict: the captured records the pre-intent check compares against."""

    def __init__(self, nodes):
        self._nodes = {n.id: n for n in nodes}

    def get(self, ref):
        return self._nodes[ref].model_copy(deep=True)


def test_the_captured_records_pass_the_pre_intent_check():
    nodes = _nodes()
    _require_snapshot_records(_View(nodes), tuple((n.id, node_to_markdown(n)) for n in nodes))


def test_a_text_that_is_not_its_canonical_rendering_refuses_before_the_intent():
    nodes = _nodes()
    records = tuple((n.id, node_to_markdown(n)) for n in nodes)
    # a quoted title parses to the captured record but is not its canonical rendering
    bent = tuple((i, t.replace("title: r\n", "title: 'r'\n", 1) if i == "run:r" else t) for i, t in records)
    assert bent != records and node_from_markdown(dict(bent)["run:r"]) == next(n for n in nodes if n.id == "run:r")
    with pytest.raises(MalformedRecord, match="canonical"):
        _require_snapshot_records(_View(nodes), bent)


def test_a_canonical_text_of_another_record_refuses_before_the_intent():
    nodes = _nodes()
    run = next(n for n in nodes if n.id == "run:r")
    other = stored.run_node("r", title="not the captured title", spec="s", produces=[r.target for r in run.relations])
    assert other.id == run.id and other != run
    records = tuple((n.id, node_to_markdown(other if n.id == run.id else n)) for n in nodes)
    with pytest.raises(MalformedRecord, match="captured"):
        _require_snapshot_records(_View(nodes), records)


# --- publish-act-remote §3.2, §4.3: the seam guards and step 7 ------------------

import os
from hashlib import sha256
from types import SimpleNamespace
from typing import Any, cast

from authority import ACTOR
from transport_fake import DirectoryTransport

from beliefs import publish as act
from beliefs.errors import ValidationRefused
from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities, scoped_authority
from beliefs.publish_request import TransportMark
from beliefs.report import Transported, TransportIncomplete
from beliefs.transport import listing_identity, local_listing, transport_files
from beliefs.world.anchors import CorpusSubject, HeadArtifact, head_artifact_bytes

REMOTE = Destination.remote("https://remote.test/pub")
CID, TOKEN = "1" * 32, "d" * 32


def _writer(tmp_path):
    from coordination_fixtures import coordination_profile
    from nodes.core.write_plan import DefaultExecutor

    from beliefs.corpus import CorpusWriter

    root = tmp_path / "written"
    root.mkdir()
    return CorpusWriter(
        root, DefaultExecutor, authority=scoped_authority(RequiredCapabilities.publishes(), ACTOR),
        profile=coordination_profile(None, version=2),
    )


def _call_publish(writer, destination, transport):
    none = cast(Any, None)
    return act.publish(
        writer, none, none, view=none, destination=destination, operations_root=none, staging_profile=none,
        clock=none, seam=none, transport=transport,
    )


def test_a_remote_destination_without_a_transport_refuses_first(tmp_path):
    with pytest.raises(ValidationRefused, match="needs a transport"):
        _call_publish(_writer(tmp_path), REMOTE, None)


def test_a_local_destination_with_a_transport_refuses_first(tmp_path):
    with pytest.raises(ValidationRefused, match="takes no transport"):
        _call_publish(_writer(tmp_path), Destination.local(str(tmp_path)), DirectoryTransport(tmp_path / "remote"))


@pytest.mark.parametrize("destination, transport", [(REMOTE, None), ("local", "fake")], ids=["remote-without", "local-with"])
def test_resume_applies_the_seam_rule_to_the_intents_destination(tmp_path, monkeypatch, destination, transport):
    target = Destination.local(str(tmp_path)) if destination == "local" else destination
    opened = SimpleNamespace(intent=SimpleNamespace(destination=target, actor=ACTOR, event_token=TOKEN))
    monkeypatch.setattr(act, "attempt_reading", lambda *_: SimpleNamespace(opened=opened, reading="unfinished", outcome=None))
    none = cast(Any, None)
    with pytest.raises(ValidationRefused):
        act.resume_publish(
            _writer(tmp_path), none, event_token=TOKEN, operations_root=tmp_path, staging_profile=none, clock=none, seam=none,
            transport=DirectoryTransport(tmp_path / "remote") if transport == "fake" else None,
        )


def _remote(tmp_path, monkeypatch, verdict="validated", fake=None):
    """A `_Remote` over a hand-built export container and a mark agreeing with it;
    the evaluation is stubbed, so step 7's own logic runs without the engine."""
    op = tmp_path / "op"
    root = op / "export" / CID
    (root / "run").mkdir(parents=True)
    (root / "run" / "a.md").write_bytes(b"a")
    sibling = head_artifact_bytes(HeadArtifact(CorpusSubject(CID), "a" * 64, "b" * 64))
    (op / "export" / f"{CID}.head-artifact.v1").write_bytes(sibling)
    monkeypatch.setattr(act, "evaluate_copy", lambda *_args: verdict)
    fake = fake or DirectoryTransport(tmp_path / "remote")
    none = cast(Any, None)
    opened = cast(Any, SimpleNamespace(intent=SimpleNamespace(destination=REMOTE, event_token=TOKEN)))
    remote = act._Remote(none, none, opened, op, none, none, None, fake)
    mark = TransportMark(TOKEN, REMOTE, CID, "2" * 32, sha256(sibling).hexdigest(), 1)
    return remote, mark, fake


def test_a_verified_transport_answers_its_listing_identity(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch)
    expected = local_listing(transport_files(remote.op / "export", CID))
    assert act._transport(remote, mark) == Transported(CID, listing_identity(expected)) and fake.pushes == 1


def test_an_export_the_evaluation_refuses_is_export_damaged_and_never_pushed(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch, verdict="refuted")
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "export-damaged") and fake.pushes == 0


def test_an_unreadable_export_file_is_export_damaged_and_never_pushed(tmp_path, monkeypatch):
    if os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    remote, mark, fake = _remote(tmp_path, monkeypatch)
    path = remote.op / "export" / CID / "run" / "a.md"
    path.chmod(0)
    try:
        assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "export-damaged") and fake.pushes == 0
    finally:
        path.chmod(0o644)


def test_bytes_changed_during_the_evaluation_are_export_damaged(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch)

    def changing(*_args):
        (remote.op / "export" / CID / "run" / "a.md").write_bytes(b"changed")
        return "validated"

    monkeypatch.setattr(act, "evaluate_copy", changing)
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "export-damaged") and fake.pushes == 0


def test_an_abandoning_seam_is_abandoned(tmp_path, monkeypatch):
    remote, mark, fake = _remote(tmp_path, monkeypatch)
    fake.abandon = True
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "abandoned")


class _Lying(DirectoryTransport):
    def __init__(self, base, lie):
        super().__init__(base)
        self.lie = lie

    def listing(self, destination, corpus_id):
        return self.lie(super().listing(destination, corpus_id))


@pytest.mark.parametrize(
    "lie",
    [
        lambda listed: {name: digest.upper() for name, digest in listed.items()},
        lambda listed: {name: digest for name, digest in listed.items() if not name.endswith(".head-artifact.v1")},
    ],
    ids=["upper-case-digests", "sibling-omitted"],
)
def test_a_listing_that_is_not_exact_is_listing_mismatch(tmp_path, monkeypatch, lie):
    """Review Focus 2: anything but an exact listing is refused, never taken as verified."""
    remote, mark, _ = _remote(tmp_path, monkeypatch, fake=_Lying(tmp_path / "remote", lie))
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "listing-mismatch")


@pytest.mark.parametrize("damage", ["symlink", "missing-sibling", "scan-error"])
def test_export_enumeration_damage_after_the_mark_never_pushes(tmp_path, monkeypatch, damage):
    remote, mark, fake = _remote(tmp_path, monkeypatch)
    if damage == "symlink":
        (remote.op / "export" / CID / "link").symlink_to("run/a.md")
    elif damage == "missing-sibling":
        (remote.op / "export" / f"{CID}.head-artifact.v1").unlink()
    else:
        def unreadable(*_args):
            raise PermissionError("cannot scan export")
        monkeypatch.setattr(act, "transport_files", unreadable)
    assert act._transport(remote, mark) == TransportIncomplete(CID, "2" * 32, "export-damaged")
    assert fake.pushes == 0


@pytest.mark.parametrize("damage", ["symlink", "scan-error"])
def test_export_enumeration_refuses_before_creating_the_mark(tmp_path, monkeypatch, damage):
    remote, mark, _ = _remote(tmp_path, monkeypatch)
    attempt = cast(Any, SimpleNamespace(
        token=TOKEN, op=remote.op, request=SimpleNamespace(destination=REMOTE),
        snapshot=SimpleNamespace(records=("record",)),
    ))
    error = MalformedRecord
    if damage == "symlink":
        (remote.op / "export" / CID / "link").symlink_to("run/a.md")
    else:
        def unreadable(*_args):
            raise PermissionError("cannot scan export")
        monkeypatch.setattr(act, "transport_files", unreadable)
        error = PermissionError
    with pytest.raises(error):
        act._mark(attempt, CID, mark.artifact)
    assert not (remote.op / "transport.v1").exists()
