"""Payload validation for schema-shaped facets (facet-contracts design §3.4, §4.1).

Shape only: a `ref` is checked for its kind prefix and a non-empty local, never
for resolution, which is the writer's seam rule (§5.2); an `actor` is checked
non-empty, never for identity, which is the writer's binding rule (§5.3).
"""

from __future__ import annotations

from collections.abc import Mapping

from beliefs.errors import FacetPayloadRefused
from beliefs.profile import CompiledFacet

__all__ = ["validate_payload"]


def _refuse(where: str, key: str, reason: str) -> FacetPayloadRefused:
    return FacetPayloadRefused(f"{where}: facet {key!r} payload malformed: {reason}")


def validate_payload(facet: CompiledFacet, payload: object, *, where: str) -> None:
    if facet.shape != "schema":
        return
    if not isinstance(payload, Mapping):
        raise _refuse(where, facet.key, "a facet payload is a mapping")
    unknown = sorted(set(payload) - set(facet.fields), key=repr)
    if unknown:
        raise _refuse(where, facet.key, f"unknown key(s) {', '.join(map(repr, unknown))}; refused, never ignored")
    for name, field in facet.fields.items():
        if name not in payload:
            if field.required:
                raise _refuse(where, facet.key, f"missing required field {name!r}")
            continue
        value = payload[name]
        if value is None:
            raise _refuse(where, facet.key, f"{name!r} is null; a field is present or absent, never null")
        if isinstance(value, (Mapping, list, tuple)):
            raise _refuse(where, facet.key, f"{name!r} is nested; the grammar admits no nesting")
        if field.type == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                raise _refuse(where, facet.key, f"{name!r} must be an integer")
            continue
        if field.type == "boolean":
            if not isinstance(value, bool):
                raise _refuse(where, facet.key, f"{name!r} must be a boolean")
            continue
        if not isinstance(value, str) or not value:
            raise _refuse(where, facet.key, f"{name!r} must be a non-empty string ({field.type})")
        if field.type in ("string", "actor"):
            continue
        prefix, separator, rest = value.partition(":")
        if separator != ":" or not rest:
            what = "kind" if field.type == "ref" else "scheme"
            raise _refuse(where, facet.key, f"{name!r} must be `<{what}>:<rest>` with a non-empty remainder")
        if field.type == "ref" and prefix not in field.kinds:
            raise _refuse(
                where, facet.key, f"{name!r} names kind {prefix!r}; declared kinds are {', '.join(field.kinds)}"
            )
        if field.type == "locator" and prefix not in field.schemes:
            raise _refuse(
                where, facet.key, f"{name!r} uses scheme {prefix!r}; declared schemes are {', '.join(field.schemes)}"
            )
