"""Cut 45 over registered roots and the composition root's durable writers."""

from dataclasses import replace
from uuid import uuid4

import pytest
from authority import ACTOR
from dataset_fixtures import dataset_ref, pinned
from domain_facet_fixtures import over_kwargs
from fixtures_cut4 import raw_write
from nodes.core.relations import Relation
from test_local_standing import retracts
from test_snapshot_retraction import broken_counter, snapshot_retraction
from test_snapshot_retraction_acceptance import _writer
from test_world_receipts import document, hold_shipped, publish, repackage
from test_world_view import make_absent
from test_world_view_acceptance import durable_world as durable_world  # noqa: PLC0414
from test_world_view_acceptance import evaluation_world, world_kwargs

from beliefs import evaluation, stored
from beliefs.belief import AcceptanceContext, AcceptancePolicy, Belief, NoBelief, NotReached, Reached, Refused
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD
from beliefs.corpus import lineage_snapshot
from beliefs.errors import (
    ContractDisagreement,
    FacetUndeclared,
    ProducerSnapshotRetracted,
    RetractionResolutionDisagreement,
    RetractionUnreadable,
)
from beliefs.evaluation import evaluate_over_traced, gather
from beliefs.lineage import effective_routes
from beliefs.world import derive
from beliefs.world.view import open_world_view


@pytest.fixture()
def case(durable_world):
    return evaluation_world(durable_world, beta_refs=())


def policy(*excluded, statement="durable policy"):
    return AcceptancePolicy(lambda _c, r: r not in excluded, statement)


def inputs(case, acceptance):
    world, _roots, epoch, a, b, profile = case
    view = open_world_view(world, epoch)
    kwargs = world_kwargs(view, profile, a, b)
    return gather(view, "proposition:p", **{key: kwargs[key] for key in ("context", "profile", "resolution", "binding")}, acceptance=acceptance)


def answer(case, acceptance):
    world, _roots, epoch, a, b, profile = case
    view = open_world_view(world, epoch)
    return evaluate_over_traced(view, "proposition:p", **over_kwargs(world_kwargs(view, profile, a, b)), acceptance=acceptance)


def published(case):
    world, roots, _epoch, a, b, profile = case
    return world, roots, publish(world, (a, b), hold_shipped(world)), a, b, profile


def twin(writer, *, outcome="supported"):
    node = writer.read_view.get("assessment:a-1").model_copy(deep=True)
    node.id, node.uid = "assessment:twin", uuid4().hex
    node.facets[stored.ASSESSMENT_FACET]["outcome"] = outcome
    node.relations = [Relation(source=node.id, predicate=r.predicate, target=r.target) for r in node.relations]
    return writer.add(stored.stamp_semantic_identity(node))


def test_assessment_twins(case):
    world, roots, _epoch, a, _b, profile = case
    writer = _writer(roots[a], profile, world)
    rejected = twin(writer, outcome="refuted")
    case = published(case)
    kept, _ = answer(case, policy(rejected.id))
    refused, _ = answer(case, policy())
    assert isinstance(kept, Belief)
    assert isinstance(refused, Refused) and "disagree" in refused.reason
    assert kept.acceptance == AcceptanceContext("durable policy", ((a, rejected.id),), True)


def test_verification_twin_edges(case):
    world, roots, _epoch, a, _b, profile = case
    writer = _writer(roots[a], profile, world)
    rejected = twin(writer)
    identity = stored.assessment_value(rejected, profile=profile).identity()
    failure = writer.add(stored.verification_node("failure", title="failure", assessment=identity,
        assessment_ref=rejected.id, scope="clean-environment", verdict="failed"))
    case = published(case)
    _result, admission = answer(case, policy(rejected.id))
    assert isinstance(admission, Reached) and identity not in admission.admitted
    passed = writer.add(stored.verification_node("pass-twin", title="pass", assessment=identity,
        assessment_ref=rejected.id, scope="clean-environment", verdict="passed"))
    case = published(case)
    _result, admission = answer(case, policy(rejected.id, failure.id, "verification:v-1"))
    assert isinstance(admission, Reached) and identity in admission.admitted
    assert passed.id in {v.ref for v in inputs(case, policy(rejected.id, failure.id)).verifications}


def test_node_and_route_corrections(case):
    world, roots, _epoch, a, b, profile = case
    writer = _writer(roots[a], profile, world)
    root = writer.retract(retracts(writer.read_view.get("assessment:a-1"), "node"))
    case = published(case)
    assert len(inputs(case, policy(root.id)).assessments) == len(inputs(case, policy()).assessments) + 1
    dataset = writer.add(stored.dataset_node(title="derived", resources=pinned("cut45-derived"),
        basis={"tag": "single", "routes": [{"identity": "route:one", "run": "run:run-a",
            "ancestor": dataset_ref("d-a"), "transforms": [dataset_ref("d-a")]}]}))
    digest = stored.stored_semantic_hash(dataset)
    assert digest is not None
    route = writer.retract(stored.retraction_node(title="route", target=stored.RouteTarget(dataset.id, dataset.id, digest, "route:one"),
        reason="wrong-route", rationale="fixture", grounds=("verification:v-1",), actor=ACTOR, event_token="route"))
    case = published(case)
    view = open_world_view(world, case[2])
    kwargs = world_kwargs(view, profile, a, b)
    kwargs["context"] = replace(kwargs["context"], snapshot=lineage_snapshot(view, (dataset.id,)))
    args = {key: kwargs[key] for key in ("context", "profile", "resolution", "binding")}
    kept = gather(view, "proposition:p", **args, acceptance=policy(route.id))
    retired = gather(view, "proposition:p", **args, acceptance=policy())
    assert len(effective_routes(kept.snapshot, dataset.id)) == 1
    assert effective_routes(retired.snapshot, dataset.id) == ()


def test_counter_and_receipt_fidelity(case):
    world, roots, _epoch, a, b, profile = case
    writer = _writer(roots[a], profile, world)
    root = writer.retract(retracts(writer.read_view.get("assessment:a-1"), "root"))
    counter = writer.retract(retracts(root, "counter"))
    case = published(case)
    assert dict(inputs(case, policy()).retractions.found)[root.id] == RETRACTION_OVERTURNED
    assert dict(inputs(case, policy(counter.id)).retractions.found)[root.id] == RETRACTION_UPHELD
    unrelated = writer.retract(retracts(writer.read_view.get("assessment:a-2"), "unrelated"))
    case = published(case)
    view = open_world_view(world, case[2])
    enumeration = replace(view.retraction_enumeration(), found=tuple(
        (ref, RETRACTION_UPHELD if ref == root.id else resolution) for ref, resolution in view.retraction_enumeration().found))
    # Adversarial packaging fixture; honest counters above use durable retract.
    receipt = document(case[2], "retraction-receipt.yaml")
    receipt["enumeration"] = derive.retraction_enumeration_projection(enumeration)
    receipt["subject"] = derive.retraction_enumeration_identity(enumeration)
    corrupt = repackage(world, case[2], {"retraction-receipt.yaml": receipt})
    with pytest.raises(RetractionResolutionDisagreement) as caught:
        inputs((world, roots, corrupt, a, b, profile), policy(unrelated.id))
    assert caught.value.ref == root.id


def test_snapshot_filter_and_history(case):
    world, roots, epoch, a, _b, profile = case
    writer = _writer(roots[a], profile, world)
    root = writer.retract(snapshot_retraction(open_world_view(world, epoch).producer_snapshot_identity()))
    with pytest.raises(ProducerSnapshotRetracted):
        inputs(case, policy())
    assert inputs(case, policy(root.id)).assessments
    counter = writer.retract(retracts(root, "counter"))
    before, after = inputs(case, policy()), inputs(case, policy(root.id))
    assert dict(before.retractions.found) == {root.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}
    assert not after.retractions.found and before.closure().digest() != after.closure().digest()
    # Adversarial malformed counter uses the raw import fixture.
    malformed = broken_counter(root, "malformed")
    raw_write(roots[a], malformed)
    with pytest.raises(RetractionUnreadable):
        inputs(case, policy())
    assert inputs(case, policy(malformed.id)).assessments


def test_completed_and_incomplete_reports(case, monkeypatch):
    a = case[3]
    def early(*_args, **_kwargs):
        raise FacetUndeclared("early")
    with monkeypatch.context() as patch:
        patch.setattr(stored, "assessment_value", early)
        result, admission = answer(case, policy("verification:v-2"))
        assert isinstance(result, Refused) and result.reason == "early"
        assert result.acceptance == AcceptanceContext("durable policy", (), False)
        assert admission == NotReached()
    def late(**_kwargs):
        raise ContractDisagreement("late")
    monkeypatch.setattr(evaluation, "consulted_contracts", late)
    result, admission = answer(case, policy("verification:v-2"))
    assert isinstance(result, Refused) and result.reason == "consulted-contracts-disagree: late"
    assert result.acceptance == AcceptanceContext("durable policy", ((a, "verification:v-2"),), True)
    assert admission == NotReached()


def test_statement_and_two_policies(case):
    first, second = inputs(case, policy(statement="first")), inputs(case, policy(statement="second"))
    assert first.closure().digest() != second.closure().digest()
    one, two = inputs(case, policy("verification:v-1")), inputs(case, policy("verification:v-2"))
    assert one.acceptance is not None and two.acceptance is not None
    assert one.acceptance.excluded != two.acceptance.excluded
    assert first.acceptance == AcceptanceContext("first", (), True)
    result, _ = answer(case, policy(statement="first"))
    assert isinstance(result, Belief) and result.belief_input_digest == first.closure().digest()


def test_accept_all_refusal_parity(case):
    before, before_admission = answer(case, None)
    after, after_admission = answer(case, policy())
    assert isinstance(before, Belief) and isinstance(after, Belief)
    assert (before.value, before.policy_binding, before_admission) == (after.value, after.policy_binding, after_admission)
    world, roots, epoch, a, b, profile = case
    kwargs = over_kwargs(world_kwargs(open_world_view(world, epoch), profile, a, b))
    make_absent(roots, b)
    view = open_world_view(world, epoch)
    outcomes = [evaluate_over_traced(view, "proposition:p", **kwargs, acceptance=p) for p in (None, policy())]
    assert all(isinstance(result, NoBelief) and result.reason == "unavailable-corpus-absent" and admission == NotReached()
               for result, admission in outcomes)
