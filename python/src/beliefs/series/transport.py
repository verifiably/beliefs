"""A checked copy of retained candidate keys through ordinary workflow parameters."""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import TYPE_CHECKING

from beliefs.identity import v1
from beliefs.series.coverage import EventCoverage
from beliefs.series.types import SeriesRefused

if TYPE_CHECKING:
    from beliefs.estimand import Estimand


def event_retained_keys(coverage: EventCoverage) -> str:
    keys = [row.key for row in coverage.report if row.windows and all(status == "complete" for status in row.windows)]
    if coverage.policy != "complete-windows" or not keys:
        raise SeriesRefused("invalid-series", "event_retained_keys requires complete-windows with retained events")
    value = "event-keys.v1." + base64.urlsafe_b64encode(v1.encode(keys)).decode("ascii").rstrip("=")
    if len(value.encode("utf-8")) > 64 * 1024:
        raise SeriesRefused("invalid-series", "event_retained_keys exceeds 64 KiB")
    return value


def check_event_parameters(estimand: Estimand, parameters: Mapping[str, object]) -> None:
    coverage = estimand.event_coverage
    if coverage is None:
        if "event_retained_keys" in parameters:
            raise SeriesRefused("invalid-series", "event_retained_keys is forbidden without event series coverage")
        return
    value = parameters.get("event_retained_keys")
    if not isinstance(value, str) or value != event_retained_keys(coverage):
        raise SeriesRefused("invalid-series", "event_retained_keys must be the exact canonical retained-key string")
