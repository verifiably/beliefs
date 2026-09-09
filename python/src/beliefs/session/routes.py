"""Invocation-scoped routes that ledger committed kernel writes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from nodes.core.frontmatter import node_from_markdown
from nodes.core.write_plan import CreateOp, WritePlan

from beliefs.errors import SessionProtocolError
from beliefs.permit import Authority
from beliefs.profile import ProfileSpec
from beliefs.runrecord import OperationPort

if TYPE_CHECKING:
    from beliefs.session.writer import WriterSession

__all__ = ["LedgeredPort", "plan_records"]


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
    ) -> str | None:
        raise SessionProtocolError("the guarded execution path is outside the session routes")
