"""The acquisition log: one JSON Lines record of every request and attempt behind a sealed set.

Each line is canonical `science.identity.v1` text, so an optional field is absent, never
null: `None` in these dataclasses means the key is not on the line. The parser refuses
anything the seal would later have to verify against the tree, naming the line.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, TypeVar, final

from beliefs.errors import CanonicalTextRefused, MalformedRecord
from beliefs.holdings.transport import ALLOWED_HEADERS, FAILURE_CATEGORIES, REFUSAL_CATEGORIES
from beliefs.identity import v1
from beliefs.report import SetSummary
from beliefs.sealed import sealed
from beliefs.tree import Tree, TreeMember, make_tree, tree_digest

__all__ = [
    "LOG_FAILURES",
    "LOG_FORMAT",
    "AcquisitionLog",
    "Attempt",
    "LogHeader",
    "Recorded",
    "RequestLine",
    "log_summary",
    "log_tree",
    "parse_acquisition_log",
    "render_acquisition_log",
]

_T = TypeVar("_T")
LOG_FORMAT = "science.acquisition-log.v1"
LOG_FAILURES = FAILURE_CATEGORIES + REFUSAL_CATEGORIES + ("expected-mismatch",)
_ATTEMPT_OUTCOMES = ("fetched", "failed", "not-attempted")
_FAILED_CATEGORIES = FAILURE_CATEGORIES + ("expected-mismatch",)
_RESULTS = ("fetched", "failed", "abandoned")
_ORIGINS = ("fetched", "imported")
_HEX32 = re.compile(r"[0-9a-f]{32}")
_FILE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def _require_digest(value: object, where: str) -> None:
    if type(value) is not str or _FILE_DIGEST.fullmatch(value) is None:
        raise MalformedRecord(f"{where} must be `sha256:` and 64 lowercase hex digits")


def _require_int(value: object, where: str, *, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise MalformedRecord(f"{where} must be an exact int of at least {minimum}")


def _require_str(value: object, where: str) -> None:
    if type(value) is not str or not value:
        raise MalformedRecord(f"{where} must be a non-empty string")


@sealed
@final
@dataclass(frozen=True)
class LogHeader:
    set: str
    origin: str
    fetched_by: str
    plan: Mapping[str, object] | None
    source_journals: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if type(self.set) is not str or _HEX32.fullmatch(self.set) is None:
            raise MalformedRecord("the log header's set is 32 lowercase hexadecimal characters")
        if self.origin not in _ORIGINS:
            raise MalformedRecord(f"the log header's origin {self.origin!r} is outside {_ORIGINS}")
        _require_str(self.fetched_by, "the log header's fetched_by")
        if (self.plan is not None) != (self.origin == "fetched"):
            raise MalformedRecord("the log header carries a plan if and only if its origin is fetched")
        if self.plan is not None and not isinstance(self.plan, Mapping):
            raise MalformedRecord("the log header's plan is a mapping")
        if type(self.source_journals) is not tuple:
            raise MalformedRecord("the log header's source journals are a tuple")
        for row in self.source_journals:
            if type(row) is not tuple or len(row) != 2:
                raise MalformedRecord("a source journal is a (name, digest) pair")
            _require_str(row[0], "a source journal's name")
            _require_digest(row[1], "a source journal's digest")
        if bool(self.source_journals) != (self.origin == "imported"):
            raise MalformedRecord("the log header names source journals if and only if its origin is imported")


@sealed
@final
@dataclass(frozen=True)
class Attempt:
    started_at: str | None
    completed_at: str | None
    outcome: str
    status: int | None
    headers: tuple[tuple[str, str], ...]
    failure: str | None

    def __post_init__(self) -> None:
        for name in ("started_at", "completed_at"):
            value = getattr(self, name)
            if value is not None:
                _require_str(value, f"an attempt's {name}")
        if self.outcome not in _ATTEMPT_OUTCOMES:
            raise MalformedRecord(f"an attempt's outcome {self.outcome!r} is outside {_ATTEMPT_OUTCOMES}")
        if self.status is not None:
            _require_int(self.status, "an attempt's status", minimum=0)
        if type(self.headers) is not tuple:
            raise MalformedRecord("an attempt's headers are a tuple of pairs")
        for row in self.headers:
            if type(row) is not tuple or len(row) != 2 or type(row[0]) is not str or type(row[1]) is not str:
                raise MalformedRecord("an attempt's header is a (name, value) pair of strings")
            if row[0] not in ALLOWED_HEADERS:
                raise MalformedRecord(f"attempt header {row[0]!r} is outside {ALLOWED_HEADERS}")
        names = [name for name, _ in self.headers]
        if names != sorted(set(names)):
            raise MalformedRecord("an attempt's headers are sorted by name and name each header once")
        if (self.failure is None) != (self.outcome == "fetched"):
            raise MalformedRecord("an attempt carries a failure if and only if its outcome is not fetched")
        if self.failure is not None:
            allowed = REFUSAL_CATEGORIES if self.outcome == "not-attempted" else _FAILED_CATEGORIES
            if self.failure not in allowed:
                raise MalformedRecord(f"a {self.outcome} attempt's failure {self.failure!r} is outside {allowed}")


@sealed
@final
@dataclass(frozen=True)
class Recorded:
    journal: int
    line: int
    digest: str | None

    def __post_init__(self) -> None:
        _require_int(self.journal, "a recorded journal index", minimum=0)
        _require_int(self.line, "a recorded journal line", minimum=1)
        if self.digest is not None:
            _require_digest(self.digest, "a recorded digest")


@sealed
@final
@dataclass(frozen=True)
class RequestLine:
    seq: int
    url: str
    parent: int | None
    expected: str | None
    attempts: tuple[Attempt, ...]
    result: str
    digest: str | None
    size: int | None
    member: str | None
    recorded: Recorded | None

    def __post_init__(self) -> None:
        _require_int(self.seq, "a request's seq", minimum=1)
        _require_str(self.url, "a request's url")
        if self.parent is not None:
            _require_int(self.parent, "a request's parent", minimum=1)
        if self.expected is not None:
            _require_digest(self.expected, "a request's expected digest")
        if type(self.attempts) is not tuple or any(type(a) is not Attempt for a in self.attempts):
            raise MalformedRecord("a request's attempts are a tuple of attempts")
        if self.result not in _RESULTS:
            raise MalformedRecord(f"a request's result {self.result!r} is outside {_RESULTS}")
        held = (self.digest, self.size, self.member)
        if self.result == "fetched":
            if any(value is None for value in held):
                raise MalformedRecord("a fetched request carries a digest, size and member")
            # TreeMember validates the path, digest and size
            TreeMember(path=self.member, digest=self.digest, size=self.size)  # pyright: ignore[reportArgumentType]
        elif any(value is not None for value in held):
            raise MalformedRecord("only a fetched request carries a digest, size and member")
        if self.recorded is not None and type(self.recorded) is not Recorded:
            raise MalformedRecord("a request's recorded is a Recorded")


@sealed
@final
@dataclass(frozen=True)
class AcquisitionLog:
    header: LogHeader
    lines: tuple[RequestLine, ...]

    def __post_init__(self) -> None:
        if type(self.header) is not LogHeader:
            raise MalformedRecord("an acquisition log starts with a LogHeader")
        if type(self.lines) is not tuple or any(type(line) is not RequestLine for line in self.lines):
            raise MalformedRecord("an acquisition log's lines are a tuple of request lines")
        imported = self.header.origin == "imported"
        results: dict[int, str] = {}
        for index, line in enumerate(self.lines, start=1):
            where = f"acquisition log line {index + 1}"
            if line.seq != index:
                raise MalformedRecord(f"{where}: seq {line.seq} is not {index}; seq runs contiguously from 1")
            if line.parent is not None and results.get(line.parent) != "fetched":
                raise MalformedRecord(f"{where}: parent {line.parent} is not an earlier fetched request")
            if imported != (line.recorded is not None):
                raise MalformedRecord(f"{where}: recorded is present if and only if the origin is imported")
            if line.recorded is not None:
                if line.recorded.journal >= len(self.header.source_journals):
                    raise MalformedRecord(f"{where}: recorded names a journal the header does not")
                if line.recorded.digest is not None and line.recorded.digest != line.digest:
                    raise MalformedRecord(f"{where}: the recorded digest differs from the line's digest")
            if not imported:
                self._check_fetched_origin(line, where)
            results[line.seq] = line.result

    @staticmethod
    def _check_fetched_origin(line: RequestLine, where: str) -> None:
        if not line.attempts:
            raise MalformedRecord(f"{where}: a fetched-origin request has at least one attempt")
        for attempt in line.attempts:
            if attempt.started_at is None or attempt.completed_at is None:
                raise MalformedRecord(f"{where}: a fetched-origin attempt has started_at and completed_at")
        got = [attempt.outcome == "fetched" for attempt in line.attempts]
        if line.result == "fetched" and not got[-1]:
            raise MalformedRecord(f"{where}: a fetched request's last attempt is fetched")
        if line.result != "fetched" and any(got):
            raise MalformedRecord(f"{where}: a {line.result} request has no fetched attempt")


def _attempt_value(attempt: Attempt) -> dict[str, object]:
    value: dict[str, object] = {"outcome": attempt.outcome}
    if attempt.started_at is not None:
        value["started_at"] = attempt.started_at
    if attempt.completed_at is not None:
        value["completed_at"] = attempt.completed_at
    if attempt.status is not None:
        value["status"] = attempt.status
    if attempt.headers:
        value["headers"] = dict(attempt.headers)
    if attempt.failure is not None:
        value["failure"] = attempt.failure
    return value


def _line_value(line: RequestLine) -> dict[str, object]:
    value: dict[str, object] = {
        "seq": line.seq,
        "request": {"method": "GET", "url": line.url},
        "attempts": [_attempt_value(attempt) for attempt in line.attempts],
        "result": line.result,
    }
    if line.parent is not None:
        value["parent"] = line.parent
    if line.expected is not None:
        value["expected"] = line.expected
    if line.digest is not None:
        value["digest"] = line.digest
        value["size"] = line.size
        value["member"] = line.member
    if line.recorded is not None:
        recorded: dict[str, object] = {"journal": line.recorded.journal, "line": line.recorded.line}
        if line.recorded.digest is not None:
            recorded["digest"] = line.recorded.digest
        value["recorded"] = recorded
    return value


def _header_value(header: LogHeader) -> dict[str, object]:
    value: dict[str, object] = {
        "format": LOG_FORMAT,
        "set": header.set,
        "origin": header.origin,
        "fetched_by": header.fetched_by,
    }
    if header.plan is not None:
        value["plan"] = header.plan
    if header.source_journals:
        value["source_journals"] = [{"digest": digest, "name": name} for name, digest in header.source_journals]
    return value


def render_acquisition_log(log: AcquisitionLog) -> bytes:
    rows = [_header_value(log.header), *(_line_value(line) for line in log.lines)]
    return b"".join(v1.encode(row) + b"\n" for row in rows)


def _keys(value: object, required: set[str], optional: set[str], where: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise MalformedRecord(f"{where} is an object")
    keys = set(value)  # pyright: ignore[reportUnknownArgumentType]
    if not required <= keys <= required | optional:
        raise MalformedRecord(f"{where} has exactly the keys {sorted(required)} and optionally {sorted(optional)}")
    return value  # pyright: ignore[reportUnknownVariableType]


def _parse_header(value: object) -> LogHeader:
    where = "acquisition log line 1"
    if type(value) is dict and value.get("origin") == "imported":  # pyright: ignore[reportUnknownMemberType]
        row = _keys(value, {"format", "set", "origin", "fetched_by", "source_journals"}, set(), where)
    else:
        row = _keys(value, {"format", "set", "origin", "fetched_by", "plan"}, set(), where)
    if row["format"] != LOG_FORMAT:
        raise MalformedRecord(f"{where}: format is {LOG_FORMAT!r}")
    journals: list[tuple[str, str]] = []
    if "source_journals" in row:
        if type(row["source_journals"]) is not list:
            raise MalformedRecord(f"{where}: source_journals is a list")
        for item in row["source_journals"]:
            entry = _keys(item, {"name", "digest"}, set(), f"{where}: a source journal")
            journals.append((entry["name"], entry["digest"]))
    return LogHeader(
        set=row["set"],
        origin=row["origin"],
        fetched_by=row["fetched_by"],
        plan=row.get("plan"),
        source_journals=tuple(journals),
    )


def _parse_attempt(value: object, where: str) -> Attempt:
    row = _keys(
        value,
        {"outcome"},
        {"started_at", "completed_at", "status", "headers", "failure"},
        f"{where}: an attempt",
    )
    headers = row.get("headers", {})
    if type(headers) is not dict or any(type(v) is not str for v in headers.values()):  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        raise MalformedRecord(f"{where}: an attempt's headers are an object of strings")
    return Attempt(
        started_at=row.get("started_at"),
        completed_at=row.get("completed_at"),
        outcome=row["outcome"],
        status=row.get("status"),
        headers=tuple(sorted(headers.items())),  # pyright: ignore[reportUnknownArgumentType]
        failure=row.get("failure"),
    )


def _parse_line(value: object, number: int) -> RequestLine:
    where = f"acquisition log line {number}"
    row = _keys(
        value,
        {"seq", "request", "attempts", "result"},
        {"parent", "expected", "digest", "size", "member", "recorded"},
        where,
    )
    request = _keys(row["request"], {"method", "url"}, set(), f"{where}: request")
    if request["method"] != "GET":
        raise MalformedRecord(f"{where}: the request method is GET")
    if type(row["attempts"]) is not list:
        raise MalformedRecord(f"{where}: attempts is a list")
    recorded = None
    if "recorded" in row:
        raw = _keys(row["recorded"], {"journal", "line"}, {"digest"}, f"{where}: recorded")
        recorded = Recorded(journal=raw["journal"], line=raw["line"], digest=raw.get("digest"))
    return RequestLine(
        seq=row["seq"],
        url=request["url"],
        parent=row.get("parent"),
        expected=row.get("expected"),
        attempts=tuple(_parse_attempt(item, where) for item in row["attempts"]),
        result=row["result"],
        digest=row.get("digest"),
        size=row.get("size"),
        member=row.get("member"),
        recorded=recorded,
    )


def _named(number: int, parse: Callable[..., _T], *args: object) -> _T:
    """Run a line's parser, naming the line in any refusal that does not already."""
    try:
        return parse(*args)
    except MalformedRecord as caught:
        if str(caught).startswith(f"acquisition log line {number}"):
            raise
        raise MalformedRecord(f"acquisition log line {number}: {caught}") from caught


def parse_acquisition_log(data: bytes) -> AcquisitionLog:
    if not data.endswith(b"\n"):
        raise MalformedRecord("an acquisition log ends with a line feed")
    rows: list[object] = []
    for number, raw in enumerate(data[:-1].split(b"\n"), start=1):
        try:
            rows.append(v1.decode(raw))
        except CanonicalTextRefused as caught:
            raise MalformedRecord(f"acquisition log line {number} is not canonical text: {caught}") from caught
    header = _named(1, _parse_header, rows[0])
    lines = tuple(_named(number, _parse_line, row, number) for number, row in enumerate(rows[1:], start=2))
    return AcquisitionLog(header, lines)


def log_tree(log: AcquisitionLog) -> Tree:
    return make_tree(
        TreeMember(path=line.member, digest=line.digest, size=line.size)  # pyright: ignore[reportArgumentType]
        for line in log.lines
        if line.result == "fetched"
    )


def log_summary(log: AcquisitionLog) -> SetSummary:
    counts = {result: sum(line.result == result for line in log.lines) for result in _RESULTS}
    traversal = log.header.plan is not None and "traversal" in log.header.plan
    return SetSummary(
        origin=log.header.origin,
        fetched_by=log.header.fetched_by,
        requests=len(log.lines),
        fetched=counts["fetched"],
        failed=counts["failed"],
        abandoned=counts["abandoned"],
        traversal_complete=not (traversal and (counts["failed"] or counts["abandoned"])),
        log="sha256:" + hashlib.sha256(render_acquisition_log(log)).hexdigest(),
        tree=tree_digest(log_tree(log)),
    )
