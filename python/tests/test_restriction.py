"""Typed scopes compare exactly, without silently acquiring operator semantics."""

from fractions import Fraction

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import MalformedRestriction, MeasurementError, ScienceError
from beliefs.profile import compile_profile
from beliefs.restriction import (
    IntervalRestriction,
    RuleRestriction,
    TermRestriction,
    TimeIntervalRestriction,
    UnionRestriction,
    co_scope,
    co_scope_by_dimension,
    restriction_from_projection,
    restriction_projection,
    type_restriction_map,
)

RULE = "classification-rule:" + "a" * 64
OTHER_RULE = "classification-rule:" + "b" * 64


@pytest.fixture()
def profile(base_contract, testing_document):
    testing_document["units"]["unconverted"] = {"symbol": "u", "quantity_kind": "duration"}
    testing_document["units"]["triple-hour"] = {"symbol": "t", "quantity_kind": "duration"}
    testing_document["conversions"]["triple"] = {
        "from": "hour",
        "to": "triple-hour",
        "kind": "multiplicative",
        "factor": "3",
        "exact": True,
    }
    for name in ("follow-up", "stage", "epoch", "case-status"):
        decl = dict(testing_document["dimensions"][name])
        decl["restriction"] = {"form": "union", "of": decl["restriction"]}
        testing_document["dimensions"]["union-" + name] = decl
    return compile_profile(
        base_contract,
        [parse_domain_contract(testing_document, source="<restriction>", base=base_contract, predecessor=None)],
    )


def interval(low=None, high=None, *, unit="testing/hour", low_closed=True, high_closed=False):
    return IntervalRestriction(
        unit, None if low is None else Fraction(low), None if high is None else Fraction(high), low_closed, high_closed
    )


def scope(value, dimension="follow-up"):
    return {"testing/" + dimension: value}


@pytest.mark.parametrize(
    ("form", "value", "projection"),
    [
        ("term", TermRestriction("testing/stage", "EX:rem"), {"sort": "testing/stage", "term": "EX:rem"}),
        (
            "interval",
            interval("-0.25", "1.125", high_closed=True),
            {"unit": "testing/hour", "low": "-0.25", "high": "1.125", "low_closed": True, "high_closed": True},
        ),
        ("interval", interval(high=2), {"unit": "testing/hour", "high": "2", "low_closed": True, "high_closed": False}),
        (
            "time-interval",
            TimeIntervalRestriction("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"),
            {"start": "2026-01-01T00:00:00Z", "end": "2026-01-02T00:00:00Z"},
        ),
        ("rule", RuleRestriction(RULE, ("EX:a", "EX:b")), {"rule": RULE, "classes": ["EX:a", "EX:b"]}),
        (
            "union",
            UnionRestriction((interval(0, 1), interval(2, 3))),
            [
                {"unit": "testing/hour", "low": "0", "high": "1", "low_closed": True, "high_closed": False},
                {"unit": "testing/hour", "low": "2", "high": "3", "low_closed": True, "high_closed": False},
            ],
        ),
    ],
)
def test_each_form_round_trips_its_projection(form, value, projection):
    assert restriction_projection(value) == projection
    assert restriction_from_projection(projection, form=form) == value


@pytest.mark.parametrize(
    "low,high,lc,hc", [(None, None, True, True), (2, 1, True, True), (1, 1, False, True), (1, 1, True, False)]
)
def test_interval_bounds(low, high, lc, hc):
    with pytest.raises(MalformedRestriction):
        interval(low, high, low_closed=lc, high_closed=hc)


def test_single_bound_and_singleton_intervals():
    assert interval(0).low == 0
    assert interval(high=0).high == 0
    assert interval(1, 1, high_closed=True).low == 1


@pytest.mark.parametrize(
    "members",
    [
        (interval(0, 1),),
        (interval(0, 1), TermRestriction("testing/stage", "EX:a")),
        (UnionRestriction((interval(0, 1), interval(2, 3))), interval(4, 5)),
    ],
)
def test_union_shape(members):
    with pytest.raises(MalformedRestriction):
        UnionRestriction(members)


@pytest.mark.parametrize(
    "form,value",
    [
        ("interval", {"unit": "testing/hour", "low": 1, "low_closed": True, "high_closed": False}),
        ("interval", {"unit": "testing/hour", "low": "NaN", "low_closed": True, "high_closed": False}),
        ("interval", {"unit": "testing/hour", "low": "1/3", "low_closed": True, "high_closed": False}),
        ("interval", {"unit": "testing/hour", "low": None, "low_closed": True, "high_closed": False}),
        ("term", {"sort": "testing/stage", "term": "EX:a", "extra": "ignored?"}),
        ("term", {"sort": "testing/stage"}),
        ("rule", {"rule": RULE, "classes": []}),
        ("rule", {"rule": OTHER_RULE, "classes": ["EX:b", "EX:a"]}),
        ("rule", {"rule": "classification-rule:no", "classes": ["EX:a"]}),
        ("time-interval", {"start": "2026-02-30T00:00:00Z", "end": "2026-03-01T00:00:00Z"}),
        ("time-interval", {"start": "2026-01-01", "end": "2026-01-02"}),
        ("time-interval", {"start": "2026-01-02T00:00:00Z", "end": "2026-01-01T00:00:00Z"}),
        ("union", [{"sort": "testing/stage", "term": "EX:a"}, {"start": "open", "end": "2026-01-01T00:00:00Z"}]),
        ("missing", {}),
    ],
)
def test_projection_refuses_malformed_shape(form, value):
    with pytest.raises(MalformedRestriction):
        restriction_from_projection(value, form=form)


def test_the_refusal_family():
    assert issubclass(MalformedRestriction, MeasurementError)
    assert issubclass(MeasurementError, ScienceError)


@pytest.mark.parametrize(
    "dimension,value",
    [
        ("missing", {"sort": "testing/stage", "term": "EX:a"}),
        ("population", {"sort": "testing/cohort", "term": "EX:a"}),
        ("follow-up", {"sort": "testing/stage", "term": "EX:a"}),
        ("follow-up", {"unit": "testing/kelvin", "low": "1", "low_closed": True, "high_closed": False}),
        ("follow-up", {"unit": "testing/missing", "low": "1", "low_closed": True, "high_closed": False}),
        ("stage", {"sort": "testing/entity", "term": "EX:a"}),
        ("stage", {"sort": "testing/stage", "term": "not-a-stage"}),
        ("case-status", {"rule": RULE, "classes": ["bad-class"]}),
        ("union-follow-up", [{"sort": "testing/stage", "term": "EX:a"}, {"sort": "testing/stage", "term": "EX:b"}]),
    ],
)
def test_typing_against_the_dimension(profile, dimension, value):
    with pytest.raises(MalformedRestriction):
        type_restriction_map(profile, {"testing/" + dimension: value})


def test_typing_needs_no_operator_and_returns_an_immutable_map(profile):
    value = {
        "testing/follow-up": restriction_projection(interval(0, 1)),
        "testing/case-status": {"rule": RULE, "classes": ["EX:a"]},
    }
    typed = type_restriction_map(profile, value)
    assert typed["testing/follow-up"] == interval(0, 1)
    assert typed["testing/case-status"] == RuleRestriction(RULE, ("EX:a",))
    with pytest.raises(TypeError):
        typed["testing/stage"] = TermRestriction("testing/stage", "EX:rem")  # type: ignore[index]


@pytest.mark.parametrize(
    "a,b,want",
    [
        (scope(interval(0, 24)), {}, "narrower"),
        (scope(interval(0, 24)), scope(interval(0, 86400, unit="testing/second")), "equal"),
        (scope(interval(0, 12)), scope(interval(0, 86400, unit="testing/second")), "narrower"),
        (scope(interval(0, 48)), scope(interval(0, 86400, unit="testing/second")), "broader"),
        (scope(interval(6, 30)), scope(interval(0, 86400, unit="testing/second")), "overlapping"),
        (scope(interval(48, 72)), scope(interval(0, 86400, unit="testing/second")), "disjoint"),
        (scope(interval(0, 24)), scope(interval(0, 24, unit="testing/unconverted")), "unknown"),
        (
            scope(interval(0, 1, high_closed=True)),
            scope(interval(0, 3, unit="testing/triple-hour", high_closed=True)),
            "equal",
        ),
        (
            scope(interval(0, 1, high_closed=True)),
            scope(interval(0, 4, unit="testing/triple-hour", high_closed=True)),
            "narrower",
        ),
        (scope(interval(0, 1)), scope(interval(1, 2)), "disjoint"),
        (scope(interval(0, 1, high_closed=True)), scope(interval(1, 2)), "overlapping"),
        (scope(interval(0)), scope(interval(0, 1)), "broader"),
        (scope(interval(0, low_closed=False)), scope(interval(0)), "narrower"),
        (
            scope(TermRestriction("testing/stage", "EX:a"), "stage"),
            scope(TermRestriction("testing/stage", "EX:a"), "stage"),
            "equal",
        ),
        (
            scope(TermRestriction("testing/stage", "EX:a"), "stage"),
            scope(TermRestriction("testing/stage", "EX:b"), "stage"),
            "unknown",
        ),
        (
            scope(RuleRestriction(RULE, ("EX:a",)), "case-status"),
            scope(RuleRestriction(RULE, ("EX:a", "EX:b")), "case-status"),
            "narrower",
        ),
        (
            scope(RuleRestriction(RULE, ("EX:a", "EX:c")), "case-status"),
            scope(RuleRestriction(RULE, ("EX:a", "EX:b")), "case-status"),
            "unknown",
        ),
        (
            scope(RuleRestriction(RULE, ("EX:a",)), "case-status"),
            scope(RuleRestriction(OTHER_RULE, ("EX:a",)), "case-status"),
            "unknown",
        ),
    ],
)
def test_co_scope_intervals_terms_and_rules_are_antisymmetric(profile, a, b, want):
    reverse = {"narrower": "broader", "broader": "narrower"}.get(want, want)
    assert co_scope(a, b, profile) == want
    assert co_scope(b, a, profile) == reverse


@pytest.mark.parametrize(
    "a,b,want",
    [
        ((interval(0, 1), interval(1, 2)), (interval(0, 2), interval(0, 1)), "equal"),
        ((interval(0, 1), interval(2, 3)), (interval(0, 2), interval(2, 4)), "narrower"),
        ((interval(0, 1), interval(2, 3)), (interval(1, 2), interval(3, 4)), "disjoint"),
        ((interval(0, 2), interval(4, 6)), (interval(1, 3), interval(5, 7)), "overlapping"),
        ((interval(0, 1), interval(1, 2, low_closed=False)), (interval(0, 2), interval(0, 1)), "narrower"),
        (
            (interval(0, 1), interval(1, 2)),
            (interval(0, 3600, unit="testing/second"), interval(3600, 7200, unit="testing/second")),
            "equal",
        ),
    ],
)
def test_co_scope_unions(profile, a, b, want):
    left, right = scope(UnionRestriction(a), "union-follow-up"), scope(UnionRestriction(b), "union-follow-up")
    assert co_scope(left, right, profile) == want
    assert co_scope(right, left, profile) == {"narrower": "broader", "broader": "narrower"}.get(want, want)


@pytest.mark.parametrize(
    "start,end,want",
    [
        ("2026-01-01T00:00:00Z", "2026-01-03T00:00:00Z", "equal"),
        ("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", "narrower"),
        ("open", "2026-01-04T00:00:00Z", "broader"),
        ("2026-01-02T00:00:00Z", "2026-01-04T00:00:00Z", "overlapping"),
        ("2026-01-03T00:00:00Z", "open", "disjoint"),
    ],
)
def test_co_scope_time_intervals(profile, start, end, want):
    a, b = (
        scope(TimeIntervalRestriction(start, end), "epoch"),
        scope(TimeIntervalRestriction("2026-01-01T00:00:00Z", "2026-01-03T00:00:00Z"), "epoch"),
    )
    assert co_scope(a, b, profile) == want
    assert co_scope(b, a, profile) == {"narrower": "broader", "broader": "narrower"}.get(want, want)


def test_the_fold_precedence_and_dimension_verdicts(profile):
    equal = (interval(0, 2), interval(0, 2))
    narrower = (interval(0, 1), interval(0, 2))
    broader = (interval(0, 3), interval(0, 2))
    overlapping = (interval(1, 3), interval(0, 2))
    disjoint = (interval(3, 4), interval(0, 2))
    unknown = (TermRestriction("testing/stage", "EX:a"), TermRestriction("testing/stage", "EX:b"))
    for cases, want in [
        ([equal], "equal"),
        ([narrower, broader], "overlapping"),
        ([unknown, overlapping], "unknown"),
        ([disjoint, unknown, narrower, broader], "disjoint"),
        ([], "equal"),
    ]:
        a = {str(i): pair[0] for i, pair in enumerate(cases)}
        b = {str(i): pair[1] for i, pair in enumerate(cases)}
        assert co_scope(a, b, profile) == want
    assert co_scope_by_dimension(scope(interval(0, 1)), {}, profile) == {"testing/follow-up": "narrower"}


def test_authored_bounds_need_exact_decimal_projection():
    with pytest.raises(MalformedRestriction):
        IntervalRestriction("testing/hour", Fraction(1, 3), None, True, False)
    value = interval("1.23456789012345678901234567890123456789")
    projected = restriction_projection(value)
    assert isinstance(projected, dict)
    assert projected["low"] == "1.23456789012345678901234567890123456789"


def test_union_against_one_leaf_and_unbounded_members(profile):
    a = scope(UnionRestriction((interval(high=0), interval(0))), "union-follow-up")
    b = scope(interval(0, 1), "union-follow-up")
    assert co_scope(a, b, profile) == "broader"
    assert co_scope(b, a, profile) == "narrower"


def test_term_and_rule_unions_preserve_the_decidable_fragment(profile):
    a, b, c = (TermRestriction("testing/stage", "EX:" + term) for term in ("a", "b", "c"))
    small, large = UnionRestriction((a, b)), UnionRestriction((a, b, c))
    assert co_scope(scope(small), scope(large), profile) == "narrower"
    assert co_scope(scope(small), scope(UnionRestriction((b, c))), profile) == "unknown"
    rules = UnionRestriction((RuleRestriction(RULE, ("EX:a",)), RuleRestriction(RULE, ("EX:b",))))
    assert co_scope(scope(rules), scope(RuleRestriction(RULE, ("EX:a", "EX:b"))), profile) == "equal"


@pytest.mark.parametrize(
    "text",
    ["1e999999999999999999999999", "1e4097", "1" * 4097],
    ids=["huge-exponent", "exponent-budget", "mantissa-budget"],
)
def test_untrusted_decimal_sizes_refuse_before_fraction_allocation(text):
    with pytest.raises(MalformedRestriction):
        restriction_from_projection(
            {"unit": "testing/hour", "low": text, "low_closed": True, "high_closed": False}, form="interval"
        )


def test_affine_interval_normalization_is_exact(profile):
    a = scope(interval("273.15", "274.15", unit="testing/kelvin"))
    b = scope(interval(0, 1, unit="testing/celsius"))
    assert co_scope(a, b, profile) == "equal"
    assert co_scope(b, a, profile) == "equal"


def test_decimal_projection_avoids_the_interpreter_integer_digit_limit():
    text = "1" * 4096 + "e4096"
    value = restriction_from_projection(
        {"unit": "testing/hour", "low": text, "low_closed": True, "high_closed": False}, form="interval"
    )
    projected = restriction_projection(value)
    assert isinstance(projected, dict)
    assert projected["low"] == "1" * 4096 + "0" * 4096


def test_union_normalization_is_symmetric_with_sparse_conversion_routes(profile):
    left = (interval(0, 1), interval(3600, 7200, unit="testing/second"))
    right = (interval(0, 3600, unit="testing/second"), interval(3, 6, unit="testing/triple-hour"))
    for a_members in (left, left[::-1]):
        for b_members in (right, right[::-1]):
            a, b = scope(UnionRestriction(a_members)), scope(UnionRestriction(b_members))
            assert co_scope(a, b, profile) == "equal"
            assert co_scope(b, a, profile) == "equal"
