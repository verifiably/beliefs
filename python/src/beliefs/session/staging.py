"""A run session's kernel staging for confined jobs.

Under a run session the kernel, not the caller, chooses where a confined job
stages: `<operations_root>/scratch/<session>/<invocation>`, with snapshots in the
shared cache `<operations_root>/scratch/environments`. Each anchor is created or
opened relative to its parent's descriptor without following a symbolic link,
and its `(st_dev, st_ino)` pinned; the bind check before every launch compares
paths against those pins and never resolves one afresh."""

from __future__ import annotations

import os
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import final

from beliefs.confinement import DEVICES, MountPlan
from beliefs.errors import ConfinementNotEstablished
from beliefs.sealed import sealed
from beliefs.session.ledger import require_hex, require_invocation_id

__all__ = ["RunStaging"]

_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FINAL = os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC
_SCRATCH = "scratch"
_CACHE = "environments"


@dataclass(frozen=True)
class _Anchor:
    """A pinned directory: its lexical path, an open descriptor, and its identity."""

    path: Path
    fd: int
    identity: tuple[int, int]


def _pinned(path: Path, fd: int) -> _Anchor:
    try:
        seen = os.fstat(fd)
    except BaseException:
        os.close(fd)
        raise
    return _Anchor(path, fd, (seen.st_dev, seen.st_ino))


@sealed
@final
class RunStaging:
    """One run session's staging. The operations root is opened and pinned at
    construction (an `OSError` when it cannot be, a symbolic link included); the
    scratch, cache, session and invocation directories on first use. The session
    holds every descriptor until `release` (an invocation's) or `close` (all)."""

    def __init__(self, operations_root: Path, session_id: str) -> None:
        if not isinstance(operations_root, Path):
            raise TypeError("operations_root must be a Path")
        self._session_id = require_hex(session_id, 32, "session id")
        path = Path(os.path.abspath(operations_root))
        self._root = _pinned(path, os.open(path, _DIRECTORY))
        self._scratch: _Anchor | None = None
        self._cache: _Anchor | None = None
        self._session: _Anchor | None = None
        # Each invocation's anchors, from the operations root down to its own directory.
        self._invocations: dict[str, tuple[_Anchor, ...]] = {}
        self._released: set[str] = set()
        self._closed = False
        self._lock = threading.Lock()

    # --- anchors ---------------------------------------------------------------------
    def invocation_dir(self, invocation: str) -> Path:
        """`<operations_root>/scratch/<session>/<invocation>`: created `0700` and
        exclusively at the invocation's first call (the session directory likewise at
        the session's first), and returned again by later calls."""
        invocation = require_invocation_id(invocation)
        with self._lock:
            self._require_open()
            chain = self._invocations.get(invocation)
            if chain is None:
                if invocation in self._released:
                    raise ConfinementNotEstablished(f"invocation {invocation}'s staging was released when it closed")
                scratch = self._scratch_anchor()
                session = self._session_anchor(scratch)
                chain = (self._root, scratch, session, self._child(session, invocation, exclusive=True))
                self._invocations[invocation] = chain
            self._recheck(*chain)
            return chain[-1].path

    def cache_dir(self) -> Path:
        """`<operations_root>/scratch/environments`, shared across sessions:
        created or opened, then pinned."""
        with self._lock:
            self._require_open()
            scratch = self._scratch_anchor()
            if self._cache is None:
                self._cache = self._child(scratch, _CACHE, exclusive=False)
            self._recheck(self._root, scratch, self._cache)
            return self._cache.path

    def _scratch_anchor(self) -> _Anchor:
        if self._scratch is None:
            self._scratch = self._child(self._root, _SCRATCH, exclusive=False)
        return self._scratch

    def _session_anchor(self, scratch: _Anchor) -> _Anchor:
        if self._session is None:
            self._session = self._child(scratch, self._session_id, exclusive=True)
        return self._session

    def _child(self, parent: _Anchor, name: str, *, exclusive: bool) -> _Anchor:
        path = parent.path / name
        try:
            os.mkdir(name, 0o700, dir_fd=parent.fd)
        except FileExistsError as caught:
            if exclusive:
                raise ConfinementNotEstablished(f"{path} already exists; kernel staging creates it afresh") from caught
        except OSError as caught:
            raise ConfinementNotEstablished(f"{path} could not be created: {caught.strerror}") from caught
        try:
            fd = os.open(name, _DIRECTORY, dir_fd=parent.fd)
        except OSError as caught:
            raise ConfinementNotEstablished(
                f"{path} could not be opened as a directory without following a symlink: {caught.strerror}"
            ) from caught
        return _pinned(path, fd)

    @staticmethod
    def _recheck(*anchors: _Anchor) -> None:
        """Step 1: each anchor's path, re-`lstat`ed, is no symlink and is the pinned directory."""
        for anchor in anchors:
            try:
                seen = os.lstat(anchor.path)
            except OSError as caught:
                raise ConfinementNotEstablished(
                    f"{anchor.path} is gone from its pinned anchor: {caught.strerror}"
                ) from caught
            if stat.S_ISLNK(seen.st_mode):
                raise ConfinementNotEstablished(f"{anchor.path} is a symlink, not its pinned anchor")
            if (seen.st_dev, seen.st_ino) != anchor.identity:
                raise ConfinementNotEstablished(f"{anchor.path} is not its pinned anchor; it was replaced")

    # --- the bind check ----------------------------------------------------------------
    def check_binds(self, plan: MountPlan, invocation: str) -> None:
        """Before a launch: (1) every anchor from the operations root down is still
        the pinned one; (2) every bind source but the two device nodes is the
        invocation's staging or the cache joined, lexically, with a relative path
        that has no `..`, `.` or empty component; (3) that path, walked from the
        pinned descriptor one component at a time without following a symlink,
        reaches the very file an `lstat` of the source finds. Any failure is
        `ConfinementNotEstablished`."""
        if type(plan) is not MountPlan:
            raise TypeError("plan must be a MountPlan")
        invocation = require_invocation_id(invocation)
        with self._lock:
            self._require_open()
            chain = self._invocations.get(invocation)
            if chain is None:
                raise ConfinementNotEstablished(f"invocation {invocation} has no staging in this session")
            allowed = (chain[-1],) if self._cache is None else (chain[-1], self._cache)
            self._recheck(*chain, *allowed[1:])
            for sandbox, source, access in plan.binds:
                if access == "dev" and source == sandbox and source in DEVICES:
                    continue
                base, parts = self._beneath(source, allowed)
                self._walk(base, parts, source)

    @staticmethod
    def _beneath(source: str, allowed: tuple[_Anchor, ...]) -> tuple[_Anchor, list[str]]:
        """Step 2, lexical: never through `realpath`."""
        for anchor in allowed:
            prefix = str(anchor.path)
            if source == prefix or source.startswith(prefix + "/"):
                parts = source[len(prefix) + 1 :].split("/")
                if any(part in ("", ".", "..") for part in parts):
                    raise ConfinementNotEstablished(
                        f"bind source {source!r} has a '..', '.' or empty component beneath {prefix}"
                    )
                return anchor, parts
        names = " or ".join(str(anchor.path) for anchor in allowed)
        raise ConfinementNotEstablished(f"bind source {source!r} is not beneath {names}")

    @staticmethod
    def _walk(anchor: _Anchor, parts: list[str], source: str) -> None:
        """Step 3: `openat(…, O_NOFOLLOW)` from the pinned descriptor, `O_PATH` for the last."""
        opened: list[int] = []
        try:
            fd = anchor.fd
            for name in parts[:-1]:
                try:
                    fd = os.open(name, _DIRECTORY, dir_fd=fd)
                except OSError as caught:
                    raise ConfinementNotEstablished(
                        f"bind source {source!r}: {name!r} is a symlink or not a directory: {caught.strerror}"
                    ) from caught
                opened.append(fd)
            try:
                final_fd = os.open(parts[-1], _FINAL, dir_fd=fd)
            except OSError as caught:
                raise ConfinementNotEstablished(
                    f"bind source {source!r} cannot be reached: {caught.strerror}"
                ) from caught
            opened.append(final_fd)
            walked = os.fstat(final_fd)
        finally:
            for fd in opened:
                os.close(fd)
        if stat.S_ISLNK(walked.st_mode):
            raise ConfinementNotEstablished(f"bind source {source!r} is a symlink")
        try:
            seen = os.lstat(source)
        except OSError as caught:
            raise ConfinementNotEstablished(f"bind source {source!r} cannot be observed: {caught.strerror}") from caught
        if (seen.st_dev, seen.st_ino) != (walked.st_dev, walked.st_ino):
            raise ConfinementNotEstablished(
                f"bind source {source!r} is not the file the walk from its pinned anchor reached"
            )

    # --- lifetime ----------------------------------------------------------------------
    def release(self, invocation: str) -> None:
        """Close an invocation's descriptor when it closes; its directory stays."""
        invocation = require_invocation_id(invocation)
        with self._lock:
            chain = self._invocations.pop(invocation, None)
            self._released.add(invocation)
            if chain is not None:
                os.close(chain[-1].fd)

    def close(self) -> None:
        """Close every descriptor. Idempotent."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            anchors = [
                *(chain[-1] for chain in self._invocations.values()),
                self._session,
                self._cache,
                self._scratch,
                self._root,
            ]
            self._invocations.clear()
            for anchor in anchors:
                if anchor is not None:
                    os.close(anchor.fd)

    def _require_open(self) -> None:
        if self._closed:
            raise ConfinementNotEstablished("the run staging is closed")
