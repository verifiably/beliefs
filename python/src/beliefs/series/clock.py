"""Exact elapsed coordinates under a bounded, explicitly asserted UTC/TAI map."""

import re
from bisect import bisect_right
from fractions import Fraction

from beliefs import _measurement_record as record
from beliefs.series.geometry import label_coordinate
from beliefs.series.types import ClockMap, ClockSegment, SeriesRefused

_WHOLE_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_FIRST_UTC = label_coordinate("1972-01-01T00:00:00Z")


def _boundary(value: object) -> Fraction:
    label = record.text(value, "clock boundary")
    if _WHOLE_UTC.fullmatch(label) is None:
        raise SeriesRefused("invalid-series", "clock boundaries require whole-second UTC labels")
    result = label_coordinate(label)
    if result < _FIRST_UTC:
        raise SeriesRefused("invalid-series", "pre-1972 UTC is unsupported")
    return result


def clock_map_from_projection(value: object) -> ClockMap:
    fields = record.shape(value, {"format", "convention", "low", "high", "segments", "procedure"})
    if fields["convention"] != "utc-tai":
        raise SeriesRefused("invalid-series", "clock convention must be utc-tai")
    low, high = _boundary(fields["low"]), _boundary(fields["high"])
    raw = fields["segments"]
    if low >= high or not isinstance(raw, list) or not 1 <= len(raw) <= 100000:
        raise SeriesRefused("invalid-series", "clock requires nonempty coverage and bounded segments")
    segments = []
    for index, item in enumerate(raw):
        row = record.shape(item, {"from", "tai_minus_utc"})
        start = _boundary(row["from"])
        offset = row["tai_minus_utc"]
        if type(offset) is not int or not low <= start < high:
            raise SeriesRefused("invalid-series", "clock segments require integer offsets within coverage")
        if index == 0:
            if start != low:
                raise SeriesRefused("invalid-series", "first clock segment starts at low")
        elif start <= segments[-1].start or start % 86400 or abs(offset - segments[-1].tai_minus_utc) != 1:
            raise SeriesRefused("invalid-series", "later clock segments require increasing midnight unit steps")
        segments.append(ClockSegment(start, offset))
    return ClockMap(low, high, tuple(segments), record.address(fields["procedure"], "procedure"))


def _instant(clock: ClockMap, label: str) -> Fraction:
    civil = label_coordinate(label)
    if not clock.low <= civil < clock.high:
        raise SeriesRefused("invalid-series", "UTC label lies outside clock coverage")
    position = bisect_right(clock.segments, civil, key=lambda segment: segment.start) - 1
    segment = clock.segments[position]
    if position + 1 < len(clock.segments):
        following = clock.segments[position + 1]
        if following.tai_minus_utc < segment.tai_minus_utc and following.start - 1 <= civil:
            raise SeriesRefused("invalid-series", "nonexistent UTC label at a negative leap transition")
    return civil + segment.tai_minus_utc


def clock_coordinate(clock: ClockMap, label: str, *, epoch: str, seconds_per_unit: Fraction) -> Fraction:
    if seconds_per_unit <= 0:
        raise SeriesRefused("invalid-series", "clock axis unit must have a positive factor")
    coordinate = (_instant(clock, label) - _instant(clock, epoch)) / seconds_per_unit
    denominator = coordinate.denominator
    for prime in (2, 5):
        while denominator % prime == 0:
            denominator //= prime
    if denominator != 1:
        raise SeriesRefused("invalid-series", "mapped coordinate requires an exact finite decimal")
    return coordinate
