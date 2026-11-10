"""Calendar conversions require explicit metadata and named exact conventions."""

from dataclasses import replace
from fractions import Fraction

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import MalformedContract, MalformedRestriction, ProfileError
from beliefs.profile import compile_profile
from beliefs.restriction import (
    IntervalRestriction,
    UnionRestriction,
    co_scope,
    restriction_from_projection,
    restriction_projection,
    type_restriction_map,
)


@pytest.fixture()
def calendar_document(testing_document):
    testing_document["units"]["calendar-month"] = {"symbol": "mo", "quantity_kind": "duration", "calendar": True}
    testing_document["conversions"]["mean-month-to-second"] = {
        "from": "calendar-month",
        "to": "second",
        "kind": "multiplicative",
        "factor": "2629800",
        "exact": True,
    }
    testing_document["duration_conventions"] = {"mean-month": {"conversion": "mean-month-to-second"}}
    return testing_document


@pytest.fixture()
def parse(base_contract):
    return lambda document: parse_domain_contract(document, source="<calendar>", base=base_contract, predecessor=None)


@pytest.fixture()
def compile(base_contract, parse):
    return lambda document: compile_profile(base_contract, [parse(document)])


def interval(unit="testing/calendar-month", convention=None, low=0, high=1):
    return IntervalRestriction(unit, Fraction(low), Fraction(high), True, True, convention=convention)


def scope(value):
    return {"testing/follow-up": value}


def test_calendar_metadata_and_named_conversion_are_compiled(parse, compile, calendar_document):
    contract, profile = parse(calendar_document), compile(calendar_document)
    assert contract.units["calendar-month"].calendar is True
    assert contract.units["second"].calendar is False
    assert contract.units["second"].schema_projection()["calendar"] is False
    assert profile.units["testing/calendar-month"].schema_projection()["calendar"] is True
    assert contract.duration_conventions["mean-month"].schema_projection() == {"conversion": "mean-month-to-second"}
    convention = profile.duration_conventions["testing/mean-month"]
    assert (convention.term, convention.conversion, convention.contract) == (
        "testing/mean-month",
        "testing/mean-month-to-second",
        "testing",
    )
    assert convention.schema_projection() == {"conversion": "testing/mean-month-to-second"}
    assert profile.conversion_between("testing/calendar-month", "testing/second") is None
    assert profile.conversion_between("testing/second", "testing/calendar-month") is None
    assert profile.conversion_between("testing/hour", "testing/second") is not None


@pytest.mark.parametrize("marker", ["true", 1, None, []])
def test_calendar_marker_is_boolean(parse, calendar_document, marker):
    calendar_document["units"]["calendar-month"]["calendar"] = marker
    with pytest.raises(MalformedContract):
        parse(calendar_document)


@pytest.mark.parametrize("dimension", [{"T": -1}, {"T": 1, "L": 1}, {"T": 1, "L": 0}, "construct", "dimensionless"])
def test_calendar_requires_exactly_the_time_dimension(compile, calendar_document, dimension):
    calendar_document["quantity_kinds"]["duration"]["dimension"] = dimension
    with pytest.raises(ProfileError):
        compile(calendar_document)


@pytest.mark.parametrize(
    "declaration",
    [{"unit": "hours", "length": 24}, {}, {"conversion": "mean-month-to-second", "retired": False}, {"conversion": 1}],
)
def test_provisional_scalar_schema_and_wrong_convention_fields_refuse(parse, calendar_document, declaration):
    calendar_document["duration_conventions"]["mean-month"] = declaration
    with pytest.raises(MalformedContract):
        parse(calendar_document)


@pytest.mark.parametrize("conversion", ["missing", "other/missing"])
def test_missing_convention_conversion_refuses_at_compile(compile, calendar_document, conversion):
    calendar_document["duration_conventions"]["mean-month"]["conversion"] = conversion
    with pytest.raises(ProfileError):
        compile(calendar_document)


@pytest.mark.parametrize(
    "change",
    [
        {"kind": "affine", "offset": "0"},
        {"exact": False},
        {"error": "0"},
        {"constant": "avogadro"},
        {"from": "hour"},
        {"to": "calendar-month"},
    ],
)
def test_convention_conversion_must_be_exact_and_join_one_calendar_endpoint(compile, calendar_document, change):
    calendar_document["conversions"]["mean-month-to-second"].update(change)
    with pytest.raises(ProfileError):
        compile(calendar_document)


def test_convention_endpoints_share_the_same_kind(compile, calendar_document):
    calendar_document["quantity_kinds"]["other-duration"] = {"dimension": {"T": 1}}
    calendar_document["units"]["second"]["quantity_kind"] = "other-duration"
    with pytest.raises(ProfileError):
        compile(calendar_document)


def test_calendar_does_not_mean_a_unit_name(compile, calendar_document):
    calendar_document["units"]["calendar-month"]["calendar"] = False
    calendar_document["duration_conventions"] = {}
    profile = compile(calendar_document)
    assert profile.conversion_between("testing/calendar-month", "testing/second") is not None


def test_missing_convention_is_unknown_even_against_itself(compile, calendar_document):
    profile = compile(calendar_document)
    value = interval()
    typed = type_restriction_map(profile, {"testing/follow-up": restriction_projection(value)})
    assert co_scope(typed, typed, profile) == "unknown"
    assert co_scope(typed, {}, profile) == "narrower"
    assert co_scope({}, typed, profile) == "broader"
    for other in (interval("testing/second", high=2629800), interval(convention="testing/mean-month")):
        assert co_scope(scope(value), scope(other), profile) == "unknown"
        assert co_scope(scope(other), scope(value), profile) == "unknown"


def test_named_calendar_normalization_is_exact_both_directions(compile, calendar_document):
    profile = compile(calendar_document)
    a, b = scope(interval(convention="testing/mean-month")), scope(interval("testing/second", high=2629800))
    assert co_scope(a, b, profile) == "equal"
    assert co_scope(b, a, profile) == "equal"
    calendar_document["conversions"]["mean-month-to-second"].update(
        {"from": "second", "to": "calendar-month", "factor": "0.5"}
    )
    reverse_profile = compile(calendar_document)
    assert co_scope(a, scope(interval("testing/second", high=2)), reverse_profile) == "equal"
    assert co_scope(scope(interval("testing/second", high=2)), a, reverse_profile) == "equal"


def test_optional_convention_projection_and_local_typing(compile, calendar_document):
    profile = compile(calendar_document)
    authored = interval(convention="mean-month")
    projection = restriction_projection(authored)
    assert restriction_from_projection(projection, form="interval") == authored
    assert isinstance(projection, dict)
    assert projection["convention"] == "mean-month"
    typed = type_restriction_map(profile, {"testing/follow-up": projection})
    assert typed["testing/follow-up"] == replace(authored, convention="testing/mean-month")
    assert "convention" not in restriction_projection(interval("testing/second"))


@pytest.mark.parametrize(
    "unit,convention",
    [
        ("testing/calendar-month", "missing"),
        ("testing/second", "mean-month"),
        ("testing/calendar-month", "wrong-month"),
    ],
)
def test_invalid_or_irrelevant_convention_refuses_typing(compile, calendar_document, unit, convention):
    calendar_document["units"]["other-month"] = {"symbol": "om", "quantity_kind": "duration", "calendar": True}
    calendar_document["conversions"]["other-month-to-second"] = {
        "from": "other-month",
        "to": "second",
        "kind": "multiplicative",
        "factor": "2",
        "exact": True,
    }
    calendar_document["duration_conventions"]["wrong-month"] = {"conversion": "other-month-to-second"}
    profile = compile(calendar_document)
    with pytest.raises(MalformedRestriction):
        type_restriction_map(profile, {"testing/follow-up": restriction_projection(interval(unit, convention))})


def test_union_members_each_require_their_own_convention(compile, calendar_document):
    calendar_document["dimensions"]["follow-up"]["restriction"] = {
        "form": "union",
        "of": {"form": "interval", "quantity_kind": "duration"},
    }
    profile = compile(calendar_document)
    values = (interval(convention="testing/mean-month"), interval(convention="testing/mean-month", low=1, high=2))
    a = type_restriction_map(
        profile,
        scope(
            restriction_projection(UnionRestriction(tuple(replace(value, convention="mean-month") for value in values)))
        ),
    )
    b = scope(interval("testing/second", high=5259600))
    assert co_scope(a, b, profile) == "equal"
    assert co_scope(b, a, profile) == "equal"
    unresolved = scope(UnionRestriction((values[0], replace(values[1], convention=None))))
    assert co_scope(unresolved, b, profile) == "unknown"
    assert co_scope(b, unresolved, profile) == "unknown"


def test_two_conventions_compare_through_their_noncalendar_units(compile, calendar_document):
    calendar_document["conversions"]["mean-month-to-hour"] = {
        "from": "calendar-month",
        "to": "hour",
        "kind": "multiplicative",
        "factor": "730.5",
        "exact": True,
    }
    calendar_document["duration_conventions"]["mean-month-hours"] = {"conversion": "mean-month-to-hour"}
    profile = compile(calendar_document)
    a, b = scope(interval(convention="testing/mean-month")), scope(interval(convention="testing/mean-month-hours"))
    assert co_scope(a, b, profile) == co_scope(b, a, profile) == "equal"
    del calendar_document["conversions"]["hour-to-second"]
    profile = compile(calendar_document)
    assert co_scope(a, b, profile) == co_scope(b, a, profile) == "unknown"


def test_editorial_convention_definition_does_not_change_schema_identity(parse, compile, calendar_document):
    before, profile = parse(calendar_document), compile(calendar_document)
    calendar_document["duration_conventions"]["mean-month"].update(
        {"definition": "A fixed mean month, not an actual calendar month.", "description": "Editorial context."}
    )
    after = parse(calendar_document)
    assert before.content_identity != after.content_identity
    assert profile.compiled_identity == compile(calendar_document).compiled_identity


def test_own_qualified_declaration_reference_preserves_the_contract_grammar(parse, calendar_document):
    calendar_document["duration_conventions"]["mean-month"]["conversion"] = "testing/mean-month-to-second"
    with pytest.raises(MalformedContract):
        parse(calendar_document)


def test_foreign_convention_reference_resolves_independent_of_activation_order(base_contract, parse, calendar_document):
    testing = parse(calendar_document)
    other = parse(
        {
            "contract": "other",
            "version": 1,
            "lineage": "genesis",
            "sorts": {},
            "dimensions": {},
            "duration_conventions": {"borrowed": {"conversion": "testing/mean-month-to-second"}},
        }
    )
    profile = compile_profile(base_contract, [other, testing])
    assert profile.duration_conventions["other/borrowed"].conversion == "testing/mean-month-to-second"
    assert profile.duration_conventions == compile_profile(base_contract, [testing, other]).duration_conventions


@pytest.mark.parametrize("convention", [None, 1, {}, "", "too/many/parts"])
def test_malformed_supplied_convention_refuses_at_the_shape_boundary(convention):
    projection = {
        "unit": "testing/calendar-month",
        "low": "0",
        "low_closed": True,
        "high_closed": False,
        "convention": convention,
    }
    with pytest.raises(MalformedRestriction):
        restriction_from_projection(projection, form="interval")


def test_calendar_unit_pairs_remain_unique(compile, calendar_document):
    calendar_document["conversions"]["duplicate-month-to-second"] = dict(
        calendar_document["conversions"]["mean-month-to-second"]
    )
    with pytest.raises(ProfileError, match="pair"):
        compile(calendar_document)
