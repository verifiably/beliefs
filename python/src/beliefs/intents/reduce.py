"""The one log qualification reduction (spec §2.1, §3.3)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, final

from beliefs.corpus import Finding
from beliefs.errors import RecordUndecodable
from beliefs.intents import evidence as evidence_module
from beliefs.intents import shapes
from beliefs.sealed import sealed
from beliefs.world.logmodel import (
    EntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
)

__all__ = [
    "IntentQualification",
    "QualificationPass",
    "RegistrationReduction",
    "qualify_chain",
    "record_paths_of",
    "reduce_chain",
    "reduce_registration",
]


@sealed
@final
@dataclass(frozen=True, slots=True)
class IntentQualification:
    digest: str
    shape: Literal["assessment-run", "operation", "holdings"] | None
    status: Literal[
        "matched",
        "unresolvable",
        "attempt-without-recorded-outcome",
        "unrecognized",
    ]
    fulfilled_by: str | None


StateFacts = Callable[[object], tuple[tuple[str, str], ...]]


def _is_file(facts: tuple[tuple[str, str], ...]) -> bool:
    return any(pair[0] == "kind" and pair[1] == "file" for pair in facts)


@sealed
@final
@dataclass(frozen=True, slots=True)
class RegistrationReduction:
    """One registration's whole reduction (successor-admission design §4.4):
    the first qualifying `(path, evidence)` in `final` order, whether any
    record path had no payload or failed to decode, and every decoded
    non-qualifying record's reason in order."""

    match: tuple[str, evidence_module.RecordEvidence] | None
    unresolved: bool
    reasons: tuple[str, ...]


@sealed
@final
@dataclass(frozen=True, slots=True)
class QualificationPass:
    """One chain pass, including the exact matched registration reductions.

    `qualify_chain` projects this value to its established public pair; the
    succession boundary consumes `matched_reductions` without scanning or
    decoding a matched registration again.
    """

    rows: tuple[IntentQualification, ...]
    findings: tuple[Finding, ...]
    matched_reductions: tuple[tuple[str, RegistrationReduction], ...]


def record_paths_of(registration: RegisteredEntryView, state_facts: StateFacts) -> list[str]:
    return [
        path
        for path, state in registration.final
        if evidence_module.record_layout_path(path) and _is_file(state_facts(state))
    ]


def reduce_registration(
    intent: shapes.DecodedIntent,
    record_paths: list[str],
    records: Mapping[str, bytes],
) -> RegistrationReduction:
    reasons: list[str] = []
    pointer_unresolved = False
    for path in record_paths:
        payload = records.get(path)
        if payload is None:
            pointer_unresolved = True
            continue
        try:
            record_evidence = evidence_module.decode_record(path, payload)
        except RecordUndecodable:
            pointer_unresolved = True
            continue
        reason = shapes.mismatch(intent, record_evidence)
        if reason is None:
            return RegistrationReduction((path, record_evidence), pointer_unresolved, tuple(reasons))
        reasons.append(reason)
    return RegistrationReduction(None, pointer_unresolved, tuple(reasons))


def qualify_chain(
    entries: tuple[EntryView, ...],
    records: Mapping[str, bytes],
    *,
    state_facts: StateFacts,
) -> tuple[tuple[IntentQualification, ...], tuple[Finding, ...]]:
    reduced = reduce_chain(entries, records, state_facts=state_facts)
    return reduced.rows, reduced.findings


def reduce_chain(
    entries: tuple[EntryView, ...],
    records: Mapping[str, bytes],
    *,
    state_facts: StateFacts,
) -> QualificationPass:
    settlement = {
        entry.registration: entry.committed
        for entry in entries
        if type(entry) is SettledEntryView
    }
    pointers: dict[str, list[RegisteredEntryView]] = {}
    for entry in entries:
        if type(entry) is RegisteredEntryView and entry.fulfills is not None:
            pointers.setdefault(entry.fulfills, []).append(entry)

    rows: list[IntentQualification] = []
    findings: list[Finding] = []
    matched_reductions: list[tuple[str, RegistrationReduction]] = []
    for entry in entries:
        if type(entry) is not IntentEntryView:
            continue
        gate = shapes.decode_intent(entry.digest, entry.payload)
        if type(gate) is shapes.Unrecognized:
            rows.append(IntentQualification(entry.digest, None, "unrecognized", None))
            findings.append(
                Finding(
                    severity=gate.severity,
                    code=gate.code,
                    ref=entry.digest,
                    detail=gate.detail,
                    message=(
                        "the intent payload fits no shape of the closed union"
                        if gate.code == "intent-domain-unrecognized"
                        else "a discriminator-matched payload fails its shape's schema"
                    ),
                )
            )
            continue
        row, intent_findings = _qualify_one(
            gate,
            pointers.get(entry.digest, []),
            settlement,
            records,
            state_facts,
            matched_reductions,
        )
        rows.append(row)
        findings.extend(intent_findings)
    return QualificationPass(
        tuple(rows),
        tuple(findings),
        tuple(matched_reductions),
    )


def _qualify_one(
    intent: shapes.DecodedIntent,
    registrations: list[RegisteredEntryView],
    settlement: Mapping[str, bool],
    records: Mapping[str, bytes],
    state_facts: StateFacts,
    matched_reductions: list[tuple[str, RegistrationReduction]],
) -> tuple[IntentQualification, tuple[Finding, ...]]:
    unresolved = False
    non_qualifying: list[tuple[str, str]] = []
    for registration in registrations:
        committed = settlement.get(registration.digest)
        if committed is None:
            unresolved = True
            continue
        if not committed:
            non_qualifying.append((registration.digest, "no-record"))
            continue
        record_paths = record_paths_of(registration, state_facts)
        if not record_paths:
            non_qualifying.append((registration.digest, "no-record"))
            continue
        reduction = reduce_registration(intent, record_paths, records)
        if reduction.match is not None:
            matched_reductions.append((registration.digest, reduction))
            return (
                IntentQualification(
                    intent.digest,
                    intent.shape,
                    "matched",
                    registration.digest,
                ),
                (),
            )
        if reduction.unresolved:
            unresolved = True
            continue
        chosen = (
            min(reduction.reasons, key=shapes.REASON_PRIORITY.index)
            if reduction.reasons
            else "no-record"
        )
        non_qualifying.append((registration.digest, chosen))
    if unresolved:
        return (
            IntentQualification(intent.digest, intent.shape, "unresolvable", None),
            (),
        )
    row = IntentQualification(
        intent.digest,
        intent.shape,
        "attempt-without-recorded-outcome",
        None,
    )
    findings = [
        Finding(
            severity="warning",
            code="intent-attempt-without-recorded-outcome",
            ref=intent.digest,
            detail="",
            message="a durable intent whose every pointer fully resolves and none qualifies",
        )
    ]
    findings.extend(
        Finding(
            severity="warning",
            code="intent-fulfillment-non-qualifying",
            ref=registration_digest,
            detail=f"intent={intent.digest} reason={reason}",
            message="a committed fulfillment that does not qualify its intent",
        )
        for registration_digest, reason in non_qualifying
    )
    return row, tuple(findings)
