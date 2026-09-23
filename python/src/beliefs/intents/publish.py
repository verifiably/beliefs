"""The publish intent (publication-records design §5): a domain-tagged payload
carrying its own evidence. Pure: one codec, one sealed value."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, final

from beliefs.coordination import Anchor, CoordinationAddress
from beliefs.errors import CanonicalTextRefused, MalformedRecord
from beliefs.holdings.records import url_locator
from beliefs.identity import v1
from beliefs.permit import require_actor
from beliefs.sealed import sealed

__all__ = ["PUBLISH_INTENT_DOMAIN", "Destination", "PublishIntent", "decode_publish_intent", "encode_publish_intent"]

PUBLISH_INTENT_DOMAIN = "science.publish-intent.v1"
_HEX32 = re.compile(r"[0-9a-f]{32}")
_RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")
_FIELDS = frozenset(
    {"domain", "kind", "event_token", "actor", "at", "view", "destination", "binding_tips", "marker_tips", "anchors"}
)


@sealed
@final
@dataclass(frozen=True)
class Destination:
    """The closed destination union (decision 9)."""

    type: Literal["local", "remote"]
    locator: str

    def __post_init__(self) -> None:
        if self.type == "local":
            if (
                type(self.locator) is not str
                or not self.locator.startswith("/")
                or self.locator.startswith("//")
                or posixpath.normpath(self.locator) != self.locator
            ):
                raise MalformedRecord(
                    f"a local destination is an absolute, normalized POSIX path, not {self.locator!r}"
                )
        elif self.type == "remote":
            canonical = url_locator(self.locator).url
            if canonical != self.locator:
                raise MalformedRecord(f"remote destination {self.locator!r} is not the canonical spelling")
        else:
            raise MalformedRecord(f"destination type {self.type!r} is outside local and remote")

    @classmethod
    def local(cls, path: str) -> Destination:
        if type(path) is not str or not path.startswith("/"):
            raise MalformedRecord("a local destination must be absolute")
        return cls("local", posixpath.normpath(path))

    @classmethod
    def remote(cls, url: str) -> Destination:
        return cls("remote", url_locator(url).url)

    def projection(self) -> dict[str, str]:
        return {"type": self.type, "locator": self.locator}

    @classmethod
    def from_projection(cls, value: object) -> Destination:
        if not isinstance(value, dict) or set(value) != {"type", "locator"}:
            raise MalformedRecord("a destination is exactly {type, locator}")
        return cls(value["type"], value["locator"])


def _strictly_ascending(values: tuple[object, ...], where: str) -> None:
    # callers validate every member's type first: ordering mixed types raises TypeError
    if list(values) != sorted(set(values)):  # type: ignore[type-var]
        raise MalformedRecord(f"{where} must be strictly ascending")


@sealed
@final
@dataclass(frozen=True)
class PublishIntent:
    """The evidence-bearing publish intent (decision 3)."""

    kind: str
    event_token: str
    actor: str
    at: str
    view: CoordinationAddress
    destination: Destination
    binding_tips: tuple[str, ...]
    marker_tips: tuple[tuple[str, str], ...]
    anchors: tuple[Anchor, ...]

    def __post_init__(self) -> None:
        if self.kind != "publish":
            raise MalformedRecord("a publish intent's kind is publish")
        if type(self.event_token) is not str or _HEX32.fullmatch(self.event_token) is None:
            raise MalformedRecord("a publish intent's event token is 32 lowercase hex")
        try:
            require_actor(self.actor)
        except (TypeError, ValueError) as caught:
            raise MalformedRecord(f"a publish intent's actor is refused: {caught}") from caught
        if type(self.at) is not str or _RFC3339.fullmatch(self.at) is None:
            raise MalformedRecord("a publish intent's at is an RFC3339 timestamp")
        try:
            datetime.fromisoformat(self.at)
        except ValueError as caught:
            raise MalformedRecord("a publish intent's at is a calendar timestamp") from caught
        if type(self.view) is not CoordinationAddress or self.view.revision is None:
            raise MalformedRecord("a publish intent names its view pinned to the resolved revision")
        if type(self.destination) is not Destination:
            raise MalformedRecord("a publish intent's destination is a Destination")
        if type(self.binding_tips) is not tuple or any(
            type(t) is not str or _HEX32.fullmatch(t) is None for t in self.binding_tips
        ):
            raise MalformedRecord("binding tips are 32-hex revision ids")
        _strictly_ascending(self.binding_tips, "binding tips")
        if type(self.marker_tips) is not tuple or any(
            type(pair) is not tuple
            or len(pair) != 2
            or any(type(m) is not str or _HEX32.fullmatch(m) is None for m in pair)
            for pair in self.marker_tips
        ):
            raise MalformedRecord("marker tips are (corpus_id, marker uid) pairs of 32-hex")
        _strictly_ascending(self.marker_tips, "marker tips")
        if type(self.anchors) is not tuple or any(type(a) is not Anchor for a in self.anchors):
            raise MalformedRecord("anchors are Anchor values")
        _strictly_ascending(tuple(a.corpus_id for a in self.anchors), "anchors by corpus_id")


def encode_publish_intent(intent: PublishIntent) -> bytes:
    if type(intent) is not PublishIntent:
        raise MalformedRecord("encode_publish_intent takes a PublishIntent")
    return v1.encode(
        {
            "domain": PUBLISH_INTENT_DOMAIN,
            "kind": intent.kind,
            "event_token": intent.event_token,
            "actor": intent.actor,
            "at": intent.at,
            "view": str(intent.view),
            "destination": intent.destination.projection(),
            "binding_tips": list(intent.binding_tips),
            "marker_tips": [list(pair) for pair in intent.marker_tips],
            "anchors": [{"corpus_id": a.corpus_id, "genesis": a.genesis, "head": a.head} for a in intent.anchors],
        }
    )


def decode_publish_intent(payload: bytes) -> PublishIntent:
    try:
        value = v1.decode(payload)
    except CanonicalTextRefused as caught:
        raise MalformedRecord("a publish intent payload is not canonical text") from caught
    if not isinstance(value, dict) or set(value) != _FIELDS or value["domain"] != PUBLISH_INTENT_DOMAIN:
        raise MalformedRecord("a publish intent carries exactly its closed field set under its domain")
    # every collection is checked for its container type before it is converted:
    # `tuple()` over a string or mapping would silently reshape it
    for name in ("binding_tips", "marker_tips", "anchors"):
        if type(value[name]) is not list:
            raise MalformedRecord(f"a publish intent's {name} is a list")
    if any(type(pair) is not list for pair in value["marker_tips"]) or any(
        type(a) is not dict for a in value["anchors"]
    ):
        raise MalformedRecord("marker tips are lists and anchors are mappings")
    try:
        intent = PublishIntent(
            kind=value["kind"],
            event_token=value["event_token"],
            actor=value["actor"],
            at=value["at"],
            view=CoordinationAddress.parse(value["view"]),
            destination=Destination.from_projection(value["destination"]),
            binding_tips=tuple(value["binding_tips"]),
            marker_tips=tuple(tuple(pair) for pair in value["marker_tips"]),
            anchors=tuple(Anchor(**anchor) for anchor in value["anchors"]),
        )
    except (TypeError, ValueError, KeyError) as caught:
        # `Anchor(**anchor)` over a mapping with other keys raises TypeError;
        # `CoordinationAddress.parse` raises ValueError
        raise MalformedRecord(f"a publish intent field is malformed: {caught}") from caught
    if encode_publish_intent(intent) != payload:
        raise MalformedRecord("a publish intent payload is not its canonical encoding")
    return intent
