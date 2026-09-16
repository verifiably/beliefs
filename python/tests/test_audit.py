"""The corpus-local semantic audit (world-changing families §6.3, §7)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from authority import ACTOR
from closure_fixtures import make_closure
from dataset_fixtures import pinned, pinned_for
from fixtures_cut3 import TESTING_PROFILE, spec_draft, spec_rules, typed_applicability, typed_estimand
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from nodes.core.relations import Relation
from profiles import BASE, pins_for
from test_relocation import _writer
from test_relocation_rows import _basis_route
from test_stored import _testing_writer

from beliefs import audit, belief, corpus, runrecord, stored
from beliefs.assess import build_assessment
from beliefs.audit import (
    NO_EVIDENCE,
    DerivationEvidence,
    DerivationOutcome,
    audit_corpus,
    check_lineage_basis,
)
from beliefs.claim import Referent, build_claim
from beliefs.errors import MalformedRecord, SignatureRefused
from beliefs.projection import project_claim
from beliefs.recipe import ResultManifest, RunClosure
from beliefs.record import AssessmentValue
from beliefs.replay import CONTENT_EQUALITY, EquivalenceImplementation
from beliefs.spec import freeze
from beliefs.verify import AssessmentVerification, build_verification

PINNED = [{"name": "matrix", "digest": "sha256:" + "1" * 64}]
OTHER_CLAIM = build_claim(
    TESTING_PROFILE,
    operator="testing/affects",
    args=(Referent("testing/entity", "EX:gene-z"), Referent("testing/outcome", "EX:pheno-y")),
    layer="causal",
    polarity="positive",
)
"""A claim at `spec_draft`'s own operator but another entity — distinct from
`TESTING_CLAIM`, which `typed_estimand`'s default estimand answers, so a target
proposition storing this claim contradicts an unmodified `spec_draft()` spec
on claim identity alone (estimand-typing §7.2, Q6)."""


@pytest.fixture()
def writer(tmp_path):
    # `TESTING_PROFILE`, not BASE: every fixture assessment here carries a
    # typed estimand against `testing/affects`, which the recomputation
    # (`check_assessment`) decodes under the writer's own profile before it
    # ever reaches the run's closure (estimand-typing §6, §9).
    return _testing_writer(tmp_path / "corpus")


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
                                        title="raw",
                    resources=pinned_for(entry.dataset),
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


def _stated_optionals(derived: AssessmentValue) -> dict[str, Any]:
    """The typed members a derived value states, ready to forward into
    `stored.assessment_node`: `estimand`/`applicability` are always present;
    `estimate`/`uncertainty` stay absent when the derivation left them so —
    a stored `None` would be a different facet from an omitted one."""
    optional: dict[str, Any] = {"estimand": derived.estimand, "applicability": derived.applicability}
    if derived.estimate is not None:
        optional["estimate"] = derived.estimate
    if derived.uncertainty is not None:
        optional["uncertainty"] = derived.uncertainty
    return optional


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
        stored.dataset_node(title="raw", resources=PINNED, empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR})
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
            estimand=typed_estimand(),
            applicability=typed_applicability(),
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
        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
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
        audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert calls == []


class TestTheAuditMintsNothing:
    def test_audit_writes_no_file_and_appends_no_intent(self, writer):
        writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
        before = sorted(p for p in writer.root.rglob("*") if p.is_file())
        port = writer._operation_port
        audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert sorted(p for p in writer.root.rglob("*") if p.is_file()) == before
        assert port.intents == [] and port.fulfilling == []


def forged_single_over_two_producers(writer) -> Node:
    """A dataset two runs produce, carrying a raw-written `single(A)` basis —
    R23's forgery, which the API cannot spell (§11.11). Returns `B`'s run, the
    record whose deletion leaves nothing to contradict the forgery (§7).

    Module-level rather than inline: `test_deletion_rows.py` builds the same
    state for the cut-18 R23 row, and one construction serves both.
    """
    dataset = writer.add(stored.dataset_node(title="d", resources=PINNED))
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

        codes = [f.code for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)]
        assert codes == ["lineage-basis-contradicted"]

        writer.delete(run_b.id)
        assert [f.code for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)] == []

    def test_a_basis_naming_every_producer_is_not_contradicted(self, writer):
        dataset = writer.add(stored.dataset_node(title="d", resources=PINNED))
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
        assert audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile) == ()


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
        outcome = audit.check_assessment(writer.read_view, node, evidence=NO_EVIDENCE, profile=writer.profile)
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

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("derivation-malformed", node.id),
        }

    def test_a_verification_kind_node_carrying_no_verification_facet(self, writer):
        bystander = _bystander(writer)
        hollow = Node(id="verification:hollow", kind="verification", title="hollow", facets={}, relations=[])
        raw_write(writer.root, stored.stamp_semantic_identity(hollow))
        writer._reconstruct()

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("derivation-malformed", hollow.id),
            ("facet-missing", hollow.id),
        }

    def test_an_assessment_whose_stored_outcome_is_outside_the_closed_set(self, writer):
        bystander = _bystander(writer)
        dataset = writer.add(
            stored.dataset_node(title="raw", resources=PINNED, empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR})
        )
        run = writer.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[dataset.id]))
        proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        # `outcome="maybe"` is outside the closed set (M13's opacity): the
        # typed constructor refuses it at mint, so the malformed record is
        # written behind the boundary — self-consistent (restamped), never
        # constructor-refused — and only the audit's recomputation catches it.
        node = stored.assessment_node(
            "a1",
            title="a1",
            spec="analysis-spec:s1",
            run=run.id,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule="rule:threshold",
            estimand=typed_estimand(),
            applicability=typed_applicability(),
        )
        node.facets[stored.ASSESSMENT_FACET]["outcome"] = "maybe"
        raw_write(writer.root, stored.stamp_semantic_identity(node))
        writer._reconstruct()

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
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
            stored.dataset_node(title="produced", resources=pinned("produced")
            )
        )
        for entry in closure.recipe.inputs:
            writer.add(
                stored.dataset_node(
                                        title="input",
                    resources=pinned_for(entry.dataset),
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
            estimand=typed_estimand(),
            applicability=typed_applicability(),
        )
        raw_write(writer.root, stored.stamp_semantic_identity(node))
        writer._reconstruct()

        with pytest.raises(SignatureRefused):
            audit.check_assessment(writer.read_view, writer.read_view.get(node.id), evidence=NO_EVIDENCE, profile=writer.profile)
        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("eligibility-unmet", node.id),
            ("derivation-malformed", node.id),
        }

    def test_a_basis_route_naming_a_non_string_run_is_malformed(self, writer):
        bystander = _bystander(writer)
        dataset = writer.add(stored.dataset_node(title="d", resources=PINNED))
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

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert {(f.code, f.ref) for f in findings} == {
            ("semantic-hash-missing", bystander),
            ("derivation-malformed", dataset.id),
        }


class TestOmegaValidIsMalformednessOnly:
    def test_a_record_flagged_only_for_display_is_still_recomputed(self, writer):
        """A malformed display facet is not malformedness in Ω_valid's sense —
        the stamp does not cover prose — so the forged basis is still read."""
        dataset = writer.add(stored.dataset_node(title="d", resources=PINNED))
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

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
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
        assert audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile) == ()

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
        assert audit.check_assessment(writer.read_view, node, evidence=evidence, profile=writer.profile) == DerivationOutcome(True, "", None)
        assert audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile) == ()

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
        outcome = audit.check_assessment(writer.read_view, node, evidence=evidence, profile=writer.profile)
        assert outcome.checked and outcome.contradiction is not None
        assert outcome.contradiction.code == "assessment-derivation-contradicted"
        assert outcome.contradiction.detail == "outcome,spec"


def test_a_well_formed_assessment_is_admitted_by_audit_and_by_import(writer, tmp_path):
    """The regression `profile` becoming a required keyword on `check_assessment`
    guards against (estimand-typing §7.2, Task 8): without it threaded through
    both `audit_corpus` and `import_bundle`'s recomputation, either would reach
    `stored.assessment_value` with no profile and fail with an uncaught
    `TypeError` before any derivation check runs — never a `RecordError` the
    audit's exception boundary catches."""
    frozen, closure, run = _derived_run(writer)
    evidence = _interpretation_evidence(frozen)
    derived = build_assessment(closure, specs=evidence.specs, implementations=evidence.implementations)
    assert isinstance(derived, AssessmentValue)
    proposition = writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    assessment = writer.add(
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
    assert audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile) == ()

    target = _testing_writer(tmp_path / "target")
    datasets = [writer.read_view.get(e.dataset) for e in closure.recipe.inputs if e.role == "observes"]
    target.import_bundle(
        [*datasets, run, proposition, assessment],
        evidence=evidence,
        observer="o",
        instrument="i",
        opened_at="2026-09-15T00:00:00Z",
        closed_at="2026-09-15T00:00:01Z",
    )
    assert target.read_view.holds(assessment.id)
    recomputed = audit.check_assessment(target.read_view, target.read_view.get(assessment.id), evidence=evidence, profile=target.profile)
    assert recomputed == DerivationOutcome(True, "", None)


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

        findings = audit_corpus(writer.read_view, evidence=evidence, profile=writer.profile)
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
                                title="d",
                resources=PINNED,
                basis={"tag": "conflict", "routes": [_basis_route("a"), _basis_route("b")]},
            )
        )
        writer.add(_producing_run("a", dataset.id))
        run_b = writer.add(_producing_run("b", dataset.id))
        _tampered_stale(writer, run_b)

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
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

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert {(f.code, f.ref) for f in findings} == {("semantic-hash-stale", run.id)}

    def test_an_assessment_naming_a_stale_run_is_unchecked(self, writer):
        assessment = _eligible_assessment(writer)
        run = writer.read_view.get(stored.typed_ref("run", stored.assessment_reference(assessment).run))
        _tampered_stale(writer, run)

        outcome = audit.check_assessment(writer.read_view, assessment, evidence=NO_EVIDENCE, profile=writer.profile)
        assert not outcome.checked and run.id in outcome.reason and outcome.contradiction is None

        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
        assert {(f.code, f.ref) for f in findings} == {("semantic-hash-stale", run.id)}


@pytest.mark.parametrize("manifest", ["base", "malformed", "symlink"])
def test_the_audit_stops_on_a_base_mismatch_without_recomputing(tmp_path, monkeypatch, manifest):
    writer = _writer(tmp_path / manifest)
    from nodes.core.corpus import Corpus

    from beliefs.corpus import ReadView
    writer.add(stored.dataset_node(title="d", resources=PINNED))
    monkeypatch.setattr(audit, "check_lineage_basis", lambda *args: pytest.fail("recomputed under unknown pins"))
    path = writer.root / "corpus.yaml"
    if manifest == "base":
        path.write_text(path.read_text().replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
    elif manifest == "malformed":
        path.write_text("manifest_version: 3\n")
    else:
        path.unlink()
        path.symlink_to("missing.yaml")
    expected = ["profile-mismatch"] if manifest == "base" else ["manifest-malformed", "profile-mismatch"]
    assert [f.code for f in audit_corpus(ReadView(Corpus(writer.root)), evidence=NO_EVIDENCE, profile=BASE)] == expected


@pytest.mark.parametrize("declaration", ["malformed", "bearer", "retrieval"])
def test_declaration_malformedness_alone_withholds_audit_recomputation(writer, declaration, monkeypatch):
    checked = []
    original = audit.check_lineage_basis

    def recompute(view, node):
        checked.append(node.id)
        return original(view, node)

    monkeypatch.setattr(audit, "check_lineage_basis", recompute)
    dataset = stored.dataset_node(title="d", resources=PINNED,
        empirical_observation={"boundary": "x"} if declaration == "malformed" else
        {"locator": "instrument:fixture", "attested_by": ACTOR,
         **({"retrieval": "act-report:gone"} if declaration == "retrieval" else {})})
    # A missing producing route is a real contradiction if recomputation runs.
    dataset.facets[stored.LINEAGE_BASIS_FACET] = {"tag": "single", "routes": [_basis_route("a")]}
    raw_write(writer.root, stored.stamp_semantic_identity(dataset))
    if declaration == "retrieval":
        # Retrieval validity is independent of whether the dataset has a basis.
        del dataset.facets[stored.LINEAGE_BASIS_FACET]
        raw_write(writer.root, stored.stamp_semantic_identity(dataset))
    else:
        raw_write(writer.root, _producing_run("b", dataset.id))
    writer._reconstruct()
    findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE, profile=writer.profile)
    codes = {f.code for f in findings}
    assert checked == ([] if declaration == "malformed" else [dataset.id])
    if declaration == "malformed":
        assert "facet-payload-malformed" in codes and "lineage-basis-contradicted" not in codes
    elif declaration == "bearer":
        assert codes == {"facet-bearer-produced", "lineage-basis-contradicted"}
    else:
        assert codes == {"facet-retrieval-unresolved"}


# --- V4 / V6 / V2: scope, rule, scope rule and report are recomputed (design §6) ---
from verification_fixtures import publish_corpus, self_consistent_forgery

from beliefs.audit import check_verification
from beliefs.replay import CodeLineageCertification

CERTIFIED = CodeLineageCertification(rationale="independent reimplementation", attribution="second team")
DERIVATION_CODES = {"verification-derivation-contradicted", "assessment-derivation-contradicted", "derivation-malformed"}


def _findings(writer, evidence, code="verification-derivation-contradicted"):
    return [f for f in audit_corpus(reopen(writer.root), evidence=evidence, profile=writer.profile) if f.code == code]


def test_v4_a_published_verification_audits_checked_with_no_contradiction(writer):
    published = publish_corpus(writer, publish=True)
    assert published.node is not None
    outcome = check_verification(writer.read_view, writer.read_view.get(published.node.id), evidence=published.evidence)
    assert outcome.checked and outcome.contradiction is None
    assert not {f.code for f in audit_corpus(reopen(writer.root), evidence=published.evidence, profile=writer.profile)} & DERIVATION_CODES


def test_v4_a_certified_verification_audits_clean_through_its_stored_certification(writer):
    """The recomputation takes the certification from the stored report (decision 7): drop it and the report identity moves. [R10]"""
    published = publish_corpus(writer, publish=True, certification=CERTIFIED)
    assert published.derived.report.certification == CERTIFIED
    assert not _findings(writer, published.evidence)


# (member named in the finding, the mutation, the corpus it is forged over). The
# scope case is the frozen cell's escalation: `clean-environment` asserted over a
# replay that does not qualify, so the honest derivation is `same-environment`.
V4_FORGERIES = [
    ("scope", lambda f: f.__setitem__("scope", "clean-environment"), {"qualifying": False}),
    ("verdict", lambda f: f.__setitem__("verdict", "failed"), {}),
    ("report", lambda f: f["report"].__setitem__("receipts", ["sha256:" + "0" * 64, f["report"]["receipts"][1]]), {}),
    ("report", lambda f: f["report"].__setitem__("original_conformance", "non-conforming: forged"), {}),
    ("rule", lambda f: f.__setitem__("rule", "some-other-rule/v1"), {}),
    ("scope_rule", lambda f: f.__setitem__("scope_rule", "scope-derivation/v9"), {}),
]
V4_IDS = ["scope", "verdict", "report-receipt", "report-conformance", "rule", "scope_rule"]


@pytest.mark.parametrize("member, mutate, corpus", V4_FORGERIES, ids=V4_IDS)
def test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member(writer, member, mutate, corpus):
    published = publish_corpus(writer, publish=True, **corpus)
    assert published.node is not None
    if member == "scope":
        assert published.derived.scope == "same-environment"  # the honest reading the forgery escalates
    forged = self_consistent_forgery(writer, published.node, mutate=mutate)
    findings = _findings(writer, published.evidence)
    assert [f.ref for f in findings] == [forged.id] and member in findings[0].detail
    assert not _findings(writer, published.evidence, code="derivation-malformed")


def test_v6_a_report_less_verification_is_checked_for_verdict_and_identity_only(writer):
    published = publish_corpus(writer, publish=True)
    assert published.node is not None
    facet = dict(published.node.facets[stored.VERIFICATION_FACET])
    del facet["report"], facet["rule"], facet["scope_rule"]
    facet["scope"] = "same-environment"  # a lowered scope a report-less record cannot be caught on (cut 18 §7)
    legacy = stored.stamp_semantic_identity(
        Node(id="verification:legacy", kind="verification", title="legacy", facets={stored.VERIFICATION_FACET: facet}, relations=[])
    )
    raw_write(writer.root, legacy)
    view = reopen(writer.root)
    outcome = check_verification(view, view.get(legacy.id), evidence=published.evidence)
    assert outcome.checked and outcome.contradiction is None
    facet["verdict"] = "failed"
    flipped = stored.stamp_semantic_identity(
        Node(id="verification:legacy-flipped", kind="verification", title="legacy", facets={stored.VERIFICATION_FACET: facet}, relations=[])
    )
    raw_write(writer.root, flipped)
    view = reopen(writer.root)
    outcome = check_verification(view, view.get(flipped.id), evidence=published.evidence)
    assert outcome.contradiction is not None and "verdict" in outcome.contradiction.detail


def test_v2_a_contradicted_assessment_still_contradicts(writer, tmp_path):
    """Decision 13: the assessment audit resolves the bare run through the typed ref."""
    published = publish_corpus(writer, publish=True)
    altered = published.assessment.model_copy(deep=True)
    altered.facets[stored.ASSESSMENT_FACET]["outcome"] = "refuted"
    stored.stamp_semantic_identity(altered)
    raw_write(writer.root, altered)
    codes = {f.code for f in audit_corpus(reopen(writer.root), evidence=published.evidence, profile=writer.profile)}
    assert "assessment-derivation-contradicted" in codes and "semantic-hash-stale" not in codes
    from test_relocation import _writer

    from beliefs.errors import ImportRefused

    target = _writer(tmp_path / "target")
    members = tuple(n for n in reopen(writer.root).iter_stored() if n.kind in {"dataset", "run", "proposition"}) + (altered,)
    with pytest.raises(ImportRefused):
        target.import_bundle(members, evidence=published.evidence, observer="o", instrument="i", opened_at="2026-09-06T00:00:00Z", closed_at="2026-09-06T00:00:01Z")


# --- V8: no spec disappears silently (design decision 15) --------------------
from beliefs.audit import check_analysis_spec, stored_specs


def _false_spec_record(spec):
    forged = stored.analysis_spec_node(spec).model_copy(update={"id": "analysis-spec:forged"})
    forged.facets[stored.ANALYSIS_SPEC_FACET]["identity"] = "forged"
    forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"] = forged.facets[stored.ANALYSIS_SPEC_FACET]["projection"].replace("fit the model", "fit another model")
    return stored.stamp_semantic_identity(forged)


def test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it(tmp_path):
    # A writer of its own on `TESTING_PROFILE`, built the same way the shared
    # `writer` fixture above is (estimand-typing Task 7 moved that fixture off
    # BASE too, for the same reason): `spec_draft()`'s typed estimand is
    # against `testing/affects`, which BASE does not declare, and restoration
    # reads the profile that wrote it.
    from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE
    from test_stored import _testing_writer

    writer = _testing_writer(tmp_path / "corpus")
    # The boundary now refuses a spec whose target does not resolve to a
    # proposition its own estimand answers (estimand-typing §7.2, Task 8), so
    # `spec_draft`'s default `target` must name a real, matching proposition.
    target = writer.add(stored.proposition_node("p", title="p", claim=project_claim(TESTING_CLAIM)))
    spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())
    good = writer.add(stored.analysis_spec_node(spec))
    forged = _false_spec_record(spec)
    raw_write(writer.root, forged)
    view = reopen(writer.root)
    assert check_analysis_spec(view.get(good.id), profile=TESTING_PROFILE).checked
    with pytest.raises(MalformedRecord):
        check_analysis_spec(view.get(forged.id), profile=TESTING_PROFILE)
    specs, findings = stored_specs(view, profile=TESTING_PROFILE)
    assert set(specs) == {spec.identity} and [f.ref for f in findings] == [forged.id] and findings[0].code == "derivation-malformed"
    assert [f.ref for f in audit_corpus(view, evidence=NO_EVIDENCE, profile=TESTING_PROFILE) if f.code == "derivation-malformed"] == [forged.id]


def test_v4_the_audit_reaches_the_same_verdict_with_specs_restored_from_the_corpus(writer):
    from fixtures_cut3 import TESTING_CLAIM

    # The stored spec's estimand is `spec_draft`'s default, built against
    # `TESTING_CLAIM` (`frozen_for`, via `typed_estimand`); the boundary now
    # requires the target proposition's own claim to agree (estimand-typing
    # §7.2, Task 8), so the proposition is minted with that same claim rather
    # than `publish_corpus`'s bare `{"operator": "affects"}` default.
    published = publish_corpus(writer, publish=True, claim=project_claim(TESTING_CLAIM))
    assert published.node is not None
    writer.add(stored.analysis_spec_node(published.frozen))
    specs, findings = stored_specs(writer.read_view, profile=writer.profile)
    assert not findings and set(specs) == {published.frozen.identity}
    from dataclasses import replace

    from_corpus = replace(published.evidence, specs=specs)
    outcome = check_verification(writer.read_view, writer.read_view.get(published.node.id), evidence=from_corpus)
    assert outcome.checked and outcome.contradiction is None


# --- Task 8: the boundary and the audit (estimand-typing §7.2, decision 10) --


def test_a_raw_written_mismatching_spec_is_caught_only_under_audit(writer):
    """§7.3c's shape: a raw write bypasses the boundary entirely, so the
    mismatch is admitted at read and caught only by the audit's own
    recomputation (`check_spec_target`), never by a reader that coerces."""
    target = writer.add(stored.proposition_node("p-other", title="other", claim=project_claim(OTHER_CLAIM)))
    spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())
    node = stored.analysis_spec_node(spec)
    raw_write(writer.root, node)
    assert reopen(writer.root).get(node.id).id == node.id  # not refused on read
    findings = audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE)
    assert [f.code for f in findings if f.ref == node.id] == ["spec-target-contradicted"]


def test_pre_grammar_records_audit_under_their_own_codes(writer):
    """Decision 10: a pre-grammar spec or assessment is named by its own code,
    never folded into `derivation-malformed` (Task 6's reviewer note)."""
    from beliefs.identity import v1

    spec_node = stored._node(
        "analysis-spec", "old", "old",
        {stored.ANALYSIS_SPEC_FACET: {"identity": "old", "projection": v1.encode({
            "target": "proposition:p", "estimand": "prose", "method": "m", "assumptions": "a",
            "falsification": "f", "input_roles": [], "applicability": "prose",
            "interpretation_rule": "r", "equivalence_rule": "e", "parameters": {},
            "nondeterminism": {"variant": "deterministic"}, "rule_bindings": [],
        }).decode()}},
        (),
    )
    assessment_node = stored._node(
        "assessment", "old", "old",
        {stored.ASSESSMENT_FACET: {
            "spec": "old", "run": "run:x", "proposition": "proposition:p",
            "outcome": "supported", "interpretation_rule": "r", "estimand": "prose",
        }},
        (),
    )
    raw_write(writer.root, stored.stamp_semantic_identity(spec_node))
    raw_write(writer.root, stored.stamp_semantic_identity(assessment_node))
    codes = {f.ref: f.code for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE)}
    assert codes[spec_node.id] == "spec-pre-grammar" and codes[assessment_node.id] == "assessment-pre-grammar"
    assert "derivation-malformed" not in codes.values()


def test_the_inconsistent_stored_pair_decodes_cleanly_refuses_at_import_and_contradicts_on_operator_alone(writer, tmp_path):
    """Q6's stored-pair arm, run through the seams the write-time refusal
    (`test_corpus_write.py::TestEstimandTargetMatch::
    test_the_inconsistent_stored_pair_is_caught_by_operator_equality`) never
    reaches: raw-written, so `_refuse` never sees it. Comparing identities
    only must let it through — the record decodes cleanly, unlike the
    same-operator arm above (`test_a_raw_written_mismatching_spec_is_caught_only_under_audit`,
    which differs by referent, not by operator, so the claim disagreement
    alone already fires and the operator equality is never what's tested).
    Here the operator disagreement is the only one — the target's true claim
    hash sits beside a different declared operator — and it alone is what
    explicit import refuses (through `_ImportView`, review finding 2) and the
    audit contradicts (review finding 1)."""
    from decimal import Decimal

    from fixtures_cut3 import TESTING_CLAIM, UNCONSULTED

    from beliefs.claim import Referent, build_claim
    from beliefs.errors import ImportRefused
    from beliefs.estimand import ContinuousContrast, Control, Measure, build_estimand
    from beliefs.identity import v1
    from beliefs.projection import claim_identity
    from beliefs.spec import SPEC_DOMAIN, frozen_projection

    target = writer.add(stored.proposition_node("p-target", title="p-target", claim=project_claim(TESTING_CLAIM)))
    correlates = build_claim(
        TESTING_PROFILE, operator="testing/correlates-with",
        args=(Referent("testing/entity", "EX:gene-x"), Referent("testing/outcome", "EX:pheno-y")),
        layer="statistical", polarity="positive",
    )
    foreign, _ = build_estimand(
        TESTING_PROFILE, correlates, snapshot=UNCONSULTED,
        contrast=ContinuousContrast(0, Referent("testing/measure", "EX:tpm"), Decimal(1)),
        measure=Measure(Referent("testing/measure", "EX:tpm"), "additive"), reference=Decimal(0),
        control=Control(Referent("testing/identification", "EX:observational"), ()),
    )  # correlates-with declares level_sorts {}, so the contrast is continuous, not levels
    spec = freeze(spec_draft(target=target.id, estimand=foreign), held_rules=spec_rules())
    projection = frozen_projection(spec)
    projection["estimand"]["claim"] = claim_identity(TESTING_CLAIM)  # type: ignore[index]  # the target's true hash, another operator
    text = v1.encode(projection)
    identity = v1.digest(SPEC_DOMAIN, projection)
    node = stored._node(
        "analysis-spec", identity, "forged",
        {stored.ANALYSIS_SPEC_FACET: {"identity": identity, "projection": text.decode()}}, (),
    )
    raw_write(writer.root, node)

    # decodes cleanly: identities only, no cross-check at restore (decision 10 / §7.2).
    restored = stored.analysis_spec_value(reopen(writer.root).get(node.id), profile=TESTING_PROFILE)
    assert restored.estimand.claim == claim_identity(TESTING_CLAIM)
    assert restored.estimand.operator == "testing/correlates-with"

    # explicit import refuses, never repairs — through _ImportView, not the live corpus's ReadView.
    target_writer = _testing_writer(tmp_path / "target")
    target_writer.add(stored.proposition_node("p-target", title="p-target", claim=project_claim(TESTING_CLAIM)))
    with pytest.raises(ImportRefused, match="estimand-target-mismatch"):
        target_writer.import_bundle(
            [node], observer="o", instrument="i",
            opened_at="2026-09-15T00:00:00Z", closed_at="2026-09-15T00:00:01Z",
        )

    # the audit contradicts on the operator equality alone — the claim agrees.
    findings = audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE)
    [finding] = [f for f in findings if f.ref == node.id]
    assert finding.code == "spec-target-contradicted"
    assert finding.detail == "operator"


def test_explicit_import_refuses_a_spec_whose_target_does_not_resolve_in_the_union(tmp_path):
    """The `_ImportView` branch of the boundary check (Task 8 review finding
    2), the unresolvable arm: a spec whose target resolves nowhere in the
    base corpus nor the bundle is refused at import, never admitted
    unchecked."""
    from beliefs.errors import ImportRefused

    target_writer = _testing_writer(tmp_path / "target")
    spec = freeze(spec_draft(target="proposition:elsewhere"), held_rules=spec_rules())
    node = stored.analysis_spec_node(spec)
    with pytest.raises(ImportRefused, match="estimand-target-unresolvable"):
        target_writer.import_bundle(
            [node], observer="o", instrument="i",
            opened_at="2026-09-15T00:00:00Z", closed_at="2026-09-15T00:00:01Z",
        )


# --- U7: composites and cross-kind succession under audit -------------------
from test_composite_boundary import _build, _claim, _proposition
from test_composite_boundary import _writer as _composite_writer

from beliefs.audit import check_composite, check_supersedes_kinds


def _composite_corpus(tmp_path):
    w = _composite_writer(tmp_path / "corpus")
    _proposition(w, "ab", _claim("EX:a", "EX:b"))
    _proposition(w, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"]), title="g"))
    return w, minted


def _codes(writer):
    return sorted((f.code, f.ref) for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile))


def test_a_well_formed_composite_audits_clean(tmp_path):
    writer, _ = _composite_corpus(tmp_path)
    assert _codes(writer) == []


def test_a_deleted_member_is_an_unresolvable_contradiction_and_the_record_stays_read(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    writer.delete("proposition:bc")
    codes = _codes(writer)
    assert ("composite-member-unresolvable", minted.id) in codes
    assert not any(code in audit.MALFORMEDNESS_CODES for code, _ in codes)


def test_a_raw_edited_member_claim_is_a_mismatch(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get("proposition:bc")
    node.facets[stored.PROPOSITION_FACET]["polarity"] = "positive"
    stored.stamp_semantic_identity(node)
    raw_write(writer.root, node)
    assert ("composite-member-mismatch", minted.id) in _codes(writer)


def test_a_relation_set_that_disagrees_with_the_facet_is_reported(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get(minted.id)
    node.relations.pop()
    raw_write(writer.root, node)  # the stamp covers the facet, not the relations, so the record is well formed
    assert ("composite-relations-mismatch", minted.id) in _codes(writer)


def test_a_composite_that_no_longer_classifies_is_malformed_not_silently_kept(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get(minted.id)
    node.facets[stored.COMPOSITE_FACET]["nodes"] = [{"sort": "biology/gene", "term": "EX:a"}, {"sort": "biology/gene", "term": "EX:b"}]  # drops c
    stored.stamp_semantic_identity(node)
    raw_write(writer.root, node)
    findings = {f.code: f for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile)}
    assert "composite-malformed" in findings and "composite-member-outside-nodes" in findings["composite-malformed"].detail


def test_a_raw_written_cross_kind_supersedes_edge_is_reported_on_any_record(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get("proposition:ab")
    node.relations.append(Relation(source=node.id, predicate=stored.SUPERSEDES, target=minted.id))
    raw_write(writer.root, node)
    assert ("supersedes-cross-kind", "proposition:ab") in _codes(writer)
    assert check_supersedes_kinds(reopen(writer.root), reopen(writer.root).get("proposition:ab"), profile=writer.profile) is not None


def test_a_successor_that_retires_the_edge_row_makes_the_composite_malformed(tmp_path):
    import copy

    from profiles import FIXTURE, biology

    from beliefs.contract import parse_domain_contract
    from beliefs.contract.document import load_document
    from beliefs.profile import compile_profile, shipped_base_contract

    writer, minted = _composite_corpus(tmp_path)
    document = load_document(FIXTURE, source=str(FIXTURE))
    assert isinstance(document, dict)
    successor = copy.deepcopy(document)
    successor["description"] = "fixture"
    successor["lineage"] = {"successor": biology("fixture").content_identity}
    successor["edges"]["affects"]["retired"] = True
    retired = compile_profile(shipped_base_contract(), [parse_domain_contract(successor, source="<r>", base=shipped_base_contract(), predecessor=biology("fixture"))])
    # `check_composite` directly: the corpus pins the predecessor, and this arm is about classification under the successor, not about pins.
    outcome = check_composite(reopen(writer.root), reopen(writer.root).get(minted.id), profile=retired)
    assert outcome.contradiction is not None and outcome.contradiction.code == "composite-malformed"
    assert "composite-member-retired" in outcome.contradiction.detail


def test_check_composite_reads_form_only_and_never_a_snapshot(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    outcome = check_composite(reopen(writer.root), reopen(writer.root).get(minted.id), profile=writer.profile)
    assert outcome.checked and outcome.contradiction is None
