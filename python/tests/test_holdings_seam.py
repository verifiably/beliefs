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
from beliefs.errors import StoreWriteRefused
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
from beliefs.world.logmodel import RegisteredEntryView, SettledEntryView, WellFormedView

TXID = "1" * 32


def _store(work, name="store"):
    root = work / name
    init_store_root(root, authority=FULL)
    return root


def test_read_path_answers_found_with_the_content_hash(certified_work):
    root = _store(certified_work)
    payload = b"held bytes"
    seam = holdings_seam()
    seam.store_write(root, "payload.bin", payload, "f" * 64)

    assert seam.read_path(root, "payload.bin") == PathObservedView(
        FileStateView("sha256:" + sha256(payload).hexdigest(), len(payload))
    )


def test_read_path_answers_absent_for_a_missing_path(certified_work):
    root = _store(certified_work)

    assert holdings_seam().read_path(root, "missing.bin") == PathObservedView(AbsentStateView())


def test_read_path_reports_a_directory_as_non_regular(certified_work):
    root = _store(certified_work)
    seam = holdings_seam()
    seam.store_write(root, "directory/payload.bin", b"held bytes", "f" * 64)

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

    outcome = holdings_seam().store_write(root, "directory/payload.bin", payload, "f" * 64)

    assert len(outcome.txid) == 32
    assert outcome.final_states == (
        ("directory", NonRegularStateView("directory")),
        ("directory/payload.bin", FileStateView("sha256:" + sha256(payload).hexdigest(), len(payload))),
    )


def test_store_delete_returns_the_absent_row(certified_work):
    root = _store(certified_work)
    seam = holdings_seam()
    seam.store_write(root, "payload.bin", b"held bytes", "f" * 64)

    outcome = seam.store_delete(root, "payload.bin", "f" * 64)

    assert outcome.final_states == (("payload.bin", AbsentStateView()),)


def test_store_move_returns_the_dual_location_result(certified_work):
    root = _store(certified_work)
    payload = b"held bytes"
    seam = holdings_seam()
    seam.store_write(root, "source.bin", payload, "f" * 64)

    outcome = seam.store_move(root, "source.bin", "destination.bin", "f" * 64)

    assert outcome.final_states == (
        ("destination.bin", FileStateView("sha256:" + sha256(payload).hexdigest(), len(payload))),
        ("source.bin", AbsentStateView()),
    )


OBJECT_PATH = "objects/sha256/ab/" + "ab" + "c" * 62


def test_store_create_writes_a_new_object_and_refuses_an_existing_one(certified_work):
    root = _store(certified_work)
    seam = holdings_seam()

    outcome = seam.store_create(root, OBJECT_PATH, b"abc", "f" * 64)

    assert (root / OBJECT_PATH).read_bytes() == b"abc"
    assert outcome.final_states[-1] == (OBJECT_PATH, FileStateView("sha256:" + sha256(b"abc").hexdigest(), 3))
    with pytest.raises(ExecutionError) as refused:
        seam.store_create(root, OBJECT_PATH, b"other", "f" * 64)
    assert refused.value.applied == 0
    assert seam.store_refusal(refused.value)
    assert (root / OBJECT_PATH).read_bytes() == b"abc"


def test_store_create_submits_create_only_effects(tmp_path, monkeypatch):
    root = tmp_path / "store"
    root.mkdir()
    captured = []

    def capture(**kwargs):
        captured.append(kwargs)
        spec = kwargs["spec"]
        return SimpleNamespace(
            txid=TXID, final_states=tuple((row.path, row.state) for row in spec.final_surface), registration="e" * 64
        )

    monkeypatch.setattr(science_root, "_mapped_submit", capture)
    holdings_seam().store_create(root, OBJECT_PATH, b"abc", "f" * 64)

    (call,) = captured
    effects = call["spec"].effects
    assert [type(effect) for effect in effects] == [
        CreateDirectory,
        CreateDirectory,
        CreateDirectory,
        CreateFileNoClobber,
    ]
    assert not any(isinstance(effect, ReplaceFile) for effect in effects)
    assert call["spec"].registered_paths == (OBJECT_PATH,)


@pytest.mark.parametrize(
    "path", ["payload.bin", "objects", "objects/other/ab/abc", "objects/sha256", "docs/objects/sha256/ab/abc"]
)
def test_store_create_refuses_a_path_outside_objects(tmp_path, path):
    with pytest.raises(StoreWriteRefused):
        holdings_seam().store_create(tmp_path, path, b"abc", "f" * 64)


@pytest.mark.parametrize(
    "act",
    [
        lambda seam, root, path: seam.store_write(root, path, b"abc", "f" * 64),
        lambda seam, root, path: seam.store_delete(root, path, "f" * 64),
        lambda seam, root, path: seam.store_move(root, "source.bin", path, "f" * 64),
        lambda seam, root, path: seam.store_move(root, path, "destination.bin", "f" * 64),
    ],
    ids=["write", "delete", "move-to", "move-from"],
)
@pytest.mark.parametrize("path", ["objects", "objects/sha256/ab/abc"])
def test_ordinary_store_primitives_refuse_object_paths(tmp_path, act, path):
    with pytest.raises(StoreWriteRefused, match="objects/ is written only by tree-write"):
        act(holdings_seam(), tmp_path, path)


def test_a_read_path_view_carries_the_byte_length(certified_work):
    root = _store(certified_work)
    seam = holdings_seam()
    seam.store_create(root, OBJECT_PATH, b"abc", "f" * 64)

    assert seam.read_path(root, OBJECT_PATH) == PathObservedView(
        FileStateView("sha256:" + sha256(b"abc").hexdigest(), byte_len=3)
    )


def test_store_mutation_on_an_ungranted_root_refuses(certified_work):
    source = _store(certified_work)
    replica = certified_work / "replica"
    replicate_root(source, replica, authority=FULL)

    with pytest.raises(ExecutionError):
        holdings_seam().store_write(replica, "payload.bin", b"held bytes", "f" * 64)


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
            registration="e" * 64,
        )

    monkeypatch.setattr(science_root, "_mapped_submit", capture)
    seam = holdings_seam()
    if operation == "create":
        path = "directory/payload.bin"
        outcome = seam.store_write(root, path, payload, "f" * 64)
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
            outcome = seam.store_write(root, "source.bin", payload, "f" * 64)
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
            outcome = seam.store_delete(root, "source.bin", "f" * 64)
            projection = [{"op": "delete", "path": "source.bin", "expected_digest": old_hash}]
            registered = ("source.bin",)
            effect_types = (DeletePath,)
            initial = (("source.bin", pre),)
            final = (("source.bin", ABSENT),)
        else:
            outcome = seam.store_move(root, "source.bin", "destination.bin", "f" * 64)
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
            else FileStateView(cast(FileState, state).content_hash, cast(FileState, state).byte_len),
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
    seam.store_write(root, "source.bin", b"source", "f" * 64)
    seam.store_write(root, "destination.bin", b"destination", "f" * 64)

    with pytest.raises(ExecutionError):
        seam.store_move(root, "source.bin", "destination.bin", "f" * 64)

    assert (root / "source.bin").read_bytes() == b"source"
    assert (root / "destination.bin").read_bytes() == b"destination"


def test_read_path_maps_an_unestablished_value(monkeypatch, tmp_path):
    monkeypatch.setattr(
        science_root,
        "read_path_state",
        lambda *_args: ReadUnestablished(UnestablishedReason.IO_FAILURE, "read failed"),
    )

    assert holdings_seam().read_path(tmp_path, "payload.bin") == ReadUnestablishedView("io-failure", "read failed")


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
    monkeypatch.setattr(science_root, "_registration_for", lambda *_args: "4" * 64)
    monkeypatch.setattr(science_root, "_read_head", head)
    seam = holdings_seam()

    assert seam.append_intent(tmp_path, payload) == "2" * 64
    assert seam.publish_fulfilling(tmp_path, plan, "3" * 64) == "4" * 64
    assert seam.store_genesis(tmp_path) == b"genesis"
    assert calls == [
        ("append", tmp_path, payload),
        ("publish", tmp_path, plan, "3" * 64),
        ("genesis", tmp_path),
    ]


def test_publish_fulfilling_returns_the_registration_digest(certified_work):
    from beliefs.holdings.boundary import intent_payload
    from beliefs.holdings.records import StoreLocator
    from beliefs.root import init_corpus_root

    observer = certified_work / "observer"
    init_corpus_root(observer, authority=FULL)
    seam = holdings_seam()
    payload = intent_payload(
        location=StoreLocator("1" * 32, "p.bin"), act_kind="write", event_token="tok", actor="observer"
    )
    with seam.corpus_lock(observer):
        intent = seam.append_intent(observer, payload)
        entry = seam.publish_fulfilling(observer, (CreateOp("notes/p.md", b"---\nid: x\n---\n"),), intent)

    view = science_root.log_seam().inspect_detached(observer)
    registered = {digest: e for digest, e in _entries(view) if getattr(e, "fulfills", None) == intent}
    assert list(registered) == [entry]


def _entries(view):
    return [(entry.digest, entry) for entry in view.entries]


def _committed_registration(root, outcome, expected_paths: tuple[str, ...]):
    chain = science_root._log_seam().inspect_detached(root)
    assert isinstance(chain, WellFormedView)
    matches = [e for e in chain.entries if isinstance(e, RegisteredEntryView) and e.digest == outcome.entry]
    assert len(matches) == 1
    assert matches[0].txid == outcome.txid
    assert tuple(path for path, _ in matches[0].initial) == expected_paths
    assert tuple(path for path, _ in matches[0].final) == expected_paths
    settlements = [e for e in chain.entries if isinstance(e, SettledEntryView) and e.registration == outcome.entry]
    assert [s.committed for s in settlements] == [True]


@pytest.mark.parametrize("operation", ["write", "create", "delete", "move"])
def test_store_outcome_entry_is_the_committed_store_registration(certified_work, operation):
    root = _store(certified_work)
    seam = holdings_seam()
    intent = "f" * 64
    seam.store_write(root, "source.bin", b"held", intent)
    if operation == "write":
        outcome = seam.store_write(root, "a/b", b"x", intent)
        expected_paths = ("a/b",)
    elif operation == "create":
        outcome = seam.store_create(root, OBJECT_PATH, b"abc", intent)
        expected_paths = (OBJECT_PATH,)
    elif operation == "delete":
        outcome = seam.store_delete(root, "source.bin", intent)
        expected_paths = ("source.bin",)
    else:
        outcome = seam.store_move(root, "source.bin", "destination.bin", intent)
        expected_paths = ("destination.bin", "source.bin")
    assert len(outcome.entry) == 64
    _committed_registration(root, outcome, expected_paths)


def test_a_malformed_store_path_is_a_store_write_refusal(certified_work):
    root = _store(certified_work)
    before = science_root._log_seam().inspect_detached(root)
    for path in ("", "/abs", "..", "a/"):
        for call in (
            lambda path=path: holdings_seam().store_write(root, path, b"x", "f" * 64),
            lambda path=path: holdings_seam().store_create(root, path, b"x", "f" * 64),
            lambda path=path: holdings_seam().store_delete(root, path, "f" * 64),
            lambda path=path: holdings_seam().store_move(root, path, "d.bin", "f" * 64),
            lambda path=path: holdings_seam().store_move(root, "s.bin", path, "f" * 64),
        ):
            with pytest.raises(StoreWriteRefused):
                call()
    assert science_root._log_seam().inspect_detached(root) == before
