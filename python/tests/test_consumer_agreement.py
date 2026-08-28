"""Three-site consumer agreement: the rule, the verifier, completion (label 12)."""

import pytest
from closure_fixtures import make_closure, sample_report
from nodes.core.frontmatter import node_to_markdown
from test_holdings_reduce import (
    LOCATION,
    OTHER_LOCATION,
    REF_A,
    capture,
    corpus,
    file_row,
    intent,
    invoke,
    member,
    observation,
    registration,
    settlement,
)
from test_intent_reduce import FakeFile, _facts

from science import stored
from science.holdings.boundary import intent_payload
from science.holdings.records import Found, StoreLocator, holdings_observation
from science.identity import v1
from science.intents.reduce import qualify_chain
from science.report import (
    CLOSED,
    UNFINISHED,
    AssessmentRunIntent,
    OperationIntent,
    Registration,
    completion,
)
from science.runrecord import publication_plan
from science.world.logmodel import (
    EntryView,
    IntentEntryView,
    RegisteredEntryView,
    SettledEntryView,
)

OBSERVATION_PATH = f"holdings-observation/{REF_A}.md"
ABSENT_RECORD_PATH = "holdings-observation/" + "0" * 64 + ".md"


def _locator(location: str) -> StoreLocator:
    _, store_id, relative_path = location.split(":", 2)
    return StoreLocator(store_id, relative_path)


def holdings_wire(*, location: str, token: str) -> bytes:
    return intent_payload(
        location=_locator(location),
        act_kind="write",
        event_token=token,
        actor="actor",
    )


def observation_record(*, location: str, token: str) -> tuple[str, bytes]:
    value = holdings_observation(
        location=_locator(location),
        outcome=Found("sha256:" + "1" * 64),
        observer="observer",
        instrument="instrument",
        event_token=token,
        observed_at="2026-01-01T00:00:00Z",
    )
    node = stored.holdings_observation_node(value)
    return (
        f"holdings-observation/{value.identity()}.md",
        node_to_markdown(node).encode("utf-8"),
    )


MATRIX = {
    "matched": (
        {"location": LOCATION, "token": "tok"},
        "settled-file",
        "matched",
        False,
    ),
    "unresolved-unsettled-registration": (
        {"location": LOCATION, "token": "tok"},
        "unsettled",
        "unresolvable",
        True,
    ),
    "unresolved-settled-file-row-no-captured-record": (
        None,
        "settled-file",
        "unresolvable",
        True,
    ),
    "rolled-back": (
        {"location": LOCATION, "token": "tok"},
        "rolled-back",
        "attempt-without-recorded-outcome",
        True,
    ),
    "wrong-location": (
        {"location": OTHER_LOCATION, "token": "tok"},
        "settled-file",
        "attempt-without-recorded-outcome",
        True,
    ),
    "wrong-token": (
        {"location": LOCATION, "token": "other"},
        "settled-file",
        "attempt-without-recorded-outcome",
        True,
    ),
    "no-observation": (
        None,
        "settled-no-record",
        "attempt-without-recorded-outcome",
        True,
    ),
}

_BLOCKED_EMPTY_HEADS = {
    "active": [],
    "blocked": [{"location": LOCATION, "reasons": ["unsettled"], "heads": []}],
}
_BLOCKED_WITH_HEAD = {
    "active": [],
    "blocked": [
        {
            "location": LOCATION,
            "reasons": ["unsettled"],
            "heads": [member(REF_A)],
        }
    ],
}
RULE_RESULTS = {
    "matched": {"active": [member(REF_A)], "blocked": []},
    "unresolved-unsettled-registration": _BLOCKED_WITH_HEAD,
    "unresolved-settled-file-row-no-captured-record": _BLOCKED_EMPTY_HEADS,
    "rolled-back": _BLOCKED_WITH_HEAD,
    "wrong-location": {
        "active": [member(REF_A, location=OTHER_LOCATION)],
        "blocked": [
            {"location": LOCATION, "reasons": ["unsettled"], "heads": []}
        ],
    },
    "wrong-token": _BLOCKED_WITH_HEAD,
    "no-observation": _BLOCKED_EMPTY_HEADS,
}


@pytest.mark.parametrize("case", sorted(MATRIX))
def test_holdings_matrix_agrees_across_both_consumers(case) -> None:
    observation_kwargs, shape, verifier_status, rule_blocks = MATRIX[case]

    rows = [observation(REF_A, **observation_kwargs)] if observation_kwargs else []
    chain = [intent("1" * 64, location=LOCATION, token="tok")]
    final = [file_row(OBSERVATION_PATH)] if shape.startswith("settled-file") else []
    chain.append(registration("2" * 64, "1" * 64, final=final))
    if shape != "unsettled":
        outcome = "rolled-back" if shape == "rolled-back" else "committed"
        chain.append(settlement("3" * 64, "2" * 64, outcome=outcome))
    result = invoke(capture(corpus(chain=chain, records=rows)))
    assert result == RULE_RESULTS[case]
    assert bool(result["blocked"]) is rule_blocks

    entries: list[EntryView] = [
        IntentEntryView(
            digest="i1",
            payload=holdings_wire(location=LOCATION, token="tok"),
        )
    ]
    records: dict[str, bytes] = {}
    if observation_kwargs:
        record_path, record_bytes = observation_record(**observation_kwargs)
        records[record_path] = record_bytes
    else:
        record_path = ABSENT_RECORD_PATH
    final_rows = (
        ((record_path, FakeFile("f")),) if shape.startswith("settled-file") else ()
    )
    entries.append(
        RegisteredEntryView(
            digest="r1",
            txid="t1",
            intent_digest="intent",
            consumer_tag="consumer",
            initial=(),
            final=final_rows,
            fulfills="i1",
        )
    )
    if shape != "unsettled":
        entries.append(
            SettledEntryView(
                digest="s1",
                txid="t1",
                registration="r1",
                committed=shape != "rolled-back",
            )
        )
    verifier_rows, _ = qualify_chain(tuple(entries), records, state_facts=_facts)
    assert verifier_rows[0].status == verifier_status


def _verifier_status(
    wire_payload: bytes,
    record_path: str,
    record_bytes: bytes,
) -> str:
    entries = (
        IntentEntryView(digest="i1", payload=wire_payload),
        RegisteredEntryView(
            digest="r1",
            txid="t1",
            intent_digest="intent",
            consumer_tag="consumer",
            initial=(),
            final=((record_path, FakeFile("f")),),
            fulfills="i1",
        ),
        SettledEntryView(
            digest="s1",
            txid="t1",
            registration="r1",
            committed=True,
        ),
    )
    rows, _ = qualify_chain(
        entries,
        {record_path: record_bytes},
        state_facts=_facts,
    )
    return rows[0].status


_INTENTS = {
    "matching-assessment": AssessmentRunIntent("s" * 64, "tok", "actor"),
    "wrong-spec-assessment": AssessmentRunIntent("x" * 64, "tok", "actor"),
    "wrong-token-assessment": AssessmentRunIntent("s" * 64, "other", "actor"),
    "production-run-attempt": OperationIntent("run-attempt", "tok", "actor"),
    "non-run-import": OperationIntent("import", "tok", "actor"),
}


def _wire(value: AssessmentRunIntent | OperationIntent) -> bytes:
    if type(value) is AssessmentRunIntent:
        return v1.encode(
            {
                "spec_identity": value.spec_identity,
                "event_token": value.event_token,
                "actor": value.actor,
            }
        )
    return v1.encode(
        {
            "kind": value.kind,
            "event_token": value.event_token,
            "actor": value.actor,
        }
    )


def _held(name: str) -> tuple[object, str, bytes]:
    if name == "assessment":
        closure = make_closure()
        _, path, (operation,) = publication_plan(closure)
        return closure, path, operation.content
    if name == "production":
        closure = make_closure(shape="dataset-production")
        _, path, (operation,) = publication_plan(closure)
        return closure, path, operation.content
    operation = {
        "run-attempt-report": "run-attempt",
        "import-report": "import",
        "audit-report": "audit",
    }[name]
    report = sample_report(operation=operation, token="tok")
    node = stored.act_report_node(report)
    return (
        report,
        f"act-report/{report.identity()}.md",
        node_to_markdown(node).encode("utf-8"),
    )


def agreement_case(held_intent: str, closure_fixture: str) -> tuple:
    value = _INTENTS[held_intent]
    held_value, record_path, record_bytes = _held(closure_fixture)
    return value, _wire(value), held_value, record_path, record_bytes


@pytest.mark.parametrize(
    ("held_intent", "closure_fixture", "expected"),
    [
        ("matching-assessment", "assessment", CLOSED),
        ("wrong-spec-assessment", "assessment", UNFINISHED),
        ("wrong-token-assessment", "assessment", UNFINISHED),
        ("production-run-attempt", "production", CLOSED),
        ("production-run-attempt", "assessment", UNFINISHED),
        ("matching-assessment", "run-attempt-report", CLOSED),
        ("non-run-import", "import-report", CLOSED),
        ("non-run-import", "audit-report", UNFINISHED),
    ],
)
def test_run_shapes_agree_between_verifier_and_completion(
    held_intent,
    closure_fixture,
    expected,
) -> None:
    intent_value, wire_payload, held_value, record_path, record_bytes = (
        agreement_case(held_intent, closure_fixture)
    )
    held_answer = completion(
        intent_value,
        (Registration(intent_value.event_token, "pointer"),),
        {"pointer": held_value},
    )
    assert held_answer == expected
    status = _verifier_status(wire_payload, record_path, record_bytes)
    assert status == (
        "matched" if expected == CLOSED else "attempt-without-recorded-outcome"
    )
