"""``Claim`` — the typed claim, and the only route to one.

```text
Claim  =  Σ (op : Operator).  Roles(op) × Qualifiers(op) × Σ (f : Form(op)). Polarity(op, f) × Layer(op)
```

A dependent sum, as far as a language without a code-generation layer can
carry it. Choosing the operator determines the *types* of everything else, and
the operators arrive through a runtime-loaded `ProfileSpec` — so neither Python
nor TypeScript can vary this constructor's static signature by them. What survives that is
exactly this: `Claim` is opaque, its
only route is the validated constructor, and the profile-dependent checks
therefore happen **once**, at one place, after which no downstream reader
re-validates.

What is *not* claimed here: that an ill-typed claim is unspellable. It is
refused, not unconstructible, and the refusals below are ordinary runtime
refusals. Writing that a Python dataclass makes wrong-sorted referents
unspellable would be exactly the slogan this module avoids, one layer down.

**Retirement is enforced on the authoring route and nowhere else**.
`build_claim` refuses a retired operator, sort or dimension, and a claim only
retired instantiations admit; `Claim._checked` refuses none of them unless asked
to (`authoring=True`, which is how `build_claim` calls it), because decode,
import and restore type a *historical* claim against the frozen declaration and
refusing there would corrupt the history retirement exists to preserve. The two routes share every profile-dependent check and
differ in exactly that one respect.

**Referent membership is not checked here.** Whether a referent's term is in
its sort's bound vocabulary depends on the `ResolutionSnapshot` — a
parameter this module does not take, since a check whose result varies with what
happens to be readable cannot be a property of the value. That check belongs to
`decode_claim`; `build_claim` types a claim's shape against the profile and
says nothing about whether its referents exist. Its *form* is checked: each
term must match its sort's identifier class.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from itertools import pairwise
from types import MappingProxyType
from typing import final

from beliefs.contract.domain import WorldKindBinding
from beliefs.errors import (
    ClaimError,
    CoefficientRefused,
    DimensionNotClaimSide,
    DuplicateMember,
    FormRefused,
    IdentifierClassMismatch,
    InadmissibleLayer,
    MalformedReferent,
    PolarityRefused,
    ProfileError,
    RestrictionSortMismatch,
    RoleRefused,
    UndeclaredDimension,
    UndeclaredSort,
    UninstantiatedTemplate,
    UnknownQuantifier,
    UntypedQualifier,
    UntypedReferent,
    WithdrawnFromAuthoring,
    WithinModelRefused,
)
from beliefs.identifiers import not_an_identifier
from beliefs.profile import CompiledBridge, CompiledRole, CompiledSort, ProfileSpec
from beliefs.sealed import sealed

__all__ = ["Claim", "Member", "Qualifier", "Referent", "build_claim", "canonical_members", "member_key"]

_WITHIN_MODEL = "within-model"
"""The one role the base contract reserves (a closed set under base v2): any
claim may carry it beside its template's roles, and it never reaches admission."""
_ONE = "one"
_CLAIM_SIDE = "claim"
_NULL_FORM = "null"
_HEX64 = "[0-9a-f]{64}"


@sealed
@final
@dataclass(frozen=True)
class Referent:
    """A bound referent: a term identifier **together with the sort it came from**.

    `Referent(gene)` and `Referent(phenotype)` are different types — a term of
    one does not inhabit the other. What that becomes at runtime is that the sort
    travels *with* the value: a bare string cannot fill a role at all, because a
    string carries no sort and so there is nothing to check against the sorts the
    role admits.

    Freely constructible: the opacity that matters is `Claim`'s, and a `Referent`
    is an ordinary typed value that a check *admits* rather than trusts. But it
    owns its own field invariant, because **`term` is the one position in a claim
    no table holds**. The operator, the layer, the dimensions and the sorts are
    all matched against the profile's tables, so a non-identifier in any of them
    refuses on its own; a referent's term is matched against a pattern (its
    sort's identifier class) and, for membership, deferred to decode against a
    snapshot. Without the check below, a `Claim` could be minted holding an
    integer where an identifier belongs — trusted, because it came through the
    boundary.
    """

    sort: str
    """The term identifier of the sort, not a local name."""

    term: str
    """The referent's term identifier within that sort's bound vocabulary."""

    def __post_init__(self) -> None:
        require_identifier(self.sort, "a referent's sort")
        require_identifier(self.term, "a referent's term")


@sealed
@final
@dataclass(frozen=True)
class Member:
    """A referent with a positive integer coefficient: one entry of a `many` role.

    The referent keeps the spelling it was written in; only `member_key` normalizes.
    """

    referent: Referent
    coefficient: int = 1

    def __post_init__(self) -> None:
        _require_referent(self.referent, "a member's referent")
        # bool is an int in Python, so it is refused first.
        if isinstance(self.coefficient, bool) or not isinstance(self.coefficient, int) or self.coefficient < 1:
            raise CoefficientRefused(
                f"a member's coefficient is {self.coefficient!r}; it must be an integer of at least 1"
            )


def member_key(referent: Referent) -> tuple[str, str]:
    """The canonical member key: the NFC of sort and term, compared by code point
    (Python's tuple-of-str order)."""
    return (unicodedata.normalize("NFC", referent.sort), unicodedata.normalize("NFC", referent.term))


def canonical_members(members: Iterable[Member], *, where: str) -> tuple[Member, ...]:
    """Members sorted by `member_key`; two sharing a key raise `DuplicateMember`."""
    items = tuple(members)
    for item in items:
        if not isinstance(item, Member):
            raise UntypedReferent(f"{where} holds {type(item).__name__}, not a Member")
    ordered = tuple(sorted(items, key=lambda m: member_key(m.referent)))
    for left, right in pairwise(ordered):
        if member_key(left.referent) == member_key(right.referent):
            raise DuplicateMember(
                f"{where} names {member_key(left.referent)!r} more than once; a role holds each referent once"
            )
    return ordered


@sealed
@final
@dataclass(frozen=True)
class Qualifier:
    """One entry of the flat fragment: `d ↦ ⟨quantifier, restriction⟩`.

    The quantifier is **explicit and kernel-owned**, never inferred. The
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
    That is the whole content of the opacity, and it is what makes the check happen once: a
    `Claim` in hand has already been typed against a profile, so no downstream
    code needs a defensive re-check, and none should have one.

    The guarantee is worth exactly what `isinstance` is worth, which is why the
    type is sealed, and why every value type whose invariant it *trusts* —
    `Referent`, `Member` and `Qualifier`, not `str` or `tuple` — is sealed and
    checks its own fields. `object.__new__` and direct attribute writes still reach
    past all of it — that is the same act as a hand-edited file on disk, the
    "raw write" case, and it produces an audit finding rather than a
    refusal.
    """

    operator: str
    """The operator's term identifier — a template or a bridge, never a local name."""

    roles: Mapping[str, Referent | tuple[Member, ...]]
    """Role name → its filling: a `Referent` for a `one` role (and for the
    reserved `within-model`), the members in canonical member-key order for a
    `many` role (possibly empty, where the role declares `min: 0`). A map, never a
    sequence: role names are the template's, so declaration order is not
    meaningful, and the projection's key order is the encoder's."""

    qualifiers: Mapping[str, Qualifier]
    """Dimension term identifier → qualifier, for the claim-side dimensions this
    claim restricts. Insertion order is not meaningful: the projection sorts by
    dimension identifier, and mapping equality ignores order."""

    form: str
    """The claim form, `polar` or `"null"`, from the template's declared set."""

    polarity: str
    """Always a tag. Where there is no sign to assert — a sign-inapt operator, or
    a `"null"`-form claim — it is the base contract's `sign_inapt_tag`. The claim
    carries no absent-polarity state, so `π_claim`'s shape can never depend on a
    contract field."""

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
            "constructor would put an unchecked claim downstream of the one boundary that checks"
            ", and every reader that trusts a Claim unconditionally would then be wrong."
        )

    def assignment(self) -> Mapping[str, frozenset[str]]:
        """Role → the sorts the claim puts in it (every member's, for a `many`
        role; empty for an empty one), the reserved `within-model` excluded: the
        assignment `ProfileSpec.admitting` reads."""
        return MappingProxyType({name: _sorts_of(value) for name, value in self.roles.items() if name != _WITHIN_MODEL})

    @classmethod
    def _checked(
        cls,
        profile: ProfileSpec,
        *,
        operator: str,
        roles: Mapping[str, Referent | Iterable[Member]],
        qualifiers: Mapping[str, Qualifier],
        form: str,
        polarity: str | None,
        layer: str,
        authoring: bool = False,
    ) -> Claim:
        """Type the parts against the profile, or refuse.

        The checks run in the order of the design's typing rule, each step
        refusing distinctly: (1) the operator resolves to a template or a bridge;
        (2) the roles present are exactly the template's declared roles, plus
        optionally a reserved role; (3) each `one` role holds one `Referent`, each
        `many` role members within its bounds, with coefficients of 1 unless the
        role admits others, and no two members with one canonical key; (4) every
        referent — roles and restrictions alike — has a declared sort whose
        identifier class its term matches, and a reserved-role referent's sort
        binds to the reserved world kind; (5) some declaration admits the
        role-to-sort assignment; (6) each qualifier names a claim-side dimension
        applying to the operator, with a kernel quantifier and a restriction of the
        dimension's sort; (7) the form is the template's and the polarity obeys
        it; (8) the layer is the operator's.

        Every check is shared by the authoring route and by decode.
        **Retirement is checked only when `authoring` is true** (`build_claim`
        passes it; decode, import and restore do not) — see the module docstring.

        The profile is authenticated **here** and not only in `build_claim`,
        because this is the other route in: decode will call it directly, and a
        check on one of two entry points is a check on neither.
        """
        _require_profile(profile)
        grammar = profile.claim_grammar

        # (1) The operator.
        declaration = profile.operator(operator)
        if authoring and declaration.retired:
            raise WithdrawnFromAuthoring(
                f"operator {operator!r} is withdrawn from authoring — the operator is retired. It stays "
                "resolvable for decode, import and restore, which type a historical claim against the frozen "
                "declaration."
            )
        template = profile.template_of(declaration)

        # (2) The roles present.
        if not isinstance(roles, Mapping):
            raise RoleRefused(
                f"the roles of a claim over {operator!r} are a {type(roles).__name__}, not a mapping from role "
                "name to a referent or members. Roles are named, never positional."
            )
        for name in roles:
            if not isinstance(name, str):
                raise RoleRefused(f"a role of a claim over {operator!r} is named {name!r}, not a role name")
        declared = set(template.roles)
        reserved = set(grammar.reserved_roles)
        missing = sorted(declared - set(roles))
        if missing:
            raise RoleRefused(
                f"{operator!r} declares role(s) {missing} and the claim fills none of them; every declared role "
                "is filled (a `many` role with `min: 0` is filled by an empty list)."
            )
        undeclared = sorted(set(roles) - declared - reserved)
        if undeclared:
            raise RoleRefused(
                f"{operator!r} declares no role(s) {undeclared}; its roles are {sorted(declared)}, and the "
                f"kernel reserves {sorted(reserved)} on every operator."
            )

        # (3) Each role's filling.
        held: dict[str, Referent | tuple[Member, ...]] = {}
        for name in sorted(roles):
            value = roles[name]
            where = f"role {name!r} of {operator!r}"
            role = template.roles.get(name)
            if role is None or role.arity == _ONE:
                _require_referent(value, where)
                assert isinstance(value, Referent)
                held[name] = value
            else:
                held[name] = _members(value, role, where)

        # (4) Every referent: its sort is declared, its term is in the sort's class.
        for name, value in held.items():
            world_kind = grammar.reserved_roles[name].world_kind if name in reserved else None
            for referent in _referents_of(value):
                _check_referent(
                    profile, referent, f"role {name!r} of {operator!r}", world_kind=world_kind, authoring=authoring
                )
        for dimension, qualifier in qualifiers.items():
            if not isinstance(qualifier, Qualifier):
                raise UntypedQualifier(
                    f"the qualifier on {dimension!r} is {type(qualifier).__name__}, not a Qualifier. "
                    "Structural typing is not enough: any object exposing `quantifier` and "
                    "`restriction` would otherwise be stored inside a Claim and trusted as one."
                )
            # The restriction needs no type check here: `Qualifier` owns that
            # invariant, and it is sealed, so there is no `Qualifier` whose
            # restriction is anything else.
            _check_referent(
                profile,
                qualifier.restriction,
                f"the restriction on {dimension!r}",
                world_kind=None,
                authoring=authoring,
            )

        # (5) Admission: some declaration lists every referent's sort for its role.
        assignment = {name: _sorts_of(value) for name, value in held.items() if name not in reserved}
        if not profile.admitting(operator, assignment, authoring=False):
            if isinstance(declaration, CompiledBridge):
                raise UninstantiatedTemplate(
                    f"bridge {operator!r} admits the role sorts {_route_sorts(declaration.roles)}; a claim with "
                    f"sorts {_route_sorts(assignment)} is outside them. A bridge's own role sorts are its "
                    "admitting declaration."
                )
            raise UninstantiatedTemplate(
                f"no instantiation of {operator!r} admits a claim with sorts {_route_sorts(assignment)}. Each "
                "role's referents must have sorts that one instantiation lists for that role."
            )
        if authoring and not profile.admitting(operator, assignment, authoring=True):
            raise WithdrawnFromAuthoring(
                f"a claim over {operator!r} with sorts {_route_sorts(assignment)} is admitted only by retired "
                "declarations. It stays typeable for decode, import and restore, which type a historical "
                "claim against the frozen declaration."
            )

        # (6) Qualifiers: claim-side dimensions applying to this operator.
        applying = set(profile.claim_dimensions(operator))
        for dimension, qualifier in qualifiers.items():
            dimension_decl = profile.dimensions.get(dimension)
            if dimension_decl is None:
                raise UndeclaredDimension(f"no dimension {dimension!r} in this profile.")
            if dimension_decl.placement != _CLAIM_SIDE:
                raise DimensionNotClaimSide(
                    f"{dimension!r} is placed {dimension_decl.placement!r}: it restricts where an estimate "
                    "applies, never what a claim says, so it is not a claim qualifier."
                )
            if dimension not in applying:
                raise UndeclaredDimension(
                    f"{dimension!r} does not apply to {operator!r}; the claim-side dimensions that do are "
                    f"{sorted(applying)}."
                )
            if qualifier.quantifier not in grammar.quantifiers:
                raise UnknownQuantifier(
                    f"quantifier {qualifier.quantifier!r} on {dimension!r} is outside the kernel's closed "
                    f"set {list(grammar.quantifiers)}."
                )
            restriction_sort = dimension_decl.restriction_sort
            if qualifier.restriction.sort != restriction_sort:
                raise RestrictionSortMismatch(
                    f"{dimension!r} restricts to sort {restriction_sort!r}; "
                    f"{qualifier.restriction.term!r} is of sort {qualifier.restriction.sort!r}."
                )
            if authoring and dimension_decl.retired:
                raise WithdrawnFromAuthoring(
                    f"dimension {dimension!r} applies to {operator!r} but is retired. It stays resolvable for "
                    "decode, which types a historical claim against the frozen declaration."
                )

        # (7) The form, and the polarity it permits.
        if form not in template.forms:
            raise FormRefused(
                f"{operator!r} admits form(s) {list(template.forms)}; {form!r} is not among them. "
                f"{_NULL_FORM!r} is admitted only where the template declares it, and only a sign-apt "
                "template may."
            )
        if form == _NULL_FORM:
            if polarity is not None:
                raise PolarityRefused(
                    f"a {_NULL_FORM!r}-form claim asserts an absent effect, which has no sign: there is no "
                    f"polarity to supply — not even {grammar.sign_inapt_tag!r}, which the projection carries "
                    "on the claim's behalf."
                )
            tag = grammar.sign_inapt_tag
        elif template.sign_apt:
            if polarity is None:
                raise PolarityRefused(
                    f"{operator!r} is sign-apt, so a polar claim asserts a polarity — one of "
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
                    f"{operator!r} is sign-inapt: Polarity(op) is the unit type, so there is no "
                    f"polarity to supply — not even {grammar.sign_inapt_tag!r}, which the projection "
                    "carries on the claim's behalf and an author never chooses."
                )
            tag = grammar.sign_inapt_tag

        # (8) The layer.
        if layer not in declaration.layers:
            raise InadmissibleLayer(
                f"{operator!r} admits layers {sorted(declaration.layers)}; {layer!r} is not among them."
            )

        claim = object.__new__(cls)
        object.__setattr__(claim, "operator", operator)
        object.__setattr__(claim, "roles", MappingProxyType(held))
        object.__setattr__(claim, "qualifiers", MappingProxyType(dict(qualifiers)))
        object.__setattr__(claim, "form", form)
        object.__setattr__(claim, "polarity", tag)
        object.__setattr__(claim, "layer", layer)
        return claim


def build_claim(
    profile: ProfileSpec,
    *,
    operator: str,
    roles: Mapping[str, Referent | Iterable[Member]],
    layer: str,
    qualifiers: Mapping[str, Qualifier] = _NO_QUALIFIERS,
    form: str = "polar",
    polarity: str | None = None,
) -> Claim:
    """Author a claim: the typed route in, and the one that enforces retirement.

    `polarity` is `None` when there is no sign to assert — a sign-inapt
    operator, or a `"null"`-form claim. That is not a default standing in for a
    value: there `Polarity` is the unit type, so there is nothing to supply, and
    supplying the sign-inapt tag explicitly is refused rather than accepted as a
    synonym. For a polar claim over a sign-apt operator `None` is refused too: a
    claim that asserts no sign says so with `unsigned`, which is a different fact
    from having no sign to assert.
    """
    return Claim._checked(
        profile,
        operator=operator,
        roles=roles,
        qualifiers=qualifiers,
        form=form,
        polarity=polarity,
        layer=layer,
        authoring=True,
    )


def _members(value: object, role: CompiledRole, where: str) -> tuple[Member, ...]:
    """A `many` role's filling, typed: members within `[min, max]`, coefficients
    of 1 unless the role admits others, in canonical member-key order with no two
    sharing a key."""
    if isinstance(value, Referent | str | bytes | Mapping) or not isinstance(value, Iterable):
        raise UntypedReferent(
            f"{where} is a `many` role and holds {type(value).__name__}; it holds an iterable of Members, "
            "each a referent with its coefficient."
        )
    items = tuple(value)
    for item in items:
        if not isinstance(item, Member):
            raise UntypedReferent(f"{where} holds {type(item).__name__}, not a Member")
    bound = f"[{role.min}, {'∞' if role.max is None else role.max}]"
    if len(items) < role.min or (role.max is not None and len(items) > role.max):
        raise RoleRefused(f"{where} holds {len(items)} member(s); its declared member count is {bound}.")
    if not role.coefficients:
        for item in items:
            if item.coefficient != 1:
                raise CoefficientRefused(
                    f"{where} admits no coefficient but 1; {item.referent.term!r} carries {item.coefficient}."
                )
    return canonical_members(items, where=where)


def _check_referent(
    profile: ProfileSpec, referent: Referent, where: str, *, world_kind: str | None, authoring: bool
) -> None:
    """Step (4) for one referent: a declared sort, the reserved world kind where
    one is required, a term in the sort's identifier class, and — authoring
    only — a sort that is not retired."""
    sort = profile.sorts.get(referent.sort)
    if sort is None:
        raise UndeclaredSort(f"{where}: no sort {referent.sort!r} in this profile.")
    if world_kind is not None:
        binding = sort.binding
        if not (isinstance(binding, WorldKindBinding) and binding.world_kind == world_kind):
            raise WithinModelRefused(
                f"{where}: sort {referent.sort!r} is bound {binding.projection()!r}; the role takes records of "
                f"world kind {world_kind!r}, so its sort must bind by `world-kind` to {world_kind!r}."
            )
    if not _in_class(sort, referent.term):
        raise IdentifierClassMismatch(
            f"{where}: {referent.term!r} is outside the identifier class of {referent.sort!r} "
            f"({_class_text(sort)}), after NFC normalization."
        )
    if authoring and sort.retired:
        raise WithdrawnFromAuthoring(
            f"{where}: sort {referent.sort!r} is retired. It stays resolvable for decode, which types a "
            "historical claim against the frozen declaration."
        )


def _in_class(sort: CompiledSort, term: str) -> bool:
    if sort.identifier_class is not None:
        return sort.identifier_class.matches(term)
    binding = sort.binding
    if not isinstance(binding, WorldKindBinding):
        raise ProfileError(f"sort {sort.term!r} declares no identifier class and is not bound to a world kind")
    # A sort bound to a world kind has the kernel's record-id grammar as its class.
    return re.fullmatch(f"{re.escape(binding.world_kind)}:{_HEX64}", unicodedata.normalize("NFC", term)) is not None


def _class_text(sort: CompiledSort) -> str:
    if sort.identifier_class is not None:
        return f"pattern {sort.identifier_class.pattern!r}"
    binding = sort.binding
    assert isinstance(binding, WorldKindBinding)
    return f"`{binding.world_kind}:` followed by 64 lowercase hex characters"


def _referents_of(value: Referent | tuple[Member, ...]) -> tuple[Referent, ...]:
    if isinstance(value, Referent):
        return (value,)
    return tuple(member.referent for member in value)


def _sorts_of(value: Referent | tuple[Member, ...]) -> frozenset[str]:
    return frozenset(referent.sort for referent in _referents_of(value))


def _route_sorts(assignment: Mapping[str, frozenset[str]]) -> dict[str, list[str]]:
    return {role: sorted(sorts) for role, sorts in sorted(assignment.items())}


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
            f"{where} holds {type(value).__name__}, not a Referent. A `one` role holds a Referent, "
            "and a bare term carries no sort to check against the sorts the role admits."
        )


def require_identifier(value: object, where: str) -> None:
    """Every position in the projection is an identifier.

    A referent's two fields are the only ones a claim carries that are not
    matched against a table somewhere, so this is where that sentence has to be
    made true rather than assumed. Public: a composite's node also checks its
    sort and term against this same identifier grammar, and a second copy of
    the check is what this exists to avoid.
    """
    problem = not_an_identifier(value)
    if problem is not None:
        raise MalformedReferent(
            f"{where}: {problem}. Every position in π_claim is an identifier, and a referent's "
            "fields are the only ones no downstream check would catch."
        )
