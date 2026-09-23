"""Inert operation values and boundary-minted act reports.

Reports are inert by type: belief, admission, closure, and dataset do not
import this module. Visibility is bought by pre-registration, never inferred
from history. `_mint_report` stays private because no API accepts an authored
report; this slice supplies only that ordinary-API bound (cut 3 §9 item 2).
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias, final

from beliefs.errors import CitationRefused, MalformedRecord, OutcomeRefused
from beliefs.identity import v1
from beliefs.permit import require_actor
from beliefs.recipe import RunClosure
from beliefs.sealed import sealed

if TYPE_CHECKING:
    from beliefs.intents.publish import PublishIntent

__all__ = [
    "ACT_REPORT_DOMAIN",
    "CLOSED",
    "EVIDENCE_REFUSAL_REASONS",
    "INDETERMINATE",
    "OPERATION_KINDS",
    "UNFINISHED",
    "ActReport",
    "AssessmentRunIntent",
    "BindingBound",
    "BindingEvidenceRefused",
    "BindingPredecessorNotStanding",
    "ByteLocatorUntested",
    "Consolidated",
    "DeclarationPinEntry",
    "Entry",
    "EvaluationFinding",
    "ImportedRecords",
    "LocatorEntry",
    "ManagedMutationEntry",
    "Moved",
    "OperationIntent",
    "PinnedDeclaration",
    "PublicationBindingEntry",
    "PublishedObservation",
    "RecordImportEntry",
    "RecordMutationEntry",
    "Registration",
    "RetrievalFailed",
    "RunAttemptEntry",
    "RunRefusal",
    "SubjectEvaluationEntry",
    "binding_outcome_from_facet",
    "cite",
    "completion",
]

ACT_REPORT_DOMAIN = "science.act-report.v1"
# The kinds a domainless `OperationIntent` opens; `publish` joins the closed set
# only beside them, because it opens through its domain intent alone
# (publication-records design, decision 10). The literal below is cut 19 J1e's
# pinned sabotage `before`: keep it byte-exact on one line, and derive beside it.
_DOMAINLESS_OPERATION_KINDS = ("acquisition", "audit", "consolidate", "corpus-write", "import", "move", "re-check", "run-attempt")
OPERATION_KINDS: tuple[str, ...] = tuple(sorted((*_DOMAINLESS_OPERATION_KINDS, "publish")))
UNFINISHED = "unfinished"
INDETERMINATE = "indeterminate"
CLOSED = "closed"


def _require_str(value: object, where: str) -> None:
    if type(value) is not str:
        raise MalformedRecord(f"{where} must be a string")


def _require_strings(value: object, where: str) -> None:
    if type(value) is not tuple or not all(type(member) is str for member in value):
        raise MalformedRecord(f"{where} must be a tuple of strings")


def _require_pairs(value: object, where: str) -> None:
    if type(value) is not tuple or not all(
        type(row) is tuple and len(row) == 2 and all(type(member) is str for member in row) for row in value
    ):
        raise MalformedRecord(f"{where} must be a tuple of (string, string) pairs")


@sealed
@final
@dataclass(frozen=True)
class OperationIntent:
    kind: str
    event_token: str
    actor: str

    def __post_init__(self) -> None:
        _require_str(self.kind, "operation intent kind")
        _require_str(self.event_token, "operation intent event token")
        require_actor(self.actor)
        if self.kind not in OPERATION_KINDS:
            raise MalformedRecord(f"operation kind {self.kind!r} is outside the closed set {OPERATION_KINDS}")
        if self.kind == "publish":
            raise MalformedRecord("publish opens only through its domain intent, science.publish-intent.v1")


@sealed
@final
@dataclass(frozen=True)
class AssessmentRunIntent:
    spec_identity: str
    event_token: str
    actor: str

    def __post_init__(self) -> None:
        _require_str(self.spec_identity, "assessment run intent spec identity")
        _require_str(self.event_token, "assessment run intent event token")
        require_actor(self.actor)
        if not self.spec_identity:
            raise MalformedRecord("an assessment run intent requires a frozen spec identity")


@sealed
@final
@dataclass(frozen=True)
class PublishedObservation:
    ref: str

    def __post_init__(self) -> None:
        _require_str(self.ref, "published observation ref")


@sealed
@final
@dataclass(frozen=True)
class ByteLocatorUntested:
    reason: str

    def __post_init__(self) -> None:
        _require_str(self.reason, "byte locator untested reason")


@sealed
@final
@dataclass(frozen=True)
class RetrievalFailed:
    reason: str

    def __post_init__(self) -> None:
        _require_str(self.reason, "retrieval failed reason")


@sealed
@final
@dataclass(frozen=True)
class EvaluationFinding:
    payload: str

    def __post_init__(self) -> None:
        _require_str(self.payload, "evaluation finding payload")


@sealed
@final
@dataclass(frozen=True)
class ImportedRecords:
    refs: tuple[str, ...]
    findings: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_strings(self.refs, "imported record refs")
        _require_strings(self.findings, "imported record findings")


@sealed
@final
@dataclass(frozen=True)
class PinnedDeclaration:
    ref: str

    def __post_init__(self) -> None:
        _require_str(self.ref, "pinned declaration ref")


@sealed
@final
@dataclass(frozen=True)
class RunRefusal:
    missing_member: str

    def __post_init__(self) -> None:
        _require_str(self.missing_member, "run refusal missing member")


@sealed
@final
@dataclass(frozen=True)
class Moved:
    source_corpus: str
    destination_corpus: str
    ref: str

    def __post_init__(self) -> None:
        _require_str(self.source_corpus, "moved source corpus")
        _require_str(self.destination_corpus, "moved destination corpus")
        _require_str(self.ref, "moved ref")


@sealed
@final
@dataclass(frozen=True)
class Consolidated:
    kept_corpus: str
    kept_ref: str
    other_corpus: str
    other_ref: str
    retired_uids: tuple[str, ...]
    rationale: str

    def __post_init__(self) -> None:
        for name, value in (
            ("kept corpus", self.kept_corpus),
            ("kept ref", self.kept_ref),
            ("other corpus", self.other_corpus),
            ("other ref", self.other_ref),
            ("rationale", self.rationale),
        ):
            _require_str(value, f"consolidated {name}")
        _require_strings(self.retired_uids, "consolidated retired uids")


EVIDENCE_REFUSAL_REASONS = (
    "mounts-changed",
    "anchor-unplaced",
    "chain-absent",
    "chain-malformed",
    "revision-missing",
    "revision-mismatch",
    "revision-malformed",
    "history-violated",
    "unregistered-revision",
    "report-unqualified",
    "tips-disagree",
)
_HEX32 = re.compile(r"[0-9a-f]{32}")


def _require_hex32(value: object, where: str) -> None:
    if type(value) is not str or _HEX32.fullmatch(value) is None:
        raise MalformedRecord(f"{where} must be 32 lowercase hexadecimal characters")


@sealed
@final
@dataclass(frozen=True)
class BindingBound:
    binding: str
    corpus_id: str
    marker: str

    def __post_init__(self) -> None:
        for name in ("binding", "corpus_id", "marker"):
            _require_hex32(getattr(self, name), f"bound {name}")


@sealed
@final
@dataclass(frozen=True)
class BindingPredecessorNotStanding:
    corpus_id: str
    marker: str
    remotely_revealed: bool
    tips: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "refusal corpus id")
        _require_hex32(self.marker, "refusal marker")
        if type(self.remotely_revealed) is not bool:
            raise MalformedRecord("remotely_revealed must be a bool")
        # validate the container, then every member, and only then compare them:
        # sorting or hashing unvalidated members raises TypeError, not MalformedRecord
        if type(self.tips) is not tuple:
            raise MalformedRecord("tips must be a tuple")
        for tip in self.tips:
            _require_hex32(tip, "refusal tip")
        if list(self.tips) != sorted(set(self.tips)):
            raise MalformedRecord("tips must be strictly ascending and unique")


@sealed
@final
@dataclass(frozen=True)
class BindingEvidenceRefused:
    corpus_id: str
    marker: str
    remotely_revealed: bool
    reason: str

    def __post_init__(self) -> None:
        _require_hex32(self.corpus_id, "refusal corpus id")
        _require_hex32(self.marker, "refusal marker")
        if type(self.remotely_revealed) is not bool:
            raise MalformedRecord("remotely_revealed must be a bool")
        if self.reason not in EVIDENCE_REFUSAL_REASONS:
            raise MalformedRecord(f"evidence refusal reason {self.reason!r} is outside {EVIDENCE_REFUSAL_REASONS}")


_BINDING_OUTCOMES: dict[str, type[BindingBound | BindingPredecessorNotStanding | BindingEvidenceRefused]] = {
    "bound": BindingBound,
    "predecessor-not-standing": BindingPredecessorNotStanding,
    "evidence-refused": BindingEvidenceRefused,
}


def binding_outcome_from_facet(
    outcome: object,
) -> BindingBound | BindingPredecessorNotStanding | BindingEvidenceRefused:
    """The stored form of a publication-binding outcome, decoded through the
    typed constructors — so the stored mirror and the values share one rule set
    (32 lowercase hex, the closed reason set, strictly ascending unique tips, a
    bool `remotely_revealed`). Raises `MalformedRecord` on anything else."""
    if not isinstance(outcome, dict) or type(outcome.get("type")) is not str or outcome["type"] not in _BINDING_OUTCOMES:
        raise MalformedRecord("a publication-binding outcome names one of its three types")
    kind = _BINDING_OUTCOMES[outcome["type"]]
    names = {field.name for field in dataclasses.fields(kind)}
    if set(outcome) != {"type", *names}:
        raise MalformedRecord(f"a {outcome['type']} outcome carries exactly {sorted(names)}")
    values = {name: outcome[name] for name in names}
    if "tips" in values:
        if type(values["tips"]) is not list:
            raise MalformedRecord("tips are a list in the stored form")
        values["tips"] = tuple(values["tips"])
    return kind(**values)


Outcome: TypeAlias = (
    PublishedObservation
    | ByteLocatorUntested
    | RetrievalFailed
    | EvaluationFinding
    | ImportedRecords
    | PinnedDeclaration
    | RunRefusal
    | Moved
    | Consolidated
    | BindingBound
    | BindingPredecessorNotStanding
    | BindingEvidenceRefused
)


def _require_outcome(entry: object, outcome: object) -> None:
    allowed = _ALLOWED_OUTCOMES[type(entry)]
    if type(outcome) not in allowed:
        raise OutcomeRefused(f"{type(entry).__name__} refuses {type(outcome).__name__}; allowed are {allowed}")


@sealed
@final
@dataclass(frozen=True)
class LocatorEntry:
    subject: str
    outcome: PublishedObservation | ByteLocatorUntested | RetrievalFailed
    instrument_inputs: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require_str(self.subject, "locator entry subject")
        _require_pairs(self.instrument_inputs, "locator entry instrument inputs")
        _require_outcome(self, self.outcome)


@sealed
@final
@dataclass(frozen=True)
class ManagedMutationEntry:
    subject: str
    outcome: PublishedObservation

    def __post_init__(self) -> None:
        _require_str(self.subject, "managed mutation entry subject")
        _require_outcome(self, self.outcome)


@sealed
@final
@dataclass(frozen=True)
class DeclarationPinEntry:
    subject: str
    outcome: PinnedDeclaration

    def __post_init__(self) -> None:
        _require_str(self.subject, "declaration pin entry subject")
        _require_outcome(self, self.outcome)


@sealed
@final
@dataclass(frozen=True)
class SubjectEvaluationEntry:
    subject: str
    outcome: EvaluationFinding

    def __post_init__(self) -> None:
        _require_str(self.subject, "subject evaluation entry subject")
        _require_outcome(self, self.outcome)


@sealed
@final
@dataclass(frozen=True)
class RecordImportEntry:
    subject: str
    outcome: ImportedRecords

    def __post_init__(self) -> None:
        _require_str(self.subject, "record import entry subject")
        _require_outcome(self, self.outcome)


@sealed
@final
@dataclass(frozen=True)
class RunAttemptEntry:
    subject: str
    outcome: RunRefusal

    def __post_init__(self) -> None:
        _require_str(self.subject, "run attempt entry subject")
        _require_outcome(self, self.outcome)


@sealed
@final
@dataclass(frozen=True)
class RecordMutationEntry:
    subject: str
    corpus: str
    outcome: Moved | Consolidated

    def __post_init__(self) -> None:
        _require_str(self.subject, "record mutation entry subject")
        _require_str(self.corpus, "record mutation entry corpus")
        _require_outcome(self, self.outcome)


@sealed
@final
@dataclass(frozen=True)
class PublicationBindingEntry:
    subject: str
    outcome: BindingBound | BindingPredecessorNotStanding | BindingEvidenceRefused

    def __post_init__(self) -> None:
        _require_str(self.subject, "publication binding entry subject")
        _require_outcome(self, self.outcome)


Entry: TypeAlias = (
    LocatorEntry
    | ManagedMutationEntry
    | DeclarationPinEntry
    | SubjectEvaluationEntry
    | RecordImportEntry
    | RecordMutationEntry
    | RunAttemptEntry
    | PublicationBindingEntry
)

_ALLOWED_OUTCOMES: dict[type[object], tuple[type[object], ...]] = {
    LocatorEntry: (PublishedObservation, ByteLocatorUntested, RetrievalFailed),
    ManagedMutationEntry: (PublishedObservation,),
    DeclarationPinEntry: (PinnedDeclaration,),
    SubjectEvaluationEntry: (EvaluationFinding,),
    RecordImportEntry: (ImportedRecords,),
    RecordMutationEntry: (Moved, Consolidated),
    RunAttemptEntry: (RunRefusal,),
    PublicationBindingEntry: (BindingBound, BindingPredecessorNotStanding, BindingEvidenceRefused),
}
_ENTRY_KINDS: dict[type[object], str] = {
    LocatorEntry: "pure-look",
    ManagedMutationEntry: "managed-mutation",
    DeclarationPinEntry: "declaration-pin",
    SubjectEvaluationEntry: "subject-evaluation",
    RecordImportEntry: "record-import",
    RecordMutationEntry: "record-mutation",
    RunAttemptEntry: "run-attempt",
    PublicationBindingEntry: "publication-binding",
}
_OUTCOME_TYPES: dict[type[object], str] = {
    PublishedObservation: "published-observation",
    ByteLocatorUntested: "byte-locator-untested",
    RetrievalFailed: "retrieval-failed",
    EvaluationFinding: "evaluation-finding",
    ImportedRecords: "imported-records",
    PinnedDeclaration: "pinned-declaration",
    RunRefusal: "run-refusal",
    Moved: "moved",
    Consolidated: "consolidated",
    BindingBound: "bound",
    BindingPredecessorNotStanding: "predecessor-not-standing",
    BindingEvidenceRefused: "evidence-refused",
}


def _outcome_facet(outcome: Outcome) -> dict[str, object]:
    fields = {name: list(value) if type(value) is tuple else value for name, value in vars(outcome).items()}
    return {"type": _OUTCOME_TYPES[type(outcome)], **fields}


def _entry_facet(entry: Entry) -> dict[str, object]:
    row: dict[str, object] = {
        "kind": _ENTRY_KINDS[type(entry)],
        "subject": entry.subject,
        "outcome": _outcome_facet(entry.outcome),
    }
    if type(entry) is LocatorEntry:
        row["instrument_inputs"] = [list(pair) for pair in entry.instrument_inputs]
    if type(entry) is RecordMutationEntry:
        row["corpus"] = entry.corpus
    return row


@sealed
@final
@dataclass(frozen=True, init=False)
class ActReport:
    operation: str
    event_token: str
    actor: str
    observer: str
    instrument: str
    opened_at: str
    closed_at: str
    entries: tuple[Entry, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("ActReport values are minted only by the boundary")

    def identity(self) -> str:
        return v1.digest(
            ACT_REPORT_DOMAIN,
            {
                "operation": self.operation,
                "event_token": self.event_token,
                "actor": self.actor,
                "observer": self.observer,
                "instrument": self.instrument,
                "opened_at": self.opened_at,
                "closed_at": self.closed_at,
                "entries": [_entry_facet(entry) for entry in self.entries],
            },
        )


def _mint_report(
    *,
    operation: str,
    event_token: str,
    actor: str,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    if type(operation) is not str or operation not in OPERATION_KINDS:
        raise MalformedRecord(f"report operation {operation!r} is outside the closed set {OPERATION_KINDS}")
    _require_str(event_token, "report event token")
    actor = require_actor(actor)
    for name, value in (
        ("report observer", observer),
        ("report instrument", instrument),
        ("report opened at", opened_at),
        ("report closed at", closed_at),
    ):
        _require_str(value, name)
    if type(entries) is not tuple or any(type(entry) not in _ENTRY_KINDS for entry in entries):
        raise MalformedRecord("report entries must be a tuple of entry values")
    report = object.__new__(ActReport)
    for name, value in (
        ("operation", operation),
        ("event_token", event_token),
        ("actor", actor),
        ("observer", observer),
        ("instrument", instrument),
        ("opened_at", opened_at),
        ("closed_at", closed_at),
        ("entries", entries),
    ):
        object.__setattr__(report, name, value)
    return report


@sealed
@final
@dataclass(frozen=True)
class Registration:
    intent_token: str
    pointer: str

    def __post_init__(self) -> None:
        _require_str(self.intent_token, "registration intent token")
        _require_str(self.pointer, "registration pointer")


Intent: TypeAlias = "OperationIntent | AssessmentRunIntent | PublishIntent"


def completion(intent: Intent, registrations: tuple[Registration, ...], held: Mapping[str, object]) -> str:
    from beliefs.intents.publish import PublishIntent

    if type(intent) not in (OperationIntent, AssessmentRunIntent, PublishIntent):
        raise MalformedRecord("completion requires an operation intent")
    if type(registrations) is not tuple or any(
        type(registration) is not Registration for registration in registrations
    ):
        raise MalformedRecord("completion registrations must be Registration values")
    if not isinstance(held, Mapping):
        raise MalformedRecord("completion held values must be a mapping")
    if type(intent) is OperationIntent and intent.kind == "corpus-write":
        # Writer-session design §4.1: the registration is the fulfillment;
        # nothing about its pointer bears on the reading (§13 item 7).
        return CLOSED if any(r.intent_token == intent.event_token for r in registrations) else UNFINISHED
    from beliefs.intents import shapes

    decoded = shapes.DecodedIntent(
        "held",
        "assessment-run"
        if type(intent) is AssessmentRunIntent
        else "publish"
        if type(intent) is PublishIntent
        else "operation",
        intent,
    )
    unresolved = False
    for registration in registrations:
        if registration.intent_token != intent.event_token:
            continue
        if registration.pointer not in held:
            unresolved = True
            continue
        value = held[registration.pointer]
        if type(value) is ActReport:
            evidence: object = shapes.ReportEvidence(value.operation, value.event_token)
        elif type(value) is RunClosure:
            evidence = shapes.RunEvidence(
                value.recipe.shape,
                value.recipe.spec_identity,
                value.occurrence.event_token,
            )
        else:
            evidence = shapes.InertRecord()
        if shapes.mismatch(decoded, evidence) is None:
            return CLOSED
    return INDETERMINATE if unresolved else UNFINISHED


def cite(report: ActReport, index: int) -> Entry:
    if type(report) is not ActReport or type(index) is not int or not 0 <= index < len(report.entries):
        raise CitationRefused("citation index must be a zero-based unsigned entry position")
    return report.entries[index]
