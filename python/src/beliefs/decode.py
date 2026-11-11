"""`decode_claim` — the boundary M₀ never stated.

```text
decodeClaim :  WireClaim × ProfileSpec × ResolutionSnapshot
               ──▶  (Claim × BindingCheckReceipt) + Refused
```

**Unconstructibility eliminates the internal guard; it does not eliminate the
boundary**. Serialized YAML, an imported record, a restored corpus and a
raw write can all *express* a combination the type cannot hold, so the type's
guarantee and this boundary's are different laws at different places. Every
import, deserialization and restore comes through here.

**Three parameters, and the third is the one that makes it a function.** With
only a wire value and a profile, the decision would still depend on which
vocabularies happen to be readable — ambient state, so two holders could decode
identical bytes differently and nothing could adjudicate. `ResolutionSnapshot`
moves that into the signature. `Refused` is spelled as an exception here, which
is the sum's refusing arm: it returns no claim, and therefore no receipt.

**Retirement is not enforced here, deliberately**. This function sees
wire bytes and cannot tell a claim being authored now from a historical one being
restored from a backup, re-imported, or replayed from the mutation log. Refusing
a retired identifier would make every corpus holding a prior claim
un-restorable — corrupting exactly the history retirement exists to preserve. So
`build_claim` refuses withdrawn identifiers and this route does not, and that is
the only respect in which the two differ.

**`WireClaim` does not leave this module.** No function
downstream of the boundary accepts one, because a downstream signature that did
would let unchecked data past the single place that checks it. The test for that
walks the package's own signatures rather than grepping for the name.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from nodes.core.node import Node

from beliefs.claim import Claim, Member, Qualifier, Referent, member_key
from beliefs.errors import (
    ClaimError,
    MalformedWireClaim,
    MalformedWireEstimand,
    UnboundReferent,
)
from beliefs.estimand import estimand_from_stored
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
    "claim_from_stored",
    "decode_claim",
    "estimand_from_stored",
    "stored_claim_terms",
]


@dataclass(frozen=True)
class WireClaim:
    """A claim as it arrives: identifiers, tags and coefficients, and nothing typed.

    Its shape is `π_claim`'s, because that is what a serialized claim is: roles
    by name, a `one` role as `{sort, term}`, a `many` role as a list of
    `{sort, term, coefficient}`, each qualifier as `{quantifier, restriction}`
    with the restriction `{sort, term}`. Every referent carries its sort on the
    wire, as in the projection; what the wire does **not** carry is any proof that
    the sort is declared, that its role admits it, or that the term is in its
    class. That is the point of the boundary: on the wire a referent is two
    strings with nothing checked; inside, a `Referent` in a `Claim` has been typed.

    Freely constructible, and it must be: it models untrusted input, so a
    validated constructor here would be validating the wrong thing at the wrong
    place. Its fields are typed for readers only — every one of them is checked
    below on the assumption that the annotations are a wish.
    """

    operator: str
    roles: Mapping[str, object]
    qualifiers: Mapping[str, Mapping[str, object]]
    form: str
    polarity: str
    layer: str


_ONE = "one"
_REFERENT_KEYS = frozenset({"sort", "term"})
_MEMBER_KEYS = frozenset({"sort", "term", "coefficient"})
_QUALIFIER_KEYS = frozenset({"quantifier", "restriction"})


def _require_text(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise MalformedWireClaim(f"{where}: expected a non-empty identifier, found {value!r}")
    return value


def _require_snapshot(snapshot: object, error: type[MalformedWireClaim | MalformedWireEstimand]) -> None:
    """`decode_claim`'s and `decode_estimand`'s shared authentication check: availability is a
    parameter, never ambient, so a decoder that supplied its own snapshot would decide by ambient
    state and two holders could read identical bytes differently."""
    if not isinstance(snapshot, ResolutionSnapshot):
        raise error(
            f"snapshot is a {type(snapshot).__name__}, not a ResolutionSnapshot — use build_snapshot(...). "
            "Availability is a parameter; a decoder that supplied its own would decide by ambient "
            "state, and two holders would read the same bytes differently."
        )


def _exact_fields(value: object, keys: frozenset[str], where: str) -> Mapping[str, object]:
    """A mapping with exactly ``keys``, every field name a string.

    The names are checked before the field arithmetic, not after: `set(body) -
    {...}` over a non-string key sorts and joins values that are not strings, and
    the `TypeError` that comes out is not a `DecodeError` — so a caller holding
    this boundary's refusing arm sees a crash instead of a refusal, on input that
    is exactly what this function exists to refuse. The contract loaders check
    mapping keys for the same reason before their own `_fields`."""
    if not isinstance(value, Mapping):
        raise MalformedWireClaim(f"{where}: expected a mapping, found {value!r}")
    for field in value:
        _require_text(field, f"{where}: a field name")
    unknown = sorted(set(value) - keys)
    if unknown:
        raise MalformedWireClaim(f"{where}: unknown field(s) {', '.join(unknown)}; refused, never ignored")
    missing = sorted(keys - set(value))
    if missing:
        raise MalformedWireClaim(f"{where}: missing field(s) {', '.join(missing)}")
    return value


def _wire_claim_referent(value: object, where: str) -> Referent:
    body = _exact_fields(value, _REFERENT_KEYS, where)
    return Referent(
        sort=_require_text(body["sort"], f"{where}.sort"), term=_require_text(body["term"], f"{where}.term")
    )


def _wire_members(value: Sequence[object], where: str) -> tuple[Member, ...]:
    """A `many` role's members, in the order written: `Claim._checked` puts them
    in canonical member-key order and refuses two sharing a key."""
    members: list[Member] = []
    for index, item in enumerate(value):
        at = f"{where}[{index}]"
        body = _exact_fields(item, _MEMBER_KEYS, at)
        coefficient = body["coefficient"]
        # bool is an int in Python, so it is refused first. An integer below 1 is
        # well-shaped and refused by `Member` itself (`CoefficientRefused`).
        if isinstance(coefficient, bool) or not isinstance(coefficient, int):
            raise MalformedWireClaim(f"{at}.coefficient: expected an integer, found {coefficient!r}")
        referent = Referent(
            sort=_require_text(body["sort"], f"{at}.sort"), term=_require_text(body["term"], f"{at}.term")
        )
        members.append(Member(referent=referent, coefficient=coefficient))
    return tuple(members)


_WireRoles = dict[str, Referent | tuple[Member, ...]]


def _wire_parts(wire: WireClaim) -> tuple[str, _WireRoles, dict[str, Qualifier], str, str, str]:
    """Check the wire value's own shape, before anything is resolved against a profile.

    This is not the profile-dependent typing — that is `Claim._checked`'s, and it
    stays there. This is the narrower question of whether the value has the shape
    a wire claim has at all, which has to be settled first because the typing
    below indexes into it. A role's shape says its arity: a mapping is a `one`
    role's referent, a sequence a `many` role's members, and anything else is
    refused here. Whether that arity is the declared one needs the template, so
    `decode_claim` checks it next.
    """
    if not isinstance(wire, WireClaim):
        raise MalformedWireClaim(
            f"decode_claim takes a WireClaim, found {type(wire).__name__}. The wire type is what marks a value "
            "as unchecked; accepting anything shaped like one would make the mark meaningless."
        )
    operator = _require_text(wire.operator, "operator")
    if not isinstance(wire.roles, Mapping):
        raise MalformedWireClaim(
            f"roles: expected a mapping from role name to a referent or members, found {wire.roles!r}; "
            "roles are named, never positional"
        )
    roles: _WireRoles = {}
    for name, value in wire.roles.items():
        where = f"roles[{name!r}]"
        _require_text(name, "a role name")
        if isinstance(value, Mapping):
            roles[name] = _wire_claim_referent(value, where)
        elif isinstance(value, Sequence) and not isinstance(value, str | bytes):
            roles[name] = _wire_members(value, where)
        else:
            raise MalformedWireClaim(
                f"{where}: expected a {{sort, term}} referent or a list of {{sort, term, coefficient}} members, "
                f"found {value!r}"
            )
    if not isinstance(wire.qualifiers, Mapping):
        raise MalformedWireClaim(f"qualifiers: expected a mapping, found {wire.qualifiers!r}")
    qualifiers: dict[str, Qualifier] = {}
    for dimension, value in wire.qualifiers.items():
        where = f"qualifiers[{dimension!r}]"
        _require_text(dimension, "a qualifier dimension")
        body = _exact_fields(value, _QUALIFIER_KEYS, where)
        qualifiers[dimension] = Qualifier(
            quantifier=_require_text(body["quantifier"], f"{where}.quantifier"),
            restriction=_wire_claim_referent(body["restriction"], f"{where}.restriction"),
        )
    return (
        operator,
        roles,
        qualifiers,
        _require_text(wire.form, "form"),
        _require_text(wire.polarity, "polarity"),
        _require_text(wire.layer, "layer"),
    )


def _require_declared_arity(profile: ProfileSpec, operator: str, roles: _WireRoles) -> None:
    """Each role's wire shape is its declared arity's: a `one` role (and a
    reserved role) a single referent, a `many` role a list of members.

    The wire shape decides how a role is read, so a mismatch is a malformed wire
    value, the role-map successor of the old arity check: a list in a `one` role
    or a referent in a `many` one never reaches typing as a different shape. An
    undeclared role is left to `Claim._checked`, which refuses it by name."""
    template = profile.template_of(profile.operator(operator))
    for name, value in roles.items():
        role = template.roles.get(name)
        if role is None and name not in profile.claim_grammar.reserved_roles:
            continue
        one = role is None or role.arity == _ONE
        if one and not isinstance(value, Referent):
            raise MalformedWireClaim(
                f"roles[{name!r}]: {operator!r} declares {name!r} a `one` role, and the wire holds a list; a `one` "
                "role is a single {sort, term} referent"
            )
        if not one and isinstance(value, Referent):
            raise MalformedWireClaim(
                f"roles[{name!r}]: {operator!r} declares {name!r} a `many` role, and the wire holds a single "
                "referent; a `many` role is a list of {sort, term, coefficient} members"
            )


def decode_claim(
    wire: WireClaim, *, profile: ProfileSpec, snapshot: ResolutionSnapshot
) -> tuple[Claim, BindingCheckReceipt]:
    """Type a wire claim against a profile and resolve its referents, or refuse.

    Order is load-bearing. The wire's own shape is checked first, against no
    profile. Typing comes next — every referent's sort travels with it, so typing
    checks the sort rather than supplying it — because a referent cannot be
    resolved before its sort is known to be declared and admitted. Resolution
    happens last, and a `not-member` anywhere refuses the whole decode: nothing is
    returned, and the receipt — which exists to record checks that *were*
    performed — is never emitted on that arm.
    """
    if not isinstance(profile, ProfileSpec):
        raise MalformedWireClaim(
            f"profile is a {type(profile).__name__}, not a compiled ProfileSpec — use compile_profile(base, domains)."
        )
    _require_snapshot(snapshot, MalformedWireClaim)
    operator, roles, qualifiers, form, polarity, layer = _wire_parts(wire)
    _require_declared_arity(profile, operator, roles)

    # Every profile-dependent check, at the one place that performs them, and the
    # same one the authoring route uses — minus retirement, which is authoring's.
    # On the wire a claim with no sign to assert carries the sign-inapt tag; inside
    # there is nothing to supply, so the tag maps back to `None`.
    claim = Claim._checked(
        profile,
        operator=operator,
        roles=roles,
        qualifiers=qualifiers,
        form=form,
        polarity=None if polarity == profile.claim_grammar.sign_inapt_tag else polarity,
        layer=layer,
    )

    outcomes: dict[str, TermOutcome] = {}
    for label, referent in _positions(claim):
        outcomes[label] = snapshot.resolve(profile.sorts[referent.sort], referent.term)

    refused = sorted(label for label, outcome in outcomes.items() if outcome.refuses)
    if refused:
        raise UnboundReferent(
            f"{', '.join(refused)}: the term is not in the vocabulary its sort binds, and the vocabulary "
            "was read — this is a finding, not an unconsulted binding. Admitting it would put an unbindable "
            "identifier into an immutable claim identity. Nothing was minted."
        )

    return claim, _emit_receipt(claim_identity(claim), snapshot, outcomes)


def _positions(claim: Claim) -> tuple[tuple[str, Referent], ...]:
    """Every referent position of a typed claim, labelled: `role:<name>` for a
    `one` role, `role:<name>[<i>]` for the i-th member of a `many` role in the
    canonical member-key order the claim holds them in, `restriction:<dimension>`
    for each qualifier."""
    positions: list[tuple[str, Referent]] = []
    for name in sorted(claim.roles):
        value = claim.roles[name]
        if isinstance(value, Referent):
            positions.append((ReferentPosition.role(name).label(), value))
        else:
            positions.extend(
                (ReferentPosition.member(name, index).label(), member.referent) for index, member in enumerate(value)
            )
    for dimension in sorted(claim.qualifiers):
        positions.append((ReferentPosition.restriction(dimension).label(), claim.qualifiers[dimension].restriction))
    return tuple(positions)


_STORED_CLAIM_KEYS = frozenset({"operator", "roles", "qualifiers", "form", "polarity", "layer"})


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
    return WireClaim(
        operator=facet["operator"],
        roles=facet["roles"],
        qualifiers=facet["qualifiers"],
        form=facet["form"],
        polarity=facet["polarity"],
        layer=facet["layer"],
    )


def stored_claim_terms(node: Node) -> tuple[tuple[Referent, ...], tuple[Referent, ...]]:
    """Read a stored claim's referents after shape validation, against no profile.

    Role referents first, roles by name and each `many` role's members in
    canonical member-key order (the order the typed claim would hold them in,
    whatever order the facet wrote them), then qualifier restrictions by
    dimension. A facet whose shape is not a wire claim's refuses with
    `MalformedWireClaim`, a referent that is not an identifier included."""
    try:
        _operator, roles, qualifiers, _form, _polarity, _layer = _wire_parts(_stored_wire(node))
    except ClaimError as refused:
        # A non-identifier sort or term, or a coefficient below 1, is a malformed
        # stored value to a reader that types nothing.
        raise MalformedWireClaim(f"{node.id}: {refused}") from refused
    referents: list[Referent] = []
    for name in sorted(roles):
        value = roles[name]
        if isinstance(value, Referent):
            referents.append(value)
        else:
            referents.extend(sorted((member.referent for member in value), key=member_key))
    return tuple(referents), tuple(qualifiers[dimension].restriction for dimension in sorted(qualifiers))


def claim_from_stored(
    node: Node, *, profile: ProfileSpec, snapshot: ResolutionSnapshot
) -> tuple[Claim, BindingCheckReceipt]:
    """Restore a `Claim` from a stored proposition's covered claim facet.

    The wire value is built **here** and consumed **here** — `WireClaim` still
    never leaves this module — and typing is delegated to `decode_claim`
    rather than duplicated, so the check still happens once, in one place. The
    same is true one level down: a role's or qualifier body's own shape is
    `_wire_parts`' check, not a second copy of it, so it is called here — its
    return discarded — before `decode_claim`, rather than left for `decode_claim`
    to reach on its own. Every ill-formed input refuses **before** delegation,
    with nothing minted and no `KeyError` or `AttributeError` on the way in: a
    restore helper is exactly where "be liberal in what you accept" would defeat
    that refuse-before-delegation rule.
    """
    wire = _stored_wire(node)
    _wire_parts(wire)
    return decode_claim(wire, profile=profile, snapshot=snapshot)


# --- Estimands --------------------------------------
#
# Interim role adaptation (beliefs-d64969); beliefs-f68a32 replaces the estimand structure around these names.
#
# `decode_estimand` mirrors `decode_claim`'s discipline one artifact over: type
# first, then resolve. What it types is the estimand's **shape**
# (`Estimand._checked`): no estimand declaration is read, because the wire
# estimand carries no role assignment and admission (R12) is over the claim's
# admitting set. Admission is `estimand.admit_estimand`'s, which every consumer
# holding the claim calls. So every referent arrives as `{sort, term}`: with no
# declaration to read, a bare term has no sort to take. The restoration route
# differs from `claim_from_stored`'s in the one respect that matters:
# `estimand_from_stored` performs **no resolution at all**, because membership was
# the freeze's own check, not something a reader repeats. Retirement is
# unenforced on every route here, for `decode_claim`'s reason: a decoder cannot
# tell authoring from restoration.
