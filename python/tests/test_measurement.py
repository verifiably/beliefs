"""Observables retain their aspects and measures declare their resulting values."""

from dataclasses import FrozenInstanceError, replace

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import AspectNotAdmitted, MalformedMeasure, MeasurementError, UndeclaredQuantityKind
from beliefs.identity.v1 import encode
from beliefs.measurement import (
    Aspect,
    Coordinates,
    Measure,
    Observable,
    check_measure,
    check_observable,
    measure_from_projection,
    measure_projection,
    observable_from_projection,
    observable_projection,
)
from beliefs.profile import compile_profile

PROCEDURE = "procedure:" + "a" * 64
SCALE = "procedure:" + "b" * 64


@pytest.fixture()
def profile(base_contract, testing_document):
    return compile_profile(
        base_contract,
        [parse_domain_contract(testing_document, source="<measurement>", base=base_contract, predecessor=None)],
    )


def measure(**changes):
    fields = {
        "observable": Observable("testing/abundance", "testing/entity"),
        "unit": "testing/tpm",
        "scale": None,
        "level": "ratio",
        "value_type": "level",
        "transformation": "testing/identity",
        "procedure": PROCEDURE,
    }
    return Measure(**(fields | changes))


def test_observables_differ_by_aspect(profile):
    observables = [
        Observable("testing/energy", "testing/event", Aspect("testing/energy-aspect", term))
        for term in ("EX:apparent", "EX:elementary-step-barrier")
    ] + [Observable("testing/energy", "testing/event")]
    assert len(set(observables)) == 3
    assert [observable_projection(o) for o in observables] == [
        {
            "quantity_kind": "testing/energy",
            "bearer_sort": "testing/event",
            "aspect": {"sort": "testing/energy-aspect", "term": "EX:apparent"},
        },
        {
            "quantity_kind": "testing/energy",
            "bearer_sort": "testing/event",
            "aspect": {"sort": "testing/energy-aspect", "term": "EX:elementary-step-barrier"},
        },
        {"quantity_kind": "testing/energy", "bearer_sort": "testing/event"},
    ]
    for observable in observables:
        check_observable(profile, observable)


@pytest.mark.parametrize("kind,sort", [("energy", "stage"), ("duration", "energy-aspect")])
def test_an_aspect_sort_the_pack_does_not_list_refuses(profile, kind, sort):
    with pytest.raises(AspectNotAdmitted):
        check_observable(profile, Observable("testing/" + kind, "testing/event", Aspect("testing/" + sort, "EX:a")))


@pytest.mark.parametrize(
    "observable,error",
    [
        (Observable("testing/missing", "testing/entity"), UndeclaredQuantityKind),
        (Observable("testing/abundance", "testing/missing"), MalformedMeasure),
        (Observable("testing/energy", "testing/event", Aspect("testing/missing", "EX:a")), MalformedMeasure),
    ],
)
def test_observable_names_resolve_exactly(profile, observable, error):
    with pytest.raises(error):
        check_observable(profile, observable)


def test_observable_check_does_not_admit_a_measurement(profile):
    # A declared bearer is shape-valid even when its measurements table is empty.
    check_observable(profile, Observable("testing/abundance", "testing/cohort"))


def test_a_unit_of_another_kind_refuses(profile):
    with pytest.raises(MalformedMeasure):
        check_measure(profile, measure(unit="testing/second"))


@pytest.mark.parametrize("field", ["unit", "transformation"])
def test_measure_names_resolve_exactly(profile, field):
    with pytest.raises(MalformedMeasure):
        check_measure(profile, measure(**{field: "testing/missing"}))


@pytest.mark.parametrize("transformation", ["testing/identity", "testing/log2-plus-one"])
def test_ratio_value_type_needs_ratio_level(transformation):
    with pytest.raises(MalformedMeasure):
        measure(value_type="ratio", level="interval", transformation=transformation)
    assert measure(value_type="ratio").level == "ratio"


def test_difference_refuses_nominal():
    with pytest.raises(MalformedMeasure):
        measure(value_type="difference", level="nominal")
    assert measure(value_type="difference", level="ordinal").level == "ordinal"


@pytest.mark.parametrize("unit,scale", [(None, None), ("testing/tpm", SCALE)])
def test_exactly_one_of_unit_or_scale(unit, scale):
    with pytest.raises(MalformedMeasure):
        measure(unit=unit, scale=scale)
    with pytest.raises(MalformedMeasure):
        Coordinates("testing/abundance", unit, scale, "level", "testing/identity")


def test_log2_plus_one_at_interval_level_passes_check_measure(profile):
    check_measure(profile, measure(level="interval", transformation="testing/log2-plus-one"))
    with pytest.raises(MalformedMeasure):
        measure(level="interval", value_type="ratio", transformation="testing/log2-plus-one")


def test_a_logarithm_refuses_a_ratio_level(profile):
    with pytest.raises(MalformedMeasure):
        check_measure(profile, measure(transformation="testing/log2"))
    check_measure(profile, measure(level="interval", transformation="testing/log2"))


@pytest.mark.parametrize("transformation", ["log2", "log2-plus-one", "logit"])
def test_transformation_input_domain_is_not_inferred_from_measure(profile, transformation):
    check_measure(
        profile, measure(level="interval", value_type="difference", transformation="testing/" + transformation)
    )


@pytest.mark.parametrize("use_scale", [False, True])
def test_projection_round_trip_and_no_nulls(profile, use_scale):
    value = measure(unit=None, scale=SCALE) if use_scale else measure()
    expected = {
        "observable": {"quantity_kind": "testing/abundance", "bearer_sort": "testing/entity"},
        "level": "ratio",
        "value_type": "level",
        "transformation": "testing/identity",
        "procedure": PROCEDURE,
        **({"scale": SCALE} if use_scale else {"unit": "testing/tpm"}),
    }
    assert measure_projection(value) == expected
    assert measure_from_projection(expected) == value
    assert observable_from_projection(expected["observable"]) == value.observable
    encode(expected)  # Canonical encoding refuses null at every depth.
    check_measure(profile, value)


def test_projection_round_trip_with_aspect():
    observable = Observable("testing/energy", "testing/event", Aspect("testing/energy-aspect", "EX:apparent"))
    assert observable_from_projection(observable_projection(observable)) == observable


def test_coordinates_view():
    value = measure()
    assert value.coordinates == Coordinates("testing/abundance", "testing/tpm", None, "level", "testing/identity")
    assert replace(value, procedure=SCALE, level="interval").coordinates == value.coordinates
    assert measure(unit=None, scale=SCALE).coordinates == Coordinates(
        "testing/abundance", None, SCALE, "level", "testing/identity"
    )
    for target, field, replacement in (
        (value.observable, "bearer_sort", "testing/event"),
        (value, "unit", "testing/ktpm"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(target, field, replacement)


@pytest.mark.parametrize(
    "changes",
    [
        {"observable": {}},
        {"unit": "tpm"},
        {"scale": "bad", "unit": None},
        {"procedure": "procedure:" + "A" * 64},
        {"procedure": "procedure:" + "a" * 63},
        {"procedure": None},
        {"level": "continuous"},
        {"value_type": "count"},
        {"transformation": "identity"},
        {"transformation": None},
    ],
)
def test_constructor_refuses_malformed_values(changes):
    with pytest.raises(MalformedMeasure):
        measure(**changes)


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        {},
        {"quantity_kind": "testing/abundance", "bearer_sort": None},
        {"quantity_kind": "abundance", "bearer_sort": "testing/entity"},
        {"quantity_kind": "testing/abundance", "bearer_sort": "testing/entity", "extra": 1},
        {"quantity_kind": "testing/energy", "bearer_sort": "testing/event", "aspect": None},
        {"quantity_kind": "testing/energy", "bearer_sort": "testing/event", "aspect": {}},
        {
            "quantity_kind": "testing/energy",
            "bearer_sort": "testing/event",
            "aspect": {"sort": "testing/energy-aspect", "term": "", "extra": 1},
        },
    ],
)
def test_observable_projection_has_a_closed_shape(value):
    with pytest.raises(MalformedMeasure):
        observable_from_projection(value)


@pytest.mark.parametrize("changes", [{"extra": 1}, {"scale": None}, {"unit": None}, {"procedure": None}])
def test_measure_projection_refuses_unknown_fields_and_null(changes):
    value = measure_projection(measure()) | changes
    with pytest.raises(MalformedMeasure):
        measure_from_projection(value)


@pytest.mark.parametrize("field", ["observable", "level", "value_type", "transformation", "procedure", "unit"])
def test_measure_projection_requires_every_field(field):
    value = measure_projection(measure())
    del value[field]
    with pytest.raises(MalformedMeasure):
        measure_from_projection(value)


def test_refusals_share_the_measurement_family():
    assert all(
        issubclass(error, MeasurementError) for error in (AspectNotAdmitted, UndeclaredQuantityKind, MalformedMeasure)
    )
