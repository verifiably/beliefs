"""Diagnostics expose payload/certificate/standing gaps without scientific admission."""

import json
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
from typing import Any, cast

import pytest
from candidate_contracts import spectral_profile
from test_convert import snapshot

from beliefs import errors, stored
from beliefs.assessment_payload import Interval, payload_from_projection, payload_projection
from beliefs.claim import Referent, build_claim
from beliefs.comparability import Convertible, NotConvertible, OutputTyping, convert, functional_properties
from beliefs.estimand import ValueReference, estimand_from_stored, estimand_projection
from beliefs.measurement import Coordinates
from beliefs.procedure import procedure_from_stored
from beliefs.proxy_model import proxy_from_stored, qualify_calibration
from beliefs.spec import revise
from beliefs.standing import check_standing, check_within_model

from .spectral_case import build_quantity, fixture_rules, freeze_quantity, spectral_case
from .spectral_diagnostics import diagnostic_contract, diagnostic_estimand, model_case

RESULTS = Path(__file__).resolve().parents[3] / "fixtures/spectral-example-results.json"


@pytest.fixture(scope="module")
def profile(base_contract):
    return spectral_profile(base_contract, extra=(diagnostic_contract(base_contract),))


def test_joint_law_requires_measured_independent(profile):
    with pytest.raises(
        errors.EstimandError, match="independent is a nonempty ordered named tuple of measured bindings"
    ):
        diagnostic_estimand(spectral_case(profile), form="law-parameters")


def test_joint_payload_refuses_partial_uncertainty(profile):
    s = spectral_case(profile)
    diagnostic = diagnostic_estimand(s, form="quantity")
    estimates = {"rho": D("0.5"), "exponent": D("-1.5")}
    partial_joint_payload = payload_projection(estimates, {"exponent": Interval(D(-2), D(-1), D("0.95"))}, {})
    with pytest.raises(errors.MalformedRecord, match="uncertainty names must match estimates"):
        payload_from_projection(partial_joint_payload, diagnostic)
    absent = payload_from_projection(payload_projection(estimates, None, {}), diagnostic)
    assert absent == (estimates, None, {})
    complete = {"rho": Interval(D(0), D(1), D("0.95")), "exponent": Interval(D(-2), D(-1), D("0.95"))}
    assert payload_from_projection(payload_projection(estimates, complete, {}), diagnostic) == (estimates, complete, {})


def test_diagnostic_certificate_is_not_spectral_support(profile):
    s = spectral_case(profile)
    a = Coordinates(s.measure.observable.quantity_kind, None, s.measure.scale, "level", "general/identity")
    b = replace(a, transformation="spectral-checks/monotone-increasing")
    snap = snapshot(s.case.records, profile=profile)
    diagnostic = functional_properties(profile.functionals["spectral-checks/joint-payload"])
    result = convert(
        a,
        b,
        binding="certified",
        functional=diagnostic,
        output=OutputTyping("dimensionless", "unit-interval"),
        snapshot=snap,
    )
    assert isinstance(result, Convertible) and result.map.cls == "strictly-increasing"
    for functional in ("general/peak-power-fraction", "general/signed-aperiodic-exponent"):
        props = functional_properties(profile.functionals[functional])
        result = convert(
            a,
            b,
            binding="certified",
            functional=props,
            output=OutputTyping("dimensionless", props.domain),
            snapshot=snap,
        )
        assert isinstance(result, NotConvertible) and result.reason == "transformation"


def test_simulation_inputs_cannot_establish_empirical_standing(profile):
    s = spectral_case(profile)
    spec = freeze_quantity(
        s, build_quantity(s, functional="general/peak-power-fraction", reference=ValueReference(D(0)))
    )
    assert any(i.role == "reads" and i.mode == "simulation" for i in spec.input_roles)
    with pytest.raises(
        errors.StandingRefused, match="empirical needs an observes input of mode observation with empirical standing"
    ):
        check_standing(
            spec, s.claim, profile=profile, records=s.case.records, empirical=lambda _: True, assessments=lambda _: True
        )


def test_model_route_requires_held_model_kind(profile):
    spec, claim, records, basis = model_case(profile)
    assert basis is None and spec.standing == "model"
    check_standing(
        spec, claim, profile=profile, records=records, empirical=lambda _: False, assessments=lambda _: False
    )
    model = procedure_from_stored(records.nodes[spec.model])
    wrong = stored.procedure_node(replace(model, kind="general/estimator", inputs=None))
    records.nodes[wrong.id] = wrong
    wrong_claim = build_claim(
        profile,
        operator=claim.operator,
        roles={**claim.roles, "within-model": Referent("spectral-checks/procedure-spec", wrong.id)},
        form="polar",
        layer="statistical",
    )
    with pytest.raises(errors.StandingRefused, match="requires a model-specification procedure kind"):
        check_within_model(wrong_claim, profile=profile, records=records)


def test_calibrated_model_needs_eligible_basis(profile):
    spec, claim, records, basis = model_case(profile, calibrated=True)
    assert spec.standing == "calibrated-model" and basis is not None
    value = stored.assessment_value(records.nodes[basis], profile=profile)
    assert value.standing == "empirical" and value.outcome == "supported"  # Synthetic typing apparatus only.
    proxy = proxy_from_stored(records.nodes[spec.estimand.calibration])
    qualify_calibration(proxy, records.read, profile)
    assert any(
        a.kind == "spectral-checks/calibration-transfer" and a.particulars["proxy"] == spec.estimand.calibration
        for a in spec.estimand.assumptions
    )
    with pytest.raises(errors.StandingRefused, match="calibration assessment is not admitted and eligible"):
        check_standing(
            spec, claim, profile=profile, records=records, empirical=lambda _: False, assessments=lambda _: False
        )
    check_standing(spec, claim, profile=profile, records=records, empirical=lambda _: False, assessments=lambda _: True)


def test_calibrated_model_missing_transfer_refuses(profile):
    spec, claim, records, _ = model_case(profile, calibrated=True)
    body = cast(dict[str, Any], estimand_projection(spec.estimand))
    body["assumptions"] = [a for a in body["assumptions"] if a["kind"] != "spectral-checks/calibration-transfer"]
    e = estimand_from_stored(body, profile=profile)
    s = spectral_case(profile)
    changed = revise(
        spec,
        edits={"estimand": e},
        held_rules=fixture_rules(),
        recorded_failures=frozenset(),
        rule_procedures={spec.interpretation_rule: s.estimator},
        profile=profile,
        claim=claim,
        records=records,
        assessment_dependency=lambda id: stored.frozen_assessment_dependency(id, records=records, profile=profile),
        series_evidence=s.case.evidence(),
    )
    with pytest.raises(errors.StandingRefused, match="calibration-transfer must name the proxy"):
        check_standing(
            changed, claim, profile=profile, records=records, empirical=lambda _: False, assessments=lambda _: True
        )


def test_calibrated_model_proxy_model_mismatch_refuses(profile):
    spec, claim, records, _ = model_case(profile, calibrated=True)
    model = procedure_from_stored(records.nodes[spec.model])
    other = stored.procedure_node(replace(model, name="Another synthetic model"))
    records.nodes[other.id] = other
    s = spectral_case(profile)
    changed = revise(
        spec,
        edits={"model": other.id},
        held_rules=fixture_rules(),
        recorded_failures=frozenset(),
        rule_procedures={spec.interpretation_rule: s.estimator},
        profile=profile,
        claim=claim,
        records=records,
        assessment_dependency=lambda id: stored.frozen_assessment_dependency(id, records=records, profile=profile),
        series_evidence=s.case.evidence(),
    )
    with pytest.raises(errors.StandingRefused, match="calibration source model or target observable disagrees"):
        check_standing(
            changed, claim, profile=profile, records=records, empirical=lambda _: False, assessments=lambda _: True
        )


@pytest.mark.parametrize(
    "case,applicable,executed", [("executed", True, True), ("inapplicable", False, False), ("failed", True, False)]
)
def test_source_shaped_status_and_coupling_stay_distinct(case, applicable, executed):
    data = json.loads(RESULTS.read_text())
    row = data["instrument_results"][case]
    assert row["applicable"] is applicable and row["executed"] is executed
    assert row["interpretation"] == "descriptive"
    assert row["applicability_reason"] == ("ok" if applicable else "too-short-after-margin")
    if executed:
        assert row["value"] == data["raw_spectral_parameterization"]["rho"]
        assert row["aux"] == {k: v for k, v in data["raw_spectral_parameterization"].items() if k != "rho"}
        assert row["execution_reason"] == "ok"
    else:
        assert row["value"] is None and row["aux"] == {}
        assert row["execution_reason"] == ("ValueError" if applicable else "not-run")
    coupling = data["coupling"]
    assert coupling["surrogate"] == "epoch-shuffle"
    assert coupling["pac_mi"]["value"] == "0.02"
    assert coupling["waveform_shape"]["aux"]["n_cycles"] == 8
    assert (
        coupling["license"]
        == "Illustrative alignment under a named surrogate; no causal edge, independent oscillators or absence claim."
    )
