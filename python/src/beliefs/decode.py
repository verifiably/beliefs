"""`decode_claim` — the boundary M₀ never stated.

```text
decodeClaim :  WireClaim × ProfileSpec × ResolutionSnapshot
               ──▶  (Claim × BindingCheckReceipt) + Refused
```

**Unconstructibility eliminates the internal guard; it does not eliminate the
boundary** (§6.3). Serialized YAML, an imported record, a restored corpus and a
raw write can all *express* a combination the type cannot hold, so the type's
guarantee and this boundary's are different laws at different places. Every
import, deserialization and restore comes through here.

**Three parameters, and the third is the one that makes it a function.** With
only a wire value and a profile, the decision would still depend on which
vocabularies happen to be readable — ambient state, so two holders could decode
identical bytes differently and nothing could adjudicate. `ResolutionSnapshot`
moves that into the signature. `Refused` is spelled as an exception here, which
is the sum's refusing arm: it returns no claim, and therefore no receipt.

**Retirement is not enforced here, deliberately** (§7.3a). This function sees
wire bytes and cannot tell a claim being authored now from a historical one being
restored from a backup, re-imported, or replayed from the mutation log. Refusing
a retired identifier would make every corpus holding a prior claim
un-restorable — corrupting exactly the history retirement exists to preserve. So
`build_claim` refuses withdrawn identifiers and this route does not, and that is
the only respect in which the two differ.

**`WireClaim` does not leave this module.** M13's second clause: no function
downstream of the boundary accepts one, because a downstream signature that did
would let unchecked data past the single place that checks it. The test for that
walks the package's own signatures rather than grepping for the name.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from nodes.core.node import Node

from beliefs.claim import Claim, Qualifier, Referent
from beliefs.errors import (
    ArityMismatch,
    MalformedWireClaim,
    MalformedWireEstimand,
    RestrictionSortMismatch,
    UnboundReferent,
    UndeclaredDimension,
    UnknownQuantifier,
)
from beliefs.estimand import ContinuousContrast, Control, Estimand, LevelsContrast, Measure
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import (
    BindingCheckReceipt,
    ReferentPosition,
    ResolutionSnapshot,
    TermOutcome,
    _emit_receipt,
)

__all__ = [
    "WireClaim",
    "WireEstimand",
    "applicability_from_stored",
    "claim_from_stored",
    "decode_claim",
    "decode_estimand",
    "estimand_from_stored",
    "stored_claim_terms",
]


@dataclass(frozen=True)
class WireClaim:
    """A claim as it arrives: identifiers and tags, and nothing typed.

    It mirrors `π_claim`'s shape (§6.5) because that is what a serialized claim
    is — and note what it does **not** carry: an argument's **sort**. The
    projection emits terms only, and the sort is recovered here from the
    operator's declaration. That asymmetry is the point of the boundary. On the
    wire a term is a bare string with nothing to check it against; inside, a
    `Referent` carries its sort and a bare string cannot occupy a slot at all.

    Freely constructible, and it must be: it models untrusted input, so a
    validated constructor here would be validating the wrong thing at the wrong
    place. Its fields are typed for readers only — every one of them is checked
    below on the assumption that the annotations are a wish.
    """

    operator: str
    args: Sequence[str]
    qualifiers: Mapping[str, Mapping[str, str]]
    polarity: str
    layer: str


def _require_text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise MalformedWireClaim(f"{where}: expected a non-empty identifier, found {value!r}")
    return value


def _require_snapshot(snapshot: object, error: type[MalformedWireClaim | MalformedWireEstimand]) -> None:
    """`decode_claim`'s and `decode_estimand`'s shared authentication check
    (§7.2): availability is a parameter, never ambient, so a decoder that
    supplied its own snapshot would decide by ambient state and two holders
    could read identical bytes differently."""
    if not isinstance(snapshot, ResolutionSnapshot):
        raise error(
            f"snapshot is a {type(snapshot).__name__}, not a ResolutionSnapshot — use build_snapshot(...). "
            "Availability is a parameter (§7.2); a decoder that supplied its own would decide by ambient "
            "state, and two holders would read the same bytes differently."
        )


def _wire_parts(wire: WireClaim) -> tuple[str, Sequence[str], Mapping[str, Mapping[str, str]], str, str]:
    """Check the wire value's own shape, before anything is resolved against a profile.

    This is not the profile-dependent typing — that is `Claim._checked`'s, and it
    stays there. This is the narrower question of whether the value has the shape
    a wire claim has at all, which has to be settled first because the typing
    below indexes into it.
    """
    if not isinstance(wire, WireClaim):
        raise MalformedWireClaim(
            f"decode_claim takes a WireClaim, found {type(wire).__name__}. The wire type is what marks a value "
            "as unchecked; accepting anything shaped like one would make the mark meaningless."
        )
    operator = _require_text(wire.operator, "operator")
    if isinstance(wire.args, str) or not isinstance(wire.args, Sequence):
        raise MalformedWireClaim(f"args: expected a sequence of term identifiers, found {wire.args!r}")
    args = tuple(_require_text(term, f"args[{index}]") for index, term in enumerate(wire.args))
    if not isinstance(wire.qualifiers, Mapping):
        raise MalformedWireClaim(f"qualifiers: expected a mapping, found {wire.qualifiers!r}")
    qualifiers: dict[str, Mapping[str, str]] = {}
    for dimension, body in wire.qualifiers.items():
        where = f"qualifiers[{dimension!r}]"
        _require_text(dimension, "a qualifier dimension")
        if not isinstance(body, Mapping):
            raise MalformedWireClaim(f"{where}: expected a mapping, found {body!r}")
        # Before the field arithmetic, not after: `set(body) - {...}` over a
        # non-string key sorts and joins values that are not strings, and the
        # `TypeError` that comes out is not a `DecodeError` — so a caller holding
        # this boundary's refusing arm sees a crash instead of a refusal, on
        # input that is exactly what this function exists to refuse. The contract
        # loaders check mapping keys for the same reason before their own
        # `_fields`; this is that guard, at the boundary that had skipped it.
        for field in body:
            _require_text(field, f"{where}: a qualifier field name")
        unknown = sorted(set(body) - {"quantifier", "restriction"})
        if unknown:
            raise MalformedWireClaim(f"{where}: unknown field(s) {', '.join(unknown)}; refused, never ignored")
        missing = sorted({"quantifier", "restriction"} - set(body))
        if missing:
            raise MalformedWireClaim(f"{where}: missing field(s) {', '.join(missing)}")
        qualifiers[dimension] = {
            "quantifier": _require_text(body["quantifier"], f"{where}.quantifier"),
            "restriction": _require_text(body["restriction"], f"{where}.restriction"),
        }
    return operator, args, qualifiers, _require_text(wire.polarity, "polarity"), _require_text(wire.layer, "layer")


def decode_claim(
    wire: WireClaim, *, profile: ProfileSpec, snapshot: ResolutionSnapshot
) -> tuple[Claim, BindingCheckReceipt]:
    """Type a wire claim against a profile and resolve its referents, or refuse.

    Order is load-bearing. Typing happens first because a referent cannot be
    resolved before its **sort** is known, and the sort comes from the operator's
    declaration. Resolution happens second, and a `not-member` anywhere refuses
    the whole decode: nothing is returned, and the receipt — which exists to
    record checks that *were* performed — is never emitted on that arm.
    """
    if not isinstance(profile, ProfileSpec):
        raise MalformedWireClaim(
            f"profile is a {type(profile).__name__}, not a compiled ProfileSpec — use compile_profile(base, domains)."
        )
    _require_snapshot(snapshot, MalformedWireClaim)
    operator, terms, qualifier_bodies, polarity, layer = _wire_parts(wire)
    declaration = profile.operator(operator)

    # Pairing terms with sorts requires equal counts, so the mismatch has to be
    # caught before the zip rather than by it. `Claim._checked` remains the
    # authority on arity; this is the same refusal raised where the pairing
    # happens, not a second opinion about validity.
    if len(terms) != declaration.arity:
        raise ArityMismatch(
            f"{operator!r} has arity {declaration.arity}; the wire claim carries {len(terms)} argument(s)."
        )
    args = tuple(Referent(sort=sort, term=term) for term, sort in zip(terms, declaration.arg_sorts, strict=True))

    qualifiers: dict[str, Qualifier] = {}
    for dimension, body in qualifier_bodies.items():
        declared = profile.dimensions.get(dimension)
        if declared is None:
            # As with arity: the restriction's sort is read off the dimension, so
            # an undeclared one cannot be built into a `Qualifier` at all.
            raise UndeclaredDimension(
                f"no dimension {dimension!r} in this profile; Dims(op) is declared per operator (§6.2)."
            )
        qualifiers[dimension] = Qualifier(
            quantifier=body["quantifier"],
            restriction=Referent(sort=declared.restriction_sort, term=body["restriction"]),
        )

    # Every profile-dependent check, at the one place that performs them, and the
    # same one the authoring route uses — minus retirement, which is authoring's.
    claim = Claim._checked(
        profile,
        operator=operator,
        args=args,
        qualifiers=qualifiers,
        polarity=None if polarity == profile.claim_grammar.sign_inapt_tag else polarity,
        layer=layer,
    )

    outcomes: dict[str, TermOutcome] = {}
    for slot, referent in enumerate(claim.args):
        outcomes[ReferentPosition.argument(slot).label()] = _resolve(profile, snapshot, referent)
    for dimension, qualifier in claim.qualifiers.items():
        outcomes[ReferentPosition.restriction(dimension).label()] = _resolve(profile, snapshot, qualifier.restriction)

    refused = sorted(label for label, outcome in outcomes.items() if outcome.refuses)
    if refused:
        raise UnboundReferent(
            f"{', '.join(refused)}: the term is not in the vocabulary its sort binds, and the vocabulary "
            "was read — this is a finding, not an unconsulted binding. Admitting it would put an unbindable "
            "identifier into an immutable claim identity (§7.2). Nothing was minted."
        )

    return claim, _emit_receipt(claim_identity(claim), snapshot, outcomes)


def _resolve(profile: ProfileSpec, snapshot: ResolutionSnapshot, referent: Referent) -> TermOutcome:
    return snapshot.resolve(profile.sorts[referent.sort].vocabulary, referent.term)


_STORED_CLAIM_KEYS = frozenset({"operator", "args", "qualifiers", "polarity", "layer"})


def _stored_wire(node: Node) -> WireClaim:
    """Read and validate the covered claim facet into the private wire shape."""
    if not isinstance(node, Node) or node.kind != "proposition":
        raise MalformedWireClaim(f"stored claim reads a proposition node, found {type(node).__name__}")
    facet = node.facets.get("proposition")
    if not isinstance(facet, Mapping):
        raise MalformedWireClaim(f"{node.id}: no covered claim facet")
    keys = set(facet)
    if keys != _STORED_CLAIM_KEYS:
        missing, extra = sorted(_STORED_CLAIM_KEYS - keys), sorted(keys - _STORED_CLAIM_KEYS)
        raise MalformedWireClaim(f"{node.id}: claim facet missing {missing}, extra {extra}; refused, never repaired")
    if isinstance(facet["args"], str) or not isinstance(facet["args"], Sequence):
        raise MalformedWireClaim(f"{node.id}: args is not a sequence")
    if not isinstance(facet["qualifiers"], Mapping):
        raise MalformedWireClaim(f"{node.id}: qualifiers is not a mapping")
    wire = WireClaim(
        operator=facet["operator"],
        args=tuple(facet["args"]),
        qualifiers=facet["qualifiers"],
        polarity=facet["polarity"],
        layer=facet["layer"],
    )
    return wire


def stored_claim_terms(node: Node) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Read stored argument and qualifier restriction terms after shape validation."""
    _operator, args, qualifier_bodies, _polarity, _layer = _wire_parts(_stored_wire(node))
    return tuple(args), tuple(body["restriction"] for body in qualifier_bodies.values())


def claim_from_stored(node: Node, *, profile: ProfileSpec, snapshot: ResolutionSnapshot) -> tuple[Claim, BindingCheckReceipt]:
    """Restore a `Claim` from a stored proposition's covered claim facet.

    The wire value is built **here** and consumed **here** — `WireClaim` still
    never leaves this module (M13) — and typing is delegated to `decode_claim`
    rather than duplicated, so the check still happens once, in one place. The
    same is true one level down: a qualifier body's own shape (missing or
    unknown fields) is `_wire_parts`' check, not a second copy of it, so it is
    called here — its return discarded — before `decode_claim`, rather than
    left for `decode_claim` to reach on its own. Every ill-formed input
    refuses **before** delegation, with nothing minted and no `KeyError` or
    `AttributeError` on the way in (M11): a restore helper is exactly where
    "be liberal in what you accept" would defeat the row.
    """
    wire = _stored_wire(node)
    _wire_parts(wire)
    return decode_claim(wire, profile=profile, snapshot=snapshot)


# --- Estimands (estimand-typing §7.2) --------------------------------------
#
# `decode_estimand` mirrors `decode_claim`'s discipline one artifact over: type
# first, against the operator's `estimands:` declaration, then resolve. But the
# restoration route differs from `claim_from_stored`'s in the one respect §7.2
# calls out: `estimand_from_stored` performs **no resolution at all**, because a
# stored spec was typed against the declarations and membership was the
# freeze's own check, not something a reader repeats. Retirement is unenforced
# on every route here, for `decode_claim`'s reason: a decoder cannot tell
# authoring from restoration.

_WIRE_ESTIMAND_KEYS = frozenset({"claim", "operator", "contrast", "measure", "reference", "control"})


def _require_estimand_text(value: object, where: str) -> str:
    """`_require_text` translated to this boundary's own error: the claim
    decoder's `MalformedWireClaim` names the wrong artifact for a caller
    holding the estimand decoder's refusing arm."""
    try:
        return _require_text(value, where)
    except MalformedWireClaim as refused:
        raise MalformedWireEstimand(str(refused)) from refused


@dataclass(frozen=True)
class WireEstimand:
    """An estimand as it arrives — identifiers, tags and decimals, nothing typed.
    Freely constructible for `WireClaim`'s reason; every field is checked below."""

    claim: str
    operator: str
    contrast: Mapping[str, object]
    measure: Mapping[str, object]
    reference: object
    control: Mapping[str, object]


def _wire_referent(value: object, where: str, *, declared: str, stored: bool) -> Referent:
    """A referent in one of two forms, and the route decides which is admitted.

    The **bare-term** form carries a term only and takes the declaration's sort;
    it is the wire form, admitted by `decode_estimand` and nowhere else. The
    **stored** form is exactly `{sort, term}` with a non-empty string sort,
    passed through unchanged so that `Estimand._checked` refuses a sort that is
    not the declared one. On a stored route (`stored=True`) a bare term is
    refused outright: substituting the declaration's sort for a wrapper that is
    missing, empty, non-string or absent altogether would repair a malformed
    record on the way in, which is the one thing a decoder must not do."""
    if isinstance(value, Mapping):
        if set(value) != {"sort", "term"}:
            raise MalformedWireEstimand(f"{where}: a stored referent is exactly {{sort, term}}")
        return Referent(sort=_require_estimand_text(value["sort"], f"{where}.sort"), term=_require_estimand_text(value["term"], f"{where}.term"))
    if stored:
        raise MalformedWireEstimand(f"{where}: a stored referent is exactly {{sort, term}}; a bare term is the wire form's, never a record's")
    return Referent(sort=declared, term=_require_estimand_text(value, where))


def _decimal(value: object, where: str) -> Decimal:
    if type(value) is not Decimal:
        raise MalformedWireEstimand(f"{where}: expected a Decimal, found {type(value).__name__}")
    return value


def _slot(value: object, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MalformedWireEstimand(f"{where}: slot is an integer, found {value!r}")
    return value


def _mapping_body(value: object, where: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise MalformedWireEstimand(f"{where}: expected a mapping, found {type(value).__name__}")
    for key in value:
        _require_estimand_text(key, f"{where}: a member name")
    return value


def _exact_keys(body: Mapping[str, object], keys: set[str], where: str) -> None:
    if set(body) != keys:
        raise MalformedWireEstimand(f"{where}: members are exactly {sorted(keys)}, found {sorted(body)}; refused, never repaired")


def _typed_estimand(wire: WireEstimand, profile: ProfileSpec, *, stored: bool) -> Estimand:
    if not isinstance(wire, WireEstimand):
        raise MalformedWireEstimand(f"decode_estimand takes a WireEstimand, found {type(wire).__name__}")
    claim = _require_estimand_text(wire.claim, "claim")
    operator = _require_estimand_text(wire.operator, "operator")
    declaration = profile.estimand(operator)
    contrast_body, measure_body, control_body = (
        _mapping_body(getattr(wire, name), name) for name in ("contrast", "measure", "control")
    )
    kind = _require_estimand_text(contrast_body.get("kind"), "contrast.kind")
    if kind not in profile.estimand_grammar.contrast_kinds:
        raise MalformedWireEstimand(f"contrast.kind {kind!r} is outside {list(profile.estimand_grammar.contrast_kinds)}")
    slot = _slot(contrast_body.get("slot"), "contrast.slot")
    if kind == "levels":
        _exact_keys(contrast_body, {"slot", "kind", "baseline", "comparison"}, "contrast")
        level_sort = declaration.level_sorts.get(str(slot), "")
        contrast: LevelsContrast | ContinuousContrast = LevelsContrast(
            slot=slot,
            baseline=_wire_referent(contrast_body["baseline"], "contrast.baseline", declared=level_sort, stored=stored),
            comparison=_wire_referent(contrast_body["comparison"], "contrast.comparison", declared=level_sort, stored=stored),
        )
    else:
        _exact_keys(contrast_body, {"slot", "kind", "quantity", "increment"}, "contrast")
        contrast = ContinuousContrast(
            slot=slot,
            quantity=_wire_referent(contrast_body["quantity"], "contrast.quantity", declared=declaration.measure_sort, stored=stored),
            increment=_decimal(contrast_body["increment"], "contrast.increment"),
        )
    _exact_keys(measure_body, {"quantity", "scale"}, "measure")
    measure = Measure(
        quantity=_wire_referent(measure_body["quantity"], "measure.quantity", declared=declaration.measure_sort, stored=stored),
        scale=_require_estimand_text(measure_body["scale"], "measure.scale"),
    )
    _exact_keys(control_body, {"identification", "conditioning"}, "control")
    conditioning = control_body["conditioning"]
    if isinstance(conditioning, (str, bytes)) or not isinstance(conditioning, Sequence):
        raise MalformedWireEstimand("control.conditioning is a sequence of referents")
    control = Control(
        identification=_wire_referent(control_body["identification"], "control.identification", declared=declaration.identification_sort, stored=stored),
        conditioning=tuple(
            _wire_referent(member, f"control.conditioning[{i}]", declared=declaration.conditioning_sort, stored=stored)
            for i, member in enumerate(conditioning)
        ),
    )
    return Estimand._checked(
        profile, claim=claim, operator=operator, contrast=contrast, measure=measure,
        reference=_decimal(wire.reference, "reference"), control=control,
    )


def decode_estimand(
    wire: WireEstimand, *, profile: ProfileSpec, snapshot: ResolutionSnapshot
) -> tuple[Estimand, BindingCheckReceipt]:
    """Type and resolve a wire estimand, or refuse — `decode_claim`'s discipline."""
    from beliefs.estimand import _referent_positions, _resolve_all

    if not isinstance(profile, ProfileSpec):
        raise MalformedWireEstimand(f"profile is a {type(profile).__name__}, not a compiled ProfileSpec — use compile_profile(base, domains).")
    _require_snapshot(snapshot, MalformedWireEstimand)
    estimand = _typed_estimand(wire, profile, stored=False)
    outcomes = _resolve_all(profile, snapshot, {ReferentPosition.estimand(p).label(): r for p, r in _referent_positions(estimand).items()})
    return estimand, _emit_receipt(estimand.claim, snapshot, outcomes)


def estimand_from_stored(projection: Mapping[str, object], *, profile: ProfileSpec) -> Estimand:
    """Restore a typed estimand from a stored spec's projection member. Typed
    against the declarations, resolved against nothing: restoration is not
    authoring, and the freeze already performed the membership check."""
    if not isinstance(projection, Mapping) or set(projection) != _WIRE_ESTIMAND_KEYS:
        raise MalformedWireEstimand(f"a stored estimand carries exactly {sorted(_WIRE_ESTIMAND_KEYS)}")
    wire = WireEstimand(**{key: projection[key] for key in _WIRE_ESTIMAND_KEYS})  # type: ignore[arg-type]
    return _typed_estimand(wire, profile, stored=True)


def applicability_from_stored(projection: Mapping[str, object], *, profile: ProfileSpec, operator: str) -> Mapping[str, Qualifier]:
    """Restore an applicability map: the same checks a claim's qualifiers get."""
    from types import MappingProxyType

    if not isinstance(projection, Mapping):
        raise MalformedWireEstimand("a stored applicability is a mapping")
    qualifiers: dict[str, Qualifier] = {}
    for dimension, body in projection.items():
        where = f"applicability[{dimension!r}]"
        declared = profile.dimensions.get(_require_estimand_text(dimension, "a dimension"))
        if declared is None:
            raise UndeclaredDimension(f"no dimension {dimension!r} in this profile")
        if not isinstance(body, Mapping) or set(body) != {"quantifier", "restriction"}:
            raise MalformedWireEstimand(f"{where}: exactly quantifier and restriction")
        qualifiers[dimension] = Qualifier(
            quantifier=_require_estimand_text(body["quantifier"], f"{where}.quantifier"),
            restriction=_wire_referent(body["restriction"], f"{where}.restriction", declared=declared.restriction_sort, stored=True),
        )
    declaration = profile.operator(operator)
    permitted = set(declaration.dimensions)
    for dimension, qualifier in qualifiers.items():
        if dimension not in permitted:
            raise UndeclaredDimension(f"{operator!r} does not permit dimension {dimension!r}")
        if qualifier.quantifier not in profile.claim_grammar.quantifiers:
            raise UnknownQuantifier(f"quantifier {qualifier.quantifier!r} is outside the kernel's closed set")
        if qualifier.restriction.sort != profile.dimensions[dimension].restriction_sort:
            raise RestrictionSortMismatch(f"{dimension!r} restricts to {profile.dimensions[dimension].restriction_sort!r}")
    return MappingProxyType(qualifiers)
