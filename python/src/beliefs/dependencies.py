"""Structural dependency walks over typed measurement records and contract terms."""

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from nodes.core.node import Node

from beliefs import _measurement_record as record
from beliefs.assumptions import AssumptionInstance
from beliefs.classification_rule import ClassificationRule, rule_from_stored
from beliefs.errors import DependencyCycle, DependencyNotHeld, IdentityError, MalformedRecord
from beliefs.identity import v1
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
    "FrozenAssessmentDependency",
    "HeldRecords",
    "Record",
    "Walk",
    "WalkValue",
    "dependencies_from_projection",
    "dependencies_projection",
    "dependency_closure",
    "read_record",
    "record_references",
    "record_terms",
    "walk",
]

ASSESSMENT_FACET_DOMAIN = "science.assessment-facet.v2"


def assessment_facet_digest(
    *, proposition: str, outcome: str, interpretation_rule: str, standing: str, typed: Mapping[str, object]
) -> str:
    """The canonical facet covered by a frozen assessment dependency."""
    return v1.digest(
        ASSESSMENT_FACET_DOMAIN,
        {
            "proposition": proposition,
            "outcome": outcome,
            "interpretation_rule": interpretation_rule,
            "standing": standing,
            **dict(typed),
        },
    )


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
    facet_digest: str | None = None

    def __post_init__(self) -> None:
        kind = self.id.partition(":")[0]
        record.address(self.id, kind)
        if self.terms != tuple(sorted(set(self.terms))):
            raise MalformedRecord("dependency terms must be sorted and unique")
        for term in self.terms:
            record.term(term, "dependency term")
        if kind == "assessment":
            if not isinstance(self.facet_digest, str) or re.fullmatch("[0-9a-f]{64}", self.facet_digest) is None:
                raise MalformedRecord("an assessment dependency requires its facet digest")
        elif self.facet_digest is not None:
            raise MalformedRecord("only an assessment dependency carries a facet digest")


@dataclass(frozen=True)
class FrozenAssessmentDependency:
    id: str
    facet_digest: str
    terms: tuple[str, ...]
    dependencies: tuple[DependencyEntry, ...]


def dependencies_projection(entries: tuple[DependencyEntry, ...]) -> list[dict[str, object]]:
    return [
        {"id": e.id, "terms": list(e.terms), **({"facet_digest": e.facet_digest} if e.facet_digest is not None else {})}
        for e in entries
    ]


def dependencies_from_projection(value: object) -> tuple[DependencyEntry, ...]:
    def read(value: object) -> DependencyEntry:
        row = record.shape(value, {"id", "terms"}, {"facet_digest"})
        return DependencyEntry(
            record.text(row["id"], "dependency id"),
            record.sequence(row["terms"], lambda t: record.term(t, "dependency term")),
            record.text(row["facet_digest"], "facet digest") if "facet_digest" in row else None,
        )

    entries = record.sequence(value, read)
    if tuple(e.id for e in entries) != tuple(sorted({e.id for e in entries})):
        raise MalformedRecord("dependencies must be sorted by id without duplicates")
    return entries


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


def dependency_closure(
    ids: Iterable[str],
    records: HeldRecords,
    profile: ProfileSpec,
    *,
    assessment_dependency: Callable[[str], FrozenAssessmentDependency] | None = None,
) -> tuple[DependencyEntry, ...]:
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
            if assessment_dependency is None:
                raise DependencyNotHeld("assessment dependency requires the frozen assessment callback")
            node = records.read(id)
            frozen = assessment_dependency(id)
            if node.id != id or frozen.id != id:
                raise MalformedRecord("assessment dependency callback returned a different identity")
            entry = DependencyEntry(id, frozen.terms, frozen.facet_digest)
            if any(dependency.id == id or dependency.id in active for dependency in frozen.dependencies):
                raise DependencyCycle(f"dependency cycle at {id!r}")
            facet = node.facets.get("assessment")
            if not isinstance(facet, Mapping) or not all(
                isinstance(facet.get(k), str)
                for k in ("typed", "proposition", "outcome", "interpretation_rule", "standing")
            ):
                raise MalformedRecord("assessment dependency has no v2 facet")
            try:
                typed = v1.decode(facet["typed"].encode("utf-8"))
            except IdentityError as error:
                raise MalformedRecord("assessment dependency facet is not canonical") from error
            if (
                not isinstance(typed, dict)
                or assessment_facet_digest(
                    proposition=facet["proposition"],
                    outcome=facet["outcome"],
                    interpretation_rule=facet["interpretation_rule"],
                    standing=facet["standing"],
                    typed=typed,
                )
                != entry.facet_digest
            ):
                raise MalformedRecord("assessment dependency facet digest disagrees with the held facet")
            if typed.get("dependencies") != dependencies_projection(frozen.dependencies):
                raise MalformedRecord("assessment callback dependencies disagree with the held facet")
            active.add(id)
            for dependency in frozen.dependencies:
                follow(dependency.id)
                if entries[dependency.id] != dependency:
                    raise MalformedRecord("assessment frozen dependency disagrees with its held record")
            active.remove(id)
            entries[id] = entry
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
