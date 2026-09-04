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
from test_relocation import MOVE_FIELDS, _node, _writer
from test_world_epoch import derivation_bindings, make_world, publish

from beliefs import relocation, stored
from beliefs.belief import Belief, evaluate
from beliefs.errors import ContractPinDisagreement, RelocationKindExcluded
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
