"""The five typed restriction forms and exact, conservative scope comparison."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal
from fractions import Fraction
from functools import cmp_to_key
from types import MappingProxyType
from typing import Generic, Literal, TypeAlias, TypeVar

from beliefs.errors import MalformedRecord, MalformedRestriction
from beliefs.identifiers import canonical
from beliefs.profile import CompiledRestrictionForm, ProfileSpec
from beliefs.reservation import OPEN, IntervalUnit

__all__ = [
    "CoScope",
    "IntervalRestriction",
    "Restriction",
    "RestrictionMap",
    "RuleRestriction",
    "TermRestriction",
    "TimeIntervalRestriction",
    "UnionRestriction",
    "check_held_rule_scope",
    "co_scope",
    "co_scope_by_dimension",
    "decimal_from_projection",
    "decimal_projection",
    "restriction_from_projection",
    "restriction_projection",
    "type_restriction_map",
]

_TERM = re.compile(r"[a-z][a-z0-9-]*/[a-z][a-z0-9-]*")
_RULE = re.compile(r"classification-rule:[0-9a-f]{64}")
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_MAX_DECIMAL_DIGITS = 4096
_MAX_DECIMAL_EXPONENT = 4096
_MAX_DECIMAL_PLACES = _MAX_DECIMAL_DIGITS + _MAX_DECIMAL_EXPONENT
_MAX_BOUND_COMPONENT = 10**_MAX_DECIMAL_PLACES


def _text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise MalformedRestriction(f"{where}: expected a non-empty string")
    return value


def _term(value: object, where: str) -> str:
    text = _text(value, where)
    if _TERM.fullmatch(text) is None:
        raise MalformedRestriction(f"{where}: expected <namespace>/<name>")
    return text


def _decimal_places(value: Fraction) -> int:
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
        if twos > _MAX_DECIMAL_PLACES:
            raise MalformedRestriction("interval bound exceeds the representable decimal precision")
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
        if fives > _MAX_DECIMAL_PLACES:
            raise MalformedRestriction("interval bound exceeds the representable decimal precision")
    if denominator != 1:
        raise MalformedRestriction("an authored interval bound must have an exact finite decimal projection")
    return max(twos, fives)


@dataclass(frozen=True)
class TermRestriction:
    sort: str
    term: str

    def __post_init__(self) -> None:
        _term(self.sort, "restriction sort")
        _text(self.term, "restriction term")


@dataclass(frozen=True)
class IntervalRestriction:
    unit: str
    low: Fraction | None
    high: Fraction | None
    low_closed: bool
    high_closed: bool
    convention: str | None = None

    def __post_init__(self) -> None:
        _term(self.unit, "restriction unit")
        if self.convention is not None:
            text = _text(self.convention, "restriction convention")
            if re.fullmatch(r"(?:[a-z][a-z0-9-]*/)?[a-z][a-z0-9-]*", text) is None:
                raise MalformedRestriction("a convention must be a local or qualified duration-convention term")
        if type(self.low_closed) is not bool or type(self.high_closed) is not bool:
            raise MalformedRestriction("interval closure flags must be booleans")
        for bound in (self.low, self.high):
            if bound is not None:
                if not isinstance(bound, Fraction):
                    raise MalformedRestriction("interval bounds must be Fractions")
                _decimal_text(bound)
        if self.low is None and self.high is None:
            raise MalformedRestriction("an interval needs at least one bound")
        if (
            self.low is not None
            and self.high is not None
            and (self.low > self.high or (self.low == self.high and not (self.low_closed and self.high_closed)))
        ):
            raise MalformedRestriction("an interval must be nonempty")


@dataclass(frozen=True)
class TimeIntervalRestriction:
    start: str
    end: str

    def __post_init__(self) -> None:
        try:
            IntervalUnit(self.start, self.end)
        except MalformedRecord as exc:
            raise MalformedRestriction(str(exc)) from exc


@dataclass(frozen=True)
class RuleRestriction:
    rule: str
    classes: tuple[str, ...]

    def __post_init__(self) -> None:
        if _RULE.fullmatch(_text(self.rule, "restriction rule")) is None:
            raise MalformedRestriction("a rule restriction needs a classification-rule id")
        if not isinstance(self.classes, tuple) or not self.classes:
            raise MalformedRestriction("rule classes must be a non-empty tuple")
        for term in self.classes:
            _text(term, "restriction class")
        normalized = tuple(canonical(term) for term in self.classes)
        if normalized != tuple(sorted(set(normalized))):
            raise MalformedRestriction("rule classes must be sorted and distinct")


@dataclass(frozen=True)
class UnionRestriction:
    members: tuple[Restriction, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.members, tuple) or len(self.members) < 2:
            raise MalformedRestriction("a union needs at least two members")
        if type(self.members[0]) not in (
            TermRestriction,
            IntervalRestriction,
            TimeIntervalRestriction,
            RuleRestriction,
        ):
            raise MalformedRestriction("a union member must be a non-union restriction")
        if any(type(member) is not type(self.members[0]) for member in self.members):
            raise MalformedRestriction("union members must have one non-union form")


Restriction: TypeAlias = (
    TermRestriction | IntervalRestriction | TimeIntervalRestriction | RuleRestriction | UnionRestriction
)
RestrictionMap: TypeAlias = Mapping[str, Restriction]
CoScope: TypeAlias = Literal["equal", "narrower", "broader", "overlapping", "disjoint", "unknown"]


def _within_decimal_budget(text: str) -> bool:
    mantissa, _, exponent = text.lower().partition("e")
    exponent_digits = exponent.lstrip("+-").lstrip("0") or "0"
    limit = str(_MAX_DECIMAL_EXPONENT)
    return len(mantissa.lstrip("+-").replace(".", "")) <= _MAX_DECIMAL_DIGITS and (
        len(exponent_digits) < len(limit) or (len(exponent_digits) == len(limit) and exponent_digits <= limit)
    )


def _decimal_text(value: Fraction) -> str:
    # Every admitted spelling bounds both components and decimal places by these limits.
    if abs(value.numerator) >= _MAX_BOUND_COMPONENT or value.denominator > _MAX_BOUND_COMPONENT:
        raise MalformedRestriction("interval bound has no projection within the decimal resource budget")
    places = _decimal_places(value)
    scaled = abs(value.numerator) * (10**places // value.denominator)
    digits = str(Decimal(scaled))
    padded = digits.zfill(places + 1)
    fixed = padded if not places else padded[:-places] + "." + padded[-places:]
    sign = "-" if value < 0 else ""
    if _within_decimal_budget(fixed):
        return sign + fixed

    significant = digits.rstrip("0")
    exponent = len(digits) - len(significant) - places
    wire_exponent = max(-_MAX_DECIMAL_EXPONENT, min(exponent, _MAX_DECIMAL_EXPONENT))
    point = len(significant) + exponent - wire_exponent
    if point <= 0:
        coefficient = "." + "0" * -point + significant
    elif point >= len(significant):
        coefficient = significant + "0" * (point - len(significant))
    else:
        coefficient = significant[:point] + "." + significant[point:]
    text = f"{sign}{coefficient}e{wire_exponent}"
    if not _within_decimal_budget(text):
        raise MalformedRestriction("interval bound has no projection within the decimal resource budget")
    return text


def restriction_projection(value: Restriction) -> dict[str, object] | list[dict[str, object]]:
    if isinstance(value, TermRestriction):
        return {"sort": value.sort, "term": value.term}
    if isinstance(value, IntervalRestriction):
        projection: dict[str, object] = {
            "unit": value.unit,
            "low_closed": value.low_closed,
            "high_closed": value.high_closed,
        }
        if value.low is not None:
            projection["low"] = _decimal_text(value.low)
        if value.high is not None:
            projection["high"] = _decimal_text(value.high)
        if value.convention is not None:
            projection["convention"] = value.convention
        return projection
    if isinstance(value, TimeIntervalRestriction):
        return {"start": value.start, "end": value.end}
    if isinstance(value, RuleRestriction):
        return {"rule": value.rule, "classes": list(value.classes)}
    return [_leaf_projection(member) for member in value.members]


def _leaf_projection(value: Restriction) -> dict[str, object]:
    projected = restriction_projection(value)
    assert isinstance(projected, dict)  # UnionRestriction excludes nested unions.
    return projected


def _bound(value: object) -> Fraction:
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        raise MalformedRestriction("interval bounds must be decimal strings")
    # Match the contract coefficient budget before allocating a rational.
    if not _within_decimal_budget(value):
        raise MalformedRestriction("interval bound exceeds the decimal digit or exponent budget (4096)")
    try:
        return Fraction(Decimal(value))
    except (ArithmeticError, ValueError) as exc:
        raise MalformedRestriction("interval bound cannot be represented exactly") from exc


def decimal_projection(value: Fraction) -> str:
    """An exact finite decimal spelling within the shared coefficient budget."""
    if not isinstance(value, Fraction):
        raise MalformedRestriction("an exact decimal value must be a Fraction")
    return _decimal_text(value)


def decimal_from_projection(value: object) -> Fraction:
    """Read a decimal string under the same budget as its exact projection."""
    return _bound(value)


def _form(value: Mapping[str, object]) -> str:
    keys = set(value)
    if "sort" in keys:
        return "term"
    if "unit" in keys:
        return "interval"
    if "start" in keys:
        return "time-interval"
    if "rule" in keys:
        return "rule"
    raise MalformedRestriction("unrecognized restriction shape")


def restriction_from_projection(value: object, *, form: str) -> Restriction:
    if form == "union":
        if not isinstance(value, list) or not value:
            raise MalformedRestriction("a union projection must be a list of restrictions")
        members = []
        for member in value:
            if not isinstance(member, Mapping) or not all(isinstance(key, str) for key in member):
                raise MalformedRestriction("union members must be restriction objects")
            members.append(restriction_from_projection(member, form=_form(member)))
        return UnionRestriction(tuple(members))
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise MalformedRestriction("a restriction projection must be an object")
    required = {
        "term": {"sort", "term"},
        "interval": {"unit", "low_closed", "high_closed"},
        "time-interval": {"start", "end"},
        "rule": {"rule", "classes"},
    }
    if form not in required:
        raise MalformedRestriction(f"unsupported restriction form {form!r}")
    optional = {"low", "high", "convention"} if form == "interval" else set()
    if not required[form] <= value.keys() or set(value) - required[form] - optional:
        raise MalformedRestriction(f"{form}: unexpected or missing restriction fields")
    if form == "term":
        return TermRestriction(value["sort"], value["term"])
    if form == "interval":
        return IntervalRestriction(
            value["unit"],
            _bound(value["low"]) if "low" in value else None,
            _bound(value["high"]) if "high" in value else None,
            value["low_closed"],
            value["high_closed"],
            convention=_text(value["convention"], "restriction convention") if "convention" in value else None,
        )
    if form == "time-interval":
        return TimeIntervalRestriction(value["start"], value["end"])
    if not isinstance(value["classes"], list):
        raise MalformedRestriction("rule classes must be a list")
    return RuleRestriction(value["rule"], tuple(value["classes"]))


def _check_terms(profile: ProfileSpec, sort: str, terms: tuple[str, ...]) -> None:
    identifier_class = profile.sorts[sort].identifier_class
    if identifier_class is not None and any(not identifier_class.matches(term) for term in terms):
        raise MalformedRestriction(f"a restriction term is outside the identifier class of {sort!r}")


def _typed(profile: ProfileSpec, value: Restriction, decl: CompiledRestrictionForm, namespace: str) -> Restriction:
    if isinstance(value, UnionRestriction) and decl.form == "union":
        assert decl.of is not None
        return UnionRestriction(tuple(_typed(profile, member, decl.of, namespace) for member in value.members))
    if isinstance(value, TermRestriction) and decl.form == "term":
        if value.sort != decl.sort:
            raise MalformedRestriction(f"expected restriction sort {decl.sort!r}")
        _check_terms(profile, value.sort, (value.term,))
        return value
    if isinstance(value, IntervalRestriction) and decl.form == "interval":
        unit = profile.units.get(value.unit)
        if unit is None or unit.quantity_kind != decl.quantity_kind:
            raise MalformedRestriction(f"restriction unit must have quantity kind {decl.quantity_kind!r}")
        if value.convention is not None:
            term = value.convention if "/" in value.convention else f"{namespace}/{value.convention}"
            convention = profile.duration_conventions.get(term)
            if convention is None or not unit.calendar:
                raise MalformedRestriction("a supplied convention must be declared and restrict a calendar unit")
            conversion = profile.conversions[convention.conversion]
            if value.unit not in (conversion.from_unit, conversion.to_unit):
                raise MalformedRestriction("the convention conversion does not involve this calendar unit")
            return replace(value, convention=term)
        return value
    if isinstance(value, RuleRestriction) and decl.form == "rule":
        assert decl.classes is not None
        _check_terms(profile, decl.classes, value.classes)
        return value
    if isinstance(value, TimeIntervalRestriction) and decl.form == "time-interval":
        return value
    raise MalformedRestriction(f"expected restriction form {decl.form!r}")


def type_restriction_map(profile: ProfileSpec, raw: Mapping[str, object]) -> RestrictionMap:
    typed: dict[str, Restriction] = {}
    for key, projected in raw.items():
        dimension = profile.dimensions.get(key)
        if dimension is None or dimension.placement != "applicability" or dimension.restriction is None:
            raise MalformedRestriction(f"{key!r} is not a declared applicability-side typed dimension")
        value = restriction_from_projection(projected, form=dimension.restriction.form)
        typed[key] = _typed(profile, value, dimension.restriction, dimension.contract)
    return MappingProxyType(typed)


def check_held_rule_scope(profile: ProfileSpec, scope: RestrictionMap, *, classes_of: Callable[[str], str]) -> None:
    """Check rule restrictions using the classes sort of each strictly read held rule."""
    for term, restriction in scope.items():
        union = isinstance(restriction, UnionRestriction)
        members = restriction.members if union else (restriction,)
        rules = [member for member in members if isinstance(member, RuleRestriction)]
        if not rules:
            continue
        dimension = profile.dimensions.get(term)
        declaration = (
            dimension.restriction if dimension is not None and dimension.placement == "applicability" else None
        )
        if union:
            declaration = declaration.of if declaration is not None and declaration.form == "union" else None
        if declaration is None or declaration.form != "rule" or declaration.classes is None:
            raise MalformedRestriction(f"{term!r} does not declare this rule restriction form")
        for rule in rules:
            actual = classes_of(rule.rule)
            if actual != declaration.classes:
                raise MalformedRestriction(
                    f"{term!r}: rule {rule.rule!r} has classes sort {actual!r}, expected {declaration.classes!r}"
                )
            _check_terms(profile, actual, rule.classes)


_Bound = TypeVar("_Bound", Fraction, str)


@dataclass(frozen=True)
class _Span(Generic[_Bound]):
    low: _Bound | None
    high: _Bound | None
    low_closed: bool
    high_closed: bool


def _low_compare(a: _Span[_Bound], b: _Span[_Bound]) -> int:
    if a.low is None:
        return 0 if b.low is None else -1
    if b.low is None:
        return 1
    return (a.low > b.low) - (a.low < b.low) or (b.low_closed - a.low_closed)


def _before(a: _Span[_Bound], b: _Span[_Bound], *, gap: bool = False) -> bool:
    if a.high is None or b.low is None:
        return False
    at_boundary = not (a.high_closed or b.low_closed) if gap else not (a.high_closed and b.low_closed)
    return a.high < b.low or (a.high == b.low and at_boundary)


def _merge(spans: list[_Span[_Bound]]) -> list[_Span[_Bound]]:
    merged: list[_Span[_Bound]] = []
    for span in sorted(spans, key=cmp_to_key(_low_compare)):
        if not merged or _before(merged[-1], span, gap=True):
            merged.append(span)
            continue
        prior = merged[-1]
        if prior.high is None or (span.high is not None and prior.high > span.high):
            continue
        high_closed = prior.high_closed or span.high_closed if prior.high == span.high else span.high_closed
        merged[-1] = _Span(prior.low, span.high, prior.low_closed, high_closed)
    return merged


def _contains(a: _Span[_Bound], b: _Span[_Bound]) -> bool:
    lower = a.low is None or (
        b.low is not None and (a.low < b.low or (a.low == b.low and (a.low_closed or not b.low_closed)))
    )
    upper = a.high is None or (
        b.high is not None and (a.high > b.high or (a.high == b.high and (a.high_closed or not b.high_closed)))
    )
    return lower and upper


def _span_scope(a: list[_Span[_Bound]], b: list[_Span[_Bound]]) -> CoScope:
    left, right = _merge(a), _merge(b)
    a_within = all(any(_contains(y, x) for y in right) for x in left)
    b_within = all(any(_contains(x, y) for x in left) for y in right)
    if a_within and b_within:
        return "equal"
    if a_within:
        return "narrower"
    if b_within:
        return "broader"
    if all(_before(x, y) or _before(y, x) for x in left for y in right):
        return "disjoint"
    return "overlapping"


def _calendar_span(value: IntervalRestriction, profile: ProfileSpec) -> tuple[str, _Span[Fraction]] | None:
    unit = profile.units.get(value.unit)
    if unit is None:
        return None
    span = _Span(value.low, value.high, value.low_closed, value.high_closed)
    if not unit.calendar:
        return (value.unit, span) if value.convention is None else None
    convention = profile.duration_conventions.get(value.convention) if value.convention is not None else None
    if convention is None:
        return None
    conversion = profile.conversions[convention.conversion]
    if conversion.from_unit == value.unit:
        target, factor = conversion.to_unit, conversion.factor
    elif conversion.to_unit == value.unit:
        target, factor = conversion.from_unit, 1 / conversion.factor
    else:
        return None
    return target, _map_span(span, factor, Fraction(0))


def _map_span(span: _Span[Fraction], factor: Fraction, offset: Fraction) -> _Span[Fraction]:
    return _Span(
        None if span.low is None else factor * span.low + offset,
        None if span.high is None else factor * span.high + offset,
        span.low_closed,
        span.high_closed,
    )


def _interval_span(span: _Span[Fraction], source: str, target: str, profile: ProfileSpec) -> _Span[Fraction] | None:
    if source == target:
        return span
    if profile.units[source].quantity_kind != profile.units[target].quantity_kind:
        return None
    conversion = profile.conversion_between(source, target)
    if conversion is None:
        return None
    factor, offset = conversion.factor, conversion.offset or Fraction(0)
    if conversion.from_unit != source:
        factor, offset = 1 / factor, -offset / factor
    return _map_span(span, factor, offset)


_SetItem = TypeVar("_SetItem")


def _subset_scope(a: set[_SetItem], b: set[_SetItem]) -> CoScope:
    if a == b:
        return "equal"
    if a < b:
        return "narrower"
    if a > b:
        return "broader"
    return "unknown"


def _compare(a: Restriction, b: Restriction, profile: ProfileSpec) -> CoScope:
    left = a.members if isinstance(a, UnionRestriction) else (a,)
    right = b.members if isinstance(b, UnionRestriction) else (b,)
    members = (*left, *right)
    intervals = [value for value in members if isinstance(value, IntervalRestriction)]
    if len(intervals) == len(members):
        normalized = [_calendar_span(value, profile) for value in intervals]
        if any(value is None for value in normalized):
            return "unknown"
        resolved = [value for value in normalized if value is not None]
        # A union's normalization unit must not depend on argument or member order.
        unit = min(unit for unit, _ in resolved) if len(members) > 2 else resolved[0][0]
        spans = [_interval_span(span, source, unit, profile) for source, span in resolved]
        if any(span is None for span in spans):
            return "unknown"
        known = [span for span in spans if span is not None]
        return _span_scope(known[: len(left)], known[len(left) :])
    times = [value for value in members if isinstance(value, TimeIntervalRestriction)]
    if len(times) == len(members):
        time_spans = [
            _Span(None if value.start == OPEN else value.start, None if value.end == OPEN else value.end, True, False)
            for value in times
        ]
        return _span_scope(time_spans[: len(left)], time_spans[len(left) :])
    terms = [value for value in members if isinstance(value, TermRestriction)]
    if len(terms) == len(members):
        return _subset_scope(
            {(canonical(value.sort), canonical(value.term)) for value in terms[: len(left)]},
            {(canonical(value.sort), canonical(value.term)) for value in terms[len(left) :]},
        )
    rules = [value for value in members if isinstance(value, RuleRestriction)]
    if len(rules) == len(members) and len({value.rule for value in rules}) == 1:
        return _subset_scope(
            {canonical(term) for value in rules[: len(left)] for term in value.classes},
            {canonical(term) for value in rules[len(left) :] for term in value.classes},
        )
    return "unknown"


def co_scope_by_dimension(a: RestrictionMap, b: RestrictionMap, profile: ProfileSpec) -> Mapping[str, CoScope]:
    return MappingProxyType(
        {
            key: _compare(a[key], b[key], profile) if key in a and key in b else "narrower" if key in a else "broader"
            for key in sorted(a.keys() | b.keys())
        }
    )


def co_scope(a: RestrictionMap, b: RestrictionMap, profile: ProfileSpec) -> CoScope:
    verdicts = set(co_scope_by_dimension(a, b, profile).values())
    for verdict in ("disjoint", "unknown"):
        if verdict in verdicts:
            return verdict
    if {"narrower", "broader"} <= verdicts or "overlapping" in verdicts:
        return "overlapping"
    if "narrower" in verdicts:
        return "narrower"
    if "broader" in verdicts:
        return "broader"
    return "equal"
