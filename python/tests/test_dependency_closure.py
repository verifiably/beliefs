"""Frozen dependency state is an independently declared member of belief closure."""

from dataclasses import replace

import pytest
from fixtures_cut4 import reopen
from test_evaluation import PROPOSITION_REF, _fixture

from beliefs import stored
from beliefs.admission import AdmissionRefused, admit
from beliefs.evaluation import gather


def test_missing_dependency_changes_closure_and_refuses(tmp_path):
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    key = fixture.assessments[0].key()
    before = gather(
        fixture.view,
        fixture.proposition,
        key=key,
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    missing = fixture.assessments[0].dependencies[0].id
    node = fixture.view.get(missing)
    paths = list(tmp_path.rglob("*.md"))
    path = next(p for p in paths if f"id: {node.id}\n" in p.read_text())
    path.unlink()
    fixture = replace(fixture, view=reopen(tmp_path))
    after = gather(
        fixture.view,
        fixture.proposition,
        key=key,
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    assert after.closure().digest() != before.closure().digest()
    assert (missing.partition(":")[0], missing) in after.declared_refs()
    assert set(after.read_trace) <= after.declared_refs()
    a = after.assessments[0]
    verdict = admit(a, after.runs[a.run], fixture.availability.observations, after.verifications, after.dependencies)
    assert isinstance(verdict, AdmissionRefused)
    assert verdict.reason.startswith("dependency-ineligible")


def calibration_fixture(tmp_path):
    from fixtures_cut4 import raw_write
    from test_standing import calibrated_prediction

    from beliefs.corpus import lineage_snapshot
    from beliefs.projection import project_claim

    fixture = _fixture(tmp_path, PROPOSITION_REF)
    spec, claim, records, basis_ref = calibrated_prediction(polarity="negative")
    basis = stored.assessment_value(records.read(basis_ref), profile=fixture.gather_kwargs["profile"])
    for node in records.nodes.values():
        if not fixture.view.holds(node.id):
            raw_write(tmp_path, node)
    proposition = stored.proposition_node("prediction", title="Prediction", claim=project_claim(claim))
    run = stored.run_node("prediction", title="Prediction", spec=spec.identity)
    assessment = stored.assessment_node(
        "prediction",
        title="Prediction",
        spec=spec.identity,
        run=run.id,
        proposition=proposition.id,
        outcome="supported",
        interpretation_rule=spec.interpretation_rule,
        target=spec.assessed_target,
    )
    from test_evaluation import _address

    calibration_run = stored.run_node(basis.run, title="Calibration", spec=basis.spec, observes=(_address("a"),))
    for node in (
        proposition,
        run,
        assessment,
        calibration_run,
        stored.verification_node(
            "basis",
            title="Basis",
            assessment=basis.identity(),
            assessment_ref=basis_ref,
            scope="clean-environment",
            verdict="passed",
        ),
    ):
        raw_write(tmp_path, node)
    view = reopen(tmp_path)
    value = stored.assessment_value(assessment, profile=fixture.gather_kwargs["profile"])
    raw_write(
        tmp_path,
        stored.verification_node(
            "prediction",
            title="Prediction",
            assessment=value.identity(),
            assessment_ref=assessment.id,
            scope="clean-environment",
            verdict="passed",
        ),
    )
    view = reopen(tmp_path)
    context = replace(fixture.context, snapshot=lineage_snapshot(view, (_address("a"),)))
    return replace(fixture, view=view, proposition=proposition.id, context=context, assessments=(value,)), basis_ref


def test_calibration_across_claims_is_read_without_specs_or_dataset_bytes(tmp_path, monkeypatch):
    from beliefs.belief import Belief
    from beliefs.evaluation import evaluate_over

    fixture, basis = calibration_fixture(tmp_path)
    # No spec is held: evaluation consumes frozen assessment targets exclusively.
    assert not fixture.view.holds("analysis-spec:s")
    inputs = gather(
        fixture.view,
        fixture.proposition,
        key=fixture.assessments[0].key(),
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    assert len(inputs.assessments) == 1
    assert basis in inputs.dependencies.assessments
    assert ("assessment", basis) in inputs.declared_refs()
    assert ("run", "r") in inputs.declared_refs()
    assert ("verification", "verification:basis") in inputs.declared_refs()
    assert set(inputs.read_trace) <= inputs.declared_refs()
    answer = evaluate_over(fixture.view, fixture.proposition, **fixture.kwargs)
    assert isinstance(answer, Belief), answer
    assert answer.belief_input_digest == inputs.closure().digest()


def test_calibration_retraction_changes_state_and_digest_not_key(tmp_path):
    from fixtures_cut4 import raw_write
    from test_local_standing import retracts

    fixture, basis = calibration_fixture(tmp_path)
    key = fixture.assessments[0].key()
    before = gather(
        fixture.view,
        fixture.proposition,
        key=key,
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    captured = fixture.view.captured()
    retraction = retracts(fixture.view.get(basis), "basis-retracted")
    raw_write(tmp_path, retraction)
    after = gather(
        reopen(tmp_path),
        fixture.proposition,
        key=key,
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    again = gather(
        captured, fixture.proposition, key=key, observations=fixture.availability.observations, **fixture.gather_kwargs
    )
    assert after.key == before.key == key
    assert before.closure().digest() == again.closure().digest() != after.closure().digest()
    assert ("retraction", retraction.id) in after.declared_refs()
    a = after.assessments[0]
    verdict = admit(a, after.runs[a.run], fixture.availability.observations, after.verifications, after.dependencies)
    assert isinstance(verdict, AdmissionRefused) and verdict.reason.startswith("dependency-ineligible")


@pytest.mark.parametrize("kind", ["assessment", "procedure", "proxy-model", "run", "dataset", "verification"])
def test_withheld_calibration_member_is_declared_and_changes_closure(tmp_path, kind):
    from fixtures_cut4 import path_for

    fixture, basis = calibration_fixture(tmp_path)
    key = fixture.assessments[0].key()
    kwargs = {**fixture.gather_kwargs, "key": key, "observations": fixture.availability.observations}
    before = gather(fixture.view, fixture.proposition, **kwargs)
    from test_evaluation import _address

    refs = {"assessment": basis, "run": "run:r", "dataset": _address("a"), "verification": "verification:basis"}
    ref = refs.get(kind) or next(d.id for d in fixture.assessments[0].dependencies if d.id.startswith(kind + ":"))
    path_for(tmp_path, ref).unlink()
    after = gather(reopen(tmp_path), fixture.proposition, **kwargs)
    assert before.closure().digest() != after.closure().digest()
    assert set(after.read_trace) <= after.declared_refs()
    if kind != "verification":
        read = (kind, "r" if kind == "run" else ref)
        assert read in after.declared_refs()
    a = after.assessments[0]
    verdict = admit(a, after.runs[a.run], fixture.availability.observations, after.verifications, after.dependencies)
    assert isinstance(verdict, AdmissionRefused)


def test_wrong_frozen_basis_facet_refuses(tmp_path):
    from fixtures_cut4 import raw_write

    fixture, basis = calibration_fixture(tmp_path)
    before = gather(
        fixture.view,
        fixture.proposition,
        key=fixture.assessments[0].key(),
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    node = fixture.view.get(basis)
    node.facets[stored.ASSESSMENT_FACET]["outcome"] = "refuted"
    raw_write(tmp_path, stored.stamp_semantic_identity(node))
    after = gather(
        reopen(tmp_path),
        fixture.proposition,
        key=fixture.assessments[0].key(),
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    assert after.closure().digest() != before.closure().digest()
    a = after.assessments[0]
    verdict = admit(a, after.runs[a.run], fixture.availability.observations, after.verifications, after.dependencies)
    assert isinstance(verdict, AdmissionRefused) and verdict.reason.startswith("dependency-ineligible")


def all_normative_fixture(tmp_path):
    from fractions import Fraction

    from fixtures_cut3 import MEASUREMENT_RECORDS, TESTING_PROFILE, FixtureRecords
    from fixtures_cut4 import raw_write
    from test_classification_rule import rule
    from test_procedure import procedure
    from test_referent_mapping import mapping

    from beliefs.assumptions import AssumptionInstance
    from beliefs.dependencies import dependency_closure
    from beliefs.identity import v1
    from beliefs.procedure import SameAs, Scale
    from beliefs.proxy_model import ProxyModel, ProxySource, ProxyTarget
    from beliefs.register import AssumptionsRegister
    from beliefs.target import target_projection

    fixture = _fixture(tmp_path, PROPOSITION_REF)
    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    authority = stored.procedure_node(
        procedure(name="Authority", scale=Scale(Fraction(0), Fraction(1), "higher-is-more"))
    )
    follower = stored.procedure_node(procedure(name="Follower", scale=SameAs(authority.id)))
    mapping_node = stored.referent_mapping_node(mapping())
    rule_node = stored.classification_rule_node(rule(classes="testing/level"))
    register = stored.assumptions_register_node(AssumptionsRegister("testing:" + "f" * 64, None, {}))
    from test_procedure import OBS

    proxy = stored.proxy_model_node(
        ProxyModel(
            ProxySource(OBS, follower.id),
            ProxyTarget(OBS, None),
            {},
            AssumptionInstance("testing/proxy-validity", {"record": "fixture", "co_scope": "equal", "dimensions": ""}),
            None,
        )
    )
    for node in (authority, follower, mapping_node, rule_node, register, proxy):
        records.nodes[node.id] = node
        raw_write(tmp_path, node)
    dependencies = dependency_closure(
        (
            *[d.id for d in fixture.assessments[0].dependencies],
            follower.id,
            mapping_node.id,
            rule_node.id,
            register.id,
            proxy.id,
        ),
        records,
        TESTING_PROFILE,
    )
    for ref in ("assessment:a-1", "assessment:a-2"):
        node = fixture.view.get(ref)
        value = stored.assessment_value(node, profile=TESTING_PROFILE)
        node.facets[stored.ASSESSMENT_FACET]["typed"] = v1.encode(
            target_projection(replace(value.target, dependencies=dependencies))
        ).decode()
        raw_write(tmp_path, stored.stamp_semantic_identity(node))
    view = reopen(tmp_path)
    values = tuple(
        stored.assessment_value(view.get(ref), profile=TESTING_PROFILE) for ref in ("assessment:a-1", "assessment:a-2")
    )
    return replace(fixture, view=view, assessments=values), (
        authority,
        follower,
        mapping_node,
        rule_node,
        register,
        proxy,
    )


@pytest.mark.parametrize(
    "kind", ["procedure", "referent-mapping", "classification-rule", "assumptions-register", "proxy-model"]
)
def test_each_normative_kind_is_gathered_and_attempted_when_missing(tmp_path, kind):
    from fixtures_cut4 import path_for

    fixture, nodes = all_normative_fixture(tmp_path)
    key = fixture.assessments[0].key()
    kwargs = {**fixture.gather_kwargs, "key": key, "observations": fixture.availability.observations}
    before = gather(fixture.view, fixture.proposition, **kwargs)
    kinds = {k for k, _ in before.read_trace}
    assert {"procedure", "referent-mapping", "classification-rule", "assumptions-register", "proxy-model"} <= kinds
    missing = next(n for n in nodes if n.kind == kind)
    assert missing.id in before.dependencies.records
    path_for(tmp_path, missing.id).unlink()
    after = gather(reopen(tmp_path), fixture.proposition, **kwargs)
    assert after.closure().digest() != before.closure().digest()
    assert (kind, missing.id) in after.declared_refs()
    assert set(after.read_trace) <= after.declared_refs()


def test_production_graph_uses_calibration_and_model_roots_and_standing(tmp_path, monkeypatch):
    from fixtures_cut4 import raw_write

    from beliefs import belief
    from beliefs.belief import Belief
    from beliefs.evaluation import evaluate_over

    fixture, _basis = calibration_fixture(tmp_path)
    first = fixture.assessments[0]
    node = stored.assessment_node(
        "prediction-2",
        title="Prediction 2",
        spec="prediction-spec-2",
        run="run:prediction-2",
        proposition=fixture.proposition,
        outcome="supported",
        interpretation_rule=first.interpretation_rule,
        target=first.target,
    )
    second = stored.assessment_value(node, profile=fixture.gather_kwargs["profile"])
    for record in (
        stored.run_node("prediction-2", title="Prediction 2", spec=second.spec),
        node,
        stored.verification_node(
            "prediction-2",
            title="Prediction 2",
            assessment=second.identity(),
            assessment_ref=node.id,
            scope="clean-environment",
            verdict="passed",
        ),
    ):
        raw_write(tmp_path, record)
    certifications, graphs = [], []
    actual_certify = belief.certify

    def certify(snapshot, left, right):
        certifications.append((left, right))
        return actual_certify(snapshot, left, right)

    monkeypatch.setattr(belief, "certify", certify)
    from beliefs.policy import BELIEF_V1

    def aggregate(problem):
        graphs.append(problem)
        return BELIEF_V1.aggregate(problem)

    implementation = replace(BELIEF_V1, aggregate=aggregate)
    answer = evaluate_over(
        reopen(tmp_path),
        fixture.proposition,
        **{
            **fixture.kwargs,
            "availability": replace(fixture.availability, implementations={implementation.identity: implementation}),
        },
    )
    assert isinstance(answer, Belief) and answer.value == 1
    from test_evaluation import _address

    assert first.model is not None
    expected = tuple(sorted((first.model, _address("a"))))
    assert certifications == [(expected, expected)]
    assert {vertex.standing for vertex in graphs[-1].vertices} == {"calibrated-model"}
    assert len(graphs[-1].edges) == 1


def test_malformed_calibration_verification_keeps_attempt_declared(tmp_path):
    from fixtures_cut4 import raw_write

    from beliefs.eligibility import Ineligible

    fixture, basis = calibration_fixture(tmp_path)
    node = fixture.view.get("verification:basis")
    node.facets["verification"]["scope"] = "invalid-scope"
    raw_write(tmp_path, stored.stamp_semantic_identity(node))
    inputs = gather(
        reopen(tmp_path),
        fixture.proposition,
        key=fixture.assessments[0].key(),
        observations=fixture.availability.observations,
        **fixture.gather_kwargs,
    )
    assert isinstance(inputs.dependencies.closure.verdicts[basis], Ineligible)
    assert ("verification", node.id) in inputs.read_trace
    assert ("verification", node.id) in inputs.declared_refs()
    assert set(inputs.read_trace) <= inputs.declared_refs()
