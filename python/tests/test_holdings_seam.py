"""The holdings store seam over the durable engine commands."""

from __future__ import annotations

import shutil
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from atoms.coordinator.commands import ReadUnestablished, UnestablishedReason
from atoms.core.effects import CreateDirectory, CreateFileNoClobber, DeletePath, MoveNoClobber, ReplaceFile
from atoms.core.fingerprint import ABSENT, DirectoryState, FileState
from authority import FULL
from nodes.core.errors import ExecutionError
from nodes.core.write_plan import CreateOp

from beliefs import root as science_root
from beliefs.holdings.seam import (
    AbsentStateView,
    FileStateView,
    NonRegularStateView,
    PathObservedView,
    ReadNotAttemptedView,
    ReadUnestablishedView,
)
from beliefs.identity import v1
from beliefs.root import (
    CREATED_DIRECTORY_MODE,
    CREATED_FILE_MODE,
    STORE_CONSUMER_TAG,
    STORE_WRITE_INTENT_DOMAIN,
    DurableExecutor,
    holdings_seam,
    init_store_root,
    replicate_root,
)

TXID = "1" * 32


def _store(work, name="store"):
    root = work / name
    init_store_root(root, authority=FULL)
    return root


def test_read_path_answers_found_with_the_content_hash(certified_work):
    root = _store(certified_work)
    payload = b"held bytes"
    seam = holdings_seam()
    seam.store_write(root, "payload.bin", payload)

    assert seam.read_path(root, "payload.bin") == PathObservedView(
        FileStateView("sha256:" + sha256(payload).hexdigest())
    )


def test_read_path_answers_absent_for_a_missing_path(certified_work):
    root = _store(certified_work)

    assert holdings_seam().read_path(root, "missing.bin") == PathObservedView(AbsentStateView())


def test_read_path_reports_a_directory_as_non_regular(certified_work):
    root = _store(certified_work)
    seam = holdings_seam()
    seam.store_write(root, "directory/payload.bin", b"held bytes")

    assert seam.read_path(root, "directory") == PathObservedView(NonRegularStateView("directory"))


def test_read_path_on_a_metadata_less_root_is_not_attempted(certified_work):
    source = _store(certified_work)
    cold = certified_work / "cold"
    shutil.copytree(source, cold, symlinks=True)

    assert holdings_seam().read_path(cold, "missing.bin") == ReadNotAttemptedView(
        reason="lifecycle-state",
        lifecycle_state="metadata-less",
        detail="",
    )


def test_store_write_returns_the_verified_final_surface(certified_work):
    root = _store(certified_work)
    payload = b"held bytes"

    outcome = holdings_seam().store_write(root, "directory/payload.bin", payload)

    assert len(outcome.txid) == 32
    assert outcome.final_states == (
        ("directory", NonRegularStateView("directory")),
        ("directory/payload.bin", FileStateView("sha256:" + sha256(payload).hexdigest())),
    )


def test_store_delete_returns_the_absent_row(certified_work):
    root = _store(certified_work)
    seam = holdings_seam()
    seam.store_write(root, "payload.bin", b"held bytes")

    outcome = seam.store_delete(root, "payload.bin")

    assert outcome.final_states == (("payload.bin", AbsentStateView()),)


def test_store_move_returns_the_dual_location_result(certified_work):
    root = _store(certified_work)
    payload = b"held bytes"
    seam = holdings_seam()
    seam.store_write(root, "source.bin", payload)

    outcome = seam.store_move(root, "source.bin", "destination.bin")

    assert outcome.final_states == (
        ("destination.bin", FileStateView("sha256:" + sha256(payload).hexdigest())),
        ("source.bin", AbsentStateView()),
    )


def test_store_mutation_on_an_ungranted_root_refuses(certified_work):
    source = _store(certified_work)
    replica = certified_work / "replica"
    replicate_root(source, replica, authority=FULL)

    with pytest.raises(ExecutionError):
        holdings_seam().store_write(replica, "payload.bin", b"held bytes")


def test_the_seam_is_a_singleton():
    assert holdings_seam() is holdings_seam()


@pytest.mark.parametrize("operation", ["create", "replace", "delete", "move"])
def test_store_commands_submit_the_exact_protocol_contract(tmp_path, monkeypatch, operation):
    root = tmp_path / "store"
    root.mkdir()
    payload = b"new bytes"
    old = b"old bytes"
    old_hash = sha256(old).hexdigest()
    post = FileState("sha256:" + sha256(payload).hexdigest(), CREATED_FILE_MODE, len(payload))
    pre = FileState("sha256:" + old_hash, 0o600, len(old))
    captured = []

    def capture(**kwargs):
        captured.append(kwargs)
        spec = kwargs["spec"]
        return SimpleNamespace(
            txid=TXID,
            final_states=tuple((row.path, row.state) for row in spec.final_surface),
        )

    monkeypatch.setattr(science_root, "_mapped_submit", capture)
    seam = holdings_seam()
    if operation == "create":
        path = "directory/payload.bin"
        outcome = seam.store_write(root, path, payload)
        projection = [{"op": "write", "path": path, "content_sha256": sha256(payload).hexdigest()}]
        registered = (path,)
        effect_types = (CreateDirectory, CreateFileNoClobber)
        initial = (("directory", ABSENT), (path, ABSENT))
        final = (("directory", DirectoryState(CREATED_DIRECTORY_MODE)), (path, post))
    else:
        source = root / "source.bin"
        source.write_bytes(old)
        source.chmod(0o600)
        if operation == "replace":
            outcome = seam.store_write(root, "source.bin", payload)
            projection = [
                {
                    "op": "write",
                    "path": "source.bin",
                    "content_sha256": sha256(payload).hexdigest(),
                    "expected_digest": old_hash,
                }
            ]
            registered = ("source.bin",)
            effect_types = (ReplaceFile,)
            initial = (("source.bin", pre),)
            final = (("source.bin", post),)
        elif operation == "delete":
            outcome = seam.store_delete(root, "source.bin")
            projection = [{"op": "delete", "path": "source.bin", "expected_digest": old_hash}]
            registered = ("source.bin",)
            effect_types = (DeletePath,)
            initial = (("source.bin", pre),)
            final = (("source.bin", ABSENT),)
        else:
            outcome = seam.store_move(root, "source.bin", "destination.bin")
            projection = [
                {
                    "op": "move",
                    "source": "source.bin",
                    "destination": "destination.bin",
                    "expected_digest": old_hash,
                }
            ]
            registered = ("destination.bin", "source.bin")
            effect_types = (MoveNoClobber,)
            initial = (("destination.bin", ABSENT), ("source.bin", pre))
            final = (("destination.bin", pre), ("source.bin", ABSENT))

    assert len(captured) == 1
    spec = captured[0]["spec"]
    payloads = captured[0]["payloads"]
    assert spec.consumer_tag == STORE_CONSUMER_TAG
    assert spec.intent_digest == "sha256:" + v1.digest(STORE_WRITE_INTENT_DOMAIN, projection)
    assert spec.fulfills is None
    assert spec.registered_paths == registered
    assert tuple(type(effect) for effect in spec.effects) == effect_types
    assert tuple((row.path, row.state) for row in spec.initial_surface) == initial
    assert tuple((row.path, row.state) for row in spec.final_surface) == final
    assert outcome.txid == TXID
    assert outcome.final_states == tuple(
        (
            path,
            AbsentStateView()
            if state is ABSENT
            else NonRegularStateView("directory")
            if isinstance(state, DirectoryState)
            else FileStateView(cast(FileState, state).content_hash),
        )
        for path, state in final
    )
    if operation in ("create", "replace"):
        assert payloads.open(post.content_hash).read() == payload
    else:
        with pytest.raises(KeyError):
            payloads.open(post.content_hash)


def test_store_move_refuses_an_existing_destination_without_changing_either_file(certified_work):
    root = _store(certified_work)
    seam = holdings_seam()
    seam.store_write(root, "source.bin", b"source")
    seam.store_write(root, "destination.bin", b"destination")

    with pytest.raises(ExecutionError):
        seam.store_move(root, "source.bin", "destination.bin")

    assert (root / "source.bin").read_bytes() == b"source"
    assert (root / "destination.bin").read_bytes() == b"destination"


def test_read_path_maps_an_unestablished_value(monkeypatch, tmp_path):
    monkeypatch.setattr(
        science_root,
        "read_path_state",
        lambda *_args: ReadUnestablished(UnestablishedReason.IO_FAILURE, "read failed"),
    )

    assert holdings_seam().read_path(tmp_path, "payload.bin") == ReadUnestablishedView(
        "io-failure", "read failed"
    )


def test_read_path_propagates_the_identical_exception(monkeypatch, tmp_path):
    sentinel = RuntimeError("engine alarm")

    def raise_sentinel(*_args):
        raise sentinel

    monkeypatch.setattr(science_root, "read_path_state", raise_sentinel)

    with pytest.raises(RuntimeError) as raised:
        holdings_seam().read_path(tmp_path, "payload.bin")
    assert raised.value is sentinel


def test_the_seam_delegates_intent_publication_and_genesis(monkeypatch, tmp_path):
    payload = b"intent"
    plan = [CreateOp("record.md", b"record")]
    calls = []

    def append(_backend, root, _metadata_root, _storage, value):
        calls.append(("append", Path(root), value))
        return "2" * 64

    def publish(executor, value):
        calls.append(("publish", executor.root, value, executor._fulfills))

    def head(root):
        calls.append(("genesis", root))
        return SimpleNamespace(genesis_payload=b"genesis")

    monkeypatch.setattr(science_root, "append_intent", append)
    monkeypatch.setattr(DurableExecutor, "execute", publish)
    monkeypatch.setattr(science_root, "_read_head", head)
    seam = holdings_seam()

    assert seam.append_intent(tmp_path, payload) == "2" * 64
    seam.publish_fulfilling(tmp_path, plan, "3" * 64)
    assert seam.store_genesis(tmp_path) == b"genesis"
    assert calls == [
        ("append", tmp_path, payload),
        ("publish", tmp_path, plan, "3" * 64),
        ("genesis", tmp_path),
    ]
