"""The two-root world-changing operations: move and consolidate.

Portable: `relocation` takes its writers as arguments, so these run against
`DefaultExecutor` behind the test recorder. What they cannot claim is cut-16
discharge — that runs on the certified engine, under the acceptance runner.
"""

from __future__ import annotations

import pytest
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor

from beliefs import coordination, relocation, stored
from beliefs.consulted import CorpusPins
from beliefs.corpus import CorpusWriter
from beliefs.errors import (
    AddressDisagreement,
    ContractPinDisagreement,
    DuplicateLocation,
    RelocationKindExcluded,
    RelocationRefused,
    RelocationTargetMissing,
    SameRootRefused,
    WriteRefused,
)

SCIENCE = "science:" + "a" * 64
BIOLOGY = "biology:" + "b" * 64


def _writer(root, *, science=SCIENCE, domains=None):
    writer = CorpusWriter(root, DefaultExecutor)
    writer.adopt_manifest(profile=CorpusPins(science, domains or {}))
    return writer


def _node(*facet_keys: str) -> Node:
    return Node(
        id="memo:relocated",
        kind="memo",
        title="relocated",
        facets={key: {} for key in facet_keys},
    )


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
