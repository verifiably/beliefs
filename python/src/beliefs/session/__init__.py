"""The writer session (writer-session design): the contract's names, and the
two compositions over `beliefs.root`."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from beliefs.corpus import CoordinationResolver, CorpusWriter, Finding
from beliefs.errors import ManifestMalformed, ManifestMissing, SessionRefused
from beliefs.permit import Authority
from beliefs.profile import ProfileSpec
from beliefs.root import durable_executor_factory, durable_operation_port, log_seam
from beliefs.session.ledger import (
    ActLine,
    InvocationRecord,
    LedgerReader,
    LedgerWriter,
    ledger_path,
    open_ledger_reader,
)
from beliefs.session.writer import (
    Claim,
    ClaimDone,
    ClaimFresh,
    ClaimMismatch,
    ClaimOpen,
    KernelRefusalValue,
    ScopedWriter,
    WriterSession,
)
from beliefs.world import WorldConfig, load_manifest
from beliefs.world.logmodel import WellFormedView

__all__ = [
    "ActLine",
    "Claim",
    "ClaimDone",
    "ClaimFresh",
    "ClaimMismatch",
    "ClaimOpen",
    "InvocationRecord",
    "KernelRefusalValue",
    "LedgerReader",
    "ScopedWriter",
    "WriterSession",
    "open_attended_session",
    "open_ledger_reader",
    "reconcile_sessions",
]


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def open_attended_session(
    world_config: WorldConfig, operations_root: Path, *, coordination: ProfileSpec | None = None
) -> WriterSession:
    """The interactive constructor (design §3.1): full permit by construction."""
    if type(world_config) is not WorldConfig:
        raise TypeError("open_attended_session takes an exact WorldConfig")
    if not isinstance(operations_root, Path):
        raise TypeError("operations_root must be a Path")
    if coordination is not None and not isinstance(coordination, ProfileSpec):
        raise TypeError("coordination must be a compiled ProfileSpec")
    if len(world_config.corpus_roots) != 1:
        raise SessionRefused(
            f"a session needs exactly one corpus root; the config names {len(world_config.corpus_roots)}"
        )
    (root,) = world_config.corpus_roots
    try:
        corpus_id = load_manifest(root).corpus_id
    except (ManifestMissing, ManifestMalformed) as caught:
        raise SessionRefused(f"{root}: the corpus is not adopted: {caught}") from caught
    view = log_seam().inspect_detached(root)
    if type(view) is not WellFormedView:
        raise SessionRefused(
            f"{root}: the chain is {type(view).__name__}; a session opens over a registered, well-formed root"
        )
    resolver = CoordinationResolver({root: coordination}) if coordination is not None else None

    session_id = secrets.token_hex(16)
    path = ledger_path(operations_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=False)
    _fsync_directory(path.parent.parent)
    ledger = LedgerWriter(path)

    def writer_factory(authority: Authority) -> CorpusWriter:
        return CorpusWriter(
            root,
            durable_executor_factory(),
            authority=authority,
            operation_port=durable_operation_port(root, authority),
            coordination_resolver=resolver,
        )

    session = WriterSession(
        session_id=session_id,
        world_id=world_config.world_id,
        corpus_root=root,
        corpus_id=corpus_id,
        operations_root=operations_root,
        ledger=ledger,
        writer_factory=writer_factory,
    )
    # §3.1: session-open is written (by the constructor) before reconciliation runs.
    session.findings = reconcile_sessions(world_config, operations_root, exclude=session_id)
    return session


def reconcile_sessions(
    world_config: WorldConfig, operations_root: Path, *, exclude: str | None = None
) -> tuple[Finding, ...]:
    """Task 8 supplies the body; until then, no prior session is read."""
    return ()
