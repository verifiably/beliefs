"""The durable create-only write (publish-act-local design §4.4)."""

from __future__ import annotations

import pytest

from beliefs import durable
from beliefs.durable import ensure_directory, write_create_only
from beliefs.errors import CreateOnlyCollision


def test_a_fresh_name_is_created_and_fsynced(tmp_path):
    target = tmp_path / "request.v1"
    assert write_create_only(target, b"one") == "created"
    assert target.read_bytes() == b"one"
    assert [p.name for p in tmp_path.iterdir()] == ["request.v1"]


def test_identical_bytes_at_the_name_are_present(tmp_path):
    target = tmp_path / "request.v1"
    write_create_only(target, b"one")
    assert write_create_only(target, b"one") == "present"


def test_different_bytes_at_the_name_collide_and_leave_the_file(tmp_path):
    target = tmp_path / "request.v1"
    write_create_only(target, b"one")
    with pytest.raises(CreateOnlyCollision) as caught:
        write_create_only(target, b"two")
    assert caught.value.path == target and target.read_bytes() == b"one"
    assert [p.name for p in tmp_path.iterdir()] == ["request.v1"]


def test_a_leftover_temporary_is_removed_first(tmp_path):
    (tmp_path / ".request.v1.0123456789abcdef.tmp").write_bytes(b"partial")
    write_create_only(tmp_path / "request.v1", b"one")
    assert [p.name for p in tmp_path.iterdir()] == ["request.v1"]


def test_the_final_name_never_shows_partial_bytes(tmp_path, monkeypatch):
    def failing_link(src, dst):
        raise OSError("cut before the link")

    monkeypatch.setattr(durable.os, "link", failing_link)
    with pytest.raises(OSError):
        write_create_only(tmp_path / "request.v1", b"one")
    assert not (tmp_path / "request.v1").exists()


def test_a_retry_after_a_death_before_the_directory_fsync_syncs_it(tmp_path, monkeypatch):
    real = durable._fsync_directory

    def dying(directory):
        raise OSError("died after the link, before the directory fsync")

    monkeypatch.setattr(durable, "_fsync_directory", dying)
    with pytest.raises(OSError):
        write_create_only(tmp_path / "request.v1", b"one")
    assert (tmp_path / "request.v1").read_bytes() == b"one"
    synced = []
    monkeypatch.setattr(durable, "_fsync_directory", lambda directory: synced.append(directory) or real(directory))
    assert write_create_only(tmp_path / "request.v1", b"one") == "present"
    assert synced == [tmp_path.resolve()]


def test_write_create_only_resolves_its_directory(tmp_path):
    """Review Focus 5: a symlinked directory component is resolved, not refused."""
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "link").symlink_to(real)
    assert write_create_only(tmp_path / "link" / "request.v1", b"one") == "created"
    assert (real / "request.v1").read_bytes() == b"one"


def test_data_must_be_bytes(tmp_path):
    with pytest.raises(TypeError):
        write_create_only(tmp_path / "request.v1", "one")  # type: ignore[arg-type]


def test_ensure_directory_creates_every_missing_component(tmp_path):
    ensure_directory(tmp_path / "a" / "b" / "c")
    assert (tmp_path / "a" / "b" / "c").is_dir()
    ensure_directory(tmp_path / "a" / "b" / "c")


def test_ensure_directory_refuses_a_file_in_the_way(tmp_path):
    (tmp_path / "a").write_bytes(b"")
    with pytest.raises(FileExistsError):
        ensure_directory(tmp_path / "a" / "b")
