"""Closed canonical formats cannot smuggle untyped or noncanonical fields."""

import json
from copy import deepcopy

import pytest

from beliefs.identity import v1

from .fixtures import objects, ref_value


def test_canonical_series_formats_and_refs():
    from beliefs.series.codec import decode_series_object, series_ref_from_projection, series_ref_projection

    for value in objects():
        checked = decode_series_object(v1.encode(value))
        assert checked.format == value["format"]
        assert checked == decode_series_object(v1.encode(value))
    value = ref_value(b"table")
    assert series_ref_projection(series_ref_from_projection(value)) == value


@pytest.mark.parametrize(
    "mutation",
    [
        lambda v: v.update(extra=1),
        lambda v: v.update(anchors=None),
        lambda v: v.update(selection=[True]),
        lambda v: v.update(selection=[]),
        lambda v: v.update(selection=[-1]),
        lambda v: v.update(selection=[1, 0]),
        lambda v: v.update(channel="e\u0301"),
    ],
)
def test_descriptor_closed_shape(mutation):
    from beliefs.series.codec import decode_series_object
    from beliefs.series.types import SeriesRefused

    value = deepcopy(objects()[0])
    mutation(value)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(SeriesRefused):
        decode_series_object(data)


@pytest.mark.parametrize(
    "data",
    [
        b'{"format":"science.series-origins.v2","origins":{},"origins":{}}',
        b'{ "format":"science.series-origins.v2","origins":{}}',
        b'{"format":"science.series-origins.v2","origins":{"a":{"label":null}}}',
        b'{"format":"science.series-table.v2","axis":{"kind":"index"},"coordinates":[0],"channels":{}}',
        b"[]",
        b"null",
        b"NaN",
    ],
)
def test_noncanonical_or_untyped_bytes_refuse(data):
    from beliefs.series.codec import decode_series_object
    from beliefs.series.types import SeriesRefused

    with pytest.raises(SeriesRefused):
        decode_series_object(data)


@pytest.mark.parametrize(
    "change",
    [
        {"dataset": "dataset:" + "a" * 64},
        {"resource": "sha256:" + "a" * 63},
        {"member": "x"},
        {"resource": "sha256-tree:" + "a" * 64},
        *(
            {"resource": "sha256-tree:" + "a" * 64, "member": p}
            for p in ("../a", "/a", "a//b", "a/./b", "a\\b", "https://x", "e\u0301")
        ),
        {"member": None},
        {"extra": 1},
    ],
)
def test_reference_requires_exact_dataset_digest_and_canonical_member(change):
    from beliefs.series.codec import series_ref_from_projection
    from beliefs.series.types import SeriesRefused

    with pytest.raises(SeriesRefused):
        series_ref_from_projection({**ref_value(b"data"), **change})


@pytest.mark.parametrize("values", [["NaN"], ["Infinity"], [True], [1], ["1/3"], [" 1"]])
def test_channel_values_are_finite_decimal_strings(values):
    from beliefs.series.codec import decode_series_object
    from beliefs.series.types import SeriesRefused

    table = deepcopy(objects()[1])
    table["coordinates"] = [0]
    table["channels"]["signal"]["values"] = values
    with pytest.raises(SeriesRefused):
        decode_series_object(v1.encode(table))


def test_row_limit_and_all_channel_shapes():
    from beliefs.series.codec import decode_series_object
    from beliefs.series.types import SeriesRefused

    table = deepcopy(objects()[1])
    table["coordinates"] = list(range(100_000))
    table["channels"]["signal"]["values"] = ["1"] * 100_000
    from beliefs.series.types import Table

    decoded = decode_series_object(v1.encode(table))
    assert isinstance(decoded, Table)
    assert len(decoded.coordinates) == 100_000
    table["coordinates"].append(100_000)
    table["channels"]["signal"]["values"].append("1")
    with pytest.raises(SeriesRefused):
        decode_series_object(v1.encode(table))
    table = deepcopy(objects()[1])
    table["channels"]["unused"] = {"coordinates": {}, "values": ["1", "2"]}
    with pytest.raises(SeriesRefused):
        decode_series_object(v1.encode(table))
