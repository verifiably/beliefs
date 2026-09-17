"""Standing over a world read: the epoch's enumeration, its scope, coverage,
relocation, absence and the split (correction-remainder slice 1 §6, §8.1)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from authority import FULL
from domain_facet_fixtures import over_kwargs, profile_with
from test_local_standing import retracts
from test_relocation import MOVE_FIELDS
from test_world_build import ALPHA, BETA
from test_world_receipts import corpora, hold_shipped, publish, world_over
from test_world_view import make_absent, split_evaluation_world, world_kwargs

from beliefs import stored
from beliefs.belief import Belief, NoBelief
from beliefs.closure import RETRACTION_UPHELD
from beliefs.corpus import CorpusWriter
from beliefs.errors import ProducerSnapshotMismatch, RetractionResolutionDisagreement
from beliefs.evaluation import evaluate_over_traced, gather
from beliefs.relocation import move
from beliefs.world.view import open_world_view


def writer_at(root: Path, profile) -> CorpusWriter:
    from nodes.core.write_plan import DefaultExecutor
    from test_corpus_write import OperationRecorder

    writer = CorpusWriter(
        root,
        DefaultExecutor,
        authority=FULL,
        profile=profile,
        operation_port=OperationRecorder(root, authority=FULL, profile=profile),
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
    from dataset_fixtures import dataset_ref, pinned
    from domain_facet_fixtures import seed

    from beliefs.lineage import certify

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
    _, inputs, answer = evaluation(world, published, profile)
    assert inputs.snapshot.not_present[lost.id] == BETA
    certification = certify(inputs.snapshot, (dataset_ref("d-a"),), (dataset_ref("d-b"),))
    if mode == "surviving":
        assert (lost.id, BETA) in inputs.absent
        assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"
    else:
        assert inputs.absent == () and isinstance(answer, Belief)
        assert inputs.closure().digest() == answer.belief_input_digest
        if mode == "retired":
            assert inputs.snapshot.retired[replacement.id] == ("route:bad",)
            assert certification.state == "independent" and answer.value == 2
        else:
            assert certification.state == "not-certified"
            assert certification.findings == (("lineage-divergent",) if mode == "conflict" else ("lineage-incomplete",))
