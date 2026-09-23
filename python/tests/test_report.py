"""T3, T5's type-union refusals, T6's order and citation arms, T8,
and T2's intent-type half. Deferred: T1's import and raw-write arms (store,
tamper log), T2's committed-registration arms (persistence), T5's began-ness
and preflight-versus-post-stop distinctions (the acquisition operation), and
T5's no-observation negative (the persistence seam) — cut 3 §4.2."""

import dataclasses
import re
from collections import defaultdict

import pytest
from closure_fixtures import make_closure, sample_report
from fixtures_cut3 import report

from beliefs import report as report_values
from beliefs import stored
from beliefs.errors import CitationRefused, MalformedRecord, OutcomeRefused
from beliefs.identity import v1
from beliefs.recipe import RunClosure
from beliefs.report import (
    ACT_REPORT_DOMAIN,
    CLOSED,
    EVIDENCE_REFUSAL_REASONS,
    INDETERMINATE,
    OPERATION_KINDS,
    UNFINISHED,
    ActReport,
    AssessmentRunIntent,
    BindingBound,
    BindingEvidenceRefused,
    BindingPredecessorNotStanding,
    ByteLocatorUntested,
    DeclarationPinEntry,
    LocatorEntry,
    ManagedMutationEntry,
    OperationIntent,
    PinnedDeclaration,
    PublicationBindingEntry,
    PublishedObservation,
    RecordImportEntry,
    Registration,
    SubjectEvaluationEntry,
    _mint_report,
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


def test_an_acquisition_report_requires_an_acquisition_intent_and_keeps_entry_order():
    from beliefs.boundary import _mint_acquisition_report

    entries = (
        LocatorEntry("url:https://example.org/a", PublishedObservation("holdings-observation:" + "a" * 64), (("timeout_seconds", "5.0"),)),
        ManagedMutationEntry("store:" + "d" * 32 + ":a.bin", PublishedObservation("holdings-observation:" + "b" * 64)),
        DeclarationPinEntry("dataset:sha256:" + "c" * 64, PinnedDeclaration("dataset:sha256:" + "c" * 64)),
    )
    intent = OperationIntent("acquisition", "tok", "actor:a")
    fields = {"observer": "o", "instrument": "i", "opened_at": "2026-09-20T00:00:00Z", "closed_at": "2026-09-20T00:00:01Z"}
    report = _mint_acquisition_report(intent, entries=entries, **fields)
    assert report.operation == "acquisition" and report.entries == entries
    permuted = _mint_acquisition_report(intent, entries=(entries[1], entries[0], entries[2]), **fields)
    assert permuted.identity() != report.identity()
    with pytest.raises(MalformedRecord):
        _mint_acquisition_report(OperationIntent("import", "tok", "actor:a"), entries=entries, **fields)


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


# --- publish (publication-records design §7, decisions 8 and 10) -------------
SUBJECT = "coord:" + "a" * 32 + "/" + "b" * 32


def publish_report(outcome):
    return _mint_report(
        operation="publish",
        event_token="c" * 32,
        actor="actor",
        observer="actor",
        instrument="beliefs.publish",
        opened_at="2026-09-22T00:00:00Z",
        closed_at="2026-09-22T00:00:01Z",
        entries=(PublicationBindingEntry(SUBJECT, outcome),),
    )


@pytest.mark.parametrize(
    "outcome",
    [
        BindingBound("d" * 32, "e" * 32, "f" * 32),
        BindingPredecessorNotStanding("e" * 32, "f" * 32, True, ("1" * 32, "2" * 32)),
        BindingEvidenceRefused("e" * 32, "f" * 32, False, "mounts-changed"),
    ],
    ids=["bound", "predecessor-not-standing", "evidence-refused"],
)
def test_each_publish_outcome_round_trips_through_the_stored_mirror(outcome):
    report = publish_report(outcome)
    node = stored.act_report_node(report)
    facet = stored.act_report_facet(node)
    (entry,) = facet["entries"]
    assert entry["kind"] == "publication-binding" and entry["subject"] == SUBJECT
    assert set(entry) == {"kind", "subject", "outcome"}


def test_publish_is_in_the_closed_set_but_never_an_operation_intent():
    assert "publish" in OPERATION_KINDS and len(OPERATION_KINDS) == 9
    with pytest.raises(MalformedRecord, match="opens only through its domain intent"):
        OperationIntent("publish", "c" * 32, "actor")


@pytest.mark.parametrize("tips", [({},), ("1" * 32, 1)], ids=["mapping-member", "mixed-str-int"])
def test_malformed_tips_raise_malformed_record_not_type_error(tips):
    """User review 2: members are validated before they are sorted or hashed."""
    with pytest.raises(MalformedRecord):
        BindingPredecessorNotStanding("e" * 32, "f" * 32, True, tips)


def test_list_tips_are_refused_as_not_a_tuple():
    """The container is checked before its members: a list is refused by its rule."""
    with pytest.raises(MalformedRecord, match="tips must be a tuple"):
        BindingPredecessorNotStanding("e" * 32, "f" * 32, True, ["1" * 32])  # type: ignore[arg-type]


def test_the_evidence_refusal_reasons_are_closed():
    assert EVIDENCE_REFUSAL_REASONS == (
        "mounts-changed",
        "anchor-unplaced",
        "chain-absent",
        "chain-malformed",
        "revision-missing",
        "revision-mismatch",
        "revision-malformed",
        "history-violated",
        "unregistered-revision",
        "report-unqualified",
        "tips-disagree",
    )
    with pytest.raises(MalformedRecord):
        BindingEvidenceRefused("e" * 32, "f" * 32, False, "other")


def reidentified(node):
    """The stored act-report with its content address recomputed after a facet edit —
    exactly the digest `stored.act_report_facet` checks (`v1.digest(ACT_REPORT_DOMAIN,
    facet)` → `act-report:<digest>`), so a mutated record is refused by the rule the
    test targets and never by a stale address (user review 2)."""
    facet = node.facets["act-report"]
    return node.model_copy(update={"id": f"act-report:{v1.digest(ACT_REPORT_DOMAIN, facet)}"})


def test_a_reidentified_unmutated_publish_report_is_accepted():
    """The control: re-identification alone changes nothing the check refuses."""
    node = stored.act_report_node(
        publish_report(BindingPredecessorNotStanding("e" * 32, "f" * 32, True, ("1" * 32, "2" * 32)))
    )
    assert reidentified(node).id == node.id
    assert stored.act_report_facet(reidentified(node))["operation"] == "publish"


_BOUND = BindingBound("d" * 32, "e" * 32, "f" * 32)
_REFUSED = BindingEvidenceRefused("e" * 32, "f" * 32, False, "mounts-changed")
_TWO_TIPS = BindingPredecessorNotStanding("e" * 32, "f" * 32, True, ("1" * 32, "2" * 32))
_ONE_TIP = BindingPredecessorNotStanding("e" * 32, "f" * 32, True, ("1" * 32,))


@pytest.mark.parametrize(
    "outcome, field, value, rule",
    [
        (_BOUND, "binding", "not-hex", "bound binding must be 32 lowercase hexadecimal"),
        (_BOUND, "corpus_id", "E" * 32, "bound corpus_id must be 32 lowercase hexadecimal"),
        (_BOUND, "marker", "f" * 31, "bound marker must be 32 lowercase hexadecimal"),
        (_REFUSED, "reason", "other", "evidence refusal reason 'other' is outside"),
        (_REFUSED, "remotely_revealed", "yes", "remotely_revealed must be a bool"),
        (_TWO_TIPS, "tips", ["2" * 32, "1" * 32], "tips must be strictly ascending and unique"),
        (_TWO_TIPS, "tips", ["1" * 32, "1" * 32], "tips must be strictly ascending and unique"),
        (_ONE_TIP, "tips", ["not-hex"], "refusal tip must be 32 lowercase hexadecimal"),
        (_ONE_TIP, "tips", [{}], "refusal tip must be 32 lowercase hexadecimal"),
        (_ONE_TIP, "extra", "x", "outcome carries exactly"),
    ],
    ids=[
        "binding-hex",
        "corpus-hex",
        "marker-hex",
        "reason",
        "revealed-bool",
        "tips-order",
        "tips-duplicate",
        "tips-hex",
        "tips-mapping",
        "extra-field",
    ],
)
def test_the_stored_mirror_refuses_what_the_constructors_refuse(outcome, field, value, rule):
    """User review, finding 3, and user review 2: each closed rule through the
    stored path, on a re-identified record, the refusal naming its rule."""
    node = stored.act_report_node(publish_report(outcome))
    node.facets["act-report"]["entries"][0]["outcome"][field] = value
    with pytest.raises(MalformedRecord, match=re.escape(rule)):
        stored.act_report_facet(reidentified(node))


def test_the_publish_report_seam_mints_one_binding_entry_for_a_publish_intent_only():
    from types import SimpleNamespace

    from beliefs.boundary import _mint_publish_report
    from beliefs.coordination import CoordinationAddress
    from beliefs.intents.publish import Destination, PublishIntent

    entry = PublicationBindingEntry(SUBJECT, _BOUND)
    times = {"observer": "actor", "instrument": "beliefs.publish", "opened_at": "t0", "closed_at": "t1"}
    intent = PublishIntent(
        kind="publish",
        event_token="c" * 32,
        actor="actor",
        at="2026-09-22T00:00:00Z",
        view=CoordinationAddress("a" * 32, "b" * 32, "c" * 32),
        destination=Destination.local("/srv/published/mm30"),
        binding_tips=(),
        marker_tips=(),
        anchors=(),
    )
    report = _mint_publish_report(intent, entry=entry, **times)
    assert (report.operation, report.event_token, report.entries) == ("publish", "c" * 32, (entry,))
    with pytest.raises(MalformedRecord, match="closes a publish intent"):
        _mint_publish_report(OperationIntent("audit", "c" * 32, "actor"), entry=entry, **times)  # type: ignore[arg-type]
    # the check is the type, not a duck-typed kind attribute
    look_alike = SimpleNamespace(kind="publish", event_token="c" * 32, actor="actor")
    with pytest.raises(MalformedRecord, match="closes a publish intent"):
        _mint_publish_report(look_alike, entry=entry, **times)  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord, match="one publication-binding entry"):
        _mint_publish_report(intent, entry=(entry,), **times)  # type: ignore[arg-type]
