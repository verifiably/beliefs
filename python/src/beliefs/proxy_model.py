"""Content-addressed proxy models, calibration bases and exact crosswalks."""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction

from nodes.core.node import Node

from beliefs import _measurement_record as record
from beliefs.assumptions import AssumptionInstance, instance_from_projection, instance_projection
from beliefs.contract.base import SUPPORTED_CONVERSION_KINDS
from beliefs.errors import MalformedRecord
from beliefs.measurement import Observable, observable_projection
from beliefs.restriction import Restriction, decimal_projection

__all__ = [
    "PROXY_DOMAIN",
    "PROXY_FACET",
    "PROXY_KIND",
    "Calibration",
    "Conversion",
    "Crosswalk",
    "Error",
    "ProxyModel",
    "ProxySource",
    "ProxyTarget",
    "proxy_from_stored",
    "proxy_identity",
    "proxy_projection",
]

PROXY_DOMAIN = "science.proxy-model.v1"
PROXY_KIND = PROXY_FACET = "proxy-model"


@dataclass(frozen=True)
class ProxySource:
    observable: Observable
    procedure: str

    def __post_init__(self) -> None:
        if not isinstance(self.observable, Observable):
            raise MalformedRecord("source observable must be an Observable")
        record.observable(self.observable)
        record.address(self.procedure, "procedure")


@dataclass(frozen=True)
class ProxyTarget:
    observable: Observable | None
    scale_of: str | None

    def __post_init__(self) -> None:
        if (self.observable is None) == (self.scale_of is None):
            raise MalformedRecord("target requires exactly one of observable or scale_of")
        if self.observable is not None:
            if not isinstance(self.observable, Observable):
                raise MalformedRecord("target observable must be an Observable")
            record.observable(self.observable)
        if self.scale_of is not None:
            record.address(self.scale_of, "procedure")


@dataclass(frozen=True)
class Calibration:
    calibrated: Observable
    assessments: tuple[str, ...]
    rules: tuple[str, ...]
    transfer: AssumptionInstance | None

    def __post_init__(self) -> None:
        if not isinstance(self.calibrated, Observable):
            raise MalformedRecord("calibrated must be an Observable")
        record.observable(self.calibrated)
        object.__setattr__(
            self,
            "assessments",
            tuple(sorted(set(record.sequence(self.assessments, lambda v: record.address(v, "assessment"))))),
        )
        object.__setattr__(
            self,
            "rules",
            tuple(sorted(set(record.sequence(self.rules, lambda v: record.text(v, "interpretation rule identity"))))),
        )
        if self.transfer is not None and not isinstance(self.transfer, AssumptionInstance):
            raise MalformedRecord("transfer must be an AssumptionInstance")


@dataclass(frozen=True)
class Conversion:
    kind: str
    factor: Fraction
    offset: Fraction | None

    def __post_init__(self) -> None:
        if record.text(self.kind, "conversion kind") not in SUPPORTED_CONVERSION_KINDS:
            raise MalformedRecord("unsupported conversion kind")
        record.number(self.factor)
        if (self.kind == "affine") != (self.offset is not None):
            raise MalformedRecord("offset is required exactly for an affine conversion")
        if self.offset is not None:
            record.number(self.offset)


@dataclass(frozen=True)
class Error:
    kind: str
    value: Fraction

    def __post_init__(self) -> None:
        record.text(self.kind, "error kind")
        record.number(self.value)


@dataclass(frozen=True)
class Crosswalk:
    linking_population: Mapping[str, str]
    conversion: Conversion
    error: Error

    def __post_init__(self) -> None:
        object.__setattr__(self, "linking_population", record.strings(self.linking_population))
        if not isinstance(self.conversion, Conversion) or not isinstance(self.error, Error):
            raise MalformedRecord("crosswalk requires a Conversion and Error")


@dataclass(frozen=True)
class ProxyModel:
    source: ProxySource
    target: ProxyTarget
    validity: Mapping[str, Restriction]
    basis: Calibration | AssumptionInstance
    crosswalk: Crosswalk | None

    def __post_init__(self) -> None:
        if not isinstance(self.source, ProxySource) or not isinstance(self.target, ProxyTarget):
            raise MalformedRecord("proxy requires a ProxySource and ProxyTarget")
        if not isinstance(self.basis, (Calibration, AssumptionInstance)):
            raise MalformedRecord("proxy basis must be a calibration or assumption")
        if self.crosswalk is not None and not isinstance(self.crosswalk, Crosswalk):
            raise MalformedRecord("crosswalk must be a Crosswalk")
        if (self.crosswalk is not None) != (self.target.scale_of is not None):
            raise MalformedRecord("crosswalk is required exactly for a scale_of target")
        if (
            isinstance(self.basis, Calibration)
            and self.target.observable is not None
            and (self.basis.transfer is not None) != (self.basis.calibrated != self.target.observable)
        ):
            raise MalformedRecord("calibration transfer is required exactly when calibrated differs from target")
        object.__setattr__(self, "validity", record.scopes(self.validity))

    @property
    def references(self) -> tuple[str, ...]:
        values = (self.source.procedure,)
        if self.target.scale_of is not None:
            values += (self.target.scale_of,)
        if isinstance(self.basis, Calibration):
            values += self.basis.assessments
        return tuple(sorted(set(values)))


def proxy_projection(value: ProxyModel) -> dict[str, object]:
    result: dict[str, object] = {
        "source": {"observable": observable_projection(value.source.observable), "procedure": value.source.procedure},
        "target": {"observable": observable_projection(value.target.observable)}
        if value.target.observable is not None
        else {"scale_of": value.target.scale_of},
        "validity": record.scope_projection(value.validity),
    }
    if isinstance(value.basis, Calibration):
        calibration: dict[str, object] = {
            "calibrated": {"observable": observable_projection(value.basis.calibrated)},
            "assessments": list(value.basis.assessments),
            "rules": list(value.basis.rules),
        }
        if value.basis.transfer is not None:
            calibration["transfer"] = instance_projection(value.basis.transfer)
        result["basis"] = {"calibration": calibration}
    else:
        result["basis"] = {"assumption": instance_projection(value.basis)}
    if value.crosswalk is not None:
        conversion = value.crosswalk.conversion
        coefficients: dict[str, object] = {"kind": conversion.kind}
        if conversion.kind == "affine":
            assert conversion.offset is not None
            coefficients.update(
                scale=decimal_projection(conversion.factor), offset=decimal_projection(conversion.offset)
            )
        else:
            coefficients["factor"] = decimal_projection(conversion.factor)
        result["crosswalk"] = {
            "linking_population": dict(value.crosswalk.linking_population),
            "conversion": coefficients,
            "error": {"kind": value.crosswalk.error.kind, "value": decimal_projection(value.crosswalk.error.value)},
        }
    return result


def proxy_identity(value: ProxyModel) -> str:
    return record.identity(PROXY_KIND, PROXY_DOMAIN, proxy_projection(value))


def _calibration_from(value: object) -> Calibration:
    fields = record.shape(value, {"calibrated", "assessments", "rules"}, {"transfer"})
    calibrated = record.shape(fields["calibrated"], {"observable"})
    return Calibration(
        record.observable(calibrated["observable"]),
        record.sequence(fields["assessments"], lambda v: record.address(v, "assessment")),
        record.sequence(fields["rules"], lambda v: record.text(v, "interpretation rule identity")),
        instance_from_projection(fields["transfer"]) if "transfer" in fields else None,
    )


def _crosswalk_from(value: object) -> Crosswalk:
    fields = record.shape(value, {"linking_population", "conversion", "error"})
    conversion = record.shape(fields["conversion"], {"kind"}, {"factor", "scale", "offset"})
    kind = record.text(conversion["kind"], "conversion kind")
    if kind == "affine":
        conversion = record.shape(conversion, {"kind", "scale", "offset"})
        converted = Conversion(kind, record.number_from(conversion["scale"]), record.number_from(conversion["offset"]))
    elif kind == "multiplicative":
        conversion = record.shape(conversion, {"kind", "factor"})
        converted = Conversion(kind, record.number_from(conversion["factor"]), None)
    else:
        raise MalformedRecord("unsupported conversion kind")
    error = record.shape(fields["error"], {"kind", "value"})
    return Crosswalk(
        record.strings(fields["linking_population"]),
        converted,
        Error(record.text(error["kind"], "error kind"), record.number_from(error["value"])),
    )


def _proxy_from(value: object) -> ProxyModel:
    fields = record.shape(value, {"source", "target", "validity", "basis"}, {"crosswalk"})
    source = record.shape(fields["source"], {"observable", "procedure"})
    target = record.shape(fields["target"], set(), {"observable", "scale_of"})
    basis = record.shape(fields["basis"], set(), {"calibration", "assumption"})
    if len(basis) != 1:
        raise MalformedRecord("basis requires exactly one of calibration or assumption")
    return ProxyModel(
        ProxySource(record.observable(source["observable"]), record.address(source["procedure"], "procedure")),
        ProxyTarget(
            record.observable(target["observable"]) if "observable" in target else None,
            record.address(target["scale_of"], "procedure") if "scale_of" in target else None,
        ),
        record.scopes(fields["validity"], stored=True),
        _calibration_from(basis["calibration"])
        if "calibration" in basis
        else instance_from_projection(basis["assumption"]),
        _crosswalk_from(fields["crosswalk"]) if "crosswalk" in fields else None,
    )


def proxy_from_stored(node: Node) -> ProxyModel:
    return record.from_stored(node, PROXY_KIND, _proxy_from, proxy_projection, proxy_identity)
