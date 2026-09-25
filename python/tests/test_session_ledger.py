"""J7 (and the ledger halves of J6): canonical lines, fsync before index, the
reader's refusals, the torn tail, and the terminal LedgerFailed state."""

from __future__ import annotations

import os
from collections.abc import Mapping

import pytest

from beliefs.coordination import CoordinationAddress
from beliefs.errors import LedgerMalformed, SessionLedgerFailed
from beliefs.session.ledger import (
    LINE_KINDS,
    ActLine,
    LedgerEmpty,
    LedgerMissing,
    LedgerUnreadable,
    LedgerWriter,
    SelectLine,
    encode_line,
    ledger_path,
    open_ledger_reader,
    read_ledger_evidence,
    validated_outcome,
)
from beliefs.session.reconcile import reconcile

SESSION = "a" * 32
ACTOR = f"session:{SESSION}"
WORLD = "b" * 32
DIGEST = "c" * 64
ENTRY = "d" * 64
INTENT = "e" * 64
AT = "2026-09-05T12:00:00Z"
P, Q, L, R1, R2 = ("1" * 32, "2" * 32, "3" * 32, "4" * 32, "5" * 32)
P_AT_R1 = f"coord:{P}@{R1}"
Q_AT_R2 = f"coord:{Q}@{R2}"


def open_line(**project):
    """The session-open line; `open_line(project=...)` adds the post-amendment key."""
    return {"line": "session-open", "session": SESSION, "actor": ACTOR, "world": WORLD,
            "permit": {"kinds": ["proposition"], "act_families": ["corpus-write"], "ungoverned": False}, "at": AT, **project}


def invocation_open(name):
    return {"line": "invocation-open", "invocation": name, "command": "mint", "input_digest": DIGEST, "at": AT}


def invocation_close(name):
    return {"line": "invocation-close", "invocation": name, "outcome": {"done": []}}


def act(name, entry=ENTRY):
    return {"line": "act", "invocation": name, "corpus": WORLD, "entry": entry, "intent": INTENT, "records": []}


def select(name, project):
    return {"line": "select", "invocation": name, "project": project}


def ledger_bytes(*lines):
    return b"".join(encode_line(line) for line in lines)


def selection_of(reader, invocation):
    record = reader.invocation(invocation)
    assert record is not None
    return record.selection


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
    assert set(LINE_KINDS) == {"session-open", "invocation-open", "act", "invocation-close", "session-close", "select"}


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


# --- selection lines (selection design §3, §4.3) -------------------------------------
def test_the_reader_reads_the_initial_project_each_selection_and_the_attribution(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    writer = LedgerWriter(path)
    a1, a2, b1 = "1" * 64, "2" * 64, "3" * 64
    for line in (
        open_line(project=P_AT_R1),
        invocation_open("A"),
        act("A", a1),
        select("A", Q_AT_R2),  # one invocation may act, select, then act again (decision 5)
        act("A", a2),
        invocation_close("A"),
        invocation_open("B"),
        select("B", None),
        act("B", b1),
        invocation_close("B"),
        invocation_open("C"),
        invocation_close("C"),
    ):
        writer.append(line)
    writer.close()
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.initial_project == CoordinationAddress(P, revision=R1)
    record_a, record_b, record_c = reader.invocations()
    assert record_a.selection == SelectLine("A", CoordinationAddress(Q, revision=R2))
    assert record_b.selection == SelectLine("B", None)
    assert record_c.selection is None
    assert [(act_line.entry, project) for act_line, project in reader.attributed_acts()] == [
        (a1, CoordinationAddress(P, revision=R1)),
        (a2, CoordinationAddress(Q, revision=R2)),
        (b1, None),
    ]


def test_a_historical_session_open_without_project_reads_as_no_selection(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(ledger_bytes(*lines()))  # open_line() is the pre-amendment six-key shape
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.initial_project is None
    assert [project for _, project in reader.attributed_acts()] == [None]
    evidence = read_ledger_evidence(tmp_path, SESSION)
    assert type(evidence) is not LedgerUnreadable
    assert "session-ledger-malformed" not in {finding.code for finding in reconcile((evidence,), {})}


def test_a_torn_select_leaves_the_previous_selection_standing(tmp_path):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(
        ledger_bytes(open_line(project=P_AT_R1), invocation_open("A"))
        + encode_line(select("A", Q_AT_R2))[:25]
    )
    reader = open_ledger_reader(tmp_path, SESSION)
    assert reader.torn_tail is True
    assert reader.initial_project == CoordinationAddress(P, revision=R1)
    assert selection_of(reader, "A") is None


@pytest.mark.parametrize(
    "line",
    [
        pytest.param(select("A", f"coord:{P}"), id="unpinned"),
        pytest.param(select("A", f"coord:{P}/{L}@{R1}"), id="subordinate"),
        pytest.param(select("A", "project-health"), id="not-an-address"),
        pytest.param(select("A", f"coord:{'A' * 32}@{R1}"), id="uppercase-hex"),  # alphabetic hex: P's digits have no case
        pytest.param(select("A", f"coord:{P}@{R1}@{R2}"), id="extra-segment"),
        pytest.param(select("A", 5), id="not-a-string"),
        pytest.param({**select("A", P_AT_R1), "at": AT}, id="extra-key"),
        pytest.param({"line": "select", "invocation": "A"}, id="missing-project"),
        pytest.param({"line": "select", "invocation": "bad id!", "project": None}, id="bad-invocation-id"),
    ],
)
def test_a_malformed_select_line_is_refused_naming_its_number(tmp_path, line):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(ledger_bytes(open_line(project=None), invocation_open("A"), line))
    with pytest.raises(LedgerMalformed, match="line 3"):
        open_ledger_reader(tmp_path, SESSION)


@pytest.mark.parametrize("project", [f"coord:{P}", f"coord:{P}/{L}@{R1}", 7])
def test_a_malformed_session_open_project_is_refused(tmp_path, project):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(ledger_bytes(open_line(project=project)))
    with pytest.raises(LedgerMalformed, match="line 1"):
        open_ledger_reader(tmp_path, SESSION)


@pytest.mark.parametrize(
    "raw, message",
    [
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), invocation_open("B"), select("A", P_AT_R1)),
            "line 4", id="select-names-an-abandoned-invocation",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), invocation_open("B"), invocation_close("B"), select("A", P_AT_R1)),
            "line 5", id="select-while-no-invocation-is-current",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), invocation_close("A"), select("A", P_AT_R1)),
            "line 4", id="select-after-its-invocation-closed",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), select("A", P_AT_R1)),
            "line 2", id="select-names-an-unopened-invocation",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), select("A", P_AT_R1), select("A", None)),
            "line 4", id="a-second-select-in-one-invocation",
        ),
        pytest.param(
            ledger_bytes(open_line(project=None), invocation_open("A"), act("A"), invocation_open("B"), select("A", P_AT_R1), act("B")),
            "line 5", id="an-invalid-select-cannot-reattribute-a-later-act",
        ),
    ],
)
def test_a_select_the_writer_could_not_have_written_is_refused(tmp_path, raw, message):
    path = ledger_path(tmp_path, SESSION)
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    with pytest.raises(LedgerMalformed, match=message):
        open_ledger_reader(tmp_path, SESSION)
    evidence = read_ledger_evidence(tmp_path, SESSION)
    assert type(evidence) is LedgerUnreadable and message in evidence.error
