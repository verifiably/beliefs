"""The audit operation (act-report-remainder design §3) — portable, over the recording port."""

from __future__ import annotations

import json
import threading
from dataclasses import replace

import pytest
from authority import FULL, narrowed
from fixtures_cut4 import raw_write
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE
from test_operation_writes import RecordingPort, intents_of, writer_over
from test_read_side import observed_dataset

from beliefs import audit_operation, stored
from beliefs import boundary as boundary_values
from beliefs.audit import NO_EVIDENCE
from beliefs.audit_operation import AuditOutcome, _finding_payload, audit
from beliefs.corpus import CorpusWriter, Finding, _operation_lock_for
from beliefs.errors import AuditRefused, BuildContended, MalformedRecord, PermitExceeded, PortMismatch
from beliefs.report import (
    CLOSED,
    UNFINISHED,
    EvaluationFinding,
    OperationIntent,
    Registration,
    SubjectEvaluationEntry,
    completion,
)


def stale_dataset(writer) -> str:
    """One `semantic-hash-stale` finding: a dataset raw-written with a body its stamp does not cover."""
    node = observed_dataset()
    node.facets[stored.DATASET_FACET]["resources"] = []
    raw_write(writer.root, node)
    writer._reconstruct()
    return node.id


class Ordered(RecordingPort):
    """The recording port with each call's *completion* logged to a shared list."""

    def __init__(self, authority, root, events: list[str]) -> None:
        super().__init__(authority, root)
        self.events = events

    def append_intent(self, payload):
        digest = super().append_intent(payload)
        self.events.append("appended")
        return digest

    def execute_fulfilling(self, plan, fulfills):
        digest = super().execute_fulfilling(plan, fulfills)
        self.events.append("closed")
        return digest


def run(writer, **kwargs) -> AuditOutcome:
    return audit(writer, observer="observer", instrument="instrument", evidence=NO_EVIDENCE, **kwargs)


def fulfilling(port: RecordingPort) -> list[tuple[tuple, str]]:
    return [payload for kind, payload in port.calls if kind == "execute_fulfilling"]


def test_a_clean_corpus_closes_through_one_report_with_no_entries(tmp_path):
    writer, port = writer_over(tmp_path)
    outcome = run(writer)
    assert outcome.findings == () and outcome.entries == ()
    assert outcome.report.operation == "audit" and outcome.report.entries == ()
    assert writer.read_view.holds(outcome.report_ref)
    (intent,) = intents_of(port)
    assert intent == OperationIntent("audit", outcome.report.event_token, FULL.actor)
    assert [kind for kind, _ in port.calls] == ["append_intent", "execute_fulfilling"]
    ((plan, fulfills),) = fulfilling(port)
    assert fulfills == "1" * 60 + "0001"  # the digest the append returned
    assert len(plan) == 1 and plan[0].path == f"act-report/{outcome.report.identity()}.md"
    assert completion(intent, (Registration(intent.event_token, outcome.report_ref),), {outcome.report_ref: outcome.report}) == CLOSED
    assert stored.act_report_facet(writer.read_view.get(outcome.report_ref))["event_token"] == intent.event_token


def test_findings_become_entries_in_the_evaluators_order_with_no_message(tmp_path):
    writer, _ = writer_over(tmp_path)
    ref = stale_dataset(writer)
    outcome = run(writer)
    assert [f.code for f in outcome.findings] == ["semantic-hash-stale"]
    (entry,) = outcome.entries
    assert entry == SubjectEvaluationEntry(ref, EvaluationFinding(_finding_payload(outcome.findings[0])))
    payload = json.loads(entry.outcome.payload)
    assert payload == {"severity": "error", "code": "semantic-hash-stale", "detail": "mismatch"}
    assert "message" not in payload
    assert outcome.report.entries == outcome.entries


def test_the_payload_is_invariant_under_a_reworded_message_and_moves_with_detail():
    finding = Finding("error", "c", "ref", "d", "one wording")
    assert _finding_payload(finding) == _finding_payload(replace(finding, message="another wording"))
    assert _finding_payload(finding) != _finding_payload(replace(finding, detail="e"))


def test_the_evaluator_runs_after_the_append_completes_and_before_the_close(tmp_path, monkeypatch):
    writer, _ = writer_over(tmp_path)
    events: list[str] = []
    real = audit_operation.audit_corpus

    def evaluator(view, *, evidence, profile):
        events.append("evaluated")
        return real(view, evidence=evidence, profile=profile)

    monkeypatch.setattr(audit_operation, "audit_corpus", evaluator)
    run(writer, port=Ordered(FULL, tmp_path, events))
    assert events == ["appended", "evaluated", "closed"]


@pytest.mark.parametrize(
    ("spoil", "refusal"),
    [
        ("no-port", AuditRefused),
        ("foreign-root-port", PortMismatch),
        ("empty-instrument", AuditRefused),
        ("unencodable-observer", AuditRefused),
        ("no-act-report-permit", PermitExceeded),
        ("evidence-type", MalformedRecord),
    ],
)
def test_every_pre_intent_refusal_appends_nothing_and_runs_the_evaluator_zero_times(tmp_path, spoil, refusal, monkeypatch):
    calls: list[object] = []
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda *a, **k: calls.append(a) or ())
    writer, port = writer_over(tmp_path)
    ports = [port]
    kwargs = {"observer": "observer", "instrument": "instrument", "evidence": NO_EVIDENCE}
    if spoil == "no-port":
        writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE)
    elif spoil == "foreign-root-port":
        (tmp_path / "other").mkdir()
        kwargs["port"] = RecordingPort(FULL, tmp_path / "other")
        ports.append(kwargs["port"])
    elif spoil == "empty-instrument":
        kwargs["instrument"] = ""
    elif spoil == "unencodable-observer":
        kwargs["observer"] = "\udcff"
    elif spoil == "no-act-report-permit":
        writer, port = writer_over(tmp_path, narrowed(kinds=("proposition",), families=("corpus-write",)))
        ports = [port]
    elif spoil == "evidence-type":
        kwargs["evidence"] = {}
    with pytest.raises(refusal):
        audit(writer, **kwargs)
    assert all(p.calls == [] for p in ports)
    assert calls == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_an_evaluator_failure_after_the_intent_propagates_and_reads_unfinished(tmp_path, monkeypatch):
    writer, port = writer_over(tmp_path)

    def failing(view, *, evidence, profile):
        raise RuntimeError("carrier failure")

    monkeypatch.setattr(audit_operation, "audit_corpus", failing)
    with pytest.raises(RuntimeError, match="carrier failure"):
        run(writer)
    assert [kind for kind, _ in port.calls] == ["append_intent"]
    (intent,) = intents_of(port)
    assert completion(intent, (), {}) == UNFINISHED
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def _held(lock) -> bool:
    seen: list[bool] = []

    def probe() -> None:
        try:
            with lock.capture():
                seen.append(False)
        except BuildContended:
            seen.append(True)

    thread = threading.Thread(target=probe)
    thread.start()
    thread.join(5)
    return seen == [True]


def test_the_hold_enters_before_the_root_lock_and_spans_the_evaluator(tmp_path, monkeypatch):
    writer, _ = writer_over(tmp_path)
    events: list[str] = []
    lock = _operation_lock_for(tmp_path)

    class Hold:
        def __enter__(self):
            events.append("hold-enter:" + ("held" if _held(lock) else "free"))
            return self

        def __exit__(self, *_exc):
            events.append("hold-exit:" + ("held" if _held(lock) else "free"))

    real = audit_operation.audit_corpus

    def evaluator(view, *, evidence, profile):
        events.append("evaluate:" + ("held" if _held(lock) else "free"))
        return real(view, evidence=evidence, profile=profile)

    monkeypatch.setattr(audit_operation, "audit_corpus", evaluator)
    run(writer, hold=Hold)
    assert events == ["hold-enter:free", "evaluate:held", "hold-exit:free"]


def test_the_mint_helper_refuses_the_wrong_intent_kind_and_the_wrong_entry_kind():
    from beliefs.report import LocatorEntry, RetrievalFailed

    now = "2026-09-22T00:00:00Z"
    entry = SubjectEvaluationEntry("proposition:" + "a" * 64, EvaluationFinding("{}"))
    with pytest.raises(MalformedRecord, match="audit operation intent"):
        boundary_values._mint_audit_report(OperationIntent("re-check", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now, entries=(entry,))
    with pytest.raises(MalformedRecord, match="subject-evaluation entries only"):
        boundary_values._mint_audit_report(
            OperationIntent("audit", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now,
            entries=(LocatorEntry("url:https://example.org/a", RetrievalFailed("x")),),
        )
    report = boundary_values._mint_audit_report(OperationIntent("audit", "t", "alice"), observer="o", instrument="i", opened_at=now, closed_at=now, entries=(entry,))
    assert report.operation == "audit" and report.entries == (entry,)
