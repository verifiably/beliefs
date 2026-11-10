"""Reconciliation, portably: every intent, chain and ledger state over stand-in
views and ledger evidence, plus one composition test that `reconcile_sessions`
returns the specified order over a real root."""

from __future__ import annotations

from pathlib import Path

import pytest
from authority import FULL
from fixtures_cut6 import PINS
from profiles import BASE, WITH_BIOLOGY

from beliefs.corpus import CorpusWriter
from beliefs.holdings.boundary import intent_payload
from beliefs.holdings.qualify import decode_holdings_intent
from beliefs.holdings.records import StoreLocator, url_locator
from beliefs.identity import v1
from beliefs.root import durable_executor_factory, init_corpus_root, log_seam
from beliefs.session import open_attended_session, open_ledger_reader, reconcile_sessions
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
    return IntentEntryView(
        digest=digest,
        payload=v1.encode({"kind": kind, "event_token": "tok-" + digest[:4], "actor": f"session:{session}"}),
    )


def registration(digest: str, fulfills: str) -> RegisteredEntryView:
    return RegisteredEntryView(digest=digest, txid="t" + digest[:4], initial=(), final=(), fulfills=fulfills)


def settled(registration_digest: str, committed: bool) -> SettledEntryView:
    return SettledEntryView(
        digest="s" + registration_digest[1:], txid="t", registration=registration_digest, committed=committed
    )


def genesis() -> GenesisEntryView:
    return GenesisEntryView(digest="g" * 64, payload=b"", baseline=())


def view(*entries, pending=()) -> WellFormedView:
    return WellFormedView(
        genesis=genesis(),
        entries=(genesis(), *entries),
        tip=entries[-1].digest if entries else "g" * 64,
        pending=tuple(pending),
    )


def ledger(session: str = S1, *, opens=(), closes=(), acts=(), closed=True, corpus: str = CORPUS) -> LedgerReader:
    lines = [
        {
            "line": "session-open",
            "session": session,
            "actor": f"session:{session}",
            "world": WORLD,
            "permit": {"kinds": [], "act_families": [], "ungoverned": True},
            "at": AT,
        }
    ]
    for invocation in opens:
        lines.append(
            {"line": "invocation-open", "invocation": invocation, "command": "mint", "input_digest": "d" * 64, "at": AT}
        )
    for invocation, entry, intent_digest in acts:
        lines.append(
            {
                "line": "act",
                "invocation": invocation,
                "corpus": corpus,
                "entry": entry,
                "intent": intent_digest,
                "records": [],
            }
        )
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
    assert codes(reconcile([ledger(opens=("A",), closed=False)], chains))[0] == (
        "session-outcome-unknown",
        "warning",
        I,
    )


def test_an_unknown_session_actor_is_reported():
    chains = {CORPUS: view(intent(I, session="9" * 32))}
    assert codes(reconcile([ledger()], chains)) == [("session-unknown", "error", I)]


def test_an_ordinary_actor_is_never_classified():
    payload = v1.encode({"kind": "corpus-write", "event_token": "t", "actor": "test-actor"})
    chains = {CORPUS: view(IntentEntryView(digest=I, payload=payload))}
    assert reconcile([ledger()], chains) == ()


@pytest.mark.parametrize(
    "evidence, code, severity",
    [
        (LedgerMissing(S1), "session-ledger-missing", "warning"),
        (LedgerEmpty(S1), "session-ledger-empty", "warning"),
        (LedgerUnreadable(S1, "line 3: bad"), "session-ledger-malformed", "error"),
    ],
)
def test_unreadable_ledgers_are_findings_and_their_intents_read_outcome_unknown(evidence, code, severity):
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True))}
    found = codes(reconcile([evidence], chains))
    assert (code, severity, S1) in found and ("session-outcome-unknown", "warning", R) in found


def test_a_torn_tail_is_reported():
    torn = parse_ledger(
        S1,
        encode_line(
            {
                "line": "session-open",
                "session": S1,
                "actor": f"session:{S1}",
                "world": WORLD,
                "permit": {"kinds": [], "act_families": [], "ungoverned": True},
                "at": AT,
            }
        )
        + b'{"line":"inv',
    )
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
    found = reconcile(
        [ledger()],
        {CORPUS: AbsentView(), "d" * 32: MalformedView(DefectView(kind="foreign-leaf", subject="x", detail="y"))},
    )
    assert codes(found) == [("session-chain-absent", "error", CORPUS), ("session-chain-malformed", "error", "d" * 32)]


def test_results_are_deterministic():
    chains = {CORPUS: view(intent(I), registration(R, I), settled(R, True), intent("j" * 64))}
    ledgers = [ledger(opens=("A",), closed=False), LedgerMissing("2" * 32)]
    assert reconcile(ledgers, chains) == reconcile(list(reversed(ledgers)), dict(chains))


def test_an_act_naming_a_corpus_with_no_truth_is_not_unverified():
    """A malformed or absent view classifies nothing for that corpus, and a
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
    """The order: corpus id, then chain position, then code.

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
    """The order is `reconcile`'s own, not a re-sort by code: an unadopted root
    leads even though `ledger-torn-tail` sorts before `session-corpus-unadopted`."""
    root, unadopted, ops = certified_work / "corpus", certified_work / "nope", certified_work / "ops"
    init_corpus_root(root, authority=FULL)
    CorpusWriter(root, durable_executor_factory(), authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
    config = WorldConfig(world_root=certified_work / "world", world_id=WORLD, corpus_roots=(root, unadopted))

    torn = ledger_path(ops, S1)
    torn.parent.mkdir(parents=True)
    torn.write_bytes(
        encode_line(
            {
                "line": "session-open",
                "session": S1,
                "actor": f"session:{S1}",
                "world": WORLD,
                "permit": {"kinds": [], "act_families": [], "ungoverned": True},
                "at": AT,
            }
        )
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


# --- the run and holdings shapes ----------------------
def run_intent(digest: str, session: str = S1) -> IntentEntryView:
    return IntentEntryView(
        digest=digest,
        payload=v1.encode({"spec_identity": "5" * 64, "event_token": "tok", "actor": f"session:{session}"}),
    )


def holdings_intent(digest: str, session: str = S1) -> IntentEntryView:
    payload = intent_payload(
        location=StoreLocator("1" * 32, "p.bin"), act_kind="write", event_token="tok", actor=f"session:{session}"
    )
    return IntentEntryView(digest=digest, payload=payload)


def url_intent(digest: str, session: str = S1) -> IntentEntryView:
    payload = intent_payload(
        location=url_locator("https://example.org/a"),
        act_kind="re-check",
        event_token="tok",
        actor=f"session:{session}",
    )
    return IntentEntryView(digest=digest, payload=payload)


def test_the_decoded_holdings_intent_carries_its_actor():
    entry = holdings_intent(I)
    decoded = decode_holdings_intent({"digest": I, "entry": {"payload": entry.payload.hex()}})
    assert decoded is not None and decoded["actor"] == f"session:{S1}"


# --- matching by (corpus, digest) -----

A_ID, B_ID = "a" * 32, "b" * 32


def _misattributed():
    """A ledger naming corpus A over a registration committed in B's chain."""
    chains = {A_ID: view(), B_ID: view(intent(I), registration(R, I), settled(R, True))}
    return codes(reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),), corpus=A_ID)], chains))


def test_a_registration_in_another_corpus_than_its_act_names_is_foreign_there():
    """The forward direction."""
    assert ("session-entry-foreign", "error", R) in _misattributed()


def test_an_act_naming_a_corpus_that_does_not_hold_it_is_unverified():
    """The backward direction."""
    assert ("session-act-unverified", "error", R) in _misattributed()


def test_the_same_act_naming_the_corpus_that_holds_it_is_covered():
    chains = {A_ID: view(), B_ID: view(intent(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),), corpus=B_ID)], chains) == ()


def test_an_act_naming_an_unconfigured_corpus_is_not_unverified():
    """Review Focus 5: no chain here is truth for it."""
    chains = {A_ID: view()}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),), corpus="e" * 32)], chains) == ()


@pytest.mark.parametrize("shape", [run_intent, holdings_intent, url_intent])
def test_a_session_intent_of_either_shape_with_no_ledger_is_unknown(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert ("session-unknown", "error", I) in codes(reconcile([], chains))


@pytest.mark.parametrize("shape", [run_intent, holdings_intent, url_intent])
def test_an_uncovered_registration_of_either_shape_is_foreign_when_closed(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert ("session-entry-foreign", "error", R) in codes(reconcile([ledger(opens=("A",), closes=("A",))], chains))


@pytest.mark.parametrize("shape", [run_intent, holdings_intent, url_intent])
def test_an_uncovered_registration_of_either_shape_is_outcome_unknown_when_open(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert ("session-outcome-unknown", "warning", R) in codes(reconcile([ledger(opens=("A",), closed=False)], chains))


@pytest.mark.parametrize("shape", [run_intent, holdings_intent, url_intent])
def test_a_covered_registration_of_either_shape_yields_nothing(shape):
    chains = {CORPUS: view(shape(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=(("A", R, I),))], chains) == ()


def test_an_interrupted_holdings_act_is_an_unclaimed_intent():
    chains = {CORPUS: view(holdings_intent(I))}
    assert ("session-intent-unclaimed", "error", I) in codes(reconcile([ledger(opens=("A",), closes=("A",))], chains))


def test_a_url_recheck_intent_and_its_fulfillment_reconcile_to_nothing():
    chains = {CORPUS: view(url_intent(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), acts=(("A", R, I),), closes=("A",))], chains) == ()


def test_an_unfulfilled_url_recheck_intent_reads_as_a_store_one_does():
    # The ledger is open with no close, so both calls also carry the ledger-level
    # "session-unclosed" finding (present regardless of shape); the equivalence
    # under test is the intent-level "session-outcome-unknown" treatment, so this
    # checks membership rather than exact equality against a list that omits it.
    chains = {CORPUS: view(url_intent(I))}
    store = {CORPUS: view(holdings_intent(I))}
    ledgers = [ledger(opens=("A",), closed=False)]
    assert codes(reconcile(ledgers, chains)) == codes(reconcile(ledgers, store))
    assert ("session-outcome-unknown", "warning", I) in codes(reconcile(ledgers, chains))


# --- store chains (spec §4.6) ------------------------------------------------------
STORE = "5" * 32


def store_view(*entries) -> WellFormedView:
    """A store chain: registrations and their settlements, never an intent."""
    return view(*entries)


def store_registration(digest: str) -> RegisteredEntryView:
    return RegisteredEntryView(digest=digest, txid="t" + digest[:4], initial=(), final=(), fulfills=None)


def test_a_store_act_verifies_against_the_store_chain():
    chains = {STORE: store_view(store_registration(R), settled(R, True))}
    acts = (("A", R, I),)
    assert reconcile([ledger(opens=("A",), closes=("A",), acts=acts, corpus=STORE)], chains) == ()


def test_a_fabricated_store_act_is_unverified():
    chains = {STORE: store_view(store_registration(R), settled(R, True))}
    fabricated = "f" * 64
    acts = (("A", fabricated, I),)
    found = codes(reconcile([ledger(opens=("A",), closes=("A",), acts=acts, corpus=STORE)], chains))
    assert found == [("session-act-unverified", "error", fabricated)]


def test_store_chains_contribute_no_intent_findings():
    """A store chain carries registrations and settlements and no intents: it
    yields no intent-loop finding, even with acts naming nothing on it."""
    other = "e" * 64
    chains = {STORE: store_view(store_registration(R), settled(R, True), store_registration(other))}
    found = codes(reconcile([ledger(opens=("A",), closed=False)], chains))
    assert found == [("session-unclosed", "warning", S1)]


def _fabricated_store_ledger(ops: Path, store_id: str, entry: str) -> None:
    """A closed session `S1` whose one act claims `entry` on the store chain."""
    path = ledger_path(ops, S1)
    path.parent.mkdir(parents=True)
    path.write_bytes(
        b"".join(
            encode_line(line)
            for line in (
                {
                    "line": "session-open",
                    "session": S1,
                    "actor": f"session:{S1}",
                    "world": WORLD,
                    "permit": {"kinds": [], "act_families": [], "ungoverned": True},
                    "at": AT,
                },
                {"line": "invocation-open", "invocation": "A", "command": "mint", "input_digest": "d" * 64, "at": AT},
                {"line": "act", "invocation": "A", "corpus": store_id, "entry": entry, "intent": I, "records": []},
                {"line": "invocation-close", "invocation": "A", "outcome": {"done": []}},
                {"line": "session-close", "at": AT},
            )
        )
    )


def test_reconcile_sessions_reads_the_given_store_roots(certified_work):
    """A real store act verifies against the store chain read from the given
    root; a fabricated one is unverified only when that root is read; and the
    constructor reads its own store root."""
    from test_session_routes import RECHECKS, _durable_session
    from test_session_writer import DIGEST

    from beliefs.holdings.boundary import write

    session = _durable_session(certified_work)
    store_root = session.store_root
    assert store_root is not None and session.world_config is not None
    config, ops = session.world_config, session.operations_root
    session.claim_invocation("A", "write", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    write(scoped.holdings_context(instrument="inst"), StoreLocator(scoped.store_id, "a.bin"), b"alpha")
    session.close_invocation("A", {"done": []})
    session.close()
    store_acts = [act for act in open_ledger_reader(ops, session.session_id).acts() if act.corpus == scoped.store_id]
    assert len(store_acts) == 1
    assert reconcile_sessions(config, ops, store_roots=(store_root,)) == ()

    fabricated = "f" * 64
    _fabricated_store_ledger(ops, scoped.store_id, fabricated)
    assert reconcile_sessions(config, ops) == ()  # the store chain was not read: no evidence either way
    assert codes(reconcile_sessions(config, ops, store_roots=(store_root,))) == [
        ("session-act-unverified", "error", fabricated)
    ]
    opened = open_attended_session(config, ops, write_root=session.corpus_root, profile=BASE, store_root=store_root)
    assert codes(opened.findings) == [("session-act-unverified", "error", fabricated)]


def test_an_unreadable_store_root_is_a_finding(certified_work):
    """A store root with no store genesis, and a root whose genesis is a
    corpus's, each read as `session-store-unreadable`, not a raise."""
    root, ops = certified_work / "corpus", certified_work / "ops"
    init_corpus_root(root, authority=FULL)
    CorpusWriter(root, durable_executor_factory(), authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
    config = WorldConfig(world_root=certified_work / "world", world_id=WORLD, corpus_roots=(root,))
    missing = certified_work / "no-store"
    found = reconcile_sessions(config, ops, store_roots=(root, missing))
    assert codes(found) == [
        ("session-store-unreadable", "error", str(root)),
        ("session-store-unreadable", "error", str(missing)),
    ]


def test_a_store_write_between_the_chain_and_ledger_reads_is_not_unverified(certified_work, monkeypatch):
    """Plan review round 1, P2-1, with controller ruling R1: the writer is
    paused after its corpus intent and before the ledgered store call. Once
    reconciliation has read the chains, the gate opens; the store root's
    operation lock, held by the ledgered store call across the registration and
    its act line, keeps the write out until reconciliation has read the ledgers
    too."""
    import dataclasses
    import threading

    from test_session_routes import RECHECKS, _durable_session
    from test_session_writer import DIGEST

    import beliefs.session as session_module
    from beliefs.holdings.boundary import write

    session = _durable_session(certified_work)
    store_root = session.store_root
    assert store_root is not None and session.world_config is not None
    config, ops = session.world_config, session.operations_root
    session.claim_invocation("A", "write", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    ctx = scoped.holdings_context(instrument="inst")

    at_gate, gate_open, chains_read, writer_done = (threading.Event() for _ in range(4))
    ledgered_store_write = ctx.seam.store_write

    def gated(root, path, content, intent):
        at_gate.set()
        assert gate_open.wait(5), "the gate never opened"
        return ledgered_store_write(root, path, content, intent)

    gated_ctx = dataclasses.replace(ctx, seam=dataclasses.replace(ctx.seam, store_write=gated))
    real_read = session_module.read_ledger_evidence
    waits: list[tuple[bool, bool]] = []
    registered_during_wait: list[int] = []

    def store_registrations() -> int:
        inspected = log_seam().inspect_detached(store_root)
        assert type(inspected) is WellFormedView
        return sum(type(entry) is RegisteredEntryView for entry in inspected.entries)

    def paused_read(operations_root, session_id):
        if not chains_read.is_set():
            before = store_registrations()
            chains_read.set()
            woke = writer_done.wait(1.0)
            waits.append((woke, writer_done.is_set()))
            registered_during_wait.append(store_registrations() - before)
        return real_read(operations_root, session_id)

    monkeypatch.setattr(session_module, "read_ledger_evidence", paused_read)
    failures: list[BaseException] = []
    results: dict[str, object] = {}

    def run_writer():
        try:
            results["written"] = write(gated_ctx, StoreLocator(scoped.store_id, "a.bin"), b"alpha")
            writer_done.set()
        except BaseException as caught:  # noqa: BLE001
            failures.append(caught)

    def run_reconcile():
        try:
            results["findings"] = reconcile_sessions(config, ops, store_roots=(store_root,))
        except BaseException as caught:  # noqa: BLE001
            failures.append(caught)

    writer = threading.Thread(name="writer", target=run_writer, daemon=True)
    writer.start()
    assert at_gate.wait(5), "the writer never reached the store call"
    auditor = threading.Thread(name="auditor", target=run_reconcile, daemon=True)
    auditor.start()
    assert chains_read.wait(5), "reconciliation never read the ledgers"
    gate_open.set()
    auditor.join(10)
    writer.join(10)
    assert not auditor.is_alive() and not writer.is_alive()
    assert failures == []
    assert waits == [(False, False)]  # the wait timed out with the write unfinished
    # The store write itself was held off: the store root's operation lock, not
    # only the corpus root's around the publication that follows it.
    assert registered_during_wait == [0]
    assert writer_done.is_set()  # and then completed
    findings = results["findings"]
    assert isinstance(findings, tuple)
    assert "session-act-unverified" not in [f.code for f in findings]
    store_acts = [act for act in session.invocation_acts("A") if act.corpus == scoped.store_id]
    assert len(store_acts) == 1
    again = reconcile_sessions(config, ops, store_roots=(store_root,))
    assert "session-act-unverified" not in [f.code for f in again]
