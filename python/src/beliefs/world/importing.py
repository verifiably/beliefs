"""Explicit import of an epoch carrier (slice 3 design §3)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal, cast

from nodes.core.write_plan import CreateOp

from beliefs.corpus import Finding
from beliefs.errors import EpochImportRefused, EpochMalformed, RetractionUnreadable
from beliefs.world import derive, epoch, read, registry

__all__ = ["EpochImportReport", "import_epoch"]


@dataclass(frozen=True)
class EpochImportReport:
    """The outcomes and effects of one admitted carrier."""

    packaging_identity: str
    outcomes: Mapping[derive.ReceiptKind, derive.ReceiptOutcome]
    findings: tuple[Finding, ...]
    written: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcomes", MappingProxyType(dict(self.outcomes)))


def import_epoch(world: registry.World, source: Path) -> EpochImportReport:
    """Admit a carrier into this world's retained epochs."""
    world.authority.require("epoch")
    try:
        members = epoch._carrier_members(Path(source))
        packaging_identity = epoch.packaging_identity_of(members)
        carrier = epoch._carrier_epoch(members, packaging_identity)
    except (EpochMalformed, OSError) as caught:
        raise EpochImportRefused("malformed-carrier", f"{source}: the carrier does not read: {caught}") from caught
    if carrier.world_anchor.subject != world.config.world_id:
        raise EpochImportRefused(
            "foreign-world",
            f"{packaging_identity}: epoch belongs to world {carrier.world_anchor.subject}, not {world.config.world_id}",
        )
    kinds = cast(tuple[derive.ReceiptKind, ...], tuple(epoch.RECEIPT_KINDS.values()))
    outcomes: dict[derive.ReceiptKind, derive.ReceiptOutcome] = {}
    for kind in kinds:
        try:
            outcomes[kind] = read.validate_receipt(world, carrier, kind)
        except RetractionUnreadable as caught:
            raise EpochImportRefused(
                "unreadable-standing",
                f"{packaging_identity}: the {kind} subject's standing cannot be decided: {caught}",
            ) from caught
    decisions: tuple[
        tuple[Literal["malformed-receipt"], Literal["malformed"]]
        | tuple[Literal["retracted-snapshot"], Literal["retracted"]]
        | tuple[Literal["refuted-receipt"], Literal["refuted"]],
        ...,
    ] = (("malformed-receipt", "malformed"), ("retracted-snapshot", "retracted"), ("refuted-receipt", "refuted"))
    for reason, outcome in decisions:
        offending = tuple(verdict for verdict in outcomes.values() if verdict.outcome == outcome)
        if offending:
            raise EpochImportRefused(
                reason,
                f"{packaging_identity}: {len(offending)} receipt(s) {outcome}: "
                + "; ".join(f"{verdict.kind}: {verdict.detail}" for verdict in offending),
                outcomes=offending,
            )
    findings = tuple(
        Finding(
            severity="warning",
            code="receipt-unresolvable",
            ref=packaging_identity,
            detail=f"{verdict.kind}: {verdict.detail}",
            message=f"{packaging_identity}: the {verdict.kind} receipt cannot be checked here and enters unchecked",
        )
        for verdict in outcomes.values()
        if verdict.outcome == "unresolvable"
    )
    with registry._locked_barrier(world) as world_root:
        directory = world_root / "epochs" / packaging_identity
        if directory.is_symlink() or (directory.exists() and not (directory.is_dir() and epoch._emptied(directory))):
            retained = epoch._locked_open_epoch(world_root, packaging_identity)
            assert dict(retained.members) == dict(members)
            written = False
        else:
            world._executor_factory(world_root).execute(
                [CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in epoch.EPOCH_MEMBERS]
            )
            written = True
    return EpochImportReport(packaging_identity, outcomes, findings, written)
