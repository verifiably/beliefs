"""Two injected transports: a scripted fake, and an in-process TLS server on a
loopback port presenting the committed test certificate. No test reaches the
network: every seam's resolver answers a fixed global address and its
connection dials the fake or the loopback server."""

from __future__ import annotations

import ssl
import threading
from dataclasses import dataclass, field
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from beliefs.holdings.transport import Approved, PinnedHTTPSConnection, PinningUnavailable, UrlSeam

PUBLIC = "93.184.216.34"
TLS_DIR = Path(__file__).parent / "fixtures" / "tls"
CERT = TLS_DIR / "server.pem"
KEY = TLS_DIR / "server.key"


@dataclass
class Scripted:
    """One scripted response: status, headers, body chunks; or the exception
    the request or a read raises (`OSError`, `HTTPException`, or anything else
    to prove an unexpected failure propagates)."""

    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    chunks: tuple[bytes, ...] = (b"",)
    raise_on_read: BaseException | None = None
    raise_on_request: BaseException | None = None


@dataclass
class RequestLog:
    requests: list[tuple[str, str, dict[str, str]]] = field(default_factory=list)
    dialled: list[tuple[str, str, int]] = field(default_factory=list)
    reads: list[int] = field(default_factory=list)
    """Every `read(size)` the transport asked for, in order."""


class _Response:
    def __init__(self, scripted: Scripted, log: RequestLog) -> None:
        self.status = scripted.status
        self._headers = scripted.headers
        self._pending = b"".join(scripted.chunks)
        self._boundaries = [len(chunk) for chunk in scripted.chunks]
        self._raise = scripted.raise_on_read
        self._log = log

    def getheader(self, name: str) -> str | None:
        for key, value in self._headers.items():
            if key.lower() == name.lower():
                return value
        return None

    def read(self, size: int) -> bytes:
        """Honours `size` like `HTTPResponse.read(amt)`: at most `size` bytes,
        and never past the current scripted chunk, so a test can shape reads."""
        self._log.reads.append(size)
        if self._raise is not None:
            raise self._raise
        if not self._pending:
            return b""
        limit = min(size, self._boundaries[0]) if self._boundaries and self._boundaries[0] else size
        out, self._pending = self._pending[:limit], self._pending[limit:]
        if self._boundaries:
            self._boundaries[0] -= len(out)
            if self._boundaries[0] <= 0:
                self._boundaries.pop(0)
        return out


class ScriptedConnection:
    """Answers each request from `script`, keyed by request target."""

    def __init__(self, approved: Approved, script: dict[str, Scripted], log: RequestLog) -> None:
        self._approved = approved
        self._script = script
        self._log = log
        log.dialled.append((approved.host, approved.address, approved.port))

    def request(self, method: str, target: str, headers: dict[str, str]) -> None:
        self._log.requests.append((method, target, dict(headers)))
        self._target = target
        scripted = self._script[target]
        if scripted.raise_on_request is not None:
            raise scripted.raise_on_request

    def getresponse(self) -> Any:
        return _Response(self._script[self._target], self._log)

    def close(self) -> None:
        pass


def scripted_seam(script: dict[str, Scripted], *, log: RequestLog | None = None, unpinnable: bool = False) -> tuple[UrlSeam, RequestLog]:
    log = RequestLog() if log is None else log

    def connect(approved: Approved, timeout: float) -> Any:
        del timeout
        if unpinnable:
            raise PinningUnavailable("cannot pin the validated address with hostname validation intact")
        return ScriptedConnection(approved, script, log)

    return UrlSeam(resolve=lambda _host, _port: [PUBLIC], connect=connect), log


# --- the in-process TLS server -----------------------------------------------


@dataclass
class Served:
    """One response the local server sends. `truncate_chunked` announces a
    chunked body, sends part of one chunk and closes: the client's read raises
    `http.client.IncompleteRead`. A `Content-Length` that disagrees with the
    body is sent as written and the connection closed after the body."""

    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    truncate_chunked: bool = False


class LocalTlsServer:
    """An HTTPS server on `127.0.0.1:<free port>` presenting `CERT`; it records
    every request it parses into `self.log` exactly as received."""

    def __init__(self, script: dict[str, Served]) -> None:
        self.log = RequestLog()
        log = self.log

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args: Any) -> None:
                pass

            def do_GET(self) -> None:
                log.requests.append(("GET", self.path, {key: value for key, value in self.headers.items()}))
                served = script.get(self.path)
                if served is None:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                self.send_response(served.status)
                if served.truncate_chunked:
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    self.wfile.write(f"{len(served.body) + 16:x}\r\n".encode() + served.body)
                    self.wfile.flush()
                    self.close_connection = True
                    return
                for key, value in served.headers.items():
                    self.send_header(key, value)
                declared = served.headers.get("Content-Length")
                if declared is None:
                    self.send_header("Content-Length", str(len(served.body)))
                elif declared != str(len(served.body)):
                    self.close_connection = True
                self.end_headers()
                self.wfile.write(served.body)

        class Server(ThreadingHTTPServer):
            daemon_threads = True

            def handle_error(self, request: Any, client_address: Any) -> None:
                pass  # a client that rejects the certificate is a test's expected outcome

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(CERT), str(KEY))
        self._server = Server(("127.0.0.1", 0), Handler)
        self._server.socket = context.wrap_socket(self._server.socket, server_side=True)
        self.port: int = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> LocalTlsServer:  # noqa: PYI034 -- matches the brief's transcribed signature exactly
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(5)


def tls_seam(server: LocalTlsServer) -> tuple[UrlSeam, RequestLog]:
    """The production pinned connection over the local server: the resolver
    answers a global address for every name, the connection dials loopback on
    the server's port with `server_hostname` the approved name, and the context
    trusts `CERT` with `check_hostname` and `CERT_REQUIRED` intact — a name the
    certificate does not carry fails the handshake."""
    context = ssl.create_default_context(cafile=str(CERT))
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    log = server.log

    def connect(approved: Approved, timeout: float) -> HTTPSConnection:
        log.dialled.append((approved.host, approved.address, approved.port))
        return PinnedHTTPSConnection(approved.host, "127.0.0.1", server.port, timeout, context)

    return UrlSeam(resolve=lambda _host, _port: [PUBLIC], connect=connect), log
