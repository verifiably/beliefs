"""The URL dereference boundary.

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
from email.utils import parsedate_to_datetime
from http.client import HTTPException, HTTPSConnection
from pathlib import Path
from typing import Any, final
from urllib.parse import urljoin, urlsplit

from beliefs.errors import MalformedRecord
from beliefs.holdings.records import UrlLocator
from beliefs.sealed import sealed

__all__ = [
    "ALLOWED_HEADERS",
    "FAILURE_CATEGORIES",
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
"""The closed set a refused hop is named by: never a host, never bytes. `malformed`
is a server-supplied hop this transport will not split, resolve or send."""
TRANSPORT_CATEGORIES = ("timeout", "tls", "connection", "protocol")
"""The closed set a failure after the request began is named by; never the exception's text,
which for a certificate error carries the redirected host."""

FAILURE_CATEGORIES = TRANSPORT_CATEGORIES + (
    "status",
    "content-encoding",
    "length-mismatch",
    "length-malformed",
    "redirect-without-location",
    "redirect-limit",
    "byte-bound",
    "redirect-refused",
)
"""The closed set a `Failed` is named by: a transport category, or the condition that ended the retrieval."""
ALLOWED_HEADERS = ("content-type", "content-length", "last-modified", "etag")
"""The only response headers a `Retrieved` carries; any other (cookies, tokens) is dropped."""
RETRY_AFTER_STATUSES = (429, 503)

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
    status: int
    headers: tuple[tuple[str, str], ...]


@sealed
@final
@dataclass(frozen=True)
class NotAttempted:
    reason: str

    def __post_init__(self) -> None:
        if self.reason not in REFUSAL_CATEGORIES:
            raise MalformedRecord("NotAttempted reason must be a refusal category")


@sealed
@final
@dataclass(frozen=True)
class Failed:
    reason: str
    category: str
    status: int | None = None
    hop: int | None = None
    refusal: str | None = None
    retry_after: int | None = None

    def __post_init__(self) -> None:
        if self.category not in FAILURE_CATEGORIES:
            raise MalformedRecord("Failed category must be a failure category")
        refused = self.category == "redirect-refused"
        if refused != (self.refusal is not None):
            raise MalformedRecord("Failed refusal is present exactly when the category is redirect-refused")
        if refused and self.refusal not in REFUSAL_CATEGORIES:
            raise MalformedRecord("Failed refusal must be a refusal category")
        if refused and self.hop is None:
            raise MalformedRecord("a redirect-refused Failed names its hop")
        if self.retry_after is not None and self.category != "status":
            raise MalformedRecord("Failed retry_after is set only for a status failure")


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


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _retry_after(value: str | None, clock: Callable[[], datetime]) -> int | None:
    """Whole seconds from a `Retry-After` value (RFC 9110 section 10.2.3): delay-seconds as given, an
    HTTP-date as the rounded-up wait from `clock`, floored at 0; anything malformed is `None`."""
    if value is None:
        return None
    text = value.strip()
    if text.isascii() and text.isdigit():
        try:
            return int(text)
        except ValueError:  # more digits than the interpreter converts: malformed
            return None
    try:
        moment = parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return max(0, math.ceil((moment - clock()).total_seconds()))


def _allowed_headers(response: Any) -> tuple[tuple[str, str], ...]:
    pairs = ((name, response.getheader(name)) for name in sorted(ALLOWED_HEADERS))
    return tuple((name, value) for name, value in pairs if value is not None)


def retrieve(
    locator: UrlLocator,
    bounds: RetrievalBounds,
    seam: UrlSeam,
    scratch: Path,
    *,
    clock: Callable[[], datetime] = _utc_now,
) -> Retrieved | NotAttempted | Failed:
    """One GET of the declared URL, every hop revalidated, the body streamed to scratch and hashed as it arrives."""
    if type(locator) is not UrlLocator:
        raise MalformedRecord("retrieve takes a UrlLocator")
    current = locator.url
    for hop in range(bounds.max_redirects + 1):
        decision = preflight(current, seam.resolve)
        if isinstance(decision, Refused):
            if hop == 0:
                return NotAttempted(decision.category)
            return Failed(
                f"redirect hop {hop} refused: {decision.category}",
                "redirect-refused",
                hop=hop,
                refusal=decision.category,
            )
        try:
            connection = seam.connect(decision, bounds.timeout_seconds)
        except PinningUnavailable:
            if hop == 0:
                return NotAttempted("unpinnable")
            return Failed(f"redirect hop {hop} refused: unpinnable", "redirect-refused", hop=hop, refusal="unpinnable")
        try:
            try:
                connection.request(
                    "GET", decision.target, headers={"Host": decision.authority, "Accept-Encoding": "identity"}
                )
                response = connection.getresponse()
            except (OSError, HTTPException) as caught:
                category = _transport_category(caught)
                return Failed(f"transport failure: {category}", category)
            if response.status in REDIRECTS:
                location = response.getheader("Location")
                if not location:
                    return Failed("redirect without a location", "redirect-without-location", status=response.status)
                joined = _join_hop(current, location)
                if joined is None:
                    return Failed(
                        f"redirect hop {hop + 1} refused: malformed",
                        "redirect-refused",
                        hop=hop + 1,
                        refusal="malformed",
                    )
                current = joined
                continue
            if response.status != 200:
                retry_after = (
                    _retry_after(response.getheader("Retry-After"), clock)
                    if response.status in RETRY_AFTER_STATUSES
                    else None
                )
                return Failed(f"status {response.status}", "status", status=response.status, retry_after=retry_after)
            encoding = response.getheader("Content-Encoding")
            if encoding is not None and encoding.strip().lower() != "identity":
                return Failed("content-encoding is not identity", "content-encoding", status=response.status)
            return _stream(response, response.getheader("Content-Length"), bounds, scratch)
        finally:
            connection.close()
    return Failed(f"redirect limit {bounds.max_redirects} exceeded", "redirect-limit")


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


def _stream_into(
    response: Any, declared_length: str | None, bounds: RetrievalBounds, target: Path
) -> Retrieved | Failed:
    hasher = hashlib.sha256()
    size = 0
    with target.open("wb") as handle:
        while True:
            try:
                chunk = response.read(min(CHUNK, bounds.max_bytes - size + 1))  # never past the ceiling plus one
            except (OSError, HTTPException) as caught:
                category = _transport_category(caught)
                return Failed(f"transport failure: {category}", category, status=response.status)
            if not chunk:
                break
            size += len(chunk)
            if size > bounds.max_bytes:
                return Failed(
                    f"exceeded the {bounds.max_bytes}-byte streaming ceiling", "byte-bound", status=response.status
                )
            hasher.update(chunk)
            handle.write(chunk)
    if declared_length is not None:
        try:
            expected = int(declared_length)
        except ValueError:
            return Failed("malformed content-length", "length-malformed", status=response.status)
        if size < expected:
            return Failed(f"body shorter than content-length {expected}", "length-mismatch", status=response.status)
        if size > expected:
            return Failed(f"body longer than content-length {expected}", "length-mismatch", status=response.status)
    return Retrieved(
        digest=f"sha256:{hasher.hexdigest()}",
        size=size,
        path=target,
        status=response.status,
        headers=_allowed_headers(response),
    )
