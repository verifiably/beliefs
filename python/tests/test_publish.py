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
