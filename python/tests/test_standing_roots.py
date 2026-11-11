"""Independence follows declared standing, never computational repetition."""

from dataclasses import replace
from types import MappingProxyType

import pytest
from fixtures_cut3 import (
    MEASUREMENT_RECORDS,
    TESTING_CLAIM,
    TESTING_PROFILE,
    FixtureRecords,
    freeze_context,
    spec_draft,
    spec_rules,
    typed_estimand,
)
from test_belief import DATASET_A, DATASET_B
from test_procedure import procedure
from test_standing import calibrated_prediction

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.dataset import dataset_address
from beliefs.eligibility import ClosureEligibility
from beliefs.errors import DependencyNotHeld
from beliefs.lineage import LineageSnapshot, certify
from beliefs.procedure import ModelInputs, procedure_from_stored
from beliefs.record import AssessmentValue, RunInput, RunValue
from beliefs.spec import freeze


def evidence(*, records=None, assessments=None, runs=None):
    from beliefs.evidence import DependencyEvidence

    return DependencyEvidence(
        ClosureEligibility(MappingProxyType({}), ()),
        {} if records is None else records,
        {} if assessments is None else assessments,
        {} if runs is None else runs,
    )


@pytest.mark.parametrize("left,right", [((), ("x",)), (("x",), ()), ((), ())])
def test_no_roots_cannot_certify(left, right):
    result = certify(LineageSnapshot(("x",), {}, {}), left, right)
    assert result.state == "not-certified"
    assert "no-roots" in result.findings


def test_shared_model_and_calibration_roots():
    from beliefs.belief import standing_roots

    inputs = ModelInputs(("sha256:" + "d" * 64,), ("sha256:" + "c" * 64,))
    model = stored.procedure_node(procedure(kind="testing/model-specification", inputs=inputs))
    records = FixtureRecords()
    records.nodes.update(MEASUREMENT_RECORDS.nodes)
    records.nodes[model.id] = model
    claim = build_claim(
        TESTING_PROFILE,
        operator=TESTING_CLAIM.operator,
        roles={**TESTING_CLAIM.roles, "within-model": Referent("testing/procedure-spec", model.id)},
        layer=TESTING_CLAIM.layer,
        polarity="positive",
    )
    spec = freeze(
        spec_draft(standing="model", model=model.id, estimand=typed_estimand(claim=claim, records=records)),
        held_rules=spec_rules(),
        **{**freeze_context(), "records": records, "claim": claim},
    )
    first = AssessmentValue("s-a", "a", "p", "supported", "rule", spec.assessed_target)
    second = replace(first, spec="s-b", run="b")
    run_a = RunValue("run:a", "s-a", (RunInput("observes", DATASET_A),))
    run_b = RunValue("run:b", "s-b", (RunInput("observes", DATASET_B),))
    supplied = evidence(records={model.id: procedure_from_stored(model)})
    expected = tuple(sorted((model.id, *inputs.datasets, *inputs.code)))
    assert standing_roots(first, run_a, supplied) == expected
    assert standing_roots(second, run_b, supplied) == expected
    with pytest.raises(DependencyNotHeld, match="model procedure"):
        standing_roots(first, run_a, evidence())
    assert certify(LineageSnapshot(expected, {}, {}), expected, expected).state == "shared-source"

    calibrated, _, held, _ = calibrated_prediction(polarity="negative")
    basis_ref = next(ref for ref in held.nodes if ref.startswith("assessment:"))
    basis = stored.assessment_value(held.read(basis_ref), profile=TESTING_PROFILE)
    calibration_run = RunValue(stored.typed_ref("run", basis.run), basis.spec, (RunInput("observes", DATASET_A),))
    prediction = replace(first, target=calibrated.assessed_target)
    from beliefs.dependencies import read_record

    supplied = evidence(
        records={d.id: read_record(held, d.id) for d in prediction.dependencies if not d.id.startswith("assessment:")},
        assessments={basis_ref: basis},
        runs={calibration_run.ref: calibration_run},
    )
    with pytest.raises(DependencyNotHeld, match="assessment or run"):
        standing_roots(prediction, run_b, replace(supplied, runs={}))
    roots = standing_roots(prediction, run_b, supplied)
    assert calibrated.model is not None
    address = dataset_address(DATASET_A)
    assert address is not None
    assert roots == tuple(sorted((calibrated.model, address)))
    assert dataset_address(DATASET_B) not in roots
    assert basis.estimand.claim != prediction.estimand.claim
    assert standing_roots(basis, calibration_run, supplied) == (address,)


def test_dependency_evidence_copies_supplied_maps():
    records = {}
    value = evidence(records=records)
    records["later"] = procedure()
    assert not value.records
    with pytest.raises(TypeError):
        value.records["later"] = procedure()  # pyright: ignore[reportIndexIssue]
