"""The typed estimand (estimand-typing design §3, §7.1, §7.3).

`Estimand` is opaque and reachable only through `build_estimand`, which types
it against the **claim** it answers: the claim's operator fixes every sort
through the operator's `estimands:` declaration, and the claim's identity
enters the value so the estimand says which proposition it answers. Every
referent is resolved under D3's five outcomes; only `not-member` refuses.
Nothing here is read by `science.belief.v1`.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import final

from beliefs.claim import Claim, Qualifier, Referent
from beliefs.errors import (
    ContrastRefused,
    ControlRefused,
    EstimandError,
    EstimandFragmentRefused,
    EstimandSortMismatch,
    MeasureRefused,
    ReferenceRefused,
    UnboundReferent,
    UncertaintyRefused,
    UntypedEstimandMember,
)
from beliefs.profile import CompiledEstimandDecl, ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import BindingCheckReceipt, ReferentPosition, ResolutionSnapshot, TermOutcome, _emit_receipt
from beliefs.sealed import sealed

__all__ = [
    "ESTIMAND_ERRORS",
    "ContinuousContrast",
    "Control",
    "Estimand",
    "Interval",
    "LevelsContrast",
    "Measure",
    "StandardError",
    "applicability_projection",
    "build_applicability",
    "build_estimand",
    "check_estimate",
    "check_uncertainty",
    "co_scoped",
    "commensurable",
    "commensuration_key",
    "estimand_projection",
    "uncertainty_projection",
]

ESTIMAND_ERRORS = (EstimandError, UnboundReferent)


def _finite(value: object, where: str, error: type[EstimandError]) -> Decimal:
    if type(value) is not Decimal:
        raise error(f"{where}: expected a Decimal, found {type(value).__name__} — binary floats are refused at the boundary")
    if not value.is_finite():
        raise error(f"{where}: {value} is not finite")
    return value


def _require_slot(value: object) -> None:
    """An integer, never a bool and never a float: the decoder already refuses
    these on the wire, and the shared constructor refuses them for every route."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContrastRefused(f"contrast.slot is an integer slot index, found {value!r}")


@sealed
@final
@dataclass(frozen=True)
class LevelsContrast:
    slot: int
    baseline: Referent
    comparison: Referent

    def __post_init__(self) -> None:
        _require_slot(self.slot)
        for name in ("baseline", "comparison"):
            if not isinstance(getattr(self, name), Referent):
                raise UntypedEstimandMember(f"contrast.{name} holds {type(getattr(self, name)).__name__}, not a Referent")


@sealed
@final
@dataclass(frozen=True)
class ContinuousContrast:
    slot: int
    quantity: Referent
    increment: Decimal

    def __post_init__(self) -> None:
        _require_slot(self.slot)
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
    """Opaque: the only route in is `build_estimand` (M13's shape, one artifact over)."""

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
        declaration: CompiledEstimandDecl = profile.estimand(operator)
        arity = profile.operator(operator).arity
        grammar = profile.estimand_grammar
        if not isinstance(contrast, (LevelsContrast, ContinuousContrast)):
            raise UntypedEstimandMember(f"contrast holds {type(contrast).__name__}")
        if not (0 <= contrast.slot < arity):
            raise ContrastRefused(f"contrast: slot {contrast.slot} is outside Fin({arity}) for {operator!r}")
        if isinstance(contrast, LevelsContrast):
            level_sort = declaration.level_sorts.get(str(contrast.slot))
            if level_sort is None:
                raise ContrastRefused(f"contrast: slot {contrast.slot} of {operator!r} declares no level sort; only a continuous contrast is admitted there")
            for name in ("baseline", "comparison"):
                _require_sort(getattr(contrast, name), level_sort, f"contrast.{name}")
            if contrast.baseline.term == contrast.comparison.term:
                raise ContrastRefused("contrast: baseline and comparison must be distinct levels")
        else:
            _require_sort(contrast.quantity, declaration.measure_sort, "contrast.quantity")
        if not isinstance(measure, Measure):
            raise UntypedEstimandMember(f"measure holds {type(measure).__name__}")
        _require_sort(measure.quantity, declaration.measure_sort, "measure.quantity")
        if measure.scale not in grammar.scales:
            raise MeasureRefused(f"measure.scale {measure.scale!r} is outside the kernel's closed set {list(grammar.scales)}")
        reference = _finite(reference, "reference", ReferenceRefused)
        if measure.scale == "multiplicative" and reference <= 0:
            raise ReferenceRefused(f"reference must be > 0 under a multiplicative scale, found {reference}")
        if not isinstance(control, Control):
            raise UntypedEstimandMember(f"control holds {type(control).__name__}")
        _require_sort(control.identification, declaration.identification_sort, "control.identification")
        for index, member in enumerate(control.conditioning):
            _require_sort(member, declaration.conditioning_sort, f"control.conditioning[{index}]")
        estimand = object.__new__(cls)
        for name, value in (("claim", claim), ("operator", operator), ("contrast", contrast), ("measure", measure), ("reference", reference), ("control", control)):
            object.__setattr__(estimand, name, value)
        return estimand


def _require_sort(referent: Referent, sort: str, where: str) -> None:
    if referent.sort != sort:
        raise EstimandSortMismatch(
            f"{where} is declared {sort!r}; {referent.term!r} is of sort {referent.sort!r} — a term with no slot to occupy"
        )


def _referent_positions(estimand: Estimand) -> dict[str, Referent]:
    positions: dict[str, Referent] = {}
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


def _resolve_all(profile: ProfileSpec, snapshot: ResolutionSnapshot, positions: Mapping[str, Referent]) -> dict[str, TermOutcome]:
    outcomes = {label: snapshot.resolve(profile.sorts[referent.sort].vocabulary, referent.term) for label, referent in positions.items()}
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
    """Type an estimand against the claim it answers, resolve its referents, or refuse.

    `**richer` exists to be refused: a second measure, a second reference, a
    multi-arm contrast handed in under any keyword is outside the inhabited
    fragment (§3.3), and the refusal names it rather than flattening it."""
    if richer:
        raise EstimandFragmentRefused(
            f"the inhabited fragment admits one contrast on one slot, one measure, one reference, one identification and "
            f"one flat conditioning set; {sorted(richer)} is outside it and is refused, not flattened (estimand-typing §3.3)"
        )
    if not isinstance(claim, Claim):
        raise UntypedEstimandMember(f"an estimand is built against a Claim, found {type(claim).__name__}")
    if not isinstance(snapshot, ResolutionSnapshot):
        raise UntypedEstimandMember("snapshot is not a ResolutionSnapshot — availability is a parameter, never ambient")
    identity = claim_identity(claim)
    estimand = Estimand._checked(profile, claim=identity, operator=claim.operator, contrast=contrast, measure=measure, reference=reference, control=control)
    outcomes = _resolve_all(profile, snapshot, {ReferentPosition.estimand(part).label(): r for part, r in _referent_positions(estimand).items()})
    return estimand, _emit_receipt(identity, snapshot, outcomes)


def build_applicability(
    profile: ProfileSpec, claim: Claim, qualifiers: Mapping[str, Qualifier], *, snapshot: ResolutionSnapshot
) -> tuple[Mapping[str, Qualifier], BindingCheckReceipt]:
    """The claim grammar's flat fragment over the target operator's dimensions
    (§4): every check `Claim._checked` performs on a qualifier, performed here on
    the applicability map, then each restriction resolved."""
    if not isinstance(claim, Claim):
        raise UntypedEstimandMember(f"applicability is built against a Claim, found {type(claim).__name__}")
    polarity = None if claim.polarity == profile.claim_grammar.sign_inapt_tag else claim.polarity
    checked = Claim._checked(profile, operator=claim.operator, args=claim.args, qualifiers=qualifiers, polarity=polarity, layer=claim.layer)
    outcomes = _resolve_all(
        profile, snapshot, {ReferentPosition.restriction(d).label(): q.restriction for d, q in checked.qualifiers.items()}
    )
    return MappingProxyType(dict(checked.qualifiers)), _emit_receipt(claim_identity(claim), snapshot, outcomes)


def _referent(referent: Referent) -> dict[str, str]:
    return {"sort": referent.sort, "term": referent.term}


def estimand_projection(estimand: Estimand) -> dict[str, object]:
    """The canonical projection (§3.2): `claim`, `operator`, the contrast by kind,
    `measure`, `reference`, `control` with conditioning sorted. Decimals stay
    `Decimal`; identity v1 renders them canonically at encode."""
    contrast: dict[str, object] = {"slot": estimand.contrast.slot}
    if isinstance(estimand.contrast, LevelsContrast):
        contrast |= {"kind": "levels", "baseline": _referent(estimand.contrast.baseline), "comparison": _referent(estimand.contrast.comparison)}
    else:
        contrast |= {"kind": "continuous", "quantity": _referent(estimand.contrast.quantity), "increment": estimand.contrast.increment}
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


def commensuration_key(estimand: Estimand) -> dict[str, object]:
    """§7.3: the projection with `control.identification` removed — the design
    key a weight table reads is the one member outside the key."""
    projection = estimand_projection(estimand)
    control: dict[str, object] = dict(projection["control"])  # type: ignore[arg-type]
    del control["identification"]
    projection["control"] = control
    return projection


def commensurable(a: Estimand, b: Estimand) -> bool:
    return commensuration_key(a) == commensuration_key(b)


def co_scoped(a: Mapping[str, Qualifier], b: Mapping[str, Qualifier]) -> bool:
    """Canonical map equality over two applicability maps (M5's). Outside the
    estimand and outside `commensurable`; a successor policy reads both."""
    return applicability_projection(a) == applicability_projection(b)


def check_estimate(estimate: Decimal, scale: str) -> Decimal:
    estimate = _finite(estimate, "estimate", UncertaintyRefused)
    if scale == "multiplicative" and estimate <= 0:
        raise UncertaintyRefused(f"estimate must be > 0 under a multiplicative scale, found {estimate}")
    return estimate


def check_uncertainty(uncertainty: Interval | StandardError, estimate: Decimal, scale: str) -> None:
    """§6's one meaning per kind: a two-sided central interval at `level` around
    the estimate on its own scale; a standard error on the scale's additive form."""
    if isinstance(uncertainty, Interval):
        low, high, level = (_finite(getattr(uncertainty, n), f"uncertainty.{n}", UncertaintyRefused) for n in ("low", "high", "level"))
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
