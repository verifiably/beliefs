"""Exact finite geometry, licensed elapsed units, and event-window support."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from fractions import Fraction
from itertools import pairwise
from typing import Protocol

from beliefs.contract.base import TimeRoles
from beliefs.profile import ProfileSpec
from beliefs.series.types import AbsoluteAxis, AnchorRow, ElapsedAxis, IndexAxis, SeriesRefused, Table


class _EventSeries(Protocol):
    @property
    def axis(self) -> IndexAxis | ElapsedAxis | AbsoluteAxis: ...
    @property
    def coordinates(self) -> tuple[int | Fraction | str, ...]: ...
    @property
    def support(self) -> tuple[tuple[int | Fraction | str, int | Fraction | str], ...] | None: ...
    @property
    def anchors(self) -> tuple[AnchorRow, ...]: ...


__all__ = ["WindowMembership", "check_table_geometry", "elapsed_factor", "label_coordinate", "window_memberships"]

_UTC = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?Z")


def label_coordinate(value: str) -> Fraction:
    match = _UTC.fullmatch(value)
    if match is None:
        raise SeriesRefused("invalid-series", "absolute coordinates require exact UTC civil labels")
    parts = match.groups()
    try:
        civil = datetime(
            int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), tzinfo=UTC
        )
    except ValueError as exc:
        raise SeriesRefused("invalid-series", "invalid UTC date/time or leap-second label") from exc
    # A civil-order key only; it never supplies physical elapsed time.
    whole = civil.toordinal() * 86400 + civil.hour * 3600 + civil.minute * 60 + civil.second
    return Fraction(whole) + (Fraction("0." + parts[6]) if parts[6] else Fraction(0))


def elapsed_factor(profile: ProfileSpec, roles: TimeRoles, unit: str) -> tuple[Fraction, frozenset[str]]:
    duration = profile.quantity_kinds.get(roles.duration)
    frequency = profile.quantity_kinds.get(roles.frequency)
    second = profile.units.get(roles.second)
    hertz = profile.units.get(roles.hertz)
    selected = profile.units.get(unit)
    if duration is None or duration.dimension != {"T": 1} or frequency is None or frequency.dimension != {"T": -1}:
        raise SeriesRefused(
            "invalid-series", "time roles require the exact activated duration/frequency identities and dimensions"
        )
    if (
        second is None
        or second.quantity_kind != roles.duration
        or second.calendar
        or hertz is None
        or hertz.quantity_kind != roles.frequency
        or hertz.calendar
    ):
        raise SeriesRefused("invalid-series", "time roles require noncalendar second and hertz")
    if selected is None or selected.quantity_kind != roles.duration or selected.calendar:
        raise SeriesRefused("invalid-series", "elapsed unit requires the licensed duration quantity")
    terms = {unit, roles.duration, roles.frequency, roles.second, roles.hertz}
    if unit == roles.second:
        return Fraction(1), frozenset(terms)
    conversion = profile.conversion_between(unit, roles.second)
    if (
        conversion is None
        or conversion.kind != "multiplicative"
        or not conversion.exact
        or conversion.offset is not None
        or conversion.error is not None
        or conversion.constant is not None
        or conversion.factor <= 0
    ):
        raise SeriesRefused(
            "invalid-series", "elapsed unit requires an exact declared multiplicative conversion to second"
        )
    terms.add(conversion.term)
    factor = conversion.factor if conversion.from_unit == unit else 1 / conversion.factor
    return factor, frozenset(terms)


def check_table_geometry(table: Table) -> None:
    def order(value: int | Fraction | str) -> Fraction:
        if isinstance(table.axis, AbsoluteAxis):
            if not isinstance(value, str):
                raise SeriesRefused("invalid-series", "absolute coordinate must be a label")
            return label_coordinate(value)
        return Fraction(value)

    coords = tuple(order(value) for value in table.coordinates)
    if any(a >= b for a, b in pairwise(coords)):
        raise SeriesRefused("invalid-series", "coordinates must strictly increase without sorting")
    if isinstance(table.axis, ElapsedAxis) and table.axis.grid == "regular":
        spacing = table.axis.spacing
        assert spacing is not None
        if any(value != coords[0] + i * spacing for i, value in enumerate(coords)):
            raise SeriesRefused("invalid-series", "coordinates disagree with the exact regular grid")
    if table.support is None:
        return
    last_high = None
    for point, (low, high) in zip(coords, table.support, strict=True):
        low, high = order(low), order(high)
        if low >= high or not low <= point < high or (last_high is not None and last_high > low):
            raise SeriesRefused(
                "invalid-series", "support must contain its point, be half-open, ordered and nonoverlapping"
            )
        last_high = high


@dataclass(frozen=True)
class WindowMembership:
    low: Fraction
    high: Fraction
    positions: tuple[int, ...]


def window_memberships(
    series: _EventSeries, windows: tuple[tuple[Fraction, Fraction], ...]
) -> tuple[tuple[WindowMembership, ...], ...]:
    if not isinstance(series.axis, ElapsedAxis) or not series.anchors:
        raise SeriesRefused("invalid-series", "event series requires elapsed coordinates and anchors")
    result = []
    for anchor in series.anchors:
        memberships = []
        for lo, hi in windows:
            low, high = anchor.coordinate + lo, anchor.coordinate + hi
            if low >= high:
                raise SeriesRefused("invalid-series", "event window must be nonempty")
            positions = tuple(i for i, at in enumerate(series.coordinates) if low <= Fraction(at) < high)
            if not positions or series.support is None:
                raise SeriesRefused("invalid-series", "event window needs nonempty samples and complete bin support")
            intervals = [series.support[i] for i in positions]
            if intervals[0][0] != low or intervals[-1][1] != high or any(a[1] != b[0] for a, b in pairwise(intervals)):
                raise SeriesRefused("invalid-series", "support does not exactly tile the event window")
            memberships.append(WindowMembership(low, high, positions))
        result.append(tuple(memberships))
    return tuple(result)
