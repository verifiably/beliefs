"""Reconciliation (writer-session design §6): chains are truth, the ledger is
evidence. A pure classification over ledger evidence and detached chain views;
it writes nothing, recovers nothing, and never raises on ledger state."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from beliefs.corpus import Finding
from beliefs.intents import shapes
from beliefs.report import OperationIntent
from beliefs.session.ledger import LedgerEmpty, LedgerEvidence, LedgerMissing, LedgerReader, LedgerUnreadable
from beliefs.world.logmodel import (
    AbsentView,
    ChainView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)

__all__ = ["reconcile"]

_SESSION_ACTOR = re.compile(r"session:([0-9a-f]{32})")

_NO_CORPUS = "\uffff"
"""The sort key's corpus slot for a finding about a ledger rather than a chain.

§13 item 6 makes the key internal — `(corpus_id, position, code, ref)` — and
§6 orders findings by corpus id first. A ledger-level finding names no corpus,
so it sorts after every corpus's own: a corpus id is 32 lowercase hexadecimal
characters, and this sentinel is above all of them.
"""

_LEDGER_CLAIM = 1 << 30
"""The position slot for `session-act-unverified`: a ledger's claim about a
corpus, ordered after every entry that corpus actually holds."""


def _finding(severity: str, code: str, ref: str, detail: str, message: str) -> Finding:
    return Finding(severity=severity, code=code, ref=ref, detail=detail, message=message)


def reconcile(ledgers: Sequence[LedgerEvidence], chains: Mapping[str, ChainView]) -> tuple[Finding, ...]:
    """§6's classification: one finding per state, ordered deterministically."""
    by_session: dict[str, LedgerEvidence] = {evidence.session_id: evidence for evidence in ledgers}
    keyed: list[tuple[tuple[str, int, str, str], Finding]] = []

    # --- ledger-level evidence ---------------------------------------------------
    for evidence in ledgers:
        sid = evidence.session_id
        if type(evidence) is LedgerMissing:
            keyed.append(
                (
                    (_NO_CORPUS, 0, "session-ledger-missing", sid),
                    _finding(
                        "warning",
                        "session-ledger-missing",
                        sid,
                        "",
                        "a session directory with no ledger file: creation was interrupted",
                    ),
                )
            )
        elif type(evidence) is LedgerEmpty:
            keyed.append(
                (
                    (_NO_CORPUS, 0, "session-ledger-empty", sid),
                    _finding(
                        "warning",
                        "session-ledger-empty",
                        sid,
                        "",
                        "an empty ledger: the session-open line never landed",
                    ),
                )
            )
        elif type(evidence) is LedgerUnreadable:
            keyed.append(
                (
                    (_NO_CORPUS, 0, "session-ledger-malformed", sid),
                    _finding(
                        "error",
                        "session-ledger-malformed",
                        sid,
                        evidence.error,
                        "the ledger reader refused this ledger",
                    ),
                )
            )
        else:
            assert type(evidence) is LedgerReader
            if not evidence.closed:
                keyed.append(
                    (
                        (_NO_CORPUS, 0, "session-unclosed", sid),
                        _finding(
                            "warning",
                            "session-unclosed",
                            sid,
                            f"open_invocations={list(evidence.open_invocations)}",
                            "a ledger with no session-close",
                        ),
                    )
                )
            if evidence.torn_tail:
                keyed.append(
                    (
                        (_NO_CORPUS, 0, "ledger-torn-tail", sid),
                        _finding(
                            "warning",
                            "ledger-torn-tail",
                            sid,
                            "",
                            "the ledger ends mid-line: the last append was interrupted",
                        ),
                    )
                )

    committed_everywhere: set[str] = set()
    well_formed: set[str] = set()

    # --- per corpus -------------------------------------------------------------------
    for corpus_id in sorted(chains):
        view = chains[corpus_id]
        if type(view) is AbsentView:
            keyed.append(
                (
                    (corpus_id, 0, "session-chain-absent", corpus_id),
                    _finding(
                        "error", "session-chain-absent", corpus_id, "", "no durable chain to compare against"
                    ),
                )
            )
            continue
        if type(view) is MalformedView:
            defect = view.defect
            keyed.append(
                (
                    (corpus_id, 0, "session-chain-malformed", corpus_id),
                    _finding(
                        "error",
                        "session-chain-malformed",
                        corpus_id,
                        f"{defect.kind}: {defect.detail}",
                        "the chain is malformed; nothing is classified",
                    ),
                )
            )
            continue
        assert type(view) is WellFormedView
        well_formed.add(corpus_id)
        entries = view.entries
        settlement = {entry.registration: entry.committed for entry in entries if type(entry) is SettledEntryView}
        by_fulfills: dict[str, list[RegisteredEntryView]] = {}
        for entry in entries:
            if type(entry) is RegisteredEntryView and entry.fulfills is not None:
                by_fulfills.setdefault(entry.fulfills, []).append(entry)
        digests = {entry.digest for entry in entries}
        committed_everywhere |= {digest for digest, committed in settlement.items() if committed}

        for txid, staged in view.pending:
            if staged not in digests:
                keyed.append(
                    (
                        (corpus_id, len(entries), "session-chain-pending", staged),
                        _finding(
                            "warning",
                            "session-chain-pending",
                            staged,
                            f"txid={txid}",
                            "a staged registration the detached view reports outside its entries; "
                            "the next write's recovery settles it",
                        ),
                    )
                )

        for position, entry in enumerate(entries):
            if type(entry) is not IntentEntryView:
                continue
            decoded = shapes.decode_intent(entry.digest, entry.payload)
            if type(decoded) is not shapes.DecodedIntent or not isinstance(decoded.value, OperationIntent):
                continue
            match = _SESSION_ACTOR.fullmatch(decoded.value.actor)
            if match is None:
                continue
            sid = match.group(1)
            evidence = by_session.get(sid)
            if evidence is None:
                keyed.append(
                    (
                        (corpus_id, position, "session-unknown", entry.digest),
                        _finding(
                            "error",
                            "session-unknown",
                            entry.digest,
                            f"actor={decoded.value.actor}",
                            "an intent by a session with no ledger under this operations root",
                        ),
                    )
                )
                continue
            reader = evidence if type(evidence) is LedgerReader else None
            open_invocations = list(reader.open_invocations) if reader is not None else []
            unknown = reader is None or bool(open_invocations)
            acts: set[str] = {act.entry for act in reader.acts()} if reader is not None else set()
            registrations = by_fulfills.get(entry.digest, [])
            committed = [r for r in registrations if settlement.get(r.digest) is True]
            pending = [r for r in registrations if settlement.get(r.digest) is None]
            if committed:
                for r in committed:
                    if r.digest in acts:
                        continue
                    if unknown:
                        keyed.append(
                            (
                                (corpus_id, position, "session-outcome-unknown", r.digest),
                                _finding(
                                    "warning",
                                    "session-outcome-unknown",
                                    r.digest,
                                    f"session={sid} invocations={open_invocations} intent={entry.digest}",
                                    "a committed session write no act line covers, under an open "
                                    "invocation or an unreadable ledger",
                                ),
                            )
                        )
                    else:
                        keyed.append(
                            (
                                (corpus_id, position, "session-entry-foreign", r.digest),
                                _finding(
                                    "error",
                                    "session-entry-foreign",
                                    r.digest,
                                    f"session={sid} intent={entry.digest}",
                                    "a committed session write no act line covers and no open "
                                    "invocation explains",
                                ),
                            )
                        )
            elif pending:
                for r in pending:
                    keyed.append(
                        (
                            (corpus_id, position, "session-entry-pending", r.digest),
                            _finding(
                                "warning",
                                "session-entry-pending",
                                r.digest,
                                f"session={sid} intent={entry.digest}",
                                "an unsettled registration fulfilling a session intent; reported, "
                                "not adjudicated",
                            ),
                        )
                    )
            elif unknown:
                keyed.append(
                    (
                        (corpus_id, position, "session-outcome-unknown", entry.digest),
                        _finding(
                            "warning",
                            "session-outcome-unknown",
                            entry.digest,
                            f"session={sid} invocations={open_invocations}",
                            "a session intent with no registration, under an open invocation or an "
                            "unreadable ledger",
                        ),
                    )
                )
            else:
                keyed.append(
                    (
                        (corpus_id, position, "session-intent-unclaimed", entry.digest),
                        _finding(
                            "error",
                            "session-intent-unclaimed",
                            entry.digest,
                            f"session={sid}",
                            "a session intent no registration fulfills and no open invocation explains",
                        ),
                    )
                )

    # --- ledger claims the chains lack -------------------------------------------------
    # Only a well-formed view is truth to compare a claim against: §6 classifies
    # nothing for a corpus whose view is absent or malformed, and a corpus with no
    # view at all (its root was not read) is not evidence either way.
    for evidence in ledgers:
        if type(evidence) is not LedgerReader:
            continue
        for act in evidence.acts():
            if act.corpus in well_formed and act.entry not in committed_everywhere:
                keyed.append(
                    (
                        (act.corpus, _LEDGER_CLAIM, "session-act-unverified", act.entry),
                        _finding(
                            "error",
                            "session-act-unverified",
                            act.entry,
                            f"session={evidence.session_id} invocation={act.invocation}",
                            "an act line naming a registration no chain holds as committed; chains are truth",
                        ),
                    )
                )

    keyed.sort(key=lambda pair: pair[0])
    return tuple(finding for _, finding in keyed)
