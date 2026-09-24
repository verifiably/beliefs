"""The durable create-only write (layer design §6.1 step 0; publish-act-local
design §4.4): temporary name, fsync, a create-only link, fsync of the directory.
Partial bytes never appear at the final name. Plain POSIX, outside every root —
the operations root and the head artifact's sibling have no engine boundary."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Literal

from beliefs.errors import CreateOnlyCollision

__all__ = ["ensure_directory", "write_create_only"]


def _fsync_directory(directory: Path) -> None:
    handle = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


def ensure_directory(path: Path) -> None:
    """Create every missing component of `path`, fsyncing each new entry's parent."""
    target = Path(path).resolve()
    missing: list[Path] = []
    probe = target
    while not probe.exists():
        missing.append(probe)
        probe = probe.parent
    if not probe.is_dir():
        raise FileExistsError(f"{probe} exists and is not a directory")
    for directory in reversed(missing):
        directory.mkdir()
        _fsync_directory(directory.parent)
    if not target.is_dir():
        raise FileExistsError(f"{target} exists and is not a directory")


def write_create_only(path: Path, data: bytes) -> Literal["created", "present"]:
    """Publish `data` at `path` create-only: identical bytes already there are
    `present`, different bytes raise `CreateOnlyCollision`."""
    if type(data) is not bytes:
        raise TypeError("a create-only write takes bytes")
    target = Path(path).parent.resolve() / Path(path).name
    directory = target.parent
    for leftover in directory.glob(f".{target.name}.*.tmp"):
        leftover.unlink()
    temporary = directory / f".{target.name}.{secrets.token_hex(8)}.tmp"
    handle = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        view = memoryview(data)
        while view:
            written = os.write(handle, view)
            view = view[written:]
        os.fsync(handle)
    finally:
        os.close(handle)
    try:
        os.link(temporary, target)
    except FileExistsError:
        temporary.unlink()
        if target.read_bytes() != data:
            raise CreateOnlyCollision(target) from None
        # an earlier call may have died after its link and before its directory
        # fsync: the retry completes that obligation before answering (finding 5)
        _fsync_directory(directory)
        return "present"
    except BaseException:
        temporary.unlink()
        raise
    temporary.unlink()
    _fsync_directory(directory)
    return "created"
