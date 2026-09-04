"""`restore_root`: one held boundary from inspection to grant (plan Task 6).

Real engine on the certified volume for every admission arm; the one-boundary
arm drives the verify-level core with the audit suite's stand-in seam, because
a probe cannot be wired into the production one. Every admission claim is read
back through `read_lifecycle_state`, never off the returned report — the
report is the evaluator's judgment of the copy, and admission is a lifecycle
fact.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from atoms.chain.model import IntentEntry, encode_entry, entry_digest
from atoms.core.errors import PreconditionRefused
from atoms.fs.linux import LinuxBackend
from authority import FULL
from fixtures_cut6 import PINS
from nodes.core.write_plan import CreateOp, ReplaceOp
from test_world_log_audit import Captures, Inspections, make_seam, surfaced

from beliefs import root as science_root
from beliefs.corpus import _operation_lock_for
from beliefs.errors import BuildContended
from beliefs.root import (
    LifecycleState,
    init_corpus_root,
    init_store_root,
    metadata_root_for,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.world import anchors, registry, verify

OTHER_STORE_ID = "6" * 32
CORPUS_A = "a1" * 16
CORPUS_B = "b2" * 16


def _executor(root: Path):
    return science_root.durable_executor_factory()(root)


def _seeded_store(work: Path, name: str = "store") -> tuple[Path, str]:
    """An initialized, still-empty store: this slice's chain states no
    payload (holdings are the next slice's row), so a store that carries raw
    payload replays as a disagreement — exactly what `_forked_form_store`
    exists to model the other way."""
    root = work / name
    store_id = init_store_root(root, authority=FULL)
    return root, store_id


def _forked_form_store(work: Path, name: str = "forked-store") -> tuple[Path, str]:
    """A raw-authored fork-form store: the genesis payload states
    `forked_from` and its baseline names the payload surface (the L6 lift),
    so the chain genuinely names files the disk must carry."""
    import hashlib

    from atoms.chain.model import GenesisEntry, state_to_json
    from atoms.core.fingerprint import FileState

    root = work / name
    (root / "artifacts").mkdir(parents=True)
    files = {
        "artifacts/head.json": b"{}",
        "blob.bin": b"opaque payload",
    }
    baseline = []
    for path, content in sorted(files.items()):
        target = root / path
        target.write_bytes(content)
        target.chmod(0o644)
        digest = hashlib.sha256(content).hexdigest()
        baseline.append(
            (path, state_to_json(FileState(f"sha256:{digest}", 0o644, len(content))))
        )
    store_id = "5" * 32
    payload = science_root._store_genesis_payload(store_id, ("f" * 64, "e" * 64))
    chain = root / ".#~chain"
    chain.mkdir()
    envelope = encode_entry(None, GenesisEntry(payload, tuple(baseline)))
    (chain / entry_digest(envelope)).write_bytes(envelope)
    return root, store_id


def _head_of(root: Path) -> tuple[str, str]:
    return science_root.chain_head_reader()(root)


def _detached_head(root: Path) -> tuple[str, str]:
    from atoms.chain.inspect import WellFormedChain
    from atoms.coordinator.commands import inspect_chain_detached

    inspected = inspect_chain_detached(LinuxBackend(), str(root))
    assert type(inspected) is WellFormedChain
    return inspected.entries[0][0], inspected.tip


def _store_record(store_id: str, genesis: str, head: str) -> verify.RegistryCarrier:
    return verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(
            anchors.StoreSubject(store_id), genesis, head, anchors.AnchorActOrigin("alice")
        )
    )


def _corpus_record(corpus_id: str, genesis: str, head: str) -> verify.RegistryCarrier:
    return verify.RegistryCarrier.from_record(
        anchors.LogHeadRecord(
            anchors.CorpusSubject(corpus_id), genesis, head, anchors.AnchorActOrigin("alice")
        )
    )


def _restore_store(root: Path, store_id: str, *carriers) -> verify.LogReport:
    return restore_root(root, anchors.StoreSubject(store_id), verify.ObserverSet(carriers), authority=FULL)


class TestStoreRestore:
    def test_malformed_copy_returns_malformed_and_stays_unserviceable(
        self, certified_work
    ):
        source, store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)
        # Interior chain damage: one entry's bytes no longer hash to its name.
        chain = replica / ".#~chain"
        victim = min(chain.iterdir())
        victim.chmod(0o600)
        victim.write_bytes(b"damaged interior bytes")

        genesis, head = _head_of(source)
        report = _restore_store(replica, store_id, _store_record(store_id, genesis, head))

        assert report.outcome == "malformed"
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_validated_store_copy_admits_read_only_serviceable(self, certified_work):
        source, store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)
        genesis, head = _head_of(source)

        report = _restore_store(replica, store_id, _store_record(store_id, genesis, head))

        assert report.outcome == "validated"
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_SERVICEABLE

    def test_re_restore_is_idempotent(self, certified_work):
        source, store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)
        genesis, head = _head_of(source)
        carrier = _store_record(store_id, genesis, head)

        first = _restore_store(replica, store_id, carrier)
        second = _restore_store(replica, store_id, carrier)

        assert first.outcome == second.outcome == "validated"
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_SERVICEABLE

    def test_validated_with_store_subject_mismatch_does_not_admit(self, certified_work):
        source, _store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)
        genesis, head = _head_of(source)
        # The raw-write license: an exported head artifact naming the presented
        # chain's digests under the selected, different store_id.
        artifact = anchors.head_artifact_bytes(
            anchors.HeadArtifact(anchors.StoreSubject(OTHER_STORE_ID), genesis, head)
        )
        carrier = verify.ArtifactCarrier.from_bytes(artifact)

        report = restore_root(
            replica, anchors.StoreSubject(OTHER_STORE_ID), verify.ObserverSet((carrier,))
        , authority=FULL)

        # Asserted, so replay refutation cannot discharge the arm vacuously.
        assert report.outcome == "validated"
        assert any(finding.code == "subject-mismatch" for finding in report.findings)
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_empty_observer_set_unresolvable_replay_not_reached(self, certified_work):
        source, store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)

        report = _restore_store(replica, store_id)

        assert report.outcome == "unresolvable"
        assert report.observer_bound == ()
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_incomplete_copy_never_validates(self, certified_work):
        source, store_id = _forked_form_store(certified_work)
        genesis, head = _detached_head(source)
        # The complete copy validates first, so the omission below is the
        # only difference the verdict can turn on.
        complete = certified_work / "complete"
        shutil.copytree(source, complete, symlinks=True)
        report = _restore_store(
            complete, store_id, _store_record(store_id, genesis, head)
        )
        assert report.outcome == "validated"

        incomplete = certified_work / "incomplete"
        shutil.copytree(source, incomplete, symlinks=True)
        # One payload file the chain's surface names, omitted — never chain
        # damage (the cut §6 obligation).
        (incomplete / "blob.bin").unlink()
        report = _restore_store(
            incomplete, store_id, _store_record(store_id, genesis, head)
        )

        assert report.outcome != "validated"
        assert read_lifecycle_state(incomplete) is LifecycleState.METADATA_LESS

    def test_validated_root_claim_residue_does_not_admit(self, certified_work):
        source, store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)
        (replica / ".#~root-claim").write_bytes(b"{}")
        genesis, head = _head_of(source)

        with pytest.raises(PreconditionRefused, match="claim"):
            _restore_store(replica, store_id, _store_record(store_id, genesis, head))
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_validated_staging_survivor_does_not_admit(self, certified_work):
        source, store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)
        (replica / ".#~chain" / ".#~stage").write_bytes(b"staged bytes")
        genesis, head = _head_of(source)

        # Even where evaluation is otherwise validated, the engine's
        # serviceability transition refuses the incomplete-creation residue,
        # loudly — the refusal propagates and no admission happens.
        with pytest.raises(PreconditionRefused, match="staging"):
            _restore_store(replica, store_id, _store_record(store_id, genesis, head))
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_two_copies_both_admit_read_only(self, certified_work):
        source, store_id = _seeded_store(certified_work)
        copies = []
        for name in ("copy-a", "copy-b"):
            copy = certified_work / name
            replicate_root(source, copy, authority=FULL)
            shutil.rmtree(metadata_root_for(copy))
            # The L10 u9 obligation: both roots are metadata-less first.
            assert read_lifecycle_state(copy) is LifecycleState.METADATA_LESS
            copies.append(copy)

        genesis, head = _head_of(source)
        carrier = _store_record(store_id, genesis, head)
        for copy in copies:
            report = _restore_store(copy, store_id, carrier)
            assert report.outcome == "validated"
            assert read_lifecycle_state(copy) is LifecycleState.READ_ONLY_SERVICEABLE
            with pytest.raises(PreconditionRefused, match="does not grant writability"):
                from atoms.coordinator.commands import append_intent

                append_intent(
                    LinuxBackend(),
                    str(copy),
                    str(metadata_root_for(copy)),
                    science_root.PRODUCTION_STORAGE,
                    b"a cooperative write",
                )

    def test_restore_never_grants_writability(self, certified_work):
        source, store_id = _seeded_store(certified_work)
        replica = certified_work / "replica"
        replicate_root(source, replica, authority=FULL)
        genesis, head = _head_of(source)
        _restore_store(replica, store_id, _store_record(store_id, genesis, head))

        assert read_lifecycle_state(replica) is not LifecycleState.WRITABLE
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_SERVICEABLE


class TestCorpusRestore:
    def _seeded_corpus(self, work: Path) -> Path:
        root = work / "corpus"
        init_corpus_root(root, authority=FULL)
        manifest = registry.manifest_bytes(registry.CorpusManifest(2, CORPUS_A, PINS))
        _executor(root).execute([CreateOp("corpus.yaml", manifest)])
        _executor(root).execute([CreateOp("verification/v1.md", b"# a record\n")])
        return root

    def test_validated_with_corpus_manifest_mismatch_does_not_admit(
        self, certified_work
    ):
        root = self._seeded_corpus(certified_work)
        # The slice-3 §1.2 case: the identity rewrite is cooperatively logged,
        # so replay validates and replay alone is not the guard.
        import hashlib

        original = registry.manifest_bytes(registry.CorpusManifest(2, CORPUS_A, PINS))
        rewritten = registry.manifest_bytes(registry.CorpusManifest(2, CORPUS_B, PINS))
        _executor(root).execute(
            [
                ReplaceOp(
                    "corpus.yaml",
                    rewritten,
                    hashlib.sha256(original).hexdigest(),
                )
            ]
        )
        replica = certified_work / "replica"
        replicate_root(root, replica, authority=FULL)
        genesis, head = _head_of(root)

        report = restore_root(
            replica,
            anchors.CorpusSubject(CORPUS_A),
            verify.ObserverSet((_corpus_record(CORPUS_A, genesis, head),)),
         authority=FULL)

        assert report.outcome == "validated"
        assert any(finding.code == "subject-mismatch" for finding in report.findings)
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_validated_corpus_copy_admits(self, certified_work):
        root = self._seeded_corpus(certified_work)
        replica = certified_work / "replica"
        replicate_root(root, replica, authority=FULL)
        genesis, head = _head_of(root)

        report = restore_root(
            replica,
            anchors.CorpusSubject(CORPUS_A),
            verify.ObserverSet((_corpus_record(CORPUS_A, genesis, head),)),
         authority=FULL)

        assert report.outcome == "validated"
        assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_SERVICEABLE


class TestTheHeldBoundary:
    def test_restore_holds_one_boundary_across_evaluate_and_grant(
        self, tmp_path, monkeypatch
    ):
        root = tmp_path / "store"
        (root / "artifacts").mkdir(parents=True)
        (root / "artifacts" / "head.json").write_bytes(b"{}")
        payload = science_root._store_genesis_payload("5" * 32, None)
        view = surfaced(root, "store", payload)
        inspections, captures = Inspections(), Captures()
        inspections.set(root, view)
        held = _operation_lock_for(root)
        observed: list[tuple[str, str]] = []

        def probe(label: str):
            def record(_root: Path) -> None:
                with pytest.raises(BuildContended), held.capture():
                    pass
                observed.append((label, str(held._holder)))

            return record

        inspections.probe = probe("inspect")
        captures.probe = probe("disk")
        real_records = verify.capture_records

        def capture_records(target: Path, kind: verify.RootKind):
            probe("records")(target)
            return real_records(target, kind)

        monkeypatch.setattr(verify, "capture_records", capture_records)
        granted: list[Path] = []

        def grant(target: Path) -> None:
            probe("grant")(target)
            granted.append(target)

        report = verify._restore_root(
            root,
            anchors.StoreSubject("5" * 32),
            verify.ObserverSet(
                (_store_record("5" * 32, view.genesis.digest, view.tip),)
            ),
            seam=make_seam(inspections, captures),
            grant=grant,
        )

        assert report.outcome == "validated"
        assert observed == [
            ("inspect", "writer"),
            ("disk", "writer"),
            ("records", "writer"),
            ("grant", "writer"),
        ]
        assert granted == [root.resolve()]
        assert held._holder is None


class TestDivergentCopies:
    def _divergent_pair(self, work: Path) -> tuple[Path, Path, str, str, str, str]:
        """Two self-consistent copies of one store, divergent after a common
        prefix: each carries a different raw-authored intent from the same
        tip."""
        source, store_id = _seeded_store(work)
        first = work / "copy-one"
        second = work / "copy-two"
        replicate_root(source, first, authority=FULL)
        replicate_root(source, second, authority=FULL)
        common_genesis, common_tip = _head_of(source)
        for copy, label in ((first, b"intent one"), (second, b"intent two")):
            envelope = encode_entry(common_tip, IntentEntry(label))
            leaf = copy / ".#~chain" / entry_digest(envelope)
            leaf.write_bytes(envelope)
        genesis_one, head_one = _detached_head(first)
        genesis_two, head_two = _detached_head(second)
        assert genesis_one == genesis_two == common_genesis
        assert head_one != head_two
        self.store_id = store_id
        return first, second, common_genesis, head_one, head_two, store_id

    def test_divergent_copies_assembled_in_one_root_are_sibling_malformed(
        self, certified_work
    ):
        first, second, genesis, head_one, head_two, store_id = self._divergent_pair(
            certified_work
        )
        # Assemble both tails in one chain directory: two successors of one
        # parent digest.
        shutil.copy(second / ".#~chain" / head_two, first / ".#~chain" / head_two)

        report = _restore_store(
            first, store_id, _store_record(store_id, genesis, head_one)
        )
        assert report.outcome == "malformed"
        assert read_lifecycle_state(first) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_both_divergent_heads_in_one_observer_set_refute(self, certified_work):
        first, _second, genesis, head_one, head_two, store_id = self._divergent_pair(
            certified_work
        )
        report = _restore_store(
            first,
            store_id,
            _store_record(store_id, genesis, head_one),
            _store_record(store_id, genesis, head_two),
        )
        assert report.outcome == "refuted"
        assert read_lifecycle_state(first) is LifecycleState.READ_ONLY_UNSERVICEABLE

    def test_divergent_copies_verified_separately_each_validate(self, certified_work):
        first, second, genesis, head_one, head_two, store_id = self._divergent_pair(
            certified_work
        )
        # The pinned surviving-observer negative IS the claim: with only its
        # own head supplied, each divergent copy validates — nothing in a
        # separate verification names the sibling head it cannot see.
        one = _restore_store(first, store_id, _store_record(store_id, genesis, head_one))
        two = _restore_store(second, store_id, _store_record(store_id, genesis, head_two))
        assert one.outcome == "validated"
        assert two.outcome == "validated"
        assert read_lifecycle_state(first) is LifecycleState.READ_ONLY_SERVICEABLE
        assert read_lifecycle_state(second) is LifecycleState.READ_ONLY_SERVICEABLE
