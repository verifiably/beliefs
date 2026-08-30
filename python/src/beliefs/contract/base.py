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
from dataclasses import dataclass
from pathlib import Path
from typing import final

import yaml

from beliefs.errors import MalformedContract, TagCollision, UnparsedContract
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = ["BaseContract", "ClaimGrammar", "load_base_contract", "parse_base_contract"]

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

_CONTRACT_FIELDS = frozenset({"contract", "version", "claim_grammar"})
_GRAMMAR_FIELDS = frozenset({"version", "tag_encoding", "quantifiers", "polarities", "sign_inapt_tag", "layers"})


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

    return BaseContract._parsed(
        _MINT,
        name=name,
        version=_positive_int(root["version"], f"{source}: version"),
        claim_grammar=claim_grammar,
        content_identity=v1.digest(BASE_CONTRACT_DOMAIN, root),
    )


def load_base_contract(path: Path) -> BaseContract:
    """Read and validate the base contract at ``path``.

    The path is a required argument. Resolving it from an ambient location would
    make the contract in force depend on the checkout, which is the property the
    belief policy's §2.3 refuses for exactly the same reason.
    """
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # never let a parser error escape as itself
        raise MalformedContract(f"{path}: not well-formed YAML: {exc}") from exc
    return parse_base_contract(document, source=str(path))
