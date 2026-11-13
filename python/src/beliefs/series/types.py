"""Immutable parsed series objects and the reader's explicit refusals."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import TypeAlias, final

from beliefs.errors import ScienceError
from beliefs.holdings.records import require_store_relative_path
from beliefs.measurement import Coordinates
from beliefs.sealed import sealed

__all__ = [
    "AbsoluteAxis",
    "AnchorRow",
    "Anchors",
    "Channel",
    "ChannelCoordinates",
    "Descriptor",
    "ElapsedAxis",
    "IndexAxis",
    "Origin",
    "Origins",
    "SeriesGraph",
    "SeriesGraphEntry",
    "SeriesObject",
    "SeriesRef",
    "SeriesRefused",
    "Table",
    "Transform",
]


class SeriesRefused(ScienceError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


@sealed
@final
@dataclass(frozen=True)
class SeriesRef:
    dataset: str
    resource: str
    member: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.dataset, str) or re.fullmatch(r"dataset:sha256:[0-9a-f]{64}", self.dataset) is None:
            raise SeriesRefused("invalid-series", "series dataset must be dataset:sha256:<64hex>")
        if (
            not isinstance(self.resource, str)
            or re.fullmatch(r"(?:sha256|sha256-tree):[0-9a-f]{64}", self.resource) is None
        ):
            raise SeriesRefused("invalid-series", "series resource must be a canonical sha256 or sha256-tree digest")
        if self.resource.startswith("sha256-tree:") != (self.member is not None):
            raise SeriesRefused("invalid-series", "member occurs exactly for a tree resource")
        if self.member is not None:
            try:
                require_store_relative_path(self.member)
            except ScienceError as exc:
                raise SeriesRefused("invalid-series", str(exc)) from exc
            if "\\" in self.member or ":" in self.member or unicodedata.normalize("NFC", self.member) != self.member:
                raise SeriesRefused("invalid-series", "member must be a canonical relative member path")


ChannelCoordinates: TypeAlias = Coordinates


@dataclass(frozen=True)
class Origin:
    source: SeriesRef
    key: str


@dataclass(frozen=True)
class IndexAxis:
    kind: str = "index"


@dataclass(frozen=True)
class ElapsedAxis:
    unit: str
    origin: Origin
    basis: str
    grid: str | None = None
    spacing: Fraction | None = None
    rate: Fraction | None = None
    kind: str = "elapsed"


@dataclass(frozen=True)
class AbsoluteAxis:
    convention: str = "utc-label"
    grid: str = "labels"
    kind: str = "absolute"


@dataclass(frozen=True)
class Transform:
    source: SeriesRef
    procedure: str
    operation: str
    mapping: tuple[int, ...] | tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class Descriptor:
    table: SeriesRef
    channel: str
    selection: tuple[int, ...]
    anchors: SeriesRef | None = None
    selection_procedure: str | None = None
    transform: Transform | None = None
    format: str = "science.series-view.v1"


@dataclass(frozen=True)
class Channel:
    coordinates: Coordinates
    values: tuple[Fraction, ...]


@dataclass(frozen=True)
class Table:
    axis: IndexAxis | ElapsedAxis | AbsoluteAxis
    coordinates: tuple[int | Fraction | str, ...]
    channels: Mapping[str, Channel]
    support: tuple[tuple[int | Fraction | str, int | Fraction | str], ...] | None = None
    format: str = "science.series-table.v1"


@dataclass(frozen=True)
class Origins:
    origins: Mapping[str, str]
    format: str = "science.series-origins.v1"


@dataclass(frozen=True)
class AnchorRow:
    key: str
    sort: str
    term: str
    coordinate: Fraction


@dataclass(frozen=True)
class Anchors:
    axis: ElapsedAxis
    rule: str
    rows: tuple[AnchorRow, ...]
    format: str = "science.series-anchors.v1"


SeriesObject: TypeAlias = Descriptor | Table | Origins | Anchors


@dataclass(frozen=True)
class SeriesGraphEntry:
    ref: SeriesRef
    format: str
    links: tuple[SeriesRef, ...]
    records: tuple[str, ...]
    terms: tuple[str, ...]


SeriesGraph: TypeAlias = tuple[SeriesGraphEntry, ...]
