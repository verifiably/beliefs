"""N2 over Cut 5's 28 selected family-adapter arms."""

from __future__ import annotations

import ast
import inspect
import textwrap
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace

import pytest
from atoms.chain.model import ChainOutcome, IntentEntry, RegisteredEntry, SettledEntry
from n2_arms import (
    CLASS_NODE_BY_CONSTRUCTION,
    MIXED_BY_CONSTRUCTION,
    STALE_BY_CONSTRUCTION,
    UNCOLLECTED_BY_CONSTRUCTION,
    VACUOUS_BY_CONSTRUCTION,
    Arm,
)
from n2_arms_cut5 import CUT5_ARMS
from nodes.core.node import Node
from test_durable_families import chain_entries, proposition
from test_n2 import MalformedArm, audit, baseline

from beliefs import stored
from beliefs.belief import Belief, evaluate
from beliefs.closure import RetractionEnumeration, build_closure
from beliefs.corpus import CorpusWriter, _cycle_edges, run_value, standing_in_local_view
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.errors import BundleMemberHeld, ImportRefused, MalformedRecord, RetractionTargetIneligible
from beliefs.lineage import LineageSnapshot
from beliefs.report import ImportedRecords, RecordImportEntry, _mint_report
from beliefs.verification import ADMITTED, INVALIDATED, NOT_ADMITTED, Verification, lifecycle_state

WORKERS = 8


def _import(writer: CorpusWriter, records):
    return writer.import_bundle(
        records,
        actor="cut5",
        observer="corpus",
        instrument="n2",
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
        grounds=("source:cut5",),
        actor="cut5",
        event_token=event,
    )


def _closure_digest(found: tuple[tuple[str, str], ...]) -> str:
    from test_closure import closure_kwargs

    kwargs = closure_kwargs()
    kwargs["retractions"] = RetractionEnumeration(found=found, coverage=("local",))
    return build_closure(**kwargs).digest()


def test_semantic_change_branch_names_no_rename_path():
    tree = ast.parse(textwrap.dedent(inspect.getsource(CorpusWriter.supersede)))
    assert "rename" not in {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }


def test_scope_supersession_preserves_predecessor_evidence(durable_writer):
    from test_belief import scenario

    observed = durable_writer.add(
        stored.dataset_node(
            "scope-observed",
            title="scope observed",
            resources=[{"name": "data", "digest": "sha256:" + "a1" * 32}],
            empirical_observation={"boundary": "instrument"},
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
        )
    )
    assessment_value = stored.assessment_value(assessment)
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
        value = stored.assessment_value(view.get(assessment.id))
        records = replace(
            template["records"],
            claims={},
            assessments=(value,),
            runs={stored.local_id("run", run.id): run_value(view, run.id)},
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
            node_corpus={value.identity(): "c1"},
        )
        return evaluate(
            proposition=predecessor.id,
            records=records,
            availability=availability,
            context=context,
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


def test_cycle_validator_returns_the_offending_edges():
    assert _cycle_edges({"retraction:a": ("retraction:b",), "retraction:b": ("retraction:a",)}) == (
        ("retraction:a", "retraction:b"),
        ("retraction:b", "retraction:a"),
    )


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


@pytest.mark.parametrize("field", ["reason", "rationale", "grounds", "actor", "event_token"])
def test_retraction_required_fields_refuse_when_empty(field):
    values = {
        "title": "required",
        "target": stored.NodeTarget("assessment:a", "assessment:a", "sha256:" + "ab" * 32),
        "reason": "defective-code",
        "rationale": "invalid result",
        "grounds": ("verification:v",),
        "actor": "cut5",
        "event_token": "required",
    }
    values[field] = () if field == "grounds" else ""

    with pytest.raises(MalformedRecord):
        stored.retraction_node(**values)


def test_retraction_enumeration_moves_only_when_in_closure():
    baseline = _closure_digest(())
    inside = _closure_digest((("retraction:inside", "standing"),))
    outside = _closure_digest(())

    assert inside != baseline
    assert outside == baseline


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
                f"direction-{slug}",
                title=slug,
                resources=[{"name": "data", "digest": "sha256:" + digest * 32}],
                empirical_observation={"boundary": "instrument"},
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
                )
            )
        )
    return tuple(found)


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
        node_corpus={support.identity(): "c1", refute.identity(): "c1"},
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
            if value is first_pass
            or standing_in_local_view(durable_writer.read_view, node_for[value.ref].id)
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
    durable_writer.add(target)
    content_identity = stored.stored_semantic_hash(target) or "sha256:" + "cd" * 32
    record = stored.retraction_node(
        title=f"ineligible {kind}",
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the target kind is ineligible",
        grounds=("source:cut5",),
        actor="cut5",
        event_token=f"ineligible-{kind}",
    )

    with pytest.raises(RetractionTargetIneligible):
        durable_writer.retract(record)
    assert not durable_writer.read_view.holds(record.id)


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    root = tmp_path_factory.mktemp("n2-cut5")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(CUT5_ARMS))
        )


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason + "\n" + "\n".join(f"  {finding.arm.label}\n    {finding.detail}" for finding in offending)
        )


class TestEveryCut5ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-5 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-5 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-5 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-5 sabotages no longer match exactly once:", findings, "stale")

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        for arm in CUT5_ARMS:
            for check in arm.checks:
                assert check.split("::")[-1].startswith("test_"), f"{arm.label}: {check}"
                assert len(check.split("::")) >= 2, f"{arm.label}: {check}"

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-5 check resolves and passes against the real package",
            sabotage=CUT5_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT5_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


class TestTheCut5InventoryIsExact:
    def test_exactly_one_declaration_exists_per_selected_bullet(self):
        assert len(CUT5_ARMS) == 28

    def test_declarations_match_the_selected_row_histogram(self):
        assert Counter(arm.row for arm in CUT5_ARMS) == {
            "S2": 1,
            "S4": 1,
            "G7": 3,
            "M5": 1,
            "S3": 2,
            "T1": 1,
            "T2": 3,
            "M3": 4,
            "R20": 1,
            "C1": 1,
            "C2": 1,
            "C3": 1,
            "C4": 1,
            "C5": 2,
            "C6": 1,
            "C10": 2,
            "G2c": 1,
            "G8": 1,
        }

    def test_deferred_semantic_import_rows_are_absent(self):
        assert not {"R19", "R22", "R23"} & {arm.row for arm in CUT5_ARMS}


@pytest.mark.parametrize(
    ("arm", "verdict"),
    [
        (VACUOUS_BY_CONSTRUCTION, "vacuous"),
        (MIXED_BY_CONSTRUCTION, "mixed"),
        (UNCOLLECTED_BY_CONSTRUCTION, "uncollected"),
        (STALE_BY_CONSTRUCTION, "stale"),
    ],
)
def test_the_harness_preserves_each_malformed_verdict(tmp_path, arm, verdict):
    assert audit(arm, tmp_path / verdict).verdict == verdict


def test_the_harness_rejects_a_class_node(tmp_path):
    with pytest.raises(MalformedArm, match="one test function"):
        audit(CLASS_NODE_BY_CONSTRUCTION, tmp_path / "class-node")
