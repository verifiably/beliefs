"""The epoch audit and the snapshot-state query (slice 3 design §4)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from test_world_build import ALPHA, BETA
from test_world_import_epoch import exported, replica_world
from test_world_receipts import document, hold_shipped, publish, published_world, repackage

from beliefs.errors import EpochMalformed
from beliefs.world import derive, epoch, registry
from beliefs.world.audit import EpochAudit, SnapshotVerdict, audit_epochs, snapshot_state

KINDS = tuple(epoch.RECEIPT_KINDS.values())


def codes(findings) -> list[str]:
    return sorted(finding.code for finding in findings)


def inventory(world: registry.World) -> dict[str, bytes]:
    return {
        str(path.relative_to(world.config.world_root)): path.read_bytes()
        for path in world.config.world_root.rglob("*")
        if path.is_file()
    }


def test_a_published_world_audits_clean(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))

    audit = audit_epochs(world)

    assert isinstance(audit, EpochAudit)
    assert [(name, kind, outcome.outcome) for name, kind, outcome in audit.receipts] == [
        (published.packaging_identity, kind, "validated") for kind in KINDS
    ]
    assert [(verdict.kind, verdict.state, verdict.unreadable) for verdict in audit.snapshots] == [
        (kind, "checked", ()) for kind in sorted(KINDS)
    ]
    assert audit.findings == ()


def test_a_malformed_receipt_is_reported_and_excluded_from_the_reduction(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    forged = repackage(world, published, {"producer-receipt.yaml": receipt})

    audit = audit_epochs(world)

    assert [(name, outcome.outcome) for name, kind, outcome in audit.receipts if kind == "producer"] == sorted(
        [(published.packaging_identity, "validated"), (forged.packaging_identity, "malformed")]
    )
    producer = next(verdict for verdict in audit.snapshots if verdict.kind == "producer")
    assert producer.state == "checked"
    assert [(finding.code, finding.ref) for finding in audit.findings] == [
        ("receipt-malformed", forged.packaging_identity)
    ]
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None
    verdict = snapshot_state(world, "producer", subject)
    assert isinstance(verdict, SnapshotVerdict)
    assert verdict.state == "checked"


def test_the_two_roads_to_unchecked_are_distinguishable(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    all_malformed = replica_world(tmp_path, roots)
    exported(published, all_malformed.config.world_root / "epochs" / ("0" * 64), {"producer-receipt.yaml": receipt})
    merely_absent = replica_world(tmp_path / "absent", {ALPHA: roots[ALPHA]})
    exported(published, merely_absent.config.world_root / "epochs" / published.packaging_identity)

    forged = audit_epochs(all_malformed)
    absent = audit_epochs(merely_absent)

    assert codes(forged.findings) == ["epoch-malformed"]
    assert [(verdict.kind, verdict.state) for verdict in absent.snapshots] == [
        (kind, "unchecked") for kind in sorted(KINDS)
    ]
    assert codes(absent.findings) == ["anchor-uncorroborated"] * 2 + ["receipt-unresolvable"] * 4


def test_an_all_malformed_snapshot_is_unchecked_with_a_finding_per_pair(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    replica = replica_world(tmp_path, roots)
    members = dict(published.members)
    members["producer-receipt.yaml"] = yaml.safe_dump(receipt, sort_keys=True, allow_unicode=True).encode("utf-8")
    identity = epoch.packaging_identity_of(members)
    directory = replica.config.world_root / "epochs" / identity
    directory.mkdir(parents=True)
    for member, content in members.items():
        (directory / member).write_bytes(content)

    audit = audit_epochs(replica)

    producer = next(
        verdict for verdict in audit.snapshots if verdict.kind == "producer" and identity in dict(verdict.receipts)
    )
    assert producer.state == "unchecked"
    assert ("receipt-malformed", identity) in [(finding.code, finding.ref) for finding in audit.findings]


def test_per_entry_stat_and_list_failures_are_reported_and_the_sweep_continues(tmp_path, monkeypatch):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    second = repackage(world, published, {"producer-receipt.yaml": receipt})
    invalid = world.config.world_root / "epochs" / "not-an-identity"
    invalid.mkdir()
    (invalid / "x").write_text("x")
    original_is_dir = Path.is_dir

    def unstatable(path: Path):
        if path.name == published.packaging_identity:
            raise PermissionError(f"{path}: stat refused")
        return original_is_dir(path)

    monkeypatch.setattr(Path, "is_dir", unstatable)
    original_emptied = epoch._emptied

    def unlistable(directory: Path):
        if directory.name == second.packaging_identity:
            raise PermissionError(f"{directory}: listing refused")
        return original_emptied(directory)

    monkeypatch.setattr(epoch, "_emptied", unlistable)
    third = repackage(world, published, {"producer-receipt.yaml": {**receipt, "rule_identity": "v2"}})

    audit = audit_epochs(world)

    assert [finding.ref for finding in audit.findings if finding.code == "epoch-malformed"] == sorted(
        ["not-an-identity", published.packaging_identity, second.packaging_identity]
    )
    assert {name for name, _kind, _outcome in audit.receipts} == {third.packaging_identity}
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None
    assert snapshot_state(world, "producer", subject).unreadable == tuple(
        sorted(["not-an-identity", published.packaging_identity, second.packaging_identity])
    )


def test_an_actually_unreadable_member_is_reported_and_the_sweep_continues(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    readable = repackage(world, published, {"producer-receipt.yaml": receipt})
    member = world.config.world_root / "epochs" / published.packaging_identity / "producer-snapshot.yaml"
    original_mode = member.stat().st_mode
    member.chmod(0)
    try:
        audit = audit_epochs(world)
        subject = published.receipts["producer-receipt.yaml"].subject_identity
        assert subject is not None
        verdict = snapshot_state(world, "producer", subject)
    finally:
        member.chmod(original_mode)

    assert [finding.ref for finding in audit.findings if finding.code == "epoch-malformed"] == [
        published.packaging_identity
    ]
    assert {name for name, _kind, _outcome in audit.receipts} == {readable.packaging_identity}
    assert verdict.unreadable == (published.packaging_identity,)


def test_a_consistent_omission_is_contradicted_under_its_own_subject(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    snapshot = document(published, "producer-snapshot.yaml")
    snapshot["producers"] = snapshot["producers"][1:]
    receipt = document(published, "producer-receipt.yaml")
    receipt["subject"] = derive.subject_identity("producer", snapshot)
    omitted = repackage(world, published, {"producer-snapshot.yaml": snapshot, "producer-receipt.yaml": receipt})

    audit = audit_epochs(world)

    states = {verdict.subject_identity: verdict.state for verdict in audit.snapshots if verdict.kind == "producer"}
    published_subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert published_subject is not None
    assert states[receipt["subject"]] == "contradicted"
    assert states[published_subject] == "checked"
    assert ("snapshot-contradicted", receipt["subject"]) in [
        (finding.code, finding.ref) for finding in audit.findings
    ]
    assert ("receipt-refuted", omitted.packaging_identity) in [
        (finding.code, finding.ref) for finding in audit.findings
    ]


def test_an_imported_carriers_anchors_are_uncorroborated_until_a_build_records_the_same_heads(tmp_path):
    from beliefs.world.importing import import_epoch

    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    import_epoch(replica, exported(published, tmp_path / "export"))

    before = audit_epochs(replica)
    assert sorted(finding.detail for finding in before.findings if finding.code == "anchor-uncorroborated") == sorted(
        [ALPHA, BETA]
    )

    publish(replica, (ALPHA, BETA), hold_shipped(replica))
    after = audit_epochs(replica)
    assert "anchor-uncorroborated" not in codes(after.findings)


def test_the_audit_and_the_query_write_nothing(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    before = inventory(world)
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None

    audit_epochs(world)
    snapshot_state(world, "producer", subject)

    assert inventory(world) == before


def test_a_symlinked_epochs_directory_still_refuses(tmp_path):
    world, _bindings, _roots, _published = published_world(tmp_path, (ALPHA, BETA))
    base = world.config.world_root / "epochs"
    real = base.rename(tmp_path / "moved-epochs")
    base.symlink_to(real)

    with pytest.raises(EpochMalformed):
        audit_epochs(world)
