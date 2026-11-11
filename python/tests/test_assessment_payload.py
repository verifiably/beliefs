"""Numerical validation uses output domains and explicit parameter names."""

from decimal import Decimal as D

import pytest
from fixtures_cut3 import typed_estimand, typed_target
from test_estimand import context as context  # noqa: PLC0414 — shared pytest fixture

from beliefs.assessment_payload import (
    Covariance,
    CurvePoint,
    Interval,
    StandardError,
    check_outputs,
    payload_from_projection,
    payload_projection,
)
from beliefs.errors import MalformedRecord
from beliefs.record import AssessmentValue


def test_named_payload_roundtrip_and_absence():
    e = typed_estimand()
    estimates = {"estimate": D(1)}
    uncertainty = {"estimate": Interval(D(0), D(2), D(".95"))}
    body = payload_projection(estimates, uncertainty, {})
    assert payload_from_projection(body, e) == (estimates, uncertainty, {})
    assert payload_projection({}, None, {}) == {}
    assert (
        AssessmentValue("s", "r", "p", "supported", "rule", typed_target(), estimates, uncertainty).estimates
        == estimates
    )


@pytest.mark.parametrize(
    "estimates,uncertainty",
    [
        ({"other": D(1)}, None),
        ({"estimate": float("nan")}, None),
        ({"estimate": D("NaN")}, None),
        ({}, {"estimate": StandardError(D(1))}),
        ({"estimate": D(3)}, {"estimate": Interval(D(0), D(2), D(".95"))}),
        ({"estimate": D(1)}, {"estimate": StandardError(D(1))}),
        ({"estimate": D(1)}, {"other": Interval(D(0), D(2), D(".95"))}),
    ],
)
def test_outputs_refuse_malformed_values(estimates, uncertainty):
    with pytest.raises(MalformedRecord):
        check_outputs(estimates, uncertainty, typed_estimand())


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: Interval(D(2), D(1), D(".95")),
        lambda: Interval(D(0), D(1), D(0)),
        lambda: Interval(D(0), D(1), D(1)),
        lambda: StandardError(D(-1)),
        lambda: Covariance(("a",), ((D(1),),)),
        lambda: Covariance(("a", "b"), ((D(1), D(2)), (D(3), D(1)))),
        lambda: Covariance(("a", "b"), ((D(-1), D(0)), (D(0), D(1)))),
        lambda: CurvePoint(D("Infinity"), D(1), None),
    ],
)
def test_malformed_uncertainty_and_curves(constructor):
    with pytest.raises(MalformedRecord):
        constructor()


def test_covariance_orders_both_axes_without_claiming_psd():
    value = Covariance(("z", "a"), ((D(4), D(3)), (D(3), D(1))))
    assert value.parameters == ("a", "z")
    assert value.matrix == ((D(1), D(3)), (D(3), D(4)))


@pytest.mark.parametrize(
    "functional,domain,bad",
    [
        ("probability-of-superiority", "unit-interval", D("1.1")),
        ("ratio-of-means", "positive", D(0)),
    ],
)
def test_output_domains_govern_payload(functional, domain, bad):
    from beliefs.estimand import OutputSpec, ValueReference

    e = typed_estimand(
        functional="testing/" + functional,
        outputs={"estimate": OutputSpec("dimensionless", domain)},
        reference=ValueReference(D(".5") if domain == "unit-interval" else D(1)),
    )
    with pytest.raises(MalformedRecord):
        check_outputs({"estimate": bad}, None, e)


def test_joint_payload_requires_all_outputs_and_canonical_covariance():
    from fixtures_cut3 import RESPONSE

    from beliefs.estimand import OutputSpec, ValueReference

    e = typed_estimand(
        form="law-parameters",
        functional="testing/arrhenius",
        bindings={"response": RESPONSE, "independent": (("temperature", RESPONSE),)},
        outputs={
            "Ea": OutputSpec("independent", "real", "testing/energy", "testing/electronvolt"),
            "lnA": OutputSpec("response-log-level", "real"),
        },
        reference={"Ea": ValueReference(D(0)), "lnA": ValueReference(D(0))},
        uncertainty="covariance",
    )
    estimates = {"Ea": D(1), "lnA": D(2)}
    uncertainty = Covariance(("lnA", "Ea"), ((D(4), D(2)), (D(2), D(1))))
    body = payload_projection(estimates, uncertainty, {})
    assert payload_from_projection(body, e) == (estimates, uncertainty, {})
    with pytest.raises(MalformedRecord):
        check_outputs({"Ea": D(1)}, None, e)
    with pytest.raises(MalformedRecord):
        check_outputs(estimates, Covariance(("Ea", "other"), ((D(1), D(0)), (D(0), D(1)))), e)


def test_event_curves_validate_every_point_and_window_payloads_stay_scalar(context):
    from fixtures_cut3 import RESPONSE
    from test_estimand import build

    from beliefs.assessment_payload import check_payload
    from beliefs.claim import Referent
    from beliefs.estimand import LagBinding, RoleAnchor

    e = build(
        context,
        form="event-locked",
        functional="testing/window-difference-against-control",
        bindings={
            "response": RESPONSE,
            "anchor": RoleAnchor("cause", None, Referent("testing/entity", "EX:a")),
            "lag": LagBinding("testing/hour", ()),
        },
    )
    curves = {"estimate": (CurvePoint(D(0), D(1), Interval(D(0), D(2), D(".95"))), CurvePoint(D(1), D(2), None))}
    assert payload_from_projection(payload_projection({}, None, curves), e) == ({}, None, curves)
    with pytest.raises(MalformedRecord):
        check_payload(e, {}, None, {"estimate": tuple(reversed(curves["estimate"]))})
    with pytest.raises(MalformedRecord):
        check_payload(e, {}, None, {"other": curves["estimate"]})
    with pytest.raises(MalformedRecord):
        check_payload(typed_estimand(), {}, None, curves)
