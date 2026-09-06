"""The controlled, additive retraction write path."""

from __future__ import annotations

from typing import ClassVar

import pytest
from authority import ACTOR, FULL, narrowed
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, DefaultExecutor
from profiles import BASE

from beliefs import errors, stored
from beliefs.corpus import ELIGIBLE_RETRACTION_TARGET_KINDS, CorpusWriter

PINNED = [{"name": "matrix", "digest": "sha256:" + "ab" * 32}]


class Recorder:
    plans: ClassVar[list[list]] = []

    def __init__(self, root):
        self._inner = DefaultExecutor(root)

    def execute(self, plan) -> None:
        Recorder.plans.append(list(plan))
        self._inner.execute(plan)


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    Recorder.plans = []
    return CorpusWriter(tmp_path, Recorder, authority=FULL, profile=BASE)


def content_identity(node: Node) -> str:
    digest = stored.stored_semantic_hash(node)
    assert digest is not None
    return digest


def mint_eligible_assessment(writer: CorpusWriter) -> Node:
    dataset = writer.add(
        stored.dataset_node(
            "raw", title="raw", resources=PINNED, empirical_observation={"locator": "instrument:fixture", "attested_by": writer.authority.actor}
        )
    )
    run = writer.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[dataset.id]))
    proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    return writer.add(
        stored.assessment_node(
            "a1",
            title="a1",
            spec="analysis-spec:s1",
            run=run.id,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule="rule:threshold",
        )
    )


def retraction_for(target: Node, *, reason: str = "defective-code") -> Node:
    return stored.retraction_node(
        title="retraction",
        target=stored.NodeTarget(target.id, target.id, content_identity(target)),
        reason=reason,
        rationale="the recorded result is invalid",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )


def test_e3_a_retraction_naming_another_actor_is_refused(tmp_path):
    writer = CorpusWriter(
        tmp_path,
        Recorder,
        authority=narrowed(kinds=("assessment", "dataset", "proposition", "retraction", "run"),
                           families=("corpus-write",), actor="not-tester"),
        profile=BASE,
    )
    target = mint_eligible_assessment(writer)
    with pytest.raises(errors.ActorMismatch):
        writer.retract(retraction_for(target))


def test_e3_a_retraction_under_its_own_actor_mints(tmp_path):
    writer = CorpusWriter(
        tmp_path,
        Recorder,
        authority=narrowed(kinds=("assessment", "dataset", "proposition", "retraction", "run"),
                           families=("corpus-write",)),
        profile=BASE,
    )
    target = mint_eligible_assessment(writer)
    assert writer.retract(retraction_for(target)).kind == "retraction"


def without_grounds(record: Node) -> Node:
    facet = dict(record.facets[stored.RETRACTION_FACET])
    facet["grounds"] = []
    record.facets[stored.RETRACTION_FACET] = facet
    record.relations = [relation for relation in record.relations if relation.predicate != stored.GROUNDED_IN]
    return stored.stamp_semantic_identity(record)


def malformed_grounds(record: Node, grounds) -> Node:
    facet = dict(record.facets[stored.RETRACTION_FACET])
    if grounds is None:
        del facet["grounds"]
    else:
        facet["grounds"] = grounds
    record.facets[stored.RETRACTION_FACET] = facet
    record.relations = [relation for relation in record.relations if relation.predicate != stored.GROUNDED_IN]
    return stored.stamp_semantic_identity(record)


def test_retract_is_create_only_and_target_untouched(writer):
    target = mint_eligible_assessment(writer)
    before = writer.read_view.get(target.id).model_dump(mode="json")

    admitted = writer.retract(retraction_for(target))

    assert len(Recorder.plans[-1]) == 1
    assert all(isinstance(op, CreateOp) for op in Recorder.plans[-1])
    assert writer.read_view.get(admitted.id) == admitted
    assert writer.read_view.get(target.id).model_dump(mode="json") == before


def test_counter_retraction_targets_a_retraction_as_a_new_chain_link(writer):
    target = mint_eligible_assessment(writer)
    first = writer.retract(retraction_for(target))

    counter = writer.retract(retraction_for(first, reason="upstream-retraction"))

    assert counter.relations[0].target == first.id
    assert writer.read_view.holds(target.id)
    assert writer.read_view.holds(first.id)


def test_retract_uses_relocation_missing_for_an_absent_node_target(writer):
    absent = stored.retraction_node(
        title="absent",
        target=stored.NodeTarget("assessment:absent", "assessment:absent", "sha256:" + "cd" * 32),
        reason="defective-code",
        rationale="missing",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )

    with pytest.raises(errors.RelocationTargetMissing):
        writer.retract(absent)


def test_retract_refuses_a_node_target_with_the_wrong_content_identity(writer):
    target = mint_eligible_assessment(writer)
    record = stored.retraction_node(
        title="wrong identity",
        target=stored.NodeTarget(target.id, target.id, "sha256:" + "ff" * 32),
        reason="defective-code",
        rationale="wrong tuple",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )

    with pytest.raises(errors.RetractionTargetUnresolvable):
        writer.retract(record)

    assert not writer.read_view.holds(record.id)


def test_retract_refuses_an_ineligible_kind_before_resolution(writer):
    proposition = stored.proposition_node("absent", title="absent", claim={"operator": "affects"})

    with pytest.raises(errors.RetractionTargetIneligible):
        writer.retract(retraction_for(proposition))


def test_retract_accepts_an_exact_route_identity(writer):
    dataset = writer.add(
        stored.dataset_node(
            "derived",
            title="derived",
            resources=PINNED,
            basis={
                "tag": "single",
                "routes": [
                    {
                        "identity": "route:one",
                        "run": "run:r1",
                        "ancestor": "dataset:raw",
                        "transforms": ["dataset:raw"],
                    }
                ],
            },
        )
    )
    record = stored.retraction_node(
        title="route retraction",
        target=stored.RouteTarget(dataset.id, dataset.id, content_identity(dataset), "route:one"),
        reason="wrong-route",
        rationale="the selected route was wrong",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )

    assert writer.retract(record).id == record.id


def test_retract_refuses_a_route_absent_from_the_stamped_basis(writer):
    dataset = writer.add(
        stored.dataset_node(
            "derived",
            title="derived",
            resources=PINNED,
            basis={"tag": "single", "routes": [{"identity": "route:one"}]},
        )
    )
    record = stored.retraction_node(
        title="route retraction",
        target=stored.RouteTarget(dataset.id, dataset.id, content_identity(dataset), "route:other"),
        reason="wrong-route",
        rationale="the selected route was wrong",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )

    with pytest.raises(errors.RetractionTargetUnresolvable):
        writer.retract(record)


def test_retract_refuses_a_route_dataset_with_the_wrong_content_identity(writer):
    dataset = writer.add(
        stored.dataset_node(
            "derived",
            title="derived",
            resources=PINNED,
            basis={"tag": "single", "routes": [{"identity": "route:one"}]},
        )
    )
    record = stored.retraction_node(
        title="route retraction",
        target=stored.RouteTarget(dataset.id, dataset.id, "sha256:" + "ff" * 32, "route:one"),
        reason="wrong-route",
        rationale="the dataset identity is wrong",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )

    with pytest.raises(errors.RetractionTargetUnresolvable):
        writer.retract(record)

    assert not writer.read_view.holds(record.id)


def test_malformed_grounds_refuse_before_target_resolution(writer):
    absent = stored.retraction_node(
        title="absent",
        target=stored.NodeTarget("assessment:absent", "assessment:absent", "sha256:" + "cd" * 32),
        reason="defective-code",
        rationale="missing",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )

    with pytest.raises(errors.RetractionGroundsMissing):
        writer.retract(without_grounds(absent))


def test_retract_refuses_missing_grounds_with_the_public_subtype(writer):
    target = mint_eligible_assessment(writer)

    for grounds in (None, [], [""], ["", ""]):
        with pytest.raises(errors.RetractionGroundsMissing):
            writer.retract(malformed_grounds(retraction_for(target), grounds))


def test_retract_keeps_malformed_ground_lists_in_validation_refused(writer):
    target = mint_eligible_assessment(writer)

    for grounds in ([1], ["verification:v1", 1], ["", "verification:v1"]):
        with pytest.raises(errors.ValidationRefused):
            writer.retract(malformed_grounds(retraction_for(target), grounds))


def test_retract_refuses_a_stale_stamp_at_the_boundary(writer):
    target = mint_eligible_assessment(writer)
    record = retraction_for(target)
    record.facets[stored.RETRACTION_FACET]["rationale"] = "changed without restamping"

    with pytest.raises(errors.ValidationRefused):
        writer.retract(record)


def test_retract_translates_malformed_raw_shapes_to_validation_refused(writer):
    target = mint_eligible_assessment(writer)
    record = retraction_for(target)
    record.facets[stored.RETRACTION_FACET]["target"] = {"arm": "node"}
    stored.stamp_semantic_identity(record)

    with pytest.raises(errors.ValidationRefused):
        writer.retract(record)


def test_retract_errors_are_write_refusals():
    for refusal in (
        errors.RetractionTargetIneligible,
        errors.RetractionTargetUnresolvable,
        errors.RetractionGroundsMissing,
    ):
        assert issubclass(refusal, errors.WriteRefused)


def test_retraction_target_kind_tuple_is_exact():
    assert ELIGIBLE_RETRACTION_TARGET_KINDS == ("assessment", "retraction", "verification")


def test_retract_accepts_a_verification_target(writer):
    verification = writer.add(
        stored.verification_node(
            "v1",
            title="v1",
            assessment="assessment-identity",
            assessment_ref="assessment:a1",
            scope="clean-environment",
            verdict="passed",
        )
    )

    assert writer.retract(retraction_for(verification)).relations[0].target == verification.id
