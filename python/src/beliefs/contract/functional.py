"""Immutable qualitative functional declarations and their closed form matrix."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar

from beliefs.contract import base
from beliefs.errors import MalformedContract

__all__ = ["FunctionalDecl", "ParameterDecl", "parse_functional"]


@dataclass(frozen=True)
class ParameterDecl:
    typing: str
    domain: str

    def schema_projection(self) -> dict[str, str]:
        return {"typing": self.typing, "domain": self.domain}


@dataclass(frozen=True)
class FunctionalDecl:
    form: str
    arity: str
    response_transformation: str
    reversal: str
    response_reversal: str
    exchange: str
    ties: str
    output: str
    domain: str
    null: str
    increment: str
    uncertainty: str
    parameters: Mapping[str, ParameterDecl] | None
    retired: ClassVar[bool] = False

    def __post_init__(self) -> None:
        if self.parameters is not None:
            object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))

    def schema_projection(self) -> dict[str, object]:
        return {
            **{name: getattr(self, name) for name in _VOCABULARIES},
            "parameters": (
                {name: parameter.schema_projection() for name, parameter in sorted(self.parameters.items())}
                if self.parameters is not None
                else "not-applicable"
            ),
        }


_VOCABULARIES = {
    "form": base.SUPPORTED_ESTIMAND_FORMS,
    "arity": base.SUPPORTED_ESTIMAND_ARITIES,
    "response_transformation": base.SUPPORTED_ESTIMAND_RESPONSE_TRANSFORMATIONS,
    "reversal": base.SUPPORTED_ESTIMAND_REVERSALS,
    "response_reversal": base.SUPPORTED_ESTIMAND_RESPONSE_REVERSALS,
    "exchange": base.SUPPORTED_ESTIMAND_EXCHANGES,
    "ties": base.SUPPORTED_ESTIMAND_TIES,
    "output": base.SUPPORTED_ESTIMAND_OUTPUTS,
    "domain": base.SUPPORTED_ESTIMAND_DOMAINS,
    "null": base.SUPPORTED_ESTIMAND_NULLS,
    "increment": base.SUPPORTED_ESTIMAND_INCREMENTS,
    "uncertainty": base.SUPPORTED_ESTIMAND_UNCERTAINTY_PROPAGATION,
}
_ARITIES = {
    "contrast": ("two", "k"),
    "quantity": ("one",),
    "law-parameters": ("not-applicable",),
    "event-locked": ("two", "k"),
    "association": ("two", "n"),
    "enrichment": ("not-applicable",),
}
_APPLICABLE = {
    "reversal": {"contrast", "event-locked"},
    "exchange": {"association"},
    "ties": {"contrast", "event-locked", "association"},
    "increment": {"contrast"},
}


def _mapping(raw: object, required: set[str], optional: set[str], where: str) -> dict[str, object]:
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise MalformedContract(f"{where}: expected a string-keyed mapping")
    if missing := required - raw.keys():
        raise MalformedContract(f"{where}: missing properties {sorted(missing)}")
    if extra := raw.keys() - required - optional:
        raise MalformedContract(f"{where}: unknown properties {sorted(extra)}")
    return raw


def _tag(raw: object, choices: tuple[str, ...], where: str) -> str:
    if not isinstance(raw, str) or raw not in choices:
        raise MalformedContract(f"{where}: expected one of {choices}, found {raw!r}")
    return raw


def parse_functional(raw: object) -> FunctionalDecl:
    body = _mapping(raw, {*_VOCABULARIES, "parameters"}, {"definition", "description", "external"}, "functional")
    for name in ("definition", "description"):
        if name in body:
            text = body[name]
            if not isinstance(text, str) or not text.strip():
                raise MalformedContract(f"functional {name}: expected nonempty prose")
    if "external" in body:
        external = _mapping(body["external"], {"reference", "mapping"}, set(), "functional external")
        if not isinstance(external["reference"], str) or not external["reference"].strip():
            raise MalformedContract("functional external reference must be nonempty text")
        _tag(external["mapping"], base.SUPPORTED_MAPPING_TYPES, "functional external mapping")
    values = {name: _tag(body[name], choices, f"functional {name}") for name, choices in _VOCABULARIES.items()}
    form = values["form"]
    if values["arity"] not in _ARITIES[form]:
        raise MalformedContract(f"functional arity does not match {form}")
    for name, forms in _APPLICABLE.items():
        value = values[name]
        if form not in forms and value != "not-applicable":
            raise MalformedContract(f"functional {name} is not applicable to {form}")
        if name in {"reversal", "exchange", "increment"} and form in forms and value == "not-applicable":
            raise MalformedContract(f"functional {name} is required for {form}")
    certificate = values["response_transformation"]
    if (certificate in {"invariant-strictly-increasing", "equivariant-affine"}) == (
        values["response_reversal"] == "not-applicable"
    ):
        raise MalformedContract("functional response_reversal does not match its certificate")
    declared = values["output"] == "declared"
    if declared != (certificate == "by-parameters"):
        raise MalformedContract("declared output and by-parameters certificate are required together")
    parameters = None
    if declared:
        raw_parameters = body["parameters"]
        if not isinstance(raw_parameters, dict) or not raw_parameters:
            raise MalformedContract("functional declared output requires named parameters")
        parsed = {}
        for name, raw_parameter in raw_parameters.items():
            if not isinstance(name, str) or not name.strip():
                raise MalformedContract("functional parameter names must be nonempty")
            parameter = _mapping(raw_parameter, {"typing", "domain"}, set(), f"parameter {name}")
            parsed[name] = ParameterDecl(
                _tag(parameter["typing"], base.SUPPORTED_ESTIMAND_PARAMETER_TYPINGS, f"parameter {name} typing"),
                _tag(
                    parameter["domain"],
                    tuple(d for d in base.SUPPORTED_ESTIMAND_DOMAINS if d != "not-applicable"),
                    f"parameter {name} domain",
                ),
            )
        parameters = parsed
    elif body["parameters"] != "not-applicable":
        raise MalformedContract("functional parameters are only applicable to declared outputs")
    if declared != (values["domain"] == "not-applicable"):
        raise MalformedContract("functional output domain does not match its output typing")
    if form == "law-parameters" and (not declared or values["null"] != "none"):
        raise MalformedContract("law-parameters requires declared parameters and null none")
    if form == "enrichment" and certificate != "fixed":
        raise MalformedContract("enrichment requires a fixed response certificate")
    for action in (values["reversal"], values["response_reversal"]):
        if action == "reciprocal" and values["domain"] != "positive":
            raise MalformedContract("reciprocal requires a positive domain")
        fixed_null = {"negate": "zero", "complement": "half", "reciprocal": "one"}.get(action)
        if values["null"] != "none" and fixed_null is not None and values["null"] != fixed_null:
            raise MalformedContract(f"functional null is not a fixed point of {action}")
    return FunctionalDecl(**values, parameters=parameters)
