"""Conformance cut 38 — the act-report remainder: `audit` and `re-check` open
through the boundary (act-report-remainder design §9.2). Twelve declaration
units over real roots on the certified volume, and three plain tests."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import threading
from dataclasses import replace
from pathlib import Path

import pytest
from atoms.chain.model import (
    SettledEntry,  # the raw-chain forgery, as cut 35's T2-d spells it; a test, not a boundary module
)
from authority import FULL
from domain_facet_fixtures import PROPOSITION_REF, kwargs_for, over_kwargs, profile_with, seed
from nodes.core.errors import ExecutionError
from profiles import BASE, pins_for
from test_audit_operation import stale_dataset
from test_holdings_acquire import chain, registrations_of
from test_operation_writes import proposition
from test_permit_boundary import WRITE_ENTRY_POINTS, modules, parsed, primitive_callers, relative
from test_session_routes import DIGEST, RECHECKS, _durable_session
from test_url_retrieval_acceptance import intents, observer, reduce, registrations, world_over
from test_world_log_codecs import Chain, ChainOutcome, state_at

from beliefs import audit_operation
from beliefs import boundary as boundary_values
from beliefs import root as science_root
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.audit_operation import audit
from beliefs.belief import Belief
from beliefs.corpus import CorpusWriter, Finding
from beliefs.errors import AuditRefused, CitationRefused, PortMismatch, RecheckRefused
from beliefs.evaluation import evaluate_over_traced
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.receipt import output_digest
from beliefs.holdings.recheck import recheck_locations
from beliefs.holdings.records import StoreLocator
from beliefs.holdings.seam import ReadNotAttemptedView, ReadUnestablishedView
from beliefs.report import (
    CLOSED,
    INDETERMINATE,
    ByteLocatorUntested,
    LocatorEntry,
    OperationIntent,
    PublishedObservation,
    RetrievalFailed,
    cite,
    completion,
)
from beliefs.root import durable_executor_factory, init_corpus_root, init_store_root, open_corpus
from beliefs.session import open_ledger_reader
from beliefs.world.logmodel import IntentEntryView, MalformedView, RegisteredEntryView

__all__ = ["observer"]  # the fixture is re-exported for pytest's collection


def operation_intent(root: Path, kind: str) -> IntentEntryView:
    """The one operation intent of `kind` — the holdings intents of the same kind carry a `location`."""
    (entry,) = [e for e in intents(root) if json.loads(e.payload).get("kind") == kind and "location" not in json.loads(e.payload)]
    return entry


def closed(root: Path, kind: str, report_ref: str, report) -> bool:
    entry = operation_intent(root, kind)
    value = OperationIntent(kind, json.loads(entry.payload)["event_token"], report.actor)
    return completion(value, registrations_of(chain(root), entry.digest, report_ref), {report_ref: report}) == CLOSED


def held(ctx, store_id: str, name: str, body: bytes) -> StoreLocator:
    location = StoreLocator(store_id, name)
    write(ctx, location, body)
    return location


def run_audit(writer: CorpusWriter, **kwargs):
    return audit(writer, observer="observer", instrument="instrument", evidence=NO_EVIDENCE, **kwargs)


class CountingPort:
    """The durable port with every fulfilling submission counted (T2-h)."""

    def __init__(self, inner) -> None:
        self._inner = inner
        self.submissions = 0

    @property
    def root(self):
        return self._inner.root

    @property
    def profile(self):
        return self._inner.profile

    @property
    def authority(self):
        return self._inner.authority

    def append_intent(self, payload):
        return self._inner.append_intent(payload)

    def preflight(self, plan):
        self._inner.preflight(plan)

    def execute(self, plan):
        self._inner.execute(plan)

    def execute_fulfilling(self, plan, fulfills):
        self.submissions += 1
        return self._inner.execute_fulfilling(plan, fulfills)

    def execute_fulfilling_guarded(self, plan, fulfills, *, guard, fallback):
        return self._inner.execute_fulfilling_guarded(plan, fulfills, guard=guard, fallback=fallback)


class RefusingPort(CountingPort):
    def append_intent(self, payload):
        raise ExecutionError("refused", index=None, applied=0)


# --- T2 ----------------------------------------------------------------------------


def test_t2e_an_audit_closes_through_exactly_one_report_after_its_intent_and_the_evaluator_ran_between_durably(observer, monkeypatch):
    ctx, writer = observer.ctx, observer.writer
    events: list[str] = []
    inner = writer._operation_port

    class Recording(CountingPort):
        """Each call's *completion* is logged after the durable port returns."""

        def append_intent(self, payload):
            digest = super().append_intent(payload)
            events.append("appended")
            return digest

        def execute_fulfilling(self, plan, fulfills):
            digest = super().execute_fulfilling(plan, fulfills)
            events.append("closed")
            return digest

    real = audit_operation.audit_corpus
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: events.append("evaluated") or real(view, evidence=evidence, profile=profile))
    outcome = run_audit(writer, port=Recording(inner))
    assert events == ["appended", "evaluated", "closed"]
    entry = operation_intent(ctx.observer_root, "audit")
    entries = chain(ctx.observer_root)  # one captured read; every read constructs fresh entry objects, so compare digests
    positions = [
        i for i, e in enumerate(entries)
        if (isinstance(e, IntentEntryView) and e.digest == entry.digest) or (isinstance(e, RegisteredEntryView) and e.fulfills == entry.digest)
    ]
    assert len(positions) == 2 and positions[0] < positions[1]
    assert len(registrations_of(chain(ctx.observer_root), entry.digest, outcome.report_ref)) == 1
    assert closed(ctx.observer_root, "audit", outcome.report_ref, outcome.report)


def test_t2f_a_recheck_closes_through_one_report_and_its_operation_intent_precedes_every_holdings_intent_durably(observer):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a, b = held(ctx, store_id, "a.bin", b"alpha"), held(ctx, store_id, "b.bin", b"beta")
    before = len(intents(ctx.observer_root))
    outcome = recheck_locations(ctx, writer, (a, b))
    later = intents(ctx.observer_root)[before:]
    assert [json.loads(e.payload).get("kind") for e in later] == ["re-check", "re-check", "re-check"]
    assert "location" not in json.loads(later[0].payload) and all("location" in json.loads(e.payload) for e in later[1:])
    fulfilled = {e.fulfills for e in registrations(ctx.observer_root)}
    assert {e.digest for e in later} <= fulfilled  # every holdings intent fulfilled by its observation, the operation's by the report
    assert len(registrations_of(chain(ctx.observer_root), later[0].digest, outcome.report_ref)) == 1
    assert closed(ctx.observer_root, "re-check", outcome.report_ref, outcome.report)


@pytest.mark.parametrize("spoil", ["wrong-root", "no-port", "refusing-port", "foreign-store"])
def test_t2g_root_selection_no_port_a_refused_append_and_a_foreign_store_begin_no_act_for_both_kinds_durably(observer, certified_work, spoil, monkeypatch):
    """The audit has no root-selection or store arm (one writer, no store), so under
    `wrong-root` and `foreign-store` its half reads the port-less writer; the
    assertion is the same for every arm — no read, no intent, no record."""
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    reads: list[str] = []
    calls: list[object] = []
    inner_read = ctx.seam.read_path
    ctx = replace(ctx, seam=replace(ctx.seam, read_path=lambda root, path: reads.append(path) or inner_read(root, path)))
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda *a, **k: calls.append(a) or ())
    portless = CorpusWriter(ctx.observer_root, durable_executor_factory(), authority=FULL, profile=BASE)
    audit_writer, audit_kwargs = portless, {}
    recheck_kwargs: dict = {}
    recheck_writer, locations = writer, (a,)
    if spoil == "wrong-root":
        other = certified_work / "other"
        init_corpus_root(other, authority=FULL)
        recheck_writer = open_corpus(other, authority=FULL, profile=BASE)
    elif spoil == "no-port":
        recheck_writer = portless
    elif spoil == "refusing-port":
        audit_writer, audit_kwargs = writer, {"port": RefusingPort(writer._operation_port)}
        recheck_kwargs["port"] = RefusingPort(writer._operation_port)
    else:
        locations = (a, StoreLocator("f" * 32, "x.bin"))
    before = chain(ctx.observer_root)
    with pytest.raises((AuditRefused, ExecutionError)):
        run_audit(audit_writer, **audit_kwargs)
    with pytest.raises((RecheckRefused, ExecutionError)):
        recheck_locations(ctx, recheck_writer, locations, **recheck_kwargs)
    assert chain(ctx.observer_root) == before
    assert reads == [] and calls == []
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())
    if spoil == "wrong-root":
        assert not any(node.kind == "act-report" for node in recheck_writer.read_view.iter_stored())


def test_t2h_each_kind_submits_exactly_one_fulfilling_execution_and_a_second_is_refused_durably(observer, certified_work):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    counting = CountingPort(writer._operation_port)
    outcome = run_audit(writer, port=counting)
    assert counting.submissions == 1
    a = held(ctx, store_id, "a.bin", b"alpha")
    recheck_counting = CountingPort(writer._operation_port)
    recheck_locations(ctx, writer, (a,), port=recheck_counting)
    assert recheck_counting.submissions == 1
    intent_digest = operation_intent(ctx.observer_root, "audit").digest
    with pytest.raises(ExecutionError, match="already fulfills"):
        writer._publish_operation_report(outcome.report, intent_digest, operations=(writer._create_op(proposition("p")),))
    assert len([e for e in registrations(ctx.observer_root) if e.fulfills == intent_digest]) == 1
    copy = certified_work / "copy"
    shutil.copytree(ctx.observer_root, copy, symlinks=True)
    forged = Chain(copy)
    forged.digests = [entry.digest for entry in chain(ctx.observer_root)]
    report_path = writer._relative_path(writer.read_view.get(outcome.report_ref))
    state = state_at(copy, report_path)
    registration = forged.registration("tx-raw", ((report_path, state),), ((report_path, state),), fulfills=intent_digest)
    forged.append(SettledEntry(txid="tx-raw", registration=registration, outcome=ChainOutcome.COMMITTED))
    view = science_root._log_seam().inspect_registered(copy)
    assert isinstance(view, MalformedView), view
    assert view.defect.kind == "duplicate-fulfillment"


def test_t2i_a_port_bound_to_another_root_is_refused_by_both_kinds_before_any_intent_durably(observer, certified_work):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    other = certified_work / "other"
    init_corpus_root(other, authority=FULL)
    foreign = science_root.durable_operation_port(other, writer.authority, profile=writer.profile)  # the writer's authority and profile; only the root differs
    before = (chain(ctx.observer_root), chain(other))
    with pytest.raises(PortMismatch):
        run_audit(writer, port=foreign)
    with pytest.raises(PortMismatch):
        recheck_locations(ctx, writer, (a,), port=foreign)
    assert (chain(ctx.observer_root), chain(other)) == before


@pytest.mark.parametrize("spoil", ["empty-instrument", "unencodable-observer", "standing-elsewhere", "standing-unrequested"])
def test_t2j_late_inputs_refuse_the_recheck_before_the_operation_intent_with_no_holdings_intent_and_no_read_durably(observer, spoil):
    from beliefs.holdings.records import Found, holdings_observation

    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    reads: list[str] = []
    inner_read = ctx.seam.read_path
    ctx = replace(ctx, seam=replace(ctx.seam, read_path=lambda root, path: reads.append(path) or inner_read(root, path)))
    kwargs: dict = {}
    if spoil == "empty-instrument":
        ctx = replace(ctx, instrument="")
    elif spoil == "unencodable-observer":
        ctx = replace(ctx, observer="\udcff")
    elif spoil == "standing-elsewhere":
        elsewhere = holdings_observation(
            location=StoreLocator(store_id, "b.bin"), outcome=Found("sha256:" + "0" * 64), observer="o", instrument="i",
            event_token="t", observed_at="2026-09-22T00:00:00Z",
        )
        kwargs["standing"] = {a.canonical(): (elsewhere,)}
    else:
        kwargs["standing"] = {StoreLocator(store_id, "b.bin").canonical(): ()}
    before = chain(ctx.observer_root)
    with pytest.raises(RecheckRefused):
        recheck_locations(ctx, writer, (a,), **kwargs)
    assert chain(ctx.observer_root) == before and reads == []


# --- T5, T6 ------------------------------------------------------------------------


def test_t5d_an_inconclusive_recheck_location_spells_untested_or_failed_by_whether_the_read_began_durably(observer):
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a, b, c = held(ctx, store_id, "a.bin", b"alpha"), StoreLocator(store_id, "b.bin"), StoreLocator(store_id, "c.bin")
    inner = ctx.seam.read_path

    def reading(root, path):
        if path == b.relative_path:
            return ReadNotAttemptedView(reason="lease-refused", lifecycle_state=None, detail="x")
        if path == c.relative_path:
            return ReadUnestablishedView(reason="io-error", detail="y")
        return inner(root, path)

    ctx = replace(ctx, seam=replace(ctx.seam, read_path=reading))
    files_before = sorted((ctx.observer_root / "holdings-observation").iterdir())
    outcome = recheck_locations(ctx, writer, (a, b, c))
    assert outcome.entries[1] == LocatorEntry(b.canonical(), ByteLocatorUntested("lease-refused"))
    assert outcome.entries[2] == LocatorEntry(c.canonical(), RetrievalFailed("io-error"))
    assert outcome.entries[1].outcome != outcome.entries[2].outcome
    assert len(sorted((ctx.observer_root / "holdings-observation").iterdir())) == len(files_before) + 1  # a's re-check only
    assert closed(ctx.observer_root, "re-check", outcome.report_ref, outcome.report)


def test_t6d_cite_resolves_each_finding_in_evaluator_order_and_a_permutation_moves_the_identity_durably(observer, monkeypatch):
    writer = observer.writer
    first = stale_dataset(writer)
    real = audit_operation.audit_corpus
    second = Finding("warning", "zz-second", "proposition:" + "b" * 64, "d2", "m2")
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: real(view, evidence=evidence, profile=profile) + (second,))
    outcome = run_audit(writer)
    assert [f.ref for f in outcome.findings] == [first, second.ref]
    assert cite(outcome.report, 0).subject == first and cite(outcome.report, 1).subject == second.ref
    with pytest.raises(CitationRefused):
        cite(outcome.report, 2)
    permuted = boundary_values._mint_audit_report(
        OperationIntent("audit", outcome.report.event_token, outcome.report.actor), observer=outcome.report.observer,
        instrument=outcome.report.instrument, opened_at=outcome.report.opened_at, closed_at=outcome.report.closed_at,
        entries=(outcome.entries[1], outcome.entries[0]),
    )
    assert permuted.identity() != outcome.report.identity()


def test_t6e_findings_differing_only_in_message_mint_equal_entries_and_one_identity_under_a_fixed_envelope_durably(observer, monkeypatch):
    writer = observer.writer
    stale_dataset(writer)
    base = run_audit(writer)
    (finding,) = base.findings
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: (replace(finding, message="reworded"),))
    reworded = run_audit(writer)
    monkeypatch.setattr(audit_operation, "audit_corpus", lambda view, *, evidence, profile: (replace(finding, detail="other-detail"),))
    detailed = run_audit(writer)
    assert reworded.entries == base.entries and detailed.entries != base.entries
    assert reworded.report.identity() != base.report.identity()  # T8: distinct tokens; not the comparison that matters
    envelope = {"observer": "o", "instrument": "i", "opened_at": "2026-09-22T00:00:00Z", "closed_at": "2026-09-22T00:00:00Z"}
    intent = OperationIntent("audit", "f" * 32, writer.authority.actor)
    fixed = lambda entries: boundary_values._mint_audit_report(intent, entries=entries, **envelope).identity()
    assert fixed(base.entries) == fixed(reworded.entries)
    assert fixed(base.entries) != fixed(detailed.entries)


# --- BI ------------------------------------------------------------------------------


def test_bi1_the_evaluator_modules_define_no_write_entry_point_and_reach_no_primitive_durably():
    evaluators = {"audit.py", "world/audit.py"}
    assert not {key for key in WRITE_ENTRY_POINTS if key.split(":", 1)[0] in evaluators}
    for module in modules():
        name = relative(module)
        if name in evaluators:
            assert primitive_callers(parsed(module), name) == set(), name
    wrappers = {"audit_operation.py", "holdings/recheck.py"}
    seen = set()
    for module in modules():
        name = relative(module)
        if name in wrappers:
            seen.add(name)
            assert primitive_callers(parsed(module), name) == set(), name
    assert seen == wrappers


def test_bi2_the_evaluators_read_runs_under_the_root_lock_after_the_intent_so_a_raced_write_lands_after_the_report_durably(observer, monkeypatch):
    ctx, writer = observer.ctx, observer.writer
    started = threading.Event()
    real = audit_operation.audit_corpus
    racer = open_corpus(ctx.observer_root, authority=FULL, profile=BASE)
    added: list[str] = []

    def race() -> None:
        started.wait(5)
        added.append(racer.add(proposition("raced")).id)

    thread = threading.Thread(target=race)

    def evaluator(view, *, evidence, profile):
        thread.start()
        started.set()
        thread.join(0.5)  # blocked on the root lock the audit holds
        assert thread.is_alive() and added == []
        return real(view, evidence=evidence, profile=profile)

    monkeypatch.setattr(audit_operation, "audit_corpus", evaluator)
    outcome = run_audit(writer)
    thread.join(10)
    assert len(added) == 1
    committed = [e for e in chain(ctx.observer_root) if isinstance(e, RegisteredEntryView)]
    report_position = next(i for i, e in enumerate(committed) if e.fulfills == operation_intent(ctx.observer_root, "audit").digest)
    raced_position = next(i for i, e in enumerate(committed) if any(path == racer._relative_path(racer.read_view.get(added[0])) for path, _ in e.final))
    assert report_position < raced_position
    assert outcome.entries == ()  # the raced record was not in the judged state


def test_bi3_the_session_routes_write_one_act_line_per_committed_transaction_and_name_the_session_actor_durably(certified_work):
    session = _durable_session(certified_work)
    session.claim_invocation("A", "audit", DIGEST)
    scoped = session.scoped(RECHECKS, "A")
    audited = scoped.audit(instrument="inst", evidence=NO_EVIDENCE)
    ctx = scoped.holdings_context(instrument="inst")
    location = StoreLocator(scoped.store_id, "a.bin")
    write(ctx, location, b"alpha")
    rechecked = scoped.recheck((location,), instrument="inst")
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert len(acts) == 4  # the audit's close, the write, the re-check act, the re-check's close
    observed = rechecked.entries[0].outcome
    assert isinstance(observed, PublishedObservation), observed
    assert {pair[1] for act in acts for pair in act.record_ids} >= {audited.report_ref, rechecked.report_ref, observed.ref}
    assert audited.report.observer == session.actor and rechecked.report.observer == session.actor


# --- plain tests: T3 and T4, already closed, exercised by the new kinds ----------------


def test_deleting_the_published_audit_report_moves_the_operation_closed_to_indeterminate(observer):
    ctx, writer = observer.ctx, observer.writer
    outcome = run_audit(writer)
    entry = operation_intent(ctx.observer_root, "audit")
    value = OperationIntent("audit", json.loads(entry.payload)["event_token"], writer.authority.actor)
    registrations_ = registrations_of(chain(ctx.observer_root), entry.digest, outcome.report_ref)
    assert completion(value, registrations_, {outcome.report_ref: outcome.report}) == CLOSED
    os.unlink(writer.root / writer._relative_path(writer.read_view.get(outcome.report_ref)))
    writer._reconstruct()
    assert completion(value, registrations_, {}) == INDETERMINATE


def test_the_two_reports_leave_the_holdings_projection_unchanged_and_an_unfinished_audit_blocks_nothing(observer, certified_work):
    """T4's projection arm for the new kinds: over a fixed set of observations, both
    reports present, then one, then none, then an unmatched audit intent — the
    reducer outputs and the corpus's audit findings never move. The re-check's own
    observation is part of the fixed set, taken before the first snapshot."""
    ctx, store_id, writer = observer.ctx, observer.store_id, observer.writer
    a = held(ctx, store_id, "a.bin", b"alpha")
    rechecked = recheck_locations(ctx, writer, (a,))  # the observation set is now fixed
    audited = run_audit(writer)
    world, binding = world_over(certified_work, ctx.observer_root)

    def snapshot():
        active, blocked, _ = reduce(world, writer.corpus_id, binding)
        findings = tuple((f.code, f.ref) for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile))
        return output_digest(active), output_digest(blocked), blocked == [], findings

    def unlink(ref: str) -> None:
        # No ordinary API deletes a report (`DeletionKindExcluded`, families design §3.0); cut 35's T4-a unlinks likewise.
        os.unlink(writer.root / writer._relative_path(writer.read_view.get(ref)))
        writer._reconstruct()

    both_reports = snapshot()
    unlink(rechecked.report_ref)
    one_report = snapshot()
    unlink(audited.report_ref)
    no_reports = snapshot()
    writer._append_operation_intent("audit", secrets.token_hex(16), ctx.actor)  # an unfinished audit
    unmatched_intent = snapshot()
    assert both_reports == one_report == no_reports == unmatched_intent
    assert both_reports[2]  # nothing blocked, throughout


def test_the_two_reports_leave_the_belief_answer_and_its_admission_byte_unchanged(certified_work):
    """T4's belief arm for the new kinds, over a belief-bearing corpus: the audit's
    report and a re-check's report are added and removed while the answer, its
    `belief_input_digest` and its traced admission stay identical."""
    belief_root, store_root = certified_work / "belief", certified_work / "belief-store"
    init_corpus_root(belief_root, authority=FULL)
    store_id = init_store_root(store_root, authority=FULL)
    profile = profile_with()
    writer = open_corpus(belief_root, authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    view = seed(writer)
    kwargs = over_kwargs(kwargs_for(view, profile))
    ctx = ActContext(belief_root, store_root, "observer", "instrument", FULL, science_root.holdings_seam(), profile=profile)

    def answer():
        return evaluate_over_traced(writer.read_view, PROPOSITION_REF, **kwargs)  # (answer, admission)

    before, before_admission = answer()
    assert isinstance(before, Belief), before  # an unadmitted scenario would satisfy T4 vacuously
    audited = run_audit(writer)
    location = held(ctx, store_id, "a.bin", b"alpha")
    rechecked = recheck_locations(ctx, writer, (location,))
    with_reports, with_admission = answer()
    assert (with_reports, with_admission) == (before, before_admission)
    assert isinstance(with_reports, Belief), with_reports
    assert with_reports.belief_input_digest == before.belief_input_digest
    for ref in (audited.report_ref, rechecked.report_ref):
        os.unlink(writer.root / writer._relative_path(writer.read_view.get(ref)))
    writer._reconstruct()
    after, after_admission = answer()
    assert (after, after_admission) == (before, before_admission)
    assert isinstance(after, Belief), after
    assert after.belief_input_digest == before.belief_input_digest
