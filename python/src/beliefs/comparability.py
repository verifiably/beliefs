"""Declaration-driven A-to-B coordinate maps and qualitative certificates."""

from __future__ import annotations

import decimal
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from types import MappingProxyType
from typing import Literal, TypeAlias, get_args

from beliefs.assumptions import AssumptionInstance, check_instance
from beliefs.dependencies import HeldRecords, Record, read_record
from beliefs.eligibility import ClosureEligibility, Ineligible
from beliefs.errors import AmbiguousCrosswalk, DependencyNotHeld, MalformedContract, MalformedRecord, ProfileError
from beliefs.measurement import Coordinates
from beliefs.procedure import Procedure, SameAs
from beliefs.profile import CompiledConversion, CompiledTransformation, ProfileSpec
from beliefs.proxy_model import ProxyModel
from beliefs.restriction import decimal_projection

__all__ = [
    "Arity",
    "Binding",
    "ComparabilitySnapshot",
    "ComposedMap",
    "Convertible",
    "Domain",
    "Exchange",
    "Flip",
    "Form",
    "FunctionalProperties",
    "Increment",
    "LogShift",
    "MapClass",
    "NeedsOperands",
    "NotConvertible",
    "Null",
    "Output",
    "OutputTyping",
    "ParameterTyping",
    "ParameterTypingName",
    "RawMap",
    "Reciprocal",
    "ResponseReversal",
    "ResponseTransformation",
    "Reversal",
    "Scale",
    "Shift",
    "Step",
    "Ties",
    "Transcendental",
    "UncertaintyDisposition",
    "UncertaintyPropagation",
    "Unknown",
    "apply_covariance",
    "apply_estimate",
    "apply_exact",
    "apply_interval",
    "apply_standard_error",
    "compare_mapped",
    "convert",
]

CONTEXT = decimal.Context(prec=34)
Form = Literal["contrast", "quantity", "law-parameters", "event-locked", "association", "enrichment"]
Arity = Literal["one", "two", "k", "n", "not-applicable"]
ResponseTransformation = Literal[
    "invariant-strictly-increasing",
    "equivariant-positive-affine",
    "equivariant-affine",
    "invariant-positive-scaling",
    "fixed",
    "none",
    "by-parameters",
]
Reversal = Literal["invariant", "complement", "negate", "reciprocal", "undefined", "not-applicable"]
ResponseReversal = Literal["invariant", "complement", "negate", "undefined", "not-applicable"]
Exchange = Literal["symmetric", "directed", "not-applicable"]
Ties = Literal["undefined", "midrank", "ignored", "not-applicable"]
Output = Literal["response-difference", "response-level", "response-log-level", "dimensionless", "declared"]
ParameterTypingName = Literal[
    "independent", "response-level", "response-difference", "response-log-level", "dimensionless"
]
Domain = Literal["real", "nonnegative", "positive", "unit-interval", "signed-unit-interval", "not-applicable"]
Null = Literal["zero", "one", "half", "none"]
Increment = Literal["linear", "none", "not-applicable"]
UncertaintyPropagation = Literal["exact", "recompute", "none"]
Binding = Literal["certified", "independent"]
MapClass = Literal["identity", "affine", "strictly-increasing", "strictly-decreasing"]
UncertaintyDisposition = Literal["exact", "needs-operands", "absent", "not-carried: crosswalk"]


def _member(value: str, vocabulary: object, name: str) -> None:
    if value not in get_args(vocabulary):
        raise MalformedContract(f"unsupported {name}: {value!r}")


@dataclass(frozen=True)
class ParameterTyping:
    typing: ParameterTypingName
    domain: Domain

    def __post_init__(self) -> None:
        _member(self.typing, ParameterTypingName, "parameter typing")
        _member(self.domain, Domain, "parameter domain")


@dataclass(frozen=True)
class FunctionalProperties:
    form: Form
    arity: Arity
    response_transformation: ResponseTransformation
    reversal: Reversal
    response_reversal: ResponseReversal
    exchange: Exchange
    ties: Ties
    output: Output
    domain: Domain
    null: Null
    increment: Increment
    uncertainty: UncertaintyPropagation
    parameters: Mapping[str, ParameterTyping] | None = None

    def __post_init__(self) -> None:
        for name, vocabulary in (
            ("form", Form),
            ("arity", Arity),
            ("response_transformation", ResponseTransformation),
            ("reversal", Reversal),
            ("response_reversal", ResponseReversal),
            ("exchange", Exchange),
            ("ties", Ties),
            ("output", Output),
            ("domain", Domain),
            ("null", Null),
            ("increment", Increment),
            ("uncertainty", UncertaintyPropagation),
        ):
            _member(getattr(self, name), vocabulary, name)
        declared = self.output == "declared"
        if declared != (self.response_transformation == "by-parameters") or declared != (self.parameters is not None):
            raise MalformedContract("declared output, by-parameters certificate and parameters are required together")
        if self.parameters is not None:
            if not self.parameters or any(
                not isinstance(name, str) or not name or not isinstance(value, ParameterTyping)
                for name, value in self.parameters.items()
            ):
                raise MalformedContract("parameters require named ParameterTyping values")
            object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))


@dataclass(frozen=True)
class OutputTyping:
    typing: ParameterTypingName
    domain: Domain

    def __post_init__(self) -> None:
        _member(self.typing, ParameterTypingName, "output typing")
        _member(self.domain, Domain, "output domain")


@dataclass
class ComparabilitySnapshot:
    profile: ProfileSpec
    records: HeldRecords
    eligibility: Callable[[str], ClosureEligibility]
    reads: tuple[str, ...] = field(default=(), init=False)

    def _observe(self, ids: tuple[str, ...]) -> None:
        self.reads = tuple(dict.fromkeys((*self.reads, *ids)))

    def read(self, id: str) -> Record:
        self._observe((id,))
        return read_record(self.records, id)

    def _eligibility(self, ids: tuple[str, ...]) -> NotConvertible | None:
        refused: list[str] = []
        for id in dict.fromkeys(ids):
            result = self.eligibility(id)
            self._observe(result.reads)
            verdict = result.verdicts[id]
            if isinstance(verdict, Ineligible):
                refused.extend((id, *verdict.concerns))
                if verdict.reason.startswith("dependency-ineligible: "):
                    refused.append(verdict.reason.removeprefix("dependency-ineligible: "))
                elif verdict.reason.startswith("basis-ineligible: "):
                    refused.append(verdict.reason.removeprefix("basis-ineligible: "))
        return NotConvertible("dependency ineligible", tuple(dict.fromkeys(refused))) if refused else None


@dataclass(frozen=True)
class RawMap:
    kind: Literal["identity", "multiplicative", "affine"]
    factor: Fraction
    offset: Fraction
    exact: bool
    error: Fraction | None
    crosswalk: str | None


@dataclass(frozen=True)
class ComposedMap:
    cls: MapClass
    scale: Fraction | Decimal | None
    offset: Fraction | Decimal | None
    decreasing: bool


@dataclass(frozen=True)
class Scale:
    factor: Fraction | Decimal


@dataclass(frozen=True)
class Shift:
    offset: Fraction | Decimal


@dataclass(frozen=True)
class LogShift:
    ln_c: Decimal


@dataclass(frozen=True)
class Flip:
    action: Literal["complement", "negate"]


@dataclass(frozen=True)
class Reciprocal:
    pass


Step: TypeAlias = Scale | Shift | LogShift | Flip | Reciprocal


@dataclass(frozen=True)
class _NeedsOperands:
    pass


@dataclass(frozen=True)
class _Transcendental:
    pass


NeedsOperands = _NeedsOperands()
Transcendental = _Transcendental()


def _render(value: Fraction) -> Decimal:
    return CONTEXT.divide(Decimal(value.numerator), Decimal(value.denominator))


def apply_estimate(steps: tuple[Step, ...], value: Decimal) -> Decimal | _NeedsOperands:
    """Render an estimate under Context34, without changing the caller's context."""
    for step in steps:
        if isinstance(step, Scale):
            value = _render(Fraction(value) * Fraction(step.factor))
        elif isinstance(step, Shift):
            value = _render(Fraction(value) + Fraction(step.offset))
        elif isinstance(step, LogShift):
            value = CONTEXT.add(value, step.ln_c)
        elif isinstance(step, Flip):
            value = CONTEXT.subtract(Decimal(1), value) if step.action == "complement" else CONTEXT.minus(value)
        else:
            assert isinstance(step, Reciprocal)
            if value <= 0:
                return NeedsOperands
            value = CONTEXT.divide(Decimal(1), value)
    return value


def apply_interval(steps: tuple[Step, ...], low: Decimal, high: Decimal) -> tuple[Decimal, Decimal] | _NeedsOperands:
    """Map endpoints in order, checking each reciprocal's positive domain."""
    for step in steps:
        if isinstance(step, Reciprocal) and low <= 0:
            return NeedsOperands
        a, b = apply_estimate((step,), low), apply_estimate((step,), high)
        if isinstance(a, _NeedsOperands) or isinstance(b, _NeedsOperands):
            return NeedsOperands
        decreasing = isinstance(step, (Flip, Reciprocal)) or isinstance(step, Scale) and step.factor < 0
        low, high = (b, a) if decreasing else (a, b)
    return low, high


def _estimate_scale(steps: tuple[Step, ...]) -> Fraction | _NeedsOperands:
    scale = Fraction(1)
    for step in steps:
        if isinstance(step, Reciprocal):
            return NeedsOperands
        if isinstance(step, Scale):
            scale *= Fraction(step.factor)
        elif isinstance(step, Flip):
            scale = -scale
    return scale


def apply_standard_error(steps: tuple[Step, ...], se: Decimal) -> Decimal | _NeedsOperands:
    scale = _estimate_scale(steps)
    return NeedsOperands if isinstance(scale, _NeedsOperands) else _render(Fraction(se) * abs(scale))


def apply_covariance(
    parameter_steps: Mapping[str, tuple[Step, ...]], order: tuple[str, ...], matrix: tuple[Decimal, ...]
) -> tuple[Decimal, ...] | _NeedsOperands:
    if len(matrix) != len(order) * len(order):
        raise ValueError("covariance matrix must be square in the declared parameter order")
    scales: list[Fraction] = []
    for parameter in order:
        scale = _estimate_scale(parameter_steps[parameter])
        if isinstance(scale, _NeedsOperands):
            return NeedsOperands
        scales.append(scale)
    return tuple(
        _render(Fraction(value) * scales[index // len(order)] * scales[index % len(order)])
        for index, value in enumerate(matrix)
    )


def apply_exact(steps: tuple[Step, ...], value: Fraction) -> Fraction | _Transcendental | _NeedsOperands:
    """Apply rational steps only; evaluated Decimal coefficients prove no equality."""
    if any(
        isinstance(step, LogShift)
        or isinstance(step, Scale)
        and isinstance(step.factor, Decimal)
        or isinstance(step, Shift)
        and isinstance(step.offset, Decimal)
        for step in steps
    ):
        return Transcendental
    for step in steps:
        if isinstance(step, Scale):
            assert isinstance(step.factor, Fraction)
            value *= step.factor
        elif isinstance(step, Shift):
            assert isinstance(step.offset, Fraction)
            value += step.offset
        elif isinstance(step, Flip):
            value = 1 - value if step.action == "complement" else -value
        elif isinstance(step, Reciprocal):
            if value <= 0:
                return NeedsOperands
            value = 1 / value
    return value


def compare_mapped(
    steps: tuple[Step, ...], value: Fraction, target: Fraction
) -> Literal["equal", "unequal", "undecidable"]:
    mapped = apply_exact(steps, value)
    if not isinstance(mapped, Fraction):
        return "undecidable"
    return "equal" if mapped == target else "unequal"


@dataclass(frozen=True)
class Convertible:
    steps: tuple[Step, ...]
    map: ComposedMap
    flip: Literal["invariant", "complement", "negate"] | None
    uncertainty: UncertaintyDisposition
    exact: bool
    error: Fraction | None
    assumptions: tuple[AssumptionInstance, ...]


@dataclass(frozen=True)
class NotConvertible:
    reason: str
    concerns: tuple[str, ...]


@dataclass(frozen=True)
class Unknown:
    reason: str
    concerns: tuple[str, ...]


def _identity() -> RawMap:
    return RawMap("identity", Fraction(1), Fraction(0), True, None, None)


def _oriented(raw: RawMap, forward: bool) -> RawMap:
    if forward:
        return raw
    return RawMap(raw.kind, 1 / raw.factor, -raw.offset / raw.factor, raw.exact, raw.error, raw.crosswalk)


def _unit_map(conversion: CompiledConversion, a_unit: str) -> RawMap:
    # The declared factor already carries the constant's numerical contribution.
    return _oriented(
        RawMap(
            "affine" if conversion.kind == "affine" else "multiplicative",
            conversion.factor,
            conversion.offset if conversion.offset is not None else Fraction(0),
            conversion.exact,
            conversion.error,
            None,
        ),
        conversion.from_unit == a_unit,
    )


def _authority(id: str, snapshot: ComparabilitySnapshot) -> tuple[str | None, tuple[str, ...]]:
    visited: list[str] = []
    while id not in visited:
        visited.append(id)
        try:
            value = snapshot.read(id)
        except DependencyNotHeld:
            return None, tuple(visited)
        if not isinstance(value, Procedure):
            raise MalformedRecord("a scale reference must name a procedure")
        if not isinstance(value.scale, SameAs):
            if not value.is_authority:
                raise MalformedRecord("a scale reference must resolve to an authority")
            return id, tuple(visited)
        id = value.scale.authority
    return None, tuple(visited)


def _scale_map(
    a: str, b: str, snapshot: ComparabilitySnapshot
) -> tuple[RawMap, tuple[AssumptionInstance, ...]] | NotConvertible:
    a_authority, a_reads = _authority(a, snapshot)
    b_authority, b_reads = _authority(b, snapshot)
    ids = (*a_reads, *b_reads)
    if a_authority is None or b_authority is None:
        refusal = snapshot._eligibility(ids)
        if refusal:
            return refusal
        raise MalformedRecord("eligibility admitted a missing or cyclic scale authority")
    if a_authority == b_authority:
        refusal = snapshot._eligibility(ids)
        return refusal if refusal else (_identity(), ())
    candidates = set(snapshot.records.crosswalks(a_authority, b_authority))
    if len(candidates) > 1:
        raise AmbiguousCrosswalk("ambiguous direct crosswalks: " + ", ".join(sorted(candidates)))
    if not candidates:
        refusal = snapshot._eligibility(ids)
        return refusal if refusal else NotConvertible("no conversion between scales", (a, b))
    id = min(candidates)
    model = snapshot.read(id)
    if (
        not isinstance(model, ProxyModel)
        or model.crosswalk is None
        or {model.source.procedure, model.target.scale_of} != {a_authority, b_authority}
    ):
        raise MalformedRecord("crosswalk index must name a proxy joining the requested authorities")
    refusal = snapshot._eligibility((*ids, id))
    if refusal:
        return refusal
    crosswalk = model.crosswalk
    raw = _oriented(
        RawMap(
            "affine" if crosswalk.conversion.kind == "affine" else "multiplicative",
            crosswalk.conversion.factor,
            crosswalk.conversion.offset if crosswalk.conversion.offset is not None else Fraction(0),
            False,
            crosswalk.error.value,
            id,
        ),
        model.source.procedure == a_authority,
    )
    kinds = [term for term in snapshot.profile.assumption_kinds if term.partition("/")[-1] == "proxy-validity"]
    if len(kinds) != 1:
        raise ProfileError("convertibility requires exactly one activated proxy-validity assumption kind")
    assumption = AssumptionInstance(
        kinds[0],
        {
            "record": id,
            "co_scope": "unknown" if model.validity else "equal",
            "dimensions": ",".join(sorted(model.validity)),
            "error": decimal_projection(crosswalk.error.value),
        },
    )
    check_instance(snapshot.profile, assumption)
    return raw, (assumption,)


def _raw_map(
    a: Coordinates, b: Coordinates, snapshot: ComparabilitySnapshot
) -> tuple[RawMap, tuple[AssumptionInstance, ...]] | NotConvertible:
    if a.unit is not None and b.unit is not None:
        if a.unit == b.unit:
            return _identity(), ()
        conversion = snapshot.profile.conversion_between(a.unit, b.unit)
        return (
            (_unit_map(conversion, a.unit), ())
            if conversion
            else NotConvertible("no conversion between units", (a.unit, b.unit))
        )
    if a.scale is not None and b.scale is not None:
        return _scale_map(a.scale, b.scale, snapshot)
    return NotConvertible("unit against scale", (a.unit or a.scale or "", b.unit or b.scale or ""))


def _affine(transformation: CompiledTransformation) -> tuple[Fraction, Fraction]:
    if transformation.kind == "identity":
        return Fraction(1), Fraction(0)
    assert transformation.scale is not None and transformation.offset is not None
    return transformation.scale, transformation.offset


def _sign(transformation: CompiledTransformation) -> int:
    if transformation.kind == "identity":
        return 1
    if transformation.kind == "affine":
        assert transformation.scale is not None
        return 1 if transformation.scale > 0 else -1
    if transformation.kind == "logarithm":
        assert transformation.base is not None
        return 1 if transformation.base > 1 else -1
    return 1 if transformation.direction == "increasing" else -1


def _affine_map(scale: Fraction | Decimal, offset: Fraction | Decimal) -> ComposedMap:
    identity = isinstance(scale, Fraction) and isinstance(offset, Fraction) and scale == 1 and offset == 0
    return ComposedMap("identity" if identity else "affine", scale, offset, scale < 0)


def _finite_decimal(value: Fraction) -> bool:
    denominator = value.denominator
    for prime in (2, 5):
        while denominator % prime == 0:
            denominator //= prime
    return denominator == 1


def _ln_fraction(value: Fraction) -> Decimal:
    # Raw factors are declared finite decimals or their exact inverses.
    if _finite_decimal(value):
        return CONTEXT.ln(Decimal(decimal_projection(value)))
    return CONTEXT.minus(CONTEXT.ln(Decimal(decimal_projection(1 / value))))


def _contains_image(source: str, target: str, factor: Fraction, offset: Fraction) -> bool:
    if target == "real":
        return True
    if source == "real":
        return False
    if source in {"positive", "nonnegative"}:
        return (
            target in {"positive", "nonnegative"}
            and factor > 0
            and (offset > 0 or offset == 0 and (target == "nonnegative" or source == "positive"))
        )
    if source == "unit-interval":
        low, high = sorted((offset, factor + offset))
        return (
            (target == "positive" and low > 0)
            or (target == "nonnegative" and low >= 0)
            or (target == "unit-interval" and low >= 0 and high <= 1)
        )
    return False


def _compose(a: CompiledTransformation, b: CompiledTransformation, raw: RawMap) -> ComposedMap | Unknown:
    concerns = (a.term, b.term)
    raw_identity = raw.factor == 1 and raw.offset == 0
    decreasing = _sign(a) * (1 if raw.factor > 0 else -1) * _sign(b) < 0
    if a.term == b.term and raw_identity:
        if a.fixed:
            return _affine_map(Fraction(1), Fraction(0))
        return ComposedMap("strictly-increasing", None, None, False)
    affine_a, affine_b = a.kind in {"identity", "affine"}, b.kind in {"identity", "affine"}
    if affine_a and affine_b:
        sa, oa = _affine(a)
        sb, ob = _affine(b)
        return _affine_map(sb * raw.factor / sa, sb * (raw.offset - raw.factor * oa / sa) + ob)
    if a.kind == b.kind == "logarithm":
        if raw.offset != 0:
            return Unknown("logarithms under offset", concerns)
        if raw.factor <= 0:
            return Unknown("domain", concerns)
        assert a.base is not None and b.base is not None
        # Evaluated logarithmic coefficients stay Decimal; only structural 0/1 is exact.
        ln_b = CONTEXT.ln(Decimal(b.number_text["base"]))
        scale = Fraction(1) if a.base == b.base else CONTEXT.divide(CONTEXT.ln(Decimal(a.number_text["base"])), ln_b)
        offset = Fraction(0) if raw.factor == 1 else CONTEXT.divide(_ln_fraction(raw.factor), ln_b)
        return _affine_map(scale, offset)
    if a.kind == b.kind == "monotone" and a.term == b.term:
        return Unknown("transformation under unit change", concerns)
    if not affine_a and not affine_b:
        return Unknown("distinct monotone kinds", concerns)
    if a.kind == "logarithm" or b.kind == "logarithm":
        if (
            a.kind == "logarithm" and not _contains_image(b.domain, a.domain, 1 / raw.factor, -raw.offset / raw.factor)
        ) or (b.kind == "logarithm" and not _contains_image(a.domain, b.domain, raw.factor, raw.offset)):
            return Unknown("domain", concerns)
    # Positive raw scaling uses the shared admissible domain, without sample-value claims.
    elif (raw.offset != 0 or raw.factor < 0) and (
        (a.kind == "monotone" and not _contains_image(b.domain, a.domain, 1 / raw.factor, -raw.offset / raw.factor))
        or (b.kind == "monotone" and not _contains_image(a.domain, b.domain, raw.factor, raw.offset))
    ):
        return Unknown("domain", concerns)
    return ComposedMap("strictly-decreasing" if decreasing else "strictly-increasing", None, None, decreasing)


def _parameter_admits(typing: ParameterTypingName, map: ComposedMap) -> bool:
    if typing in {"independent", "dimensionless"}:
        return True
    if map.cls not in {"identity", "affine"}:
        return False
    if typing == "response-log-level":
        assert map.scale is not None
        return map.offset == 0 and map.scale > 0
    return True


def _admits(functional: FunctionalProperties, map: ComposedMap) -> bool:
    certificate = functional.response_transformation
    if map.cls == "identity" or certificate == "invariant-strictly-increasing":
        return True
    if certificate == "by-parameters":
        assert functional.parameters is not None
        return all(_parameter_admits(value.typing, map) for value in functional.parameters.values())
    if map.cls != "affine":
        return False
    assert map.scale is not None
    if certificate == "equivariant-affine":
        return True
    if certificate == "equivariant-positive-affine":
        return map.scale > 0
    return certificate == "invariant-positive-scaling" and map.scale > 0 and map.offset == 0


def _output_steps(
    map: ComposedMap,
    raw: RawMap,
    output: OutputTyping,
    a: CompiledTransformation,
    b: CompiledTransformation,
) -> tuple[Step, ...] | None:
    if map.cls == "identity" or output.typing == "dimensionless":
        return ()
    if output.typing == "response-log-level":
        if raw.factor <= 0 or raw.offset != 0 or a.kind != "identity" or b.kind != "identity":
            return None
        return (LogShift(_ln_fraction(raw.factor)),)
    if map.scale is None or map.offset is None:
        return None
    steps: tuple[Step, ...] = (Scale(map.scale),)
    if output.typing != "response-difference" and map.offset != 0:
        steps += (Shift(map.offset),)
    return steps


def convert(
    a: Coordinates,
    b: Coordinates,
    *,
    binding: Binding,
    functional: FunctionalProperties,
    output: OutputTyping,
    snapshot: ComparabilitySnapshot,
) -> Convertible | NotConvertible | Unknown:
    """Admit an A-to-B coordinate map and derive its output and uncertainty actions."""
    if binding not in {"certified", "independent"}:
        raise ValueError(f"unsupported binding: {binding!r}")
    if a.quantity_kind != b.quantity_kind:
        conversion = (
            snapshot.profile.conversion_between(a.unit, b.unit) if a.unit is not None and b.unit is not None else None
        )
        if conversion is None or conversion.constant is None:
            return NotConvertible("quantity kind", (a.quantity_kind, b.quantity_kind))
    value = _raw_map(a, b, snapshot)
    if isinstance(value, NotConvertible):
        return value
    raw, assumptions = value
    own_output = binding == "certified" and output.typing == "independent"
    if own_output:
        effective = raw
    elif a.value_type == "ratio":
        if raw.offset != 0:
            return NotConvertible("ratio across affine change", (a.unit or a.scale or "", b.unit or b.scale or ""))
        effective = _identity()
    elif a.value_type == "difference":
        effective = RawMap(raw.kind, raw.factor, Fraction(0), raw.exact, raw.error, raw.crosswalk)
    else:
        effective = raw
    a_transformation = snapshot.profile.transformations[a.transformation]
    b_transformation = snapshot.profile.transformations[b.transformation]
    map = _affine_map(raw.factor, raw.offset) if own_output else _compose(a_transformation, b_transformation, effective)
    if isinstance(map, Unknown):
        return map
    concerns = (a.transformation, b.transformation)
    if binding == "independent":
        if map.cls != "identity":
            return NotConvertible("independent-variable map", concerns)
    elif output.typing != "independent" and not _admits(functional, map):
        return NotConvertible("transformation", concerns)
    flip: Literal["invariant", "complement", "negate"] | None = None
    if binding == "certified" and output.typing != "independent" and map.decreasing:
        action = functional.response_reversal
        if action != "invariant" and action != "complement" and action != "negate":
            return NotConvertible("response reversal", concerns)
        flip = action
    if raw.crosswalk is not None and raw.error is not None and functional.ties == "undefined":
        return NotConvertible("ties", (raw.crosswalk,))
    steps: tuple[Step, ...] = ()
    if binding == "certified":
        estimate_steps = _output_steps(map, raw, output, a_transformation, b_transformation)
        if estimate_steps is None:
            return NotConvertible("transformation", concerns)
        steps = estimate_steps
        if (flip == "complement" or flip == "negate") and (
            map.cls == "strictly-decreasing" or output.typing in {"dimensionless", "response-log-level"}
        ):
            steps += (Flip(flip),)
    uncertainty: UncertaintyDisposition = "exact"
    if raw.crosswalk is not None:
        uncertainty = "not-carried: crosswalk"
    elif functional.uncertainty == "none":
        uncertainty = "absent"
    elif functional.uncertainty == "recompute" and map.cls != "identity":
        uncertainty = "needs-operands"
    return Convertible(steps, map, flip, uncertainty, raw.exact, raw.error, assumptions)
