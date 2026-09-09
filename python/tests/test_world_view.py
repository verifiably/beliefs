"""A coherent world read view bound to one published epoch."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from fixtures_cut4 import raw_write, reopen
from nodes.core.errors import RefError
from nodes.core.write_plan import DefaultExecutor
from test_world_build import ALPHA, BETA, sample_nodes, slug_for
from test_world_receipts import corpora, hold_shipped, publish, world_over

from beliefs import stored
from beliefs.corpus import ReadView, _root_state_for
from beliefs.errors import BuildContended, EpochUnknown, RecordNotPresent, ResolutionRefused
from beliefs.world import read
from beliefs.world.view import DriftReport, WorldReadView, open_world_view


def two_corpus_world(tmp_path: Path):
    coverage = (ALPHA, BETA)
    roots = corpora(
        tmp_path,
        {ALPHA: sample_nodes(slug_for(ALPHA, coverage)), BETA: sample_nodes(slug_for(BETA, coverage))},
    )
    world = world_over(tmp_path, roots)
    return world, roots, publish(world, coverage, hold_shipped(world))


def address_in(published, corpus_id: str, kind: str = "dataset") -> str:
    entries = cast(list[dict[str, str]], published.documents["address-map.yaml"]["addresses"])
    for entry in entries:
        if entry["corpus_id"] == corpus_id and entry["address"].startswith(f"{kind}:"):
            return entry["address"]
    raise AssertionError(f"no {kind} in {corpus_id}")


def make_absent(roots: dict[str, Path], corpus_id: str) -> None:
    (roots[corpus_id] / "corpus.yaml").unlink()


class TestOpening:
    def test_the_stamp_is_the_epochs(self, tmp_path):
        world, _roots, published = two_corpus_world(tmp_path)
        view = open_world_view(world, published)
        assert isinstance(view, WorldReadView)
        assert view.stamp == read.BoundStamp(published.packaging_identity, published.coverage)
        assert view.absent() == ()
        assert view.drift() == ()

    def test_a_foreign_world_epoch_is_unknown(self, tmp_path):
        _world, roots, published = two_corpus_world(tmp_path)
        foreign = world_over(tmp_path, roots, name="foreign", world_id="2" * 32)
        with pytest.raises(EpochUnknown):
            open_world_view(foreign, published)

    def test_a_present_corpus_captures_and_an_absent_one_is_named(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        alpha, beta = address_in(published, ALPHA), address_in(published, BETA)
        assert view.absent() == (BETA,)
        assert type(view.locate(alpha)) is read.Resolved
        assert type(view.locate(beta)) is read.NotPresent
        assert type(view.locate("dataset:never-observed")) is read.Unknown
        assert view.corpus_of(beta) == BETA
        assert view.corpus_of("dataset:never-observed") is None
        assert view.resolve(beta) is None and not view.holds(beta)
        with pytest.raises(RecordNotPresent) as caught:
            view.get(beta)
        assert (caught.value.ref, caught.value.corpus_id, caught.value.stamp) == (beta, BETA, view.stamp)
        with pytest.raises(RefError):
            view.get("dataset:never-observed")

    def test_a_writer_holding_the_lock_refuses_the_open_at_once(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        with _root_state_for(roots[ALPHA], DefaultExecutor).lock, pytest.raises(BuildContended):
            open_world_view(world, published)

    def test_one_uid_under_two_corpora_refuses_at_open(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        alpha = address_in(published, ALPHA)
        twin = reopen(roots[ALPHA]).get(alpha).model_copy(deep=True, update={"id": "dataset:twin"})
        raw_write(roots[BETA], twin)
        with pytest.raises(ResolutionRefused, match="uid uniqueness"):
            open_world_view(world, published)

    def test_a_carrier_disagreeing_with_the_map_is_corruption(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        alpha = address_in(published, ALPHA)
        entries = cast(list[dict[str, str]], published.documents["address-map.yaml"]["addresses"])
        uid = next(e["uid"] for e in entries if e["address"] == alpha)
        path = roots[ALPHA] / "dataset" / f"{alpha.partition(':')[2]}.md"
        path.write_text(path.read_text().replace(uid, "f" * 32))
        with pytest.raises(ResolutionRefused):
            open_world_view(world, published)


class TestBoundReads:
    def test_reads_are_from_the_capture_and_drift_is_reported_on_the_next_open(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        first = open_world_view(world, published)
        alpha = address_in(published, ALPHA)
        before = first.get(alpha)
        late = stored.dataset_node("late", title="late")
        raw_write(roots[ALPHA], late)
        assert first.get(alpha) == before
        assert "dataset:late" not in {n.id for n in first.iter_stored()}
        assert first.drift() == ()
        assert type(first.locate("dataset:late")) is read.Unknown
        second = open_world_view(world, published)
        assert second.drift() == (
            DriftReport(ALPHA, dict(published.coverage)[ALPHA], second.drift()[0].captured_state, (late.uid,)),
        )
        assert "dataset:late" not in {n.id for n in second.iter_stored()}

    def test_enumeration_is_mapped_records_in_corpus_order(self, tmp_path):
        world, _roots, published = two_corpus_world(tmp_path)
        view = open_world_view(world, published)
        ids = [n.id for n in view.iter_stored()]
        entries = cast(list[dict[str, Any]], published.documents["address-map.yaml"]["addresses"])
        recorded = {cast(str, e["address"]) for e in entries}
        assert set(ids) <= recorded and len(ids) == len(set(ids))
        corpora_seen = [cast(str, view.corpus_of(i)) for i in ids]
        assert corpora_seen == sorted(corpora_seen)

    def test_get_validates_like_the_facade(self, tmp_path):
        from nodes.core.corpus import Corpus
        from nodes.core.frontmatter import node_to_markdown

        from beliefs.errors import SemanticHashStale

        world, roots, published = two_corpus_world(tmp_path)
        alpha = address_in(published, ALPHA)
        node = Corpus(roots[ALPHA]).get(alpha)
        node.facets["dataset"]["resources"] = [{"digest": "f" * 64}]
        (roots[ALPHA] / "dataset" / f"{alpha.partition(':')[2]}.md").write_text(node_to_markdown(node))
        view = open_world_view(world, published)
        with pytest.raises(SemanticHashStale):
            view.get(alpha)

    def test_corpus_view_is_the_holding_corpus_and_refuses_absence(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert type(view.corpus_view(address_in(published, ALPHA))) is ReadView
        with pytest.raises(RecordNotPresent):
            view.corpus_view(address_in(published, BETA))
        with pytest.raises(RefError):
            view.corpus_view("dataset:never-observed")


def test_returned_objects_are_detached(tmp_path):
    world, _roots, published = two_corpus_world(tmp_path)
    view = open_world_view(world, published)
    alpha = address_in(published, ALPHA)
    node = view.get(alpha)
    node.title = "mutated"
    node.facets["dataset"]["resources"].append({"digest": "x"})
    assert view.get(alpha).title != "mutated"
    assert view.get(alpha).facets["dataset"]["resources"] == []
    yielded = next(n for n in view.iter_stored() if n.id == alpha)
    yielded.deprecated_ids.append("dataset:fake")
    assert "dataset:fake" not in next(n for n in view.iter_stored() if n.id == alpha).deprecated_ids
    assert view.get(alpha) is not view.get(alpha)
