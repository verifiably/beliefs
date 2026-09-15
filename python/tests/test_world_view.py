"""A coherent world read view bound to one published epoch."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from authority import FULL
from dataset_fixtures import dataset_ref, pinned
from domain_facet_fixtures import kwargs_for, profile_with, seed
from fixtures_cut4 import raw_write, reopen
from nodes.core.corpus import Corpus
from nodes.core.errors import RefError
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_world_build import ALPHA, BETA, sample_nodes, slug_for
from test_world_receipts import corpora, hold_shipped, publish, world_over
from verification_fixtures import publish_corpus, self_consistent_forgery

from beliefs import stored
from beliefs.corpus import CorpusWriter, ReadView, _root_state_for, lineage_snapshot
from beliefs.errors import BuildContended, CaptureDrift, EpochUnknown, RecordNotPresent, ResolutionRefused
from beliefs.lineage import Absence, snapshot_projection
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
    d0 = stored.dataset_node(title="d0", resources=pinned("d0"))
    r1 = stored.run_node("r1", title="r1", spec="s", transforms=[d0.id], produces=[dataset_ref("d1")])
    d1 = stored.dataset_node(
        title="d1",
        resources=pinned("d1"),
        basis={
            "tag": "single",
            "routes": [
                {"identity": "route:d1", "run": r1.id, "ancestor": d0.id, "transforms": [d0.id]}
            ],
        },
    )
    r2 = stored.run_node("r2", title="r2", spec="s", transforms=[d1.id], produces=[dataset_ref("d2")])
    d2 = stored.dataset_node(
        title="d2",
        resources=pinned("d2"),
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
        path = Corpus(roots[ALPHA]).store.path_for(alpha)
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
        Corpus(roots[ALPHA]).store.path_for(old).unlink()
        raw_write(roots[ALPHA], renamed)

        with pytest.raises(ResolutionRefused, match="live address"):
            open_world_view(world, published)


class TestBoundReads:
    def test_published_producers_unite_alias_rows_with_producer_present_or_absent(self, tmp_path):
        dataset = stored.dataset_node(title="dataset", resources=pinned("d-new")).model_copy(
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
        late = stored.dataset_node(title="late", resources=pinned("late"))
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
        Corpus(roots[ALPHA]).store.path_for(alpha).write_text(node_to_markdown(node))
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
    @pytest.mark.parametrize("source_state", ["unknown", "absent", "local", "foreign"])
    def test_inbound_resolves_the_declared_source_not_the_container(self, tmp_path, source_state):
        from beliefs.corpus import RelationAdjacency
        from beliefs.traversal import closure

        holder = stored.dataset_node(title="holder", resources=pinned("holder"))
        target = stored.dataset_node(title="target", resources=pinned("target"))
        source = stored.dataset_node(title="source", resources=pinned("source"))
        holder.relations.append(Relation(source=source.id, predicate="cites", target=target.id))
        alpha = (holder, target, source) if source_state == "local" else (holder, target)
        beta = (source,) if source_state in ("absent", "foreign") else ()
        roots = corpora(tmp_path, {ALPHA: alpha, BETA: beta})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))
        if source_state == "absent":
            make_absent(roots, BETA)
        view = open_world_view(world, published)
        local = ReadView.opened_at(roots[ALPHA])

        edges = view.inbound(target.id)
        if source_state == "unknown":
            assert type(view.locate(source.id)) is read.Unknown
            assert edges == []
        else:
            assert len(edges) == 1 and edges[0].relation == holder.relations[0]
            assert edges[0].target_uid == target.uid
            assert edges[0].source_uid == (None if source_state == "absent" else source.uid)
        local_edges = local.inbound(target.id)
        assert len(local_edges) == 1
        assert local_edges[0].source_uid == (source.uid if source_state == "local" else None)
        world_reach = closure(target.id, RelationAdjacency(view, "cites", "inbound"))
        local_reach = closure(target.id, RelationAdjacency(local, "cites", "inbound"))
        assert world_reach.reached == ((source.id,) if source_state in ("local", "foreign") else ())
        assert local_reach.reached == ((source.id,) if source_state == "local" else ())

    def test_inbound_crosses_the_corpus_edge_and_is_dangling_locally(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        view = open_world_view(world, published)
        producers_of_d1 = {
            e.relation.source for e in view.inbound(dataset_ref("d1")) if e.relation.predicate == "produces"
        }
        assert producers_of_d1 == {"run:r1"}
        producers_of_d2 = {
            e.relation.source for e in view.inbound(dataset_ref("d2")) if e.relation.predicate == "produces"
        }
        assert producers_of_d2 == {"run:r2"}
        # r2 transforms d1, which BETA holds: found at the world layer, dangling in ALPHA alone.
        assert {
            e.relation.source for e in view.inbound(dataset_ref("d1")) if e.relation.predicate == "transforms"
        } == {"run:r2"}
        with pytest.raises(RefError):  # the corpus facade cannot even ask about a ref it does not hold
            ReadView.opened_at(roots[ALPHA]).inbound(dataset_ref("d1"))

    def test_inbound_to_an_absent_record_still_finds_present_sources(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert type(view.locate(dataset_ref("d1"))) is read.NotPresent
        assert {e.relation.source for e in view.inbound(dataset_ref("d1"))} == {"run:r2"}
        assert view.inbound("dataset:never-observed") == []

    def test_a_drift_source_files_no_edge_and_producers_excludes_it(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        raw_write(roots[ALPHA], stored.run_node("late", title="late", spec="s", produces=[dataset_ref("d2")]))
        view = open_world_view(world, published)
        assert "run:late" not in {e.relation.source for e in view.inbound(dataset_ref("d2"))}
        assert view.producers(dataset_ref("d2")) == ("run:r2",)

    def test_a_drift_copy_of_a_foreign_target_does_not_hide_the_edge(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        raw_write(roots[ALPHA], stored.dataset_node(title="a drift copy of BETA's d1", resources=pinned("d1")))
        view = open_world_view(world, published)
        assert view.corpus_of(dataset_ref("d1")) == BETA
        assert {
            e.relation.source for e in view.inbound(dataset_ref("d1")) if e.relation.predicate == "transforms"
        } == {"run:r2"}

    def test_published_producers_survive_an_absent_carrier(self, tmp_path):
        world, roots, published = chain_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        assert view.published_producers(dataset_ref("d1")) == ("run:r1",)
        assert view.published_producers(dataset_ref("d2")) == ("run:r2",)
        assert view.published_producers("dataset:never-observed") == ()


def test_returned_objects_are_detached(tmp_path):
    world, _roots, published = two_corpus_world(tmp_path)
    view = open_world_view(world, published)
    alpha = address_in(published, ALPHA)
    node = view.get(alpha)
    resources = [dict(resource) for resource in node.facets["dataset"]["resources"]]
    node.title = "mutated"
    node.facets["dataset"]["resources"].append({"digest": "x"})
    assert view.get(alpha).title != "mutated"
    assert view.get(alpha).facets["dataset"]["resources"] == resources
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
        world_reach = closure(dataset_ref("d2"), LineageAdjacency(view))
        assert set(world_reach.reached) == {dataset_ref("d1"), dataset_ref("d0")}
        assert world_reach.unresolved == ()
        local_reach = closure(dataset_ref("d2"), LineageAdjacency(ReadView.opened_at(roots[ALPHA])))
        assert set(local_reach.reached) == set()
        assert local_reach.unresolved != ()
        produced = closure(dataset_ref("d1"), RelationAdjacency(view, "produces", "inbound"))
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


class TestLineageSnapshotOverTheWorld:
    def test_absence_is_entered_with_its_corpus_and_only_from_not_present(self, tmp_path):
        from beliefs.corpus import lineage_snapshot
        from beliefs.lineage import certify

        world, roots, published = chain_world(tmp_path)
        complete = lineage_snapshot(open_world_view(world, published), [dataset_ref("d2")])
        assert complete.not_present == {}
        assert certify(complete, (dataset_ref("d2"),), ()).state == "independent"

        make_absent(roots, BETA)
        partial = lineage_snapshot(open_world_view(world, published), [dataset_ref("d2")])
        assert partial.not_present == {dataset_ref("d1"): BETA}
        (route,) = partial.bases[dataset_ref("d2")].routes
        assert route.resolved_run == "run:r2" and route.resolved_ancestor is None
        result = certify(partial, (dataset_ref("d2"),), ())
        assert result.state == "not-certified" and "lineage-incomplete" in result.findings
        assert result.absent == (Absence(dataset_ref("d1"), BETA),)
        assert snapshot_projection(partial) != snapshot_projection(complete)

    def test_an_absent_root_is_recorded_before_any_walk(self, tmp_path):
        from beliefs.corpus import lineage_snapshot
        from beliefs.lineage import certify

        world, roots, published = chain_world(tmp_path)
        make_absent(roots, BETA)
        snapshot = lineage_snapshot(open_world_view(world, published), [dataset_ref("d1")])
        assert snapshot.not_present == {dataset_ref("d1"): BETA} and snapshot.roots == (dataset_ref("d1"),)
        result = certify(snapshot, (dataset_ref("d1"),), ())
        assert result.state == "not-certified" and result.absent == (Absence(dataset_ref("d1"), BETA),)

    def test_an_unknown_root_refuses_in_world_and_corpus_views(self, tmp_path):
        from beliefs.corpus import lineage_snapshot

        world, roots, published = chain_world(tmp_path)
        for view in (open_world_view(world, published), ReadView.opened_at(roots[ALPHA])):
            with pytest.raises(RefError):
                lineage_snapshot(view, ["dataset:unknown"])

    def test_a_refusal_is_not_absence(self, tmp_path):
        from nodes.core.corpus import Corpus
        from nodes.core.frontmatter import node_to_markdown

        from beliefs.corpus import lineage_snapshot
        from beliefs.errors import SemanticHashStale

        world, roots, published = chain_world(tmp_path)
        node = Corpus(roots[ALPHA]).get(dataset_ref("d2"))
        node.facets["dataset"]["resources"] = [{"digest": "f" * 64}]
        Corpus(roots[ALPHA]).store.path_for(node.id).write_text(node_to_markdown(node))
        view = open_world_view(world, published)
        with pytest.raises(SemanticHashStale):
            lineage_snapshot(view, [dataset_ref("d2")])

    def test_a_published_producer_survives_its_absent_carrier(self, tmp_path):
        from beliefs.corpus import lineage_snapshot
        from beliefs.lineage import divergence_state

        d0 = stored.dataset_node(title="d0", resources=pinned("d0"))
        d3 = stored.dataset_node(
            title="d3",
            resources=pinned("d3"),
            basis={
                "tag": "single",
                "routes": [
                    {
                        "identity": "route:d3",
                        "run": "run:r3",
                        "ancestor": d0.id,
                        "transforms": [d0.id],
                    }
                ],
            },
        )
        r3 = stored.run_node("r3", title="r3", spec="s", transforms=[d0.id], produces=[d3.id])
        roots = corpora(tmp_path, {ALPHA: (d0, d3), BETA: (r3,)})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))
        present = lineage_snapshot(open_world_view(world, published), [d3.id])
        assert [p.absent for p in present.producers[d3.id]] == [()]
        assert divergence_state(present, d3.id) == "undiverged"

        make_absent(roots, BETA)
        gone = lineage_snapshot(open_world_view(world, published), [d3.id])
        (producer,) = gone.producers[d3.id]
        assert producer.stored_run == r3.id and producer.resolved_run is None and producer.absent == (BETA,)
        assert gone.not_present == {r3.id: BETA}
        assert divergence_state(gone, d3.id) == "incomplete"
        assert snapshot_projection(gone)["divergence"] == {d3.id: "incomplete"}

    def test_a_basisless_dataset_with_an_absent_published_producer_is_incomplete(self, tmp_path):
        from beliefs.corpus import lineage_snapshot
        from beliefs.lineage import certify

        dataset = stored.dataset_node(title="basisless", resources=pinned("basisless"))
        run = stored.run_node("producer", title="producer", spec="s", produces=[dataset.id])
        roots = corpora(tmp_path, {ALPHA: (dataset,), BETA: (run,)})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))
        make_absent(roots, BETA)

        snapshot = lineage_snapshot(open_world_view(world, published), [dataset.id])
        result = certify(snapshot, (dataset.id,), ())

        assert snapshot.producers[dataset.id][0].absent == (BETA,)
        assert result.state == "not-certified" and result.findings == ("lineage-incomplete",)


DATASET_D_A = dataset_ref("d-a")


def split_evaluation_world(tmp_path: Path, beta_refs=(DATASET_D_A,)):
    """Split the seeded corpus across carriers; by default only d-a lives in BETA."""
    scratch = tmp_path / "scratch"
    seeded = seed(scratch, axis="rows")
    nodes = list(seeded.iter_stored())
    beta_nodes = [n for n in nodes if n.id in beta_refs]
    rest = [n for n in nodes if n.id not in beta_refs]
    roots = corpora(tmp_path, {ALPHA: tuple(rest), BETA: tuple(beta_nodes)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    return world, roots, published


def world_kwargs(view, profile):
    """`kwargs_for` over the world view: attribution derived, both corpora pinned alike."""
    kwargs = kwargs_for(view, profile)
    context = replace(
        kwargs["context"],
        snapshot=lineage_snapshot(view, (dataset_ref("d-a"), dataset_ref("d-b"))),
        retractions=replace(kwargs["context"].retractions, coverage=(ALPHA, BETA)),
        node_corpus={},
        pins={ALPHA: kwargs["context"].pins["c1"], BETA: kwargs["context"].pins["c1"]},
    )
    return {**kwargs, "context": context}


class TestEvaluationOverTheWorld:
    @pytest.mark.parametrize("consumer", ["gather", "evaluate", "evaluate_over"])
    @pytest.mark.parametrize("pin_state", ["agree", "disagree", "missing"])
    def test_run_only_corpus_pins_enter_both_contract_walks(self, tmp_path, consumer, pin_state):
        from beliefs.belief import Belief, Refused, evaluate
        from beliefs.errors import ContractDisagreement, MalformedRecord
        from beliefs.evaluation import EvaluationInputs, evaluate_over, gather

        world, _roots, published = split_evaluation_world(tmp_path, ("run:run-a", "run:run-b"))
        view = open_world_view(world, published)
        profile = profile_with()
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert {ref for ref, corpora in inputs.node_corpus.items() if BETA in corpora} == {
            "run:run-a", "run:run-b",
        }
        pins = dict(kwargs["context"].pins)
        other = replace(pins[BETA], science_contract="science:" + "0" * 64)
        pins["unrelated"] = other
        if pin_state == "disagree":
            pins[BETA] = other
        elif pin_state == "missing":
            del pins[BETA]
        context = replace(kwargs["context"], pins=pins)

        def run():
            if consumer == "gather":
                return gather(view, "proposition:p", context=context, profile=profile,
                              resolution=kwargs["resolution"], binding=kwargs["binding"])
            if consumer == "evaluate":
                return evaluate(proposition="proposition:p", records=inputs.records(),
                                context=replace(context, node_corpus=inputs.node_corpus),
                                profile=profile, availability=kwargs["availability"], binding=kwargs["binding"])
            return evaluate_over(view, "proposition:p", **{**kwargs, "context": context})

        if pin_state == "missing":
            with pytest.raises(MalformedRecord, match="hold a closure node but have no entry in pins"):
                run()
        elif pin_state == "disagree" and consumer == "gather":
            with pytest.raises(ContractDisagreement, match="pin different science_contracts"):
                run()
        elif pin_state == "disagree":
            result = run()
            assert isinstance(result, Refused) and "consulted-contracts-disagree" in result.reason
        elif consumer == "gather":
            result = run()
            assert isinstance(result, EvaluationInputs) and result.consulted == inputs.consulted
        else:
            result = run()
            assert isinstance(result, Belief) and result.value == 2

    def test_a_belief_over_two_corpora_attributes_at_the_read(self, tmp_path):
        from beliefs.belief import Belief
        from beliefs.evaluation import evaluate_over, gather

        world, _roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert inputs.absent == ()
        assert ("biology", kwargs["context"].pins[ALPHA].domains["biology"]) in inputs.consulted
        assert len(inputs.observed_facets) == 1  # d-a's gene-axis row, read through BETA's own ReadView
        assert inputs.node_corpus[inputs.observed_facets[0].address] == (BETA,)
        assert inputs.node_corpus["run:run-a"] == (ALPHA,)
        assert set(inputs.read_trace) <= inputs.declared_refs()
        result = evaluate_over(view, "proposition:p", **kwargs)
        assert isinstance(result, Belief)

    def test_an_absent_input_corpus_is_the_banked_reason(self, tmp_path):
        from beliefs.belief import NoBelief
        from beliefs.evaluation import evaluate_over

        world, roots, published = split_evaluation_world(tmp_path)
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        result = evaluate_over(view, "proposition:p", **world_kwargs(view, profile_with()))
        assert isinstance(result, NoBelief)
        assert result.reason == "unavailable-corpus-absent" and BETA in result.detail

    @pytest.mark.parametrize("role", [stored.READS, stored.TRANSFORMS, stored.OBSERVES])
    def test_an_absent_assessment_run_and_every_input_role_are_reported(self, tmp_path, role):
        """Absence beyond the observed dataset: the assessment's own run, and a
        input of each role, each recorded in the absent corpus."""
        from beliefs.belief import NoBelief
        from beliefs.evaluation import evaluate_over, gather

        scratch = tmp_path / "scratch"
        seeded = seed(scratch, axis="rows")
        nodes = list(seeded.iter_stored())
        raw_write(scratch, stored.dataset_node(title="d-t", resources=pinned("d-t")))
        run_b = next(n for n in nodes if n.id == "run:run-b")
        run_b.relations.append(Relation(source=run_b.id, predicate=role, target=dataset_ref("d-t")))
        stored.stamp_semantic_identity(run_b)
        raw_write(scratch, run_b)
        nodes = list(reopen(scratch).iter_stored())
        beta_side = tuple(n for n in nodes if n.id in ("run:run-a", dataset_ref("d-t")))
        alpha_side = tuple(n for n in nodes if n.id not in ("run:run-a", dataset_ref("d-t")))
        roots = corpora(tmp_path, {ALPHA: alpha_side, BETA: beta_side})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))
        profile = profile_with()
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert ("run:run-a", BETA) in inputs.absent and (dataset_ref("d-t"), BETA) in inputs.absent
        result = evaluate_over(view, "proposition:p", **kwargs)
        assert isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent"

    def test_the_derived_attribution_reaches_evaluate(self, tmp_path):
        """An unrelated corpus pinned differently must not reach the consulted
        walk: `evaluate` recomputes it from the context, so the context it gets
        carries the attribution the read derived, not every supplied pin."""
        from beliefs.belief import Belief
        from beliefs.evaluation import evaluate_over

        world, _roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        unrelated = replace(kwargs["context"].pins[ALPHA], science_contract="science:" + "0" * 64)
        context = replace(kwargs["context"], pins={**kwargs["context"].pins, "unrelated": unrelated})
        result = evaluate_over(view, "proposition:p", **{**kwargs, "context": context})
        assert isinstance(result, Belief)

    def test_a_supplied_attribution_over_a_world_view_refuses(self, tmp_path):
        from beliefs.errors import MalformedRecord
        from beliefs.evaluation import gather

        world, _roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        supplied = replace(kwargs["context"], node_corpus={"anything": (ALPHA,)})
        with pytest.raises(MalformedRecord, match="node_corpus.*derived"):
            gather(view, "proposition:p", context=supplied, profile=profile,
                   resolution=kwargs["resolution"], binding=kwargs["binding"])

    @pytest.mark.parametrize("change", ["content", "addition", "removal"])
    def test_a_facet_read_is_held_to_the_capture(self, tmp_path, change):
        """A namespaced facet is not under the semantic hash: editing it after the
        capture leaves `get` content-valid and the address unchanged, and only the
        row-set comparison sees it. A whitespace-only rewrite keeps the row set and
        must not refuse."""
        from beliefs.errors import CaptureDrift
        from beliefs.evaluation import gather

        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        path = Corpus(roots[BETA]).store.path_for(dataset_ref("d-a"))
        path.write_text(path.read_text() + "\n")
        gather(view, "proposition:p", context=kwargs["context"], profile=profile,
               resolution=kwargs["resolution"], binding=kwargs["binding"])
        node = reopen(roots[BETA]).get(dataset_ref("d-a"))
        if change == "content":
            node.facets["biology/gene-axis"]["axis"] = "columns"
        elif change == "removal":
            del node.facets["biology/gene-axis"]
        else:
            node.facets["testing/annotation"] = {"note": "added"}
        path.write_text(node_to_markdown(node))
        assert view.get(dataset_ref("d-a")).facets["biology/gene-axis"]["axis"] == "rows"  # the capture stands
        with pytest.raises(CaptureDrift):
            gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                   resolution=kwargs["resolution"], binding=kwargs["binding"])


    def test_identical_assessment_values_at_distinct_addresses_consult_both_corpora(self, tmp_path):
        from beliefs.belief import Belief, Refused
        from beliefs.evaluation import evaluate_over, gather

        nodes = tuple(seed(tmp_path / "scratch").iter_stored())
        twin = stored.assessment_node(
            "a-twin", title="twin", spec="spec-a", run="run:run-a", proposition="proposition:p",
            outcome="supported", interpretation_rule="rule-1",
        )
        original = next(n for n in nodes if n.id == "assessment:a-1")
        assert original.id != twin.id and original.uid != twin.uid
        assert stored.assessment_value(original) == stored.assessment_value(twin)
        roots = corpora(tmp_path, {ALPHA: nodes, BETA: (twin,)})
        world = world_over(tmp_path, roots)
        view = open_world_view(world, publish(world, (ALPHA, BETA), hold_shipped(world)))
        profile = profile_with()
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert inputs.node_corpus[stored.assessment_value(original).identity()] == (ALPHA, BETA)
        with pytest.raises(TypeError):
            cast(Any, inputs.node_corpus)[stored.assessment_value(original).identity()] = (ALPHA,)
        assert isinstance(evaluate_over(view, "proposition:p", **kwargs), Belief)
        pins = kwargs["context"].pins
        disagreeing = replace(pins[BETA], science_contract="science:" + "0" * 64)
        context = replace(kwargs["context"], pins={ALPHA: pins[ALPHA], BETA: disagreeing})
        result = evaluate_over(view, "proposition:p", **{**kwargs, "context": context})
        assert isinstance(result, Refused) and "consulted-contracts-disagree" in result.reason

    def test_a_proposition_only_absent_carrier_is_reported(self, tmp_path):
        from beliefs.belief import NoBelief
        from beliefs.evaluation import evaluate_over, gather

        world, roots, published = split_evaluation_world(tmp_path, ("proposition:p",))
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        profile = profile_with()
        kwargs = world_kwargs(view, profile)
        assert kwargs["context"].snapshot.not_present == {}
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert inputs.absent == (("proposition:p", BETA),)
        result = evaluate_over(view, "proposition:p", **kwargs)
        assert isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent"
        assert BETA in result.detail

    def test_absence_in_the_supplied_snapshot_is_reported(self, tmp_path):
        from beliefs.belief import NoBelief
        from beliefs.evaluation import evaluate_over, gather

        nodes = tuple(seed(tmp_path / "scratch").iter_stored())
        extra = stored.dataset_node(title="extra", resources=pinned("extra"))
        roots = corpora(tmp_path, {ALPHA: nodes, BETA: (extra,)})
        world = world_over(tmp_path, roots)
        published = publish(world, (ALPHA, BETA), hold_shipped(world))
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        profile = profile_with()
        kwargs = world_kwargs(view, profile)
        context = replace(kwargs["context"], snapshot=lineage_snapshot(
            view, (dataset_ref("d-a"), dataset_ref("d-b"), dataset_ref("extra"))))
        inputs = gather(view, "proposition:p", context=context, profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert inputs.absent == ((dataset_ref("extra"), BETA),)
        result = evaluate_over(view, "proposition:p", **{**kwargs, "context": context})
        assert isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent"

    def test_an_unknown_proposition_reference_is_not_absence(self, tmp_path):
        from beliefs.evaluation import gather

        nodes = tuple(n for n in seed(tmp_path / "scratch").iter_stored() if n.kind != "proposition")
        roots = corpora(tmp_path, {ALPHA: nodes, BETA: ()})
        world = world_over(tmp_path, roots)
        view = open_world_view(world, publish(world, (ALPHA, BETA), hold_shipped(world)))
        profile = profile_with()
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert inputs.absent == () and inputs.claim is None


def split_verification_world(tmp_path: Path):
    scratch = tmp_path / "scratch"
    writer = CorpusWriter(scratch, DefaultExecutor, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    published = publish_corpus(writer, publish=True)
    assert published.node is not None
    forged = self_consistent_forgery(
        writer, published.node, mutate=lambda facet: facet.__setitem__("verdict", "failed")
    )
    nodes = tuple(reopen(scratch).iter_stored())
    runs = tuple(node for node in nodes if node.kind == "run")
    roots = corpora(tmp_path, {ALPHA: tuple(node for node in nodes if node.kind != "run"), BETA: runs})
    world = world_over(tmp_path, roots)
    epoch = publish(world, (ALPHA, BETA), hold_shipped(world))
    view = open_world_view(world, epoch)
    assert view.corpus_of(published.node.id) == ALPHA
    assert all(view.corpus_of(run.id) == BETA for run in runs)
    return published, forged, roots, view, world, epoch


class TestR19AcrossCorpora:
    def test_a_genuine_verification_is_checked(self, tmp_path):
        from beliefs.audit import check_verification

        published, _forged, _roots, view, _world, _epoch = split_verification_world(tmp_path)
        assert published.node is not None
        outcome = check_verification(view, view.get(published.node.id), evidence=published.evidence)
        assert outcome.checked and outcome.contradiction is None

    def test_a_verdict_only_well_formed_forgery_is_a_finding(self, tmp_path):
        from beliefs.audit import check_verification

        published, forged, _roots, view, _world, _epoch = split_verification_world(tmp_path)
        outcome = check_verification(view, view.get(forged.id), evidence=published.evidence)
        assert outcome.checked and outcome.contradiction is not None
        assert outcome.contradiction.code == "verification-derivation-contradicted"

    def test_a_malformed_record_raises(self, tmp_path):
        from beliefs.audit import check_verification
        from beliefs.errors import MalformedRecord

        published, _forged, _roots, view, _world, _epoch = split_verification_world(tmp_path)
        assert published.node is not None
        malformed = view.get(published.node.id)
        malformed.facets["verification"]["report"] = {"forged": True}
        with pytest.raises(MalformedRecord):
            check_verification(view, malformed, evidence=published.evidence)

    def test_a_corpus_local_view_leaves_foreign_runs_unchecked(self, tmp_path):
        from beliefs.audit import check_verification

        published, _forged, roots, _view, _world, _epoch = split_verification_world(tmp_path)
        assert published.node is not None
        local = ReadView.opened_at(roots[ALPHA])
        outcome = check_verification(local, local.get(published.node.id), evidence=published.evidence)
        assert not outcome.checked and outcome.contradiction is None
        assert outcome.reason.endswith("does not resolve here")


def damage(root: Path, kind: str) -> None:
    """Apply one damage named by the four construction clauses."""
    from nodes.core.frontmatter import node_from_markdown

    stored_files = sorted(root.rglob("*.md"))
    if kind == "parse-error":
        (root / "verification").mkdir(exist_ok=True)
        (root / "verification" / "bad.md").write_text("---\nnot: [a valid record\n---\n", encoding="utf-8")
        return
    if kind == "path-mismatch":
        source = stored_files[0]
        source.rename(source.with_name("moved-" + source.name))
        return
    original = node_from_markdown(stored_files[0].read_text(encoding="utf-8"))
    twin = original.model_copy(deep=True)
    kind_prefix, _, slug = original.id.partition(":")
    twin.id = f"{kind_prefix}:{slug}-twin"
    if kind == "uid-collision":
        pass
    elif kind == "id-collision":
        twin.uid = f"twin-{original.uid}"
        twin.deprecated_ids = [original.id]
    else:
        raise ValueError(kind)
    raw_write(root, twin)


class TestReportMode:
    @pytest.mark.parametrize("kind", ["parse-error", "path-mismatch", "uid-collision", "id-collision"])
    def test_a_damaged_carrier_is_reported_and_never_served(self, tmp_path, kind):
        from beliefs.errors import CorpusDamaged, CorpusStateMalformed

        world, roots, published = two_corpus_world(tmp_path)
        damage(roots[BETA], kind)

        with pytest.raises(CorpusStateMalformed):
            open_world_view(world, published)
        view = open_world_view(world, published, on_damage="report")

        (report,) = view.damaged()
        assert report.corpus_id == BETA and report.cause == "construction"
        assert kind in {finding.code for finding in report.findings}
        assert view.absent() == () and all(d.corpus_id != BETA for d in view.drift())
        address = address_in(published, BETA)
        for read_it in (view.locate, view.resolve, view.holds, view.get, view.inbound, view.corpus_view):
            with pytest.raises(CorpusDamaged):
                read_it(address)
        assert view.corpus_of(address) == BETA
        assert all(node.id != address for node in view.iter_stored())
        assert view.captured_records(BETA) and view.captured_manifest(BETA).corpus_id == BETA
        assert view.get(address_in(published, ALPHA)).id == address_in(published, ALPHA)

    def test_a_foreign_base_pin_is_damage_with_no_records(self, tmp_path):
        from fixtures_cut6 import manifest_document

        from beliefs.errors import ContractMismatch, CorpusDamaged

        world, roots, published = two_corpus_world(tmp_path)
        manifest = manifest_document(BETA).replace(
            f"science_contract: {pins_for(BASE).science_contract}", "science_contract: science:" + "0" * 64
        )
        (roots[BETA] / "corpus.yaml").write_text(manifest, encoding="utf-8")

        with pytest.raises(ContractMismatch):
            open_world_view(world, published)
        view = open_world_view(world, published, on_damage="report")

        (report,) = view.damaged()
        assert report.cause == "base-pin" and report.findings == ()
        assert view.captured_records(BETA) == ()
        assert view.captured_manifest(BETA).profile.science_contract == "science:" + "0" * 64
        with pytest.raises(CorpusDamaged):
            view.get(address_in(published, BETA))

    def test_a_damaged_corpus_skips_the_map_and_owner_checks(self, tmp_path):
        world, roots, published = two_corpus_world(tmp_path)
        damage(roots[BETA], "uid-collision")
        view = open_world_view(world, published, on_damage="report")
        assert view.damaged()[0].corpus_id == BETA

    def test_the_hold_is_the_lock_only_lookup(self, tmp_path, monkeypatch):
        """Strict corpus construction must happen only after the hold is taken."""
        from beliefs import corpus as corpus_module

        world, roots, published = two_corpus_world(tmp_path)
        damage(roots[BETA], "parse-error")

        def refuse(*_a, **_k):
            raise AssertionError("_root_state_for called under report mode")

        monkeypatch.setattr(corpus_module, "_root_state_for", refuse)
        view = open_world_view(world, published, on_damage="report")
        assert view.damaged()[0].corpus_id == BETA

    def test_drift_moving_inside_the_hold_still_raises(self, tmp_path, monkeypatch):
        world, roots, published = two_corpus_world(tmp_path)
        from beliefs.world import registry as registry_module

        calls = {"n": 0}
        original = registry_module.corpus_state_identity

        def moving(root):
            calls["n"] += 1
            if calls["n"] == 2:
                raw_write(roots[ALPHA], stored.dataset_node(title="late", resources=pinned("late")))
            return original(root)

        monkeypatch.setattr(registry_module, "corpus_state_identity", moving)
        with pytest.raises(CaptureDrift):
            open_world_view(world, published, on_damage="report")


def test_mapped_records_enumerate_what_iter_stored_yields_without_copying(tmp_path):
    world, _roots, published = two_corpus_world(tmp_path)
    view = open_world_view(world, published)
    pairs = list(view._mapped_records())
    assert [node.id for _, node in pairs] == [node.id for node in view.iter_stored()]
    assert [corpus for corpus, _ in pairs] == [view.corpus_of(node.id) for _, node in pairs]
    first = pairs[0][1]
    assert pairs[0][1] is first and next(iter(view._mapped_records()))[1] is first
