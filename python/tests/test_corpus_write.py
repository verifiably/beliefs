"""The add path's refusals, the plans it emits, and the operation lock.

Portable: the write API takes its executor factory as an argument, so these run
against `DefaultExecutor` behind a recorder. What they cannot claim is cut-4
discharge — a record minted through `DefaultExecutor` is minted through the
substrate's best-effort path, not through the certified engine.
"""

from __future__ import annotations

import re
import threading
import time
from typing import Any, ClassVar, cast

import pytest
from fixtures_cut6 import PINS
from nodes.core.errors import CollisionError, ExecutionError, ValidationError
from nodes.core.node import Node, NodeMetadata
from nodes.core.write_plan import CreateOp, DefaultExecutor, DeleteOp, ReplaceOp

from beliefs import stored
from beliefs.corpus import CorpusWriter, OperationLock, _operation_lock_for
from beliefs.errors import (
    BasisMissing,
    BuildHold,
    CollisionRefused,
    EligibilityUnmet,
    ManifestAlreadyPresent,
    ManifestMalformed,
    RecordAlreadyMinted,
    ScienceError,
    ValidationRefused,
    WriteRefused,
)
from beliefs.root import open_corpus
from beliefs.world import load_manifest, manifest_bytes

PINNED = [{"name": "matrix", "digest": "sha256:" + "ab" * 32}]


class Recorder:
    """Every plan that reaches an executor, applied through the substrate's own
    best-effort executor so later reads see the result."""

    plans: ClassVar[list[list]] = []

    def __init__(self, root):
        self._inner = DefaultExecutor(root)

    def execute(self, plan) -> None:
        Recorder.plans.append(list(plan))
        self._inner.execute(plan)


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    Recorder.plans = []
    return CorpusWriter(tmp_path, Recorder)


def observed_dataset(slug="raw"):
    return stored.dataset_node(
        slug, title=slug, resources=PINNED, empirical_observation={"boundary": "instrument"}
    )


def admissible(writer: CorpusWriter, *, observes=True):
    dataset = observed_dataset()
    writer.add(dataset)
    run = stored.run_node(
        "r1", title="r1", spec="analysis-spec:s1", observes=[dataset.id] if observes else []
    )
    writer.add(run)
    writer.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    return stored.assessment_node(
        "a1",
        title="a1",
        spec="analysis-spec:s1",
        run=run.id,
        proposition="proposition:p1",
        outcome="supported",
        interpretation_rule="rule:threshold",
    )


class TestTheAddPathIsAddOnly:
    def test_adopt_manifest_mints_and_executes_one_create(self, writer):
        manifest = writer.adopt_manifest(profile=PINS)

        assert re.fullmatch(r"[0-9a-f]{32}", manifest.corpus_id)
        assert manifest.forked_from is None
        assert Recorder.plans[-1] == [CreateOp("corpus.yaml", manifest_bytes(manifest))]
        assert load_manifest(writer.read_view._corpus.store.root) == manifest

    def test_adopt_manifest_never_remints(self, writer):
        first = writer.adopt_manifest(profile=PINS)

        with pytest.raises(ManifestAlreadyPresent):
            writer.adopt_manifest(profile=PINS)

        assert load_manifest(writer.read_view._corpus.store.root) == first

    def test_adopt_manifest_refuses_malformed_profile_before_execution(self, writer):
        malformed = type(PINS)(
            science_contract=PINS.science_contract,
            domains=cast(Any, {**PINS.domains, 1: "biology:" + "b" * 64}),
        )

        with pytest.raises(ManifestMalformed):
            writer.adopt_manifest(profile=malformed)

        assert Recorder.plans == []

    def test_a_mint_emits_exactly_one_create(self, writer):
        writer.add(observed_dataset())
        (plan,) = Recorder.plans
        assert [type(op) for op in plan] == [CreateOp]

    def test_no_plan_this_surface_emits_carries_a_replace_or_a_delete(self, writer):
        writer.add(observed_dataset())
        with pytest.raises(RecordAlreadyMinted):
            writer.add(writer.read_view.get("dataset:raw"))
        assert not any(isinstance(op, (ReplaceOp, DeleteOp)) for plan in Recorder.plans for op in plan)

    def test_an_existing_uid_and_id_pair_refuses_before_plan_construction(self, writer):
        minted = observed_dataset()
        writer.add(minted)
        with pytest.raises(RecordAlreadyMinted):
            writer.add(minted)
        assert len(Recorder.plans) == 1

    def test_the_minted_node_is_returned_as_nodes_mints_it(self, writer):
        minted = observed_dataset()
        assert writer.add(minted).uid == minted.uid

    def test_a_stale_governed_stamp_refuses_before_execution(self, writer):
        stale = observed_dataset()
        stale.facets[stored.DATASET_FACET]["resources"][0]["digest"] = "sha256:" + "cd" * 32

        with pytest.raises(ValidationRefused, match="semantic-identity stamp"):
            writer.add(stale)

        assert Recorder.plans == []

    def test_a_missing_governed_stamp_refuses_before_execution(self, writer):
        unstamped = observed_dataset()
        del unstamped.facets[stored.SEMANTIC_IDENTITY_FACET]

        with pytest.raises(ValidationRefused, match="semantic-identity stamp"):
            writer.add(unstamped)

        assert Recorder.plans == []

    def test_an_unrenderable_node_refuses_before_execution(self, writer):
        node = Node(id="note:surrogate", kind="note", title="surrogate", body="\ud800")

        with pytest.raises(ValidationRefused, match="losslessly renderable"):
            writer.add(node)

        assert Recorder.plans == []


class TestW3TheBasisRefusal:
    def test_a_source_with_no_accepted_external_identifier_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(stored.source_node("s1", title="A paper", identifiers={}))

    def test_a_source_with_a_doi_is_minted(self, writer):
        assert writer.add(stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})).id

    def test_an_unaccepted_identifier_is_not_a_basis(self, writer):
        # The set is closed: a url or a title-and-year is not an external
        # identifier, and there is no derived-identity escape to reach.
        with pytest.raises(BasisMissing):
            writer.add(stored.source_node("s1", title="A paper", identifiers={"url": "https://example.org"}))

    def test_a_dataset_with_no_content_identity_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(stored.dataset_node("d1", title="DepMap", resources=[]))

    def test_a_dataset_with_one_unpinned_resource_refuses(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(
                stored.dataset_node("d1", title="DepMap", resources=[*PINNED, {"name": "unpinned"}])
            )

    def test_a_dataset_whose_bytes_are_held_nowhere_is_minted(self, writer):
        # G9, and the admission ramp's narrowing: identity is not holding. The
        # add path performs no holding check — `declared` / `held` is derived on
        # read and never stored.
        minted = writer.add(stored.dataset_node("d1", title="DepMap 24Q2", resources=PINNED))
        assert writer.read_view.holds(minted.id)

    def test_a_note_is_not_what_a_missing_basis_coerces_to(self, writer):
        with pytest.raises(BasisMissing):
            writer.add(stored.source_node("s1", title="A paper", identifiers={}))
        assert not writer.read_view.holds("source:s1")


class TestS7TheWriteBoundary:
    def test_an_assesses_edge_whose_run_has_no_observes_input_refuses(self, writer):
        with pytest.raises(EligibilityUnmet):
            writer.add(admissible(writer, observes=False))

    def test_an_admissible_assesses_edge_is_minted(self, writer):
        assert writer.add(admissible(writer)).id == "assessment:a1"

    def test_an_assessment_naming_a_run_this_corpus_does_not_hold_refuses(self, writer):
        with pytest.raises(EligibilityUnmet):
            writer.add(
                stored.assessment_node(
                    "a1",
                    title="a1",
                    spec="analysis-spec:s1",
                    run="run:elsewhere",
                    proposition="proposition:p1",
                    outcome="supported",
                    interpretation_rule="rule:threshold",
                )
            )


class TestTheRefusalsWrapAndOrder:
    def test_add_reserves_family_owned_kinds_before_document_validation(self, writer):
        retraction = stored.retraction_node(
            title="r",
            target=stored.NodeTarget("assessment:a1", "assessment:a1", "sha256:" + "cd" * 32),
            reason="defective-code",
            rationale="invalid",
            grounds=("verification:v1",),
            actor="tester",
            event_token="event-1",
        )
        retraction.metadata = NodeMetadata.model_construct(version="bad")
        with pytest.raises(WriteRefused, match="a retraction enters through retract"):
            writer.add(retraction)

        report = Node.model_construct(id="act-report:r1", kind="act-report")
        with pytest.raises(
            WriteRefused,
            match="an act-report is minted by the boundary and stored by import",
        ):
            writer.add(report)

    def test_a_document_validation_failure_is_wrapped(self, writer):
        malformed = Node.model_construct(
            id="dataset:d1", uid="a" * 32, kind="run", title="wrong kind", facets={}, relations=[]
        )
        with pytest.raises(ValidationRefused) as refused:
            writer.add(malformed)
        assert refused.value.__cause__ is not None

    def test_a_forged_nested_model_is_revalidated_before_add(self, writer):
        malformed = observed_dataset()
        malformed.metadata = NodeMetadata.model_construct(version="bad")

        with pytest.raises(ValidationRefused):
            writer.add(malformed)

        assert not writer.read_view.holds(malformed.id)
        assert Recorder.plans == []

    def test_a_collision_is_wrapped_and_no_nodes_error_escapes_raw(self, writer):
        first = observed_dataset()
        writer.add(first)
        second = observed_dataset("other")
        second.uid = first.uid
        with pytest.raises(CollisionRefused) as refused:
            writer.add(second)
        assert isinstance(refused.value.__cause__, CollisionError)

    def test_an_identity_claim_held_by_another_uid_is_a_collision(self, writer):
        writer.add(observed_dataset())
        twin = observed_dataset()  # same id, fresh uid
        with pytest.raises(CollisionRefused):
            writer.add(twin)

    def test_every_refusal_is_a_science_error(self, writer):
        assert issubclass(WriteRefused, ScienceError)
        for refusal in (RecordAlreadyMinted, BasisMissing, EligibilityUnmet, ValidationRefused, CollisionRefused):
            assert issubclass(refusal, WriteRefused)

    def test_the_add_only_guard_refuses_before_the_basis_check(self, writer):
        minted = writer.add(observed_dataset())
        minted.facets[stored.DATASET_FACET]["resources"] = []  # no content identity any more
        with pytest.raises(RecordAlreadyMinted):
            writer.add(minted)

    def test_the_basis_check_refuses_before_eligibility(self, writer):
        # A dataset with no content identity and an assesses edge it could not
        # support either: the earlier refusal is the one raised.
        node = stored.dataset_node("d1", title="d1", resources=[])
        node.relations.append(
            stored.Relation(source=node.id, predicate=stored.ASSESSES, target="proposition:p1")
        )
        with pytest.raises(BasisMissing):
            writer.add(node)

    def test_eligibility_refuses_before_document_validation(self, writer):
        malformed = stored.assessment_node(
            "a1",
            title="a1",
            spec="analysis-spec:s1",
            run="run:elsewhere",
            proposition="proposition:p1",
            outcome="supported",
            interpretation_rule="rule:threshold",
        )
        malformed.kind = "run"  # a document-validation failure, behind an eligibility one
        with pytest.raises(EligibilityUnmet):
            writer.add(malformed)

    def test_document_validation_refuses_before_the_collision_check(self, writer):
        writer.add(observed_dataset())
        malformed = Node.model_construct(
            id="dataset:raw", uid="b" * 32, kind="run", title="colliding and malformed", facets={}, relations=[]
        )
        with pytest.raises(ValidationRefused):
            writer.add(malformed)


class TestTheExecutionLayerCrossesUnwrapped:
    def test_an_executor_failure_is_not_translated_into_a_write_refusal(self, tmp_path):
        class Failing:
            def __init__(self, root):
                self.root = root

            def execute(self, plan):
                raise ExecutionError("engine said no", index=None, applied=None)

        writer = CorpusWriter(tmp_path, Failing)
        with pytest.raises(ExecutionError) as raised:
            writer.add(observed_dataset())
        assert not isinstance(raised.value, ScienceError)


class TestTheOperationLock:
    """§7's deterministic barrier check, and the sabotage it exists to catch: a
    lock covering only `execute` lets the second add complete its reads and its
    planning while the first is still inside the engine, and two plans reach the
    executor with no collision refused anywhere."""

    def test_two_writers_one_root_share_lock_and_state(self, tmp_path):
        Recorder.plans = []
        a = CorpusWriter(tmp_path, Recorder)
        b = CorpusWriter(tmp_path, Recorder)

        assert a._operation is b._operation
        minted = a.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
        assert b.read_view.holds(minted.id)

        other = CorpusWriter(tmp_path / "other", Recorder)
        assert other._operation is not a._operation

    def test_second_writer_with_different_factory_refuses(self, tmp_path):
        CorpusWriter(tmp_path, Recorder)
        with pytest.raises(ScienceError):
            CorpusWriter(tmp_path, DefaultExecutor)

    def test_open_corpus_twice_shares_state(self, tmp_path):
        a = open_corpus(tmp_path)
        b = open_corpus(tmp_path)
        assert a._operation is b._operation

    def test_two_same_uid_adds_are_serialized_end_to_end(self, tmp_path):
        entered = threading.Event()
        release = threading.Event()
        plans: list[list] = []
        lock = threading.Lock()

        class Barrier:
            def __init__(self, root):
                self._inner = DefaultExecutor(root)

            def execute(self, plan):
                with lock:
                    plans.append(list(plan))
                entered.set()
                assert release.wait(timeout=10)
                self._inner.execute(plan)

        first_writer = CorpusWriter(tmp_path, Barrier)
        second_writer = CorpusWriter(tmp_path, Barrier)
        first = observed_dataset("first")
        second = observed_dataset("second")
        second.uid = first.uid  # same uid, different id

        outcome: list[BaseException | None] = [None]

        def add_first():
            first_writer.add(first)

        def add_second():
            try:
                second_writer.add(second)
                outcome[0] = None
            except BaseException as caught:  # noqa: BLE001 - the outcome is the assertion
                outcome[0] = caught

        one = threading.Thread(target=add_first)
        one.start()
        assert entered.wait(timeout=10)  # the first add is inside the executor

        two = threading.Thread(target=add_second)
        two.start()
        # Long enough for the second add to reach whatever it blocks on: under
        # the operation lock that is the lock itself, and under an execute-only
        # lock it is the barrier, with its plan already built.
        time.sleep(0.25)
        try:
            with lock:
                planned = len(plans)
        finally:
            # Released whatever the count turned out to be: a failing assertion
            # must not leave two threads parked on a barrier.
            release.set()
            one.join(timeout=10)
            two.join(timeout=10)

        assert planned == 1  # exactly one plan reached the executor
        assert isinstance(outcome[0], CollisionRefused)
        assert len(plans) == 1
        assert not one.is_alive() and not two.is_alive()

    def test_a_write_during_a_capture_refuses_and_commits_nothing(self, tmp_path):
        """The build's capture excludes writers without queueing them: the add
        refuses where it stands, and nothing of it reaches the executor."""
        Recorder.plans = []
        writer = CorpusWriter(tmp_path, Recorder)
        node = observed_dataset("captured")
        outcome: list[BaseException | None] = [None]

        def add_under_capture():
            try:
                writer.add(node)
            except BaseException as caught:  # noqa: BLE001 - the outcome is the assertion
                outcome[0] = caught

        with writer._state.lock.capture():
            attempt = threading.Thread(target=add_under_capture)
            attempt.start()
            # Bounded: a writer that queued behind the capture would still be
            # alive here, and this join would be the thing that reports it.
            attempt.join(timeout=10)
            assert not attempt.is_alive()

        assert isinstance(outcome[0], BuildHold)
        assert Recorder.plans == []
        assert not writer.read_view.holds(node.id)

    def test_cooperating_writers_still_serialize_and_succeed(self, tmp_path):
        """No capture, no refusal: four writers released together all land."""
        Recorder.plans = []
        writers = [CorpusWriter(tmp_path, Recorder) for _ in range(4)]
        nodes = [observed_dataset(f"co{index}") for index in range(4)]
        together = threading.Barrier(len(writers))
        failures: list[BaseException] = []

        def add(writer, node):
            try:
                together.wait(timeout=10)  # every writer arrives at once
                writer.add(node)
            except BaseException as caught:  # noqa: BLE001 - the outcome is the assertion
                failures.append(caught)

        threads = [
            threading.Thread(target=add, args=(writer, node))
            for writer, node in zip(writers, nodes)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            assert not thread.is_alive()

        assert failures == []
        assert len(Recorder.plans) == len(nodes)
        assert all(writers[0].read_view.holds(node.id) for node in nodes)


class TestTheLockOnlyLookup:
    """`_operation_lock_for`: the same per-root lock, without a `Corpus`.

    Audit locks a root it never opens, and the root it audits may be exactly
    the one whose bytes are damaged — so the lookup that hands out the lock
    cannot be the one that also builds a corpus and reads every node. Two
    entry points, one registry, one lock object: a lock that merely behaved
    like the writer's would serialize nothing.
    """

    def test_the_lookup_yields_the_lock_the_write_api_later_holds(self, tmp_path):
        looked_up = _operation_lock_for(tmp_path)
        writer = CorpusWriter(tmp_path, Recorder)

        assert writer._operation is looked_up

    def test_the_write_apis_lock_is_what_a_later_lookup_yields(self, tmp_path):
        # The other order, because a lookup that constructed a second lock
        # after the writer had one would still pass the arm above.
        writer = CorpusWriter(tmp_path, Recorder)

        assert _operation_lock_for(tmp_path) is writer._operation

    def test_the_lookup_resolves_the_root_the_way_the_write_api_does(self, tmp_path):
        (tmp_path / "sub").mkdir()
        writer = CorpusWriter(tmp_path, Recorder)

        assert _operation_lock_for(tmp_path / "sub" / "..") is writer._operation

    def test_the_lookup_works_over_damaged_node_bytes(self, tmp_path):
        (tmp_path / "dataset").mkdir()
        (tmp_path / "dataset" / "broken.md").write_text("---\nnot: a node\n---\n", encoding="utf-8")

        looked_up = _operation_lock_for(tmp_path)

        assert isinstance(looked_up, OperationLock)
        assert _operation_lock_for(tmp_path) is looked_up
        # The corpus-constructing entry point cannot serve here, which is why
        # the lock-only one exists.
        with pytest.raises(ValidationError):
            CorpusWriter(tmp_path, Recorder)

    def test_two_roots_do_not_share_a_lock(self, tmp_path):
        assert _operation_lock_for(tmp_path / "one") is not _operation_lock_for(tmp_path / "two")
