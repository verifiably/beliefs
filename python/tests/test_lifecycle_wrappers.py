"""The lifecycle wrappers and the writability-gate precedence (plan Task 5).

Real engine, real volume: every root lives under `certified_work`, on the
repository's own certified configuration, and every state below is read back
through the Science wrappers. Fabrications follow the atoms suite's own
patterns — chain surgery for pending entries, a raw carrier rewrite for the
pre-lifecycle vintage, the machine-identity seam for host deltas — and each
fixture asserts the state it fabricated before the arm turns on it.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest
from atoms.chain.model import SettledEntry, decode_entry
from atoms.core.errors import PreconditionRefused
from atoms.fs.linux import LinuxBackend
from nodes.core.errors import ExecutionError
from nodes.core.write_plan import CreateOp

from science import root as science_root
from science.root import (
    LifecycleState,
    init_corpus_root,
    init_store_root,
    metadata_root_for,
    migrate_root_to_lifecycle_v3,
    read_lifecycle_state,
    replicate_root,
)
from science.world import anchors, verify

_OTHER_MACHINE = "f" * 32
CORPUS_ID = "a1" * 16


def _executor(root: Path):
    return science_root.durable_executor_factory()(root)


def _chain_files(root: Path) -> dict[str, bytes]:
    directory = root / ".#~chain"
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


def _unsettle(root: Path) -> tuple[str, str]:
    """Remove a committed transaction's settlement leaf: an evidence-starved
    pending entry recovery cannot re-settle (the atoms pending-gate shape)."""
    registration: tuple[str, str] | None = None
    settlement: str | None = None
    for name, payload in _chain_files(root).items():
        entry = decode_entry(payload)[1]
        if type(entry) is SettledEntry:
            settlement = name
            registration = (entry.txid, entry.registration)
    assert registration is not None and settlement is not None
    (root / ".#~chain" / settlement).unlink()
    return registration


def _seeded_corpus(work: Path, name: str = "corpus") -> Path:
    root = work / name
    init_corpus_root(root)
    _executor(root).execute([CreateOp("verification/v1.md", b"# a record\n")])
    return root


def _fabricate_v2_vintage(root: Path) -> None:
    """Rewrite the carrier to the exact pre-lifecycle store, raw."""
    from atoms.store.schema import APPLICATION_ID, V2_SCHEMA_STATEMENTS

    metadata = metadata_root_for(root)
    shutil.rmtree(metadata)
    metadata.mkdir()
    (metadata / "lock").touch(mode=0o600)
    connection = sqlite3.connect(metadata / "atoms.db", isolation_level=None)
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        for statement in V2_SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.execute("PRAGMA user_version = 2")
        connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
    finally:
        connection.close()
    (metadata / "atoms.db").chmod(0o600)


class TestReplication:
    def test_completed_replica_reads_read_only_unserviceable(self, certified_work):
        source = certified_work / "store"
        init_store_root(source)
        (source / "payload.bin").write_bytes(b"opaque payload")
        replica = certified_work / "replica"

        replicate_root(source, replica)

        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE
        assert read_lifecycle_state(source) is LifecycleState.WRITABLE

    def test_replica_chain_is_byte_identical(self, certified_work):
        source = certified_work / "store"
        init_store_root(source)
        (source / "payload.bin").write_bytes(b"opaque payload")
        replica = certified_work / "replica"

        replicate_root(source, replica)

        assert _chain_files(replica) == _chain_files(source)

    def test_replicate_refuses_an_existing_destination(self, certified_work):
        source = certified_work / "store"
        init_store_root(source)
        occupied = certified_work / "occupied"
        occupied.mkdir()
        (occupied / "squatter").write_bytes(b"here first")

        with pytest.raises(PreconditionRefused):
            replicate_root(source, occupied)
        assert sorted(entry.name for entry in occupied.iterdir()) == ["squatter"]

    def test_replicate_returns_the_retained_operation_id(self, certified_work):
        source = certified_work / "store"
        init_store_root(source)
        replica = certified_work / "replica"

        first = replicate_root(source, replica)
        second = replicate_root(source, replica)
        assert first == second

    def test_replicate_refuses_pairwise_overlapping_root_and_metadata_paths(
        self, certified_work
    ):
        source = certified_work / "store"
        init_store_root(source)

        with pytest.raises(PreconditionRefused, match="overlap"):
            replicate_root(source, source / "inside")


class TestTheWritabilityGate:
    def test_metadata_less_copy_refuses_mutation_at_the_writability_gate(
        self, certified_work
    ):
        source = _seeded_corpus(certified_work)
        copy = certified_work / "copy"
        shutil.copytree(source, copy, symlinks=True)
        pending = _unsettle(copy)

        # The fixture's own claims: the copy genuinely carries a pending
        # entry and no metadata.
        assert not metadata_root_for(copy).exists()
        assert read_lifecycle_state(copy) is LifecycleState.METADATA_LESS

        with pytest.raises(ExecutionError, match="does not grant writability"):
            _executor(copy).execute([CreateOp("verification/v2.md", b"# more\n")])

        # The chain evaluation still reads unresolvable at step 3, the
        # pending entry named, behind an anchor stating the copy's own tip.
        from atoms.chain.inspect import WellFormedChain
        from atoms.coordinator.commands import inspect_chain_detached

        inspected = inspect_chain_detached(LinuxBackend(), str(copy))
        assert type(inspected) is WellFormedChain
        record = anchors.LogHeadRecord(
            anchors.CorpusSubject(CORPUS_ID),
            inspected.entries[0][0],
            inspected.tip,
            anchors.AnchorActOrigin("alice"),
        )
        report = science_root.audit_log(
            science_root.WorldConfig(certified_work / "world", "f" * 32, (copy,)),
            anchors.CorpusSubject(CORPUS_ID),
            copy,
            verify.ObserverSet((verify.RegistryCarrier.from_record(record),)),
            actor="alice",
        )
        assert report.outcome == "unresolvable"
        assert pending in report.pending

    def test_writable_pending_root_still_refuses_pending_unresolved(
        self, certified_work
    ):
        root = _seeded_corpus(certified_work)
        _unsettle(root)

        # The fixture's claim: the grant stands.
        assert read_lifecycle_state(root) is LifecycleState.WRITABLE

        with pytest.raises(ExecutionError, match="unsettled registrations"):
            _executor(root).execute([CreateOp("verification/v2.md", b"# more\n")])

    def test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation(
        self, certified_work
    ):
        source = certified_work / "store"
        init_store_root(source)
        (source / "payload.bin").write_bytes(b"opaque payload")
        copy = certified_work / "cold-store"
        shutil.copytree(source, copy, symlinks=True)

        assert read_lifecycle_state(copy) is LifecycleState.METADATA_LESS
        from atoms.coordinator.commands import append_intent

        with pytest.raises(
            PreconditionRefused, match="does not grant writability"
        ):
            append_intent(
                LinuxBackend(),
                str(copy),
                str(metadata_root_for(copy)),
                science_root.PRODUCTION_STORAGE,
                b"an intent",
            )


class TestTheStateRead:
    def test_lifecycle_union_is_closed_at_five(self):
        assert {member.value for member in LifecycleState} == {
            "writable",
            "read-only-serviceable",
            "read-only-unserviceable",
            "metadata-less",
            "binding-mismatched",
        }
        assert len(LifecycleState) == 5

    def test_binding_delta_reads_binding_mismatched(self, certified_work, monkeypatch):
        from atoms.coordinator import lifecycle as atoms_lifecycle

        root = certified_work / "store"
        init_store_root(root)

        monkeypatch.setattr(
            atoms_lifecycle, "_read_machine_identity", lambda: _OTHER_MACHINE
        )
        assert read_lifecycle_state(root) is LifecycleState.BINDING_MISMATCHED
        monkeypatch.undo()

        moved = certified_work / "store-moved"
        shutil.move(root, moved)
        shutil.move(metadata_root_for(root), metadata_root_for(moved))
        assert read_lifecycle_state(moved) is LifecycleState.BINDING_MISMATCHED


class TestMigration:
    def test_migration_refuses_metadata_less_and_mismatched(
        self, certified_work, monkeypatch
    ):
        from atoms.coordinator import lifecycle as atoms_lifecycle

        bare = certified_work / "bare"
        bare.mkdir()
        with pytest.raises(PreconditionRefused, match="metadata"):
            migrate_root_to_lifecycle_v3(bare)

        root = certified_work / "store"
        init_store_root(root)
        monkeypatch.setattr(
            atoms_lifecycle, "_read_machine_identity", lambda: _OTHER_MACHINE
        )
        with pytest.raises(PreconditionRefused, match="mismatch"):
            migrate_root_to_lifecycle_v3(root)

    def test_migration_authorized_success_reads_writable(self, certified_work):
        root = _seeded_corpus(certified_work)
        _fabricate_v2_vintage(root)
        assert read_lifecycle_state(root) is LifecycleState.READ_ONLY_UNSERVICEABLE

        migrate_root_to_lifecycle_v3(root)

        assert read_lifecycle_state(root) is LifecycleState.WRITABLE
