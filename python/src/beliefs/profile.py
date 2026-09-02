"""``ProfileSpec`` — the sole compiled runtime profile.

D §6 closed substrate §12 by **retiring** the second per-kind source of truth
rather than picking a winner between two. One normative source — the `science`
base contract together with the activated domain contracts — and every runtime
artifact compiled from it:

    base contract  ─┐   (normative SSOT)
                    ├─▶  ProfileSpec  ─┬─▶  KindSpec set  (D4, deferred)
    domain contracts┘   (compiled)     └─▶  claim schemas (M7, here)

Only the claim-schema half is built. `KindSpec` compilation is **D4**, fully
deferred from cut 1, and an operator roster is not a per-kind artifact — an
operator belongs to no kind, which is why D §6 had to be widened rather than
merely read (M7).

**`ProfileSpec` resolves; contracts authorize** (§7.5). The two roles must not
blur, and the sharp consequence is that **`ProfileSpec`'s own identity never
appears in `π_claim` or in the consulted set**. If a compiled artifact were an
identity authority, recompiling — a different merge order, a different compiler —
could move claim identity with no contract edit anywhere, which is
`KIND_DESCRIPTORS`' defect one level up. What enters `belief_input_digest` is the
set of **contract** identities (D6), never the compiled artifact's.

``compiled_identity`` exists for a narrower job: it is what M7 means by
*"semantic-schema edits recompile, description edits do not."* It is derived from
the merged **schema projections** alone, so an editorial edit moves the contract
identity and leaves this one still. It is not an input to any claim.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from beliefs import stored
from beliefs.contract.base import BaseContract, ClaimGrammar
from beliefs.contract.coordination import CoordinationContract
from beliefs.contract.domain import DomainContract, OperatorDecl, VocabularyBinding
from beliefs.errors import (
    ContractMismatch,
    DuplicateContribution,
    ProfileError,
    UnparsedContract,
    WithdrawnFromAuthoring,
)
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "CompiledCoordinationKind",
    "CompiledDimension",
    "CompiledOperator",
    "CompiledSort",
    "ProfileSpec",
    "compile_profile",
]

PROFILE_DOMAIN = "science.profile.v1"

_MINT = object()
"""`compile_profile`'s own token — see `beliefs.contract.base._MINT` for what a
token achieves in this language and what it cannot."""


@dataclass(frozen=True)
class CompiledCoordinationKind:
    fields: frozenset[str]
    query_versions: frozenset[str]

    def projection(self) -> dict[str, object]:
        return {"fields": sorted(self.fields), "query_versions": sorted(self.query_versions)}


@dataclass(frozen=True)
class CompiledSort:
    term: str
    vocabulary: VocabularyBinding
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {"vocabulary": self.vocabulary.projection(), "retired": self.retired}


@dataclass(frozen=True)
class CompiledDimension:
    term: str
    restriction_sort: str
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {"restriction_sort": self.restriction_sort, "retired": self.retired}


@dataclass(frozen=True)
class CompiledOperator:
    """A declaration with every local name resolved to a term identifier.

    Resolution is the compiled artifact's whole job. `arg_sorts` and `dimensions`
    are written locally in a contract and are namespaced here, because a claim's
    projection carries **term identifiers** (§6.5) and a local name is not one.
    """

    term: str
    arity: int
    arg_sorts: tuple[str, ...]
    sign_apt: bool
    layers: tuple[str, ...]
    dimensions: tuple[str, ...]
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        # Sets are sorted, slots are not — see `OperatorDecl.schema_projection`.
        return {
            "arity": self.arity,
            "arg_sorts": list(self.arg_sorts),
            "sign_apt": self.sign_apt,
            "layers": sorted(self.layers),
            "dimensions": sorted(self.dimensions),
            "retired": self.retired,
        }


@sealed
@final
@dataclass(frozen=True, init=False)
class ProfileSpec:
    """**Compiled, never authored.**

    There is no public field-wise constructor, and the mappings below are read-only
    views over private copies. Both are the same requirement as M13's for `Claim`,
    one level up: an authored `ProfileSpec` would be the second per-kind source of
    truth D §6 retired, and a mutated one would carry a `compiled_identity`
    describing a profile that no longer exists.
    """

    claim_grammar: ClaimGrammar
    operators: Mapping[str, CompiledOperator]
    dimensions: Mapping[str, CompiledDimension]
    sorts: Mapping[str, CompiledSort]
    coordination_kinds: Mapping[str, CompiledCoordinationKind]
    coordination_address_root: str | None
    coordination_query_kinds: frozenset[str]
    coordination_query_relations: frozenset[str]

    base_contract_identity: str
    """Unconditional. D §8: a derivation reading no base-profile facet at all
    still consults the base contract, because a base contract can reinterpret a
    kernel kind or a relation signature."""

    activated_contracts: Mapping[str, str]
    """Namespace → content identity, for the domains **activated** in this
    profile.

    **Activated is not consulted, and the two must never be conflated.** D6's
    conditional arm is explicit that an activated-but-unconsulted contract
    contributes *nothing* to `belief_input_digest`; a computation that took
    ``activated_contracts.values()`` wholesale would move a belief because an
    unrelated domain was switched on, which is the exact defect D6's negative arm
    tests for. This is a **resolution table** — what a claim's identifiers can be
    resolved against — and the consulted subset is whatever a derivation actually
    reaches. Nothing here computes it: belief is outside cut 1, and §7.1's
    amendment widens the walk that would (operator, dimension, sort and
    vocabulary-binding triggers, not only facet namespaces).
    """

    compiled_identity: str

    # As in `Claim`: the lock is this method. `@dataclass` will not overwrite an
    # `__init__` the class already defines, so `init=False` is a backstop rather
    # than the mechanism.
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ProfileError(
            "ProfileSpec is compiled, never authored — use compile_profile(base, domains). "
            "D §6 closed substrate §12 by retiring the second per-kind source of truth; an "
            "authored profile would reintroduce it, and one built field-wise could carry a "
            "compiled_identity that describes a different profile than its own contents."
        )

    @classmethod
    def _compiled(cls, token: object, **fields: object) -> ProfileSpec:
        if token is not _MINT:
            raise ProfileError(
                "ProfileSpec._compiled is compile_profile's own route and takes its mint token; "
                "use compile_profile(base, domains)."
            )
        spec = object.__new__(cls)
        for name, value in fields.items():
            object.__setattr__(spec, name, value)
        return spec

    def projection(self) -> dict[str, object]:
        """The canonical projection ``compiled_identity`` is taken over.

        Exposed because the property that merge order is inert is **not**
        enforced here: `science.identity.v1` sorts object keys at encode time, so
        any insertion order already yields the same bytes. What would break it is
        a shape change — carrying the operators as a **sequence** rather than a
        map keyed by term — and that is what a test can check.
        """
        coordination = None
        if self.coordination_address_root is not None:
            coordination = {
                "address_root": self.coordination_address_root,
                "kinds": {
                    name: self.coordination_kinds[name].projection()
                    for name in sorted(self.coordination_kinds)
                },
                "query_vocabulary": {
                    "kinds": sorted(self.coordination_query_kinds),
                    "relations": sorted(self.coordination_query_relations),
                },
            }
        return _projection(
            self.claim_grammar,
            self.operators,
            self.dimensions,
            self.sorts,
            coordination=coordination,
        )

    def operator(self, term: str) -> CompiledOperator:
        """Resolve an operator term identifier, or refuse.

        §7.4 row 4a: a claim naming an operator whose declaring contract is not
        in the profile is a **local, static** failure, so it refuses here and
        nothing is minted. That is a different failure from 4b's cross-corpus
        conflict, which is only visible when a derivation assembles a closure.
        """
        try:
            return self.operators[term]
        except KeyError:
            raise ProfileError(
                f"no operator {term!r} in this profile. Operators are domain-issued (§7.1); "
                f"activated namespaces are {sorted(self.activated_contracts)}."
            ) from None

    def authorable_operators(self) -> tuple[str, ...]:
        """The operators the typed **authoring** constructor may offer.

        §7.3a: retirement lives in authoring, not in validation. A retired
        identifier is still *resolvable* — decode, import and restore type a
        historical claim against the frozen retired declaration — and refusing it
        at decode would corrupt exactly the history retirement exists to
        preserve. So this filter governs authoring only.

        **Retirement reaches an operator through its argument sorts.** Every slot
        of `Fin(arity(op))` must be filled, so an operator one of whose
        `arg_sorts` is retired cannot be authored at all: `Referent(s)` for a
        retired `s` has nothing an author may select. Offering the operator and
        then refusing every attempt to fill the slot would put the refusal one
        step too late, at a boundary §7.3a puts squarely in authoring.

        **Permitted dimensions do not reach it.** §6.2 makes `Dims(op)` the set
        of dimensions *permitted*, not required, so a retired dimension withdraws
        only itself — see `authorable_dimensions`.
        """
        return tuple(sorted(term for term, operator in self.operators.items() if self._is_authorable(operator)))

    def _is_authorable(self, operator: CompiledOperator) -> bool:
        if operator.retired:
            return False
        return all(not self.sorts[sort].retired for sort in operator.arg_sorts)

    def authorable_dimensions(self, term: str) -> tuple[str, ...]:
        """The qualifier dimensions an author may select on ``term``.

        **The operator's own authorability is checked first, and a withdrawn
        operator refuses.** A qualifier is a qualifier *of* a claim, and there is
        no claim to qualify at an operator that cannot be authored — offering a
        dimension for one would let an author assemble most of a claim before the
        boundary refused it, which is the same one-step-too-late failure that
        made `authorable_operators` reach through argument sorts.

        Refusing is also what keeps two different facts apart. An empty tuple is
        already the honest answer for a live operator that permits no dimensions
        — `subtype-of` is one — so returning it here would make *"withdrawn"* and
        *"has none"* the same answer, which is §7.5's `inapt`/`unsigned` collapse
        committed one level down.

        A dimension is itself withdrawn either by its own retirement or by the
        retirement of the sort its restrictions bind to: a restriction is sorted
        exactly as an argument is (§6.2), so a retired restriction sort leaves
        nothing selectable, and a dimension whose restriction cannot be bound is
        not a dimension an author can use.
        """
        operator = self.operator(term)
        if not self._is_authorable(operator):
            raise WithdrawnFromAuthoring(
                f"operator {term!r} is withdrawn from authoring — {self._withdrawal_reason(operator)}. "
                "§7.3a: it stays resolvable for decode, import and restore, which type a historical claim "
                "against the frozen declaration."
            )
        return tuple(
            sorted(
                dimension
                for dimension in operator.dimensions
                if not self.dimensions[dimension].retired
                and not self.sorts[self.dimensions[dimension].restriction_sort].retired
            )
        )

    def _withdrawal_reason(self, operator: CompiledOperator) -> str:
        if operator.retired:
            return "the operator is retired"
        retired = sorted({sort for sort in operator.arg_sorts if self.sorts[sort].retired})
        return f"its argument sorts {retired} are retired, so its slots cannot be filled"


def compile_profile(
    base: BaseContract,
    domains: Iterable[DomainContract],
    *,
    coordination: CoordinationContract | None = None,
) -> ProfileSpec:
    """Merge the base contract and the activated domain contracts.

    Merging happens **upstream** of any registration, which is why D §6 could
    report a zero `nodes` delta: `Registry` never sees two contributors for one
    kind because the compiled product is already one fully-composed spec.

    **Both inputs must have come from a parser**, and that check is what makes
    `ProfileSpec`'s own refusal to be authored worth anything. Without it the
    refusal certifies that this function ran, not that any document was read: a
    hand-built `BaseContract` and `DomainContract` compile to a perfectly genuine
    `ProfileSpec` resolving operators, sorts and layers that no contract declares
    — and the claims typed against it are indistinguishable from real ones, down
    to agreeing byte-for-byte with the other implementation.
    """
    if not isinstance(base, BaseContract):
        raise UnparsedContract(
            f"the base contract is a {type(base).__name__}, not a parsed BaseContract — use "
            "parse_base_contract(document, source=...) or load_base_contract(path). A profile compiled from "
            "an authored grammar would resolve claims against polarities and layers nobody declared."
        )
    if coordination is not None and not isinstance(coordination, CoordinationContract):
        raise UnparsedContract(
            f"the coordination contract is a {type(coordination).__name__}, not a parsed "
            "CoordinationContract — use parse_coordination_contract or load_coordination_contract."
        )
    if coordination is not None:
        unknown_kinds = set(coordination.query_kinds) - set(stored.WORLD_KINDS)
        unknown_relations = set(coordination.query_relations) - set(stored.WORLD_RELATIONS)
        if unknown_kinds or unknown_relations:
            raise ProfileError("coordination query vocabulary is outside the kernel inventory")
    activated = list(domains)
    for contract in activated:
        if not isinstance(contract, DomainContract):
            raise UnparsedContract(
                f"a domain contract is a {type(contract).__name__}, not a parsed DomainContract — use "
                "parse_domain_contract(document, source=..., base=..., predecessor=...) or "
                "load_domain_contract(path, base=...). Operators are domain-issued (§7.1), and an authored "
                "contract issues them on no authority."
            )
        # Provenance is not enough on its own: two contracts can each be entirely
        # genuine and still not belong together. A domain's layer selections are
        # checked once, at parse, against whatever base it was given, and the
        # compiled operator then carries them as facts — so a domain parsed under
        # a wider base and compiled under a narrower one yields a claim standing
        # on a layer the compiled base does not declare, with no forgery
        # anywhere. The check that was missing is between the two contracts.
        if contract.base_identity != base.content_identity:
            raise ContractMismatch(
                f"domain contract {contract.namespace!r} was typed against base contract "
                f"{contract.base_identity[:12]}…, and this profile is being compiled with "
                f"{base.content_identity[:12]}…. A domain selects its layers from the base vocabulary and "
                "may not extend it (§7.1); that check ran at parse time against a different document, so "
                "nothing here can stand behind it."
            )

    seen: dict[str, DomainContract] = {}
    for contract in activated:
        if contract.namespace in seen:
            raise DuplicateContribution(
                f"two contracts contribute to namespace {contract.namespace!r}. Contributions in different "
                "namespaces compose; two to one namespace are refused at compile, never last-writer-wins."
            )
        seen[contract.namespace] = contract

    sorts: dict[str, CompiledSort] = {}
    dimensions: dict[str, CompiledDimension] = {}
    operators: dict[str, CompiledOperator] = {}

    # Sorted for a reproducible construction order, which helps a reader diffing
    # two profiles. It is **not** what makes merge order inert: identity.v1 sorts
    # object keys at encode time, so this loop's order cannot reach the identity
    # either way. Recorded because the opposite is easy to assume — and was
    # assumed here first, until sabotaging the sort left the suite green.
    for namespace in sorted(seen):
        contract = seen[namespace]
        for name, decl in contract.sorts.items():
            sorts[contract.term(name)] = CompiledSort(
                term=contract.term(name), vocabulary=decl.vocabulary, retired=decl.retired, contract=namespace
            )
        for name, dimension in contract.dimensions.items():
            dimensions[contract.term(name)] = CompiledDimension(
                term=contract.term(name),
                restriction_sort=contract.term(dimension.restriction_sort),
                retired=dimension.retired,
                contract=namespace,
            )
        for name, operator in contract.operators.items():
            operators[contract.term(name)] = _compile_operator(contract, operator)

    coordination_kinds = (
        {
            name: CompiledCoordinationKind(
                fields=frozenset(declaration.fields),
                query_versions=frozenset(declaration.query_versions),
            )
            for name, declaration in coordination.kinds.items()
        }
        if coordination is not None
        else {}
    )
    coordination_projection = (
        _coordination_projection(coordination) if coordination is not None else None
    )
    activated_contracts = {ns: contract.content_identity for ns, contract in seen.items()}
    if coordination is not None:
        activated_contracts["coordination"] = coordination.content_identity

    return ProfileSpec._compiled(
        _MINT,
        claim_grammar=base.claim_grammar,
        # Wrapped so `compiled_identity` cannot come to describe a profile that
        # no longer exists. The `dict()` copy is insurance against a later
        # restructure that wraps something a caller still holds — today these are
        # compiler locals nobody else can reach, so sabotaging the copy alone
        # breaks nothing, and no test claims otherwise.
        operators=MappingProxyType(dict(operators)),
        dimensions=MappingProxyType(dict(dimensions)),
        sorts=MappingProxyType(dict(sorts)),
        coordination_kinds=MappingProxyType(dict(coordination_kinds)),
        coordination_address_root=(coordination.address_root if coordination is not None else None),
        coordination_query_kinds=(frozenset(coordination.query_kinds) if coordination is not None else frozenset()),
        coordination_query_relations=(
            frozenset(coordination.query_relations) if coordination is not None else frozenset()
        ),
        base_contract_identity=base.content_identity,
        activated_contracts=MappingProxyType(activated_contracts),
        compiled_identity=v1.digest(
            PROFILE_DOMAIN,
            _projection(
                base.claim_grammar,
                operators,
                dimensions,
                sorts,
                coordination=coordination_projection,
            ),
        ),
    )


def _coordination_projection(contract: CoordinationContract) -> dict[str, object]:
    return contract.schema_projection()


def _projection(
    claim_grammar: ClaimGrammar,
    operators: Mapping[str, CompiledOperator],
    dimensions: Mapping[str, CompiledDimension],
    sorts: Mapping[str, CompiledSort],
    *,
    coordination: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Every declaration is keyed **by term identifier**, never held positionally.

    That is the load-bearing choice. A sequence would make the merge order an
    identity input, so recompiling after activating the same domains in a
    different order would move the compiled identity — and D §6 retired the
    second per-kind source of truth precisely so that a compiled artifact could
    not drift from what it was compiled from.
    """
    projection: dict[str, object] = {
        # Closed *sets*, so sorted here too. The base contract keeps its authored
        # order in memory because that order is what a reader sees; it is not an
        # input to anything, since a kernel tag's bytes are its symbol.
        "claim_grammar": {
            "version": claim_grammar.version,
            "quantifiers": sorted(claim_grammar.quantifiers),
            "polarities": sorted(claim_grammar.polarities),
            "sign_inapt_tag": claim_grammar.sign_inapt_tag,
            "layers": sorted(claim_grammar.layers),
        },
        "operators": {term: decl.schema_projection() for term, decl in operators.items()},
        "dimensions": {term: decl.schema_projection() for term, decl in dimensions.items()},
        "sorts": {term: decl.schema_projection() for term, decl in sorts.items()},
    }
    if coordination is not None:
        projection["coordination"] = dict(coordination)
    return projection


def _compile_operator(contract: DomainContract, operator: OperatorDecl) -> CompiledOperator:
    return CompiledOperator(
        term=contract.term(operator.name),
        arity=operator.arity,
        arg_sorts=tuple(contract.term(sort) for sort in operator.arg_sorts),
        sign_apt=operator.sign_apt,
        layers=operator.layers,
        dimensions=tuple(contract.term(dimension) for dimension in operator.dimensions),
        retired=operator.retired,
        contract=contract.namespace,
    )
