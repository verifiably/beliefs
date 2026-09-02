from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import ClassVar

import pytest
from nodes.core.errors import ExecutionError
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import CreateOp, DefaultExecutor

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import BundleMemberHeld, ImportRefused
from beliefs.identity import v1
from beliefs.report import ImportedRecords, RecordImportEntry, _mint_report


class Recorder:
    plans: ClassVar[list[list]] = []

    def __init__(self, root):
        self._inner = DefaultExecutor(root)

    def execute(self, plan) -> None:
        Recorder.plans.append(list(plan))
        self._inner.execute(plan)


class FakePort:
    intents: ClassVar[list[bytes]] = []
    executed: ClassVar[list[list]] = []
    fulfilling: ClassVar[list[tuple[list, str]]] = []
    intent_digest = "ab" * 32

    def __init__(self, root):
        self._inner = DefaultExecutor(root)

    def append_intent(self, payload: bytes) -> str:
        FakePort.intents.append(payload)
        return self.intent_digest

    def execute(self, plan) -> None:
        FakePort.executed.append(list(plan))
        self._inner.execute(plan)

    def execute_fulfilling(self, plan, fulfills: str) -> None:
        FakePort.fulfilling.append((list(plan), fulfills))
        self._inner.execute(plan)


@pytest.fixture()
def writer_with_port(tmp_path):
    Recorder.plans, FakePort.intents, FakePort.fulfilling = [], [], []
    return CorpusWriter(tmp_path, Recorder, operation_port=FakePort(tmp_path))


def test_import_refuses_a_coordination_member_by_name(writer_with_port):
    member = Node(id="note:old", kind="note", title="old")
    with pytest.raises(ImportRefused) as caught:
        writer_with_port.import_bundle(
            [member],
            actor="a",
            observer="o",
            instrument="i",
            opened_at="T0",
            closed_at="T1",
        )
    assert caught.value.member == member.id


def prop(slug: str) -> Node:
    return stored.proposition_node(slug, title=slug, claim={"operator": "affects"})


def import_records(writer: CorpusWriter, records):
    return writer.import_bundle(
        records,
        actor="k",
        observer="corpus",
        instrument="test",
        opened_at="T0",
        closed_at="T1",
    )


def retraction(slug: str, target: str) -> Node:
    record = Node(
        id=f"retraction:{slug}",
        kind="retraction",
        title=slug,
        facets={
            stored.RETRACTION_FACET: {
                "target": {
                    "arm": "node",
                    "ref": target,
                    "resolved": target,
                    "content_identity": "0" * 64,
                },
                "reason": "authored-error",
                "rationale": "test cycle",
                "grounds": ["source:test"],
                "actor": "k",
                "event_token": slug,
            }
        },
        relations=[],
    )
    record.relations = [
        # The stored constructor derives this same edge from the target.
        Relation(source=record.id, predicate=stored.RETRACTS, target=target)
    ]
    return stored.stamp_semantic_identity(record)


def test_import_admits_bundle_in_one_payload_plan(writer_with_port):
    report = import_records(writer_with_port, [prop("a"), prop("b")])

    assert FakePort.intents == [v1.encode({"kind": "import", "event_token": report.event_token, "actor": "k"})]
    (payload,) = Recorder.plans
    assert len(payload) == 2 and all(isinstance(op, CreateOp) for op in payload)
    ((report_plan, fulfills),) = FakePort.fulfilling
    assert len(report_plan) == 1 and isinstance(report_plan[0], CreateOp)
    assert fulfills == FakePort.intent_digest
    assert writer_with_port.read_view.holds("proposition:a")
    assert writer_with_port.read_view.holds(f"act-report:{report.identity()}")
    assert report.entries == (
        RecordImportEntry(
            subject=writer_with_port._corpus.store.root.name,
            outcome=ImportedRecords(refs=("proposition:a", "proposition:b"), findings=()),
        ),
    )


def test_member_held_refuses_whole_bundle_no_payload_write(writer_with_port):
    writer_with_port.add(prop("a"))
    Recorder.plans = []

    with pytest.raises(BundleMemberHeld) as caught:
        import_records(writer_with_port, [prop("a"), prop("b")])

    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds("proposition:b")
    assert caught.value.member == "proposition:a"
    assert caught.value.report_ref is not None
    assert writer_with_port.read_view.holds(caught.value.report_ref)


def test_local_destination_path_collision_is_a_held_member(writer_with_port):
    writer_with_port.add(prop("a:b"))
    Recorder.plans = []

    with pytest.raises(BundleMemberHeld):
        import_records(writer_with_port, [prop("a__b")])

    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds("proposition:a__b")


def test_bundle_members_cannot_share_a_deprecated_identity_claim(writer_with_port):
    first = prop("first").model_copy(update={"deprecated_ids": ["proposition:shared"]})
    second = prop("second").model_copy(update={"deprecated_ids": ["proposition:shared"]})

    with pytest.raises(BundleMemberHeld) as caught:
        import_records(writer_with_port, [first, second])

    assert caught.value.report_ref is not None
    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(first.id)
    assert not writer_with_port.read_view.holds(second.id)


def test_bundle_deprecated_claim_cannot_collide_with_an_arriving_live_id(writer_with_port):
    live = prop("claimed")
    alias = prop("alias").model_copy(update={"deprecated_ids": [live.id]})

    with pytest.raises(BundleMemberHeld):
        import_records(writer_with_port, [alias, live])

    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(live.id)


def test_bundle_member_live_id_cannot_also_be_deprecated(writer_with_port):
    malformed = prop("self-alias").model_copy(update={"deprecated_ids": ["proposition:self-alias"]})

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [malformed])

    assert caught.value.report_ref is not None
    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(malformed.id)


def test_bundle_member_cannot_repeat_a_deprecated_id(writer_with_port):
    malformed = prop("duplicate-alias").model_copy(
        update={"deprecated_ids": ["proposition:old", "proposition:old"]}
    )

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [malformed])

    assert caught.value.report_ref is not None
    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(malformed.id)


def test_bundle_relation_resolves_through_an_arriving_deprecated_id(writer_with_port):
    dataset = stored.dataset_node(
        "current",
        title="current",
        resources=[{"name": "data", "digest": "sha256:" + "ab" * 32}],
    ).model_copy(update={"deprecated_ids": ["dataset:previous"]})
    run = stored.run_node("run", title="run", spec="analysis-spec:s", observes=["dataset:previous"])

    report = import_records(writer_with_port, [run, dataset])

    outcome = report.entries[0].outcome
    assert isinstance(outcome, ImportedRecords) and outcome.findings == ()
    assert writer_with_port.read_view.resolve("dataset:previous") == dataset.id


def test_raw_bundle_cycle_shapes_refuse_before_cycle_classification(writer_with_port):
    first = retraction("a", "retraction:b")
    second = retraction("b", "retraction:a")

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [first, second])

    assert caught.value.member == "retraction:a"
    assert caught.value.cycle_edges == ()
    assert Recorder.plans == []


def test_raw_local_cycle_shape_refuses_before_cycle_classification(writer_with_port):
    DefaultExecutor(writer_with_port._corpus.store.root).execute(
        [writer_with_port._create_op(retraction("a", "retraction:b"))]
    )
    writer_with_port._reconstruct()
    Recorder.plans = []

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [retraction("b", "retraction:a")])

    assert caught.value.member == "retraction:b"
    assert caught.value.cycle_edges == ()
    assert Recorder.plans == []


def test_unresolved_foreign_input_admits_with_finding(writer_with_port):
    foreign = stored.verification_node(
        "foreign",
        title="foreign",
        assessment="assessment-identity",
        assessment_ref="assessment:elsewhere",
        scope="clean-environment",
        verdict="passed",
    )

    report = import_records(writer_with_port, [foreign])

    outcome = report.entries[0].outcome
    assert isinstance(outcome, ImportedRecords)
    assert outcome.refs == (foreign.id,)
    assert outcome.findings == (f"unresolved: {foreign.id} -> assessment:elsewhere",)
    assert writer_with_port.read_view.holds(foreign.id)
    assert "validated" not in writer_with_port.read_view.get(foreign.id).facets[stored.VERIFICATION_FACET]


def test_uncanonically_encodable_success_finding_refuses_before_payload(writer_with_port):
    record = Node(
        id="memo:surrogate-finding",
        kind="memo",
        title="surrogate finding",
        relations=[
            Relation(
                source="memo:surrogate-finding",
                predicate="refers-to",
                target="\ud800",
            )
        ],
    )

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [record])

    assert caught.value.report_ref is not None
    assert "\ud800" not in str(caught.value)
    assert len(FakePort.intents) == 1
    assert len(FakePort.fulfilling) == 1
    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(record.id)


def test_ordinary_eligibility_is_evaluated_over_bundle_union(writer_with_port):
    dataset = stored.dataset_node(
        "observed",
        title="observed",
        resources=[{"name": "data", "digest": "sha256:" + "ab" * 32}],
        empirical_observation={"boundary": "instrument"},
    )
    run = stored.run_node("run", title="run", spec="analysis-spec:s", observes=[dataset.id])
    proposition = prop("claim")
    assessment = stored.assessment_node(
        "assessment",
        title="assessment",
        spec="analysis-spec:s",
        run=run.id,
        proposition=proposition.id,
        outcome="supported",
        interpretation_rule="rule:threshold",
    )

    report = import_records(writer_with_port, [assessment, run, proposition, dataset])

    outcome = report.entries[0].outcome
    assert isinstance(outcome, ImportedRecords) and outcome.findings == ()
    assert all(writer_with_port.read_view.holds(record.id) for record in (assessment, run, proposition, dataset))


def test_retraction_target_can_resolve_from_the_same_bundle(writer_with_port):
    verification = stored.verification_node(
        "target",
        title="target",
        assessment="assessment-identity",
        assessment_ref="assessment:elsewhere",
        scope="clean-environment",
        verdict="passed",
    )
    content_identity = stored.stored_semantic_hash(verification)
    assert content_identity is not None
    retracted = stored.retraction_node(
        title="withdraw target",
        target=stored.NodeTarget(
            ref=verification.id,
            resolved=verification.id,
            content_identity=content_identity,
        ),
        reason="authored-error",
        rationale="the verification is wrong",
        grounds=["source:grounds"],
        actor="k",
        event_token="retract-target",
    )

    import_records(writer_with_port, [verification, retracted])

    assert writer_with_port.read_view.holds(retracted.id)


def test_stale_stamp_member_refuses(writer_with_port):
    stale = prop("stale")
    stale.facets[stored.PROPOSITION_FACET]["operator"] = "forged"

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [stale])

    assert caught.value.member == stale.id
    assert Recorder.plans == []


@pytest.mark.parametrize("grounds", [[], [""]])
def test_malformed_retraction_grounds_close_intent_without_payload(writer_with_port, grounds):
    target = stored.verification_node(
        "grounds-target",
        title="grounds target",
        assessment="assessment-identity",
        assessment_ref="assessment:elsewhere",
        scope="clean-environment",
        verdict="passed",
    )
    content_identity = stored.stored_semantic_hash(target)
    assert content_identity is not None
    valid = stored.retraction_node(
        title="withdraw target",
        target=stored.NodeTarget(target.id, target.id, content_identity),
        reason="authored-error",
        rationale="invalid grounds fixture",
        grounds=("source:ground",),
        actor="k",
        event_token="invalid-grounds",
    )
    facet = deepcopy(valid.facets)
    facet[stored.RETRACTION_FACET]["grounds"] = grounds
    malformed = stored.stamp_semantic_identity(
        valid.model_copy(update={"facets": facet, "relations": valid.relations[:1]})
    )

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [target, malformed])

    assert caught.value.report_ref is not None
    assert len(FakePort.intents) == 1
    assert len(FakePort.fulfilling) == 1
    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(target.id)


def test_post_intent_domain_validation_failure_closes_with_import_refused(writer_with_port):
    malformed = Node(
        id="memo:semantic-domain",
        kind="memo",
        title="semantic domain",
        facets={stored.SEMANTIC_IDENTITY_FACET: {"digest": "x"}},
    )

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [malformed])

    assert caught.value.report_ref is not None
    assert len(FakePort.intents) == 1
    assert len(FakePort.fulfilling) == 1
    assert Recorder.plans == []


def test_unencodable_post_intent_refusal_closes_with_one_canonical_report(writer_with_port):
    malformed = prop("bad-id")
    malformed.id = "proposition:\ud800"

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [malformed])

    assert caught.value.report_ref is not None
    assert len(FakePort.intents) == 1
    assert len(FakePort.fulfilling) == 1
    assert Recorder.plans == []
    report_node = writer_with_port.read_view.get(caught.value.report_ref)
    (finding,) = report_node.facets["act-report"]["entries"][0]["outcome"]["findings"]
    assert "proposition:\\ud800" in finding
    finding.encode("utf-8")


def test_malformed_intent_digest_refuses_before_payload_or_report(tmp_path):
    class MalformedDigestPort(FakePort):
        intent_digest = "bad"

    Recorder.plans, FakePort.intents, FakePort.fulfilling = [], [], []
    writer = CorpusWriter(tmp_path, Recorder, operation_port=MalformedDigestPort(tmp_path))

    with pytest.raises(ExecutionError, match="intent digest"):
        import_records(writer, [prop("not-written")])

    assert len(FakePort.intents) == 1
    assert FakePort.fulfilling == []
    assert Recorder.plans == []
    assert not writer.read_view.holds("proposition:not-written")


def test_unrenderable_member_closes_the_intent_without_a_payload(writer_with_port):
    unrenderable = stored.proposition_node(
        "decimal",
        title="decimal",
        claim={"estimate": Decimal("1.25")},
    )

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [unrenderable])

    assert caught.value.report_ref is not None
    assert len(FakePort.intents) == 1
    assert len(FakePort.fulfilling) == 1
    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(unrenderable.id)


def test_member_that_cannot_round_trip_refuses_before_payload(writer_with_port):
    lossy = Node(
        id="memo:roundtrip",
        kind="memo",
        title="roundtrip",
        facets={"custom": {("a", "b"): "value"}},
    )

    with pytest.raises(ImportRefused) as caught:
        import_records(writer_with_port, [lossy])

    assert caught.value.report_ref is not None
    assert len(FakePort.intents) == 1
    assert len(FakePort.fulfilling) == 1
    assert Recorder.plans == []
    assert not writer_with_port.read_view.holds(lossy.id)


def test_foreign_act_report_enters_inert(writer_with_port):
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

    import_records(writer_with_port, [foreign])

    held = writer_with_port.read_view.get(foreign.id)
    assert held == foreign
    assert held.facets["act-report"]["actor"] == "elsewhere"


def test_malformed_foreign_act_report_refuses_even_when_restamped(writer_with_port):
    foreign_report = _mint_report(
        operation="import",
        event_token="foreign",
        actor="elsewhere",
        observer="other-corpus",
        instrument="other-tool",
        opened_at="T-2",
        closed_at="T-1",
        entries=(),
    )
    original = stored.act_report_node(foreign_report)
    facets = deepcopy(original.facets)
    facets["act-report"]["entries"] = [{"kind": "made-up"}]
    malformed = stored.stamp_semantic_identity(original.model_copy(update={"facets": facets}))

    with pytest.raises(ImportRefused):
        import_records(writer_with_port, [malformed])

    assert Recorder.plans == []


def test_contradictory_nondeterminism_contract_refused(writer_with_port):
    spec = stored.stamp_semantic_identity(
        Node(
            id="analysis-spec:s",
            kind="analysis-spec",
            title="s",
            facets={
                "analysis-spec": {
                    "equivalence_rule": "content-identity-equality/v1",
                    "nondeterminism": {
                        "variant": "stochastic-unseeded",
                        "rationale": "the process has no stable seed surface",
                    },
                }
            },
            relations=[],
        )
    )

    with pytest.raises(ImportRefused, match="bitwise"):
        import_records(writer_with_port, [spec])

    assert Recorder.plans == []


def test_malformed_nondeterminism_contract_refuses_without_leaking_a_type_error(writer_with_port):
    spec = stored.stamp_semantic_identity(
        Node(
            id="analysis-spec:malformed",
            kind="analysis-spec",
            title="malformed",
            facets={"analysis-spec": {"equivalence_rule": [], "nondeterminism": {"variant": []}}},
            relations=[],
        )
    )

    with pytest.raises(ImportRefused, match="malformed analysis-spec"):
        import_records(writer_with_port, [spec])

    assert Recorder.plans == []


@pytest.mark.parametrize("records", [[], ()])
def test_refusal_before_intent_when_request_malformed(writer_with_port, records):
    with pytest.raises(ImportRefused):
        import_records(writer_with_port, records)
    assert FakePort.intents == []
    assert FakePort.fulfilling == []


@pytest.mark.parametrize("field", ["actor", "observer", "instrument", "opened_at", "closed_at"])
def test_attribution_and_times_refuse_before_intent(writer_with_port, field):
    values = {
        "actor": "k",
        "observer": "corpus",
        "instrument": "test",
        "opened_at": "T0",
        "closed_at": "T1",
    }
    values[field] = ""

    with pytest.raises(ImportRefused):
        writer_with_port.import_bundle([prop("a")], **values)

    assert FakePort.intents == []


@pytest.mark.parametrize("field", ["actor", "observer", "instrument", "opened_at", "closed_at"])
def test_uncanonically_encodable_report_fields_refuse_before_intent(writer_with_port, field):
    values = {
        "actor": "k",
        "observer": "corpus",
        "instrument": "test",
        "opened_at": "T0",
        "closed_at": "T1",
    }
    values[field] = "\ud800"

    with pytest.raises(ImportRefused):
        writer_with_port.import_bundle([prop("a")], **values)

    assert FakePort.intents == []
    assert FakePort.fulfilling == []
    assert Recorder.plans == []


def test_uncanonically_encodable_report_subject_refuses_before_intent(tmp_path):
    Recorder.plans, FakePort.intents, FakePort.fulfilling = [], [], []
    root = tmp_path / "\udcff"
    writer = CorpusWriter(root, Recorder, operation_port=FakePort(root))

    with pytest.raises(ImportRefused):
        import_records(writer, [prop("a")])

    assert FakePort.intents == []
    assert FakePort.fulfilling == []
    assert Recorder.plans == []


def test_no_operation_port_refuses_before_any_act(tmp_path):
    Recorder.plans = []
    writer = CorpusWriter(tmp_path, Recorder)
    with pytest.raises(ImportRefused, match="no operation port"):
        import_records(writer, [prop("a")])
    assert Recorder.plans == []


def test_refusal_report_failure_leaves_intent_open_and_engine_error_unchanged(tmp_path):
    class ReportFailure(RuntimeError):
        pass

    class FailingPort(FakePort):
        def execute_fulfilling(self, plan, fulfills: str) -> None:
            raise ReportFailure

    Recorder.plans, FakePort.intents, FakePort.fulfilling = [], [], []
    writer = CorpusWriter(tmp_path, Recorder, operation_port=FailingPort(tmp_path))
    writer.add(prop("held"))
    Recorder.plans = []

    with pytest.raises(ReportFailure):
        import_records(writer, [prop("held"), prop("not-written")])

    assert len(FakePort.intents) == 1
    assert Recorder.plans == []
    assert not writer.read_view.holds("proposition:not-written")


def test_success_report_failure_leaves_payload_visible_and_intent_open(tmp_path):
    class ReportFailure(RuntimeError):
        pass

    class FailingPort(FakePort):
        def execute_fulfilling(self, plan, fulfills: str) -> None:
            raise ReportFailure

    Recorder.plans, FakePort.intents, FakePort.fulfilling = [], [], []
    writer = CorpusWriter(tmp_path, Recorder, operation_port=FailingPort(tmp_path))

    with pytest.raises(ReportFailure) as caught:
        import_records(writer, [prop("admitted")])

    assert type(caught.value) is ReportFailure
    assert len(FakePort.intents) == 1
    assert FakePort.fulfilling == []
    assert writer.read_view.holds("proposition:admitted")
