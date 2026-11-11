"""The typed estimand.

`Estimand` is opaque. `Estimand._checked` types its **shape** against the
profile: the operator resolves, the contrast names one of the operator's
template's roles (and, for a `many` role, the member it contrasts), and every
referent has a declared sort. It establishes no admission. Admission is the
claim-aware step `admit_estimand` (R12): the estimand is admitted when some
estimand declaration of the claim's admitting set admits every field of it, and
the step returns those declarations' contracts. `build_estimand` is the
authoring route, through both; the stored readers (`decode_estimand`,
`estimand_from_stored`) restore shape only, and every consumer that needs
admission holds the claim and calls `admit_estimand`. `Estimand` carries no
declaration contracts. Every referent is resolved under its five outcomes; only
`not-member` refuses. Nothing here is read by `science.belief.v1`.
"""

# Interim role adaptation (beliefs-d64969); beliefs-f68a32 replaces the estimand structure around these names.

from __future__ import annotations

import itertools
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import cast, final

from beliefs.claim import Claim, Qualifier, Referent, check_referent, member_key
from beliefs.contract.base import SUPPORTED_CONTRAST_KINDS, SUPPORTED_SCALES, SUPPORTED_UNCERTAINTY_KINDS
from beliefs.errors import (
    ContrastRefused,
    ControlRefused,
    DimensionNotApplicabilitySide,
    EstimandError,
    EstimandFragmentRefused,
    EstimandNotAdmitted,
    EstimandSortMismatch,
    MeasureRefused,
    ReferenceRefused,
    RestrictionSortMismatch,
    UnboundReferent,
    UncertaintyRefused,
    UndeclaredDimension,
    UnknownQuantifier,
    UntypedEstimandMember,
    UntypedQualifier,
)
from beliefs.profile import CompiledEstimandDecl, ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import BindingCheckReceipt, ReferentPosition, ResolutionSnapshot, TermOutcome, _emit_receipt
from beliefs.sealed import sealed

__all__ = [
    "ESTIMAND_ERRORS",
    "SUPPORTED_CONTRAST_KINDS",
    "SUPPORTED_SCALES",
    "SUPPORTED_UNCERTAINTY_KINDS",
    "ContinuousContrast",
    "Control",
    "Estimand",
    "Interval",
    "LevelsContrast",
    "Measure",
    "StandardError",
    "admit_estimand",
    "applicability_projection",
    "build_applicability",
    "build_estimand",
    "check_estimate",
    "check_uncertainty",
    "co_scoped",
    "commensurable",
    "commensuration_key",
    "estimand_projection",
    "uncertainty_from_mapping",
    "uncertainty_projection",
]

ESTIMAND_ERRORS = (EstimandError, UnboundReferent)

_MANY = "many"
_APPLICABILITY_SIDE = "applicability"


def _finite(value: object, where: str, error: type[EstimandError]) -> Decimal:
    if type(value) is not Decimal:
        raise error(
            f"{where}: expected a Decimal, found {type(value).__name__} — binary floats are refused at the boundary"
        )
    if not value.is_finite():
        raise error(f"{where}: {value} is not finite")
    return value


def _require_role(role: object, member: object) -> None:
    """A role name, never an index; a member that is a `Referent` or absent. The
    decoder refuses other shapes on the wire, and the shared constructor refuses
    them for every route."""
    if not isinstance(role, str) or not role:
        raise ContrastRefused(f"contrast.role is a role name, found {role!r}")
    if member is not None and not isinstance(member, Referent):
        raise UntypedEstimandMember(f"contrast.member holds {type(member).__name__}, not a Referent")


@sealed
@final
@dataclass(frozen=True)
class LevelsContrast:
    """Two levels contrasted on one role of the claim. For a `many` role,
    `member` names the member of the role the contrast is on; for a `one` role it
    is `None`."""

    role: str
    member: Referent | None
    baseline: Referent
    comparison: Referent

    def __post_init__(self) -> None:
        _require_role(self.role, self.member)
        for name in ("baseline", "comparison"):
            if not isinstance(getattr(self, name), Referent):
                raise UntypedEstimandMember(
                    f"contrast.{name} holds {type(getattr(self, name)).__name__}, not a Referent"
                )


@sealed
@final
@dataclass(frozen=True)
class ContinuousContrast:
    """A continuous increment on one role of the claim; `member` as for `LevelsContrast`."""

    role: str
    member: Referent | None
    quantity: Referent
    increment: Decimal

    def __post_init__(self) -> None:
        _require_role(self.role, self.member)
        if not isinstance(self.quantity, Referent):
            raise UntypedEstimandMember(f"contrast.quantity holds {type(self.quantity).__name__}, not a Referent")
        if _finite(self.increment, "contrast.increment", ContrastRefused) <= 0:
            raise ContrastRefused(f"contrast.increment must be > 0, found {self.increment}")


@sealed
@final
@dataclass(frozen=True)
class Measure:
    quantity: Referent
    scale: str

    def __post_init__(self) -> None:
        if not isinstance(self.quantity, Referent):
            raise UntypedEstimandMember(f"measure.quantity holds {type(self.quantity).__name__}, not a Referent")


@sealed
@final
@dataclass(frozen=True)
class Control:
    identification: Referent
    conditioning: tuple[Referent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identification, Referent):
            raise UntypedEstimandMember("control.identification is not a Referent")
        if not all(isinstance(member, Referent) for member in self.conditioning):
            raise UntypedEstimandMember("control.conditioning holds a non-Referent")
        keyed = sorted(self.conditioning, key=lambda r: (r.sort, r.term))
        for earlier, later in itertools.pairwise(keyed):
            if earlier == later:
                raise ControlRefused(f"control.conditioning: duplicate member {later.term!r}")
        object.__setattr__(self, "conditioning", tuple(keyed))


@sealed
@final
@dataclass(frozen=True)
class Interval:
    low: Decimal
    high: Decimal
    level: Decimal


@sealed
@final
@dataclass(frozen=True)
class StandardError:
    value: Decimal


@sealed
@final
@dataclass(frozen=True, init=False)
class Estimand:
    """Opaque: the authoring route is `build_estimand`, and a stored one is
    restored by `decode_estimand` or `estimand_from_stored`. A value in hand is
    shape-checked; whether it is admitted for a claim is `admit_estimand`'s."""

    claim: str
    operator: str
    contrast: LevelsContrast | ContinuousContrast
    measure: Measure
    reference: Decimal
    control: Control

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise EstimandError("Estimand is validated at construction — use build_estimand(profile, claim, ...)")

    @classmethod
    def _checked(
        cls,
        profile: ProfileSpec,
        *,
        claim: str,
        operator: str,
        contrast: LevelsContrast | ContinuousContrast,
        measure: Measure,
        reference: Decimal,
        control: Control,
    ) -> Estimand:
        """Type the estimand's shape, or refuse: the operator resolves, the
        contrast's `role` is a role of the operator's template and `member` is
        present exactly when that role is `many`, and every referent's sort is a
        declared sort. No estimand declaration is read: that is admission, which
        needs the claim (`admit_estimand`)."""
        template = profile.template_of(profile.operator(operator))
        grammar = profile.estimand_grammar
        if not isinstance(contrast, (LevelsContrast, ContinuousContrast)):
            raise UntypedEstimandMember(f"contrast holds {type(contrast).__name__}")
        role = template.roles.get(contrast.role)
        if role is None:
            raise ContrastRefused(
                f"contrast: role {contrast.role!r} is not a role of {operator!r}; its roles are {sorted(template.roles)}"
            )
        if role.arity == _MANY and contrast.member is None:
            raise ContrastRefused(
                f"contrast: role {contrast.role!r} of {operator!r} is a `many` role, so the contrast names the "
                "member it is on"
            )
        if role.arity != _MANY and contrast.member is not None:
            raise ContrastRefused(
                f"contrast: role {contrast.role!r} of {operator!r} is a `one` role and takes no member"
            )
        if contrast.member is not None:
            _require_declared(profile, contrast.member, "contrast.member")
        if isinstance(contrast, LevelsContrast):
            for name in ("baseline", "comparison"):
                _require_declared(profile, getattr(contrast, name), f"contrast.{name}")
            if contrast.baseline.sort != contrast.comparison.sort:
                raise EstimandSortMismatch(
                    f"contrast: the baseline is of sort {contrast.baseline.sort!r} and the comparison of "
                    f"{contrast.comparison.sort!r}; two levels of one contrast share a sort"
                )
            if member_key(contrast.baseline) == member_key(contrast.comparison):
                raise ContrastRefused("contrast: baseline and comparison must be distinct levels")
        else:
            _require_declared(profile, contrast.quantity, "contrast.quantity")
        if not isinstance(measure, Measure):
            raise UntypedEstimandMember(f"measure holds {type(measure).__name__}")
        _require_declared(profile, measure.quantity, "measure.quantity")
        if measure.scale not in grammar.scales:
            raise MeasureRefused(
                f"measure.scale {measure.scale!r} is outside the kernel's closed set {list(grammar.scales)}"
            )
        reference = _finite(reference, "reference", ReferenceRefused)
        if measure.scale not in SUPPORTED_SCALES:
            raise MeasureRefused(f"scale {measure.scale!r} is not operable")
        if measure.scale == "multiplicative" and reference <= 0:
            raise ReferenceRefused(f"reference must be > 0 under a multiplicative scale, found {reference}")
        if not isinstance(control, Control):
            raise UntypedEstimandMember(f"control holds {type(control).__name__}")
        _require_declared(profile, control.identification, "control.identification")
        for index, member in enumerate(control.conditioning):
            _require_declared(profile, member, f"control.conditioning[{index}]")
        estimand = object.__new__(cls)
        for name, value in (
            ("claim", claim),
            ("operator", operator),
            ("contrast", contrast),
            ("measure", measure),
            ("reference", reference),
            ("control", control),
        ):
            object.__setattr__(estimand, name, value)
        return estimand


def _require_declared(profile: ProfileSpec, referent: Referent, where: str) -> None:
    if referent.sort not in profile.sorts:
        raise EstimandSortMismatch(
            f"{where}: {referent.term!r} is of sort {referent.sort!r}, which this profile does not declare — a "
            "term with no position to occupy"
        )


def admit_estimand(profile: ProfileSpec, estimand: Estimand, claim: Claim, *, authoring: bool) -> frozenset[str]:
    """The interim admission step (R12): admit `estimand` for `claim`, or refuse.

    The estimand must carry the claim's identity and operator (else
    `EstimandNotAdmitted`), and a `many`-role contrast's `member` must be a
    member of the claim's role by canonical member key (else `ContrastRefused`).
    The declarations read are the estimand declarations of the claim's own
    admitting set — `profile.admitting(operator, claim.assignment(), …)`, never
    every instantiation of the operator — with retired declarations excluded when
    `authoring`. The estimand is admitted when at least one of them admits
    **every** field (the contrast's level sorts, the measure, identification and
    conditioning sorts); fields are never combined across declarations. Returns
    the contracts of the declarations that do, which join the consulted set;
    refuses `EstimandNotAdmitted` when none does. The result reads the admission
    index, so it cannot depend on contract activation order."""
    if not isinstance(estimand, Estimand):
        raise UntypedEstimandMember(f"admission takes an Estimand, found {type(estimand).__name__}")
    if not isinstance(claim, Claim):
        raise UntypedEstimandMember(f"an estimand is admitted against a Claim, found {type(claim).__name__}")
    identity = claim_identity(claim)
    if estimand.claim != identity:
        raise EstimandNotAdmitted(f"the estimand answers claim {estimand.claim[:12]}…, not this claim {identity[:12]}…")
    if estimand.operator != claim.operator:
        raise EstimandNotAdmitted(
            f"the estimand's operator {estimand.operator!r} is not the claim's {claim.operator!r}"
        )
    contrast = estimand.contrast
    if contrast.member is not None:
        filling = claim.roles.get(contrast.role)
        members = filling if isinstance(filling, tuple) else ()
        if member_key(contrast.member) not in {member_key(m.referent) for m in members}:
            raise ContrastRefused(
                f"contrast: {contrast.member.term!r} of sort {contrast.member.sort!r} is not a member of the claim's "
                f"role {contrast.role!r}"
            )
    admitting = profile.admitting(claim.operator, claim.assignment(), authoring=authoring)
    declarations = profile.estimand_declarations(claim.operator, admitting)
    if not declarations:
        raise EstimandNotAdmitted(
            f"no declaration admitting this claim over {claim.operator!r} declares an estimand "
            f"(admitting: {list(admitting)}); an admitting declaration with none admits no estimand"
        )
    refusals = {declaration.target: _unadmitted(declaration, estimand) for declaration in declarations}
    admitted = frozenset(declaration.contract for declaration in declarations if not refusals[declaration.target])
    if not admitted:
        detail = "; ".join(f"{target} refuses {', '.join(fields)}" for target, fields in sorted(refusals.items()))
        raise EstimandNotAdmitted(
            f"no estimand declaration of the claim's admitting set admits the whole estimand ({detail}); fields "
            "are never combined across declarations"
        )
    return admitted


def _unadmitted(declaration: CompiledEstimandDecl, estimand: Estimand) -> tuple[str, ...]:
    """The positions of the estimand one declaration does not admit; empty when it admits every field."""
    refused: list[str] = []
    contrast = estimand.contrast
    if isinstance(contrast, LevelsContrast):
        level_sort = declaration.level_sorts.get(contrast.role)
        refused.extend(
            f"contrast.{name}"
            for name in ("baseline", "comparison")
            if level_sort is None or getattr(contrast, name).sort != level_sort
        )
    elif contrast.quantity.sort != declaration.measure_sort:
        refused.append("contrast.quantity")
    if estimand.measure.quantity.sort != declaration.measure_sort:
        refused.append("measure.quantity")
    if estimand.control.identification.sort != declaration.identification_sort:
        refused.append("control.identification")
    refused.extend(
        f"control.conditioning[{index}]"
        for index, member in enumerate(estimand.control.conditioning)
        if member.sort != declaration.conditioning_sort
    )
    return tuple(refused)


def _referent_positions(estimand: Estimand) -> dict[str, Referent]:
    positions: dict[str, Referent] = {}
    if estimand.contrast.member is not None:
        positions["contrast.member"] = estimand.contrast.member
    if isinstance(estimand.contrast, LevelsContrast):
        positions["contrast.baseline"] = estimand.contrast.baseline
        positions["contrast.comparison"] = estimand.contrast.comparison
    else:
        positions["contrast.quantity"] = estimand.contrast.quantity
    positions["measure.quantity"] = estimand.measure.quantity
    positions["control.identification"] = estimand.control.identification
    for index, member in enumerate(estimand.control.conditioning):
        positions[f"control.conditioning[{index}]"] = member
    return positions


def _resolve_all(
    profile: ProfileSpec, snapshot: ResolutionSnapshot, positions: Mapping[str, Referent]
) -> dict[str, TermOutcome]:
    outcomes = {
        label: snapshot.resolve(profile.sorts[referent.sort], referent.term) for label, referent in positions.items()
    }
    refused = sorted(label for label, outcome in outcomes.items() if outcome.refuses)
    if refused:
        raise UnboundReferent(
            f"{', '.join(refused)}: the term is not in the vocabulary its sort binds, and the vocabulary was read. Nothing was minted."
        )
    return outcomes


def build_estimand(
    profile: ProfileSpec,
    claim: Claim,
    *,
    contrast: LevelsContrast | ContinuousContrast,
    measure: Measure,
    reference: Decimal,
    control: Control,
    snapshot: ResolutionSnapshot,
    **richer: object,
) -> tuple[Estimand, BindingCheckReceipt]:
    """Type an estimand against the claim it answers, admit it, resolve its referents, or refuse.

    The shape check (`Estimand._checked`) comes first, then admission over the
    claim's authoring admitting set (`admit_estimand(…, authoring=True)`, retired
    declarations excluded), then resolution. `**richer` exists to be refused: a
    second measure, a second reference, a multi-arm contrast handed in under any
    keyword is outside the inhabited fragment, and the refusal names it rather
    than flattening it."""
    if richer:
        raise EstimandFragmentRefused(
            f"the inhabited fragment admits one contrast on one role, one measure, one reference, one identification and "
            f"one flat conditioning set; {sorted(richer)} is outside it and is refused, not flattened"
        )
    if not isinstance(claim, Claim):
        raise UntypedEstimandMember(f"an estimand is built against a Claim, found {type(claim).__name__}")
    if not isinstance(snapshot, ResolutionSnapshot):
        raise UntypedEstimandMember("snapshot is not a ResolutionSnapshot — availability is a parameter, never ambient")
    identity = claim_identity(claim)
    estimand = Estimand._checked(
        profile,
        claim=identity,
        operator=claim.operator,
        contrast=contrast,
        measure=measure,
        reference=reference,
        control=control,
    )
    admit_estimand(profile, estimand, claim, authoring=True)
    outcomes = _resolve_all(
        profile,
        snapshot,
        {ReferentPosition.estimand(part).label(): r for part, r in _referent_positions(estimand).items()},
    )
    return estimand, _emit_receipt(identity, snapshot, outcomes)


def _checked_applicability(
    profile: ProfileSpec, operator: str, qualifiers: Mapping[str, Qualifier]
) -> Mapping[str, Qualifier]:
    """Type an applicability map against the applicability-side dimensions whose
    `applies_to` names `operator`, or refuse. Shared by `build_applicability` and
    the stored reader, so the two cannot type one map two ways."""
    term = profile.operator(operator).term
    grammar = profile.claim_grammar
    if not isinstance(qualifiers, Mapping):
        raise UntypedQualifier(
            f"applicability is a mapping of dimension → Qualifier, found {type(qualifiers).__name__}"
        )
    for dimension, qualifier in qualifiers.items():
        if not isinstance(qualifier, Qualifier):
            raise UntypedQualifier(
                f"the applicability entry on {dimension!r} is {type(qualifier).__name__}, not a Qualifier"
            )
        declared = profile.dimensions.get(dimension)
        if declared is None:
            raise UndeclaredDimension(f"no dimension {dimension!r} in this profile.")
        if declared.placement != _APPLICABILITY_SIDE:
            raise DimensionNotApplicabilitySide(
                f"{dimension!r} is placed {declared.placement!r}: it says what a claim asserts, never where an "
                "estimate applies, so it is not an applicability restriction."
            )
        if term not in declared.applies_to:
            raise UndeclaredDimension(f"{dimension!r} does not apply to {operator!r}.")
        if qualifier.quantifier not in grammar.quantifiers:
            raise UnknownQuantifier(
                f"quantifier {qualifier.quantifier!r} on {dimension!r} is outside the kernel's closed set "
                f"{list(grammar.quantifiers)}."
            )
        if qualifier.restriction.sort != declared.restriction_sort:
            raise RestrictionSortMismatch(
                f"{dimension!r} restricts to sort {declared.restriction_sort!r}; "
                f"{qualifier.restriction.term!r} is of sort {qualifier.restriction.sort!r}."
            )
        check_referent(
            profile, qualifier.restriction, f"the restriction on {dimension!r}", world_kind=None, authoring=False
        )
    return MappingProxyType(dict(qualifiers))


def build_applicability(
    profile: ProfileSpec, claim: Claim, qualifiers: Mapping[str, Qualifier], *, snapshot: ResolutionSnapshot
) -> tuple[Mapping[str, Qualifier], BindingCheckReceipt]:
    """Type each restriction against an applicability-side dimension whose
    `applies_to` names the claim's operator, then resolve it. The claim is not
    re-typed: a claim-side dimension here refuses with
    `DimensionNotApplicabilitySide`, the converse of the claim's
    `DimensionNotClaimSide`."""
    if not isinstance(claim, Claim):
        raise UntypedEstimandMember(f"applicability is built against a Claim, found {type(claim).__name__}")
    checked = _checked_applicability(profile, claim.operator, qualifiers)
    outcomes = _resolve_all(
        profile,
        snapshot,
        {ReferentPosition.restriction(d).label(): q.restriction for d, q in checked.items()},
    )
    return checked, _emit_receipt(claim_identity(claim), snapshot, outcomes)


def _referent(referent: Referent) -> dict[str, str]:
    return {"sort": referent.sort, "term": referent.term}


def estimand_projection(estimand: Estimand) -> dict[str, object]:
    """The canonical projection: `claim`, `operator`, the contrast by kind with
    its `role` and, for a `many` role, its `member` (absent otherwise, never
    null), `measure`, `reference`, `control` with conditioning sorted. Decimals
    stay `Decimal`; identity v1 renders them canonically at encode."""
    contrast: dict[str, object] = {"role": estimand.contrast.role}
    if estimand.contrast.member is not None:
        contrast["member"] = _referent(estimand.contrast.member)
    if isinstance(estimand.contrast, LevelsContrast):
        contrast |= {
            "kind": "levels",
            "baseline": _referent(estimand.contrast.baseline),
            "comparison": _referent(estimand.contrast.comparison),
        }
    else:
        contrast |= {
            "kind": "continuous",
            "quantity": _referent(estimand.contrast.quantity),
            "increment": estimand.contrast.increment,
        }
    return {
        "claim": estimand.claim,
        "operator": estimand.operator,
        "contrast": contrast,
        "measure": {"quantity": _referent(estimand.measure.quantity), "scale": estimand.measure.scale},
        "reference": estimand.reference,
        "control": {
            "identification": _referent(estimand.control.identification),
            "conditioning": [_referent(member) for member in estimand.control.conditioning],
        },
    }


def applicability_projection(qualifiers: Mapping[str, Qualifier]) -> dict[str, object]:
    return {
        dimension: {"quantifier": q.quantifier, "restriction": _referent(q.restriction)}
        for dimension, q in sorted(qualifiers.items())
    }


def uncertainty_projection(uncertainty: Interval | StandardError) -> dict[str, object]:
    if isinstance(uncertainty, Interval):
        return {"kind": "interval", "low": uncertainty.low, "high": uncertainty.high, "level": uncertainty.level}
    return {"kind": "standard-error", "value": uncertainty.value}


def uncertainty_from_mapping(mapping: object, *, estimate: Decimal | None, scale: str) -> Interval | StandardError:
    """`uncertainty_projection`'s inverse, checked: decode a `{"kind": …}`
    body — a rule's raw output or a stored record's restored `typed` member —
    into an `Interval` or a `StandardError`, then run `check_uncertainty`
    against the estimate it accompanies and the estimand's scale. The one
    decoder both `assess.build_assessment` and `stored.assessment_value` call,
    so the derivation and the stored reader can never decode the same body two
    different ways. Raises `UncertaintyRefused` throughout; each caller
    translates it into its own error."""
    if not isinstance(mapping, Mapping):
        raise UncertaintyRefused(f"uncertainty is a mapping with a kind, found {type(mapping).__name__}")
    kind = mapping.get("kind")
    if kind == "interval" and set(mapping) == {"kind", "low", "high", "level"}:
        uncertainty: Interval | StandardError = Interval(
            low=cast(Decimal, mapping["low"]),
            high=cast(Decimal, mapping["high"]),
            level=cast(Decimal, mapping["level"]),
        )
    elif kind == "standard-error" and set(mapping) == {"kind", "value"}:
        uncertainty = StandardError(value=cast(Decimal, mapping["value"]))
    else:
        raise UncertaintyRefused(
            f"uncertainty kind {kind!r} with members {sorted(mapping)} is neither interval nor standard-error"
        )
    if estimate is None:
        raise UncertaintyRefused("an uncertainty with no estimate to be uncertain about")
    check_uncertainty(uncertainty, estimate, scale)
    return uncertainty


def commensuration_key(estimand: Estimand) -> dict[str, object]:
    """The projection with `control.identification` removed: the commensuration
    key a weight table reads. `identification` is the one member outside it."""
    projection = estimand_projection(estimand)
    control: dict[str, object] = dict(projection["control"])  # type: ignore[arg-type]
    del control["identification"]
    projection["control"] = control
    return projection


def commensurable(a: Estimand, b: Estimand) -> bool:
    return commensuration_key(a) == commensuration_key(b)


def co_scoped(a: Mapping[str, Qualifier], b: Mapping[str, Qualifier]) -> bool:
    """Canonical map equality over two applicability maps. Outside the
    estimand and outside `commensurable`; a successor policy reads both."""
    return applicability_projection(a) == applicability_projection(b)


def check_estimate(estimate: Decimal, scale: str) -> Decimal:
    if scale not in SUPPORTED_SCALES:
        raise UncertaintyRefused(f"scale {scale!r} is not operable")
    estimate = _finite(estimate, "estimate", UncertaintyRefused)
    if scale == "multiplicative" and estimate <= 0:
        raise UncertaintyRefused(f"estimate must be > 0 under a multiplicative scale, found {estimate}")
    return estimate


def check_uncertainty(uncertainty: Interval | StandardError, estimate: Decimal, scale: str) -> None:
    """One meaning per kind: a two-sided central interval at `level` around
    the estimate on its own scale; a standard error on the scale's additive form."""
    if scale not in SUPPORTED_SCALES:
        raise UncertaintyRefused(f"scale {scale!r} is not operable")
    if isinstance(uncertainty, Interval):
        low, high, level = (
            _finite(getattr(uncertainty, n), f"uncertainty.{n}", UncertaintyRefused) for n in ("low", "high", "level")
        )
        if not (low <= estimate <= high):
            raise UncertaintyRefused(f"uncertainty: the interval [{low}, {high}] excludes the estimate {estimate}")
        if not (0 < level < 1):
            raise UncertaintyRefused(f"uncertainty.level must lie in (0, 1), found {level}")
        if scale == "multiplicative" and low <= 0:
            raise UncertaintyRefused(f"uncertainty.low must be > 0 under a multiplicative scale, found {low}")
        return
    if isinstance(uncertainty, StandardError):
        if _finite(uncertainty.value, "uncertainty.value", UncertaintyRefused) < 0:
            raise UncertaintyRefused(f"a standard error is non-negative, found {uncertainty.value}")
        return
    raise UncertaintyRefused(f"uncertainty holds {type(uncertainty).__name__}, not Interval or StandardError")
