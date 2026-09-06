"""R19 and R22 over the durable store: what a read does, and what it does not.

Both rows are about the **read side**. Cut 3 could state them only over value
sets; here a record lands at an address and reloads, so *"not refused"* and
*"the reader said nothing"* are assertions about a read that runs.

**Heldness stays exactly what cut 3 made it** — a value a fixture supplies.
Nothing is mounted, nothing is acquired, and no managed deletion runs: making
artifacts unreachable *here* while a copy remains held elsewhere is a statement
about the observations supplied to the call, which is the only place this slice
represents heldness at all.
"""

from __future__ import annotations

import pytest
from authority import ACTOR
from durable_fixture import PROPOSITION, RULE, SPEC
from fixtures_cut3 import D_OUT, recipe, spec_draft, spec_rules
from fixtures_cut3 import closure as run_closure
from fixtures_cut4 import raw_write, reopen

from beliefs import stored
from beliefs.admission import admit
from beliefs.closure import RetractionEnumeration, build_closure
from beliefs.corpus import corpus_check, lineage_snapshot, run_value
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.lineage import LineageSnapshot
from beliefs.replay import byte_tolerance_rule
from beliefs.spec import freeze
from beliefs.verify import build_verification

OBSERVED_DIGEST = "sha256:" + "1a" * 32
ASSESSMENT = "assessment:a1"
RUN = "run:r1"
RAW = "dataset:raw"


# --- the pieces both rows read the store through ------------------------------


def assessments_of(view):
    return tuple(
        stored.assessment_value(node) for node in view.iter_stored() if node.kind == "assessment"
    )


def verifications_of(view):
    return tuple(
        stored.verification_value(node) for node in view.iter_stored() if node.kind == "verification"
    )


def belief_digest(view, proposition: str = PROPOSITION) -> str:
    """The belief input closure's digest, taken over the reloaded store.

    The producer snapshot, the retraction enumeration, the consulted pairs and
    the policy binding are **supplied**, exactly as cut 3's selected arms had
    them: the closure digests them, and nothing here computes them.
    """
    assessments = assessments_of(view)
    runs = {value.run: run_value(view, value.run) for value in assessments if view.holds(value.run)}
    return build_closure(
        proposition=proposition,
        assessments=assessments,
        runs=runs,
        verifications=verifications_of(view),
        snapshot=lineage_snapshot(view, []),
        producer_snapshot_identity="producer-snapshot-1",
        retractions=RetractionEnumeration(found=(), coverage=("supplied",)),
        consulted=(("science", "base-1"),),
        binding=("science.belief.v1", "impl-1"),
    ).digest()


def observed_dataset():
    return stored.dataset_node(
        "raw",
        title="raw",
        resources=[{"name": "matrix", "digest": OBSERVED_DIGEST}],
        empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
    )


def mint_assessment(writer, *, outcome: str, slug_name: str = "a1"):
    return writer.add(
        stored.assessment_node(
            slug_name,
            title=slug_name,
            spec=SPEC,
            run=RUN,
            proposition=PROPOSITION,
            outcome=outcome,
            interpretation_rule=RULE,
        )
    )


def mint_run_and_proposition(writer):
    writer.add(observed_dataset())
    writer.add(stored.run_node("r1", title="r1", spec=SPEC, observes=[RAW]))
    writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))


def passed_verification_under_a_tolerance():
    """A `passed` verification built by the constructor cut 3 selected, with a
    **declared tolerance** as the held equivalence implementation.

    Its scope is whatever the boundary policy derives, and `clean-environment`
    is no more reachable here than it was in cut 3 — confinement is the
    boundary-policy work this slice does not build. What the constructor
    supplies, and what this arm needs, is the verdict and the rule.
    """
    spec = freeze(spec_draft(), held_rules=spec_rules())
    bindings = (("content-identity-equality/v1", "impl-tolerance-1e-6"), ("median-difference/v1", "impl-interp-1"))
    original = run_closure(recipe=recipe(spec_identity=spec.identity, rule_bindings=bindings))
    replayed = run_closure(recipe=recipe(spec_identity=spec.identity, rule_bindings=bindings))
    return build_verification(
        original,
        replayed,
        specs={spec.identity: spec},
        held_rules={"impl-tolerance-1e-6": byte_tolerance_rule({D_OUT: b"1.0"})},
        contract_identity="contract-1",
        epoch="epoch-1",
    )


class TestR19aTheGenuineAvailabilityTransition:
    """Record a `passed` verification under a declared tolerance, mint it
    durably, then make its artifacts unreachable **here** while they remain held
    elsewhere: it is not refused, admission is unchanged, and no `inconclusive`
    is recorded."""

    @pytest.fixture()
    def stored_verification(self, durable_writer, durable_root):
        mint_run_and_proposition(durable_writer)
        assessment = stored.assessment_value(mint_assessment(durable_writer, outcome="supported"))
        built = passed_verification_under_a_tolerance()
        durable_writer.add(
            stored.verification_node(
                "v1",
                title="v1",
                assessment=assessment.identity(),
                assessment_ref=ASSESSMENT,
                scope=built.scope,
                verdict=built.verdict,
            )
        )
        return built

    @staticmethod
    def admission(view, *, reachable_here: bool):
        """Heldness is supplied. `reachable_here` changes only where the bytes
        are reported to live — the observation itself stands, because a copy
        remains held elsewhere."""
        assessment = stored.assessment_value(view.get(ASSESSMENT))
        run = run_value(view, RUN)
        location = "local-mount" if reachable_here else "host-b"
        address = dataset_address(stored.dataset_declaration(view.get(RAW)))
        assert address is not None  # the fixture pins the dataset, so it has one
        observations = {address: (ByteObservation(digest=OBSERVED_DIGEST, location=location),)}
        return admit(assessment, run, observations, verifications_of(view))

    def test_the_verification_is_passed_under_the_declared_tolerance(self, stored_verification):
        assert stored_verification.verdict == "passed"
        assert stored_verification.rule == "content-identity-equality/v1"

    def test_the_record_reloads_and_is_not_refused(self, stored_verification, durable_root):
        value = stored.verification_value(reopen(durable_root).get("verification:v1"))
        assert (value.verdict, value.scope) == (stored_verification.verdict, stored_verification.scope)

    def test_admission_is_unchanged_when_the_artifacts_are_unreachable_here(
        self, stored_verification, durable_root
    ):
        view = reopen(durable_root)
        before = self.admission(view, reachable_here=True)
        after = self.admission(reopen(durable_root), reachable_here=False)
        assert before == after

    def test_unavailability_never_reaches_admission_as_a_heldness_answer(
        self, stored_verification, durable_root
    ):
        outcome = self.admission(reopen(durable_root), reachable_here=False)
        assert "input-not-held" not in getattr(outcome, "reason", "")

    def test_no_inconclusive_is_recorded_anywhere_in_the_store(self, stored_verification, durable_root):
        assert [value.verdict for value in verifications_of(reopen(durable_root))] == ["passed"]

    def test_reading_the_record_validates_nothing(self, stored_verification, durable_root):
        # The read returns the stored fields; it does not re-run the comparison,
        # so there is nothing for unavailability to turn into a verdict.
        view = reopen(durable_root)
        assert stored.verification_value(view.get("verification:v1")).verdict == "passed"
        assert corpus_check(view) == ()


class TestR19deTheReadSideNegatives:
    def test_a_self_consistent_forged_verification_is_not_refused(self, durable_writer, durable_root):
        mint_run_and_proposition(durable_writer)
        assessment = stored.assessment_value(mint_assessment(durable_writer, outcome="supported"))
        raw_write(
            durable_root,
            stored.verification_node(
                "forged",
                title="forged",
                assessment=assessment.identity(),
                assessment_ref=ASSESSMENT,
                scope="clean-environment",
                verdict="passed",
            ),
        )
        view = reopen(durable_root)
        assert stored.verification_value(view.get("verification:forged")).verdict == "passed"

    def test_reload_does_not_validate_it(self, durable_writer, durable_root):
        mint_run_and_proposition(durable_writer)
        assessment = stored.assessment_value(mint_assessment(durable_writer, outcome="supported"))
        raw_write(
            durable_root,
            stored.verification_node(
                "forged",
                title="forged",
                assessment=assessment.identity(),
                assessment_ref=ASSESSMENT,
                scope="clean-environment",
                verdict="passed",
            ),
        )
        assert corpus_check(reopen(durable_root)) == ()

    def test_a_self_consistent_raw_written_run_is_not_detected(self, durable_writer, durable_root):
        mint_run_and_proposition(durable_writer)
        raw_write(durable_root, stored.run_node("smuggled", title="smuggled", spec=SPEC, observes=[RAW]))
        view = reopen(durable_root)
        assert view.holds("run:smuggled")
        assert corpus_check(view) == ()

    def test_an_unaudited_verification_is_indistinguishable_from_a_genuine_one(
        self, durable_writer, durable_root
    ):
        mint_run_and_proposition(durable_writer)
        assessment = stored.assessment_value(mint_assessment(durable_writer, outcome="supported"))
        built = passed_verification_under_a_tolerance()
        genuine = stored.verification_node(
            "genuine",
            title="genuine",
            assessment=assessment.identity(),
            assessment_ref=ASSESSMENT,
            scope=built.scope,
            verdict=built.verdict,
        )
        durable_writer.add(genuine)
        forged = stored.verification_node(
            "forged",
            title="forged",
            assessment=assessment.identity(),
            assessment_ref=ASSESSMENT,
            scope=built.scope,
            verdict=built.verdict,
        )
        raw_write(durable_root, forged)

        view = reopen(durable_root)
        # The reader has nothing to tell them apart by: same fields, same
        # self-consistent stamp, one minted and one written behind the API.
        genuine_fields = view.get(genuine.id).facets
        forged_fields = view.get(forged.id).facets
        assert genuine_fields[stored.VERIFICATION_FACET] == forged_fields[stored.VERIFICATION_FACET]
        assert genuine_fields[stored.SEMANTIC_IDENTITY_FACET] == forged_fields[stored.SEMANTIC_IDENTITY_FACET]
        assert corpus_check(view) == ()


class TestR22TheForgeryAtTheCorrectAddress:
    """Mint an assessment, take the belief digest over the reloaded store, then
    raw-write a file **at the address a genuine record would occupy** carrying
    `supported` where the derivation from the same run yields `refuted`. The
    digest moves and the reader says nothing: change detection, not truth
    detection."""

    @pytest.fixture()
    def forged(self, durable_writer, durable_root):
        mint_run_and_proposition(durable_writer)
        mint_assessment(durable_writer, outcome="refuted")  # what the derivation yields
        correct = belief_digest(reopen(durable_root))
        forgery = stored.assessment_node(
            "a1",
            title="a1",
            spec=SPEC,
            run=RUN,
            proposition=PROPOSITION,
            outcome="supported",  # what the forger wants it to say
            interpretation_rule=RULE,
        )
        raw_write(durable_root, forgery)  # the basis is (spec, run, proposition): the same address
        return correct

    def test_the_belief_digest_differs_from_the_correct_states(self, forged, durable_root):
        assert belief_digest(reopen(durable_root)) != forged

    def test_the_forgery_is_self_consistent_so_the_stale_hash_check_has_nothing_to_say(
        self, forged, durable_root
    ):
        view = reopen(durable_root)
        assert stored.assessment_value(view.get(ASSESSMENT)).outcome == "supported"

    def test_the_corpus_check_reports_nothing(self, forged, durable_root):
        assert corpus_check(reopen(durable_root)) == ()

    def test_a_digest_over_assessment_identities_alone_would_have_missed_it(self, forged, durable_root):
        # The identity is `(spec, run, proposition)` and the forgery changes
        # none of them; what moves is the keyed facet digest paired with it.
        view = reopen(durable_root)
        value = stored.assessment_value(view.get(ASSESSMENT))
        assert value.identity() == stored.assessment_value(
            stored.assessment_node(
                "a1",
                title="a1",
                spec=SPEC,
                run=RUN,
                proposition=PROPOSITION,
                outcome="refuted",
                interpretation_rule=RULE,
            )
        ).identity()
        assert value.facet_digest() != stored.assessment_value(
            stored.assessment_node(
                "a1",
                title="a1",
                spec=SPEC,
                run=RUN,
                proposition=PROPOSITION,
                outcome="refuted",
                interpretation_rule=RULE,
            )
        ).facet_digest()

    def test_the_snapshot_stays_an_argument_to_the_digest(self, forged, durable_root):
        # The closure is corpus-local and the producer snapshot is supplied, so
        # no clause of this reaches the rules store or the world index.
        assert isinstance(lineage_snapshot(reopen(durable_root), []), LineageSnapshot)
