"""The six declaration-only conversion traces, through estimate application."""

from dataclasses import replace
from decimal import Context, Decimal
from fractions import Fraction

from functionals_fixture import (
    ARRHENIUS,
    DIFFERENCE_OF_MEANS,
    HODGES_LEHMANN_SHIFT,
    PROBABILITY_OF_SUPERIORITY,
    RATIO_OF_MEANS,
    SPEARMAN_CORRELATION,
)
from test_convert import authorities, coords, result, snapshot

from beliefs import comparability as c


def test_trace_1_tpm_against_log2_plus_one():
    answer = result(coords(), coords(transformation="log2-plus-one"))
    assert isinstance(answer, c.Convertible)
    assert (answer.map.cls, answer.steps, answer.flip, answer.uncertainty) == ("strictly-increasing", (), None, "exact")
    assert c.apply_estimate(answer.steps, Decimal("0.75")) == Decimal("0.75")
    refused = result(coords(), coords(transformation="log2-plus-one"), HODGES_LEHMANN_SHIFT)
    assert isinstance(refused, c.NotConvertible) and refused.reason == "transformation"


def test_constant_mediated_steps():
    answer = result(
        coords("electronvolt"), coords("kilojoule-per-mole"), ARRHENIUS, output=c.OutputTyping("independent", "real")
    )
    assert isinstance(answer, c.Convertible)
    assert answer.steps == (c.Scale(Fraction("96.48533212")),)
    assert answer.uncertainty == "exact" and answer.exact is False
    assert answer.error == Fraction("0.0000000005") and answer.assumptions == ()
    assert c.apply_estimate(answer.steps, Decimal(1)) == Decimal("96.48533212")


def test_log_base_direction_applies():
    forward = result(coords(transformation="ln"), coords(transformation="log2"), DIFFERENCE_OF_MEANS)
    reverse = result(coords(transformation="log2"), coords(transformation="ln"), DIFFERENCE_OF_MEANS)
    assert isinstance(forward, c.Convertible) and isinstance(reverse, c.Convertible)
    assert len(forward.steps) == len(reverse.steps) == 1
    rendered_forward = c.apply_estimate(forward.steps, Decimal(1))
    rendered_reverse = c.apply_estimate(reverse.steps, Decimal(1))
    assert isinstance(rendered_forward, Decimal) and Decimal("1.44269") < rendered_forward < Decimal("1.44270")
    assert isinstance(rendered_reverse, Decimal) and Decimal("0.69314") < rendered_reverse < Decimal("0.69315")


def test_trace_2_same_transformation_both_sides():
    fixed = result(coords(transformation="log2-plus-one"), coords(transformation="log2-plus-one"), HODGES_LEHMANN_SHIFT)
    assert isinstance(fixed, c.Convertible) and fixed.map.cls == "identity" and fixed.steps == ()
    for transformation in ("standardize", "negated-standardize"):
        answer = result(coords(transformation=transformation), coords(transformation=transformation))
        assert isinstance(answer, c.Convertible)
        assert answer.map.cls == "strictly-increasing" and answer.steps == () and answer.flip is None
        assert c.apply_estimate(answer.steps, Decimal("0.75")) == Decimal("0.75")
        refused = result(
            coords(transformation=transformation), coords(transformation=transformation), DIFFERENCE_OF_MEANS
        )
        assert isinstance(refused, c.NotConvertible) and refused.reason == "transformation"
    shifted = result(coords(transformation="log2"), coords("ktpm", "log2"), DIFFERENCE_OF_MEANS)
    assert isinstance(shifted, c.Convertible) and shifted.steps == (c.Scale(Fraction(1)),)
    assert c.apply_estimate(shifted.steps, Decimal("3.75")) == Decimal("3.75")


def test_trace_3_arrhenius():
    ln_a = result(
        coords("per-second"), coords("per-hour"), ARRHENIUS, output=c.OutputTyping("response-log-level", "real")
    )
    assert isinstance(ln_a, c.Convertible)
    shift = Context(prec=34).ln(Decimal(3600))
    assert ln_a.map.scale == 3600 and ln_a.steps == (c.LogShift(shift),)
    response = result(
        coords("per-second"), coords("per-hour"), ARRHENIUS, output=c.OutputTyping("response-level", "real")
    )
    assert isinstance(response, c.Convertible) and response.steps == (c.Scale(Fraction(3600)),)
    assert c.apply_estimate(ln_a.steps, Decimal(2)) == Context(prec=34).add(Decimal(2), shift)
    assert c.apply_standard_error(ln_a.steps, Decimal("0.1")) == Decimal("0.1")
    ea = result(
        coords("electronvolt"), coords("kilojoule-per-mole"), ARRHENIUS, output=c.OutputTyping("independent", "real")
    )
    assert isinstance(ea, c.Convertible)
    assert ea.steps == (c.Scale(Fraction("96.48533212")),) and ea.uncertainty == "exact"
    assert ea.exact is False and ea.error == Fraction("0.0000000005") and ea.assumptions == ()
    assert c.apply_interval(ea.steps, Decimal(1), Decimal(2)) == (Decimal("96.48533212"), Decimal("192.97066424"))
    assert c.apply_covariance(
        {"Ea": ea.steps, "lnA": ln_a.steps}, ("Ea", "lnA"), (Decimal(1), Decimal(2), Decimal(2), Decimal(3))
    ) == (Decimal("9309.4193143067036944"), Decimal("192.97066424"), Decimal("192.97066424"), Decimal(3))
    refused = result(
        coords("kelvin"), coords("celsius"), ARRHENIUS, output=c.OutputTyping("response-log-level", "real")
    )
    assert isinstance(refused, c.NotConvertible) and refused.reason == "transformation"
    for unit in ("celsius", "millikelvin"):
        refused = result(
            coords("kelvin"),
            coords(unit),
            ARRHENIUS,
            binding="independent",
            output=c.OutputTyping("response-log-level", "real"),
        )
        assert isinstance(refused, c.NotConvertible) and refused.reason == "independent-variable map"


def test_trace_4_crosswalk_difference_of_means():
    records, a, b, model = authorities()
    id = records.put(model)
    answer = result(coords(None, scale=a), coords(None, scale=b), DIFFERENCE_OF_MEANS, snap=snapshot(records))
    assert isinstance(answer, c.Convertible)
    assert answer.steps == (c.Scale(Fraction(-2)),) and answer.flip == "negate"
    assert c.apply_estimate(answer.steps, Decimal(1)) == Decimal(-2)
    assert answer.uncertainty == "not-carried: crosswalk"
    assert answer.assumptions[0].particulars["record"] == id
    assert answer.assumptions[0].particulars["error"] == "1.4"


def test_trace_5_flips():
    a, b = coords(transformation="negate"), coords()
    answer = result(a, b, PROBABILITY_OF_SUPERIORITY)
    assert isinstance(answer, c.Convertible) and answer.steps == (c.Flip("complement"),)
    assert c.apply_estimate(answer.steps, Decimal("0.75")) == Decimal("0.25")
    assert c.apply_interval(answer.steps, Decimal("0.45"), Decimal("0.55")) == (Decimal("0.45"), Decimal("0.55"))
    refused = result(a, b, RATIO_OF_MEANS)
    assert isinstance(refused, c.NotConvertible) and refused.reason == "transformation"
    correlation = result(a, b, SPEARMAN_CORRELATION)
    assert isinstance(correlation, c.Convertible) and correlation.steps == (c.Flip("negate"),)
    assert correlation.uncertainty == "needs-operands"


def test_trace_6_levels_and_regions():
    level = replace(DIFFERENCE_OF_MEANS, form="quantity", output="response-level")
    answer = result(coords("kelvin"), coords("celsius"), level)
    assert isinstance(answer, c.Convertible)
    assert answer.steps == (c.Scale(Fraction(1)), c.Shift(Fraction("-273.15")))
    assert c.apply_estimate(answer.steps, Decimal(300)) == Decimal("26.85")
    assert c.apply_interval(answer.steps, Decimal("273.15"), Decimal(300)) == (Decimal(0), Decimal("26.85"))
    difference = result(coords("kelvin"), coords("celsius"), DIFFERENCE_OF_MEANS)
    assert isinstance(difference, c.Convertible) and difference.steps == (c.Scale(Fraction(1)),)
    assert c.apply_interval(difference.steps, Decimal("-0.5"), Decimal("0.5")) == (Decimal("-0.5"), Decimal("0.5"))
    assert c.apply_interval((c.Scale(Fraction(-2)),), Decimal(-1), Decimal(2)) == (Decimal(-4), Decimal(2))
