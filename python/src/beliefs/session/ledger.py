"""The session ledger (writer-session design §3.2, §3.5): canonical JSON lines,
appended and fsynced before the index learns them; a reader that refuses a
malformed line and reports a torn tail; and the evidence union reconciliation
takes when a ledger is missing, empty, or unreadable."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeAlias, final

from beliefs.errors import LedgerMalformed, SessionLedgerFailed
from beliefs.sealed import sealed

__all__ = [
    "LINE_KINDS",
    "ActLine",
    "InvocationRecord",
    "LedgerEmpty",
    "LedgerEvidence",
    "LedgerMissing",
    "LedgerReader",
    "LedgerUnreadable",
    "LedgerWriter",
    "encode_line",
    "ledger_path",
    "open_ledger_reader",
    "read_ledger_evidence",
    "require_hex",
    "require_invocation_id",
    "utc_now",
    "validated_outcome",
]

LINE_KINDS = ("session-open", "invocation-open", "act", "invocation-close", "session-close")
LEDGER_FILE = "ledger.v1"
_INVOCATION = re.compile(r"[A-Za-z0-9_-]{1,64}")
_HEX = "0123456789abcdef"


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def encode_line(line: Mapping[str, object]) -> bytes:
    return (json.dumps(line, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def ledger_path(operations_root: Path, session_id: str) -> Path:
    return Path(operations_root) / "sessions" / session_id / LEDGER_FILE


def require_invocation_id(value: object) -> str:
    if type(value) is not str or _INVOCATION.fullmatch(value) is None:
        raise ValueError(f"invocation id must match [A-Za-z0-9_-]{{1,64}}: {value!r}")
    return value


def require_hex(value: object, width: int, what: str) -> str:
    if type(value) is not str or len(value) != width or any(c not in _HEX for c in value):
        raise ValueError(f"{what} must be {width} lowercase hexadecimal characters")
    return value


def _require_str(value: object, what: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{what} must be a non-empty string")
    return value


def _pairs(value: object, what: str) -> tuple[tuple[str, str], ...]:
    if type(value) is not list or any(
        type(pair) is not list or len(pair) != 2 or any(type(m) is not str or not m for m in pair) for pair in value
    ):
        raise ValueError(f"{what} must be a list of [uid, id] string pairs")
    return tuple((pair[0], pair[1]) for pair in value)


def validated_outcome(outcome: object) -> dict[str, object]:
    """§3.3: exactly `{"done": pairs}` or `{"refusal": {code, message, data}}`."""
    if not isinstance(outcome, Mapping) or len(outcome) != 1:
        raise ValueError("an outcome carries exactly one key, done or refusal")
    if "done" in outcome:
        return {"done": [list(pair) for pair in _pairs(outcome["done"], "a done outcome")]}
    if "refusal" in outcome:
        refusal = outcome["refusal"]
        if not isinstance(refusal, Mapping) or set(refusal) != {"code", "message", "data"}:
            raise ValueError("a refusal outcome carries exactly code, message and data")
        _require_str(refusal["code"], "refusal code")
        if type(refusal["message"]) is not str:
            raise ValueError("refusal message must be a string")
        if not isinstance(refusal["data"], Mapping):
            raise ValueError("refusal data must be a JSON object")
        return {"refusal": {"code": refusal["code"], "message": refusal["message"], "data": deepcopy(dict(refusal["data"]))}}
    raise ValueError("an outcome is done or refusal")


@sealed
@final
@dataclass(frozen=True)
class ActLine:
    invocation: str
    corpus: str
    entry: str
    intent: str
    record_ids: tuple[tuple[str, str], ...]


@sealed
@final
@dataclass(frozen=True)
class InvocationRecord:
    invocation: str
    command: str
    input_digest: str
    acts: tuple[ActLine, ...]
    outcome: Mapping[str, object] | None


class LedgerWriter:
    """Append-only; every line is written, flushed and fsynced before the call
    returns, and a failure anywhere in that sequence is terminal (§3.2)."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._file = open(self._path, "ab", buffering=0)  # noqa: SIM115 - held for the session's lifetime
        self._failed = False

    @property
    def failed(self) -> bool:
        return self._failed

    def _write(self, data: bytes) -> None:
        written = self._file.write(data)
        if written != len(data):
            raise OSError(f"short write: {written} of {len(data)} bytes reached the ledger")

    def append(self, line: Mapping[str, object]) -> None:
        if self._failed:
            raise SessionLedgerFailed("the session ledger failed earlier; nothing further is appended")
        data = encode_line(_validated_line(line, line_number=None))
        try:
            self._write(data)
            self._file.flush()
            os.fsync(self._file.fileno())
        except OSError as caught:
            self._failed = True
            try:
                self._file.close()
            except OSError:
                pass  # deliberate best-effort cleanup; must not mask the primary SessionLedgerFailed
            raise SessionLedgerFailed(f"ledger append failed: {caught}") from caught

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()


def _validated_line(line: Mapping[str, object], *, line_number: int | None) -> dict[str, object]:
    where = f"line {line_number}" if line_number is not None else "an appended line"
    try:
        if not isinstance(line, Mapping):
            raise TypeError("a ledger line is a JSON object")
        kind = line.get("line")
        if kind not in LINE_KINDS:
            raise ValueError(f"unknown line kind {kind!r}")
        expected = {
            "session-open": {"line", "session", "actor", "world", "permit", "at"},
            "invocation-open": {"line", "invocation", "command", "input_digest", "at"},
            "act": {"line", "invocation", "corpus", "entry", "intent", "records"},
            "invocation-close": {"line", "invocation", "outcome"},
            "session-close": {"line", "at"},
        }[kind]
        if set(line) != expected:
            raise ValueError(f"{kind} carries exactly {sorted(expected)}")
        if kind == "session-open":
            require_hex(line["session"], 32, "session id")
            _require_str(line["actor"], "actor")
            require_hex(line["world"], 32, "world id")
            permit = line["permit"]
            if not isinstance(permit, Mapping) or set(permit) != {"kinds", "act_families", "ungoverned"}:
                raise ValueError("permit summary carries kinds, act_families and ungoverned")
            _require_str(line["at"], "at")
        elif kind == "invocation-open":
            require_invocation_id(line["invocation"])
            _require_str(line["command"], "command")
            require_hex(line["input_digest"], 64, "input digest")
            _require_str(line["at"], "at")
        elif kind == "act":
            require_invocation_id(line["invocation"])
            require_hex(line["corpus"], 32, "corpus id")
            require_hex(line["entry"], 64, "entry digest")
            require_hex(line["intent"], 64, "intent digest")
            _pairs(line["records"], "act records")
        elif kind == "invocation-close":
            require_invocation_id(line["invocation"])
            validated_outcome(line["outcome"])
        else:
            _require_str(line["at"], "at")
    except (ValueError, TypeError) as caught:
        raise LedgerMalformed(f"{where}: {caught}") from caught
    return dict(line)


class LedgerReader:
    """One ledger, parsed in full (§3.5).

    By the time a line reaches this constructor, `_parse` has already refused
    any line the writer's protocol cannot produce (an `act` or
    `invocation-close` naming an invocation never opened or already closed, a
    repeated `invocation-open`, or any line after `session-close`) — so every
    `act`/`invocation-close` here targets an invocation this loop has already
    recorded, and no salvaging is needed."""

    def __init__(self, session_id: str, lines: list[dict[str, object]], torn_tail: bool) -> None:
        self.session_id = session_id
        self.torn_tail = torn_tail
        head = lines[0]
        self.actor = str(head["actor"])
        self.world_id = str(head["world"])
        self.closed = any(line["line"] == "session-close" for line in lines)
        self._records: dict[str, InvocationRecord] = {}
        self._order: list[str] = []
        acts: dict[str, list[ActLine]] = {}
        for line in lines[1:]:
            kind = line["line"]
            if kind == "invocation-open":
                invocation = str(line["invocation"])
                self._order.append(invocation)
                self._records[invocation] = InvocationRecord(invocation, str(line["command"]), str(line["input_digest"]), (), None)
                acts[invocation] = []
            elif kind == "act":
                invocation = str(line["invocation"])
                acts[invocation].append(
                    ActLine(invocation, str(line["corpus"]), str(line["entry"]), str(line["intent"]), _pairs(line["records"], "act records"))
                )
            elif kind == "invocation-close":
                invocation = str(line["invocation"])
                current = self._records[invocation]
                self._records[invocation] = InvocationRecord(invocation, current.command, current.input_digest, (), validated_outcome(line["outcome"]))
        for invocation, record in list(self._records.items()):
            self._records[invocation] = InvocationRecord(invocation, record.command, record.input_digest, tuple(acts.get(invocation, ())), record.outcome)

    @property
    def open_invocations(self) -> tuple[str, ...]:
        return tuple(i for i in self._order if self._records[i].outcome is None)

    def acts(self) -> tuple[ActLine, ...]:
        return tuple(act for i in self._order for act in self._records[i].acts)

    def invocations(self) -> tuple[InvocationRecord, ...]:
        return tuple(self._records[i] for i in self._order)

    def invocation(self, invocation_id: str) -> InvocationRecord | None:
        return self._records.get(invocation_id)


def _parse(session_id: str, raw: bytes) -> LedgerReader:
    """Parse every complete line, refusing both a malformed line's own shape
    (`_validated_line`) and a line the writer's protocol can never produce:
    an `act` or `invocation-close` naming an invocation never opened or
    already closed, a repeated `invocation-open`, or any line after
    `session-close` (design §7 row J7; fail-early forbids salvaging any of
    these rather than tolerating and reporting around them)."""
    if not raw:
        raise LedgerMalformed("line 1: the ledger is empty; no session-open")
    torn_tail = not raw.endswith(b"\n")
    chunks = raw.split(b"\n")[:-1]  # the last chunk is empty after a newline, or the torn tail
    lines: list[dict[str, object]] = []
    opened: set[str] = set()
    closed: set[str] = set()
    session_closed_at: int | None = None
    for number, chunk in enumerate(chunks, start=1):
        try:
            parsed = json.loads(chunk.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as caught:
            raise LedgerMalformed(f"line {number}: not a JSON object: {caught}") from caught
        validated = _validated_line(parsed, line_number=number)
        if number == 1:
            if validated["line"] != "session-open":
                raise LedgerMalformed("line 1: the first line is not session-open")
        elif session_closed_at is not None:
            raise LedgerMalformed(f"line {number}: no line follows session-close (line {session_closed_at})")
        else:
            kind = validated["line"]
            if kind == "invocation-open":
                invocation = str(validated["invocation"])
                if invocation in opened:
                    raise LedgerMalformed(f"line {number}: invocation {invocation!r} is already open")
                opened.add(invocation)
            elif kind == "act":
                invocation = str(validated["invocation"])
                if invocation not in opened:
                    raise LedgerMalformed(f"line {number}: act names invocation {invocation!r}, never opened")
                if invocation in closed:
                    raise LedgerMalformed(f"line {number}: act names invocation {invocation!r}, already closed")
            elif kind == "invocation-close":
                invocation = str(validated["invocation"])
                if invocation not in opened:
                    raise LedgerMalformed(f"line {number}: invocation-close names invocation {invocation!r}, never opened")
                if invocation in closed:
                    raise LedgerMalformed(f"line {number}: invocation {invocation!r} is already closed")
                closed.add(invocation)
            elif kind == "session-close":
                session_closed_at = number
            elif kind == "session-open":
                raise LedgerMalformed(f"line {number}: a second session-open")
        lines.append(validated)
    if not lines:
        raise LedgerMalformed("line 1: the ledger is empty; no session-open")
    return LedgerReader(session_id, lines, torn_tail)


def open_ledger_reader(operations_root: Path, session_id: str) -> LedgerReader:
    return _parse(session_id, ledger_path(operations_root, session_id).read_bytes())


@sealed
@final
@dataclass(frozen=True)
class LedgerMissing:
    session_id: str


@sealed
@final
@dataclass(frozen=True)
class LedgerEmpty:
    session_id: str


@sealed
@final
@dataclass(frozen=True)
class LedgerUnreadable:
    session_id: str
    error: str


LedgerEvidence: TypeAlias = LedgerReader | LedgerMissing | LedgerEmpty | LedgerUnreadable


def read_ledger_evidence(operations_root: Path, session_id: str) -> LedgerEvidence:
    """Reconciliation's input (§6, decision 14): never raises on ledger state."""
    path = ledger_path(operations_root, session_id)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return LedgerMissing(session_id)
    except OSError as caught:  # a directory in the file's place, a permission or device error: evidence, not an exception
        return LedgerUnreadable(session_id, f"{type(caught).__name__}: {caught}")
    if not raw:
        return LedgerEmpty(session_id)
    try:
        return _parse(session_id, raw)
    except LedgerMalformed as caught:
        return LedgerUnreadable(session_id, str(caught))
