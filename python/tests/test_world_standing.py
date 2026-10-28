"""Standing over a world read: the epoch's enumeration, its scope, coverage,
relocation, absence and the split (correction-remainder slice 1 §6, §8.1)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from authority import ACTOR, FULL
from domain_facet_fixtures import over_kwargs, profile_with
from fixtures_cut4 import raw_write
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
    """Slice 1 §11.1's split: a counter-retraction `move`d apart from the retraction
    it counters. From cut 48 §4.5 the shipped (v2-bound) enumeration folds once over
    the whole capture and the world reads it; the v1 binding keeps refusing."""

    def _split(self, tmp_path, retraction):
        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
        first = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
        counter = alpha.retract(retracts(first, "t2"))
        bind = {} if retraction is None else {"retraction": retraction}
        together = publish(world, (ALPHA, BETA), hold_shipped(world, **bind))
        _view, inputs, _answer = evaluation(world, together, profile)
        from beliefs.corpus import local_retraction_enumeration

        assert dict(inputs.retractions.found)[first.id] == "overturned"
        assert dict(local_retraction_enumeration(alpha.read_view).found) == dict(inputs.retractions.found)
        move(alpha, beta, counter.id, **MOVE_FIELDS)
        split = publish(world, (ALPHA, BETA), hold_shipped(world, **bind))
        return world, split, profile, first, counter

    def test_a_counter_retraction_moved_away_is_folded_once(self, tmp_path):
        world, split, profile, first, counter = self._split(tmp_path, None)  # the shipped default binding
        found = dict(open_world_view(world, split).retraction_enumeration().found)
        assert found == {first.id: "overturned", counter.id: "upheld"}
        _view, inputs, _answer = evaluation(world, split, profile)
        assert dict(inputs.retractions.found) == found

    def test_a_v1_bound_epoch_still_refuses_the_disagreement(self, tmp_path):
        world, split, profile, first, _counter = self._split(tmp_path, "v1")
        assert dict(open_world_view(world, split).retraction_enumeration().found)[first.id] == "upheld"
        with pytest.raises(RetractionResolutionDisagreement) as refused:
            evaluation(world, split, profile)
        assert refused.value.ref == first.id


def _overlap(tmp_path, *, counter_in=ALPHA, deeper=False):
    """R retracting ALPHA's `assessment:a-1`, C countering R, held as cut 48 §4.5's
    1b case: R in both corpora; C in `counter_in` (and, with `deeper`, D countering
    C in ALPHA and C in both)."""
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    profile = profile_with()
    alpha, beta = writer_at(roots[ALPHA], profile), writer_at(roots[BETA], profile)
    first = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
    counter = alpha.retract(retracts(first, "t2"))
    raw_write(roots[BETA], first)
    if deeper:
        alpha.retract(retracts(counter, "t3"))
        raw_write(roots[BETA], counter)
    elif counter_in == BETA:
        move(alpha, beta, counter.id, **MOVE_FIELDS)
    return world, roots, profile, first, counter


def test_g14_i_v2_fold_world(tmp_path):
    """Cut 48 §4.5: the v2-bound build folds standing once over the merged holders."""
    from dataset_fixtures import pinned
    from fixtures_cut4 import raw_write as raw

    from beliefs.errors import AddressMapConflict, RuleNonconformant
    from beliefs.world.read import validate_receipt

    receipts = []
    for counter_in in (ALPHA, BETA):
        world, _roots, profile, first, counter = _overlap(tmp_path / counter_in[:1], counter_in=counter_in)
        published = publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v2"))
        view = open_world_view(world, published)
        assert view.holders_of(first.id) == (ALPHA, BETA) and view.holders_of(counter.id) == (counter_in,)
        assert sorted(view.retraction_enumeration().found) == sorted(
            [(first.id, RETRACTION_OVERTURNED), (counter.id, RETRACTION_UPHELD)]
        )
        receipts.append(published.receipts["retraction-receipt.yaml"])
        assert validate_receipt(world, published, "retraction-enumeration").outcome == "validated"
        _view, inputs, _answer = evaluation(world, published, profile)
        assert dict(inputs.retractions.found) == dict(view.retraction_enumeration().found)
        legacy = publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v1"))
        v1_found = open_world_view(world, legacy).retraction_enumeration().found
        assert sorted(pair for pair in v1_found if pair[0] == first.id) == [
            (first.id, RETRACTION_OVERTURNED),
            (first.id, RETRACTION_UPHELD),
        ]
    assert receipts[0].subject_identity == receipts[1].subject_identity
    assert receipts[0].rule_identity == receipts[1].rule_identity
    # R,C,D / R,C: the deeper chain upholds R through the merged fold.
    world, roots, profile, first, counter = _overlap(tmp_path / "deeper", deeper=True)
    published = publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v2"))
    found = dict(open_world_view(world, published).retraction_enumeration().found)
    assert found[first.id] == RETRACTION_UPHELD and found[counter.id] == RETRACTION_OVERTURNED
    assert len(found) == 3 and list(found.values()).count(RETRACTION_UPHELD) == 2
    # The colliding route: a route identity equal to R's address, retracted by route, adds no edge in gather.
    from dataset_fixtures import dataset_ref

    from beliefs.corpus import lineage_snapshot
    from beliefs.lineage import effective_routes

    alpha = writer_at(roots[ALPHA], profile)
    target = alpha.read_view.get(dataset_ref("d-a")).model_copy(deep=True)
    target.facets[stored.LINEAGE_BASIS_FACET] = {
        "tag": "single",
        "routes": [
            {
                "identity": first.id,
                "run": "run:run-b",
                "ancestor": dataset_ref("d-b"),
                "transforms": [dataset_ref("d-b")],
            }
        ],
    }
    target = stored.stamp_semantic_identity(target)
    raw(roots[ALPHA], target)
    target_hash = stored.stored_semantic_hash(target)
    assert target_hash is not None
    colliding = stored.retraction_node(
        title="route",
        target=stored.RouteTarget(target.id, target.id, target_hash, first.id),
        reason="wrong-route",
        rationale="fixture",
        grounds=("verification:v-1",),
        actor=ACTOR,
        event_token="colliding-route",
    )
    raw(roots[ALPHA], colliding)
    published = publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v2"))
    view = open_world_view(world, published)
    found = dict(view.retraction_enumeration().found)
    assert found[first.id] == RETRACTION_UPHELD and found[colliding.id] == RETRACTION_UPHELD
    kwargs = world_kwargs(view, profile)
    inputs = gather(
        view,
        "proposition:p",
        context=replace(kwargs["context"], snapshot=lineage_snapshot(view, (target.id,))),
        profile=profile,
        resolution=kwargs["resolution"],
        binding=kwargs["binding"],
    )
    assert dict(inputs.retractions.found) == found
    assert effective_routes(inputs.snapshot, target.id) == ()
    # A raw-written counter cycle across holders refuses through the kernel's wrap.
    x = stored.retraction_node(
        title="x",
        target=stored.NodeTarget("retraction:z", "retraction:z", "0" * 64),
        reason="defective-code",
        rationale="fixture",
        grounds=("verification:v-1",),
        actor=ACTOR,
        event_token="x",
    )
    raw(roots[ALPHA], x)
    raw(roots[BETA], retracts(x, "y").model_copy(update={"deprecated_ids": ["retraction:z"]}))
    with pytest.raises(RuleNonconformant):
        publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v2"))
    # One address under two distinct uids refuses at the address map, before any rule runs.
    one = stored.dataset_node(title="twice", resources=pinned("twice"))
    two = stored.dataset_node(title="twice", resources=pinned("twice"))
    assert one.id == two.id and one.uid != two.uid
    roots = corpora(tmp_path / "distinct", {ALPHA: (one,), BETA: (two,)})
    world = world_over(tmp_path / "distinct", roots)
    with pytest.raises(AddressMapConflict) as caught:
        publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v2"))
    assert caught.value.finding.code == "duplicate-location"


def test_v1_and_v2_bound_epochs_agree_without_a_split(tmp_path):
    """Cut 48 §4.5: the semantic change travels in the receipt's rule identity alone."""
    from test_world_receipts import document

    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    profile = profile_with()
    alpha = writer_at(roots[ALPHA], profile)
    first = alpha.retract(retracts(support_in(open_world_view(world, published), ALPHA), "t1"))
    alpha.retract(retracts(first, "t2"))
    v1 = publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v1"))
    v2 = publish(world, (ALPHA, BETA), hold_shipped(world, retraction="v2"))
    one, other = v1.receipts["retraction-receipt.yaml"], v2.receipts["retraction-receipt.yaml"]
    assert one.rule_identity != other.rule_identity and one.subject_identity == other.subject_identity
    assert (
        document(v1, "retraction-receipt.yaml")["enumeration"] == document(v2, "retraction-receipt.yaml")["enumeration"]
    )
    _view, v1_inputs, _answer = evaluation(world, v1, profile)
    _view, v2_inputs, _answer = evaluation(world, v2, profile)
    assert v1_inputs.closure().digest() == v2_inputs.closure().digest()


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
def test_an_absent_covered_corpus_answers_absence_regardless_of_lineage_mode(tmp_path, mode):
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


def test_a_found_retraction_in_a_damaged_carrier_refuses_as_corpus_damaged(tmp_path):
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
        assert (r.id, RETRACTION_OVERTURNED) in inputs.retractions.found and (
            c.id,
            RETRACTION_UPHELD,
        ) in inputs.retractions.found
        assert ("retraction", r.id) in inputs.read_trace and ("retraction", c.id) in inputs.read_trace
        assert inputs.closure().digest() != baseline.closure().digest()
        assert len({ref for ref, _ in inputs.retractions.found}) == len(inputs.retractions.found)

    def test_an_absent_covered_corpus_answers_absence_for_the_snapshot(self, tmp_path):
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        make_absent(roots, BETA)
        view = open_world_view(world, published)
        kwargs = world_kwargs(view, profile)
        inputs = gather(
            view,
            "proposition:p",
            context=kwargs["context"],
            profile=profile,
            resolution=kwargs["resolution"],
            binding=kwargs["binding"],
        )
        identity = view.producer_snapshot_identity()
        assert (f"producer-snapshot:{identity}", BETA) in inputs.absent

    def test_absence_takes_precedence_over_a_retracted_bound_snapshot(self, tmp_path):
        """`if not absent and bound in snapshot_standing.retracted` (evaluation.py):
        an absent covered corpus makes the snapshot's standing itself unreadable
        (decision 7), so the read answers absence rather than `ProducerSnapshotRetracted`
        even though the snapshot is, in fact, retracted in the corpus that is present."""
        world, roots, published = split_evaluation_world(tmp_path)
        profile = profile_with()
        _identity, _w, _r = _retract_snapshot(world, roots, published, profile)
        make_absent(roots, BETA)
        view, inputs, answer = evaluation(world, published, profile)
        identity = view.producer_snapshot_identity()
        assert (f"producer-snapshot:{identity}", BETA) in inputs.absent
        assert isinstance(answer, NoBelief) and answer.reason == "unavailable-corpus-absent"

    @pytest.mark.parametrize("retraction_in", [None, BETA])
    def test_a_damaged_covered_corpus_refuses_whatever_it_holds(self, tmp_path, retraction_in):
        # beta_refs=(): BETA holds none of the lineage walk's own refs, so
        # `world_kwargs` (which locates d-a/d-b before gather ever runs) does not
        # itself trip `_refuse_damaged`; the refusal this test pins is `gather`'s
        # own world-block check over every covered corpus, holdings aside — including
        # when what BETA holds is the snapshot's own retraction (decision 7: damage
        # refuses before the retraction that might resolve it is ever read).
        from test_world_view import damage

        world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        if retraction_in is not None:
            _retract_snapshot(world, roots, published, profile, corpus=retraction_in)
        damage(roots[BETA], "parse-error")
        view = open_world_view(world, published, on_damage="report")
        kwargs = world_kwargs(view, profile)
        with pytest.raises(CorpusDamaged) as caught:
            gather(
                view,
                "proposition:p",
                context=kwargs["context"],
                profile=profile,
                resolution=kwargs["resolution"],
                binding=kwargs["binding"],
            )
        assert (
            caught.value.ref == f"producer-snapshot:{view.producer_snapshot_identity()}"
            and caught.value.corpus_id == BETA
        )

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
        narrow = publish(world, (ALPHA,), hold_shipped(world))  # a different identity
        old_identity = narrow.receipts["producer-receipt.yaml"].subject_identity
        assert old_identity is not None
        writer = writer_at(roots[ALPHA], profile, resolver=RetainedSnapshots(world))
        writer.retract(snapshot_retraction(old_identity))
        later = publish(world, (ALPHA, BETA), hold_shipped(world))  # captures that retraction
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

    def test_a_retraction_outside_coverage_cannot_be_authored_and_a_raw_write_there_leaves_the_read_unchanged(
        self, tmp_path
    ):
        """Decision 3: a snapshot-arm retraction resolves at authoring only in a
        corpus the target snapshot's own coverage names; a writer over BETA refuses
        one naming a producer snapshot covering only ALPHA. A raw write around that
        refusal lands in a corpus decision 1's live fold never visits for this
        snapshot (BETA is outside `narrow`'s own coverage), so the read is unchanged."""
        from fixtures_cut4 import raw_write
        from test_world_receipts import hold_shipped, publish

        from beliefs.errors import RetractionTargetUnresolvable

        # beta_refs=(): d-a/d-b stay in ALPHA, so a `narrow` epoch covering only ALPHA
        # can still resolve `world_kwargs`'s own lineage walk; with the default split
        # (d-a in BETA) `narrow` would not even publish d-a's address, and the setup
        # would refuse with `RefError` before the coverage question is ever reached.
        world, roots, _published = split_evaluation_world(tmp_path, beta_refs=())
        profile = profile_with()
        narrow = publish(world, (ALPHA,), hold_shipped(world))
        narrow_identity = narrow.receipts["producer-receipt.yaml"].subject_identity
        assert narrow_identity is not None
        _v, baseline, _a = evaluation(world, narrow, profile)
        writer = writer_at(roots[BETA], profile, resolver=RetainedSnapshots(world))
        with pytest.raises(RetractionTargetUnresolvable, match="outside the coverage"):
            writer.retract(snapshot_retraction(narrow_identity))
        raw_write(roots[BETA], snapshot_retraction(narrow_identity))
        _v, inputs, _a = evaluation(world, narrow, profile)
        assert inputs.retractions.found == baseline.retractions.found
        assert inputs.closure().digest() == baseline.closure().digest()
