"""The `science` base contract — the kernel-owned structure of a ``Claim``.

Formal model §7.1 splits the vocabulary along the existing base/domain line: this
contract owns the claim grammar version, the closed quantifier and polarity tag
sets, the layer vocabulary, and the canonical byte encoding of every kernel tag.
Operators, dimensions and sorts are **domain-issued without exception** — the
base contract may not issue one.

**A tag's canonical bytes are its symbol.** §8 asks the base contract to fix
"the closed sets and their bytes, not their spelling", and §7.4 row 5 warns
against "an implementation choosing a different serialization for a tag". Those
are one requirement, not two: what must not happen is an implementation deciding
the bytes for itself. So the contract declares the encoding rule (``tag_encoding``)
and the symbols, and the bytes follow from both.

The alternative — a second, independent encoding per tag, so a symbol could be
renamed without re-minting — was considered and rejected. It buys renaming of a
closed set of ten kernel tags, which nothing needs, and it costs every tag a
second name that something must keep in correspondence. §7.3 already pairs
*authored and stable* with *enters claim identity*, which is exactly what a tag
symbol is; §7.4 row 5 then prices a change to one as severe, which is the
intended answer rather than a problem to engineer around.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import final

from beliefs.contract.facets import FacetDecl, parse_facet_declarations
from beliefs.errors import MalformedContract, TagCollision, UnparsedContract
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "COMPOSES_SIGNATURE",
    "COMPOSITE_GRAMMAR",
    "ESTIMAND_GRAMMAR",
    "SUPPORTED_CONTRAST_KINDS",
    "SUPPORTED_SCALES",
    "SUPPORTED_UNCERTAINTY_KINDS",
    "BaseContract",
    "ClaimGrammar",
    "CompositeGrammar",
    "EstimandGrammar",
    "FacetUse",
    "KindDecl",
    "RelationDecl",
    "load_base_contract",
    "parse_base_contract",
]

BASE_CONTRACT_DOMAIN = "science.contract.v1"
TAG_ENCODING = "science.identity.v1"

_TAG = re.compile(r"^[a-z][a-z0-9-]*$")

_MINT = object()
"""The parser's own token, required by ``BaseContract._parsed``.

**What this achieves, stated exactly, because it is less than the TypeScript
side's brand.** There, ``#minted`` cannot be installed from outside the class
body — that is a language guarantee, and a forgery is impossible rather than
inconvenient. Python has no module privacy: ``object.__new__(BaseContract)``
followed by ``object.__setattr__`` reproduces what ``_parsed`` does, in two
lines, with nothing here consulted. So this token cannot make provenance
unforgeable, and does not claim to.

What it does is remove ``_parsed`` from the set of **ordinary** routes. Before
it, a caller with no intent to forge anything could reach a real ``BaseContract``
through a method that merely looked internal, and every downstream check would
believe it. After it, reaching one means reaching for ``object.__new__`` or a
private module attribute — which is §6.3's raw-write row, where the boundary is
bypassed rather than defeated, and which belongs to the audit surface. The
distinction worth keeping is between a hole and a documented limit.
"""

_CONTRACT_FIELDS = frozenset(
    {"contract", "version", "claim_grammar", "estimand_grammar", "composite_grammar", "kinds", "relations", "facets"}
)
_GRAMMAR_FIELDS = frozenset({"version", "tag_encoding", "quantifiers", "polarities", "sign_inapt_tag", "layers"})
_ESTIMAND_GRAMMAR_FIELDS = frozenset({"version", "tag_encoding", "contrast_kinds", "scales", "uncertainty_kinds"})
_COMPOSITE_GRAMMAR_FIELDS = frozenset({"version", "shapes"})
SUPPORTED_SHAPES = ("dag",)
"""The shapes this implementation derives (design §3.4). A contract naming a
shape outside this set is refused at parse: a profile carrying `pag` would
otherwise run `dag` classification under another shape's name."""
SUPPORTED_CONTRAST_KINDS = ("continuous", "levels")
SUPPORTED_SCALES = ("additive", "multiplicative")
SUPPORTED_UNCERTAINTY_KINDS = ("interval", "standard-error")
"""The three estimand closed sets this implementation operates. A contract
must declare each set exactly: widening would route a new tag through an
existing operation, while narrowing would declare less than the kernel does."""
_RELATION_FIELDS = frozenset({"group", "sources", "targets"})
_RELATION_OPTIONAL = frozenset({"same_kind"})
_RELATION_GROUPS = ("world", "lifecycle")
ESTIMAND_GRAMMAR = "science.estimand.v1"
COMPOSITE_GRAMMAR = "science.composite.v1"
"""The tag a stored composite facet carries under `grammar` (design §3.2)."""
COMPOSES_SIGNATURE = (("composite",), ("proposition",))
"""`composes`' one signature (composite-claims §3.1, U1): a composite composes
propositions, and nothing else composes anything. Declared here rather than
spelled inline so the parser and its message read from one statement."""


@dataclass(frozen=True)
class ClaimGrammar:
    """The closed sets a claim's structure draws from."""

    version: int
    quantifiers: tuple[str, ...]
    polarities: tuple[str, ...]
    sign_inapt_tag: str
    layers: tuple[str, ...]

    @property
    def polarity_tags(self) -> tuple[str, ...]:
        """Every inhabitant of the polarity position, which is **always emitted**.

        §7.5: the position carries ``sign_inapt_tag`` for the unit inhabitant
        rather than being absent, so ``π_claim``'s shape depends on the claim's
        own content and never on a contract field. A ``sign_apt`` flip therefore
        cannot re-project a stored claim.
        """
        return (*self.polarities, self.sign_inapt_tag)


@dataclass(frozen=True)
class EstimandGrammar:
    """The closed structural sets an estimand draws from (estimand-typing §3.1).

    Structural, not vocabulary: each tag names an operation the kernel performs
    on the value that carries it, which is what keeps these three sets out of
    the survey's admission rule the way quantifiers are kept out."""

    version: int
    contrast_kinds: tuple[str, ...]
    scales: tuple[str, ...]
    uncertainty_kinds: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {
            "version": self.version,
            "contrast_kinds": sorted(self.contrast_kinds),
            "scales": sorted(self.scales),
            "uncertainty_kinds": sorted(self.uncertainty_kinds),
        }


@dataclass(frozen=True)
class CompositeGrammar:
    """The closed set of shapes a composite may take (design §3.1). A shape is
    a derivation the kernel performs, never a domain's declaration."""

    version: int
    shapes: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {"version": self.version, "shapes": list(self.shapes)}


@dataclass(frozen=True)
class FacetUse:
    required: bool
    covered: bool


@dataclass(frozen=True)
class KindDecl:
    name: str
    role: str
    domain: str | None
    facets: Mapping[str, FacetUse]

    def projection(self) -> dict[str, object]:
        projection: dict[str, object] = {
            "role": self.role,
            "facets": {
                key: {"required": use.required, "covered": use.covered} for key, use in sorted(self.facets.items())
            },
        }
        if self.domain is not None:
            projection["domain"] = self.domain
        return projection


@dataclass(frozen=True)
class RelationDecl:
    name: str
    group: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    same_kind: bool = False
    """An instance's endpoints must be records of one kind (design §3.1).
    Admissible only where `sources` and `targets` are equal sets, so the rule
    can never name a pair the signature already forbids."""

    def projection(self) -> dict[str, object]:
        return {
            "group": self.group,
            "sources": sorted(self.sources),
            "targets": sorted(self.targets),
            "same_kind": self.same_kind,
        }


@sealed
@final
@dataclass(frozen=True, init=False)
class BaseContract:
    """**Parsed, never authored.**

    The same lock as ``ProfileSpec`` and ``Claim``, one link further up, and the
    link that makes theirs worth anything: a profile's refusal to be authored
    certifies that ``compile_profile`` ran, not that the documents were read. A
    hand-built contract types a claim against a grammar nobody wrote down, and
    the resulting claim is indistinguishable from a real one — including to the
    other implementation, which agrees with it exactly.

    ``content_identity`` is the sharper reason. It is derived here from the
    document, and it is what enters ``belief_input_digest`` (§7.3); a field-wise
    constructor would let it be supplied, so a contract could carry an identity
    attesting to a document it does not contain.
    """

    name: str
    version: int
    claim_grammar: ClaimGrammar
    estimand_grammar: EstimandGrammar
    composite_grammar: CompositeGrammar
    kinds: Mapping[str, KindDecl]
    relations: Mapping[str, RelationDecl]
    facets: Mapping[str, FacetDecl]

    content_identity: str
    """Content-derived, and the half that enters ``belief_input_digest`` (§7.3).

    Over the **canonical projection**, not the raw bytes: reformatting must not
    move an identity (D5), and raw bytes would make whitespace and key order
    significant. One consequence is worth naming — a **comment** is not in the
    projection, so editing one does not move this identity, and §7.3's editorial
    list overstates by that one item.
    """

    # As in `ProfileSpec`: the lock is this method. `@dataclass` will not
    # overwrite an `__init__` the class already defines, so `init=False` is a
    # backstop rather than the mechanism.
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise UnparsedContract(
            "BaseContract is parsed, never authored — use parse_base_contract(document, source=...). "
            "The contracts are the normative SSOT (D §6); an authored one would let a claim be typed "
            "against a claim grammar no document declares, and carry a content_identity for a document "
            "it does not contain."
        )

    @classmethod
    def _parsed(cls, token: object, **fields: object) -> BaseContract:
        if token is not _MINT:
            raise UnparsedContract(
                "BaseContract._parsed is the parser's own route and takes its mint token; "
                "use parse_base_contract(document, source=...) or load_base_contract(path)."
            )
        contract = object.__new__(cls)
        for name, value in fields.items():
            object.__setattr__(contract, name, value)
        return contract


def _mapping(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise MalformedContract(f"{where}: expected a mapping, found {type(value).__name__}")
    for key in value:
        if not isinstance(key, str):
            raise MalformedContract(f"{where}: key {key!r} is {type(key).__name__}, not a string")
    return value  # type: ignore[return-value]


def _exact_fields(mapping: dict[str, object], permitted: frozenset[str], where: str) -> None:
    unknown = sorted(set(mapping) - permitted)
    if unknown:
        raise MalformedContract(f"{where}: unknown field(s) {', '.join(unknown)}; refused, never ignored")
    missing = sorted(permitted - set(mapping))
    if missing:
        raise MalformedContract(f"{where}: missing field(s) {', '.join(missing)}")


def _exact_fields_or_empty(mapping: dict[str, object], permitted: frozenset[str], where: str) -> None:
    if not mapping:
        return
    unknown = sorted(set(mapping) - permitted)
    if unknown:
        raise MalformedContract(f"{where}: unknown field(s) {', '.join(unknown)}; refused, never ignored")
    if "facets" not in mapping:
        raise MalformedContract(f"{where}: missing field(s) facets")


def v1_domain_ok(domain: str) -> bool:
    try:
        v1.check_domain(domain)
    except Exception:  # noqa: BLE001 - any refusal means "not a domain"
        return False
    return True


def _positive_int(value: object, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MalformedContract(f"{where}: expected a positive integer, found {value!r}")
    return value


def _tag(value: object, where: str) -> str:
    if not isinstance(value, str) or not _TAG.fullmatch(value):
        raise MalformedContract(f"{where}: {value!r} is not a tag; expected lowercase `[a-z][a-z0-9-]*`")
    return value


def _closed_set(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MalformedContract(f"{where}: expected a non-empty list of tags, found {value!r}")
    tags = tuple(_tag(item, f"{where}[{i}]") for i, item in enumerate(value))
    seen: set[str] = set()
    for tag in tags:
        if tag in seen:
            raise TagCollision(f"{where}: {tag!r} appears twice in a closed set")
        seen.add(tag)
    return tags


def parse_base_contract(document: object, *, source: str) -> BaseContract:
    """Validate a parsed base-contract document, or refuse it."""
    root = _mapping(document, source)
    _exact_fields(root, _CONTRACT_FIELDS, source)

    name = root["contract"]
    if not isinstance(name, str) or name != "science":
        raise MalformedContract(f"{source}: the base contract's name is `science`, found {name!r}")

    grammar_where = f"{source}: claim_grammar"
    grammar = _mapping(root["claim_grammar"], grammar_where)
    _exact_fields(grammar, _GRAMMAR_FIELDS, grammar_where)

    encoding = grammar["tag_encoding"]
    if encoding != TAG_ENCODING:
        raise MalformedContract(
            f"{grammar_where}: tag_encoding is {encoding!r}, and this implementation encodes tags only under "
            f"{TAG_ENCODING!r}. Loading it under a different rule would be exactly the incidental re-encoding "
            "§7.4 row 5 forbids."
        )

    polarities = _closed_set(grammar["polarities"], f"{grammar_where}: polarities")
    sign_inapt_tag = _tag(grammar["sign_inapt_tag"], f"{grammar_where}: sign_inapt_tag")
    if sign_inapt_tag in polarities:
        raise TagCollision(
            f"{grammar_where}: sign_inapt_tag {sign_inapt_tag!r} is also an assertable polarity. "
            "`unsigned` says the operator has a sign and this claim asserts none; the inapt tag says the "
            "operator has no sign to assert. One tag cannot carry both."
        )

    claim_grammar = ClaimGrammar(
        version=_positive_int(grammar["version"], f"{grammar_where}: version"),
        quantifiers=_closed_set(grammar["quantifiers"], f"{grammar_where}: quantifiers"),
        polarities=polarities,
        sign_inapt_tag=sign_inapt_tag,
        layers=_closed_set(grammar["layers"], f"{grammar_where}: layers"),
    )

    composite_where = f"{source}: composite_grammar"
    composite = _mapping(root["composite_grammar"], composite_where)
    _exact_fields(composite, _COMPOSITE_GRAMMAR_FIELDS, composite_where)
    composite_grammar = CompositeGrammar(
        version=_positive_int(composite["version"], f"{composite_where}: version"),
        shapes=_closed_set(composite["shapes"], f"{composite_where}: shapes"),
    )
    unsupported = sorted(set(composite_grammar.shapes) - set(SUPPORTED_SHAPES))
    if unsupported:
        raise MalformedContract(
            f"{composite_where}: shapes {unsupported} are not shapes this implementation derives ({SUPPORTED_SHAPES}); "
            "a later grammar version arrives with its classification, never ahead of it"
        )

    estimand_where = f"{source}: estimand_grammar"
    estimand = _mapping(root["estimand_grammar"], estimand_where)
    _exact_fields(estimand, _ESTIMAND_GRAMMAR_FIELDS, estimand_where)
    if estimand["tag_encoding"] != TAG_ENCODING:
        raise MalformedContract(
            f"{estimand_where}: tag_encoding is {estimand['tag_encoding']!r}; this implementation encodes tags only "
            f"under {TAG_ENCODING!r} (estimand-typing §3.1)."
        )
    estimand_grammar = EstimandGrammar(
        version=_positive_int(estimand["version"], f"{estimand_where}: version"),
        contrast_kinds=_closed_set(estimand["contrast_kinds"], f"{estimand_where}: contrast_kinds"),
        scales=_closed_set(estimand["scales"], f"{estimand_where}: scales"),
        uncertainty_kinds=_closed_set(estimand["uncertainty_kinds"], f"{estimand_where}: uncertainty_kinds"),
    )
    for set_name, declared, supported in (
        ("contrast_kinds", estimand_grammar.contrast_kinds, SUPPORTED_CONTRAST_KINDS),
        ("scales", estimand_grammar.scales, SUPPORTED_SCALES),
        ("uncertainty_kinds", estimand_grammar.uncertainty_kinds, SUPPORTED_UNCERTAINTY_KINDS),
    ):
        if set(declared) != set(supported):
            unoperable = sorted(set(declared) ^ set(supported))
            raise MalformedContract(
                f"{estimand_where}: {set_name} declares {sorted(declared)}, not the set this implementation operates "
                f"{sorted(supported)}; {unoperable} is not operable here (a later grammar version arrives with its "
                "interpretation, never ahead of it)"
            )

    facets = parse_facet_declarations(root["facets"], where=f"{source}: facets", namespace=None)
    kinds: dict[str, KindDecl] = {}
    for kind_name, body_value in _mapping(root["kinds"], f"{source}: kinds").items():
        where = f"{source}: kinds.{kind_name}"
        body = _mapping(body_value, where)
        _exact_fields_or_empty(body, frozenset({"domain", "facets", "role"}), where)
        role = body.get("role", "world")
        if role not in ("world", "prose"):
            raise MalformedContract(f"{where}: role is `world` or `prose`, found {role!r}")
        domain = body.get("domain")
        facet_values = _mapping(body.get("facets", {}), f"{where}.facets")
        if role == "prose":
            if domain is not None or set(facet_values) - {"display"}:
                raise MalformedContract(f"{where}: a prose kind carries no domain and no facet but display")
        elif body and (not isinstance(domain, str) or not v1_domain_ok(domain)):
            raise MalformedContract(f"{where}: a governed kind names a `science.<kind>.v<n>` domain")
        uses: dict[str, FacetUse] = {}
        for key, use_value in facet_values.items():
            if key not in facets:
                raise MalformedContract(f"{where}.facets: {key!r} is not a facet this contract declares")
            use = _mapping(use_value, f"{where}.facets.{key}")
            _exact_fields(use, frozenset({"required", "covered"}), f"{where}.facets.{key}")
            if not isinstance(use["required"], bool) or not isinstance(use["covered"], bool):
                raise MalformedContract(f"{where}.facets.{key}: required and covered are booleans")
            uses[key] = FacetUse(required=use["required"], covered=use["covered"])
        kind_domain = domain if isinstance(domain, str) and role == "world" and body else None
        kinds[kind_name] = KindDecl(kind_name, role, kind_domain, MappingProxyType(uses))

    relations: dict[str, RelationDecl] = {}
    for relation_name, body_value in _mapping(root["relations"], f"{source}: relations").items():
        where = f"{source}: relations.{relation_name}"
        body = _mapping(body_value, where)
        _exact_fields({k: v for k, v in body.items() if k not in _RELATION_OPTIONAL}, _RELATION_FIELDS, where)
        if body["group"] not in _RELATION_GROUPS:
            raise MalformedContract(f"{where}: group is one of {', '.join(_RELATION_GROUPS)}, found {body['group']!r}")
        sources = _closed_set(body["sources"], f"{where}: sources")
        targets = _closed_set(body["targets"], f"{where}: targets")
        for kind in (*sources, *targets):
            if kind not in kinds:
                raise MalformedContract(f"{where}: {kind!r} is not a kind this contract declares")
        same_kind = body.get("same_kind", False)
        if not isinstance(same_kind, bool):
            raise MalformedContract(f"{where}: same_kind is a boolean, found {same_kind!r}")
        if same_kind and set(sources) != set(targets):
            raise MalformedContract(
                f"{where}: same_kind requires sources and targets to be equal sets; "
                f"{sorted(set(sources) ^ set(targets))} appear on one side only"
            )
        composes_sources, composes_targets = COMPOSES_SIGNATURE
        if relation_name == "composes" and (sources != composes_sources or targets != composes_targets):
            # Composite-claims §3.1, U1: `composes` has one signature, and it is
            # the kernel's, not a contract author's. A widened endpoint set would
            # let a composite compose something that is not a proposition, or a
            # record that is not a composite compose one, and every reader below
            # — the boundary's `restore_members`, `classify`, the audit — is
            # written against exactly this pair.
            raise MalformedContract(
                f"{where}: composes is {composes_sources[0]} \u2192 {composes_targets[0]}, "
                f"one signature and no other; found {list(sources)} \u2192 {list(targets)}"
            )
        relations[relation_name] = RelationDecl(relation_name, body["group"], sources, targets, same_kind)

    return BaseContract._parsed(
        _MINT,
        name=name,
        version=_positive_int(root["version"], f"{source}: version"),
        claim_grammar=claim_grammar,
        estimand_grammar=estimand_grammar,
        composite_grammar=composite_grammar,
        kinds=MappingProxyType(kinds),
        relations=MappingProxyType(relations),
        facets=MappingProxyType(facets),
        content_identity=v1.digest(BASE_CONTRACT_DOMAIN, root),
    )


def load_base_contract(path: Path) -> BaseContract:
    """Read and validate the base contract at ``path`` (duplicate keys refused, §3.7)."""
    from beliefs.contract.document import load_document

    return parse_base_contract(load_document(path, source=str(path)), source=str(path))
