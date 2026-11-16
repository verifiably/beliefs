"""Quantity accommodation and the separate frozen-key/comparison limits."""

import json
from dataclasses import replace
from decimal import Decimal as D
from fractions import Fraction as F
from pathlib import Path

import pytest
from candidate_contracts import spectral_profile
from test_convert import snapshot

from beliefs import errors, stored
from beliefs.assessment_payload import Interval
from beliefs.claim import Referent, build_claim
from beliefs.estimand import ValueReference, estimand_projection
from beliefs.procedure import SameAs, procedure_from_stored
from beliefs.projection import claim_identity
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.types import SeriesRefused
from beliefs.target_comparison import (
    AssessedProposition,
    PermittedUnder,
    SynthesisRefused,
    TargetConvertible,
    TargetNotConvertible,
    convertibility,
    synthesis,
)

from .spectral_case import build_quantity, fixture_value, freeze_quantity, spectral_case
from .test_spectral_series import raw, table, view_of

RHO = "general/peak-power-fraction"
EXPONENT = "general/signed-aperiodic-exponent"
RESULTS = Path(__file__).resolve().parents[3] / "fixtures/spectral-example-results.json"


@pytest.fixture(scope="module")
def profile(base_contract):
    return spectral_profile(base_contract)


def quantity(s, functional=RHO, reference=None):
    return build_quantity(s, functional=functional, reference=reference or ValueReference(D(0)))


def pair(s, spec):
    return AssessedProposition(s.claim, spec.assessed_target, spec.interpretation_rule)


def context(a, b):
    a.case.records.nodes.update(b.case.records.nodes)
    return {
        "profile": a.profile,
        "snapshot": snapshot(a.case.records, profile=a.profile),
        "snapshot_identity": "snapshot:spectral-fixture",
    }


def test_quantity_origins_and_outputs(profile):
    s = spectral_case(profile)
    for functional, domain in ((RHO, "unit-interval"), (EXPONENT, "real")):
        e = quantity(s, functional)
        assert e.form == "quantity" and set(e.bindings) == {"response"}
        assert e.bindings["response"].series == s.series
        assert e.outputs["estimate"].typing == "dimensionless"
        assert e.outputs["estimate"].domain == domain
        assert e.reference == ValueReference(D(0))
        assert s.applicability.values == {}
        spec = freeze_quantity(s, e)
        assert s.estimator in {d.id for d in spec.assessed_target.dependencies}
        assert all(i.role == "reads" and i.mode in ("simulation", "annotation") for i in spec.input_roles)
        value = fixture_value(spec, estimate=D("0.25") if functional == RHO else D("-1.5"))
        assert value.outcome == "inconclusive" and value.uncertainty is None
        assert e.uncertainty == "interval"  # Schema tag with absent payload, not estimated coverage.


def test_reference_is_mandatory(profile):
    s = spectral_case(profile)
    for f in (RHO, EXPONENT):
        with pytest.raises(errors.EstimandError):
            build_quantity(s, functional=f)


def test_non_event_missing_response_refuses(profile):
    s = spectral_case(profile)
    t = s.case.rewrite(table(s), lambda d: d["channels"]["signal"].update(values=["1", {"missing": True}, "1"]))
    changed = replace(s, series=series_ref_from_projection(view_of(s, t)))
    with pytest.raises(SeriesRefused, match="missing"):
        quantity(changed)


def test_crossed_valid_role_and_series_is_an_owned_gap(profile):
    # beliefs-327ccd: construction checks the graph but does not bind it to the role's dataset.
    a, b = spectral_case(profile), spectral_case(profile, spacing="3600")
    a.case.records.nodes.update(b.case.records.nodes)
    crossed_claim = build_claim(
        profile,
        operator=a.claim.operator,
        roles={"series": Referent("general/series-view", b.series.dataset)},
        form="polar",
        layer="statistical",
    )
    crossed = replace(a, claim=crossed_claim)
    e = quantity(crossed)
    assert e.claim == claim_identity(crossed_claim)
    assert e.bindings["response"].series.dataset == a.series.dataset != b.series.dataset


@pytest.mark.parametrize("damage", ["channel", "coordinates", "index", "absolute", "irregular"])
def test_response_binding_refusals(profile, damage):
    s = spectral_case(profile)
    if damage == "coordinates":
        changed = replace(s, measure=replace(s.measure, value_type="difference"))
    else:
        if damage == "channel":
            ref = s.case.rewrite(series_ref_projection(s.series), lambda d: d.update(channel="absent"))
        else:
            t = raw(s, table(s))
            if damage == "index":
                t.update(axis={"kind": "index"}, coordinates=[0, 1, 2])
            elif damage == "absolute":
                t.update(
                    axis={"kind": "absolute", "convention": "utc-label", "grid": "labels"},
                    coordinates=["2000-01-01T00:00:00Z", "2000-01-01T00:00:01Z", "2000-01-01T00:00:02Z"],
                )
            else:
                t["axis"]["grid"] = {"kind": "irregular"}
                t["coordinates"][2] = "0.025"
            ref = view_of(s, s.case.hold(t))
        changed = replace(s, series=series_ref_from_projection(ref))
    with pytest.raises(SeriesRefused):
        quantity(changed)


def test_freeze_rechecks_held_bytes(profile):
    s = spectral_case(profile)
    e = quantity(s)
    s.case.buffers[table(s)["resource"].split(":")[1]] = b"changed after authoring"
    with pytest.raises(SeriesRefused, match="digest"):
        freeze_quantity(s, e)


def test_illustrative_spectral_arithmetic():
    data = json.loads(RESULTS.read_text())
    fixture = data["arithmetic"]
    bins = list(map(F, fixture["frequency_cycles_per_sample"]))
    power, floor = list(map(F, fixture["observed_linear_power"])), list(map(F, fixture["floor_linear_power"]))
    excess = [
        max(p - f, F(0)) if keep else F(0) for p, f, keep in zip(power, floor, fixture["peak_support"], strict=True)
    ]

    def area(y):
        return sum((b - a) * (u + v) / 2 for a, b, u, v in zip(bins, bins[1:], y, y[1:]))

    assert area(power) > 0
    rho = area(excess) / area(power)
    beta = D(fixture["beta"])
    exponent = -beta
    exponent_interval = tuple(-D(v) for v in reversed(fixture["beta_interval"]))
    physical_band = tuple(F(v) / F(fixture["spacing_seconds"]) for v in fixture["band_cycles_per_sample"])
    assert rho == F(1, 2)
    assert exponent == D("-1.5")
    assert exponent_interval == (D(-2), D(-1))
    assert physical_band == (F(10), F(20))
    assert data["illustrative"] is True and data["fitter_executed"] is False


def test_bound_limited_status_is_not_coverage(profile):
    s = spectral_case(profile)
    source = json.loads(RESULTS.read_text())["bound_limited"]
    assert source["exponent_identified"] is False
    spec = freeze_quantity(s, quantity(s, EXPONENT))
    interval = Interval(*(D(v) for v in source["exponent_interval"]), D("0.95"))
    value = fixture_value(spec, estimate=D(source["exponent"]), uncertainty={"estimate": interval})
    assert value.estimates["estimate"] == D(source["exponent"])
    assert value.outcome == "inconclusive"  # Payload accepts the number; status is not enforced.
    assert fixture_value(spec, estimate=D(source["exponent"])).uncertainty is None


@pytest.mark.parametrize(
    "parameters",
    [{"floor_model": "line"}, {"nperseg": "2"}, {"band_cycles_per_sample": "[0.05,0.2]", "band_hz": "[5,20]"}],
)
def test_estimator_only_changes_separate_keys_but_compare_permissively(profile, parameters):
    # beliefs-db0fed: keys separate, current pairwise comparisons still accept.
    left, right = spectral_case(profile), spectral_case(profile, estimator_parameters=parameters)
    a, b = freeze_quantity(left, quantity(left)), freeze_quantity(right, quantity(right))
    assert claim_identity(left.claim) == claim_identity(right.claim)
    assert estimand_projection(a.estimand) == estimand_projection(b.estimand)
    assert a.identity != b.identity
    assert a.assessed_target.dependencies != b.assessed_target.dependencies
    assert fixture_value(a, estimate=D("0.25")).key() != fixture_value(b, estimate=D("0.25")).key()
    pa, pb = pair(left, a), pair(right, b)
    ctx = context(left, right)
    assert isinstance(convertibility(pa, pb, **ctx), TargetConvertible)
    result = synthesis(pa, pb, observable_proxies=lambda _a, _b: (), **ctx)
    assert isinstance(result, PermittedUnder)
    assert any(
        assumption.kind == "general/procedure-validity" and assumption.particulars["record"] == left.measuring
        for assumption in result.assumptions
    )


def test_raw_channel_procedure_mismatch_refuses(profile):
    left, right = spectral_case(profile), spectral_case(profile)
    authority = procedure_from_stored(right.case.records.nodes[right.measuring])
    second = stored.procedure_node(replace(authority, name="Second raw assay", scale=SameAs(right.measuring)))
    right.case.records.nodes[second.id] = second
    right = replace(right, measure=replace(right.measure, procedure=second.id), measuring=second.id)
    a, b = freeze_quantity(left, quantity(left)), freeze_quantity(right, quantity(right))
    ctx = context(left, right)
    assert isinstance(convertibility(pair(left, a), pair(right, b), **ctx), TargetConvertible)
    result = synthesis(pair(left, a), pair(right, b), observable_proxies=lambda _a, _b: (), **ctx)
    assert isinstance(result, SynthesisRefused) and result.reason == "procedure"


def test_equivalent_time_axes_keep_distinct_graph_targets(profile):
    hours, seconds = (
        spectral_case(profile, axis_unit="si-brochure/hour", spacing="1"),
        spectral_case(profile, spacing="3600"),
    )
    a, b = freeze_quantity(hours, quantity(hours)), freeze_quantity(seconds, quantity(seconds))
    result = convertibility(pair(hours, a), pair(seconds, b), **context(hours, seconds))
    assert isinstance(result, TargetNotConvertible) and result.reason == "target"


def test_selection_changes_view_and_claim(profile):
    s = spectral_case(profile)
    selected = series_ref_from_projection(view_of(s, table(s), (0, 2), selection_procedure=s.estimator))
    claim = build_claim(
        profile,
        operator=s.claim.operator,
        roles={"series": Referent("general/series-view", selected.dataset)},
        form="polar",
        layer="statistical",
    )
    changed = replace(s, series=selected, claim=claim)
    a, b = freeze_quantity(s, quantity(s)), freeze_quantity(changed, quantity(changed))
    assert claim_identity(claim) != claim_identity(s.claim)
    assert a.identity != b.identity
    assert fixture_value(a, estimate=D("0.25")).key() != fixture_value(b, estimate=D("0.25")).key()


def test_reference_variation_changes_target_and_refuses_synthesis(profile):
    s = spectral_case(profile)
    a = freeze_quantity(s, quantity(s))
    b = freeze_quantity(s, quantity(s, reference=ValueReference(D("0.5"))))
    assert a.identity != b.identity
    verdict = synthesis(pair(s, a), pair(s, b), observable_proxies=lambda _a, _b: (), **context(s, s))
    assert isinstance(verdict, SynthesisRefused) and verdict.reason == "reference"
