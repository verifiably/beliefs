"""Shared shape and canonical-value checks for measurement record facets."""

import re
from collections.abc import Callable, Mapping
from fractions import Fraction
from types import MappingProxyType
from typing import TypeVar

from nodes.core.node import Node

from beliefs.errors import IdentityError, MalformedMeasure, MalformedRecord, MalformedRestriction
from beliefs.identifiers import canonical
from beliefs.identity import v1
from beliefs.measurement import Observable, observable_from_projection, observable_projection
from beliefs.restriction import (
    Restriction,
    decimal_from_projection,
    decimal_projection,
    restriction_from_projection,
    restriction_projection,
)

_T = TypeVar("_T")


def text(value: object, where: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value):
        raise MalformedRecord(f"{where}: expected {'a' if empty else 'a non-empty'} string")
    if canonical(value) != value:
        raise MalformedRecord(f"{where}: expected canonical NFC text")
    try:
        v1.encode(value)
    except IdentityError as exc:
        raise MalformedRecord(f"{where}: text is not canonically encodable") from exc
    return value


def term(value: object, where: str) -> str:
    result = text(value, where)
    if re.fullmatch(r"[a-z][a-z0-9-]*/[a-z][a-z0-9-]*", result) is None:
        raise MalformedRecord(f"{where}: expected <namespace>/<name>")
    return result


def address(value: object, kind: str) -> str:
    result = text(value, kind)
    if re.fullmatch(re.escape(kind) + r":[0-9a-f]{64}", result) is None:
        raise MalformedRecord(f"expected {kind}: followed by 64 lowercase hex digits")
    return result


def shape(value: object, required: set[str], optional: set[str] | frozenset[str] = frozenset()) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise MalformedRecord("expected an object with string keys")
    if not required <= value.keys() or set(value) - required - optional:
        raise MalformedRecord("missing or unexpected fields")
    if any(item is None for item in value.values()):
        raise MalformedRecord("optional fields must be absent, never null")
    return value


def sequence(value: object, read: Callable[[object], _T]) -> tuple[_T, ...]:
    if not isinstance(value, (list, tuple)):
        raise MalformedRecord("expected a sequence")
    return tuple(read(item) for item in value)


def strings(value: object) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise MalformedRecord("expected a mapping of strings")
    return MappingProxyType({text(k, "key"): text(v, "value", empty=True) for k, v in value.items()})


def observable(value: object) -> Observable:
    try:
        result = value if isinstance(value, Observable) else observable_from_projection(value)
        projection = observable_projection(result)
        if v1.decode(v1.encode(projection)) != projection:
            raise MalformedRecord("observable text must be canonical NFC")
        return result
    except (MalformedMeasure, IdentityError) as exc:
        raise MalformedRecord(f"invalid observable: {exc}") from exc


def observables(value: object) -> tuple[Observable, ...]:
    if not isinstance(value, (list, tuple)) or any(not isinstance(row, Observable) for row in value):
        raise MalformedRecord("expected typed observables")
    rows = sequence(value, observable)
    return tuple(sorted(set(rows), key=lambda row: v1.encode(observable_projection(row))))


def number(value: object) -> Fraction:
    if not isinstance(value, Fraction):
        raise MalformedRecord("a numeric field must be an exact Fraction")
    try:
        decimal_projection(value)
    except MalformedRestriction as exc:
        raise MalformedRecord(f"invalid exact decimal: {exc}") from exc
    return value


def number_from(value: object) -> Fraction:
    try:
        return decimal_from_projection(value)
    except MalformedRestriction as exc:
        raise MalformedRecord(f"invalid decimal string: {exc}") from exc


def scopes(value: object, *, stored: bool = False) -> Mapping[str, Restriction]:
    if not isinstance(value, Mapping):
        raise MalformedRecord("scope must be a restriction mapping")
    result: dict[str, Restriction] = {}
    for key, item in value.items():
        key = term(key, "scope dimension")
        if not stored and not isinstance(item, Restriction):
            raise MalformedRecord("scope values must be typed restrictions")
        try:
            projection = item if stored else restriction_projection(item)
            if isinstance(projection, list):
                form = "union"
            elif isinstance(projection, Mapping):
                forms = [
                    form
                    for field, form in (
                        ("sort", "term"),
                        ("unit", "interval"),
                        ("start", "time-interval"),
                        ("rule", "rule"),
                    )
                    if field in projection
                ]
                if len(forms) != 1:
                    raise MalformedRecord("unrecognized restriction shape")
                form = forms[0]
            else:
                raise MalformedRecord("unrecognized restriction shape")
            result[key] = restriction_from_projection(projection, form=form)
            projected = restriction_projection(result[key])
            if v1.decode(v1.encode(projected)) != projected:
                raise MalformedRecord("restriction text must be canonical NFC")
        except (MalformedRestriction, IdentityError) as exc:
            raise MalformedRecord(f"invalid restriction for {key}: {exc}") from exc
    return MappingProxyType(result)


def scope_projection(value: Mapping[str, Restriction]) -> dict[str, object]:
    return {key: restriction_projection(item) for key, item in value.items()}


def identity(kind: str, domain: str, projection: object) -> str:
    try:
        return kind + ":" + v1.digest(domain, projection)
    except IdentityError as exc:
        raise MalformedRecord("record fields are not canonically encodable") from exc


def from_stored(
    node: Node,
    kind: str,
    read: Callable[[object], _T],
    project: Callable[[_T], dict[str, object]],
    identify: Callable[[_T], str],
) -> _T:
    if node.kind != kind:
        raise MalformedRecord(f"{node.id}: not a {kind} record")
    try:
        facet = node.facets.get(kind)
        result = read(facet)
        if project(result) != facet:
            raise MalformedRecord("stored facet is not the canonical projection")
        if identify(result) != node.id:
            raise MalformedRecord("the id does not recompute from the facet")
        return result
    except MalformedRecord as exc:
        raise MalformedRecord(f"{node.id}: {exc}") from exc
