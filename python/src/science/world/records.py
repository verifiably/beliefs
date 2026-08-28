"""The shared ceiling and fd-anchored, classified, bounded record capture."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from science.world.verify import RootKind

RECORD_CEILING = 8 * 1024 * 1024
"""Maximum bytes in a qualifying published record (spec §3.1)."""

RECORD_NAMESPACES = ("run", "act-report", "holdings-observation")


def _leaf_seam(path: str) -> None:
    """Interpose after enumeration and before the no-follow leaf open."""


def capture_records(
    root: Path,
    kind: RootKind,
) -> tuple[tuple[str, bytes], ...]:
    if kind != "corpus":
        return ()
    captured: list[tuple[str, bytes]] = []
    try:
        root_fd = os.open(root, os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return ()
    try:
        for namespace in RECORD_NAMESPACES:
            _capture_directory(root_fd, namespace, namespace, captured)
    finally:
        os.close(root_fd)
    return tuple(sorted(captured))


def _capture_directory(
    parent_fd: int,
    name: str,
    prefix: str,
    captured: list[tuple[str, bytes]],
) -> None:
    try:
        dir_fd = os.open(name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError:
        return
    try:
        try:
            with os.scandir(dir_fd) as scan:
                children = sorted(scan, key=lambda child: child.name)
        except OSError:
            return
        for child in children:
            if child.name.startswith("."):
                continue
            path = f"{prefix}/{child.name}"
            if child.is_dir(follow_symlinks=False):
                _capture_directory(dir_fd, child.name, path, captured)
                continue
            _leaf_seam(path)
            payload = _read_leaf(dir_fd, child.name)
            if payload is not None:
                captured.append((path, payload))
    finally:
        os.close(dir_fd)


def _read_leaf(dir_fd: int, name: str) -> bytes | None:
    """Classify before a readable open; withhold every failure or oversize."""
    try:
        path_fd = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=dir_fd)
    except OSError:
        return None
    try:
        try:
            if not stat.S_ISREG(os.fstat(path_fd).st_mode):
                return None
            read_fd = os.open(f"/proc/self/fd/{path_fd}", os.O_RDONLY)
        except OSError:
            return None
        try:
            chunks: list[bytes] = []
            remaining = RECORD_CEILING + 1
            while remaining > 0:
                chunk = os.read(read_fd, min(remaining, 1 << 20))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
            return None if len(data) > RECORD_CEILING else data
        except OSError:
            return None
        finally:
            os.close(read_fd)
    finally:
        os.close(path_fd)
