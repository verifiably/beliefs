"""Explicit import of an epoch carrier (slice 3 design §3)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from nodes.core.write_plan import DefaultExecutor
from test_snapshot_retraction import retracted_world
from test_world_build import ALPHA, BETA, ChainHeads
from test_world_receipts import document, hold_shipped, published_world, world_over

from beliefs.errors import EpochImportRefused, EpochUnknown, PermitExceeded
from beliefs.permit import READ_ONLY
from beliefs.world import derive, epoch, read, registry
from beliefs.world.importing import import_epoch


def exported(published: epoch.Epoch, into: Path, changes: dict[str, object] | None = None) -> Path:
    """A carrier copy outside any world root, edited member by member."""
    members = dict(published.members)
    for member, edited in (changes or {}).items():
        members[member] = yaml.safe_dump(edited, sort_keys=True, allow_unicode=True).encode("utf-8")
    into.mkdir(parents=True)
    for member, content in members.items():
        (into / member).write_bytes(content)
    return into


def replica_world(tmp_path: Path, roots: dict[str, Path], *, hold: bool = True) -> registry.World:
    """A second world of the same id over the same corpora, publishing nothing."""
    world = world_over(tmp_path, roots, name="replica")
    if hold:
        hold_shipped(world)
    return world


def epochs_of(world: registry.World) -> set[str]:
    base = world.config.world_root / "epochs"
    return {entry.name for entry in base.iterdir()} if base.exists() else set()


def test_a_validated_carrier_is_admitted_without_a_pointer_or_a_log_head_record(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    source = exported(published, tmp_path / "export")

    report = import_epoch(replica, source)

    assert report.written is True
    assert report.packaging_identity == published.packaging_identity
    assert {kind: outcome.outcome for kind, outcome in report.outcomes.items()} == dict.fromkeys(
        epoch.RECEIPT_KINDS.values(), "validated"
    )
    assert report.findings == ()
    assert read.open_epoch(replica, published.packaging_identity).members == published.members
    with pytest.raises(EpochUnknown):
        read.current_epoch(replica)
    assert registry._scan_registry(replica.config.world_root).log_heads == ()
    assert epochs_of(replica) == {published.packaging_identity}


def test_a_second_import_of_the_same_carrier_writes_nothing(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    source = exported(published, tmp_path / "export")
    import_epoch(replica, source)
    before = {p: p.stat().st_mtime_ns for p in (replica.config.world_root / "epochs").rglob("*")}

    report = import_epoch(replica, source)

    assert report.written is False
    assert {p: p.stat().st_mtime_ns for p in (replica.config.world_root / "epochs").rglob("*")} == before


def test_a_carrier_missing_a_member_is_refused_as_malformed_with_nothing_written(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    source = exported(published, tmp_path / "export")
    (source / "producer-receipt.yaml").unlink()

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(replica, source)
    assert refused.value.reason == "malformed-carrier"
    assert epochs_of(replica) == set()


def test_a_carrier_of_another_world_is_refused(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    other = world_over(tmp_path, roots, name="other", world_id="e" * 32)
    hold_shipped(other)
    source = exported(published, tmp_path / "export")

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(other, source)
    assert refused.value.reason == "foreign-world"
    assert epochs_of(other) == set()


def test_a_malformed_receipt_refuses_before_any_write_and_names_every_kind(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    receipt = document(published, "producer-receipt.yaml")
    receipt["corpus_states"] = receipt["corpus_states"][:1]
    source = exported(published, tmp_path / "export", {"producer-receipt.yaml": receipt})

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(replica, source)
    assert refused.value.reason == "malformed-receipt"
    assert [outcome.kind for outcome in refused.value.outcomes] == ["producer"]
    assert epochs_of(replica) == set()


def test_a_refuted_receipt_refuses_before_any_write(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    snapshot = document(published, "producer-snapshot.yaml")
    snapshot["producers"] = snapshot["producers"][1:]
    receipt = document(published, "producer-receipt.yaml")
    receipt["subject"] = derive.subject_identity("producer", snapshot)
    source = exported(
        published, tmp_path / "export", {"producer-snapshot.yaml": snapshot, "producer-receipt.yaml": receipt}
    )

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(replica, source)
    assert refused.value.reason == "refuted-receipt"
    assert epochs_of(replica) == set()


def test_an_unresolvable_receipt_is_admitted_with_a_finding_and_no_stored_verdict(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    only_alpha = replica_world(tmp_path, {ALPHA: roots[ALPHA]})
    source = exported(published, tmp_path / "export")

    report = import_epoch(only_alpha, source)

    assert report.written is True
    assert all(outcome.outcome == "unresolvable" for outcome in report.outcomes.values())
    assert [finding.code for finding in report.findings] == ["receipt-unresolvable"] * 4
    carrier = only_alpha.config.world_root / "epochs" / published.packaging_identity
    assert {p.name for p in carrier.iterdir()} == set(epoch.EPOCH_MEMBERS)


def test_the_permit_is_required_before_the_carrier_is_read(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    reader = registry.World(
        registry.WorldConfig(tmp_path / "reader", "f" * 32, tuple(roots.values())),
        DefaultExecutor,
        chain_head=ChainHeads(),
        corpus_executor_factory=DefaultExecutor,
        authority=READ_ONLY,
    )
    source = exported(published, tmp_path / "export")
    (source / "coverage.yaml").unlink()

    with pytest.raises(PermitExceeded):
        import_epoch(reader, source)


def test_a_retracted_producer_subject_refuses_before_any_write(tmp_path):
    _world, _roots, _b, published, *_ = retracted_world(tmp_path)
    source = exported(published, tmp_path / "export")
    replica = world_over(tmp_path, _roots, name="replica"); hold_shipped(replica)
    with pytest.raises(EpochImportRefused) as caught:
        import_epoch(replica, source)
    assert caught.value.reason == "retracted-snapshot"
    assert [o.outcome for o in caught.value.outcomes] == ["retracted"]
    assert epochs_of(replica) == set()


def test_an_unreadable_standing_refuses_before_any_write(tmp_path):
    from fixtures_cut4 import raw_write
    from test_snapshot_retraction import broken_counter
    _world, roots, _b, published, _i, _w, r, _c = retracted_world(tmp_path)
    broken = broken_counter(r)
    raw_write(roots[ALPHA], broken)
    replica = world_over(tmp_path, roots, name="replica"); hold_shipped(replica)
    with pytest.raises(EpochImportRefused) as caught:
        import_epoch(replica, exported(published, tmp_path / "export"))
    assert caught.value.reason == "unreadable-standing" and epochs_of(replica) == set()
