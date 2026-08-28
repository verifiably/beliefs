"""The closed intent union: total decoding and matching (spec §2.2, §3.2)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, final

from science.errors import CanonicalTextRefused, MalformedRecord
from science.identity import v1
from science.intents import holdings as holdings_shape
from science.report import OPERATION_KINDS, AssessmentRunIntent, OperationIntent
from science.sealed import sealed

__all__ = [
    "REASON_PRIORITY",
    "DecodedIntent",
    "InertRecord",
    "ObservationEvidence",
    "ReportEvidence",
    "RunEvidence",
    "Unrecognized",
    "decode_intent",
    "mismatch",
]

REASON_PRIORITY = (
    "wrong-spec",
    "wrong-token",
    "wrong-kind",
    "wrong-shape",
    "wrong-location",
    "wrong-purpose",
    "no-record",
)


@sealed
@final
@dataclass(frozen=True)
class DecodedIntent:
    digest: str
    shape: Literal["assessment-run", "operation", "holdings"]
    value: AssessmentRunIntent | OperationIntent | Mapping[str, str]


@sealed
@final
@dataclass(frozen=True)
class Unrecognized:
    digest: str
    code: str
    severity: str
    detail: str


@sealed
@final
@dataclass(frozen=True)
class RunEvidence:
    shape: str
    spec_identity: str | None
    event_token: str


@sealed
@final
@dataclass(frozen=True)
class ReportEvidence:
    operation: str
    event_token: str


@sealed
@final
@dataclass(frozen=True)
class ObservationEvidence:
    location: str
    event_token: str


@sealed
@final
@dataclass(frozen=True)
class InertRecord:
    """A readable published record that qualifies nothing."""


def _malformed(digest: str, shape: str) -> Unrecognized:
    return Unrecognized(digest, "intent-payload-malformed", "error", shape)


def decode_intent(digest: str, payload: bytes) -> DecodedIntent | Unrecognized:
    """Decode every payload through exactly one discriminator branch."""
    try:
        sniffed: object = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        sniffed = None
    if isinstance(sniffed, dict) and "domain" in sniffed:
        if sniffed["domain"] == holdings_shape.HOLDINGS_INTENT_DOMAIN:
            row = {"digest": digest, "entry": {"payload": payload.hex()}}
            try:
                decoded = holdings_shape.decode_holdings_intent(row)
            except ValueError:
                return _malformed(digest, "holdings")
            assert decoded is not None
            return DecodedIntent(digest, "holdings", decoded)
        return Unrecognized(
            digest,
            "intent-domain-unrecognized",
            "warning",
            str(sniffed["domain"]),
        )
    try:
        value = v1.decode(payload)
    except CanonicalTextRefused:
        return Unrecognized(
            digest,
            "intent-domain-unrecognized",
            "warning",
            "undecodable",
        )
    if not isinstance(value, dict):
        return Unrecognized(
            digest,
            "intent-domain-unrecognized",
            "warning",
            "domainless-unrecognized",
        )
    if set(value) == {"kind", "event_token", "actor"} and value.get("kind") in OPERATION_KINDS:
        try:
            _require_fields(value, ("kind", "event_token", "actor"))
            return DecodedIntent(
                digest,
                "operation",
                OperationIntent(value["kind"], value["event_token"], value["actor"]),
            )
        except MalformedRecord:
            return _malformed(digest, "operation")
    if set(value) == {"spec_identity", "event_token", "actor"}:
        try:
            _require_fields(value, ("spec_identity", "event_token", "actor"))
            return DecodedIntent(
                digest,
                "assessment-run",
                AssessmentRunIntent(
                    value["spec_identity"],
                    value["event_token"],
                    value["actor"],
                ),
            )
        except MalformedRecord:
            return _malformed(digest, "assessment-run")
    return Unrecognized(
        digest,
        "intent-domain-unrecognized",
        "warning",
        "domainless-unrecognized",
    )


def _require_fields(value: dict[str, object], names: tuple[str, ...]) -> None:
    for name in names:
        member = value[name]
        if type(member) is not str or not member:
            raise MalformedRecord(f"intent field {name} must be a non-empty string")


def mismatch(intent: DecodedIntent, evidence: object) -> str | None:
    """Return ``None`` when evidence qualifies the intent, else its reason."""
    if type(evidence) is InertRecord:
        return "wrong-purpose"
    value = intent.value
    if isinstance(value, AssessmentRunIntent):
        if type(evidence) is RunEvidence:
            if evidence.shape != "assessment":
                return "wrong-shape"
            if evidence.spec_identity != value.spec_identity:
                return "wrong-spec"
            return None if evidence.event_token == value.event_token else "wrong-token"
        if type(evidence) is ReportEvidence:
            if evidence.operation != "run-attempt":
                return "wrong-kind"
            return None if evidence.event_token == value.event_token else "wrong-token"
        return "wrong-purpose"
    if isinstance(value, OperationIntent):
        if value.kind == "run-attempt":
            if type(evidence) is RunEvidence:
                if evidence.shape != "dataset-production":
                    return "wrong-shape"
                return None if evidence.event_token == value.event_token else "wrong-token"
            if type(evidence) is ReportEvidence:
                if evidence.operation != "run-attempt":
                    return "wrong-kind"
                return None if evidence.event_token == value.event_token else "wrong-token"
            return "wrong-purpose"
        if type(evidence) is ReportEvidence:
            if evidence.operation != value.kind:
                return "wrong-kind"
            return None if evidence.event_token == value.event_token else "wrong-token"
        return "wrong-purpose"
    if type(evidence) is ObservationEvidence:
        if evidence.location != value["location"]:
            return "wrong-location"
        return None if evidence.event_token == value["event_token"] else "wrong-token"
    return "wrong-purpose"
