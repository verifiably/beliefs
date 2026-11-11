"""Frozen assessed-target values and world-free dependency coverage checks."""

from dataclasses import dataclass
from typing import Literal, TypeAlias

from beliefs import _measurement_record as wire
from beliefs.applicability import Applicability, applicability_from_stored, applicability_projection
from beliefs.dependencies import DependencyEntry, dependencies_from_projection, dependencies_projection, walk
from beliefs.errors import MalformedRecord
from beliefs.estimand import (
    AxisLevels,
    Estimand,
    IncrementBinding,
    LagBinding,
    binding_roots,
    estimand_from_stored,
    estimand_projection,
    estimand_referents,
    measured_bindings,
)
from beliefs.profile import ProfileSpec

Standing: TypeAlias = Literal["empirical", "model", "calibrated-model"]


@dataclass(frozen=True)
class AssessedTarget:
    estimand: Estimand
    applicability: Applicability
    dependencies: tuple[DependencyEntry, ...]
    model: str | None
    standing: Standing

    def __post_init__(self) -> None:
        if not isinstance(self.estimand, Estimand) or not isinstance(self.applicability, Applicability):
            raise MalformedRecord("assessed targets require typed estimand and applicability values")
        if self.standing not in {"empirical", "model", "calibrated-model"}:
            raise MalformedRecord("unknown standing class")
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        entries = {e.id: e for e in self.dependencies}
        if tuple(entries) != tuple(sorted(entries)) or len(entries) != len(self.dependencies):
            raise MalformedRecord("target dependencies must be unique and sorted")
        roots = set(binding_roots(self.estimand)) | set(self.applicability.rule_ids())
        if self.model is not None:
            wire.address(self.model, "procedure")
            roots.add(self.model)
        if not roots <= entries.keys() or any(entries.get(e.id) != e for e in self.estimand.dependencies):
            raise MalformedRecord("assessed target dropped or changed a frozen dependency")


def target_projection(value: AssessedTarget) -> dict[str, object]:
    return {
        "estimand": estimand_projection(value.estimand),
        "applicability": applicability_projection(value.applicability),
        "dependencies": dependencies_projection(value.dependencies),
        **({"model": value.model} if value.model is not None else {}),
    }


def target_from_projection(value: object, *, standing: Standing, profile: ProfileSpec) -> AssessedTarget:
    body = wire.shape(value, {"estimand", "applicability", "dependencies"}, {"model"})
    estimand = estimand_from_stored(body["estimand"], profile=profile)
    applicability = applicability_from_stored(body["applicability"], profile=profile, operator=estimand.operator)
    return AssessedTarget(
        estimand,
        applicability,
        dependencies_from_projection(body["dependencies"]),
        wire.address(body["model"], "procedure") if "model" in body else None,
        standing,
    )


def target_terms(value: AssessedTarget, profile: ProfileSpec) -> frozenset[str]:
    """All vocabulary terms copied when a calibration freezes this target."""
    e = value.estimand
    operator = profile.operator(e.operator)
    terms = {
        operator.term,
        profile.template_of(operator).term,
        e.functional,
        e.control.identification,
        e.control.design,
        e.control.selection,
    }
    terms.update(r.sort for r in estimand_referents(e).values())

    def unit(term: str) -> None:
        terms.update((term, profile.units[term].quantity_kind))

    for binding in measured_bindings(e):
        terms.update(walk(binding.measure.observable, profile).terms)
        terms.add(binding.measure.transformation)
        if binding.measure.unit is not None:
            unit(binding.measure.unit)
    for binding in e.bindings.values():
        if isinstance(binding, IncrementBinding):
            unit(binding.unit)
        elif isinstance(binding, LagBinding):
            unit(binding.unit)
            for interval in binding.windows:
                terms.update(walk(interval, profile).terms)
        elif isinstance(binding, AxisLevels):
            for interval in binding.levels:
                terms.update(walk(interval, profile).terms)
    for output in e.outputs.values():
        if output.quantity_kind is not None:
            terms.add(output.quantity_kind)
        if output.unit is not None:
            unit(output.unit)
    terms.update(walk(value.applicability.restrictions(), profile).terms)
    terms.update(profile.dimensions[dim].restriction_sort for dim in value.applicability.values)
    terms.update(a.kind for a in e.assumptions)
    for entry in value.dependencies:
        terms.update(entry.terms)
    return frozenset(terms)
