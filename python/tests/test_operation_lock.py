"""`OperationLock`'s five states, driven by events and gates only.

Nothing here sleeps. Every wait and every join is bounded and asserted, because
a sleep long enough to "let the other thread get there" is a hope, not a
synchronization primitive: it passes on a quiet machine and lies on a busy one.

The one case that needs a queued writer to wake *after* a whole capture has
begun and ended cannot be reached by hoping to win a race either. It is reached
by wrapping the condition's own mutex (`GatedLock`), which is the exact place a
notified waiter must pass through before it can look at the lock's state.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import cast

import pytest

from beliefs.corpus import OperationLock
from beliefs.errors import BuildContended, BuildHold

WAIT = 5.0  # seconds: the bound on every wait and join in this file


class GatedLock:
    """A real mutex that can hold one nominated thread outside the critical
    section at the moment a `Condition` waiter re-acquires it.

    `threading.Condition.wait` releases this lock when its caller parks and
    re-acquires it once notified. Both moments are what these tests need:
    `parked` reports that a queued writer is genuinely in the queue rather than
    refusing, and the gate holds a notified writer there — awake but still
    outside the lock — for as long as it takes to run a whole capture past it.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.gated_thread: threading.Thread | None = None
        self.parked = threading.Event()
        self.waking = threading.Event()
        self.resume = threading.Event()
        self._armed = False

    def arm(self) -> None:
        """Hold the nominated thread the next time it re-acquires this lock."""
        self._armed = True

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        if blocking and self._armed and threading.current_thread() is self.gated_thread:
            self._armed = False
            self.waking.set()
            assert self.resume.wait(timeout=WAIT)
        return self._lock.acquire(blocking, timeout)

    def release(self) -> None:
        if threading.current_thread() is self.gated_thread:
            self.parked.set()
        self._lock.release()

    def locked(self) -> bool:
        # `threading.Condition` asks its mutex this from Python 3.14 on; a lock
        # that cannot answer fails the condition's ownership check outright.
        return self._lock.locked()

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.release()


def gated_lock() -> tuple[OperationLock, GatedLock]:
    """An `OperationLock` whose condition rides a mutex the test can gate.

    White-box on purpose: the condition's mutex is the only point at which a
    woken writer can be held outside the lock, and holding it there is what
    turns the capture-generation case from a race into a certainty.
    """
    lock = OperationLock()
    gated = GatedLock()
    # `Condition` needs only acquire/release from its lock, and falls back to
    # them when the lock supplies no `_release_save`/`_acquire_restore`/
    # `_is_owned` — which is exactly how `GatedLock` gets onto the wait path.
    # The cast says that to a checker; it changes nothing at runtime.
    lock._condition = threading.Condition(cast(threading.Lock, gated))
    return lock, gated


def spawn(
    work: Callable[[], None], *, gate: GatedLock | None = None
) -> tuple[threading.Thread, list[BaseException | None]]:
    """Run `work` in one thread, capturing whatever it raises.

    A gate is nominated before the thread starts, so the first release it makes
    — the one `Condition.wait` performs as it parks — is already observable.
    """
    caught: list[BaseException | None] = [None]

    def body() -> None:
        try:
            work()
        except BaseException as raised:  # noqa: BLE001 - the outcome is the assertion
            caught[0] = raised

    thread = threading.Thread(target=body)
    if gate is not None:
        gate.gated_thread = thread
    thread.start()
    return thread, caught


def joined(thread: threading.Thread) -> None:
    """A bounded join: a thread still alive after it is a thread that queued."""
    thread.join(timeout=WAIT)
    assert not thread.is_alive()


def take_as_writer(lock: OperationLock) -> None:
    with lock:
        pass


def take_as_capture(lock: OperationLock) -> None:
    with lock.capture():
        pass


def test_a_free_writer_holds_it_and_frees_it() -> None:
    lock = OperationLock()

    with lock:
        attempt, refused = spawn(lambda: take_as_capture(lock))
        joined(attempt)
    assert isinstance(refused[0], BuildContended)  # it really was held

    take_as_writer(lock)  # a later writer, arriving free, is not refused
    take_as_capture(lock)  # nor is a later capture: the release left nothing


def test_same_thread_writer_acquisition_is_reentrant_and_balanced() -> None:
    lock = OperationLock()
    order: list[str] = []

    def nested_writer() -> None:
        with lock:
            order.append("outer")
            with lock:
                order.append("inner")
            with pytest.raises(BuildContended), lock.capture():
                pass
        order.append("released")

    writer = threading.Thread(target=nested_writer, daemon=True)
    writer.start()
    writer.join(timeout=WAIT)

    assert not writer.is_alive(), "same-thread nested writer acquisition deadlocked"
    assert order == ["outer", "inner", "released"]
    take_as_capture(lock)


def test_an_unbalanced_writer_release_raises_and_clears_nothing() -> None:
    """The bare lock raised on an unbalanced release; losing that would let a
    writer's `__exit__` quietly hand away a capture's hold."""
    lock = OperationLock()

    with pytest.raises(RuntimeError):
        lock.__exit__(None, None, None)  # nothing held at all

    with lock.capture():
        with pytest.raises(RuntimeError):
            lock.__exit__(None, None, None)  # held, but not by a writer
        attempt, refused = spawn(lambda: take_as_writer(lock))
        joined(attempt)
        assert isinstance(refused[0], BuildHold)  # the capture still holds it

    take_as_writer(lock)  # and the capture's own release still frees it


def test_a_writer_behind_a_writer_queues_and_then_acquires() -> None:
    lock, gated = gated_lock()
    order: list[str] = []

    def second_writer() -> None:
        with lock:
            order.append("second")

    lock.__enter__()  # the first writer holds it
    order.append("first")
    second, refused = spawn(second_writer, gate=gated)
    # `parked` says only that the second writer released the mutex, which a
    # refusal would also do; that it *queued* is settled below, by having
    # acquired without refusing and strictly after the first writer left.
    assert gated.parked.wait(timeout=WAIT)
    lock.__exit__(None, None, None)

    joined(second)
    assert refused[0] is None
    assert order == ["first", "second"]


def test_a_capture_behind_a_writer_refuses_immediately() -> None:
    lock = OperationLock()

    with lock:
        attempt, refused = spawn(lambda: take_as_capture(lock))
        joined(attempt)  # a capture that queued would still be alive here

    assert isinstance(refused[0], BuildContended)


def test_a_capture_behind_a_capture_refuses_immediately() -> None:
    lock = OperationLock()

    with lock.capture():
        attempt, refused = spawn(lambda: take_as_capture(lock))
        joined(attempt)

    assert isinstance(refused[0], BuildContended)


def test_a_writer_arriving_during_a_capture_refuses() -> None:
    lock = OperationLock()

    with lock.capture():
        attempt, refused = spawn(lambda: take_as_writer(lock))
        joined(attempt)  # it refused on arrival; it never joined a queue

    assert isinstance(refused[0], BuildHold)
    take_as_writer(lock)  # the released capture leaves the lock usable


def test_writer_waiting_across_capture_generation_refuses() -> None:
    """The queued writer wakes to a capture that is already over.

    It queued behind another writer, legitimately. By the time it is notified,
    a capture has begun and ended: there is no holder left to see, only the
    generation the capture moved. Re-queueing here would let the write land on
    the far side of a snapshot it was never part of.
    """
    lock, gated = gated_lock()

    lock.__enter__()  # the first writer holds it
    queued, refused = spawn(lambda: take_as_writer(lock), gate=gated)
    assert gated.parked.wait(timeout=WAIT)  # the second writer is in the queue

    gated.arm()  # hold it outside the mutex once it is notified
    lock.__exit__(None, None, None)  # the first writer releases and notifies
    assert gated.waking.wait(timeout=WAIT)  # notified, still outside the lock

    take_as_capture(lock)  # a whole capture begins and ends in that window
    gated.resume.set()  # only now may the queued writer look at the state

    joined(queued)
    assert isinstance(refused[0], BuildHold)
