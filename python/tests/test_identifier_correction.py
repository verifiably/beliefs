"""Slice 2b §5–§8: the source write boundary, the correction seam, its layers,
relocation and the read side."""

from __future__ import annotations

from typing import TypedDict

import pytest
from authority import ACTOR, FULL, lacking
from fixtures_cut4 import raw_write
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp
from profiles import BASE
from test_corpus_write import Recorder
from test_operation_writes import intents_of, primitive_calls, writer_over
from test_relocation import _recording_port, _writer
from test_session_writer import DIGEST, make_session
from test_source_address import ADDR_A, ADDR_B, ADDR_C, CANONICAL_DOI, A, B, C, consolidation, entry, raw_source

from beliefs import source, stored
from beliefs.corpus import CorpusWriter, OperationCommit, ReadView, corpus_check
from beliefs.errors import (
    BasisMissing,
    CollisionRefused,
    CorrectionRefused,
    FacetPayloadRefused,
    HistoryDisagreement,
    IdentifierMalformed,
    PermitExceeded,
    RelocationRefused,
    SourceAddressDisagreement,
    ValidationRefused,
)
from beliefs.permit import RequiredCapabilities
from beliefs.relocation import consolidate, move


class _ImportFields(TypedDict):
    observer: str
    instrument: str
    opened_at: str
    closed_at: str


@pytest.fixture()
def writer(request, tmp_path) -> CorpusWriter:
    Recorder.plans.clear()
    callspec = getattr(request.node, "callspec", None)
    root = tmp_path / callspec.id if callspec is not None else tmp_path
    return CorpusWriter(root / "corpus", Recorder, authority=FULL, profile=BASE)


class TestTheBoundary:
    def test_a_builder_source_is_admitted(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))
        assert writer.read_view.get(minted.id).id == ADDR_B

    def test_an_empty_basis_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(raw_source({}, node_id="source:handle"))

    def test_a_non_canonical_stored_value_refuses(self, writer):
        node = raw_source({"doi": "10.1234/ABC"}, node_id=source.source_address({"doi": "10.1234/ABC"}))
        with pytest.raises(IdentifierMalformed) as caught:
            writer.add(node)
        assert caught.value.reason == "non-canonical"

    def test_non_canonical_refusal_is_independent_of_insertion_order(self, writer):
        for identifiers in (
            {"pmid": "pmid:1", "doi": "10.1234/ABC"},
            {"doi": "10.1234/ABC", "pmid": "pmid:1"},
        ):
            with pytest.raises(IdentifierMalformed) as caught:
                writer.add(raw_source(identifiers, node_id=ADDR_B))
            assert (caught.value.scheme, caught.value.reason) == ("doi", "non-canonical")

    def test_an_unknown_scheme_beside_a_valid_doi_refuses(self, writer):
        node = raw_source({"doi": CANONICAL_DOI, "url": "x"}, node_id=ADDR_B)
        with pytest.raises(IdentifierMalformed) as caught:
            writer.add(node)
        assert caught.value.reason == "unknown-scheme"

    def test_a_handle_address_refuses(self, writer):
        with pytest.raises(SourceAddressDisagreement):
            writer.add(raw_source(B, node_id="source:Chen2023"))

    def test_add_refuses_a_history(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A]))

    def test_a_history_free_source_with_a_deprecated_id_refuses(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, deprecated=[ADDR_A]))

    def test_import_admits_a_well_formed_history_and_refuses_a_malformed_one(self, tmp_path):
        # `import_bundle` is a boundary operation: it needs an operation port, which this
        # module's `writer` fixture lacks. test_relocation._writer builds one with a recording port.
        from test_relocation import _writer

        from beliefs.errors import ImportRefused

        importer = _writer(tmp_path / "importer")
        report: _ImportFields = {
            "observer": "o",
            "instrument": "i",
            "opened_at": "2026-09-10T00:00:00Z",
            "closed_at": "2026-09-10T00:00:01Z",
        }
        good = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        importer.import_bundle([good], **report)
        assert importer.read_view.get(ADDR_B).deprecated_ids == [ADDR_A]
        # The malformed member claims addresses nothing else holds, so the only refusal it can
        # meet is history validation — a BundleMemberHeld on a colliding deprecated id would
        # subclass ImportRefused and satisfy a looser assertion with the validation removed.
        eight, nine = {"pmid": "8"}, {"pmid": "9"}
        bad = raw_source(
            nine,
            history=[entry(eight, nine, grounds="")],
            deprecated=[source.source_address(eight)],
        )
        with pytest.raises(ImportRefused) as caught:
            importer.import_bundle([bad], **report)
        assert type(caught.value) is ImportRefused and caught.value.member == bad.id
        assert "grounds" in str(caught.value)

    def test_import_admits_a_nested_history_and_refuses_a_malformed_nested_one(self, tmp_path):
        from beliefs.errors import ImportRefused

        importer = _writer(tmp_path / "importer")
        good = raw_source(
            B,
            history=[entry(A, B, token="t1"), consolidation(B, [entry(A, C, token="o1"), entry(C, B, token="o2")])],
            deprecated=sorted([ADDR_A, ADDR_C]),
        )
        importer.import_bundle([good], **REPORT)
        assert importer.read_view.get(ADDR_B).deprecated_ids == sorted([ADDR_A, ADDR_C])
        eight, nine = {"pmid": "8"}, {"pmid": "9"}
        bad = raw_source(
            nine,
            history=[entry(eight, nine, token="t1"), consolidation(nine, [entry(eight, nine, token="o1", grounds="")])],
            deprecated=[source.source_address(eight)],
        )
        with pytest.raises(ImportRefused) as caught:
            importer.import_bundle([bad], **REPORT)
        assert caught.value.member == bad.id and "grounds" in str(caught.value)

    def test_add_still_refuses_a_nested_history(self, writer):
        with pytest.raises(ValidationRefused):
            writer.add(raw_source(B, history=[entry(A, B, token="t1"), consolidation(B, [entry(A, B, token="o1")])], deprecated=[ADDR_A]))

    def test_a_dataset_without_content_identity_still_refuses(self, writer):
        node = stored.governed_node("dataset", "d", "d", {stored.DATASET_FACET: {"resources": []}}, ())
        with pytest.raises(BasisMissing):
            writer.add(node)


def raw_edit_history(writer, node_id, mutate):
    """Rewrite one stored source's file outside the boundary, as a forger would."""
    node = writer.read_view.get(node_id).model_copy(deep=True)
    mutate(node)
    raw_write(writer.root, node)
    writer._reconstruct()


class TestTheReadSide:
    def test_a_raw_edited_history_refuses_on_read(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))

        def mutate(node):
            node.facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": []}

        raw_edit_history(writer, minted.id, mutate)
        with pytest.raises(FacetPayloadRefused):
            writer.read_view.get(minted.id)

    def test_a_duplicated_deprecated_id_refuses_on_read(self, tmp_path):
        from test_relocation import _writer

        importer = _writer(tmp_path / "importer")
        corrected = raw_source(B, history=[entry(A, B)], deprecated=[ADDR_A])
        importer.import_bundle(
            [corrected],
            observer="o",
            instrument="i",
            opened_at="2026-09-10T00:00:00Z",
            closed_at="2026-09-10T00:00:01Z",
        )
        assert importer.read_view.get(ADDR_B).deprecated_ids == [ADDR_A]

        raw_edit_history(importer, corrected.id, lambda node: node.deprecated_ids.append(ADDR_A))
        with pytest.raises(FacetPayloadRefused):
            importer.read_view.get(corrected.id)

    def test_the_check_view_reports_facet_payload_malformed(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))

        def mutate(node):
            node.facets[stored.IDENTIFIER_CORRECTION_FACET] = {"entries": [entry(A, B, grounds="")]}

        raw_edit_history(writer, minted.id, mutate)
        findings = corpus_check(writer.read_view, BASE)
        assert any(
            finding.code == "facet-payload-malformed"
            and finding.ref == minted.id
            and finding.detail == stored.IDENTIFIER_CORRECTION_FACET
            for finding in findings
        )



def minted_a(writer):
    return writer.add(stored.source_node(title="p", identifiers=A))


class TestTheSeamRefusals:
    def test_source_permit_refuses_before_resolution(self, tmp_path):
        restricted = CorpusWriter(tmp_path / "restricted", Recorder, authority=lacking(kinds=("source",)), profile=BASE)
        before = len(Recorder.plans)
        with pytest.raises(PermitExceeded):
            restricted.correct_identifier("source:nowhere", {"doi": "10.1/x"}, grounds="")
        assert len(Recorder.plans) == before

    def test_non_canonical_refusal_is_independent_of_insertion_order(self, writer):
        minted = minted_a(writer)
        for identifiers in (
            {"pmid": "pmid:1", "doi": "10.1234/ABC"},
            {"doi": "10.1234/ABC", "pmid": "pmid:1"},
        ):
            with pytest.raises(IdentifierMalformed) as caught:
                writer.correct_identifier(minted.id, identifiers, grounds="g")
            assert (caught.value.scheme, caught.value.reason) == ("doi", "non-canonical")

    def test_target_missing(self, writer):
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier("source:nowhere", {"doi": "10.1/x"}, grounds="")
        assert caught.value.reason == "target-missing"

    def test_not_a_source(self, writer):
        d = writer.add(stored.dataset_node(title="d", resources=[{"name": "d", "digest": "sha256:" + "1" * 64}]))
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier(d.id, {"doi": "10.1/x"}, grounds="")
        assert caught.value.reason == "not-a-source"

    def test_a_raw_edited_subject_refuses_before_append(self, writer):
        # The one edit only the boundary catches: identifiers moved under the stored id with the
        # stamp recomputed — validated_node's stamp and history checks both pass, and without the
        # pre-append _refuse_source the seam would build a successor whose history never held the
        # stored address, dropping it from the redirect set.
        minted = minted_a(writer)

        def move_identifiers(node):
            node.facets[stored.SOURCE_FACET]["identifiers"] = dict(C)
            stored.stamp_semantic_identity(node)

        raw_edit_history(writer, minted.id, move_identifiers)
        assert writer.read_view.get(minted.id).id == minted.id  # readable: the read path does not catch it
        with pytest.raises(SourceAddressDisagreement):
            writer.correct_identifier(minted.id, {"doi": "10.1/x"}, grounds="")

    def test_malformed_supplied_identifiers(self, writer):
        minted = minted_a(writer)
        with pytest.raises(IdentifierMalformed) as caught:
            writer.correct_identifier(minted.id, {"doi": "10.1/x"}, grounds="")
        assert caught.value.reason == "malformed"

    def test_non_canonical_supplied_map_refuses_before_unchanged(self, writer):
        minted = minted_a(writer)
        with pytest.raises(IdentifierMalformed) as caught:
            writer.correct_identifier(minted.id, {"pmid": "PMID:1"}, grounds="g")
        assert caught.value.reason == "non-canonical"

    def test_empty_map(self, writer):
        minted = minted_a(writer)
        with pytest.raises(BasisMissing):
            writer.correct_identifier(minted.id, {}, grounds="")

    @pytest.mark.parametrize("grounds", ["", "\udcff"])
    def test_grounds_empty_or_unencodable(self, writer, grounds):
        minted = minted_a(writer)
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier(minted.id, A, grounds=grounds)
        assert caught.value.reason == "grounds-empty"

    def test_unchanged(self, writer):
        minted = minted_a(writer)
        with pytest.raises(CorrectionRefused) as caught:
            writer.correct_identifier(minted.id, A, grounds="g")
        assert caught.value.reason == "unchanged"

    def test_collision_with_another_records_address(self, writer):
        minted = minted_a(writer)
        writer.add(stored.source_node(title="other", identifiers=C))
        with pytest.raises(CollisionRefused):
            writer.correct_identifier(minted.id, C, grounds="g")

    def test_collision_with_retired_address_of_another_record(self, writer):
        minted = minted_a(writer)
        other = writer.add(stored.source_node(title="other", identifiers=C))
        writer.correct_identifier(other.id, {"pmid": "3"}, grounds="g")  # C is now other's retired address
        with pytest.raises(CollisionRefused):
            writer.correct_identifier(minted.id, C, grounds="g")

    def test_every_refusal_has_no_effect(self, writer):
        minted = minted_a(writer)
        before = len(Recorder.plans)
        for call in (
            lambda: writer.correct_identifier("source:nowhere", B, grounds="g"),
            lambda: writer.correct_identifier(minted.id, A, grounds="g"),
            lambda: writer.correct_identifier(minted.id, B, grounds=""),
        ):
            with pytest.raises(CorrectionRefused):
                call()
        assert len(Recorder.plans) == before
        assert writer.read_view.get(minted.id).model_dump() == minted.model_dump()


class TestTheSeamEffects:
    def test_moved_creates_and_deletes_preserving_uid(self, writer):
        minted = minted_a(writer)
        before = len(Recorder.plans)
        expected = writer._corpus.manifest[writer._relative_path(minted)].sha256
        corrected = writer.correct_identifier(minted.id, B, grounds="checked the PDF")
        assert len(Recorder.plans) == before + 1
        plan = Recorder.plans[-1]
        assert [type(op) for op in plan] == [CreateOp, DeleteOp]
        assert plan[1].expected_digest == expected
        assert corrected.uid == minted.uid and corrected.id == ADDR_B
        assert corrected.deprecated_ids == [ADDR_A]
        (correction,) = stored.identifier_corrections(corrected)
        assert (dict(correction.from_identifiers), dict(correction.to_identifiers), correction.actor, correction.grounds) == (A, B, ACTOR, "checked the PDF")
        assert writer.read_view.resolve(ADDR_A) == ADDR_B
        assert writer.read_view.get(ADDR_B).facets == corrected.facets

    def test_unmoved_replaces_in_place(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))
        before = len(Recorder.plans)
        expected = writer._corpus.manifest[writer._relative_path(minted)].sha256
        corrected = writer.correct_identifier(minted.id, {**B, "isbn": "9780306406157"}, grounds="g")
        assert len(Recorder.plans) == before + 1
        assert Recorder.plans[-1][0].expected_digest == expected
        assert [type(op) for op in Recorder.plans[-1]] == [ReplaceOp]
        assert corrected.id == minted.id and corrected.deprecated_ids == []
        assert len(stored.identifier_corrections(corrected)) == 1

    def test_removing_the_selected_identifier_moves_the_address(self, writer):
        minted = writer.add(stored.source_node(title="p", identifiers=B))
        corrected = writer.correct_identifier(minted.id, A, grounds="the DOI was another paper's")
        assert corrected.id == ADDR_A and corrected.deprecated_ids == [ADDR_B]

    def test_a_return_makes_the_old_address_live_again(self, writer):
        minted = minted_a(writer)
        writer.correct_identifier(minted.id, B, grounds="g1")
        back = writer.correct_identifier(ADDR_B, A, grounds="g2")
        assert back.id == ADDR_A and back.uid == minted.uid
        assert back.deprecated_ids == [ADDR_B]
        assert [c.event_token for c in stored.identifier_corrections(back)] and len(stored.identifier_corrections(back)) == 2
        assert writer.read_view.resolve(ADDR_B) == ADDR_A

    def test_a_deprecated_ref_names_the_live_subject(self, writer):
        minted = minted_a(writer)
        writer.correct_identifier(minted.id, B, grounds="g")
        corrected = writer.correct_identifier(ADDR_A, C, grounds="g")
        assert corrected.id == ADDR_C and sorted(corrected.deprecated_ids) == sorted([ADDR_A, ADDR_B])

    def test_referrers_are_byte_unchanged(self, writer):
        # A retraction's `grounded-in` edge is the reference a record may hold to a source
        # (a source is not an eligible retraction NodeTarget). No source-assertion builder exists.
        from test_retract import content_identity, mint_eligible_assessment

        minted = minted_a(writer)
        assessment = mint_eligible_assessment(writer)
        # The id is content-derived over the grounds, so the grounds are supplied at build time;
        # mutating a built retraction leaves its id stale and _validated_retraction refuses it.
        retraction = stored.retraction_node(
            title="retraction",
            target=stored.NodeTarget(assessment.id, assessment.id, content_identity(assessment)),
            reason="defective-code",
            rationale="the recorded result is invalid",
            grounds=(minted.id,),
            actor=ACTOR,
            event_token="event-1",
        )
        writer.retract(retraction)
        files_before = {p: p.read_bytes() for p in (writer.root / "retraction").glob("*.md")}
        try:
            writer.correct_identifier(minted.id, B, grounds="g")
        finally:
            assert {p: p.read_bytes() for p in (writer.root / "retraction").glob("*.md")} == files_before
        assert writer.read_view.resolve(minted.id) == ADDR_B
        assert writer.read_view.inbound(ADDR_B) == writer.read_view.inbound(minted.id)


SOURCES = RequiredCapabilities.for_kinds({"source"}, {})


class TestTheSessionLayers:
    def test_the_operation_facade_returns_the_fulfilling_commit(self, tmp_path):
        writer, port = writer_over(tmp_path)
        minted = writer.add(stored.source_node(title="p", identifiers=A))

        commit = writer.operations.correct_identifier(minted.id, B, grounds="g")

        assert type(commit) is OperationCommit and commit.record is not None
        assert commit.record.id == ADDR_B and commit.record.uid == minted.uid
        assert primitive_calls(port) == ["preflight", "append_intent", "execute_fulfilling"]
        (intent,) = intents_of(port)
        assert intent.kind == "corpus-write" and intent.event_token == commit.event_token
        _, (_, fulfills) = port.calls[-1]
        assert fulfills == commit.intent_digest and commit.entry_digest == "2" * 60 + "0002"

    def test_the_scoped_writer_commits_one_corpus_write_and_ledgers_an_act(self, tmp_path):
        session, ports = make_session(tmp_path)
        scoped = session.scoped(SOURCES, "A")
        session.claim_invocation("A", "mint", DIGEST)
        minted = scoped.add(stored.source_node(title="p", identifiers=A))
        (port,) = ports
        calls_before = len(port.calls)
        intents_before = len(intents_of(port))

        corrected = scoped.correct_identifier(minted.id, B, grounds="g")

        assert corrected.id == ADDR_B and corrected.uid == minted.uid
        acts = session.invocation_acts("A")
        assert len(acts) == 2 and acts[-1].record_ids == ((corrected.uid, corrected.id),)
        assert primitive_calls(port)[calls_before:] == ["preflight", "append_intent", "execute_fulfilling"]
        (intent,) = intents_of(port)[intents_before:]
        _, (_, fulfills) = port.calls[-1]
        assert intent.kind == "corpus-write" and fulfills == acts[-1].intent
        assert not any(node.kind == "act-report" for node in ReadView.opened_at(port.root).iter_stored())


REPORT: _ImportFields = {
    "observer": "o",
    "instrument": "i",
    "opened_at": "2026-09-10T00:00:00Z",
    "closed_at": "2026-09-10T00:00:01Z",
}


@pytest.fixture()
def two_writers(tmp_path):
    return _writer(tmp_path / "left"), _writer(tmp_path / "right")


class TestRelocation:
    def test_move_carries_history_and_deprecated_ids(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=A))
        corrected = left.correct_identifier(minted.id, B, grounds="g")
        move(left, right, corrected.id, **REPORT)
        arrived = right.read_view.get(ADDR_B)
        assert arrived.uid == corrected.uid and arrived.deprecated_ids == [ADDR_A]
        assert stored.identifier_corrections(arrived) == stored.identifier_corrections(corrected)
        assert right.read_view.resolve(ADDR_A) == ADDR_B

    def test_consolidate_absorbs_divergent_histories(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer, grounds in ((left, "g-left"), (right, "g-right")):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds=grounds)
        (keep_entry,) = stored.identifier_corrections(left.read_view.get(ADDR_B))
        (other_entry,) = stored.identifier_corrections(right.read_view.get(ADDR_B))
        survivor, keep_report, other_report = consolidate((left, ADDR_B), (right, ADDR_B), rationale="one paper", **REPORT)
        spine, merged = stored.identifier_corrections(survivor)
        assert spine == keep_entry
        assert merged.from_identifiers == B and merged.to_identifiers == B
        assert merged.absorbed == (other_entry,)
        assert (merged.actor, merged.grounds) == (left.authority.actor, "one paper")
        assert merged.event_token == keep_report.event_token == other_report.event_token
        assert survivor.deprecated_ids == [ADDR_A]
        assert left.read_view.resolve(ADDR_A) == ADDR_B
        assert right.read_view.resolve(ADDR_B) is None and right.read_view.resolve(ADDR_A) is None

    def test_swapping_keep_absorbs_the_other_entry(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer, grounds in ((left, "g-left"), (right, "g-right")):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds=grounds)
        (left_entry,) = stored.identifier_corrections(left.read_view.get(ADDR_B))
        survivor, *_ = consolidate((right, ADDR_B), (left, ADDR_B), rationale="one paper", **REPORT)
        spine, merged = stored.identifier_corrections(survivor)
        assert spine.grounds == "g-right" and merged.absorbed == (left_entry,)

    def test_consolidate_fast_forwards_a_prefix(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=B))
        right.import_bundle([minted], **REPORT)
        right.correct_identifier(ADDR_B, C, grounds="a typo")
        right.correct_identifier(ADDR_C, B, grounds="no, B was right")
        other = right.read_view.get(ADDR_B)
        assert len(stored.identifier_corrections(other)) == 2
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert stored.identifier_corrections(survivor) == stored.identifier_corrections(other)
        assert all(c.absorbed == () for c in stored.identifier_corrections(survivor))
        assert survivor.deprecated_ids == [ADDR_C]
        assert left.read_view.resolve(ADDR_C) == ADDR_B

    def test_consolidate_of_history_free_replicas_carries_no_facet(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=B))
        right.import_bundle([minted], **REPORT)
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert stored.IDENTIFIER_CORRECTION_FACET not in survivor.facets and survivor.deprecated_ids == []

    def test_correct_identifier_appends_after_a_consolidation_entry(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        further = left.correct_identifier(survivor.id, C, grounds="g2")
        history = stored.identifier_corrections(further)
        assert len(history) == 3 and history[1].absorbed != () and history[2].to_identifiers == C
        assert further.deprecated_ids == sorted([ADDR_A, ADDR_B])

    def test_move_carries_a_nested_history(self, two_writers):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        moved, *_ = move(left, right, survivor.id, **REPORT)
        assert stored.identifier_corrections(moved) == stored.identifier_corrections(survivor)
        assert right.read_view.resolve(ADDR_A) == ADDR_B

    def test_consolidate_twice_nests(self, tmp_path):
        left, right, third = (_writer(tmp_path / name) for name in ("left", "right", "third"))
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right, third):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        once, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r1", **REPORT)
        twice, *_ = consolidate((third, ADDR_B), (left, ADDR_B), rationale="r2", **REPORT)
        history = stored.identifier_corrections(twice)
        assert len(history) == 2 and history[1].absorbed == stored.identifier_corrections(once)
        assert history[1].absorbed[1].absorbed != ()
        assert twice.deprecated_ids == [ADDR_A]

    def test_consolidate_retries_after_an_interrupted_replacement(self, two_writers, monkeypatch):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        for writer in (left, right):
            writer.add(node.model_copy(deep=True))
            writer.correct_identifier(ADDR_A, B, grounds="g")
        original = CorpusWriter._delete_locked
        armed = {"once": True}

        def interrupt(self, ref):
            if armed["once"] and self.root == right.root:
                armed["once"] = False
                raise RuntimeError("interrupted after keep's replacement")
            return original(self, ref)

        monkeypatch.setattr(CorpusWriter, "_delete_locked", interrupt)
        with pytest.raises(RuntimeError):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="first", **REPORT)
        first = stored.identifier_corrections(left.read_view.get(ADDR_B))
        assert len(first) == 2 and first[1].grounds == "first"
        assert right.read_view.holds(ADDR_B)
        survivor, keep_report, other_report = consolidate((left, ADDR_B), (right, ADDR_B), rationale="second", **REPORT)
        assert stored.identifier_corrections(survivor) == first
        assert first[1].event_token != keep_report.event_token == other_report.event_token
        assert not right.read_view.holds(ADDR_B)

    def test_consolidate_refuses_conflicting_token_reuse(self, two_writers):
        left, right = two_writers
        left.add(stored.source_node(title="p", identifiers=A))
        corrected = left.correct_identifier(ADDR_A, B, grounds="g")
        (held,) = stored.identifier_corrections(corrected)
        reused = raw_source(B, history=[entry(A, B, token=held.event_token, grounds="other grounds")], deprecated=[ADDR_A])
        right.import_bundle([reused], **REPORT)
        before = (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B))
        intents_before = {id(w): list(_recording_port(w).intents) for w in (left, right)}
        with pytest.raises(HistoryDisagreement, match="two different events"):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B)) == before
        for writer in (left, right):
            assert _recording_port(writer).intents == intents_before[id(writer)]

    @pytest.mark.parametrize("rationale", ["", "\ud800"], ids=["empty", "unencodable"])
    @pytest.mark.parametrize("divergent", [False, True], ids=["identity-path", "absorb-path"])
    def test_consolidate_refuses_a_malformed_rationale_on_both_paths(self, two_writers, rationale, divergent):
        left, right = two_writers
        node = stored.source_node(title="p", identifiers=A)
        left.add(node.model_copy(deep=True))
        left.correct_identifier(ADDR_A, B, grounds="g")
        if divergent:
            right.add(node.model_copy(deep=True))
            right.correct_identifier(ADDR_A, B, grounds="g2")
        else:
            right.import_bundle([left.read_view.get(ADDR_B)], **REPORT)
        before = (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B))
        intents_before = {id(w): list(_recording_port(w).intents) for w in (left, right)}
        reports_before = {id(w): sum(n.kind == "act-report" for n in w.read_view.iter_stored()) for w in (left, right)}
        with pytest.raises(RelocationRefused, match="rationale"):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale=rationale, **REPORT)
        assert (left.read_view.get(ADDR_B), right.read_view.get(ADDR_B)) == before
        for writer in (left, right):
            assert _recording_port(writer).intents == intents_before[id(writer)]
            assert sum(n.kind == "act-report" for n in writer.read_view.iter_stored()) == reports_before[id(writer)]

    def test_divergent_identifier_maps_refuse_consolidation(self, two_writers):
        left, right = two_writers
        left.add(stored.source_node(title="p", identifiers=B))
        right.add(stored.source_node(title="p", identifiers={**B, "isbn": "9780306406157"}))
        with pytest.raises(HistoryDisagreement, match="isbn"):
            consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)

    def test_consolidate_refuses_a_handle_addressed_replica_at_replace(self, two_writers):
        left, right = two_writers
        forged = raw_source(B, node_id="source:Chen2023")
        for writer in (left, right):
            raw_write(writer.root, forged)
            writer._reconstruct()
        with pytest.raises(SourceAddressDisagreement):
            consolidate((left, forged.id), (right, forged.id), rationale="r", **REPORT)

    def test_consolidate_accepts_byte_identical_replicas(self, two_writers):
        left, right = two_writers
        minted = left.add(stored.source_node(title="p", identifiers=A))
        corrected = left.correct_identifier(minted.id, B, grounds="g")
        right.import_bundle([corrected], **REPORT)
        survivor, *_ = consolidate((left, ADDR_B), (right, ADDR_B), rationale="r", **REPORT)
        assert survivor.uid == corrected.uid and survivor.deprecated_ids == [ADDR_A]
        assert stored.identifier_corrections(survivor) == stored.identifier_corrections(corrected)
