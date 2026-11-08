"""The acquisition log: its parser, renderer, tree and summary."""

from __future__ import annotations

import dataclasses
import hashlib
from typing import Any

import pytest

from beliefs.errors import MalformedRecord
from beliefs.holdings.acquisition_log import (
    LOG_FAILURES,
    LOG_FORMAT,
    AcquisitionLog,
    Attempt,
    LogHeader,
    Recorded,
    RequestLine,
    log_summary,
    log_tree,
    parse_acquisition_log,
    render_acquisition_log,
)
from beliefs.holdings.transport import FAILURE_CATEGORIES, REFUSAL_CATEGORIES
from beliefs.identity import v1
from beliefs.report import SetSummary
from beliefs.tree import TreeMember, make_tree, tree_digest

_SET = "a" * 32
_D1 = "sha256:" + "1" * 64
_D2 = "sha256:" + "2" * 64
_D3 = "sha256:" + "3" * 64
_T0 = "2026-11-08T00:00:00Z"
_T1 = "2026-11-08T00:00:01Z"


def got(outcome: str = "fetched", **changes: Any) -> Attempt:
    fields: dict[str, Any] = {
        "started_at": _T0,
        "completed_at": _T1,
        "outcome": outcome,
        "status": 200 if outcome == "fetched" else None,
        "headers": (("content-type", "text/csv"),) if outcome == "fetched" else (),
        "failure": None if outcome == "fetched" else "timeout",
    }
    fields.update(changes)
    return Attempt(**fields)


def fetched_line(seq: int, url: str, member: str, digest: str = _D1, **changes: Any) -> RequestLine:
    fields: dict[str, Any] = {
        "seq": seq,
        "url": url,
        "parent": None,
        "expected": None,
        "attempts": (got(),),
        "result": "fetched",
        "digest": digest,
        "size": 5,
        "member": member,
        "recorded": None,
    }
    fields.update(changes)
    return RequestLine(**fields)


def failed_line(seq: int, result: str = "failed", **changes: Any) -> RequestLine:
    fields: dict[str, Any] = {
        "seq": seq,
        "url": f"https://example.org/{seq}",
        "parent": None,
        "expected": None,
        "attempts": (got("failed"), got("failed", failure="status", status=503)),
        "result": result,
        "digest": None,
        "size": None,
        "member": None,
        "recorded": None,
    }
    fields.update(changes)
    return RequestLine(**fields)


def fetched_header(plan: dict[str, Any] | None = None) -> LogHeader:
    return LogHeader(
        set=_SET,
        origin="fetched",
        fetched_by="science/acquire.v1 (beliefs transport)",
        plan={"seeds": ["https://example.org/a"]} if plan is None else plan,
        source_journals=(),
    )


def imported_header() -> LogHeader:
    return LogHeader(
        set=_SET,
        origin="imported",
        fetched_by="sun scripts/acquire.py@c269ffca",
        plan=None,
        source_journals=(("journal-a.jsonl", _D3),),
    )


def fetched_log() -> AcquisitionLog:
    return AcquisitionLog(
        fetched_header(),
        (
            fetched_line(1, "https://example.org/a", "a/one.csv", attempts=(got("failed"), got())),
            fetched_line(
                2,
                "https://example.org/b",
                "a/two.csv",
                digest=_D2,
                parent=1,
                expected=_D2,
                attempts=(got(headers=(("content-length", "5"), ("etag", '"x"'))),),
            ),
            failed_line(3),
            failed_line(4, "abandoned", attempts=(got("not-attempted", failure="scheme"),)),
        ),
    )


def imported_log() -> AcquisitionLog:
    return AcquisitionLog(
        imported_header(),
        (
            fetched_line(
                1,
                "https://example.org/a",
                "a/one.csv",
                attempts=(),
                recorded=Recorded(journal=0, line=7, digest=_D1),
            ),
            fetched_line(
                2,
                "https://example.org/b",
                "b.csv",
                digest=_D2,
                attempts=(got(started_at=None, completed_at=None),),
                recorded=Recorded(journal=0, line=8, digest=None),
            ),
        ),
    )


def lines_of(log: AcquisitionLog) -> list[bytes]:
    return render_acquisition_log(log).split(b"\n")[:-1]


def joined(lines: list[bytes]) -> bytes:
    return b"".join(line + b"\n" for line in lines)


def test_the_failure_set_is_the_transport_categories_the_refusals_and_expected_mismatch():
    assert LOG_FAILURES == FAILURE_CATEGORIES + REFUSAL_CATEGORIES + ("expected-mismatch",)


def test_a_fetched_log_round_trips():
    log = fetched_log()
    data = render_acquisition_log(log)
    assert parse_acquisition_log(data) == log
    assert render_acquisition_log(parse_acquisition_log(data)) == data
    assert v1.decode(lines_of(log)[0])["format"] == LOG_FORMAT  # pyright: ignore[reportIndexIssue]


def test_an_imported_log_round_trips_with_absent_fields_absent():
    log = imported_log()
    data = render_acquisition_log(log)
    assert parse_acquisition_log(data) == log
    assert b"null" not in data
    second = v1.decode(lines_of(log)[2])
    assert "started_at" not in second["attempts"][0]  # pyright: ignore[reportIndexIssue]
    assert "digest" not in second["recorded"]  # pyright: ignore[reportIndexIssue]


def edit(log: AcquisitionLog, index: int, change: Any) -> bytes:
    """The log's bytes with line `index` (0 is the header) re-encoded after `change(value)`."""
    lines = lines_of(log)
    value = v1.decode(lines[index])
    change(value)
    lines[index] = v1.encode(value)
    return joined(lines)


def _drop(*path: str) -> Any:
    def apply(value: Any) -> None:
        for step in path[:-1]:
            value = value[step]
        del value[path[-1]]

    return apply


def _set(*path: str, to: Any) -> Any:
    def apply(value: Any) -> None:
        for step in path[:-1]:
            value = value[step]
        value[path[-1]] = to

    return apply


def refusal_cases() -> list[tuple[str, bytes, str]]:
    f, i = fetched_log(), imported_log()
    good = lines_of(f)
    return [
        ("null", good[0][:-1] + b',"x":null}\n' + b"".join(x + b"\n" for x in good[1:]), "line 1"),
        ("non-canonical", good[0].replace(b'"origin"', b' "origin"', 1) + b"\n" + joined(good[1:]), "line 1"),
        ("no final LF", render_acquisition_log(f)[:-1], "ends with a line feed"),
        ("blank line", joined([*good, b""]), "line 6"),
        ("seq gap", edit(f, 2, _set("seq", to=3)), "line 3"),
        ("forward parent", edit(f, 1, _set("parent", to=2)), "line 2"),
        ("parent not fetched", edit(f, 4, _set("parent", to=3)), "line 5"),
        (
            "failure outside the set",
            edit(
                f,
                3,
                _set("attempts", to=[{"outcome": "failed", "failure": "boom", "started_at": _T0, "completed_at": _T1}]),
            ),
            "line 4",
        ),
        (
            "refusal failure on a failed attempt",
            edit(
                f,
                3,
                _set(
                    "attempts", to=[{"outcome": "failed", "failure": "scheme", "started_at": _T0, "completed_at": _T1}]
                ),
            ),
            "line 4",
        ),
        (
            "failure on a fetched attempt",
            edit(
                f,
                1,
                _set(
                    "attempts",
                    to=[{"outcome": "fetched", "failure": "timeout", "started_at": _T0, "completed_at": _T1}],
                ),
            ),
            "line 2",
        ),
        (
            "no failure on a failed attempt",
            edit(f, 3, _set("attempts", to=[{"outcome": "failed", "started_at": _T0, "completed_at": _T1}])),
            "line 4",
        ),
        (
            "unknown attempt outcome",
            edit(f, 1, _set("attempts", to=[{"outcome": "ok", "started_at": _T0, "completed_at": _T1}])),
            "line 2",
        ),
        (
            "header outside the allowlist",
            edit(
                f,
                1,
                _set(
                    "attempts",
                    to=[{"outcome": "fetched", "headers": {"set-cookie": "x"}, "started_at": _T0, "completed_at": _T1}],
                ),
            ),
            "line 2",
        ),
        ("fetched without a member", edit(f, 1, _drop("member")), "line 2"),
        ("failed with a member", edit(f, 3, _set("member", to="x.csv")), "line 4"),
        ("imported without recorded", edit(i, 1, _drop("recorded")), "line 2"),
        ("recorded on a fetched log", edit(f, 1, _set("recorded", to={"journal": 0, "line": 1})), "line 2"),
        ("recorded digest mismatch", edit(i, 1, _set("recorded", "digest", to=_D2)), "line 2"),
        ("recorded journal out of range", edit(i, 1, _set("recorded", "journal", to=1)), "line 2"),
        ("plan on an import", edit(i, 0, _set("plan", to={"seeds": []})), "line 1"),
        ("source journals on a fetch", edit(f, 0, _set("source_journals", to=[])), "line 1"),
        ("imported without source journals", edit(i, 0, _set("source_journals", to=[])), "line 1"),
        ("fetch without a plan", edit(f, 0, _drop("plan")), "line 1"),
        ("header with an extra key", edit(f, 0, _set("extra", to="x")), "line 1"),
        ("wrong format", edit(f, 0, _set("format", to="science.acquisition-log.v2")), "line 1"),
        ("request with an extra key", edit(f, 1, _set("request", "headers", to={})), "line 2"),
        ("request method not GET", edit(f, 1, _set("request", "method", to="POST")), "line 2"),
        ("unknown result", edit(f, 1, _set("result", to="gone")), "line 2"),
        ("fetched-origin line without attempts", edit(f, 1, _set("attempts", to=[])), "line 2"),
        (
            "fetched-origin attempt without a time",
            edit(f, 1, _set("attempts", to=[{"outcome": "fetched", "status": 200}])),
            "line 2",
        ),
        (
            "fetched line ending in a failure",
            edit(
                f,
                1,
                _set(
                    "attempts",
                    to=[
                        {"outcome": "fetched", "started_at": _T0, "completed_at": _T1},
                        {"outcome": "failed", "failure": "timeout", "started_at": _T0, "completed_at": _T1},
                    ],
                ),
            ),
            "line 2",
        ),
        (
            "failed line with a fetched attempt",
            edit(f, 3, _set("attempts", to=[{"outcome": "fetched", "started_at": _T0, "completed_at": _T1}])),
            "line 4",
        ),
        ("size not an int", edit(f, 1, _set("size", to="5")), "line 2"),
        ("bad expected digest", edit(f, 1, _set("expected", to="md5:abc")), "line 2"),
    ]


@pytest.mark.parametrize(
    ("data", "named"),
    [pytest.param(data, named, id=name) for name, data, named in refusal_cases()],
)
def test_log_refuses(data: bytes, named: str):
    with pytest.raises(MalformedRecord, match=named):
        parse_acquisition_log(data)


def test_a_fetched_log_renders_a_line_it_would_refuse_to_parse_never():
    bad = dataclasses.replace(fetched_log().lines[0], attempts=())
    with pytest.raises(MalformedRecord, match="line 2"):
        AcquisitionLog(fetched_header(), (bad,))


def test_log_tree_is_the_fetched_members():
    tree = log_tree(fetched_log())
    assert tree == make_tree([TreeMember("a/one.csv", _D1, 5), TreeMember("a/two.csv", _D2, 5)])


def test_log_tree_refuses_a_member_named_twice():
    log = AcquisitionLog(
        fetched_header(),
        (fetched_line(1, "https://example.org/a", "x.csv"), fetched_line(2, "https://example.org/b", "x.csv")),
    )
    with pytest.raises(MalformedRecord, match="twice"):
        log_tree(log)


def test_log_summary_counts_and_traversal_completeness():
    static = fetched_log()
    summary = log_summary(static)
    assert summary == SetSummary(
        origin="fetched",
        fetched_by="science/acquire.v1 (beliefs transport)",
        requests=4,
        fetched=2,
        failed=1,
        abandoned=1,
        traversal_complete=True,
        log="sha256:" + hashlib.sha256(render_acquisition_log(static)).hexdigest(),
        tree=tree_digest(log_tree(static)),
    )
    traversal = AcquisitionLog(fetched_header({"traversal": {"depth": 1}}), static.lines)
    assert log_summary(traversal).traversal_complete is False
    clean = AcquisitionLog(fetched_header({"traversal": {"depth": 1}}), static.lines[:2])
    assert log_summary(clean).traversal_complete is True
    assert log_summary(imported_log()).traversal_complete is True


def test_set_summary_refuses_counts_that_do_not_add_up():
    good = log_summary(fetched_log())
    with pytest.raises(MalformedRecord, match="requests"):
        dataclasses.replace(good, requests=5)
    with pytest.raises(MalformedRecord, match="origin"):
        dataclasses.replace(good, origin="found")
    with pytest.raises(MalformedRecord, match="log"):
        dataclasses.replace(good, log="sha256-tree:" + "a" * 64)
    with pytest.raises(MalformedRecord, match="tree"):
        dataclasses.replace(good, tree="sha256:" + "a" * 64)
    with pytest.raises(MalformedRecord, match="traversal_complete"):
        dataclasses.replace(good, traversal_complete=1)  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord, match="fetched"):
        dataclasses.replace(good, fetched=True)  # type: ignore[arg-type]
