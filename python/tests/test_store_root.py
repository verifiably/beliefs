"""Store roots: the opaque identity, the init act, and the store projection.

Plan Task 3 (docs/superpowers/plans/2026-08-23-root-lifecycle.md). The engine
is stubbed the way `test_root.py` stubs it — Science's own logic is the
subject — except the detached genesis read, which is real: fabricated chain
leaves are canonical engine bytes, so `store_identity` exercises
the same decode a cold arrival would.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from atoms.chain.model import GenesisEntry, encode_entry, entry_digest
from atoms.core.errors import PreconditionRefused
from authority import FULL

from beliefs import root as science_root
from beliefs.errors import CorpusRootRefused
from beliefs.root import (
    LifecycleState,
    init_corpus_root,
    init_store_root,
    store_identity,
)
from beliefs.world.verify import registered_surface_paths

_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def _fabricate_genesis(store_root: Path, payload: bytes) -> str:
    """One durable, well-formed genesis chain: real canonical engine bytes."""
    chain = store_root / ".#~chain"
    chain.mkdir(parents=True)
    envelope = encode_entry(None, GenesisEntry(payload, ()))
    digest = entry_digest(envelope)
    (chain / digest).write_bytes(envelope)
    return digest


def _recording_register(calls: list) -> object:
    def record(_backend, project_root, metadata_root, _storage, payload, surface):
        calls.append((project_root, metadata_root, payload, surface))
        return "d" * 64

    return record


class TestStoreIdentity:
    def test_a_fresh_store_round_trips_its_id(self, certified_work):
        root = certified_work / "store"
        minted = init_store_root(root, authority=FULL)
        assert store_identity(root) == minted

    def test_an_empty_directory_and_a_missing_root_read_none(self, tmp_path):
        (tmp_path / "empty").mkdir()
        assert store_identity(tmp_path / "empty") is None
        assert store_identity(tmp_path / "absent") is None

    def test_a_corpus_root_is_refused_not_none(self, certified_work):
        root = certified_work / "corpus"
        init_corpus_root(root, authority=FULL)
        with pytest.raises(CorpusRootRefused, match="store genesis payload is malformed"):
            store_identity(root)

    def test_a_malformed_store_genesis_is_refused(self, tmp_path):
        root = tmp_path / "store"
        _fabricate_genesis(root, b'{"domain":"science.store-root.v1"}')
        with pytest.raises(CorpusRootRefused):
            store_identity(root)

    def test_the_private_name_is_gone(self):
        assert not hasattr(science_root, "_read_existing_store_genesis")


class TestInitStoreRoot:
    def test_init_store_root_mints_a_fresh_opaque_id(self, tmp_path, monkeypatch):
        calls: list = []
        monkeypatch.setattr(science_root, "register_root", _recording_register(calls))

        first = init_store_root(tmp_path / "store-a", authority=FULL)
        second = init_store_root(tmp_path / "store-b", authority=FULL)

        assert _HEX32.fullmatch(first) and _HEX32.fullmatch(second)
        assert first != second
        # The genesis carries only the domain and the minted id: renaming the
        # root directory changes nothing the genesis payload states.
        _root, _metadata, payload, surface = calls[0]
        assert payload == science_root._store_genesis_payload(first, None)
        assert science_root._decode_store_genesis(payload) == (first, None)
        assert surface == ()

    def test_init_store_root_refuses_a_populated_payload_root(
        self, tmp_path, monkeypatch
    ):
        def trapped(*_args):
            raise AssertionError("a refused init must not register")

        monkeypatch.setattr(science_root, "register_root", trapped)
        store_root = tmp_path / "store"
        store_root.mkdir()
        (store_root / "payload.bin").write_bytes(b"already here")

        with pytest.raises(CorpusRootRefused, match="initializes empty"):
            init_store_root(store_root, authority=FULL)
        assert not (store_root / ".#~chain").exists()

    def test_interrupted_init_retry_returns_the_original_store_id(
        self, tmp_path, monkeypatch
    ):
        store_root = tmp_path / "store"
        store_root.mkdir()
        original = "ab" * 16
        _fabricate_genesis(
            store_root, science_root._store_genesis_payload(original, None)
        )
        monkeypatch.setattr(
            science_root,
            "_read_lifecycle_state_callback",
            lambda *_args: LifecycleState.READ_ONLY_UNSERVICEABLE,
        )
        calls: list = []
        monkeypatch.setattr(science_root, "register_root", _recording_register(calls))

        assert init_store_root(store_root, authority=FULL) == original
        # The retry re-registers the durable genesis's own id, never a re-mint.
        assert calls[0][2] == science_root._store_genesis_payload(original, None)

    def test_cold_existing_store_root_refuses_reinitialization(
        self, tmp_path, monkeypatch
    ):
        store_root = tmp_path / "store"
        store_root.mkdir()
        _fabricate_genesis(
            store_root, science_root._store_genesis_payload("cd" * 16, None)
        )
        monkeypatch.setattr(
            science_root,
            "_read_lifecycle_state_callback",
            lambda *_args: LifecycleState.METADATA_LESS,
        )

        def refusing(*_args):
            raise PreconditionRefused(
                "matching genesis has no local initialization operation"
            )

        monkeypatch.setattr(science_root, "register_root", refusing)

        with pytest.raises(
            CorpusRootRefused, match="restored or forked, never re-initialized"
        ):
            init_store_root(store_root, authority=FULL)

    def test_completed_init_is_idempotent_without_reregistering(
        self, tmp_path, monkeypatch
    ):
        store_root = tmp_path / "store"
        store_root.mkdir()
        original = "ef" * 16
        _fabricate_genesis(
            store_root, science_root._store_genesis_payload(original, None)
        )
        monkeypatch.setattr(
            science_root,
            "_read_lifecycle_state_callback",
            lambda *_args: LifecycleState.WRITABLE,
        )

        def trapped(*_args):
            raise AssertionError("a completed init must not re-register")

        monkeypatch.setattr(science_root, "register_root", trapped)
        assert init_store_root(store_root, authority=FULL) == original


class TestStoreGenesisPayload:
    def test_store_genesis_payload_round_trips(self):
        store_id = "12" * 16
        forked = ("f" * 64, "e" * 64)

        plain = science_root._store_genesis_payload(store_id, None)
        assert science_root._decode_store_genesis(plain) == (store_id, None)

        lifted = science_root._store_genesis_payload(store_id, forked)
        assert science_root._decode_store_genesis(lifted) == (store_id, forked)

        from beliefs.identity import v1

        malformed = (
            v1.encode({"domain": science_root.STORE_GENESIS_DOMAIN}),
            v1.encode(
                {"domain": science_root.STORE_GENESIS_DOMAIN, "store_id": "zz"}
            ),
            v1.encode(
                {
                    "domain": science_root.STORE_GENESIS_DOMAIN,
                    "store_id": store_id,
                    "forked_from": ["f" * 64, "e" * 64],
                }
            ),
            v1.encode(
                {
                    "domain": science_root.STORE_GENESIS_DOMAIN,
                    "store_id": store_id,
                    "forked_from": {"genesis": "f" * 64},
                }
            ),
            v1.encode(
                {
                    "domain": science_root.STORE_GENESIS_DOMAIN,
                    "store_id": store_id,
                    "forked_from": {"genesis": "not-hex", "head": "e" * 64},
                }
            ),
            v1.encode(
                {
                    "domain": science_root.STORE_GENESIS_DOMAIN,
                    "store_id": store_id,
                    "forked_from": {
                        "genesis": "f" * 64,
                        "head": "e" * 64,
                        "extra": "no",
                    },
                }
            ),
            b"not canonical json at all",
        )
        for payload in malformed:
            with pytest.raises(CorpusRootRefused):
                science_root._decode_store_genesis(payload)


class TestStoreSurface:
    def test_store_surface_excludes_bookkeeping(self, tmp_path):
        store_root = tmp_path / "store"
        (store_root / ".#~chain").mkdir(parents=True)
        (store_root / ".#~chain" / ("a" * 64)).write_bytes(b"chain bytes")
        (store_root / ".#~root-claim").write_bytes(b"claim bytes")
        (store_root / ".nodes-index").write_bytes(b"index cache")
        (store_root / "artifacts").mkdir()
        (store_root / "artifacts" / "head.json").write_bytes(b"{}")
        (store_root / "blob.bin").write_bytes(b"opaque")
        (store_root / "notes.txt").write_bytes(b"anything at all")

        assert registered_surface_paths(store_root, "store") == (
            "artifacts/head.json",
            "blob.bin",
            "notes.txt",
        )

    def test_store_surface_does_not_follow_symlinks(self, tmp_path):
        store_root = tmp_path / "store"
        (store_root / "real").mkdir(parents=True)
        (store_root / "real" / "inner.bin").write_bytes(b"inner")
        (store_root / "link").symlink_to("real", target_is_directory=True)

        surface = registered_surface_paths(store_root, "store")
        assert surface == ("link", "real/inner.bin")
