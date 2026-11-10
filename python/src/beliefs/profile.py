"""``ProfileSpec`` — the sole compiled runtime profile.

The second per-kind source of truth is **retired** rather than reconciled with
the first. There is one normative source — the `science`
base contract together with the activated domain contracts — and every runtime
artifact compiled from it:

    base contract  ─┐   (normative SSOT)
                    ├─▶  ProfileSpec  ─┬─▶  KindSpec set
    domain contracts┘   (compiled)     └─▶  claim schemas

Kind and facet declarations compile into one private registry alongside the claim
schemas: sorts, dimensions, templates, instantiations, bridges, estimand
declarations and duration conventions, with the admission index derived from the
instantiations. Operators (templates and bridges) belong to no kind.

**`ProfileSpec` resolves; contracts authorize**. The two roles must not
blur, and the sharp consequence is that **`ProfileSpec`'s own identity never
appears in `π_claim` or in the consulted set**. If a compiled artifact were an
identity authority, recompiling — a different merge order, a different compiler —
could move claim identity with no contract edit anywhere, which is
`KIND_DESCRIPTORS`' defect one level up. What enters `belief_input_digest` is the
set of **contract** identities, never the compiled artifact's.

``compiled_identity`` exists for a narrower job: it is the identity under which
*semantic-schema edits recompile and description edits do not.* It is derived from
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

from beliefs.contract.base import (
    BaseContract,
    ClaimGrammar,
    CompositeGrammar,
    EstimandGrammar,
    FacetUse,
    MeasurementGrammar,
    RelationDecl,
)
from beliefs.contract.coordination import CoordinationContract
from beliefs.contract.domain import (
    BridgeDecl,
    DimensionDecl,
    DomainContract,
    EstimandDecl,
    InstantiationDecl,
    SortBinding,
    TemplateDecl,
    _name,
)
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
from beliefs.patterns import IdentifierClass
from beliefs.sealed import sealed

__all__ = [
    "CompiledBridge",
    "CompiledCoordinationKind",
    "CompiledDimension",
    "CompiledDurationConvention",
    "CompiledEstimandDecl",
    "CompiledFacet",
    "CompiledInstantiation",
    "CompiledKind",
    "CompiledOperator",
    "CompiledRole",
    "CompiledSort",
    "CompiledTemplate",
    "ProfileSpec",
    "compile_profile",
    "shipped_base",
    "shipped_base_contract",
    "shipped_coordination",
    "shipped_domain_contract",
]

PROFILE_DOMAIN = "science.profile.v1"

_CLAIM_PLACEMENT = "claim"
"""The placement of a dimension a claim's qualifiers may carry; the other base
placement, `applicability`, is the estimand grammar's."""

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


def shipped_coordination(version: int = 2) -> CoordinationContract:
    """The coordination contract carried by this package: versions 1–3, each parsed against its
    immediate predecessor. The default is normalised before the cache, so `shipped_coordination()` and
    `shipped_coordination(2)` are one object."""
    if type(version) is not int:
        # `True in (1, 2)` holds and `@cache` would conflate True with 1
        raise ProfileError(f"a coordination contract version is an exact int, not {version!r}")
    if version not in (1, 2, 3):
        raise ProfileError(f"this package ships coordination contract versions 1, 2 and 3, not {version!r}")
    return _shipped_coordination(version)


@cache
def _shipped_coordination(version: int) -> CoordinationContract:
    from beliefs.contract.coordination import parse_coordination_contract
    from beliefs.contract.document import parse_document

    source = f"beliefs/contracts/coordination/v{version}/CONTRACT.yaml"
    text = (
        resources.files("beliefs")
        .joinpath(f"contracts/coordination/v{version}/CONTRACT.yaml")
        .read_text(encoding="utf-8")
    )
    predecessor = None if version == 1 else _shipped_coordination(version - 1)
    return parse_coordination_contract(parse_document(text, source=source), source=source, predecessor=predecessor)


@cache
def shipped_domain_contract(namespace: str) -> DomainContract:
    """Parse a domain contract carried by this package, against the shipped base.

    No pack ships under base v2: every contract is a genesis there, and a field's
    first v2 pack is its own design act. So the resource directory is empty and
    this refuses every namespace with ``ProfileError`` until one ships."""
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
    binding: SortBinding
    identifier_class: IdentifierClass | None
    categories: frozenset[str]
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        projection: dict[str, object] = {
            "binding": self.binding.projection(),
            "categories": sorted(self.categories),
            "retired": self.retired,
        }
        if self.identifier_class is not None:
            projection["identifier_class"] = {
                "prefix": self.identifier_class.prefix,
                "pattern": self.identifier_class.pattern,
            }
        return projection


@dataclass(frozen=True)
class CompiledDimension:
    term: str
    restriction_sort: str
    placement: str
    applies_to: frozenset[str]
    """The operator terms (templates and bridges) a claim over which may carry
    this dimension, each resolved at compile."""
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {
            "restriction_sort": self.restriction_sort,
            "placement": self.placement,
            "applies_to": sorted(self.applies_to),
            "retired": self.retired,
        }


@dataclass(frozen=True)
class CompiledRole:
    name: str
    arity: str
    min: int
    max: int | None
    coefficients: bool
    constraint: frozenset[str]

    def projection(self) -> dict[str, object]:
        projection: dict[str, object] = {
            "arity": self.arity,
            "coefficients": self.coefficients,
            "constraint": sorted(self.constraint),
        }
        if self.arity == "many":
            projection["min"] = self.min
            if self.max is not None:
                projection["max"] = self.max
        return projection


@dataclass(frozen=True)
class CompiledTemplate:
    """A template, under its operator term ``<namespace>/<name>``: what enters ``π_claim``."""

    term: str
    roles: Mapping[str, CompiledRole]
    sign_apt: bool
    layers: tuple[str, ...]
    forms: tuple[str, ...]
    edge: tuple[str, str] | None
    """``(cause role, effect role)``, read by composites; ``None`` forms no edge."""
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        projection: dict[str, object] = {
            "roles": {name: role.projection() for name, role in self.roles.items()},
            "sign_apt": self.sign_apt,
            "layers": sorted(self.layers),
            "forms": sorted(self.forms),
            "retired": self.retired,
        }
        if self.edge is not None:
            projection["edge"] = {"cause": self.edge[0], "effect": self.edge[1]}
        return projection


@dataclass(frozen=True)
class CompiledInstantiation:
    """An instantiation with its template and every listed sort resolved to term
    identifiers. Its term is bookkeeping and never enters claim identity."""

    term: str
    template: str
    roles: Mapping[str, frozenset[str]]
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {
            "template": self.template,
            "roles": {role: sorted(sorts) for role, sorts in self.roles.items()},
            "retired": self.retired,
        }


@dataclass(frozen=True)
class CompiledBridge:
    """A bridging relation, an operator of its own. Its roles are its template's
    and ``layers`` is the effective set: the declared narrowing, or the
    template's layers when it declares none."""

    term: str
    template: str
    mapping: str
    roles: Mapping[str, frozenset[str]]
    layers: tuple[str, ...]
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {
            "template": self.template,
            "mapping": self.mapping,
            "roles": {role: sorted(sorts) for role, sorts in self.roles.items()},
            "layers": sorted(self.layers),
            "retired": self.retired,
        }


CompiledOperator = CompiledTemplate | CompiledBridge
"""An operator a claim names: a template or a bridge, both ``<namespace>/<name>``."""


@dataclass(frozen=True)
class CompiledEstimandDecl:
    """An `estimands:` entry with every sort resolved to a term identifier, under
    the compiled typed address of its target (``instantiation:<namespace>/<name>``
    or ``bridge:<namespace>/<name>``).

    Interim role adaptation (beliefs-d64969); beliefs-f68a32 replaces the
    estimand structure around these names.
    """

    target: str
    level_sorts: Mapping[str, str]
    """Role name → sort term."""
    measure_sort: str
    identification_sort: str
    conditioning_sort: str
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {
            "level_sorts": {role: self.level_sorts[role] for role in sorted(self.level_sorts)},
            "measure_sort": self.measure_sort,
            "identification_sort": self.identification_sort,
            "conditioning_sort": self.conditioning_sort,
        }


@dataclass(frozen=True)
class CompiledDurationConvention:
    term: str
    fields: Mapping[str, str | int]
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {key: self.fields[key] for key in sorted(self.fields)}


@dataclass(frozen=True)
class CompiledKind:
    name: str
    role: str  # "world" | "prose" — coordination kinds carry "coordination"
    domain: str | None
    facets: Mapping[str, FacetUse]
    covered: tuple[str, ...]
    """The covered facets **sorted by key by code point** — coverage order is never
    the authored order, so one contract identity yields one stamp."""
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
    views over private copies. Both are the same requirement as the opacity of `Claim`,
    one level up: an authored `ProfileSpec` would be the second per-kind source of
    truth that was retired, and a mutated one would carry a `compiled_identity`
    describing a profile that no longer exists.
    """

    kinds: Mapping[str, CompiledKind]
    facets: Mapping[str, CompiledFacet]
    relations: Mapping[str, RelationDecl]
    _registry: Registry
    claim_grammar: ClaimGrammar
    composite_grammar: CompositeGrammar
    estimand_grammar: EstimandGrammar
    measurement_grammar: MeasurementGrammar
    sorts: Mapping[str, CompiledSort]
    dimensions: Mapping[str, CompiledDimension]
    templates: Mapping[str, CompiledTemplate]
    instantiations: Mapping[str, CompiledInstantiation]
    bridges: Mapping[str, CompiledBridge]
    estimands: Mapping[str, CompiledEstimandDecl]
    """Keyed by the compiled typed address of each declaration's target,
    ``instantiation:<namespace>/<name>`` or ``bridge:<namespace>/<name>``."""
    duration_conventions: Mapping[str, CompiledDurationConvention]
    admission: Mapping[str, tuple[str, ...]]
    """The admission index: template term → the typed addresses
    ``instantiation:<namespace>/<name>`` of every instantiation of it across the
    activated contracts, retired ones included, sorted. Built from the contract
    set alone, so no answer read from it depends on activation order."""
    coordination_kinds: Mapping[str, CompiledCoordinationKind]
    coordination_address_root: str | None
    coordination_query_kinds: frozenset[str]
    coordination_query_relations: frozenset[str]

    base_contract_identity: str
    """Unconditional: a derivation reading no base-profile facet at all
    still consults the base contract, because a base contract can reinterpret a
    kernel kind or a relation signature."""

    activated_contracts: Mapping[str, str]
    """Namespace → content identity, for the domains **activated** in this
    profile.

    **Activated is not consulted, and the two must never be conflated.** An
    activated-but-unconsulted contract contributes *nothing* to
    `belief_input_digest`; a computation that took
    ``activated_contracts.values()`` wholesale would move a belief because an
    unrelated domain was switched on, which is the defect the tests for an
    unconsulted contract exist to catch. This is a **resolution table** — what a claim's identifiers can be
    resolved against — and the consulted subset is whatever a derivation actually
    reaches. Nothing here computes it: the walk that would reaches through operator,
    instantiation, dimension, sort and binding triggers, not only facet namespaces.
    """

    compiled_identity: str

    # As in `Claim`: the lock is this method. `@dataclass` will not overwrite an
    # `__init__` the class already defines, so `init=False` is a backstop rather
    # than the mechanism.
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ProfileError(
            "ProfileSpec is compiled, never authored — use compile_profile(base, domains). "
            "The second per-kind source of truth was retired; an "
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
        a shape change — carrying the templates as a **sequence** rather than a
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
            self.estimand_grammar,
            self.measurement_grammar,
            self.composite_grammar,
            _ClaimTables(
                sorts=self.sorts,
                dimensions=self.dimensions,
                templates=self.templates,
                instantiations=self.instantiations,
                bridges=self.bridges,
                estimands=self.estimands,
                duration_conventions=self.duration_conventions,
            ),
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
        """Kind registered and facet keys declared, raising `nodes`' own
        `UnknownKindError` / `FacetError`. The registry stays private: exposing it
        would let a caller register or mutate a kind without moving a pin."""
        self._registry.validate(node)

    def document_violations(self, node: Node) -> tuple[Violation, ...]:
        return tuple(self._registry.check(node))

    def operator(self, term: str) -> CompiledOperator:
        """Resolve an operator term identifier — a template or a bridge — or refuse.

        A claim naming an operator whose declaring contract is not
        in the profile is a **local, static** failure, so it refuses here and
        nothing is minted. That is a different failure from a cross-corpus
        conflict, which is only visible when a derivation assembles a closure.
        Templates and bridges share one identity position, and a contract may not
        declare both under one name, so at most one table holds ``term``.
        """
        template = self.templates.get(term)
        if template is not None:
            return template
        bridge = self.bridges.get(term)
        if bridge is not None:
            return bridge
        raise ProfileError(
            f"no operator {term!r} in this profile. Operators (templates and bridges) are domain-issued; "
            f"activated namespaces are {sorted(self.activated_contracts)}."
        )

    def template_of(self, operator: CompiledOperator) -> CompiledTemplate:
        """The template whose roles, sign aptness, forms and edge ``operator``
        has: itself, or a bridge's template."""
        if isinstance(operator, CompiledTemplate):
            return operator
        try:
            return self.templates[operator.template]
        except KeyError:
            raise ProfileError(f"bridge {operator.term!r} maps to {operator.template!r}, not in this profile") from None

    def admitting(self, operator: str, assignment: Mapping[str, frozenset[str]], *, authoring: bool) -> tuple[str, ...]:
        """The typed addresses of the declarations admitting a claim over
        ``operator`` whose roles carry the sorts in ``assignment``.

        For a template, the instantiations (from the admission index, in its
        order) whose sort set for every role contains every sort the claim puts
        in that role; for a bridge, the bridge itself when its own sort sets do.
        ``authoring`` excludes retired declarations, as every authoring choice
        does; decode passes ``False``, since a historical claim stays typeable
        through a retired declaration. A reserved role (``within-model``) is
        admitted on every operator by the kernel, so it reaches no declaration;
        a role the template does not declare refuses.
        """
        declared = self.operator(operator)
        template = self.template_of(declared)
        roles: dict[str, frozenset[str]] = {}
        for role, sorts in assignment.items():
            if role in self.claim_grammar.reserved_roles:
                continue
            if role not in template.roles:
                raise ProfileError(f"{operator!r} declares no role {role!r}; its roles are {sorted(template.roles)}")
            if not isinstance(sorts, frozenset):
                raise ProfileError(f"{operator!r}: role {role!r} carries {sorts!r}, not a frozenset of sort terms")
            roles[role] = sorts
        routes: tuple[tuple[str, CompiledInstantiation | CompiledBridge], ...]
        if isinstance(declared, CompiledBridge):
            routes = ((f"bridge:{declared.term}", declared),)
        else:
            routes = tuple((address, self.declaration_at(address)) for address in self.admission[declared.term])
        return tuple(
            address
            for address, route in routes
            if not (authoring and route.retired) and all(sorts <= route.roles[role] for role, sorts in roles.items())
        )

    def estimand_declarations(self, operator: str, admitting: tuple[str, ...]) -> tuple[CompiledEstimandDecl, ...]:
        """The estimand declarations at the typed addresses ``admitting``, in the
        order given. An admitting declaration with no estimand declaration
        contributes none. Every address must be a declaration of ``operator``:
        an instantiation of it, or the bridge itself."""
        declared = self.operator(operator)
        found: list[CompiledEstimandDecl] = []
        for address in admitting:
            target = self.declaration_at(address)
            owner = target.term if isinstance(target, CompiledBridge) else target.template
            if owner != declared.term:
                raise ProfileError(f"{address!r} is a declaration of {owner!r}, not of operator {operator!r}")
            declaration = self.estimands.get(address)
            if declaration is not None:
                found.append(declaration)
        return tuple(found)

    def declaration_at(self, address: str) -> CompiledInstantiation | CompiledBridge:
        """Dereference a typed address, ``instantiation:<namespace>/<name>`` or
        ``bridge:<namespace>/<name>``. The tables stay keyed by term: the kind
        before the first ``:`` says which one to read."""
        kind, separator, term = address.partition(":")
        if not separator:
            raise ProfileError(
                f"{address!r} is not a typed address; expected `instantiation:<namespace>/<name>` or "
                "`bridge:<namespace>/<name>`"
            )
        if kind == "instantiation":
            instantiation = self.instantiations.get(term)
            if instantiation is None:
                raise ProfileError(f"no instantiation {term!r} in this profile")
            return instantiation
        if kind == "bridge":
            bridge = self.bridges.get(term)
            if bridge is None:
                raise ProfileError(f"no bridge {term!r} in this profile")
            return bridge
        raise ProfileError(f"{address!r}: {kind!r} is not an addressable declaration; expected instantiation or bridge")

    def claim_dimensions(self, operator: str) -> tuple[str, ...]:
        """The claim-side dimensions whose ``applies_to`` names ``operator``,
        sorted: the dimensions a claim over it may carry as qualifiers, wherever
        they are declared."""
        term = self.operator(operator).term
        return tuple(
            sorted(
                name
                for name, dimension in self.dimensions.items()
                if dimension.placement == _CLAIM_PLACEMENT and term in dimension.applies_to
            )
        )

    def authorable_operators(self) -> tuple[str, ...]:
        """The operators the typed **authoring** constructor may offer.

        Retirement lives in authoring, not in validation. A retired
        identifier is still *resolvable* — decode, import and restore type a
        historical claim against the frozen retired declaration — and refusing it
        at decode would corrupt exactly the history retirement exists to
        preserve. So this filter governs authoring only.

        **Retirement reaches a bridge through its template.** A bridge has its
        template's roles, forms and edge, so a retired template withdraws its
        bridges with it, as a composite refuses them as members.

        **Retirement reaches an operator through its routes.** A claim's roles
        are filled with sorts some live declaration admits: an instantiation of
        the template, or the bridge itself. An operator none of whose routes is
        live — retired, or listing only retired sorts for a role that must be
        filled — cannot be authored at all, and offering it would put the refusal
        one step too late.

        **Permitted dimensions do not reach it.** A dimension's ``applies_to``
        permits, it does not require, so a retired dimension withdraws only
        itself — see `authorable_dimensions`.
        """
        operators: tuple[CompiledOperator, ...] = (*self.templates.values(), *self.bridges.values())
        return tuple(sorted(operator.term for operator in operators if self._is_authorable(operator)))

    def _is_authorable(self, operator: CompiledOperator) -> bool:
        return not operator.retired and not self.template_of(operator).retired and self._has_live_route(operator)

    def _has_live_route(self, operator: CompiledOperator) -> bool:
        template = self.template_of(operator)
        routes: tuple[CompiledInstantiation | CompiledBridge, ...]
        if isinstance(operator, CompiledBridge):
            routes = (operator,)
        else:
            routes = tuple(self.declaration_at(address) for address in self.admission[operator.term])
        return any(
            not route.retired
            and all(
                template.roles[role].min == 0 or any(not self.sorts[sort].retired for sort in sorts)
                for role, sorts in route.roles.items()
            )
            for route in routes
        )

    def authorable_dimensions(self, term: str) -> tuple[str, ...]:
        """The qualifier dimensions an author may select on ``term``.

        **The operator's own authorability is checked first, and a withdrawn
        operator refuses.** A qualifier is a qualifier *of* a claim, and there is
        no claim to qualify at an operator that cannot be authored.

        Refusing is also what keeps two different facts apart. An empty tuple is
        already the honest answer for a live operator that permits no dimensions,
        so returning it here would make *"withdrawn"* and *"has none"* the same
        answer, which is the `inapt`/`unsigned` collapse committed one level down.

        A dimension is itself withdrawn either by its own retirement or by the
        retirement of the sort its restrictions bind to. Only claim-side
        dimensions are offered: an applicability-side one never appears in a
        claim's qualifiers.
        """
        operator = self.operator(term)
        if not self._is_authorable(operator):
            raise WithdrawnFromAuthoring(
                f"operator {term!r} is withdrawn from authoring — {self._withdrawal_reason(operator)}. "
                "It stays resolvable for decode, import and restore, which type a historical claim "
                "against the frozen declaration."
            )
        return tuple(
            dimension
            for dimension in self.claim_dimensions(term)
            if not self.dimensions[dimension].retired
            and not self.sorts[self.dimensions[dimension].restriction_sort].retired
        )

    def _withdrawal_reason(self, operator: CompiledOperator) -> str:
        if operator.retired:
            return "the operator is retired"
        template = self.template_of(operator)
        if template.retired:
            return f"its template {template.term!r} is retired"
        return (
            "no live route admits it: every instantiation of it (or, for a bridge, the bridge itself) is retired "
            "or lists only retired sorts for a role that must be filled"
        )


def compile_profile(
    base: BaseContract,
    domains: Iterable[DomainContract],
    *,
    coordination: CoordinationContract | None = None,
) -> ProfileSpec:
    """Merge the base contract and the activated domain contracts.

    Merging happens **upstream** of any registration, which is why the merge could
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
                "load_domain_contract(path, base=...). Operators are domain-issued, and an authored "
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
                "may not extend it; that check ran at parse time against a different document, so "
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

    # Sorted for a reproducible construction order, which helps a reader diffing
    # two profiles. It is **not** what makes merge order inert: identity.v1 sorts
    # object keys at encode time, so this loop's order cannot reach the identity
    # either way. The tables are built in dependency order — sorts and templates
    # first, from every contract, since a declaration may name another
    # contract's — and nothing resolved later can depend on activation order.
    contracts = [seen[namespace] for namespace in sorted(seen)]
    sorts = {
        contract.term(name): CompiledSort(
            term=contract.term(name),
            binding=decl.binding,
            identifier_class=decl.identifier_class,
            categories=frozenset(decl.categories),
            retired=decl.retired,
            contract=contract.namespace,
        )
        for contract in contracts
        for name, decl in contract.sorts.items()
    }
    templates = {
        contract.term(name): _compile_template(contract, decl)
        for contract in contracts
        for name, decl in contract.templates.items()
    }
    bridges = {
        contract.term(name): _compile_bridge(contract, decl, sorts, templates)
        for contract in contracts
        for name, decl in contract.bridges.items()
    }
    dimensions = {
        contract.term(name): _compile_dimension(contract, decl, sorts, templates, bridges)
        for contract in contracts
        for name, decl in contract.dimensions.items()
    }
    instantiations = {
        contract.term(name): _compile_instantiation(contract, decl, sorts, templates)
        for contract in contracts
        for name, decl in contract.instantiations.items()
    }
    estimands: dict[str, CompiledEstimandDecl] = {}
    for contract in contracts:
        for decl in contract.estimands.values():
            compiled = _compile_estimand(contract, decl, sorts, templates, instantiations, bridges)
            estimands[compiled.target] = compiled
    duration_conventions = {
        contract.term(name): CompiledDurationConvention(
            term=contract.term(name), fields=decl.fields, contract=contract.namespace
        )
        for contract in contracts
        for name, decl in contract.duration_conventions.items()
    }
    admission = {
        term: tuple(
            sorted(
                f"instantiation:{instantiation.term}"
                for instantiation in instantiations.values()
                if instantiation.template == term
            )
        )
        for term in templates
    }
    tables = _ClaimTables(
        # Wrapped so `compiled_identity` cannot come to describe a profile that
        # no longer exists. The `dict()` copy is insurance against a later
        # restructure that wraps something a caller still holds.
        sorts=MappingProxyType(dict(sorts)),
        dimensions=MappingProxyType(dict(dimensions)),
        templates=MappingProxyType(dict(templates)),
        instantiations=MappingProxyType(dict(instantiations)),
        bridges=MappingProxyType(dict(bridges)),
        estimands=MappingProxyType(dict(estimands)),
        duration_conventions=MappingProxyType(dict(duration_conventions)),
    )

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
        estimand_grammar=base.estimand_grammar,
        measurement_grammar=base.measurement_grammar,
        composite_grammar=base.composite_grammar,
        sorts=tables.sorts,
        dimensions=tables.dimensions,
        templates=tables.templates,
        instantiations=tables.instantiations,
        bridges=tables.bridges,
        estimands=tables.estimands,
        duration_conventions=tables.duration_conventions,
        admission=MappingProxyType(admission),
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
                base.estimand_grammar,
                base.measurement_grammar,
                base.composite_grammar,
                tables,
                kinds=kinds,
                facets=facets,
                relations=base.relations,
                coordination=coordination_projection,
            ),
        ),
    )


def _coordination_projection(contract: CoordinationContract) -> dict[str, object]:
    return contract.schema_projection()


@dataclass(frozen=True)
class _ClaimTables:
    """The compiled claim-vocabulary tables, each keyed by term (estimands by
    compiled typed address)."""

    sorts: Mapping[str, CompiledSort]
    dimensions: Mapping[str, CompiledDimension]
    templates: Mapping[str, CompiledTemplate]
    instantiations: Mapping[str, CompiledInstantiation]
    bridges: Mapping[str, CompiledBridge]
    estimands: Mapping[str, CompiledEstimandDecl]
    duration_conventions: Mapping[str, CompiledDurationConvention]


def _projection(
    claim_grammar: ClaimGrammar,
    estimand_grammar: EstimandGrammar,
    measurement_grammar: MeasurementGrammar,
    composite_grammar: CompositeGrammar,
    tables: _ClaimTables,
    *,
    kinds: Mapping[str, CompiledKind],
    facets: Mapping[str, CompiledFacet],
    relations: Mapping[str, RelationDecl],
    coordination: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Every declaration is keyed **by term identifier** (an estimand declaration
    by the compiled typed address of its target), never held positionally.

    That is the load-bearing choice. A sequence would make the merge order an
    identity input, so recompiling after activating the same domains in a
    different order would move the compiled identity — and the second per-kind source of truth was
    retired precisely so that a compiled artifact could not drift from what it was compiled from.
    The admission index is derived from the instantiations and is not projected.
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
        "estimand_grammar": estimand_grammar.projection(),
        "measurement_grammar": measurement_grammar.projection(),
        "composite_grammar": composite_grammar.projection(),
        "kinds": {name: kind.projection() for name, kind in kinds.items()},
        "facets": {key: facet.projection() for key, facet in facets.items()},
        "relations": {name: relation.projection() for name, relation in relations.items()},
        "sorts": {term: decl.schema_projection() for term, decl in tables.sorts.items()},
        "dimensions": {term: decl.schema_projection() for term, decl in tables.dimensions.items()},
        "templates": {term: decl.schema_projection() for term, decl in tables.templates.items()},
        "instantiations": {term: decl.schema_projection() for term, decl in tables.instantiations.items()},
        "bridges": {term: decl.schema_projection() for term, decl in tables.bridges.items()},
        "estimands": {address: decl.schema_projection() for address, decl in tables.estimands.items()},
        "duration_conventions": {term: decl.schema_projection() for term, decl in tables.duration_conventions.items()},
    }
    if coordination is not None:
        projection["coordination"] = dict(coordination)
    return projection


def _local_term(contract: DomainContract, reference: str) -> str:
    """A local name namespaced into ``contract``; a ``<namespace>/<name>`` reference as written."""
    return reference if "/" in reference else contract.term(reference)


def _resolve_sort(contract: DomainContract, name: str, sorts: Mapping[str, CompiledSort], *, where: str) -> str:
    term = _local_term(contract, name)
    if term not in sorts:
        namespace = term.partition("/")[0]
        raise MalformedContract(
            f"{contract.namespace}: {where} names sort {term!r}, but no compiled contract declares sort {term!r} "
            f"(namespace {namespace!r}). A cross-contract sort resolves at compile or refuses; nothing here can "
            "stand behind an undeclared sort."
        )
    return term


def _resolve_template(
    contract: DomainContract, reference: str, templates: Mapping[str, CompiledTemplate], *, where: str
) -> CompiledTemplate:
    term = _local_term(contract, reference)
    template = templates.get(term)
    if template is None:
        raise ProfileError(
            f"{contract.namespace}: {where} names template {term!r}, which no activated contract declares. An "
            "instantiation or bridge of an undeclared template has no roles to fill, so it refuses at compile."
        )
    return template


def _compile_template(contract: DomainContract, decl: TemplateDecl) -> CompiledTemplate:
    return CompiledTemplate(
        term=contract.term(decl.name),
        roles=MappingProxyType(
            {
                name: CompiledRole(
                    name=role.name,
                    arity=role.arity,
                    min=role.min,
                    max=role.max,
                    coefficients=role.coefficients,
                    constraint=frozenset(role.constraint),
                )
                for name, role in decl.roles.items()
            }
        ),
        sign_apt=decl.sign_apt,
        layers=decl.layers,
        forms=decl.forms,
        edge=decl.edge,
        retired=decl.retired,
        contract=contract.namespace,
    )


def _compile_role_sorts(
    contract: DomainContract,
    roles: Mapping[str, tuple[str, ...]],
    template: CompiledTemplate,
    sorts: Mapping[str, CompiledSort],
    *,
    where: str,
) -> Mapping[str, frozenset[str]]:
    """Resolve the sorts listed per role, after checking the role names match the
    template's exactly and every listed sort declares the categories the role's
    constraint requires."""
    lacking = sorted(set(roles) - set(template.roles))
    if lacking:
        raise ProfileError(
            f"{contract.namespace}: {where} names role(s) {', '.join(lacking)}, which {template.term!r} does not "
            f"declare; its roles are {sorted(template.roles)}"
        )
    omitted = sorted(set(template.roles) - set(roles))
    if omitted:
        raise ProfileError(
            f"{contract.namespace}: {where} omits role(s) {', '.join(omitted)} of {template.term!r}; every role "
            "lists the sorts that may fill it"
        )
    resolved: dict[str, frozenset[str]] = {}
    for role, listed in roles.items():
        terms = frozenset(_resolve_sort(contract, sort, sorts, where=f"{where}.{role}") for sort in listed)
        required = template.roles[role].constraint
        for term in sorted(terms):
            missing = required - sorts[term].categories
            if missing:
                raise ProfileError(
                    f"{contract.namespace}: {where}.{role} lists {term!r}, which does not declare the role "
                    f"categor(ies) {sorted(missing)} that {template.term!r}'s role {role!r} requires"
                )
        resolved[role] = terms
    return MappingProxyType(resolved)


def _compile_instantiation(
    contract: DomainContract,
    decl: InstantiationDecl,
    sorts: Mapping[str, CompiledSort],
    templates: Mapping[str, CompiledTemplate],
) -> CompiledInstantiation:
    where = f"instantiations.{decl.name}"
    template = _resolve_template(contract, decl.template, templates, where=f"{where}: template")
    return CompiledInstantiation(
        term=contract.term(decl.name),
        template=template.term,
        roles=_compile_role_sorts(contract, decl.roles, template, sorts, where=f"{where}: roles"),
        retired=decl.retired,
        contract=contract.namespace,
    )


def _compile_bridge(
    contract: DomainContract,
    decl: BridgeDecl,
    sorts: Mapping[str, CompiledSort],
    templates: Mapping[str, CompiledTemplate],
) -> CompiledBridge:
    where = f"bridges.{decl.name}"
    template = _resolve_template(contract, decl.template, templates, where=f"{where}: template")
    layers = template.layers
    if decl.layers is not None:
        wider = [layer for layer in decl.layers if layer not in template.layers]
        if wider:
            raise ProfileError(
                f"{contract.namespace}: {where}: layers {wider} are outside {template.term!r}'s layers "
                f"{list(template.layers)}. A bridge may narrow its template's layers, never widen them."
            )
        layers = decl.layers
    return CompiledBridge(
        term=contract.term(decl.name),
        template=template.term,
        mapping=decl.mapping,
        roles=_compile_role_sorts(contract, decl.roles, template, sorts, where=f"{where}: roles"),
        layers=layers,
        retired=decl.retired,
        contract=contract.namespace,
    )


def _compile_dimension(
    contract: DomainContract,
    decl: DimensionDecl,
    sorts: Mapping[str, CompiledSort],
    templates: Mapping[str, CompiledTemplate],
    bridges: Mapping[str, CompiledBridge],
) -> CompiledDimension:
    where = f"dimensions.{decl.name}"
    restriction_sort = _resolve_sort(contract, decl.restriction_sort, sorts, where=f"{where}: restriction_sort")
    applies_to: set[str] = set()
    for reference in decl.applies_to:
        # A local name resolves against this contract only, even when another
        # activated contract declares the same local name.
        term = _local_term(contract, reference)
        if term not in templates and term not in bridges:
            raise ProfileError(
                f"{contract.namespace}: {where}: applies_to names {term!r}, which is no operator (template or "
                "bridge) an activated contract declares"
            )
        applies_to.add(term)
    return CompiledDimension(
        term=contract.term(decl.name),
        restriction_sort=restriction_sort,
        placement=decl.placement,
        applies_to=frozenset(applies_to),
        retired=decl.retired,
        contract=contract.namespace,
    )


def _compile_estimand(
    contract: DomainContract,
    decl: EstimandDecl,
    sorts: Mapping[str, CompiledSort],
    templates: Mapping[str, CompiledTemplate],
    instantiations: Mapping[str, CompiledInstantiation],
    bridges: Mapping[str, CompiledBridge],
) -> CompiledEstimandDecl:
    where = f"estimands.{decl.target}"
    kind, _, name = decl.target.partition(":")
    term = contract.term(name)
    # The parser admits only a target this contract declares, so both lookups hold.
    target = instantiations[term] if kind == "instantiation" else bridges[term]
    template = templates[target.template]
    for role in decl.level_sorts:
        if role not in template.roles:
            raise ProfileError(
                f"{contract.namespace}: {where}: level_sorts names role {role!r}, which {template.term!r} does not "
                f"declare; its roles are {sorted(template.roles)}"
            )
    return CompiledEstimandDecl(
        target=f"{kind}:{term}",
        level_sorts=MappingProxyType(
            {
                role: _resolve_sort(contract, sort, sorts, where=f"{where}: level_sorts.{role}")
                for role, sort in decl.level_sorts.items()
            }
        ),
        measure_sort=_resolve_sort(contract, decl.measure_sort, sorts, where=f"{where}: measure_sort"),
        identification_sort=_resolve_sort(
            contract, decl.identification_sort, sorts, where=f"{where}: identification_sort"
        ),
        conditioning_sort=_resolve_sort(contract, decl.conditioning_sort, sorts, where=f"{where}: conditioning_sort"),
        contract=contract.namespace,
    )
