"""Bounded reads of metadata left in the job's writable output directory."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_REPORT_BYTES = 8 * 1024 * 1024

_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_MAX_SEED_ENTRIES = 65536


@contextmanager
def pinned_directory(path: Path | int) -> Iterator[int]:
    fd = os.dup(path) if isinstance(path, int) else os.open(path, _DIRECTORY)
    try:
        yield fd
    finally:
        os.close(fd)


def _regular_bytes(parent: int, name: str, limit: int) -> bytes:
    fd = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=parent)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
            raise OSError("job report is not a single-linked regular file within the size limit")
        # Reopen the pinned regular inode. No job-controlled name is resolved here.
        with open(f"/proc/self/fd/{fd}", "rb") as reader:
            data = reader.read(info.st_size + 1)
        if len(data) != info.st_size:
            raise OSError("job report changed size while being read")
        return data
    finally:
        os.close(fd)


def event_lines(path: Path, *, output_fd: int | None) -> list[str]:
    if output_fd is None:
        with pinned_directory(path.parent) as directory:
            data = _regular_bytes(directory, path.name, _REPORT_BYTES)
    else:
        if path.is_absolute() or len(path.parts) != 2 or ".." in path.parts:
            raise ValueError("expected a report in a direct child of the pinned output directory")
        directory = os.open(path.parts[0], _DIRECTORY, dir_fd=output_fd)
        try:
            data = _regular_bytes(directory, path.name, _REPORT_BYTES)
        finally:
            os.close(directory)
    return data.decode("utf-8").splitlines()


def seed_reports(scratch: Path | int) -> Iterator[tuple[Path, bytes]]:
    with pinned_directory(scratch) as root:
        try:
            directory = os.open(".seeds", _DIRECTORY, dir_fd=root)
        except FileNotFoundError:
            return
        try:
            names = []
            with os.scandir(directory) as entries:
                for i, entry in enumerate(entries):
                    if i >= _MAX_SEED_ENTRIES:
                        raise OSError("too many seed directory entries")
                    if entry.name.endswith(".json"):
                        names.append(entry.name)
            remaining = _REPORT_BYTES
            for name in sorted(names):
                data = _regular_bytes(directory, name, remaining)
                remaining -= len(data)
                yield Path(name), data
        finally:
            os.close(directory)
