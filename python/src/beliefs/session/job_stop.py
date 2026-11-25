"""A governed job's two confined children and its one terminal registration."""

from __future__ import annotations

import ctypes
import errno
import os
import select
import signal
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from subprocess import Popen

from nodes.core.write_plan import WritePlan

from beliefs.errors import SessionSealed

__all__ = ["FailureObservation", "JobStop"]


def _pidfd(name: str, *args: int | None) -> int:
    # The certified Python may omit the wrappers provided by its host libc.
    operation = getattr(ctypes.CDLL(None, use_errno=True), name)
    result = operation(*args)
    if result < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


@dataclass(frozen=True)
class FailureObservation:
    invocation_id: str
    phase: str
    intent: str
    returncode: int


class GovernedJob:
    def __init__(self, lock: threading.RLock, invocation: str, phase: str) -> None:
        self.lock = lock
        self.invocation = invocation
        self.phase = phase
        self.intent: str | None = None
        self.cancel_plan: WritePlan | None = None
        self.cut = False
        self.final = False
        self.consumed = False
        self.confirmed = False
        self.failure: FailureObservation | None = None
        self._child_fd: int | None = None
        self._signalled = False

    @contextmanager
    def child(self, spawn: Callable[[], Popen[str]]) -> Iterator[Popen[str]]:
        with self.lock:
            if self.cut or self.final:
                raise SessionSealed("the governed job cannot launch after the cutoff")
            process = spawn()
            try:
                fd = _pidfd("pidfd_open", process.pid, 0)
            except BaseException:
                process.kill()
                process.communicate()
                raise
            self._child_fd = fd
            self._signalled = False
        try:
            yield process
        finally:
            with self.lock:
                self._child_fd = None
                os.close(fd)

    def sweep(self) -> None:
        if not self.lock.acquire(blocking=False):
            return
        try:
            fd = self._child_fd
            if not self.cut or fd is None or self._signalled:
                return
            poll = select.poll()
            poll.register(fd, select.POLLIN)
            if poll.poll(0):
                return
            try:
                _pidfd("pidfd_send_signal", fd, signal.SIGKILL, None, 0)
            except OSError as exc:
                if exc.errno != errno.ESRCH:
                    raise
            else:
                self._signalled = True
        finally:
            self.lock.release()

    def checked_exit(self, code: int) -> bool:
        """Called only after the confined launch and its closure check both returned."""
        with self.lock:
            if type(code) is int and self.intent is not None:
                if self.cut and self._signalled and code == -signal.SIGKILL:
                    self.confirmed = True
                elif not self.cut and code != 0:
                    self.failure = FailureObservation(self.invocation, self.phase, self.intent, code)
            return self.confirmed


@dataclass(frozen=True)
class JobStop:
    cause: str
    _job: GovernedJob | None

    def sweep(self) -> None:
        if self._job is not None:
            self._job.sweep()

    def observation(self) -> FailureObservation | None:
        return None if self._job is None else self._job.failure
