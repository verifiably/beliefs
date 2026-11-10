"""Proxy models bind calibrated or assumed mappings and structural crosswalk rules."""

from dataclasses import replace
from fractions import Fraction
from typing import Any

import pytest
from test_procedure import AID, OBS, PID, node_for

from beliefs.assumptions import AssumptionInstance
from beliefs.errors import MalformedRecord
from beliefs.identity import v1
from beliefs.proxy_model import (
    Calibration,
    Conversion,
    Crosswalk,
    Error,
    ProxyModel,
    ProxySource,
    ProxyTarget,
    proxy_from_stored,
    proxy_identity,
    proxy_projection,
)

ASSUMPTION = AssumptionInstance("testing/proxy-validity", {"record": "proxy"})
RULE = "beliefs/outcome-file/v1"
OTHER = replace(OBS, aspect=None)
CROSSWALK = Crosswalk(
    {"cohort": "adults"}, Conversion("affine", Fraction(-2), Fraction(10)), Error("standard-error", Fraction(14, 10))
)


def proxy(**changes):
    return ProxyModel(
        **(
            {
                "source": ProxySource(OBS, PID),
                "target": ProxyTarget(OBS, None),
                "validity": {},
                "basis": ASSUMPTION,
                "crosswalk": None,
            }
            | changes
        )
    )


def test_identity_is_content_addressed():
    value = proxy()
    assert proxy_identity(value) == proxy_identity(proxy())
    assert proxy_identity(value) == "proxy-model:" + v1.digest("science.proxy-model.v1", proxy_projection(value))
    assert proxy_identity(value) != proxy_identity(replace(value, target=ProxyTarget(OTHER, None)))


@pytest.mark.parametrize(
    "extras",
    [
        {},
        {"basis": Calibration(OBS, (AID,), (RULE,), None)},
        {"target": ProxyTarget(None, PID), "crosswalk": CROSSWALK},
        {"target": ProxyTarget(OTHER, None), "basis": Calibration(OBS, (AID,), (RULE,), ASSUMPTION)},
    ],
)
def test_projection_has_no_nulls_and_round_trips(extras):
    value = proxy(**extras)
    facet: dict[str, Any] = proxy_projection(value)
    v1.encode(facet)
    assert proxy_from_stored(node_for("proxy-model", proxy_identity(value), facet)) == value


def test_from_stored_refuses_a_non_canonical_facet_and_a_wrong_id():
    value = proxy()
    facet: dict[str, Any] = proxy_projection(value)
    for bad in (
        facet | {"crosswalk": None},
        facet | {"extra": "x"},
        facet | {"basis": {}},
        facet | {"basis": {"assumption": {"kind": "testing/x", "particulars": {}}, "calibration": {}}},
        facet | {"source": {"observable": {"bad": "value"}, "procedure": PID}},
    ):
        with pytest.raises(MalformedRecord):
            proxy_from_stored(node_for("proxy-model", proxy_identity(value), bad))
    with pytest.raises(MalformedRecord):
        proxy_from_stored(node_for("proxy-model", "proxy-model:" + "a" * 64, facet))


def test_crosswalk_present_exactly_for_scale_of():
    for changes in ({"crosswalk": CROSSWALK}, {"target": ProxyTarget(None, PID)}):
        with pytest.raises(MalformedRecord):
            proxy(**changes)
    assert proxy(target=ProxyTarget(None, PID), crosswalk=CROSSWALK).crosswalk == CROSSWALK
    for observable, scale_of in ((None, None), (OBS, PID)):
        with pytest.raises(MalformedRecord):
            ProxyTarget(observable, scale_of)


def test_transfer_presence_rule():
    for target, transfer in ((OBS, ASSUMPTION), (OTHER, None)):
        with pytest.raises(MalformedRecord):
            proxy(target=ProxyTarget(target, None), basis=Calibration(OBS, (AID,), (RULE,), transfer))
    assert proxy(basis=Calibration(OBS, (AID,), (RULE,), None))
    assert proxy(target=ProxyTarget(OTHER, None), basis=Calibration(OBS, (AID,), (RULE,), ASSUMPTION))
    assert proxy(target=ProxyTarget(None, PID), crosswalk=CROSSWALK, basis=Calibration(OTHER, (AID,), (RULE,), None))


def test_references():
    value = proxy(target=ProxyTarget(None, PID), crosswalk=CROSSWALK, basis=Calibration(OBS, (AID,), (RULE,), None))
    assert set(value.references) == {PID, AID}
    assert proxy().references == (PID,)


@pytest.mark.parametrize(
    "factory,args",
    [
        (ProxySource, (OBS, "procedure:bad")),
        (ProxyTarget, (None, "bad")),
        (Calibration, (OBS, (PID,), (RULE,), None)),
        (Calibration, (OBS, (AID,), ("",), None)),
        (Conversion, ("unknown", Fraction(1), None)),
        (Conversion, ("affine", Fraction(1), None)),
        (Conversion, ("multiplicative", Fraction(1), Fraction(0))),
        (Conversion, ("affine", Fraction(1, 3), Fraction(0))),
        (Error, ("", Fraction(1))),
        (Error, ("standard-error", Fraction(1, 3))),
        (Crosswalk, ({"a": 1}, Conversion("multiplicative", Fraction(1), None), Error("se", Fraction(0)))),
    ],
)
def test_field_grammar(factory, args):
    with pytest.raises(MalformedRecord):
        factory(*args)


def test_affine_and_multiplicative_wire_numbers_are_exact_strings():
    value = proxy(target=ProxyTarget(None, PID), crosswalk=CROSSWALK)
    facet: dict[str, Any] = proxy_projection(value)
    assert facet["crosswalk"]["conversion"] == {"kind": "affine", "scale": "-2", "offset": "10"}
    facet["crosswalk"]["conversion"]["scale"] = -2
    with pytest.raises(MalformedRecord):
        proxy_from_stored(node_for("proxy-model", proxy_identity(value), facet))


@pytest.mark.parametrize("number", [Fraction(1, 10**4096), Fraction(10**4096), Fraction(123, 10**4098)])
def test_crosswalk_coefficients_round_trip_exactly_at_the_decimal_budget(number):
    crosswalk = Crosswalk({}, Conversion("affine", number, -number), Error("standard-error", number))
    value = proxy(target=ProxyTarget(None, PID), crosswalk=crosswalk)
    assert proxy_from_stored(node_for("proxy-model", proxy_identity(value), proxy_projection(value))) == value


@pytest.mark.parametrize(
    "bad",
    [
        {"kind": "affine", "factor": "2", "offset": "1"},
        {"kind": "multiplicative", "scale": "2"},
        {"kind": "multiplicative", "factor": "2", "offset": "1"},
        {"kind": "affine", "scale": "2", "factor": "2", "offset": "1"},
        {"kind": "affine", "scale": "NaN", "offset": "0"},
        {"kind": "affine", "scale": "1e4097", "offset": "0"},
    ],
)
def test_crosswalk_reader_refuses_alternative_spellings_and_invalid_decimal_values(bad):
    value = proxy(target=ProxyTarget(None, PID), crosswalk=CROSSWALK)
    facet: dict[str, Any] = proxy_projection(value)
    facet["crosswalk"]["conversion"] = bad
    with pytest.raises(MalformedRecord):
        proxy_from_stored(node_for("proxy-model", proxy_identity(value), facet))


def test_calibration_and_crosswalk_nested_fields_are_shape_exact():
    value = proxy(target=ProxyTarget(None, PID), crosswalk=CROSSWALK, basis=Calibration(OBS, (AID,), (RULE,), None))
    for path in (
        ("basis", "calibration"),
        ("basis", "calibration", "calibrated"),
        ("crosswalk",),
        ("crosswalk", "conversion"),
        ("crosswalk", "error"),
    ):
        facet: dict[str, Any] = proxy_projection(value)
        row = facet
        for key in path:
            row = row[key]
        row["extra"] = "unexpected"
        with pytest.raises(MalformedRecord):
            proxy_from_stored(node_for("proxy-model", proxy_identity(value), facet))


def test_multiplicative_crosswalk_projects_factor_only_and_round_trips():
    value = proxy(
        target=ProxyTarget(None, PID),
        crosswalk=Crosswalk(
            {}, Conversion("multiplicative", Fraction(3, 2), None), Error("standard-error", Fraction(0))
        ),
    )
    facet: dict[str, Any] = proxy_projection(value)
    assert facet["crosswalk"]["conversion"] == {"kind": "multiplicative", "factor": "1.5"}
    assert proxy_from_stored(node_for("proxy-model", proxy_identity(value), facet)) == value
