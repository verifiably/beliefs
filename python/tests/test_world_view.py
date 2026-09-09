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


def chain_nodes():
    """D0 -> R1 -> D1 -> R2 -> D2, R1 and D1 placed in BETA by the caller."""
    d0 = stored.dataset_node("d0", title="d0")
    r1 = stored.run_node("r1", title="r1", spec="s", transforms=[d0.id], produces=["dataset:d1"])
    d1 = stored.dataset_node(
        "d1",
        title="d1",
        basis={
            "tag": "single",
            "routes": [
                {"identity": "route:d1", "run": r1.id, "ancestor": d0.id, "transforms": [d0.id]}
            ],
        },
    )
    r2 = stored.run_node("r2", title="r2", spec="s", transforms=[d1.id], produces=["dataset:d2"])
    d2 = stored.dataset_node(
        "d2",
        title="d2",
        basis={
            "tag": "single",
            "routes": [
                {"identity": "route:d2", "run": r2.id, "ancestor": d1.id, "transforms": [d1.id]}
            ],
        },
    )
    return d0, r1, d1, r2, d2


def chain_world(tmp_path: Path):
    d0, r1, d1, r2, d2 = chain_nodes()
    coverage = (ALPHA, BETA)
    roots = corpora(tmp_path, {ALPHA: (d0, r2, d2), BETA: (r1, d1)})
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    return world, roots, publish(world, coverage, bindings)


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

    def test_a_postpublication_live_address_rename_is_corruption(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        old = address_in(published, ALPHA)
        renamed = reopen(roots[ALPHA]).get(old).model_copy(
            deep=True,
            update={"id": "dataset:postpublication-new", "deprecated_ids": [old]},
        )
        (roots[ALPHA] / "dataset" / f"{old.partition(':')[2]}.md").unlink()
        raw_write(roots[ALPHA], renamed)

        with pytest.raises(ResolutionRefused, match="live address"):
            open_world_view(world, published)


class TestBoundReads:
    def test_published_producers_unite_alias_rows_with_producer_present_or_absent(self, tmp_path):
        dataset = stored.dataset_node("d-new", title="dataset").model_copy(
            update={"deprecated_ids": ["dataset:d-old"]}
        )
        first = stored.run_node("r1", title="run 1", spec="analysis-spec:r1", produces=[dataset.id])
        second = stored.run_node("r2", title="run 2", spec="analysis-spec:r2", produces=["dataset:d-old"])
        roots = corpora(tmp_path, {ALPHA: (dataset,), BETA: (first, second)})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))

        view = open_world_view(world, published)
        assert view.published_producers(dataset.id) == (first.id, second.id)
        assert view.published_producers("dataset:d-old") == (first.id, second.id)

        make_absent(roots, BETA)
        absent = open_world_view(world, published)
        assert absent.published_producers(dataset.id) == (first.id, second.id)
        assert absent.published_producers("dataset:d-old") == (first.id, second.id)

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


class TestCrossCorpusEdges:
    def test_inbound_crosses_the_corpus_edge_and_is_dangling_locally(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        view = open_world_view(world, published)
        producers_of_d1 = {
            e.relation.source for e in view.inbound("dataset:d1") if e.relation.predicate == "produces"
        }
        assert producers_of_d1 == {"run:r1"}
        producers_of_d2 = {
            e.relation.source for e in view.inbound("dataset:d2") if e.relation.predicate == "produces"
        }
        assert producers_of_d2 == {"run:r2"}
        # r2 transforms d1, which BETA holds: found at the world layer, dangling in ALPHA alone.
        assert {
            e.relation.source for e in view.inbound("dataset:d1") if e.relation.predicate == "transforms"
        } == {"run:r2"}
        with pytest.raises(RefError):  # the corpus facade cannot even ask about a ref it does not hold
            ReadView.opened_at(roots[ALPHA]).inbound("dataset:d1")

    def test_inbound_to_an_absent_record_still_finds_present_sources(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert type(view.locate("dataset:d1")) is read.NotPresent
        assert {e.relation.source for e in view.inbound("dataset:d1")} == {"run:r2"}
        assert view.inbound("dataset:never-observed") == []

    def test_a_drift_source_files_no_edge_and_producers_excludes_it(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        raw_write(roots[ALPHA], stored.run_node("late", title="late", spec="s", produces=["dataset:d2"]))
        view = open_world_view(world, published)
        assert "run:late" not in {e.relation.source for e in view.inbound("dataset:d2")}
        assert view.producers("dataset:d2") == ("run:r2",)

    def test_a_drift_copy_of_a_foreign_target_does_not_hide_the_edge(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        raw_write(roots[ALPHA], stored.dataset_node("d1", title="a drift copy of BETA's d1"))
        view = open_world_view(world, published)
        assert view.corpus_of("dataset:d1") == BETA
        assert {
            e.relation.source for e in view.inbound("dataset:d1") if e.relation.predicate == "transforms"
        } == {"run:r2"}

    def test_published_producers_survive_an_absent_carrier(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert view.published_producers("dataset:d1") == ("run:r1",)
        assert view.published_producers("dataset:d2") == ("run:r2",)
        assert view.published_producers("dataset:never-observed") == ()


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


class TestW10:
    def test_the_world_closure_is_complete_and_the_local_one_truncates(self, tmp_path):
        from beliefs.corpus import LineageAdjacency, RelationAdjacency
        from beliefs.traversal import closure

        world, roots, published = chain_world(tmp_path)
        view = open_world_view(world, published)
        world_reach = closure("dataset:d2", LineageAdjacency(view))
        assert set(world_reach.reached) == {"dataset:d1", "dataset:d0"}
        assert world_reach.unresolved == ()
        local_reach = closure("dataset:d2", LineageAdjacency(ReadView.opened_at(roots[ALPHA])))
        assert set(local_reach.reached) == set()
        assert local_reach.unresolved != ()
        produced = closure("dataset:d1", RelationAdjacency(view, "produces", "inbound"))
        assert set(produced.reached) == {"run:r1"}

    def test_derived_from_and_superseded_by_cross_the_world_only(self, tmp_path):
        from nodes.core.relations import Relation

        from beliefs.corpus import derived_from, superseded_by

        d0, r1, d1, _r2, _d2 = chain_nodes()
        old = stored.proposition_node("old", title="old", claim={"operator": "affects"})
        new = stored.proposition_node("new", title="new", claim={"operator": "causes"})
        new.relations.append(Relation(source=new.id, predicate=stored.SUPERSEDES, target=old.id))
        roots = corpora(tmp_path, {ALPHA: (d0, old), BETA: (r1, d1, new)})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))

        view = open_world_view(world, published)
        assert derived_from(view, d1.id).reached == (d0.id,)
        assert superseded_by(view, old.id) == (new.id,)
        assert derived_from(ReadView.opened_at(roots[BETA]), d1.id).reached == ()
        assert superseded_by(ReadView.opened_at(roots[ALPHA]), old.id) == ()
