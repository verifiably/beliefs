"""``Claim`` — the typed claim, and the only route to one.

```text
Claim  =  Σ (op : Operator).  Args(op) × Qualifiers(op) × Polarity(op) × Layer(op)
```

§6.2's dependent sum, as far as a language without a code-generation layer can
carry it. Choosing the operator determines the *types* of everything else, and
the operators arrive through a runtime-loaded `ProfileSpec` — so neither Python
nor TypeScript can vary this constructor's static signature by them. §6.3 says
exactly what survives that, and **M13 is scoped to it**: `Claim` is opaque, its
only route is the validated constructor, and the profile-dependent checks
therefore happen **once**, at one place, after which no downstream reader
re-validates.

What is *not* claimed here: that an ill-typed claim is unspellable. It is
refused, not unconstructible, and the refusals below are ordinary runtime
refusals. Writing that a Python dataclass makes wrong-sorted arguments
unspellable would be the slogan §6.2 warns against, one layer down.

**Retirement is enforced on the authoring route and nowhere else** (§7.3a).
`build_claim` refuses a withdrawn operator or dimension; `Claim._checked` does
not, because decode, import and restore type a *historical* claim against the
frozen declaration and refusing there would corrupt the history retirement
exists to preserve. The two routes share every profile-dependent check and
differ in exactly that one respect.

**Referent membership is not checked here.** Whether an argument's term is in
its sort's bound vocabulary depends on the `ResolutionSnapshot` (§7.2) — a
parameter this module does not take, since a check whose result varies with what
happens to be readable cannot be a property of the value. That is M4's, and it
arrives with `decodeClaim`. Until it does, `build_claim` types a claim's shape
against the profile and says nothing about whether its referents exist.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs.errors import (
    ArgumentSortMismatch,
    ArityMismatch,
    ClaimError,
    InadmissibleLayer,
    MalformedReferent,
    PolarityRefused,
    ProfileError,
    RestrictionSortMismatch,
    UndeclaredDimension,
    UnknownQuantifier,
    UntypedQualifier,
    UntypedReferent,
    WithdrawnFromAuthoring,
)
from beliefs.identifiers import not_an_identifier
from beliefs.profile import ProfileSpec
from beliefs.sealed import sealed

__all__ = ["Claim", "Qualifier", "Referent", "build_claim"]


@sealed
@final
@dataclass(frozen=True)
class Referent:
    """A bound referent: a term identifier **together with the sort it came from**.

    §6.2 types an argument slot as `Referent(ArgSort(op, i))`, and `Referent(gene)`
    and `Referent(phenotype)` are different types — a term of one does not inhabit
    the other. What that becomes at runtime is that the sort travels *with* the
    value: a bare string cannot occupy a slot at all (M4), because a string
    carries no sort and so there is nothing to compare against the slot.

    Freely constructible: the opacity M13 requires is `Claim`'s, and a `Referent`
    is an ordinary typed value that a check *admits* rather than trusts. But it
    owns its own field invariant, because **`term` is the one position in a claim
    that nothing downstream checks**. The operator, the layer, the dimensions and
    the sorts are all matched against the profile's tables, so a non-identifier
    in any of them refuses on its own; a referent's term is checked only for
    *membership*, and that is deferred to decode against a snapshot. Without the
    check below, a `Claim` could be minted holding an integer where an identifier
    belongs — trusted, because it came through the boundary.
    """

    sort: str
    """The term identifier of the sort, not a local name."""

    term: str
    """The referent's term identifier within that sort's bound vocabulary."""

    def __post_init__(self) -> None:
        _require_referent_identifier(self.sort, "a referent's sort")
        _require_referent_identifier(self.term, "a referent's term")


@sealed
@final
@dataclass(frozen=True)
class Qualifier:
    """One entry of the flat fragment: `d ↦ ⟨quantifier, restriction⟩` (§6.4).

    The quantifier is **explicit and kernel-owned**, never inferred. Kernel §4.1's
    founding example turns on it: *"in adults"* is generic over a population and
    *"in all humans"* is universal over one, and a structure that defaulted the
    quantifier would make the two differ only where an editor happened to look.
    """

    quantifier: str
    restriction: Referent

    def __post_init__(self) -> None:
        # The quantifier is *not* checked here: it is matched against the
        # kernel's closed set at construction, so a bad one already refuses.
        _require_referent(self.restriction, "a qualifier's restriction")


_NO_QUALIFIERS: Mapping[str, Qualifier] = MappingProxyType({})


@sealed
@final
@dataclass(frozen=True, init=False)
class Claim:
    """**Opaque, and reachable only through a validated construction.**

    There is no public field-wise constructor and no coercion from a wire value.
    That is M13's whole content, and it is what makes the check happen once: a
    `Claim` in hand has already been typed against a profile, so no downstream
    code needs a defensive re-check, and none should have one.

    The guarantee is worth exactly what `isinstance` is worth, which is why the
    type is sealed, and why every value type whose invariant it *trusts* —
    `Referent` and `Qualifier`, not `str` or `tuple` — is sealed and checks its
    own fields (§6.3). `object.__new__` and direct attribute writes still reach
    past all of it — that is the same act as a hand-edited file on disk, the
    third row of §6.3's table, and it produces an audit finding rather than a
    refusal.
    """

    operator: str
    """The operator's term identifier (§6.5) — never a local name."""

    args: tuple[Referent, ...]
    """One referent per slot of `Fin(arity(op))`, in slot order. Slots are
    ordered and stay ordered; the sets around them are sorted (§6.2)."""

    qualifiers: Mapping[str, Qualifier]
    """Dimension term identifier → qualifier, for the dimensions this claim
    restricts. Insertion order is not meaningful: §6.5 sorts by dimension
    identifier in the projection, and mapping equality ignores order."""

    polarity: str
    """Always a tag, and for a sign-inapt operator always the base contract's
    `sign_inapt_tag` (§7.5). The claim carries no absent-polarity state, so
    `π_claim`'s shape can never depend on a contract field."""

    layer: str
    """The layer term identifier, from the operator's declared set."""

    # The lock is this method, not `init=False`. `@dataclass` declines to
    # overwrite an `__init__` already in the class body, so flipping `init=False`
    # to `True` changes nothing — which is worth stating, because it means the
    # decorator argument cannot be read as the thing doing the work. It is a
    # backstop: with this method deleted it still leaves the class with no
    # field-wise constructor to inherit.
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ClaimError(
            "Claim is validated at construction — use build_claim(profile, ...). A field-wise "
            "constructor would put an unchecked claim downstream of the one boundary that checks "
            "(M13), and every reader that trusts a Claim unconditionally would then be wrong."
        )

    @classmethod
    def _checked(
        cls,
        profile: ProfileSpec,
        *,
        operator: str,
        args: tuple[Referent, ...],
        qualifiers: Mapping[str, Qualifier],
        polarity: str | None,
        layer: str,
    ) -> Claim:
        """Type the parts against the profile, or refuse.

        Every check here is profile-dependent and therefore runtime (§6.3), and
        every one is shared by the authoring route and by decode. Retirement is
        **not** among them — see the module docstring.

        The profile is authenticated **here** and not only in `build_claim`,
        because this is the other route in: decode will call it directly, and a
        check on one of two entry points is a check on neither.
        """
        _require_profile(profile)
        declaration = profile.operator(operator)

        if len(args) != declaration.arity:
            raise ArityMismatch(
                f"{operator!r} has arity {declaration.arity}; {len(args)} argument(s) supplied. "
                "Every slot of Fin(arity(op)) is filled, and no slot is filled twice."
            )
        for index, (referent, sort) in enumerate(zip(args, declaration.arg_sorts, strict=True)):
            _require_referent(referent, f"slot {index} of {operator!r}")
            if referent.sort != sort:
                raise ArgumentSortMismatch(
                    f"slot {index} of {operator!r} is declared {sort!r}; {referent.term!r} is of sort "
                    f"{referent.sort!r}. Inside the model these are different types, so this is not a "
                    "rejected value but a term with no slot to occupy."
                )

        permitted = set(declaration.dimensions)
        for dimension, qualifier in qualifiers.items():
            if not isinstance(qualifier, Qualifier):
                raise UntypedQualifier(
                    f"the qualifier on {dimension!r} is {type(qualifier).__name__}, not a Qualifier. "
                    "Structural typing is not enough: any object exposing `quantifier` and "
                    "`restriction` would otherwise be stored inside a Claim and trusted as one."
                )
            if dimension not in permitted:
                raise UndeclaredDimension(
                    f"{operator!r} does not permit dimension {dimension!r}; it permits "
                    f"{sorted(permitted)}. Dims(op) is declared per operator (§6.2)."
                )
            if qualifier.quantifier not in profile.claim_grammar.quantifiers:
                raise UnknownQuantifier(
                    f"quantifier {qualifier.quantifier!r} on {dimension!r} is outside the kernel's closed "
                    f"set {list(profile.claim_grammar.quantifiers)} (§6.4)."
                )
            # The restriction needs no type check here: `Qualifier` owns that
            # invariant, and it is sealed, so there is no `Qualifier` whose
            # restriction is anything else.
            restriction_sort = profile.dimensions[dimension].restriction_sort
            if qualifier.restriction.sort != restriction_sort:
                raise RestrictionSortMismatch(
                    f"{dimension!r} restricts to sort {restriction_sort!r}; "
                    f"{qualifier.restriction.term!r} is of sort {qualifier.restriction.sort!r}."
                )

        grammar = profile.claim_grammar
        if declaration.sign_apt:
            if polarity is None:
                raise PolarityRefused(
                    f"{operator!r} is sign-apt, so a polarity must be asserted — one of "
                    f"{list(grammar.polarities)}. {grammar.sign_inapt_tag!r} is not among them: it says the "
                    "operator has no sign to assert, which is a different fact from asserting none."
                )
            if polarity not in grammar.polarities:
                raise PolarityRefused(
                    f"polarity {polarity!r} is outside the base contract's closed set {list(grammar.polarities)}."
                )
            tag = polarity
        else:
            if polarity is not None:
                raise PolarityRefused(
                    f"{operator!r} is sign-inapt: Polarity(op) is the unit type (§6.3), so there is no "
                    f"polarity to supply — not even {grammar.sign_inapt_tag!r}, which the projection "
                    "carries on the claim's behalf (§7.5) and an author never chooses."
                )
            tag = grammar.sign_inapt_tag

        if layer not in declaration.layers:
            raise InadmissibleLayer(
                f"{operator!r} admits layers {sorted(declaration.layers)}; {layer!r} is not among them."
            )

        claim = object.__new__(cls)
        object.__setattr__(claim, "operator", operator)
        object.__setattr__(claim, "args", tuple(args))
        object.__setattr__(claim, "qualifiers", MappingProxyType(dict(qualifiers)))
        object.__setattr__(claim, "polarity", tag)
        object.__setattr__(claim, "layer", layer)
        return claim


def build_claim(
    profile: ProfileSpec,
    *,
    operator: str,
    args: tuple[Referent, ...],
    layer: str,
    qualifiers: Mapping[str, Qualifier] = _NO_QUALIFIERS,
    polarity: str | None = None,
) -> Claim:
    """Author a claim: the typed route in, and the one that enforces retirement.

    `polarity` is `None` when the operator has no sign to assert. That is not a
    default standing in for a value — for a sign-inapt operator `Polarity(op)` is
    the unit type, so there is nothing to supply, and supplying the sign-inapt
    tag explicitly is refused rather than accepted as a synonym. For a sign-apt
    operator `None` is refused too: a claim that asserts no sign says so with
    `unsigned`, which is a different fact from having no sign to assert.
    """
    _require_profile(profile)
    selectable = profile.authorable_dimensions(operator)
    permitted = set(profile.operator(operator).dimensions)
    withdrawn = sorted((set(qualifiers) & permitted) - set(selectable))
    if withdrawn:
        raise WithdrawnFromAuthoring(
            f"dimension(s) {withdrawn} are permitted for {operator!r} but retired — either themselves or "
            "through their restriction sort. §7.3a: they stay resolvable for decode, which types a "
            "historical claim against the frozen declaration."
        )
    return Claim._checked(profile, operator=operator, args=args, qualifiers=qualifiers, polarity=polarity, layer=layer)


def _require_profile(value: object) -> None:
    """Refuse anything that is not a compiled profile.

    `ProfileSpec` is sealed and refuses to be authored, so this is not defending
    against a second `ProfileSpec` — it is refusing a **duck**. Every check below
    goes through `profile.operator(...)` and `profile.claim_grammar`, and any
    object exposing those would type a claim against declarations of its own
    choosing while the resulting `Claim` is entirely genuine. The TypeScript side
    has checked this since its profile became a class; this side had not, which
    is the same asymmetry the last round found in the other direction.
    """
    if not isinstance(value, ProfileSpec):
        raise ProfileError(
            f"profile is a {type(value).__name__}, not a compiled ProfileSpec — use "
            "compile_profile(base, domains). Structural similarity is not enough: every check a claim "
            "passes is read out of this object, so an impostor types a claim against itself."
        )


def _require_referent(value: object, where: str) -> None:
    if not isinstance(value, Referent):
        raise UntypedReferent(
            f"{where} holds {type(value).__name__}, not a Referent. A slot is typed Referent(s) (§6.2), "
            "and a bare term carries no sort to check against the one declared."
        )


def _require_referent_identifier(value: object, where: str) -> None:
    """Every position in the projection is an identifier (§6.5).

    A referent's two fields are the only ones a claim carries that are not
    matched against a table somewhere, so this is where that sentence has to be
    made true rather than assumed.
    """
    problem = not_an_identifier(value)
    if problem is not None:
        raise MalformedReferent(
            f"{where}: {problem}. Every position in π_claim is an identifier (§6.5), and a referent's "
            "fields are the only ones no downstream check would catch."
        )
