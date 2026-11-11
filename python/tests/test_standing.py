"""Declared standing is validated, never inferred from convenient observations."""

from dataclasses import replace
from typing import Any

import pytest
from fixtures_cut3 import (
    MEASUREMENT_RECORDS,
    TESTING_CLAIM,
    TESTING_PROFILE,
    FixtureRecords,
    freeze_context,
    spec_draft,
    spec_rules,
)
from test_procedure import procedure

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.errors import ScienceError
from beliefs.procedure import ModelInputs
from beliefs.spec import freeze
from beliefs.standing import check_standing, check_within_model


def model_context():
    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    node = stored.procedure_node(procedure(kind="testing/model-specification", inputs=ModelInputs((), ())))
    records.nodes[node.id] = node
    claim = build_claim(
        TESTING_PROFILE,
        operator=TESTING_CLAIM.operator,
        roles={**TESTING_CLAIM.roles, "within-model": Referent("testing/procedure-spec", node.id)},
        layer=TESTING_CLAIM.layer,
        polarity="positive",
    )
    return records, node, claim


@pytest.mark.parametrize("mode,accepted", [("observation", True), ("simulation", False), ("annotation", False)])
def test_empirical_needs_observation_mode(mode, accepted):
    draft = spec_draft()
    spec = freeze(
        replace(draft, input_roles=tuple(replace(i, mode=mode) for i in draft.input_roles)),
        held_rules=spec_rules(),
        **freeze_context(),
    )
    if accepted:
        check_standing(
            spec,
            TESTING_CLAIM,
            profile=TESTING_PROFILE,
            records=MEASUREMENT_RECORDS,
            empirical=lambda _: True,
            assessments=lambda _: True,
        )
    else:
        with pytest.raises(ScienceError, match="standing-route-mismatch"):
            check_standing(
                spec,
                TESTING_CLAIM,
                profile=TESTING_PROFILE,
                records=MEASUREMENT_RECORDS,
                empirical=lambda _: True,
                assessments=lambda _: True,
            )


def test_within_model_checks_the_held_procedure_kind():
    records, _node, claim = model_context()
    check_within_model(claim, profile=TESTING_PROFILE, records=records)
    estimator = stored.procedure_node(procedure())
    records.nodes[estimator.id] = estimator
    wrong = build_claim(
        TESTING_PROFILE,
        operator=claim.operator,
        roles={**claim.roles, "within-model": Referent("testing/procedure-spec", estimator.id)},
        layer=claim.layer,
        polarity="positive",
    )
    with pytest.raises(ScienceError, match="standing-route-mismatch"):
        check_within_model(wrong, profile=TESTING_PROFILE, records=records)


def test_model_route_keeps_its_declared_standing_with_observations():
    from fixtures_cut3 import typed_estimand

    records, node, claim = model_context()
    e = typed_estimand(claim=claim, records=records)
    spec = freeze(
        spec_draft(estimand=e, standing="model", model=node.id),
        held_rules=spec_rules(),
        **{**freeze_context(), "records": records, "claim": claim},
    )
    check_standing(
        spec, claim, profile=TESTING_PROFILE, records=records, empirical=lambda _: True, assessments=lambda _: True
    )
    assert spec.standing == "model"
    with pytest.raises(ScienceError, match="standing-route-mismatch"):
        check_standing(
            spec,
            TESTING_CLAIM,
            profile=TESTING_PROFILE,
            records=records,
            empirical=lambda _: True,
            assessments=lambda _: True,
        )


def calibration_context(*, scope=None, source=None, empirical_kind="testing/instrument"):
    from decimal import Decimal

    from fixtures_cut3 import typed_estimand
    from test_procedure import OBS

    from beliefs.applicability import Applicability
    from beliefs.claim import Member
    from beliefs.estimand import Control, MeasuredBinding, OutputSpec, ValueReference
    from beliefs.measurement import Measure
    from beliefs.proxy_model import Calibration, ProxyModel, ProxySource, ProxyTarget

    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    model = (
        source
        if source is not None
        else stored.procedure_node(procedure(kind="testing/model-specification", inputs=ModelInputs((), ())))
    )
    instrument = stored.procedure_node(
        procedure(
            name="Empirical calibration instrument",
            kind=empirical_kind,
            inputs=ModelInputs((), ()) if empirical_kind == "testing/model-specification" else None,
        )
    )
    records.nodes.update({n.id: n for n in (model, instrument)})
    ref = Referent("testing/event", "EX:e")
    claim = build_claim(
        TESTING_PROFILE,
        operator="testing/correlates-with",
        roles={"parties": (Member(ref), Member(Referent("testing/product", "EX:p")))},
        layer="statistical",
        polarity="positive",
    )

    def variable(proc):
        return MeasuredBinding(
            "parties",
            ref,
            Measure(OBS, "testing/electronvolt", None, "ratio", "level", "testing/identity", proc),
            None,
            None,
        )

    app = Applicability({}) if scope is None else scope
    e = typed_estimand(
        claim=claim,
        form="association",
        functional="testing/spearman-correlation",
        bindings={"variables": (("model", variable(model.id)), ("observed", variable(instrument.id)))},
        outputs={"estimate": OutputSpec("dimensionless", "signed-unit-interval")},
        reference=ValueReference(Decimal(0)),
        control=Control("testing/observational", (), "testing/independent-groups", "testing/cohort-enrolment"),
        applicability=app,
        records=records,
    )
    from beliefs.target import AssessedTarget

    assessment = stored.assessment_node(
        "c" * 64,
        title="Calibration",
        spec="s",
        run="run:r",
        proposition="p",
        outcome="supported",
        interpretation_rule="rule",
        target=AssessedTarget(e, app, e.dependencies, None, "empirical"),
    )
    records.nodes[assessment.id] = assessment
    proxy = ProxyModel(
        ProxySource(OBS, model.id),
        ProxyTarget(OBS, None),
        {},
        Calibration(OBS, (assessment.id,), ("rule",), None),
        None,
    )
    return records, model, assessment, proxy


@pytest.mark.parametrize("change", ["standing", "outcome", "rule", "source", "empirical-model"])
def test_calibration_rejects_nonempirical_or_wrong_agreement(change):
    from beliefs.proxy_model import qualify_calibration

    records, model, node, proxy = calibration_context(
        empirical_kind="testing/model-specification" if change == "empirical-model" else "testing/instrument"
    )
    if change in {"standing", "outcome", "rule"}:
        value = stored.assessment_value(node, profile=TESTING_PROFILE)
        from beliefs.identity import v1
        from beliefs.target import target_projection

        if change == "standing":
            # A structurally valid model assessment is not empirical calibration.
            target = replace(value.target, standing="model", model=model.id)
            node.facets["assessment"]["standing"] = "model"
            node.facets["assessment"]["typed"] = v1.encode(target_projection(target)).decode()
        elif change == "outcome":
            node.facets["assessment"]["outcome"] = "refuted"
        else:
            node.facets["assessment"]["interpretation_rule"] = "unlisted"
    elif change == "source":
        proxy = replace(proxy, source=replace(proxy.source, procedure="procedure:" + "f" * 64))
    with pytest.raises(ScienceError, match="calibration"):
        qualify_calibration(proxy, records.read, TESTING_PROFILE)


def test_empirical_two_variable_calibration_is_qualified():
    from beliefs.proxy_model import qualify_calibration

    records, _, _, proxy = calibration_context()
    qualify_calibration(proxy, records.read, TESTING_PROFILE)


def calibrated_prediction(
    *, prediction_scope=None, validity=None, transfer=False, store_basis=None, polarity="positive"
):
    from decimal import Decimal

    from fixtures_cut3 import typed_estimand
    from test_procedure import OBS

    from beliefs.applicability import Applicability
    from beliefs.assumptions import AssumptionInstance
    from beliefs.claim import Member
    from beliefs.classification_rule import ClassificationRule
    from beliefs.estimand import Control, MeasuredBinding, OutputSpec, ValueReference
    from beliefs.measurement import Measure

    assert OBS.aspect is not None
    target = replace(OBS, aspect=replace(OBS.aspect, term="EX:intrinsic")) if transfer else OBS
    source = stored.procedure_node(
        procedure(
            kind="testing/model-specification", inputs=ModelInputs((), ()), yields=tuple(dict.fromkeys((OBS, target)))
        )
    )
    records, model, basis, proxy = calibration_context(source=source)
    if store_basis is not None:
        basis = store_basis(records, basis)
        value = stored.assessment_value(basis, profile=TESTING_PROFILE)
        records.nodes[basis.id] = basis
        proxy = replace(proxy, basis=replace(proxy.basis, assessments=(basis.id,), rules=(value.interpretation_rule,)))
    particulars = {
        "proxy": "calibration",
        "calibrated_observable": "adsorption energy",
        "target_observable": "intrinsic barrier",
    }
    instance = AssumptionInstance("testing/calibration-transfer", particulars)
    proxy = replace(
        proxy,
        target=replace(proxy.target, observable=target),
        validity=validity or {},
        basis=replace(proxy.basis, transfer=instance if transfer else None),
    )
    node = stored.proxy_model_node(proxy)
    records.nodes[node.id] = node
    rule = stored.classification_rule_node(
        ClassificationRule("testing/event", (target,), "Event anchor", None, None, None)
    )
    records.nodes[rule.id] = rule
    ref = Referent("testing/event", "EX:e")
    claim = build_claim(
        TESTING_PROFILE,
        operator="testing/correlates-with",
        roles={"parties": (Member(ref), Member(Referent("testing/product", "EX:p")))},
        layer="statistical",
        polarity=polarity,
    )
    response = MeasuredBinding(
        "parties",
        ref,
        Measure(target, "testing/electronvolt", None, "ratio", "level", "testing/identity", model.id),
        None,
        None,
    )
    named = AssumptionInstance("testing/calibration-transfer", {**particulars, "proxy": node.id})
    callback = lambda id: stored.frozen_assessment_dependency(id, records=records, profile=TESTING_PROFILE)
    app = Applicability(prediction_scope or {})
    e = typed_estimand(
        claim=claim,
        form="quantity",
        functional="testing/peak-power-fraction",
        bindings={"response": response},
        outputs={"estimate": OutputSpec("dimensionless", "unit-interval")},
        reference=ValueReference(Decimal(0)),
        control=Control("testing/observational", (), "testing/independent-groups", "testing/cohort-enrolment"),
        assumptions=((instance, named) if transfer else (named,)),
        calibration=node.id,
        records=records,
        applicability=app,
        assessment_dependency=callback,
    )
    spec = freeze(
        spec_draft(
            target="proposition:prediction",
            estimand=e,
            applicability=app,
            standing="calibrated-model",
            model=model.id,
            input_roles=(),
        ),
        held_rules=spec_rules(),
        **{**freeze_context(), "claim": claim, "records": records},
        assessment_dependency=callback,
    )
    return spec, claim, records, basis.id


@pytest.mark.parametrize(
    "prediction,validity,accepted",
    [
        (None, None, True),
        ((1, 2), (0, 3), True),
        ((0, 3), (1, 2), False),
        ((0, 2), (1, 3), False),
        (None, (1, 2), False),
        ((1, 2), None, True),
    ],
)
def test_calibrated_prediction_scope_must_be_covered(prediction, validity, accepted):
    from fractions import Fraction

    from beliefs.applicability import ScopedRestriction
    from beliefs.restriction import IntervalRestriction

    def scope(bounds):
        return (
            {}
            if bounds is None
            else {
                "testing/follow-up": IntervalRestriction(
                    "testing/hour", Fraction(bounds[0]), Fraction(bounds[1]), True, True
                )
            }
        )

    raw = scope(prediction)
    spec, claim, records, _ = calibrated_prediction(
        prediction_scope={d: ScopedRestriction("generic", r) for d, r in raw.items()}, validity=scope(validity)
    )
    if accepted:
        check_standing(
            spec, claim, profile=TESTING_PROFILE, records=records, empirical=lambda _: False, assessments=lambda _: True
        )
    else:
        with pytest.raises(ScienceError, match="calibration-scope-uncovered"):
            check_standing(
                spec,
                claim,
                profile=TESTING_PROFILE,
                records=records,
                empirical=lambda _: False,
                assessments=lambda _: True,
            )


def test_chemistry_transfer_and_admission_are_explicit_and_do_not_change_the_key():
    from beliefs.record import AssessmentValue

    spec, claim, records, _ = calibrated_prediction(transfer=True)
    kwargs: dict[str, Any] = {"profile": TESTING_PROFILE, "records": records, "empirical": lambda _: False}
    check_standing(spec, claim, **kwargs, assessments=lambda _: True)
    before = AssessmentValue("s", "r", "p", "supported", "rule", spec.assessed_target).key()
    with pytest.raises(ScienceError, match="not admitted"):
        check_standing(spec, claim, **kwargs, assessments=lambda _: False)
    assert AssessmentValue("s", "r", "p", "supported", "rule", spec.assessed_target).key() == before


def test_recursive_calibration_eligibility_is_snapshot_bound_and_needs_verification():
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
    from beliefs.eligibility import AssessmentEligibilityReader, Eligible, Ineligible
    from beliefs.record import RunInput, RunValue
    from beliefs.verification import Verification

    records, _, node, _ = calibration_context()
    value = stored.assessment_value(node, profile=TESTING_PROFILE)
    digest = "sha256:" + "a" * 64
    records.observation_held = lambda digest: digest == "sha256:" + "a" * 64  # pyright: ignore[reportAttributeAccessIssue]
    run = RunValue(
        "run:r", "s", (RunInput("observes", DatasetDeclaration((ResourceDeclaration("observed", digest),))),)
    )
    verification = Verification("verification:v", value.identity(), "clean-environment", "passed")
    earlier = AssessmentEligibilityReader(records, TESTING_PROFILE, lambda _: run, lambda _: (verification,))
    assert earlier(node.id) == Eligible()
    later_records = FixtureRecords()
    later_records.nodes.update(records.nodes)
    later_records.observation_held = records.observation_held
    later_records.retraction_in_force = lambda id: id == node.id
    later = AssessmentEligibilityReader(later_records, TESTING_PROFILE, lambda _: run, lambda _: (verification,))
    assert isinstance(later(node.id), Ineligible)
    assert earlier(node.id) == Eligible()
    assert isinstance(
        AssessmentEligibilityReader(records, TESTING_PROFILE, lambda _: run, lambda _: ())(node.id), Ineligible
    )


def test_recursive_eligibility_refuses_a_changed_frozen_basis_facet():
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
    from beliefs.eligibility import AssessmentEligibilityReader, Ineligible
    from beliefs.record import AssessmentValue, RunInput, RunValue
    from beliefs.verification import Verification

    spec, _, records, basis_id = calibrated_prediction()
    value = AssessmentValue("s", "r", "p", "supported", spec.interpretation_rule, spec.assessed_target)
    node = stored.assessment_node(
        value.identity(),
        title="Prediction",
        spec="s",
        run="run:r",
        proposition="p",
        outcome="supported",
        interpretation_rule=value.interpretation_rule,
        target=value.target,
    )
    records.nodes[node.id] = node
    records.nodes[basis_id].facets["assessment"]["outcome"] = "refuted"
    stored.stamp_semantic_identity(records.nodes[basis_id])
    records.observation_held = lambda digest: True  # pyright: ignore[reportAttributeAccessIssue]
    run = RunValue(
        "run:r", "s", (RunInput("observes", DatasetDeclaration((ResourceDeclaration("x", "sha256:" + "a" * 64),))),)
    )
    reader = AssessmentEligibilityReader(
        records,
        TESTING_PROFILE,
        lambda _: run,
        lambda id: (Verification("verification:v", id, "clean-environment", "passed"),),
    )
    result = reader(node.id)
    assert isinstance(result, Ineligible) and "frozen" in result.reason


@pytest.mark.parametrize("mode", ["observation", "simulation", "annotation"])
def test_real_writer_enforces_spec_evidence_mode(certified_work, mode):
    from authority import FULL
    from verification_fixtures import publish_corpus

    from beliefs.errors import EligibilityUnmet
    from beliefs.root import init_corpus_root, open_corpus
    from beliefs.spec import SpecInput

    root = certified_work / "standing"
    init_corpus_root(root, authority=FULL)
    writer = open_corpus(root, authority=FULL, profile=TESTING_PROFILE)
    published = publish_corpus(writer)
    prior = published.frozen
    draft = spec_draft(
        target=published.proposition.id,
        input_roles=tuple(SpecInput(i.role, i.dataset, mode) for i in prior.input_roles),
    )
    spec = freeze(draft, held_rules=spec_rules(), **freeze_context())
    if not writer.read_view.holds("analysis-spec:" + spec.identity):
        writer.add(stored.analysis_spec_node(spec))
    observes = stored.inputs_of(writer.read_view.get("run:" + published.original.address()), stored.OBSERVES)
    run = writer.add(stored.run_node("mode-run", title="mode", spec=spec.identity, observes=observes))
    node = stored.assessment_node(
        "mode-assessment",
        title="mode",
        spec=spec.identity,
        run=run.id,
        proposition=published.proposition.id,
        outcome="supported",
        interpretation_rule=spec.interpretation_rule,
        target=spec.assessed_target,
    )
    if mode == "observation":
        assert writer.add(node).id == node.id
    else:
        with pytest.raises(EligibilityUnmet, match="standing-route-mismatch"):
            writer.add(node)


def test_real_writer_and_corpus_check_refuse_an_estimator_as_a_model(certified_work):
    from authority import FULL
    from fixtures_cut4 import raw_write, reopen

    from beliefs.corpus import corpus_check
    from beliefs.errors import EligibilityUnmet
    from beliefs.projection import project_claim
    from beliefs.root import init_corpus_root, open_corpus

    root = certified_work / "model-kind"
    init_corpus_root(root, authority=FULL)
    writer = open_corpus(root, authority=FULL, profile=TESTING_PROFILE)
    node = writer.add(stored.procedure_node(procedure()))
    claim = build_claim(
        TESTING_PROFILE,
        operator=TESTING_CLAIM.operator,
        roles={**TESTING_CLAIM.roles, "within-model": Referent("testing/procedure-spec", node.id)},
        layer=TESTING_CLAIM.layer,
        polarity="positive",
    )
    proposition = stored.proposition_node("model", title="model", claim=project_claim(claim))
    with pytest.raises(EligibilityUnmet, match="standing-route-mismatch"):
        writer.add(proposition)
    raw_write(root, proposition)
    assert any(
        f.code == "standing-unmet" and f.ref == proposition.id for f in corpus_check(reopen(root), TESTING_PROFILE)
    )


@pytest.mark.parametrize("role,accepted", [("reads", False), ("transforms", True)])
def test_real_writer_matches_authored_spec_input_roles(certified_work, role, accepted):
    from authority import FULL
    from verification_fixtures import publish_corpus

    from beliefs.errors import EligibilityUnmet
    from beliefs.root import init_corpus_root, open_corpus

    root = certified_work / "input-modes"
    init_corpus_root(root, authority=FULL)
    writer = open_corpus(root, authority=FULL, profile=TESTING_PROFILE)
    published = publish_corpus(writer)
    spec = published.frozen
    observed = stored.inputs_of(writer.read_view.get("run:" + published.original.address()), stored.OBSERVES)
    run = writer.add(
        stored.run_node("extra-role", title="extra", spec=spec.identity, observes=observed, **{role: observed})
    )
    node = stored.assessment_node(
        "extra-role",
        title="extra",
        spec=spec.identity,
        run=run.id,
        proposition=published.proposition.id,
        outcome="supported",
        interpretation_rule=spec.interpretation_rule,
        target=spec.assessed_target,
    )
    if accepted:
        assert writer.add(node).id == node.id
    else:
        with pytest.raises(EligibilityUnmet, match="standing-route-mismatch.*input"):
            writer.add(node)


def test_calibrated_prediction_mints_and_later_basis_retraction_changes_only_eligibility(certified_work):
    from authority import FULL
    from dataset_fixtures import dataset
    from test_eligibility import retract

    from beliefs.claim import Member
    from beliefs.corpus import _CapturedCheckView, eligibility_outcome
    from beliefs.projection import project_claim
    from beliefs.root import init_corpus_root, open_corpus
    from beliefs.spec import SpecInput

    root = certified_work / "calibrated"
    init_corpus_root(root, authority=FULL)
    writer = open_corpus(root, authority=FULL, profile=TESTING_PROFILE)
    basis_node = None

    def hold_basis(records, node):
        nonlocal basis_node
        from fixtures_cut3 import ESTIMATOR_PROCEDURE

        basis_value = stored.assessment_value(node, profile=TESTING_PROFILE)
        for id in {d.id for d in basis_value.dependencies} | {ESTIMATOR_PROCEDURE}:
            held = records.read(id)
            if not writer.read_view.holds(held.id):
                writer.add(held)
        ref = Referent("testing/event", "EX:e")
        claim = build_claim(
            TESTING_PROFILE,
            operator="testing/correlates-with",
            roles={"parties": (Member(ref), Member(Referent("testing/product", "EX:p")))},
            layer="statistical",
            polarity="positive",
        )
        proposition = writer.add(stored.proposition_node("calibration", title="agreement", claim=project_claim(claim)))
        observed = writer.add(
            dataset(
                "calibration",
                empirical_observation={"locator": "instrument:fixture", "attested_by": writer.authority.actor},
            )
        )
        value = stored.assessment_value(node, profile=TESTING_PROFILE)
        spec = freeze(
            spec_draft(
                target=proposition.id,
                estimand=value.estimand,
                applicability=value.applicability,
                input_roles=(SpecInput("observes", observed.id, "observation"),),
            ),
            held_rules=spec_rules(),
            **{**freeze_context(), "records": records, "claim": claim},
        )
        writer.add(stored.analysis_spec_node(spec))
        run = writer.add(stored.run_node("calibration", title="agreement", spec=spec.identity, observes=(observed.id,)))
        from beliefs.record import AssessmentValue

        identity = AssessmentValue(
            spec.identity, "calibration", proposition.id, "supported", spec.interpretation_rule, spec.assessed_target
        ).identity()
        result = writer.add(
            stored.assessment_node(
                identity,
                title="agreement",
                spec=spec.identity,
                run=run.id,
                proposition=proposition.id,
                outcome="supported",
                interpretation_rule=spec.interpretation_rule,
                target=spec.assessed_target,
            )
        )
        actual = stored.assessment_value(result, profile=TESTING_PROFILE)
        writer.add(
            stored.verification_node(
                "calibration",
                title="passed",
                assessment=actual.identity(),
                assessment_ref=result.id,
                scope="clean-environment",
                verdict="passed",
            )
        )
        basis_node = result
        return result

    spec, claim, records, _ = calibrated_prediction(transfer=True, store_basis=hold_basis)
    writer.add(stored.proposition_node("prediction", title="prediction", claim=project_claim(claim)))
    for dependency in spec.assessed_target.dependencies:
        if not writer.read_view.holds(dependency.id):
            writer.add(records.read(dependency.id))
    writer.add(stored.analysis_spec_node(spec))
    run = writer.add(stored.run_node("prediction", title="model execution", spec=spec.identity))
    prediction = writer.add(
        stored.assessment_node(
            "prediction",
            title="prediction",
            spec=spec.identity,
            run=run.id,
            proposition=spec.target,
            outcome="supported",
            interpretation_rule=spec.interpretation_rule,
            target=spec.assessed_target,
        )
    )
    earlier = _CapturedCheckView(tuple(writer.read_view.iter_stored()))
    key = stored.assessment_value(prediction, profile=TESTING_PROFILE).key()
    assert eligibility_outcome(earlier, prediction, TESTING_PROFILE) is None
    assert basis_node is not None
    retract(writer, basis_node)
    later = eligibility_outcome(writer.read_view, prediction, TESTING_PROFILE)
    assert later is not None and "not admitted" in later.reason
    assert eligibility_outcome(earlier, prediction, TESTING_PROFILE) is None
    assert stored.assessment_value(prediction, profile=TESTING_PROFILE).key() == key


def test_same_claim_record_alias_keeps_the_frozen_target(certified_work):
    from authority import FULL
    from verification_fixtures import publish_corpus

    from beliefs.projection import project_claim
    from beliefs.root import init_corpus_root, open_corpus

    root = certified_work / "claim-alias"
    init_corpus_root(root, authority=FULL)
    writer = open_corpus(root, authority=FULL, profile=TESTING_PROFILE)
    published = publish_corpus(writer)
    alias = writer.add(stored.proposition_node("same-claim", title="same claim", claim=project_claim(TESTING_CLAIM)))
    value = stored.assessment_value(published.assessment, profile=TESTING_PROFILE)
    twin = writer.add(
        stored.assessment_node(
            "same-claim",
            title="same target",
            spec=value.spec,
            run="run:" + value.run,
            proposition=alias.id,
            outcome=value.outcome,
            interpretation_rule=value.interpretation_rule,
            target=value.target,
        )
    )
    assert stored.assessment_value(twin, profile=TESTING_PROFILE).key() == value.key()
