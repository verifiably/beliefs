"""The certified-tuple gate.

Everything under `tests/acceptance` runs against the **real engine on a real
volume**, and the gate below **errors** when that volume's configuration tuple
is not certified. It never skips, and the distinction is the whole point: a
skip reports green for a guarantee that was not exercised, and an environment
where durability cannot be exercised must not be able to report cut-4 discharge.

**The work directory has to sit on the certified volume**, which the platform
temporary directory generally does not — `/tmp` is a tmpfs on most hosts, and a
tmpfs has no barrier-option table at all. So the default is a directory beside
the checkout, and `SCIENCE_CUT4_ROOT` overrides it for a host that keeps its
certified volume elsewhere.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from itertools import count
from pathlib import Path

import pytest
from authority import FULL

from beliefs.root import (
    init_corpus_root,
    init_world_root,
    metadata_root_for,
    open_corpus,
    open_world,
)
from beliefs.world import Fresh, WorldConfig

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORK = REPO_ROOT / ".cut4-acceptance"

_counter = count()


class UncertifiedVolume(Exception):
    """The acceptance run's own error, raised rather than skipped."""


@pytest.fixture(scope="session")
def work_directory() -> Path:
    """The shared directory the per-test roots live under.

    **It is created and never removed here.** Concurrent acceptance processes
    share it — the N2 audit runs a `pytest` per check, eight at a time — and a
    session teardown that deleted the directory would delete the roots of every
    other process still running. Each root cleans up after itself; the work
    directory is the acceptance command's to remove.
    """
    configured = os.environ.get("SCIENCE_CUT4_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


@pytest.fixture()
def durable_root(work_directory) -> Iterator[Path]:
    """A registered corpus root on the certified volume, or a loud failure.

    The registration is the acceptance run's own smoke test: `init_corpus_root`
    reaches the engine's volume binding, so an uncertified tuple fails here,
    once, with the engine's own words rather than as a puzzling refusal inside
    some later assertion.
    """
    root = work_directory / f"corpus-{os.getpid()}-{next(_counter)}"
    try:
        init_corpus_root(root, authority=FULL)
    except Exception as refused:
        raise UncertifiedVolume(
            f"the durable acceptance arms need a certified volume under {work_directory}; "
            f"the engine refused: {refused}. Set SCIENCE_CUT4_ROOT to a certified volume. "
            "This is an error and not a skip: an environment that cannot exercise durability "
            "must not be able to report cut-4 discharge."
        ) from refused
    yield root
    shutil.rmtree(root, ignore_errors=True)
    shutil.rmtree(metadata_root_for(root), ignore_errors=True)


@pytest.fixture()
def durable_writer(durable_root):
    """The composition root's own product, bound to a registered root."""
    return open_corpus(durable_root, authority=FULL)


@pytest.fixture()
def durable_coordination_roots(work_directory, base_contract):
    from coordination_fixtures import coordination_profile, pins_for

    profile = coordination_profile(base_contract)
    roots = tuple(
        work_directory / f"coordination-{os.getpid()}-{next(_counter)}-{side}"
        for side in ("left", "right")
    )
    try:
        for root in roots:
            init_corpus_root(root, authority=FULL)
            open_corpus(root, authority=FULL).adopt_manifest(profile=pins_for(profile))
        yield roots, profile
    finally:
        for root in roots:
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


@pytest.fixture()
def durable_coordination_world(work_directory, durable_coordination_roots):
    (corpus_root, _), profile = durable_coordination_roots
    world_root = work_directory / f"coordination-world-{os.getpid()}-{next(_counter)}"
    config = WorldConfig(world_root, "e" * 32, (corpus_root,))
    try:
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(corpus_root, provenance=Fresh())
        yield world, corpus_root, profile
    finally:
        shutil.rmtree(world_root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(world_root), ignore_errors=True)


@pytest.fixture(scope="session")
def minted_corpus(work_directory) -> Iterator[Path]:
    """Cut 4's fixture records, minted **once** through the add path into one
    registered root and never written to again.

    Shared by the read-only arms, which is what they are: every one of them
    reopens the store from disk. An arm that writes — the raw-write act, a
    second mint — takes its own root instead, so no arm can observe another's
    construction.
    """
    from durable_fixture import mint_cut4_corpus

    root = work_directory / f"minted-{os.getpid()}"
    try:
        init_corpus_root(root, authority=FULL)
    except Exception as refused:
        raise UncertifiedVolume(
            f"the durable acceptance arms need a certified volume under {work_directory}; "
            f"the engine refused: {refused}"
        ) from refused
    mint_cut4_corpus(open_corpus(root, authority=FULL))
    yield root
    shutil.rmtree(root, ignore_errors=True)
    shutil.rmtree(metadata_root_for(root), ignore_errors=True)


class ConfinementUnavailableHost(Exception):
    """The confined arms' own error, raised rather than skipped."""


@pytest.fixture()
def confined_host() -> None:
    """The confinement gate: bubblewrap with --info-fd, unprivileged user
    namespaces, and the loader's --list. It errors and never skips — an
    environment that cannot exercise confinement must not be able to report
    cut-13 discharge. No durable root is involved."""
    from beliefs.confinement import host_prerequisites

    reason = host_prerequisites()
    if reason is not None:
        raise ConfinementUnavailableHost(
            f"the confined acceptance arms need bubblewrap and user namespaces on this host; {reason}. "
            "This is an error and not a skip."
        )
