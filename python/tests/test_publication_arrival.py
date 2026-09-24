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
