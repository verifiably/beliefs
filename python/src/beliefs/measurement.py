"""Observable identity and explicit coordinates of measured values."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from beliefs.contract.base import SUPPORTED_LEVELS_OF_MEASUREMENT, SUPPORTED_VALUE_TYPES
from beliefs.errors import AspectNotAdmitted, MalformedMeasure, UndeclaredQuantityKind
from beliefs.profile import ProfileSpec

if TYPE_CHECKING:
    from beliefs.procedure import Procedure

__all__ = [
    "Aspect",
    "Coordinates",
    "Measure",
    "Observable",
    "check_measure",
    "check_measure_procedure",
    "check_observable",
    "measure_from_projection",
    "measure_projection",
    "observable_from_projection",
    "observable_projection",
]

_TERM = re.compile(r"[a-z][a-z0-9-]*/[a-z][a-z0-9-]*")
_PROCEDURE = re.compile(r"procedure:[0-9a-f]{64}")


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise MalformedMeasure(f"{where}: expected a non-empty string")
    return value


def _term(value: object, where: str) -> str:
    text = _text(value, where)
    if _TERM.fullmatch(text) is None:
        raise MalformedMeasure(f"{where}: expected <namespace>/<name>")
    return text


def _procedure(value: object, where: str) -> str:
    text = _text(value, where)
    if _PROCEDURE.fullmatch(text) is None:
        raise MalformedMeasure(f"{where}: expected a procedure id with 64 lowercase hex digits")
    return text


@dataclass(frozen=True)
class Aspect:
    sort: str
    term: str

    def __post_init__(self) -> None:
        _term(self.sort, "aspect sort")
        _text(self.term, "aspect term")


@dataclass(frozen=True)
class Observable:
    quantity_kind: str
    bearer_sort: str
    aspect: Aspect | None = None

    def __post_init__(self) -> None:
        _term(self.quantity_kind, "observable quantity kind")
        _term(self.bearer_sort, "observable bearer sort")
        if self.aspect is not None and not isinstance(self.aspect, Aspect):
            raise MalformedMeasure("observable aspect must be an Aspect")


def observable_projection(observable: Observable) -> dict[str, object]:
    value: dict[str, object] = {
        "quantity_kind": observable.quantity_kind,
        "bearer_sort": observable.bearer_sort,
    }
    if observable.aspect is not None:
        value["aspect"] = {"sort": observable.aspect.sort, "term": observable.aspect.term}
    return value


def _shape(value: object, required: set[str], optional: set[str], where: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise MalformedMeasure(f"{where}: expected an object")
    if not required <= value.keys() or set(value) - required - optional:
        raise MalformedMeasure(f"{where}: missing or unexpected fields")
    if any(field is None for field in value.values()):
        raise MalformedMeasure(f"{where}: optional fields must be absent, never null")
    return value


def observable_from_projection(value: object) -> Observable:
    fields = _shape(value, {"quantity_kind", "bearer_sort"}, {"aspect"}, "observable")
    aspect = None
    if "aspect" in fields:
        parts = _shape(fields["aspect"], {"sort", "term"}, set(), "aspect")
        aspect = Aspect(_term(parts["sort"], "aspect sort"), _text(parts["term"], "aspect term"))
    return Observable(
        _term(fields["quantity_kind"], "observable quantity kind"),
        _term(fields["bearer_sort"], "observable bearer sort"),
        aspect,
    )


def check_observable(profile: ProfileSpec, observable: Observable) -> None:
    if observable.quantity_kind not in profile.quantity_kinds:
        raise UndeclaredQuantityKind(f"undeclared quantity kind {observable.quantity_kind!r}")
    if observable.bearer_sort not in profile.sorts:
        raise MalformedMeasure(f"undeclared bearer sort {observable.bearer_sort!r}")
    if observable.aspect is not None:
        if observable.aspect.sort not in profile.sorts:
            raise MalformedMeasure(f"undeclared aspect sort {observable.aspect.sort!r}")
        if observable.aspect.sort not in profile.aspect_sorts(observable.quantity_kind):
            raise AspectNotAdmitted(
                f"aspect sort {observable.aspect.sort!r} is not admitted for {observable.quantity_kind!r}"
            )


@dataclass(frozen=True)
class Coordinates:
    """The coordinate view used for conversion, independent of bearer and procedure."""

    quantity_kind: str
    unit: str | None
    scale: str | None
    value_type: str
    transformation: str

    def __post_init__(self) -> None:
        _term(self.quantity_kind, "coordinate quantity kind")
        if (self.unit is None) == (self.scale is None):
            raise MalformedMeasure("exactly one of unit or scale is required")
        if self.unit is not None:
            _term(self.unit, "measure unit")
        if self.scale is not None:
            _procedure(self.scale, "measure scale")
        if _text(self.value_type, "measure value type") not in SUPPORTED_VALUE_TYPES:
            raise MalformedMeasure(f"unsupported value type {self.value_type!r}")
        _term(self.transformation, "measure transformation")


@dataclass(frozen=True)
class Measure:
    observable: Observable
    unit: str | None
    scale: str | None
    level: str
    value_type: str
    transformation: str
    procedure: str

    def __post_init__(self) -> None:
        if not isinstance(self.observable, Observable):
            raise MalformedMeasure("measure observable must be an Observable")
        _ = self.coordinates
        if _text(self.level, "measure level") not in SUPPORTED_LEVELS_OF_MEASUREMENT:
            raise MalformedMeasure(f"unsupported level of measurement {self.level!r}")
        if self.value_type == "ratio" and self.level != "ratio":
            raise MalformedMeasure("a ratio value type requires ratio-level values")
        if self.value_type == "difference" and self.level == "nominal":
            raise MalformedMeasure("a difference value type refuses nominal-level values")
        _procedure(self.procedure, "measure procedure")

    @property
    def coordinates(self) -> Coordinates:
        return Coordinates(self.observable.quantity_kind, self.unit, self.scale, self.value_type, self.transformation)


def measure_projection(measure: Measure) -> dict[str, object]:
    value: dict[str, object] = {
        "observable": observable_projection(measure.observable),
        "level": measure.level,
        "value_type": measure.value_type,
        "transformation": measure.transformation,
        "procedure": measure.procedure,
    }
    if measure.unit is not None:
        value["unit"] = measure.unit
    if measure.scale is not None:
        value["scale"] = measure.scale
    return value


def measure_from_projection(value: object) -> Measure:
    fields = _shape(
        value,
        {"observable", "level", "value_type", "transformation", "procedure"},
        {"unit", "scale"},
        "measure",
    )
    return Measure(
        observable_from_projection(fields["observable"]),
        _term(fields["unit"], "measure unit") if "unit" in fields else None,
        _procedure(fields["scale"], "measure scale") if "scale" in fields else None,
        _text(fields["level"], "measure level"),
        _text(fields["value_type"], "measure value type"),
        _term(fields["transformation"], "measure transformation"),
        _procedure(fields["procedure"], "measure procedure"),
    )


def check_measure(profile: ProfileSpec, measure: Measure) -> None:
    check_observable(profile, measure.observable)
    if measure.unit is not None:
        unit = profile.units.get(measure.unit)
        if unit is None:
            raise MalformedMeasure(f"undeclared unit {measure.unit!r}")
        if unit.quantity_kind != measure.observable.quantity_kind:
            raise MalformedMeasure("the unit's quantity kind must match the observable's")
    transformation = profile.transformations.get(measure.transformation)
    if transformation is None:
        raise MalformedMeasure(f"undeclared transformation {measure.transformation!r}")
    if transformation.kind == "logarithm" and measure.level == "ratio":
        raise MalformedMeasure("a logarithm refuses ratio-level values")


def check_measure_procedure(measure: Measure, procedure: Procedure, authority: Procedure | None) -> None:
    """Check the complete yield before resolving the measurement's scale authority."""
    from beliefs.errors import ProcedureYieldMismatch, ScaleAuthorityMismatch
    from beliefs.procedure import SameAs, procedure_identity

    if measure.observable not in procedure.yields:
        raise ProcedureYieldMismatch("the procedure does not yield this complete observable")
    if measure.scale is None:
        return
    expected = (
        procedure_identity(procedure)
        if procedure.is_authority
        else (procedure.scale.authority if isinstance(procedure.scale, SameAs) else None)
    )
    if (
        measure.scale != expected
        or authority is None
        or not authority.is_authority
        or procedure_identity(authority) != expected
    ):
        raise ScaleAuthorityMismatch("the measure's scale does not match its procedure's held authority")
