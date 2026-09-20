"""The URL dereference boundary (url-retrieval design §4).

The survey instrument's preflight, pinned connection and streaming fetch,
made total over an injectable seam: `retrieve` answers with the **phase** the
look classifies from and never raises for a resolution, transport, status or
bound condition. Nothing here reads the network unless the production seam is
supplied; every test injects a scripted one.
"""

from __future__ import annotations

import hashlib
import ipaddress
import math
import socket
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http.client import HTTPException, HTTPSConnection
from pathlib import Path
from typing import Any, final
from urllib.parse import urljoin, urlsplit

from beliefs.errors import MalformedRecord
from beliefs.holdings.records import UrlLocator
from beliefs.sealed import sealed

__all__ = [
    "REFUSAL_CATEGORIES",
    "TRANSPORT_CATEGORIES",
    "Approved",
    "Failed",
    "NotAttempted",
    "PinnedHTTPSConnection",
    "PinningUnavailable",
    "Refused",
    "RetrievalBounds",
    "Retrieved",
    "UrlSeam",
    "pinned_connection",
    "preflight",
    "refuse_scratch_root",
    "retrieve",
    "system_resolver",
    "url_seam",
]

CHUNK = 1024 * 1024
REDIRECTS = (301, 302, 303, 307, 308)
REFUSAL_CATEGORIES = ("scheme", "no-host", "unresolvable", "non-public-address", "unpinnable", "malformed")
"""The closed set a refused hop is named by (decision 6); never a host, never bytes. `malformed`
is a server-supplied hop this transport will not split, resolve or send."""
TRANSPORT_CATEGORIES = ("timeout", "tls", "connection", "protocol")
"""The closed set a failure after the request began is named by; never the exception's text,
which for a certificate error carries the redirected host."""

Resolver = Callable[[str, int], list[str]]
ConnectionFactory = Callable[["Approved", float], HTTPSConnection]


@sealed
@final
@dataclass(frozen=True)
class RetrievalBounds:
    timeout_seconds: float
    max_bytes: int
    max_redirects: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.timeout_seconds, (int, float))
            or isinstance(self.timeout_seconds, bool)
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise MalformedRecord("timeout_seconds must be a finite positive number")
        for name in ("max_bytes", "max_redirects"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise MalformedRecord(f"{name} must be a non-negative integer")

    def instrument_inputs(self) -> tuple[tuple[str, str], ...]:
        return (
            ("timeout_seconds", repr(float(self.timeout_seconds))),
            ("max_bytes", str(self.max_bytes)),
            ("max_redirects", str(self.max_redirects)),
        )


@dataclass(frozen=True)
class Approved:
    """A hop that cleared preflight: the address validated, the request as it will be sent."""

    host: str
    port: int
    target: str
    authority: str
    address: str


@dataclass(frozen=True)
class Refused:
    category: str


@sealed
@final
@dataclass(frozen=True)
class Retrieved:
    digest: str
    size: int
    path: Path


@sealed
@final
@dataclass(frozen=True)
class NotAttempted:
    reason: str


@sealed
@final
@dataclass(frozen=True)
class Failed:
    reason: str


@dataclass(frozen=True)
class UrlSeam:
    resolve: Resolver
    connect: ConnectionFactory


class PinningUnavailable(RuntimeError):
    """The validated address cannot be used with name validation intact; no request is issued."""


def _transport_category(caught: OSError | HTTPException) -> str:
    """The fixed name a failure after the request began is reported by. Order
    matters: `socket.timeout` is a `TimeoutError` is an `OSError`; `ssl.SSLError`
    is an `OSError`; `RemoteDisconnected` is both an `OSError` and an `HTTPException`."""
    if isinstance(caught, TimeoutError):
        return "timeout"
    if isinstance(caught, ssl.SSLError):
        return "tls"
    if isinstance(caught, OSError):
        return "connection"
    return "protocol"


def system_resolver(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    return [str(info[4][0]) for info in infos]


class PinnedHTTPSConnection(HTTPSConnection):
    """Dials the validated address; keeps `host` as the name so SNI and the certificate validate against it."""

    def __init__(self, host: str, address: str, port: int, timeout: float, context: ssl.SSLContext) -> None:
        super().__init__(host, port=port, timeout=timeout, context=context)
        self._address = address
        self._pinned_context = context

    def connect(self) -> None:
        sock = socket.create_connection((self._address, self.port), self.timeout)
        self.sock = self._pinned_context.wrap_socket(sock, server_hostname=self.host)


def pinned_connection(approved: Approved, timeout: float) -> HTTPSConnection:
    context = ssl.create_default_context()
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        raise PinningUnavailable("cannot pin the validated address with hostname validation intact")
    return PinnedHTTPSConnection(approved.host, approved.address, approved.port, timeout, context)


def url_seam() -> UrlSeam:
    """The production seam: the system resolver and the pinned TLS connection."""
    return UrlSeam(resolve=system_resolver, connect=pinned_connection)


def _join_hop(current: str, location: str) -> str | None:
    """The next hop, or `None` for server-supplied bytes this transport will not
    split, resolve or send: non-ASCII, whitespace or a control byte, an
    authority `urlsplit` refuses, a port out of range. Nothing of the bytes is
    reported — `urlsplit`'s own errors name the host."""
    if any(not (0x21 <= ord(character) <= 0x7E) for character in location):
        return None
    try:
        joined = urljoin(current, location)
        urlsplit(joined).port  # noqa: B018 -- raises ValueError for an out-of-range port; the value itself is unused
    except ValueError:
        return None
    return joined


def preflight(url: str, resolver: Resolver) -> Approved | Refused:
    """Decide whether a hop may be requested at all; every refusal is a fixed category."""
    try:
        parts = urlsplit(url)
        parts.port  # noqa: B018 -- raises ValueError for an out-of-range port; the value itself is unused
    except ValueError:
        return Refused("malformed")
    if parts.scheme != "https":
        return Refused("scheme")
    if not parts.hostname:
        return Refused("no-host")
    try:
        port = 443 if parts.port is None else parts.port  # an explicit port is sent as given, `0` included
        addresses = resolver(parts.hostname, port)
    except (OSError, ValueError):
        return Refused("unresolvable")
    if not addresses:
        return Refused("unresolvable")
    if any(not ipaddress.ip_address(address).is_global for address in addresses):
        return Refused("non-public-address")
    target = (parts.path or "/") + ("?" + parts.query if "?" in url.split("#", 1)[0] else "")
    literal = f"[{parts.hostname}]" if parts.netloc.rpartition("@")[2].startswith("[") else parts.hostname
    authority = literal if port == 443 else f"{literal}:{port}"  # `hostname` strips the brackets; the wire keeps them
    return Approved(host=parts.hostname, port=port, target=target, authority=authority, address=addresses[0])


def refuse_scratch_root(scratch: Path, roots: tuple[Path, ...]) -> None:
    resolved = Path(scratch).resolve()
    for root in roots:
        bound = Path(root).resolve()
        if resolved == bound or bound in resolved.parents:
            raise MalformedRecord(f"scratch root {str(scratch)!r} lies under a corpus or store root {str(root)!r}")


def retrieve(locator: UrlLocator, bounds: RetrievalBounds, seam: UrlSeam, scratch: Path) -> Retrieved | NotAttempted | Failed:
    """One GET of the declared URL, every hop revalidated, the body streamed to scratch and hashed as it arrives."""
    if type(locator) is not UrlLocator:
        raise MalformedRecord("retrieve takes a UrlLocator")
    current = locator.url
    for hop in range(bounds.max_redirects + 1):
        decision = preflight(current, seam.resolve)
        if isinstance(decision, Refused):
            if hop == 0:
                return NotAttempted(decision.category)
            return Failed(f"redirect hop {hop} refused: {decision.category}")
        try:
            connection = seam.connect(decision, bounds.timeout_seconds)
        except PinningUnavailable:
            return NotAttempted("unpinnable") if hop == 0 else Failed(f"redirect hop {hop} refused: unpinnable")
        try:
            try:
                connection.request(
                    "GET", decision.target, headers={"Host": decision.authority, "Accept-Encoding": "identity"}
                )
                response = connection.getresponse()
            except (OSError, HTTPException) as caught:
                return Failed(f"transport failure: {_transport_category(caught)}")
            if response.status in REDIRECTS:
                location = response.getheader("Location")
                if not location:
                    return Failed("redirect without a location")
                joined = _join_hop(current, location)
                if joined is None:
                    return Failed(f"redirect hop {hop + 1} refused: malformed")
                current = joined
                continue
            if response.status != 200:
                return Failed(f"status {response.status}")
            encoding = response.getheader("Content-Encoding")
            if encoding is not None and encoding.strip().lower() != "identity":
                return Failed(f"content-encoding {encoding.strip().lower()} is not identity")
            return _stream(response, response.getheader("Content-Length"), bounds, scratch)
        finally:
            connection.close()
    return Failed(f"redirect limit {bounds.max_redirects} exceeded")


def _stream(response: Any, declared_length: str | None, bounds: RetrievalBounds, scratch: Path) -> Retrieved | Failed:
    scratch.mkdir(parents=True, exist_ok=True)
    target = scratch / f"retrieve-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%f')}-{id(response)}"
    try:
        outcome = _stream_into(response, declared_length, bounds, target)
    except BaseException:
        target.unlink(missing_ok=True)  # an unexpected failure propagates, and leaves no scratch file behind
        raise
    if isinstance(outcome, Failed):
        target.unlink(missing_ok=True)
    return outcome


def _stream_into(response: Any, declared_length: str | None, bounds: RetrievalBounds, target: Path) -> Retrieved | Failed:
    hasher = hashlib.sha256()
    size = 0
    with target.open("wb") as handle:
        while True:
            try:
                chunk = response.read(min(CHUNK, bounds.max_bytes - size + 1))  # never past the ceiling plus one
            except (OSError, HTTPException) as caught:
                return Failed(f"transport failure: {_transport_category(caught)}")
            if not chunk:
                break
            size += len(chunk)
            if size > bounds.max_bytes:
                return Failed(f"exceeded the {bounds.max_bytes}-byte streaming ceiling")
            hasher.update(chunk)
            handle.write(chunk)
    if declared_length is not None:
        try:
            expected = int(declared_length)
        except ValueError:
            return Failed("malformed content-length")
        if size < expected:
            return Failed(f"body shorter than content-length {expected}")
        if size > expected:
            return Failed(f"body longer than content-length {expected}")
    return Retrieved(digest=f"sha256:{hasher.hexdigest()}", size=size, path=target)
