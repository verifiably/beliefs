"""The two-root world-changing operations: move and consolidate.

Portable: `relocation` takes its writers as arguments, so these run against
`DefaultExecutor` behind the test recorder. What they cannot claim is cut-16
discharge — that runs on the certified engine, under the acceptance runner.
"""

from __future__ import annotations

import pytest
from fixtures_cut3 import report as sample_report
from fixtures_cut6 import PINS
from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from test_corpus_write import OperationRecorder

from beliefs import coordination, relocation, stored
from beliefs.consulted import CorpusPins
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    AddressDisagreement,
    ContractPinDisagreement,
    DuplicateLocation,
    MalformedRecord,
    RelocationKindExcluded,
    RelocationRefused,
    RelocationTargetMissing,
    SameRootRefused,
    WriteRefused,
)
from beliefs.identity import v1
from beliefs.report import Moved, RecordMutationEntry

SCIENCE = PINS.science_contract
BIOLOGY = PINS.domains["biology"]
MOVE_FIELDS = {
    "actor": "a",
    "observer": "o",
    "instrument": "i",
    "opened_at": "2026-09-03T10:00:00Z",
    "closed_at": "2026-09-03T10:00:01Z",
}


def _writer(root, *, science=SCIENCE, domains=None, operation_port=True):
    port = OperationRecorder(root) if operation_port else None
    writer = CorpusWriter(root, DefaultExecutor, operation_port=port)
    writer.adopt_manifest(profile=CorpusPins(science, domains or {}))
    return writer


def _node(*facet_keys: str) -> Node:
    return Node(
        id="memo:relocated",
        kind="memo",
        title="relocated",
        facets={key: {} for key in facet_keys},
    )


@pytest.fixture()
def source_writer(tmp_path):
    return _writer(tmp_path / "source", domains=PINS.domains)


@pytest.fixture()
def destination_writer(tmp_path):
    return _writer(tmp_path / "destination", domains=PINS.domains)


@pytest.fixture()
def writer(tmp_path):
    return _writer(tmp_path / "only", domains=PINS.domains)


def test_move_relocates_without_touching_identity(source_writer, destination_writer):
    node = stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})
    node = source_writer.add(node.model_copy(update={"deprecated_ids": ["source:former"]}))

    moved, _, _ = relocation.move(source_writer, destination_writer, node.id, **MOVE_FIELDS)

    assert (moved.uid, moved.id) == (node.uid, node.id)
    assert moved.deprecated_ids == node.deprecated_ids
    assert destination_writer.read_view.get(node.id).uid == node.uid
    with pytest.raises(RefError):
        source_writer.read_view.get(node.id)


def test_move_refuses_an_occupied_destination(source_writer, destination_writer):
    node = source_writer.add(
        stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})
    )
    destination_writer.add(
        stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})
    )

    with pytest.raises(DuplicateLocation):
        relocation.move(source_writer, destination_writer, node.id, **MOVE_FIELDS)


def test_move_refuses_a_same_root_pair(writer):
    node = writer.add(
        stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})
    )

    with pytest.raises(SameRootRefused):
        relocation.move(writer, writer, node.id, **MOVE_FIELDS)


def test_move_refuses_a_missing_source_before_later_preconditions(
    source_writer, destination_writer
):
    destination_writer.add(
        stored.source_node("missing", title="occupied", identifiers={"doi": "10.1/missing"})
    )

    with pytest.raises(RelocationTargetMissing):
        relocation.move(source_writer, destination_writer, "source:missing", **MOVE_FIELDS)


def test_move_refuses_an_excluded_kind_before_contract_agreement(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(
        tmp_path / "destination",
        science="science:" + "c" * 64,
        domains=PINS.domains,
    )
    report = sample_report()
    source._publish_operation_report(report, "ab" * 32)
    source_port = source._operation_port
    assert isinstance(source_port, OperationRecorder)
    source_port.intents.clear()
    source_port.fulfilling.clear()

    with pytest.raises(RelocationKindExcluded):
        relocation.move(
            source,
            destination,
            f"act-report:{report.identity()}",
            **MOVE_FIELDS,
        )

    assert source_port.intents == []


def test_move_checks_contract_agreement_before_destination_occupancy(tmp_path):
    source = _writer(tmp_path / "source", domains=PINS.domains)
    destination = _writer(
        tmp_path / "destination",
        science="science:" + "c" * 64,
        domains=PINS.domains,
    )
    node = source.add(
        stored.source_node("s1", title="source", identifiers={"doi": "10.1/abc"})
    )
    destination.add(
        stored.source_node("s1", title="destination", identifiers={"doi": "10.1/abc"})
    )

    with pytest.raises(ContractPinDisagreement):
        relocation.move(source, destination, node.id, **MOVE_FIELDS)


def test_move_mints_one_report_per_root_under_one_token(source_writer, destination_writer):
    node = source_writer.add(
        stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})
    )

    moved, destination_report, source_report = relocation.move(
        source_writer, destination_writer, node.id, **MOVE_FIELDS
    )

    assert moved.id == node.id
    assert destination_report.event_token == source_report.event_token
    assert destination_report.operation == source_report.operation == "move"
    assert destination_report.opened_at == source_report.opened_at == MOVE_FIELDS["opened_at"]
    assert destination_report.closed_at == source_report.closed_at == MOVE_FIELDS["closed_at"]
    assert destination_report.identity() != source_report.identity()
    destination_entry, source_entry = destination_report.entries[0], source_report.entries[0]
    assert isinstance(destination_entry, RecordMutationEntry)
    assert isinstance(source_entry, RecordMutationEntry)
    assert destination_entry.subject == source_entry.subject == node.id
    assert destination_entry.corpus == destination_writer.corpus_id
    assert source_entry.corpus == source_writer.corpus_id
    assert destination_entry.outcome == source_entry.outcome == Moved(
        source_writer.corpus_id, destination_writer.corpus_id, node.id
    )
    for writer_, report in (
        (destination_writer, destination_report),
        (source_writer, source_report),
    ):
        port = writer_._operation_port
        assert isinstance(port, OperationRecorder)
        assert len(port.intents) == len(port.fulfilling) == 1
        assert v1.decode(port.intents[0]) == {
            "kind": "move",
            "event_token": destination_report.event_token,
            "actor": MOVE_FIELDS["actor"],
        }
        assert port.fulfilling[0][1] == port.intent_digest
        assert writer_.read_view.holds(f"act-report:{report.identity()}")


@pytest.mark.parametrize("missing", ["source", "destination"])
def test_move_preflights_both_operation_ports_before_either_intent(tmp_path, missing):
    source = _writer(
        tmp_path / missing / "source",
        domains=PINS.domains,
        operation_port=missing != "source",
    )
    destination = _writer(
        tmp_path / missing / "destination",
        domains=PINS.domains,
        operation_port=missing != "destination",
    )
    node = source.add(
        stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})
    )
    configured = destination if missing == "source" else source
    configured_port = configured._operation_port
    assert isinstance(configured_port, OperationRecorder)

    with pytest.raises(RelocationRefused, match=f"{missing} corpus has no operation port"):
        relocation.move(source, destination, node.id, **MOVE_FIELDS)

    assert configured_port.intents == []
    assert source.read_view.holds(node.id)
    assert not destination.read_view.holds(node.id)


def test_move_validates_report_metadata_before_either_intent(source_writer, destination_writer):
    node = source_writer.add(
        stored.source_node("s1", title="A paper", identifiers={"doi": "10.1/abc"})
    )

    with pytest.raises(MalformedRecord, match="canonically encodable"):
        relocation.move(
            source_writer,
            destination_writer,
            node.id,
            **{**MOVE_FIELDS, "observer": "\ud800"},
        )

    for writer_ in (source_writer, destination_writer):
        port = writer_._operation_port
        assert isinstance(port, OperationRecorder)
        assert port.intents == []
    assert source_writer.read_view.holds(node.id)
    assert not destination_writer.read_view.holds(node.id)


def test_every_relocation_refusal_is_a_write_refusal():
    for error in (
        RelocationRefused, SameRootRefused, AddressDisagreement, DuplicateLocation,
        ContractPinDisagreement, RelocationKindExcluded, RelocationTargetMissing,
    ):
        assert issubclass(error, WriteRefused)


def test_both_locks_acquires_distinct_roots_in_sorted_order(tmp_path, monkeypatch):
    events = []

    class RecordingLock:
        def __init__(self, name):
            self.name = name

        def __enter__(self):
            events.append(("enter", self.name))

        def __exit__(self, *_):
            events.append(("exit", self.name))

    later = CorpusWriter(tmp_path / "z", DefaultExecutor)
    earlier = CorpusWriter(tmp_path / "a", DefaultExecutor)
    monkeypatch.setattr(later, "_operation", RecordingLock("z"))
    monkeypatch.setattr(earlier, "_operation", RecordingLock("a"))

    with relocation._both_locks(later, earlier):
        assert events == [("enter", "a"), ("enter", "z")]

    assert events == [
        ("enter", "a"),
        ("enter", "z"),
        ("exit", "z"),
        ("exit", "a"),
    ]


def test_both_locks_acquires_one_distinct_root_once(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor)
    twin = CorpusWriter(tmp_path, DefaultExecutor)

    with relocation._both_locks(writer, twin):
        assert writer._operation._writer_depth == 1


def test_excluded_kinds_are_reports_observations_and_the_coordination_closed_set():
    assert relocation.EXCLUDED_KINDS == (
        "act-report",
        "holdings-observation",
        *coordination.COORDINATION_KINDS,
    )
    assert "coordination-revision" not in relocation.EXCLUDED_KINDS


def test_same_root_refuses_after_path_resolution(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor)
    twin = CorpusWriter(tmp_path / ".", DefaultExecutor)

    with pytest.raises(SameRootRefused):
        relocation._refuse_same_root(writer, twin)


@pytest.mark.parametrize("kind", relocation.EXCLUDED_KINDS)
def test_every_excluded_kind_refuses(kind):
    with pytest.raises(RelocationKindExcluded):
        relocation._refuse_excluded_kind(Node(id=f"{kind}:one", kind=kind, title="one"))


def test_contract_agreement_always_checks_the_science_contract(tmp_path):
    source = _writer(tmp_path / "source")
    destination = _writer(tmp_path / "destination", science="science:" + "c" * 64)

    with pytest.raises(ContractPinDisagreement):
        relocation._refuse_contract_disagreement(_node("display"), source, destination)


def test_contract_agreement_refuses_a_different_used_domain_pin(tmp_path):
    source = _writer(tmp_path / "source", domains={"biology": BIOLOGY})
    destination = _writer(
        tmp_path / "destination",
        domains={"biology": "biology:" + "c" * 64},
    )

    with pytest.raises(ContractPinDisagreement):
        relocation._refuse_contract_disagreement(
            _node("biology/gene-axis"), source, destination
        )


def test_contract_agreement_refuses_a_missing_used_domain_pin(tmp_path):
    source = _writer(tmp_path / "source", domains={"biology": BIOLOGY})
    destination = _writer(tmp_path / "destination")

    with pytest.raises(ContractPinDisagreement):
        relocation._refuse_contract_disagreement(
            _node("biology/gene-axis"), source, destination
        )


def test_contract_agreement_refuses_a_missing_used_source_domain_pin(tmp_path):
    source = _writer(tmp_path / "source")
    destination = _writer(tmp_path / "destination", domains={"biology": BIOLOGY})

    with pytest.raises(ContractPinDisagreement):
        relocation._refuse_contract_disagreement(
            _node("biology/gene-axis"), source, destination
        )


def test_contract_agreement_ignores_different_unused_domain_pins(tmp_path):
    source = _writer(
        tmp_path / "source",
        domains={"biology": BIOLOGY, "chemistry": "chemistry:" + "d" * 64},
    )
    destination = _writer(
        tmp_path / "destination",
        domains={"biology": BIOLOGY, "chemistry": "chemistry:" + "e" * 64},
    )

    relocation._refuse_contract_disagreement(
        _node("display", "biology/gene-axis"), source, destination
    )


def test_corpus_writer_exposes_its_root_manifest_identity_and_pins(tmp_path):
    pins = CorpusPins(SCIENCE, {"biology": BIOLOGY})
    writer = CorpusWriter(tmp_path, DefaultExecutor)
    manifest = writer.adopt_manifest(profile=pins)

    assert writer.root == tmp_path.resolve()
    assert writer.corpus_id == manifest.corpus_id
    assert writer.manifest_pins() == pins


def test_used_facet_namespaces_are_only_the_namespaced_facet_prefixes():
    assert stored.used_facet_namespaces(
        _node("display", "biology/gene-axis", "testing/measure")
    ) == frozenset({"biology", "testing"})
