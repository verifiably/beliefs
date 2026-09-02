from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from beliefs import stored
from beliefs.identifiers import not_an_identifier
from beliefs.identity import v1

VIEW_QUERY_VERSION = "science.view-query.v1"


def _world_address(value: object, where: str) -> str:
    if type(value) is not str:
        raise ValueError(f"view query {where} must be a world address string")
    kind, separator, local = value.partition(":")
    if (
        separator != ":"
        or kind not in stored.WORLD_KINDS
        or not local
        or value.startswith("coord:")
    ):
        raise ValueError(f"view query {where} must be a world-tier address")
    return value


def _distinct_strings(value: object, where: str) -> tuple[str, ...]:
    if (
        type(value) is not list
        or not value
        or any(type(member) is not str or not member for member in value)
    ):
        raise ValueError(f"view query {where} must be a non-empty string list")
    members = tuple(value)
    if len(set(members)) != len(members):
        raise ValueError(f"view query {where} must not repeat a member")
    return tuple(sorted(members))


@dataclass(frozen=True)
class Kinds:
    values: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {"kinds": list(self.values)}


@dataclass(frozen=True)
class ReferencesTerm:
    value: str

    def projection(self) -> dict[str, object]:
        return {"references-term": self.value}


@dataclass(frozen=True)
class Closure:
    anchor: str
    predicates: tuple[str, ...]
    direction: Literal["out", "in", "both"]

    def projection(self) -> dict[str, object]:
        return {
            "closure": {
                "anchor": self.anchor,
                "predicates": list(self.predicates),
                "direction": self.direction,
            }
        }


@dataclass(frozen=True)
class Addresses:
    values: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {"addresses": list(self.values)}


Predicate: TypeAlias = Kinds | ReferencesTerm | Closure | Addresses


@dataclass(frozen=True)
class Clause:
    predicates: tuple[Predicate, ...]

    def projection(self) -> dict[str, object]:
        return {"all": [predicate.projection() for predicate in self.predicates]}


@dataclass(frozen=True)
class ViewQuery:
    clauses: tuple[Clause, ...]

    def projection(self) -> dict[str, object]:
        return {"version": VIEW_QUERY_VERSION, "clauses": [clause.projection() for clause in self.clauses]}

    def world_kinds(self) -> frozenset[str]:
        return frozenset(
            kind
            for clause in self.clauses
            for predicate in clause.predicates
            if isinstance(predicate, Kinds)
            for kind in predicate.values
        )

    def relations(self) -> frozenset[str]:
        return frozenset(
            relation
            for clause in self.clauses
            for predicate in clause.predicates
            if isinstance(predicate, Closure)
            for relation in predicate.predicates
        )

    def addresses(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    address
                    for clause in self.clauses
                    for predicate in clause.predicates
                    for address in (
                        (predicate.anchor,)
                        if isinstance(predicate, Closure)
                        else predicate.values
                        if isinstance(predicate, Addresses)
                        else ()
                    )
                }
            )
        )


def _predicate(value: object, where: str) -> Predicate:
    if type(value) is not dict or len(value) != 1:
        raise ValueError(f"view query {where} must have exactly one predicate member")
    key, member = next(iter(value.items()))
    if key == "kinds":
        kinds = _distinct_strings(member, f"{where}.kinds")
        if any(kind not in stored.WORLD_KINDS for kind in kinds):
            raise ValueError(f"view query {where}.kinds must name world kinds")
        return Kinds(kinds)
    if key == "references-term":
        if (problem := not_an_identifier(member)) is not None:
            raise ValueError(f"view query {where}.references-term: {problem}")
        assert isinstance(member, str)
        return ReferencesTerm(member)
    if key == "addresses":
        addresses = _distinct_strings(member, f"{where}.addresses")
        return Addresses(tuple(_world_address(address, f"{where}.addresses") for address in addresses))
    if key != "closure" or type(member) is not dict or set(member) != {
        "anchor",
        "predicates",
        "direction",
    }:
        raise ValueError(f"view query {where} is not a recognized v1 predicate")
    anchor = _world_address(member["anchor"], f"{where}.closure.anchor")
    predicates = _distinct_strings(member["predicates"], f"{where}.closure.predicates")
    direction = member["direction"]
    if direction not in ("out", "in", "both"):
        raise ValueError(f"view query {where}.closure.direction must be out, in, or both")
    return Closure(anchor, predicates, direction)


def parse_view_query(value: object) -> ViewQuery:
    if type(value) is not dict or set(value) != {"version", "clauses"}:
        raise ValueError("view query must have exactly version and clauses")
    if value["version"] != VIEW_QUERY_VERSION:
        raise ValueError(f"view query version must be {VIEW_QUERY_VERSION}")
    clauses = value["clauses"]
    if type(clauses) is not list:
        raise ValueError("view query clauses must be a list")
    parsed: list[Clause] = []
    for clause_index, clause in enumerate(clauses):
        if type(clause) is not dict or set(clause) != {"all"}:
            raise ValueError(f"view query clauses[{clause_index}] must have exactly all")
        predicates = clause["all"]
        if type(predicates) is not list or not predicates:
            raise ValueError(f"view query clauses[{clause_index}].all must be non-empty")
        members = tuple(
            sorted(
                (
                    _predicate(predicate, f"clauses[{clause_index}].all[{predicate_index}]")
                    for predicate_index, predicate in enumerate(predicates)
                ),
                key=lambda predicate: v1.encode(predicate.projection()),
            )
        )
        parsed.append(Clause(members))
    return ViewQuery(tuple(sorted(parsed, key=lambda clause: v1.encode(clause.projection()))))
