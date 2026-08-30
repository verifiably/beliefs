"""Fork-of admission and `admit_arrival`'s inspection modes (plan Task 8).

Real engine throughout: worlds and corpora are initialized through their own
acts on the certified volume, the grant in the writable-refusal arm is
`register_root`'s own (cut §6 — never fabricated bookkeeping), and the modes
are observed by wrapping the production seam's two inspection slots with a
recorder that delegates.
"""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path

import pytest

from beliefs import root as science_root
from beliefs.errors import CorpusRootRefused
from beliefs.root import (
    LifecycleState,
    admit_arrival,
    fork_corpus,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.world import anchors, registry, verify

WORLD_ID = "f" * 32
PARENT_ID = "a1" * 16
_OTHER_MACHINE = "e" * 32


def _parent_corpus(work: Path, name: str = "parent") -> Path:
    """A registered parent whose whole surface is log-covered: the manifest
    and the one record are authored through the durable executor, so a copy
    of this root replays clean — which is what lets the arrival arms turn on
    the *mode*, not on a replay verdict."""
    from fixtures_cut6 import PINS
    from nodes.core.frontmatter import node_to_markdown
    from nodes.core.node import Node
    from nodes.core.write_plan import CreateOp

    root = work / name
    init_corpus_root(root)
    executor = science_root.durable_executor_factory()(root)
    executor.execute(
        [
            CreateOp(
                "corpus.yaml",
                registry.manifest_bytes(registry.CorpusManifest(2, PARENT_ID, PINS)),
            )
        ]
    )
    record = node_to_markdown(
        Node(
            id="note:seed",
            uid="1" * 32,
            kind="note",
            title="the seeded record",
            facets={},
        )
    ).encode("utf-8")
    executor.execute([CreateOp("note/seed.md", record)])
    return root


def _world_over(work: Path, name: str, *roots: Path):
    config = science_root.WorldConfig(work / name, WORLD_ID, tuple(roots))
    init_world_root(config)
    return open_world(config)


def _recording_seam(monkeypatch) -> list[str]:
    production = science_root._log_seam()
    calls: list[str] = []

    def registered(root: Path):
        calls.append("registered")
        return production.inspect_registered(root)

    def detached(root: Path):
        calls.append("detached")
        return production.inspect_detached(root)

    recording = verify.LogSeam(
        inspect_registered=registered,
        inspect_detached=detached,
        capture=production.capture,
        read_head=production.read_head,
        absent_state=production.absent_state,
        world_lock=production.world_lock,
        corpus_lock=production.corpus_lock,
        lifecycle_state=production.lifecycle_state,
    )
    monkeypatch.setattr(science_root, "_LOG_SEAM", recording)
    return calls


def _arrive(world, root: Path):
    return admit_arrival(
        world,
        root,
        registry.ReplicaOf(PARENT_ID),
        verify.ObserverSet(()),
        actor="alice",
    )


def test_fork_product_admits_through_the_fork_of_path(certified_work):
    parent = _parent_corpus(certified_work)
    child = certified_work / "child"
    world = _world_over(certified_work, "world", parent, child)
    world.admit(parent, provenance=registry.Fresh(), actor="alice")

    minted = fork_corpus(parent, child)
    assert minted.forked_from is not None
    record = world.admit(
        child,
        provenance=registry.ForkOf(
            minted.forked_from.corpus_id, minted.forked_from.corpus_state
        ),
        actor="alice",
    )

    assert record.corpus_id == minted.corpus_id
    # No fixture-authored manifest anywhere: what the world admitted is what
    # the fork act installed.
    assert registry.load_manifest(child).corpus_id == minted.corpus_id


def test_arrival_registered_mode_on_serviceable(certified_work, monkeypatch):
    parent = _parent_corpus(certified_work)
    replica = certified_work / "replica"
    replicate_root(parent, replica)
    genesis, head = science_root.chain_head_reader()(parent)
    restore_root(
        replica,
        anchors.CorpusSubject(PARENT_ID),
        verify.ObserverSet(
            (
                verify.RegistryCarrier.from_record(
                    anchors.LogHeadRecord(
                        anchors.CorpusSubject(PARENT_ID),
                        genesis,
                        head,
                        anchors.AnchorActOrigin("alice"),
                    )
                ),
            )
        ),
    )
    assert read_lifecycle_state(replica) is LifecycleState.READ_ONLY_SERVICEABLE

    world = _world_over(certified_work, "world", replica)
    calls = _recording_seam(monkeypatch)
    record, _report = _arrive(world, replica)

    assert record.corpus_id == PARENT_ID
    assert "registered" in calls
    assert "detached" not in calls


def test_arrival_detached_on_unserviceable_metadata_less_and_mismatched(
    certified_work, monkeypatch
):
    parent = _parent_corpus(certified_work)

    # Unserviceable: a completed replica, unrestored.
    unserviceable = certified_work / "unserviceable"
    replicate_root(parent, unserviceable)
    assert read_lifecycle_state(unserviceable) is LifecycleState.READ_ONLY_UNSERVICEABLE

    # Metadata-less: a raw copy without its sibling.
    cold = certified_work / "cold"
    shutil.copytree(parent, cold, symlinks=True)
    assert read_lifecycle_state(cold) is LifecycleState.METADATA_LESS

    # Binding-mismatched: a replica moved after its stamp — the path half of
    # the binding delta, so nothing global changes under the other roots.
    placed = certified_work / "placed"
    replicate_root(parent, placed)
    mismatched = certified_work / "mismatched"
    shutil.move(placed, mismatched)
    shutil.move(metadata_root_for(placed), metadata_root_for(mismatched))
    assert read_lifecycle_state(mismatched) is LifecycleState.BINDING_MISMATCHED

    for index, root in enumerate((unserviceable, cold, mismatched)):
        world = _world_over(certified_work, f"world-{index}", root)
        calls = _recording_seam(monkeypatch)
        _arrive(world, root)
        assert calls and "registered" not in calls
        monkeypatch.undo()


def test_arrival_refuses_a_writable_root(certified_work):
    parent = _parent_corpus(certified_work)
    # The grant is register_root's own (cut §6), read back before the arm.
    assert read_lifecycle_state(parent) is LifecycleState.WRITABLE
    world = _world_over(certified_work, "world", parent)

    with pytest.raises(CorpusRootRefused, match="writable"):
        _arrive(world, parent)


def test_restored_arrival_requires_restore_first(certified_work, monkeypatch):
    parent = _parent_corpus(certified_work)
    copy = certified_work / "copy"
    shutil.copytree(parent, copy, symlinks=True)

    first_world = _world_over(certified_work, "world-before", copy)
    calls = _recording_seam(monkeypatch)
    _arrive(first_world, copy)
    assert calls == ["detached"]
    monkeypatch.undo()

    genesis, head = science_root.chain_head_reader()(parent)
    restore_root(
        copy,
        anchors.CorpusSubject(PARENT_ID),
        verify.ObserverSet(
            (
                verify.RegistryCarrier.from_record(
                    anchors.LogHeadRecord(
                        anchors.CorpusSubject(PARENT_ID),
                        genesis,
                        head,
                        anchors.AnchorActOrigin("alice"),
                    )
                ),
            )
        ),
    )
    assert read_lifecycle_state(copy) is LifecycleState.READ_ONLY_SERVICEABLE

    second_world = _world_over(certified_work, "world-after", copy)
    calls = _recording_seam(monkeypatch)
    _arrive(second_world, copy)
    assert calls == ["registered"]


def test_store_subject_unspellable_at_arrival():
    # Label 8's corpus-only negative: the arrival act's provenance is typed
    # ReplicaOf, and neither its signature nor its runtime accepts a store.
    parameters = inspect.signature(admit_arrival).parameters
    assert str(parameters["provenance"].annotation) == "ReplicaOf"
    assert "store" not in str(parameters)
    with pytest.raises(TypeError, match="replica"):
        admit_arrival(
            object(),  # type: ignore[arg-type]
            Path("nowhere"),
            anchors.StoreSubject("5" * 32),  # type: ignore[arg-type]
            verify.ObserverSet(()),
            actor="alice",
        )
