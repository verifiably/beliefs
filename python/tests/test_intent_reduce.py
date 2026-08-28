"""The one intent-qualification precedence reducer (spec §2.1, §3.3)."""

from dataclasses import dataclass

import pytest
from closure_fixtures import make_closure
from nodes.core.frontmatter import node_to_markdown

from science import runrecord, stored
from science.holdings.records import Found, StoreLocator, holdings_observation
from science.identity import v1
from science.intents.reduce import IntentQualification, qualify_chain
from science.recipe import RunClosure
from science.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView


def _publication(closure: RunClosure) -> tuple[str, bytes]:
    _, path, (op,) = runrecord.publication_plan(closure)
    return path, op.content


_RUN = _publication(make_closure())
_WRONG_SPEC_RUN = _publication(make_closure(spec="x" * 64))
_PRODUCTION_RUN = _publication(make_closure(shape="dataset-production"))
_OBSERVATION_VALUE = holdings_observation(
    location=StoreLocator("a" * 32, "payload/data.csv"),
    outcome=Found("sha256:" + "ab" * 32),
    observer="observer-1",
    instrument="instrument-1",
    event_token="tok",
    observed_at="2026-08-24T12:00:00Z",
)
_OBSERVATION = (
    f"holdings-observation/{_OBSERVATION_VALUE.identity()}.md",
    node_to_markdown(stored.holdings_observation_node(_OBSERVATION_VALUE)).encode(
        "utf-8"
    ),
)


@pytest.fixture(scope="module")
def run_path() -> str:
    return _RUN[0]


@pytest.fixture(scope="module")
def run_bytes() -> bytes:
    return _RUN[1]


@pytest.fixture(scope="module")
def wrong_spec_run_path() -> str:
    return _WRONG_SPEC_RUN[0]


@pytest.fixture(scope="module")
def wrong_spec_run_bytes() -> bytes:
    return _WRONG_SPEC_RUN[1]


@pytest.fixture(scope="module")
def production_run_path() -> str:
    return _PRODUCTION_RUN[0]


@pytest.fixture(scope="module")
def production_run_bytes() -> bytes:
    return _PRODUCTION_RUN[1]


@pytest.fixture(scope="module")
def observation_path() -> str:
    return _OBSERVATION[0]


@pytest.fixture(scope="module")
def observation_bytes() -> bytes:
    return _OBSERVATION[1]


@dataclass(frozen=True)
class FakeFile:
    tag: str


ABSENT_ROW = object()


def _facts(state: object) -> tuple[tuple[str, str], ...]:
    return (
        (("kind", "file"),)
        if type(state) is FakeFile
        else (("kind", "absent"),)
    )


def _assessment_payload(spec: str = "s" * 64, token: str = "tok") -> bytes:
    return v1.encode({"spec_identity": spec, "event_token": token, "actor": "a"})


def _production_payload(token: str = "tok") -> bytes:
    return v1.encode({"kind": "run-attempt", "event_token": token, "actor": "a"})


def _intent(digest: str, payload: bytes) -> IntentEntryView:
    return IntentEntryView(digest=digest, payload=payload)


def _registration(
    digest: str,
    fulfills: str,
    *files: str,
    absent: tuple[str, ...] = (),
) -> RegisteredEntryView:
    final = tuple((path, FakeFile(path)) for path in files) + tuple(
        (path, ABSENT_ROW) for path in absent
    )
    return RegisteredEntryView(
        digest=digest,
        txid="tx-" + digest,
        initial=(),
        final=final,
        fulfills=fulfills,
    )


def _settled(registration: str, committed: bool = True) -> SettledEntryView:
    return SettledEntryView(
        digest="s-" + registration,
        txid="tx-" + registration,
        registration=registration,
        committed=committed,
    )


def _qualify(entries, records):
    return qualify_chain(tuple(entries), records, state_facts=_facts)


def test_no_pointers_reads_attempt_without_recorded_outcome() -> None:
    rows, findings = _qualify([_intent("i1", _assessment_payload())], {})
    assert rows == (
        IntentQualification(
            "i1",
            "assessment-run",
            "attempt-without-recorded-outcome",
            None,
        ),
    )
    assert [finding.code for finding in findings] == [
        "intent-attempt-without-recorded-outcome"
    ]
    assert findings[0].ref == "i1"


def test_matched_by_run_publication_sets_fulfilled_by(run_path, run_bytes) -> None:
    entries = [
        _intent("i1", _assessment_payload()),
        _registration("r1", "i1", run_path),
        _settled("r1"),
    ]
    rows, findings = _qualify(entries, {run_path: run_bytes})
    assert rows == (IntentQualification("i1", "assessment-run", "matched", "r1"),)
    assert findings == ()


def test_every_resolved_non_qualifying_pointer_is_named_with_its_reason(
    run_path,
    run_bytes,
    observation_path,
    observation_bytes,
    wrong_spec_run_path,
    wrong_spec_run_bytes,
) -> None:
    entries = [
        _intent("i1", _assessment_payload(token="other")),
        _registration("r1", "i1", observation_path),
        _settled("r1"),
        _registration("r2", "i1", wrong_spec_run_path),
        _settled("r2"),
        _registration("r3", "i1", run_path),
        _settled("r3"),
        _registration("r4", "i1"),
        _settled("r4"),
    ]
    records = {
        observation_path: observation_bytes,
        wrong_spec_run_path: wrong_spec_run_bytes,
        run_path: run_bytes,
    }
    rows, findings = _qualify(entries, records)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert [(finding.code, finding.ref) for finding in findings] == [
        ("intent-attempt-without-recorded-outcome", "i1"),
        ("intent-fulfillment-non-qualifying", "r1"),
        ("intent-fulfillment-non-qualifying", "r2"),
        ("intent-fulfillment-non-qualifying", "r3"),
        ("intent-fulfillment-non-qualifying", "r4"),
    ]
    assert "reason=wrong-purpose" in findings[1].detail
    assert "reason=wrong-spec" in findings[2].detail
    assert "reason=wrong-token" in findings[3].detail
    assert "reason=no-record" in findings[4].detail
    assert all("intent=i1" in finding.detail for finding in findings[1:])


def test_unresolvable_wins_over_non_qualifying_and_emits_nothing(run_path) -> None:
    entries = [
        _intent("i1", _assessment_payload()),
        _registration("r1", "i1", run_path),
        _settled("r1"),
        _registration("r2", "i1"),
        _settled("r2"),
    ]
    rows, findings = _qualify(entries, {})
    assert rows == (
        IntentQualification("i1", "assessment-run", "unresolvable", None),
    )
    assert findings == ()


def test_undecodable_bytes_are_unresolvable(run_path) -> None:
    entries = [
        _intent("i1", _assessment_payload()),
        _registration("r1", "i1", run_path),
        _settled("r1"),
    ]
    rows, findings = _qualify(entries, {run_path: b"\xffgarbage"})
    assert rows[0].status == "unresolvable"
    assert findings == ()


def test_unsettled_pointer_is_unresolvable_regardless_of_disk(
    run_path,
    run_bytes,
) -> None:
    entries = [
        _intent("i1", _assessment_payload()),
        _registration("r1", "i1", run_path),
    ]
    rows, _ = _qualify(entries, {run_path: run_bytes})
    assert rows[0].status == "unresolvable"


def test_rolled_back_only_pointers_read_attempt_without_recorded_outcome(
    run_path,
    run_bytes,
) -> None:
    entries = [
        _intent("i1", _assessment_payload()),
        _registration("r1", "i1", run_path),
        _settled("r1", committed=False),
    ]
    rows, findings = _qualify(entries, {run_path: run_bytes})
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert [finding.code for finding in findings] == [
        "intent-attempt-without-recorded-outcome",
        "intent-fulfillment-non-qualifying",
    ]


def test_an_absent_final_row_never_reads_present_bytes(run_path, run_bytes) -> None:
    entries = [
        _intent("i1", _assessment_payload()),
        _registration("r1", "i1", absent=(run_path,)),
        _settled("r1"),
    ]
    rows, findings = _qualify(entries, {run_path: run_bytes})
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=no-record" in findings[1].detail


def test_unrecognized_rows_carry_the_gate_finding_and_none_reduce() -> None:
    entries = [
        _intent("i1", v1.encode({"domain": "science.other.v1"})),
        _intent("i2", b"{}"),
        _intent(
            "i3",
            v1.encode({"kind": "import", "event_token": "", "actor": "a"}),
        ),
    ]
    rows, findings = _qualify(entries, {})
    assert [row.status for row in rows] == ["unrecognized"] * 3
    assert [row.shape for row in rows] == [None] * 3
    assert [(finding.code, finding.severity) for finding in findings] == [
        ("intent-domain-unrecognized", "warning"),
        ("intent-domain-unrecognized", "warning"),
        ("intent-payload-malformed", "error"),
    ]


def test_wrong_shape_both_directions(
    run_path,
    run_bytes,
    production_run_path,
    production_run_bytes,
) -> None:
    entries = [
        _intent("i1", _production_payload()),
        _registration("r1", "i1", run_path),
        _settled("r1"),
    ]
    _, findings = _qualify(entries, {run_path: run_bytes})
    assert "reason=wrong-shape" in findings[1].detail
    entries = [
        _intent("i2", _assessment_payload()),
        _registration("r2", "i2", production_run_path),
        _settled("r2"),
    ]
    _, findings = _qualify(
        entries,
        {production_run_path: production_run_bytes},
    )
    assert "reason=wrong-shape" in findings[1].detail
