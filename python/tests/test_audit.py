"""The corpus-local semantic audit (world-changing families §6.3, §7)."""

from __future__ import annotations

import pytest
from fixtures_cut4 import raw_write
from nodes.core.node import Node
from test_relocation import _writer
from test_relocation_rows import _basis_route

from beliefs import audit, belief, corpus, stored
from beliefs.audit import (
    NO_EVIDENCE,
    DerivationEvidence,
    DerivationOutcome,
    audit_corpus,
    check_lineage_basis,
)
from beliefs.errors import MalformedRecord

PINNED = [{"name": "matrix", "digest": "sha256:" + "1" * 64}]


@pytest.fixture()
def writer(tmp_path):
    return _writer(tmp_path / "corpus")


def _producing_run(slug: str, dataset_id: str) -> Node:
    """A minimal run node holding a `produces` edge to `dataset_id`."""
    return stored.run_node(slug, title=slug, spec="analysis-spec:s1", produces=[dataset_id])


def _eligible_assessment(writer) -> Node:
    """An assessment the write boundary admits, over a run carrying no closure
    projection: eligibility is a stored-edge predicate, and a decodable run
    closure is a separate fact that a hand-built run simply does not have."""
    dataset = writer.add(
        stored.dataset_node("raw", title="raw", resources=PINNED, empirical_observation={"boundary": "instrument"})
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
            actor="tester",
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


class TestLineageBasisRecomputation:
    def test_a_forged_single_is_contradicted_while_the_second_producer_stands(self, writer):
        """R23's audit clause: `single(A)` stamped, `B` also produces → finding;
        delete `B`'s run → the semantic finding disappears (§7)."""
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
