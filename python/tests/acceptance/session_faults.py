"""Fault fixtures for J2 (design §13 item 4): a backend that halts at the first
publish-phase call, leaving a real staged, unsettled transaction."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from atoms.fs.backend import Backend
from atoms.fs.platform import select_backend
from atoms.fs.volume import StorageProfile
from nodes.core.write_plan import WritePlan

from beliefs.permit import Authority
from beliefs.root import DurableOperationPort

PUBLISH_PHASE = ("exchange", "transfer_noclobber", "link_anchor")
#: How many publish-phase calls `run_transaction` makes before the record's own
#: publish — the registration leaf's, at least. Fixed by Step 2's trace.
PUBLISH_CALLS_BEFORE_RECORD = 6


class TracingBackend:
    """Delegates every engine call and records the method names, in order — the
    instrument that finds the transaction's publish step (design §13 item 4)."""

    def __init__(self) -> None:
        self._inner = select_backend()
        self.calls: list[str] = []

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._inner, name)
        if not callable(target):
            return target

        def recording(*args: Any, **kwargs: Any) -> Any:
            self.calls.append(name)
            return target(*args, **kwargs)

        return recording


class HaltingBackend:
    """Delegates every engine call to the real backend; once `armed`, skips
    `skip` publish-phase calls and raises `OSError` at every one after that
    until the port disarms it. Arming happens inside `execute_fulfilling`,
    after `append_intent` has landed, so the intent is never what halts.

    **Arm it only over a kind directory that already exists.** A transaction that
    must create `<kind>/` publishes the directory too, one publish-phase call
    *before* the record's, so the skip count would land one step early; every arm
    therefore writes a record of the same kind before arming.

    The window stays open for the whole fulfilling execution deliberately: the
    engine answers a failed publish by rolling the transaction back, and a
    rollback that succeeds settles the registration, which is the state §13
    item 4 must *not* leave. Halting the rollback's publishes too is what
    leaves the registration durable and unsettled — the pending state §6
    classifies and the next write's recovery resolves.
    """

    def __init__(self, *, skip: int) -> None:
        self._inner = select_backend()
        self.skip = skip
        self.remaining = 0
        self.writes = 0
        self.armed = False
        self.halted = False
        self.arm_next = False  # set by a test; the port arms at its next fulfilling execution

    def arm(self) -> None:
        self.remaining = self.skip
        self.writes = 0
        self.armed = True
        self.halted = False

    def disarm(self) -> None:
        self.armed = False
        self.remaining = 0

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._inner, name)
        if name == "write":

            def counting(*args: Any, **kwargs: Any) -> Any:
                self.writes += 1
                return target(*args, **kwargs)

            return counting
        if name in PUBLISH_PHASE:

            def halting(*args: Any, **kwargs: Any) -> Any:
                if self.armed:
                    if self.remaining > 0:
                        self.remaining -= 1
                    else:
                        # §13 item 4: the halt follows at least one staged `write`.
                        assert self.writes > 0, "the halt must follow a staged write"
                        self.halted = True
                        raise OSError("halted by the J2 fixture before the record's publish")
                return target(*args, **kwargs)

            return halting
        return target


class HaltingPort(DurableOperationPort):
    """Arms its backend at the transaction-specific point: inside
    `_execute_fulfilling`, after the intent has landed as its own entry."""

    def __init__(
        self,
        root: Path,
        *,
        backend: HaltingBackend,
        storage: StorageProfile,
        metadata_root: Path,
        authority: Authority,
        profile,
    ) -> None:
        # The delegate answers every engine call through `__getattr__`, which the
        # structural `Backend` protocol cannot see; the cast is the whole of what
        # this constructor adds.
        super().__init__(
            root,
            backend=cast(Backend, backend),
            storage=storage,
            metadata_root=metadata_root,
            authority=authority,
            profile=profile,
        )
        self.halting_backend = backend

    def _execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None:
        backend = self.halting_backend
        if not backend.arm_next:
            return super()._execute_fulfilling(plan, fulfills)
        backend.arm_next = False
        backend.arm()
        try:
            return super()._execute_fulfilling(plan, fulfills)
        finally:
            backend.disarm()
