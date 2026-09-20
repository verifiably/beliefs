"""The URL dereference boundary: preflight, the pinned connection, the fetch."""

from __future__ import annotations

import socket
import ssl
from hashlib import sha256
from http.client import BadStatusLine, IncompleteRead
from pathlib import Path
from typing import Any

import pytest
from holdings_transport_fixtures import PUBLIC, LocalTlsServer, Scripted, Served, scripted_seam, tls_seam

from beliefs.errors import MalformedRecord
from beliefs.holdings import transport
from beliefs.holdings.records import url_locator
from beliefs.holdings.transport import (
    Approved,
    Failed,
    NotAttempted,
    PinnedHTTPSConnection,
    PinningUnavailable,
    RetrievalBounds,
    Retrieved,
    pinned_connection,
    preflight,
    refuse_scratch_root,
    retrieve,
)

BOUNDS = RetrievalBounds(timeout_seconds=5.0, max_bytes=64, max_redirects=3)
DATA = url_locator("https://example.org/data")
SIGNED_HOP = "https://bucket.s3.example/data?X-Amz-Signature=deadbeefcafe&X-Amz-Credential=AKIA"
TOKEN_HOST_HOP = "https://tok3n-9f2a.example.net/data"


def ok(body: bytes, **headers: str) -> Scripted:
    return Scripted(200, {"Content-Length": str(len(body)), **headers}, (body,))


def fetch(
    script: dict[str, Scripted],
    locator: Any = DATA,
    bounds: RetrievalBounds = BOUNDS,
    *,
    tmp_path: Path,
    **seam_kwargs: Any,
) -> tuple[Retrieved | NotAttempted | Failed, Any]:
    seam, log = scripted_seam(script, **seam_kwargs)
    return retrieve(locator, bounds, seam, tmp_path), log


# --- preflight ---------------------------------------------------------------


@pytest.mark.parametrize("url,category", [("http://example.org/", "scheme"), ("https://example.org/", "unresolvable")])
def test_preflight_refuses_with_a_category(url, category):
    def failing(_host, _port):
        raise OSError("no such host")

    decision = preflight(url, failing)
    assert decision == transport.Refused(category)


def test_preflight_refuses_a_non_public_address():
    assert preflight("https://example.org/", lambda _h, _p: ["10.0.0.7"]) == transport.Refused("non-public-address")
    assert preflight("https://example.org/", lambda _h, _p: []) == transport.Refused("unresolvable")


def test_preflight_approves_with_the_faithful_target_and_authority():
    approved = preflight("https://example.org:8443/data?", lambda _h, _p: [PUBLIC])
    assert approved == Approved(host="example.org", port=8443, target="/data?", authority="example.org:8443", address=PUBLIC)
    relative = preflight("https://example.org/a/b/", lambda _h, _p: [PUBLIC])
    assert isinstance(relative, Approved) and relative.authority == "example.org"
    literal = preflight("https://[2606:4700:4700::1111]:8443/x", lambda _h, _p: [PUBLIC])
    assert literal == Approved(host="2606:4700:4700::1111", port=8443, target="/x", authority="[2606:4700:4700::1111]:8443", address=PUBLIC)
    bracketed = preflight("https://[2606:4700:4700::1111]/x", lambda _h, _p: [PUBLIC])
    assert isinstance(bracketed, Approved) and bracketed.authority == "[2606:4700:4700::1111]"


@pytest.mark.parametrize("url", ["https://[tok3n-9f2a.example.net]/data", "https://example.org:99999/data"])
def test_preflight_refuses_an_unsplittable_url_as_malformed_without_its_bytes(url):
    assert preflight(url, lambda _h, _p: [PUBLIC]) == transport.Refused("malformed")


# --- the request as sent -----------------------------------------------------


def test_the_request_transmits_the_canonical_locator_faithfully(tmp_path):
    result, log = fetch({"/data?": ok(b"x")}, url_locator("https://example.org:8443/data?"), tmp_path=tmp_path)
    assert isinstance(result, Retrieved)
    (method, target, headers), = log.requests
    assert (method, target) == ("GET", "/data?")
    assert headers["Host"] == "example.org:8443"
    assert headers["Accept-Encoding"] == "identity"
    result, log = fetch({"/a/b/": ok(b"x")}, url_locator("https://example.org/a/./b/"), tmp_path=tmp_path)
    assert log.requests[0][1] == "/a/b/" and log.requests[0][2]["Host"] == "example.org"
    result, log = fetch({"/x": ok(b"6")}, url_locator("https://[2606:4700:4700::1111]:8443/x"), tmp_path=tmp_path)
    assert log.requests[0][2]["Host"] == "[2606:4700:4700::1111]:8443"
    assert log.dialled == [("2606:4700:4700::1111", PUBLIC, 8443)]


# --- the pinned connection ---------------------------------------------------


def test_the_pinned_connection_dials_the_validated_address_and_validates_the_name(monkeypatch):
    dialled: list[tuple[str, int]] = []
    wrapped: list[str] = []
    sentinel = object()

    class FakeContext:
        check_hostname = True
        verify_mode = ssl.CERT_REQUIRED

        def wrap_socket(self, sock: Any, *, server_hostname: str) -> Any:
            assert sock is sentinel
            wrapped.append(server_hostname)
            return sentinel

    monkeypatch.setattr(transport.socket, "create_connection", lambda address, timeout: dialled.append(address) or sentinel)
    connection = PinnedHTTPSConnection("host.example", PUBLIC, 443, 5.0, FakeContext())  # type: ignore[arg-type]
    connection.connect()
    assert dialled == [(PUBLIC, 443)]
    assert wrapped == ["host.example"]


@pytest.mark.parametrize("check_hostname,verify_mode", [(False, ssl.CERT_REQUIRED), (True, ssl.CERT_NONE)])
def test_a_context_that_would_skip_validation_refuses_to_pin(monkeypatch, check_hostname, verify_mode):
    class Lax:
        pass

    context = Lax()
    context.check_hostname = check_hostname  # type: ignore[attr-defined]
    context.verify_mode = verify_mode  # type: ignore[attr-defined]
    monkeypatch.setattr(transport.ssl, "create_default_context", lambda: context)
    with pytest.raises(PinningUnavailable):
        pinned_connection(Approved("host.example", 443, "/a", "host.example", PUBLIC), 5.0)


def test_an_unpinnable_context_issues_no_request(tmp_path, monkeypatch):
    monkeypatch.setattr(transport.socket, "create_connection", lambda *a, **k: pytest.fail("a socket was opened"))
    result, log = fetch({"/data": ok(b"x")}, tmp_path=tmp_path, unpinnable=True)
    assert result == NotAttempted("unpinnable")
    assert log.requests == []


# --- redirects ---------------------------------------------------------------


def test_a_relative_location_is_joined_before_it_is_revalidated(tmp_path):
    result, log = fetch({"/data": Scripted(302, {"Location": "/moved"}), "/moved": ok(b"body")}, tmp_path=tmp_path)
    assert isinstance(result, Retrieved)
    assert [target for _m, target, _h in log.requests] == ["/data", "/moved"]


@pytest.mark.parametrize("hop", [SIGNED_HOP, TOKEN_HOST_HOP])
def test_a_refused_hop_is_failed_by_ordinal_and_category_and_never_by_its_bytes(tmp_path, hop):
    seam, log = scripted_seam({"/data": Scripted(302, {"Location": hop})})
    private = transport.UrlSeam(resolve=lambda host, _p: ["10.1.1.1"] if host != "example.org" else [PUBLIC], connect=seam.connect)
    result = retrieve(DATA, BOUNDS, private, tmp_path)
    assert result == Failed("redirect hop 1 refused: non-public-address")
    assert isinstance(result, Failed)
    for secret in ("X-Amz-Signature", "deadbeefcafe", "AKIA", "tok3n-9f2a", "s3.example", "example.net"):
        assert secret not in result.reason
    assert len(log.requests) == 1


@pytest.mark.parametrize(
    "hop",
    [
        "https://[tok3n-9f2a.example.net]/data",  # `urlsplit` raises naming the host
        "https://tok3n-9f2a.example.net:99999/data",  # `.port` raises
        "https://tok3n-9f2a.example.net/däta",  # `putrequest` would raise naming the target
        "https://tok3n-9f2a.example.net/da ta",
        "/moved\r\nX-Injected: tok3n",
    ],
)
def test_a_malformed_hop_is_refused_as_malformed_and_never_by_its_bytes(tmp_path, hop):
    result, log = fetch({"/data": Scripted(302, {"Location": hop})}, tmp_path=tmp_path)
    assert result == Failed("redirect hop 1 refused: malformed")
    assert isinstance(result, Failed)
    assert "tok3n" not in result.reason and "example.net" not in result.reason
    assert len(log.requests) == 1


def test_too_many_redirects_is_failed_naming_the_bound(tmp_path):
    script = {f"/h{i}": Scripted(302, {"Location": f"/h{i + 1}"}) for i in range(6)}
    script["/data"] = Scripted(302, {"Location": "/h0"})
    result, _ = fetch(script, tmp_path=tmp_path)
    assert result == Failed("redirect limit 3 exceeded")


def test_a_redirect_without_a_location_is_failed(tmp_path):
    result, _ = fetch({"/data": Scripted(302, {})}, tmp_path=tmp_path)
    assert result == Failed("redirect without a location")


# --- the body ----------------------------------------------------------------


@pytest.mark.parametrize(
    "scripted,reason",
    [
        (Scripted(404, {}, (b"",)), "status 404"),
        (Scripted(500, {}, (b"",)), "status 500"),
        (Scripted(200, {"Content-Length": "4", "Content-Encoding": "gzip"}, (b"abcd",)), "content-encoding gzip is not identity"),
        (Scripted(200, {"Content-Length": "8"}, (b"abcd",)), "body shorter than content-length 8"),
        (Scripted(200, {"Content-Length": "2"}, (b"abcd",)), "body longer than content-length 2"),
        (Scripted(200, {}, (b"ab",), raise_on_read=TimeoutError("timed out")), "transport failure: timeout"),
        (Scripted(200, {"Content-Length": "many"}, (b"ab",)), "malformed content-length"),
    ],
)
def test_an_incomplete_or_wrong_body_is_failed_carrying_no_digest(tmp_path, scripted, reason):
    result, _ = fetch({"/data": scripted}, tmp_path=tmp_path)
    assert result == Failed(reason)
    assert not hasattr(result, "digest")
    assert list(tmp_path.iterdir()) == []


def test_the_ceiling_ends_the_stream_and_finalizes_no_digest(tmp_path):
    body = b"x" * 65
    result, log = fetch({"/data": Scripted(200, {}, (body[:32], body[32:]))}, tmp_path=tmp_path)
    assert result == Failed("exceeded the 64-byte streaming ceiling")
    assert log.reads == [65, 33]  # each read asks for the remaining allowance plus one
    assert list(tmp_path.iterdir()) == []


def test_each_read_is_bounded_by_the_remaining_allowance_plus_one(tmp_path):
    result, log = fetch({"/data": Scripted(200, {}, (b"y" * 1000,))}, tmp_path=tmp_path)
    assert result == Failed("exceeded the 64-byte streaming ceiling")
    assert log.reads == [65]  # one read of 65 bytes, never 1 MiB against a 64-byte ceiling


@pytest.mark.parametrize(
    "raised,category",
    [
        (socket.timeout("timed out"), "timeout"),  # noqa: UP041 -- deliberately the pre-3.10 spelling alongside TimeoutError
        (TimeoutError("timed out"), "timeout"),
        (ssl.SSLCertVerificationError("hostname 'tok3n-9f2a.example.net' doesn't match"), "tls"),
        (ssl.SSLError(1, "tlsv1 alert"), "tls"),
        (ConnectionResetError("peer reset"), "connection"),
        (IncompleteRead(b"ab", 6), "protocol"),
        (BadStatusLine("garbage"), "protocol"),
    ],
)
def test_a_transport_failure_is_failed_by_category_and_leaves_no_scratch(tmp_path, raised, category):
    result, _ = fetch({"/data": Scripted(200, {}, (b"ab",), raise_on_read=raised)}, tmp_path=tmp_path)
    assert result == Failed(f"transport failure: {category}")
    assert list(tmp_path.iterdir()) == []
    result, log = fetch({"/data": Scripted(raise_on_request=raised)}, tmp_path=tmp_path)
    assert result == Failed(f"transport failure: {category}")
    assert isinstance(result, Failed)
    assert "tok3n" not in result.reason and "example.net" not in result.reason and "peer" not in result.reason
    assert len(log.requests) == 1


def test_a_programming_failure_mid_stream_raises_and_leaves_no_scratch(tmp_path):
    with pytest.raises(RuntimeError, match="boom"):
        fetch({"/data": Scripted(200, {}, (b"ab",), raise_on_read=RuntimeError("boom"))}, tmp_path=tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("timeout", [float("inf"), float("nan"), 0, -1.0, True])
def test_bounds_refuse_a_non_finite_or_non_positive_timeout(timeout):
    with pytest.raises(MalformedRecord):
        RetrievalBounds(timeout_seconds=timeout, max_bytes=1, max_redirects=0)


def test_a_complete_body_is_retrieved_with_its_digest_and_scratch_path(tmp_path):
    result, _ = fetch({"/data": ok(b"payload")}, tmp_path=tmp_path)
    assert isinstance(result, Retrieved)
    assert result.digest == "sha256:" + sha256(b"payload").hexdigest()
    assert result.size == 7
    assert result.path.parent == tmp_path and result.path.read_bytes() == b"payload"


def test_the_scratch_root_refuses_the_roots_and_their_descendants(tmp_path):
    (tmp_path / "observer").mkdir()
    for scratch in (tmp_path / "observer", tmp_path / "observer" / "tmp"):
        with pytest.raises(MalformedRecord):
            refuse_scratch_root(scratch, (tmp_path / "observer", tmp_path / "store"))
    refuse_scratch_root(tmp_path / "scratch", (tmp_path / "observer", tmp_path / "store"))


# --- the in-process TLS server: real framing, real reads, real validation ------


def test_over_tls_a_complete_body_is_retrieved_and_the_request_arrives_faithfully(tmp_path):
    with LocalTlsServer({"/data?": Served(body=b"payload")}) as server:
        seam, log = tls_seam(server)
        result = retrieve(url_locator("https://example.org:8443/data?"), BOUNDS, seam, tmp_path)
    assert isinstance(result, Retrieved)
    assert result.digest == "sha256:" + sha256(b"payload").hexdigest() and result.size == 7
    ((method, target, headers),) = log.requests
    assert (method, target, headers["Host"], headers["Accept-Encoding"]) == ("GET", "/data?", "example.org:8443", "identity")
    assert log.dialled == [("example.org", PUBLIC, 8443)]
    result.path.unlink()


def test_over_tls_an_ipv6_authority_arrives_bracketed_in_host(tmp_path):
    with LocalTlsServer({"/x": Served(body=b"6")}) as server:
        seam, log = tls_seam(server)
        result = retrieve(url_locator("https://[2606:4700:4700::1111]:8443/x"), BOUNDS, seam, tmp_path)
    assert isinstance(result, Retrieved)  # the certificate carries the IP SAN; validation ran against the literal
    assert log.requests[0][2]["Host"] == "[2606:4700:4700::1111]:8443"
    assert log.dialled == [("2606:4700:4700::1111", PUBLIC, 8443)]
    result.path.unlink()


def test_over_tls_a_truncated_chunked_body_is_a_protocol_failure_with_no_scratch(tmp_path):
    with LocalTlsServer({"/data": Served(body=b"partial", truncate_chunked=True)}) as server:
        seam, _ = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert result == Failed("transport failure: protocol")
    assert list(tmp_path.iterdir()) == []


def test_over_tls_a_redirect_is_followed_and_each_hop_revalidated(tmp_path):
    script = {"/data": Served(302, {"Location": "https://mirror.example.org/moved"}), "/moved": Served(body=b"moved")}
    with LocalTlsServer(script) as server:
        seam, log = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert isinstance(result, Retrieved) and result.size == 5
    assert [(target, headers["Host"]) for _m, target, headers in log.requests] == [("/data", "example.org"), ("/moved", "mirror.example.org")]
    assert [host for host, _a, _p in log.dialled] == ["example.org", "mirror.example.org"]
    result.path.unlink()


def test_over_tls_the_ceiling_ends_the_stream_one_byte_past_the_bound(tmp_path):
    with LocalTlsServer({"/data": Served(body=b"z" * 4096)}) as server:
        seam, _ = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert result == Failed("exceeded the 64-byte streaming ceiling")
    assert list(tmp_path.iterdir()) == []


def test_over_tls_a_certificate_failure_after_a_credential_bearing_redirect_names_only_its_category(tmp_path):
    with LocalTlsServer({"/data": Served(302, {"Location": TOKEN_HOST_HOP})}) as server:
        seam, log = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert result == Failed("transport failure: tls")
    assert isinstance(result, Failed)
    assert "tok3n-9f2a" not in result.reason and "example.net" not in result.reason
    assert len(log.requests) == 1  # the second hop's handshake never completed, so the server parsed no request
    assert [host for host, _a, _p in log.dialled] == ["example.org", "tok3n-9f2a.example.net"]
