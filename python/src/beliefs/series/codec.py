"""Closed canonical series JSON; shape checks do not claim axis semantics."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from decimal import Decimal
from fractions import Fraction
from itertools import pairwise
from types import MappingProxyType
from typing import TypeVar

from beliefs import _measurement_record as record
from beliefs.errors import ScienceError
from beliefs.identity import v1
from beliefs.measurement import Coordinates
from beliefs.series.clock import clock_map_from_projection
from beliefs.series.geometry import label_coordinate
from beliefs.series.types import (
    MISSING,
    AbsoluteAxis,
    AnchorProvenance,
    AnchorRow,
    Anchors,
    Channel,
    ClockMapTransform,
    ClockOrigin,
    Descriptor,
    ElapsedAxis,
    IndexAxis,
    MissingValue,
    Origin,
    OriginRow,
    Origins,
    SeriesObject,
    SeriesRef,
    SeriesRefused,
    Table,
    Transform,
)

__all__ = ["decode_series_object", "series_ref_from_projection", "series_ref_projection"]

_FILE_BYTES = 16 * 1024 * 1024
_ROWS = 100_000
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
_T = TypeVar("_T")


def _number(value: object) -> Fraction:
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise SeriesRefused("invalid-series", "expected a finite decimal string")
    return Fraction(Decimal(value))


def _index(value: object) -> int:
    if type(value) is not int or value < 0:
        raise SeriesRefused("invalid-series", "expected a nonnegative integer")
    return value


def _array(value: object, parse: Callable[[object], _T], *, nonempty: bool = True) -> tuple[_T, ...]:
    if not isinstance(value, list) or (nonempty and not value) or len(value) > _ROWS:
        raise SeriesRefused("invalid-series", "expected a nonempty array of at most 100000 rows")
    return tuple(parse(item) for item in value)


def series_ref_from_projection(value: object) -> SeriesRef:
    try:
        fields = record.shape(value, {"dataset", "resource"}, {"member"})
        return SeriesRef(
            record.text(fields["dataset"], "series dataset"),
            record.text(fields["resource"], "series resource"),
            record.text(fields["member"], "series member") if "member" in fields else None,
        )
    except ScienceError as exc:
        if isinstance(exc, SeriesRefused):
            raise
        raise SeriesRefused("invalid-series", str(exc)) from exc


def series_ref_projection(ref: SeriesRef) -> dict[str, object]:
    value: dict[str, object] = {"dataset": ref.dataset, "resource": ref.resource}
    if ref.member is not None:
        value["member"] = ref.member
    return value


def _axis(value: object, *, anchors: bool = False) -> IndexAxis | ElapsedAxis | AbsoluteAxis:
    fields = record.shape(value, {"kind"}, {"unit", "origin", "basis", "grid", "convention"})
    kind = fields["kind"]
    if kind == "index" and not anchors:
        record.shape(value, {"kind"})
        return IndexAxis()
    if kind == "absolute":
        fields = record.shape(value, {"kind", "convention", "grid"})
        if fields["convention"] != "utc-label" or fields["grid"] != "labels":
            raise SeriesRefused("invalid-series", "unsupported absolute convention or grid")
        return AbsoluteAxis()
    if kind != "elapsed":
        raise SeriesRefused("invalid-series", "unsupported coordinate kind")
    fields = record.shape(value, {"kind", "unit", "origin", "basis"} | (set() if anchors else {"grid"}))
    origin = record.shape(fields["origin"], {"source", "key"})
    basis = record.text(fields["basis"], "elapsed basis")
    if basis not in ("native-elapsed", "synthetic", "clock-mapped"):
        raise SeriesRefused("invalid-series", "unsupported elapsed basis")
    grid, spacing, rate = None, None, None
    if not anchors:
        raw_grid = record.shape(fields["grid"], {"kind"}, {"spacing", "rate"})
        grid = record.text(raw_grid["kind"], "grid kind")
        if grid == "irregular":
            record.shape(raw_grid, {"kind"})
        elif grid == "regular":
            record.shape(raw_grid, {"kind", "spacing"}, {"rate"})
            spacing = _number(raw_grid["spacing"])
            rate = _number(raw_grid["rate"]) if "rate" in raw_grid else None
            if spacing <= 0 or (rate is not None and rate <= 0):
                raise SeriesRefused("invalid-series", "spacing and rate must be positive")
        else:
            raise SeriesRefused("invalid-series", "unsupported elapsed grid")
    return ElapsedAxis(
        record.term(fields["unit"], "axis unit"),
        Origin(series_ref_from_projection(origin["source"]), record.text(origin["key"], "origin key")),
        basis,
        grid,
        spacing,
        rate,
    )


def _coordinates(value: object) -> Coordinates:
    fields = record.shape(value, {"quantity_kind", "value_type", "transformation"}, {"unit", "scale"})
    return Coordinates(
        record.term(fields["quantity_kind"], "quantity kind"),
        record.term(fields["unit"], "unit") if "unit" in fields else None,
        record.address(fields["scale"], "procedure") if "scale" in fields else None,
        record.text(fields["value_type"], "value type"),
        record.term(fields["transformation"], "transformation"),
    )


def _transform(value: object) -> Transform | ClockMapTransform:
    fields = record.shape(value, {"source", "procedure", "operation"}, {"mapping"})
    if fields["operation"] == "clock-map":
        record.shape(value, {"source", "procedure", "operation"})
        return ClockMapTransform(
            series_ref_from_projection(fields["source"]), record.address(fields["procedure"], "procedure")
        )
    fields = record.shape(value, {"source", "procedure", "operation", "mapping"})
    operation = record.text(fields["operation"], "operation")
    if operation == "select":
        mapping = _array(fields["mapping"], _index)
    elif operation == "rebin":
        mapping = _array(fields["mapping"], lambda group: _array(group, _index))
    else:
        raise SeriesRefused("invalid-series", f"unsupported series operation {operation!r}")
    return Transform(
        series_ref_from_projection(fields["source"]),
        record.address(fields["procedure"], "procedure"),
        operation,
        mapping,
    )


def _anchor_row(value: object, axis: ElapsedAxis | AbsoluteAxis) -> AnchorRow:
    utc = isinstance(axis, AbsoluteAxis) or axis.basis == "clock-mapped"
    fields = record.shape(value, {"key", "class", "coordinate"} | ({"source_epoch"} if utc else set()))
    cls = record.shape(fields["class"], {"sort", "term"})
    coordinate = (
        record.text(fields["coordinate"], "UTC anchor")
        if isinstance(axis, AbsoluteAxis)
        else _number(fields["coordinate"])
    )
    if isinstance(coordinate, str):
        label_coordinate(coordinate)
    return AnchorRow(
        record.text(fields["key"], "anchor key"),
        record.term(cls["sort"], "anchor class sort"),
        record.text(cls["term"], "anchor class term"),
        coordinate,
        record.text(fields["source_epoch"], "source epoch") if utc else None,
    )


def _origin_row(value: object) -> OriginRow:
    fields = record.shape(value, {"label"}, {"clock"})
    clock = None
    if "clock" in fields:
        raw = record.shape(fields["clock"], {"map", "epoch"})
        epoch = record.text(raw["epoch"], "clock epoch")
        label_coordinate(epoch)
        clock = ClockOrigin(series_ref_from_projection(raw["map"]), epoch)
    return OriginRow(record.text(fields["label"], "origin label"), clock)


def _value(value: object) -> Fraction | MissingValue:
    if isinstance(value, dict) and set(value) == {"missing"} and value["missing"] is True:
        return MISSING
    return _number(value)


def _decode(value: object) -> SeriesObject:
    if not isinstance(value, Mapping):
        raise SeriesRefused("invalid-series", "series object must be a mapping")
    tag = value.get("format")
    if not isinstance(tag, str):
        raise SeriesRefused("invalid-series", "series format must be text")
    if tag in {f"science.series-{kind}.v1" for kind in ("view", "table", "origins", "anchors")}:
        raise SeriesRefused("pre-v2-series", "previous series generation requires its matching source release")
    if tag == "science.series-clock-map.v1":
        return clock_map_from_projection(value)
    if tag == "science.series-view.v2":
        fields = record.shape(
            value, {"format", "table", "channel", "selection"}, {"anchors", "selection_procedure", "transform"}
        )
        selection = _array(fields["selection"], _index)
        if any(a >= b for a, b in pairwise(selection)):
            raise SeriesRefused("invalid-series", "selection must be strictly increasing")
        return Descriptor(
            series_ref_from_projection(fields["table"]),
            record.text(fields["channel"], "channel"),
            selection,
            series_ref_from_projection(fields["anchors"]) if "anchors" in fields else None,
            record.address(fields["selection_procedure"], "procedure") if "selection_procedure" in fields else None,
            _transform(fields["transform"]) if "transform" in fields else None,
        )
    if tag == "science.series-origins.v2":
        fields = record.shape(value, {"format", "origins"})
        if not isinstance(fields["origins"], dict) or not fields["origins"] or len(fields["origins"]) > _ROWS:
            raise SeriesRefused("invalid-series", "origins must be a bounded nonempty mapping")
        return Origins(
            MappingProxyType({record.text(k, "origin key"): _origin_row(v) for k, v in fields["origins"].items()})
        )
    if tag == "science.series-anchors.v2":
        fields = record.shape(value, {"format", "axis", "rule", "rows", "provenance"}, {"transform"})
        axis = _axis(fields["axis"], anchors=True)
        assert isinstance(axis, (ElapsedAxis, AbsoluteAxis))
        raw = record.shape(fields["provenance"], {"procedure", "epoch_definition"})
        provenance = AnchorProvenance(
            record.address(raw["procedure"], "procedure"), record.text(raw["epoch_definition"], "epoch definition")
        )
        transform = _transform(fields["transform"]) if "transform" in fields else None
        mapped = isinstance(axis, ElapsedAxis) and axis.basis == "clock-mapped"
        if (mapped and not isinstance(transform, ClockMapTransform)) or (not mapped and transform is not None):
            raise SeriesRefused("invalid-series", "only clock-mapped anchors require a clock-map transform")
        assert transform is None or isinstance(transform, ClockMapTransform)
        return Anchors(
            axis,
            record.address(fields["rule"], "classification-rule"),
            _array(fields["rows"], lambda row: _anchor_row(row, axis)),
            provenance,
            transform,
        )
    if tag != "science.series-table.v2":
        raise SeriesRefused("invalid-series", "unsupported series format")
    fields = record.shape(value, {"format", "axis", "coordinates", "channels"}, {"support"})
    axis = _axis(fields["axis"])
    parse = (
        _index
        if isinstance(axis, IndexAxis)
        else (lambda item: record.text(item, "UTC label"))
        if isinstance(axis, AbsoluteAxis)
        else _number
    )
    coordinates = _array(fields["coordinates"], parse)
    raw_channels = fields["channels"]
    if not isinstance(raw_channels, dict) or not raw_channels:
        raise SeriesRefused("invalid-series", "table requires a channel mapping")
    channels: dict[str, Channel] = {}
    for name, raw in raw_channels.items():
        channel = record.shape(raw, {"coordinates", "values"})
        values = _array(channel["values"], _value)
        if len(values) != len(coordinates):
            raise SeriesRefused("invalid-series", "channel length differs from coordinates")
        channels[record.text(name, "channel")] = Channel(_coordinates(channel["coordinates"]), values)
    support = None
    if "support" in fields:

        def pair(item: object):
            bounds = _array(item, parse)
            if len(bounds) != 2:
                raise SeriesRefused("invalid-series", "support has exactly two bounds")
            return (bounds[0], bounds[1])

        support = _array(fields["support"], pair)
        if len(support) != len(coordinates):
            raise SeriesRefused("invalid-series", "support length differs from coordinates")
    return Table(axis, coordinates, MappingProxyType(channels), support)


def decode_series_object(data: bytes) -> SeriesObject:
    if not isinstance(data, bytes) or len(data) > _FILE_BYTES:
        raise SeriesRefused("invalid-series", "series file exceeds 16 MiB or is not bytes")
    try:
        return _decode(v1.decode(data))
    except SeriesRefused:
        raise
    except (ScienceError, ValueError, RecursionError) as exc:
        raise SeriesRefused("invalid-series", f"invalid canonical series object: {exc}") from exc
