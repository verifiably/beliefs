"""The fork acts, the fork geneses, and the L6 lift in code (plan Task 7).

Real engine on the certified volume. The parent corpora here carry stored
nodes written through the `Corpus` handle — the fork reads the parent's
surface as it stands, and the child's fork genesis baseline is what makes
that surface log-covered on the child where it never was on the parent.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from atoms.chain.model import GenesisEntry, encode_entry, entry_digest
from atoms.coordinator.commands import (
    RootOperationMismatch,
    fork_root,
    resume_fork_root,
)
from atoms.fs.linux import LinuxBackend
from test_world_build import corpus_at

from science import root as science_root
from science.root import (
    LifecycleState,
    SourceSnapshotMoved,
    fork_corpus,
    fork_store,
    init_corpus_root,
    init_store_root,
    metadata_root_for,
    read_lifecycle_state,
)
from science.world import anchors, registry, verify

PARENT_ID = "a1" * 16


def _parent_corpus(work: Path, name: str = "parent") -> Path:
    """A registered parent with a manifest and one stored record."""
    from nodes.core.node import Node

    root = work / name
    init_corpus_root(root)
    corpus_at(
        root,
        PARENT_ID,
        (
            Node(
                id="note:seed",
                uid="1" * 32,
                kind="note",
                title="the seeded record",
                facets={},
            ),
        ),
    )
    return root


def _head_of(root: Path) -> tuple[str, str]:
    return science_root.chain_head_reader()(root)


def _record(corpus_id: str, genesis: str, head: str) -> verify.RegistryCarrier:
    return verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(
            anchors.CorpusSubject(corpus_id), genesis, head, anchors.AnchorActOrigin("alice")
        )
    )


def _audit(work: Path, subject, root: Path, *carriers) -> verify.LogReport:
    return science_root.audit_log(
        science_root.WorldConfig(work / "audit-world", "f" * 32, (root,)),
        subject,
        root,
        verify.ObserverSet(carriers),
        actor="alice",
    )


def _genesis_view(root: Path):
    from atoms.chain.inspect import WellFormedChain
    from atoms.coordinator.commands import inspect_chain_detached

    inspected = inspect_chain_detached(LinuxBackend(), str(root))
    assert type(inspected) is WellFormedChain
    return inspected


def _genesis_entry(root: Path) -> GenesisEntry:
    _digest, genesis = _genesis_view(root).entries[0]
    assert type(genesis) is GenesisEntry
    return genesis


class TestForkCorpus:
    def test_fork_corpus_mints_a_fresh_id_independent_of_path_and_name(
        self, certified_work
    ):
        parent = _parent_corpus(certified_work)
        first = fork_corpus(parent, certified_work / "child-one")
        second = fork_corpus(parent, certified_work / "child-two")

        assert first.corpus_id != second.corpus_id
        assert first.corpus_id != PARENT_ID
        for manifest in (first, second):
            assert manifest.forked_from is not None
            assert manifest.forked_from.corpus_id == PARENT_ID
            assert len(manifest.forked_from.corpus_state) == 64

    def test_fork_manifest_is_complete_before_writability(self, certified_work):
        parent = _parent_corpus(certified_work)
        child = certified_work / "child"
        minted = fork_corpus(parent, child)

        assert read_lifecycle_state(child) is LifecycleState.WRITABLE
        stored = registry.load_manifest(child)
        assert stored == minted
        assert stored.forked_from is not None

    def test_fork_genesis_carries_parent_digests_and_nonempty_baseline(
        self, certified_work
    ):
        parent = _parent_corpus(certified_work)
        parent_genesis, parent_head = _head_of(parent)
        child = certified_work / "child"
        fork_corpus(parent, child)

        genesis = _genesis_entry(child)
        forked = anchors.parse_corpus_genesis(genesis.payload)
        assert forked == (parent_genesis, parent_head)
        baseline_paths = [path for path, _state in genesis.baseline]
        assert "corpus.yaml" in baseline_paths
        assert any(path.endswith(".md") for path in baseline_paths)

    def test_nonfork_genesis_still_requires_empty_baseline(self):
        from science.world import logmodel

        genesis = logmodel.GenesisEntryView(
            digest="g" * 64,
            payload=science_root.GENESIS_PAYLOAD,
            baseline=(("corpus.yaml", ("kind", "file")),),
        )
        view = logmodel.WellFormedView(
            genesis=genesis, entries=(genesis,), tip=genesis.digest, pending=()
        )
        report = verify.evaluate_log(
            anchors.CorpusSubject(PARENT_ID),
            view,
            verify.ObserverSet(()),
            (),
            None,
            object(),
        )
        assert report.outcome == "malformed"
        assert any(
            finding.code == "genesis-form-invalid" for finding in report.findings
        )

    def test_source_moved_between_derivation_and_fork_refuses(self, certified_work):
        parent = _parent_corpus(certified_work)
        _genesis, head = _head_of(parent)
        # The head moves after derivation.
        from nodes.core.write_plan import CreateOp

        science_root.durable_executor_factory()(parent).execute(
            [CreateOp("verification/late.md", b"# late\n")]
        )
        child = certified_work / "child"

        with pytest.raises(SourceSnapshotMoved):
            fork_root(
                LinuxBackend(),
                str(parent),
                str(metadata_root_for(parent)),
                str(child),
                str(metadata_root_for(child)),
                science_root.PRODUCTION_STORAGE,
                expected_source_head=head,
                genesis_payload=science_root._fork_corpus_genesis_payload(
                    (_genesis, head)
                ),
                surface_paths=("corpus.yaml",),
                dest_overrides=(),
            )
        assert not child.exists()


class TestForkRetry:
    def _interrupt(self, monkeypatch, seam: str):
        from atoms.coordinator import lifecycle as atoms_lifecycle

        real = getattr(atoms_lifecycle, seam)

        class Cut(BaseException):
            pass

        def failing(*args, **kwargs):
            raise Cut(seam)

        monkeypatch.setattr(atoms_lifecycle, seam, failing)
        return Cut, lambda: monkeypatch.setattr(atoms_lifecycle, seam, real)

    def test_fork_retry_reuses_the_original_child_identity(
        self, certified_work, monkeypatch
    ):
        parent = _parent_corpus(certified_work)
        child = certified_work / "child"
        cut, restore = self._interrupt(monkeypatch, "_complete_root_operation")
        with pytest.raises(cut):
            fork_corpus(parent, child)
        restore()

        minted = fork_corpus(parent, child)
        assert registry.load_manifest(child).corpus_id == minted.corpus_id
        assert read_lifecycle_state(child) is LifecycleState.WRITABLE

        # Resupplying different bytes against the retained operation refuses.
        _genesis, head = _head_of(parent)
        with pytest.raises(RootOperationMismatch):
            fork_root(
                LinuxBackend(),
                str(parent),
                str(metadata_root_for(parent)),
                str(child),
                str(metadata_root_for(child)),
                science_root.PRODUCTION_STORAGE,
                expected_source_head=head,
                genesis_payload=b"different opaque bytes",
                surface_paths=("corpus.yaml",),
                dest_overrides=(),
            )

    def test_fork_resume_reads_pending_claim_before_lifecycle_stamp(
        self, certified_work, monkeypatch
    ):
        parent = _parent_corpus(certified_work)
        child = certified_work / "child"
        cut, restore = self._interrupt(monkeypatch, "_stamp_copy_destination")
        with pytest.raises(cut):
            fork_corpus(parent, child)
        restore()

        import json

        claimed = json.loads((child / ".#~root-claim").read_bytes())["operation_id"]
        minted = fork_corpus(parent, child)
        assert registry.load_manifest(child).corpus_id == minted.corpus_id
        assert science_root._fork_pending(child) is None
        assert claimed is not None

    def test_fork_resume_reads_pending_operation_after_lifecycle_stamp(
        self, certified_work, monkeypatch
    ):
        parent = _parent_corpus(certified_work)
        child = certified_work / "child"
        cut, restore = self._interrupt(monkeypatch, "_copy_tree")
        with pytest.raises(cut):
            fork_corpus(parent, child)
        restore()

        pending = science_root._fork_pending(child)
        assert pending is not None
        minted = fork_corpus(parent, child)
        assert registry.load_manifest(child).corpus_id == minted.corpus_id
        assert read_lifecycle_state(child) is LifecycleState.WRITABLE

    def test_fork_resume_after_genesis_does_not_need_the_source(
        self, certified_work, monkeypatch
    ):
        parent = _parent_corpus(certified_work)
        child = certified_work / "child"
        cut, restore = self._interrupt(monkeypatch, "_complete_root_operation")
        with pytest.raises(cut):
            fork_corpus(parent, child)
        restore()

        shutil.rmtree(parent)
        shutil.rmtree(metadata_root_for(parent))
        minted = fork_corpus(parent, child)
        assert registry.load_manifest(child).corpus_id == minted.corpus_id
        assert read_lifecycle_state(child) is LifecycleState.WRITABLE

    def test_fork_resume_refuses_wrong_or_completed_operation_id(
        self, certified_work
    ):
        parent = _parent_corpus(certified_work)
        child = certified_work / "child"
        fork_corpus(parent, child)

        with pytest.raises(RootOperationMismatch):
            resume_fork_root(
                LinuxBackend(),
                str(child),
                str(metadata_root_for(child)),
                science_root.PRODUCTION_STORAGE,
                science_root.RootOperationId("0" * 32),
            )


class TestForkStore:
    def test_fork_store_mints_and_carries_the_parent_digests(self, certified_work):
        parent = certified_work / "parent-store"
        init_store_root(parent)
        parent_genesis, parent_head = _head_of(parent)
        child = certified_work / "child-store"

        child_id = fork_store(parent, child)

        assert read_lifecycle_state(child) is LifecycleState.WRITABLE
        genesis = _genesis_entry(child)
        decoded_id, forked = science_root._decode_store_genesis(genesis.payload)
        assert decoded_id == child_id
        assert forked == (parent_genesis, parent_head)


class TestTheL6Lift:
    def _forked_child(self, work: Path) -> tuple[Path, str, str, str, str]:
        parent = _parent_corpus(work)
        child = work / "child"
        minted = fork_corpus(parent, child)
        genesis, head = _head_of(child)
        member = next(
            path
            for path, _state in _genesis_entry(child).baseline
            if path.endswith(".md")
        )
        return child, minted.corpus_id, genesis, head, member

    def test_l6_anchored_baseline_deletion_refutes(self, certified_work):
        child, child_id, genesis, head, member = self._forked_child(certified_work)
        # The fixture's obligations: the member is baseline-covered and
        # pre-log — in the fork genesis's baseline, in no post-genesis entry.
        assert member in [path for path, _s in _genesis_entry(child).baseline]
        assert len(_genesis_view(child).entries) == 1

        (child / member).unlink()
        report = _audit(
            certified_work,
            anchors.CorpusSubject(child_id),
            child,
            _record(child_id, genesis, head),
        )
        assert report.outcome == "refuted"

    def test_l6_anchor_free_rewrite_is_unresolvable(self, certified_work):
        child, child_id, _genesis, _head, member = self._forked_child(certified_work)
        copy = certified_work / "rewritten"
        shutil.copytree(child, copy, symlinks=True)
        original_genesis_bytes = min((copy / ".#~chain").iterdir()).read_bytes()

        # The consistent rewrite: genesis, baseline, and chain omit the member.
        original = _genesis_entry(copy)
        kept = tuple(
            (path, state) for path, state in original.baseline if path != member
        )
        rewritten = encode_entry(None, GenesisEntry(original.payload, kept))
        shutil.rmtree(copy / ".#~chain")
        (copy / ".#~chain").mkdir()
        (copy / ".#~chain" / entry_digest(rewritten)).write_bytes(rewritten)
        (copy / member).unlink()

        # The fixture's obligations: byte-difference and full omission.
        assert rewritten != original_genesis_bytes
        assert member not in [path for path, _s in _genesis_entry(copy).baseline]
        assert not (copy / member).exists()

        report = _audit(certified_work, anchors.CorpusSubject(child_id), copy)
        assert report.outcome == "unresolvable"
        assert report.outcome not in ("validated", "refuted")

    def test_parent_anchor_never_compared_in_fork_subject_evaluation(
        self, certified_work
    ):
        parent = _parent_corpus(certified_work)
        parent_genesis, parent_head = _head_of(parent)
        child = certified_work / "child"
        minted = fork_corpus(parent, child)

        report = _audit(
            certified_work,
            anchors.CorpusSubject(minted.corpus_id),
            child,
            _record(PARENT_ID, parent_genesis, parent_head),
        )
        # The parent anchor is filtered by subject selection: it contributes
        # to no genesis or ancestry judgment over the fork.
        assert report.observer_bound == ()
        assert report.outcome == "unresolvable"

    def test_two_fork_geneses_same_child_subject_refute(self, certified_work):
        child, child_id, genesis, head, _member = self._forked_child(certified_work)
        copy = certified_work / "replaced"
        shutil.copytree(child, copy, symlinks=True)

        # A self-consistent chain under a different fork genesis, same child
        # subject: the forked_from head differs, everything else stands.
        original = _genesis_entry(copy)
        other_payload = science_root._fork_corpus_genesis_payload(
            ("d" * 64, "c" * 64)
        )
        replaced = encode_entry(None, GenesisEntry(other_payload, original.baseline))
        shutil.rmtree(copy / ".#~chain")
        (copy / ".#~chain").mkdir()
        (copy / ".#~chain" / entry_digest(replaced)).write_bytes(replaced)

        # The fixture's obligations: same subject, differing geneses.
        assert registry.load_manifest(copy).corpus_id == child_id
        assert _genesis_view(copy).entries[0][0] != genesis

        report = _audit(
            certified_work,
            anchors.CorpusSubject(child_id),
            copy,
            _record(child_id, genesis, head),
        )
        assert report.outcome == "refuted"
