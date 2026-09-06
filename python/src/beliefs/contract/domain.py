"""Domain contracts — operators, dimensions and sorts.

§7.1: **operators are domain-issued without exception**, and the base contract
may not issue one. A domain-neutral relation like ``subtype-of`` belongs to a
general-purpose domain contract, since nothing requires a "domain" to be a
natural science.

Two identities, deliberately different in kind (§7.3):

    term identifier     authored, stable, namespaced      enters claim identity
    contract identity   content-derived, moves on edit    enters belief_input_digest

Succession (§8.3) is the *never redefine* rule made checkable. It compares the
**canonical schema projection** — the meaning-bearing fields — so an editorial
edit is free while an `arity` change is refused at load. Two fields are
deliberately outside that projection:

* ``description``, which is editorial by definition; and
* ``retired``, because retirement is a status change and putting it in the
  projection would make **retiring** an identifier a redefinition of it, which
  is precisely the operation §7.3a requires to be permitted.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import final

from beliefs.contract.base import BaseContract
from beliefs.contract.facets import FacetDecl, parse_facet_declarations
from beliefs.errors import MalformedContract, SuccessionViolation, UnparsedContract
from beliefs.identifiers import not_a_canonical_identifier
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "DimensionDecl",
    "DomainContract",
    "OperatorDecl",
    "SortDecl",
    "VocabularyBinding",
    "check_succession",
    "load_domain_contract",
    "parse_domain_contract",
]

DOMAIN_CONTRACT_DOMAIN = "science.contract.v1"

_MINT = object()
"""The parser's own token — see ``beliefs.contract.base._MINT`` for what a token
achieves in this language and what it cannot."""

_NAME = re.compile(r"^[a-z][a-z0-9-]*$")

_CONTRACT_FIELDS = frozenset({"contract", "version", "lineage", "sorts", "dimensions", "operators"})
_OPERATOR_FIELDS = frozenset({"arity", "arg_sorts", "sign_apt", "layers", "dimensions"})
_OPERATOR_OPTIONAL = frozenset({"description", "retired"})
_DIMENSION_FIELDS = frozenset({"restriction_sort"})
_SORT_FIELDS = frozenset({"vocabulary"})


@sealed
@final
@dataclass(frozen=True)
class VocabularyBinding:
    """D §5: a held ontology dataset by content identity, **or** a namespace with
    an explicit release. **A bare namespace is refused** — the binding is exact or
    it is absent, and a binding without a release would let the same identifier
    mean different things in two checkouts.

    That *or* is a sum, and three optional fields are a product: the record shape
    admits inhabitants D §5 does not have, and one of them is dangerous.
    ``projection`` drops ``namespace`` and ``release`` on the dataset arm — which
    is correct, since on that arm they carry no information — so a value holding
    *both* a dataset identity and a namespace projects as though the namespace
    were not there. Two such bindings that differ, and are therefore distinct keys
    resolved against different vocabularies, encode identically; any identity
    taken over a collection of them stops being determined by its contents. So
    the sum is enforced here, at construction, which is the only place that can
    make ``projection`` **injective** — and enforcing the sum is only half of it.
    The fields must also be **canonical**, because the encoding normalizes to NFC
    and two fields that differ only in normalization are two Python keys and one
    encoded binding. Same collision, arriving through the text rather than through
    the shape. Two readers depend on that: a contract's
    content identity, taken through ``SortDecl.schema_projection``, and a
    `ResolutionSnapshot`'s, taken over an order the encoded binding determines.
    Colliding bindings would let two different contracts share one content
    identity — which is what ``ContractMismatch`` compares — and let one snapshot
    take two identities depending on the order its bindings were supplied.

    Sealed, and alone among the declaration types in this module in being so. The
    others are reachable only through the parser, inside a branded contract; this
    one is **constructed by callers**, at `build_snapshot`, where a subclass
    overriding ``projection`` would reopen the collision with the constructor
    check still in place.
    """

    namespace: str | None
    release: str | None
    dataset_identity: str | None

    def __post_init__(self) -> None:
        if self.dataset_identity is not None:
            _require_binding_text(self.dataset_identity, "a binding's dataset identity")
            if self.namespace is not None or self.release is not None:
                raise MalformedContract(
                    f"a binding names dataset {self.dataset_identity!r} and also namespace "
                    f"{self.namespace!r}/{self.release!r}. D §5's binding is one arm or the other; a value "
                    "carrying both projects as the dataset alone, so two bindings resolved against different "
                    "vocabularies would encode identically."
                )
            return
        _require_binding_text(self.namespace, "a binding's namespace")
        _require_binding_text(self.release, "a binding's release")

    def projection(self) -> dict[str, object]:
        if self.dataset_identity is not None:
            return {"dataset": self.dataset_identity}
        return {"namespace": self.namespace, "release": self.release}


def _require_binding_text(value: object, where: str) -> None:
    problem = not_a_canonical_identifier(value)
    if problem is not None:
        raise MalformedContract(f"{where}: {problem}.")


@dataclass(frozen=True)
class SortDecl:
    name: str
    vocabulary: VocabularyBinding
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        return {"vocabulary": self.vocabulary.projection()}


@dataclass(frozen=True)
class DimensionDecl:
    name: str
    restriction_sort: str
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        return {"restriction_sort": self.restriction_sort}


@dataclass(frozen=True)
class OperatorDecl:
    """§6.2's declared schemas, and nothing else: ``arity``, ``arg_sorts``,
    ``sign_apt``, ``layers``, ``dimensions`` are exactly ``arity(op)``,
    ``ArgSort(op)``, ``signApt(op)``, ``Layers(op)``, ``Dims(op)``.

    ``RestrictionSort(op)`` is resolved through the dimension declarations rather
    than restated per operator, so two operators sharing ``population`` cannot
    disagree about what a population restriction binds to.
    """

    name: str
    arity: int
    arg_sorts: tuple[str, ...]
    sign_apt: bool
    layers: tuple[str, ...]
    dimensions: tuple[str, ...]
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        # `arg_sorts` is positional and `layers`/`dimensions` are not, and the
        # difference is §6.2's: `ArgSort(op) : Fin(arity(op)) → Sort` is a
        # function on slots, while `Dims(op)` and `Layers(op)` are *finite sets*.
        # Holding a set in the order its author happened to type it would make
        # reordering one line of YAML a **redefinition**, refused at load — a
        # false positive at the one place the corpus can least afford one.
        return {
            "arity": self.arity,
            "arg_sorts": list(self.arg_sorts),
            "sign_apt": self.sign_apt,
            "layers": sorted(self.layers),
            "dimensions": sorted(self.dimensions),
        }


@sealed
@final
@dataclass(frozen=True, init=False)
class DomainContract:
    """**Parsed, never authored** — see ``BaseContract`` for why the lock is here
    rather than only on what is compiled from it.

    Operators, sorts and dimensions are **domain-issued without exception**
    (§7.1), and this is the object that issues them. An authored one issues them
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
    """``None`` is ``genesis``. §8.3 records that genesis is an escape hatch: the
    rules enforce immutability **within a declared lineage**, not across a
    namespace, and closing the parallel-genesis case needs governance this design
    does not supply (ρC1, open)."""

    sorts: Mapping[str, SortDecl]
    dimensions: Mapping[str, DimensionDecl]
    operators: Mapping[str, OperatorDecl]
    facets: Mapping[str, FacetDecl]
    content_identity: str

    base_identity: str
    """The content identity of the base contract this domain was **typed
    against**, recorded so that compilation can check it is the same one.

    A domain's layer selections are validated at parse time against a base
    contract, and nothing else ever revalidates them — the compiled operator
    carries the layers as facts. So parsing under one base and compiling under
    another is not a forgery and needs no forged object: both contracts are
    genuine, both parsers did their jobs, and the result is a claim standing on a
    layer the compiled base does not declare. What was missing is not a check on
    either contract but a check **between** them, and this field is what makes
    that check possible.
    """

    # As in `BaseContract` and `ProfileSpec`: the lock is this method, and
    # `init=False` a backstop — `@dataclass` will not overwrite an `__init__` the
    # class already defines.
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise UnparsedContract(
            "DomainContract is parsed, never authored — use parse_domain_contract(document, source=..., "
            "base=..., predecessor=...). Operators, sorts and dimensions are domain-issued (§7.1), and an "
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
        operators: dict[str, OperatorDecl],
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
            ("operators", MappingProxyType(dict(operators))),
            ("facets", MappingProxyType(dict(facets))),
            ("content_identity", content_identity),
            ("base_identity", base_identity),
        ):
            object.__setattr__(contract, name, value)
        return contract

    def term(self, local: str) -> str:
        """The namespaced term identifier — what enters ``π_claim`` (§6.5)."""
        return f"{self.namespace}/{local}"

    def claim_vocabulary(self) -> dict[str, dict[str, object]]:
        """Every claim-vocabulary identifier and its canonical schema projection.

        §8.3's scope restriction is deliberate: these rules govern claim
        vocabulary and nothing else. An unscoped "every identifier" would have
        this design quietly deciding facet versioning, which D §12 leaves open.
        """
        return {key: decl.schema_projection() for key, decl in self._declarations()}

    def retired_identifiers(self) -> frozenset[str]:
        """The tombstoned claim-vocabulary identifiers.

        Tracked beside the schema projection rather than inside it. Inside, the
        act of retiring would read as a redefinition and be refused; outside and
        unchecked, retirement would be reversible. It is neither: see
        ``check_succession``.
        """
        return frozenset(key for key, decl in self._declarations() if decl.retired)

    def _declarations(self) -> tuple[tuple[str, SortDecl | DimensionDecl | OperatorDecl], ...]:
        return (
            *((f"sort:{name}", decl) for name, decl in self.sorts.items()),
            *((f"dimension:{name}", decl) for name, decl in self.dimensions.items()),
            *((f"operator:{name}", decl) for name, decl in self.operators.items()),
        )


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


def _parse_vocabulary(value: object, where: str) -> VocabularyBinding:
    if isinstance(value, str):
        if not value.startswith("dataset:") or not value[len("dataset:") :]:
            raise MalformedContract(f"{where}: {value!r} is not a binding; expected `dataset:<content-identity>`")
        return VocabularyBinding(namespace=None, release=None, dataset_identity=value[len("dataset:") :])
    binding = _mapping(value, where)
    _fields(binding, frozenset({"namespace", "release"}), frozenset(), where)
    namespace, release = binding["namespace"], binding["release"]
    if not isinstance(namespace, str) or not namespace or not isinstance(release, str) or not release:
        raise MalformedContract(
            f"{where}: a namespace binding needs a non-empty namespace and an explicit release. "
            "A bare namespace is refused (D §5) — without a release the same identifier can mean "
            "different things in two checkouts, with no way to tell."
        )
    return VocabularyBinding(namespace=namespace, release=release, dataset_identity=None)


def _parse_lineage(value: object, where: str) -> str | None:
    if value == "genesis":
        return None
    lineage = _mapping(value, where)
    _fields(lineage, frozenset({"successor"}), frozenset(), where)
    predecessor = lineage["successor"]
    if not isinstance(predecessor, str) or not predecessor:
        raise MalformedContract(f"{where}: successor must name a predecessor contract identity, found {predecessor!r}")
    return predecessor


def _parse_operator(name: str, value: object, where: str) -> OperatorDecl:
    body = _mapping(value, where)
    _fields(body, _OPERATOR_FIELDS, _OPERATOR_OPTIONAL, where)

    arity = body["arity"]
    if isinstance(arity, bool) or not isinstance(arity, int) or arity < 0:
        raise MalformedContract(f"{where}: arity must be a non-negative integer, found {arity!r}")

    raw_sorts = body["arg_sorts"]
    if not isinstance(raw_sorts, list):
        raise MalformedContract(f"{where}: arg_sorts must be a list, found {raw_sorts!r}")
    arg_sorts = tuple(_name(item, f"{where}: arg_sorts[{i}]") for i, item in enumerate(raw_sorts))
    if len(arg_sorts) != arity:
        raise MalformedContract(
            f"{where}: arity is {arity} but arg_sorts has {len(arg_sorts)} entries. "
            "ArgSort(op) is a function on Fin(arity(op)); a mismatch leaves a slot with no sort or a sort with no slot."
        )

    raw_layers = body["layers"]
    if not isinstance(raw_layers, list) or not raw_layers:
        raise MalformedContract(
            f"{where}: layers must be a non-empty list. §6.2: an operator admitting no layer would make "
            "Claim uninhabited at that operator."
        )
    layers = tuple(_name(item, f"{where}: layers[{i}]") for i, item in enumerate(raw_layers))
    _no_duplicates(layers, f"{where}: layers")

    raw_dimensions = body["dimensions"]
    if not isinstance(raw_dimensions, list):
        raise MalformedContract(f"{where}: dimensions must be a list, found {raw_dimensions!r}")
    dimensions = tuple(_name(item, f"{where}: dimensions[{i}]") for i, item in enumerate(raw_dimensions))
    _no_duplicates(dimensions, f"{where}: dimensions")

    return OperatorDecl(
        name=name,
        arity=arity,
        arg_sorts=arg_sorts,
        sign_apt=_bool(body["sign_apt"], f"{where}: sign_apt"),
        layers=layers,
        dimensions=dimensions,
        retired=_bool(body.get("retired", False), f"{where}: retired"),
    )


def _no_duplicates(values: tuple[str, ...], where: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise MalformedContract(f"{where}: {value!r} appears twice")
        seen.add(value)


def parse_domain_contract(
    document: object, *, source: str, base: BaseContract, predecessor: DomainContract | None
) -> DomainContract:
    """Validate a parsed domain-contract document, or refuse it.

    The base contract is required because a domain's layer selections are checked
    against it: §7.1 makes the layer set **base-owned but per-operator
    restricted**, and a domain that could mint a layer would be redefining what
    kind of thing a claim is.

    ``predecessor`` is required for the reason given on ``load_domain_contract``,
    and the check runs **here** rather than only at the file boundary. Validating
    only on the path that happens to read a file would leave the same contract
    admissible through the path that does not, which is not a weaker guarantee
    but an unstated one.

    **Both dependencies are authenticated.** A parser that takes another parsed
    artifact and trusts it by shape has the hole its own callers were closed
    against, one level in: the layer check below is only as good as the base
    contract handed to it, and the succession check only as good as the
    predecessor. Which base was used is then recorded on the result, so that
    compilation can tell whether the contract in front of it was typed against
    the base it is being compiled with.
    """
    if not isinstance(base, BaseContract):
        raise UnparsedContract(
            f"base is a {type(base).__name__}, not a parsed BaseContract — use parse_base_contract("
            "document, source=...) or load_base_contract(path). A domain's layers are checked against "
            "the base contract and against nothing else afterwards."
        )
    if predecessor is not None and not isinstance(predecessor, DomainContract):
        raise UnparsedContract(
            f"predecessor is a {type(predecessor).__name__}, not a parsed DomainContract. Succession is "
            "the *never redefine* rule made checkable (§8.3); checked against an authored predecessor it "
            "certifies nothing, since the thing it compares against was written to pass."
        )
    root = _mapping(document, source)
    for section in ("kinds", "relations"):
        if section in root:
            raise MalformedContract(
                f"{source}: a domain contract declares no {section}; a kernel kind or relation signature is the "
                "base contract's, and a domain contributes facets to kinds that already exist (D §3.3, D8) — refused"
            )
    _fields(root, _CONTRACT_FIELDS, frozenset({"description", "facets"}), source)

    namespace = _name(root["contract"], f"{source}: contract")
    if namespace == "coordination":
        raise MalformedContract(f"{source}: 'coordination' is reserved for the coordination contract")
    if namespace == base.name:
        raise MalformedContract(
            f"{source}: {namespace!r} is the base contract's namespace. Operators are domain-issued without "
            "exception (§7.1), and a base-issued operator would sit outside the closure walk every other "
            "operator goes through."
        )

    version = root["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise MalformedContract(f"{source}: version must be a positive integer, found {version!r}")

    sorts = {
        name: SortDecl(
            name=name,
            vocabulary=_parse_vocabulary(
                _require_sort_body(body, f"{source}: sorts.{name}")["vocabulary"], f"{source}: sorts.{name}: vocabulary"
            ),
            retired=_bool(
                _require_sort_body(body, f"{source}: sorts.{name}").get("retired", False),
                f"{source}: sorts.{name}: retired",
            ),
        )
        for name, body in _declarations(root["sorts"], f"{source}: sorts").items()
    }

    dimensions: dict[str, DimensionDecl] = {}
    for name, body in _declarations(root["dimensions"], f"{source}: dimensions").items():
        where = f"{source}: dimensions.{name}"
        decl = _mapping(body, where)
        _fields(decl, _DIMENSION_FIELDS, frozenset({"description", "retired"}), where)
        restriction_sort = _name(decl["restriction_sort"], f"{where}: restriction_sort")
        if restriction_sort not in sorts:
            raise MalformedContract(
                f"{where}: restriction_sort {restriction_sort!r} is not a sort this contract declares"
            )
        dimensions[name] = DimensionDecl(
            name=name, restriction_sort=restriction_sort, retired=_bool(decl.get("retired", False), f"{where}: retired")
        )

    operators: dict[str, OperatorDecl] = {}
    for name, body in _declarations(root["operators"], f"{source}: operators").items():
        where = f"{source}: operators.{name}"
        operator = _parse_operator(name, body, where)
        for slot, sort in enumerate(operator.arg_sorts):
            if sort not in sorts:
                raise MalformedContract(f"{where}: arg_sorts[{slot}] {sort!r} is not a sort this contract declares")
        for dimension in operator.dimensions:
            if dimension not in dimensions:
                raise MalformedContract(f"{where}: {dimension!r} is not a dimension this contract declares")
        for layer in operator.layers:
            if layer not in base.claim_grammar.layers:
                raise MalformedContract(
                    f"{where}: layer {layer!r} is not in the base contract's layer vocabulary. A domain selects "
                    "from the base vocabulary and may not extend it (§7.1)."
                )
        operators[name] = operator

    facets = parse_facet_declarations(root.get("facets", {}), where=f"{source}: facets", namespace=namespace)

    contract = DomainContract._parsed(
        _MINT,
        namespace=namespace,
        version=version,
        predecessor=_parse_lineage(root["lineage"], f"{source}: lineage"),
        sorts=sorts,
        dimensions=dimensions,
        operators=operators,
        facets=facets,
        content_identity=v1.digest(DOMAIN_CONTRACT_DOMAIN, root),
        base_identity=base.content_identity,
    )
    check_succession(contract, predecessor)
    return contract


def _require_sort_body(body: object, where: str) -> dict[str, object]:
    decl = _mapping(body, where)
    _fields(decl, _SORT_FIELDS, frozenset({"description", "retired"}), where)
    return decl


def _declarations(value: object, where: str) -> dict[str, object]:
    declarations = _mapping(value, where)
    for name in declarations:
        _name(name, f"{where}: {name}")
    return declarations


def check_succession(contract: DomainContract, predecessor: DomainContract | None) -> None:
    """§8.3's two-contract check, refused at contract **load**, not at claim decode.

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
            "declaration is retained immutably as a tombstone (§7.3a) — dropping one renders an existing claim "
            "population untypeable, which is redefinition arriving by another route."
        )

    for identifier in sorted(set(prior) & set(current)):
        if prior[identifier] != current[identifier]:
            raise SuccessionViolation(
                f"{contract.namespace}: {identifier} has a different canonical schema projection than in its "
                "predecessor. Redefinition is refused within a declared lineage — retire the identifier and "
                "issue a new one, which keeps every prior assertion bound to what it actually asserted (§7.3)."
            )

    resurrected = sorted((predecessor.retired_identifiers() - contract.retired_identifiers()) & set(current))
    if resurrected:
        raise SuccessionViolation(
            f"{contract.namespace}: un-retires {', '.join(resurrected)}. Retirement is one-way.\n"
            "§7.3a puts retirement in **authoring** — the typed constructor cannot select a retired identifier — "
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
