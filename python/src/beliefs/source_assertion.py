"""Source assertion values, canonical facet, identity, and record-local checks.

A source assertion records that one source asserts, denies, or hypothesizes a
proposition, as read by one extractor at one span of one representation. This
module holds only the pure value, its canonical stored round-trip, and its
record-local validation check; it imports neither `atoms` nor `beliefs.corpus`.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast, final

from nodes.core.relations import Relation

from beliefs.errors import IdentityError, MalformedRecord, SignatureRefused
from beliefs.identity import v1
from beliefs.permit import require_actor
from beliefs.reservation import UNREAD, CheckRefusal, KindOf
from beliefs.sealed import sealed

__all__ = [
    "ANCHORED_IN",
    "EXTENTS",
    "SIGNS",
    "SOURCE_ASSERTION_DOMAIN",
    "Bearing",
    "Reading",
    "Representation",
    "SourceAssertion",
    "Span",
    "source_assertion_from_stored",
    "source_assertion_refusal",
]

SIGNS: tuple[str, ...] = ("asserts", "denies", "hypothesizes")
EXTENTS: tuple[str, ...] = ("full", "abstract")
SOURCE_ASSERTION_DOMAIN = "science.source-assertion.v1"
ANCHORED_IN = "anchored_in"

_SHA256 = re.compile(r"[0-9a-f]{64}")


def _check_text(value: object, where: str) -> str:
    """Require an exact non-empty Unicode-NFC string encodable under v1."""
    if type(value) is not str or not value:
        raise MalformedRecord(f"{where}: {value!r} must be a non-empty string")
    if not unicodedata.is_normalized("NFC", value):
        raise MalformedRecord(f"{where}: text must already be in Unicode NFC")
    try:
        v1.encode(value)
    except IdentityError as caught:
        raise MalformedRecord(f"{where}: text is not v1-encodable: {caught}") from caught
    return value


def _check_actor(value: object, where: str) -> str:
    _check_text(value, where)
    try:
        return require_actor(value)
    except (TypeError, ValueError) as caught:
        raise MalformedRecord(f"{where}: {value!r} is not an actor: {caught}") from caught


def _check_prefixed(value: object, prefix: str, where: str) -> str:
    text = _check_text(value, where)
    if not text.startswith(prefix) or len(text) <= len(prefix):
        raise MalformedRecord(f"{where}: {value!r} must carry a {prefix!r} reference")
    return text


def _require_dict_keys(value: object, required: set[str], optional: set[str], where: str) -> dict[str, object]:
    if type(value) is not dict:
        raise MalformedRecord(f"{where} must be a dict, not {type(value).__name__}")
    keys = set(value)
    if not all(type(k) is str for k in keys):
        raise MalformedRecord(f"{where} keys must be strings")
    missing = required - keys
    if missing:
        raise MalformedRecord(f"{where} is missing {sorted(missing)}")
    extra = keys - required - optional
    if extra:
        raise MalformedRecord(f"{where} has unexpected keys {sorted(extra)}")
    return cast(dict[str, object], value)


@sealed
@final
@dataclass(frozen=True)
class Representation:
    """The byte-level copy and reading depth a reader extracted from."""

    sha256: str
    media_type: str
    extent: str

    def __post_init__(self) -> None:
        sha256 = _check_text(self.sha256, "representation.sha256")
        if _SHA256.fullmatch(sha256) is None:
            raise MalformedRecord(f"representation.sha256: {sha256!r} must be 64 lowercase hex digits")
        _check_text(self.media_type, "representation.media_type")
        extent = _check_text(self.extent, "representation.extent")
        if extent not in EXTENTS:
            raise MalformedRecord(f"representation.extent: {extent!r} is outside the closed set {EXTENTS}")


@sealed
@final
@dataclass(frozen=True)
class Span:
    """The exact NFC quote and its locator within the representation."""

    quote: str
    locator: str

    def __post_init__(self) -> None:
        _check_text(self.quote, "span.quote")
        _check_text(self.locator, "span.locator")


@sealed
@final
@dataclass(frozen=True)
class Reading:
    """Who extracted what span from which representation, and any inner attribution."""

    representation: Representation
    span: Span
    extracted_by: str
    attributed_to: str | None = None

    def __post_init__(self) -> None:
        if type(self.representation) is not Representation:
            raise MalformedRecord("read.representation must be a Representation")
        if type(self.span) is not Span:
            raise MalformedRecord("read.span must be a Span")
        _check_actor(self.extracted_by, "read.extracted_by")
        if self.attributed_to is not None:
            _check_text(self.attributed_to, "read.attributed_to")


@sealed
@final
@dataclass(frozen=True)
class Bearing:
    """The closed stance (`asserts`, `denies`, `hypothesizes`) on a typed proposition."""

    sign: str
    proposition: str

    def __post_init__(self) -> None:
        if type(self.sign) is not str:
            raise MalformedRecord(f"bears_on.sign: {self.sign!r} must be a string")
        if self.sign not in SIGNS:
            raise SignatureRefused(
                f"a source-assertion cannot carry {self.sign!r}; its closed signatures are "
                f"{SIGNS} — an `assesses` edge is the assessment's, by type"
            )
        _check_prefixed(self.proposition, "proposition:", "bears_on.proposition")


@sealed
@final
@dataclass(frozen=True)
class SourceAssertion:
    """One reader's attributed reading of one source's stance on one proposition."""

    source: str
    read: Reading
    bears_on: Bearing
    recorded_by: str

    def __post_init__(self) -> None:
        _check_prefixed(self.source, "source:", "source")
        if type(self.read) is not Reading:
            raise MalformedRecord("read must be a Reading")
        if type(self.bears_on) is not Bearing:
            raise MalformedRecord("bears_on must be a Bearing")
        _check_actor(self.recorded_by, "recorded_by")

    def facet(self) -> dict[str, object]:
        """Return the canonical `source-assertion` facet payload."""
        read_dict: dict[str, object] = {
            "representation": {
                "sha256": self.read.representation.sha256,
                "media_type": self.read.representation.media_type,
                "extent": self.read.representation.extent,
            },
            "span": {
                "quote": self.read.span.quote,
                "locator": self.read.span.locator,
            },
            "extracted_by": self.read.extracted_by,
        }
        if self.read.attributed_to is not None:
            read_dict["attributed_to"] = self.read.attributed_to
        return {
            "read": read_dict,
            "bears_on": {
                "sign": self.bears_on.sign,
                "proposition": self.bears_on.proposition,
            },
            "recorded_by": self.recorded_by,
        }

    def identity(self) -> str:
        """Compute the content digest over `read` and `bears_on` only."""
        facet = self.facet()
        return v1.digest(SOURCE_ASSERTION_DOMAIN, {"read": facet["read"], "bears_on": facet["bears_on"]})

    @property
    def id(self) -> str:
        return f"source-assertion:{self.identity()}"

    def relations(self) -> list[Relation]:
        """Return the single canonical `anchored_in` edge to the source."""
        return [Relation(source=self.id, predicate=ANCHORED_IN, target=self.source)]

    @classmethod
    def from_stored(cls, facet: object, relations: Sequence[Relation]) -> SourceAssertion:
        """Decode a stored `source-assertion` facet and its relations."""
        return source_assertion_from_stored(facet, relations)


def source_assertion_from_stored(facet: object, relations: Sequence[Relation]) -> SourceAssertion:
    """Decode and validate a stored `source-assertion` facet against its anchor edge."""
    if isinstance(relations, (str, bytes)) or not isinstance(relations, Sequence):
        raise MalformedRecord(f"relations must be a sequence of Relation, not {relations!r}")
    for relation in relations:
        if not isinstance(relation, Relation):
            raise MalformedRecord(f"relations entry must be a Relation, not {relation!r}")
    anchored = [r for r in relations if r.predicate == ANCHORED_IN]
    if len(anchored) != 1:
        raise MalformedRecord(f"a source-assertion carries exactly one {ANCHORED_IN!r} edge, found {len(anchored)}")
    anchor = anchored[0]

    top = _require_dict_keys(facet, {"read", "bears_on", "recorded_by"}, set(), "a source-assertion facet")
    read = _require_dict_keys(
        top["read"], {"representation", "span", "extracted_by"}, {"attributed_to"}, "source-assertion read"
    )
    representation = _require_dict_keys(
        read["representation"], {"sha256", "media_type", "extent"}, set(), "source-assertion representation"
    )
    span = _require_dict_keys(read["span"], {"quote", "locator"}, set(), "source-assertion span")
    bears_on = _require_dict_keys(top["bears_on"], {"sign", "proposition"}, set(), "source-assertion bears_on")
    if "attributed_to" in read and read["attributed_to"] is None:
        raise MalformedRecord("read.attributed_to must be omitted when absent, never null")

    try:
        value = SourceAssertion(
            source=anchor.target,
            read=Reading(
                representation=Representation(
                    sha256=cast(str, representation["sha256"]),
                    media_type=cast(str, representation["media_type"]),
                    extent=cast(str, representation["extent"]),
                ),
                span=Span(
                    quote=cast(str, span["quote"]),
                    locator=cast(str, span["locator"]),
                ),
                extracted_by=cast(str, read["extracted_by"]),
                attributed_to=cast(str | None, read.get("attributed_to")),
            ),
            bears_on=Bearing(
                sign=cast(str, bears_on["sign"]),
                proposition=cast(str, bears_on["proposition"]),
            ),
            recorded_by=cast(str, top["recorded_by"]),
        )
    except SignatureRefused as caught:
        raise MalformedRecord(str(caught)) from caught

    if anchor.source != value.id:
        raise MalformedRecord(
            f"the {ANCHORED_IN!r} edge's source {anchor.source!r} does not match the assertion's id {value.id!r}"
        )
    if value.facet() != top:
        raise MalformedRecord("the stored facet is not the canonical form of the source assertion it decodes to")
    return value


def _edge_key(relation: Relation) -> tuple[str, str, str]:
    return relation.source, relation.predicate, relation.target


def source_assertion_refusal(
    value: SourceAssertion, relations: Sequence[Relation], *, kind_of: KindOf
) -> CheckRefusal | None:
    """Check edge equality and resolve source and proposition references by kind; first failure wins."""
    expected = value.relations()
    keys = {_edge_key(r) for r in relations}
    if len(relations) != len(keys) or sorted(relations, key=_edge_key) != sorted(expected, key=_edge_key):
        return CheckRefusal(
            "source-assertion-edge-mismatch",
            "the relations differ from those the source assertion names",
        )
    for slot, ref, kind in (
        ("source", value.source, "source"),
        ("proposition", value.bears_on.proposition, "proposition"),
    ):
        found = kind_of(ref)
        if found is None:
            return CheckRefusal("source-assertion-ref-unresolved", f"the {slot} {ref!r} resolves to no record here")
        if found is UNREAD:
            continue
        if found != kind:
            return CheckRefusal("source-assertion-ref-unresolved", f"the {slot} {ref!r} is a {found}, not a {kind}")
    return None
