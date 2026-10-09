"""Cut 45: caller acceptance precedes semantic reads and standing effects."""

from dataclasses import FrozenInstanceError, replace
from typing import Any, cast

import pytest

# These checks fail if acceptance is applied after correction validation/folding.
from authority import ACTOR
from domain_facet_fixtures import LOCAL_CORPUS_ID, over_kwargs, profile_with
from fixtures_cut3 import typed_applicability, typed_estimand
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from test_belief import scenario
from test_evaluation import PROPOSITION_REF, _fixture
from test_local_standing import retracts
from test_relocation import MOVE_FIELDS
from test_snapshot_retraction import broken_counter, snapshot_retraction
from test_world_build import ALPHA, BETA
from test_world_receipts import document, hold_shipped, publish, repackage
from test_world_standing import support_in, writer_at
from test_world_view import split_evaluation_world, world_kwargs

from beliefs import belief, evaluation, stored
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD
from beliefs.errors import (
    ContractDisagreement,
    CorpusDamaged,
    FacetUndeclared,
    LoneSurrogate,
    MalformedRecord,
    ProducerSnapshotRetracted,
    RetractionResolutionDisagreement,
    RetractionUnreadable,
)
from beliefs.evaluation import evaluate_over_traced, gather
from beliefs.relocation import move
from beliefs.world import derive
from beliefs.world.view import open_world_view


def test_g13_b_complete_report(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    seen = []
    policy = belief.AcceptancePolicy(
        lambda c, r: seen.append((c, r)) or r not in {"assessment:a-3", "verification:v-3"}, "policy"
    )
    inputs = gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs, acceptance=policy)
    assert inputs.acceptance == belief.AcceptanceContext(
        "policy", ((LOCAL_CORPUS_ID, "assessment:a-3"), (LOCAL_CORPUS_ID, "verification:v-3")), True
    )
    assert len(seen) == len(set(seen)) == 6
    assert set(inputs.read_trace) <= inputs.declared_refs()


def test_g13_c_early_error(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    nodes = tuple(fixture.view.iter_stored())

    def refused(*_args, **_kwargs):
        raise FacetUndeclared("early sentinel")

    monkeypatch.setattr(stored, "assessment_value", refused)
    answers = []
    for reverse in (False, True):
        ordered = sorted(nodes, key=lambda n: n.id == "assessment:a-3", reverse=reverse)
        monkeypatch.setattr(type(fixture.view), "iter_stored", lambda _self, ordered=ordered: iter(ordered))
        answer, admission = evaluate_over_traced(
            fixture.view, PROPOSITION_REF, **fixture.kwargs, acceptance=_policy("assessment:a-3")
        )
        assert isinstance(answer, belief.Refused) and answer.reason == "early sentinel"
        assert admission == belief.NotReached()
        answers.append(answer.acceptance)
    assert answers == [belief.AcceptanceContext("fixture policy", (), False)] * 2


def test_g13_d_late_error(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    seen = []

    def refused(**_kwargs):
        raise ContractDisagreement("late sentinel")

    monkeypatch.setattr(evaluation, "consulted_contracts", refused)
    policy = belief.AcceptancePolicy(lambda c, r: seen.append((c, r)) or r != "assessment:a-3", "policy")
    answer, admission = evaluate_over_traced(fixture.view, PROPOSITION_REF, **fixture.kwargs, acceptance=policy)
    assert isinstance(answer, belief.Refused) and answer.reason == "consulted-contracts-disagree: late sentinel"
    assert answer.acceptance == belief.AcceptanceContext("policy", ((LOCAL_CORPUS_ID, "assessment:a-3"),), True)
    assert admission == belief.NotReached() and len(seen) == len(set(seen)) == 6


def test_g13_e_late_absence(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    context = replace(
        fixture.context,
        snapshot=replace(fixture.context.snapshot, not_present={fixture.context.snapshot.roots[0]: "missing"}),
    )
    answer, admission = evaluate_over_traced(
        fixture.view, PROPOSITION_REF, **{**fixture.kwargs, "context": context}, acceptance=_policy("assessment:a-3")
    )
    assert isinstance(answer, belief.NoBelief) and answer.reason == "unavailable-corpus-absent"
    assert answer.acceptance == belief.AcceptanceContext("fixture policy", ((LOCAL_CORPUS_ID, "assessment:a-3"),), True)
    assert admission == belief.NotReached()


def test_g13_f_supplied_context(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    context = replace(fixture.context, acceptance=belief.AcceptanceContext("forged", (), True))

    def unexpected(*_args, **_kwargs):
        pytest.fail("forged selection reached a read")

    monkeypatch.setattr(type(fixture.view), "iter_stored", unexpected)
    monkeypatch.setattr(type(fixture.view), "resolve", unexpected)
    for policy in (None, belief.AcceptancePolicy(unexpected, "real")):
        with pytest.raises(MalformedRecord, match="supplied-acceptance-context"):
            gather(fixture.view, PROPOSITION_REF, **{**fixture.gather_kwargs, "context": context}, acceptance=policy)


def test_g13_h_closure_statement(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)

    def run(statement, reject=()):
        policy = belief.AcceptancePolicy(lambda _c, r: r not in reject, statement)
        inputs = gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs, acceptance=policy)
        answer, _ = evaluate_over_traced(fixture.view, PROPOSITION_REF, **fixture.kwargs, acceptance=policy)
        assert isinstance(answer, belief.Belief)
        assert inputs.closure().digest() == answer.belief_input_digest
        assert inputs.closure().projection["acceptance_policy"] == statement
        return answer

    first = run("first")
    second = run("second")
    irrelevant = run("first", ("assessment:a-3",))
    assert first.value == second.value == irrelevant.value
    assert first.belief_input_digest != second.belief_input_digest
    assert first.belief_input_digest == irrelevant.belief_input_digest
    unrestricted = gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs)
    assert "acceptance_policy" not in unrestricted.closure().projection


def test_g13_i_two_policies(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    seen = []
    for rejected in (("assessment:a-3",), ("verification:v-3",)):
        policy = belief.AcceptancePolicy(
            lambda c, r, rejected=rejected: seen.append((c, r)) or r not in rejected, "same"
        )
        inputs = gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs, acceptance=policy)
        assert inputs.acceptance is not None
        assert inputs.acceptance.excluded == ((LOCAL_CORPUS_ID, rejected[0]),)
    assert len(seen) == 12 and len(set(seen)) == 6
    world, roots, published = split_evaluation_world(tmp_path / "world", beta_refs=())
    root = snapshot_retraction(open_world_view(world, published).producer_snapshot_identity())
    raw_write(roots[ALPHA], root)
    counter = retracts(root, "counter")
    raw_write(roots[ALPHA], counter)
    view = open_world_view(world, published)
    assert view.snapshot_standing().history
    assert _gather_world(view, {root.id}).retractions.found == ()
    with pytest.raises(ProducerSnapshotRetracted):
        _gather_world(view, {counter.id})


def test_g13_j_capture_integrity(tmp_path):
    from test_world_view import damage, make_absent

    for condition in ("absent", "damaged"):
        world, roots, published = split_evaluation_world(tmp_path / condition)
        kwargs = over_kwargs(world_kwargs(open_world_view(world, published), profile_with()))
        if condition == "absent":
            make_absent(roots, BETA)
        else:
            damage(roots[BETA], "parse-error")
        view = open_world_view(world, published, on_damage="report")
        policy = belief.AcceptancePolicy(lambda _c, _r: False, "none")
        if condition == "damaged":
            with pytest.raises(CorpusDamaged):
                evaluate_over_traced(view, PROPOSITION_REF, **kwargs, acceptance=policy)
        else:
            answer, admission = evaluate_over_traced(view, PROPOSITION_REF, **kwargs, acceptance=policy)
            assert isinstance(answer, belief.NoBelief) and answer.reason == "unavailable-corpus-absent"
            assert answer.acceptance == belief.AcceptanceContext("none", (), False)
            assert admission == belief.NotReached()


@pytest.mark.parametrize(
    "case", ("clean", "counter", "split", "corrupt", "malformed", "drift", "snapshot", "absent", "binding")
)
def test_g12_l_accept_all_refusal_parity(tmp_path, case):
    from test_world_view import make_absent

    length = 2 if case in {"counter", "split"} else 1 if case == "corrupt" else 0
    world, roots, published, chain = _ordinary_chain(tmp_path, length)
    if case == "split":
        move(
            writer_at(roots[ALPHA], profile_with()), writer_at(roots[BETA], profile_with()), chain[1].id, **MOVE_FIELDS
        )
        published = publish(world, (ALPHA, BETA), hold_shipped(world))
    elif case == "corrupt":
        enumeration = replace(
            open_world_view(world, published).retraction_enumeration(), found=((chain[0].id, RETRACTION_OVERTURNED),)
        )
        receipt = document(published, "retraction-receipt.yaml")
        receipt["enumeration"] = derive.retraction_enumeration_projection(enumeration)
        receipt["subject"] = derive.retraction_enumeration_identity(enumeration)
        published = repackage(world, published, {"retraction-receipt.yaml": receipt})
    elif case == "malformed":
        raw_write(roots[ALPHA], Node(id="retraction:bad", kind="retraction", title="bad"))
    elif case == "drift":
        node = support_in(open_world_view(world, published), ALPHA).model_copy(deep=True)
        node.deprecated_ids.append("assessment:drift-alias")
        raw_write(roots[ALPHA], node)
    elif case == "snapshot":
        root = snapshot_retraction(open_world_view(world, published).producer_snapshot_identity())
        raw_write(roots[ALPHA], root)
        raw_write(roots[ALPHA], retracts(root, "snapshot-counter"))
    elif case == "absent":
        make_absent(roots, BETA)
    view = open_world_view(world, published)
    kwargs = over_kwargs(world_kwargs(view, profile_with()))
    if case == "binding":
        kwargs["binding"] = object()
    outcomes = []
    for policy in (None, _policy()):
        try:
            answer, admission = evaluate_over_traced(view, PROPOSITION_REF, **kwargs, acceptance=policy)
        except (RetractionResolutionDisagreement, RetractionUnreadable, ProducerSnapshotRetracted) as refused:
            outcomes.append((type(refused), str(refused), getattr(refused, "ref", None)))
        else:
            if isinstance(answer, belief.Belief):
                outcomes.append((type(answer), answer.value, answer.policy_binding, admission))
            else:
                outcomes.append((type(answer), answer.reason, getattr(answer, "detail", None), admission))
    assert outcomes[0] == outcomes[1]


def test_rejected_malformed_verification_and_local_correction(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    verification = fixture.view.get("verification:v-1").model_copy(update={"facets": {}}, deep=True)
    raw_write(tmp_path, verification)
    correction = Node(id="retraction:bad", kind="retraction", title="bad")
    raw_write(tmp_path, correction)
    original = stored.verification_value

    def decode(node):
        assert node.id != verification.id, "rejected verification decoded"
        return original(node)

    monkeypatch.setattr(stored, "verification_value", decode)
    inputs = gather(
        reopen(tmp_path), PROPOSITION_REF, **fixture.gather_kwargs, acceptance=_policy(verification.id, correction.id)
    )
    assert inputs.acceptance is not None and inputs.acceptance.complete
    assert not inputs.retractions.found
    assert verification.id not in {v.ref for v in inputs.verifications}


def test_canonical_correction_alias_decides_once(tmp_path, monkeypatch):
    world, roots, published, (root,) = _ordinary_chain(tmp_path)
    alias = "retraction:old"
    raw_write(roots[ALPHA], root.model_copy(update={"deprecated_ids": [alias]}))
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    view = open_world_view(world, published)
    enumeration = replace(view.retraction_enumeration(), found=((alias, RETRACTION_UPHELD),))
    monkeypatch.setattr(type(view), "retraction_enumeration", lambda _self: enumeration)
    seen = []
    kwargs = world_kwargs(view, profile_with())
    inputs = gather(
        view,
        PROPOSITION_REF,
        context=kwargs["context"],
        profile=profile_with(),
        resolution=kwargs["resolution"],
        binding=kwargs["binding"],
        acceptance=belief.AcceptancePolicy(lambda c, r: seen.append((c, r)) or True, "policy"),
    )
    assert seen.count((ALPHA, root.id)) == 1
    assert (ALPHA, alias) not in seen and root.id in dict(inputs.retractions.found)


def test_excluded_evidence_holder_still_serves_dependencies(tmp_path):
    from dataset_fixtures import dataset_ref

    world, _roots, published = split_evaluation_world(
        tmp_path, beta_refs=("proposition:p", dataset_ref("d-a"), "assessment:a-2")
    )
    view = open_world_view(world, published)
    kwargs = over_kwargs(world_kwargs(view, profile_with()))
    answer, admission = evaluate_over_traced(
        view, PROPOSITION_REF, **kwargs, acceptance=belief.AcceptancePolicy(lambda c, _r: c != BETA, "alpha evidence")
    )
    assert isinstance(answer, belief.Belief) and isinstance(admission, belief.Reached)
    assert answer.acceptance is not None and (BETA, "assessment:a-2") in answer.acceptance.excluded


def _policy(*rejected):
    return belief.AcceptancePolicy(lambda _c, ref: ref not in rejected, "fixture policy")


def _twin(root, *, outcome="supported"):
    node = stored.assessment_node(
        "twin",
        title="twin",
        spec="spec-a",
        run="run:run-a",
        proposition=PROPOSITION_REF,
        outcome=outcome,
        interpretation_rule="rule-1",
        estimand=typed_estimand(),
        applicability=typed_applicability(),
    )
    raw_write(root, node)
    return node


def _verification(root, fixture, *, verdict="failed", edge="assessment:a-1", supersedes=None):
    node = stored.verification_node(
        "extra",
        title="extra",
        assessment=fixture.assessments[0].identity(),
        assessment_ref=edge,
        scope="clean-environment",
        verdict=verdict,
        supersedes=supersedes,
    )
    raw_write(root, node)
    return node


def _admission(root, fixture, policy):
    answer, admission = evaluate_over_traced(reopen(root), PROPOSITION_REF, **fixture.kwargs, acceptance=policy)
    assert isinstance(admission, belief.Reached), answer
    return admission.admitted


def test_g10_a_all_assessments_rejected(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    answer, admission = evaluate_over_traced(
        fixture.view,
        PROPOSITION_REF,
        **fixture.kwargs,
        acceptance=_policy("assessment:a-1", "assessment:a-2", "assessment:a-3"),
    )
    assert isinstance(answer, belief.NoBelief) and answer.reason == "no-eligible-assessment"
    assert admission == belief.Reached(frozenset())


def test_g10_b_contradictory_twin(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    twin = _twin(tmp_path, outcome="refuted")
    answer, _ = evaluate_over_traced(reopen(tmp_path), PROPOSITION_REF, **fixture.kwargs, acceptance=_policy(twin.id))
    assert isinstance(answer, belief.Belief)
    answer, _ = evaluate_over_traced(reopen(tmp_path), PROPOSITION_REF, **fixture.kwargs, acceptance=_policy())
    assert isinstance(answer, belief.Refused) and "disagree" in answer.reason


def test_g10_c_malformed_assessment(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    twin = _twin(tmp_path)
    raw_write(tmp_path, twin.model_copy(update={"facets": {}}))
    original = stored.assessment_value

    def decode(node, **kwargs):
        assert node.id != twin.id, "rejected facet decoded"
        return original(node, **kwargs)

    monkeypatch.setattr(stored, "assessment_value", decode)
    inputs = gather(reopen(tmp_path), PROPOSITION_REF, **fixture.gather_kwargs, acceptance=_policy(twin.id))
    assert len(inputs.assessments) == 2


def test_g10_d_canonical_holder(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path)
    view = open_world_view(world, published)
    node = support_in(view, ALPHA).model_copy(deep=True)
    node.deprecated_ids.append("assessment:former")
    raw_write(roots[ALPHA], node)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    view = open_world_view(world, published)
    seen = []
    kwargs = world_kwargs(view, profile_with())
    gather(
        view,
        PROPOSITION_REF,
        context=kwargs["context"],
        profile=profile_with(),
        resolution=kwargs["resolution"],
        binding=kwargs["binding"],
        acceptance=belief.AcceptancePolicy(lambda c, r: seen.append((c, r)) or True, "policy"),
    )
    assert (ALPHA, node.id) in seen and (ALPHA, "assessment:former") not in seen
    assert len(seen) == len(set(seen))


def test_g10_e_manifest_preflight(tmp_path, monkeypatch):
    from beliefs.errors import ManifestMalformed, ManifestMissing

    fixture = _fixture(tmp_path, PROPOSITION_REF)

    def unexpected(*_args, **_kwargs):
        pytest.fail("manifest preflight read records")

    monkeypatch.setattr(type(fixture.view), "iter_stored", unexpected)
    monkeypatch.setattr(type(fixture.view), "resolve", unexpected)
    manifest = tmp_path / "corpus.yaml"
    manifest.unlink()
    with pytest.raises(ManifestMissing):
        gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs, acceptance=_policy())
    manifest.write_text("not: a manifest")
    with pytest.raises(ManifestMalformed):
        gather(fixture.view, PROPOSITION_REF, **fixture.gather_kwargs, acceptance=_policy())


def test_g10_f_accepted_attribution(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    view = open_world_view(world, published)
    accepted = support_in(view, ALPHA)
    twin = accepted.model_copy(update={"id": "assessment:beta-twin", "uid": "fixture-beta-twin"}, deep=True)
    from nodes.core.relations import Relation

    twin.relations = [Relation(source=twin.id, predicate=r.predicate, target=r.target) for r in twin.relations]
    raw_write(roots[BETA], twin)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    inputs = _gather_world(open_world_view(world, published), {twin.id})
    identity = stored.assessment_value(accepted, profile=profile_with()).identity()
    assert inputs.node_corpus[identity] == (ALPHA,)


def test_g11_a_rejected_failure(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    failure = _verification(tmp_path, fixture)
    assert fixture.assessments[0].identity() in _admission(tmp_path, fixture, _policy(failure.id))
    assert fixture.assessments[0].identity() not in _admission(tmp_path, fixture, _policy())


def test_g11_b_rejected_pass(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    assert fixture.assessments[0].identity() not in _admission(tmp_path, fixture, _policy("verification:v-1"))


def test_g11_c_rejected_superseder(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    failure = _verification(tmp_path, fixture)
    later = stored.verification_node(
        "later",
        title="later",
        assessment=fixture.assessments[0].identity(),
        assessment_ref="assessment:a-1",
        scope="clean-environment",
        verdict="passed",
        supersedes=failure.id,
    )
    raw_write(tmp_path, later)
    assert fixture.assessments[0].identity() not in _admission(tmp_path, fixture, _policy(later.id))
    assert fixture.assessments[0].identity() in _admission(tmp_path, fixture, _policy())


def test_g11_d_failure_names_rejected_twin(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    twin = _twin(tmp_path)
    _verification(tmp_path, fixture, edge=twin.id)
    assert fixture.assessments[0].identity() not in _admission(tmp_path, fixture, _policy(twin.id))


def test_g11_e_pass_names_rejected_twin(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    twin = _twin(tmp_path)
    _verification(tmp_path, fixture, edge=twin.id, verdict="passed")
    assert fixture.assessments[0].identity() in _admission(tmp_path, fixture, _policy(twin.id, "verification:v-1"))


def test_g11_f_edge_scope(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    view = open_world_view(world, published)
    rejected = support_in(view, ALPHA)
    correction = writer_at(roots[ALPHA], profile_with()).retract(retracts(rejected, "excluded-target"))
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    inputs = _gather_world(open_world_view(world, published), {rejected.id})
    identity = stored.assessment_value(rejected, profile=profile_with()).identity()
    assert identity not in {a.identity() for a in inputs.assessments}
    assert correction.id not in dict(inputs.retractions.found)


def test_acceptance_value_validation():
    policy_type: Any = belief.AcceptancePolicy
    context_type = belief.AcceptanceContext
    for text in ("", 1, None):
        with pytest.raises(MalformedRecord, match="acceptance-statement-not-text"):
            policy_type(lambda _c, _r: True, text)
    with pytest.raises(MalformedRecord, match="acceptance-predicate-not-callable"):
        policy_type(None, "policy")
    with pytest.raises(LoneSurrogate):
        policy_type(lambda _c, _r: True, "\ud800")
    with pytest.raises(LoneSurrogate):
        context_type("\ud800", (), False)
    with pytest.raises(MalformedRecord, match="incomplete-acceptance-exclusions"):
        context_type("policy", (("c", "assessment:a"),), False)
    selection = context_type("policy", (("z", "a"), ("a", "b"), ("z", "a")), True)
    assert selection.excluded == (("a", "b"), ("z", "a"))
    with pytest.raises(FrozenInstanceError):
        selection.statement = "changed"  # pyright: ignore[reportAttributeAccessIssue]


def test_g13_g_pure_incomplete(monkeypatch):
    selection = belief.AcceptanceContext("policy", (), False)
    kwargs = scenario()
    kwargs["context"] = replace(kwargs["context"], acceptance=selection)

    def unexpected_consulted(**_kwargs):
        pytest.fail("incomplete selection reached the consulted walk")

    monkeypatch.setattr(belief, "consulted_contracts", unexpected_consulted)
    answer, admission = belief.evaluate_traced(**kwargs)
    assert isinstance(answer, belief.Refused)
    assert answer.reason == "acceptance-selection-incomplete"
    assert answer.acceptance == selection
    assert admission == belief.NotReached()
    answer, admission = belief.evaluate_traced(**scenario(context=kwargs["context"], binding=object()))
    assert isinstance(answer, belief.Refused) and answer.reason.startswith("binding-not-exact")
    assert answer.acceptance == selection and admission == belief.NotReached()

    def unexpected(*_args, **_kwargs):
        pytest.fail("binding guard performed reads")

    policy = belief.AcceptancePolicy(unexpected, "policy")
    answer, admission = evaluate_over_traced(
        cast(Any, object()),
        PROPOSITION_REF,
        availability=kwargs["availability"],
        context=kwargs["context"],
        profile=kwargs["profile"],
        resolution=cast(Any, object()),
        binding=object(),
        acceptance=policy,
    )
    assert isinstance(answer, belief.Refused) and answer.reason.startswith("binding-not-exact")
    assert answer.acceptance == selection and admission == belief.NotReached()


def test_pure_completed_context_accompanies_every_answer():
    selection = belief.AcceptanceContext("policy", (("c", "unrelated"),), True)
    kwargs = scenario()
    kwargs["context"] = replace(kwargs["context"], acceptance=selection)
    assert isinstance(belief.evaluate(**kwargs), belief.Belief)
    assert belief.evaluate(**kwargs).acceptance == selection
    unavailable = replace(kwargs["availability"], fixtures={})
    answer = belief.evaluate(**scenario(context=kwargs["context"], availability=unavailable))
    assert isinstance(answer, belief.NoBelief) and answer.acceptance == selection
    answer = belief.evaluate(**scenario(context=kwargs["context"], binding=object()))
    assert isinstance(answer, belief.Refused) and answer.acceptance == selection


def _gather_world(view, reject=(), *, context=None):
    profile = profile_with()
    kwargs = world_kwargs(view, profile)
    return gather(
        view,
        "proposition:p",
        profile=profile,
        context=kwargs["context"] if context is None else context,
        resolution=kwargs["resolution"],
        binding=kwargs["binding"],
        acceptance=belief.AcceptancePolicy(lambda _c, r: r not in reject, "fixture policy"),
    )


def _ordinary_chain(tmp_path, length=1):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    writer = writer_at(roots[ALPHA], profile_with())
    target = support_in(open_world_view(world, published), ALPHA)
    chain = []
    for index in range(length):
        target = writer.retract(retracts(target, f"chain-{index}"))
        chain.append(target)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    return world, roots, published, chain


def test_g12_a_node_retraction(tmp_path):
    world, _roots, published, (root,) = _ordinary_chain(tmp_path)
    view = open_world_view(world, published)
    kept = _gather_world(view, {root.id})
    subtracted = _gather_world(view)
    assert len(kept.assessments) == len(subtracted.assessments) + 1
    assert root.id not in dict(kept.retractions.found)


def test_g12_b_route_retraction(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    writer = writer_at(roots[ALPHA], profile_with())
    from dataset_fixtures import dataset_ref

    from beliefs.corpus import lineage_snapshot
    from beliefs.lineage import effective_routes

    target = writer.read_view.get(dataset_ref("d-a")).model_copy(deep=True)
    target.facets[stored.LINEAGE_BASIS_FACET] = {
        "tag": "single",
        "routes": [
            {
                "identity": "route:fixture",
                "run": "run:run-b",
                "ancestor": dataset_ref("d-b"),
                "transforms": [dataset_ref("d-b")],
            }
        ],
    }
    target = stored.stamp_semantic_identity(target)
    raw_write(roots[ALPHA], target)
    target_hash = stored.stored_semantic_hash(target)
    assert target_hash is not None
    correction = stored.retraction_node(
        title="route",
        target=stored.RouteTarget(target.id, target.id, target_hash, "route:fixture"),
        reason="wrong-route",
        rationale="fixture",
        grounds=("verification:v-1",),
        actor=ACTOR,
        event_token="route",
    )
    raw_write(roots[ALPHA], correction)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile_with())
    context = replace(kwargs["context"], snapshot=lineage_snapshot(view, (target.id,)))
    kept = _gather_world(view, {correction.id}, context=context)
    retired = _gather_world(view, context=context)
    assert len(effective_routes(kept.snapshot, target.id)) == 1
    assert effective_routes(retired.snapshot, target.id) == ()


def test_g12_c_counter_retraction(tmp_path):
    world, _roots, published, (root, counter) = _ordinary_chain(tmp_path, 2)
    view = open_world_view(world, published)
    before = _gather_world(view)
    after = _gather_world(view, {counter.id})
    assert len(after.assessments) == len(before.assessments) - 1
    assert dict(after.retractions.found)[root.id] == RETRACTION_UPHELD
    assert counter.id not in dict(after.retractions.found)


def test_g12_d_changed_chain_receipt(tmp_path):
    world, _roots, published, (root, counter, deep) = _ordinary_chain(tmp_path, 3)
    view = open_world_view(world, published)
    assert dict(view.retraction_enumeration().found)[root.id] == RETRACTION_UPHELD
    selected = _gather_world(view, {deep.id})
    assert dict(selected.retractions.found) == {root.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}


def test_g12_e_malformed_snapshot_candidate(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    malformed = Node(id="retraction:malformed", kind="retraction", title="malformed")
    raw_write(roots[ALPHA], malformed)
    view = open_world_view(world, published)
    with pytest.raises(RetractionUnreadable):
        _gather_world(view)
    assert _gather_world(view, {malformed.id}).assessments


def test_g12_f_accepted_snapshot_chain(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    initial = open_world_view(world, published)
    root = snapshot_retraction(initial.producer_snapshot_identity())
    broken = broken_counter(root)
    raw_write(roots[ALPHA], root)
    raw_write(roots[ALPHA], broken)
    view = open_world_view(world, published)
    with pytest.raises(RetractionUnreadable) as caught:
        _gather_world(view)
    assert caught.value.ref == broken.id


def test_g12_g_mapped_oracle(tmp_path, monkeypatch):
    world, roots, published, (root,) = _ordinary_chain(tmp_path)
    alias = "retraction:former"
    root = root.model_copy(update={"deprecated_ids": [alias]})
    raw_write(roots[ALPHA], root)
    root_hash = stored.stored_semantic_hash(root)
    assert root_hash is not None
    counter = stored.retraction_node(
        title="counter",
        target=stored.NodeTarget(alias, root.id, root_hash),
        reason="defective-code",
        rationale="fixture",
        grounds=("verification:v-1",),
        actor=ACTOR,
        event_token="alias-counter",
    )
    raw_write(roots[ALPHA], counter)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    added_alias = "retraction:post-epoch-alias"
    root = root.model_copy(update={"deprecated_ids": [alias, added_alias]})
    raw_write(roots[ALPHA], root)
    view = open_world_view(world, published)
    assert view._captured_views[ALPHA].resolve(added_alias) == root.id
    assert view._mapped_view(ALPHA).resolve(added_alias) is None
    assert view._mapped_view(ALPHA).resolve(alias) == root.id
    # Characterize the primitive's live-id precedence independently of the
    # corpus admission boundary, which correctly refuses this collision.
    from beliefs.corpus import _CapturedCheckView

    drift = Node(id=alias, kind="retraction", title="synthetic drift")
    captured = _CapturedCheckView((root, drift))
    mapped = _CapturedCheckView((root,), addresses={alias: root.id, root.id: root.id})
    assert captured.resolve(alias) == drift.id
    assert mapped.resolve(alias) == root.id
    standing = view.snapshot_standing()
    monkeypatch.setattr(type(view), "snapshot_standing", lambda _self, **_kwargs: standing)
    original = _CapturedCheckView.resolve
    calls = []

    def resolve(self, ref):
        if self is view._captured_views[ALPHA]:
            calls.append(ref)
        return original(self, ref)

    monkeypatch.setattr(_CapturedCheckView, "resolve", resolve)
    selected = _gather_world(view)
    assert dict(selected.retractions.found)[root.id] == RETRACTION_OVERTURNED
    assert calls == [], "ordinary fold used the full capture instead of its mapped resolver"


def test_g12_h_split_with_exclusion(tmp_path):
    world, roots, _published, (root, counter) = _ordinary_chain(tmp_path, 2)
    alpha = writer_at(roots[ALPHA], profile_with())
    beta = writer_at(roots[BETA], profile_with())
    unrelated = alpha.retract(retracts(alpha.read_view.get("assessment:a-2"), "unrelated"))
    move(alpha, beta, counter.id, **MOVE_FIELDS)
    split = publish(world, (ALPHA, BETA), hold_shipped(world))
    with pytest.raises(RetractionResolutionDisagreement) as caught:
        _gather_world(open_world_view(world, split), {unrelated.id})
    assert caught.value.ref == root.id


def test_g12_i_unchanged_receipt(tmp_path):
    world, roots, published, (root,) = _ordinary_chain(tmp_path)
    alpha = writer_at(roots[ALPHA], profile_with())
    unrelated = alpha.retract(retracts(alpha.read_view.get("assessment:a-2"), "unrelated"))
    published = publish(world, (ALPHA, BETA), hold_shipped(world))
    view = open_world_view(world, published)
    enumeration = replace(
        view.retraction_enumeration(),
        found=tuple(
            (ref, RETRACTION_OVERTURNED if ref == root.id else resolution)
            for ref, resolution in view.retraction_enumeration().found
        ),
    )
    receipt = document(published, "retraction-receipt.yaml")
    receipt["enumeration"] = derive.retraction_enumeration_projection(enumeration)
    receipt["subject"] = derive.retraction_enumeration_identity(enumeration)
    corrupt = repackage(world, published, {"retraction-receipt.yaml": receipt})
    with pytest.raises(RetractionResolutionDisagreement) as caught:
        _gather_world(open_world_view(world, corrupt), {unrelated.id})
    assert caught.value.ref == root.id


def test_g12_j_snapshot_root(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    root = snapshot_retraction(open_world_view(world, published).producer_snapshot_identity())
    raw_write(roots[ALPHA], root)
    view = open_world_view(world, published)
    with pytest.raises(ProducerSnapshotRetracted):
        _gather_world(view)
    assert _gather_world(view, {root.id}).assessments


def test_g12_k_snapshot_history(tmp_path):
    world, roots, published = split_evaluation_world(tmp_path, beta_refs=())
    root = snapshot_retraction(open_world_view(world, published).producer_snapshot_identity())
    counter = retracts(root, "snapshot-counter")
    raw_write(roots[ALPHA], root)
    raw_write(roots[ALPHA], counter)
    view = open_world_view(world, published)
    before = _gather_world(view)
    after = _gather_world(view, {root.id})
    assert dict(before.retractions.found) == {root.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}
    assert after.retractions.found == ()
    assert not any(kind == "retraction" for kind, _ref in after.read_trace)
    assert before.closure().digest() != after.closure().digest()


def test_g13_a_policy_validation(tmp_path):
    test_acceptance_value_validation()
    # Truth coercion or retrying a raising predicate must fail this check.
    world, _roots, published, _chain = _ordinary_chain(tmp_path)
    view = open_world_view(world, published)
    kwargs = world_kwargs(view, profile_with())
    for result in (1, None, "true"):
        callback: Any = lambda _c, _r, result=result: result
        policy = belief.AcceptancePolicy(callback, "policy")
        with pytest.raises(MalformedRecord, match="acceptance-result-not-bool"):
            gather(
                view,
                "proposition:p",
                context=kwargs["context"],
                profile=profile_with(),
                resolution=kwargs["resolution"],
                binding=kwargs["binding"],
                acceptance=policy,
            )

    def raising(_corpus, _address):
        raise ValueError("predicate failure")

    with pytest.raises(ValueError, match="predicate failure"):
        gather(
            view,
            "proposition:p",
            context=kwargs["context"],
            profile=profile_with(),
            resolution=kwargs["resolution"],
            binding=kwargs["binding"],
            acceptance=belief.AcceptancePolicy(raising, "policy"),
        )
