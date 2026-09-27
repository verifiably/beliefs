"""The engine facts the remote publish act relies on (publish-act-remote design
§4.2, §4.3; plan Task 0): a serviceable export root is plain files, its chain
head reads, and restore's evaluation, granting nothing, validates it intact and
refuses it with a selected record deleted or altered, writing nothing."""

from __future__ import annotations

import os
import shutil
import stat
from itertools import count
from pathlib import Path

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile
from nodes.core.frontmatter import node_to_markdown
from nodes.core.paths import path_for_node_id
from profiles import pins_for

from beliefs import stored
from beliefs.errors import LogEvidenceRefused
from beliefs.root import (
    LifecycleState,
    _log_seam,
    chain_head_reader,
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
from beliefs.world.anchors import CorpusSubject, decode_head_artifact
from beliefs.world.registry import load_manifest
from beliefs.world.verify import ArtifactCarrier, ObserverSet, _restore_root

V2 = coordination_profile(None, version=2)
_counter = count()


def _grant_nothing(_root: Path) -> None:
    """The evaluation's grant: none."""


def writable(root: Path) -> None:
    """Lift write permission on a serviceable root's tree (DAMAGE_WRITABLE)."""
    for path in (root, *root.rglob("*")):
        if not path.is_symlink():
            os.chmod(path, stat.S_IMODE(path.stat().st_mode) | stat.S_IWUSR)


@pytest.fixture()
def exported(certified_work):
    """A two-record corpus admitted into its own world, exported, replicated and
    restored: a serviceable export root beside its sibling, as step 6 leaves it."""
    stem = certified_work / f"publish-remote-engine-{os.getpid()}-{next(_counter)}"
    corpus, world_root, container = stem / "staging", stem / "world", stem / "export"
    container.mkdir(parents=True)
    try:
        init_corpus_root(corpus, authority=FULL)
        writer = open_corpus(corpus, authority=FULL, profile=V2)
        writer.adopt_manifest(profile=pins_for(V2))
        records = [stored.run_node(name, title=name, spec="s", produces=[]) for name in ("a", "b")]
        for node in records:
            writer._stage_record(node_to_markdown(node))
        corpus_id = load_manifest(corpus).corpus_id
        config = WorldConfig(world_root, "e" * 32, (corpus,))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        world.admit(corpus, provenance=Fresh())
        artifact = export_head_artifact(world, CorpusSubject(corpus_id))
        export = container / corpus_id
        (container / f"{corpus_id}.head-artifact.v1").write_bytes(artifact)
        replicate_root(corpus, export, authority=FULL)
        observers = ObserverSet((ArtifactCarrier.from_bytes(artifact),))
        assert restore_root(export, CorpusSubject(corpus_id), observers, authority=FULL).outcome == "validated"
        yield export, corpus_id, observers, artifact, records
    finally:
        for path in (corpus, world_root, stem / "export"):
            if path.exists():
                writable(path)
            shutil.rmtree(path, ignore_errors=True)
            shutil.rmtree(metadata_root_for(path), ignore_errors=True)
        for leftover in container.glob("*.metadata") if container.exists() else ():
            shutil.rmtree(leftover, ignore_errors=True)
        shutil.rmtree(stem, ignore_errors=True)


def _evaluate(export: Path, corpus_id: str, observers: ObserverSet) -> str:
    return _restore_root(export, CorpusSubject(corpus_id), observers, seam=_log_seam(), grant=_grant_nothing).outcome


def _tree(root: Path) -> list[tuple[str, bytes | None]]:
    return sorted((str(p.relative_to(root)), p.read_bytes() if p.is_file() else None) for p in root.rglob("*"))


def test_a_serviceable_export_root_holds_only_directories_and_regular_files(exported):
    """EXPORT_LAYOUT, and CHAIN_DIR printed for Task 8's Y16-a sabotage."""
    export, *_ = exported
    for directory, dirnames, filenames in os.walk(export):
        for name in (*dirnames, *filenames):
            path = Path(directory) / name
            assert not path.is_symlink() and (path.is_dir() or path.is_file()), path
    print("TOP LEVEL =", sorted(p.name for p in export.iterdir()))


def test_the_chain_head_reads_a_serviceable_export(exported):
    """CHAIN_HEAD_SERVICEABLE: the sibling's genesis and head are the export's chain head."""
    export, corpus_id, _, artifact, _ = exported
    decoded = decode_head_artifact(artifact)
    assert decoded.subject == CorpusSubject(corpus_id)
    assert (decoded.genesis, decoded.head) == chain_head_reader()(export)


def test_the_evaluation_validates_an_intact_serviceable_export(exported):
    """EVALUATE_INTACT: the no-grant evaluation over a root already serviceable."""
    export, corpus_id, observers, _, _ = exported
    assert _evaluate(export, corpus_id, observers) == "validated"


def test_the_evaluation_writes_nothing(exported):
    """EVALUATE_WRITES_NOTHING: the tree, its metadata sibling and the lifecycle state are unchanged."""
    export, corpus_id, observers, _, _ = exported
    before = (_tree(export), _tree(metadata_root_for(export)), read_lifecycle_state(export))
    _evaluate(export, corpus_id, observers)
    assert (_tree(export), _tree(metadata_root_for(export)), read_lifecycle_state(export)) == before
    assert read_lifecycle_state(export) is LifecycleState.READ_ONLY_SERVICEABLE


def test_the_evaluation_refuses_a_deleted_selected_record(exported):
    """EVALUATE_DELETED, and DAMAGE_WRITABLE: lifting write permission is enough to damage it."""
    export, corpus_id, observers, _, records = exported
    writable(export)
    (export / path_for_node_id(records[0].id)).unlink()
    assert _evaluate(export, corpus_id, observers) != "validated"


def test_the_evaluation_refuses_an_altered_selected_record(exported):
    """EVALUATE_ALTERED."""
    export, corpus_id, observers, _, records = exported
    writable(export)
    path = export / path_for_node_id(records[0].id)
    path.write_bytes(path.read_bytes() + b"\n")
    assert _evaluate(export, corpus_id, observers) != "validated"


@pytest.mark.parametrize("damage", ["unreadable", "undecodable"])
def test_the_evaluation_over_an_unreadable_or_undecodable_record(exported, damage):
    """EVALUATE_UNREADABLE and EVALUATE_UNDECODABLE: an outcome other than
    `validated`, or the exception type printed for `root.py` to translate."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 files")
    export, corpus_id, observers, _, records = exported
    writable(export)
    path = export / path_for_node_id(records[0].id)
    if damage == "unreadable":
        path.chmod(0)
    else:
        path.write_bytes(b"\x00\xffnot a record")
    try:
        outcome = _evaluate(export, corpus_id, observers)
    except LogEvidenceRefused as caught:  # unreadable record is an engine refusal
        print(f"EVALUATE_{damage.upper()} raises {type(caught).__module__}.{type(caught).__qualname__}")
    else:
        print(f"EVALUATE_{damage.upper()} answers {outcome}")
        assert outcome != "validated"
    finally:
        path.chmod(0o644)


def test_a_damaged_chain_raises_from_the_chain_head(exported):
    """CHAIN_HEAD_DAMAGED: the type `root.export_chain_head` translates."""
    export, *_ = exported
    writable(export)
    chain = export / ".#~chain"  # CHAIN_DIR, as the layout probe prints it
    victim = next(p for p in sorted(chain.rglob("*")) if p.is_file())
    victim.write_bytes(b"garbage")
    with pytest.raises(Exception) as caught:  # a probe: the type is the finding
        chain_head_reader()(export)
    print(f"CHAIN_HEAD_DAMAGED = {type(caught.value).__module__}.{type(caught.value).__qualname__}")


@pytest.mark.parametrize("damage", ["deleted", "unreadable"])
def test_a_missing_or_unreadable_chain_raises_from_the_chain_head(exported, damage):
    """CHAIN_HEAD_DELETED and CHAIN_HEAD_UNREADABLE (the round-2 reviewer saw
    `PreconditionRefused` for both), and EVALUATE_CHAIN_DELETED."""
    if damage == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-0 directories")
    export, corpus_id, observers, _, _ = exported
    writable(export)
    chain = export / ".#~chain"
    if damage == "deleted":
        shutil.rmtree(chain)
    else:
        chain.chmod(0)
    try:
        with pytest.raises(Exception) as caught:  # a probe: the type is the finding
            chain_head_reader()(export)
        print(f"CHAIN_HEAD_{damage.upper()} = {type(caught.value).__module__}.{type(caught.value).__qualname__}")
        if damage == "deleted":
            outcome = _evaluate(export, corpus_id, observers)
            print(f"EVALUATE_CHAIN_DELETED answers {outcome}")
            assert outcome != "validated"
    finally:
        if chain.exists():
            chain.chmod(0o755)
