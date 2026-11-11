"""Quantified operator-scoped restrictions, separate from measurement scopes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from beliefs.claim import Claim, Referent, check_referent
from beliefs.errors import (
    DimensionNotApplicabilitySide,
    MalformedRestriction,
    UnboundReferent,
    UndeclaredDimension,
    UnknownQuantifier,
    WithdrawnFromAuthoring,
)
from beliefs.identity import v1
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import BindingCheckReceipt, ResolutionSnapshot, TermOutcome, _emit_receipt
from beliefs.restriction import (
    Restriction,
    RestrictionMap,
    RuleRestriction,
    TermRestriction,
    UnionRestriction,
    restriction_projection,
    type_restriction_map,
)

__all__ = [
    "Applicability",
    "ScopedRestriction",
    "applicability_from_stored",
    "applicability_projection",
    "build_applicability",
    "checked",
]


@dataclass(frozen=True)
class ScopedRestriction:
    quantifier: str
    restriction: Restriction


@dataclass(frozen=True)
class Applicability:
    values: Mapping[str, ScopedRestriction]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def restrictions(self) -> RestrictionMap:
        return MappingProxyType({dimension: value.restriction for dimension, value in self.values.items()})

    def rule_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    member.rule
                    for value in self.values.values()
                    for member in _members(value.restriction)
                    if isinstance(member, RuleRestriction)
                }
            )
        )


def _members(value: Restriction) -> tuple[Restriction, ...]:
    return value.members if isinstance(value, UnionRestriction) else (value,)


def _referents(profile: ProfileSpec, dimension: str, value: Restriction) -> dict[str, Referent]:
    result: dict[str, Referent] = {}
    for index, member in enumerate(_members(value)):
        label = f"restriction:{dimension}"
        if isinstance(value, UnionRestriction):
            label += f":{index}"
        if isinstance(member, TermRestriction):
            result[label] = Referent(member.sort, member.term)
        elif isinstance(member, RuleRestriction):
            declaration = profile.dimensions[dimension].restriction
            assert declaration is not None
            if declaration.form == "union":
                declaration = declaration.of
            assert declaration is not None and declaration.classes is not None
            for class_index, term in enumerate(member.classes):
                result[f"{label}:{class_index}"] = Referent(declaration.classes, term)
    return result


def checked(
    profile: ProfileSpec, operator: str, values: Mapping[str, ScopedRestriction], *, authoring: bool
) -> Applicability:
    """Validate vocabulary and shape without reading records or resolving membership."""
    term = profile.operator(operator).term
    if not isinstance(values, Mapping):
        raise MalformedRestriction("applicability must be a mapping")
    projected: dict[str, object] = {}
    for dimension, scoped in values.items():
        declaration = profile.dimensions.get(dimension)
        if declaration is None or term not in declaration.applies_to:
            raise UndeclaredDimension(f"{dimension!r} does not apply to {operator!r}")
        if declaration.placement != "applicability":
            raise DimensionNotApplicabilitySide(f"{dimension!r} is not placed applicability")
        if authoring and declaration.retired:
            raise WithdrawnFromAuthoring(f"dimension {dimension!r} is retired")
        if not isinstance(scoped, ScopedRestriction):
            raise MalformedRestriction(f"{dimension!r} requires a ScopedRestriction")
        if scoped.quantifier not in profile.claim_grammar.quantifiers:
            raise UnknownQuantifier(f"unknown quantifier {scoped.quantifier!r} on {dimension!r}")
        value = scoped.restriction
        if isinstance(value, UnionRestriction):
            keys = [v1.encode(restriction_projection(member)) for member in value.members]
            if keys != sorted(set(keys)):
                raise MalformedRestriction("union members must be in canonical order and distinct")
        projected[dimension] = restriction_projection(value)
    typed = type_restriction_map(profile, projected)
    for dimension, restriction in typed.items():
        for label, referent in _referents(profile, dimension, restriction).items():
            check_referent(profile, referent, label, world_kind=None, authoring=authoring)
    return Applicability(
        {dimension: ScopedRestriction(values[dimension].quantifier, value) for dimension, value in typed.items()}
    )


def build_applicability(
    profile: ProfileSpec, claim: Claim, values: Mapping[str, ScopedRestriction], *, snapshot: ResolutionSnapshot
) -> tuple[Applicability, BindingCheckReceipt]:
    value = checked(profile, claim.operator, values, authoring=True)
    outcomes: dict[str, TermOutcome] = {}
    for dimension, restriction in value.restrictions().items():
        for label, referent in _referents(profile, dimension, restriction).items():
            outcome = snapshot.resolve(profile.sorts[referent.sort], referent.term)
            if outcome.refuses:
                raise UnboundReferent(f"{label}: term {referent.term!r} is not a vocabulary member")
            outcomes[label] = outcome
    return value, _emit_receipt(claim_identity(claim), snapshot, outcomes)


def applicability_projection(value: Applicability) -> dict[str, object]:
    return {
        dimension: {"quantifier": scoped.quantifier, "restriction": restriction_projection(scoped.restriction)}
        for dimension, scoped in value.values.items()
    }


def applicability_from_stored(value: object, *, profile: ProfileSpec, operator: str) -> Applicability:
    if not isinstance(value, Mapping):
        raise MalformedRestriction("a stored applicability is a mapping")
    values: dict[str, ScopedRestriction] = {}
    for dimension, body in value.items():
        if (
            not isinstance(dimension, str)
            or not isinstance(body, Mapping)
            or set(body) != {"quantifier", "restriction"}
        ):
            raise MalformedRestriction("an applicability entry has exactly quantifier and restriction")
        typed = type_restriction_map(profile, {dimension: body["restriction"]})
        values[dimension] = ScopedRestriction(body["quantifier"], typed[dimension])
    return checked(profile, operator, values, authoring=False)
