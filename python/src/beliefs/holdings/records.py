"""The immutable, canonical holdings-observation record kind."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import final
from urllib.parse import urlsplit

from beliefs.errors import LoneSurrogate, MalformedRecord
from beliefs.identity import v1
from beliefs.sealed import sealed

__all__ = [
    "ALGORITHM_WIDTHS",
    "HOLDINGS_OBSERVATION_DOMAIN",
    "HOLDINGS_OBSERVATION_KIND",
    "Absent",
    "Found",
    "HoldingsObservation",
    "Locator",
    "Outcome",
    "StoreLocator",
    "UrlLocator",
    "holdings_observation",
    "require_canonical_digest",
    "require_store_relative_path",
    "url_locator",
]

HOLDINGS_OBSERVATION_DOMAIN = "science.holdings-observation.v1"
HOLDINGS_OBSERVATION_KIND = "holdings-observation"

_STORE_ID = re.compile(r"^[0-9a-f]{32}$")
_DIGEST = re.compile(r"^(?P<algorithm>[a-z0-9-]+):(?P<hex>[0-9a-f]+)$")
_OBSERVED_AT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REFERENCE = re.compile(r"^[0-9a-f]{64}$")
ALGORITHM_WIDTHS: Mapping[str, int] = MappingProxyType({"sha256": 64})


def require_canonical_digest(value: str, where: str) -> None:
    match = _DIGEST.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise MalformedRecord(f"{where}: {value!r} is not `<algorithm>:<lowercase hex>`")
    width = ALGORITHM_WIDTHS.get(match.group("algorithm"))
    if width is not None and len(match.group("hex")) != width:
        raise MalformedRecord(
            f"{where}: {value!r} does not carry {match.group('algorithm')}'s exact width of {width}"
        )


def require_store_relative_path(value: str) -> None:
    if not isinstance(value, str):
        raise MalformedRecord(f"store relative path: {value!r} is not a string")
    if not value:
        raise MalformedRecord("store relative path may not be empty")
    if "\x00" in value:
        raise MalformedRecord(f"store relative path {value!r} contains a NUL byte")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise MalformedRecord(f"store relative path {value!r} is not encodable as UTF-8: {exc}") from exc
    if value.startswith("/"):
        raise MalformedRecord(f"store relative path {value!r} must be relative")
    if value.endswith("/"):
        raise MalformedRecord(f"store relative path {value!r} may not end with '/'")
    for component in value.split("/"):
        if not component:
            raise MalformedRecord(f"store relative path {value!r} contains an empty component")
        if component in (".", ".."):
            raise MalformedRecord(f"store relative path {value!r} contains a {component!r} component")
        if component.startswith(".#~"):
            raise MalformedRecord(f"store relative path {value!r} aliases the reserved scratch sigil")


@sealed
@final
@dataclass(frozen=True)
class StoreLocator:
    store_id: str
    relative_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.store_id, str) or _STORE_ID.fullmatch(self.store_id) is None:
            raise MalformedRecord(f"store identity {self.store_id!r} is not 32 lowercase hexadecimal characters")
        require_store_relative_path(self.relative_path)

    def canonical(self) -> str:
        return f"store:{self.store_id}:{self.relative_path}"


_DEFAULT_PORTS = MappingProxyType({"https": 443, "http": 80})
_UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_HEX = frozenset("0123456789abcdefABCDEF")


def _remove_dot_segments(path: str) -> str:
    """RFC 3986 §5.2.4, step for step, so an existing empty segment survives
    (`/a//.` is `/a//`) and a removed final dot-segment leaves exactly the
    slash the algorithm leaves (`/a/..` is `/`)."""
    remaining, output = path, ""
    while remaining:
        if remaining.startswith("../"):
            remaining = remaining[3:]
        elif remaining.startswith(("./", "/./")):
            remaining = remaining[2:]
        elif remaining == "/.":
            remaining = "/"
        elif remaining.startswith("/../"):
            remaining = remaining[3:]
            output = output[: output.rfind("/")] if "/" in output else ""
        elif remaining == "/..":
            remaining = "/"
            output = output[: output.rfind("/")] if "/" in output else ""
        elif remaining in (".", ".."):
            remaining = ""
        else:
            start = 1 if remaining.startswith("/") else 0
            end = remaining.find("/", start)
            end = len(remaining) if end == -1 else end
            output += remaining[:end]
            remaining = remaining[end:]
    return output


def _normalized_path(path: str) -> str:
    """Percent-encoding normalized (uppercase hex, unreserved decoded), then
    dot-segments removed (RFC 3986 §5.2.4); the path component only."""
    out: list[str] = []
    index = 0
    while index < len(path):
        character = path[index]
        if character != "%":
            out.append(character)
            index += 1
            continue
        pair = path[index + 1 : index + 3]
        if len(pair) != 2 or any(digit not in _HEX for digit in pair):
            raise MalformedRecord(f"url path {path!r} carries a malformed percent-encoding")
        decoded = chr(int(pair, 16))
        out.append(decoded if decoded in _UNRESERVED else "%" + pair.upper())
        index += 3
    return _remove_dot_segments("".join(out))


def _canonical_url(spelling: str) -> str:
    if not isinstance(spelling, str) or not spelling:
        raise MalformedRecord("a url locator is a non-empty string")
    if any(not (0x21 <= ord(character) <= 0x7E) for character in spelling):
        raise MalformedRecord(f"url {spelling!r} carries a non-ASCII, whitespace or control byte")
    if "#" in spelling:
        raise MalformedRecord(f"url {spelling!r} carries a fragment; a fragment never names a location")
    try:
        parts = urlsplit(spelling)
    except ValueError as caught:  # an unbalanced IPv6 bracket
        raise MalformedRecord(f"url {spelling!r} does not split: {caught}") from caught
    scheme = parts.scheme.lower()
    if scheme not in _DEFAULT_PORTS:
        raise MalformedRecord(f"url {spelling!r}: scheme {parts.scheme!r} is outside http and https")
    if "@" in parts.netloc:
        raise MalformedRecord(f"url {spelling!r} carries userinfo; a credential never enters a location")
    host = parts.hostname
    if not host:
        raise MalformedRecord(f"url {spelling!r} names no host")
    if parts.netloc.startswith("["):
        try:
            ipaddress.IPv6Address(host)
        except ValueError as caught:
            raise MalformedRecord(f"url {spelling!r}: a bracketed host is an IPv6 literal") from caught
        host = f"[{host}]"  # `hostname` strips the brackets; the authority keeps them
    try:
        port = parts.port
    except ValueError as caught:
        raise MalformedRecord(f"url {spelling!r} carries a malformed port") from caught
    if port == 0:
        raise MalformedRecord(f"url {spelling!r} names port 0; no service listens there and nothing repairs it")
    authority = host if port in (None, _DEFAULT_PORTS[scheme]) else f"{host}:{port}"
    path = _normalized_path(parts.path or "/")
    query = "?" + parts.query if "?" in spelling else ""
    return f"{scheme}://{authority}{path}{query}"


@sealed
@final
@dataclass(frozen=True)
class UrlLocator:
    url: str

    def __post_init__(self) -> None:
        if _canonical_url(self.url) != self.url:
            raise MalformedRecord(f"url locator {self.url!r} is not the canonical spelling; construct it with url_locator")

    def canonical(self) -> str:
        return f"url:{self.url}"


def url_locator(spelling: str) -> UrlLocator:
    """Canonicalize under holdings §2's exact profile, or refuse."""
    return UrlLocator(_canonical_url(spelling))


Locator = StoreLocator | UrlLocator


@sealed
@final
@dataclass(frozen=True)
class Found:
    digest: str

    def __post_init__(self) -> None:
        require_canonical_digest(self.digest, "a found observation's digest")


@sealed
@final
@dataclass(frozen=True)
class Absent:
    pass


Outcome = Found | Absent


@sealed
@final
@dataclass(frozen=True)
class HoldingsObservation:
    location: Locator
    outcome: Outcome
    expected: str | None
    observer: str
    instrument: str
    event_token: str
    observed_at: str
    supersedes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.location, (StoreLocator, UrlLocator)):
            raise MalformedRecord("a holdings observation names a store or url locator")
        if not isinstance(self.outcome, (Found, Absent)):
            raise MalformedRecord("a holdings observation outcome is Found or Absent")
        if isinstance(self.location, UrlLocator) and isinstance(self.outcome, Absent):
            raise MalformedRecord("a url location never establishes absent; only a store dereference can")
        if self.expected is not None:
            require_canonical_digest(self.expected, "a holdings observation's expected digest")
            if isinstance(self.outcome, Found) and self.expected.split(":", 1)[0] != self.outcome.digest.split(":", 1)[0]:
                raise MalformedRecord("a found observation's expected digest must use the found digest's algorithm")
        for name in ("observer", "instrument", "event_token"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise MalformedRecord(f"a holdings observation's {name} must be a non-empty string")
            try:
                v1.encode(value)
            except LoneSurrogate as exc:
                raise MalformedRecord(f"a holdings observation's {name} must encode as identity text") from exc
        if not isinstance(self.observed_at, str) or _OBSERVED_AT.fullmatch(self.observed_at) is None:
            raise MalformedRecord("a holdings observation's observed_at is not canonical UTC")
        try:
            datetime.strptime(self.observed_at, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError as exc:
            raise MalformedRecord("a holdings observation's observed_at is not a calendar timestamp") from exc
        if not isinstance(self.supersedes, tuple) or any(
            not isinstance(reference, str) or _REFERENCE.fullmatch(reference) is None for reference in self.supersedes
        ):
            raise MalformedRecord("a holdings observation's supersedes values are canonical references")
        if tuple(sorted(set(self.supersedes))) != self.supersedes:
            raise MalformedRecord("a holdings observation's supersedes values are unique and sorted")

    def facet(self) -> dict[str, object]:
        doc: dict[str, object] = {
            "kind": HOLDINGS_OBSERVATION_KIND,
            "location": self.location_facet(),
            "outcome": {"finding": "found", "digest": self.outcome.digest}
            if isinstance(self.outcome, Found)
            else {"finding": "absent"},
            "observer": self.observer,
            "instrument": self.instrument,
            "event_token": self.event_token,
            "observed_at": self.observed_at,
            "supersedes": list(self.supersedes),
        }
        if self.expected is not None:
            doc["expected"] = self.expected
        return doc

    def identity(self) -> str:
        return v1.digest(HOLDINGS_OBSERVATION_DOMAIN, self.facet())

    def location_facet(self) -> dict[str, str]:
        if isinstance(self.location, UrlLocator):
            return {"type": "url", "url": self.location.url}
        return {"type": "store", "store_id": self.location.store_id, "relative_path": self.location.relative_path}


def holdings_observation(
    *,
    location: Locator,
    outcome: Outcome,
    expected: str | None = None,
    observer: str,
    instrument: str,
    event_token: str,
    observed_at: str,
    supersedes: tuple[HoldingsObservation, ...] = (),
) -> HoldingsObservation:
    if not isinstance(location, (StoreLocator, UrlLocator)):
        raise MalformedRecord("a holdings observation names a store or url locator")
    if not isinstance(supersedes, tuple) or not all(isinstance(predecessor, HoldingsObservation) for predecessor in supersedes):
        raise MalformedRecord("holdings observation predecessors are HoldingsObservation values")
    if any(predecessor.location.canonical() != location.canonical() for predecessor in supersedes):
        raise MalformedRecord("a holdings observation supersedes only records at its canonical location")
    return HoldingsObservation(
        location=location,
        outcome=outcome,
        expected=expected,
        observer=observer,
        instrument=instrument,
        event_token=event_token,
        observed_at=observed_at,
        supersedes=tuple(sorted({predecessor.identity() for predecessor in supersedes})),
    )
