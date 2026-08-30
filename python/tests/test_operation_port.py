"""The engine-agnostic operation port and its durable composition-root binding."""

from __future__ import annotations

from typing import ClassVar

import pytest
from atoms.chain.errors import ChainStateInvalid
from atoms.core.errors import (
    CapabilityUnavailable,
    PreconditionRefused,
    ProjectApprovalRefused,
    ProtocolError,
    SpecValidationError,
    TransactionHalted,
)
from atoms.fs.platform import select_backend
from atoms.store.errors import MetadataStoreInvalid
from nodes.core.errors import ExecutionError, PlanRefusedError
from nodes.core.write_plan import CreateOp, WritePlan

from beliefs import root as science_root
from beliefs import stored
from beliefs.corpus import CorpusWriter, OperationPort, _operation_lock_for
from beliefs.errors import BuildHold
from beliefs.root import (
    PRODUCTION_STORAGE,
    DurableOperationPort,
    init_corpus_root,
    init_store_root,
    open_corpus,
)
from beliefs.world.logmodel import RegisteredEntryView, WellFormedView
from beliefs.world.records import RECORD_CEILING

FULFILLS = "ab" * 32
PAYLOAD = b"\x00opaque intent\xff"


class Recorder:
    def __init__(self, _root) -> None:
        pass

    def execute(self, plan: WritePlan) -> None:
        pass


class FakePort:
    intents: ClassVar[list[bytes]] = []
    executed: ClassVar[list[WritePlan]] = []
    fulfilling: ClassVar[list[tuple[WritePlan, str]]] = []

    def append_intent(self, payload: bytes) -> str:
        self.intents.append(payload)
        return FULFILLS

    def execute(self, plan: WritePlan) -> None:
        self.executed.append(plan)

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None:
        self.fulfilling.append((plan, fulfills))


def durable_port(tmp_path) -> DurableOperationPort:
    return DurableOperationPort(
        tmp_path,
        backend=select_backend(),
        storage=PRODUCTION_STORAGE,
        metadata_root=tmp_path.with_name(tmp_path.name + ".metadata"),
    )


def _registered_port(root):
    init_corpus_root(root)
    return durable_port(root)


def _registrations(root):
    chain = science_root._log_seam().inspect_registered(root)
    assert type(chain) is WellFormedView
    return [
        entry for entry in chain.entries if type(entry) is RegisteredEntryView
    ]


class TestTheStructuralPort:
    def test_a_fake_records_the_two_real_boundary_calls(self, tmp_path):
        FakePort.intents = []
        FakePort.fulfilling = []
        port: OperationPort = FakePort()
        writer = CorpusWriter(tmp_path, Recorder, operation_port=port)
        plan = [CreateOp(path="p.md", content=b"record")]

        configured = writer._operation_port
        assert configured is port
        assert configured is not None
        digest = configured.append_intent(PAYLOAD)
        configured.execute_fulfilling(plan, digest)

        assert FakePort.intents == [PAYLOAD]
        assert FakePort.fulfilling == [(plan, FULFILLS)]

    def test_the_port_defaults_to_none_without_changing_portable_construction(self, tmp_path):
        assert CorpusWriter(tmp_path, Recorder)._operation_port is None

    def test_ports_do_not_change_the_stable_shared_executor_factory(self, tmp_path):
        with_port = CorpusWriter(tmp_path, Recorder, operation_port=FakePort())
        without_port = CorpusWriter(tmp_path, Recorder)

        assert with_port._state is without_port._state


class TestTheDurablePort:
    def test_open_corpus_wires_the_durable_port(self, tmp_path):
        assert isinstance(open_corpus(tmp_path)._operation_port, DurableOperationPort)

    def test_append_intent_forwards_the_opaque_payload_unchanged(self, tmp_path, monkeypatch):
        calls: list[tuple] = []

        def capture(backend, project_root, metadata_root, storage, payload):
            calls.append((backend, project_root, metadata_root, storage, payload))
            return FULFILLS

        monkeypatch.setattr(science_root, "append_intent", capture)
        port = durable_port(tmp_path)

        assert port.append_intent(PAYLOAD) == FULFILLS
        backend, project_root, metadata_root, storage, payload = calls[0]
        assert backend is port._backend
        assert project_root == str(tmp_path)
        assert metadata_root == str(tmp_path) + ".metadata"
        assert storage is PRODUCTION_STORAGE
        assert payload is PAYLOAD

    def test_execute_fulfilling_threads_the_exact_digest_into_the_spec(self, tmp_path, monkeypatch):
        submitted = []

        def capture(_backend, _project_root, _metadata_root, _storage, spec, _payloads):
            submitted.append(spec)

        monkeypatch.setattr(science_root, "run_transaction", capture)

        durable_port(tmp_path).execute_fulfilling(
            [CreateOp(path="p.md", content=b"record")],
            FULFILLS,
        )

        assert submitted[0].fulfills == FULFILLS

    @pytest.mark.parametrize(
        ("raised", "applied"),
        [
            (ProjectApprovalRefused("rooted proof"), 0),
            (PreconditionRefused("clean refusal"), 0),
            (CapabilityUnavailable("not certified"), 0),
            (SpecValidationError("engine validation"), None),
            (MetadataStoreInvalid("stop and preserve"), None),
            (ChainStateInvalid("stop and preserve"), None),
            (TransactionHalted("unattributable"), None),
            (ProtocolError("engine contract"), None),
            (RuntimeError("unrecognized"), None),
        ],
    )
    def test_each_append_failure_maps_to_its_arm(self, tmp_path, monkeypatch, raised, applied):
        def fail(*_args, **_kwargs):
            raise raised

        monkeypatch.setattr(science_root, "append_intent", fail)

        with pytest.raises(ExecutionError) as mapped:
            durable_port(tmp_path).append_intent(PAYLOAD)

        assert (mapped.value.index, mapped.value.applied) == (None, applied)
        assert mapped.value.__cause__ is raised

    @pytest.mark.parametrize("mutation", ["append_intent", "execute", "execute_fulfilling"])
    def test_every_mutation_takes_the_roots_operation_lock(
        self, tmp_path, monkeypatch, mutation
    ) -> None:
        monkeypatch.setattr(science_root, "append_intent", lambda *_args: FULFILLS)
        monkeypatch.setattr(science_root.DurableExecutor, "execute", lambda *_args: None)
        port = durable_port(tmp_path)
        plan = [CreateOp(path="p.md", content=b"record")]

        with _operation_lock_for(tmp_path).capture(), pytest.raises(BuildHold):
            if mutation == "append_intent":
                port.append_intent(PAYLOAD)
            elif mutation == "execute":
                port.execute(plan)
            else:
                port.execute_fulfilling(plan, FULFILLS)


def test_execute_publishes_fulfilling_nothing(certified_work) -> None:
    port = _registered_port(certified_work)
    port.execute(
        [CreateOp(path="act-report/" + "a" * 64 + ".md", content=b"content")]
    )
    (registration,) = _registrations(certified_work)
    assert registration.fulfills is None
    assert (certified_work / "act-report" / ("a" * 64 + ".md")).read_bytes() == b"content"


def test_corpus_writer_reenters_its_durable_ports_shared_lock(certified_work) -> None:
    init_corpus_root(certified_work)
    writer = open_corpus(certified_work)
    node = stored.proposition_node("p", title="p", claim={"operator": "affects"})

    writer.import_bundle(
        [node],
        actor="actor",
        observer="observer",
        instrument="instrument",
        opened_at="T0",
        closed_at="T1",
    )

    assert writer.read_view.holds(node.id)


def test_execute_refuses_a_malformed_plan_before_any_write(certified_work) -> None:
    port = _registered_port(certified_work)
    with pytest.raises(PlanRefusedError):
        port.execute([CreateOp(path="../escape.md", content=b"x")])
    assert _registrations(certified_work) == []


def test_execute_surfaces_an_execution_failure_as_execution_error(certified_work) -> None:
    port = _registered_port(certified_work)
    plan = [CreateOp(path="act-report/" + "b" * 64 + ".md", content=b"x")]
    port.execute(plan)
    with pytest.raises(ExecutionError):
        port.execute(plan)


def test_oversized_postimage_refuses_before_any_write(certified_work) -> None:
    port = _registered_port(certified_work)
    boundary = b"x" * RECORD_CEILING
    port.execute(
        [CreateOp(path="act-report/" + "c" * 64 + ".md", content=boundary)]
    )
    with pytest.raises(PlanRefusedError):
        port.execute(
            [CreateOp(path="act-report/" + "d" * 64 + ".md", content=boundary + b"x")]
        )
    with pytest.raises(PlanRefusedError):
        port.execute_fulfilling(
            [CreateOp(path="run/" + "e" * 64 + ".md", content=boundary + b"x")],
            "f" * 64,
        )
    assert not (certified_work / "act-report" / ("d" * 64 + ".md")).exists()
    assert not (certified_work / "run").exists()
    assert len(_registrations(certified_work)) == 1


def test_non_port_writes_are_unaffected_by_the_ceiling(certified_work) -> None:
    init_store_root(certified_work)
    big = b"x" * (RECORD_CEILING + 1)
    outcome = science_root._store_write(certified_work, "payload.bin", big)
    assert (certified_work / "payload.bin").read_bytes() == big
    assert outcome.txid
