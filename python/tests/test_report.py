"""T3, T5's type-union refusals, T6's order and citation arms, T8,
and T2's intent-type half. Deferred: T1's import and raw-write arms (store,
tamper log), T2's committed-registration arms (persistence), T5's began-ness
and preflight-versus-post-stop distinctions (the acquisition operation), and
T5's no-observation negative (the persistence seam) — cut 3 §4.2."""

import dataclasses
from collections import defaultdict

import pytest
from closure_fixtures import make_closure, sample_report
from fixtures_cut3 import report

from beliefs import report as report_values
from beliefs.errors import CitationRefused, MalformedRecord, OutcomeRefused
from beliefs.recipe import RunClosure
from beliefs.report import (
    CLOSED,
    INDETERMINATE,
    UNFINISHED,
    ActReport,
    AssessmentRunIntent,
    ByteLocatorUntested,
    LocatorEntry,
    ManagedMutationEntry,
    OperationIntent,
    RecordImportEntry,
    Registration,
    SubjectEvaluationEntry,
    cite,
    completion,
)


# --- T5 ----------------------------------------------------------------------
def test_t5_byte_locator_untested_is_unspellable_on_a_managed_mutation_entry():
    with pytest.raises(OutcomeRefused):
        ManagedMutationEntry(
            subject="store://data/x",
            outcome=ByteLocatorUntested(reason="preflight refusal"),  # type: ignore[arg-type]
        )


def test_t5_byte_locator_untested_is_unspellable_on_a_record_import_entry():
    with pytest.raises(OutcomeRefused):
        RecordImportEntry(
            subject="record:abc",
            outcome=ByteLocatorUntested(reason="preflight refusal"),  # type: ignore[arg-type]
        )


def test_t5_byte_locator_untested_is_unspellable_on_a_subject_evaluation_entry():
    with pytest.raises(OutcomeRefused):
        SubjectEvaluationEntry(
            subject="record:abc",
            outcome=ByteLocatorUntested(reason="preflight refusal"),  # type: ignore[arg-type]
        )


def test_t5_a_locator_entry_can_carry_it():
    entry = LocatorEntry(subject="url://example", outcome=ByteLocatorUntested(reason="cooperative stop"))
    assert entry.outcome.reason == "cooperative stop"  # type: ignore[union-attr]


def test_record_mutation_entry_projects_its_corpus_and_outcome():
    entry = report_values.RecordMutationEntry(
        subject="dataset:d1",
        corpus="corpus-a",
        outcome=report_values.Moved(
            source_corpus="corpus-a", destination_corpus="corpus-b", ref="dataset:d1"
        ),
    )
    facet = report_values._entry_facet(entry)
    assert facet["kind"] == "record-mutation"
    assert facet["subject"] == "dataset:d1"
    assert facet["corpus"] == "corpus-a"
    assert facet["outcome"] == {
        "type": "moved",
        "source_corpus": "corpus-a",
        "destination_corpus": "corpus-b",
        "ref": "dataset:d1",
    }


def test_record_mutation_entry_refuses_a_locator_outcome():
    with pytest.raises(OutcomeRefused):
        report_values.RecordMutationEntry(
            subject="dataset:d1",
            corpus="corpus-a",
            outcome=ByteLocatorUntested(reason="preflight-refused"),  # type: ignore[arg-type]
        )


def test_consolidated_retires_nothing_when_the_uid_was_shared():
    facet = report_values._outcome_facet(
        report_values.Consolidated(
            kept_corpus="corpus-a",
            kept_ref="source:s1",
            other_corpus="corpus-b",
            other_ref="source:s1",
            retired_uids=(),
            rationale="a copied corpus; one uid throughout",
        )
    )
    assert facet["retired_uids"] == []


def test_consolidated_records_the_retired_uid_and_the_judgement():
    facet = report_values._outcome_facet(
        report_values.Consolidated(
            kept_corpus="corpus-a",
            kept_ref="source:s1",
            other_corpus="corpus-b",
            other_ref="source:s1",
            retired_uids=("u-2",),
            rationale="corpus-a holds the authored record",
        )
    )
    assert facet["type"] == "consolidated"
    assert facet["retired_uids"] == ["u-2"]
    assert facet["rationale"] == "corpus-a holds the authored record"


def test_the_two_relocation_operation_kinds_are_admitted():
    assert "move" in report_values.OPERATION_KINDS
    assert "consolidate" in report_values.OPERATION_KINDS
    assert "delete" not in report_values.OPERATION_KINDS


# --- T3 ----------------------------------------------------------------------
def test_t3_an_unmatched_intent_reads_unfinished():
    intent = OperationIntent(kind="acquisition", event_token="tok-1", actor="tester")
    assert completion(intent, registrations=(), held={}) == UNFINISHED


def test_t3_an_unreadable_fulfillment_pointer_reads_indeterminate_never_unfinished():
    intent = OperationIntent(kind="acquisition", event_token="tok-1", actor="tester")
    reading = completion(intent, (Registration(intent_token="tok-1", pointer="gone"),), held={})
    assert reading == INDETERMINATE


def test_t3_a_mapping_cannot_fabricate_a_missing_fulfillment_pointer():
    intent = OperationIntent(kind="acquisition", event_token="tok-1", actor="tester")
    held: defaultdict[str, object] = defaultdict(object)
    registrations = (Registration(intent_token="tok-1", pointer="gone"),)
    assert completion(intent, registrations, held) == INDETERMINATE
    assert "gone" not in held


def test_t3_a_fulfilled_intent_reads_closed():
    published = report()
    intent = OperationIntent(kind="acquisition", event_token=published.event_token, actor="tester")
    registrations = (Registration(intent_token=published.event_token, pointer=published.identity()),)
    assert completion(intent, registrations, held={published.identity(): published}) == CLOSED


def test_t3_a_non_qualifying_pointer_never_matches():
    published = report(event_token="tok-other")  # a report carrying a DIFFERENT token
    intent = OperationIntent(kind="acquisition", event_token="tok-1", actor="tester")
    registrations = (Registration(intent_token="tok-1", pointer=published.identity()),)
    assert completion(intent, registrations, held={published.identity(): published}) == UNFINISHED


def test_t3_no_status_field_is_spellable_on_any_record():
    for kind in (ActReport, OperationIntent, AssessmentRunIntent, RunClosure):
        names = {f.name for f in dataclasses.fields(kind)}
        assert not names & {"status", "state", "completion"}, kind


def test_t3_deleting_a_report_moves_closed_to_indeterminate_not_unfinished():
    published = report()
    intent = OperationIntent(kind="acquisition", event_token=published.event_token, actor="tester")
    registrations = (Registration(intent_token=published.event_token, pointer=published.identity()),)
    assert completion(intent, registrations, held={published.identity(): published}) == CLOSED
    assert completion(intent, registrations, held={}) == INDETERMINATE  # §4's retention cost, checkable


def test_wrong_spec_run_closure_reads_unfinished() -> None:
    closure = make_closure()
    intent = AssessmentRunIntent("b" * 64, closure.occurrence.event_token, "actor")
    registrations = (Registration(intent.event_token, closure.address()),)
    assert completion(intent, registrations, {closure.address(): closure}) == UNFINISHED


def test_assessment_shaped_closure_never_closes_a_production_intent() -> None:
    closure = make_closure()
    intent = OperationIntent("run-attempt", closure.occurrence.event_token, "actor")
    registrations = (Registration(intent.event_token, closure.address()),)
    assert completion(intent, registrations, {closure.address(): closure}) == UNFINISHED


def test_existing_completion_vocabulary_is_preserved() -> None:
    published = sample_report(operation="run-attempt", token="tok")
    intent = OperationIntent("run-attempt", "tok", "actor")
    registrations = (Registration("tok", "pointer"),)
    assert completion(intent, registrations, {"pointer": published}) == CLOSED
    assert completion(intent, registrations, {}) == INDETERMINATE
    other = OperationIntent("audit", "tok", "actor")
    assert completion(other, registrations, {"pointer": published}) == UNFINISHED


# --- T6 (the citation half; the R18 arm is Task 10's) -------------------------
def test_t6_permuting_two_entries_moves_the_report_identity():
    ordered = report()
    permuted = report(entries=tuple(reversed(ordered.entries)))
    assert ordered.identity() != permuted.identity()


def test_t6_a_citation_resolves_to_exactly_one_entry():
    published = report()
    assert cite(published, 0) is published.entries[0]
    assert cite(published, 1) is published.entries[1]


def test_t6_an_out_of_range_index_is_refused_at_the_citing_site():
    published = report()
    with pytest.raises(CitationRefused):
        cite(published, 2)
    with pytest.raises(CitationRefused):
        cite(published, -1)  # zero-based and unsigned (act-report §2.2)


# --- T8 ----------------------------------------------------------------------
def test_t8_equal_facets_with_distinct_event_tokens_are_two_reports():
    a, b = report(event_token="tok-a"), report(event_token="tok-b")
    assert a.entries == b.entries and a.actor == b.actor and a.opened_at == b.opened_at
    assert a.identity() != b.identity()  # the R3 discipline at the report


def test_t8_every_facet_member_moves_the_identity():
    baseline = report().identity()
    for field, value in [
        ("operation", "audit"),
        ("event_token", "tok-9"),
        ("actor", "other"),
        ("observer", "other-observer"),
        ("instrument", "other-instrument"),
        ("opened_at", "2026-08-12T02:00:00Z"),
        ("closed_at", "2026-08-12T03:00:00Z"),
    ]:
        assert report(**{field: value}).identity() != baseline
    assert report(entries=report().entries[:1]).identity() != baseline


def test_t8_no_ordinary_api_edits_supersedes_or_deletes_a_report():
    import beliefs.report as report_module

    assert not any(
        name.startswith(("edit", "supersede", "delete", "update", "retract")) for name in report_module.__all__
    )
    assert "supersedes" not in {f.name for f in dataclasses.fields(ActReport)}
    with pytest.raises(dataclasses.FrozenInstanceError):
        report().actor = "someone-else"  # type: ignore[misc]


# --- T2's intent-type half (the operational arms are Task 6's) ----------------
def test_t2_the_assessment_run_intent_is_unspellable_without_a_spec_identity():
    with pytest.raises(TypeError):
        AssessmentRunIntent(event_token="tok-1", actor="tester")  # type: ignore[call-arg]
    with pytest.raises(MalformedRecord):
        AssessmentRunIntent(spec_identity="", event_token="tok-1", actor="tester")


def test_the_operation_kind_enum_is_closed():
    with pytest.raises(MalformedRecord):
        OperationIntent(kind="deployment", event_token="tok-1", actor="tester")


# --- corpus-write (writer-session design §4.1) --------------------------------
def test_corpus_write_is_an_operation_kind_and_constructs_an_intent():
    assert "corpus-write" in report_values.OPERATION_KINDS
    intent = OperationIntent(kind="corpus-write", event_token="tok-9", actor="session:" + "a" * 32)
    assert intent.kind == "corpus-write"


def test_a_corpus_write_intent_reads_closed_on_a_token_matching_registration_whatever_it_points_at():
    intent = OperationIntent(kind="corpus-write", event_token="tok-9", actor="session:" + "a" * 32)
    registrations = (Registration(intent_token="tok-9", pointer="proposition/p1.md"),)
    assert completion(intent, registrations, held={}) == CLOSED
    assert completion(intent, registrations, held={"proposition/p1.md": object()}) == CLOSED


def test_a_corpus_write_intent_with_no_registration_reads_unfinished():
    intent = OperationIntent(kind="corpus-write", event_token="tok-9", actor="session:" + "a" * 32)
    assert completion(intent, registrations=(), held={}) == UNFINISHED
    assert completion(intent, (Registration(intent_token="other", pointer="x"),), held={}) == UNFINISHED
