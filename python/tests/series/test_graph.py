"""Frozen graph rows are keyed by exact refs, sorted and closed by reachability."""

from copy import deepcopy

import pytest

from .fixtures import SeriesCase, channel_coordinates


def test_selected_channel_union(series_profile, time_roles):
    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.reader import _read_series_roots

    case = SeriesCase()
    channels = {
        "signal": {"coordinates": channel_coordinates(), "values": ["1", "2"]},
        "other": {
            "coordinates": {**channel_coordinates(), "quantity_kind": "testing/fraction", "unit": "testing/unity"},
            "values": ["1", "2"],
        },
        "inactive": {
            "coordinates": {**channel_coordinates(), "quantity_kind": "missing/count", "unit": "missing/item"},
            "values": ["1", "2"],
        },
    }
    table = case.table(["0", "0.01"], channels=channels)
    first = case.view(table, [0, 1])
    second = case.hold({"format": "science.series-view.v2", "table": table, "channel": "other", "selection": [0, 1]})
    refs = tuple(map(series_ref_from_projection, (first, second)))

    def read(roots):
        return _read_series_roots(
            roots, profile=series_profile, records=case.records, evidence=case.evidence(), time_roles=time_roles
        )

    a = read(refs)
    b = read(tuple(reversed(refs)))
    assert a[0].graph == a[1].graph == b[0].graph
    row = next(row for row in a[0].graph if row.ref == series_ref_from_projection(table))
    assert "testing/count" in row.terms
    assert "testing/fraction" in row.terms
    assert not any(term.startswith("missing/") for term in row.terms)


def test_graph_projection_is_exact_and_closed(series_profile, time_roles):
    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.graph import graph_from_projection, graph_projection
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    ref = case.view(case.table(["0", "0.01"]), [0, 1])
    checked = case.read(ref, series_profile, time_roles)
    roots = (series_ref_from_projection(ref),)
    projection = graph_projection(checked.graph)
    assert graph_from_projection(projection, roots=roots) == checked.graph
    for malformed in (projection[:-1], projection + projection[:1], list(reversed(projection))):
        with pytest.raises(SeriesRefused):
            graph_from_projection(malformed, roots=roots)
    cyclic = deepcopy(projection)
    cyclic[0]["links"] = [cyclic[0]["ref"]]
    with pytest.raises(SeriesRefused):
        graph_from_projection(cyclic, roots=roots)


def test_descriptor_graph_requires_its_table_link():
    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.graph import graph_from_projection
    from beliefs.series.types import SeriesRefused

    case = SeriesCase()
    ref = case.view(case.table(["0", "0.01"]), [0, 1])
    with pytest.raises(SeriesRefused):
        graph_from_projection(
            [{"ref": ref, "format": "science.series-view.v2", "links": [], "records": [], "terms": []}],
            roots=(series_ref_from_projection(ref),),
        )
