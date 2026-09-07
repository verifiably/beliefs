"""R19 and R22 at the explicit-import boundary (world-changing families §6.3).

Explicit import is an **operation**, and this is where a derivation is
recomputed before anything is written: a verification whose two runs resolve
here has its verdict recomputed from them, an assessment has its facet
recomputed from its run, and a record that contradicts its own recomputation
refuses the whole bundle before the payload transaction opens.

The two negatives are the point of the row, not decoration. Mounting the runs
a forged verification names is **not** an epistemic event — nothing revalidates
on arrival — and writing the same forgery straight into a corpus directory
bypasses the operation entirely, so it is caught only when an audit runs.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import TypedDict

import pytest
from fixtures_cut3 import spec_draft, spec_rules
from fixtures_cut4 import path_for, raw_write
from nodes.core.node import Node
from test_audit import (
    _interpretation_evidence,
    _stated_optionals,
    _tampered_stale,
    add_observed_datasets,
    assessment_closure,
    run_publication,
)
from test_relocation import _writer, _writer_for

from beliefs import runrecord, stored
from beliefs.assess import build_assessment
from beliefs.audit import DerivationEvidence, audit_corpus
from beliefs.corpus import corpus_check
from beliefs.errors import ImportRefused
from beliefs.recipe import ResultManifest
from beliefs.record import AssessmentValue
from beliefs.replay import CONTENT_EQUALITY
from beliefs.report import ImportedRecords
from beliefs.runrecord import run_ref
from beliefs.spec import freeze
from beliefs.verification import ADMITTED, lifecycle_state
from beliefs.verify import AssessmentVerification, build_verification


class _ImportFields(TypedDict):
    """The report fields every import here shares, typed so unpacking them
    beside an explicit `evidence=` cannot be read as supplying it."""

    observer: str
    instrument: str
    opened_at: str
    closed_at: str


IMPORT_FIELDS: _ImportFields = {
    "observer": "o",
    "instrument": "i",
    "opened_at": "2026-09-04T00:00:00Z",
    "closed_at": "2026-09-04T00:00:01Z",
}
CONTRACT = "science:" + "c" * 64
EPOCH = "epoch:" + "e" * 64
ASSESSMENT_REF = "assessment:a"
"""What the `verifies` edge binds. It resolves nowhere here on purpose: a
verification is *about* an assessment identity, and the corpus address it names
is a separate fact an importing corpus may simply not hold."""

DISAGREEING_RESULT = ResultManifest(
    outputs=(("out-a", "sha256:" + "a" * 64), ("out-b", "sha256:" + "b" * 64))
)
"""A replay manifest the held equivalence rule maps to `failed` — the honest
verdict a forgery claiming `passed` contradicts."""


def _evidence(frozen) -> DerivationEvidence:
    """Task 3's interpretation evidence, plus the equivalence implementation a
    verification recomputation resolves from the original run's bindings."""
    return replace(
        _interpretation_evidence(frozen), held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY}
    )


def _flip(verdict: str) -> str:
    return "failed" if verdict == "passed" else "passed"


def _stored_from(
    verification: AssessmentVerification,
    *,
    slug: str = "v",
    supersedes: str | None = None,
    verdict: str | None = None,
    scope: str | None = None,
) -> Node:
    """The stored record for a derived verification value: the assessment
    identity it is about, its verdict and scope, and the two runs it names."""
    return stored.verification_node(
        slug,
        title=slug,
        assessment=verification.assessment,
        assessment_ref=ASSESSMENT_REF,
        scope=verification.scope if scope is None else scope,
        verdict=verification.verdict if verdict is None else verdict,
        supersedes=supersedes,
        derivation=(run_ref(verification.original), run_ref(verification.replayed)),
    )


def _assessment_node_from(derived: AssessmentValue, *, slug: str, proposition: str, outcome: str) -> Node:
    return stored.assessment_node(
        slug,
        title=slug,
        spec=derived.spec,
        run=runrecord.run_ref(derived.run),
        proposition=proposition,
        outcome=outcome,
        interpretation_rule=derived.interpretation_rule,
        **_stated_optionals(derived),
    )


def _report_findings(report) -> tuple[str, ...]:
    """The findings the stored act-report entry carries."""
    outcome = report.entries[0].outcome
    assert isinstance(outcome, ImportedRecords)
    return outcome.findings


def _admission(w, identity: str) -> str:
    """Kernel §3.3's state for one assessment identity, over every verification
    the corpus holds — the only thing the mount, the audit and the superseding
    act are allowed to move, and only the last of them may."""
    return lifecycle_state(
        tuple(
            value
            for value in (
                stored.verification_value(node)
                for node in w.read_view.iter_stored()
                if node.kind == "verification"
            )
            if value.assessment == identity
        )
    )


def _two_runs(corpus, *, mount: bool, agreeing: bool) -> SimpleNamespace:
    """Two assessment-shaped runs of one recipe, a frozen spec, the held
    equivalence and interpretation implementations, and the verification
    `build_verification` derives from them.

    `mount=False` leaves the runs out of the corpus but keeps their stored
    records, so a later import is the mount R19 transition (b) asks for.

    `corpus` is a path here and an open durable writer in Task 8's acceptance
    module, so both suites build the pair through one construction.
    """
    writer = _writer_for(corpus)
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    evidence = _evidence(frozen)
    original = assessment_closure(frozen, token="tok-original")
    replayed = assessment_closure(
        frozen, token="tok-replayed", result=None if agreeing else DISAGREEING_RESULT
    )
    original_node = run_publication(original)
    replayed_node = run_publication(replayed)
    if mount:
        add_observed_datasets(writer, original)
        writer.add(original_node)
        writer.add(replayed_node)
    verification = build_verification(
        original,
        replayed,
        specs=evidence.specs,
        held_rules=evidence.held_rules,
        contract_identity=CONTRACT,
        epoch=EPOCH,
    )
    assert isinstance(verification, AssessmentVerification)
    return SimpleNamespace(
        writer=writer,
        spec=frozen,
        evidence=evidence,
        original=original,
        replayed=replayed,
        original_node=original_node,
        replayed_node=replayed_node,
        verification=verification,
        assessment_identity=verification.assessment,
    )


@pytest.fixture()
def derived(tmp_path):
    """Two persisted assessment-shaped runs of one recipe, a frozen spec, the
    held equivalence and interpretation implementations, and the verification
    `build_verification` derives from them. The replay agrees, so the derived
    verdict is `passed` and any other stored verdict is a contradiction."""
    namespace = _two_runs(tmp_path / "corpus", mount=True, agreeing=True)
    assert namespace.verification.verdict == "passed"
    return namespace


@pytest.fixture()
def derived_unmounted(tmp_path):
    """The same two runs, **not** persisted, and a replay that disagrees: the
    honest verdict is `failed`, so a forgery claiming `passed` admits while its
    runs are absent and is contradicted the moment they are mounted."""
    namespace = _two_runs(tmp_path / "corpus", mount=False, agreeing=False)
    assert namespace.verification.verdict == "failed"
    return namespace


class TestR19ExplicitImport:
    def test_a_forged_verification_with_resolvable_runs_is_refused_before_any_write(self, derived):
        genuine = derived.verification
        forged = stored.verification_node(
            "forged",
            title="forged",
            assessment=genuine.assessment,
            assessment_ref=ASSESSMENT_REF,
            scope=genuine.scope,
            verdict=_flip(genuine.verdict),
            derivation=(run_ref(genuine.original), run_ref(genuine.replayed)),
        )
        before = sorted(p for p in derived.writer.root.rglob("*.md"))
        with pytest.raises(ImportRefused) as refused:
            derived.writer.import_bundle([forged], evidence=derived.evidence, **IMPORT_FIELDS)
        assert refused.value.member == forged.id
        assert not path_for(derived.writer.root, forged.id).exists()
        # the refusal report is the import family's own; no bundle member landed
        assert [
            p for p in derived.writer.root.rglob("*.md") if p not in before and "act-report" not in str(p)
        ] == []

    def test_an_import_whose_runs_do_not_resolve_proceeds_with_a_finding(self, tmp_path):
        writer = _writer(tmp_path / "c")
        unresolvable = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
            derivation=("run:nowhere", "run:nowhere-2"),
        )
        report = writer.import_bundle([unresolvable], **IMPORT_FIELDS)
        findings = _report_findings(report)
        assert any(f.startswith("derivation-unchecked: verification:v") for f in findings)
        assert writer.read_view.get(unresolvable.id).facets[stored.VERIFICATION_FACET].get("validated") is None

    def test_no_validation_state_is_written_onto_a_verification(self, derived):
        node = _stored_from(derived.verification)
        derived.writer.import_bundle([node], evidence=derived.evidence, **IMPORT_FIELDS)
        assert "validated" not in derived.writer.read_view.get(node.id).facets[stored.VERIFICATION_FACET]

    def test_a_genuine_verification_imports(self, derived):
        node = _stored_from(derived.verification)
        derived.writer.import_bundle([node], evidence=derived.evidence, **IMPORT_FIELDS)
        assert derived.writer.read_view.get(node.id).kind == "verification"

    def test_evidence_is_supplied_and_never_ambient(self, derived):
        """The same forgery the resolvable-runs case refuses admits with a
        finding when the caller holds nothing: unchecked is not a verdict."""
        forged = _stored_from(derived.verification, slug="forged", verdict=_flip(derived.verification.verdict))
        report = derived.writer.import_bundle([forged], **IMPORT_FIELDS)
        assert any(f.startswith(f"derivation-unchecked: {forged.id}") for f in _report_findings(report))
        assert derived.writer.read_view.get(forged.id).kind == "verification"

    def test_a_malformed_derivation_member_refuses_the_bundle(self, derived):
        """`verification_derivation` refuses rather than repairs, and so does
        the boundary that reads it: a member that cannot be read is not one
        that reads as absent."""
        node = _stored_from(derived.verification, slug="malformed")
        facet = {**node.facets[stored.VERIFICATION_FACET], "derivation": {"original": "run:o"}}
        malformed = node.model_copy(update={"facets": {**node.facets, stored.VERIFICATION_FACET: facet}})
        stored.stamp_semantic_identity(malformed)
        with pytest.raises(ImportRefused) as refused:
            derived.writer.import_bundle([malformed], evidence=derived.evidence, **IMPORT_FIELDS)
        assert refused.value.member == malformed.id
        assert not path_for(derived.writer.root, malformed.id).exists()

    def test_a_stale_run_leaves_the_arriving_verification_unchecked_not_refused(self, derived):
        """A neighbour whose own stamp is stale is `corpus_check`'s to classify,
        under its own ref. The arriving record is neither convicted of its
        neighbour's fault nor validated: it admits, unchecked, with the
        neighbour named in the reason."""
        run = derived.writer.read_view.get(run_ref(derived.original.address()))
        _tampered_stale(derived.writer, run)
        node = _stored_from(derived.verification)
        report = derived.writer.import_bundle([node], evidence=derived.evidence, **IMPORT_FIELDS)
        assert any(
            finding.startswith(f"derivation-unchecked: {node.id}")
            and run.id in finding
            and "is malformed here" in finding
            for finding in _report_findings(report)
        )
        assert derived.writer.read_view.get(node.id).kind == "verification"


class TestR19TransitionB:
    def test_forged_unavailable_to_available(self, derived_unmounted):
        """Import the forgery while its runs are absent → admits; mount the
        runs → admission unchanged; audit → contradiction, mints nothing;
        constructor act → superseding verification; admission changes because
        of that node."""
        w = derived_unmounted.writer
        identity = derived_unmounted.assessment_identity
        genuine = derived_unmounted.verification
        forged = stored.verification_node(
            "forged",
            title="forged",
            assessment=identity,
            assessment_ref=ASSESSMENT_REF,
            scope="clean-environment",
            verdict="passed",
            derivation=(run_ref(genuine.original), run_ref(genuine.replayed)),
        )
        report = w.import_bundle([forged], evidence=derived_unmounted.evidence, **IMPORT_FIELDS)
        assert any(f.startswith(f"derivation-unchecked: {forged.id}") for f in _report_findings(report))
        assert _admission(w, identity) == ADMITTED
        assert audit_corpus(w.read_view, evidence=derived_unmounted.evidence, profile=w.profile) == ()

        w.import_bundle(
            [derived_unmounted.original_node, derived_unmounted.replayed_node], **IMPORT_FIELDS
        )  # the mount
        assert _admission(w, identity) == ADMITTED, "mounting is not an epistemic event"
        assert "validated" not in w.read_view.get(forged.id).facets[stored.VERIFICATION_FACET]

        files = sorted(p for p in w.root.rglob("*.md"))
        findings = audit_corpus(w.read_view, evidence=derived_unmounted.evidence, profile=w.profile)
        assert [f.code for f in findings] == ["verification-derivation-contradicted"]
        assert [f.ref for f in findings] == [forged.id]
        assert sorted(p for p in w.root.rglob("*.md")) == files, "the audit mints nothing"
        assert _admission(w, identity) == ADMITTED, "the audit alone changes nothing"

        superseding = build_verification(
            derived_unmounted.original,
            derived_unmounted.replayed,
            specs=derived_unmounted.evidence.specs,
            held_rules=derived_unmounted.evidence.held_rules,
            contract_identity=CONTRACT,
            epoch=EPOCH,
        )
        assert isinstance(superseding, AssessmentVerification)
        node = _stored_from(superseding, slug="superseding", supersedes=forged.id)
        w.import_bundle([node], evidence=derived_unmounted.evidence, **IMPORT_FIELDS)
        assert _admission(w, identity) != ADMITTED
        assert [f.ref for f in audit_corpus(w.read_view, evidence=derived_unmounted.evidence, profile=w.profile)] == [forged.id]


class TestR19NegativesDAndE:
    def test_a_raw_written_forgery_is_caught_only_under_audit(self, derived):
        forged = _stored_from(derived.verification, slug="forged", verdict=_flip(derived.verification.verdict))
        raw_write(derived.writer.root, forged)  # `verification_node` already stamps it
        derived.writer._reconstruct()
        assert derived.writer.read_view.get(forged.id).kind == "verification"  # not refused, not detected on read
        assert corpus_check(derived.writer.read_view, derived.writer.profile) == ()  # the corpus check says nothing
        assert [f.code for f in audit_corpus(derived.writer.read_view, evidence=derived.evidence, profile=derived.writer.profile)] == [
            "verification-derivation-contradicted"
        ]

    def test_a_self_consistent_raw_run_is_not_detected_and_an_unaudited_forgery_is_indistinguishable(
        self, derived
    ):
        """A raw-written run whose own hashes agree is invisible to every read
        path — nothing structural is wrong, because nothing is — and a forged
        verification differs from a genuine one on no read-path predicate at
        all. Log-backed detection is Task 8's durable arm; this closes neither
        limitation, it pins them."""
        third = assessment_closure(derived.spec, token="tok-raw")
        raw_write(derived.writer.root, run_publication(third))
        derived.writer._reconstruct()
        view = derived.writer.read_view
        raw_run = view.get(run_ref(third.address()))
        assert raw_run.kind == "run"
        # its internal hashes agree: the projection decodes and readdresses to
        # the id it was written under
        assert run_ref(runrecord.decode_run_closure(raw_run).address()) == raw_run.id
        assert corpus_check(view, derived.writer.profile) == ()
        assert audit_corpus(view, evidence=derived.evidence, profile=derived.writer.profile) == ()  # recomputation has nothing to contradict

        genuine = _stored_from(derived.verification, slug="genuine")
        forged = _stored_from(
            derived.verification, slug="forged", verdict=_flip(derived.verification.verdict)
        )
        raw_write(derived.writer.root, genuine)
        raw_write(derived.writer.root, forged)
        derived.writer._reconstruct()
        view = derived.writer.read_view

        def read_path(node_id: str) -> tuple[object, ...]:
            record = view.get(node_id)
            return (
                view.holds(node_id),
                record.kind,
                stored.semantic_hash_missing(record),
                stored.semantic_hash_disagrees(record),
                stored.verification_derivation(record),
                "validated" in record.facets[stored.VERIFICATION_FACET],
                {finding.code for finding in corpus_check(view, derived.writer.profile) if finding.ref == node_id},
            )

        assert read_path(genuine.id) == read_path(forged.id)
        assert corpus_check(view, derived.writer.profile) == ()
        assert {(f.code, f.ref) for f in audit_corpus(view, evidence=derived.evidence, profile=derived.writer.profile)} == {
            ("verification-derivation-contradicted", forged.id)
        }


class TestR22ExplicitImport:
    def test_import_recomputes_the_assessment_facet_and_refuses_a_mismatch(self, derived):
        genuine = build_assessment(
            derived.original, specs=derived.evidence.specs, implementations=derived.evidence.implementations
        )
        assert isinstance(genuine, AssessmentValue)
        proposition = derived.writer.add(
            stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
        )
        forged = _assessment_node_from(
            genuine,
            slug="forged",
            proposition=proposition.id,
            outcome="refuted" if genuine.outcome == "supported" else "supported",
        )
        with pytest.raises(ImportRefused) as refused:
            derived.writer.import_bundle([forged], evidence=derived.evidence, **IMPORT_FIELDS)
        assert refused.value.member == forged.id
        assert not path_for(derived.writer.root, forged.id).exists()

    def test_a_genuine_assessment_imports(self, derived):
        genuine = build_assessment(
            derived.original, specs=derived.evidence.specs, implementations=derived.evidence.implementations
        )
        assert isinstance(genuine, AssessmentValue)
        proposition = derived.writer.add(
            stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
        )
        node = _assessment_node_from(
            genuine, slug="a1", proposition=proposition.id, outcome=genuine.outcome
        )
        derived.writer.import_bundle([node], evidence=derived.evidence, **IMPORT_FIELDS)
        assert derived.writer.read_view.get(node.id).kind == "assessment"

    def test_a_raw_written_assessment_is_caught_only_under_audit(self, derived):
        genuine = build_assessment(
            derived.original, specs=derived.evidence.specs, implementations=derived.evidence.implementations
        )
        assert isinstance(genuine, AssessmentValue)
        proposition = derived.writer.add(
            stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
        )
        forged = _assessment_node_from(
            genuine,
            slug="forged",
            proposition=proposition.id,
            outcome="refuted" if genuine.outcome == "supported" else "supported",
        )
        raw_write(derived.writer.root, forged)
        derived.writer._reconstruct()
        assert derived.writer.read_view.get(forged.id).kind == "assessment"
        assert corpus_check(derived.writer.read_view, derived.writer.profile) == ()
        assert [f.code for f in audit_corpus(derived.writer.read_view, evidence=derived.evidence, profile=derived.writer.profile)] == [
            "assessment-derivation-contradicted"
        ]
