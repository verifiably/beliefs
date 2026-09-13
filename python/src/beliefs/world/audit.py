"""Audit retained epoch receipts and reduce snapshot states."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, cast

from beliefs.corpus import Finding
from beliefs.errors import EpochMalformed
from beliefs.world import anchors, derive, epoch, read, registry

__all__ = ["SNAPSHOT_STATES", "EpochAudit", "SnapshotVerdict", "audit_epochs", "snapshot_state"]

SNAPSHOT_STATES: tuple[str, ...] = ("checked", "contradicted", "unchecked")
SnapshotState = Literal["checked", "contradicted", "unchecked"]
_KINDS = cast(tuple[derive.ReceiptKind, ...], tuple(epoch.RECEIPT_KINDS.values()))


@dataclass(frozen=True)
class SnapshotVerdict:
    kind: derive.ReceiptKind
    subject_identity: str
    state: SnapshotState
    receipts: tuple[tuple[str, derive.ReceiptOutcome], ...]
    unreadable: tuple[str, ...]


@dataclass(frozen=True)
class EpochAudit:
    receipts: tuple[tuple[str, derive.ReceiptKind, derive.ReceiptOutcome], ...]
    snapshots: tuple[SnapshotVerdict, ...]
    findings: tuple[Finding, ...]


def _reduce(outcomes: list[derive.ReceiptOutcome]) -> SnapshotState:
    well_formed = [outcome for outcome in outcomes if outcome.outcome != "malformed"]
    if any(outcome.outcome == "validated" for outcome in well_formed):
        return "checked"
    if any(outcome.outcome == "refuted" for outcome in well_formed):
        return "contradicted"
    return "unchecked"


def _retained(
    world: registry.World,
) -> tuple[Mapping[str, epoch.Epoch], tuple[tuple[str, str], ...], registry.RegistryView]:
    opened: dict[str, epoch.Epoch] = {}
    unreadable: list[tuple[str, str]] = []
    with registry._locked_barrier(world) as world_root:
        view = registry._scan_registry(world_root)
        for name, refusal in epoch._locked_retained_directories(world_root):
            if refusal is not None:
                unreadable.append((name, refusal))
                continue
            try:
                opened[name] = epoch._locked_open_epoch(world_root, name)
            except (EpochMalformed, OSError) as caught:
                unreadable.append((name, str(caught)))
    return opened, tuple(unreadable), view


def _receipt_finding(name: str, outcome: derive.ReceiptOutcome) -> Finding | None:
    detail = f"{outcome.kind}: {outcome.detail}"
    if outcome.outcome == "malformed":
        return Finding(
            "error",
            "receipt-malformed",
            name,
            detail,
            f"{name}: the {outcome.kind} receipt violates its contract: {outcome.detail}",
        )
    if outcome.outcome == "refuted":
        return Finding(
            "error",
            "receipt-refuted",
            name,
            detail,
            f"{name}: the {outcome.kind} receipt is refuted by reconstruction; "
            f"a rebuild (build_epoch) publishes the correction: {outcome.detail}",
        )
    if outcome.outcome == "unresolvable":
        return Finding(
            "warning",
            "receipt-unresolvable",
            name,
            detail,
            f"{name}: the {outcome.kind} receipt cannot be checked in this checkout: {outcome.detail}",
        )
    return None


def _anchor_findings(opened: Mapping[str, epoch.Epoch], view: registry.RegistryView) -> list[Finding]:
    recorded = {(record.subject, record.genesis, record.head) for record in view.log_heads}
    findings: list[Finding] = []
    for name in sorted(opened):
        for anchor in opened[name].anchors:
            if (anchors.CorpusSubject(anchor.subject), anchor.genesis_digest, anchor.head_digest) not in recorded:
                findings.append(
                    Finding(
                        "warning",
                        "anchor-uncorroborated",
                        name,
                        anchor.subject,
                        f"{name}: no registry log-head record carries the heads this epoch anchors "
                        f"{anchor.subject} at",
                    )
                )
    return findings


def _verdicts(
    opened: Mapping[str, epoch.Epoch],
    outcomes: list[tuple[str, derive.ReceiptKind, derive.ReceiptOutcome]],
    unreadable: tuple[str, ...],
) -> tuple[SnapshotVerdict, ...]:
    groups: dict[tuple[derive.ReceiptKind, str], list[tuple[str, derive.ReceiptOutcome]]] = {}
    for name, kind, outcome in outcomes:
        subject = opened[name].receipts[read._member_for(kind)].subject_identity
        try:
            subject = registry._require_lower_hex(subject, 64, "subject")
        except ValueError:
            continue
        groups.setdefault((kind, subject), []).append((name, outcome))
    return tuple(
        SnapshotVerdict(
            kind,
            subject,
            _reduce([outcome for _name, outcome in members]),
            tuple(sorted(members, key=lambda pair: pair[0])),
            unreadable,
        )
        for (kind, subject), members in sorted(groups.items())
    )


def audit_epochs(world: registry.World) -> EpochAudit:
    """Evaluate every retained pair and corroborate every retained anchor."""
    opened, unreadable, view = _retained(world)
    findings = [
        Finding("error", "epoch-malformed", name, refusal, f"{name}: this retained carrier does not read: {refusal}")
        for name, refusal in unreadable
    ]
    outcomes: list[tuple[str, derive.ReceiptKind, derive.ReceiptOutcome]] = []
    for name in sorted(opened):
        for kind in _KINDS:
            outcome = read.validate_receipt(world, opened[name], kind)
            outcomes.append((name, kind, outcome))
            finding = _receipt_finding(name, outcome)
            if finding is not None:
                findings.append(finding)
    findings.extend(_anchor_findings(opened, view))
    snapshots = _verdicts(opened, outcomes, tuple(name for name, _refusal in unreadable))
    for verdict in snapshots:
        if verdict.state == "contradicted":
            findings.append(
                Finding(
                    "error",
                    "snapshot-contradicted",
                    verdict.subject_identity,
                    verdict.kind,
                    f"{verdict.subject_identity}: no receipt naming this {verdict.kind} subject validates "
                    "and at least one is refuted",
                )
            )
    return EpochAudit(tuple(outcomes), snapshots, tuple(sorted(findings, key=lambda finding: finding.sort_key)))


def snapshot_state(
    world: registry.World, kind: derive.ReceiptKind, subject_identity: str
) -> SnapshotVerdict:
    """Reduce one subject over every retained carrier without writing."""
    opened, unreadable, _view = _retained(world)
    member = read._member_for(kind)
    members = [
        (name, read.validate_receipt(world, opened[name], kind))
        for name in sorted(opened)
        if opened[name].receipts[member].subject_identity == subject_identity
    ]
    return SnapshotVerdict(
        kind,
        subject_identity,
        _reduce([outcome for _name, outcome in members]),
        tuple(members),
        tuple(name for name, _refusal in unreadable),
    )
