"""The world registry through the certified composition root: initialization recovery and registered paths."""

from __future__ import annotations

import os
import shutil
from itertools import count

import pytest
from atoms.chain.model import RegisteredEntry
from atoms.core.errors import PreconditionRefused
from authority import FULL
from fixtures_cut6 import PINS
from profiles import WITH_BIOLOGY
from test_durable_families import chain_entries

from beliefs import root
from beliefs.world import Fresh, WorldConfig, admission_digest, status_digest

_COUNTER = count()


@pytest.fixture()
def world_case(work_directory):
    suffix = f"{os.getpid()}-{next(_COUNTER)}"
    world_root = work_directory / f"world-{suffix}"
    corpus_root = work_directory / f"corpus-{suffix}"
    config = WorldConfig(world_root, "6" * 32, (corpus_root,))
    try:
        root.init_world_root(config, authority=FULL)
        assert {path.name for path in world_root.iterdir()} == {".#~chain", "world.yaml"}
        root.init_corpus_root(corpus_root, authority=FULL)
        root.open_corpus(corpus_root, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
        assert not any((world_root / name).exists() for name in ("registry", "epochs", "rules"))
        before_admission = chain_entries(world_root)
        world = root.open_world(config, authority=FULL)
        admission = world.admit(corpus_root, provenance=Fresh())
        assert (world_root / "registry").is_dir()
        assert not any((world_root / name).exists() for name in ("epochs", "rules"))
        yield {
            "world": world,
            "world_root": world_root,
            "admission": admission,
            "before_admission": before_admission,
            "after_admission": chain_entries(world_root),
            "corpus_entries": chain_entries(corpus_root),
        }
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(world_root), ignore_errors=True)
        shutil.rmtree(corpus_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(corpus_root), ignore_errors=True)


def _registrations(entries):
    return tuple(entry for _, entry in entries if isinstance(entry, RegisteredEntry))


def test_world_initialization_recovers_between_genesis_and_mirror(work_directory, monkeypatch):
    suffix = f"{os.getpid()}-{next(_COUNTER)}"
    world_root = work_directory / f"crash-world-{suffix}"
    config = WorldConfig(world_root, "7" * 32, ())
    execute = root.DurableExecutor.execute
    raised = False

    def crash_once(self, plan):
        nonlocal raised
        if not raised:
            raised = True
            raise RuntimeError("crash before mirror transaction")
        return execute(self, plan)

    try:
        monkeypatch.setattr(root.DurableExecutor, "execute", crash_once)
        with pytest.raises(RuntimeError, match="crash before mirror"):
            root.init_world_root(config, authority=FULL)
        assert (world_root / ".#~chain").is_dir()
        assert not (world_root / "world.yaml").exists()
        monkeypatch.setattr(root.DurableExecutor, "execute", execute)
        root.init_world_root(config, authority=FULL)
        entries = chain_entries(world_root)
        root.init_world_root(config, authority=FULL)
        assert chain_entries(world_root) == entries
        with pytest.raises(PreconditionRefused):
            root.init_world_root(WorldConfig(world_root, "8" * 32, ()), authority=FULL)
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(world_root), ignore_errors=True)


def test_world_mirror_registration_names_world_yaml(world_case):
    (registration,) = _registrations(world_case["before_admission"])
    assert "world.yaml" in dict(registration.final)


def test_manifest_registration_names_corpus_yaml(world_case):
    (registration,) = _registrations(world_case["corpus_entries"])
    assert "corpus.yaml" in dict(registration.final)


def test_registry_registrations_name_each_record_path(world_case):
    added = world_case["after_admission"][len(world_case["before_admission"]) :]
    (registration,) = _registrations(added)
    admission = world_case["admission"]
    assert set(dict(registration.final)) == {f"registry/{admission_digest(admission)}.yaml"}

    before_status = chain_entries(world_case["world_root"])
    status = world_case["world"].retire(admission.corpus_id)
    (status_registration,) = _registrations(chain_entries(world_case["world_root"])[len(before_status) :])
    assert set(dict(status_registration.final)) == {f"registry/{status_digest(status)}.yaml"}
