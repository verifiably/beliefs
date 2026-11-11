"""Read-only correspondence, conversion and synthesis of frozen assessed targets."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from fractions import Fraction
from types import MappingProxyType
from typing import Literal, TypeAlias, cast

from beliefs.assumptions import AssumptionInstance, check_instance, instance_projection
from beliefs.claim import Claim, Referent, member_key
from beliefs.comparability import (
    ComparabilitySnapshot,
    ComposedMap,
    Convertible,
    Domain,
    Flip,
    NotConvertible,
    OutputTyping,
    ParameterTypingName,
    Reciprocal,
    Scale,
    Unknown,
    apply_exact,
    compare_mapped,
    convert,
    functional_properties,
    unit_map,
)
from beliefs.estimand import (
    AxisLevels,
    IncrementBinding,
    LagBinding,
    MeasuredBinding,
    NullReference,
    OutputSpec,
    RoleAnchor,
    RoleBinding,
    RoleLevels,
    RoleTermLevels,
    RuleClassLevels,
    ValueReference,
)
from beliefs.identity import v1
from beliefs.measurement import Coordinates, Observable
from beliefs.procedure import Procedure
from beliefs.profile import ProfileSpec
from beliefs.proxy_model import ProxyModel
from beliefs.restriction import IntervalRestriction, co_scope, co_scope_by_dimension, restriction_projection
from beliefs.target import AssessedTarget


@dataclass(frozen=True)
class AssessedProposition:
    claim: Claim
    target: AssessedTarget
    interpretation_rule: str


@dataclass(frozen=True)
class TargetConvertible:
    outputs: Mapping[str, Convertible]
    level_reversal: str | None
    assumptions: tuple[AssumptionInstance, ...]
    snapshot: str
    kind: Literal["convertible"] = field(default="convertible", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "outputs", MappingProxyType(dict(self.outputs)))


@dataclass(frozen=True)
class TargetNotConvertible:
    reason: str
    snapshot: str
    kind: Literal["not-convertible"] = field(default="not-convertible", init=False)


@dataclass(frozen=True)
class TargetUnknown:
    reason: str
    snapshot: str
    kind: Literal["unknown"] = field(default="unknown", init=False)


@dataclass(frozen=True)
class Permitted:
    snapshot: str
    kind: Literal["permitted"] = field(default="permitted", init=False)


@dataclass(frozen=True)
class PermittedUnder:
    assumptions: tuple[AssumptionInstance, ...]
    snapshot: str
    kind: Literal["permitted-under"] = field(default="permitted-under", init=False)


@dataclass(frozen=True)
class SynthesisRefused:
    reason: str
    snapshot: str
    kind: Literal["refused"] = field(default="refused", init=False)


ConversionVerdict: TypeAlias = TargetConvertible | TargetNotConvertible | TargetUnknown
SynthesisVerdict: TypeAlias = Permitted | PermittedUnder | SynthesisRefused | TargetNotConvertible | TargetUnknown
Pair: TypeAlias = tuple[str, MeasuredBinding | IncrementBinding, MeasuredBinding | IncrementBinding]


@dataclass(frozen=True)
class _Correspondence:
    pairs: tuple[Pair, ...]
    reversal: str | None
    increment: Fraction
    crosswalks: frozenset[str] = frozenset()


def _union(*groups: tuple[AssumptionInstance, ...]) -> tuple[AssumptionInstance, ...]:
    unique = {v1.encode(instance_projection(a)): a for group in groups for a in group}
    return tuple(unique[key] for key in sorted(unique))


def _source(
    binding: RoleBinding | MeasuredBinding | IncrementBinding | RoleTermLevels | RoleAnchor, claim: Claim
) -> tuple[object, ...]:
    ref = binding.member if binding.member is not None else claim.roles[binding.role]
    refs = (member_key(ref),) if isinstance(ref, Referent) else tuple(sorted(member_key(m.referent) for m in ref))
    return binding.role, refs


def _unit_coefficients(a: str, b: str, profile: ProfileSpec) -> tuple[Fraction, Fraction] | None:
    if a == b:
        return Fraction(1), Fraction(0)
    conversion = profile.conversion_between(a, b)
    if conversion is None:
        return None
    raw = unit_map(conversion, a)
    return raw.factor, raw.offset


def _factor(a: str, b: str, profile: ProfileSpec) -> Fraction | None:
    coefficients = _unit_coefficients(a, b, profile)
    return None if coefficients is None else coefficients[0]


def _intervals(a: tuple[IntervalRestriction, ...], b: tuple[IntervalRestriction, ...], profile: ProfileSpec) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b, strict=True):
        coefficients = _unit_coefficients(x.unit, y.unit, profile)
        if (
            coefficients is None
            or coefficients[0] <= 0
            or (x.low_closed, x.high_closed, x.convention) != (y.low_closed, y.high_closed, y.convention)
        ):
            return False
        assert coefficients is not None
        factor, offset = coefficients
        if tuple(None if n is None else n * factor + offset for n in (x.low, x.high)) != (y.low, y.high):
            return False
    return True


def _correspondence(a: AssessedProposition, b: AssessedProposition, profile: ProfileSpec) -> _Correspondence | str:
    left, right = a.target.estimand, b.target.estimand
    if (left.form, left.functional) != (right.form, right.functional):
        return "functional"
    if left.bindings.keys() != right.bindings.keys() or left.outputs.keys() != right.outputs.keys():
        return "target"
    if any((x.typing, x.domain) != (right.outputs[n].typing, right.outputs[n].domain) for n, x in left.outputs.items()):
        return "target"
    functional = profile.functionals[left.functional].declaration
    pairs: list[Pair] = []
    reversal = None
    increment = Fraction(1)

    def measured(label: str, x: MeasuredBinding | IncrementBinding, y: MeasuredBinding | IncrementBinding) -> bool:
        if _source(x, a.claim) != _source(y, b.claim):
            return False
        pairs.append((label, x, y))
        return True

    for name, x in left.bindings.items():
        y = right.bindings[name]
        if type(x) is not type(y):
            return "target"
        if isinstance(x, MeasuredBinding):
            assert isinstance(y, MeasuredBinding)
            if not measured(name, x, y):
                return "target"
        elif isinstance(x, IncrementBinding):
            assert isinstance(y, IncrementBinding)
            if not measured(name, x, y):
                return "target"
            factor = _factor(x.unit, y.unit, profile)
            if factor is None or factor <= 0:
                return "target"
            increment = Fraction(y.increment) / (Fraction(x.increment) * factor)
            if increment != 1 and functional.increment != "linear":
                return "target"
        elif isinstance(x, tuple):
            assert isinstance(y, tuple)
            xd, yd = dict(x), dict(y)
            if xd.keys() != yd.keys() or functional.exchange == "directed" and tuple(xd) != tuple(yd):
                return "target"
            if not all(measured(f"{name}.{label}", xd[label], yd[label]) for label in sorted(xd)):
                return "target"
        elif isinstance(x, (RoleTermLevels, RuleClassLevels, RoleLevels, AxisLevels)):
            if isinstance(x, RoleTermLevels):
                assert isinstance(y, RoleTermLevels)
                if _source(x, a.claim) != _source(y, b.claim):
                    return "target"
                same, reverse = x.levels == y.levels, x.levels == tuple(reversed(y.levels))
            elif isinstance(x, RuleClassLevels):
                assert isinstance(y, RuleClassLevels)
                if x.rule != y.rule:
                    return "target"
                same, reverse = x.classes == y.classes, x.classes == tuple(reversed(y.classes))
            elif isinstance(x, AxisLevels):
                assert isinstance(y, AxisLevels)
                same, reverse = (
                    _intervals(x.levels, y.levels, profile),
                    _intervals(x.levels, tuple(reversed(y.levels)), profile),
                )
            else:
                assert isinstance(x, RoleLevels) and isinstance(y, RoleLevels)
                xs = tuple(_source(v, a.claim) for v in x.roles)
                ys = tuple(_source(v, b.claim) for v in y.roles)
                same, reverse = xs == ys, xs == tuple(reversed(ys))
                other = y.roles if same else tuple(reversed(y.roles))
                if not all(measured(f"{name}.{i}", v, w) for i, (v, w) in enumerate(zip(x.roles, other, strict=True))):
                    return "target"
            if not same:
                if not reverse or functional.reversal in {"not-applicable", "undefined"}:
                    return "target"
                reversal = functional.reversal
        elif isinstance(x, RoleAnchor):
            assert isinstance(y, RoleAnchor)
            if _source(x, a.claim) != _source(y, b.claim) or x.category != y.category:
                return "target"
        elif isinstance(x, LagBinding):
            assert isinstance(y, LagBinding)
            if _factor(x.unit, y.unit, profile) is None or not _intervals(x.windows, y.windows, profile):
                return "target"
        elif isinstance(x, RoleBinding):
            assert isinstance(y, RoleBinding)
            if _source(x, a.claim) != _source(y, b.claim):
                return "target"
        else:
            if x != y:
                return "target"
    return _Correspondence(tuple(pairs), reversal, increment)


def _verdict(
    value: Convertible | NotConvertible | Unknown, snapshot: str
) -> Convertible | TargetNotConvertible | TargetUnknown:
    if isinstance(value, NotConvertible):
        return TargetNotConvertible(value.reason, snapshot)
    if isinstance(value, Unknown):
        return TargetUnknown(value.reason, snapshot)
    return value


def _coordinates(output: OutputSpec, identity: str) -> Coordinates:
    assert output.quantity_kind is not None
    return Coordinates(output.quantity_kind, output.unit, output.scale, "level", identity)


def _identity_transformation(profile: ProfileSpec) -> str:
    # The identity coordinate is a declared property, never a pack-specific name.
    values = [term for term, value in profile.transformations.items() if value.kind == "identity" and value.fixed]
    return min(values)


def _convert(
    a: AssessedProposition,
    b: AssessedProposition,
    *,
    profile: ProfileSpec,
    snapshot: ComparabilitySnapshot,
    snapshot_identity: str,
) -> tuple[ConversionVerdict, _Correspondence | None]:
    correspondence = _correspondence(a, b, profile)
    if isinstance(correspondence, str):
        return TargetNotConvertible(correspondence, snapshot_identity), None
    left, right = a.target.estimand, b.target.estimand
    functional = functional_properties(profile.functionals[left.functional])
    # An independent-variable refusal must precede every output action.
    for label, x, y in correspondence.pairs:
        if label.startswith("independent."):
            result = _verdict(
                convert(
                    x.measure.coordinates,
                    y.measure.coordinates,
                    binding="independent",
                    functional=functional,
                    output=OutputTyping("dimensionless", "real"),
                    snapshot=snapshot,
                ),
                snapshot_identity,
            )
            if not isinstance(result, Convertible):
                return result, correspondence
    certified = [
        (label, x, y) for label, x, y in correspondence.pairs if label == "response" or label.startswith("variables.")
    ]
    output_maps: dict[str, Convertible] = {}
    binding_maps: list[Convertible] = []
    crosswalks: set[str] = set()
    for label, x, y in certified:
        first = next(iter(left.outputs.values()))
        output = (
            OutputTyping("dimensionless", "real")
            if functional.parameters is not None
            else OutputTyping(cast(ParameterTypingName, first.typing), cast(Domain, first.domain))
        )
        result = _verdict(
            convert(
                x.measure.coordinates,
                y.measure.coordinates,
                binding="certified",
                functional=functional,
                output=output,
                snapshot=snapshot,
            ),
            snapshot_identity,
        )
        if not isinstance(result, Convertible):
            return result, correspondence
        binding_maps.append(result)
        if result.uncertainty.startswith("not-carried: crosswalk"):
            crosswalks.add(label)
    correspondence = replace(correspondence, crosswalks=frozenset(crosswalks))
    for name, output in left.outputs.items():
        if functional.parameters is not None:
            if output.typing == "independent":
                target_output = right.outputs[name]
                identity = _identity_transformation(profile)
                ca, cb = _coordinates(output, identity), _coordinates(target_output, identity)
            else:
                _, x, y = certified[0]
                ca, cb = x.measure.coordinates, y.measure.coordinates
            result = _verdict(
                convert(
                    ca,
                    cb,
                    binding="certified",
                    functional=functional,
                    output=OutputTyping(cast(ParameterTypingName, output.typing), cast(Domain, output.domain)),
                    snapshot=snapshot,
                ),
                snapshot_identity,
            )
            if not isinstance(result, Convertible):
                return result, correspondence
        elif binding_maps:
            result = binding_maps[0]
            if len(binding_maps) > 1:
                steps = tuple(step for value in binding_maps for step in value.steps)
                flips = tuple(step for step in steps if isinstance(step, Flip))
                assert len(flips) == len(steps)  # Association outputs are dimensionless.
                steps = (flips[0],) if len(flips) % 2 else ()
                action = flips[0].action if steps else None
                output_map = ComposedMap(
                    "affine" if steps else "identity",
                    Fraction(-1 if steps else 1),
                    Fraction(1 if action == "complement" else 0),
                    bool(steps),
                )
                uncertainty = next(
                    (v.uncertainty for v in binding_maps if v.uncertainty.startswith("not-carried")),
                    "needs-operands"
                    if any(v.uncertainty == "needs-operands" for v in binding_maps)
                    else result.uncertainty,
                )
                result = replace(
                    result,
                    steps=steps,
                    map=output_map,
                    flip=action,
                    uncertainty=uncertainty,
                    assumptions=_union(*(v.assumptions for v in binding_maps)),
                    exact=all(v.exact for v in binding_maps),
                )
        else:
            result = Convertible(
                (), ComposedMap("identity", Fraction(1), Fraction(0), False), None, "exact", True, None, ()
            )
        extra = ()
        if correspondence.reversal == "negate":
            extra = (Flip("negate"),)
        elif correspondence.reversal == "complement":
            extra = (Flip("complement"),)
        elif correspondence.reversal == "reciprocal":
            extra = (Reciprocal(),)
        if correspondence.increment != 1:
            extra += (Scale(correspondence.increment),)
        output_maps[name] = replace(result, steps=(*result.steps, *extra))
    assumptions = _union(left.assumptions, right.assumptions, *(v.assumptions for v in output_maps.values()))
    return TargetConvertible(output_maps, correspondence.reversal, assumptions, snapshot_identity), correspondence


def convertibility(
    a: AssessedProposition,
    b: AssessedProposition,
    *,
    profile: ProfileSpec,
    snapshot: ComparabilitySnapshot,
    snapshot_identity: str,
) -> ConversionVerdict:
    return _convert(a, b, profile=profile, snapshot=snapshot, snapshot_identity=snapshot_identity)[0]


def _assumption(profile: ProfileSpec, name: str, particulars: Mapping[str, str]) -> AssumptionInstance:
    kinds = [kind for kind in profile.assumption_kinds if kind.partition("/")[2] == name]
    if len(kinds) != 1:
        from beliefs.errors import ProfileError

        raise ProfileError(f"target comparison requires exactly one {name} assumption kind")
    value = AssumptionInstance(kinds[0], particulars)
    check_instance(profile, value)
    return value


def _observable(binding: MeasuredBinding | IncrementBinding, snapshot: ComparabilitySnapshot) -> Observable:
    if isinstance(binding, MeasuredBinding) and binding.proxy is not None:
        value = snapshot.read(binding.proxy)
        assert isinstance(value, ProxyModel) and value.target.observable is not None
        return value.target.observable
    return binding.measure.observable


def _references(
    a: ValueReference | NullReference, b: ValueReference | NullReference, conversion: Convertible
) -> Literal["equal", "unequal", "undecidable"]:
    if type(a) is not type(b):
        return "unequal"
    if isinstance(a, ValueReference):
        assert isinstance(b, ValueReference)
        return compare_mapped(conversion.steps, Fraction(a.value), Fraction(b.value))
    assert isinstance(b, NullReference)
    ends = tuple(apply_exact(conversion.steps, Fraction(value)) for value in (a.low, a.high))
    if not all(isinstance(value, Fraction) for value in ends):
        return "undecidable"
    low, high = sorted(cast(tuple[Fraction, Fraction], ends))
    return "equal" if (low, high) == (Fraction(b.low), Fraction(b.high)) else "unequal"


def synthesis(
    a: AssessedProposition,
    b: AssessedProposition,
    *,
    profile: ProfileSpec,
    snapshot: ComparabilitySnapshot,
    snapshot_identity: str,
    observable_proxies: Callable[[Observable, Observable], tuple[str, ...]],
) -> SynthesisVerdict:
    conversion, correspondence = _convert(a, b, profile=profile, snapshot=snapshot, snapshot_identity=snapshot_identity)
    if not isinstance(conversion, TargetConvertible):
        return conversion
    assert correspondence is not None
    assumptions = _union(a.target.estimand.assumptions, b.target.estimand.assumptions)
    for _, x, y in correspondence.pairs:
        proxies = tuple(
            binding.proxy for binding in (x, y) if isinstance(binding, MeasuredBinding) and binding.proxy is not None
        )
        if snapshot.check_eligibility(proxies) is not None:
            return TargetNotConvertible("dependency ineligible", snapshot_identity)
        ox, oy = _observable(x, snapshot), _observable(y, snapshot)
        if ox == oy:
            continue
        candidate: tuple[str, ProxyModel, tuple[str, ...]] | None = None
        undecidable = False
        for ref in sorted(set(observable_proxies(ox, oy))):
            if snapshot.check_eligibility((ref,)) is not None:
                continue
            value = snapshot.read(ref)
            if not isinstance(value, ProxyModel) or value.target.observable is None:
                continue
            if {value.source.observable, value.target.observable} != {ox, oy}:
                continue
            scopes = tuple(co_scope(t.target.applicability.restrictions(), value.validity, profile) for t in (a, b))
            if "disjoint" in scopes:
                continue
            if "unknown" in scopes:
                undecidable = True
                continue
            if set(scopes) <= {"equal", "narrower"}:
                candidate = ref, value, scopes
                break
            if candidate is None:
                candidate = ref, value, scopes
        if candidate is None:
            return (
                TargetUnknown("observable", snapshot_identity)
                if undecidable
                else SynthesisRefused("observable", snapshot_identity)
            )
        ref, value, scopes = candidate
        if not set(scopes) <= {"equal", "narrower"}:
            assumptions = _union(
                assumptions,
                (
                    _assumption(
                        profile,
                        "proxy-validity",
                        {"record": ref, "co_scope": ",".join(scopes), "dimensions": ",".join(sorted(value.validity))},
                    ),
                ),
            )
        if isinstance(value.basis, AssumptionInstance):
            assumptions = _union(assumptions, (value.basis,))
    for instance in _union(*(value.assumptions for value in conversion.outputs.values())):
        ref = instance.particulars["record"]
        proxy = snapshot.read(ref)
        assert isinstance(proxy, ProxyModel) and proxy.crosswalk is not None
        scopes = tuple(co_scope(value.target.applicability.restrictions(), proxy.validity, profile) for value in (a, b))
        if "disjoint" in scopes:
            return SynthesisRefused("scope", snapshot_identity)
        if "unknown" in scopes:
            return TargetUnknown("scope", snapshot_identity)
        dimensions = sorted(
            {
                dimension
                for value in (a, b)
                for dimension, relation in co_scope_by_dimension(
                    value.target.applicability.restrictions(), proxy.validity, profile
                ).items()
                if relation != "equal"
            }
        )
        qualified = AssumptionInstance(
            instance.kind,
            {
                **instance.particulars,
                "co_scope": ",".join(sorted(set(scopes))),
                "dimensions": ",".join(dimensions),
            },
        )
        check_instance(profile, qualified)
        assumptions = _union(assumptions, (qualified,))
    for label, x, y in correspondence.pairs:
        ids = x.measure.procedure, y.measure.procedure
        if snapshot.check_eligibility(ids) is not None:
            return TargetNotConvertible("dependency ineligible", snapshot_identity)
        px, py = snapshot.read(ids[0]), snapshot.read(ids[1])
        assert isinstance(px, Procedure) and isinstance(py, Procedure)
        crosswalk = label in correspondence.crosswalks
        if ids[0] != ids[1] and ids[1] not in px.compatible_with and ids[0] not in py.compatible_with and not crosswalk:
            return SynthesisRefused("procedure", snapshot_identity)
    left, right = a.target.estimand, b.target.estimand
    if left.control != right.control:
        return SynthesisRefused("control", snapshot_identity)
    scope = co_scope(a.target.applicability.restrictions(), b.target.applicability.restrictions(), profile)
    if scope == "unknown":
        return TargetUnknown("scope", snapshot_identity)
    if scope == "disjoint":
        return SynthesisRefused("scope", snapshot_identity)
    if scope != "equal":
        differences = co_scope_by_dimension(
            a.target.applicability.restrictions(), b.target.applicability.restrictions(), profile
        )
        dimensions = ",".join(k for k, v in sorted(differences.items()) if v != "equal")
        intervals = sorted(
            v1.encode(
                {k: restriction_projection(v) for k, v in value.target.applicability.restrictions().items()}
            ).decode()
            for value in (a, b)
        )
        assumptions = _union(
            assumptions,
            (
                _assumption(
                    profile,
                    "transport-exchangeability",
                    {"dimensions": dimensions, "co_scope": scope, "scopes": " | ".join(intervals)},
                ),
            ),
        )
    references = []
    for name, output in conversion.outputs.items():
        ra = left.reference[name] if isinstance(left.reference, Mapping) else left.reference
        rb = right.reference[name] if isinstance(right.reference, Mapping) else right.reference
        references.append(_references(ra, rb, output))
    if "unequal" in references:
        return SynthesisRefused("reference", snapshot_identity)
    if "undecidable" in references:
        return TargetUnknown("reference", snapshot_identity)
    if a.interpretation_rule != b.interpretation_rule:
        return SynthesisRefused("interpretation rule", snapshot_identity)
    if a.target.standing != b.target.standing:
        return SynthesisRefused("standing", snapshot_identity)
    return PermittedUnder(assumptions, snapshot_identity) if assumptions else Permitted(snapshot_identity)
