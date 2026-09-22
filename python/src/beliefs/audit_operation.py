"""The audit operation (act-report-remainder design §3).

One operation intent, then `audit_corpus` over the writer's own view, then
one act-report carrying one subject-evaluation entry per finding — every
step under the caller's hold and the root lock, so the state the evaluator
judged is the state at the intent's chain position (decision 4). The
evaluator stays read-only (`audit.py` is not imported by anything that
writes); this wrapper reports.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import final

from beliefs import boundary as boundary_values
from beliefs import stored
from beliefs.audit import audit_corpus
from beliefs.corpus import CorpusWriter, Finding
from beliefs.errors import AuditRefused, LoneSurrogate, MalformedRecord
from beliefs.evidence import DerivationEvidence
from beliefs.identity import v1
from beliefs.report import ActReport, EvaluationFinding, OperationIntent, SubjectEvaluationEntry
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed

__all__ = ["AuditOutcome", "audit"]


@sealed
@final
@dataclass(frozen=True)
class AuditOutcome:
    report: ActReport
    report_ref: str
    findings: tuple[Finding, ...]
    entries: tuple[SubjectEvaluationEntry, ...]


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finding_payload(finding: Finding) -> str:
    """`severity`, `code` and `detail` — never `message`, which `Finding`
    makes normative for nothing (decision 3): a reworded message moves no
    report identity. A detail the canonical encoder refuses propagates."""
    return v1.encode({"severity": finding.severity, "code": finding.code, "detail": finding.detail}).decode("utf-8")


def _entry(finding: Finding) -> SubjectEvaluationEntry:
    return SubjectEvaluationEntry(finding.ref, EvaluationFinding(_finding_payload(finding)))


def audit(
    writer: CorpusWriter,
    *,
    observer: str,
    instrument: str,
    evidence: DerivationEvidence,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> AuditOutcome:
    """`hold` is the caller's outer lock — the session route passes the one
    `ScopedWriter._act` takes first — entered before the root lock and held,
    with it, across the evaluator's read (decision 4)."""
    # 1. Checks, before any effect (§3 step 1).
    if type(evidence) is not DerivationEvidence:
        raise MalformedRecord("audit takes a DerivationEvidence")
    writer.authority.require("corpus-write", ("act-report",))
    for name, value in (("observer", observer), ("instrument", instrument)):
        if type(value) is not str or not value:
            raise AuditRefused(f"audit {name} must be a non-empty string")
    try:
        v1.encode({"actor": writer.authority.actor, "observer": observer, "instrument": instrument})
    except LoneSurrogate as caught:
        raise AuditRefused(f"audit report fields are not canonically encodable: {caught}") from caught
    if port is None and writer._operation_port is None:
        raise AuditRefused("this corpus has no operation port; audit is a boundary operation")
    writer._require_bound_port(port)
    # 2. The hold: the caller's, then the root's (decision 4).
    outer = nullcontext() if hold is None else hold()
    with outer, writer._operation:
        # 3. Open.
        intent = OperationIntent("audit", secrets.token_hex(16), writer.authority.actor)
        opened_at = _now()
        intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)
        # 4. Act: the read after the intent, so the chain position names the state judged.
        writer._reconstruct()
        findings = audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile)
        # 5. Close.
        entries = tuple(_entry(finding) for finding in findings)
        closed_at = _now()
        report = boundary_values._mint_audit_report(
            intent, observer=observer, instrument=instrument, opened_at=opened_at, closed_at=closed_at, entries=entries,
        )
        report_ref = stored.act_report_node(report).id
        writer._publish_operation_report(report, intent_digest, port=port)
    return AuditOutcome(report, report_ref, findings, entries)
