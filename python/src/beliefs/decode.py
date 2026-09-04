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

from nodes.core.node import Node

from beliefs.claim import Claim, Qualifier, Referent
from beliefs.errors import ArityMismatch, MalformedWireClaim, UnboundReferent, UndeclaredDimension
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import (
    BindingCheckReceipt,
    ReferentPosition,
    ResolutionSnapshot,
    TermOutcome,
    _emit_receipt,
)

__all__ = ["WireClaim", "claim_from_stored", "decode_claim"]


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
    if not isinstance(snapshot, ResolutionSnapshot):
        raise MalformedWireClaim(
            f"snapshot is a {type(snapshot).__name__}, not a ResolutionSnapshot — use build_snapshot(...). "
            "Availability is a parameter (§7.2); a decoder that supplied its own would decide by ambient "
            "state, and two holders would read the same bytes differently."
        )
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
_STORED_QUALIFIER_BODY_KEYS = frozenset({"quantifier", "restriction"})


def claim_from_stored(node: Node, *, profile: ProfileSpec, snapshot: ResolutionSnapshot) -> tuple[Claim, BindingCheckReceipt]:
    """Restore a `Claim` from a stored proposition's covered claim facet.

    The wire value is built **here** and consumed **here** — `WireClaim` still
    never leaves this module (M13) — and typing is delegated to `decode_claim`
    rather than duplicated, so the check still happens once, in one place.
    Every ill-formed input refuses **before** delegation, with nothing minted
    and no `KeyError` or `AttributeError` on the way in (M11): a restore helper
    is exactly where "be liberal in what you accept" would defeat the row.
    """
    if not isinstance(node, Node) or node.kind != "proposition":
        raise MalformedWireClaim(f"claim_from_stored restores a proposition node, found {type(node).__name__}")
    facet = node.facets.get("proposition")  # stored.PROPOSITION_FACET; restated to keep decode.py free of stored.py
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
    for dimension, body in facet["qualifiers"].items():
        if not isinstance(body, Mapping) or set(body) != _STORED_QUALIFIER_BODY_KEYS:
            raise MalformedWireClaim(f"{node.id}: qualifiers[{dimension!r}] is not a well-formed qualifier body")
    wire = WireClaim(
        operator=facet["operator"],
        args=tuple(facet["args"]),
        qualifiers=facet["qualifiers"],
        polarity=facet["polarity"],
        layer=facet["layer"],
    )
    return decode_claim(wire, profile=profile, snapshot=snapshot)
