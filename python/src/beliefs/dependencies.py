"""Structural dependency walks over typed measurement records and contract terms."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from nodes.core.node import Node

from beliefs import _measurement_record as record
from beliefs.assumptions import AssumptionInstance
from beliefs.classification_rule import ClassificationRule, rule_from_stored
from beliefs.errors import DependencyCycle, DependencyNotHeld, MalformedRecord
from beliefs.measurement import Observable
from beliefs.procedure import Procedure, SameAs, procedure_from_stored
from beliefs.profile import ProfileSpec
from beliefs.proxy_model import Calibration, ProxyModel, proxy_from_stored
from beliefs.referent_mapping import ReferentMapping, mapping_from_stored
from beliefs.register import AssumptionsRegister, register_from_stored
from beliefs.restriction import (
    IntervalRestriction,
    Restriction,
    RestrictionMap,
    RuleRestriction,
    TermRestriction,
    TimeIntervalRestriction,
    UnionRestriction,
    check_held_rule_scope,
)

__all__ = [
    "DependencyEntry",
    "HeldRecords",
    "Record",
    "Walk",
    "WalkValue",
    "dependency_closure",
    "read_record",
    "record_references",
    "record_terms",
    "walk",
]

Record: TypeAlias = Procedure | ReferentMapping | ProxyModel | ClassificationRule | AssumptionsRegister
WalkValue: TypeAlias = Record | Observable | RestrictionMap | Restriction | AssumptionInstance


class HeldRecords(Protocol):
    def holds(self, id: str) -> bool: ...
    def read(self, id: str) -> Node: ...
    def retraction_in_force(self, id: str) -> bool: ...
    def observation_held(self, digest: str) -> bool: ...
    def crosswalks(self, a: str, b: str) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class DependencyEntry:
    id: str
    terms: tuple[str, ...]


@dataclass(frozen=True)
class Walk:
    terms: frozenset[str]
    references: frozenset[str]


def read_record(records: HeldRecords, id: str) -> Record:
    if not records.holds(id):
        raise DependencyNotHeld(f"dependency {id!r} is not held")
    node = records.read(id)
    if node.id != id:
        raise MalformedRecord(f"dependency reader returned {node.id!r} for {id!r}")
    kind = id.partition(":")[0]
    record.address(id, kind)
    if kind == "procedure":
        return procedure_from_stored(node)
    if kind == "referent-mapping":
        return mapping_from_stored(node)
    if kind == "proxy-model":
        return proxy_from_stored(node)
    if kind == "classification-rule":
        return rule_from_stored(node)
    if kind == "assumptions-register":
        return register_from_stored(node)
    raise MalformedRecord(f"unsupported measurement dependency kind {kind!r}")


def walk(value: WalkValue, profile: ProfileSpec) -> Walk:
    terms: set[str] = set()
    references: set[str] = set()

    def visit(value: WalkValue) -> None:
        if isinstance(value, Observable):
            terms.update((value.quantity_kind, value.bearer_sort))
            if value.aspect is not None:
                terms.add(value.aspect.sort)
        elif isinstance(value, Mapping):
            for dimension, restriction in value.items():
                terms.add(dimension)
                visit(restriction)
        elif isinstance(value, TermRestriction):
            terms.add(value.sort)
        elif isinstance(value, IntervalRestriction):
            terms.update((value.unit, profile.units[value.unit].quantity_kind))
            if value.convention is not None:
                convention = profile.duration_conventions[value.convention]
                conversion = profile.conversions[convention.conversion]
                terms.update((value.convention, conversion.term))
                for unit in (conversion.from_unit, conversion.to_unit):
                    terms.update((unit, profile.units[unit].quantity_kind))
        elif isinstance(value, RuleRestriction):
            references.add(value.rule)
        elif isinstance(value, UnionRestriction):
            for member in value.members:
                visit(member)
        elif isinstance(value, (TimeIntervalRestriction, AssumptionsRegister)):
            pass
        elif isinstance(value, AssumptionInstance):
            terms.add(value.kind)
        elif isinstance(value, Procedure):
            terms.add(value.kind)
            for observable in value.yields:
                visit(observable)
            visit(value.validated_in)
            if isinstance(value.scale, SameAs):
                references.add(value.scale.authority)
        elif isinstance(value, ReferentMapping):
            terms.update((value.source_sort, value.target_sort))
            if value.aggregation is not None:
                terms.add(value.aggregation)
        elif isinstance(value, ProxyModel):
            visit(value.source.observable)
            references.add(value.source.procedure)
            if value.target.observable is not None:
                visit(value.target.observable)
            if value.target.scale_of is not None:
                references.add(value.target.scale_of)
            visit(value.validity)
            if isinstance(value.basis, Calibration):
                visit(value.basis.calibrated)
                references.update(value.basis.assessments)
                if value.basis.transfer is not None:
                    visit(value.basis.transfer)
            else:
                visit(value.basis)
        elif isinstance(value, ClassificationRule):
            terms.add(value.classes)
            for observable in value.reads:
                visit(observable)
        else:
            raise TypeError(f"unsupported dependency walk value: {type(value).__name__}")

    visit(value)
    return Walk(frozenset(terms), frozenset(references))


def record_terms(value: WalkValue, profile: ProfileSpec) -> tuple[str, ...]:
    return tuple(sorted(walk(value, profile).terms))


def record_references(value: WalkValue, profile: ProfileSpec) -> tuple[str, ...]:
    return tuple(sorted(walk(value, profile).references))


def dependency_closure(ids: Iterable[str], records: HeldRecords, profile: ProfileSpec) -> tuple[DependencyEntry, ...]:
    entries: dict[str, DependencyEntry] = {}
    active: set[str] = set()
    rule_classes: dict[str, str] = {}

    def follow(id: str) -> None:
        if id in active:
            raise DependencyCycle(f"dependency cycle at {id!r}")
        if id in entries:
            return
        if id.startswith("assessment:"):
            record.address(id, "assessment")
            if not records.holds(id):
                raise DependencyNotHeld(f"dependency {id!r} is not held")
            entries[id] = DependencyEntry(id, ())
            return
        value = read_record(records, id)
        active.add(id)
        result = walk(value, profile)
        for reference in sorted(result.references):
            follow(reference)
        if isinstance(value, ClassificationRule):
            rule_classes[id] = value.classes
        elif isinstance(value, Procedure):
            check_held_rule_scope(profile, value.validated_in, classes_of=rule_classes.__getitem__)
        elif isinstance(value, ProxyModel):
            check_held_rule_scope(profile, value.validity, classes_of=rule_classes.__getitem__)
        active.discard(id)
        entries[id] = DependencyEntry(id, tuple(sorted(result.terms)))

    for id in sorted(set(ids)):
        follow(id)
    return tuple(entries[id] for id in sorted(entries))
