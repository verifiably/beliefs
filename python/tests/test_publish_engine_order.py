"""The engine facts the publish act's resumption relies on (publish-act-local
design §2 decision 8, §9): each reinvoked lifecycle operation converges on the
state its first call left. Tests may import `atoms`; the source modules do not."""

from __future__ import annotations

import os
import shutil
from itertools import count

import pytest
from authority import FULL
from profiles import BASE, pins_for

from beliefs.corpus import ReadView
from beliefs.root import (
    LifecycleState,
    export_head_artifact,
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    open_corpus,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.world import Fresh, WorldConfig
from beliefs.world.anchors import CorpusSubject
from beliefs.world.registry import load_manifest
from beliefs.world.verify import ArtifactCarrier, ObserverSet

_counter = count()


@pytest.fixture()
def staged(certified_work):
    """A corpus admitted into its own one-carrier world, as step 1 builds it."""
    stem = certified_work / f"publish-engine-{os.getpid()}-{next(_counter)}"
    corpus, world_root, export = stem / "staging", stem / "world", stem / "dest" / "exported"
    (stem / "dest").mkdir(parents=True)
    try:
        init_corpus_root(corpus, authority=FULL)
        open_corpus(corpus, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
        config = WorldConfig(world_root, "e" * 32, (corpus,))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(corpus, provenance=Fresh())
        yield corpus, config, world, export
    finally:
        for path in (corpus, world_root, export):
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)
        shutil.rmtree(stem, ignore_errors=True)


def test_init_retry_converges(staged):
    """INIT_RETRY: both initializers, reinvoked, change nothing and raise nothing."""
    corpus, config, _, _ = staged
    init_corpus_root(corpus, authority=FULL)
    init_world_root(config, authority=FULL)
    open_world(config, authority=FULL)


def test_admit_retry_converges(staged):
    """ADMIT_RETRY: the same fresh adoption again returns an equal record."""
    corpus, config, _, _ = staged
    again = open_world(config, authority=FULL).admit(corpus, provenance=Fresh())
    assert again.manifest.corpus_id == load_manifest(corpus).corpus_id


def test_export_is_stable(staged):
    """EXPORT_STABLE: a pure function of the chain."""
    corpus, _, world, _ = staged
    subject = CorpusSubject(load_manifest(corpus).corpus_id)
    assert export_head_artifact(world, subject) == export_head_artifact(world, subject)


def test_replicate_retry_after_completion_converges(staged):
    """REPLICATE_RETRY: a completed replication, retried exactly, returns the
    same operation id and leaves the replica read-only and unserviceable."""
    corpus, _, _, export = staged
    first = replicate_root(corpus, export, authority=FULL)
    second = replicate_root(corpus, export, authority=FULL)
    assert first == second
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_UNSERVICEABLE


def test_replicate_retry_after_restore_converges(staged):
    """REPLICATE_AFTER_RESTORE: a replication retried exactly after its copy was
    restored returns the same operation id and leaves the copy serviceable —
    the resume after a crash past step 6 reinvokes it (finding 2)."""
    corpus, _, world, export = staged
    corpus_id = load_manifest(corpus).corpus_id
    artifact = export_head_artifact(world, CorpusSubject(corpus_id))
    first = replicate_root(corpus, export, authority=FULL)
    restore_root(export, CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(artifact),)), authority=FULL)
    assert replicate_root(corpus, export, authority=FULL) == first
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_SERVICEABLE


def test_replicate_over_a_foreign_serviceable_root_refuses(staged, certified_work):
    """FOREIGN_REPLICA: another corpus's replica at the export path (read-only,
    not yet restored) refuses this replication. The exception type is recorded for Task 8."""
    corpus, _, _, export = staged
    other = certified_work / f"publish-engine-foreign-{os.getpid()}-{next(_counter)}"
    try:
        init_corpus_root(other, authority=FULL)
        open_corpus(other, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
        replicate_root(other, export, authority=FULL)
        with pytest.raises(Exception) as refused:
            replicate_root(corpus, export, authority=FULL)
        print(f"FOREIGN_REPLICA = {type(refused.value).__module__}.{type(refused.value).__name__}")
    finally:
        shutil.rmtree(other, ignore_errors=True)
        shutil.rmtree(metadata_root_for(other), ignore_errors=True)


def test_a_restored_replica_reads_and_stays_serviceable(staged):
    """READ_SERVICEABLE: restore against the exported artifact validates, and a
    ReadView opens the serviceable copy (admit_publication's read)."""
    corpus, _, world, export = staged
    corpus_id = load_manifest(corpus).corpus_id
    artifact = export_head_artifact(world, CorpusSubject(corpus_id))
    replicate_root(corpus, export, authority=FULL)
    report = restore_root(
        export, CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(artifact),)), authority=FULL
    )
    assert report.outcome == "validated"
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_SERVICEABLE
    assert tuple(ReadView.opened_at(export).iter_stored()) == ()
