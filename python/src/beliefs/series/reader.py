"""One strict finite reader; checked values last only for this invocation."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import pairwise
from typing import cast, final

from beliefs.classification_rule import ClassificationRule
from beliefs.contract.base import TimeRoles
from beliefs.dependencies import HeldRecords, read_record
from beliefs.errors import ScienceError
from beliefs.identity import v1
from beliefs.procedure import Procedure
from beliefs.profile import ProfileSpec
from beliefs.sealed import sealed
from beliefs.series.codec import decode_series_object, series_ref_projection
from beliefs.series.evidence import ReadBudget, SeriesEvidence, load_series_object
from beliefs.series.geometry import check_table_geometry, elapsed_factor
from beliefs.series.graph import graph_from_projection, graph_projection
from beliefs.series.types import (
    AbsoluteAxis,
    AnchorRow,
    Anchors,
    ChannelCoordinates,
    Descriptor,
    ElapsedAxis,
    IndexAxis,
    Origins,
    SeriesGraph,
    SeriesGraphEntry,
    SeriesObject,
    SeriesRef,
    SeriesRefused,
    Table,
)

__all__ = ["CheckedSeries", "read_series"]

_MINT = object()


@sealed
@final
@dataclass(frozen=True, init=False)
class CheckedSeries:
    ref: SeriesRef
    descriptor: Descriptor
    axis: IndexAxis | ElapsedAxis | AbsoluteAxis
    coordinates: tuple[int | Fraction | str, ...]
    values: tuple[Fraction, ...]
    channel_coordinates: ChannelCoordinates
    support: tuple[tuple[int | Fraction | str, int | Fraction | str], ...] | None
    anchors: tuple[AnchorRow, ...]
    anchor_rule: str | None
    count: int
    span: Fraction | None
    spacing_seconds: Fraction | None
    rate_hz: Fraction | None
    graph: SeriesGraph

    def __init__(self, **kwargs: object) -> None:
        if kwargs.pop("_mint", None) is not _MINT:
            raise SeriesRefused("invalid-series", "CheckedSeries is minted only by the byte reader")
        for key, value in kwargs.items():
            object.__setattr__(self, key, value)


def _key(ref: SeriesRef) -> bytes:
    return v1.encode(series_ref_projection(ref))


def _same_axis(a: Table | CheckedSeries | Anchors, b: Table | CheckedSeries | Anchors) -> bool:
    if isinstance(a.axis, ElapsedAxis) and isinstance(b.axis, ElapsedAxis):
        return (a.axis.unit, a.axis.origin, a.axis.basis) == (b.axis.unit, b.axis.origin, b.axis.basis)
    return a.axis == b.axis


class _Reader:
    def __init__(self, profile: ProfileSpec, records: HeldRecords, evidence: SeriesEvidence, roles: TimeRoles) -> None:
        self.profile, self.records, self.evidence, self.roles = profile, records, evidence, roles
        self.budget = ReadBudget()
        self.objects: dict[SeriesRef, SeriesObject] = {}
        self.rows: dict[SeriesRef, SeriesGraphEntry] = {}

    def load(self, ref: SeriesRef) -> SeriesObject:
        if ref not in self.objects:
            self.objects[ref] = decode_series_object(
                load_series_object(ref, records=self.records, evidence=self.evidence, budget=self.budget)
            )
        return self.objects[ref]

    def row(
        self,
        ref: SeriesRef,
        obj: SeriesObject,
        links: tuple[SeriesRef, ...] = (),
        records: tuple[str, ...] = (),
        terms: tuple[str, ...] = (),
    ) -> None:
        old = self.rows.get(ref)
        if old is not None:
            links += old.links
            records += old.records
            terms += old.terms
        self.rows[ref] = SeriesGraphEntry(
            ref, obj.format, tuple(sorted(set(links), key=_key)), tuple(sorted(set(records))), tuple(sorted(set(terms)))
        )

    def procedure(self, ref: str, *, implementation: bool = False) -> Procedure:
        value = read_record(self.records, ref)
        if not isinstance(value, Procedure) or (implementation and value.implementation is None):
            raise SeriesRefused(
                "invalid-series", "series selection/transform requires a held procedure with Implementation"
            )
        return value

    def origin(self, axis: ElapsedAxis) -> None:
        ref = axis.origin.source
        with self.budget.enter(ref):
            obj = self.load(ref)
            if not isinstance(obj, Origins) or axis.origin.key not in obj.origins:
                raise SeriesRefused("invalid-series", "elapsed origin does not resolve the exact origins row")
            self.row(ref, obj)

    def table(self, ref: SeriesRef, channel: str) -> Table:
        with self.budget.enter(ref):
            obj = self.load(ref)
            if not isinstance(obj, Table):
                raise SeriesRefused("invalid-series", "descriptor table must resolve the table format")
            check_table_geometry(obj)
            links: tuple[SeriesRef, ...] = ()
            terms: set[str] = set()
            refs: tuple[str, ...] = ()
            if isinstance(obj.axis, ElapsedAxis):
                self.origin(obj.axis)
                links = (obj.axis.origin.source,)
                factor, axis_terms = elapsed_factor(self.profile, self.roles, obj.axis.unit)
                terms.update(axis_terms)
                if obj.axis.rate is not None and (
                    obj.axis.spacing is None or obj.axis.rate * obj.axis.spacing * factor != 1
                ):
                    raise SeriesRefused("invalid-series", "rate and spacing are not exactly reciprocal")
            if channel not in obj.channels:
                raise SeriesRefused("invalid-series", "descriptor channel is absent from the exact table")
            coordinates = obj.channels[channel].coordinates
            if (
                coordinates.quantity_kind not in self.profile.quantity_kinds
                or coordinates.transformation not in self.profile.transformations
            ):
                raise SeriesRefused("invalid-series", "selected channel coordinates are not activated")
            terms.update((coordinates.quantity_kind, coordinates.transformation))
            if coordinates.unit is not None:
                unit = self.profile.units.get(coordinates.unit)
                if unit is None or unit.quantity_kind != coordinates.quantity_kind:
                    raise SeriesRefused("invalid-series", "selected channel unit/quantity disagree")
                terms.add(unit.term)
            else:
                assert coordinates.scale is not None
                authority = self.procedure(coordinates.scale)
                if not authority.is_authority or not any(
                    row.quantity_kind == coordinates.quantity_kind for row in authority.yields
                ):
                    raise SeriesRefused("invalid-series", "selected channel scale has no matching authority")
                refs = (coordinates.scale,)
            self.row(ref, obj, links, refs, tuple(terms))
            return obj

    def anchors(self, ref: SeriesRef, table: Table) -> Anchors:
        with self.budget.enter(ref):
            obj = self.load(ref)
            if not isinstance(obj, Anchors) or not isinstance(table.axis, ElapsedAxis) or not _same_axis(table, obj):
                raise SeriesRefused("invalid-series", "anchors must use the identical elapsed axis meaning")
            self.origin(obj.axis)
            rule = read_record(self.records, obj.rule)
            if not isinstance(rule, ClassificationRule):
                raise SeriesRefused("invalid-series", "anchor rule is not a held classification rule")
            sort = self.profile.sorts.get(rule.classes)
            keys = [row.key for row in obj.rows]
            if len(set(keys)) != len(keys) or any(a.coordinate >= b.coordinate for a, b in pairwise(obj.rows)):
                raise SeriesRefused("invalid-series", "anchor keys are unique and coordinates strictly increase")
            for row in obj.rows:
                if row.sort != rule.classes or sort is None or sort.retired:
                    raise SeriesRefused("invalid-series", "anchor class sort disagrees with its rule")
                if sort.identifier_class is not None and re.fullmatch(sort.identifier_class.pattern, row.term) is None:
                    raise SeriesRefused("invalid-series", "anchor class is outside its declared identifier class")
            _, terms = elapsed_factor(self.profile, self.roles, obj.axis.unit)
            self.row(ref, obj, (obj.axis.origin.source,), (obj.rule,), tuple(terms | {rule.classes}))
            return obj

    def descriptor(self, ref: SeriesRef) -> CheckedSeries:
        with self.budget.enter(ref):
            obj = self.load(ref)
            if not isinstance(obj, Descriptor):
                raise SeriesRefused("invalid-series", "series root/source must resolve a descriptor")
            table = self.table(obj.table, obj.channel)
            if obj.selection[-1] >= len(table.coordinates):
                raise SeriesRefused("invalid-series", "selection is outside the table")
            full = obj.selection == tuple(range(len(table.coordinates)))
            refs: list[str] = []
            if full and obj.selection_procedure is not None:
                raise SeriesRefused("invalid-series", "full selection must omit selection_procedure")
            if not full:
                if obj.selection_procedure is None:
                    raise SeriesRefused("invalid-series", "nontrivial selection requires selection_procedure")
                self.procedure(obj.selection_procedure, implementation=True)
                refs.append(obj.selection_procedure)
            coords = tuple(table.coordinates[i] for i in obj.selection)
            channel = table.channels[obj.channel]
            values = tuple(channel.values[i] for i in obj.selection)
            support = tuple(table.support[i] for i in obj.selection) if table.support is not None else None
            span = None if isinstance(table.axis, AbsoluteAxis) else Fraction(coords[-1]) - Fraction(coords[0])
            spacing, rate = None, None
            if isinstance(table.axis, ElapsedAxis) and len(coords) >= 2:
                difference = Fraction(coords[1]) - Fraction(coords[0])
                if all(Fraction(b) - Fraction(a) == difference for a, b in pairwise(coords)):
                    factor, _ = elapsed_factor(self.profile, self.roles, table.axis.unit)
                    spacing = difference * factor
                    rate = 1 / spacing
            anchor_rows: tuple[AnchorRow, ...] = ()
            anchor_rule = None
            links = [obj.table]
            if obj.anchors is not None:
                anchors = self.anchors(obj.anchors, table)
                anchor_rows, anchor_rule = anchors.rows, anchors.rule
                links.append(obj.anchors)
            checked = CheckedSeries(
                _mint=_MINT,
                ref=ref,
                descriptor=obj,
                axis=table.axis,
                coordinates=coords,
                values=values,
                channel_coordinates=channel.coordinates,
                support=support,
                anchors=anchor_rows,
                anchor_rule=anchor_rule,
                count=len(coords),
                span=span,
                spacing_seconds=spacing,
                rate_hz=rate,
                graph=(),
            )
            if obj.transform is not None:
                transform = obj.transform
                self.procedure(transform.procedure, implementation=True)
                source = self.descriptor(transform.source)
                self.check_transform(checked, source)
                links.append(transform.source)
                refs.append(transform.procedure)
            self.row(ref, obj, tuple(links), tuple(refs))
            return checked

    def check_transform(self, output: CheckedSeries, source: CheckedSeries) -> None:
        transform = output.descriptor.transform
        assert transform is not None
        if not _same_axis(output, source) or output.channel_coordinates != source.channel_coordinates:
            raise SeriesRefused("invalid-series", "transform cannot relabel axes or channel coordinates")
        mapping = transform.mapping
        if len(mapping) != output.count:
            raise SeriesRefused("invalid-series", "transform mapping must have one entry per selected output row")
        if transform.operation == "select":
            if any(type(i) is not int or i < 0 or i >= source.count for i in mapping):
                raise SeriesRefused("invalid-series", "select mapping must strictly increase within source positions")
            positions = cast(tuple[int, ...], mapping)
            if any(a >= b for a, b in pairwise(positions)):
                raise SeriesRefused("invalid-series", "select mapping must strictly increase")
            if output.coordinates != tuple(source.coordinates[i] for i in positions) or output.values != tuple(
                source.values[i] for i in positions
            ):
                raise SeriesRefused("invalid-series", "select must copy source values and coordinates exactly")
            expected_support = tuple(source.support[i] for i in positions) if source.support is not None else None
            if output.support != expected_support:
                raise SeriesRefused("invalid-series", "select must copy support exactly")
            return
        if not isinstance(output.axis, ElapsedAxis) or source.support is None or output.support is None:
            raise SeriesRefused("invalid-series", "rebin needs explicit elapsed support on both tables")
        previous = -1
        for group, bounds in zip(mapping, output.support, strict=True):
            if (
                not isinstance(group, tuple)
                or not group
                or any(type(i) is not int or i < 0 or i >= source.count for i in group)
                or group[0] <= previous
                or any(b != a + 1 for a, b in pairwise(group))
            ):
                raise SeriesRefused(
                    "invalid-series", "rebin groups must be ordered contiguous source positions without reuse"
                )
            previous = group[-1]
            intervals = [source.support[i] for i in group]
            if bounds != (intervals[0][0], intervals[-1][1]) or any(a[1] != b[0] for a, b in pairwise(intervals)):
                raise SeriesRefused("invalid-series", "rebin source support does not tile output support")


def _read_series_roots(
    refs: tuple[SeriesRef, ...],
    *,
    profile: ProfileSpec,
    records: HeldRecords,
    evidence: SeriesEvidence,
    time_roles: TimeRoles,
) -> tuple[CheckedSeries, ...]:
    if type(profile) is not ProfileSpec:
        raise SeriesRefused("invalid-series", "series reader requires a compiled ProfileSpec")
    if type(evidence) is not SeriesEvidence:
        raise SeriesRefused("evidence-unavailable", "series reader requires explicit local evidence")
    reader = _Reader(profile, records, evidence, time_roles)
    try:
        checked = tuple(reader.descriptor(ref) for ref in refs)
        graph = tuple(sorted(reader.rows.values(), key=lambda row: _key(row.ref)))
        graph = graph_from_projection(graph_projection(graph), roots=refs)
        return tuple(replace(value, _mint=_MINT, graph=graph) for value in checked)
    except SeriesRefused:
        raise
    except ScienceError as exc:
        raise SeriesRefused("invalid-series", str(exc)) from exc


def read_series(
    ref: SeriesRef, *, profile: ProfileSpec, records: HeldRecords, evidence: SeriesEvidence
) -> CheckedSeries:
    if type(profile) is not ProfileSpec:
        raise SeriesRefused("invalid-series", "series reader requires a compiled ProfileSpec")
    return _read_series_roots(
        (ref,), profile=profile, records=records, evidence=evidence, time_roles=profile.time_roles
    )[0]
