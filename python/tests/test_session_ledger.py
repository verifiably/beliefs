"""J7 (and the ledger halves of J6): canonical lines, fsync before index, the
reader's refusals, the torn tail, and the terminal LedgerFailed state."""

from __future__ import annotations

import os
from collections.abc import Mapping

import pytest

from beliefs.errors import LedgerMalformed, SessionLedgerFailed
from beliefs.session.ledger import (
    LINE_KINDS,
    ActLine,
    LedgerEmpty,
    LedgerMissing,
    LedgerUnreadable,
    LedgerWriter,
    encode_line,
    ledger_path,
    open_ledger_reader,
    read_ledger_evidence,
    validated_outcome,
)

SESSION = "a" * 32
ACTOR = f"session:{SESSION}"
WORLD = "b" * 32
DIGEST = "c" * 64
ENTRY = "d" * 64
INTENT = "e" * 64
AT = "2026-09-05T12:00:00Z"


def open_line():
    return {"line": "session-open", "session": SESSION, "actor": ACTOR, "world": WORLD,
            "permit": {"kinds": ["proposition"], "act_families": ["corpus-write"], "ungoverned": False}, "at": AT}


def lines():
    return [
        open_line(),
        {"line": "invocation-open", "invocation": "A", "command": "mint", "input_digest": DIGEST, "at": AT},
        {"line": "act", "invocation": "A", "corpus": WORLD, "entry": ENTRY, "intent": INTENT, "records": [["u1", "proposition:p1"]]},
        {"line": "invocation-close", "invocation": "A", "outcome": {"done": [["u1", "proposition:p1"]]}},
        {"line": "session-close", "at": AT},
    ]


@pytest.fixture()
def fsyncs(monkeypatch):
    calls = []
    real = os.fsync

    def counting(fd):
        calls.append(fd)
        return real(fd)

    monkeypatch.setattr(os, "fsync", counting)
    return calls


def test_lines_are_canonical_json_one_per_line():
    encoded = encode_line({"z": 1, "a": [1, 2], "line": "act"})
    assert encoded == b'{"a":[1,2],"line":"act","z":1}\n'
    assert set(LINE_KINDS) == {"session-open", "invocation-open", "act", "invocation-close", "session-close"}


def test_each_append_is_fsynced_once_and_lands_before_return(tmp_path, fsyncs):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    for index, line in enumerate(lines(), start=1):
        writer.append(line)
        assert len(fsyncs) == index
        assert path.read_bytes().endswith(encode_line(line))
    writer.close()


def test_the_reader_round_trips_every_line(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    for line in lines():
        writer.append(line)
    writer.close()
    reader = open_ledger_reader(tmp_path, SESSION)
    assert (reader.session_id, reader.actor, reader.world_id, reader.closed, reader.torn_tail) == (SESSION, ACTOR, WORLD, True, False)
    assert reader.open_invocations == ()
    (record,) = reader.invocations()
    assert record.command == "mint" and record.input_digest == DIGEST
    assert record.acts == (ActLine("A", WORLD, ENTRY, INTENT, (("u1", "proposition:p1"),)),)
    assert record.outcome == {"done": [["u1", "proposition:p1"]]}
    assert reader.invocation("A") is record and reader.invocation("Z") is None


def test_open_invocations_lists_every_unclosed_one_in_order(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    writer.append(open_line())
    for name in ("A", "B", "C"):
        writer.append({"line": "invocation-open", "invocation": name, "command": "mint", "input_digest": DIGEST, "at": AT})
    writer.append({"line": "invocation-close", "invocation": "B", "outcome": {"refusal": {"code": "x", "message": "m", "data": {}}}})
    writer.close()
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.open_invocations == ("A", "C") and reader.closed is False


def test_a_torn_tail_is_reported_and_every_complete_line_is_read(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    for line in lines()[:3]:
        writer.append(line)
    writer.close()
    with path.open("ab") as handle:
        handle.write(b'{"line":"invocation-close","invoc')
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.torn_tail is True and len(reader.acts()) == 1 and reader.open_invocations == ("A",)


@pytest.mark.parametrize(
    "bad, message",
    [
        (b"not json\n", "line 2"),
        (b'{"line":"unknown-kind"}\n', "line 2"),
        (b'{"line":"act","invocation":"A","corpus":"x","entry":"short","intent":"' + b"e" * 64 + b'","records":[]}\n', "line 2"),
    ],
)
def test_a_malformed_interior_line_is_refused_naming_its_number(tmp_path, bad, message):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(encode_line(open_line()) + bad + encode_line({"line": "session-close", "at": AT}))
    with pytest.raises(LedgerMalformed, match=message):
        open_ledger_reader(tmp_path, SESSION)


def test_a_first_line_that_is_not_session_open_is_malformed(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(encode_line({"line": "session-close", "at": AT}))
    with pytest.raises(LedgerMalformed, match="line 1"):
        open_ledger_reader(tmp_path, SESSION)


@pytest.mark.parametrize(
    "raw, message",
    [
        pytest.param(
            encode_line(open_line())
            + encode_line({"line": "invocation-close", "invocation": "A", "outcome": {"done": []}}),
            "line 2",
            id="invocation-close-never-opened",
        ),
        pytest.param(
            encode_line(open_line())
            + encode_line({"line": "act", "invocation": "A", "corpus": WORLD, "entry": ENTRY, "intent": INTENT, "records": []}),
            "line 2",
            id="act-never-opened",
        ),
        pytest.param(
            encode_line(open_line())
            + encode_line({"line": "invocation-open", "invocation": "A", "command": "mint", "input_digest": DIGEST, "at": AT})
            + encode_line({"line": "invocation-close", "invocation": "A", "outcome": {"done": []}})
            + encode_line({"line": "act", "invocation": "A", "corpus": WORLD, "entry": ENTRY, "intent": INTENT, "records": []}),
            "line 4",
            id="act-after-its-invocation-closed",
        ),
        pytest.param(
            encode_line(open_line())
            + encode_line({"line": "invocation-open", "invocation": "A", "command": "mint", "input_digest": DIGEST, "at": AT})
            + encode_line({"line": "invocation-open", "invocation": "A", "command": "mint", "input_digest": DIGEST, "at": AT}),
            "line 3",
            id="invocation-open-reopened",
        ),
        pytest.param(
            encode_line(open_line())
            + encode_line({"line": "session-close", "at": AT})
            + encode_line({"line": "session-close", "at": AT}),
            "line 3",
            id="line-after-session-close",
        ),
        pytest.param(
            encode_line(open_line())
            + encode_line(open_line()),
            "line 2",
            id="a-second-session-open",
        ),
        pytest.param(
            encode_line(open_line())
            + encode_line({"line": "invocation-open", "invocation": "A", "command": "mint", "input_digest": DIGEST, "at": AT})
            + encode_line({"line": "invocation-close", "invocation": "A", "outcome": {"done": []}})
            + encode_line({"line": "invocation-close", "invocation": "A", "outcome": {"done": []}}),
            "line 4",
            id="invocation-close-of-an-already-closed-invocation",
        ),
    ],
)
def test_a_line_the_writer_protocol_cannot_produce_is_refused_naming_its_number(tmp_path, raw, message):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    with pytest.raises(LedgerMalformed, match=message):
        open_ledger_reader(tmp_path, SESSION)


def test_an_empty_or_missing_ledger_is_not_malformed_to_the_reader_but_is_evidence(tmp_path):
    with pytest.raises(FileNotFoundError):
        open_ledger_reader(tmp_path, SESSION)
    assert read_ledger_evidence(tmp_path, SESSION) == LedgerMissing(SESSION)
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")
    with pytest.raises(LedgerMalformed):
        open_ledger_reader(tmp_path, SESSION)
    assert read_ledger_evidence(tmp_path, SESSION) == LedgerEmpty(SESSION)
    path.write_bytes(b"garbage\n")
    evidence = read_ledger_evidence(tmp_path, SESSION)
    assert type(evidence) is LedgerUnreadable and evidence.session_id == SESSION and "line 1" in evidence.error
    path.unlink()
    path.mkdir()  # a directory where the file should be: IsADirectoryError on read
    evidence = read_ledger_evidence(tmp_path, SESSION)
    assert type(evidence) is LedgerUnreadable and "IsADirectoryError" in evidence.error


def test_a_partial_write_ends_the_writer_and_preserves_the_bytes(tmp_path, monkeypatch):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    writer.append(open_line())
    before = path.read_bytes()
    partial = encode_line(lines()[1])[:17]

    def failing_write(data):
        writer._file.write(partial)
        raise OSError("disk gone")

    monkeypatch.setattr(writer, "_write", failing_write)
    with pytest.raises(SessionLedgerFailed):
        writer.append(lines()[1])
    assert writer.failed is True
    with pytest.raises(SessionLedgerFailed):
        writer.append(lines()[2])
    assert path.read_bytes() == before + partial
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.torn_tail is True and reader.open_invocations == ()


def test_a_short_write_without_an_exception_ends_the_writer(tmp_path, monkeypatch):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    writer.append(open_line())
    before = path.read_bytes()
    real_write = writer._file.write

    def short(data):
        return real_write(data[:17])  # the OS accepted part of the line and returned normally

    monkeypatch.setattr(writer._file, "write", short)
    with pytest.raises(SessionLedgerFailed, match="short write"):
        writer.append(lines()[1])
    assert writer.failed is True
    assert path.read_bytes() == before + encode_line(lines()[1])[:17]
    assert open_ledger_reader(tmp_path, SESSION).torn_tail is True


def test_a_failed_fsync_ends_the_writer(tmp_path, monkeypatch):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    writer.append(open_line())

    def failing(fd):
        raise OSError("fsync failed")

    monkeypatch.setattr(os, "fsync", failing)
    with pytest.raises(SessionLedgerFailed):
        writer.append(lines()[1])
    assert writer.failed is True


def test_validated_outcome_accepts_the_two_shapes_and_nothing_else():
    assert validated_outcome({"done": [["u", "proposition:p"]]}) == {"done": [["u", "proposition:p"]]}
    refusal = validated_outcome({"refusal": {"code": "c", "message": "m", "data": {"k": 1}}})["refusal"]
    assert isinstance(refusal, Mapping) and refusal["code"] == "c"
    for bad in ({}, {"done": [], "refusal": {}}, {"done": [["u"]]}, {"refusal": {"code": 1, "message": "m", "data": {}}}, {"refusal": {"code": "c", "message": "m", "data": []}}, {"other": 1}):
        with pytest.raises(ValueError):
            validated_outcome(bad)
