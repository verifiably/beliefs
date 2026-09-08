"""``ProfileSpec`` — the sole compiled runtime profile.

D §6 closed substrate §12 by **retiring** the second per-kind source of truth
rather than picking a winner between two. One normative source — the `science`
base contract together with the activated domain contracts — and every runtime
artifact compiled from it:

    base contract  ─┐   (normative SSOT)
                    ├─▶  ProfileSpec  ─┬─▶  KindSpec set  (D4)
    domain contracts┘   (compiled)     └─▶  claim schemas (M7, here)

Kind and facet declarations compile into one private registry alongside the claim
schemas. Operators belong to no kind (M7).

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
from functools import cache
from importlib import resources
from types import MappingProxyType
from typing import final

from nodes.core.node import Node
from nodes.core.registry import KindSpec, Registry, Violation

from beliefs.contract.base import BaseContract, ClaimGrammar, FacetUse, RelationDecl
from beliefs.contract.coordination import CoordinationContract
from beliefs.contract.domain import DomainContract, OperatorDecl, VocabularyBinding, _name
from beliefs.contract.facets import FieldDecl
from beliefs.errors import (
    ContractMismatch,
    DuplicateContribution,
    MalformedContract,
    ProfileError,
    UnparsedContract,
    WithdrawnFromAuthoring,
)
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "CompiledCoordinationKind",
    "CompiledDimension",
    "CompiledFacet",
    "CompiledKind",
    "CompiledOperator",
    "CompiledSort",
    "ProfileSpec",
    "compile_profile",
    "shipped_base",
    "shipped_base_contract",
    "shipped_domain_contract",
]

PROFILE_DOMAIN = "science.profile.v1"

_MINT = object()
"""`compile_profile`'s own token — see `beliefs.contract.base._MINT` for what a
token achieves in this language and what it cannot."""


@cache
def shipped_base_contract() -> BaseContract:
    """Parse the base contract carried by this package."""
    from beliefs.contract.base import parse_base_contract
    from beliefs.contract.document import parse_document

    source = "beliefs/contracts/science/CONTRACT.yaml"
    text = resources.files("beliefs").joinpath("contracts/science/CONTRACT.yaml").read_text(encoding="utf-8")
    return parse_base_contract(parse_document(text, source=source), source=source)


@cache
def shipped_domain_contract(namespace: str) -> DomainContract:
    """Parse a domain contract carried by this package, against the shipped base."""
    from beliefs.contract.document import parse_document
    from beliefs.contract.domain import parse_domain_contract

    try:
        _name(namespace, "namespace")
    except MalformedContract:
        raise ProfileError(f"this package ships no domain contract for namespace {namespace!r}") from None
    source = f"beliefs/domains/{namespace}/DOMAIN.yaml"
    resource = resources.files("beliefs").joinpath(f"domains/{namespace}/DOMAIN.yaml")
    if not resource.is_file():
        raise ProfileError(f"this package ships no domain contract for namespace {namespace!r}")
    text = resource.read_text(encoding="utf-8")
    return parse_domain_contract(
        parse_document(text, source=source), source=source, base=shipped_base_contract(), predecessor=None
    )


@cache
def shipped_base() -> ProfileSpec:
    """Compile the base-only runtime profile once per process."""
    return compile_profile(shipped_base_contract(), [])


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


@dataclass(frozen=True)
class CompiledKind:
    name: str
    role: str  # "world" | "prose" — coordination kinds carry "coordination"
    domain: str | None
    facets: Mapping[str, FacetUse]
    covered: tuple[str, ...]
    """The covered facets **sorted by key by code point** — coverage order is never
    the authored order, so one contract identity yields one stamp (§4.2)."""
    contract: str

    def projection(self) -> dict[str, object]:
        # No null anywhere: `science.identity.v1` refuses it. An undomained kind
        # simply carries no `domain` key; its role says what it is.
        projection: dict[str, object] = {
            "role": self.role,
            "facets": {k: {"required": u.required, "covered": u.covered} for k, u in sorted(self.facets.items())},
        }
        if self.domain is not None:
            projection["domain"] = self.domain
        return projection


@dataclass(frozen=True)
class CompiledFacet:
    key: str
    shape: str
    attaches_to: frozenset[str]
    fields: Mapping[str, FieldDecl]
    contract: str

    def projection(self) -> dict[str, object]:
        return {
            "shape": self.shape,
            "fields": {name: field.projection() for name, field in sorted(self.fields.items())},
            "attaches_to": sorted(self.attaches_to),
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

    kinds: Mapping[str, CompiledKind]
    facets: Mapping[str, CompiledFacet]
    relations: Mapping[str, RelationDecl]
    _registry: Registry
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
                "kinds": {name: self.coordination_kinds[name].projection() for name in sorted(self.coordination_kinds)},
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
            kinds=self.kinds,
            facets=self.facets,
            relations=self.relations,
            coordination=coordination,
        )

    def facets_of(self, kind: str) -> Mapping[str, CompiledFacet]:
        """Every facet the kind may carry: its own declared facets and every domain
        facet attaching to it."""
        if kind not in self.kinds:
            raise ProfileError(f"kind {kind!r} is not in the compiled inventory")
        own = {key: self.facets[key] for key in self.kinds[kind].facets}
        attached = {key: f for key, f in self.facets.items() if kind in f.attaches_to}
        return MappingProxyType({**own, **attached})

    def validate_document(self, node: Node) -> None:
        """Kind registered and facet keys declared (G5, D4), raising `nodes`' own
        `UnknownKindError` / `FacetError`. The registry stays private: exposing it
        would let a caller register or mutate a kind without moving a pin."""
        self._registry.validate(node)

    def document_violations(self, node: Node) -> tuple[Violation, ...]:
        return tuple(self._registry.check(node))

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
        unknown_kinds = set(coordination.query_kinds) - {
            name for name, kind in base.kinds.items() if kind.role == "world"
        }
        unknown_relations = set(coordination.query_relations) - {
            name for name, relation in base.relations.items() if relation.group == "world"
        }
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

    kinds = {
        name: CompiledKind(
            name,
            decl.role,
            decl.domain,
            decl.facets,
            tuple(sorted(key for key, use in decl.facets.items() if use.covered)),
            "science",
        )
        for name, decl in base.kinds.items()
    }
    facets = {
        key: CompiledFacet(key, decl.shape, frozenset(), decl.fields, "science") for key, decl in base.facets.items()
    }
    if coordination is not None:
        for name in coordination.kinds:
            if name in kinds:
                raise DuplicateContribution(f"coordination kind {name!r} already declared by the base contract")
            kinds[name] = CompiledKind(
                name,
                "coordination",
                None,
                MappingProxyType({"coordination": FacetUse(True, False)}),
                (),
                "coordination",
            )
        if "coordination" in facets:
            raise DuplicateContribution("facet 'coordination' already declared by the base contract")
        facets["coordination"] = CompiledFacet(
            "coordination", "reader", frozenset(), MappingProxyType({}), "coordination"
        )
    for namespace in sorted(seen):
        for key, facet in seen[namespace].facets.items():
            for kind in facet.attaches_to:
                if kind not in kinds or kinds[kind].role != "world":
                    raise ProfileError(f"{key}: attaches_to names {kind!r}, not a world kind")
            facets[key] = CompiledFacet(key, facet.shape, frozenset(facet.attaches_to), facet.fields, namespace)
    for key, facet in facets.items():
        for name, field in facet.fields.items():
            for kind in field.kinds:
                if kind not in kinds:
                    raise ProfileError(f"{key}: field {name!r} names kind {kind!r}, not in the compiled inventory")
    registry = Registry()
    for name, kind in kinds.items():
        registry.register(
            KindSpec(
                name=name,
                required_facets={key for key, use in kind.facets.items() if use.required},
                optional_facets=(
                    {key for key, use in kind.facets.items() if not use.required}
                    | {key for key, facet in facets.items() if name in facet.attaches_to}
                    | ({"semantic-identity"} if kind.domain is not None else set())
                ),
            )
        )

    sorts: dict[str, CompiledSort] = {}
    dimensions: dict[str, CompiledDimension] = {}
    operators: dict[str, CompiledOperator] = {}

    # Sorted for a reproducible construction order, which helps a reader diffing
    # two profiles. It is **not** what makes merge order inert: identity.v1 sorts
    # object keys at encode time, so this loop's order cannot reach the identity
    # either way.
    for namespace in sorted(seen):
        contract = seen[namespace]
        for name, decl in contract.sorts.items():
            sorts[contract.term(name)] = CompiledSort(
                term=contract.term(name), vocabulary=decl.vocabulary, retired=decl.retired, contract=namespace
            )
    for namespace in sorted(seen):
        contract = seen[namespace]
        for name, dimension in contract.dimensions.items():
            dimensions[contract.term(name)] = CompiledDimension(
                term=contract.term(name),
                restriction_sort=_resolve_sort(
                    contract, dimension.restriction_sort, sorts, where=f"dimensions.{name}: restriction_sort"
                ),
                retired=dimension.retired,
                contract=namespace,
            )
        for name, operator in contract.operators.items():
            operators[contract.term(name)] = _compile_operator(contract, operator, sorts)

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
    coordination_projection = _coordination_projection(coordination) if coordination is not None else None
    activated_contracts = {ns: contract.content_identity for ns, contract in seen.items()}
    if coordination is not None:
        activated_contracts["coordination"] = coordination.content_identity

    return ProfileSpec._compiled(
        _MINT,
        kinds=MappingProxyType(kinds),
        facets=MappingProxyType(facets),
        relations=base.relations,
        _registry=registry,
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
                kinds=kinds,
                facets=facets,
                relations=base.relations,
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
    kinds: Mapping[str, CompiledKind],
    facets: Mapping[str, CompiledFacet],
    relations: Mapping[str, RelationDecl],
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
        "kinds": {name: kind.projection() for name, kind in kinds.items()},
        "facets": {key: facet.projection() for key, facet in facets.items()},
        "relations": {name: relation.projection() for name, relation in relations.items()},
        "operators": {term: decl.schema_projection() for term, decl in operators.items()},
        "dimensions": {term: decl.schema_projection() for term, decl in dimensions.items()},
        "sorts": {term: decl.schema_projection() for term, decl in sorts.items()},
    }
    if coordination is not None:
        projection["coordination"] = dict(coordination)
    return projection


def _resolve_sort(
    contract: DomainContract, name: str, sorts: Mapping[str, CompiledSort], *, where: str
) -> str:
    term = name if "/" in name else contract.term(name)
    if term not in sorts:
        namespace = term.partition("/")[0]
        raise MalformedContract(
            f"{contract.namespace}: {where} names sort {term!r}, but no contract for namespace {namespace!r} is "
            "compiled into this profile. A cross-contract slot resolves at compile or refuses; nothing here can "
            "stand behind a sort no compiled contract declares."
        )
    return term


def _compile_operator(
    contract: DomainContract, operator: OperatorDecl, sorts: Mapping[str, CompiledSort]
) -> CompiledOperator:
    return CompiledOperator(
        term=contract.term(operator.name),
        arity=operator.arity,
        arg_sorts=tuple(
            _resolve_sort(contract, sort, sorts, where=f"operators.{operator.name}: arg_sorts[{slot}]")
            for slot, sort in enumerate(operator.arg_sorts)
        ),
        sign_apt=operator.sign_apt,
        layers=operator.layers,
        dimensions=tuple(contract.term(dimension) for dimension in operator.dimensions),
        retired=operator.retired,
        contract=contract.namespace,
    )
