"""The corpus-local semantic audit (world-changing families §6.3, §7)."""

from __future__ import annotations

from dataclasses import replace

import pytest
from authority import ACTOR
from closure_fixtures import make_closure
from fixtures_cut3 import spec_draft, spec_rules
from fixtures_cut4 import raw_write
from nodes.core.node import Node
from test_relocation import _writer
from test_relocation_rows import _basis_route

from beliefs import audit, belief, corpus, runrecord, stored
from beliefs.assess import build_assessment
from beliefs.audit import (
    NO_EVIDENCE,
    DerivationEvidence,
    DerivationOutcome,
    audit_corpus,
    check_lineage_basis,
)
from beliefs.errors import MalformedRecord, SignatureRefused
from beliefs.recipe import ResultManifest, RunClosure
from beliefs.record import AssessmentValue
from beliefs.replay import CONTENT_EQUALITY, EquivalenceImplementation
from beliefs.spec import freeze
from beliefs.verify import AssessmentVerification, build_verification

PINNED = [{"name": "matrix", "digest": "sha256:" + "1" * 64}]


@pytest.fixture()
def writer(tmp_path):
    return _writer(tmp_path / "corpus")


def _producing_run(slug: str, dataset_id: str) -> Node:
    """A minimal run node holding a `produces` edge to `dataset_id`."""
    return stored.run_node(slug, title=slug, spec="analysis-spec:s1", produces=[dataset_id])


def _bystander(writer) -> str:
    """A record `corpus_check` flags, minted so a finding already exists by the
    time the malformed one is reached. Its survival is the assertion."""
    node = stored.proposition_node("bystander", title="bystander", claim={"operator": "affects"})
    del node.facets[stored.SEMANTIC_IDENTITY_FACET]
    raw_write(writer.root, node)
    return node.id


def _derived_run(writer):
    """A real, decodable assessment run and the frozen spec it was run under.

    The closure fixture's recipe binds one placeholder rule, so its bindings are
    replaced with the frozen spec's own — `build_assessment` and `_resolve_rule`
    both read the **recipe's** bindings, not the spec's.
    """
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    closure = assessment_closure(frozen)
    add_observed_datasets(writer, closure)
    run = writer.add(run_publication(closure))
    return frozen, closure, run


def assessment_closure(frozen, *, token: str = "tok", result: ResultManifest | None = None) -> RunClosure:
    """One decodable assessment closure run under `frozen`.

    `token` and `result` are what a second closure of the same recipe varies:
    both are covered by the closure address, so either yields a distinct run —
    a replay that agrees (same result) or one that does not.
    """
    base = make_closure(shape="assessment", token=token)
    recipe = replace(base.recipe, spec_identity=frozen.identity, rule_bindings=frozen.rule_bindings)
    return RunClosure(
        recipe=recipe,
        result=base.result if result is None else result,
        # The closure fixture's occurrence names `tester`; a run closure added
        # directly must name the writer's bound actor (write permits §4.2).
        occurrence=replace(base.occurrence, actor=ACTOR),
    )


def add_observed_datasets(writer, closure: RunClosure) -> None:
    """Mint the empirical dataset each `observes` input names, once. Two runs of
    one recipe observe the same dataset, and minting it twice collides."""
    for entry in closure.recipe.inputs:
        if entry.role == "observes" and not writer.read_view.holds(entry.dataset):
            writer.add(
                stored.dataset_node(
                    entry.dataset.removeprefix("dataset:"),
                    title="raw",
                    resources=PINNED,
                    empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
                )
            )


def run_publication(closure: RunClosure) -> Node:
    """The stored run record a boundary publication of `closure` would write."""
    return stored.run_publication_node(
        closure.address(),
        title="assessment run",
        projection=runrecord.projection_text(closure).decode("utf-8"),
        spec=closure.recipe.spec_identity,
        observes=tuple(e.dataset for e in closure.recipe.inputs if e.role == "observes"),
        reads=tuple(e.dataset for e in closure.recipe.inputs if e.role == "reads"),
    )


def _stated_optionals(derived: AssessmentValue) -> dict[str, str]:
    """The optional members the derived value actually states. Absent optionals
    stay absent — a stored `None` is a different facet from an omitted one."""
    return {
        name: value
        for name in ("estimate", "uncertainty", "estimand", "applicability")
        if isinstance(value := getattr(derived, name), str)
    }


def _interpretation_evidence(frozen) -> DerivationEvidence:
    implementation = spec_rules()[frozen.interpretation_rule]
    return DerivationEvidence(
        specs={frozen.identity: frozen},
        held_rules={},
        implementations={implementation.identity: implementation},
    )


def _verification_evidence(frozen) -> DerivationEvidence:
    """The interpretation evidence above, plus the equivalence implementation
    the original run's own `rule_bindings` name — what recomputing a *verdict*
    needs and what recomputing a facet does not."""
    return replace(
        _interpretation_evidence(frozen), held_rules={CONTENT_EQUALITY.identity: CONTENT_EQUALITY}
    )


DISAGREEING_RESULT = ResultManifest(
    outputs=(("out-a", "sha256:" + "a" * 64), ("out-b", "sha256:" + "b" * 64))
)
"""A replay manifest the held content-identity rule maps to `failed`. Reaching
a failing verdict this way needs no second engine: the rule compares the two
result manifests, and these differ."""


def _replayed_pair(writer, *, agreeing: bool = True) -> tuple[DerivationEvidence, AssessmentVerification]:
    """Two persisted assessment runs of one recipe, and the verification
    `build_verification` derives from them. Both runs are decodable, so a
    stored record naming them can actually be recomputed."""
    frozen = freeze(spec_draft(), held_rules=spec_rules())
    original = assessment_closure(frozen, token="tok-original")
    replayed = assessment_closure(
        frozen, token="tok-replayed", result=None if agreeing else DISAGREEING_RESULT
    )
    add_observed_datasets(writer, original)
    writer.add(run_publication(original))
    writer.add(run_publication(replayed))
    evidence = _verification_evidence(frozen)
    derived = build_verification(
        original,
        replayed,
        specs=evidence.specs,
        held_rules=evidence.held_rules,
        contract_identity="science:" + "c" * 64,
        epoch="epoch:" + "e" * 64,
    )
    assert isinstance(derived, AssessmentVerification)
    return evidence, derived


def _eligible_assessment(writer) -> Node:
    """An assessment the write boundary admits, over a run carrying no closure
    projection: eligibility is a stored-edge predicate, and a decodable run
    closure is a separate fact that a hand-built run simply does not have."""
    dataset = writer.add(
        stored.dataset_node("raw", title="raw", resources=PINNED, empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR})
    )
    run = writer.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[dataset.id]))
    proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    return writer.add(
        stored.assessment_node(
            "a1",
            title="a1",
            spec="analysis-spec:s1",
            run=run.id,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule="rule:threshold",
        )
    )


def raw_cyclic_retraction_pair(writer) -> tuple[Node, Node]:
    """Two retractions naming each other, written behind the boundary.

    A retraction's slug *is* the digest of its own facet, and that facet names
    the target's ref and content identity — so a pair in which each retracts
    the other has no fixed point and cannot be minted at all. Fabricating one
    is the only way such a pair reaches a store, and what reaches it is
    malformed by construction: the mutated member's id no longer recomputes
    from its facet, and both name a content identity that resolves to nothing.
    A fixture for **classification**, never a test for acyclicity.
    """

    def retraction(title: str, target_ref: str) -> Node:
        return stored.retraction_node(
            title=title,
            target=stored.NodeTarget(target_ref, target_ref, "sha256:" + "e" * 64),
            reason="authored-error",
            rationale="each of the pair withdraws the other",
            grounds=("verification:absent",),
            actor=ACTOR,
            event_token="event-cycle",
        )

    second = retraction("second", "retraction:pending")
    first = retraction("first", second.id)
    facet = dict(second.facets[stored.RETRACTION_FACET])
    facet["target"] = {**facet["target"], "ref": first.id, "resolved": first.id}
    second.facets[stored.RETRACTION_FACET] = facet
    second.relations = [
        relation.model_copy(update={"target": first.id}) if relation.predicate == stored.RETRACTS else relation
        for relation in second.relations
    ]
    stored.stamp_semantic_identity(second)

    raw_write(writer.root, first)
    raw_write(writer.root, second)
    writer._reconstruct()
    return first, second


class TestTheDerivationMember:
    def test_a_verification_may_name_its_two_runs(self):
        node = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
            derivation=("run:orig", "run:replay"),
        )
        assert stored.verification_derivation(node) == ("run:orig", "run:replay")
        assert stored.verification_value(node).verdict == "passed"

    def test_a_verification_without_one_reads_none(self):
        node = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
        )
        assert stored.verification_derivation(node) is None

    @pytest.mark.parametrize(
        "bad",
        [
            {"original": "run:o"},
            {"original": 1, "replayed": "run:r"},
            {"original": "run:o", "replayed": "run:r", "extra": 1},
            {"original": "run:o", "replayed": "replay:r"},
            "run:o",
        ],
    )
    def test_a_malformed_member_refuses_rather_than_repairs(self, bad):
        node = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
        )
        facet = {**node.facets[stored.VERIFICATION_FACET], "derivation": bad}
        malformed = node.model_copy(update={"facets": {stored.VERIFICATION_FACET: facet}})
        with pytest.raises(MalformedRecord):
            stored.verification_derivation(malformed)

    def test_the_member_is_covered_by_the_semantic_stamp(self):
        without = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
        )
        with_it = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
            derivation=("run:o", "run:r"),
        )
        assert stored.recompute_semantic_hash(without) != stored.recompute_semantic_hash(with_it)


class TestTheEvidenceIsExplicit:
    def test_no_evidence_holds_nothing(self):
        assert NO_EVIDENCE == DerivationEvidence(specs={}, held_rules={}, implementations={})


class TestOmegaValidComesFirst:
    def test_a_malformed_record_is_classified_and_nothing_reads_it(self, writer, monkeypatch):
        """M3's audit arm: a raw-written cyclic retraction pair is malformed
        (its content identities cannot close), and the audit says so before
        any standing or belief evaluation — asserted by making both raise."""
        raw_cyclic_retraction_pair(writer)
        monkeypatch.setattr(corpus, "standing_in_local_view", lambda *a, **k: pytest.fail("standing was evaluated"))
        monkeypatch.setattr(belief, "evaluate", lambda *a, **k: pytest.fail("belief was evaluated"))
        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert findings and all(finding.severity == "error" for finding in findings)
        assert {finding.code for finding in findings} <= {
            "semantic-hash-stale",
            "semantic-hash-missing",
            "retraction-target-invalid",
            "retraction-cycle",
        }

    def test_a_flagged_record_is_not_recomputed(self, writer, monkeypatch):
        calls: list[str] = []
        monkeypatch.setattr(
            audit,
            "check_verification",
            lambda view, node, *, evidence: calls.append(node.id) or audit.DerivationOutcome(False, "stub", None),
        )
        bad = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
        )
        del bad.facets[stored.SEMANTIC_IDENTITY_FACET]
        raw_write(writer.root, bad)  # unstamped: semantic-hash-missing
        writer._reconstruct()
        audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert calls == []


class TestTheAuditMintsNothing:
    def test_audit_writes_no_file_and_appends_no_intent(self, writer):
        writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
        before = sorted(p for p in writer.root.rglob("*") if p.is_file())
        port = writer._operation_port
        audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert sorted(p for p in writer.root.rglob("*") if p.is_file()) == before
        assert port.intents == [] and port.fulfilling == []


def forged_single_over_two_producers(writer) -> Node:
    """A dataset two runs produce, carrying a raw-written `single(A)` basis —
    R23's forgery, which the API cannot spell (§11.11). Returns `B`'s run, the
    record whose deletion leaves nothing to contradict the forgery (§7).

    Module-level rather than inline: `test_deletion_rows.py` builds the same
    state for the cut-18 R23 row, and one construction serves both.
    """
    dataset = writer.add(stored.dataset_node("d", title="d", resources=PINNED))
    writer.add(_producing_run("a", dataset.id))
    run_b = writer.add(_producing_run("b", dataset.id))
    forged = dataset.model_copy(
        update={
            "facets": {
                **dataset.facets,
                stored.LINEAGE_BASIS_FACET: {"tag": "single", "routes": [_basis_route("a")]},
            }
        }
    )
    raw_write(writer.root, stored.stamp_semantic_identity(forged))
    writer._reconstruct()
    return run_b


class TestLineageBasisRecomputation:
    def test_a_forged_single_is_contradicted_while_the_second_producer_stands(self, writer):
        """R23's audit clause: `single(A)` stamped, `B` also produces → finding;
        delete `B`'s run → the semantic finding disappears (§7)."""
        run_b = forged_single_over_two_producers(writer)

        codes = [f.code for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE)]
        assert codes == ["lineage-basis-contradicted"]

        writer.delete(run_b.id)
        assert [f.code for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE)] == []

    def test_a_basis_naming_every_producer_is_not_contradicted(self, writer):
        dataset = writer.add(stored.dataset_node("d", title="d", resources=PINNED))
        writer.add(_producing_run("a", dataset.id))
        assert check_lineage_basis(writer.read_view, dataset) == DerivationOutcome(False, "no stamped basis", None)

        stamped = dataset.model_copy(
            update={
                "facets": {
                    **dataset.facets,
                    stored.LINEAGE_BASIS_FACET: {"tag": "single", "routes": [_basis_route("a")]},
                }
            }
        )
        raw_write(writer.root, stored.stamp_semantic_identity(stamped))
        writer._reconstruct()

        node = writer.read_view.get(dataset.id)
        assert check_lineage_basis(writer.read_view, node) == DerivationOutcome(True, "", None)
        assert audit_corpus(writer.read_view, evidence=NO_EVIDENCE) == ()


class TestUncheckedIsNotContradicted:
    def test_a_verification_without_a_derivation_member_is_unchecked(self, writer):
        node = writer.add(
            stored.verification_node(
                "v",
                title="v",
                assessment="a" * 64,
                assessment_ref="assessment:a",
                scope="clean-environment",
                verdict="passed",
            )
        )
        outcome = audit.check_verification(writer.read_view, node, evidence=NO_EVIDENCE)
        assert outcome == audit.DerivationOutcome(False, "no derivation member", None)

    def test_a_verification_whose_runs_do_not_resolve_is_unchecked(self, writer):
        node = writer.add(
            stored.verification_node(
                "v",
                title="v",
                assessment="a" * 64,
                assessment_ref="assessment:a",
                scope="clean-environment",
                verdict="passed",
                derivation=("run:o", "run:r"),
            )
        )
        outcome = audit.check_verification(writer.read_view, node, evidence=NO_EVIDENCE)
        assert not outcome.checked and "run:o" in outcome.reason and outcome.contradiction is None

    def test_an_assessment_whose_run_carries_no_closure_is_unchecked(self, writer):
        node = _eligible_assessment(writer)
        outcome = audit.check_assessment(writer.read_view, node, evidence=NO_EVIDENCE)
        assert not outcome.checked and "projection" in outcome.reason and outcome.contradiction is None


class TestTheAuditReportsAndNeverRaises:
    """A record whose members refuse to be read is a finding, not an abort:
    `corpus_check`'s contract is "reported and never raised", and an audit that
    raised would discard every finding already collected for its neighbours."""

    def test_a_stamp_consistent_verification_with_a_malformed_derivation(self, writer):
        bystander = _bystander(writer)
        node = stored.verification_node(
            "v",
            title="v",
            assessment="a" * 64,
            assessment_ref="assessment:a",
            scope="clean-environment",
            verdict="passed",
        )
        node.facets[stored.VERIFICATION_FACET] = {
            **node.facets[stored.VERIFICATION_FACET],
            "derivation": {"original": "run:o"},
        }
        raw_write(writer.root, stored.stamp_semantic_identity(node))
        writer._reconstruct()

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("derivation-malformed", node.id),
        }

    def test_a_verification_kind_node_carrying_no_verification_facet(self, writer):
        bystander = _bystander(writer)
        hollow = Node(id="verification:hollow", kind="verification", title="hollow", facets={}, relations=[])
        raw_write(writer.root, stored.stamp_semantic_identity(hollow))
        writer._reconstruct()

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("derivation-malformed", hollow.id),
        }

    def test_an_assessment_whose_stored_outcome_is_outside_the_closed_set(self, writer):
        bystander = _bystander(writer)
        dataset = writer.add(
            stored.dataset_node("raw", title="raw", resources=PINNED, empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR})
        )
        run = writer.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[dataset.id]))
        proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        node = writer.add(
            stored.assessment_node(
                "a1",
                title="a1",
                spec="analysis-spec:s1",
                run=run.id,
                proposition=proposition.id,
                outcome="maybe",
                interpretation_rule="rule:threshold",
            )
        )

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("derivation-malformed", node.id),
        }

    def test_an_assessment_naming_a_dataset_production_run(self, writer):
        """`build_assessment` refuses a dataset-production closure with
        `SignatureRefused` (R7), not `MalformedRecord`. Catching only the
        latter let one such assessment abort the whole audit and discard every
        finding already collected — the failure mode the malformed-record catch
        was added to close, reopened by a sibling of the same base."""
        bystander = _bystander(writer)
        base = make_closure(shape="dataset-production")
        closure = replace(base, occurrence=replace(base.occurrence, actor=ACTOR))
        dataset = writer.add(
            stored.dataset_node(
                "produced", title="produced", resources=PINNED
            )
        )
        for entry in closure.recipe.inputs:
            writer.add(
                stored.dataset_node(
                    entry.dataset.removeprefix("dataset:"),
                    title="input",
                    resources=PINNED,
                    empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
                )
            )
        run = writer.add(
            stored.run_publication_node(
                closure.address(),
                title="production run",
                projection=runrecord.projection_text(closure).decode("utf-8"),
                spec=None,
                transforms=tuple(
                    e.dataset for e in closure.recipe.inputs if e.role == "transforms"
                ),
                reads=tuple(e.dataset for e in closure.recipe.inputs if e.role == "reads"),
                produces=(dataset.id,),
            )
        )
        proposition = writer.add(
            stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
        )
        node = stored.assessment_node(
            "a1",
            title="a1",
            spec="analysis-spec:s1",
            run=run.id,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule="rule:threshold",
        )
        raw_write(writer.root, stored.stamp_semantic_identity(node))
        writer._reconstruct()

        with pytest.raises(SignatureRefused):
            audit.check_assessment(writer.read_view, writer.read_view.get(node.id), evidence=NO_EVIDENCE)
        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("eligibility-unmet", node.id),
            ("derivation-malformed", node.id),
        }

    def test_a_basis_route_naming_a_non_string_run_is_malformed(self, writer):
        bystander = _bystander(writer)
        dataset = writer.add(stored.dataset_node("d", title="d", resources=PINNED))
        forged = dataset.model_copy(
            update={
                "facets": {
                    **dataset.facets,
                    stored.LINEAGE_BASIS_FACET: {
                        "tag": "single",
                        "routes": [{**_basis_route("a"), "run": ["run:a"]}],
                    },
                }
            }
        )
        raw_write(writer.root, stored.stamp_semantic_identity(forged))
        writer._reconstruct()

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("derivation-malformed", dataset.id),
        }


class TestOmegaValidIsMalformednessOnly:
    def test_a_record_flagged_only_for_display_is_still_recomputed(self, writer):
        """A malformed display facet is not malformedness in Ω_valid's sense —
        the stamp does not cover prose — so the forged basis is still read."""
        dataset = writer.add(stored.dataset_node("d", title="d", resources=PINNED))
        writer.add(_producing_run("a", dataset.id))
        writer.add(_producing_run("b", dataset.id))
        forged = dataset.model_copy(
            update={
                "facets": {
                    **dataset.facets,
                    stored.LINEAGE_BASIS_FACET: {"tag": "single", "routes": [_basis_route("a")]},
                }
            }
        )
        stored.stamp_semantic_identity(forged)
        forged.facets[stored.DISPLAY_FACET] = {"display_statement": ["not a string"]}
        raw_write(writer.root, forged)
        writer._reconstruct()

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {
            ("display-malformed", dataset.id),
            ("lineage-basis-contradicted", dataset.id),
        }


class TestVerificationRecomputation:
    """R19's audit arm at the value width. `check_verification` compares two
    members — the verdict and the assessment identity the original run's own
    derivation yields — and each has to be able to disagree on its own, or a
    silently *unchecked* outcome would read the same as an agreeing one."""

    @staticmethod
    def _node(writer, derived: AssessmentVerification, **overrides) -> Node:
        return writer.add(
            stored.verification_node(
                "v",
                title="v",
                assessment=overrides.get("assessment", derived.assessment),
                assessment_ref="assessment:a",
                scope=derived.scope,
                verdict=overrides.get("verdict", derived.verdict),
                derivation=(runrecord.run_ref(derived.original), runrecord.run_ref(derived.replayed)),
            )
        )

    def test_a_verification_derived_from_its_own_runs_is_checked_and_agrees(self, writer):
        evidence, derived = _replayed_pair(writer)
        assert derived.verdict == "passed"
        node = self._node(writer, derived)
        assert audit.check_verification(writer.read_view, node, evidence=evidence) == DerivationOutcome(
            True, "", None
        )
        assert audit_corpus(writer.read_view, evidence=evidence) == ()

    def test_a_failing_replay_is_equally_checked_and_agrees(self, writer):
        """The agreeing arm is not the passing arm: a stored `failed` over a
        replay that genuinely differs is derived, not contradicted."""
        evidence, derived = _replayed_pair(writer, agreeing=False)
        assert derived.verdict == "failed"
        node = self._node(writer, derived)
        assert audit.check_verification(writer.read_view, node, evidence=evidence) == DerivationOutcome(
            True, "", None
        )

    def test_a_forged_verdict_is_contradicted_and_names_both_verdicts(self, writer):
        evidence, derived = _replayed_pair(writer)
        node = self._node(writer, derived, verdict="failed")
        outcome = audit.check_verification(writer.read_view, node, evidence=evidence)
        assert outcome.checked and outcome.contradiction is not None
        assert outcome.contradiction.code == "verification-derivation-contradicted"
        assert outcome.contradiction.detail == "verdict stored='failed' recomputed='passed'"

    def test_a_forged_assessment_identity_is_contradicted_on_its_own(self, writer):
        """The verdict agrees; only the assessment identity is wrong. A stored
        verification pointing at an assessment the original run's derivation
        does not yield is a forgery the verdict comparison cannot see."""
        evidence, derived = _replayed_pair(writer)
        node = self._node(writer, derived, assessment="f" * 64)
        outcome = audit.check_verification(writer.read_view, node, evidence=evidence)
        assert outcome.checked and outcome.contradiction is not None
        assert (
            outcome.contradiction.detail
            == "assessment identity differs from the original run's derivation"
        )


class TestAssessmentComparisonNamespaces:
    """R22's comparison compares like with like. The derived value carries the
    spec's claim target and a bare closure address; the stored facet carries
    corpus refs. Comparing them whole would contradict on agreement."""

    def test_a_facet_derived_from_its_own_run_is_not_contradicted(self, writer):
        frozen, closure, _run = _derived_run(writer)
        evidence = _interpretation_evidence(frozen)
        derived = build_assessment(closure, specs=evidence.specs, implementations=evidence.implementations)
        assert isinstance(derived, AssessmentValue)
        proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        node = writer.add(
            stored.assessment_node(
                "a1",
                title="a1",
                spec=derived.spec,
                run=runrecord.run_ref(derived.run),
                proposition=proposition.id,
                outcome=derived.outcome,
                interpretation_rule=derived.interpretation_rule,
                **_stated_optionals(derived),
            )
        )
        assert audit.check_assessment(writer.read_view, node, evidence=evidence) == DerivationOutcome(True, "", None)
        assert audit_corpus(writer.read_view, evidence=evidence) == ()

    def test_a_facet_disagreeing_on_outcome_and_spec_names_both_members(self, writer):
        frozen, closure, _run = _derived_run(writer)
        evidence = _interpretation_evidence(frozen)
        derived = build_assessment(closure, specs=evidence.specs, implementations=evidence.implementations)
        assert isinstance(derived, AssessmentValue)
        proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        node = writer.add(
            stored.assessment_node(
                "a1",
                title="a1",
                spec="analysis-spec:forged",
                run=runrecord.run_ref(derived.run),
                proposition=proposition.id,
                outcome="refuted",
                interpretation_rule=derived.interpretation_rule,
                **_stated_optionals(derived),
            )
        )
        outcome = audit.check_assessment(writer.read_view, node, evidence=evidence)
        assert outcome.checked and outcome.contradiction is not None
        assert outcome.contradiction.code == "assessment-derivation-contradicted"
        assert outcome.contradiction.detail == "outcome,spec"


class TestAnEvaluatorOutsideTheClosedSet:
    def test_a_verdict_outside_VERDICTS_is_malformed_not_contradicted(self, writer):
        frozen, _closure, run = _derived_run(writer)
        verification = writer.add(
            stored.verification_node(
                "v",
                title="v",
                assessment="a" * 64,
                assessment_ref=run.id,
                scope="clean-environment",
                verdict="passed",
                derivation=(run.id, run.id),
            )
        )
        evidence = DerivationEvidence(
            specs={frozen.identity: frozen},
            held_rules={"impl-eq-1": EquivalenceImplementation("impl-eq-1", lambda a, b: "garbage", ())},
            implementations={},
        )
        with pytest.raises(MalformedRecord):
            audit.check_verification(writer.read_view, verification, evidence=evidence)

        findings = audit_corpus(writer.read_view, evidence=evidence)
        assert ("derivation-malformed", verification.id) in {(f.code, f.ref) for f in findings}


def _tampered_stale(writer, node: Node) -> Node:
    """Rewrite one node's governed facet without restamping, behind the write
    boundary: `corpus_check` classifies it `semantic-hash-stale`, and every
    `view.get` of it raises."""
    stale = node.model_copy(
        update={"facets": {**node.facets, stored.RUN_FACET: {"spec": "analysis-spec:tampered"}}}
    )
    raw_write(writer.root, stale)
    writer._reconstruct()
    return stale


class TestAnUnreadableNeighbourLeavesTheRecordUnchecked:
    """A neighbour whose own stamp is stale is `corpus_check`'s to classify,
    under its own ref. The record that reached it is neither convicted of its
    neighbour's fault nor allowed to abort the audit: it is unchecked, and the
    reason names the neighbour."""

    def test_a_stale_producing_run_leaves_the_dataset_unchecked(self, writer):
        dataset = writer.add(
            stored.dataset_node(
                "d",
                title="d",
                resources=PINNED,
                basis={"tag": "conflict", "routes": [_basis_route("a"), _basis_route("b")]},
            )
        )
        writer.add(_producing_run("a", dataset.id))
        run_b = writer.add(_producing_run("b", dataset.id))
        _tampered_stale(writer, run_b)

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {("semantic-hash-stale", run_b.id)}

        outcome = check_lineage_basis(writer.read_view, writer.read_view.get(dataset.id))
        assert not outcome.checked and run_b.id in outcome.reason and outcome.contradiction is None

    def test_a_verification_naming_a_stale_run_is_unchecked(self, writer):
        run = writer.add(stored.run_node("o", title="o", spec="analysis-spec:s1"))
        verification = writer.add(
            stored.verification_node(
                "v",
                title="v",
                assessment="a" * 64,
                assessment_ref=run.id,
                scope="clean-environment",
                verdict="passed",
                derivation=(run.id, run.id),
            )
        )
        _tampered_stale(writer, run)

        outcome = audit.check_verification(writer.read_view, verification, evidence=NO_EVIDENCE)
        assert not outcome.checked and run.id in outcome.reason and outcome.contradiction is None

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {("semantic-hash-stale", run.id)}

    def test_an_assessment_naming_a_stale_run_is_unchecked(self, writer):
        assessment = _eligible_assessment(writer)
        run = writer.read_view.get(stored.assessment_value(assessment).run)
        _tampered_stale(writer, run)

        outcome = audit.check_assessment(writer.read_view, assessment, evidence=NO_EVIDENCE)
        assert not outcome.checked and run.id in outcome.reason and outcome.contradiction is None

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert {(f.code, f.ref) for f in findings} == {("semantic-hash-stale", run.id)}
