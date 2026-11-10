"""Invocation-scoped routes that ledger committed kernel writes."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from nodes.core.frontmatter import node_from_markdown
from nodes.core.write_plan import CreateOp, WritePlan

from beliefs.errors import SessionProtocolError, StoreWriteRefused
from beliefs.holdings.seam import StoreActSeam, StoreOutcomeView
from beliefs.permit import Authority
from beliefs.profile import ProfileSpec
from beliefs.runrecord import GuardedCommit, OperationPort

if TYPE_CHECKING:
    from beliefs.session.writer import WriterSession

__all__ = ["LedgeredPort", "ledgered_seam", "plan_records"]


def plan_records(plan: Sequence[object]) -> tuple[tuple[str, str], ...]:
    """Read each created record's uid and id from the plan's own bytes."""
    records: list[tuple[str, str]] = []
    for op in plan:
        if type(op) is not CreateOp:
            raise SessionProtocolError(f"a session route commits creates only; the plan carries {type(op).__name__}")
        node = node_from_markdown(op.content.decode("utf-8"))
        records.append((node.uid, node.id))
    return tuple(records)


class LedgeredPort:
    """An operation port bound to one current session invocation."""

    __slots__ = ("_inner", "_invocation", "_session")

    def __init__(self, session: WriterSession, invocation: str, inner: OperationPort) -> None:
        self._session = session
        self._invocation = invocation
        self._inner = inner

    @property
    def root(self) -> Path:
        return self._inner.root

    @property
    def profile(self) -> ProfileSpec:
        return self._inner.profile

    @property
    def authority(self) -> Authority:
        return self._inner.authority

    def preflight(self, plan: WritePlan) -> None:
        self._inner.preflight(plan)

    def append_intent(self, payload: bytes) -> str:
        with self._session._lock:
            self._session._require_current(self._invocation)
            return self._inner.append_intent(payload)

    def execute(self, plan: WritePlan) -> None:
        raise SessionProtocolError("a session route commits only fulfilling writes")

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> str:
        with self._session._lock:
            self._session._require_current(self._invocation)
            records = plan_records(plan)
            entry = self._inner.execute_fulfilling(plan, fulfills)
            self._session._record_committed(self._invocation, intent=fulfills, entry=entry, records=records)
            return entry

    def execute_fulfilling_guarded(
        self,
        plan: WritePlan,
        fulfills: str,
        *,
        guard: Callable[[Any], str | None],
        fallback: Callable[[str], WritePlan],
    ) -> GuardedCommit:
        """The guarded commit: each plan's
        records are read and validated before it reaches the inner port — the
        primary's before delegation, the fallback's inside the delegated call
        after the guard chose it — and one act line names the plan that
        committed."""
        with self._session._lock:
            self._session._require_current(self._invocation)
            records = plan_records(plan)
            chosen: list[tuple[tuple[str, str], ...]] = []

            def checked_fallback(reason: str) -> WritePlan:
                fallback_plan = fallback(reason)
                chosen.append(plan_records(fallback_plan))
                return fallback_plan

            commit = self._inner.execute_fulfilling_guarded(plan, fulfills, guard=guard, fallback=checked_fallback)
            committed = records if commit.reason is None else chosen[0]
            self._session._record_committed(self._invocation, intent=fulfills, entry=commit.entry, records=committed)
            return commit


def ledgered_seam(session: WriterSession, invocation: str, inner: StoreActSeam) -> StoreActSeam:
    """Guard a holdings seam and ledger each committed registration: a published
    observation on the corpus chain, and every store transaction on the store
    chain.

    A store call holds the session lock, then the store root's operation lock,
    across the call and its `act` line, so no other writer's line or close falls
    between them. Holdings takes the observer root's operation lock only around an
    intent append or a publication, never around a store call, so a writer holds
    one operation lock at a time. A store call that raises anything but
    `StoreWriteRefused` (the composition root's refusal of its arguments, before
    anything reaches the engine) marks the ledger failed before the exception
    propagates: the engine registers before it applies effects, so even a routine
    refusal does not prove that nothing registered, and no `act` line can describe
    a registration that rolled back."""

    def guarded(member: Callable[..., Any]) -> Callable[..., Any]:
        def call(*args: Any) -> Any:
            with session._lock:
                session._require_current(invocation)
                return member(*args)

        return call

    @contextmanager
    def corpus_lock(root: Path) -> Iterator[None]:
        with session._lock:
            session._require_current(invocation)
            with inner.corpus_lock(root):
                yield

    def publish_fulfilling(root: Path, plan: Sequence[object], intent: str) -> str:
        with session._lock:
            session._require_current(invocation)
            records = plan_records(plan)
            entry = inner.publish_fulfilling(root, plan, intent)
            session._record_committed(invocation, intent=intent, entry=entry, records=records)
            return entry

    @contextmanager
    def store_registration(root: Path) -> Iterator[None]:
        with session._lock:
            session._require_current(invocation)
            if Path(root) != session.store_root:
                raise SessionProtocolError(f"a store call names {root}, not this session's store root")
            with inner.corpus_lock(root):
                try:
                    yield
                except StoreWriteRefused:
                    raise
                except BaseException as caught:
                    session._ledger.fail(f"a store call may have registered: {type(caught).__name__}: {caught}")
                    raise

    def store_write(root: Path, path: str, content: bytes, intent: str) -> StoreOutcomeView:
        with store_registration(root):
            outcome = inner.store_write(root, path, content, intent)
            session._record_store_act(invocation, entry=outcome.entry, intent=intent)
            return outcome

    def store_delete(root: Path, path: str, intent: str) -> StoreOutcomeView:
        with store_registration(root):
            outcome = inner.store_delete(root, path, intent)
            session._record_store_act(invocation, entry=outcome.entry, intent=intent)
            return outcome

    def store_move(root: Path, source: str, destination: str, intent: str) -> StoreOutcomeView:
        with store_registration(root):
            outcome = inner.store_move(root, source, destination, intent)
            session._record_store_act(invocation, entry=outcome.entry, intent=intent)
            return outcome

    def store_create(root: Path, path: str, content: bytes, intent: str) -> StoreOutcomeView:
        with store_registration(root):
            outcome = inner.store_create(root, path, content, intent)
            session._record_store_act(invocation, entry=outcome.entry, intent=intent)
            return outcome

    return StoreActSeam(
        corpus_lock=corpus_lock,
        append_intent=guarded(inner.append_intent),
        publish_fulfilling=publish_fulfilling,
        read_path=guarded(inner.read_path),
        store_write=store_write,
        store_delete=store_delete,
        store_move=store_move,
        store_genesis=guarded(inner.store_genesis),
        store_refusal=inner.store_refusal,
        store_create=store_create,
    )
