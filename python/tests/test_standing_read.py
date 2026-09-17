"""Standing at the read (correction-remainder slice 1): the fold, the local
enumeration, and — from Task 4 on — `gather`'s subtraction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from authority import ACTOR, FULL
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_local_standing import assessment, retracts

from beliefs import corpus, stored
from beliefs.closure import RETRACTION_OVERTURNED, RETRACTION_UPHELD, RetractionEnumeration
from beliefs.corpus import CorpusWriter, ReadView, local_retraction_enumeration, retraction_standing
from beliefs.errors import MalformedRecord, ManifestMissing, RetractionUnreadable


def adopted(tmp_path: Path, name: str = "corpus") -> CorpusWriter:
    """A corpus with a manifest: `ReadView.corpus_id` reads one, and
    `test_local_standing.seed` writes none (spec §8.1)."""
    writer = CorpusWriter(tmp_path / name, DefaultExecutor, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return writer


def add_assessment(writer: CorpusWriter):
    """Supply the real write boundary's prerequisites for `assessment()`."""
    dataset = writer.add(
        stored.dataset_node(
            title="raw",
            resources=[{"name": "matrix", "digest": "sha256:" + "ab" * 32}],
            empirical_observation={"locator": "instrument:fixture", "attested_by": writer.authority.actor},
        )
    )
    writer.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[dataset.id]))
    writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    return writer.add(assessment())


def test_the_local_enumeration_is_empty_with_the_manifest_coverage(tmp_path):
    writer = adopted(tmp_path)
    view = writer.read_view
    assert view.corpus_id == writer.corpus_id
    assert local_retraction_enumeration(view) == RetractionEnumeration(found=(), coverage=(writer.corpus_id,))


def test_the_local_enumeration_folds_standing_and_keys_by_id(tmp_path):
    writer = adopted(tmp_path)
    target = add_assessment(writer)
    first = writer.retract(retracts(target, "t1"))
    counter = writer.retract(retracts(first, "t2"))
    view = writer.read_view
    found = dict(local_retraction_enumeration(view).found)
    assert found == {first.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}
    facets = {n.id: corpus._validated_retraction_facet(n) for n in view.iter_stored() if n.kind == "retraction"}
    standing = retraction_standing(view, facets)
    assert standing[first.id] is False and standing[counter.id] is True and standing[target.id] is True
    assert corpus.standing_in_local_view(view, target.id) is True


def test_a_manifest_less_corpus_cannot_declare_coverage(tmp_path):
    from fixtures_cut4 import raw_write, reopen

    raw_write(tmp_path / "bare", assessment())
    with pytest.raises(ManifestMissing):
        _coverage = local_retraction_enumeration(reopen(tmp_path / "bare")).coverage


def test_a_raw_retraction_the_capture_validator_refuses_is_unreadable_at_the_enumeration(tmp_path):
    from fixtures_cut4 import raw_write

    writer = adopted(tmp_path)
    target = add_assessment(writer)
    node = retracts(target, "t1")
    node.facets[stored.RETRACTION_FACET].pop("grounds")
    raw_write(writer.root, stored.stamp_semantic_identity(node))
    with pytest.raises(RetractionUnreadable) as refused:
        local_retraction_enumeration(ReadView.opened_at(writer.root))
    assert refused.value.ref == node.id
    assert refused.value.cause == f"{node.id}: malformed retraction facet"
    assert isinstance(refused.value.__cause__, corpus.MalformedRecord)


from dataclasses import replace

from domain_facet_fixtures import kwargs_for, over_kwargs, profile_with, seed

from beliefs.admission import AdmissionRefused, Admitted, admit
from beliefs.belief import Belief, evaluate
from beliefs.evaluation import evaluate_over, gather
from beliefs.verification import ADMITTED, INVALIDATED, NOT_ADMITTED, lifecycle_state


def seeded(tmp_path, *, outcomes=("supported", "refuted")):
    """The domain-facet scenario in a writer-adopted corpus: `assessment:a-1`
    (`run:run-a` over `dataset:d-a`) and `assessment:a-2` (`run:run-b` over
    `dataset:d-b`), each carrying one clean-environment pass (`verification:v-1`,
    `verification:v-2`), both roots basisless so the pair certifies independent.
    `outcomes` is the one knob this slice adds to `seed` (a second parameter,
    default `("supported", "supported")` so every existing caller is unchanged):
    with a-2 refuting, the baseline belief is 0 and subtracting a-1 moves it to
    -1 — cut 5's C4 arithmetic through `evaluate_over` instead of a test-side
    filter."""
    profile = profile_with()
    writer = CorpusWriter(tmp_path / "scratch", DefaultExecutor, authority=FULL, profile=profile)
    writer.adopt_manifest(profile=pins_for(profile))
    seed(writer, axis="rows", outcomes=outcomes)
    return writer, profile


def fresh(writer) -> ReadView:
    """A view opened after the last write — a raw write past the boundary is
    not in the writer's index, and the writer's view would not find it."""
    return ReadView.opened_at(writer.root)


def gathered(writer, profile, view=None):
    view = view or fresh(writer)
    kwargs = over_kwargs(kwargs_for(view, profile))
    return kwargs, gather(
        view, "proposition:p", **over_kwargs({k: kwargs[k] for k in ("context", "profile", "resolution", "binding")})
    )


A1, A2, V1, V2 = "assessment:a-1", "assessment:a-2", "verification:v-1", "verification:v-2"


class TestSubtractionAtTheRead:
    def test_a_retracted_assessment_leaves_the_read_set_before_decoding(self, tmp_path):
        writer, profile = seeded(tmp_path)
        _kwargs, baseline = gathered(writer, profile)
        retraction = writer.retract(retracts(writer.read_view.get(A1), "t1"))
        _kwargs, after = gathered(writer, profile)
        gone = {a.identity() for a in baseline.assessments} - {a.identity() for a in after.assessments}
        assert len(gone) == 1
        assert ("retraction", retraction.id) in after.read_trace
        assert not any(kind == "assessment" and ref in gone for kind, ref in after.read_trace)
        assert ("retraction", retraction.id) in after.declared_refs()
        assert after.retractions.found == ((retraction.id, RETRACTION_UPHELD),)
        assert after.retractions.coverage == (writer.corpus_id,)
        assert after.closure().digest() != baseline.closure().digest()

    def test_a_counter_retraction_returns_the_assessment_with_a_third_digest(self, tmp_path):
        writer, profile = seeded(tmp_path)
        a = gathered(writer, profile)[1].closure().digest()
        first = writer.retract(retracts(writer.read_view.get(A1), "t1"))
        b = gathered(writer, profile)[1].closure().digest()
        counter = writer.retract(retracts(first, "t2"))
        _kwargs, after = gathered(writer, profile)
        assert len(after.assessments) == 2
        assert dict(after.retractions.found) == {first.id: RETRACTION_OVERTURNED, counter.id: RETRACTION_UPHELD}
        assert len({a, b, after.closure().digest()}) == 3

    def test_the_answer_moves_through_evaluate_over_with_no_test_side_filter(self, tmp_path):
        writer, profile = seeded(tmp_path)  # a-1 supports, a-2 refutes: 0
        kwargs, _inputs = gathered(writer, profile)
        before = evaluate_over(fresh(writer), "proposition:p", **over_kwargs(kwargs))
        writer.retract(retracts(writer.read_view.get(A1), "t1"))
        kwargs, inputs = gathered(writer, profile)
        after = evaluate_over(fresh(writer), "proposition:p", **over_kwargs(kwargs))
        assert isinstance(before, Belief) and isinstance(after, Belief)
        assert before.value == 0 and after.value == -1
        assert inputs.closure().digest() == after.belief_input_digest

    def test_a_supplied_enumeration_is_a_type_error_and_a_pre_retired_snapshot_refuses(self, tmp_path):
        writer, profile = seeded(tmp_path)
        kwargs = kwargs_for(writer.read_view, profile)
        with pytest.raises(TypeError):
            replace(kwargs["context"], retractions=RetractionEnumeration(found=(), coverage=()))
        snapshot = kwargs["context"].snapshot
        # Construct the forbidden input directly: retire() drops entries for these basisless roots.
        pre = replace(kwargs["context"], snapshot=replace(snapshot, retired={snapshot.roots[0]: ("route:x",)}))
        assert pre.snapshot.retired
        with pytest.raises(MalformedRecord, match="may not pre-retire"):
            gather(
                writer.read_view,
                "proposition:p",
                context=pre,
                profile=profile,
                resolution=kwargs["resolution"],
                binding=kwargs["binding"],
            )

    def test_evaluate_without_retractions_is_a_type_error(self):
        from test_belief import scenario

        kwargs: dict[str, Any] = dict(scenario())
        kwargs.pop("retractions")
        with pytest.raises(TypeError):
            evaluate(**kwargs)


class TestTheAmendedG8Clause:
    """A retracted verification leaves the read set; `active` recomputes over
    what remains (spec decision 5). Read two ways: the belief value through
    `evaluate_over` (a-1 admitted → 0, a-1 not admitted → -1 with a-2 refuting
    alone) and the gate itself, `admit(assessment, run, observations,
    verifications)`, which answers `Admitted` or `AdmissionRefused`."""

    def _gate(self, writer, profile):
        """The gate's answer, the lifecycle state it rests on (the gate's reason
        does not distinguish `invalidated` from `not-admitted`), and the belief."""
        kwargs, inputs = gathered(writer, profile)
        identity = stored.assessment_reference(writer.read_view.get(A1)).identity()
        a1 = next(a for a in inputs.assessments if a.identity() == identity)
        gate = admit(a1, inputs.runs[a1.run], kwargs["availability"].observations, inputs.verifications)
        state = lifecycle_state(tuple(v for v in inputs.verifications if v.assessment == identity))
        answer = evaluate_over(fresh(writer), "proposition:p", **over_kwargs(kwargs))
        assert isinstance(answer, Belief)
        return gate, state, answer

    def test_retracting_a_false_failure_admits_iff_a_standing_pass_remains(self, tmp_path):
        writer, profile = seeded(tmp_path)  # a-1 carries v-1, a clean-environment pass
        a1 = writer.read_view.get(A1)
        failing = writer.add(verification_for(a1, scope="clean-environment", verdict="failed", slug="fail"))
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, AdmissionRefused) and state == INVALIDATED and answer.value == -1
        writer.retract(retracts(failing, "false-failure"))
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, Admitted) and state == ADMITTED and answer.value == 0
        writer.retract(retracts(writer.read_view.get(V1), "false-pass"))  # the only standing pass
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, AdmissionRefused) and state == NOT_ADMITTED and answer.value == -1

    def test_retracting_a_resolution_restores_the_failure_it_named(self, tmp_path):
        writer, profile = seeded(tmp_path)
        a1 = writer.read_view.get(A1)
        failing = writer.add(verification_for(a1, scope="clean-environment", verdict="failed", slug="fail"))
        resolution = writer.add(
            verification_for(a1, scope="clean-environment", verdict="passed", slug="fix", supersedes=failing.id)
        )
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, Admitted) and state == ADMITTED and answer.value == 0
        writer.retract(retracts(resolution, "false-resolution"))
        gate, state, answer = self._gate(writer, profile)
        assert isinstance(gate, AdmissionRefused) and state == INVALIDATED and answer.value == -1


class TestUnreadableAndAbsent:
    def test_a_stale_target_ref_restamped_is_unreadable(self, tmp_path):
        from fixtures_cut4 import raw_write

        writer, profile = seeded(tmp_path)
        node = retracts(writer.read_view.get(A1), "t1")
        node.facets[stored.RETRACTION_FACET]["target"]["ref"] = "assessment:gone"
        node.facets[stored.RETRACTION_FACET]["target"]["resolved"] = "assessment:gone"
        raw_write(writer.root, stored.stamp_semantic_identity(node))
        with pytest.raises(RetractionUnreadable) as refused:
            gathered(writer, profile, fresh(writer))  # a fresh view: the writer's index does not hold a raw write
        assert refused.value.ref == node.id

    def test_a_canonical_retraction_with_wrong_content_identity_is_unreadable(self, tmp_path):
        from fixtures_cut4 import raw_write

        writer, profile = seeded(tmp_path)
        target = writer.read_view.get(A1)
        node = stored.retraction_node(
            title="t1",
            target=stored.NodeTarget(target.id, target.id, "sha256:" + "ab" * 32),
            reason="defective-code",
            rationale="the record is invalid",
            grounds=("verification:v1",),
            actor=ACTOR,
            event_token="t1",
        )
        CorpusWriter._validated_retraction(node)  # canonical shape; the target identity check must refuse it
        raw_write(writer.root, node)
        with pytest.raises(RetractionUnreadable, match="content identity"):
            gathered(writer, profile, fresh(writer))

    def test_a_stale_stamp_is_unreadable_too(self, tmp_path):
        from fixtures_cut4 import raw_write

        writer, profile = seeded(tmp_path)
        node = retracts(writer.read_view.get(A1), "t1")
        stamped = stored.stamp_semantic_identity(node)
        stamped.facets[stored.RETRACTION_FACET]["rationale"] = "edited after the stamp"
        raw_write(writer.root, stamped)
        with pytest.raises(RetractionUnreadable, match="semantic-hash-stale|stale"):
            gathered(writer, profile, fresh(writer))


def verification_for(assessment, *, scope: str, verdict: str, slug: str, supersedes: str | None = None):
    return stored.verification_node(
        slug,
        title=slug,
        assessment=stored.assessment_reference(assessment).identity(),
        assessment_ref=assessment.id,
        scope=scope,
        verdict=verdict,
        supersedes=supersedes,
    )


def test_unrelated_retraction_leaves_the_input_digest_unchanged(tmp_path):
    from fixtures_cut3 import typed_applicability, typed_estimand

    writer, profile = seeded(tmp_path)
    baseline = gathered(writer, profile)[1]
    writer.add(stored.proposition_node("q", title="q", claim={"operator": "affects"}))
    other = writer.add(
        stored.assessment_node(
            "other",
            title="other",
            spec="spec-a",
            run="run:run-a",
            proposition="proposition:q",
            outcome="supported",
            interpretation_rule="rule-1",
            estimand=typed_estimand(),
            applicability=typed_applicability(),
        )
    )
    writer.retract(retracts(other, "unrelated"))
    after = gathered(writer, profile)[1]
    assert after.retractions.found == ()
    assert after.closure().digest() == baseline.closure().digest()


def test_subtracted_assessments_and_verifications_are_never_decoded(tmp_path):
    from fixtures_cut4 import raw_write

    writer, profile = seeded(tmp_path)
    kwargs, _ = gathered(writer, profile)
    for ref, facet, member in ((A1, stored.ASSESSMENT_FACET, "outcome"), (V2, stored.VERIFICATION_FACET, "verdict")):
        node = writer.read_view.get(ref).model_copy(deep=True)
        node.facets[facet][member] = "malformed"
        node = stored.stamp_semantic_identity(node)
        raw_write(writer.root, node)
        raw_write(writer.root, stored.stamp_semantic_identity(retracts(node, ref)))
    inputs = gather(
        fresh(writer), "proposition:p", **{k: kwargs[k] for k in ("context", "profile", "resolution", "binding")}
    )
    assert len(inputs.assessments) == 1
    assert not inputs.verifications
    assert len(inputs.retractions.found) == 2


def test_a_found_retraction_missing_from_the_local_index_is_unreadable(tmp_path):
    from fixtures_cut4 import raw_write
    from nodes.core.errors import RefError

    writer, profile = seeded(tmp_path)
    view = fresh(writer)
    kwargs = kwargs_for(view, profile)
    retraction = stored.stamp_semantic_identity(retracts(view.get(A1), "unindexed"))
    raw_write(writer.root, retraction)
    assert (retraction.id, RETRACTION_UPHELD) in local_retraction_enumeration(view).found
    with pytest.raises(RetractionUnreadable) as refused:
        gather(view, "proposition:p", **{k: kwargs[k] for k in ("context", "profile", "resolution", "binding")})
    assert refused.value.ref == retraction.id
    assert isinstance(refused.value.__cause__, RefError)
    assert refused.value.cause == str(refused.value.__cause__)
