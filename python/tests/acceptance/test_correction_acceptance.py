"""Cut 33: correction standing through the certified durable boundary."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import pytest
from authority import ACTOR, FULL
from dataset_fixtures import dataset_ref, pinned
from domain_facet_fixtures import kwargs_for, over_kwargs
from fixtures_cut3 import typed_applicability, typed_estimand
from fixtures_cut4 import path_for, raw_write
from nodes.core.errors import RefError
from nodes.core.node import Node
from profiles import pins_for
from test_evaluation import CLAIM_FACET
from test_local_standing import retracts
from test_relocation import MOVE_FIELDS
from test_standing_read import TestTheAmendedG8Clause as _G8
from test_standing_read import verification_for
from test_world_receipts import hold_shipped, publish
from test_world_view_acceptance import durable_world as durable_world  # noqa: PLC0414 - register the shared fixture
from test_world_view_acceptance import evaluation_world, world_kwargs

from beliefs import stored
from beliefs.admission import AdmissionRefused, Admitted
from beliefs.audit import NO_EVIDENCE, audit_corpus, audit_world
from beliefs.belief import Belief
from beliefs.closure import RETRACTION_UPHELD, RetractionEnumeration
from beliefs.corpus import ReadView, lineage_snapshot, local_retraction_enumeration
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.errors import RetractionResolutionDisagreement, RetractionUnreadable
from beliefs.evaluation import evaluate_over, gather
from beliefs.lineage import certify
from beliefs.relocation import move
from beliefs.root import open_corpus
from beliefs.verification import ADMITTED, INVALIDATED, NOT_ADMITTED
from beliefs.world.view import open_world_view


def _seed(writer, *, conflict=False, outcomes=("supported", "refuted")):
    writer.adopt_manifest(profile=pins_for(writer.profile))
    basis = None
    if conflict:
        ancestors = [
            writer.add(
                stored.dataset_node(
                    title=name,
                    resources=pinned(name),
                    empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
                )
            )
            for name in ("one", "two")
        ]
        writer.add(stored.run_node("ancestor", title="ancestor", spec="ancestor"))
        basis = {
            "tag": "conflict",
            "routes": [
                {
                    "identity": f"route:{name}",
                    "run": "run:ancestor",
                    "ancestor": ancestor.id,
                    "transforms": [ancestor.id],
                }
                for name, ancestor in zip(("one", "two"), ancestors, strict=True)
            ],
        }
    writer.add(stored.proposition_node("p", title="p", claim=CLAIM_FACET))
    for index, (side, outcome) in enumerate(zip(("a", "b"), outcomes, strict=True), start=1):
        dataset = writer.add(
            stored.dataset_node(
                title=f"d-{side}",
                resources=pinned(f"d-{side}"),
                empirical_observation=None
                if conflict and side == "a"
                else {"locator": "instrument:fixture", "attested_by": ACTOR},
                basis=basis if side == "a" else None,
            )
        )
        run = writer.add(
            stored.run_node(
                f"run-{side}",
                title=side,
                spec=f"spec-{side}",
                observes=[dataset.id, dataset_ref("one")] if conflict and side == "a" else [dataset.id],
            )
        )
        assessment = writer.add(
            stored.assessment_node(
                f"a-{index}",
                title=side,
                spec=f"spec-{side}",
                run=run.id,
                proposition="proposition:p",
                outcome=outcome,
                interpretation_rule="rule-1",
                estimand=typed_estimand(),
                applicability=typed_applicability(),
            )
        )
        writer.add(verification_for(assessment, scope="clean-environment", verdict="passed", slug=f"v-{index}"))
    return writer


def _read(writer):
    view = ReadView.opened_at(writer.root)
    kwargs = over_kwargs(kwargs_for(view, writer.profile))
    if view.holds(dataset_ref("one")):
        kwargs["context"] = replace(
            kwargs["context"],
            snapshot=lineage_snapshot(view, (dataset_ref("d-a"), dataset_ref("d-b"), dataset_ref("one"))),
        )
        kwargs["availability"] = replace(
            kwargs["availability"],
            observations={
                **kwargs["availability"].observations,
                dataset_ref("one"): (ByteObservation(digest=pinned("one")[0]["digest"], location="repo://data"),),
            },
        )
    inputs = gather(view, "proposition:p", **{k: v for k, v in kwargs.items() if k != "availability"})
    answer = evaluate_over(view, "proposition:p", **kwargs)
    return inputs, answer


def _route(writer, name, ref):
    node = writer.read_view.get(ref)
    identity = stored.stored_semantic_hash(node)
    assert identity is not None
    return stored.retraction_node(
        title=name,
        target=stored.RouteTarget(node.id, node.id, identity, f"route:{name}"),
        reason="wrong-route",
        rationale="wrong ancestry",
        grounds=("verification:v-1",),
        actor=ACTOR,
        event_token=name,
    )


def test_c7a_retiring_one_conflicting_route_certifies_over_the_survivor(durable_writer):
    writer = _seed(durable_writer, conflict=True, outcomes=("supported", "supported"))
    before, answer = _read(writer)
    roots = ((dataset_ref("d-a"), dataset_ref("one")), (dataset_ref("d-b"),))
    observed = {
        run.spec: {dataset_address(entry.dataset) for entry in run.inputs if entry.role == "observes"}
        for run in before.runs.values()
    }
    assert observed == {"spec-a": set(roots[0]), "spec-b": set(roots[1])}
    assert certify(before.snapshot, *roots).state == "not-certified"
    assert isinstance(answer, Belief) and answer.value == 1
    writer.retract(_route(writer, "one", dataset_ref("d-a")))
    after, answer = _read(writer)
    assert after.runs == before.runs
    lineage = cast(dict[str, Any], after.closure().projection["lineage"])
    assert lineage["divergence"][dataset_ref("d-a")] == "undiverged"
    assert lineage["bases"][dataset_ref("d-a")]["retired"] == ["route:one"]
    assert certify(after.snapshot, *roots).state == "independent"
    assert isinstance(answer, Belief) and answer.value == 2
    assert after.closure().digest() == answer.belief_input_digest


def test_c7b_retiring_every_route_is_not_certified_with_lineage_incomplete(durable_writer):
    writer = _seed(durable_writer, conflict=True)
    for name in ("one", "two"):
        writer.retract(_route(writer, name, dataset_ref("d-a")))
    inputs, _answer = _read(writer)
    certification = certify(inputs.snapshot, (dataset_ref("d-a"),), (dataset_ref("d-b"),))
    assert certification.state == "not-certified"
    assert certification.findings == ("lineage-incomplete",)


def test_c7c_the_stored_basis_is_byte_unchanged_and_retract_writes_one_record(durable_writer):
    writer = _seed(durable_writer, conflict=True)
    ref = dataset_ref("d-a")
    original = path_for(writer.root, ref).read_bytes()
    identity = stored.stored_semantic_hash(writer.read_view.get(ref))
    for name in ("one", "two"):
        count = len(tuple(writer.read_view.iter_stored()))
        writer.retract(_route(writer, name, dataset_ref("d-a")))
        assert path_for(writer.root, ref).read_bytes() == original
        assert stored.stored_semantic_hash(ReadView.opened_at(writer.root).get(ref)) == identity
        assert len(tuple(writer.read_view.iter_stored())) == count + 1


def _world(durable_world):
    world, roots, epoch, a, b, profile = evaluation_world(durable_world, beta_refs=())
    return (
        world,
        roots,
        epoch,
        a,
        b,
        profile,
        tuple(open_corpus(roots[c], authority=FULL, profile=profile) for c in (a, b)),
    )


def _world_read(world, epoch, a, b, profile, proposition="proposition:p"):
    view = open_world_view(world, epoch)
    kwargs = world_kwargs(view, profile, a, b)
    return view, gather(view, proposition, **{k: kwargs[k] for k in ("context", "profile", "resolution", "binding")})


def test_c3a_an_uncovered_retraction_moves_nothing_and_coverage_is_a_digest_member(durable_world):
    world, _roots, _epoch, a, b, profile, (alpha, beta) = _world(durable_world)
    baseline_epoch = publish(world, (a,), hold_shipped(world))
    _, before = _world_read(world, baseline_epoch, a, b, profile)
    widened_only = replace(before, retractions=replace(before.retractions, coverage=(*before.retractions.coverage, b)))
    assert before.closure().digest() != widened_only.closure().digest()
    retraction = alpha.retract(retracts(alpha.read_view.get("assessment:a-1"), "uncovered"))
    move(alpha, beta, retraction.id, **MOVE_FIELDS)
    narrow = publish(world, (a,), hold_shipped(world))
    _, inputs = _world_read(world, narrow, a, b, profile)
    assert inputs.retractions == RetractionEnumeration(found=(), coverage=(a,))
    assert len(inputs.assessments) == 2 and inputs.closure().digest() == before.closure().digest()
    wide = publish(world, (a, b), hold_shipped(world))
    _, inputs = _world_read(world, wide, a, b, profile)
    assert inputs.retractions.found == ((retraction.id, RETRACTION_UPHELD),)
    assert len(inputs.assessments) == 1


def test_c3b_an_in_coverage_move_leaves_the_digest_and_moves_the_receipts(durable_world):
    world, _roots, _epoch, a, b, profile, (alpha, beta) = _world(durable_world)
    target = alpha.read_view.get("assessment:a-1")
    alpha.retract(retracts(target, "standing"))
    for ref in (dataset_ref("d-a"), "run:run-a", "proposition:p"):
        move(alpha, beta, ref, **MOVE_FIELDS)
    first = publish(world, (a, b), hold_shipped(world))
    _, before = _world_read(world, first, a, b, profile)
    move(alpha, beta, target.id, **MOVE_FIELDS)
    second = publish(world, (a, b), hold_shipped(world))
    _, after = _world_read(world, second, a, b, profile)
    assert after.producer_snapshot_identity == before.producer_snapshot_identity
    assert after.snapshot == before.snapshot and after.consulted == before.consulted
    assert after.closure().digest() == before.closure().digest()
    assert dict(second.coverage) != dict(first.coverage)


def test_c10a_raw_written_refused_shapes_are_reported_by_both_audits(durable_world):
    world, roots, _epoch, a, b, profile, (alpha, _beta) = _world(durable_world)
    note = Node(id="note:ineligible", kind="note", title="ineligible")
    raw_write(roots[a], note)
    targets = (alpha.read_view.get("proposition:p"), alpha.read_view.get("run:run-a"))
    invalid = [retracts(n, n.kind) for n in targets]
    invalid.append(
        stored.retraction_node(
            title="note",
            target=stored.NodeTarget(note.id, note.id, "sha256:" + "ab" * 32),
            reason="defective-code",
            rationale="invalid kind",
            grounds=("verification:v-1",),
            actor=ACTOR,
            event_token="note",
        )
    )
    derived = alpha.add(
        stored.dataset_node(
            title="derived-audit",
            resources=pinned("derived-audit"),
            basis={
                "tag": "single",
                "routes": [
                    {
                        "identity": "route:present",
                        "run": "run:run-a",
                        "ancestor": dataset_ref("d-a"),
                        "transforms": [dataset_ref("d-a")],
                    }
                ],
            },
        )
    )
    invalid.append(_route(alpha, "absent", derived.id))
    for node in invalid:
        raw_write(roots[a], node)
    epoch = publish(world, (a, b), hold_shipped(world))
    local = audit_corpus(ReadView.opened_at(roots[a]), evidence=NO_EVIDENCE, profile=profile)
    global_findings = audit_world(world, epoch, evidence=NO_EVIDENCE, profile=profile).corpora[a]
    for findings in (local, global_findings):
        assert {n.id for n in invalid} <= {f.ref for f in findings if f.code == "retraction-target-invalid"}


def test_bi1_node_standing_subtracts_at_the_read(durable_writer):
    writer = _seed(durable_writer)
    before, answer_before = _read(writer)
    retraction = writer.retract(retracts(writer.read_view.get("assessment:a-1"), "subtract"))
    after, answer_after = _read(writer)
    assert isinstance(answer_before, Belief) and isinstance(answer_after, Belief)
    assert answer_before.value == 0 and answer_after.value == -1
    assert len(after.assessments) == len(before.assessments) - 1
    assert after.retractions.found == ((retraction.id, RETRACTION_UPHELD),)
    assert after.closure().digest() == answer_after.belief_input_digest


def test_bi2_a_retracted_verification_leaves_the_read_set(durable_writer):
    writer = _seed(durable_writer)
    target = writer.read_view.get("assessment:a-1")
    failing = writer.add(verification_for(target, scope="clean-environment", verdict="failed", slug="failure"))
    gate = _G8()._gate
    admission, state, answer = gate(writer, writer.profile)
    assert isinstance(admission, AdmissionRefused) and state == INVALIDATED and answer.value == -1
    writer.retract(retracts(failing, "false-failure"))
    admission, state, answer = gate(writer, writer.profile)
    assert isinstance(admission, Admitted) and state == ADMITTED and answer.value == 0
    writer.retract(retracts(writer.read_view.get("verification:v-1"), "false-pass"))
    admission, state, answer = gate(writer, writer.profile)
    assert isinstance(admission, AdmissionRefused) and state == NOT_ADMITTED and answer.value == -1
    failing = writer.add(verification_for(target, scope="clean-environment", verdict="failed", slug="failure-two"))
    resolution = writer.add(
        verification_for(target, scope="clean-environment", verdict="passed", slug="resolution", supersedes=failing.id)
    )
    admission, state, answer = gate(writer, writer.profile)
    assert isinstance(admission, Admitted) and state == ADMITTED and answer.value == 0
    writer.retract(retracts(resolution, "false-resolution"))
    admission, state, answer = gate(writer, writer.profile)
    assert isinstance(admission, AdmissionRefused) and state == INVALIDATED and answer.value == -1


def test_bi3_the_enumeration_is_the_views_and_input_scoped(durable_world):
    world, _roots, _epoch, a, b, profile, (alpha, _beta) = _world(durable_world)
    alpha.add(stored.proposition_node("q", title="q", claim=CLAIM_FACET))
    other = alpha.add(
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
    unrelated = alpha.retract(retracts(other, "unrelated"))
    first = publish(world, (a, b), hold_shipped(world))
    _, before = _world_read(world, first, a, b, profile, "proposition:q")
    relevant = alpha.retract(retracts(alpha.read_view.get("assessment:a-1"), "relevant"))
    second = publish(world, (a, b), hold_shipped(world))
    view, inputs = _world_read(world, second, a, b, profile)
    assert set(dict(view.retraction_enumeration().found)) == {relevant.id, unrelated.id}
    assert inputs.retractions.found == ((relevant.id, RETRACTION_UPHELD),)
    assert dict(inputs.retractions.found)[relevant.id] == dict(view.retraction_enumeration().found)[relevant.id]
    _, after = _world_read(world, second, a, b, profile, "proposition:q")
    assert before.closure().digest() == after.closure().digest()
    with pytest.raises(TypeError):
        replace(world_kwargs(view, profile, a, b)["context"], retractions=inputs.retractions)


def test_bi4_an_unreadable_found_retraction_refuses(durable_writer):
    writer = _seed(durable_writer)
    target = writer.read_view.get("assessment:a-1")
    for shape in ("stale-target", "wrong-identity", "stale-stamp"):
        node = retracts(target, shape)
        if shape == "stale-target":
            node.facets[stored.RETRACTION_FACET]["target"].update(ref="assessment:gone", resolved="assessment:gone")
        elif shape == "wrong-identity":
            node.facets[stored.RETRACTION_FACET]["target"]["content_identity"] = "sha256:" + "ab" * 32
        node = stored.stamp_semantic_identity(node)
        if shape == "stale-stamp":
            node.facets[stored.RETRACTION_FACET]["rationale"] = "changed after stamping"
        raw_write(writer.root, node)
        with pytest.raises(RetractionUnreadable) as refused:
            _read(writer)
        assert refused.value.ref == node.id
        path_for(writer.root, node.id).unlink()
    # Enumeration scans disk, while this previously opened view retains its index.
    # The found ref is unreadable specifically at gather's lookup boundary.
    view = ReadView.opened_at(writer.root)
    kwargs = kwargs_for(view, writer.profile)
    node = retracts(target, "unindexed")
    raw_write(writer.root, node)
    assert (node.id, RETRACTION_UPHELD) in local_retraction_enumeration(view).found
    with pytest.raises(RetractionUnreadable) as refused:
        gather(view, "proposition:p", **{k: kwargs[k] for k in ("context", "profile", "resolution", "binding")})
    assert refused.value.ref == node.id and isinstance(refused.value.__cause__, RefError)
    assert refused.value.cause == str(refused.value.__cause__)


def test_bi5_a_resolution_disagreement_refuses(durable_world):
    world, _roots, _epoch, a, b, profile, (alpha, beta) = _world(durable_world)
    first = alpha.retract(retracts(alpha.read_view.get("assessment:a-1"), "first"))
    counter = alpha.retract(retracts(first, "counter"))
    together = publish(world, (a, b), hold_shipped(world))
    _, inputs = _world_read(world, together, a, b, profile)
    assert dict(inputs.retractions.found)[first.id] == "overturned"
    move(alpha, beta, counter.id, **MOVE_FIELDS)
    split = publish(world, (a, b), hold_shipped(world))
    assert dict(open_world_view(world, split).retraction_enumeration().found)[first.id] == "upheld"
    with pytest.raises(RetractionResolutionDisagreement) as refused:
        _world_read(world, split, a, b, profile)
    assert refused.value.ref == first.id
