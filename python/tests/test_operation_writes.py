"""The operation seams (writer-session design §4.2–§4.4, §13 items 9–13): J1's
refusal-before-intent arms, J3's act-time permit refusal, J4's actor rule — portably,
over the in-memory executor and a port returning synthetic registration digests."""

from __future__ import annotations

import inspect
from typing import Any, cast

import pytest
from authority import ACTOR, FULL, narrowed
from nodes.core.errors import ExecutionError, PlanRefusedError
from nodes.core.node import Node
from nodes.core.write_plan import CreateOp, DefaultExecutor, DeleteOp, ReplaceOp, WritePlan
from test_retract import mint_eligible_assessment

from beliefs import stored
from beliefs.corpus import CorpusWriter, OperationCommit, OperationWrites, _root_state_for
from beliefs.errors import (
    ActorMismatch,
    OperationPortMissing,
    PermitExceeded,
    PermitFact,
    PlanRefused,
    RelocationTargetMissing,
    ScienceError,
    WriteRefused,
)
from beliefs.intents.shapes import DecodedIntent, decode_intent
from beliefs.permit import Authority, WritePermit
from beliefs.report import OperationIntent
from beliefs.world.records import RECORD_CEILING


def proposition(slug: str, operator: str = "affects") -> Node:
    return stored.proposition_node(slug, title=slug, claim={"operator": operator})


def retraction(target: Node, ground: str, actor: str) -> Node:
    identity = stored.stored_semantic_hash(target)
    assert identity is not None
    return stored.retraction_node(title="retraction", target=stored.NodeTarget(target.id, target.id, identity),
                                  reason="defective-code", rationale="invalid", grounds=(ground,), actor=actor, event_token="e1")


class RecordingPort:
    """Records the primitive calls in order and returns synthetic digests; applies the
    plan through a DefaultExecutor so the corpus's index update sees the record."""

    def __init__(self, authority: Authority, root) -> None:
        self.authority = authority
        self.root = root
        self.calls: list[tuple[str, Any]] = []
        self._counter = 0

    def _digest(self, tag: str) -> str:
        self._counter += 1
        return (tag * 60) + f"{self._counter:04d}"

    def append_intent(self, payload: bytes) -> str:
        self.calls.append(("append_intent", payload))
        return self._digest("1")

    def preflight(self, plan: WritePlan) -> None:
        self.calls.append(("preflight", tuple(plan)))
        for op in plan:
            content = getattr(op, "content", None)
            if isinstance(content, bytes) and len(content) > RECORD_CEILING:
                raise PlanRefusedError("over the record ceiling")

    def execute(self, plan: WritePlan) -> None:
        self.calls.append(("execute", tuple(plan)))

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> str:
        self.calls.append(("execute_fulfilling", (tuple(plan), fulfills)))
        DefaultExecutor(self.root).execute(list(plan))
        return self._digest("2")


def writer_over(tmp_path, authority: Authority = FULL) -> tuple[CorpusWriter, RecordingPort]:
    port = RecordingPort(authority, tmp_path)
    return CorpusWriter(tmp_path, DefaultExecutor, authority=authority, operation_port=port), port


def intents_of(port: RecordingPort) -> list[OperationIntent]:
    decoded = [decode_intent("d" * 64, payload) for kind, payload in port.calls if kind == "append_intent"]
    return [cast(OperationIntent, entry.value) for entry in decoded if isinstance(entry, DecodedIntent)]


def primitive_calls(port: RecordingPort) -> list[str]:
    return [kind for kind, _ in port.calls]


# --- J1: one intent, one fulfilling execution, in order; the ordinary body is the refusal implementation
def test_add_commits_as_preflight_intent_then_fulfilling_execution(tmp_path):
    writer, port = writer_over(tmp_path)
    commit = writer.operations.add(proposition("p1"))
    assert type(commit) is OperationCommit and commit.record is not None and commit.record.id == "proposition:p1"
    assert primitive_calls(port) == ["preflight", "append_intent", "execute_fulfilling"]
    (intent,) = intents_of(port)
    assert intent == OperationIntent("corpus-write", commit.event_token, ACTOR)
    _, (plan, fulfills) = port.calls[2]
    assert fulfills == commit.intent_digest and type(plan[0]) is CreateOp
    assert writer.read_view.get("proposition:p1").id == "proposition:p1"  # the index updated incrementally
    state = _root_state_for(tmp_path, DefaultExecutor)
    assert state.unresolved is False and state.fulfilling is None


def test_the_ordinary_path_appends_no_intent_and_the_scope_is_never_left_bound(tmp_path):
    writer, port = writer_over(tmp_path)
    writer.add(proposition("p1"))
    assert primitive_calls(port) == []
    assert _root_state_for(tmp_path, DefaultExecutor).fulfilling is None


def test_delete_commits_a_delete_op_and_carries_no_record(tmp_path):
    writer, port = writer_over(tmp_path)
    writer.add(proposition("p1"))
    port.calls.clear()
    commit = writer.operations.delete("proposition:p1")
    assert commit.record is None
    _, (plan, _) = port.calls[-1]
    assert type(plan[0]) is DeleteOp and writer.read_view.resolve("proposition:p1") is None


def test_revise_commits_a_replace_op(tmp_path):
    writer, port = writer_over(tmp_path)
    node = writer.add(proposition("p1"))
    port.calls.clear()
    commit = writer.operations.revise(node.model_copy(update={"title": "renamed"}))
    _, (plan, _) = port.calls[-1]
    assert type(plan[0]) is ReplaceOp and commit.record is not None


def test_retract_and_supersede_commit_through_their_ordinary_bodies(tmp_path):
    writer, port = writer_over(tmp_path)
    target = mint_eligible_assessment(writer)
    p9 = writer.add(proposition("p9"))
    port.calls.clear()
    writer.operations.retract(retraction(target, "proposition:p1", ACTOR))
    writer.operations.supersede(proposition("p2", "inhibits"), of=p9.id)
    assert primitive_calls(port) == ["preflight", "append_intent", "execute_fulfilling"] * 2


# --- J1: every refusal precedes the intent, and every refusal is the ordinary method's own
@pytest.mark.parametrize(
    "authority",
    [narrowed(kinds=("source",), families=("corpus-write",)), narrowed(kinds=("proposition",), families=("run",))],
)
def test_a_permit_refusal_appends_nothing(tmp_path, authority):
    writer, port = writer_over(tmp_path, authority)
    with pytest.raises(PermitExceeded):
        writer.operations.add(proposition("p1"))
    assert port.calls == []


# One root per case: pytest hands every parameter of a long-named test the same `tmp_path`,
# and a shared root would carry the previous case's records into this one.
@pytest.mark.parametrize("case, build", [
    ("add-act-report", lambda w: (w.add, w.operations.add, proposition("p1").model_copy(update={"kind": "act-report"}))),
    ("add-retraction", lambda w: (w.add, w.operations.add, retraction(mint_eligible_assessment(w), "proposition:x", ACTOR))),
    ("retract-foreign-actor", lambda w: (w.retract, w.operations.retract, retraction(mint_eligible_assessment(w), "proposition:x", "someone-else"))),
])
def test_the_twin_refuses_exactly_as_the_ordinary_method_and_appends_nothing(tmp_path, case, build):
    root = tmp_path / case
    root.mkdir()
    writer, port = writer_over(root)
    ordinary, twin, record = build(writer)
    port.calls.clear()
    with pytest.raises(WriteRefused) as first:
        ordinary(record)
    with pytest.raises(WriteRefused) as second:
        twin(record)
    assert type(second.value) is type(first.value) and str(second.value) == str(first.value)
    assert port.calls == []


def test_an_over_ceiling_record_is_plan_refused_before_the_intent(tmp_path):
    """Through the complete twin: the preflight refusal is `PlanRefused`, never wrapped as a
    post-submission `ExecutionError`, because nothing was submitted."""
    writer, port = writer_over(tmp_path)
    huge = proposition("p1").model_copy(update={"body": "x" * (RECORD_CEILING + 1)})
    with pytest.raises(PlanRefused) as caught:
        writer.operations.add(huge)
    assert type(caught.value) is PlanRefused and isinstance(caught.value.__cause__, PlanRefusedError)
    assert primitive_calls(port) == ["preflight"]
    from beliefs.corpus import _root_state_for

    assert _root_state_for(tmp_path, DefaultExecutor).fulfilling is None


def test_supersede_of_a_missing_target_refuses_before_the_intent(tmp_path):
    writer, port = writer_over(tmp_path)
    with pytest.raises(RelocationTargetMissing):
        writer.operations.supersede(proposition("p2", "inhibits"), of="proposition:gone")
    assert port.calls == []


def test_a_writer_without_a_port_refuses_every_operation_before_any_refusal(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=narrowed())
    with pytest.raises(OperationPortMissing):
        writer.operations.add(proposition("p1"))


# --- §13 item 11: one locked call, one submission, no nesting -------------------------------
def test_a_nested_fulfilling_scope_and_a_second_submission_are_hard_errors(tmp_path):
    writer, port = writer_over(tmp_path)
    with writer._state.lock, writer._fulfilling() as scope:
        with pytest.raises(ScienceError, match="nested"), writer._fulfilling():
            pass
        writer.add(proposition("p1"))  # the one submission
        assert scope.consumed and scope.result is not None
        with pytest.raises(ScienceError, match="exactly one submission"):
            writer.add(proposition("p2"))
    assert _root_state_for(tmp_path, DefaultExecutor).fulfilling is None  # cleared in finally
    assert primitive_calls(port) == ["preflight", "append_intent", "execute_fulfilling"]


def test_the_scope_binds_the_calling_writers_authority_and_port(tmp_path):
    narrow = narrowed(kinds=("proposition",), families=("corpus-write",))
    _, wide_port = writer_over(tmp_path)
    narrow_port = RecordingPort(narrow, tmp_path)
    narrow_writer = CorpusWriter(tmp_path, DefaultExecutor, authority=narrow, operation_port=narrow_port)
    narrow_writer.operations.add(proposition("p1"))
    assert primitive_calls(narrow_port) == ["preflight", "append_intent", "execute_fulfilling"] and wide_port.calls == []
    assert intents_of(narrow_port)[0].actor == ACTOR


def test_the_twin_judges_the_permit_before_it_settles(tmp_path):
    """§13 item 11: on an unresolved root whose recovery fails, the ordinary method and its twin
    both refuse the permit — neither reaches recovery, and no byte moves before the judgment."""
    from beliefs.corpus import _root_state_for

    events = []

    class Factory:
        def __call__(self, root):
            return DefaultExecutor(root)

        def recover(self, root):
            events.append("recover")
            raise ExecutionError("engine down", index=None, applied=None)

    factory = Factory()
    narrow = narrowed(kinds=("proposition",), families=("corpus-write",))
    port = RecordingPort(narrow, tmp_path)
    writer = CorpusWriter(tmp_path, factory, authority=narrow, operation_port=port)
    assert _root_state_for(tmp_path, factory).unresolved is True
    source = stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s1"})
    with pytest.raises(PermitExceeded):
        writer.add(source)
    with pytest.raises(PermitExceeded):
        writer.operations.add(source)
    assert events == [] and port.calls == []
    with pytest.raises(ExecutionError, match="engine down"):
        writer.operations.add(proposition("p1"))  # permitted: now recovery runs, and fails
    assert events == ["recover"] and port.calls == []


def test_a_post_submission_failure_on_the_twin_is_an_execution_error(tmp_path, monkeypatch):
    """J2 through the operation path: the executor committed, nodes' index update failed."""
    from beliefs.corpus import _root_state_for

    writer, port = writer_over(tmp_path)
    writer.add(proposition("p0"))
    state = _root_state_for(tmp_path, DefaultExecutor)
    index_type = type(state.corpus.index)
    monkeypatch.setattr(index_type, "upsert", lambda self, node: (_ for _ in ()).throw(RuntimeError("index down")))
    with pytest.raises(ExecutionError, match="index down") as caught:
        writer.operations.add(proposition("p1"))
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert primitive_calls(port) == ["preflight", "append_intent", "execute_fulfilling"]  # the submission happened
    assert state.unresolved is True and state.fulfilling is None
    monkeypatch.undo()
    with pytest.raises(WriteRefused) as refused:  # a body refusal before submission is not normalized
        writer.operations.add(proposition("p0").model_copy(update={"kind": "act-report"}))
    assert not isinstance(refused.value, ExecutionError)
    huge = proposition("p3").model_copy(update={"body": "x" * (RECORD_CEILING + 1)})
    with pytest.raises(PlanRefused):  # nor is the preflight's, even though the scope was consumed
        writer.operations.add(huge)


# --- J3: the act-time refusal comes from the kernel entry point ------------------------------------
def test_the_requirement_is_the_effective_permit_at_the_act(tmp_path):
    writer, port = writer_over(tmp_path, narrowed(kinds=("proposition",), families=("corpus-write",)))
    writer.operations.add(proposition("p1"))
    with pytest.raises(PermitExceeded) as caught:
        writer.operations.add(stored.source_node("s1", title="s1", identifiers={"doi": "10.1/s1"}))
    assert caught.value.requirement == PermitFact("kind", "source") and caught.value.capability.kinds == ("proposition",)
    assert primitive_calls(port) == ["preflight", "append_intent", "execute_fulfilling"]  # only the first write reached the seam


def test_commit_fulfilling_requires_the_kinds_the_plan_emits():
    from beliefs.corpus import _plan_kinds

    assert _plan_kinds([CreateOp("proposition/p1.md", b"x"), DeleteOp("source/s1.md", expected_digest="0" * 64)]) == ("proposition", "source")
    with pytest.raises(PlanRefused):
        _plan_kinds([CreateOp("corpus.yaml", b"x")])


# --- J4: the actor is the bound one ------------------------------------------------------------------
def test_every_intent_carries_the_bound_actor_and_no_seam_takes_one(tmp_path):
    writer, port = writer_over(tmp_path, Authority(WritePermit.full(), "session:" + "a" * 32))
    writer.operations.add(proposition("p1"))
    assert intents_of(port)[0].actor == "session:" + "a" * 32
    for name, member in inspect.getmembers(OperationWrites, inspect.isfunction):
        assert "actor" not in inspect.signature(member).parameters, name


def test_the_two_intent_producers_emit_one_encoding(tmp_path):
    """One wire encoding, two producers: the routed seam's payload is byte-identical to
    `_append_operation_intent`'s for the same (kind, event_token, actor), so a shape change
    at one site cannot leave the chain carrying two readings of `corpus-write`."""
    writer, port = writer_over(tmp_path)
    commit = writer.operations.add(proposition("p1"))
    (seam_payload,) = [payload for kind, payload in port.calls if kind == "append_intent"]
    writer._append_operation_intent("corpus-write", commit.event_token, ACTOR)
    payloads = [payload for kind, payload in port.calls if kind == "append_intent"]
    assert payloads == [seam_payload, seam_payload]
    assert intents_of(port) == [OperationIntent("corpus-write", commit.event_token, ACTOR)] * 2


def test_a_retraction_naming_another_actor_is_actor_mismatch_with_nothing_appended(tmp_path):
    writer, port = writer_over(tmp_path)
    target = mint_eligible_assessment(writer)
    port.calls.clear()
    with pytest.raises(ActorMismatch):
        writer.operations.retract(retraction(target, "proposition:p1", "someone-else"))
    assert port.calls == []
    assert writer.operations.retract(retraction(target, "proposition:p1", ACTOR)).record is not None
