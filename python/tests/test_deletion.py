"""The ordinary-write `delete` (world-changing families §3.1)."""

from __future__ import annotations

from copy import deepcopy

import pytest
from fixtures_cut4 import path_for
from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from test_relocation import _node, _writer
from test_retract import mint_eligible_assessment

from beliefs import stored
from beliefs.corpus import EXCLUDED_MUTATION_KINDS, CorpusWriter
from beliefs.errors import (
    DeletionKindExcluded,
    DeletionRefused,
    DeletionTargetMissing,
    RelocationTargetMissing,
    WriteRefused,
)
from beliefs.report import OPERATION_KINDS


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    return _writer(tmp_path / "corpus")


def retraction_for(target: Node, ground: str) -> Node:
    """A minimal well-formed retraction of `target`, grounded in `ground`.

    Local to this module: `tests/test_retract.py::retraction_for` takes a
    keyword-only `reason` and a fixed `grounds` tuple, an incompatible shape
    for the positional `(target, ground)` this module's tests want.
    """
    identity = stored.stored_semantic_hash(target)
    assert identity is not None
    return stored.retraction_node(
        title="retraction",
        target=stored.NodeTarget(target.id, target.id, identity),
        reason="defective-code",
        rationale="the recorded result is invalid",
        grounds=(ground,),
        actor="tester",
        event_token="event-1",
    )


def _other_node(suffix: str) -> Node:
    """A second, distinctly identified node in the same corpus as `_node()`.

    `test_relocation.py::_node` always returns the fixed id `memo:relocated`
    — right for its own tests, which move one node between two writers, but a
    collision if `add`ed twice into the same writer.
    """
    return _node().model_copy(update={"id": f"memo:{suffix}"})


def _stored_act_report(writer: CorpusWriter) -> Node:
    """An act-report as it actually enters a corpus: `import_bundle` of a
    foreign report (cut 16's T8 test, `test_import_bundle.py::
    test_foreign_act_report_enters_inert`) — never minted locally."""
    from beliefs.report import ImportedRecords, RecordImportEntry, _mint_report

    foreign_report = _mint_report(
        operation="import",
        event_token="foreign",
        actor="elsewhere",
        observer="other-corpus",
        instrument="other-tool",
        opened_at="T-2",
        closed_at="T-1",
        entries=(RecordImportEntry(subject="other", outcome=ImportedRecords(refs=("memo:x",), findings=())),),
    )
    foreign = stored.act_report_node(foreign_report)
    writer.import_bundle(
        [foreign], actor="k", observer="corpus", instrument="test", opened_at="T0", closed_at="T1"
    )
    return writer.read_view.get(foreign.id)


def test_delete_removes_exactly_one_record_and_mints_nothing(tmp_path):
    # `test_relocation._writer` wires a bare `DefaultExecutor`, which records
    # nothing — its `operation_port` only ever sees `append_intent` and
    # `execute_fulfilling` calls (`test_corpus_write.py::
    # test_publish_operation_report_fulfills_once_stores_and_reconstructs`
    # pins `port.executed == []` for exactly that reason). The one engine
    # effect `delete` performs reaches the corpus's own executor, so this test
    # wires `Recorder` (test_corpus_write.py's plan-tracking executor) as that
    # executor to observe it, alongside an `OperationRecorder` operation port
    # to observe that no intent and no fulfillment are ever recorded.
    from test_corpus_write import OperationRecorder, Recorder

    Recorder.plans = []
    port = OperationRecorder(tmp_path)
    writer = CorpusWriter(tmp_path, Recorder, operation_port=port)
    kept = writer.add(_node())
    doomed = writer.add(_other_node("doomed"))
    intents_before, executed_before = len(port.intents), len(Recorder.plans)

    writer.delete(doomed.id)

    assert writer.read_view.resolve(doomed.id) is None
    with pytest.raises(RefError):
        writer.read_view.get(doomed.id)
    assert writer.read_view.get(kept.id) == kept
    assert not path_for(writer.root, doomed.id).exists()
    assert len(port.intents) == intents_before, "delete appends no intent"
    assert not port.fulfilling, "delete fulfills nothing"
    assert len(Recorder.plans) == executed_before + 1, "one engine effect"
    assert [type(op).__name__ for op in Recorder.plans[-1]] == ["DeleteOp"]
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_the_operation_enum_carries_no_delete_kind():
    assert "delete" not in OPERATION_KINDS


def test_delete_leaves_no_tombstone_and_the_corpus_reads_as_if_never_minted(tmp_path):
    with_delete = _writer(tmp_path / "a")
    never = _writer(tmp_path / "b")
    shared = _node()
    with_delete.add(shared)
    doomed = with_delete.add(_other_node("doomed"))
    never.add(shared)

    with_delete.delete(doomed.id)

    assert sorted(n.id for n in with_delete.read_view.iter_stored()) == sorted(
        n.id for n in never.read_view.iter_stored()
    )
    assert sorted(p.name for p in with_delete.root.rglob("*") if p.is_file() and not p.name.startswith(".")) == sorted(
        p.name for p in never.root.rglob("*") if p.is_file() and not p.name.startswith(".")
    )


def test_delete_refuses_a_missing_target(writer):
    with pytest.raises(DeletionTargetMissing):
        writer.delete("note:absent")


def test_delete_resolves_a_deprecated_id_to_the_live_record(writer):
    # A ref that resolves through `deprecated_ids` deletes the record it resolves to.
    node = writer.add(_node().model_copy(update={"deprecated_ids": ["note:old-name"]}))
    writer.delete("note:old-name")
    assert writer.read_view.resolve(node.id) is None


@pytest.mark.parametrize("kind", ["act-report", "holdings-observation", "project"])
def test_delete_refuses_every_excluded_kind(writer, kind):
    # Bypass the add path: excluded kinds cannot be minted through `add`, so the
    # record is placed by a raw write and `delete` is asked to remove it.
    from fixtures_cut4 import raw_write

    if kind == "project":
        # `stored._node` stamps a semantic-identity digest that only the
        # `beliefs.stored`-owned kinds have a domain for; `project` is a
        # coordination kind and is built the way coordination fixtures do.
        from coordination_fixtures import raw_coordination_node

        node = raw_coordination_node("project", "a" * 32, "c" * 32)
    else:
        node = stored._node(kind, "raw", "raw", {}, ())
    raw_write(writer.root, node)
    writer._reconstruct()
    with pytest.raises(DeletionKindExcluded):
        writer.delete(node.id)
    assert path_for(writer.root, node.id).exists()


def test_delete_refuses_a_kind_the_coordination_profile_names(tmp_path, base_contract):
    # A kind excluded only through a mounted `CoordinationResolver`'s profile,
    # not through the static `EXCLUDED_MUTATION_KINDS` set.
    from coordination_fixtures import (
        COORDINATION_DOCUMENT,
        coordination_profile,
        mounted_root,
        raw_add,
        raw_coordination_node,
    )

    from beliefs.corpus import CoordinationResolver

    document = deepcopy(COORDINATION_DOCUMENT)
    document["kinds"] = {
        **document["kinds"],
        "milestone": {"fields": ["name", "body", "author", "at"], "query_versions": []},
    }
    assert "milestone" not in EXCLUDED_MUTATION_KINDS
    profile = coordination_profile(base_contract, document=document)
    root = mounted_root(tmp_path / "coord", profile)
    node = raw_coordination_node("milestone", "a" * 32, "c" * 32)
    raw_add(root, node)

    resolver = CoordinationResolver({root: profile})
    profiled_writer = CorpusWriter(root, DefaultExecutor, coordination_resolver=resolver)
    profiled_writer._reconstruct()

    with pytest.raises(DeletionKindExcluded):
        profiled_writer.delete(node.id)
    assert path_for(profiled_writer.root, node.id).exists()


def test_the_exclusion_table_is_the_relocation_table():
    from beliefs import relocation

    assert relocation.EXCLUDED_KINDS is EXCLUDED_MUTATION_KINDS
    assert set(EXCLUDED_MUTATION_KINDS) >= {"act-report", "holdings-observation", "project"}


def test_delete_accepts_a_retraction(writer):
    target = mint_eligible_assessment(writer)
    retraction = writer.retract(retraction_for(target, "grounds"))
    writer.delete(retraction.id)
    assert writer.read_view.resolve(retraction.id) is None
    assert writer.read_view.get(target.id) == target


def test_inbound_references_never_prevent_deletion(writer):
    from nodes.core.relations import Relation

    target = writer.add(_node())
    referrer = writer.add(
        _other_node("referrer").model_copy(
            update={"relations": [Relation(source="note:ref", predicate="cites", target=target.id)]}
        )
    )
    writer.delete(target.id)
    assert writer.read_view.resolve(target.id) is None
    assert writer.read_view.get(referrer.id).relations[0].target == target.id, "the dangling reference stays"


def test_deletion_refusals_are_write_refusals():
    assert issubclass(DeletionRefused, WriteRefused)
    assert issubclass(DeletionTargetMissing, DeletionRefused)
    assert issubclass(DeletionKindExcluded, DeletionRefused)


# --- T8 re-read against delete -------------------------------------------------


def test_t8_delete_refuses_an_act_report_and_mints_none(writer):
    report = _stored_act_report(writer)
    # `import_bundle` mints its own act-report for the import operation, on top
    # of the foreign report it stores — so the live count is 2, not 1. What
    # matters here is that the refused `delete` mints no further act-report.
    act_reports_before = sum(1 for n in writer.read_view.iter_stored() if n.kind == "act-report")
    with pytest.raises(DeletionKindExcluded):
        writer.delete(report.id)
    assert writer.read_view.get(report.id) == report
    assert sum(1 for n in writer.read_view.iter_stored() if n.kind == "act-report") == act_reports_before


# --- C1 re-read under §2.2's narrowing ----------------------------------------


def test_c1_retract_never_deletes_or_re_addresses_its_target(writer, monkeypatch):
    target = mint_eligible_assessment(writer)
    before = path_for(writer.root, target.id).read_bytes()
    calls: list[str] = []
    original = CorpusWriter._delete_locked
    monkeypatch.setattr(CorpusWriter, "_delete_locked", lambda self, ref: calls.append(ref) or original(self, ref))
    writer.retract(retraction_for(target, "grounds"))
    assert calls == [], "the retraction operation never reaches the delete seam"
    assert path_for(writer.root, target.id).read_bytes() == before
    assert writer.read_view.resolve(target.id) == target.id


# --- §3.6 re-resolution after a real delete -----------------------------------


def test_retract_refuses_a_target_deleted_under_it(writer, monkeypatch):
    """The target resolves at entry and is deleted before plan construction."""
    target = mint_eligible_assessment(writer)
    record = retraction_for(target, "grounds")
    original_refuse = CorpusWriter._refuse

    def delete_then_refuse(self, node, **kwargs):
        if node.kind == "retraction":
            self._delete_locked(target.id)
        return original_refuse(self, node, **kwargs)

    monkeypatch.setattr(CorpusWriter, "_refuse", delete_then_refuse)
    with pytest.raises(RelocationTargetMissing):
        writer.retract(record)
    assert writer.read_view.resolve(record.id) is None


def test_supersede_refuses_a_predecessor_deleted_under_it(writer, monkeypatch):
    predecessor = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    successor = stored.proposition_node("q", title="q", claim={"operator": "causes"})
    original_refuse = CorpusWriter._refuse

    def delete_then_refuse(self, node, **kwargs):
        if node.kind == "proposition" and node.id == successor.id:
            self._delete_locked(predecessor.id)
        return original_refuse(self, node, **kwargs)

    monkeypatch.setattr(CorpusWriter, "_refuse", delete_then_refuse)
    with pytest.raises(RelocationTargetMissing):
        writer.supersede(successor, of=predecessor.id)
    assert writer.read_view.resolve(successor.id) is None
