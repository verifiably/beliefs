"""The act's classifier (publish-act-local design §5). Its flows and resume
refusals are Task 8's acceptance module; these tests read raw staging files."""

from __future__ import annotations

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_publish_intent import intent

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.publication import marker_record
from beliefs.publish import _Population, _population
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
