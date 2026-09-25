"""The attended writer session and its invocation-bound scoped writer
(writer-session design §3, §5)."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, final

from nodes.core.node import Node

from beliefs.coordination import CoordinationAddress, CoordinationRefused
from beliefs.corpus import CoordinationResolver, CorpusWriter, Finding, OperationCommit, _operation_lock_for
from beliefs.errors import (
    CoordinationUnavailable,
    PermitExceeded,
    PermitFact,
    ProjectNotResolvable,
    ScienceError,
    SessionClosed,
    SessionLedgerFailed,
    SessionProtocolError,
)
from beliefs.holdings.seam import StoreActSeam
from beliefs.permit import Authority, RequiredCapabilities, WritePermit, permit_covers, scoped_authority
from beliefs.profile import ProfileSpec
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed
from beliefs.session.ledger import (
    ActLine,
    LedgerWriter,
    SelectLine,
    require_hex,
    require_invocation_id,
    utc_now,
    validated_outcome,
)

if TYPE_CHECKING:
    from beliefs.audit_operation import AuditOutcome
    from beliefs.corpus import ReadView
    from beliefs.evidence import DerivationEvidence
    from beliefs.holdings.acquire import AcquisitionOutcome, AcquisitionRequest
    from beliefs.holdings.boundary import ActContext
    from beliefs.holdings.recheck import RecheckOutcome
    from beliefs.holdings.records import HoldingsObservation, StoreLocator
    from beliefs.holdings.transport import UrlSeam
    from beliefs.world.view import WorldReadView

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
    one normalization path (design §5). Unraised by this slice's nine methods."""

    def __init__(self, value: object) -> None:
        super().__init__(str(getattr(value, "reason", repr(value))))
        self.value = value


@dataclass
class _Invocation:
    command: str
    input_digest: str
    acts: list[ActLine]
    outcome: Mapping[str, object] | None
    selection: SelectLine | None = None


def require_project_address(address: object) -> CoordinationAddress:
    """An unpinned project address: the only thing a caller may ask to select
    (selection design §4). The kernel pins it; a caller never supplies a revision."""
    if type(address) is not CoordinationAddress or address.local is not None or address.revision is not None:
        raise ValueError(f"a selection names an unpinned project address, not {address!r}")
    return address


def resolve_project(resolver: CoordinationResolver | None, address: CoordinationAddress) -> CoordinationAddress:
    """`address` resolved through `resolver` to its one standing `project` tip, and
    pinned to that revision (selection design decision 2)."""
    if resolver is None:
        raise CoordinationUnavailable(f"{address}: no coordination resolver is mounted to resolve a project")
    resolved = resolver.resolve(address)
    if resolved is None:
        raise ProjectNotResolvable(f"{address}: the selected project does not resolve")
    if isinstance(resolved, CoordinationRefused):
        raise ProjectNotResolvable(f"{address}: the selected project is divergent", tips=resolved.tips)
    if resolved.kind != "project":
        raise ProjectNotResolvable(f"{address}: resolves to a {resolved.kind}, not a project")
    return address.pinned(resolved.uid)


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
        coordination_resolver: CoordinationResolver | None = None,
        project: CoordinationAddress | None = None,
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
        if project is not None and (
            type(project) is not CoordinationAddress or project.local is not None or project.revision is None
        ):
            raise ValueError(f"an initial selection is a project address pinned to its revision, not {project!r}")
        self._coordination_resolver = coordination_resolver
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
                "project": None if project is None else str(project),
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

    # --- selection (selection design §4.2) -----------------------------------------------
    def select_project(self, invocation_id: str, address: CoordinationAddress | None) -> CoordinationAddress | None:
        """Ledger the current invocation's one selection change and return it
        pinned, or None for a clear. The index learns it only after the append
        returns; a failed append is terminal and leaves the index unchanged."""
        invocation = require_invocation_id(invocation_id)
        if address is not None:
            require_project_address(address)
        with self._lock:
            self._require_live()
            if invocation != self._current:
                raise SessionProtocolError(f"{invocation} cannot select; the current invocation is {self._current}")
            entry = self._index[invocation]
            if entry.selection is not None:
                raise SessionProtocolError(f"{invocation} already recorded its selection")
            pinned = None if address is None else resolve_project(self._coordination_resolver, address)
            self._ledger.append({"line": "select", "invocation": invocation, "project": None if pinned is None else str(pinned)})
            entry.selection = SelectLine(invocation, pinned)
            return pinned

    def invocation_selection(self, invocation_id: str) -> SelectLine | None:
        invocation = require_invocation_id(invocation_id)
        with self._lock:
            self._require_live()
            found = self._index.get(invocation)
            return None if found is None else found.selection

    def _require_current(self, invocation: str) -> None:
        with self._lock:
            self._require_live()
            if self._current != invocation:
                raise SessionProtocolError(
                    f"writer bound to {invocation} cannot act; current invocation is {self._current}"
                )

    def _record_committed(
        self, invocation: str, *, intent: str, entry: str, records: tuple[tuple[str, str], ...]
    ) -> None:
        """Ledger one committed write by its digests and record pairs. Reached
        only from `ScopedWriter._act` and the session routes, each of which
        already holds this lock and checked currency under it, so the
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
            self._ledger.append(
                {
                    "line": "act",
                    "invocation": invocation,
                    "corpus": self.corpus_id,
                    "entry": entry,
                    "intent": intent,
                    "records": [list(pair) for pair in records],
                }
            )
            self._index[invocation].acts.append(ActLine(invocation, self.corpus_id, entry, intent, records))

    def _record_act(self, invocation: str, commit: OperationCommit) -> None:
        records = () if commit.record is None else ((commit.record.uid, commit.record.id),)
        self._record_committed(invocation, intent=commit.intent_digest, entry=commit.entry_digest, records=records)

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
    """The facade a handler holds (design §5): nine corpus-write methods, the
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

    def operation_port(self) -> OperationPort:
        """Return this invocation's durable, act-ledgered run route."""
        from beliefs.session.routes import LedgeredPort

        port = self._writer._operation_port
        if port is None:
            raise SessionProtocolError("this scoped writer has no durable operation port")
        return LedgeredPort(self._session, self._invocation, port)

    def holdings_context(self, *, instrument: str) -> ActContext:
        """Return this invocation's durable, act-ledgered holdings route."""
        from beliefs.holdings.boundary import ActContext
        from beliefs.session.routes import ledgered_seam

        session = self._session
        if session.store_root is None or session._holdings_seam is None or session.profile is None:
            raise SessionProtocolError("this session was opened with no store root; the holdings route has no store")
        return ActContext(
            observer_root=session.corpus_root,
            store_root=session.store_root,
            observer=session.actor,
            instrument=instrument,
            authority=self._authority,
            seam=ledgered_seam(session, self._invocation, session._holdings_seam),
            profile=session.profile,
        )

    def acquire(
        self,
        request: AcquisitionRequest,
        *,
        instrument: str,
        scratch: Path,
        seam: UrlSeam | None = None,
        standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    ) -> AcquisitionOutcome:
        """This invocation's acquisition route (url-retrieval design §8): the
        holdings context supplies the ledgered store seam, `operation_port()` the
        ledgered operation port, and no lock of this facade is held across the
        request (decision 15)."""
        from beliefs.holdings.acquire import acquire as run_acquisition
        from beliefs.holdings.transport import url_seam

        ctx = self.holdings_context(instrument=instrument)
        return run_acquisition(
            ctx, self._writer, request, seam=url_seam() if seam is None else seam, scratch=scratch,
            standing=standing, port=self.operation_port(), hold=self._closing_hold,
        )

    def audit(self, *, instrument: str, evidence: DerivationEvidence) -> AuditOutcome:
        """This invocation's audit route (act-report-remainder design §5): the
        ledgered operation port, and this session's lock taken before the root
        lock across the whole operation — the evaluator reads the writer's own
        index and does no I/O outside the root (decision 4)."""
        from beliefs.audit_operation import audit as run_audit

        return run_audit(
            self._writer, observer=self._session.actor, instrument=instrument, evidence=evidence,
            port=self.operation_port(), hold=self._closing_hold,
        )

    def recheck(
        self,
        locations: tuple[StoreLocator, ...],
        *,
        instrument: str,
        standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    ) -> RecheckOutcome:
        """This invocation's re-check route (act-report-remainder design §5):
        the holdings context supplies the ledgered store seam, `operation_port()`
        the ledgered operation port, and no lock of this facade is held across
        an act (decision 6)."""
        from beliefs.holdings.recheck import recheck_locations

        ctx = self.holdings_context(instrument=instrument)
        return recheck_locations(
            ctx, self._writer, locations, standing=standing, port=self.operation_port(), hold=self._closing_hold,
        )

    @contextmanager
    def _closing_hold(self) -> Iterator[None]:
        """The acquisition's close under this session's lock, taken before the
        root lock exactly as `_act` takes it, currency re-checked on entry (§13
        item 18). The ledgered port's `execute_fulfilling` re-enters the same
        `RLock` inside."""
        with self._session._lock:
            self._session._require_current(self._invocation)
            yield

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

    def attest_coreference(self, record: Node, *, view: ReadView | WorldReadView | None = None) -> Node:
        minted = self._act(lambda: self._writer.operations.attest_coreference(record, view=view))
        assert minted is not None
        return minted

    def correct_identifier(self, ref: str, identifiers: Mapping[str, object], *, grounds: str) -> Node:
        minted = self._act(lambda: self._writer.operations.correct_identifier(ref, identifiers, grounds=grounds))
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
