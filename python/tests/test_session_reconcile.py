"""J8 portably: every intent, chain and ledger state of design §6 over stand-in
views and ledger evidence, plus one composition test that `reconcile_sessions`
returns §6's order over a real root."""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import FULL
from fixtures_cut6 import PINS
from profiles import WITH_BIOLOGY

from beliefs.corpus import CorpusWriter
from beliefs.identity import v1
from beliefs.root import durable_executor_factory, init_corpus_root
from beliefs.session import reconcile_sessions
from beliefs.session.ledger import LedgerEmpty, LedgerMissing, LedgerReader, LedgerUnreadable, encode_line, ledger_path
from beliefs.session.ledger import _parse as parse_ledger
from beliefs.session.reconcile import reconcile
from beliefs.world.logmodel import (
    AbsentView,
    DefectView,
    GenesisEntryView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
    WellFormedView,
)
from beliefs.world.registry import WorldConfig

S1 = "1" * 32
CORPUS = "c" * 32
AT = "2026-09-05T12:00:00Z"
WORLD = "a" * 32  # a world id is 32 lowercase hexadecimal characters (the ledger validates it)


def intent(digest: str, session: str = S1, kind: str = "corpus-write") -> IntentEntryView:
    return IntentEntryView(digest=digest, payload=v1.encode({"kind": kind, "event_token": "tok-" + digest[:4], "actor": f"session:{session}"}))


def registration(digest: str, fulfills: str) -> RegisteredEntryView:
    return RegisteredEntryView(digest=digest, txid="t" + digest[:4], initial=(), final=(), fulfills=fulfills)


def settled(registration_digest: str, committed: bool) -> SettledEntryView:
    return SettledEntryView(digest="s" + registration_digest[1:], txid="t", registration=registration_digest, committed=committed)


def genesis() -> GenesisEntryView:
    return GenesisEntryView(digest="g" * 64, payload=b"", baseline=())


def view(*entries, pending=()) -> WellFormedView:
    return WellFormedView(genesis=genesis(), entries=(genesis(), *entries), tip=entries[-1].digest if entries else "g" * 64, pending=tuple(pending))


def ledger(session: str = S1, *, opens=(), closes=(), acts=(), closed=True) -> LedgerReader:
    lines = [{"line": "session-open", "session": session, "actor": f"session:{session}", "world": WORLD,
              "permit": {"kinds": [], "act_families": [], "ungoverned": True}, "at": AT}]
    for invocation in opens:
        lines.append({"line": "invocation-open", "invocation": invocation, "command": "mint", "input_digest": "d" * 64, "at": AT})
    for invocation, entry, intent_digest in acts:
        lines.append({"line": "act", "invocation": invocation, "corpus": CORPUS, "entry": entry, "intent": intent_digest, "records": []})
    for invocation in closes:
        lines.append({"line": "invocation-close", "invocation": invocation, "outcome": {"done": []}})
    if closed:
        lines.append({"line": "session-close", "at": AT})
    return parse_ledger(session, b"".join(encode_line(line) for line in lines))


def codes(findings):
    return [(f.code, f.severity, f.ref) for f in findings]


I, R = "a" * 64, "b" * 64  # an intent and a registration digest: 64 lowercase hexadecimal characters


def test_a_covered_registration_yields_nothing():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),))], chains) == ()


def test_uncovered_committed_registration_under_an_open_invocation_is_outcome_unknown():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    findings = reconcile([ledger(opens=("A", "B"), closes=("B",), closed=False)], chains)
    assert ("session-outcome-unknown", "warning", R) in codes(findings)
    unknown = next(f for f in findings if f.code == "session-outcome-unknown")
    assert "invocations=['A']" in unknown.detail and f"intent={I}" in unknown.detail
    assert ("session-unclosed", "warning", S1) in codes(findings)


def test_uncovered_committed_registration_with_no_open_invocation_is_foreign():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    assert codes(reconcile([ledger()], chains)) == [("session-entry-foreign", "error", R)]


def test_an_unsettled_registration_is_pending():
    chains = {CORPUS: view(intent(I), registration(R, I))}
    assert codes(reconcile([ledger()], chains)) == [("session-entry-pending", "warning", R)]


def test_a_rolled_back_registration_is_no_registration():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, False))}
    assert codes(reconcile([ledger()], chains)) == [("session-intent-unclaimed", "error", I)]


def test_an_intent_with_no_registration_under_an_open_invocation_is_outcome_unknown():
    chains = {CORPUS: view(intent(I))}
    assert codes(reconcile([ledger(opens=("A",), closed=False)], chains))[0] == ("session-outcome-unknown", "warning", I)


def test_an_unknown_session_actor_is_reported():
    chains = {CORPUS: view(intent(I, session="9" * 32))}
    assert codes(reconcile([ledger()], chains)) == [("session-unknown", "error", I)]


def test_an_ordinary_actor_is_never_classified():
    payload = v1.encode({"kind": "corpus-write", "event_token": "t", "actor": "test-actor"})
    chains = {CORPUS: view(IntentEntryView(digest=I, payload=payload))}
    assert reconcile([ledger()], chains) == ()


@pytest.mark.parametrize("evidence, code, severity", [
    (LedgerMissing(S1), "session-ledger-missing", "warning"),
    (LedgerEmpty(S1), "session-ledger-empty", "warning"),
    (LedgerUnreadable(S1, "line 3: bad"), "session-ledger-malformed", "error"),
])
def test_unreadable_ledgers_are_findings_and_their_intents_read_outcome_unknown(evidence, code, severity):
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    found = codes(reconcile([evidence], chains))
    assert (code, severity, S1) in found and ("session-outcome-unknown", "warning", R) in found


def test_a_torn_tail_is_reported():
    torn = parse_ledger(S1, encode_line({"line": "session-open", "session": S1, "actor": f"session:{S1}", "world": WORLD,
                                          "permit": {"kinds": [], "act_families": [], "ungoverned": True}, "at": AT}) + b'{"line":"inv')
    assert ("ledger-torn-tail", "warning", S1) in codes(reconcile([torn], {CORPUS: view()}))


def test_an_act_line_the_chain_does_not_hold_is_unverified():
    chains = {CORPUS: view(intent(I))}
    findings = reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),))], chains)
    assert ("session-act-unverified", "error", R) in codes(findings)


def test_the_views_pending_pairs_absent_from_entries_are_reported_without_an_intent():
    staged = "e" * 64
    chains = {CORPUS: view(intent(I), pending=(("txid-1", staged),))}
    found = reconcile([ledger()], chains)
    pending = next(f for f in found if f.code == "session-chain-pending")
    assert pending.ref == staged and "txid-1" in pending.detail and "intent" not in pending.detail


def test_absent_and_malformed_views_classify_nothing():
    found = reconcile([ledger()], {CORPUS: AbsentView(), "d" * 32: MalformedView(DefectView(kind="foreign-leaf", subject="x", detail="y"))})
    assert codes(found) == [("session-chain-absent", "error", CORPUS), ("session-chain-malformed", "error", "d" * 32)]


def test_results_are_deterministic():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True), intent("j" * 64))}
    ledgers = [ledger(opens=("A",), closed=False), LedgerMissing("2" * 32)]
    assert reconcile(ledgers, chains) == reconcile(list(reversed(ledgers)), dict(chains))


def test_an_act_naming_a_corpus_with_no_truth_is_not_unverified():
    """§6: a malformed or absent view classifies nothing for that corpus, and a
    corpus `chains` does not carry is not evidence either way."""
    acts = (("A", R, I),)
    malformed = {CORPUS: MalformedView(DefectView(kind="foreign-leaf", subject="x", detail="y"))}
    found = codes(reconcile([ledger(opens=("A",), closes=("A",), acts=acts)], malformed))
    assert found == [("session-chain-malformed", "error", CORPUS)]

    absent = {CORPUS: AbsentView()}
    assert codes(reconcile([ledger(opens=("A",), closes=("A",), acts=acts)], absent)) == [
        ("session-chain-absent", "error", CORPUS)
    ]

    unread = {"d" * 32: view(intent(I))}
    assert "session-act-unverified" not in [
        code for code, _, _ in codes(reconcile([ledger(opens=("A",), closes=("A",), acts=acts)], unread))
    ]


def test_findings_are_ordered_by_corpus_then_position_not_grouped_by_code():
    """§6's order: corpus id, then chain position, then code.

    Both halves are pinned against a sort by code: within `CORPUS` the later
    entry's `session-entry-foreign` follows the earlier entry's
    `session-intent-unclaimed`, and the second corpus's findings follow both.
    """
    other = "d" * 32
    j, k, m = "c" * 64, "d" * 64, "e" * 64
    chains = {
        other: view(intent(m)),
        CORPUS: view(intent(I), intent(j), registration(k, j), settled(k, True)),
    }
    assert codes(reconcile([ledger()], chains)) == [
        ("session-intent-unclaimed", "error", I),
        ("session-entry-foreign", "error", k),
        ("session-intent-unclaimed", "error", m),
    ]


def test_reconcile_sessions_keeps_the_reconcile_order_and_leads_with_the_unadopted_roots(certified_work):
    """§6's order is `reconcile`'s own, not a re-sort by code: an unadopted root
    leads even though `ledger-torn-tail` sorts before `session-corpus-unadopted`."""
    root, unadopted, ops = certified_work / "corpus", certified_work / "nope", certified_work / "ops"
    init_corpus_root(root, authority=FULL)
    CorpusWriter(root, durable_executor_factory(), authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
    config = WorldConfig(world_root=certified_work / "world", world_id=WORLD, corpus_roots=(root, unadopted))

    torn = ledger_path(ops, S1)
    torn.parent.mkdir(parents=True)
    torn.write_bytes(
        encode_line({"line": "session-open", "session": S1, "actor": f"session:{S1}", "world": WORLD,
                     "permit": {"kinds": [], "act_families": [], "ungoverned": True}, "at": AT})
        + b'{"line":"inv'
    )
    (Path(ops) / "sessions" / ("2" * 32)).mkdir()

    found = codes(reconcile_sessions(config, ops, exclude="2" * 32))
    assert found == [
        ("session-corpus-unadopted", "error", str(unadopted)),
        ("ledger-torn-tail", "warning", S1),
        ("session-unclosed", "warning", S1),
    ]
    assert codes(reconcile_sessions(config, ops)) == [
        ("session-corpus-unadopted", "error", str(unadopted)),
        ("ledger-torn-tail", "warning", S1),
        ("session-ledger-missing", "warning", "2" * 32),
        ("session-unclosed", "warning", S1),
    ]
