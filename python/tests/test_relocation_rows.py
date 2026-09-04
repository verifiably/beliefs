"""Frozen cut-16 row evidence for the public ``move`` operation."""

from __future__ import annotations

from dataclasses import replace

import pytest
import yaml
from fixtures_cut3 import report as sample_report
from fixtures_cut6 import PINS
from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.relations import Relation
from test_belief import scenario as belief_scenario
from test_corpus_write import OperationRecorder
from test_relocation import CONSOLIDATE_FIELDS, MOVE_FIELDS, _node, _writer
from test_world_epoch import derivation_bindings, make_world, publish

from beliefs import relocation, stored
from beliefs.belief import Belief, evaluate
from beliefs.errors import (
    ContractPinDisagreement,
    RelocationKindExcluded,
    RelocationTargetMissing,
)
from beliefs.identity import v1
from beliefs.world import derive, registry


def _world_for(tmp_path, *writers):
    world, _ = make_world(tmp_path, *(writer.root for writer in writers))
    for writer in writers:
        world.admit(writer.root, provenance=registry.Fresh(), actor="alice")
    return world, tuple(writer.corpus_id for writer in writers), derivation_bindings(world)


def _belief_digest(published):
    snapshot = derive.producer_snapshot(
        yaml.safe_load(published.members["producer-snapshot.yaml"])
    )
    assert yaml.safe_load(published.members["producers-map.yaml"]) == (
        derive.producers_map_projection(snapshot.producers)
    )
    assert (
        published.receipts["producer-receipt.yaml"].subject_identity
        == snapshot.identity()
    )
    ordinary = belief_scenario()
    result = evaluate(
        **{
            **ordinary,
            "context": replace(
                ordinary["context"],
                producer_snapshot_identity=snapshot.identity(),
            ),
        }
    )
    assert isinstance(result, Belief)
    return result.belief_input_digest


def _basis_route(name):
    return {
        "identity": f"route:{name}",
        "run": f"run:{name}",
        "ancestor": f"dataset:{name}",
        "transforms": [f"dataset:{name}"],
    }


def _duplicate_datasets(tmp_path):
    keep_writer = _writer(tmp_path / "keep", domains=PINS.domains)
    other_writer = _writer(tmp_path / "other", domains=PINS.domains)
    keep = stored.dataset_node(
        "duplicate",
        title="kept title",
        resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
        basis={"tag": "single", "routes": [_basis_route("z")]},
    ).model_copy(update={"deprecated_ids": ["dataset:old-a"]})
    keep.relations = [
        Relation(source=keep.id, predicate="derived-from", target="dataset:z"),
        Relation(
            source=keep.id,
            predicate="shared",
            target="dataset:shared",
            attrs={"authored": "keep"},
        ),
    ]
    other = stored.dataset_node(
        "duplicate",
        title="other title",
        resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
        basis={"tag": "single", "routes": [_basis_route("a")]},
    ).model_copy(update={"deprecated_ids": ["dataset:old-b"]})
    other.relations = [
        Relation(source=other.id, predicate="derived-from", target="dataset:a"),
        Relation(
            source=other.id,
            predicate="shared",
            target="dataset:shared",
            attrs={"authored": "other"},
        ),
    ]
    return keep_writer, other_writer, keep_writer.add(keep), other_writer.add(other)


def _move_published_dataset(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(tmp_path / "destination", domains=PINS.domains)
    dataset = source.add(
        stored.dataset_node(
            "moved",
            title="moved",
            resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
        )
    )
    run = source.add(
        stored.run_node(
            "producer",
            title="producer",
            spec="analysis-spec:producer",
            produces=[dataset.id],
        )
    )
    world, coverage, bindings = _world_for(tmp_path, source, destination)
    before = publish(world, coverage, bindings)
    states_before = {
        writer.corpus_id: registry.corpus_state_identity(writer.root)
        for writer in (source, destination)
    }

    moved, destination_report, source_report = relocation.move(
        source, destination, dataset.id, **MOVE_FIELDS
    )

    after = publish(world, coverage, bindings)
    states_after = {
        writer.corpus_id: registry.corpus_state_identity(writer.root)
        for writer in (source, destination)
    }
    expected_producers = {dataset.id: (run.id,)}
    for published in (before, after):
        snapshot = derive.producer_snapshot(
            yaml.safe_load(published.members["producer-snapshot.yaml"])
        )
        assert dict(snapshot.producers) == expected_producers
        assert yaml.safe_load(published.members["producers-map.yaml"]) == {
            "producers": [{"dataset": dataset.id, "runs": [run.id]}]
        }
    return {
        "source": source,
        "destination": destination,
        "dataset": dataset,
        "run": run,
        "moved": moved,
        "destination_report": destination_report,
        "source_report": source_report,
        "before": before,
        "after": after,
        "states_before": states_before,
        "states_after": states_after,
    }


def test_w5_a_move_changes_only_location(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(tmp_path / "destination", domains=PINS.domains)
    node = stored.source_node("paper", title="paper", identifiers={"doi": "10.1/paper"})
    node = source.add(node.model_copy(update={"deprecated_ids": ["source:old-paper"]}))
    inbound = source.add(
        Node(
            id="memo:citation",
            kind="memo",
            title="citation",
            relations=[Relation(source="memo:citation", predicate="cites", target=node.id)],
        )
    )
    world, coverage, bindings = _world_for(tmp_path, source, destination)
    before = publish(world, coverage, bindings)
    before_inbound = source.read_view.get(inbound.id).relations

    moved, _, _ = relocation.move(source, destination, node.id, **MOVE_FIELDS)

    after = publish(world, coverage, bindings)
    assert (moved.uid, moved.id, moved.deprecated_ids) == (
        node.uid,
        node.id,
        node.deprecated_ids,
    )
    assert destination.read_view.get(node.id) == node
    with pytest.raises(RefError):
        source.read_view.get(node.id)
    assert source.read_view.get(inbound.id).relations == before_inbound
    assert before.members["address-map.yaml"] != after.members["address-map.yaml"]
    assert _belief_digest(before) == _belief_digest(after)


def test_w5_a_producers_map_member_moves_without_moving_the_digest(tmp_path):
    moved = _move_published_dataset(tmp_path)
    before, after = moved["before"], moved["after"]

    assert before.members["producers-map.yaml"] == after.members["producers-map.yaml"]
    assert moved["run"].id.encode() in before.members["producers-map.yaml"]
    assert before.members["address-map.yaml"] != after.members["address-map.yaml"]
    assert moved["states_before"] != moved["states_after"]
    assert all(
        moved["states_before"][corpus_id] != moved["states_after"][corpus_id]
        for corpus_id in moved["states_before"]
    )
    assert before.receipts["producer-receipt.yaml"].subject_identity == after.receipts[
        "producer-receipt.yaml"
    ].subject_identity
    assert before.receipts["producer-receipt.yaml"].identity != after.receipts[
        "producer-receipt.yaml"
    ].identity
    assert _belief_digest(before) == _belief_digest(after)


def test_g3_location_is_not_a_closure_member(tmp_path):
    moved = _move_published_dataset(tmp_path)
    assert moved["before"].members["address-map.yaml"] != moved["after"].members[
        "address-map.yaml"
    ]
    assert _belief_digest(moved["before"]) == _belief_digest(moved["after"])


def test_d7_a_permitted_move_preserves_w5(tmp_path):
    moved = _move_published_dataset(tmp_path)
    assert moved["source"].manifest_pins() == moved["destination"].manifest_pins() == PINS
    assert _belief_digest(moved["before"]) == _belief_digest(moved["after"])


def test_d7_move_refuses_a_domain_facet_across_identities(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(
        tmp_path / "destination",
        domains={"biology": "biology:" + "c" * 64},
    )
    node = source.add(_node("biology/gene-axis"))

    with pytest.raises(ContractPinDisagreement, match="biology"):
        relocation.move(source, destination, node.id, **MOVE_FIELDS)

    assert source.read_view.holds(node.id) and not destination.read_view.holds(node.id)


def test_d7_move_refuses_a_base_contract_for_a_facetless_node(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(
        tmp_path / "destination",
        science="science:" + "c" * 64,
        domains=PINS.domains,
    )
    node = source.add(
        stored.source_node("paper", title="paper", identifiers={"doi": "10.1/paper"})
    )

    with pytest.raises(ContractPinDisagreement, match="science contracts"):
        relocation.move(source, destination, node.id, **MOVE_FIELDS)

    assert source.read_view.holds(node.id) and not destination.read_view.holds(node.id)


def test_d7_move_refuses_a_missing_pin(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(tmp_path / "destination")
    node = source.add(_node("biology/gene-axis"))

    with pytest.raises(ContractPinDisagreement, match="biology"):
        relocation.move(source, destination, node.id, **MOVE_FIELDS)

    assert source.read_view.holds(node.id) and not destination.read_view.holds(node.id)


def test_c3_an_in_coverage_move_leaves_the_digest_and_moves_the_receipt(tmp_path):
    moved = _move_published_dataset(tmp_path)
    before, after = moved["before"], moved["after"]
    assert _belief_digest(before) == _belief_digest(after)
    assert before.receipts["producer-receipt.yaml"].corpus_states == tuple(
        sorted(moved["states_before"].items())
    )
    assert after.receipts["producer-receipt.yaml"].corpus_states == tuple(
        sorted(moved["states_after"].items())
    )


def test_r23_location_is_not_evidence(tmp_path):
    moved = _move_published_dataset(tmp_path)
    assert moved["before"].members["producers-map.yaml"] == moved["after"].members[
        "producers-map.yaml"
    ]
    assert moved["states_before"] != moved["states_after"]
    assert _belief_digest(moved["before"]) == _belief_digest(moved["after"])


def test_r23_the_receipt_is_not_a_belief_input(tmp_path):
    moved = _move_published_dataset(tmp_path)
    before_receipt = moved["before"].receipts["producer-receipt.yaml"]
    after_receipt = moved["after"].receipts["producer-receipt.yaml"]
    assert before_receipt.identity != after_receipt.identity
    assert before_receipt.subject_identity == after_receipt.subject_identity
    assert _belief_digest(moved["before"]) == _belief_digest(moved["after"])


def test_t2_a_move_is_one_intent_and_one_report_in_each_root(tmp_path):
    moved = _move_published_dataset(tmp_path)
    destination_report = moved["destination_report"]
    source_report = moved["source_report"]
    assert destination_report.event_token == source_report.event_token
    assert destination_report.opened_at == source_report.opened_at == MOVE_FIELDS["opened_at"]
    assert destination_report.closed_at == source_report.closed_at == MOVE_FIELDS["closed_at"]
    for writer, report in (
        (moved["destination"], destination_report),
        (moved["source"], source_report),
    ):
        port = writer._operation_port
        assert isinstance(port, OperationRecorder)
        assert len(port.intents) == len(port.fulfilling) == 1
        assert writer.read_view.holds(f"act-report:{report.identity()}")


def test_t8_move_refuses_an_act_report_subject(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(tmp_path / "destination", domains=PINS.domains)
    report = sample_report()
    source._publish_operation_report(report, "ab" * 32)
    source_port = source._operation_port
    assert isinstance(source_port, OperationRecorder)
    source_port.intents.clear()
    source_port.fulfilling.clear()

    with pytest.raises(RelocationKindExcluded, match="act-report"):
        relocation.move(
            source,
            destination,
            f"act-report:{report.identity()}",
            **MOVE_FIELDS,
        )

    assert source.read_view.holds(f"act-report:{report.identity()}")
    assert not destination.read_view.holds(f"act-report:{report.identity()}")
    assert source_port.intents == []


def test_consolidate_unions_relations_and_preserves_both_bases(tmp_path):
    keep_writer, other_writer, keep, other = _duplicate_datasets(tmp_path)
    inbound = keep_writer.add(
        Node(
            id="memo:inbound",
            kind="memo",
            title="inbound",
            relations=[
                Relation(source="memo:inbound", predicate="cites", target=keep.id)
            ],
        )
    )
    inbound_before = keep_writer.read_view.get(inbound.id)

    survivor, _, _ = relocation.consolidate(
        (keep_writer, keep.id),
        (other_writer, other.id),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == keep.id
    assert survivor.uid == keep.uid
    assert survivor.title == keep.title
    assert survivor.facets[stored.DATASET_FACET] == keep.facets[stored.DATASET_FACET]
    assert survivor.relations == [
        Relation(source=keep.id, predicate="derived-from", target="dataset:a"),
        Relation(source=keep.id, predicate="derived-from", target="dataset:z"),
        Relation(
            source=keep.id,
            predicate="shared",
            target="dataset:shared",
            attrs={"authored": "keep"},
        ),
    ]
    assert survivor.facets[stored.LINEAGE_BASIS_FACET] == {
        "tag": "conflict",
        "routes": [_basis_route("a"), _basis_route("z")],
    }
    assert survivor.deprecated_ids == ["dataset:old-a", "dataset:old-b"]
    assert keep.id not in survivor.deprecated_ids
    assert keep_writer.read_view.get(inbound.id) == inbound_before
    assert not any(
        node.kind == "coreference-attestation"
        for writer in (keep_writer, other_writer)
        for node in writer.read_view.iter_stored()
    )
    with pytest.raises(RefError):
        other_writer.read_view.get(other.id)


def test_d7_consolidate_refuses_a_domain_facet_across_identities(tmp_path):
    keep_writer = _writer(
        tmp_path / "domain" / "keep",
        domains={"biology": "biology:" + "c" * 64},
    )
    other_writer = _writer(tmp_path / "domain" / "other", domains=PINS.domains)
    keep = keep_writer.add(_node("biology/gene-axis"))
    other = other_writer.add(_node("biology/gene-axis"))

    with pytest.raises(ContractPinDisagreement, match="biology"):
        relocation.consolidate(
            (keep_writer, keep.id),
            (other_writer, other.id),
            **CONSOLIDATE_FIELDS,
        )


def test_d7_consolidate_refuses_a_base_contract_for_a_facetless_node(tmp_path):
    keep_writer = _writer(
        tmp_path / "base" / "keep",
        science="science:" + "c" * 64,
        domains=PINS.domains,
    )
    other_writer = _writer(tmp_path / "base" / "other", domains=PINS.domains)
    keep = keep_writer.add(
        stored.source_node("s1", title="kept", identifiers={"doi": "10.1/abc"})
    )
    other = other_writer.add(
        stored.source_node("s1", title="other", identifiers={"doi": "10.1/abc"})
    )

    with pytest.raises(ContractPinDisagreement, match="science contracts"):
        relocation.consolidate(
            (keep_writer, keep.id),
            (other_writer, other.id),
            **CONSOLIDATE_FIELDS,
        )


def test_d7_consolidate_refuses_a_missing_pin(tmp_path):
    keep_writer = _writer(tmp_path / "missing" / "keep")
    other_writer = _writer(tmp_path / "missing" / "other", domains=PINS.domains)
    keep = keep_writer.add(_node("biology/gene-axis"))
    other = other_writer.add(_node("biology/gene-axis"))

    with pytest.raises(ContractPinDisagreement, match="biology"):
        relocation.consolidate(
            (keep_writer, keep.id),
            (other_writer, other.id),
            **CONSOLIDATE_FIELDS,
        )


def test_m3_consolidating_equal_basis_retraction_replicas_leaves_the_counter_retraction(
    tmp_path,
):
    keep_writer = _writer(tmp_path / "keep", domains=PINS.domains)
    other_writer = _writer(tmp_path / "other", domains=PINS.domains)
    targets = []
    for writer in (keep_writer, other_writer):
        observed = writer.add(
            stored.dataset_node(
                "raw",
                title="raw",
                resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
                empirical_observation={"boundary": "instrument"},
            )
        )
        run = writer.add(
            stored.run_node(
                "r1", title="r1", spec="analysis-spec:s1", observes=[observed.id]
            )
        )
        proposition = writer.add(
            stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
        )
        targets.append(
            writer.add(
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
        )
    target_identity = stored.stored_semantic_hash(targets[0])
    assert target_identity is not None
    replica = stored.retraction_node(
        title="retraction",
        target=stored.NodeTarget(targets[0].id, targets[0].id, target_identity),
        reason="defective-code",
        rationale="invalid result",
        grounds=("verification:v1",),
        actor="tester",
        event_token="event-1",
    )
    first = keep_writer.retract(replica)
    other_writer.retract(replica)
    first_identity = stored.stored_semantic_hash(first)
    assert first_identity is not None
    counter = keep_writer.retract(
        stored.retraction_node(
            title="counter",
            target=stored.NodeTarget(first.id, first.id, first_identity),
            reason="upstream-retraction",
            rationale="the retraction was withdrawn",
            grounds=("verification:v2",),
            actor="tester",
            event_token="event-2",
        )
    )
    counter_before = keep_writer.read_view.get(counter.id)

    survivor, _, _ = relocation.consolidate(
        (keep_writer, first.id),
        (other_writer, first.id),
        **CONSOLIDATE_FIELDS,
    )

    assert stored.stored_semantic_hash(survivor) == first_identity
    assert keep_writer.read_view.get(counter.id) == counter_before
    assert counter.relations[0].target == first.id


def test_the_survivor_is_readable_after_consolidation(tmp_path):
    keep_writer, other_writer, keep, other = _duplicate_datasets(tmp_path)
    before = stored.stored_semantic_hash(keep)

    survivor, _, _ = relocation.consolidate(
        (keep_writer, keep.id),
        (other_writer, other.id),
        **CONSOLIDATE_FIELDS,
    )

    assert keep_writer.read_view.get(survivor.id) == survivor
    assert stored.stored_semantic_hash(survivor) != before
    assert not stored.semantic_hash_disagrees(survivor)


def test_consolidate_is_idempotent_over_an_already_unioned_survivor(tmp_path):
    keep_writer, other_writer, keep, other = _duplicate_datasets(tmp_path)
    survivor, _, _ = relocation.consolidate(
        (keep_writer, keep.id),
        (other_writer, other.id),
        **CONSOLIDATE_FIELDS,
    )
    other_writer.add(other)

    repeated, _, _ = relocation.consolidate(
        (keep_writer, survivor.id),
        (other_writer, other.id),
        **CONSOLIDATE_FIELDS,
    )

    assert repeated == survivor


def test_t2_a_consolidate_is_one_intent_and_one_report_in_each_root(
    tmp_path, monkeypatch
):
    keep_writer, other_writer, keep, other = _duplicate_datasets(tmp_path)
    report_operations = {}
    for label, writer in (("keep", keep_writer), ("other", other_writer)):
        create_op = writer._create_op

        def capture(record, *, _label=label, _create=create_op):
            operation = _create(record)
            report_operations[_label] = operation
            return operation

        monkeypatch.setattr(writer, "_create_op", capture)

    _, keep_report, other_report = relocation.consolidate(
        (keep_writer, keep.id),
        (other_writer, other.id),
        **CONSOLIDATE_FIELDS,
    )

    assert keep_report.event_token == other_report.event_token
    assert keep_report.opened_at == other_report.opened_at == CONSOLIDATE_FIELDS["opened_at"]
    assert keep_report.closed_at == other_report.closed_at == CONSOLIDATE_FIELDS["closed_at"]
    for label, writer, report in (
        ("keep", keep_writer, keep_report),
        ("other", other_writer, other_report),
    ):
        port = writer._operation_port
        assert isinstance(port, OperationRecorder)
        assert len(port.intents) == len(port.fulfilling) == 1
        assert v1.decode(port.intents[0]) == {
            "kind": "consolidate",
            "event_token": keep_report.event_token,
            "actor": CONSOLIDATE_FIELDS["actor"],
        }
        assert port.fulfilling[0][1] == port.intent_digest
        assert port.fulfilling[0][0][0] is report_operations[label]
        assert writer.read_view.holds(f"act-report:{report.identity()}")


def test_retract_refuses_a_target_moved_away(tmp_path):
    """§3.6 clause 1, through the operation that creates the state."""
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(tmp_path / "destination", domains=PINS.domains)
    observation = source.add(
        stored.dataset_node(
            "observation",
            title="observation",
            resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
            empirical_observation={"boundary": "instrument"},
        )
    )
    destination.add(observation)
    run = source.add(
        stored.run_node(
            "producer",
            title="producer",
            spec="analysis-spec:producer",
            observes=[observation.id],
        )
    )
    destination.add(run)
    proposition = source.add(
        stored.proposition_node("claim", title="claim", claim={"operator": "affects"})
    )
    target = source.add(
        stored.assessment_node(
            "target",
            title="target",
            spec="analysis-spec:producer",
            run=run.id,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule="rule:threshold",
        )
    )
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    record = stored.retraction_node(
        title="retraction",
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=("verification:v1",),
        actor="tester",
        event_token="event-1",
    )
    relocation.move(source, destination, target.id, **MOVE_FIELDS)

    with pytest.raises(RelocationTargetMissing) as caught:
        source.retract(record)
    assert isinstance(caught.value.__cause__, RefError)


def test_supersede_refuses_a_predecessor_moved_away(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(tmp_path / "destination", domains=PINS.domains)
    predecessor = source.add(
        stored.proposition_node("p1", title="p1", claim={"operator": "affects"})
    )
    successor = stored.proposition_node(
        "p2", title="p2", claim={"operator": "inhibits"}
    )
    relocation.move(source, destination, predecessor.id, **MOVE_FIELDS)

    with pytest.raises(RelocationTargetMissing) as caught:
        source.supersede(successor, of=predecessor.id)
    assert isinstance(caught.value.__cause__, RefError)
