"""Drive real mode refusals at record capture's exact open seams."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from science.world import records


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)


@contextmanager
def unreadable_leaf_at_open(
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
    relative_path: str,
) -> Iterator[None]:
    """Withdraw a leaf's mode immediately before its readable fd open."""
    initial_mode = _mode(target)
    real_seam = records._leaf_seam
    real_open = records.os.open
    armed = False
    opened: list[str] = []

    def arm(path: str) -> None:
        nonlocal armed
        real_seam(path)
        if path == relative_path:
            armed = True

    def open_path(path, flags: int, mode: int = 0o777, *, dir_fd: int | None = None):
        nonlocal armed
        if armed and isinstance(path, str) and path.startswith("/proc/self/fd/"):
            target.chmod(0)
            assert _mode(target) == 0
            opened.append(relative_path)
            armed = False
        return real_open(path, flags, mode, dir_fd=dir_fd)

    with monkeypatch.context() as scoped:
        scoped.setattr(records, "_leaf_seam", arm)
        scoped.setattr(records.os, "open", open_path)
        try:
            yield
        finally:
            target.chmod(initial_mode)
    assert opened == [relative_path]


@contextmanager
def unopenable_directory_at_open(
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
) -> Iterator[None]:
    """Withdraw a directory's mode immediately before its fd open."""
    initial_mode = _mode(target)
    real_open = records.os.open
    opened: list[str] = []

    def open_path(path, flags: int, mode: int = 0o777, *, dir_fd: int | None = None):
        if (
            not opened
            and path == target.name
            and dir_fd is not None
            and flags & os.O_DIRECTORY
        ):
            target.chmod(0)
            assert _mode(target) == 0
            opened.append(target.name)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    with monkeypatch.context() as scoped:
        scoped.setattr(records.os, "open", open_path)
        try:
            yield
        finally:
            target.chmod(initial_mode)
    assert opened == [target.name]
