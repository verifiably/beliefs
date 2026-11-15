"""Coverage is computed from checked bytes, including every excluded candidate."""

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F

import pytest
from fixtures_cut3 import typed_estimand
from test_estimand import context as context  # noqa: PLC0414

from beliefs.errors import ScienceError
from beliefs.estimand import LagBinding, MeasuredBinding, check_series, estimand_from_stored, estimand_projection
from beliefs.identity import v1
from beliefs.restriction import IntervalRestriction
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.types import SeriesRefused

from .fixtures import raw_object
from .test_authoring import event_case
from .test_geometry import h_case


def build(case, bindings, profile, **kwargs):
    return typed_estimand(
        profile=profile,
        records=case.records,
        form="event-locked",
        functional="testing/window-difference-against-control",
        bindings=bindings,
        series_evidence=case.evidence(),
        **{"coverage_policy": "complete-windows", **kwargs},
    )


def diagnose(case, bindings, profile, **kwargs):
    from beliefs.estimand import diagnose_event_coverage

    return diagnose_event_coverage(
        **bindings,
        profile=profile,
        records=case.records,
        evidence=case.evidence(),
        **{"coverage_policy": "complete-windows", **kwargs},
    )


def test_coverage_priority_and_memberships(series_profile, time_roles):
    from beliefs.series.coverage import compute_coverage

    case, ref = h_case()
    view = raw_object(case.buffers[ref["resource"].split(":")[1]])

    def geometry(obj):
        obj["coordinates"] = ["0", "1", "3", "4", "5"]
        obj["support"] = [["0", "1"], ["1", "2"], ["3", "4"], ["4", "5"], ["5", "6"]]
        obj["channels"]["signal"]["values"] = ["1", "2", {"missing": True}, "4", "5"]
        obj["axis"]["grid"] = {"kind": "irregular"}

    table = case.rewrite(view["table"], geometry)
    anchors = case.rewrite(view["anchors"], lambda obj: obj.update(rows=obj["rows"][:1]))
    ref = case.rewrite(ref, lambda obj: obj.update(table=table, anchors=anchors, selection=list(range(5))))
    checked = case.read(ref, series_profile, time_roles)
    windows = ((-1, 1), (2, 3), (F(1, 2), 4), (1, 4), (3, 4), (4, 6))
    result = compute_coverage(checked, tuple((F(a), F(b)) for a, b in windows))
    assert result.coverage.report[0].windows == (
        "outside-support",
        "outside-support",
        "partial-bin",
        "support-gap",
        "missing-value",
        "complete",
    )
    assert result.retained_keys == () and result.memberships == ()
    complete = compute_coverage(checked, ((F(4), F(6)), (F(5), F(6))))
    assert complete.retained_keys == ("0",)
    assert tuple(tuple(row.positions) for row in complete.memberships[0]) == ((3, 4), (4,))
    assert complete.graph == checked.graph


def test_all_excluded_diagnostic_does_not_mint(context):
    case, bindings = event_case(context)
    bindings["lag"] = LagBinding(
        "si-brochure/hour", (IntervalRestriction("si-brochure/hour", F(1000), F(1001), True, False),) * 2
    )
    result = diagnose(case, bindings, context)
    assert result.retained_keys == ()
    assert [row.windows for row in result.coverage.report] == [
        ("outside-support", "outside-support"),
        ("outside-support", "outside-support"),
    ]
    with pytest.raises(SeriesRefused, match="retained"):
        build(case, bindings, context)


@pytest.mark.parametrize("policy", [None, "drop", 1, {}])
def test_coverage_policy_is_explicit_and_scoped(policy, context):
    case, bindings = event_case(context)
    with pytest.raises(SeriesRefused, match="coverage_policy"):
        build(case, bindings, context, coverage_policy=policy)
    with pytest.raises(SeriesRefused, match="coverage_policy"):
        diagnose(case, bindings, context, coverage_policy=policy)


def test_policy_forbidden_on_other_targets(context):
    with pytest.raises(SeriesRefused, match="coverage_policy"):
        typed_estimand(coverage_policy="complete-windows")
    case, bindings = event_case(context)
    bindings["response"] = replace(bindings["response"], series=None)
    with pytest.raises(SeriesRefused, match="coverage_policy"):
        build(case, bindings, context)
    assert build(case, bindings, context, coverage_policy=None).event_coverage is None


def test_coverage_requires_full_response_chain(context):
    case, bindings = event_case(context)
    ref = series_ref_projection(bindings["response"].series)
    selected = case.rewrite(
        ref, lambda obj: obj.update(selection=obj["selection"][1:], selection_procedure=case.procedure())
    )
    bindings["response"] = replace(bindings["response"], series=series_ref_from_projection(selected))
    with pytest.raises(SeriesRefused, match="full"):
        diagnose(case, bindings, context)
    with pytest.raises(SeriesRefused, match="full"):
        build(case, bindings, context)


def test_one_view_two_lags_and_report_tampering(context):
    case, bindings = event_case(context)
    first = build(case, bindings, context)
    bindings["lag"] = LagBinding(
        "si-brochure/hour", (IntervalRestriction("si-brochure/hour", F(-49), F(0), True, False),) * 2
    )
    second = build(case, bindings, context)
    assert first.series_graph == second.series_graph
    assert first.event_coverage != second.event_coverage
    assert v1.encode(estimand_projection(first)) != v1.encode(estimand_projection(second))
    assert second.event_coverage is not None
    assert second.event_coverage.report[0].windows == ("outside-support", "outside-support")
    assert diagnose(case, bindings, context).retained_keys == ("1",)
    body = raw_object(v1.encode(estimand_projection(second)))
    body["event_coverage"]["report"][0]["windows"] = ["complete", "complete"]
    forged = estimand_from_stored(body, profile=context)
    with pytest.raises(SeriesRefused, match="coverage"):
        check_series(forged, profile=context, records=case.records, evidence=case.evidence())


@pytest.mark.parametrize(
    "edit",
    [
        lambda b: b.pop("event_coverage"),
        lambda b: b.update(event_coverage=None),
        lambda b: b["event_coverage"].update(extra=True),
        lambda b: b["event_coverage"].update(policy="guess"),
        lambda b: b["event_coverage"]["report"].append(b["event_coverage"]["report"][0]),
        lambda b: b["event_coverage"]["report"][0].update(windows=["complete"]),
        lambda b: b["event_coverage"]["report"][0].update(windows=["other", "complete"]),
        lambda b: b["event_coverage"].update(report=[]),
        lambda b: [row.update(windows=["missing-value", "complete"]) for row in b["event_coverage"]["report"]],
    ],
)
def test_report_stored_shape(edit, context):
    case, bindings = event_case(context)
    body = deepcopy(estimand_projection(build(case, bindings, context)))
    edit(body)
    with pytest.raises(ScienceError):
        estimand_from_stored(body, profile=context)


def test_report_bounds(series_profile, time_roles):
    from beliefs.series.coverage import compute_coverage, coverage_from_projection

    case, ref = h_case()
    checked = case.read(ref, series_profile, time_roles)
    with pytest.raises(SeriesRefused, match="100000"):
        compute_coverage(checked, ((F(0), F(1)),) * 50001)
    with pytest.raises(ScienceError, match="16 MiB"):
        coverage_from_projection(
            {
                "policy": "complete-windows",
                "report": [{"key": str(i) + "x" * 1700, "windows": ["complete"]} for i in range(10000)],
            },
            window_count=1,
        )


def test_non_event_missing_values_refuse(author_profile):
    from .test_authoring import author_case

    case, value = author_case(author_profile)
    response = value.bindings["response"]
    assert isinstance(response, MeasuredBinding) and response.series is not None
    view = raw_object(case.buffers[response.series.resource.split(":")[1]])
    table = case.rewrite(
        view["table"], lambda obj: obj["channels"]["signal"].update(values=["1", {"missing": True}, "3"])
    )
    ref = case.rewrite(series_ref_projection(response.series), lambda obj: obj.update(table=table))
    with pytest.raises(SeriesRefused, match="missing"):
        typed_estimand(
            profile=author_profile,
            records=case.records,
            bindings={**value.bindings, "response": replace(response, series=series_ref_from_projection(ref))},
            series_evidence=case.evidence(),
        )


@pytest.mark.parametrize("change", ["missing-support", "malformed-support", "wrong-rule"])
def test_invalid_evidence_is_never_an_exclusion(change, context):
    case, bindings = event_case(context)
    ref = series_ref_projection(bindings["response"].series)
    assert isinstance(ref["resource"], str)
    view = raw_object(case.buffers[ref["resource"].split(":")[1]])
    if change == "wrong-rule":
        bindings["anchor"] = replace(bindings["anchor"], rule="classification-rule:" + "a" * 64)
    else:

        def edit(obj):
            if change == "missing-support":
                obj.pop("support")
            else:
                obj["support"][0][1] = obj["support"][0][0]

        table = case.rewrite(view["table"], edit)
        ref = case.rewrite(ref, lambda obj: obj.update(table=table))
        bindings["response"] = replace(bindings["response"], series=series_ref_from_projection(ref))
    with pytest.raises(ScienceError):
        diagnose(case, bindings, context)


def test_clock_mapped_coverage_and_sparse_source_refusal(series_profile, time_roles):
    from beliefs.series.coverage import compute_coverage

    from .test_clock import mapped_case

    case, ref, _clock, procedure = mapped_case()
    checked = case.read(ref, series_profile, time_roles)
    assert compute_coverage(checked, ((F(0), F(2)), (F(2), F(3)))).retained_keys == ("first",)
    view = raw_object(case.buffers[ref["resource"].split(":")[1]])
    source = case.rewrite(
        view["transform"]["source"], lambda obj: obj.update(selection=[0], selection_procedure=procedure)
    )
    ref = case.rewrite(
        ref,
        lambda obj: obj.update(
            selection=[0], selection_procedure=procedure, transform={**obj["transform"], "source": source}
        ),
    )
    checked = case.read(ref, series_profile, time_roles)
    with pytest.raises(SeriesRefused, match="full"):
        compute_coverage(checked, ((F(0), F(2)),))


def test_materialized_select_forbidden_for_event_response(context):
    case, bindings = event_case(context)
    ref = series_ref_projection(bindings["response"].series)
    source = case.rewrite(ref, lambda obj: obj.pop("anchors"))
    ref = case.rewrite(
        ref,
        lambda obj: obj.update(
            transform={
                "operation": "select",
                "source": source,
                "procedure": case.procedure(),
                "mapping": list(range(len(obj["selection"]))),
            }
        ),
    )
    bindings["response"] = replace(bindings["response"], series=series_ref_from_projection(ref))
    with pytest.raises(SeriesRefused, match="select/rebin"):
        diagnose(case, bindings, context)


def test_wide_overlapping_memberships_keep_bounded_storage(series_profile, time_roles):
    from sys import getsizeof

    from beliefs.series.coverage import compute_coverage

    case, ref = h_case()
    view = raw_object(case.buffers[ref["resource"].split(":")[1]])

    def table_rows(obj):
        obj["coordinates"] = [str(i) for i in range(5000)]
        obj["support"] = [[str(i), str(i + 1)] for i in range(5000)]
        obj["channels"]["signal"]["values"] = ["1"] * 5000
        obj["axis"]["grid"] = {"kind": "regular", "spacing": "1"}

    def anchor_rows(obj):
        row = obj["rows"][0]
        obj["rows"] = [{**row, "key": str(i), "coordinate": str(i)} for i in range(100)]

    table = case.rewrite(view["table"], table_rows)
    anchors = case.rewrite(view["anchors"], anchor_rows)
    ref = case.rewrite(ref, lambda obj: obj.update(table=table, anchors=anchors, selection=list(range(5000))))
    checked = case.read(ref, series_profile, time_roles)
    result = compute_coverage(checked, ((F(0), F(2000)), (F(1000), F(4000))))
    assert len(result.retained_keys) == 100
    assert all(row.windows == ("complete", "complete") for row in result.coverage.report)
    first, second = result.memberships[0]
    assert (len(first.positions), first.positions[0], first.positions[-1]) == (2000, 0, 1999)
    assert (len(second.positions), second.positions[0], second.positions[-1]) == (3000, 1000, 3999)
    assert tuple(first.positions[1000:]) == tuple(second.positions[:1000])
    assert result.memberships[-1][1].positions[-1] == 4098
    # A modest valid input must not copy half a million positions merely to
    # report 200 complete cells. The bound counts containers, not shared ints.
    assert sum(getsizeof(row.positions) for rows in result.memberships for row in rows) < 100_000
