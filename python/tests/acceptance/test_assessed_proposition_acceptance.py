"""Certified writer, keyed admission and frozen closure for every standing route."""

import pytest
from fixtures_cut3 import TESTING_PROFILE, freeze_context, spec_draft, spec_rules, typed_estimand
from fixtures_cut4 import reopen
from profiles import pins_for
from test_standing import calibrated_prediction, model_context
from verification_fixtures import evaluation_kwargs, publish_corpus

from beliefs import stored
from beliefs.admission import AdmissionRefused, Admitted, admit
from beliefs.claim import Referent, build_claim
from beliefs.evaluation import claim_view, gather
from beliefs.projection import project_claim
from beliefs.spec import SpecInput, freeze


def _calibrated(writer):
    from dataset_fixtures import dataset

    from beliefs.claim import Member

    def hold_basis(records, node):
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
    return prediction


def _model(writer):
    records, model, claim = model_context()
    writer.add(model)
    proposition = writer.add(stored.proposition_node("model", title="Model", claim=project_claim(claim)))
    spec = freeze(
        spec_draft(
            target=proposition.id,
            estimand=typed_estimand(claim=claim, records=records),
            standing="model",
            model=model.id,
            input_roles=(),
        ),
        held_rules=spec_rules(),
        **{**freeze_context(), "records": records, "claim": claim},
    )
    for entry in spec.assessed_target.dependencies:
        if not writer.read_view.holds(entry.id):
            writer.add(records.read(entry.id))
    writer.add(stored.analysis_spec_node(spec))
    run = writer.add(stored.run_node("model", title="Model", spec=spec.identity))
    return writer.add(
        stored.assessment_node(
            "model",
            title="Model",
            spec=spec.identity,
            run=run.id,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule=spec.interpretation_rule,
            target=spec.assessed_target,
        )
    )


def _inputs(writer, assessment):
    # The view is reopened after each publication; no live writer state supplies evidence.
    view = reopen(writer.root)
    value = stored.assessment_value(assessment, profile=TESTING_PROFILE)
    kwargs = evaluation_kwargs(view)
    inputs = gather(
        view,
        value.proposition,
        key=value.key(),
        observations=kwargs["availability"].observations,
        **{k: v for k, v in kwargs.items() if k != "availability"},
    )
    verdict = admit(
        inputs.assessments[0],
        inputs.runs[value.run],
        kwargs["availability"].observations,
        inputs.verifications,
        inputs.dependencies,
    )
    return view, value, kwargs, inputs, verdict


@pytest.mark.parametrize("route", ["empirical", "model", "calibrated-model"])
def test_real_writer_route_reaches_keyed_admission_and_closure(durable_writer, route):
    writer = durable_writer
    writer.adopt_manifest(profile=pins_for(TESTING_PROFILE))
    assessment = (
        publish_corpus(writer).assessment
        if route == "empirical"
        else _model(writer)
        if route == "model"
        else _calibrated(writer)
    )
    _, value, _, before, verdict = _inputs(writer, assessment)
    assert value.standing == route
    assert isinstance(verdict, AdmissionRefused)
    assert verdict.reason.startswith("not-admitted-verification-state")
    writer.add(
        stored.verification_node(
            route,
            title="Passed",
            assessment=value.identity(),
            assessment_ref=assessment.id,
            scope="clean-environment",
            verdict="passed",
        )
    )
    view, value, kwargs, after, verdict = _inputs(writer, assessment)
    assert isinstance(verdict, Admitted), verdict
    assert before.closure().digest() != after.closure().digest()
    assert set(after.read_trace) <= after.declared_refs()
    result = claim_view(view, value.proposition, **kwargs)
    assert tuple(result.beliefs) == (value.key(),)
    assert result.claim_answer is None
    assert value.key() == before.key == after.key


def test_assessment_target_migration_preserves_run_record_schema(durable_writer):
    from beliefs.identity import v1

    published = publish_corpus(durable_writer)
    node = durable_writer.read_view.get("run:" + published.original.address())
    assert set(node.facets[stored.RUN_FACET]) == {"spec"}
    assert set(node.facets[stored.RUN_CLOSURE_FACET]) == {"projection"}
    projection = v1.decode(node.facets[stored.RUN_CLOSURE_FACET]["projection"].encode())
    assert isinstance(projection, dict)
    assert set(projection) == {"recipe", "result", "occurrence"}
    assert isinstance(projection["recipe"], dict)
    assert not {"estimand", "applicability", "standing", "dependencies", "model"} & set(projection["recipe"])
