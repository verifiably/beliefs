"""Marker-required arrival (publish-act-local design §10)."""

from __future__ import annotations

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile, raw_add
from nodes.core.write_plan import DefaultExecutor
from profiles import pins_for
from test_publish_intent import intent

from beliefs import publication_arrival, stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import PublicationArrivalRefused
from beliefs.publication import binding_record, marker_record
from beliefs.publication_arrival import admit_publication


@pytest.fixture()
def arriving(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(publication_arrival, "admit_arrival", lambda *args, **kwargs: calls.append((args, kwargs)) or ("record", "report"))
    profile = coordination_profile(None, version=2)
    writer = CorpusWriter(tmp_path / "arriving", lambda root: DefaultExecutor(root), authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    run = stored.run_node("r", title="r", spec="s", produces=[])
    writer._stage_record(__import__("nodes.core.frontmatter", fromlist=["node_to_markdown"]).node_to_markdown(run))
    return writer, run, calls


def _marker(selection):
    return marker_record(intent(), world_id="d" * 32, epoch="f" * 64, selection=selection)


def test_a_consistent_publication_is_handed_to_admit_arrival(arriving):
    writer, run, calls = arriving
    writer._stage_marker(_marker((run.id,)))
    assert admit_publication("world", writer.root, "observers") == ("record", "report")
    ((args, _),) = calls
    assert args[1] == writer.root.resolve() and args[2].parent_corpus_id == writer.corpus_id


def test_no_marker_refuses_before_admission(arriving):
    writer, _, calls = arriving
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "marker-absent" and calls == []


def test_two_markers_refuse(arriving):
    writer, run, calls = arriving
    writer._stage_marker(_marker((run.id,)))
    raw_add(writer.root, marker_record(intent(event_token="9" * 32), world_id="d" * 32, epoch="f" * 64, selection=(run.id,)))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "marker-duplicated" and calls == []


def test_a_malformed_marker_refuses(arriving):
    writer, run, calls = arriving
    marker = _marker((run.id,))
    marker.facets[stored.COORDINATION_FACET]["selection"] = ["not an id"]
    raw_add(writer.root, marker)
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "marker-malformed" and calls == []


def test_a_binding_in_the_root_refuses(arriving):
    writer, run, calls = arriving
    writer._stage_marker(_marker((run.id,)))
    raw_add(writer.root, binding_record(intent(), corpus_id="1" * 32, marker="2" * 32, artifact="3" * 64))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "binding-present" and calls == []


@pytest.mark.parametrize("extra", [True, False], ids=["record-beyond-selection", "selected-record-missing"])
def test_records_other_than_the_selection_refuse(arriving, extra):
    writer, run, calls = arriving
    other = stored.run_node("s", title="s", spec="s", produces=[])
    if extra:
        raw_add(writer.root, other)
        writer._stage_marker(_marker((run.id,)))
    else:
        writer._stage_marker(_marker(tuple(sorted((run.id, other.id)))))
    with pytest.raises(PublicationArrivalRefused) as caught:
        admit_publication("world", writer.root, "observers")
    assert caught.value.reason == "selection-mismatch" and caught.value.refs == (other.id,) and calls == []


# --- publish-act-remote §7.1: the tip reading ---------------------------------

import os
from pathlib import Path

from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id

from beliefs.coordination import CoordinationAddress
from beliefs.errors import PublicationReadingRefused
from beliefs.intents.publish import Destination
from beliefs.publication import marker_uid
from beliefs.publication_arrival import CurrentPublication, DivergentPublication, publication_tip
from beliefs.world import load_manifest

REMOTE = Destination.remote("https://remote.test/pub")
VIEW = CoordinationAddress("a" * 32, "b" * 32, "c" * 32)
_PROFILE = coordination_profile(None, version=2)


def _root(tmp_path: Path, name: str) -> CorpusWriter:
    writer = CorpusWriter(tmp_path / name, lambda root: DefaultExecutor(root), authority=FULL, profile=_PROFILE)
    writer.adopt_manifest(profile=pins_for(_PROFILE))
    return writer


def _publish_into(writer: CorpusWriter, token: str, *, carried=(), records=("r",), destination=REMOTE):
    """Stage the selected records and the marker of `token`'s publish, carrying `carried` as its marker tips."""
    nodes = [stored.run_node(name, title=name, spec="s", produces=[]) for name in records]
    for node in nodes:
        writer._stage_record(node_to_markdown(node))
    value = intent(event_token=token, marker_tips=tuple(carried), destination=destination)
    writer._stage_marker(marker_record(value, world_id="d" * 32, epoch="f" * 64, selection=tuple(sorted(n.id for n in nodes))))
    return writer.root, load_manifest(writer.root).corpus_id, marker_uid(token)


def _held(tmp_path, name, token, **kwargs):
    return _publish_into(_root(tmp_path, name), token, **kwargs)


def test_no_marker_at_the_address_reads_none(tmp_path):
    assert publication_tip((), VIEW, REMOTE) is None
    root, _, _ = _held(tmp_path, "elsewhere", "1" * 32, destination=Destination.remote("https://remote.test/other"))
    assert publication_tip((root,), VIEW, REMOTE) is None


def test_one_marker_is_current(tmp_path):
    root, corpus_id, marker = _held(tmp_path, "a", "1" * 32)
    assert publication_tip((root,), VIEW, REMOTE) == CurrentPublication(corpus_id, marker)


def test_two_siblings_are_divergent_ascending(tmp_path):
    a, ca, ma = _held(tmp_path, "a", "1" * 32)
    b, cb, mb = _held(tmp_path, "b", "2" * 32)
    assert publication_tip((b, a), VIEW, REMOTE) == DivergentPublication(tuple(sorted([(ca, ma), (cb, mb)])))


def test_publications_sharing_selected_records_are_read_side_by_side(tmp_path):
    """Decision 9's premise: one record in two held roots does not stop the reading."""
    a, ca, ma = _held(tmp_path, "a", "1" * 32, records=("r", "s"))
    b, cb, mb = _held(tmp_path, "b", "2" * 32, carried=((ca, ma),), records=("r", "s"))
    assert publication_tip((a, b), VIEW, REMOTE) == CurrentPublication(cb, mb)


def test_an_orphan_with_a_successor_reads_the_successor(tmp_path):
    a, ca, ma = _held(tmp_path, "a", "1" * 32)
    b, cb, mb = _held(tmp_path, "b", "2" * 32, carried=((ca, ma),))
    assert publication_tip((a, b), VIEW, REMOTE) == CurrentPublication(cb, mb)


def test_a_missing_intermediate_is_divergent(tmp_path):
    a, ca, ma = _held(tmp_path, "a", "1" * 32)
    c, cc, mc = _held(tmp_path, "c", "3" * 32, carried=(("9" * 32, marker_uid("2" * 32)),))  # C supersedes B only
    assert publication_tip((a, c), VIEW, REMOTE) == DivergentPublication(tuple(sorted([(ca, ma), (cc, mc)])))


def test_one_marker_uid_in_two_corpora_is_marker_duplicated(tmp_path):
    a, _, _ = _held(tmp_path, "a", "1" * 32)
    b, _, _ = _held(tmp_path, "b", "1" * 32)
    with pytest.raises(PublicationReadingRefused) as caught:
        publication_tip((a, b), VIEW, REMOTE)
    assert caught.value.reason == "marker-duplicated" and caught.value.corpus_id is None


def test_a_supersession_cycle_refuses(tmp_path):
    first, second = _root(tmp_path, "a"), _root(tmp_path, "b")
    ca, cb = first.corpus_id, second.corpus_id
    a, _, _ = _publish_into(first, "1" * 32, carried=((cb, marker_uid("2" * 32)),))
    b, _, _ = _publish_into(second, "2" * 32, carried=((ca, marker_uid("1" * 32)),))
    with pytest.raises(PublicationReadingRefused) as caught:
        publication_tip((a, b), VIEW, REMOTE)
    assert caught.value.reason == "supersession-cycle"


_R = stored.run_node("r", title="r", spec="s", produces=[])


def _two_markers(writer):
    _publish_into(writer, "1" * 32)
    raw_add(writer.root, marker_record(intent(event_token="9" * 32, destination=REMOTE), world_id="d" * 32, epoch="f" * 64, selection=(_R.id,)))


def _beyond_selection(writer):
    _publish_into(writer, "1" * 32)
    raw_add(writer.root, stored.run_node("s", title="s", spec="s", produces=[]))


def _binding(writer):
    _publish_into(writer, "1" * 32)
    raw_add(writer.root, binding_record(intent(destination=REMOTE), corpus_id="1" * 32, marker="2" * 32, artifact="3" * 64))


def _malformed(writer):
    writer._stage_record(node_to_markdown(_R))
    node = marker_record(intent(event_token="1" * 32, destination=REMOTE), world_id="d" * 32, epoch="f" * 64, selection=(_R.id,))
    node.facets[stored.COORDINATION_FACET]["selection"] = ["not an id"]
    raw_add(writer.root, node)


def _inconsistent(writer):
    writer._stage_record(node_to_markdown(_R))
    node = marker_record(intent(event_token="1" * 32, destination=REMOTE), world_id="d" * 32, epoch="f" * 64, selection=(_R.id,))
    node.facets[stored.COORDINATION_FACET]["event_token"] = "8" * 32
    raw_add(writer.root, node)


@pytest.mark.parametrize(
    "build, reason",
    [
        (_two_markers, "marker-duplicated"),
        (_beyond_selection, "selection-mismatch"),
        (_binding, "binding-present"),
        (_malformed, "marker-malformed"),
        # The changed token fails the existing content rule before consistency.
        (_inconsistent, "marker-malformed"),
    ],
    ids=["two-markers", "beyond-selection", "binding", "malformed", "inconsistent"],
)
def test_the_reading_refuses_what_arrival_would_refuse(tmp_path, monkeypatch, build, reason):
    writer = _root(tmp_path, "held")
    build(writer)
    with pytest.raises(PublicationReadingRefused) as caught:
        publication_tip((writer.root,), VIEW, REMOTE)
    assert caught.value.reason == reason and caught.value.corpus_id == writer.corpus_id
    monkeypatch.setattr(publication_arrival, "admit_arrival", lambda *args, **kwargs: ("record", "report"))
    with pytest.raises(PublicationArrivalRefused) as arrival:
        admit_publication("world", writer.root, "observers")
    assert arrival.value.reason == reason


@pytest.mark.parametrize("damage", ["unreadable", "undecodable"])
@pytest.mark.parametrize("holds_marker", [True, False], ids=["marker-root", "markerless-root"])
def test_a_damaged_root_refuses_capture_damaged(tmp_path, damage, holds_marker):
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    writer = _root(tmp_path, "held")
    if holds_marker:
        _publish_into(writer, "1" * 32)
    extra = stored.run_node("zz", title="zz", spec="s", produces=[])
    raw_add(writer.root, extra)
    path = writer.root / path_for_node_id(extra.id)
    if damage == "unreadable":
        path.chmod(0)
    else:
        path.write_bytes(b"\x00\xffnot a record")
    try:
        with pytest.raises(PublicationReadingRefused) as caught:
            publication_tip((writer.root,), VIEW, REMOTE)
        assert caught.value.reason == "capture-damaged" and caught.value.corpus_id == writer.corpus_id
    finally:
        path.chmod(0o644)


def test_a_root_named_twice_is_a_value_error(tmp_path):
    """Review Focus 5: by path and through a symlink."""
    root, _, _ = _held(tmp_path, "a", "1" * 32)
    os.symlink(root, tmp_path / "link")
    with pytest.raises(ValueError):
        publication_tip((root, tmp_path / "link"), VIEW, REMOTE)
    with pytest.raises(TypeError):
        publication_tip([root], VIEW, REMOTE)  # type: ignore[arg-type]
