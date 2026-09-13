"""Cut 27: receipt and damage guarantees over certified durable roots."""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp
from typing import cast

import pytest
import yaml
from authority import FULL
from durable_fixture import pinned
from fixtures_cut4 import raw_write
from profiles import BASE
from test_relocation_rows import _belief_digest
from test_world_audit import codes, stale
from test_world_epoch_audit import inventory
from test_world_import_epoch import exported
from test_world_receipts import document, hold_shipped, publish, repackage
from test_world_view import address_in, chain_nodes, damage
from test_world_view_acceptance import chain, durable_world  # noqa: F401

# Imported pytest fixtures are injected as arguments below.
# ruff: noqa: F811
from verification_fixtures import publish_corpus

from beliefs import stored
from beliefs.audit import NO_EVIDENCE, audit_corpus, audit_world
from beliefs.corpus import ReadView, lineage_snapshot
from beliefs.errors import (
    ContractMismatch,
    CorpusDamaged,
    CorpusStateMalformed,
    CoverageUnresolvable,
    EpochImportRefused,
    EpochUnknown,
)
from beliefs.lineage import certify, divergence_state, snapshot_projection
from beliefs.resolution import build_snapshot
from beliefs.root import init_world_root, metadata_root_for, open_corpus, open_world, replicate_root, restore_root
from beliefs.world import Fresh, WorldConfig, anchors, derive, epoch, read, registry, rules, verify
from beliefs.world import view as view_module
from beliefs.world.audit import audit_epochs, snapshot_state
from beliefs.world.importing import import_epoch
from beliefs.world.view import open_world_view

KINDS = cast(tuple[derive.ReceiptKind, ...], tuple(epoch.RECEIPT_KINDS.values()))


@pytest.fixture()
def scratch(work_directory):
    path = Path(mkdtemp(prefix="cut27-", dir=work_directory))
    try:
        yield path
    finally:
        shutil.rmtree(path)


def replica(scratch, original, roots, *, hold=True, name="replica", world_id=None):
    config = WorldConfig(scratch / name, world_id or original.config.world_id, tuple(roots.values()))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    for path in roots.values():
        world.admit(path, provenance=Fresh())
    if hold:
        hold_shipped(world)
    return world


def remount(world, roots):
    return open_world(replace(world.config, corpus_roots=tuple(roots.values())), authority=FULL)


def omission(published, *, consistent):
    snapshot = document(published, "producer-snapshot.yaml")
    omitted = [entry for entry in snapshot["producers"] if "run:r2" in entry["runs"]]
    assert len(omitted) == 1
    snapshot["producers"] = [entry for entry in snapshot["producers"] if entry not in omitted]
    changes: dict[str, object] = {"producer-snapshot.yaml": snapshot}
    if consistent:
        receipt = document(published, "producer-receipt.yaml")
        receipt["subject"] = derive.subject_identity("producer", snapshot)
        changes["producer-receipt.yaml"] = receipt
    return changes


def outcomes(audit):
    return {(name, kind): outcome for name, kind, outcome in audit.receipts}


def never(*_args, **_kwargs):
    raise AssertionError("availability or evaluation was consulted before its gate")


def test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably(chain, scratch):
    world, roots, published, _a, _b = chain
    target = replica(scratch, world, roots)
    for consistent, reason in ((False, "malformed-receipt"), (True, "refuted-receipt")):
        source = exported(published, scratch / str(consistent), omission(published, consistent=consistent))
        before = inventory(target)
        with pytest.raises(EpochImportRefused) as caught:
            import_epoch(target, source)
        assert caught.value.reason == reason
        assert inventory(target) == before


def test_every_coverage_declaration_must_agree_durably(chain, scratch, monkeypatch):
    world, roots, published, a, _b = chain
    target = replica(scratch, world, roots)
    receipt = document(published, "producer-receipt.yaml")
    receipt["corpus_states"] = [s for s in receipt["corpus_states"] if s["corpus_id"] == a]
    coverage = document(published, "coverage.yaml")
    coverage["coverage"] = [s for s in coverage["coverage"] if s["corpus_id"] == a]
    anchors = document(published, "anchors.yaml")
    anchors["corpora"] = [s for s in anchors["corpora"] if s["subject"] == a]
    source = exported(
        published,
        scratch / "export",
        {
            "producer-receipt.yaml": receipt,
            "coverage.yaml": coverage,
            "anchors.yaml": anchors,
        },
    )
    assert target.status(a).present
    before = inventory(target)
    with monkeypatch.context() as patch:
        patch.setattr(registry, "corpus_state_identity", never)
        patch.setattr(registry, "_carrier_roots", never)
        patch.setattr(rules, "_locked_resolve_rule_binding", never)
        with pytest.raises(EpochImportRefused) as caught:
            import_epoch(target, source)
    assert caught.value.reason == "malformed-receipt"
    assert any("subject declares coverage" in outcome.detail for outcome in caught.value.outcomes)
    assert inventory(target) == before


def test_a_missing_receipt_a_corpus_state_and_a_bare_version_are_refused_durably(chain, scratch):
    world, _roots, published, _a, _b = chain
    target = replica(scratch, world, {}, hold=False)
    before = inventory(target)
    for fault in ("missing", "state", "version"):
        receipt = document(published, "producer-receipt.yaml")
        if fault == "state":
            receipt["corpus_states"][0]["corpus_state"] = receipt["corpus_states"][0]["corpus_id"]
        elif fault == "version":
            receipt["rule_identity"] = "v1"
        source = exported(published, scratch / fault, {"producer-receipt.yaml": receipt})
        if fault == "missing":
            (source / "producer-receipt.yaml").unlink()
        with pytest.raises(EpochImportRefused) as caught:
            import_epoch(target, source)
        assert caught.value.reason == ("malformed-carrier" if fault == "missing" else "malformed-receipt")
        assert inventory(target) == before


def test_an_unresolvable_receipt_imports_with_a_finding_and_a_later_audit_evaluates_it_durably(chain, scratch):
    world, roots, published, a, b = chain
    target = replica(scratch, world, {a: roots[a]})
    report = import_epoch(target, exported(published, scratch / "export"))
    assert report.written and report.packaging_identity == published.packaging_identity
    assert [f.code for f in report.findings] == ["receipt-unresolvable"] * 4
    assert [o.outcome for o in report.outcomes.values()] == ["unresolvable"] * 4
    carrier = target.config.world_root / "epochs" / published.packaging_identity
    assert {p.name for p in carrier.iterdir()} == set(epoch.EPOCH_MEMBERS)
    assert {p.name: p.read_bytes() for p in carrier.iterdir()} == published.members
    target = remount(target, roots)
    target.admit(roots[b], provenance=Fresh())
    assert [o.outcome for o in outcomes(audit_epochs(target)).values()] == ["validated"] * 4


def test_a_moved_corpus_and_one_of_two_moving_are_unresolvable_durably(chain):
    world, roots, published, a, b = chain
    unchanged = registry.corpus_state_identity(roots[a])
    open_corpus(roots[b], authority=FULL, profile=BASE).add(
        stored.dataset_node("late", title="late", resources=pinned())
    )
    for kind in KINDS:
        outcome = read.validate_receipt(world, published, kind)
        assert outcome.outcome == "unresolvable" and b in outcome.detail
    assert registry.corpus_state_identity(roots[a]) == unchanged


def test_a_fabricated_carrier_is_read_through_and_caught_only_under_audit_durably(chain, monkeypatch):
    world, _roots, published, a, _b = chain
    forged = malformed_pair(world, published)
    with monkeypatch.context() as patch:
        patch.setattr(read, "validate_receipt", never)
        assert read.open_epoch(world, forged.packaging_identity).members == forged.members
        assert type(read.resolve_address(world, forged, address_in(published, a))) is read.Resolved
    assert ("receipt-malformed", forged.packaging_identity) in [(f.code, f.ref) for f in audit_epochs(world).findings]


def malformed_pair(world, published, marker="v1"):
    return repackage(
        world,
        published,
        {
            "producer-receipt.yaml": {
                **document(published, "producer-receipt.yaml"),
                "rule_identity": marker,
            }
        },
    )


def test_an_all_malformed_snapshot_is_unchecked_with_a_finding_per_pair_durably(chain, scratch):
    world, roots, published, _a, _b = chain
    target = replica(scratch, world, roots)
    carriers = [malformed_pair(target, published, marker) for marker in ("v1", "v2")]
    audit = audit_epochs(target)
    verdict = next(v for v in audit.snapshots if v.kind == "producer")
    assert verdict.state == "unchecked" and len(verdict.receipts) == 2
    assert {(f.code, f.ref) for f in audit.findings if f.code.startswith("receipt-")} == {
        ("receipt-malformed", p.packaging_identity) for p in carriers
    }
    assert all(o.outcome == "malformed" for _name, o in verdict.receipts)


def test_the_two_roads_to_unchecked_are_distinguishable_durably(chain, scratch):
    world, roots, published, a, _b = chain
    malformed = replica(scratch, world, roots)
    malformed_pair(malformed, published)
    absent = replica(scratch, world, {a: roots[a]}, name="absent")
    import_epoch(absent, exported(published, scratch / "export"))
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert snapshot_state(malformed, "producer", subject).state == "unchecked"
    assert snapshot_state(absent, "producer", subject).state == "unchecked"
    assert [f.code for f in audit_epochs(malformed).findings if f.code.startswith("receipt-")] == ["receipt-malformed"]
    assert [f.code for f in audit_epochs(absent).findings if f.code.startswith("receipt-")] == [
        "receipt-unresolvable"
    ] * 4


def test_a_validating_receipt_beside_a_malformed_one_is_checked_durably(chain):
    world, _roots, published, _a, _b = chain
    forged = malformed_pair(world, published)
    # Equality includes both retained receipts, so lexical packaging order
    # cannot let a last-only query pass merely by retaining the valid one.
    audit = audit_epochs(world)
    verdict = next(v for v in audit.snapshots if v.kind == "producer")
    assert verdict.state == "checked" and len(verdict.receipts) == 2
    assert snapshot_state(world, "producer", verdict.subject_identity) == verdict
    assert ("receipt-malformed", forged.packaging_identity) in [(f.code, f.ref) for f in audit.findings]
    assert not any(
        f.code == "snapshot-contradicted" for f in audit_world(world, forged, evidence=NO_EVIDENCE, profile=BASE).world
    )


def test_mounting_evaluates_nothing_and_the_three_callers_agree_durably(chain, scratch, monkeypatch):
    world, roots, published, a, b = chain
    with monkeypatch.context() as patch:
        patch.setattr(read, "validate_receipt", never)
        target = replica(scratch, world, roots)
        rebuilt = publish(target, (a, b), hold_shipped(target))
    report = import_epoch(target, exported(published, scratch / "export"))
    audit = audit_epochs(target)
    for kind, outcome in report.outcomes.items():
        assert outcomes(audit)[published.packaging_identity, kind] == outcome
        subject = published.receipts[read._member_for(kind)].subject_identity
        verdict = snapshot_state(target, kind, subject)
        assert dict(verdict.receipts)[published.packaging_identity] == outcome
        assert verdict == next(v for v in audit.snapshots if v.kind == kind and v.subject_identity == subject)
    assert rebuilt.packaging_identity in {name for name, _kind, _outcome in audit.receipts}


def test_the_same_pair_moves_from_unresolvable_to_refuted_after_mount_and_audit_durably(chain, scratch):
    world, roots, published, a, b = chain
    target = replica(scratch, world, {a: roots[a]})
    report = import_epoch(target, exported(published, scratch / "export", omission(published, consistent=True)))
    assert report.written and report.outcomes["producer"].outcome == "unresolvable"
    target = remount(target, roots)
    target.admit(roots[b], provenance=Fresh())
    audit = audit_epochs(target)
    assert outcomes(audit)[report.packaging_identity, "producer"].outcome == "refuted"
    assert next(v.state for v in audit.snapshots if v.kind == "producer") == "contradicted"


def test_the_unheld_rule_route_evaluates_after_installation_durably(chain, scratch):
    world, roots, published, _a, _b = chain
    target = replica(scratch, world, roots, hold=False)
    report = import_epoch(target, exported(published, scratch / "export"))
    assert report.written and [f.code for f in report.findings] == ["receipt-unresolvable"] * 4
    hold_shipped(target)
    assert [o.outcome for o in outcomes(audit_epochs(target)).values()] == ["validated"] * 4


def test_import_refuses_a_write_and_audit_and_query_write_nothing_durably(chain, scratch):
    world, roots, published, _a, _b = chain
    target = replica(scratch, world, roots)
    before = inventory(target)
    source = exported(published, scratch / "refuted", omission(published, consistent=True))
    with pytest.raises(EpochImportRefused) as caught:
        import_epoch(target, source)
    assert caught.value.reason == "refuted-receipt" and inventory(target) == before
    source = exported(published, scratch / "export")
    assert import_epoch(target, source).written
    expected = {
        **before,
        **{f"epochs/{published.packaging_identity}/{name}": value for name, value in published.members.items()},
    }
    after = inventory(target)
    # The durable executor also records its intent and settlement. No other
    # world content may accompany the eleven requested CreateOps.
    chain_appends = {
        name: value for name, value in after.items() if name not in before and name.startswith(".#~chain/")
    }
    assert len(chain_appends) == 2
    expected.update(chain_appends)
    assert after == expected
    with pytest.raises(EpochUnknown):
        read.current_epoch(target)
    assert not import_epoch(target, source).written
    assert inventory(target) == expected
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    for call in (
        lambda: audit_epochs(target),
        lambda: snapshot_state(target, "producer", subject),
        lambda: audit_world(target, published, evidence=NO_EVIDENCE, profile=BASE),
    ):
        before = inventory(target)
        call()
        assert inventory(target) == before


def test_an_unreadable_carrier_is_a_finding_and_the_next_carrier_is_still_evaluated_durably(chain):
    world, _roots, published, _a, _b = chain
    readable = malformed_pair(world, published)
    member = world.config.world_root / "epochs" / published.packaging_identity / "producer-snapshot.yaml"
    mode = member.stat().st_mode
    member.chmod(0)
    try:
        audit = audit_epochs(world)
        subject = published.receipts["producer-receipt.yaml"].subject_identity
        verdict = snapshot_state(world, "producer", subject)
    finally:
        member.chmod(mode)
    assert [f.ref for f in audit.findings if f.code == "epoch-malformed"] == [published.packaging_identity]
    assert {name for name, _kind, _outcome in audit.receipts} == {readable.packaging_identity}
    assert len(audit.receipts) == 4 and verdict.unreadable == (published.packaging_identity,)


def test_a_built_epochs_anchors_are_corroborated_and_an_imported_ones_are_not_durably(chain, scratch):
    world, roots, published, a, b = chain
    assert not any(f.code == "anchor-uncorroborated" for f in audit_epochs(world).findings)
    target = replica(scratch, world, roots)
    import_epoch(target, exported(published, scratch / "export"))
    assert registry._scan_registry(target.config.world_root).log_heads == ()
    assert sorted(f.detail for f in audit_epochs(target).findings if f.code == "anchor-uncorroborated") == sorted(
        (a, b)
    )
    publish(target, (a, b), hold_shipped(target))
    assert not any(f.code == "anchor-uncorroborated" for f in audit_epochs(target).findings)


@pytest.mark.parametrize("kind", ["parse-error", "path-mismatch", "uid-collision", "id-collision"])
def test_a_damaged_carrier_is_reported_and_never_served_durably(chain, kind):
    world, roots, published, a, b = chain
    raw_write(roots[b], stale("remainder"))
    damage(roots[b], kind)
    with pytest.raises(CorpusStateMalformed):
        open_world_view(world, published)
    view = open_world_view(world, published, on_damage="report")
    (report,) = view.damaged()
    assert report.corpus_id == b and report.cause == "construction"
    assert kind in {f.code for f in report.findings}
    assert view.absent() == () and all(d.corpus_id != b for d in view.drift())
    address = address_in(published, b)
    for fetch in (view.locate, view.resolve, view.holds, view.get, view.inbound, view.corpus_view):
        with pytest.raises(CorpusDamaged):
            fetch(address)
    assert view.corpus_of(address) == b and all(n.id != address for n in view.iter_stored())
    assert view.captured_records(b) and view.captured_manifest(b).corpus_id == b
    assert view.get(address_in(published, a)).id == address_in(published, a)
    findings = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE).corpora[b]
    assert kind in {f.code for f in findings}
    assert ("semantic-hash-stale", "mismatch") in codes(findings)
    assert any(f.code == "corpus-damaged" and f.detail.startswith("construction:") for f in findings)
    assert not any(f.code == "drift" for f in findings)
    for receipt_kind in KINDS:
        result = read.validate_receipt(world, published, receipt_kind)
        assert result.outcome == "unresolvable" and b in result.detail


def test_a_foreign_base_pin_is_base_pin_damage_durably(chain):
    world, roots, published, _a, b = chain
    manifest = registry.load_manifest(roots[b])
    foreign = replace(manifest, profile=replace(manifest.profile, science_contract="science:" + "0" * 64))
    (roots[b] / "corpus.yaml").write_bytes(registry.manifest_bytes(foreign))
    with pytest.raises(ContractMismatch):
        open_world_view(world, published)
    view = open_world_view(world, published, on_damage="report")
    (report,) = view.damaged()
    assert report.cause == "base-pin" and report.findings == ()
    assert view.captured_records(b) == () and view.captured_manifest(b) == foreign
    with pytest.raises(CorpusDamaged):
        view.get(address_in(published, b))
    assert codes(audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE).corpora[b]) == [
        ("corpus-damaged", "base-pin"),
        ("profile-mismatch", "base"),
    ]


def test_the_default_open_still_refuses_and_no_state_identity_is_taken_over_a_remainder_durably(chain, monkeypatch):
    world, roots, published, _a, b = chain
    damage(roots[b], "parse-error")
    with pytest.raises(CorpusStateMalformed):
        open_world_view(world, published)
    calls = []
    original = registry.corpus_state_identity

    def recorded(root):
        calls.append(root)
        return original(root)

    monkeypatch.setattr(registry, "corpus_state_identity", recorded)
    view = open_world_view(world, published, on_damage="report")
    assert calls.count(roots[b]) == 1
    assert view.damaged()[0].corpus_id == b
    assert not any(d.corpus_id == b for d in view.drift())
    assert all(n.id != address_in(published, b) for n in view.iter_stored())


def verification_world(durable_world):
    _cid, _root, writer = durable_world.corpus()
    original = publish_corpus(writer, publish=True)
    assert original.node is not None
    nodes = tuple(writer.read_view.iter_stored())
    world = durable_world(tuple(n for n in nodes if n.kind != "run"), tuple(n for n in nodes if n.kind == "run"))
    return original, world


def test_drift_absence_and_unreachable_recomputation_are_findings_durably(chain, durable_world):
    world, roots, published, a, b = chain
    late = stale("late")
    raw_write(roots[a], late)
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    assert codes(audit.corpora[a]) == [
        ("drift", "state"),
        ("drift", f"unmapped:{late.uid}"),
        ("semantic-hash-stale", "mismatch"),
    ]
    absent = remount(world, {a: roots[a]})
    assert codes(audit_world(absent, published, evidence=NO_EVIDENCE, profile=BASE).corpora[b]) == [
        ("corpus-absent", "")
    ]
    original, (world, roots, published, a, b) = verification_world(durable_world)
    damage(roots[b], "parse-error")
    findings = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE).corpora[a]
    assert original.node is not None
    assert any(f.code == "derivation-unreachable" and f.ref == original.node.id and f.detail == b for f in findings)


def test_attestation_endpoints_and_shared_identifiers_are_findings_durably(durable_world):
    left = stored.dataset_node("left", title="left")
    right = stored.dataset_node("right", title="right")
    gone = stored.dataset_node("gone", title="gone")

    def attestation(left, right):
        return stored.coreference_attestation_node(
            title="same work",
            endpoints=tuple(sorted((left, right))),
            stance=1,
            actor=FULL.actor,
            grounds="same work",
            event_token="event-1",
        )

    crossing = attestation(left.id, right.id)
    dangling = attestation(left.id, gone.id)
    first = stored.source_node(title="paper", identifiers={"doi": "10.1234/abc", "pmid": "42"})
    second = stored.source_node(title="paper again", identifiers={"pmid": "42"})
    unrelated = stored.source_node(title="other", identifiers={"pmid": "43"})
    world, roots, initial, a, b = durable_world((left, gone, first, unrelated), (right, second))
    writer = open_corpus(roots[a], authority=FULL, profile=BASE)
    view = open_world_view(world, initial)
    writer.attest_coreference(crossing, view=view)
    writer.attest_coreference(dangling, view=view)
    publish(world, (a, b), hold_shipped(world))
    open_corpus(roots[a], authority=FULL, profile=BASE).delete(gone.id)
    published = publish(world, (a, b), hold_shipped(world))
    findings = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE).world
    assert codes(findings) == [("attestation-endpoint-unknown", gone.id), ("source-identifier-shared", "pmid:42")]
    shared = next(f for f in findings if f.code == "source-identifier-shared")
    assert shared.ref == min(first.id, second.id) and shared.severity == "warning"
    absent = audit_world(remount(world, {a: roots[a]}), published, evidence=NO_EVIDENCE, profile=BASE)
    assert codes(f for f in absent.world if f.code.startswith("attestation-endpoint")) == [
        ("attestation-endpoint-unknown", gone.id)
    ]
    assert len([f for f in absent.world if f.code == "receipt-unresolvable"]) == 4
    damage(roots[b], "parse-error")
    damaged = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    assert ("attestation-endpoint-unreachable", right.id) in codes(damaged.world)
    (roots[b] / "verification" / "bad.md").unlink()
    repaired = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    assert codes(repaired.world) == codes(findings) and repaired.corpora[b] == ()


def test_the_world_audit_reproduces_every_per_record_finding_durably(chain, monkeypatch):
    world, roots, published, a, _b = chain
    raw_write(roots[a], stale("captured"))
    local = audit_corpus(ReadView.opened_at(roots[a]), evidence=NO_EVIDENCE, profile=BASE)
    captured = open_world_view(world, published, on_damage="report")
    raw_write(roots[a], stale("after-capture"))
    monkeypatch.setattr(view_module, "open_world_view", lambda *_args, **_kwargs: captured)
    findings = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE).corpora[a]
    assert tuple(f for f in findings if f.code != "drift") == local
    assert any(f.code == "semantic-hash-stale" for f in local)
    assert not any(f.ref == "dataset:after-capture" for f in findings)


def test_the_evaluator_answers_unresolvable_for_a_damaged_carrier_and_the_edge_is_indeterminate_durably(chain):
    world, roots, published, a, b = chain
    damage(roots[b], "parse-error")
    for kind in KINDS:
        result = read.validate_receipt(world, published, kind)
        assert result.outcome == "unresolvable" and b in result.detail
    assert (
        read.coreference_edge(world, published, *sorted((address_in(published, a), address_in(published, b)))).state
        == "indeterminate"
    )


def restore_copy(world, path, corpus_id):
    observers = verify.ObserverSet(
        tuple(
            verify.RegistryCarrier.from_record(record)
            for record in registry._scan_registry(world.config.world_root).log_heads
            if record.subject == anchors.CorpusSubject(corpus_id)
        )
    )
    assert observers.carriers
    report = restore_root(path, anchors.CorpusSubject(corpus_id), observers, authority=FULL)
    assert report.outcome == "validated" and report.findings == ()


def test_root_move_rename_and_clone_change_no_identity_durably(durable_world, scratch):
    d0, r1, d1, r2, d2 = chain_nodes()
    world, roots, published, a, b = durable_world((d0, r2, d2), (r1, d1))
    before = (published.coverage, published.documents["producer-snapshot.yaml"], _belief_digest(published))
    bindings = hold_shipped(world)
    for relocation in ("moved", "renamed-differently", "cloned"):
        source = roots[b]
        target = scratch / relocation
        if relocation == "cloned":
            replicate_root(source, target, authority=FULL)
            shutil.rmtree(source)
        else:
            source.rename(target)
        # Engine metadata is bound to its path. A moved semantic root takes a
        # cold read-serviceability grant; copying old metadata would mismatch.
        restore_copy(world, target, b)
        roots[b] = target
        world = remount(world, roots)
        again = publish(world, (a, b), bindings)
        assert registry.load_manifest(target).corpus_id == b
        assert (again.coverage, again.documents["producer-snapshot.yaml"], _belief_digest(again)) == before


def test_a_coordinated_forgery_is_undetected_and_reads_as_a_fork_durably(chain, scratch):
    world, roots, published, a, b = chain
    copy = scratch / "pre-edit"
    replicate_root(roots[b], copy, authority=FULL)
    restore_copy(world, copy, b)
    forged_id = "d" * 32
    forged_manifest = replace(registry.load_manifest(roots[b]), corpus_id=forged_id)
    (roots[b] / "corpus.yaml").write_bytes(registry.manifest_bytes(forged_manifest))
    admission = registry.AdmissionRecord(forged_manifest, Fresh(), "forger")
    directory = world.config.world_root / "registry"
    (directory / f"{registry.admission_digest(admission)}.yaml").write_bytes(
        yaml.safe_dump(registry.admission_projection(admission), sort_keys=True).encode()
    )
    forged = publish(world, (a, forged_id), hold_shipped(world))
    assert forged_id in dict(forged.coverage)
    status = world.status(forged_id)
    assert (status.known, status.live, status.present, status.findings) == (True, True, True, ())
    assert all(read.validate_receipt(world, published, k).outcome == "unresolvable" for k in KINDS)
    world = remount(world, {a: roots[a], b: copy})
    assert all(read.validate_receipt(world, published, k).outcome == "validated" for k in KINDS)
    scan = registry._scan_registry(world.config.world_root)
    assert {record.manifest.corpus_id for record in scan.admissions} == {a, b, forged_id}
    assert not any(record.manifest.forked_from for record in scan.admissions if record.manifest.corpus_id == forged_id)


def test_two_carriers_of_one_id_refuse_the_build_durably(chain, scratch):
    world, roots, _published, a, b = chain
    twin = scratch / "twin"
    shutil.copytree(roots[a], twin)
    shutil.copytree(metadata_root_for(roots[a]), metadata_root_for(twin))
    world = open_world(replace(world.config, corpus_roots=(*roots.values(), twin)), authority=FULL)
    with pytest.raises(CoverageUnresolvable) as caught:
        publish(world, (a, b), hold_shipped(world))
    assert "exactly one configured carrier root" in str(caught.value) and str(twin) in str(caught.value)
    assert not hasattr(world, "merge") and not hasattr(world, "consolidate")


def test_a_cross_corpus_producer_diverges_and_moves_the_digest_durably(durable_world):
    d0, r1, d1, _r2, _d2 = chain_nodes()
    other = stored.dataset_node("b", title="b")
    r2 = stored.run_node("r2x", title="r2x", spec="s", transforms=[other.id], produces=[d1.id])
    world, roots, published, a, b = durable_world((d0, r1, d1), (other, r2))
    snapshot = lineage_snapshot(open_world_view(world, published), [d1.id])
    assert divergence_state(snapshot, d1.id) == "divergent"
    result = certify(snapshot, (d1.id,), (d0.id,))
    assert result.state == "not-certified" and "lineage-divergent" in result.findings
    with_r2 = snapshot_projection(snapshot)
    # Hold corpus ids and every other node fixed; only the competing run changes.
    open_corpus(roots[b], authority=FULL, profile=BASE).delete(r2.id)
    without = publish(world, (a, b), hold_shipped(world))
    without_r2 = lineage_snapshot(open_world_view(world, without), [d1.id])
    assert divergence_state(without_r2, d1.id) != "divergent"
    assert with_r2 != snapshot_projection(without_r2)
    assert _belief_digest(published) != _belief_digest(without)


def test_open_refusals_never_become_absence_durably(chain):
    world, roots, published, _a, b = chain
    damage(roots[b], "parse-error")
    view = open_world_view(world, published, on_damage="report")
    address = address_in(published, b)
    absent = {}
    for fetch in (view.locate, view.resolve, view.holds, view.get, view.inbound, view.corpus_view):
        with pytest.raises(CorpusDamaged):
            answer = fetch(address)
            if type(answer) is read.NotPresent:
                absent[address] = b
    assert view.absent() == () and absent == {}
    with pytest.raises(CorpusDamaged):
        lineage_snapshot(view, [address])
    healthy = lineage_snapshot(view, ["dataset:d0"])
    assert healthy.not_present == {}
    resolution = build_snapshot(not_present=absent)
    assert resolution.identity == build_snapshot().identity


def test_a_carrier_of_another_world_is_refused_durably(chain, scratch):
    world, roots, published, _a, _b = chain
    foreign = replica(scratch, world, roots, world_id="f" * 32)
    before = inventory(foreign)
    with pytest.raises(EpochImportRefused) as caught:
        import_epoch(foreign, exported(published, scratch / "export"))
    assert caught.value.reason == "foreign-world" and inventory(foreign) == before


@pytest.mark.parametrize("fault", ["narrower", "extra", "duplicate", "subject"])
def test_other_coverage_and_subject_faults_are_malformed_before_availability_durably(
    chain, scratch, monkeypatch, fault
):
    world, roots, published, _a, _b = chain
    targets = (replica(scratch, world, roots), replica(scratch, world, {}, hold=False, name="empty"))
    changes = {}
    for member in epoch.RECEIPT_KINDS:
        receipt = document(published, member)
        if fault == "narrower":
            receipt["corpus_states"] = receipt["corpus_states"][:1]
        elif fault == "extra":
            receipt["corpus_states"].append({"corpus_id": "f" * 32, "corpus_state": "f" * 64})
        elif fault == "duplicate":
            receipt["corpus_states"].append(dict(receipt["corpus_states"][0]))
            receipt["corpus_states"].sort(key=lambda entry: entry["corpus_id"])
        else:
            receipt["subject"] = "0" * 64
        changes[member] = receipt
    source = exported(published, scratch / "export", changes)
    for target in targets:
        before = inventory(target)
        with monkeypatch.context() as patch:
            patch.setattr(registry, "corpus_state_identity", never)
            patch.setattr(registry, "_carrier_roots", never)
            patch.setattr(rules, "_locked_resolve_rule_binding", never)
            with pytest.raises(EpochImportRefused) as caught:
                import_epoch(target, source)
        assert caught.value.reason == "malformed-receipt"
        assert inventory(target) == before


@pytest.mark.parametrize("unheld", ["rule_identity", "corpus_state"])
def test_well_formed_unheld_identities_are_unresolvable_durably(chain, scratch, unheld):
    world, roots, published, _a, _b = chain
    target = replica(scratch, world, roots)
    receipt = document(published, "producer-receipt.yaml")
    if unheld == "rule_identity":
        receipt[unheld] = "0" * 64
    else:
        receipt["corpus_states"][0][unheld] = "0" * 64
    report = import_epoch(target, exported(published, scratch / "export", {"producer-receipt.yaml": receipt}))
    assert report.written
    assert report.outcomes["producer"].outcome == "unresolvable"
    assert [f.code for f in report.findings] == ["receipt-unresolvable"]
