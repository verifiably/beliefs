"""The closed estimand grammar, authored against a claim and held records."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from decimal import Decimal
from types import MappingProxyType
from typing import TypeAlias, cast, final

from beliefs import _measurement_record as wire
from beliefs.applicability import Applicability
from beliefs.applicability import checked as check_applicability
from beliefs.aptness import check_aptness
from beliefs.assumptions import AssumptionInstance, check_instance, instance_from_projection, instance_projection
from beliefs.claim import Claim, Referent, check_referent, member_key
from beliefs.classification_rule import ClassificationRule
from beliefs.contract.base import SUPPORTED_ESTIMAND_FORMS, SUPPORTED_UNCERTAINTY_KINDS
from beliefs.dependencies import (
    DependencyEntry,
    FrozenAssessmentDependency,
    HeldRecords,
    dependencies_from_projection,
    dependencies_projection,
    dependency_closure,
    read_record,
)
from beliefs.errors import (
    ContrastRefused,
    ControlRefused,
    EstimandError,
    EstimandNotAdmitted,
    IdentificationNotLicensed,
    MalformedRecord,
    ReferenceRefused,
    UnboundReferent,
    UncertaintyRefused,
    UntypedEstimandMember,
)
from beliefs.identity import v1
from beliefs.measurement import Measure, check_measure, measure_from_projection, measure_projection
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity
from beliefs.proxy_model import Calibration, ProxyModel
from beliefs.resolution import BindingCheckReceipt, ResolutionSnapshot, TermOutcome, _emit_receipt
from beliefs.restriction import IntervalRestriction, restriction_from_projection, restriction_projection
from beliefs.sealed import sealed


@dataclass(frozen=True)
class RoleBinding:
    role: str
    member: Referent | None


@dataclass(frozen=True)
class MeasuredBinding:
    role: str
    member: Referent | None
    measure: Measure
    mapping: str | None
    proxy: str | None


@dataclass(frozen=True)
class RoleTermLevels:
    role: str
    member: Referent | None
    levels: tuple[Referent, ...]


@dataclass(frozen=True)
class RuleClassLevels:
    rule: str
    classes: tuple[Referent, ...]


@dataclass(frozen=True)
class RoleLevels:
    roles: tuple[MeasuredBinding, MeasuredBinding]


@dataclass(frozen=True)
class AxisLevels:
    levels: tuple[IntervalRestriction, ...]


@dataclass(frozen=True)
class IncrementBinding:
    role: str
    member: Referent | None
    measure: Measure
    increment: Decimal
    unit: str


@dataclass(frozen=True)
class RuleAnchor:
    rule: str
    classes: tuple[Referent, ...]


@dataclass(frozen=True)
class RoleAnchor:
    role: str
    member: Referent | None
    category: Referent


@dataclass(frozen=True)
class LagBinding:
    unit: str
    windows: tuple[IntervalRestriction, ...]


@dataclass(frozen=True)
class DatasetBinding:
    digest: str


Binding: TypeAlias = (
    RoleBinding
    | MeasuredBinding
    | RoleTermLevels
    | RuleClassLevels
    | RoleLevels
    | AxisLevels
    | IncrementBinding
    | RuleAnchor
    | RoleAnchor
    | LagBinding
    | DatasetBinding
    | tuple[tuple[str, MeasuredBinding], ...]
)


@dataclass(frozen=True)
class OutputSpec:
    typing: str
    domain: str
    quantity_kind: str | None = None
    unit: str | None = None
    scale: str | None = None


@dataclass(frozen=True)
class ValueReference:
    value: Decimal


@dataclass(frozen=True)
class NullReference:
    low: Decimal
    high: Decimal


Reference: TypeAlias = ValueReference | NullReference


@dataclass(frozen=True)
class Control:
    identification: str
    conditioning: tuple[Referent, ...]
    design: str
    selection: str

    def __post_init__(self) -> None:
        if not isinstance(self.conditioning, tuple) or not all(isinstance(r, Referent) for r in self.conditioning):
            raise ControlRefused("conditioning is a tuple of referents")
        keys = tuple(member_key(r) for r in self.conditioning)
        if len(set(keys)) != len(keys):
            raise ControlRefused("conditioning referents must be distinct")
        object.__setattr__(self, "conditioning", tuple(sorted(self.conditioning, key=member_key)))


_VARIABLES = {
    "contrast": {"response", "grouping"},
    "quantity": {"response"},
    "law-parameters": {"response", "independent"},
    "event-locked": {"response", "anchor", "lag"},
    "association": {"variables"},
    "enrichment": {"membership", "reference_set", "universe"},
}


@sealed
@final
@dataclass(frozen=True, init=False)
class Estimand:
    claim: str
    operator: str
    form: str
    functional: str
    bindings: Mapping[str, Binding]
    outputs: Mapping[str, OutputSpec]
    reference: Reference | Mapping[str, Reference]
    control: Control
    uncertainty: str
    assumptions: tuple[AssumptionInstance, ...]
    calibration: str | None
    dependencies: tuple[DependencyEntry, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise UntypedEstimandMember("Estimand values are built by build_estimand or restored by estimand_from_stored")


def _mint(**values: object) -> Estimand:
    result = object.__new__(Estimand)
    for field in fields(Estimand):
        object.__setattr__(result, field.name, values[field.name])
    object.__setattr__(result, "bindings", MappingProxyType(dict(result.bindings)))
    object.__setattr__(result, "outputs", MappingProxyType(dict(sorted(result.outputs.items()))))
    if isinstance(result.reference, Mapping):
        object.__setattr__(result, "reference", MappingProxyType(dict(sorted(result.reference.items()))))
    return result


def finite(value: object, where: str) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ReferenceRefused(f"{where} must be a finite Decimal")
    return value


def in_domain(value: object, domain: str) -> Decimal:
    number = finite(value, "value")
    if domain not in {"real", "positive", "nonnegative", "unit-interval", "signed-unit-interval"}:
        raise ReferenceRefused(f"unsupported numeric domain {domain!r}")
    if (
        (domain == "positive" and number <= 0)
        or (domain == "nonnegative" and number < 0)
        or (domain == "unit-interval" and not 0 <= number <= 1)
        or (domain == "signed-unit-interval" and not -1 <= number <= 1)
    ):
        raise ReferenceRefused(f"value {number} is outside {domain}")
    return number


def _role(
    profile: ProfileSpec,
    operator: str,
    binding: RoleBinding | MeasuredBinding | RoleTermLevels | IncrementBinding | RoleAnchor,
    claim: Claim | None,
) -> Referent | None:
    role = profile.template_of(profile.operator(operator)).roles.get(binding.role)
    if role is None:
        raise ContrastRefused(f"unknown role {binding.role!r}")
    if role.arity == "many":
        if not isinstance(binding.member, Referent):
            raise ContrastRefused("a many-role binding names its member")
        if claim is not None:
            members = claim.roles[binding.role]
            assert isinstance(members, tuple)
            if member_key(binding.member) not in {member_key(m.referent) for m in members}:
                raise ContrastRefused("the bound member is not in the claim role")
        return binding.member
    if binding.member is not None:
        raise ContrastRefused("a one-role binding carries no member")
    if claim is None:
        return None
    value = claim.roles[binding.role]
    assert isinstance(value, Referent)
    return value


def measured_bindings(value: Estimand) -> tuple[MeasuredBinding | IncrementBinding, ...]:
    result: list[MeasuredBinding | IncrementBinding] = []
    for binding in value.bindings.values():
        if isinstance(binding, (MeasuredBinding, IncrementBinding)):
            result.append(binding)
        elif isinstance(binding, RoleLevels):
            result.extend(binding.roles)
        elif isinstance(binding, tuple):
            result.extend(row[1] for row in binding)
    return tuple(result)


def binding_roots(value: Estimand) -> tuple[str, ...]:
    roots: set[str] = set()
    for binding in measured_bindings(value):
        roots.add(binding.measure.procedure)
        if binding.measure.scale is not None:
            roots.add(binding.measure.scale)
        if isinstance(binding, MeasuredBinding):
            roots.update(r for r in (binding.mapping, binding.proxy) if r is not None)
    for binding in value.bindings.values():
        if isinstance(binding, (RuleClassLevels, RuleAnchor)):
            roots.add(binding.rule)
    roots.update(output.scale for output in value.outputs.values() if output.scale is not None)
    if value.calibration is not None:
        roots.add(value.calibration)
    return tuple(sorted(roots))


def estimand_referents(value: Estimand) -> dict[str, Referent]:
    result: dict[str, Referent] = {}
    for name, binding in value.bindings.items():
        if (
            isinstance(binding, (RoleBinding, MeasuredBinding, RoleTermLevels, IncrementBinding, RoleAnchor))
            and binding.member is not None
        ):
            result[f"{name}.member"] = binding.member
        if isinstance(binding, (RoleTermLevels, RuleClassLevels, RuleAnchor)):
            refs = binding.levels if isinstance(binding, RoleTermLevels) else binding.classes
            result.update({f"{name}.levels[{i}]": ref for i, ref in enumerate(refs)})
        if isinstance(binding, RoleAnchor):
            result[f"{name}.category"] = binding.category
        nested = (
            binding.roles
            if isinstance(binding, RoleLevels)
            else tuple(b for _, b in binding)
            if isinstance(binding, tuple)
            else ()
        )
        for i, item in enumerate(nested):
            if item.member is not None:
                result[f"{name}[{i}].member"] = item.member
    for i, binding in enumerate(measured_bindings(value)):
        aspect = binding.measure.observable.aspect
        if aspect is not None:
            result[f"measure[{i}].aspect"] = Referent(aspect.sort, aspect.term)
    result.update({f"control.conditioning[{i}]": ref for i, ref in enumerate(value.control.conditioning)})
    return result


def _check_interval(profile: ProfileSpec, value: IntervalRestriction) -> None:
    if value.convention is None:
        return
    unit = profile.units.get(value.unit)
    convention = profile.duration_conventions.get(value.convention)
    if unit is None or not unit.calendar or convention is None:
        raise ContrastRefused("interval convention must be declared and restrict a calendar unit")
    conversion = profile.conversions[convention.conversion]
    if value.unit not in (conversion.from_unit, conversion.to_unit):
        raise ContrastRefused("interval convention conversion must involve the interval unit")


def _check_shape(profile: ProfileSpec, value: Estimand, *, claim: Claim | None, authoring: bool) -> Estimand:
    decl = profile.functionals.get(value.functional)
    if decl is None or value.form not in SUPPORTED_ESTIMAND_FORMS or decl.declaration.form != value.form:
        raise EstimandError("form/functional mismatch")
    functional = decl.declaration
    if set(value.bindings) != _VARIABLES[value.form]:
        raise EstimandError("bindings must be exactly the form's variables")
    bindings = dict(value.bindings)
    for binding in bindings.values():
        sequence = (
            binding.levels
            if isinstance(binding, (RoleTermLevels, AxisLevels))
            else binding.classes
            if isinstance(binding, (RuleClassLevels, RuleAnchor))
            else binding.roles
            if isinstance(binding, RoleLevels)
            else binding.windows
            if isinstance(binding, LagBinding)
            else ()
        )
        if not isinstance(sequence, tuple):
            raise EstimandError("binding sequences must be immutable tuples")
    for key in ("response",):
        if key in bindings and not isinstance(bindings[key], MeasuredBinding):
            raise EstimandError(f"{key} is a measured binding")
    if value.form == "contrast":
        grouping = bindings["grouping"]
        if not isinstance(grouping, (RoleTermLevels, RuleClassLevels, RoleLevels, AxisLevels, IncrementBinding)):
            raise ContrastRefused("unsupported contrast grouping")
        if isinstance(grouping, IncrementBinding):
            if functional.increment != "linear" or finite(grouping.increment, "increment") <= 0:
                raise ContrastRefused("this functional requires a positive admitted increment")
            unit = profile.units.get(grouping.unit)
            if unit is None or unit.quantity_kind != grouping.measure.observable.quantity_kind:
                raise ContrastRefused("increment unit must have the grouping quantity kind")
            count = 2
        else:
            levels = (
                grouping.roles
                if isinstance(grouping, RoleLevels)
                else grouping.classes
                if isinstance(grouping, RuleClassLevels)
                else grouping.levels
            )
            count = len(levels)
            if (
                count < 2
                or len(
                    {
                        v1.encode(_binding_projection(x))
                        if isinstance(x, MeasuredBinding)
                        else v1.encode(restriction_projection(x))
                        if isinstance(x, IntervalRestriction)
                        else member_key(x)
                        for x in levels
                    }
                )
                != count
            ):
                raise ContrastRefused("levels must contain at least two distinct entries")
            if isinstance(grouping, RoleLevels) and count != 2:
                raise ContrastRefused("role-source grouping has exactly two measured roles")
            if isinstance(grouping, AxisLevels):
                for interval in grouping.levels:
                    _check_interval(profile, interval)
                response = bindings["response"]
                assert isinstance(response, MeasuredBinding)
                if any(
                    profile.units.get(x.unit) is None
                    or profile.units[x.unit].quantity_kind != response.measure.observable.quantity_kind
                    for x in grouping.levels
                ):
                    raise ContrastRefused("axis levels require response quantity-kind units")
        if functional.arity == "two" and count != 2:
            raise ContrastRefused("functional arity two requires exactly two levels")
    if value.form in {"association", "law-parameters"}:
        key = "variables" if value.form == "association" else "independent"
        rows = bindings[key]
        if (
            not isinstance(rows, tuple)
            or not rows
            or any(
                not isinstance(row, tuple)
                or len(row) != 2
                or not isinstance(row[0], str)
                or not row[0]
                or not isinstance(row[1], MeasuredBinding)
                for row in rows
            )
        ):
            raise EstimandError(f"{key} is a nonempty ordered named tuple of measured bindings")
        if len({name for name, _ in rows}) != len(rows):
            raise EstimandError("variable names must be unique")
        if value.form == "association":
            if len(rows) < 2 or (functional.arity == "two" and len(rows) != 2):
                raise EstimandError("association arity mismatch")
            if functional.exchange == "symmetric":
                bindings[key] = tuple(sorted(rows, key=lambda row: (v1.encode(_binding_projection(row[1])), row[0])))
    if value.form == "event-locked":
        anchor, lag = bindings["anchor"], bindings["lag"]
        if not isinstance(anchor, (RuleAnchor, RoleAnchor)) or not isinstance(lag, LagBinding):
            raise EstimandError("event-locked requires an anchor and lag")
        unit = profile.units.get(lag.unit)
        if unit is None or not unit.quantity_kind.endswith("/duration"):
            raise EstimandError("lag must use a duration unit")
        if lag.windows and (len(lag.windows) < 2 or (functional.arity == "two" and len(lag.windows) != 2)):
            raise EstimandError("event window arity mismatch")
        for interval in lag.windows:
            _check_interval(profile, interval)
        if any(w.unit != lag.unit for w in lag.windows):
            raise EstimandError("lag windows must use the binding's lag unit")
    if value.form == "enrichment":
        if (
            not isinstance(bindings["membership"], RoleBinding)
            or not isinstance(bindings["reference_set"], RoleBinding)
            or not isinstance(bindings["universe"], DatasetBinding)
        ):
            raise EstimandError("enrichment requires membership, reference-set and dataset bindings")
        membership = profile.template_of(profile.operator(value.operator)).roles.get(bindings["membership"].role)
        if membership is None or membership.arity != "many" or bindings["membership"].member is not None:
            raise EstimandError("enrichment membership names a whole many role")
        wire.address(bindings["universe"].digest, "sha256")
    normalized = _mint(
        **{
            field.name: bindings if field.name == "bindings" else getattr(value, field.name)
            for field in fields(Estimand)
        }
    )
    for binding in value.bindings.values():
        if isinstance(binding, (RoleBinding, MeasuredBinding, RoleTermLevels, IncrementBinding, RoleAnchor)):
            if value.form == "enrichment" and binding is value.bindings["membership"]:
                continue
            referent = _role(profile, value.operator, binding, claim)
            if isinstance(binding, RoleTermLevels) and any(
                ref.sort != (referent.sort if referent is not None else binding.levels[0].sort)
                for ref in binding.levels
            ):
                raise ContrastRefused("role-term levels use the bound role's sort")
            if isinstance(binding, RoleAnchor):
                sort = profile.sorts.get(binding.category.sort)
                if sort is None or "class" not in sort.categories:
                    raise ContrastRefused("an anchor role requires a class-category sort")
                if referent is not None and binding.category.sort != referent.sort:
                    raise ContrastRefused("anchor category must use the bound role's sort")
        elif isinstance(binding, RoleLevels):
            for role in binding.roles:
                _role(profile, value.operator, role, claim)
        elif isinstance(binding, tuple):
            for _, role in binding:
                _role(profile, value.operator, role, claim)
        elif isinstance(binding, (RuleClassLevels, RuleAnchor)):
            wire.address(binding.rule, "classification-rule")
            if (
                not binding.classes
                or len({member_key(r) for r in binding.classes}) != len(binding.classes)
                or len({r.sort for r in binding.classes}) != 1
            ):
                raise ContrastRefused("rule classes are distinct referents of one sort")
    for label, referent in estimand_referents(value).items():
        check_referent(profile, referent, label, world_kind=None, authoring=authoring)
    for binding in measured_bindings(value):
        check_measure(profile, binding.measure)
    control = value.control
    identification = profile.identification_classes.get(control.identification)
    if (
        identification is None
        or control.design not in profile.designs
        or control.selection not in profile.selection_mechanisms
    ):
        raise ControlRefused("control names declared identification, design and selection terms")
    if claim is not None and claim.layer not in identification.licenses_layers:
        raise IdentificationNotLicensed(f"{control.identification} does not license layer {claim.layer}")
    expected = (
        {name: (p.typing, p.domain) for name, p in functional.parameters.items()}
        if functional.parameters is not None
        else {"estimate": (functional.output, functional.domain)}
    )
    if set(value.outputs) != set(expected):
        raise EstimandError("output names must match the functional declaration")
    for name, output in value.outputs.items():
        if not isinstance(output, OutputSpec) or (output.typing, output.domain) != expected[name]:
            raise EstimandError("output typing and domain must match its declaration")
        if output.typing == "independent":
            if output.quantity_kind not in profile.quantity_kinds or (output.unit is None) == (output.scale is None):
                raise EstimandError("independent parameters require a quantity kind and unit xor scale")
            if output.unit is not None and (
                output.unit not in profile.units or profile.units[output.unit].quantity_kind != output.quantity_kind
            ):
                raise EstimandError("independent output unit has the wrong quantity kind")
            if output.scale is not None:
                wire.address(output.scale, "procedure")
        elif any(x is not None for x in (output.quantity_kind, output.unit, output.scale)):
            raise EstimandError("only independent parameters carry output coordinates")
    refs = value.reference if isinstance(value.reference, Mapping) else {"estimate": value.reference}
    if set(refs) != set(expected) or ((functional.output == "declared") != isinstance(value.reference, Mapping)):
        raise ReferenceRefused("references must match the functional outputs")
    for name, reference in refs.items():
        if isinstance(reference, ValueReference):
            if claim is not None and claim.form == "null":
                raise ReferenceRefused("null claims require regions")
            in_domain(reference.value, value.outputs[name].domain)
        elif isinstance(reference, NullReference):
            if claim is not None and claim.form != "null":
                raise ReferenceRefused("polar claims require value references")
            low, high = (
                in_domain(reference.low, value.outputs[name].domain),
                in_domain(reference.high, value.outputs[name].domain),
            )
            null = {"zero": Decimal(0), "one": Decimal(1), "half": Decimal("0.5")}.get(functional.null)
            if null is None or not low <= null <= high:
                raise ReferenceRefused("a null region must contain the functional's null value")
        else:
            raise ReferenceRefused("reference must be ValueReference or NullReference")
    if value.uncertainty not in SUPPORTED_UNCERTAINTY_KINDS or (
        value.uncertainty == "covariance" and len(value.outputs) < 2
    ):
        raise UncertaintyRefused("unsupported uncertainty representation for these outputs")
    for assumption in value.assumptions:
        check_instance(profile, assumption)
    return normalized


def admit_estimand(profile: ProfileSpec, estimand: Estimand, claim: Claim, *, authoring: bool) -> frozenset[str]:
    if estimand.claim != claim_identity(claim) or estimand.operator != claim.operator:
        raise EstimandNotAdmitted("estimand names a different claim")
    _check_shape(profile, estimand, claim=claim, authoring=authoring)
    assignment = {
        role: frozenset({value.sort}) if isinstance(value, Referent) else frozenset(m.referent.sort for m in value)
        for role, value in claim.roles.items()
        if role != "within-model"
    }
    admitting = profile.admitting(claim.operator, assignment, authoring=authoring)
    contracts = {
        decl.contract
        for decl in profile.estimand_declarations(claim.operator, admitting)
        if estimand.form in decl.forms and all(r.sort in decl.conditioning_sorts for r in estimand.control.conditioning)
    }
    if not contracts:
        raise EstimandNotAdmitted("no single admitting estimand declaration admits the complete value")
    return frozenset(contracts)


def build_estimand(
    profile: ProfileSpec,
    claim: Claim,
    *,
    form: str,
    functional: str,
    bindings: Mapping[str, Binding],
    outputs: Mapping[str, OutputSpec],
    reference: Reference | Mapping[str, Reference],
    control: Control,
    uncertainty: str,
    assumptions: tuple[AssumptionInstance, ...],
    calibration: str | None,
    applicability: Applicability,
    snapshot: ResolutionSnapshot,
    records: HeldRecords,
    assessment_dependency: Callable[[str], FrozenAssessmentDependency] | None = None,
) -> tuple[Estimand, BindingCheckReceipt]:
    applicability = check_applicability(profile, claim.operator, applicability.values, authoring=True)
    value = _mint(
        claim=claim_identity(claim),
        operator=claim.operator,
        form=form,
        functional=functional,
        bindings=bindings,
        outputs=outputs,
        reference=reference,
        control=control,
        uncertainty=uncertainty,
        assumptions=assumptions,
        calibration=calibration,
        dependencies=(),
    )
    value = _check_shape(profile, value, claim=claim, authoring=True)
    admit_estimand(profile, value, claim, authoring=True)
    gathered = list(assumptions)
    for binding in measured_bindings(value):
        referent = _role(profile, claim.operator, binding, claim)
        assert referent is not None
        check_referent(profile, referent, "measured role", world_kind=None, authoring=True)
        apt = check_aptness(
            profile,
            referent.sort,
            binding.measure,
            binding.mapping if isinstance(binding, MeasuredBinding) else None,
            binding.proxy if isinstance(binding, MeasuredBinding) else None,
            applicability.restrictions(),
            records,
            assessment_dependency=assessment_dependency,
        )
        gathered.extend(apt.assumptions)
    for binding in value.bindings.values():
        if isinstance(binding, (RuleClassLevels, RuleAnchor)):
            rule = read_record(records, binding.rule)
            if not isinstance(rule, ClassificationRule) or any(r.sort != rule.classes for r in binding.classes):
                raise ContrastRefused("held rule classes disagree with the bound classes sort")
        elif isinstance(binding, DatasetBinding) and not records.observation_held(binding.digest):
            raise EstimandError("enrichment universe dataset is not held")
    if calibration is not None:
        model = read_record(records, calibration)
        response = value.bindings.get("response")
        if (
            not isinstance(model, ProxyModel)
            or not isinstance(model.basis, Calibration)
            or not isinstance(response, MeasuredBinding)
        ):
            raise EstimandError("calibration must name a calibrated response proxy")
        response_ref = _role(profile, claim.operator, response, claim)
        assert response_ref is not None
        response_target = check_aptness(
            profile,
            response_ref.sort,
            response.measure,
            response.mapping,
            response.proxy,
            applicability.restrictions(),
            records,
            assessment_dependency=assessment_dependency,
        ).target_observable
        if model.target.observable != response_target:
            raise EstimandError("calibration proxy target does not match the response target")
        if not any(
            a.kind.endswith("/calibration-transfer") and a.particulars.get("proxy") == calibration for a in assumptions
        ):
            raise EstimandError("calibration requires its named transfer assumption")
    unique = {v1.encode(instance_projection(a)): a for a in gathered}
    deps = dependency_closure(binding_roots(value), records, profile, assessment_dependency=assessment_dependency)
    value = _mint(
        **{
            f.name: deps
            if f.name == "dependencies"
            else tuple(unique[k] for k in sorted(unique))
            if f.name == "assumptions"
            else getattr(value, f.name)
            for f in fields(Estimand)
        }
    )
    outcomes: dict[str, TermOutcome] = {}
    for label, ref in estimand_referents(value).items():
        outcome = snapshot.resolve(profile.sorts[ref.sort], ref.term)
        if outcome.refuses:
            raise UnboundReferent(f"{label}: the referenced term is not a member")
        outcomes["estimand:" + label] = outcome
    return value, _emit_receipt(value.claim, snapshot, outcomes)


def _ref_projection(ref: Referent) -> dict[str, str]:
    return {"sort": ref.sort, "term": ref.term}


def _role_projection(
    binding: RoleBinding | MeasuredBinding | RoleTermLevels | IncrementBinding | RoleAnchor,
) -> dict[str, object]:
    return {"role": binding.role, **({"member": _ref_projection(binding.member)} if binding.member is not None else {})}


def _binding_projection(binding: Binding) -> object:
    if isinstance(binding, tuple):
        return [{"name": name, "binding": _binding_projection(value)} for name, value in binding]
    if isinstance(binding, MeasuredBinding):
        return {
            **_role_projection(binding),
            "measure": measure_projection(binding.measure),
            **({"mapping": binding.mapping} if binding.mapping is not None else {}),
            **({"proxy": binding.proxy} if binding.proxy is not None else {}),
        }
    if isinstance(binding, IncrementBinding):
        return {
            **_role_projection(binding),
            "measure": measure_projection(binding.measure),
            "increment": {"value": binding.increment, "unit": binding.unit},
        }
    if isinstance(binding, RoleTermLevels):
        return {
            **_role_projection(binding),
            "levels": {"source": "role-terms", "levels": [_ref_projection(x) for x in binding.levels]},
        }
    if isinstance(binding, (RuleClassLevels, RuleAnchor)):
        return {
            "rule": binding.rule,
            "classes": [_ref_projection(x) for x in binding.classes],
            **({"source": "rule-classes"} if isinstance(binding, RuleClassLevels) else {}),
        }
    if isinstance(binding, RoleLevels):
        return {"source": "roles", "roles": [_binding_projection(x) for x in binding.roles]}
    if isinstance(binding, AxisLevels):
        return {"source": "axis", "levels": [restriction_projection(x) for x in binding.levels]}
    if isinstance(binding, RoleAnchor):
        return {**_role_projection(binding), "category": _ref_projection(binding.category)}
    if isinstance(binding, LagBinding):
        return {"unit": binding.unit, "windows": [restriction_projection(x) for x in binding.windows]}
    if isinstance(binding, DatasetBinding):
        return {"digest": binding.digest}
    return _role_projection(binding)


def reference_projection(value: Reference | Mapping[str, Reference]) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {name: reference_projection(ref) for name, ref in value.items()}
    if isinstance(value, ValueReference):
        return {"kind": "value", "value": value.value}
    return {"kind": "null", "region": {"low": value.low, "high": value.high}}


def estimand_projection(value: Estimand) -> dict[str, object]:
    return {
        "claim": value.claim,
        "operator": value.operator,
        "form": value.form,
        "functional": value.functional,
        "bindings": {name: _binding_projection(binding) for name, binding in value.bindings.items()},
        "outputs": {
            name: {f.name: getattr(output, f.name) for f in fields(OutputSpec) if getattr(output, f.name) is not None}
            for name, output in value.outputs.items()
        },
        "reference": reference_projection(value.reference),
        "control": {
            "identification": value.control.identification,
            "conditioning": [_ref_projection(x) for x in value.control.conditioning],
            "design": value.control.design,
            "selection": value.control.selection,
        },
        "uncertainty": value.uncertainty,
        "assumptions": [instance_projection(x) for x in value.assumptions],
        "dependencies": dependencies_projection(value.dependencies),
        **({"calibration": value.calibration} if value.calibration is not None else {}),
    }


def _read_ref(value: object) -> Referent:
    body = wire.shape(value, {"sort", "term"})
    return Referent(wire.term(body["sort"], "referent sort"), cast(str, body["term"]))


def _read_interval(value: object) -> IntervalRestriction:
    interval = restriction_from_projection(value, form="interval")
    assert isinstance(interval, IntervalRestriction)
    return interval


def _read_binding(value: object, variable: str) -> Binding:
    if variable in {"variables", "independent"}:

        def named(row: object) -> tuple[str, MeasuredBinding]:
            body = wire.shape(row, {"name", "binding"})
            binding = _read_binding(body["binding"], "response")
            assert isinstance(binding, MeasuredBinding)
            return wire.text(body["name"], "variable name"), binding

        return wire.sequence(value, named)
    if variable == "universe":
        body = wire.shape(value, {"digest"})
        return DatasetBinding(wire.address(body["digest"], "sha256"))
    if variable == "lag":
        body = wire.shape(value, {"unit", "windows"})
        return LagBinding(wire.term(body["unit"], "lag unit"), wire.sequence(body["windows"], _read_interval))
    if not isinstance(value, Mapping):
        raise MalformedRecord("binding must be a mapping")
    if "rule" in value:
        body = wire.shape(value, {"rule", "classes"}, {"source"} if variable == "grouping" else set())
        args = wire.address(body["rule"], "classification-rule"), wire.sequence(body["classes"], _read_ref)
        if variable == "grouping" and body.get("source") != "rule-classes":
            raise MalformedRecord("grouping rule source must be rule-classes")
        return RuleClassLevels(*args) if variable == "grouping" else RuleAnchor(*args)
    if value.get("source") == "roles":
        body = wire.shape(value, {"source", "roles"})
        roles = wire.sequence(body["roles"], lambda row: _read_binding(row, "response"))
        if len(roles) != 2 or not all(isinstance(r, MeasuredBinding) for r in roles):
            raise MalformedRecord("roles grouping requires two measured roles")
        return RoleLevels(cast(tuple[MeasuredBinding, MeasuredBinding], roles))
    if value.get("source") == "axis":
        body = wire.shape(value, {"source", "levels"})
        return AxisLevels(wire.sequence(body["levels"], _read_interval))
    required = {"role"}
    optional = {"member"}
    if variable == "response":
        required.add("measure")
        optional.update({"mapping", "proxy"})
    elif variable == "grouping":
        required.add("increment" if "increment" in value else "levels")
        if "increment" in value:
            required.add("measure")
    elif variable == "anchor":
        required.add("category")
    body = wire.shape(value, required, optional)
    role = wire.text(body["role"], "binding role")
    member = _read_ref(body["member"]) if "member" in body else None
    if variable == "response":
        return MeasuredBinding(
            role,
            member,
            measure_from_projection(body["measure"]),
            wire.address(body["mapping"], "referent-mapping") if "mapping" in body else None,
            wire.address(body["proxy"], "proxy-model") if "proxy" in body else None,
        )
    if variable == "grouping":
        if "increment" in body:
            increment = wire.shape(body["increment"], {"value", "unit"})
            return IncrementBinding(
                role,
                member,
                measure_from_projection(body["measure"]),
                finite(increment["value"], "increment"),
                wire.term(increment["unit"], "increment unit"),
            )
        levels = wire.shape(body["levels"], {"source", "levels"})
        if levels["source"] != "role-terms":
            raise MalformedRecord("role grouping levels require source role-terms")
        return RoleTermLevels(role, member, wire.sequence(levels["levels"], _read_ref))
    if variable == "anchor":
        return RoleAnchor(role, member, _read_ref(body["category"]))
    return RoleBinding(role, member)


def _read_reference(value: object, declared: bool) -> Reference | Mapping[str, Reference]:
    if declared:
        if not isinstance(value, Mapping):
            raise MalformedRecord("declared output references must be a map")
        return {wire.text(k, "output name"): cast(Reference, _read_reference(v, False)) for k, v in value.items()}
    if not isinstance(value, Mapping):
        raise MalformedRecord("reference must be a mapping")
    if value.get("kind") == "value":
        body = wire.shape(value, {"kind", "value"})
        return ValueReference(finite(body["value"], "reference"))
    body = wire.shape(value, {"kind", "region"})
    if body["kind"] != "null":
        raise MalformedRecord("unsupported reference kind")
    region = wire.shape(body["region"], {"low", "high"})
    return NullReference(finite(region["low"], "region low"), finite(region["high"], "region high"))


def estimand_from_stored(value: object, *, profile: ProfileSpec) -> Estimand:
    body = wire.shape(
        value,
        {
            "claim",
            "operator",
            "form",
            "functional",
            "bindings",
            "outputs",
            "reference",
            "control",
            "uncertainty",
            "assumptions",
            "dependencies",
        },
        {"calibration"},
    )
    if not isinstance(body["bindings"], Mapping) or not isinstance(body["outputs"], Mapping):
        raise MalformedRecord("bindings and outputs must be mappings")
    control = wire.shape(body["control"], {"identification", "conditioning", "design", "selection"})
    outputs = {}
    for name, raw in body["outputs"].items():
        fields_ = wire.shape(raw, {"typing", "domain"}, {"quantity_kind", "unit", "scale"})
        outputs[wire.text(name, "output name")] = OutputSpec(
            wire.text(fields_["typing"], "output typing"),
            wire.text(fields_["domain"], "output domain"),
            wire.term(fields_["quantity_kind"], "output quantity kind") if "quantity_kind" in fields_ else None,
            wire.term(fields_["unit"], "output unit") if "unit" in fields_ else None,
            wire.address(fields_["scale"], "procedure") if "scale" in fields_ else None,
        )
    functional = wire.term(body["functional"], "functional")
    decl = profile.functionals.get(functional)
    if decl is None:
        raise EstimandError("undeclared functional")
    result = _mint(
        claim=wire.text(body["claim"], "claim identity"),
        operator=wire.term(body["operator"], "operator"),
        form=wire.text(body["form"], "form"),
        functional=functional,
        bindings={wire.text(k, "variable"): _read_binding(v, k) for k, v in body["bindings"].items()},
        outputs=outputs,
        reference=_read_reference(body["reference"], decl.declaration.output == "declared"),
        control=Control(
            wire.term(control["identification"], "identification"),
            wire.sequence(control["conditioning"], _read_ref),
            wire.term(control["design"], "design"),
            wire.term(control["selection"], "selection"),
        ),
        uncertainty=wire.text(body["uncertainty"], "uncertainty"),
        assumptions=wire.sequence(body["assumptions"], instance_from_projection),
        calibration=wire.address(body["calibration"], "proxy-model") if "calibration" in body else None,
        dependencies=dependencies_from_projection(body["dependencies"]),
    )
    encoded_assumptions = [v1.encode(instance_projection(a)) for a in result.assumptions]
    if encoded_assumptions != sorted(set(encoded_assumptions)):
        raise MalformedRecord("stored assumptions must be sorted and distinct")
    result = _check_shape(profile, result, claim=None, authoring=False)
    if not set(binding_roots(result)) <= {e.id for e in result.dependencies}:
        raise MalformedRecord("estimand dropped a cited dependency")
    if estimand_projection(result) != value:
        raise MalformedRecord("stored estimand is not its canonical projection")
    return result


ESTIMAND_ERRORS = (EstimandError, UnboundReferent)
