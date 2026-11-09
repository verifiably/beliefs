"""Domain contracts under base v2 — sorts, dimensions, relation templates,
instantiations, bridges, estimand declarations and duration conventions.

**Operators are domain-issued without exception**, and the base contract
may not issue one. An operator is a template or a bridge, identified as
``<namespace>/<name>``. A domain-neutral relation like ``subtype-of`` belongs to a
general-purpose domain contract, since nothing requires a "domain" to be a
natural science.

Two identities, deliberately different in kind:

    term identifier     authored, stable, namespaced      enters claim identity
    contract identity   content-derived, moves on edit    enters belief_input_digest

Succession is the *never redefine* rule made checkable. It compares the
**canonical schema projection** — the meaning-bearing fields — so an editorial
edit is free while a role's arity change is refused at load. Three fields are
deliberately outside that projection:

* ``description``, which is editorial by definition;
* a template's ``definition``, which is meaning-bearing prose but not schema:
  an editorial clarification is not a redefinition, and the assumptions
  register carries what the template does not establish; and
* ``retired``, because retirement is a status change and putting it in the
  projection would make **retiring** an identifier a redefinition of it, which
  is precisely the operation that must be permitted.

All three are inside the contract's content identity, like every other byte of
the document.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar, Self, final

from beliefs.contract.base import BaseContract
from beliefs.contract.facets import FacetDecl, parse_facet_declarations
from beliefs.errors import MalformedContract, SubclassRefused, SuccessionViolation, UnparsedContract
from beliefs.identifiers import not_a_canonical_identifier
from beliefs.identity import v1
from beliefs.patterns import IdentifierClass
from beliefs.sealed import sealed

__all__ = [
    "BridgeDecl",
    "DatasetBinding",
    "DimensionDecl",
    "DomainContract",
    "DurationConventionDecl",
    "EstimandDecl",
    "ExternalRef",
    "InstantiationDecl",
    "ReleaseBinding",
    "RoleDecl",
    "RunOutputBinding",
    "SchemeBinding",
    "SelectionBinding",
    "SortBinding",
    "SortDecl",
    "TemplateDecl",
    "WorldKindBinding",
    "check_succession",
    "load_domain_contract",
    "parse_binding",
    "parse_domain_contract",
]

DOMAIN_CONTRACT_DOMAIN = "science.contract.v1"

_MINT = object()
"""The parser's own token — see ``beliefs.contract.base._MINT`` for what a token
achieves in this language and what it cannot."""

_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
_HEX64 = "[0-9a-f]{64}"

_CONTRACT_FIELDS = frozenset({"contract", "version", "lineage", "sorts", "dimensions"})
_CONTRACT_OPTIONAL = frozenset(
    {"description", "templates", "instantiations", "bridges", "duration_conventions", "estimands", "facets"}
)
_V1_FIELDS = ("operators", "edges")
_SORT_FIELDS = frozenset({"binding"})
_SORT_OPTIONAL = frozenset({"identifier_class", "categories", "description", "retired"})
_DIMENSION_FIELDS = frozenset({"restriction_sort", "placement", "applies_to"})
_TEMPLATE_FIELDS = frozenset({"roles", "sign_apt", "layers", "forms"})
_TEMPLATE_OPTIONAL = frozenset({"edge", "definition", "external", "description", "retired"})
_ROLE_OPTIONAL = frozenset({"min", "max", "coefficients", "constraint"})
_INSTANTIATION_FIELDS = frozenset({"template", "roles"})
_BRIDGE_FIELDS = frozenset({"template", "mapping", "roles"})
_ESTIMAND_FIELDS = frozenset({"level_sorts", "measure_sort", "identification_sort", "conditioning_sort"})
_EDITORIAL = frozenset({"description", "retired"})

_ARITIES = ("one", "many")
_NULL_FORM = "null"
"""The form a sign-inapt template may not declare: a `null` claim carries the
inapt tag and asserts an effect absent, which only a signed relation has."""
_BRIDGE_REFUSED_MAPPINGS = ("exact", "broader")
_ESTIMAND_TARGET_KINDS = ("instantiation", "bridge")


# --- bindings -------------------------------------------------------------------

_ARMS_CLOSED = False


class SortBinding:
    """What a sort's terms are checked against: **exactly one of six arms**.

    A sealed tagged sum. Each arm is its own frozen dataclass, and the base
    admits exactly the six declared in this module: a seventh, declared anywhere
    later, is refused at class creation, and each arm is sealed in turn. That is
    what makes ``projection`` **injective** across arms: every projection carries
    the ``kind`` tag, so two arms whose remaining fields coincide never encode
    alike, and no subclass can override ``projection`` to collide with a genuine
    arm.

    Injectivity matters to two readers: a contract's identity, taken through
    ``SortDecl.schema_projection``, and a `ResolutionSnapshot`'s, taken over an
    order the encoded binding determines. The fields must also be **canonical**
    (NFC), because the encoding normalizes and two fields differing only in
    normalization are two Python keys and one encoded binding.

    Constructed by callers at `build_snapshot`, not only by the parser, so each
    arm checks its own fields' grammar at construction. The checks that need the
    base contract (that ``world_kind`` names a world kind, that the record-id
    prefixes name declared kinds) are ``parse_binding``'s.
    """

    __slots__ = ()
    kind: ClassVar[str]

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        if cls is SortBinding:
            raise TypeError("SortBinding is a sealed sum; construct one of its six arms")
        return super().__new__(cls)

    def __init_subclass__(cls, **kwargs: object) -> None:
        if _ARMS_CLOSED:
            raise SubclassRefused(
                f"SortBinding admits exactly the six arms the base contract's binding_kinds names; {cls.__name__} "
                "would be a seventh, whose projection nothing keeps distinct from the others."
            )
        super().__init_subclass__(**kwargs)

    def projection(self) -> dict[str, str]:
        """The binding as canonical data, ``kind`` included."""
        values = {field.name: getattr(self, field.name) for field in fields(self)}  # type: ignore[arg-type]
        return {"kind": self.kind, **values}


def _require_text(value: object, where: str) -> str:
    problem = not_a_canonical_identifier(value)
    if problem is not None:
        raise MalformedContract(f"{where}: {problem}.")
    assert isinstance(value, str)
    return value


def _require_record_id(value: object, kind: str, where: str) -> str:
    text = _require_text(value, where)
    if not re.fullmatch(f"{re.escape(kind)}:{_HEX64}", text):
        raise MalformedContract(
            f"{where}: {text!r} is not a {kind} record id, `{kind}:` followed by 64 lowercase hex characters"
        )
    return text


@sealed
@final
@dataclass(frozen=True)
class ReleaseBinding(SortBinding):
    """A vocabulary namespace at an explicit release. A bare namespace is not a
    binding: without a release the same identifier can mean different things in
    two checkouts, with no way to tell."""

    kind: ClassVar[str] = "release"
    namespace: str
    release: str

    def __post_init__(self) -> None:
        _require_text(self.namespace, "a release binding's namespace")
        _require_text(self.release, "a release binding's release")


@sealed
@final
@dataclass(frozen=True)
class DatasetBinding(SortBinding):
    """The members of one held dataset, by its record id."""

    kind: ClassVar[str] = "dataset"
    dataset: str

    def __post_init__(self) -> None:
        _require_record_id(self.dataset, "dataset", "a dataset binding's dataset")


@sealed
@final
@dataclass(frozen=True)
class SchemeBinding(SortBinding):
    """A computable identifier scheme: membership is the identifier-class check."""

    kind: ClassVar[str] = "scheme"
    scheme: str
    version: str

    def __post_init__(self) -> None:
        _require_text(self.scheme, "a scheme binding's scheme")
        _require_text(self.version, "a scheme binding's version")


@sealed
@final
@dataclass(frozen=True)
class SelectionBinding(SortBinding):
    """The dataset arm plus provenance: the members a classification rule
    selected from a catalogue, held as their own dataset."""

    kind: ClassVar[str] = "selection"
    dataset: str
    rule: str
    selected: str
    annotator: str

    def __post_init__(self) -> None:
        _require_record_id(self.dataset, "dataset", "a selection binding's dataset")
        _require_record_id(self.rule, "classification-rule", "a selection binding's rule")
        _require_record_id(self.selected, "dataset", "a selection binding's selected")
        _require_text(self.annotator, "a selection binding's annotator")


@sealed
@final
@dataclass(frozen=True)
class RunOutputBinding(SortBinding):
    """The dataset arm plus provenance: the dataset a run produced."""

    kind: ClassVar[str] = "run-output"
    run: str
    dataset: str

    def __post_init__(self) -> None:
        _require_record_id(self.run, "run", "a run-output binding's run")
        _require_record_id(self.dataset, "dataset", "a run-output binding's dataset")


@sealed
@final
@dataclass(frozen=True)
class WorldKindBinding(SortBinding):
    """Records of one kernel world kind; the kernel's record-id grammar is the
    sort's identifier class."""

    kind: ClassVar[str] = "world-kind"
    world_kind: str

    def __post_init__(self) -> None:
        _require_text(self.world_kind, "a world-kind binding's world_kind")
        if not _NAME.fullmatch(self.world_kind):
            raise MalformedContract(f"a world-kind binding's world_kind: {self.world_kind!r} is not a kind name")


_ARMS: Mapping[str, type[SortBinding]] = MappingProxyType(
    {
        arm.kind: arm
        for arm in (ReleaseBinding, DatasetBinding, SchemeBinding, SelectionBinding, RunOutputBinding, WorldKindBinding)
    }
)
_ARMS_CLOSED = True


def parse_binding(value: object, *, where: str, base: BaseContract) -> SortBinding:
    """Parse one sort's ``binding``: a mapping naming its arm by ``kind`` and
    carrying exactly that arm's fields."""
    body = _mapping(value, where)
    if "kind" not in body:
        raise MalformedContract(f"{where}: missing field(s) kind; a binding names its arm")
    kind = body["kind"]
    if not isinstance(kind, str) or kind not in base.claim_grammar.binding_kinds or kind not in _ARMS:
        raise MalformedContract(
            f"{where}: binding kind {kind!r} is not one of the base contract's binding_kinds "
            f"{list(base.claim_grammar.binding_kinds)}"
        )
    arm = _ARMS[kind]
    names = tuple(field.name for field in fields(arm))  # type: ignore[arg-type]
    # A field of another arm is an unknown field here: a binding carrying two
    # arms' fields is refused, never read as one of them.
    _fields(body, frozenset({"kind", *names}), frozenset(), where)
    values = {name: _require_text(body[name], f"{where}: {name}") for name in names}
    if kind == "selection":
        _require_base_kind("classification-rule", base, f"{where}: rule")
    if kind == "run-output":
        _require_base_kind("run", base, f"{where}: run")
    binding = _construct(arm, values, where)
    if isinstance(binding, WorldKindBinding):
        declared = base.kinds.get(binding.world_kind)
        if declared is None or declared.role != "world":
            raise MalformedContract(
                f"{where}: world_kind {binding.world_kind!r} is not a world kind the base contract declares"
            )
    return binding


def _construct(arm: type[SortBinding], values: Mapping[str, str], where: str) -> SortBinding:
    try:
        return arm(**values)
    except MalformedContract as error:
        raise MalformedContract(f"{where}: {error}") from None


def _require_base_kind(kind: str, base: BaseContract, where: str) -> None:
    if kind not in base.kinds:
        raise MalformedContract(f"{where}: names {kind!r} records, a kind the base contract does not declare")


# --- declarations ---------------------------------------------------------------


@dataclass(frozen=True)
class SortDecl:
    name: str
    binding: SortBinding
    identifier_class: IdentifierClass | None
    """``None`` exactly when the binding is ``world-kind``, whose class is the
    kernel's record-id grammar."""
    categories: tuple[str, ...]
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        projection: dict[str, object] = {"binding": self.binding.projection(), "categories": sorted(self.categories)}
        if self.identifier_class is not None:
            projection["identifier_class"] = {
                "prefix": self.identifier_class.prefix,
                "pattern": self.identifier_class.pattern,
            }
        return projection


@dataclass(frozen=True)
class DimensionDecl:
    """A dimension, on exactly one side: ``placement`` is ``claim`` or
    ``applicability``. ``applies_to`` lists the operators (local, or
    ``<namespace>/<name>``) a claim over which may carry it, resolved at compile."""

    name: str
    restriction_sort: str
    placement: str
    applies_to: tuple[str, ...]
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        return {
            "restriction_sort": self.restriction_sort,
            "placement": self.placement,
            "applies_to": sorted(self.applies_to),
        }


@dataclass(frozen=True)
class RoleDecl:
    """One role of a template. A ``one`` role holds one referent, its ``min``
    and ``max`` are both 1 and it admits no coefficient; a ``many`` role holds a multiset whose size
    lies in ``[min, max]`` (``max`` ``None`` is unbounded). ``constraint`` names
    the role categories a filling sort must declare."""

    name: str
    arity: str
    min: int
    max: int | None
    coefficients: bool
    constraint: tuple[str, ...]

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
class ExternalRef:
    """A reference to an external definition and how the template maps to it.
    Referencing a definition activates nothing."""

    reference: str
    mapping: str

    def projection(self) -> dict[str, object]:
        return {"reference": self.reference, "mapping": self.mapping}


@dataclass(frozen=True)
class TemplateDecl:
    """A relation template: its roles, sign aptness, layers, forms and, for a
    causal template, the edge its composites read."""

    name: str
    roles: Mapping[str, RoleDecl]
    sign_apt: bool
    layers: tuple[str, ...]
    forms: tuple[str, ...]
    edge: tuple[str, str] | None
    """``(cause role, effect role)``, or ``None`` for a template forming no edge."""
    definition: str | None
    external: ExternalRef | None
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        # `layers` and `forms` are sets, so they are sorted: holding a set in
        # the order its author typed it would make reordering a line of YAML a
        # redefinition. `definition` is prose and stays out.
        projection: dict[str, object] = {
            "roles": {name: role.projection() for name, role in self.roles.items()},
            "sign_apt": self.sign_apt,
            "layers": sorted(self.layers),
            "forms": sorted(self.forms),
        }
        if self.edge is not None:
            projection["edge"] = {"cause": self.edge[0], "effect": self.edge[1]}
        if self.external is not None:
            projection["external"] = self.external.projection()
        return projection


@dataclass(frozen=True)
class InstantiationDecl:
    """Which sorts may fill each role of a template, in this contract. Its name
    is bookkeeping and never enters claim identity."""

    name: str
    template: str
    roles: Mapping[str, tuple[str, ...]]
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        return {"template": self.template, "roles": {role: sorted(sorts) for role, sorts in self.roles.items()}}


@dataclass(frozen=True)
class BridgeDecl:
    """A bridging relation: an operator of its own that maps to a template
    (``narrower`` or ``contextual``), inherits its roles, sign aptness, forms
    and edge, declares the sorts filling each role, and may narrow its layers
    (``None`` inherits them)."""

    name: str
    template: str
    mapping: str
    roles: Mapping[str, tuple[str, ...]]
    layers: tuple[str, ...] | None
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        projection: dict[str, object] = {
            "template": self.template,
            "mapping": self.mapping,
            "roles": {role: sorted(sorts) for role, sorts in self.roles.items()},
        }
        if self.layers is not None:
            projection["layers"] = sorted(self.layers)
        return projection


@dataclass(frozen=True)
class EstimandDecl:
    """Which sorts fill the kernel's estimand structure for one instantiation or
    bridge. Keyed by the typed local address of its target, ``instantiation:<name>``
    or ``bridge:<name>``, since the two tables are separate namespaces and may
    share a name. Carries no `retired` of its own — retiring the target retires it.

    Interim role adaptation (beliefs-d64969); beliefs-f68a32 replaces the
    estimand structure around these names.
    """

    target: str
    level_sorts: Mapping[str, str]
    """Role name → sort. A role absent here admits only a `continuous` contrast."""
    measure_sort: str
    identification_sort: str
    conditioning_sort: str

    @property
    def retired(self) -> bool:
        return False

    def schema_projection(self) -> dict[str, object]:
        return {
            "level_sorts": {role: self.level_sorts[role] for role in sorted(self.level_sorts)},
            "measure_sort": self.measure_sort,
            "identification_sort": self.identification_sort,
            "conditioning_sort": self.conditioning_sort,
        }


@dataclass(frozen=True)
class DurationConventionDecl:
    """A duration convention: a mapping of scalar fields. beliefs-c23d2c fixes the
    fields; until then none is validated beyond being a string or an integer."""

    name: str
    fields: Mapping[str, str | int]

    @property
    def retired(self) -> bool:
        return False

    def schema_projection(self) -> dict[str, object]:
        return {key: self.fields[key] for key in sorted(self.fields)}


_Declaration = (
    SortDecl | DimensionDecl | TemplateDecl | InstantiationDecl | BridgeDecl | EstimandDecl | DurationConventionDecl
)


@sealed
@final
@dataclass(frozen=True, init=False)
class DomainContract:
    """**Parsed, never authored** — see ``BaseContract`` for why the lock is here
    rather than only on what is compiled from it.

    Operators, sorts and dimensions are **domain-issued without exception**,
    and this is the object that issues them. An authored one issues them
    on no authority at all.

    The declaration tables are read-only views over private dicts, for the reason
    ``ProfileSpec``'s are: ``content_identity`` is derived from the document at
    parse time, so a contract edited afterwards would carry an identity
    describing a document that no longer matches its contents — and a profile
    recompiled from it would resolve identifiers no document declares.
    """

    namespace: str
    version: int

    predecessor: str | None
    """``None`` is ``genesis``. Genesis is an escape hatch: the
    rules enforce immutability **within a declared lineage**, not across a
    namespace, and closing the parallel-genesis case needs governance the
    kernel does not supply (open; see the lineage rules in docs/contracts.md)."""

    sorts: Mapping[str, SortDecl]
    dimensions: Mapping[str, DimensionDecl]
    templates: Mapping[str, TemplateDecl]
    instantiations: Mapping[str, InstantiationDecl]
    bridges: Mapping[str, BridgeDecl]
    estimands: Mapping[str, EstimandDecl]
    """Keyed by typed local target, ``instantiation:<name>`` or ``bridge:<name>``."""
    duration_conventions: Mapping[str, DurationConventionDecl]
    facets: Mapping[str, FacetDecl]
    content_identity: str

    base_identity: str
    """The content identity of the base contract this domain was **typed
    against**, recorded so that compilation can check it is the same one.

    A domain's layer, form, placement, category and mapping selections are
    validated at parse time against a base contract, and nothing else ever
    revalidates them — the compiled declarations carry them as facts. So parsing
    under one base and compiling under another is not a forgery and needs no
    forged object: both contracts are genuine, both parsers did their jobs, and
    the result is a claim standing on a tag the compiled base does not declare.
    What was missing is not a check on either contract but a check **between**
    them, and this field is what makes that check possible.
    """

    # As in `BaseContract` and `ProfileSpec`: the lock is this method, and
    # `init=False` a backstop — `@dataclass` will not overwrite an `__init__` the
    # class already defines.
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise UnparsedContract(
            "DomainContract is parsed, never authored — use parse_domain_contract(document, source=..., "
            "base=..., predecessor=...). Operators, sorts and dimensions are domain-issued, and an "
            "authored contract issues them on no authority; it would also carry a content_identity for a "
            "document it does not contain, and skip the succession check entirely."
        )

    @classmethod
    def _parsed(
        cls,
        token: object,
        *,
        namespace: str,
        version: int,
        predecessor: str | None,
        sorts: dict[str, SortDecl],
        dimensions: dict[str, DimensionDecl],
        templates: dict[str, TemplateDecl],
        instantiations: dict[str, InstantiationDecl],
        bridges: dict[str, BridgeDecl],
        estimands: dict[str, EstimandDecl],
        duration_conventions: dict[str, DurationConventionDecl],
        facets: dict[str, FacetDecl],
        content_identity: str,
        base_identity: str,
    ) -> DomainContract:
        if token is not _MINT:
            raise UnparsedContract(
                "DomainContract._parsed is the parser's own route and takes its mint token; use "
                "parse_domain_contract(document, source=..., base=..., predecessor=...) or "
                "load_domain_contract(path, base=...)."
            )
        contract = object.__new__(cls)
        for name, value in (
            ("namespace", namespace),
            ("version", version),
            ("predecessor", predecessor),
            ("sorts", MappingProxyType(dict(sorts))),
            ("dimensions", MappingProxyType(dict(dimensions))),
            ("templates", MappingProxyType(dict(templates))),
            ("instantiations", MappingProxyType(dict(instantiations))),
            ("bridges", MappingProxyType(dict(bridges))),
            ("estimands", MappingProxyType(dict(estimands))),
            ("duration_conventions", MappingProxyType(dict(duration_conventions))),
            ("facets", MappingProxyType(dict(facets))),
            ("content_identity", content_identity),
            ("base_identity", base_identity),
        ):
            object.__setattr__(contract, name, value)
        return contract

    def term(self, local: str) -> str:
        """The namespaced term identifier — what enters ``π_claim``."""
        return f"{self.namespace}/{local}"

    def claim_vocabulary(self) -> dict[str, dict[str, object]]:
        """Every claim-vocabulary declaration, keyed by its typed address, and its
        canonical schema projection.

        The scope restriction is deliberate: these rules govern claim
        vocabulary and nothing else. An unscoped "every identifier" would
        quietly decide facet versioning, which is left open.
        """
        return {key: decl.schema_projection() for key, decl in self._declarations()}

    def retired_identifiers(self) -> frozenset[str]:
        """The tombstoned claim-vocabulary declarations, by typed address.

        Tracked beside the schema projection rather than inside it. Inside, the
        act of retiring would read as a redefinition and be refused; outside and
        unchecked, retirement would be reversible. It is neither: see
        ``check_succession``.
        """
        return frozenset(key for key, decl in self._declarations() if decl.retired)

    def _declarations(self) -> tuple[tuple[str, _Declaration], ...]:
        # Each table is its own namespace, so each key carries its table's tag:
        # the sort and the dimension `population` are two declarations, and so
        # are an instantiation and a bridge sharing a name. An estimand's key is
        # already a typed address, so its tag is followed by one.
        return (
            *((f"sort:{name}", decl) for name, decl in self.sorts.items()),
            *((f"dimension:{name}", decl) for name, decl in self.dimensions.items()),
            *((f"template:{name}", decl) for name, decl in self.templates.items()),
            *((f"instantiation:{name}", decl) for name, decl in self.instantiations.items()),
            *((f"bridge:{name}", decl) for name, decl in self.bridges.items()),
            *((f"estimand:{target}", decl) for target, decl in self.estimands.items()),
            *((f"duration-convention:{name}", decl) for name, decl in self.duration_conventions.items()),
        )


# --- parse helpers ----------------------------------------------------------------


def _mapping(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise MalformedContract(f"{where}: expected a mapping, found {type(value).__name__}")
    for key in value:
        if not isinstance(key, str):
            raise MalformedContract(f"{where}: key {key!r} is {type(key).__name__}, not a string")
    return value  # type: ignore[return-value]


def _fields(mapping: dict[str, object], required: frozenset[str], optional: frozenset[str], where: str) -> None:
    unknown = sorted(set(mapping) - required - optional)
    if unknown:
        raise MalformedContract(f"{where}: unknown field(s) {', '.join(unknown)}; refused, never ignored")
    missing = sorted(required - set(mapping))
    if missing:
        raise MalformedContract(f"{where}: missing field(s) {', '.join(missing)}")


def _name(value: object, where: str) -> str:
    if not isinstance(value, str) or not _NAME.fullmatch(value):
        raise MalformedContract(f"{where}: {value!r} is not an identifier; expected lowercase `[a-z][a-z0-9-]*`")
    return value


def _bool(value: object, where: str) -> bool:
    if not isinstance(value, bool):
        raise MalformedContract(f"{where}: expected true or false, found {value!r}")
    return value


def _no_duplicates(values: tuple[str, ...], where: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise MalformedContract(f"{where}: {value!r} appears twice")
        seen.add(value)


def _closed_list(value: object, allowed: tuple[str, ...], where: str, *, what: str, empty: bool) -> tuple[str, ...]:
    """A list drawn from one of the base contract's closed sets, without repeats."""
    if not isinstance(value, list) or (not empty and not value):
        raise MalformedContract(f"{where}: expected a {'' if empty else 'non-empty '}list of {what}s, found {value!r}")
    for i, item in enumerate(value):
        if not isinstance(item, str) or item not in allowed:
            raise MalformedContract(
                f"{where}[{i}]: {item!r} is not a {what} the base contract declares {list(allowed)}. A domain "
                "selects from the base vocabulary and may not extend it."
            )
    items = tuple(value)
    _no_duplicates(items, where)
    return items


def _reference(value: object, where: str, *, namespace: str, base_name: str, what: str) -> str:
    """A local name, or ``<namespace>/<name>`` naming another contract's
    declaration, deferred to compile."""
    if not isinstance(value, str) or not value:
        raise MalformedContract(f"{where}: {value!r} is not a {what} reference")
    if "/" not in value:
        return _name(value, where)
    foreign, _, local = value.partition("/")
    _name(foreign, f"{where}: namespace")
    _name(local, f"{where}: {what}")
    if foreign == namespace:
        raise MalformedContract(
            f"{where}: {value!r} names this contract's own namespace; a local {what} is spelled by its local "
            f"name {local!r} and nothing else"
        )
    if foreign == base_name:
        raise MalformedContract(
            f"{where}: {value!r} names the base contract, which declares no claim vocabulary; a {what} is a domain's"
        )
    return value


def _sort_reference(value: object, where: str, *, namespace: str, base_name: str, sorts: Mapping[str, SortDecl]) -> str:
    """Validate a local or deferred cross-contract sort reference."""
    reference = _reference(value, where, namespace=namespace, base_name=base_name, what="sort")
    if "/" not in reference and reference not in sorts:
        raise MalformedContract(f"{where}: {reference!r} is not a sort this contract declares")
    return reference


def _declarations(value: object, where: str) -> dict[str, object]:
    declarations = _mapping(value, where)
    for name in declarations:
        _name(name, f"{where}: {name}")
    return declarations


def _parse_lineage(value: object, where: str) -> str | None:
    if value == "genesis":
        return None
    lineage = _mapping(value, where)
    _fields(lineage, frozenset({"successor"}), frozenset(), where)
    predecessor = lineage["successor"]
    if not isinstance(predecessor, str) or not predecessor:
        raise MalformedContract(f"{where}: successor must name a predecessor contract identity, found {predecessor!r}")
    return predecessor


def _parse_identifier_class(value: object, where: str) -> IdentifierClass:
    body = _mapping(value, where)
    _fields(body, frozenset({"prefix", "pattern"}), frozenset(), where)
    prefix, pattern = body["prefix"], body["pattern"]
    if not isinstance(prefix, str) or not isinstance(pattern, str):
        raise MalformedContract(f"{where}: prefix and pattern are strings, found {prefix!r} and {pattern!r}")
    try:
        return IdentifierClass(prefix=prefix, pattern=pattern)
    except MalformedContract as error:
        raise MalformedContract(f"{where}: {error}") from None


def _parse_sort(name: str, value: object, where: str, base: BaseContract) -> SortDecl:
    body = _mapping(value, where)
    _fields(body, _SORT_FIELDS, _SORT_OPTIONAL, where)
    binding = parse_binding(body["binding"], where=f"{where}: binding", base=base)
    identifier_class: IdentifierClass | None = None
    if isinstance(binding, WorldKindBinding):
        if "identifier_class" in body:
            raise MalformedContract(
                f"{where}: identifier_class is refused on a world-kind sort; its class is the kernel's record-id "
                "grammar, `<kind>:` followed by 64 lowercase hex"
            )
    else:
        if "identifier_class" not in body:
            raise MalformedContract(
                f"{where}: identifier_class is required on a {binding.kind!r} binding; it is what a term is checked "
                "against at claim construction"
            )
        identifier_class = _parse_identifier_class(body["identifier_class"], f"{where}: identifier_class")
    categories = _closed_list(
        body.get("categories", []),
        base.claim_grammar.role_categories,
        f"{where}: categories",
        what="role category",
        empty=True,
    )
    return SortDecl(
        name=name,
        binding=binding,
        identifier_class=identifier_class,
        categories=categories,
        retired=_bool(body.get("retired", False), f"{where}: retired"),
    )


def _parse_role(name: str, value: object, where: str, base: BaseContract) -> RoleDecl:
    body = _mapping(value, where)
    _fields(body, frozenset({"arity"}), _ROLE_OPTIONAL, where)
    arity = body["arity"]
    if arity not in _ARITIES:
        raise MalformedContract(f"{where}: arity is `one` or `many`, found {arity!r}")
    if arity == "one":
        for field in ("min", "max", "coefficients"):
            if field in body:
                raise MalformedContract(
                    f"{where}: `{field}` is declared on a `one` role; min, max and coefficients apply to a "
                    "`many` role only"
                )
        minimum, maximum = 1, 1
    else:
        minimum = _count(body.get("min", 1), f"{where}: min", floor=0)
        maximum = None
        if "max" in body:
            maximum = _count(body["max"], f"{where}: max", floor=max(minimum, 1))
    return RoleDecl(
        name=name,
        arity=str(arity),
        min=minimum,
        max=maximum,
        coefficients=_bool(body.get("coefficients", False), f"{where}: coefficients"),
        constraint=_closed_list(
            body.get("constraint", []),
            base.claim_grammar.role_categories,
            f"{where}: constraint",
            what="role category",
            empty=True,
        ),
    )


def _count(value: object, where: str, *, floor: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < floor:
        raise MalformedContract(f"{where}: expected an integer of at least {floor}, found {value!r}")
    return value


def _parse_template(name: str, value: object, where: str, base: BaseContract) -> TemplateDecl:
    body = _mapping(value, where)
    _fields(body, _TEMPLATE_FIELDS, _TEMPLATE_OPTIONAL, where)
    grammar = base.claim_grammar

    roles: dict[str, RoleDecl] = {}
    for role_name, role_body in _mapping(body["roles"], f"{where}: roles").items():
        role_where = f"{where}: roles.{role_name}"
        _name(role_name, role_where)
        if role_name in grammar.reserved_roles:
            raise MalformedContract(
                f"{role_where}: {role_name!r} is a role the base contract reserves on every operator; no "
                "template may declare it"
            )
        roles[role_name] = _parse_role(role_name, role_body, role_where, base)

    sign_apt = _bool(body["sign_apt"], f"{where}: sign_apt")
    layers = _closed_list(body["layers"], grammar.layers, f"{where}: layers", what="layer", empty=False)
    forms = _closed_list(body["forms"], grammar.forms, f"{where}: forms", what="form", empty=False)
    if _NULL_FORM in forms and not sign_apt:
        raise MalformedContract(
            f'{where}: forms includes "{_NULL_FORM}" on a sign-inapt template. A null claim asserts an effect '
            "absent, which only a signed relation has."
        )

    edge: tuple[str, str] | None = None
    if "edge" in body:
        edge = _parse_edge(body["edge"], f"{where}: edge", roles=roles, layers=layers)

    definition: str | None = None
    if "definition" in body:
        text = body["definition"]
        if not isinstance(text, str) or not text.strip():
            raise MalformedContract(f"{where}: definition is prose, found {text!r}")
        definition = text

    external: ExternalRef | None = None
    if "external" in body:
        external_where = f"{where}: external"
        reference = _mapping(body["external"], external_where)
        _fields(reference, frozenset({"reference", "mapping"}), frozenset(), external_where)
        mapping = reference["mapping"]
        if not isinstance(mapping, str) or mapping not in grammar.mapping_types:
            raise MalformedContract(
                f"{external_where}: mapping {mapping!r} is not one of the base contract's mapping_types "
                f"{list(grammar.mapping_types)}"
            )
        external = ExternalRef(
            reference=_require_text(reference["reference"], f"{external_where}: reference"), mapping=mapping
        )

    return TemplateDecl(
        name=name,
        roles=MappingProxyType(roles),
        sign_apt=sign_apt,
        layers=layers,
        forms=forms,
        edge=edge,
        definition=definition,
        external=external,
        retired=_bool(body.get("retired", False), f"{where}: retired"),
    )


def _parse_edge(
    value: object, where: str, *, roles: Mapping[str, RoleDecl], layers: tuple[str, ...]
) -> tuple[str, str]:
    body = _mapping(value, where)
    _fields(body, frozenset({"cause", "effect"}), frozenset(), where)
    if "causal" not in layers:
        raise MalformedContract(f"{where}: the template admits no causal layer, so it forms no edge")
    cause, effect = body["cause"], body["effect"]
    for position, role in (("cause", cause), ("effect", effect)):
        if not isinstance(role, str) or role not in roles:
            raise MalformedContract(f"{where}: {position} {role!r} is not a role this template declares")
    assert isinstance(cause, str) and isinstance(effect, str)
    if cause == effect:
        raise MalformedContract(f"{where}: cause and effect must be distinct roles, both are {cause!r}")
    return cause, effect


def _parse_role_sorts(
    value: object, where: str, *, resolve: Callable[[object, str], str]
) -> Mapping[str, tuple[str, ...]]:
    roles: dict[str, tuple[str, ...]] = {}
    for role, sorts in _mapping(value, where).items():
        role_where = f"{where}.{role}"
        _name(role, role_where)
        if not isinstance(sorts, list) or not sorts:
            raise MalformedContract(f"{role_where}: expected a non-empty list of sorts, found {sorts!r}")
        listed = tuple(resolve(sort, f"{role_where}[{i}]") for i, sort in enumerate(sorts))
        _no_duplicates(listed, role_where)
        roles[role] = listed
    return MappingProxyType(roles)


def _parse_estimand_target(
    key: str,
    where: str,
    *,
    instantiations: Mapping[str, InstantiationDecl],
    bridges: Mapping[str, BridgeDecl],
) -> str:
    kind, separator, name = key.partition(":")
    if not separator or kind not in _ESTIMAND_TARGET_KINDS:
        raise MalformedContract(
            f"{where}: {key!r} is not a typed target. An estimand declaration is keyed `instantiation:<name>` or "
            "`bridge:<name>`: the two tables are separate namespaces, and an untyped key cannot say which it names."
        )
    _name(name, f"{where}: {kind} name")
    declared = instantiations if kind == "instantiation" else bridges
    if name not in declared:
        raise MalformedContract(f"{where}: {name!r} is not a {kind} this contract declares")
    return key


def parse_domain_contract(
    document: object, *, source: str, base: BaseContract, predecessor: DomainContract | None
) -> DomainContract:
    """Validate a parsed domain-contract document, or refuse it.

    The base contract is required because a domain's selections are checked
    against it: layers, forms, placements, role categories, binding kinds and
    mapping types are **base-owned closed sets**, and a domain that could extend
    one would be redefining what kind of thing a claim is.

    ``predecessor`` is required for the reason given on ``load_domain_contract``,
    and the check runs **here** rather than only at the file boundary. Validating
    only on the path that happens to read a file would leave the same contract
    admissible through the path that does not, which is not a weaker guarantee
    but an unstated one.

    **Both dependencies are authenticated.** A parser that takes another parsed
    artifact and trusts it by shape has the hole its own callers were closed
    against, one level in: the closed-set checks below are only as good as the
    base contract handed to them, and the succession check only as good as the
    predecessor. Which base was used is then recorded on the result, so that
    compilation can tell whether the contract in front of it was typed against
    the base it is being compiled with.

    References to another contract's declarations (``<namespace>/<name>``) are
    checked for form here and resolved at compile, which is where the other
    contract is.
    """
    if not isinstance(base, BaseContract):
        raise UnparsedContract(
            f"base is a {type(base).__name__}, not a parsed BaseContract — use parse_base_contract("
            "document, source=...) or load_base_contract(path). A domain's selections are checked against "
            "the base contract and against nothing else afterwards."
        )
    if predecessor is not None and not isinstance(predecessor, DomainContract):
        raise UnparsedContract(
            f"predecessor is a {type(predecessor).__name__}, not a parsed DomainContract. Succession is "
            "the *never redefine* rule made checkable; checked against an authored predecessor it "
            "certifies nothing, since the thing it compares against was written to pass."
        )
    root = _mapping(document, source)
    for section in ("kinds", "relations"):
        if section in root:
            raise MalformedContract(
                f"{source}: a domain contract declares no {section}; a kernel kind or relation signature is the "
                "base contract's, and a domain contributes facets to kinds that already exist — refused"
            )
    v1_fields = [section for section in _V1_FIELDS if section in root]
    if v1_fields:
        raise MalformedContract(
            f"{source}: unknown field(s) {', '.join(v1_fields)}; the v1 grammar's operators and edges are replaced "
            "by templates, instantiations and bridges under base v2, so a v1 document cannot parse by accident — "
            "refused, never ignored"
        )
    _fields(root, _CONTRACT_FIELDS, _CONTRACT_OPTIONAL, source)

    namespace = _name(root["contract"], f"{source}: contract")
    if namespace == "coordination":
        raise MalformedContract(f"{source}: 'coordination' is reserved for the coordination contract")
    if namespace == base.name:
        raise MalformedContract(
            f"{source}: {namespace!r} is the base contract's namespace. Operators are domain-issued without "
            "exception, and a base-issued operator would sit outside the closure walk every other "
            "operator goes through."
        )

    version = root["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise MalformedContract(f"{source}: version must be a positive integer, found {version!r}")

    grammar = base.claim_grammar

    sorts = {
        name: _parse_sort(name, body, f"{source}: sorts.{name}", base)
        for name, body in _declarations(root["sorts"], f"{source}: sorts").items()
    }

    def resolve(value: object, where: str) -> str:
        return _sort_reference(value, where, namespace=namespace, base_name=base.name, sorts=sorts)

    def operator(value: object, where: str) -> str:
        return _reference(value, where, namespace=namespace, base_name=base.name, what="operator")

    dimensions: dict[str, DimensionDecl] = {}
    for name, body in _declarations(root["dimensions"], f"{source}: dimensions").items():
        where = f"{source}: dimensions.{name}"
        decl = _mapping(body, where)
        _fields(decl, _DIMENSION_FIELDS, _EDITORIAL, where)
        placement = decl["placement"]
        if not isinstance(placement, str) or placement not in grammar.placements:
            raise MalformedContract(
                f"{where}: placement {placement!r} is not one of the base contract's placements "
                f"{list(grammar.placements)}"
            )
        raw_applies = decl["applies_to"]
        if not isinstance(raw_applies, list):
            raise MalformedContract(f"{where}: applies_to must be a list of operators, found {raw_applies!r}")
        applies_to = tuple(operator(item, f"{where}: applies_to[{i}]") for i, item in enumerate(raw_applies))
        _no_duplicates(applies_to, f"{where}: applies_to")
        dimensions[name] = DimensionDecl(
            name=name,
            restriction_sort=resolve(decl["restriction_sort"], f"{where}: restriction_sort"),
            placement=placement,
            applies_to=applies_to,
            retired=_bool(decl.get("retired", False), f"{where}: retired"),
        )

    templates = {
        name: _parse_template(name, body, f"{source}: templates.{name}", base)
        for name, body in _declarations(root.get("templates", {}), f"{source}: templates").items()
    }

    instantiations: dict[str, InstantiationDecl] = {}
    for name, body in _declarations(root.get("instantiations", {}), f"{source}: instantiations").items():
        where = f"{source}: instantiations.{name}"
        decl = _mapping(body, where)
        _fields(decl, _INSTANTIATION_FIELDS, _EDITORIAL, where)
        instantiations[name] = InstantiationDecl(
            name=name,
            template=_reference(
                decl["template"], f"{where}: template", namespace=namespace, base_name=base.name, what="template"
            ),
            roles=_parse_role_sorts(decl["roles"], f"{where}: roles", resolve=resolve),
            retired=_bool(decl.get("retired", False), f"{where}: retired"),
        )

    bridges: dict[str, BridgeDecl] = {}
    for name, body in _declarations(root.get("bridges", {}), f"{source}: bridges").items():
        where = f"{source}: bridges.{name}"
        decl = _mapping(body, where)
        _fields(decl, _BRIDGE_FIELDS, frozenset({"layers", *_EDITORIAL}), where)
        if name in templates:
            raise MalformedContract(
                f"{where}: {name!r} is also a template of this contract. Templates and bridges are both operators, "
                f"identified only as `{namespace}/{name}`, so the two would collide on one operator identifier."
            )
        mapping = decl["mapping"]
        if not isinstance(mapping, str) or mapping not in grammar.mapping_types:
            raise MalformedContract(
                f"{where}: mapping {mapping!r} is not one of the base contract's mapping_types "
                f"{list(grammar.mapping_types)}"
            )
        if mapping in _BRIDGE_REFUSED_MAPPINGS:
            raise MalformedContract(
                f"{where}: mapping {mapping!r} is refused on a bridge: an exact bridge is its template, and a "
                "broader one commits to less than the evidence form it bridges to. A bridge is narrower or "
                "contextual."
            )
        layers = None
        if "layers" in decl:
            layers = _closed_list(decl["layers"], grammar.layers, f"{where}: layers", what="layer", empty=False)
        bridges[name] = BridgeDecl(
            name=name,
            template=_reference(
                decl["template"], f"{where}: template", namespace=namespace, base_name=base.name, what="template"
            ),
            mapping=mapping,
            roles=_parse_role_sorts(decl["roles"], f"{where}: roles", resolve=resolve),
            layers=layers,
            retired=_bool(decl.get("retired", False), f"{where}: retired"),
        )

    facets = parse_facet_declarations(root.get("facets", {}), where=f"{source}: facets", namespace=namespace)

    estimands: dict[str, EstimandDecl] = {}
    for key, body in _mapping(root.get("estimands", {}), f"{source}: estimands").items():
        where = f"{source}: estimands.{key}"
        target = _parse_estimand_target(key, where, instantiations=instantiations, bridges=bridges)
        decl = _mapping(body, where)
        _fields(decl, _ESTIMAND_FIELDS, frozenset({"description"}), where)
        level_sorts: dict[str, str] = {}
        for role, sort in _mapping(decl["level_sorts"], f"{where}: level_sorts").items():
            _name(role, f"{where}: level_sorts key")
            level_sorts[role] = resolve(sort, f"{where}: level_sorts.{role}")
        estimands[target] = EstimandDecl(
            target=target,
            level_sorts=MappingProxyType(level_sorts),
            measure_sort=resolve(decl["measure_sort"], f"{where}: measure_sort"),
            identification_sort=resolve(decl["identification_sort"], f"{where}: identification_sort"),
            conditioning_sort=resolve(decl["conditioning_sort"], f"{where}: conditioning_sort"),
        )

    duration_conventions: dict[str, DurationConventionDecl] = {}
    for name, body in _declarations(root.get("duration_conventions", {}), f"{source}: duration_conventions").items():
        where = f"{source}: duration_conventions.{name}"
        scalars: dict[str, str | int] = {}
        for field, scalar in _mapping(body, where).items():
            if isinstance(scalar, bool) or not isinstance(scalar, str | int):
                raise MalformedContract(f"{where}: {field} is a string or an integer, found {scalar!r}")
            scalars[field] = scalar
        duration_conventions[name] = DurationConventionDecl(name=name, fields=MappingProxyType(scalars))

    contract = DomainContract._parsed(
        _MINT,
        namespace=namespace,
        version=version,
        predecessor=_parse_lineage(root["lineage"], f"{source}: lineage"),
        sorts=sorts,
        dimensions=dimensions,
        templates=templates,
        instantiations=instantiations,
        bridges=bridges,
        estimands=estimands,
        duration_conventions=duration_conventions,
        facets=facets,
        content_identity=v1.digest(DOMAIN_CONTRACT_DOMAIN, root),
        base_identity=base.content_identity,
    )
    check_succession(contract, predecessor)
    return contract


def check_succession(contract: DomainContract, predecessor: DomainContract | None) -> None:
    """The two-contract succession check, refused at contract **load**, not at claim decode.

    A content-derived identity says what a contract *is* and never what it
    *succeeds*, which is why the predecessor is passed in rather than derived.
    """
    if contract.predecessor is None:
        if predecessor is not None:
            raise SuccessionViolation(
                f"{contract.namespace}: declares genesis but a predecessor was supplied. Genesis means "
                "compared against nothing; validating it against a contract anyway would report a lineage "
                "the document does not claim."
            )
        return

    if predecessor is None:
        raise SuccessionViolation(
            f"{contract.namespace}: declares successor({contract.predecessor}) but no predecessor was supplied. "
            "The check is a two-contract check and cannot be performed against one; skipping it would let a "
            "redefinition through on the evidence that nobody looked."
        )
    if predecessor.content_identity != contract.predecessor:
        raise SuccessionViolation(
            f"{contract.namespace}: declares successor({contract.predecessor}) but the supplied predecessor's "
            f"content identity is {predecessor.content_identity}"
        )
    if predecessor.namespace != contract.namespace:
        raise SuccessionViolation(
            f"{contract.namespace}: cannot succeed a contract in namespace {predecessor.namespace!r}"
        )

    current, prior = contract.claim_vocabulary(), predecessor.claim_vocabulary()

    dropped = sorted(set(prior) - set(current))
    if dropped:
        raise SuccessionViolation(
            f"{contract.namespace}: drops claim-vocabulary declaration(s) {', '.join(dropped)}. A retired "
            "declaration is retained immutably as a tombstone — dropping one renders an existing claim "
            "population untypeable, which is redefinition arriving by another route."
        )

    for identifier in sorted(set(prior) & set(current)):
        if prior[identifier] != current[identifier]:
            raise SuccessionViolation(
                f"{contract.namespace}: {identifier} has a different canonical schema projection than in its "
                "predecessor. Redefinition is refused within a declared lineage — retire the identifier and "
                "issue a new one, which keeps every prior assertion bound to what it actually asserted."
            )

    resurrected = sorted((predecessor.retired_identifiers() - contract.retired_identifiers()) & set(current))
    if resurrected:
        raise SuccessionViolation(
            f"{contract.namespace}: un-retires {', '.join(resurrected)}. Retirement is one-way.\n"
            "Retirement belongs to **authoring** — the typed constructor cannot select a retired identifier — "
            "so the retired set is what decides whether a claim was authorable when it was written. If that set "
            "can shrink, it is not reconstructible from any point in the lineage, and two contracts in one "
            "lineage disagree about whether an existing claim was legitimately authored, with the later one "
            "silently winning. That is a change to what already-written records mean, which is exactly what "
            "redefinition is — arriving through the status field instead of the schema field, which is why "
            "keeping `retired` out of the schema projection needs this rule beside it and not instead of it."
        )


def load_domain_contract(path: Path, *, base: BaseContract, predecessor: DomainContract | None) -> DomainContract:
    """Read, validate and **succession-check** the domain contract at ``path``.

    ``predecessor`` is required and has no default, including for a genesis
    contract, which passes an explicit ``None``. A default would make the check
    skippable by omission, and an unperformed check that reports success is the
    failure mode this corpus names most often: *a failure to look is not a
    finding of absence.*
    """
    from beliefs.contract.document import load_document

    document = load_document(path, source=str(path))
    return parse_domain_contract(document, source=str(path), base=base, predecessor=predecessor)
