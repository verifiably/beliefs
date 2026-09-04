from __future__ import annotations

import dataclasses
from copy import deepcopy

import pytest
from fixtures_cut3 import memory_assessment as run_assessment
from fixtures_cut3 import report as _mint
from nodes.core.node import Node

from beliefs import stored
from beliefs.boundary import RunRefused
from beliefs.errors import MalformedRecord
from beliefs.report import (
    ACT_REPORT_DOMAIN,
    ActReport,
    Consolidated,
    Moved,
    RecordMutationEntry,
    RunAttemptEntry,
    RunRefusal,
)


@pytest.fixture
def act_report(tmp_path) -> ActReport:
    outcome = run_assessment(tmp_path, spec=None.__class__)
    assert isinstance(outcome, RunRefused) and isinstance(outcome.report, ActReport)
    return outcome.report


def changed_report(report: ActReport, **changes: object) -> ActReport:
    changed = object.__new__(ActReport)
    for field in dataclasses.fields(report):
        object.__setattr__(changed, field.name, changes.get(field.name, getattr(report, field.name)))
    return changed


def _record_mutation_entry() -> RecordMutationEntry:
    return RecordMutationEntry(
        subject="dataset:d1",
        corpus="corpus-a",
        outcome=Moved(source_corpus="corpus-a", destination_corpus="corpus-b", ref="dataset:d1"),
    )


def _consolidated_record_mutation_entry() -> RecordMutationEntry:
    return RecordMutationEntry(
        subject="source:s1",
        corpus="corpus-a",
        outcome=Consolidated(
            kept_corpus="corpus-a",
            kept_ref="source:s1",
            other_corpus="corpus-b",
            other_ref="source:s1",
            retired_uids=("u-2",),
            rationale="corpus-a holds the authored record",
        ),
    )


def test_a_record_mutation_report_round_trips():
    report_value = _mint(operation="move", entries=(_record_mutation_entry(),))
    node = stored.act_report_node(report_value)
    assert stored.act_report_facet(node)["entries"] == [
        {
            "kind": "record-mutation",
            "subject": "dataset:d1",
            "corpus": "corpus-a",
            "outcome": {
                "type": "moved",
                "source_corpus": "corpus-a",
                "destination_corpus": "corpus-b",
                "ref": "dataset:d1",
            },
        }
    ]


def test_a_record_mutation_entry_missing_its_corpus_is_malformed():
    node = stored.act_report_node(_mint(operation="move", entries=(_record_mutation_entry(),)))
    del node.facets["act-report"]["entries"][0]["corpus"]
    with pytest.raises(MalformedRecord, match="malformed act-report entry"):
        stored.act_report_facet(node)


def test_a_record_mutation_entry_refuses_a_foreign_outcome_type():
    node = stored.act_report_node(_mint(operation="move", entries=(_record_mutation_entry(),)))
    node.facets["act-report"]["entries"][0]["outcome"]["type"] = "published-observation"
    with pytest.raises(MalformedRecord, match="malformed act-report entry"):
        stored.act_report_facet(node)


def test_a_consolidated_record_mutation_report_round_trips():
    node = stored.act_report_node(_mint(operation="consolidate", entries=(_consolidated_record_mutation_entry(),)))
    assert stored.act_report_facet(node)["entries"][0] == {
        "kind": "record-mutation",
        "subject": "source:s1",
        "corpus": "corpus-a",
        "outcome": {
            "type": "consolidated",
            "kept_corpus": "corpus-a",
            "kept_ref": "source:s1",
            "other_corpus": "corpus-b",
            "other_ref": "source:s1",
            "retired_uids": ["u-2"],
            "rationale": "corpus-a holds the authored record",
        },
    }


@pytest.mark.parametrize("retired_uids", [(), ["u-2", 1]])
def test_a_consolidated_record_mutation_entry_refuses_malformed_retired_uids(retired_uids: object):
    node = stored.act_report_node(_mint(operation="consolidate", entries=(_consolidated_record_mutation_entry(),)))
    node.facets["act-report"]["entries"][0]["outcome"]["retired_uids"] = retired_uids
    with pytest.raises(MalformedRecord, match="malformed act-report entry"):
        stored.act_report_facet(node)


def test_boundary_minted_report_round_trips_as_one_covered_stamped_facet(act_report: ActReport):
    node = stored.act_report_node(act_report)

    assert node.kind == "act-report"
    assert node.id == f"act-report:{act_report.identity()}"
    assert node.title == "run-attempt report"
    assert node.relations == []
    assert node.facets["act-report"] == {
        "operation": "run-attempt",
        "event_token": act_report.event_token,
        "actor": "tester",
        "observer": "observer-1",
        "instrument": "beliefs.boundary/v1",
        "opened_at": "2026-08-12T00:00:00Z",
        "closed_at": "2026-08-12T00:00:00Z",
        "entries": [
            {
                "kind": "run-attempt",
                "subject": "absent",
                "outcome": {"type": "run-refusal", "missing_member": "no-frozen-spec"},
            }
        ],
    }
    assert set(node.facets) == {"act-report", stored.SEMANTIC_IDENTITY_FACET}
    assert stored.SEMANTIC_DOMAINS["act-report"] == ACT_REPORT_DOMAIN
    assert stored.COVERED_FACETS["act-report"] == ("act-report",)
    assert not stored.semantic_hash_missing(node)
    assert not stored.semantic_hash_disagrees(node)


def test_two_stored_mints_of_the_same_report_share_the_full_identity(act_report: ActReport):
    first = stored.act_report_node(act_report)
    repeated = stored.act_report_node(act_report)

    assert first.id == repeated.id
    assert first.id.removeprefix("act-report:") == act_report.identity()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("operation", "audit"),
        ("event_token", "different-event"),
        ("actor", "different-actor"),
        ("observer", "different-observer"),
        ("instrument", "different-instrument"),
        ("opened_at", "2026-08-12T00:01:00Z"),
        ("closed_at", "2026-08-12T00:01:00Z"),
        (
            "entries",
            (RunAttemptEntry(subject="different", outcome=RunRefusal(missing_member="input")),),
        ),
    ],
)
def test_changing_each_report_identity_field_moves_the_stored_id(act_report: ActReport, field: str, value: object):
    changed = changed_report(act_report, **{field: value})

    assert stored.act_report_node(changed).id != stored.act_report_node(act_report).id


def test_foreign_act_report_with_a_stale_stamp_is_detected(act_report: ActReport):
    minted = stored.act_report_node(act_report)
    facets = deepcopy(minted.facets)
    facets["act-report"]["actor"] = "foreign"
    foreign = Node(
        id=minted.id,
        kind="act-report",
        title=minted.title,
        facets=facets,
        relations=[],
    )

    assert stored.semantic_hash_disagrees(foreign)


def test_act_report_node_refuses_a_non_report_value():
    with pytest.raises(MalformedRecord, match="ActReport"):
        stored.act_report_node(object())  # type: ignore[arg-type]


def test_act_report_node_refuses_an_unencodable_boundary_report(tmp_path):
    with pytest.raises(MalformedRecord, match="canonically encodable"):
        run_assessment(tmp_path, spec=None.__class__, started_at="\ud800")
