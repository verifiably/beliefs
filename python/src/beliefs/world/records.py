"""The shared ceiling and fd-anchored, classified, bounded record capture."""

from __future__ import annotations

import errno
import os
import stat
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from beliefs.world.verify import RootKind

RECORD_CEILING = 8 * 1024 * 1024
"""Maximum bytes in a qualifying published record (spec §3.1)."""

RECORD_NAMESPACES = ("run", "act-report", "holdings-observation")


def _leaf_seam(path: str) -> None:
    """Interpose after enumeration and before the no-follow leaf open."""


def _close(fd: int) -> None:
    """Close once; cleanup failures are outside the capture surface."""
    with suppress(OSError):
        os.close(fd)


@dataclass(frozen=True)
class CapturedSurface:
    """One descent's records and its three named failures (successor-admission
    design §4.2). `records` is exactly what `capture_records` returns over the
    same namespaces; the path lists are what it used to swallow."""

    records: tuple[tuple[str, bytes], ...]
    withheld: tuple[str, ...]
    """Regular files withheld for size."""
    unreadable: tuple[str, ...]
    """Leaves the descent could not characterise: directory-entry
    classification, `O_PATH` open, readable open, `fstat` re-check or read
    failed."""
    uninspectable: tuple[str, ...]
    """Directories that exist but could not be opened or enumerated — every
    failure but `ENOENT`, which is an absent namespace and is silent."""


@dataclass
class _Descent:
    records: list[tuple[str, bytes]] = field(default_factory=list)
    withheld: list[str] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)
    uninspectable: list[str] = field(default_factory=list)


_LeafFailure = Literal["withheld", "unreadable", "silent"]


def capture_records(
    root: Path,
    kind: RootKind,
) -> tuple[tuple[str, bytes], ...]:
    """Cut 11's captured surface, unchanged: the three record namespaces of a
    corpus root, every failure silent, nothing for any other root kind."""
    if kind != "corpus":
        return ()
    return capture_surface(root, RECORD_NAMESPACES).records


def capture_surface(root: Path, namespaces: tuple[str, ...]) -> CapturedSurface:
    into = _Descent()
    try:
        root_fd = os.open(root, os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        into.uninspectable.append(".")
        return _finish(into)
    try:
        for namespace in namespaces:
            _capture_directory(root_fd, namespace, namespace, into)
    finally:
        _close(root_fd)
    return _finish(into)


def _finish(into: _Descent) -> CapturedSurface:
    return CapturedSurface(
        tuple(sorted(into.records)),
        tuple(sorted(into.withheld)),
        tuple(sorted(into.unreadable)),
        tuple(sorted(into.uninspectable)),
    )


def _capture_directory(
    parent_fd: int,
    name: str,
    prefix: str,
    into: _Descent,
) -> None:
    try:
        dir_fd = os.open(name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError as failure:
        if failure.errno != errno.ENOENT:
            into.uninspectable.append(prefix)
        return
    try:
        try:
            with os.scandir(dir_fd) as scan:
                children = sorted(scan, key=lambda child: child.name)
        except OSError as failure:
            if failure.errno != errno.ENOENT:
                into.uninspectable.append(prefix)
            return
        for child in children:
            if child.name.startswith("."):
                continue
            path = f"{prefix}/{child.name}"
            try:
                is_directory = child.is_dir(follow_symlinks=False)
            except OSError:
                into.unreadable.append(path)
                continue
            if is_directory:
                _capture_directory(dir_fd, child.name, path, into)
                continue
            _leaf_seam(path)
            payload = _read_leaf(dir_fd, child.name)
            if isinstance(payload, bytes):
                into.records.append((path, payload))
            elif payload == "withheld":
                into.withheld.append(path)
            elif payload == "unreadable":
                into.unreadable.append(path)
    finally:
        _close(dir_fd)


def _read_leaf(dir_fd: int, name: str) -> bytes | _LeafFailure:
    """Classify before a readable open; name every failure or oversize.

    A leaf that classifies as something other than a regular file is
    `silent` — not a record, never was. One the descent cannot classify or
    cannot read is `unreadable`; one over the ceiling is `withheld`."""
    try:
        path_fd = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=dir_fd)
    except OSError:
        return "unreadable"
    try:
        try:
            if not stat.S_ISREG(os.fstat(path_fd).st_mode):
                return "silent"
        except OSError:
            return "unreadable"
        try:
            read_fd = os.open(f"/proc/self/fd/{path_fd}", os.O_RDONLY)
        except OSError:
            return "unreadable"
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
            return "withheld" if len(data) > RECORD_CEILING else data
        except OSError:
            return "unreadable"
        finally:
            _close(read_fd)
    finally:
        _close(path_fd)
