"""Family writes through the certified composition root."""

from __future__ import annotations

import os
import shutil
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from atoms.chain.model import (
    ChainOutcome,
    IntentEntry,
    RegisteredEntry,
    SettledEntry,
    decode_entry,
)
from authority import ACTOR, FULL
from fixtures_cut3 import TESTING_PROFILE, typed_applicability, typed_estimand
from fixtures_cut4 import path_for, reopen
from nodes.core.errors import ExecutionError
from nodes.core.node import Node
from profiles import BASE
from test_closure import _closure_digest

from beliefs import stored
from beliefs.belief import Belief, evaluate
from beliefs.closure import RetractionEnumeration
from beliefs.corpus import CorpusWriter, run_value, standing_in_local_view, superseded_by
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.errors import BundleMemberHeld, ImportRefused, RetractionTargetIneligible
from beliefs.lineage import LineageSnapshot
from beliefs.report import ImportedRecords, RecordImportEntry, _mint_report
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus
from beliefs.verification import ADMITTED, INVALIDATED, NOT_ADMITTED, Verification, lifecycle_state


def proposition(slug: str, operator: str = "affects"):
    return stored.proposition_node(slug, title=slug, claim={"operator": operator})


def chain_entries(root: Path):
    found = {}
    for path in (root / ".#~chain").iterdir():
        assert path.name != ".#~stage"
        previous, entry = decode_entry(path.read_bytes())
        found[path.name] = (previous, entry)

    successors = {previous: (digest, entry) for digest, (previous, entry) in found.items()}
    ordered = []
    previous = None
    while previous in successors:
        digest, entry = successors[previous]
        ordered.append((digest, entry))
        previous = digest
    assert len(ordered) == len(found)
    return tuple(ordered)


def test_supersede_survives_facade_reload(durable_writer, durable_root):
    predecessor = durable_writer.add(proposition("prior"))
    successor = durable_writer.supersede(proposition("successor", "causes"), of=predecessor.id)

    view = reopen(durable_root)
    assert view.get(successor.id) == successor
    assert superseded_by(view, predecessor.id) == (successor.id,)
    assert view.get(predecessor.id) == predecessor


def test_revise_survives_facade_reload_with_unchanged_stamp(durable_writer, durable_root):
    original = durable_writer.add(proposition("revised"))
    stamp = stored.stored_semantic_hash(original)

    durable_writer.revise(original.model_copy(update={"title": "revised title"}))

    reloaded = reopen(durable_root).get(original.id)
    assert reloaded.title == "revised title"
    assert stored.stored_semantic_hash(reloaded) == stamp


def test_retract_survives_facade_reload(durable_writer, durable_root):
    target = durable_writer.add(
        stored.verification_node(
            "retracted",
            title="retracted",
            assessment="assessment-identity",
            assessment_ref="assessment:a1",
            scope="clean-environment",
            verdict="passed",
        )
    )
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    retraction = stored.retraction_node(
        title="durable retraction",
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=("source:acceptance",),
        actor=ACTOR,
        event_token="durable-retraction",
    )

    admitted = durable_writer.retract(retraction)

    view = reopen(durable_root)
    assert view.get(admitted.id) == admitted
    assert view.get(target.id) == target
    assert standing_in_local_view(view, target.id) is False


def test_import_bundle_records_the_exact_durable_chain(durable_root):
    writer = open_corpus(durable_root, authority=FULL, profile=BASE)
    before = chain_entries(durable_root)

    report = writer.import_bundle(
        [proposition("imported-a"), proposition("imported-b")],
        observer="corpus",
        instrument="families",
        opened_at="T0",
        closed_at="T1",
    )

    after = chain_entries(durable_root)
    added = after[len(before) :]
    assert len(added) == 5
    assert tuple(type(entry) for _, entry in added) == (
        IntentEntry,
        RegisteredEntry,
        SettledEntry,
        RegisteredEntry,
        SettledEntry,
    )

    intent_digest, _ = added[0]
    payload_registration_digest, payload_registration = added[1]
    _, payload_settlement = added[2]
    report_registration_digest, report_registration = added[3]
    _, report_settlement = added[4]
    assert isinstance(payload_registration, RegisteredEntry)
    assert isinstance(payload_settlement, SettledEntry)
    assert isinstance(report_registration, RegisteredEntry)
    assert isinstance(report_settlement, SettledEntry)
    assert payload_registration.fulfills is None
    assert payload_settlement.registration == payload_registration_digest
    assert payload_settlement.outcome is ChainOutcome.COMMITTED
    assert report_registration.fulfills == intent_digest
    assert report_settlement.registration == report_registration_digest
    assert report_settlement.outcome is ChainOutcome.COMMITTED

    report_ref = f"act-report:{report.identity()}"
    reloaded_report = reopen(durable_root).get(report_ref)
    expected_report = stored.act_report_node(report)
    assert reloaded_report.facets == expected_report.facets
    assert stored.stored_semantic_hash(reloaded_report) == stored.stored_semantic_hash(expected_report)


def test_import_on_an_uncertified_tuple_refuses():
    shm = Path("/dev/shm")
    if not shm.is_dir():
        raise AssertionError(
            "/dev/shm is unavailable, so the uncertified-tuple family negative cannot run; "
            "this is an error and not a skip"
        )
    root = shm / f"science-families-uncertified-{os.getpid()}"
    try:
        with pytest.raises(Exception) as registration:
            init_corpus_root(root, authority=FULL)
        assert "allowlist" in str(registration.value) or "barrier-option" in str(registration.value)

        with pytest.raises(ExecutionError) as refused:
            open_corpus(root, authority=FULL, profile=BASE).import_bundle(
                [proposition("uncertified")],
                observer="corpus",
                instrument="families",
                opened_at="T0",
                closed_at="T1",
            )
        assert (refused.value.index, refused.value.applied) == (None, 0)
        assert refused.value.__cause__ is not None
        assert not path_for(root, "proposition:uncertified").exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def _import(writer: CorpusWriter, records):
    return writer.import_bundle(
        records,
        observer="corpus",
        instrument="durable",
        opened_at="T0",
        closed_at="T1",
    )


def _retraction(target, event: str):
    identity = stored.stored_semantic_hash(target)
    assert identity is not None
    return stored.retraction_node(
        title=event,
        target=stored.NodeTarget(target.id, target.id, identity),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=("source:test",),
        actor="test-actor",
        event_token=event,
    )


def _mint_assessment_pair(writer: CorpusWriter):
    proposition_node = writer.add(
        stored.proposition_node("direction", title="direction", claim={"operator": "affects"})
    )
    found = []
    for slug, outcome, digest in (
        ("support", "supported", "b1"),
        ("refute", "refuted", "b2"),
    ):
        dataset = writer.add(
            stored.dataset_node(
                title=slug,
                resources=[{"name": "data", "digest": "sha256:" + digest * 32}],
                empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
            )
        )
        run = writer.add(
            stored.run_node(
                f"direction-{slug}",
                title=slug,
                spec=f"analysis-spec:{slug}",
                observes=(dataset.id,),
            )
        )
        found.append(
            writer.add(
                stored.assessment_node(
                    f"direction-{slug}",
                    title=slug,
                    spec=f"analysis-spec:{slug}",
                    run=run.id,
                    proposition=proposition_node.id,
                    outcome=outcome,
                    interpretation_rule="rule:threshold",
                    estimand=typed_estimand(),
                    applicability=typed_applicability(),
                )
            )
        )
    return tuple(found)


def test_scope_supersession_preserves_predecessor_evidence(durable_writer):
    from test_belief import scenario

    observed = durable_writer.add(
        stored.dataset_node(
            title="scope observed",
            resources=[{"name": "data", "digest": "sha256:" + "a1" * 32}],
            empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
        )
    )
    run = durable_writer.add(
        stored.run_node(
            "scope-run",
            title="scope run",
            spec="analysis-spec:scope",
            observes=(observed.id,),
        )
    )
    predecessor = durable_writer.add(
        stored.proposition_node(
            "in-adults",
            title="in adults",
            claim={"operator": "affects", "qualifiers": {"population": "adults"}},
        )
    )
    assessment = durable_writer.add(
        stored.assessment_node(
            "scope-assessment",
            title="scope assessment",
            spec="analysis-spec:scope",
            run=run.id,
            proposition=predecessor.id,
            outcome="supported",
            interpretation_rule="rule:threshold",
            estimand=typed_estimand(),
            applicability=typed_applicability(),
        )
    )
    assessment_value = stored.assessment_value(assessment, profile=TESTING_PROFILE)
    verification = durable_writer.add(
        stored.verification_node(
            "scope-verification",
            title="scope verification",
            assessment=assessment_value.identity(),
            assessment_ref=assessment.id,
            scope="clean-environment",
            verdict="passed",
        )
    )
    before = durable_writer.read_view.get(predecessor.id).model_dump(mode="json")
    template = scenario()
    declaration = stored.dataset_declaration(observed)
    address = dataset_address(declaration)
    digest = declaration.resources[0].digest
    assert address is not None and digest is not None

    def predecessor_belief():
        view = durable_writer.read_view
        value = stored.assessment_value(view.get(assessment.id), profile=TESTING_PROFILE)
        records = replace(
            template["records"],
            claims={},
            assessments=(value,),
            runs={value.run: run_value(view, run.id)},
            source_assertions=(),
            verifications=(stored.verification_value(view.get(verification.id)),),
        )
        availability = replace(
            template["availability"],
            observations={address: (ByteObservation(digest=digest, location="corpus:scope"),)},
        )
        context = replace(
            template["context"],
            snapshot=LineageSnapshot(roots=(address,), bases={}, producers={}),
            node_corpus={value.identity(): ("c1",)},
        )
        return evaluate(
            proposition=predecessor.id,
            records=records,
            availability=availability,
            context=context,
            retractions=RetractionEnumeration(found=(), coverage=("c1",)),
            binding=template["binding"],
            profile=template["profile"],
        )

    belief_before = predecessor_belief()
    assert isinstance(belief_before, Belief)

    successor = durable_writer.supersede(
        stored.proposition_node(
            "in-all-humans",
            title="in all humans",
            claim={"operator": "affects", "qualifiers": {"population": "all-humans"}},
        ),
        of=predecessor.id,
    )

    assert stored.stored_semantic_hash(successor) != stored.stored_semantic_hash(predecessor)
    assert durable_writer.read_view.get(predecessor.id).model_dump(mode="json") == before
    assert durable_writer.read_view.get(assessment.id).relations[0].target == predecessor.id
    assert predecessor_belief() == belief_before
    assert successor.relations == [
        stored.Relation(source=successor.id, predicate=stored.SUPERSEDES, target=predecessor.id)
    ]


def test_restamped_semantic_edit_is_imported(durable_writer):
    record = proposition("restamped")
    record.facets[stored.PROPOSITION_FACET]["operator"] = "causes"
    stored.stamp_semantic_identity(record)

    _import(durable_writer, (record,))

    assert durable_writer.read_view.get(record.id) == record


def test_foreign_act_report_is_attributed_inert_and_structurally_validated(durable_writer):
    foreign = stored.act_report_node(
        _mint_report(
            operation="import",
            event_token="foreign-valid",
            actor="elsewhere",
            observer="other-corpus",
            instrument="other-tool",
            opened_at="T-2",
            closed_at="T-1",
            entries=(
                RecordImportEntry(
                    subject="other",
                    outcome=ImportedRecords(refs=("note:not-minted",), findings=()),
                ),
            ),
        )
    )

    _import(durable_writer, (foreign,))

    held = durable_writer.read_view.get(foreign.id)
    assert held == foreign
    assert held.facets["act-report"]["actor"] == "elsewhere"
    assert "validated" not in held.facets["act-report"]
    assert not durable_writer.read_view.holds("note:not-minted")

    original = stored.act_report_node(
        _mint_report(
            operation="import",
            event_token="foreign-malformed",
            actor="elsewhere",
            observer="other-corpus",
            instrument="other-tool",
            opened_at="T-2",
            closed_at="T-1",
            entries=(),
        )
    )
    facets = deepcopy(original.facets)
    facets["act-report"]["entries"] = [{"kind": "made-up"}]
    malformed = stored.stamp_semantic_identity(original.model_copy(update={"facets": facets}))

    with pytest.raises(ImportRefused):
        _import(durable_writer, (malformed,))
    assert not durable_writer.read_view.holds(malformed.id)


def test_post_intent_refusal_writes_one_fulfilling_report_and_no_payload(durable_writer, durable_root):
    durable_writer.add(proposition("held"))
    before = chain_entries(durable_root)

    with pytest.raises(BundleMemberHeld) as refused:
        _import(durable_writer, (proposition("held"), proposition("not-written")))

    added = chain_entries(durable_root)[len(before) :]
    assert tuple(type(entry) for _, entry in added) == (IntentEntry, RegisteredEntry, SettledEntry)
    intent_digest, _ = added[0]
    registration_digest, registration = added[1]
    _, settlement = added[2]
    assert registration.fulfills == intent_digest
    assert settlement.registration == registration_digest
    assert settlement.outcome is ChainOutcome.COMMITTED
    assert refused.value.report_ref is not None
    assert not durable_writer.read_view.holds("proposition:not-written")


def test_intent_append_failure_begins_no_act(durable_writer, durable_root, monkeypatch):
    class IntentFailure(RuntimeError):
        pass

    port = durable_writer._operation_port
    assert port is not None

    def fail(_self, _payload):
        raise IntentFailure

    monkeypatch.setattr(type(port), "append_intent", fail)
    before = chain_entries(durable_root)

    with pytest.raises(IntentFailure):
        _import(durable_writer, (proposition("no-act"),))

    assert chain_entries(durable_root) == before
    assert not durable_writer.read_view.holds("proposition:no-act")


def test_import_consumes_a_forced_cycle_verdict(durable_writer, monkeypatch):
    monkeypatch.setattr(
        CorpusWriter,
        "_import_cycle_edges",
        lambda _self, _records: (("retraction:a", "retraction:b"),),
    )

    with pytest.raises(ImportRefused) as refused:
        _import(durable_writer, (proposition("forced-cycle"),))

    assert refused.value.cycle_edges == (("retraction:a", "retraction:b"),)
    assert not durable_writer.read_view.holds("proposition:forced-cycle")


def test_retraction_subtraction_is_direction_free(durable_writer):
    from test_belief import scenario

    support_node, refute_node = _mint_assessment_pair(durable_writer)
    kwargs = scenario()
    support, refute = kwargs["records"].assessments
    refute = replace(refute, outcome="refuted")
    pass_support, pass_refute = kwargs["records"].verifications
    pass_refute = replace(pass_refute, assessment=refute.identity())
    records = replace(
        kwargs["records"],
        assessments=(support, refute),
        verifications=(pass_support, pass_refute),
    )
    context = replace(
        kwargs["context"],
        node_corpus={support.identity(): ("c1",), refute.identity(): ("c1",)},
    )
    node_for = {support.identity(): support_node, refute.identity(): refute_node}

    def current_belief():
        assessments = tuple(
            assessment
            for assessment in records.assessments
            if standing_in_local_view(durable_writer.read_view, node_for[assessment.identity()].id)
        )
        return evaluate(
            **{
                **kwargs,
                "records": replace(records, assessments=assessments),
                "context": context,
            }
        )

    baseline = current_belief()
    assert isinstance(baseline, Belief) and baseline.value == 0

    support_retraction = durable_writer.retract(_retraction(support_node, "remove-support"))
    without_support = current_belief()
    assert isinstance(without_support, Belief) and without_support.value == -1

    durable_writer.retract(_retraction(support_retraction, "restore-support"))
    assert current_belief() == baseline

    durable_writer.retract(_retraction(refute_node, "remove-refute"))
    without_refute = current_belief()
    assert isinstance(without_refute, Belief) and without_refute.value == 1


def test_retraction_chain_restores_admission_with_distinct_digests(durable_writer):
    node = durable_writer.add(
        stored.verification_node(
            "chain-pass",
            title="chain pass",
            assessment="assessment:chain",
            assessment_ref="assessment:chain",
            scope="clean-environment",
            verdict="passed",
        )
    )
    value = Verification(node.id, "assessment:chain", "clean-environment", "passed")
    assert lifecycle_state((value,)) == ADMITTED
    initial_digest = _closure_digest(())

    first = durable_writer.retract(_retraction(node, "chain-first"))
    assert not standing_in_local_view(durable_writer.read_view, node.id)
    assert lifecycle_state(()) == NOT_ADMITTED
    subtracted_digest = _closure_digest(((first.id, "standing"),))

    counter = durable_writer.retract(_retraction(first, "chain-counter"))
    assert standing_in_local_view(durable_writer.read_view, node.id)
    assert lifecycle_state((value,)) == ADMITTED
    restored_digest = _closure_digest(((first.id, "overturned"), (counter.id, "standing")))

    assert len({initial_digest, subtracted_digest, restored_digest}) == 3


def test_verification_retractions_recompute_admission_and_belief(durable_writer):
    from test_belief import scenario

    kwargs = scenario()
    first_assessment, affected = kwargs["records"].assessments
    first_pass = kwargs["records"].verifications[0]
    passing_node = durable_writer.add(
        stored.verification_node(
            "standing-pass",
            title="standing pass",
            assessment=affected.identity(),
            assessment_ref="assessment:affected",
            scope="clean-environment",
            verdict="passed",
        )
    )
    failing_node = durable_writer.add(
        stored.verification_node(
            "standing-fail",
            title="standing fail",
            assessment=affected.identity(),
            assessment_ref="assessment:affected",
            scope="clean-environment",
            verdict="failed",
        )
    )
    passing = Verification(passing_node.id, affected.identity(), "clean-environment", "passed")
    failing = Verification(failing_node.id, affected.identity(), "clean-environment", "failed")
    all_values = (first_pass, passing, failing)
    node_for = {passing.ref: passing_node, failing.ref: failing_node}

    def current_values():
        return tuple(
            value
            for value in all_values
            if value is first_pass or standing_in_local_view(durable_writer.read_view, node_for[value.ref].id)
        )

    def current_belief():
        return evaluate(**{**kwargs, "records": replace(kwargs["records"], verifications=current_values())})

    assert lifecycle_state((passing, failing)) == INVALIDATED
    invalidated = current_belief()
    assert isinstance(invalidated, Belief) and invalidated.value == 1

    durable_writer.retract(_retraction(failing_node, "clear-failure"))
    assert lifecycle_state(tuple(v for v in current_values() if v.assessment == affected.identity())) == ADMITTED
    restored = current_belief()
    assert isinstance(restored, Belief) and restored.value == 2
    assert restored.belief_input_digest != invalidated.belief_input_digest

    durable_writer.retract(_retraction(passing_node, "remove-pass"))
    assert lifecycle_state(tuple(v for v in current_values() if v.assessment == affected.identity())) == NOT_ADMITTED
    deadmitted = current_belief()
    assert isinstance(deadmitted, Belief) and deadmitted.value == 1
    assert first_assessment in kwargs["records"].assessments


@pytest.mark.parametrize("kind", ["note", "proposition", "run"])
def test_ineligible_node_target_kinds_refuse(durable_writer, kind):
    if kind == "note":
        target = Node(
            id="note:target",
            kind="note",
            title="target",
        )
    elif kind == "proposition":
        target = stored.proposition_node("target", title="target", claim={"operator": "affects"})
    else:
        target = stored.run_node("target", title="target", spec="analysis-spec:target")
    if kind != "note":  # a note enters through the coordination family door, not the writer
        durable_writer.add(target)
    content_identity = stored.stored_semantic_hash(target) or "sha256:" + "cd" * 32
    record = stored.retraction_node(
        title=f"ineligible {kind}",
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the target kind is ineligible",
        grounds=("source:test",),
        actor="test-actor",
        event_token=f"ineligible-{kind}",
    )

    with pytest.raises(RetractionTargetIneligible):
        durable_writer.retract(record)
    assert not durable_writer.read_view.holds(record.id)
