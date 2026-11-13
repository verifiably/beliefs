"""Exact coordinates, selected extents, UTC labels and support are distinct."""

from decimal import Decimal
from fractions import Fraction

import pytest

from .fixtures import SeriesCase, raw_object


def test_exact_geometry(series_profile, time_roles):
    case = SeriesCase()
    coordinates = [str(Decimal(i) / 100) for i in range(1001)]
    table = case.table(coordinates)
    checked = case.read(case.view(table, list(range(1001))), series_profile, time_roles)
    assert (checked.count, checked.span, checked.spacing_seconds, checked.rate_hz) == (
        1001,
        Fraction(10),
        Fraction(1, 100),
        Fraction(100),
    )
    selected = case.read(
        case.view(table, list(range(0, 1001, 2)), selection_procedure=case.procedure()), series_profile, time_roles
    )
    assert (selected.count, selected.span, selected.spacing_seconds, selected.rate_hz) == (
        501,
        Fraction(10),
        Fraction(1, 50),
        Fraction(50),
    )
    assert len(selected.graph) == 3


@pytest.mark.parametrize(
    "coords,grid,expected",
    [
        (["0", "0.01", "0.025"], {"kind": "irregular"}, None),
        (["0", "3600"], {"kind": "regular", "spacing": "3600"}, Fraction(1, 3600)),
        (["-2", "-1", "0"], {"kind": "regular", "spacing": "1"}, Fraction(1)),
        (["0"], {"kind": "regular", "spacing": "0.01"}, None),
    ],
)
def test_irregular_singleton_and_exact_rational_rate(coords, grid, expected, series_profile, time_roles):
    case = SeriesCase()
    axis = {
        "kind": "elapsed",
        "unit": "si-brochure/second",
        "origin": case.origin(),
        "basis": "synthetic",
        "grid": grid,
    }
    checked = case.read(case.view(case.table(coords, axis=axis), list(range(len(coords)))), series_profile, time_roles)
    assert checked.rate_hz == expected
    assert checked.span == Fraction(coords[-1]) - Fraction(coords[0])


@pytest.mark.parametrize(
    "coords,grid",
    [
        (["0", "0.01", "0.025"], {"kind": "regular", "spacing": "0.01"}),
        (["0", "0"], {"kind": "irregular"}),
        (["1", "0"], {"kind": "irregular"}),
        (["0", "0.02"], {"kind": "regular", "spacing": "0.02", "rate": "100"}),
        (["0", "0.01"], {"kind": "regular", "spacing": "0"}),
        (["0", "0.01"], {"kind": "regular", "spacing": "-1"}),
    ],
)
def test_invalid_grid_refuses(coords, grid, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    axis = {
        "kind": "elapsed",
        "unit": "si-brochure/second",
        "origin": case.origin(),
        "basis": "synthetic",
        "grid": grid,
    }
    with pytest.raises(SeriesRefused):
        case.read(case.view(case.table(coords, axis=axis), list(range(len(coords)))), series_profile, time_roles)


@pytest.mark.parametrize("coords", [[0, 1], ["2026-01-01T00:00:00.09Z", "2026-01-01T00:00:00.1Z"]])
def test_index_and_absolute_never_infer_hz(coords, series_profile, time_roles):
    case = SeriesCase()
    axis = (
        {"kind": "index"}
        if isinstance(coords[0], int)
        else {"kind": "absolute", "convention": "utc-label", "grid": "labels"}
    )
    checked = case.read(case.view(case.table(coords, axis=axis), [0, 1]), series_profile, time_roles)
    assert checked.rate_hz is None
    assert checked.spacing_seconds is None
    if isinstance(coords[0], str):
        assert checked.coordinates == tuple(coords)
        assert checked.span is None


@pytest.mark.parametrize("label", ["2026-02-30T00:00:00Z", "2026-01-01T00:00:60Z", "2026-01-01T00:00:00+00:00"])
def test_bad_utc_label_refuses(label, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    with pytest.raises(SeriesRefused):
        case.read(
            case.view(case.table([label], axis={"kind": "absolute", "convention": "utc-label", "grid": "labels"}), [0]),
            series_profile,
            time_roles,
        )


@pytest.mark.parametrize("unit", ["testing/second", "si-brochure/hertz", "missing/second"])
def test_elapsed_requires_the_licensed_duration_identity(unit, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    axis = {
        "kind": "elapsed",
        "unit": unit,
        "origin": case.origin(),
        "basis": "synthetic",
        "grid": {"kind": "regular", "spacing": "1"},
    }
    with pytest.raises(SeriesRefused):
        case.read(case.view(case.table(["0", "1"], axis=axis), [0, 1]), series_profile, time_roles)


@pytest.mark.parametrize("support", [[["0", "1"], ["1", "2"]], [["0", "2"], ["1", "3"]], [["0", "1"], ["2", "3"]]])
def test_support_validation_preserves_gaps(support, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    axis = {
        "kind": "elapsed",
        "unit": "si-brochure/second",
        "origin": case.origin(),
        "basis": "synthetic",
        "grid": {"kind": "irregular"},
    }
    ref = case.view(case.table(["0.5", "2.5"], axis=axis, support=support), [0, 1])
    if support == [["0", "1"], ["2", "3"]]:
        checked = case.read(ref, series_profile, time_roles)
        assert checked.support == ((Fraction(0), Fraction(1)), (Fraction(2), Fraction(3)))
    else:
        with pytest.raises(SeriesRefused):
            case.read(ref, series_profile, time_roles)


def h_case():
    from test_classification_rule import rule

    from beliefs import stored

    case = SeriesCase()
    axis = {
        "kind": "elapsed",
        "unit": "si-brochure/second",
        "origin": case.origin(),
        "basis": "synthetic",
        "grid": {"kind": "regular", "spacing": "3600"},
    }
    lows = list(range(-172800, 1152000, 3600))
    table = case.table(
        [str(low + 1800) for low in lows], axis=axis, support=[[str(low), str(low + 3600)] for low in lows]
    )
    node = stored.classification_rule_node(rule(classes="testing/level"))
    case.records.nodes[node.id] = node
    anchors = case.hold(
        {
            "format": "science.series-anchors.v1",
            "axis": {key: value for key, value in axis.items() if key != "grid"},
            "rule": node.id,
            "rows": [
                {"key": str(i), "class": {"sort": "testing/level", "term": "EX:event"}, "coordinate": str(at)}
                for i, at in enumerate((0, 720000))
            ],
        }
    )
    return case, case.view(table, list(range(len(lows))), anchors=anchors)


def test_anchor_linkage_geometry(series_profile, time_roles):
    from beliefs.series.geometry import window_memberships

    case, ref = h_case()
    checked = case.read(ref, series_profile, time_roles)
    windows = window_memberships(checked, ((Fraction(-172800), Fraction(0)), (Fraction(86400), Fraction(432000))))
    assert tuple(tuple((row.low, row.high) for row in anchor) for anchor in windows) == (
        ((-172800, 0), (86400, 432000)),
        ((547200, 720000), (806400, 1152000)),
    )
    assert tuple(tuple(len(row.positions) for row in anchor) for anchor in windows) == ((48, 96), (48, 96))
    repeated = window_memberships(checked, ((Fraction(-172800), Fraction(0)), (Fraction(-172800), Fraction(0))))
    assert repeated[0][0].positions == repeated[0][1].positions
    assert len(repeated[0][0].positions) == 48


def test_partial_bins_and_missing_support_refuse_event_coverage(series_profile, time_roles):
    from beliefs.series.geometry import window_memberships
    from beliefs.series.types import SeriesRefused

    case, ref = h_case()
    checked = case.read(ref, series_profile, time_roles)
    with pytest.raises(SeriesRefused):
        window_memberships(checked, ((Fraction(-172799), Fraction(0)),))


@pytest.mark.parametrize(
    "change",
    [
        lambda obj: obj["rows"][1].update(key="0"),
        lambda obj: obj["rows"][1].update(coordinate="0"),
        lambda obj: obj["rows"][0]["class"].update(sort="testing/event"),
        lambda obj: obj["rows"][0]["class"].update(term="NOT-A-MEMBER"),
        lambda obj: obj["axis"].update(basis="native-elapsed"),
    ],
)
def test_anchor_origin_rule_class_and_row_mismatches_refuse(change, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case, ref = h_case()
    descriptor = raw_object(case.buffers[ref["resource"].split(":")[1]])
    anchors = case.rewrite(descriptor["anchors"], change)
    ref = case.rewrite(ref, lambda obj: obj.update(anchors=anchors))
    with pytest.raises(SeriesRefused):
        case.read(ref, series_profile, time_roles)


@pytest.mark.parametrize("missing", ["anchors", "support", "gap"])
def test_event_windows_require_anchors_and_exact_support(missing, series_profile, time_roles):
    from beliefs.series.geometry import window_memberships
    from beliefs.series.types import SeriesRefused

    case, ref = h_case()
    descriptor = raw_object(case.buffers[ref["resource"].split(":")[1]])
    if missing == "anchors":
        ref = case.rewrite(ref, lambda obj: obj.pop("anchors"))
    else:

        def change(obj):
            if missing == "support":
                obj.pop("support")
            else:
                obj["support"][0][0] = "-172799"

        table = case.rewrite(descriptor["table"], change)
        ref = case.rewrite(ref, lambda obj: obj.update(table=table))
    checked = case.read(ref, series_profile, time_roles)
    with pytest.raises(SeriesRefused):
        window_memberships(checked, ((Fraction(-172800), Fraction(0)),))


@pytest.mark.parametrize(
    "change",
    [
        lambda axis: axis.update(basis="clock-derived"),
        lambda axis: axis["origin"].update(timestamp="2026-01-01T00:00:00Z"),
    ],
)
def test_timestamp_origins_and_undeclared_clock_basis_refuse(change, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    axis = {
        "kind": "elapsed",
        "unit": "si-brochure/second",
        "origin": case.origin(),
        "basis": "synthetic",
        "grid": {"kind": "regular", "spacing": "1"},
    }
    change(axis)
    with pytest.raises(SeriesRefused):
        case.read(case.view(case.table(["0", "1"], axis=axis), [0, 1]), series_profile, time_roles)


def test_same_time_names_with_another_defining_source_refuse(base_contract, testing_document, time_roles):
    from time_roles_fixture import time_document

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.profile import compile_profile
    from beliefs.series.types import SeriesRefused

    document = time_document()
    document["defining_source"]["id"] = "urn:other:source"
    profile = compile_profile(
        base_contract,
        [
            parse_domain_contract(testing_document, source="<testing>", base=base_contract, predecessor=None),
            parse_domain_contract(document, source="<wrong source>", base=base_contract, predecessor=None),
        ],
    )
    case = SeriesCase()
    with pytest.raises(SeriesRefused, match="defining source"):
        case.read(case.view(case.table(["0", "0.01"]), [0, 1]), profile, time_roles)


def test_public_reader_requires_compiled_profile_and_explicit_evidence(series_profile):
    from types import SimpleNamespace

    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.reader import read_series
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    ref = series_ref_from_projection(case.view(case.table(["0", "0.01"]), [0, 1]))
    with pytest.raises(SeriesRefused) as caught:
        read_series(ref, profile=series_profile, records=case.records, evidence=None)  # pyright: ignore[reportArgumentType]
    assert caught.value.code == "evidence-unavailable"
    with pytest.raises(SeriesRefused, match="compiled"):
        read_series(ref, profile=SimpleNamespace(), records=case.records, evidence=case.evidence())  # pyright: ignore[reportArgumentType]


def test_missing_anchor_rule_preserves_dependency_not_held(series_profile, time_roles):
    from beliefs.errors import DependencyNotHeld

    case, ref = h_case()
    descriptor = raw_object(case.buffers[ref["resource"].split(":")[1]])
    anchors = case.rewrite(descriptor["anchors"], lambda obj: obj.update(rule="classification-rule:" + "f" * 64))
    ref = case.rewrite(ref, lambda obj: obj.update(anchors=anchors))
    with pytest.raises(DependencyNotHeld):
        case.read(ref, series_profile, time_roles)
