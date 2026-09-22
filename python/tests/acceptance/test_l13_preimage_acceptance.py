"""Cut 37's durable arms: the L13 preimage resolver on the certified engine and volume.

Every selected behaviour of `docs/designs/2026-09-21-conformance-cut-37.md` §3
runs here through `root` only, over registered roots beside `work_directory`.
One test per declaration unit, named for its unit. The corpus each unit needs
is authored through the durable executor the write API is built with: a
logged manifest, a logged failing verification, and a logged `DeleteOp` of it
— the same registered transaction path `CorpusWriter.delete` runs on (cut
18's durable check covers `delete`'s own chain shape).
"""

from __future__ import annotations

import hashlib
import os
import shutil
from collections.abc import Iterator
from dataclasses import replace
from itertools import count
from pathlib import Path

import pytest
from authority import FULL
from fixtures_cut6 import PINS
from nodes.core.frontmatter import node_to_markdown
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, DeleteOp
from test_permit_boundary import WRITE_ENTRY_POINTS

from beliefs import root as science_root
from beliefs.errors import LogEvidenceRefused, PreimageMismatch
from beliefs.root import (
    admit_arrival,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.world import anchors, registry, verify
from beliefs.world.logmodel import (
    GenesisEntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

CORPUS_ID = "13" * 16
WORLD_ID = "37" * 16
RECORD = "verification/v-1-fail.md"
DISCUSSION = "discussion/seed.md"
_COUNTER = count()


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _verification(verdict: str) -> bytes:
    return node_to_markdown(
        Node(
            id="verification:v-1-fail",
            uid="1" * 32,
            kind="verification",
            title="v-1-fail",
            facets={"verification": {"assessment": "assessment:a1", "scope": "clean-environment", "verdict": verdict}},
        )
    ).encode("utf-8")


FAILED = _verification("failed")
OTHER_VERSION = _verification("passed")
"""The same record — same id, so the same claimed path — rendered with another
verdict and never stored: what R16's path match would have resolved."""
SEED = node_to_markdown(Node(id="discussion:seed", uid="2" * 32, kind="discussion", title="the seeded record", facets={})).encode("utf-8")


@pytest.fixture
def lane(work_directory) -> Iterator[Path]:
    """One directory per test on the certified volume; every root and its
    metadata sibling live inside it, so one `rmtree` removes them all."""
    base = work_directory.resolve() / f"cut37-{os.getpid()}-{next(_COUNTER)}"
    base.mkdir(parents=True)
    yield base
    shutil.rmtree(base, ignore_errors=True)


def _corpus(base: Path, name: str = "source", *, seed: bool = False) -> Path:
    """A registered corpus: a logged manifest, a logged failing verification,
    then a logged removal of it. With `seed`, a `discussion` record is logged
    and removed as well."""
    root = base / name
    init_corpus_root(root, authority=FULL)
    executor = science_root.durable_executor_factory()(root)
    executor.execute([CreateOp("corpus.yaml", registry.manifest_bytes(registry.CorpusManifest(2, CORPUS_ID, PINS)))])
    executor.execute([CreateOp(RECORD, FAILED)])
    executor.execute([DeleteOp(RECORD, _sha(FAILED))])
    if seed:
        executor.execute([CreateOp(DISCUSSION, SEED)])
        executor.execute([DeleteOp(DISCUSSION, _sha(SEED))])
    assert not (root / RECORD).exists()
    return root


def _carrier(root: Path) -> verify.RegistryCarrier:
    """A registry log-head record anchoring the root's present tip, the
    `named-local` carrier the audit and a restore bind for a corpus subject."""
    genesis, head = science_root.chain_head_reader()(root)
    return verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(anchors.CorpusSubject(CORPUS_ID), genesis, head, anchors.AnchorActOrigin("alice"))
    )


def _observers(root: Path) -> verify.ObserverSet:
    return verify.ObserverSet((_carrier(root),))


def _audit(base: Path, root: Path, *, history: dict[str, bytes] | None = None, observers: verify.ObserverSet | None = None) -> verify.LogReport:
    config = science_root.WorldConfig(base / "audit-world", WORLD_ID, (root,))
    return science_root.audit_log(config, anchors.CorpusSubject(CORPUS_ID), root, observers or _observers(root), actor="alice", history=history)


def _restored(base: Path, source: Path, name: str = "restored") -> Path:
    replica = base / name
    replicate_root(source, replica, authority=FULL)
    restore_root(replica, anchors.CorpusSubject(CORPUS_ID), _observers(source), authority=FULL)
    assert read_lifecycle_state(replica).value == "read-only-serviceable"
    return replica


def _arrived(base: Path, source: Path, *, tag: str = "a", history: dict[str, bytes] | None = None) -> verify.LogReport:
    """A raw copy of `source` (no metadata sibling: `metadata-less`, detached
    inspection) admitted to a fresh world through `admit_arrival`."""
    cold = base / f"cold-{tag}"
    shutil.copytree(source, cold, symlinks=True)
    assert read_lifecycle_state(cold).value == "metadata-less"
    config = science_root.WorldConfig(base / f"arrival-world-{tag}", WORLD_ID, (cold,))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    _record, report = admit_arrival(world, cold, registry.ReplicaOf(CORPUS_ID), _observers(source), history=history)
    return report


def _findings(report: verify.LogReport, ref: str = RECORD) -> list[verify.Finding]:
    return [finding for finding in report.findings if finding.ref == ref]


def _codes(report: verify.LogReport, ref: str = RECORD) -> list[str]:
    return [finding.code for finding in _findings(report, ref)]


def _removed_digest(root: Path) -> str:
    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    removal = [r for r in verify.committed_removals(view, science_root._log_seam().absent_state) if r.path == RECORD]
    assert len(removal) == 1
    digest = verify.removed_digest(removal[0].state, science_root._log_seam().state_facts)
    assert digest is not None
    return digest


def _tree(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


# --- L13 ---------------------------------------------------------------------


def test_l13a_a_logged_removal_is_in_the_timeline_and_draws_record_removed_durably(lane):
    """L13-a. The removal is in the replayed timeline — `validated`, no
    disagreement — and draws `record-removed` naming the path and the removing
    transaction, unchanged in code, severity, ref, detail and message."""
    source = _corpus(lane)
    report = _audit(lane, source)
    assert report.outcome == "validated"
    removed = _findings(report)[0]
    assert (removed.code, removed.severity, removed.ref) == ("record-removed", "warning", RECORD)
    view = science_root._log_seam().inspect_registered(source)
    assert type(view) is WellFormedView
    txid = verify.committed_removals(view, science_root._log_seam().absent_state)[0].txid
    assert removed.detail == f"txid={txid}"
    assert removed.message == "a committed transaction removed a registered-surface record"


def test_l13b_the_surviving_preimage_classifies_the_removal_on_the_writable_root_durably(lane):
    """L13-b. No `history`: the writable root's retained preimage resolves by
    the removed state's digest and classifies the removal as a failing
    verification's, `source=preimage`, the digest equal to sha256 of the bytes
    the record had before removal; the message names the removed bytes."""
    source = _corpus(lane)
    report = _audit(lane, source)
    assert report.outcome == "validated"
    assert _codes(report) == ["record-removed", "failing-verification-removed"]
    classified = _findings(report)[1]
    assert classified.severity == "error"
    assert classified.detail.endswith(f"digest=sha256:{_sha(FAILED)} source=preimage")
    assert _removed_digest(source) == f"sha256:{_sha(FAILED)}"
    assert classified.message.startswith("the removed record's bytes, resolved by digest")
    assert "held copy" not in classified.message


def test_l13c_a_held_copy_of_another_version_of_the_record_resolves_nothing_durably(lane):
    """L13-c. `history` holds the same record rendered with verdict `passed`
    (same id, same claimed path, another digest). On the writable root the
    preimage classifies `verdict=failed` and the copy is named nowhere; on the
    restored copy the removal reads `removal-unclassified` naming the removed
    digest only — R16's misclassification, reversed."""
    source = _corpus(lane)
    other = {f"sha256:{_sha(OTHER_VERSION)}": OTHER_VERSION}
    assert _sha(OTHER_VERSION) != _sha(FAILED)

    writable = _audit(lane, source, history=other)
    assert _codes(writable) == ["record-removed", "failing-verification-removed"]
    assert _findings(writable)[1].detail.endswith("source=preimage")
    assert _sha(OTHER_VERSION) not in _findings(writable)[1].detail

    restored = _restored(lane, source)
    report = _audit(lane, restored, history=other)
    assert _codes(report) == ["record-removed", "removal-unclassified"]
    absent = _findings(report)[1]
    assert absent.detail == f"{_findings(report)[0].detail} digest=sha256:{_sha(FAILED)} preimage=refused"
    assert _sha(OTHER_VERSION) not in absent.detail and _sha(OTHER_VERSION) not in absent.message


def test_l13d_no_local_history_is_stated_and_a_held_copy_of_the_removed_bytes_resolves_durably(lane):
    """L13-d. The restored read-only copy retains no preimage: the audit reads
    `removal-unclassified preimage=refused` with the engine's lifecycle words;
    the detached arrival of a raw copy reports `preimage=not-consulted`; with
    the removed bytes held under their digest, both classify
    `source=held-copy`."""
    source = _corpus(lane)
    removed = {f"sha256:{_sha(FAILED)}": FAILED}

    restored = _restored(lane, source)
    report = _audit(lane, restored)
    assert report.outcome == "validated"
    assert _codes(report) == ["record-removed", "removal-unclassified"]
    absent = _findings(report)[1]
    assert absent.severity == "warning"
    assert absent.detail.endswith(f"digest=sha256:{_sha(FAILED)} preimage=refused")
    assert "read-only-serviceable does not grant writability" in absent.message
    with_copy = _audit(lane, restored, history=removed)
    assert _codes(with_copy) == ["record-removed", "failing-verification-removed"]
    assert _findings(with_copy)[1].detail.endswith(f"digest=sha256:{_sha(FAILED)} source=held-copy")

    arrival = _arrived(lane, source)
    assert arrival.outcome == "validated"
    assert _codes(arrival) == ["record-removed", "removal-unclassified"]
    assert _findings(arrival)[1].detail.endswith("preimage=not-consulted")
    arrival_with_copy = _arrived(lane, source, tag="b", history=removed)
    assert _codes(arrival_with_copy) == ["record-removed", "failing-verification-removed"]
    assert _findings(arrival_with_copy)[1].detail.endswith("source=held-copy")


def test_l13e_corrupt_local_history_refuses_the_act_and_touches_no_project_file_durably(lane):
    """L13-e. The indexed preimage leaf under the metadata root is unlinked
    (a truncated leaf trips the registered inspection's own store checks
    first, as raw `MetadataStoreInvalid`; a missing one is found by the
    reader): the audit refuses `LogEvidenceRefused(phase="preimage",
    engine_error="MetadataStoreInvalid")`, produces no report, and every
    project file is byte-identical."""
    source = _corpus(lane)
    leaf = metadata_root_for(source) / "blobs" / "sha256" / _sha(FAILED)
    assert leaf.is_file(), "the store indexes the removed bytes under their digest"
    before = _tree(source)
    leaf.unlink()

    with pytest.raises(LogEvidenceRefused) as caught:
        _audit(lane, source)
    assert (caught.value.phase, caught.value.engine_error) == ("preimage", "MetadataStoreInvalid")
    assert _tree(source) == before


def test_l13f_a_removed_record_of_another_kind_classifies_as_not_a_verification_durably(lane):
    """L13-f. A removed `discussion` record resolves through its preimage and
    reads `removal-classified kind=discussion source=preimage` at `warning`.
    The unreadable-facet, not-a-record and `digest=none` arms are declared at
    the unit level over fabricated views (`test_world_log_replay.py`)."""
    source = _corpus(lane, seed=True)
    report = _audit(lane, source)
    assert _codes(report, DISCUSSION) == ["record-removed", "removal-classified"]
    classified = _findings(report, DISCUSSION)[1]
    assert classified.severity == "warning"
    assert classified.detail.endswith(f"digest=sha256:{_sha(SEED)} source=preimage kind=discussion")
    assert _codes(report) == ["record-removed", "failing-verification-removed"]


def test_l13g_retirement_appends_a_status_event_and_deletes_nothing_durably(lane):
    """L13-g (relabel; cut 8's L13u4 cited). A real world retires an admitted
    corpus: the registry gains one record, none is removed, and the world
    chain's committed removals are empty."""
    source = _corpus(lane)
    config = science_root.WorldConfig(lane / "retire-world", WORLD_ID, (source,))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=FULL)
    world.admit(source, provenance=registry.Fresh())
    registry_dir = config.world_root / "registry"
    before = sorted(p.name for p in registry_dir.glob("*.yaml"))

    world.retire(CORPUS_ID)

    after = sorted(p.name for p in registry_dir.glob("*.yaml"))
    assert set(before) <= set(after) and len(after) == len(before) + 1
    view = science_root._log_seam().inspect_registered(config.world_root)
    assert type(view) is WellFormedView
    assert verify.committed_removals(view, science_root._log_seam().absent_state) == ()


def test_l13h_preimage_gc_appears_in_no_chain_and_a_read_appends_nothing_durably(lane):
    """L13-h (relabel; cut 8's L13u5 cited). The entry-class union is closed
    and carries no collection member; an audit that resolved a preimage leaves
    the corpus chain's entries and tip byte-identical."""
    from dataclasses import fields

    for cls in (GenesisEntryView, IntentEntryView, RegisteredEntryView, SettledEntryView):
        assert not any("gc" in field.name or "collect" in field.name for field in fields(cls)), cls
    source = _corpus(lane)
    seam = science_root._log_seam()
    before = seam.inspect_registered(source)
    report = _audit(lane, source)
    assert _codes(report)[1] == "failing-verification-removed"
    after = seam.inspect_registered(source)
    assert type(before) is WellFormedView and after == before


# --- boundary invariants -----------------------------------------------------


def _probing_seam(monkeypatch, root: Path, observed: list[tuple[str, str]]):
    """Production reads with both capture completions and preimage reads
    observed against `root`'s real operation lock."""
    from beliefs.corpus import _operation_lock_for
    from beliefs.errors import BuildContended

    production = science_root._log_seam()
    production_capture_records = verify.capture_records
    held = _operation_lock_for(root)

    def read(target: Path, txid: str, path: str, max_bytes: int):
        with pytest.raises(BuildContended), held.capture():
            pass
        observed.append(("preimage", str(held._holder)))
        return production.read_preimage(target, txid, path, max_bytes)

    def capture(target: Path, paths):
        result = production.capture(target, paths)
        observed.append(("surface-capture", str(held._holder)))
        return result

    def capture_records(target: Path, kind):
        result = production_capture_records(target, kind)
        observed.append(("record-capture", str(held._holder)))
        return result

    seam = verify.LogSeam(
        inspect_registered=production.inspect_registered,
        inspect_detached=production.inspect_detached,
        capture=capture,
        read_head=production.read_head,
        absent_state=production.absent_state,
        world_lock=production.world_lock,
        corpus_lock=production.corpus_lock,
        lifecycle_state=production.lifecycle_state,
        state_facts=production.state_facts,
        read_preimage=read,
    )
    monkeypatch.setattr(science_root, "_LOG_SEAM", seam)
    monkeypatch.setattr(verify, "capture_records", capture_records)
    return seam


def test_bi1_the_reads_are_inside_the_hold_after_the_captures_with_the_chains_arguments_durably(lane, monkeypatch):
    """BI-1. One read per committed removal with a file pre-state, made under
    the writer hold after both captures complete, with the chain's txid, path and
    byte_len; arrival and restore make none."""
    source = _corpus(lane, seed=True)
    observed: list[tuple[str, str]] = []
    calls: list[tuple[str, str, int]] = []
    seam = _probing_seam(monkeypatch, source, observed)
    inner = seam.read_preimage

    def recording(target, txid, path, max_bytes):
        calls.append((txid, path, max_bytes))
        return inner(target, txid, path, max_bytes)

    monkeypatch.setattr(science_root, "_LOG_SEAM", replace(seam, read_preimage=recording))
    _audit(lane, source)
    assert observed == [
        ("surface-capture", "writer"),
        ("record-capture", "writer"),
        ("preimage", "writer"),
        ("preimage", "writer"),
    ]
    view = science_root._log_seam().inspect_registered(source)
    assert type(view) is WellFormedView
    expected = [
        (r.txid, r.path, int(dict(science_root._log_seam().state_facts(r.state))["byte_len"]))
        for r in verify.committed_removals(view, science_root._log_seam().absent_state)
    ]
    assert calls == expected and len(calls) == 2

    calls.clear()
    replica = lane / "replica"
    replicate_root(source, replica, authority=FULL)
    restore_root(replica, anchors.CorpusSubject(CORPUS_ID), _observers(source), authority=FULL)
    assert calls == []
    _arrived(lane, source)
    assert calls == []


def test_bi2_a_read_mutates_nothing_and_joins_no_write_inventory_durably(lane):
    """BI-2. Every file under the root and under its metadata sibling's
    `blobs/` tree is byte-identical across an audit that resolved a preimage,
    and `read_preimage` is in no `WRITE_ENTRY_POINTS` row."""
    source = _corpus(lane)
    blobs = metadata_root_for(source) / "blobs"
    before_root, before_blobs = _tree(source), _tree(blobs)
    report = _audit(lane, source)
    assert _codes(report)[1] == "failing-verification-removed"
    assert _tree(source) == before_root and _tree(blobs) == before_blobs
    assert not any("preimage" in name for name in WRITE_ENTRY_POINTS)


def test_bi3_a_preimage_that_hashes_elsewhere_refuses_before_any_finding_durably(lane, monkeypatch):
    """BI-3. Over a real chain with every other seam callable the production
    one, a `read_preimage` returning bytes of another digest refuses
    `PreimageMismatch` and no report is produced."""
    source = _corpus(lane)
    production = science_root._log_seam()
    monkeypatch.setattr(
        science_root,
        "_LOG_SEAM",
        replace(production, read_preimage=lambda *_: verify.PreimageRead(OTHER_VERSION)),
    )
    with pytest.raises(PreimageMismatch, match=RECORD):
        _audit(lane, source)
