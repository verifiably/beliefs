"""Deterministic complete-window diagnostics over fully checked held series."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction
from typing import final

from beliefs import _measurement_record as wire
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.series.geometry import WindowMembership
from beliefs.series.reader import CheckedSeries
from beliefs.series.types import AbsoluteAxis, ClockMapTransform, ElapsedAxis, MissingValue, SeriesGraph, SeriesRefused

_STATUSES = frozenset({"outside-support", "partial-bin", "support-gap", "missing-value", "complete"})
_MINT = object()


@dataclass(frozen=True)
class CoverageRow:
    key: str
    windows: tuple[str, ...]


@dataclass(frozen=True)
class EventCoverage:
    policy: str
    report: tuple[CoverageRow, ...]


@sealed
@final
@dataclass(frozen=True, init=False)
class CheckedEventCoverage:
    coverage: EventCoverage
    retained_keys: tuple[str, ...]
    memberships: tuple[tuple[WindowMembership, ...], ...]
    graph: SeriesGraph

    def __init__(
        self,
        *,
        _mint: object,
        coverage: EventCoverage,
        retained_keys: tuple[str, ...],
        memberships: tuple[tuple[WindowMembership, ...], ...],
        graph: SeriesGraph,
    ) -> None:
        if _mint is not _MINT:
            raise SeriesRefused("invalid-series", "CheckedEventCoverage is minted only by the coverage checker")
        object.__setattr__(self, "coverage", coverage)
        object.__setattr__(self, "retained_keys", retained_keys)
        object.__setattr__(self, "memberships", memberships)
        object.__setattr__(self, "graph", graph)


def coverage_projection(value: EventCoverage) -> dict[str, object]:
    return {"policy": value.policy, "report": [{"key": row.key, "windows": list(row.windows)} for row in value.report]}


def _bounds(rows: int, windows: int) -> None:
    if rows < 1 or windows < 1 or rows * windows > 100000:
        raise SeriesRefused("invalid-series", "coverage requires 1..100000 candidate/window cells")


def _byte_bound(value: EventCoverage) -> None:
    if len(v1.encode(coverage_projection(value)["report"])) > 16 * 1024 * 1024:
        raise SeriesRefused("invalid-series", "coverage report exceeds 16 MiB")


def coverage_from_projection(value: object, *, window_count: int) -> EventCoverage:
    body = wire.shape(value, {"policy", "report"})
    if body["policy"] != "complete-windows" or not isinstance(body["report"], list):
        raise SeriesRefused("invalid-series", "coverage requires complete-windows and a report array")
    _bounds(len(body["report"]), window_count)
    rows = []
    keys: set[str] = set()
    for raw in body["report"]:
        row = wire.shape(raw, {"key", "windows"})
        key = wire.text(row["key"], "candidate key")
        windows = wire.sequence(row["windows"], lambda status: wire.text(status, "window status"))
        if key in keys or len(windows) != window_count or any(status not in _STATUSES for status in windows):
            raise SeriesRefused("invalid-series", "coverage keys must be unique with exact window arity/statuses")
        keys.add(key)
        rows.append(CoverageRow(key, windows))
    result = EventCoverage("complete-windows", tuple(rows))
    if not any(all(status == "complete" for status in row.windows) for row in rows):
        raise SeriesRefused("invalid-series", "coverage must have at least one retained candidate")
    _byte_bound(result)
    return result


def _full_response(series: CheckedSeries) -> None:
    # The reader proves that absence of selection_procedure means every table row.
    if series.descriptor.selection_procedure is not None:
        raise SeriesRefused("invalid-series", "event coverage requires full response selection")
    if not isinstance(series.axis, ElapsedAxis):
        raise SeriesRefused("invalid-series", "event coverage requires elapsed coordinates")
    if series.axis.basis != "clock-mapped":
        if series.descriptor.transform is not None:
            raise SeriesRefused("invalid-series", "event response forbids select/rebin transforms")
        return
    if not isinstance(series.descriptor.transform, ClockMapTransform) or len(series.predecessors) != 1:
        raise SeriesRefused("invalid-series", "event response requires exactly one clock-map hop")
    source = series.predecessors[0]
    if (
        not isinstance(source.axis, AbsoluteAxis)
        or source.descriptor.transform is not None
        or source.descriptor.selection_procedure is not None
        or source.anchors
    ):
        raise SeriesRefused(
            "invalid-series", "event clock-map source requires full untransformed absolute rows without anchors"
        )


def compute_coverage(series: CheckedSeries, windows: tuple[tuple[Fraction, Fraction], ...]) -> CheckedEventCoverage:
    _full_response(series)
    if not series.anchors or series.support is None:
        raise SeriesRefused("invalid-series", "event coverage requires anchors and support metadata")
    _bounds(len(series.anchors), len(windows))
    if any(low >= high for low, high in windows):
        raise SeriesRefused("invalid-series", "event window must be nonempty")
    # Ordered, nonoverlapping intervals were checked before this algorithm. Prefix
    # counts make each status query logarithmic, regardless of window width.
    lows = tuple(Fraction(pair[0]) for pair in series.support)
    highs = tuple(Fraction(pair[1]) for pair in series.support)
    gaps, missing = [0], [0]
    for i, value in enumerate(series.values):
        gaps.append(gaps[-1] + int(i > 0 and highs[i - 1] != lows[i]))
        missing.append(missing[-1] + int(isinstance(value, MissingValue)))
    report, retained, memberships = [], [], []
    for anchor in series.anchors:
        assert isinstance(anchor.coordinate, Fraction)
        statuses, ranges = [], []
        for lo, hi in windows:
            low, high = anchor.coordinate + lo, anchor.coordinate + hi
            left, right = bisect_right(highs, low), bisect_left(lows, high)
            if low < lows[0] or high > highs[-1] or left >= right:
                status = "outside-support"
            elif lows[left] < low or highs[right - 1] > high:
                status = "partial-bin"
            elif lows[left] != low or highs[right - 1] != high or gaps[right] != gaps[left + 1]:
                status = "support-gap"
            elif missing[right] != missing[left]:
                status = "missing-value"
            else:
                status = "complete"
            statuses.append(status)
            ranges.append((low, high, left, right))
        report.append(CoverageRow(anchor.key, tuple(statuses)))
        if all(status == "complete" for status in statuses):
            retained.append(anchor.key)
            memberships.append(
                tuple(WindowMembership(low, high, tuple(range(left, right))) for low, high, left, right in ranges)
            )
    coverage = EventCoverage("complete-windows", tuple(report))
    _byte_bound(coverage)
    return CheckedEventCoverage(
        _mint=_MINT,
        coverage=coverage,
        retained_keys=tuple(retained),
        memberships=tuple(memberships),
        graph=series.graph,
    )
