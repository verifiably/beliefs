"""Declared scope relations: endpoint values and the domain declaration table.

A scope relation is a reviewed, normative commitment that two leaf scopes of one
applicability dimension select exactly the same cases (`equal`) or that the left
scope is properly contained in the right (`narrower`). The base contract owns the
closed relation vocabulary; a domain contract declares relations by name.

Endpoints are exactly one term of the dimension's sort, or exactly one class of
one classification rule named by its exact record id. Mixed, union, interval or
multi-class endpoints are refused: the declared fragment is equality and strict
atomic containment and nothing more.

Parsing checks shape only. Dimension, sort and identifier-class agreement need
the other contracts and are checked when the profile compiles; a rule body's
contents need held records and are checked where a comparison is used.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from beliefs.errors import MalformedContract
from beliefs.identifiers import not_a_canonical_identifier

__all__ = [
    "SCOPE_RELATION_FIELDS",
    "CompiledScopeRelation",
    "RuleScopeEndpoint",
    "ScopeEndpoint",
    "ScopeRelation",
    "ScopeRelationDecl",
    "TermScopeEndpoint",
    "parse_scope_relations",
]

ScopeRelation = Literal["equal", "narrower"]
SCOPE_RELATION_FIELDS = frozenset({"dimension", "relation", "left", "right"})
_EDITORIAL = frozenset({"description", "retired"})
_NAME = re.compile(r"[a-z][a-z0-9-]*")
_RULE = re.compile(r"classification-rule:[0-9a-f]{64}")


def _identifier(value: object, where: str) -> str:
    problem = not_a_canonical_identifier(value)
    if problem is not None:
        raise MalformedContract(f"{where}: {problem}")
    assert isinstance(value, str)
    return value


@dataclass(frozen=True)
class TermScopeEndpoint:
    """One term of the dimension's restriction sort."""

    sort: str
    term: str

    def __post_init__(self) -> None:
        if not isinstance(self.sort, str) or not self.sort:
            raise MalformedContract("a term scope endpoint names a sort")
        _identifier(self.term, "term scope endpoint")

    def projection(self) -> dict[str, object]:
        return {"sort": self.sort, "term": self.term}


@dataclass(frozen=True)
class RuleScopeEndpoint:
    """Exactly one class of one classification rule, named by exact record id."""

    rule: str
    classes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.rule, str) or _RULE.fullmatch(self.rule) is None:
            raise MalformedContract(f"a rule scope endpoint names a classification-rule id, found {self.rule!r}")
        if not isinstance(self.classes, tuple) or len(self.classes) != 1:
            raise MalformedContract(
                "a rule scope endpoint names exactly one class; a class set is not a declared endpoint"
            )
        _identifier(self.classes[0], "rule scope endpoint class")

    def projection(self) -> dict[str, object]:
        return {"rule": self.rule, "classes": list(self.classes)}


ScopeEndpoint = TermScopeEndpoint | RuleScopeEndpoint


@dataclass(frozen=True)
class ScopeRelationDecl:
    """A named relation between two leaf scopes of one applicability dimension.

    ``retired`` is outside the schema projection, as for every retirable
    declaration: retiring is a status change, never a redefinition.
    """

    name: str
    dimension: str
    relation: ScopeRelation
    left: ScopeEndpoint
    right: ScopeEndpoint
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        return {
            "dimension": self.dimension,
            "relation": self.relation,
            "left": self.left.projection(),
            "right": self.right.projection(),
        }


@dataclass(frozen=True)
class CompiledScopeRelation:
    """A relation qualified for one profile: its term, its owning contract and the
    declaration with dimension and sorts qualified. Retirement is projected here
    because it changes the profile's comparison table."""

    term: str
    contract: str
    declaration: ScopeRelationDecl

    def schema_projection(self) -> dict[str, object]:
        return {**self.declaration.schema_projection(), "retired": self.declaration.retired}


def _mapping(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise MalformedContract(f"{where}: expected a mapping")
    return value


def _endpoint(value: object, where: str, sort_reference: Callable[[object, str], str]) -> ScopeEndpoint:
    body = _mapping(value, where)
    if set(body) == {"sort", "term"}:
        return TermScopeEndpoint(sort_reference(body["sort"], f"{where}: sort"), _identifier(body["term"], where))
    if set(body) == {"rule", "classes"}:
        classes = body["classes"]
        if not isinstance(classes, list):
            raise MalformedContract(f"{where}: classes is a list of exactly one class")
        try:
            return RuleScopeEndpoint(body["rule"], tuple(classes))  # type: ignore[arg-type]
        except MalformedContract as refused:
            raise MalformedContract(f"{where}: {refused}") from None
    raise MalformedContract(
        f"{where}: an endpoint is exactly {{sort, term}} or {{rule, classes}}; interval, time-interval and "
        "union endpoints are not admitted"
    )


def parse_scope_relations(
    value: object,
    where: str,
    *,
    relations: tuple[str, ...],
    dimension_reference: Callable[[object, str], str],
    sort_reference: Callable[[object, str], str],
) -> dict[str, ScopeRelationDecl]:
    """Parse a domain contract's optional ``scope_relations`` table; absent is empty.

    ``relations`` is the base contract's closed tag set. The reference callables
    validate local or ``<namespace>/<name>`` references as the domain parser does
    for every other declaration.
    """
    table = _mapping(value, where)
    parsed: dict[str, ScopeRelationDecl] = {}
    for name, body_value in table.items():
        entry_where = f"{where}.{name}"
        if _NAME.fullmatch(name) is None:
            raise MalformedContract(f"{entry_where}: {name!r} is not an identifier")
        body = _mapping(body_value, entry_where)
        unknown = sorted(set(body) - SCOPE_RELATION_FIELDS - _EDITORIAL)
        if unknown:
            raise MalformedContract(f"{entry_where}: unknown field(s) {', '.join(unknown)}; refused, never ignored")
        missing = sorted(SCOPE_RELATION_FIELDS - set(body))
        if missing:
            raise MalformedContract(f"{entry_where}: missing field(s) {', '.join(missing)}")
        relation = body["relation"]
        if not isinstance(relation, str) or relation not in relations:
            raise MalformedContract(
                f"{entry_where}: relation {relation!r} is not one of the base contract's scope relations "
                f"{list(relations)}; `broader` is a comparison result, and subclass, part-of or within edges are "
                "not declared scope relations"
            )
        retired = body.get("retired", False)
        if not isinstance(retired, bool):
            raise MalformedContract(f"{entry_where}: retired is true or false")
        if "description" in body and not isinstance(body["description"], str):
            raise MalformedContract(f"{entry_where}: description is a string")
        left = _endpoint(body["left"], f"{entry_where}: left", sort_reference)
        right = _endpoint(body["right"], f"{entry_where}: right", sort_reference)
        if type(left) is not type(right):
            raise MalformedContract(f"{entry_where}: both endpoints have one form, term or rule")
        parsed[name] = ScopeRelationDecl(
            name=name,
            dimension=dimension_reference(body["dimension"], f"{entry_where}: dimension"),
            relation=relation,  # type: ignore[arg-type]
            left=left,
            right=right,
            retired=retired,
        )
    return parsed
