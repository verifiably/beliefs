"""Standing over a world read: the epoch's enumeration, its scope, coverage,
relocation, absence and the split (correction-remainder slice 1 §6, §8.1)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from authority import FULL
from domain_facet_fixtures import over_kwargs, profile_with
from test_local_standing import retracts
from test_local_standing import retracts as counter_of
from test_relocation import MOVE_FIELDS
from test_snapshot_retraction import broken_counter, snapshot_retraction
from test_world_build import ALPHA, BETA
from test_world_receipts import corpora, hold_shipped, publish, world_over
from test_world_view import make_absent, split_evaluation_world, world_kwargs

from beliefs import stored
from beliefs.belief import Belief, NoBelief
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    CorpusDamaged,
    ProducerSnapshotMismatch,
    ProducerSnapshotRetracted,
    RetractionResolutionDisagreement,
    RetractionUnreadable,
)
from beliefs.evaluation import evaluate_over_traced, gather
from beliefs.relocation import move
from beliefs.world.epoch import RetainedSnapshots
from beliefs.world.view import open_world_view


def writer_at(root: Path, profile, *, resolver=None) -> CorpusWriter:
    from nodes.core.write_plan import DefaultExecutor
    from test_corpus_write import OperationRecorder

    writer = CorpusWriter(
        root,
        DefaultExecutor,
        authority=FULL,
        profile=profile,
        operation_port=OperationRecorder(root, authority=FULL, profile=profile),
        snapshot_resolver=resolver,
    )
    from profiles import pins_for

    from beliefs.world import registry

    manifest = registry.load_manifest(root)
    (root / "corpus.yaml").write_bytes(registry.manifest_bytes(replace(manifest, profile=pins_for(profile))))
    return writer


def evaluation(world, published, profile):
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile)  # sets producer_snapshot_identity from the view (Step 2)
    inputs = gather(
        view,
        "proposition:p",
        context=kwargs["context"],
        profile=profile,
        resolution=kwargs["resolution"],
        binding=kwargs["binding"],
    )
    answer, _admission = evaluate_over_traced(view, "proposition:p", **over_kwargs(kwargs))
    return view, inputs, answer


def support_in(view, corpus_id):
    return next(n for n in view.captured_records(corpus_id) if n.id == "assessment:a-1")


class TestTheEpochsEnumerationReachesBelief:
    def test_a_retraction_in_coverage_subtracts_and_the_closure_carries_the_epochs_member(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        _view, before, _answer = evaluation(world, published, profile)
        alpha = writer_at(roots[ALPHA], profile)
        retraction = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        rebuilt = publish(world, (ALPHA, BETA), hold_shipped(world))
        view, after, answer = evaluation(world, rebuilt, profile)
        assert len(after.assessments) == len(before.assessments) - 1
        assert after.retractions == replace(view.retraction_enumeration(), found=((retraction.id, RETRACTION_UPHELD),))
        assert isinstance(answer, Belief) and after.closure().digest() == answer.belief_input_digest

    def test_a_supplied_snapshot_identity_that_is_not_the_epochs_refuses(self, tmp_path):
        world, _roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        context = replace(kwargs["context"], producer_snapshot_identity="producer-snapshot-1")
        with pytest.raises(ProducerSnapshotMismatch):
            gather(
                view,
                "proposition:p",
                context=context,
                profile=profile,
                resolution=kwargs["resolution"],
                binding=kwargs["binding"],
            )


class TestC3Coverage:
    def test_an_uncovered_retraction_moves_nothing_and_the_widening_reaches_it(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        baseline_epoch = publish(world, (ALPHA,), hold_shipped(world))
        _, baseline, _ = evaluation(world, baseline_epoch, profile)
        retraction = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        move(alpha, beta, retraction.id, **MOVE_FIELDS)  # the retraction now lives in BETA; its target stays in ALPHA
        narrow = publish(world, (ALPHA,), hold_shipped(world))
        _view, inputs, _answer = evaluation(world, narrow, profile)
        assert inputs.retractions.found == () and inputs.retractions.coverage == (ALPHA,)
        assert len(inputs.assessments) == 2
        assert inputs.closure().digest() == baseline.closure().digest()
        wide = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, widened, _answer = evaluation(world, wide, profile)
        assert widened.retractions.found == ((retraction.id, RETRACTION_UPHELD),)
        assert len(widened.assessments) == 1

    def test_the_coverage_declaration_is_a_digest_member_in_isolation(self, tmp_path):
        world, _roots, published = split_evaluation_world(tmp_path, beta_refs=())
        _view, inputs, _answer = evaluation(world, published, profile_with())
        narrow = inputs.closure().digest()
        wide = (
            replace(inputs, retractions=replace(inputs.retractions, coverage=(*inputs.retractions.coverage, "9" * 32)))
            .closure()
            .digest()
        )
        assert narrow != wide

    def test_an_in_coverage_move_leaves_the_digest_and_moves_the_receipts(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        target = support_in(open_world_view(world, published), ALPHA)
        alpha.retract(retracts(target, "t1"))
        from dataset_fixtures import dataset_ref

        move(alpha, beta, dataset_ref("d-a"), **MOVE_FIELDS)
        move(alpha, beta, "run:run-a", **MOVE_FIELDS)
        move(alpha, beta, "proposition:p", **MOVE_FIELDS)
        first = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, before, _answer = evaluation(world, first, profile)
        move(alpha, beta, target.id, **MOVE_FIELDS)
        second = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, after, _answer = evaluation(world, second, profile)
        assert after.producer_snapshot_identity == before.producer_snapshot_identity
        assert after.snapshot == before.snapshot and after.consulted == before.consulted
        assert after.closure().digest() == before.closure().digest()
        assert dict(second.coverage) != dict(first.coverage)  # both corpus states moved


class TestAbsence:
    def test_a_found_retraction_in_an_absent_corpus_is_the_absence_answer(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        retraction = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        move(alpha, beta, retraction.id, **MOVE_FIELDS)
        wide = publish(world, (ALPHA, BETA), hold_shipped(world))
        make_absent(roots, BETA)
        _view, inputs, answer = evaluation(world, wide, profile)
        assert inputs.assessments == () and (retraction.id, BETA) in inputs.absent
        assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"


class TestTheSplit:
    def test_a_counter_retraction_moved_away_refuses_the_disagreement(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        first = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        counter = alpha.retract(retracts(first, "t2"))
        together = publish(world, (ALPHA, BETA), hold_shipped(world))
        _view, inputs, _answer = evaluation(world, together, profile)
        from beliefs.corpus import local_retraction_enumeration

        assert dict(inputs.retractions.found)[first.id] == "overturned"
        assert dict(local_retraction_enumeration(alpha.read_view).found) == dict(inputs.retractions.found)
        move(alpha, beta, counter.id, **MOVE_FIELDS)
        split = publish(world, (ALPHA, BETA), hold_shipped(world))
        assert dict(open_world_view(world, split).retraction_enumeration().found)[first.id] == "upheld"
        with pytest.raises(RetractionResolutionDisagreement) as refused:
            evaluation(world, split, profile)
        assert refused.value.ref == first.id


def test_a_retraction_target_in_an_absent_corpus_answers_absence(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    profile = profile_with()
    alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
    target = support_in(open_world_view(world, published), ALPHA)
    alpha.retract(retracts(target, "absent-target"))
    from dataset_fixtures import dataset_ref

    move(alpha, beta, dataset_ref("d-a"), **MOVE_FIELDS)
    move(alpha, beta, "run:run-a", **MOVE_FIELDS)
    move(alpha, beta, "proposition:p", **MOVE_FIELDS)
    move(alpha, beta, target.id, **MOVE_FIELDS)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    make_absent(roots, BETA)
    _, inputs, answer = evaluation(world, published, profile)
    assert inputs.assessments == () and (target.id, BETA) in inputs.absent
    assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"


@pytest.mark.parametrize("mode", ["retired", "surviving", "conflict", "unresolved"])
def test_lineage_absence_uses_the_effective_world_walk(tmp_path, mode):
    from authority import ACTOR
    from dataset_fixtures import pinned
    from domain_facet_fixtures import seed

    view = seed(tmp_path / "seed")
    nodes = list(view.iter_stored())
    lost = stored.dataset_node(title="lost-ancestor", resources=pinned("lost-ancestor"))
    safe = stored.dataset_node(title="safe-ancestor", resources=pinned("safe-ancestor"))
    middle = stored.dataset_node(
        title="middle",
        resources=pinned("middle"),
        basis={
            "tag": "single",
            "routes": [
                {"identity": "route:middle", "run": "run:ancestor", "ancestor": lost.id, "transforms": [lost.id]},
            ],
        },
    )
    routes = [
        {
            "identity": "route:bad",
            "run": "run:unknown" if mode == "unresolved" else "run:ancestor",
            "ancestor": middle.id,
            "transforms": [middle.id],
        },
        {"identity": "route:safe", "run": "run:ancestor", "ancestor": safe.id, "transforms": [safe.id]},
    ]
    replacement = stored.dataset_node(
        title="d-a",
        resources=pinned("d-a"),
        domain_facets={"biology/gene-axis": {"axis": "rows"}},
        basis={
            "tag": "single" if mode == "unresolved" else "conflict",
            "routes": routes[:1] if mode == "unresolved" else routes,
        },
    )
    nodes = [replacement if node.id == replacement.id else node for node in nodes]
    nodes.extend([safe, middle, stored.run_node("ancestor", title="ancestor", spec="s")])
    roots = corpora(tmp_path, {ALPHA: tuple(nodes), BETA: (lost,)})
    world = world_over(tmp_path, roots)
    profile = profile_with()
    alpha = writer_at(roots[ALPHA], profile)
    writer_at(roots[BETA], profile)
    if mode in ("retired", "surviving"):
        target = alpha.read_view.get(replacement.id)
        identity = stored.stored_semantic_hash(target)
        assert identity is not None
        alpha.retract(
            stored.retraction_node(
                title="route",
                target=stored.RouteTarget(
                    target.id, target.id, identity, "route:bad" if mode == "retired" else "route:safe"
                ),
                reason="wrong-route",
                rationale="wrong ancestry",
                grounds=("verification:v-1",),
                actor=ACTOR,
                event_token=mode,
            )
        )
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    make_absent(roots, BETA)
    view, inputs, answer = evaluation(world, published, profile)
    assert inputs.snapshot.not_present[lost.id] == BETA
    # correction-remainder slice 2 decision 7: BETA is in the producer snapshot's own
    # coverage, so its absence answers absence for every mode here, before lineage's
    # own per-mode walk ever runs — not only for the "surviving" walk that names it.
    assert (f"producer-snapshot:{view.producer_snapshot_identity()}", BETA) in inputs.absent
    assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"


def test_a_found_retraction_in_a_damaged_carrier_is_unreadable(tmp_path):
    from test_world_view import damage

    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    profile = profile_with()
    alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
    retraction = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "damaged-carrier"))
    move(alpha, beta, retraction.id, **MOVE_FIELDS)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    kwargs = world_kwargs(open_world_view(world, published), profile)
    damage(roots[BETA], "parse-error")
    view = open_world_view(world, published, on_damage="report")
    # correction-remainder slice 2 decision 7: a damaged covered corpus refuses the whole
    # world read before the standing loop is reached, whether or not it holds the
    # retraction the query would otherwise find — so this refuses as `CorpusDamaged`
    # directly rather than as a `RetractionUnreadable` wrapping one.
    with pytest.raises(CorpusDamaged) as refused:
        gather(view, "proposition:p", **{k: kwargs[k] for k in ("context", "profile", "resolution", "binding")})
    assert refused.value.ref == f"producer-snapshot:{view.producer_snapshot_identity()}"
    assert refused.value.corpus_id == BETA


def _retract_snapshot(world, roots, published, profile, *, corpus=ALPHA):
    identity = published.receipts["producer-receipt.yaml"].subject_identity
    writer = writer_at(roots[corpus], profile, resolver=RetainedSnapshots(world))
    return identity, writer, writer.retract(snapshot_retraction(identity))


class TestTheSnapshotTarget:
    def test_a_retracted_bound_snapshot_refuses(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _identity, _w, _r = _retract_snapshot(world, roots, published, profile)
        with pytest.raises(ProducerSnapshotRetracted):
            evaluation(world, published, profile)

    def test_a_counter_retraction_restores_and_the_history_is_in_the_digest(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _view, baseline, _answer = evaluation(world, published, profile)
        _identity, writer, r = _retract_snapshot(world, roots, published, profile)
        c = writer.retract(counter_of(r, "counter"))
        _view, inputs, _answer = evaluation(world, published, profile)
        assert (r.id, RETRACTION_OVERTURNED) in inputs.retractions.found and (c.id, RETRACTION_UPHELD) in inputs.retractions.found
        assert ("retraction", r.id) in inputs.read_trace and ("retraction", c.id) in inputs.read_trace
        assert inputs.closure().digest() != baseline.closure().digest()
        assert len({ref for ref, _ in inputs.retractions.found}) == len(inputs.retractions.found)

    def test_an_absent_covered_corpus_answers_absence_for_the_snapshot(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        inputs = gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                        resolution=kwargs["resolution"], binding=kwargs["binding"])
        identity = view.producer_snapshot_identity()
        assert (f"producer-snapshot:{identity}", BETA) in inputs.absent

    def test_a_damaged_covered_corpus_refuses_whatever_it_holds(self, tmp_path):
        # beta_refs=(): BETA holds none of the lineage walk's own refs, so
        # `world_kwargs` (which locates d-a/d-b before gather ever runs) does not
        # itself trip `_refuse_damaged`; the refusal this test pins is `gather`'s
        # own world-block check over every covered corpus, holdings aside.
        from test_world_view import damage
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        damage(roots[BETA], "parse-error")
        view = open_world_view(world, published, on_damage="report")
        kwargs = world_kwargs(view, profile)
        with pytest.raises(CorpusDamaged) as caught:
            gather(view, "proposition:p", context=kwargs["context"], profile=profile,
                   resolution=kwargs["resolution"], binding=kwargs["binding"])
        assert caught.value.ref == f"producer-snapshot:{view.producer_snapshot_identity()}" and caught.value.corpus_id == BETA

    def test_a_rebuild_after_retraction_keeps_the_identity_and_still_refuses(self, tmp_path):
        from test_world_receipts import hold_shipped, publish
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        identity, writer, r = _retract_snapshot(world, roots, published, profile)
        rebuilt = publish(world, (ALPHA, BETA), hold_shipped(world))
        assert rebuilt.receipts["producer-receipt.yaml"].subject_identity == identity
        with pytest.raises(ProducerSnapshotRetracted):
            evaluation(world, rebuilt, profile)
        writer.retract(counter_of(r, "counter"))
        rebuilt2 = publish(world, (ALPHA, BETA), hold_shipped(world))
        _v, over_rebuilt, _a = evaluation(world, rebuilt2, profile)
        _v, over_old, _a = evaluation(world, published, profile)
        assert over_rebuilt.retractions.found == over_old.retractions.found

    def test_an_older_snapshots_retraction_is_out_of_the_closure(self, tmp_path):
        from test_world_receipts import hold_shipped, publish
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _v, baseline, _a = evaluation(world, published, profile)
        narrow = publish(world, (ALPHA,), hold_shipped(world))          # a different identity
        old_identity = narrow.receipts["producer-receipt.yaml"].subject_identity
        assert old_identity is not None
        writer = writer_at(roots[ALPHA], profile, resolver=RetainedSnapshots(world))
        writer.retract(snapshot_retraction(old_identity))
        later = publish(world, (ALPHA, BETA), hold_shipped(world))       # captures that retraction
        _v, inputs, _a = evaluation(world, later, profile)
        assert inputs.retractions.found == baseline.retractions.found

    def test_a_broken_counter_retraction_refuses_the_read(self, tmp_path):
        from fixtures_cut4 import raw_write
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _identity, _writer, r = _retract_snapshot(world, roots, published, profile)
        broken = broken_counter(r)
        raw_write(roots[ALPHA], broken)
        with pytest.raises(RetractionUnreadable) as caught:
            evaluation(world, published, profile)
        assert caught.value.ref == broken.id
