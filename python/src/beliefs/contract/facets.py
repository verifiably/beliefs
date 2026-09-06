"""Facet declaration parsing shared by base and domain contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from beliefs.errors import MalformedContract

__all__ = ["FIELD_TYPES", "FacetDecl", "FieldDecl", "parse_facet_declarations"]

FIELD_TYPES = ("string", "integer", "boolean", "ref", "locator", "actor")
_FIELD_NAME = re.compile(r"[a-z][a-z0-9_]*")
_KEY = re.compile(r"[a-z][a-z0-9-]*")
_FIELD_KEYS = frozenset({"type", "required", "kinds", "schemes"})


@dataclass(frozen=True)
class FieldDecl:
    name: str
    type: str
    required: bool
    kinds: tuple[str, ...]
    schemes: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        projection: dict[str, object] = {"type": self.type, "required": self.required}
        if self.type == "ref":
            projection["kinds"] = sorted(self.kinds)
        if self.type == "locator":
            projection["schemes"] = sorted(self.schemes)
        return projection


@dataclass(frozen=True)
class FacetDecl:
    key: str
    shape: str
    fields: Mapping[str, FieldDecl]
    attaches_to: tuple[str, ...]
    description: str | None

    def projection(self) -> dict[str, object]:
        return {
            "shape": self.shape,
            "fields": {name: field.projection() for name, field in sorted(self.fields.items())},
            "attaches_to": sorted(self.attaches_to),
        }


def _mapping(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise MalformedContract(f"{where}: expected a mapping with string keys")
    return value  # type: ignore[return-value]


def _names(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MalformedContract(f"{where}: expected a non-empty list")
    names: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not _KEY.fullmatch(entry):
            raise MalformedContract(f"{where}: {entry!r} is not an identifier")
        if entry in names:
            raise MalformedContract(f"{where}: duplicate {entry!r}")
        names.append(entry)
    return tuple(names)


def parse_field(name: str, value: object, where: str) -> FieldDecl:
    if not _FIELD_NAME.fullmatch(name):
        raise MalformedContract(f"{where}: {name!r} is not a field identifier; expected `[a-z][a-z0-9_]*`")
    body = _mapping(value, where)
    unknown = sorted(set(body) - _FIELD_KEYS)
    if unknown:
        raise MalformedContract(f"{where}: unknown field key(s) {', '.join(unknown)}; refused, never ignored")
    field_type = body.get("type")
    if field_type not in FIELD_TYPES:
        raise MalformedContract(f"{where}: type {field_type!r} is not one of {', '.join(FIELD_TYPES)}")
    if "required" not in body or not isinstance(body["required"], bool):
        raise MalformedContract(f"{where}: required is a mandatory boolean")
    if ("kinds" in body) != (field_type == "ref"):
        raise MalformedContract(f"{where}: kinds is required for type ref and refused for every other type")
    if ("schemes" in body) != (field_type == "locator"):
        raise MalformedContract(f"{where}: schemes is required for type locator and refused for every other type")
    kinds = _names(body["kinds"], f"{where}: kinds") if field_type == "ref" else ()
    schemes = _names(body["schemes"], f"{where}: schemes") if field_type == "locator" else ()
    return FieldDecl(name, field_type, body["required"], kinds, schemes)


def parse_facet_declarations(value: object, *, where: str, namespace: str | None) -> dict[str, FacetDecl]:
    declarations: dict[str, FacetDecl] = {}
    for local, body_value in _mapping(value, where).items():
        if not _KEY.fullmatch(local):
            raise MalformedContract(f"{where}: {local!r} is not a facet identifier")
        facet_where = f"{where}.{local}"
        body = _mapping(body_value, facet_where)
        key = local if namespace is None else f"{namespace}/{local}"
        raw_description = body.get("description")
        if "description" in body and not isinstance(raw_description, str):
            raise MalformedContract(f"{facet_where}: description is a string, never null")
        description = raw_description if isinstance(raw_description, str) else None
        if namespace is None:
            shape = body.get("shape")
            if shape not in ("reader", "schema"):
                raise MalformedContract(f"{facet_where}: shape is `reader` or `schema`, found {shape!r}")
            permitted = {"shape", "description", "reader"} if shape == "reader" else {"shape", "description", "fields"}
            unknown = sorted(set(body) - permitted)
            if unknown:
                raise MalformedContract(
                    f"{facet_where}: unknown key(s) {', '.join(unknown)} for a {shape}-shaped facet"
                )
            if shape == "reader":
                if not isinstance(body.get("reader"), str) or not body["reader"]:
                    raise MalformedContract(f"{facet_where}: a reader-shaped facet names its reader")
                declarations[key] = FacetDecl(key, "reader", MappingProxyType({}), (), description)
                continue
            if "fields" not in body:
                raise MalformedContract(f"{facet_where}: a schema-shaped facet declares fields")
            attaches_to: tuple[str, ...] = ()
        else:
            unknown = sorted(set(body) - {"attaches_to", "fields", "description"})
            if unknown:
                raise MalformedContract(f"{facet_where}: unknown key(s) {', '.join(unknown)}")
            if "attaches_to" not in body or "fields" not in body:
                raise MalformedContract(f"{facet_where}: a domain facet declares attaches_to and fields")
            attaches_to = _names(body["attaches_to"], f"{facet_where}: attaches_to")
        fields = {
            name: parse_field(name, field_value, f"{facet_where}.fields.{name}")
            for name, field_value in _mapping(body["fields"], f"{facet_where}.fields").items()
        }
        declarations[key] = FacetDecl(key, "schema", MappingProxyType(fields), attaches_to, description)
    return declarations
