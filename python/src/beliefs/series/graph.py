"""Portable graph shape and closure checks; this module performs no IO."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from beliefs import _measurement_record as record
from beliefs.errors import ScienceError
from beliefs.identity import v1
from beliefs.series.codec import series_ref_from_projection, series_ref_projection
from beliefs.series.types import SeriesGraph, SeriesGraphEntry, SeriesRef, SeriesRefused

__all__ = ["graph_from_projection", "graph_projection", "graph_roots", "graph_terms"]

_FORMATS = frozenset(
    {"science.series-view.v1", "science.series-table.v1", "science.series-origins.v1", "science.series-anchors.v1"}
)
_T = TypeVar("_T")
_K = TypeVar("_K", str, bytes)


def _ref_key(ref: SeriesRef) -> bytes:
    return v1.encode(series_ref_projection(ref))


def _sorted_array(value: object, parse: Callable[[object], _T], key: Callable[[_T], _K]) -> tuple[_T, ...]:
    if not isinstance(value, list):
        raise SeriesRefused("invalid-series", "graph lists are arrays")
    result = tuple(parse(item) for item in value)
    keys = [key(item) for item in result]
    if keys != sorted(set(keys)):
        raise SeriesRefused("invalid-series", "graph lists must be sorted and unique")
    return result


def _record(value: object) -> str:
    text = record.text(value, "series record")
    kind = text.partition(":")[0]
    if kind not in ("procedure", "classification-rule"):
        raise SeriesRefused("invalid-series", "series graph cites only procedure/rule record roots")
    return record.address(text, kind)


def graph_from_projection(value: object, *, roots: tuple[SeriesRef, ...]) -> SeriesGraph:
    try:
        if not isinstance(value, list) or len(value) > 256:
            raise SeriesRefused("invalid-series", "series graph is a bounded array")
        entries: list[SeriesGraphEntry] = []
        for row in value:
            fields = record.shape(row, {"ref", "format", "links", "records", "terms"})
            format = record.text(fields["format"], "series format")
            if format not in _FORMATS:
                raise SeriesRefused("invalid-series", "unknown graph format")
            entries.append(
                SeriesGraphEntry(
                    series_ref_from_projection(fields["ref"]),
                    format,
                    _sorted_array(fields["links"], series_ref_from_projection, _ref_key),
                    _sorted_array(fields["records"], _record, lambda x: x),
                    _sorted_array(fields["terms"], lambda x: record.term(x, "series term"), lambda x: x),
                )
            )
        keys = [_ref_key(row.ref) for row in entries]
        if keys != sorted(set(keys)):
            raise SeriesRefused("invalid-series", "graph rows must be sorted and unique by full ref")
        rows = {row.ref: row for row in entries}
        heights: dict[SeriesRef, int] = {}
        active: set[SeriesRef] = set()

        def visit(ref: SeriesRef) -> int:
            if ref in active:
                raise SeriesRefused("invalid-series", "graph cycle")
            if ref not in rows:
                raise SeriesRefused("invalid-series", "graph has a dangling root/link")
            if ref in heights:
                return heights[ref]
            active.add(ref)
            height = 1 + max((visit(link) for link in rows[ref].links), default=0)
            if height > 32:
                raise SeriesRefused("invalid-series", "graph exceeds depth 32")
            active.remove(ref)
            heights[ref] = height
            return height

        for root in roots:
            if root not in rows or rows[root].format != "science.series-view.v1":
                raise SeriesRefused("invalid-series", "series root must resolve a descriptor")
            visit(root)
        reached = set(heights)
        if reached != set(rows):
            raise SeriesRefused("invalid-series", "series graph has unreachable extras")
        for row in entries:
            kinds = [rows[link].format for link in row.links]
            if row.format == "science.series-view.v1":
                valid = (
                    kinds.count("science.series-table.v1") == 1
                    and kinds.count("science.series-anchors.v1") <= 1
                    and kinds.count("science.series-view.v1") <= 1
                    and "science.series-origins.v1" not in kinds
                    and not row.terms
                    and all(ref.startswith("procedure:") for ref in row.records)
                )
            elif row.format == "science.series-table.v1":
                valid = kinds in ([], ["science.series-origins.v1"]) and all(
                    ref.startswith("procedure:") for ref in row.records
                )
            elif row.format == "science.series-origins.v1":
                valid = not kinds and not row.records and not row.terms
            else:
                valid = (
                    kinds == ["science.series-origins.v1"]
                    and len(row.records) == 1
                    and row.records[0].startswith("classification-rule:")
                )
            if not valid:
                raise SeriesRefused("invalid-series", "graph links/roots contradict their declared object format")
        return tuple(entries)
    except SeriesRefused:
        raise
    except ScienceError as exc:
        raise SeriesRefused("invalid-series", str(exc)) from exc


def graph_projection(graph: SeriesGraph) -> list[dict[str, object]]:
    return [
        {
            "ref": series_ref_projection(row.ref),
            "format": row.format,
            "links": [series_ref_projection(link) for link in row.links],
            "records": list(row.records),
            "terms": list(row.terms),
        }
        for row in graph
    ]


def graph_roots(graph: SeriesGraph) -> frozenset[str]:
    return frozenset([row.ref.dataset for row in graph] + [ref for row in graph for ref in row.records])


def graph_terms(graph: SeriesGraph) -> frozenset[str]:
    return frozenset(term for row in graph for term in row.terms)
