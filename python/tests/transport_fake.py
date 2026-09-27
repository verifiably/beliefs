"""A directory-backed `Transport` for the remote publish tests
(publish-act-remote design §11.2): `https://remote.test/<name>` is the
directory `<base>/<name>`, and each transported name is a file under it. A
test double; it never ships."""

from __future__ import annotations

import shutil
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path

from beliefs.intents.publish import Destination
from beliefs.transport import TransportAbandoned

_PREFIX = "https://remote.test/"


class TransportFault(Exception):
    """A transient transport failure: the act propagates it and the attempt stays unfinished."""


class DirectoryTransport:
    def __init__(self, base: Path, *, fail_on_push: int | None = None, fail_after_files: int | None = None) -> None:
        self.base = Path(base)
        self.pushes = 0
        self.abandon = False
        self.fail_on_push = fail_on_push  # raise at the start of this push call (1-based)
        self.fail_after_files = fail_after_files  # raise after uploading this many files, on any push
        self.after_push: Callable[[Path], None] | None = None  # a fault applied to the remote after a push

    def remote_dir(self, destination: Destination) -> Path:
        if destination.type != "remote" or not destination.locator.startswith(_PREFIX):
            raise ValueError(f"the fake serves {_PREFIX}…, not {destination.locator!r}")
        return self.base / destination.locator.removeprefix(_PREFIX)

    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None:
        self.pushes += 1
        if self.abandon:
            return TransportAbandoned("the fake abandons")
        if self.fail_on_push == self.pushes:
            raise TransportFault(f"push {self.pushes} fails")
        target = self.remote_dir(destination)
        for uploaded, (name, path) in enumerate(sorted(files.items())):
            if self.fail_after_files is not None and uploaded == self.fail_after_files:
                raise TransportFault(f"push {self.pushes} fails after {uploaded} files")
            remote = target / name
            remote.parent.mkdir(parents=True, exist_ok=True)
            remote.write_bytes(Path(path).read_bytes())
        if self.after_push is not None:
            self.after_push(target)
        return None

    def listing(self, destination: Destination, corpus_id: str) -> dict[str, str]:
        target = self.remote_dir(destination)
        listed: dict[str, str] = {}
        for path in sorted(target.rglob("*")) if target.is_dir() else ():
            name = path.relative_to(target).as_posix()
            if path.is_file() and (name == f"{corpus_id}.head-artifact.v1" or name.startswith(f"{corpus_id}/")):
                listed[name] = sha256(path.read_bytes()).hexdigest()
        return listed

    def materialize(self, destination: Destination, corpus_id: str, into: Path) -> tuple[Path, bytes]:
        """A recipient's raw copy (decision 10): the root's files without any
        `.metadata` sibling, so it reads `METADATA_LESS`, and the sibling's bytes."""
        target = self.remote_dir(destination)
        into.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target / corpus_id, into / corpus_id)
        return into / corpus_id, (target / f"{corpus_id}.head-artifact.v1").read_bytes()
