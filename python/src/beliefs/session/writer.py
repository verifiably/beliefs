"""The attended writer session and its invocation-bound scoped writer
(writer-session design §3, §5)."""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, final

from nodes.core.node import Node

from beliefs.coordination import CoordinationAddress
from beliefs.corpus import CorpusWriter, Finding, OperationCommit, _operation_lock_for
from beliefs.errors import (
    PermitExceeded,
    PermitFact,
    ScienceError,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
)
from beliefs.holdings.seam import StoreActSeam
from beliefs.permit import Authority, RequiredCapabilities, WritePermit, permit_covers, scoped_authority
from beliefs.profile import ProfileSpec
from beliefs.sealed import sealed
from beliefs.session.ledger import (
    ActLine,
    LedgerWriter,
    require_hex,
    require_invocation_id,
    utc_now,
    validated_outcome,
)

__all__ = [
    "Claim",
    "ClaimDone",
    "ClaimFresh",
    "ClaimMismatch",
    "ClaimOpen",
    "KernelRefusalValue",
    "ScopedWriter",
    "WriterSession",
]


@sealed
@final
@dataclass(frozen=True)
class ClaimFresh:
    pass


@sealed
@final
@dataclass(frozen=True)
class ClaimDone:
    outcome: Mapping[str, object]


@sealed
@final
@dataclass(frozen=True)
class ClaimOpen:
    pass


@sealed
@final
@dataclass(frozen=True)
class ClaimMismatch:
    pass


Claim: TypeAlias = ClaimFresh | ClaimDone | ClaimOpen | ClaimMismatch


class KernelRefusalValue(Exception):
    """A value-style kernel refusal carried as an exception so the dispatcher has
    one normalization path (design §5). Unraised by this slice's seven methods."""

    def __init__(self, value: object) -> None:
        super().__init__(str(getattr(value, "reason", repr(value))))
        self.value = value


@dataclass
class _Invocation:
    command: str
    input_digest: str
    acts: list[ActLine]
    outcome: Mapping[str, object] | None


class WriterSession:
    """The trusted server-side object (design §3.1). Holds the ceiling, the
    ledger and the index; constructs no writer of its own."""

    def __init__(
        self,
        *,
        session_id: str,
        world_id: str,
        corpus_root: Path,
        corpus_id: str,
        operations_root: Path,
        ledger: LedgerWriter,
        writer_factory: Callable[[Authority], CorpusWriter],
        findings: tuple[Finding, ...] = (),
        ceiling: WritePermit | None = None,
        profile: ProfileSpec | None = None,
        store_root: Path | None = None,
        store_id: str | None = None,
        holdings_seam: StoreActSeam | None = None,
    ) -> None:
        self.session_id = require_hex(session_id, 32, "session id")
        self.actor = f"session:{self.session_id}"  # derived, never supplied (J4)
        self.world_id = require_hex(world_id, 32, "world id")
        self.corpus_root = Path(corpus_root)
        self.corpus_id = require_hex(corpus_id, 32, "corpus id")
        self.operations_root = Path(operations_root)
        self.findings = findings
        self._ledger = ledger
        self._writer_factory = writer_factory
        self._ceiling = WritePermit.full() if ceiling is None else ceiling
        if (store_root is None) != (store_id is None):
            raise TypeError("a session binds a store root and its id together, or neither")
        self.profile = profile
        self.store_root = None if store_root is None else Path(store_root)
        self.store_id = store_id
        self._holdings_seam = holdings_seam
        # Re-entrant: a scoped act holds this lock for its whole duration and the
        # helpers it calls take it again (§13 item 18). `claim_invocation` and
        # `close_invocation` are unchanged by that — they still take it once.
        self._lock = threading.RLock()
        self._index: dict[str, _Invocation] = {}
        self._current: str | None = None
        self._closed = False
        summary = self._ceiling.summary()
        self._ledger.append(
            {
                "line": "session-open",
                "session": self.session_id,
                "actor": self.actor,
                "world": self.world_id,
                "permit": {
                    "kinds": list(summary.kinds),
                    "act_families": list(summary.act_families),
                    "ungoverned": self._ceiling.ungoverned,
                },
                "at": utc_now(),
            }
        )

    # --- liveness -------------------------------------------------------------
    def _require_live(self) -> None:
        if self._ledger.failed:
            raise SessionLedgerFailed("the session ledger failed; this session is terminal")
        if self._closed:
            raise SessionClosed("the session is closed")

    @property
    def current_invocation(self) -> str | None:
        return self._current

    # --- the scoped writer -----------------------------------------------------
    def scoped(self, required: RequiredCapabilities, invocation_id: str) -> ScopedWriter:
        if type(required) is not RequiredCapabilities:
            raise TypeError("scoped judges a RequiredCapabilities")
        invocation = require_invocation_id(invocation_id)
        with self._lock:
            self._require_live()
        if not permit_covers(self._ceiling, required):
            summary = self._ceiling.summary()
            missing_family = sorted(required.permit.act_families - self._ceiling.act_families)
            if missing_family:
                raise PermitExceeded(PermitFact("family", missing_family[0]), summary)
            missing_kind = sorted(required.permit.kinds - self._ceiling.kinds)
            raise PermitExceeded(PermitFact("kind", missing_kind[0]), summary)
        authority = scoped_authority(required, self.actor)
        return ScopedWriter(self, self._writer_factory(authority), invocation, authority)

    # --- claims ------------------------------------------------------------------
    def claim_invocation(self, invocation_id: str, command: str, input_digest: str) -> Claim:
        invocation = require_invocation_id(invocation_id)
        if type(command) is not str or not command:
            raise ValueError("command must be a non-empty string")
        digest = require_hex(input_digest, 64, "input digest")
        with self._lock:
            self._require_live()
            entry = self._index.get(invocation)
            if entry is None:
                self._ledger.append(
                    {
                        "line": "invocation-open",
                        "invocation": invocation,
                        "command": command,
                        "input_digest": digest,
                        "at": utc_now(),
                    }
                )
                self._index[invocation] = _Invocation(command, digest, [], None)
                self._current = invocation
                return ClaimFresh()
            if entry.command != command or entry.input_digest != digest:
                return ClaimMismatch()
            if entry.outcome is None:
                return ClaimOpen()
            return ClaimDone(deepcopy(entry.outcome))  # the index is never handed out (§3.3)

    def close_invocation(self, invocation_id: str, outcome: Mapping[str, object]) -> None:
        invocation = require_invocation_id(invocation_id)
        validated = validated_outcome(outcome)
        with self._lock:
            self._require_live()
            if invocation != self._current:
                raise SessionProtocolError(f"{invocation} is not the current invocation ({self._current})")
            self._ledger.append({"line": "invocation-close", "invocation": invocation, "outcome": validated})
            self._index[invocation].outcome = validated
            self._current = None

    def invocation_acts(self, invocation_id: str) -> tuple[ActLine, ...]:
        invocation = require_invocation_id(invocation_id)
        with self._lock:
            self._require_live()
            entry = self._index.get(invocation)
            return () if entry is None else tuple(entry.acts)

    def _require_current(self, invocation: str) -> None:
        with self._lock:
            self._require_live()
            if self._current != invocation:
                raise SessionProtocolError(
                    f"writer bound to {invocation} cannot act; current invocation is {self._current}"
                )

    def _record_act(self, invocation: str, commit: OperationCommit) -> None:
        """Ledger one committed operation. Reached only from `ScopedWriter._act`,
        which already holds this lock and checked currency under it, so the
        re-check below is an invariant, not a refusal: an operation whose
        registration is durable can no longer be refused, and only a crash or a
        ledger I/O failure — both terminal — may leave it unledgered (§5,
        §13 item 18)."""
        with self._lock:
            self._require_live()
            if self._current != invocation:
                raise ScienceError(
                    f"the current invocation moved from {invocation} to {self._current} while an act "
                    "held the session lock"
                )
            records = [] if commit.record is None else [[commit.record.uid, commit.record.id]]
            self._ledger.append(
                {
                    "line": "act",
                    "invocation": invocation,
                    "corpus": self.corpus_id,
                    "entry": commit.entry_digest,
                    "intent": commit.intent_digest,
                    "records": records,
                }
            )
            self._index[invocation].acts.append(
                ActLine(
                    invocation,
                    self.corpus_id,
                    commit.entry_digest,
                    commit.intent_digest,
                    tuple((pair[0], pair[1]) for pair in records),
                )
            )

    # --- close -----------------------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            if self._ledger.failed:
                raise SessionLedgerFailed("the session ledger failed; this session is terminal")
            if self._closed:
                return
            self._ledger.append({"line": "session-close", "at": utc_now()})
            self._closed = True
            self._ledger.close()


class ScopedWriter:
    """The facade a handler holds (design §5): seven corpus-write methods, the
    two routes of the session-routes design §3.3, one invocation."""

    __slots__ = ("_authority", "_invocation", "_session", "_writer")

    def __init__(self, session: WriterSession, writer: CorpusWriter, invocation_id: str, authority: Authority) -> None:
        self._session = session
        self._writer = writer
        self._invocation = invocation_id
        self._authority = authority

    @property
    def invocation_id(self) -> str:
        return self._invocation

    @property
    def actor(self) -> str:
        """The session actor — also the scoped authority's, so the observer a
        command passes and the actor a boundary stamps agree."""
        return self._session.actor

    @property
    def store_id(self) -> str:
        store_id = self._session.store_id
        if store_id is None:
            raise SessionProtocolError("this session was opened with no store root; the holdings route has no store")
        return store_id

    def _act(self, perform: Callable[[], OperationCommit]) -> Node | None:
        """One act: currency, the commit and the `act` line as one atomic step.

        The session lock is taken first and held across `perform`, then the raw
        root lock (the one `_commit` nests in). That order — session, then
        root — is the only one taken anywhere: claims and closes take the
        session lock alone and nothing takes the root lock before the session
        lock, so the two never deadlock. Holding the session lock only for the
        currency check would leave a window in which another thread closes or
        re-claims between the durable commit and the ledger, producing a
        committed registration with no `act` line in a session that stays live
        (§13 item 18).
        """
        with self._session._lock, _operation_lock_for(self._writer.root):
            self._session._require_current(self._invocation)
            commit = perform()
            self._session._record_act(self._invocation, commit)
            return commit.record

    def add(self, node: Node) -> Node:
        record = self._act(lambda: self._writer.operations.add(node))
        assert record is not None
        return record

    def retract(self, record: Node) -> Node:
        minted = self._act(lambda: self._writer.operations.retract(record))
        assert minted is not None
        return minted

    def supersede(self, successor: Node, *, of: str) -> Node:
        minted = self._act(lambda: self._writer.operations.supersede(successor, of=of))
        assert minted is not None
        return minted

    def revise(self, node: Node) -> Node:
        minted = self._act(lambda: self._writer.operations.revise(node))
        assert minted is not None
        return minted

    def delete(self, ref: str) -> None:
        self._act(lambda: self._writer.operations.delete(ref))

    def mint_coordination(
        self, kind: str, *, project: CoordinationAddress | None = None, content: Mapping[str, object]
    ) -> Node:
        minted = self._act(lambda: self._writer.operations.mint_coordination(kind, project=project, content=content))
        assert minted is not None
        return minted

    def revise_coordination(
        self, kind: str, address: CoordinationAddress, *, predecessors: Sequence[str], content: Mapping[str, object]
    ) -> Node:
        minted = self._act(
            lambda: self._writer.operations.revise_coordination(
                kind, address, predecessors=predecessors, content=content
            )
        )
        assert minted is not None
        return minted
