"""Exact declared UTC offset arithmetic and held clock provenance."""

import json
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path

import pytest

from beliefs.identity import v1
from beliefs.series.codec import decode_series_object
from beliefs.series.types import SeriesRefused

from .fixtures import SeriesCase, objects

EPOCH = "2016-12-31T23:59:59Z"
MIDNIGHT = "2017-01-01T00:00:00Z"


def clock_document(procedure="procedure:" + "a" * 64, *, offset=11):
    return {
        "format": "science.series-clock-map.v1",
        "convention": "utc-tai",
        "low": EPOCH,
        "high": "2017-01-02T00:00:00Z",
        "procedure": procedure,
        "segments": [{"from": EPOCH, "tai_minus_utc": 10}, {"from": MIDNIGHT, "tai_minus_utc": offset}],
    }


def test_clock_exact_boundaries():
    clock = decode_series_object(v1.encode(clock_document()))
    from beliefs.series.clock import clock_coordinate
    from beliefs.series.types import ClockMap

    assert isinstance(clock, ClockMap)
    assert clock_coordinate(clock, MIDNIGHT, epoch=EPOCH, seconds_per_unit=F(1)) == 2
    assert clock_coordinate(clock, MIDNIGHT, epoch="2016-12-31T23:59:59.5Z", seconds_per_unit=F(1)) == F(3, 2)
    assert clock_coordinate(clock, MIDNIGHT, epoch=EPOCH, seconds_per_unit=F(2)) == 1
    with pytest.raises(SeriesRefused, match="finite decimal"):
        clock_coordinate(clock, MIDNIGHT, epoch=EPOCH, seconds_per_unit=F(3))
    for label in ["2016-12-31T23:59:58Z", "2017-01-02T00:00:00Z", "2016-12-31T23:59:60Z", "2017-01-01T01:00:00+01:00"]:
        with pytest.raises(SeriesRefused):
            clock_coordinate(clock, label, epoch=EPOCH, seconds_per_unit=F(1))
        with pytest.raises(SeriesRefused):
            clock_coordinate(clock, MIDNIGHT, epoch=label, seconds_per_unit=F(1))


def test_negative_leap_missing_second_refuses():
    from beliefs.series.clock import clock_coordinate
    from beliefs.series.types import ClockMap

    doc = clock_document(offset=9)
    doc["low"] = doc["segments"][0]["from"] = "2016-12-31T23:59:58Z"
    clock = decode_series_object(v1.encode(doc))
    assert isinstance(clock, ClockMap)
    for label in [EPOCH, "2016-12-31T23:59:59.5Z", "2016-12-31T23:59:59.999Z"]:
        with pytest.raises(SeriesRefused, match="nonexistent"):
            clock_coordinate(clock, label, epoch=doc["low"], seconds_per_unit=F(1))
    assert clock_coordinate(clock, MIDNIGHT, epoch=doc["low"], seconds_per_unit=F(1)) == 1


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(convention="gps"),
        lambda d: d.update(low="1971-12-31T23:59:59Z"),
        lambda d: d.update(high=d["low"]),
        lambda d: d["segments"][0].update(tai_minus_utc=True),
        lambda d: d["segments"][1].update(tai_minus_utc=10),
        lambda d: d["segments"][1].update(tai_minus_utc=12),
        lambda d: d["segments"][1].update(**{"from": "2017-01-01T00:00:01Z"}),
        lambda d: d["segments"][1].update(**{"from": "2017-01-01T00:00:00.0Z"}),
        lambda d: d["segments"][1].update(**{"from": d["low"]}),
        lambda d: d.update(segments=[]),
        lambda d: d.update(extra=1),
    ],
)
def test_clock_shape_is_closed(change):
    doc = clock_document()
    change(doc)
    with pytest.raises(SeriesRefused):
        decode_series_object(v1.encode(doc))


def mapped_case(
    *,
    missing=False,
    raw_epoch="2016-12-31T23:59:60Z",
    definition="Start of the containing second",
    anchor_coordinate=EPOCH,
    mapped_anchor="0",
):
    case = SeriesCase()
    procedure = case.procedure(definition=definition)
    clock = case.hold(clock_document(procedure))
    origin = {
        "source": case.hold(
            {
                "format": "science.series-origins.v2",
                "origins": {
                    "zero": {"label": "A freely named experiment epoch", "clock": {"map": clock, "epoch": EPOCH}},
                },
            }
        ),
        "key": "zero",
    }
    values = [{"missing": True}, "2"] if missing else ["1", "2"]
    absolute = {"kind": "absolute", "convention": "utc-label", "grid": "labels"}
    axis = {
        "kind": "elapsed",
        "unit": "si-brochure/second",
        "origin": origin,
        "basis": "clock-mapped",
        "grid": {"kind": "irregular"},
    }
    source_table = case.table(
        [EPOCH, MIDNIGHT], axis=absolute, values=values, support=[[EPOCH, MIDNIGHT], [MIDNIGHT, "2017-01-01T00:00:01Z"]]
    )
    source = case.view(source_table, [0, 1])
    output = case.table(["0", "2"], axis=axis, values=values, support=[["0", "2"], ["2", "3"]])
    transform = {"source": source, "procedure": procedure, "operation": "clock-map"}
    from beliefs import stored
    from beliefs.classification_rule import ClassificationRule

    rule_node = stored.classification_rule_node(
        ClassificationRule("testing/event", (), "Synthetic event classes", None, None, "synthetic annotator")
    )
    case.records.nodes[rule_node.id] = rule_node
    provenance = {"procedure": procedure, "epoch_definition": definition}
    source_anchors = {
        "format": "science.series-anchors.v2",
        "axis": absolute,
        "rule": rule_node.id,
        "provenance": provenance,
        "rows": [
            {
                "key": "first",
                "class": {"sort": "testing/event", "term": "EX:onset"},
                "coordinate": anchor_coordinate,
                "source_epoch": raw_epoch,
            }
        ],
    }
    anchors = {
        **source_anchors,
        "axis": {k: v for k, v in axis.items() if k != "grid"},
        "rows": [{**source_anchors["rows"][0], "coordinate": mapped_anchor}],
        "transform": {"source": case.hold(source_anchors), "procedure": procedure, "operation": "clock-map"},
    }
    view = case.view(output, [0, 1], transform=transform, anchors=case.hold(anchors))
    return case, view, clock, procedure


def test_mapped_pairs_and_provenance(series_profile, time_roles):
    case, view, _, _ = mapped_case(missing=True)
    checked = case.read(view, series_profile, time_roles)
    from beliefs.series.types import MissingValue

    assert checked.coordinates == (F(0), F(2))
    assert isinstance(checked.values[0], MissingValue)
    assert checked.support == ((F(0), F(2)), (F(2), F(3)))
    source_epoch = checked.anchors[0].source_epoch
    assert source_epoch is not None and source_epoch.endswith(":60Z")
    assert checked.anchors[0].coordinate == 0


def test_clock_graph_dependencies(series_profile, time_roles):
    case, view, clock, procedure = mapped_case()
    checked = case.read(view, series_profile, time_roles)
    from beliefs.series.codec import series_ref_from_projection

    row = next(r for r in checked.graph if r.ref == series_ref_from_projection(clock))
    assert row.format == "science.series-clock-map.v1"
    assert row.links == row.terms == ()
    assert row.records == (procedure,)
    assert len(checked.predecessors) == 1


def test_consumer_defined_epoch_is_visible(series_profile, time_roles):
    first, a, _, _ = mapped_case(raw_epoch="2016-12-31T23:59:59.5Z")
    second, b, _, _ = mapped_case(
        raw_epoch="2016-12-31T23:59:59.5Z",
        definition="Exact catalogue label",
        anchor_coordinate="2016-12-31T23:59:59.5Z",
        mapped_anchor="0.5",
    )
    x, y = first.read(a, series_profile, time_roles), second.read(b, series_profile, time_roles)
    assert a != b and x.graph != y.graph
    assert x.anchors[0].source_epoch == y.anchors[0].source_epoch
    assert x.anchors[0].coordinate != y.anchors[0].coordinate


def test_missing_marker_identity_roundtrip():
    from beliefs.series.types import MissingValue, Table

    doc = deepcopy(objects()[1])
    doc["format"] = "science.series-table.v2"
    doc["channels"]["signal"]["values"][0] = {"missing": True}
    encoded = v1.encode(doc)
    assert v1.encode(v1.decode(encoded)) == encoded
    parsed = decode_series_object(encoded)
    assert isinstance(parsed, Table) and isinstance(parsed.channels["signal"].values[0], MissingValue)
    for bad in [{"missing": False}, {"missing": True, "extra": 1}, "missing", -9999]:
        doc["channels"]["signal"]["values"][0] = bad
        with pytest.raises(SeriesRefused):
            decode_series_object(v1.encode(doc))


@pytest.mark.parametrize("value", json.loads((Path(__file__).parents[1] / "fixtures/series-v1.json").read_text()))
def test_pre_v2_series_refused_by_name(value):
    with pytest.raises(SeriesRefused) as caught:
        decode_series_object(v1.encode(value))
    assert caught.value.code == "pre-v2-series"


def _raw(case, ref):
    from .fixtures import raw_object

    return raw_object(case.buffers[ref["resource"].split(":")[1]])


@pytest.mark.parametrize(
    "change",
    [
        "values",
        "coordinate",
        "support",
        "selection",
        "mapping",
        "original",
        "transformed-source",
        "absolute-anchors",
        "different-origin",
        "source-epoch",
        "provenance",
        "duplicate-anchor",
        "parsed-leap-label",
        "coverage-endpoint",
    ],
)
def test_mapped_route_refuses_contradictions(change, series_profile, time_roles):
    case, ref, _, procedure = mapped_case()
    view = _raw(case, ref)
    table = _raw(case, view["table"])
    anchors = _raw(case, view["anchors"])
    if change == "values":
        table["channels"]["signal"]["values"][0] = "99"
    elif change == "coordinate":
        table["coordinates"][1] = "2.5"
    elif change == "support":
        table["support"][0][1] = "1"
    elif change == "selection":
        view.update(selection=[0], selection_procedure=procedure)
    elif change == "mapping":
        view["transform"]["mapping"] = [0, 1]
    elif change == "original":
        del view["transform"]
    elif change == "transformed-source":
        source = _raw(case, view["transform"]["source"])
        source["transform"] = {
            "source": view["transform"]["source"],
            "procedure": procedure,
            "operation": "select",
            "mapping": [0, 1],
        }
        view["transform"]["source"] = case.hold(source)
    elif change == "absolute-anchors":
        source = _raw(case, view["transform"]["source"])
        source["anchors"] = anchors["transform"]["source"]
        view["transform"]["source"] = case.hold(source)
    elif change == "different-origin":
        origin = _raw(case, table["axis"]["origin"]["source"])
        origin["origins"]["zero"]["label"] = "Another label with the same epoch"
        table["axis"]["origin"]["source"] = case.hold(origin)
    elif change == "source-epoch":
        anchors["rows"][0]["source_epoch"] = EPOCH
    elif change == "provenance":
        anchors["provenance"]["epoch_definition"] = "A changed assertion"
    elif change == "duplicate-anchor":
        anchors["rows"].append({**anchors["rows"][0], "key": "second"})
    elif change == "parsed-leap-label":
        prior = _raw(case, anchors["transform"]["source"])
        prior["rows"][0]["coordinate"] = "2016-12-31T23:59:60Z"
        anchors["transform"]["source"] = case.hold(prior)
    elif change == "coverage-endpoint":
        source = _raw(case, view["transform"]["source"])
        prior = _raw(case, source["table"])
        prior["support"][-1][1] = "2017-01-02T00:00:00Z"
        source["table"] = case.hold(prior)
        view["transform"]["source"] = case.hold(source)
    view["table"], view["anchors"] = case.hold(table), case.hold(anchors)
    with pytest.raises(SeriesRefused):
        case.read(case.hold(view), series_profile, time_roles)


def test_unused_origin_map_is_not_consulted(series_profile, time_roles):
    case, ref, _, _ = mapped_case()
    view = _raw(case, ref)
    table = _raw(case, view["table"])
    origins = _raw(case, table["axis"]["origin"]["source"])
    from .fixtures import ref_value

    origins["origins"]["unused"] = {"label": "Not consulted", "clock": {"map": ref_value(b"not held"), "epoch": EPOCH}}
    origin_ref = case.hold(origins)
    table["axis"]["origin"]["source"] = origin_ref
    anchors = _raw(case, view["anchors"])
    anchors["axis"]["origin"]["source"] = origin_ref
    view["table"], view["anchors"] = case.hold(table), case.hold(anchors)
    assert case.read(case.hold(view), series_profile, time_roles).coordinates == (F(0), F(2))


def test_clock_map_graph_rejects_extra_links_and_terms(series_profile, time_roles):
    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.graph import graph_from_projection, graph_projection

    case, ref, _, _ = mapped_case()
    graph = graph_projection(case.read(ref, series_profile, time_roles).graph)
    for member, value in [("terms", ["testing/count"]), ("links", [ref]), ("records", [])]:
        changed = deepcopy(graph)
        row = next(r for r in changed if r["format"] == "science.series-clock-map.v1")
        row[member] = value
        with pytest.raises(SeriesRefused):
            graph_from_projection(changed, roots=(series_ref_from_projection(ref),))


def test_clock_checks_only_selected_pairs(series_profile, time_roles):
    case, ref, _, procedure = mapped_case()
    view = _raw(case, ref)
    source = _raw(case, view["transform"]["source"])
    source.update(selection=[0], selection_procedure=procedure)
    view.update(selection=[0], selection_procedure=procedure)
    view["transform"]["source"] = case.hold(source)
    table = _raw(case, view["table"])
    table["channels"]["signal"]["values"][1] = "99"
    view["table"] = case.hold(table)
    assert case.read(case.hold(view), series_profile, time_roles).values == (F(1),)
    source.update(selection=[0, 1])
    del source["selection_procedure"]
    view.update(selection=[0, 1])
    del view["selection_procedure"]
    view["transform"]["source"] = case.hold(source)
    with pytest.raises(SeriesRefused, match="selected values"):
        case.read(case.hold(view), series_profile, time_roles)


@pytest.mark.parametrize("operation,mapping", [("select", [0, 1]), ("rebin", [[0], [1]])])
def test_mapped_select_and_rebin_are_refused(operation, mapping, series_profile, time_roles):
    case, ref, _, procedure = mapped_case()
    view = _raw(case, ref)
    view["transform"] = {"source": ref, "procedure": procedure, "operation": operation, "mapping": mapping}
    with pytest.raises(SeriesRefused, match="clock-map transform"):
        case.read(case.hold(view), series_profile, time_roles)


@pytest.mark.parametrize("location", ["map", "view-transform", "anchor-transform", "anchor-provenance"])
def test_clock_route_requires_implemented_procedures(location, series_profile, time_roles):
    from test_procedure import procedure

    from beliefs import stored

    case, ref, clock, _ = mapped_case()
    node = stored.procedure_node(procedure(yields=(), implementation=None))
    case.records.nodes[node.id] = node
    view = _raw(case, ref)
    anchors = _raw(case, view["anchors"])
    if location == "map":
        doc = _raw(case, clock)
        doc["procedure"] = node.id
        table = _raw(case, view["table"])
        origins = _raw(case, table["axis"]["origin"]["source"])
        origins["origins"]["zero"]["clock"]["map"] = case.hold(doc)
        origin = case.hold(origins)
        table["axis"]["origin"]["source"] = origin
        anchors["axis"]["origin"]["source"] = origin
        view["table"] = case.hold(table)
    elif location == "view-transform":
        view["transform"]["procedure"] = node.id
    elif location == "anchor-transform":
        anchors["transform"]["procedure"] = node.id
    else:
        anchors["provenance"]["procedure"] = node.id
    view["anchors"] = case.hold(anchors)
    with pytest.raises(SeriesRefused, match="Implementation"):
        case.read(case.hold(view), series_profile, time_roles)
