"""Content-addressed procedures, scale declarations and pinned implementations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction

from nodes.core.node import Node

from beliefs import _measurement_record as record
from beliefs.contract.base import SUPPORTED_MAPPING_TYPES, SUPPORTED_SCALE_ORIENTATIONS
from beliefs.errors import MalformedRecord
from beliefs.measurement import Observable, observable_projection
from beliefs.restriction import Restriction, decimal_projection

__all__ = [
    "PROCEDURE_DOMAIN",
    "PROCEDURE_FACET",
    "PROCEDURE_KIND",
    "External",
    "Implementation",
    "ModelInputs",
    "Procedure",
    "SameAs",
    "Scale",
    "procedure_from_stored",
    "procedure_identity",
    "procedure_projection",
]

PROCEDURE_DOMAIN = "science.procedure.v1"
PROCEDURE_KIND = PROCEDURE_FACET = "procedure"


@dataclass(frozen=True)
class Scale:
    range_low: Fraction
    range_high: Fraction
    orientation: str

    def __post_init__(self) -> None:
        record.number(self.range_low)
        record.number(self.range_high)
        if self.range_low >= self.range_high:
            raise MalformedRecord("scale range must have low < high")
        if record.text(self.orientation, "orientation") not in SUPPORTED_SCALE_ORIENTATIONS:
            raise MalformedRecord("unsupported scale orientation")


@dataclass(frozen=True)
class SameAs:
    authority: str

    def __post_init__(self) -> None:
        record.address(self.authority, PROCEDURE_KIND)


@dataclass(frozen=True)
class Implementation:
    reference: str
    digest: str

    def __post_init__(self) -> None:
        record.text(self.reference, "implementation reference")
        record.address(self.digest, "sha256")


@dataclass(frozen=True)
class External:
    reference: str
    mapping: str

    def __post_init__(self) -> None:
        record.text(self.reference, "external reference")
        if record.text(self.mapping, "external mapping") not in SUPPORTED_MAPPING_TYPES:
            raise MalformedRecord("unsupported external mapping")


@dataclass(frozen=True)
class ModelInputs:
    datasets: tuple[str, ...]
    code: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("datasets", "code"):
            values = record.sequence(getattr(self, name), lambda v: record.address(v, "sha256"))
            object.__setattr__(self, name, tuple(sorted(set(values))))


@dataclass(frozen=True)
class Procedure:
    kind: str
    name: str
    definition: str
    yields: tuple[Observable, ...]
    scale: Scale | SameAs | None
    validated_in: Mapping[str, Restriction]
    compatible_with: tuple[str, ...]
    evidence: tuple[str, ...]
    implementation: Implementation | None
    inputs: ModelInputs | None
    parameters: Mapping[str, str]
    external: External | None

    def __post_init__(self) -> None:
        record.term(self.kind, "procedure kind")
        record.text(self.name, "procedure name")
        record.text(self.definition, "procedure definition")
        object.__setattr__(self, "yields", record.observables(self.yields))
        if self.scale is not None and not isinstance(self.scale, (Scale, SameAs)):
            raise MalformedRecord("scale must be a range or same_as")
        object.__setattr__(self, "validated_in", record.scopes(self.validated_in))
        for name, kind in (("compatible_with", "procedure"), ("evidence", "assessment")):
            values = record.sequence(getattr(self, name), lambda v, kind=kind: record.address(v, kind))
            object.__setattr__(self, name, tuple(sorted(set(values))))
        object.__setattr__(self, "parameters", record.strings(self.parameters))
        for name, cls in (("implementation", Implementation), ("inputs", ModelInputs), ("external", External)):
            if getattr(self, name) is not None and not isinstance(getattr(self, name), cls):
                raise MalformedRecord(f"procedure {name} must be a {cls.__name__}")

    @property
    def is_authority(self) -> bool:
        return isinstance(self.scale, Scale)


def _implementation_projection(value: Implementation) -> dict[str, object]:
    return {"reference": value.reference, "digest": value.digest}


def _external_projection(value: External) -> dict[str, object]:
    return {"reference": value.reference, "mapping": value.mapping}


def _implementation_from(value: object) -> Implementation:
    fields = record.shape(value, {"reference", "digest"})
    return Implementation(
        record.text(fields["reference"], "implementation reference"), record.address(fields["digest"], "sha256")
    )


def _external_from(value: object) -> External:
    fields = record.shape(value, {"reference", "mapping"})
    return External(
        record.text(fields["reference"], "external reference"), record.text(fields["mapping"], "external mapping")
    )


def procedure_projection(value: Procedure) -> dict[str, object]:
    result: dict[str, object] = {
        "kind": value.kind,
        "name": value.name,
        "definition": value.definition,
        "yields": [observable_projection(row) for row in value.yields],
        "validated_in": record.scope_projection(value.validated_in),
        "compatible_with": list(value.compatible_with),
        "evidence": list(value.evidence),
        "parameters": dict(value.parameters),
    }
    if isinstance(value.scale, Scale):
        result["scale"] = {
            "range": [decimal_projection(value.scale.range_low), decimal_projection(value.scale.range_high)],
            "orientation": value.scale.orientation,
        }
    elif isinstance(value.scale, SameAs):
        result["scale"] = {"same_as": value.scale.authority}
    if value.implementation is not None:
        result["implementation"] = _implementation_projection(value.implementation)
    if value.inputs is not None:
        result["inputs"] = {"datasets": list(value.inputs.datasets), "code": list(value.inputs.code)}
    if value.external is not None:
        result["external"] = _external_projection(value.external)
    return result


def procedure_identity(value: Procedure) -> str:
    return record.identity(PROCEDURE_KIND, PROCEDURE_DOMAIN, procedure_projection(value))


def _procedure_from(value: object) -> Procedure:
    fields = record.shape(
        value,
        {"kind", "name", "definition", "yields", "validated_in", "compatible_with", "evidence", "parameters"},
        {"scale", "implementation", "inputs", "external"},
    )
    scale = None
    if "scale" in fields:
        raw = record.shape(fields["scale"], set(), {"range", "orientation", "same_as"})
        if set(raw) == {"same_as"}:
            scale = SameAs(record.address(raw["same_as"], "procedure"))
        elif set(raw) == {"range", "orientation"}:
            bounds = record.sequence(raw["range"], record.number_from)
            if len(bounds) != 2:
                raise MalformedRecord("a scale range has exactly two bounds")
            scale = Scale(bounds[0], bounds[1], record.text(raw["orientation"], "orientation"))
        else:
            raise MalformedRecord("scale is exactly range and orientation, or same_as")
    inputs = None
    if "inputs" in fields:
        raw = record.shape(fields["inputs"], {"datasets", "code"})
        inputs = ModelInputs(
            record.sequence(raw["datasets"], lambda v: record.address(v, "sha256")),
            record.sequence(raw["code"], lambda v: record.address(v, "sha256")),
        )
    return Procedure(
        record.term(fields["kind"], "procedure kind"),
        record.text(fields["name"], "name"),
        record.text(fields["definition"], "definition"),
        record.sequence(fields["yields"], record.observable),
        scale,
        record.scopes(fields["validated_in"], stored=True),
        record.sequence(fields["compatible_with"], lambda v: record.address(v, "procedure")),
        record.sequence(fields["evidence"], lambda v: record.address(v, "assessment")),
        _implementation_from(fields["implementation"]) if "implementation" in fields else None,
        inputs,
        record.strings(fields["parameters"]),
        _external_from(fields["external"]) if "external" in fields else None,
    )


def procedure_from_stored(node: Node) -> Procedure:
    return record.from_stored(node, PROCEDURE_KIND, _procedure_from, procedure_projection, procedure_identity)
