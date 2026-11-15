"""Materialized select copies rows; rebin validates coverage, not averages."""

from fractions import Fraction

import pytest

from .fixtures import SeriesCase


def test_select_and_rebin_provenance(series_profile, time_roles):
    case = SeriesCase()
    source_table = case.table(["0", "0.01", "0.02"])
    source = case.view(source_table, [0, 1, 2])
    table = case.table(
        ["0", "0.02"],
        axis={
            "kind": "elapsed",
            "unit": "si-brochure/second",
            "origin": case.origin(),
            "basis": "synthetic",
            "grid": {"kind": "regular", "spacing": "0.02"},
        },
    )
    ref = case.view(
        table,
        [0, 1],
        transform={"source": source, "procedure": case.procedure(), "operation": "select", "mapping": [0, 2]},
    )
    assert case.read(ref, series_profile, time_roles).rate_hz == 50
    bad = case.view(
        table,
        [0, 1],
        transform={"source": source, "procedure": case.procedure(), "operation": "select", "mapping": [0, 1]},
    )
    from beliefs.series.types import SeriesRefused

    with pytest.raises(SeriesRefused):
        case.read(bad, series_profile, time_roles)


@pytest.mark.parametrize("count", [12, 60])
def test_rebin_accepts_rounded_values_without_reexecution(count, series_profile, time_roles):
    case = SeriesCase()
    axis = {
        "kind": "elapsed",
        "unit": "si-brochure/second",
        "origin": case.origin(),
        "basis": "synthetic",
        "grid": {"kind": "regular", "spacing": "1"},
    }
    table = case.table(
        [str(i) + ".5" for i in range(count)],
        axis=axis,
        support=[[str(i), str(i + 1)] for i in range(count)],
        values=["0"] * (count - 1) + ["1"],
    )
    source = case.view(table, list(range(count)))
    output_axis = {**axis, "grid": {"kind": "irregular"}}
    output = case.table(["0.5"], axis=output_axis, support=[["0", str(count)]], values=["0.083333"])
    ref = case.view(
        output,
        [0],
        transform={
            "source": source,
            "procedure": case.procedure(),
            "operation": "rebin",
            "mapping": [list(range(count))],
        },
    )
    checked = case.read(ref, series_profile, time_roles)
    assert checked.values == (Fraction("0.083333"),)


@pytest.mark.parametrize(
    "operation,mapping",
    [("clock-map", [0]), ("filter", [0]), ("select", [1, 0]), ("select", [0, 0]), ("rebin", [[0], [0]])],
)
def test_bad_transforms_refuse(operation, mapping, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    source = case.view(case.table(["0", "0.01"]), [0, 1])
    with pytest.raises(SeriesRefused):
        case.read(
            case.view(
                case.table(["0", "0.01"]),
                [0, 1],
                transform={"source": source, "procedure": case.procedure(), "operation": operation, "mapping": mapping},
            ),
            series_profile,
            time_roles,
        )


def test_subset_procedure_required_and_full_selection_procedure_refuses(series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    table = case.table(["0", "0.01"])
    for ref in (case.view(table, [0]), case.view(table, [0, 1], selection_procedure=case.procedure())):
        with pytest.raises(SeriesRefused):
            case.read(ref, series_profile, time_roles)


@pytest.mark.parametrize(
    "change",
    [
        lambda obj: obj["channels"]["signal"].update(values=["9", "9"]),
        lambda obj: obj["channels"]["signal"]["coordinates"].update(
            quantity_kind="testing/fraction", unit="testing/unity"
        ),
        lambda obj: obj["axis"].update(basis="native-elapsed"),
    ],
)
def test_materialized_select_cannot_relabel_or_compute(change, series_profile, time_roles):
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    table = case.table(["0", "0.01"])
    source = case.view(table, [0, 1])
    output = case.rewrite(table, change)
    ref = case.view(
        output,
        [0, 1],
        transform={"source": source, "procedure": case.procedure(), "operation": "select", "mapping": [0, 1]},
    )
    with pytest.raises(SeriesRefused):
        case.read(ref, series_profile, time_roles)


def test_select_copies_missing_and_rebin_refuses_it(series_profile, time_roles):
    from beliefs.series.types import MissingValue, SeriesRefused

    case = SeriesCase()
    source = case.view(
        case.table(["0", "0.01"], values=[{"missing": True}, "2"], support=[["0", "0.01"], ["0.01", "0.02"]]), [0, 1]
    )
    output = case.table(["0"], values=[{"missing": True}], support=[["0", "0.01"]])
    selected = case.view(
        output, [0], transform={"source": source, "procedure": case.procedure(), "operation": "select", "mapping": [0]}
    )
    assert isinstance(case.read(selected, series_profile, time_roles).values[0], MissingValue)
    rebinned = case.view(
        case.table(["0"], values=["2"], support=[["0", "0.02"]]),
        [0],
        transform={"source": source, "procedure": case.procedure(), "operation": "rebin", "mapping": [[0, 1]]},
    )
    with pytest.raises(SeriesRefused, match="missing"):
        case.read(rebinned, series_profile, time_roles)
