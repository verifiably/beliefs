"""Cut 11's durable acceptance arms: genuine boundaries, real chains."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from closure_fixtures import make_closure, sample_report
from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.write_plan import CreateOp
from test_operation_port import durable_port

from science import root as science_root
from science import stored
from science.corpus import ReadView
from science.identity import v1
from science.intents.reduce import qualify_chain
from science.production import mint_dataset
from science.root import init_corpus_root
from science.runrecord import bare_address, decode_run_record, publication_plan, run_ref
from science.world.logmodel import IntentEntryView, WellFormedView
from science.world.records import capture_records


def _port(base, name):
    root = base / name
    init_corpus_root(root)
    return root, durable_port(root)


def _qualification(root):
    seam = science_root._log_seam()
    view = seam.inspect_registered(root)
    assert type(view) is WellFormedView
    return qualify_chain(
        view.entries,
        dict(capture_records(root, "corpus")),
        state_facts=seam.state_facts,
    )


def _append_assessment(port, *, spec="s" * 64, token="tok"):
    return port.append_intent(
        v1.encode({"spec_identity": spec, "event_token": token, "actor": "a"})
    )


def _append_operation(port, *, kind, token="tok"):
    return port.append_intent(v1.encode({"kind": kind, "event_token": token, "actor": "a"}))


def _report_plan(report):
    node = stored.act_report_node(report)
    return (
        CreateOp(
            f"act-report/{report.identity()}.md",
            node_to_markdown(node).encode("utf-8"),
        ),
    )


def _observation_plan(token="tok"):
    from science.holdings.records import Found, StoreLocator, holdings_observation

    value = holdings_observation(
        location=StoreLocator(store_id="0" * 32, relative_path="a/b"),
        outcome=Found("sha256:" + "1" * 64),
        observer="observer-1",
        instrument="instrument-1",
        event_token=token,
        observed_at="2026-08-27T00:00:00Z",
        supersedes=(),
    )
    node = stored.holdings_observation_node(value)
    return (
        CreateOp(
            f"holdings-observation/{value.identity()}.md",
            node_to_markdown(node).encode("utf-8"),
        ),
    )


def _non_qualifying_reason(findings):
    details = [
        finding.detail
        for finding in findings
        if finding.code == "intent-fulfillment-non-qualifying"
    ]
    assert len(details) == 1, findings
    return details[0]


def test_u2_wrong_purpose_member(certified_work):
    root, port = _port(certified_work, "u2-wrong-purpose")
    port.execute_fulfilling(_observation_plan(), _append_assessment(port))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-purpose" in _non_qualifying_reason(findings)


def test_u2_wrong_spec_member(certified_work):
    root, port = _port(certified_work, "u2-wrong-spec")
    _, _, plan = publication_plan(make_closure(spec="x" * 64))
    port.execute_fulfilling(plan, _append_assessment(port))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-spec" in _non_qualifying_reason(findings)


def test_u2_wrong_token_member(certified_work):
    root, port = _port(certified_work, "u2-wrong-token")
    _, _, plan = publication_plan(make_closure(token="other"))
    port.execute_fulfilling(plan, _append_assessment(port))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-token" in _non_qualifying_reason(findings)


def test_u2_no_record_member(certified_work):
    root, port = _port(certified_work, "u2-no-record")
    port.execute_fulfilling(
        (CreateOp("notes/memo.md", b"no record here"),),
        _append_assessment(port),
    )
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=no-record" in _non_qualifying_reason(findings)


def test_u3_decayed_genuine_run_is_unresolvable_silently(certified_work):
    root, port = _port(certified_work, "u3")
    closure = make_closure()
    _, path, plan = publication_plan(closure)
    port.execute_fulfilling(plan, _append_assessment(port))
    rows, _ = _qualification(root)
    assert rows[0].status == "matched"
    full = (root / path).read_bytes()
    (root / path).write_bytes(full[: len(full) // 2])
    rows, findings = _qualification(root)
    assert rows[0].status == "unresolvable"
    assert findings == ()


def test_u5_raced_appends_serialize_into_one_chain(certified_work):
    root, port = _port(certified_work, "u5")
    barrier = threading.Barrier(2)

    def append(token: str) -> str:
        barrier.wait()
        return _append_operation(port, kind="audit", token=token)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(append, token) for token in ("t1", "t2")]
        digests = [future.result() for future in futures]
    assert len(digests) == 2 and len(set(digests)) == 2
    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    chained = sorted(entry.digest for entry in view.entries if type(entry) is IntentEntryView)
    assert len(chained) == 2 and chained == sorted(digests)


class _Cancelled(BaseException):
    pass


def test_u8_negative_discarded_attempt_is_indistinguishable(certified_work, tmp_path):
    from fixtures_cut3 import run_assessment

    root, inner = _port(certified_work, "u8")

    class CancelledBeforePublication:
        def append_intent(self, payload: bytes) -> str:
            return inner.append_intent(payload)

        def execute(self, plan) -> None:
            raise _Cancelled()

        def execute_fulfilling(self, plan, fulfills: str) -> None:
            raise _Cancelled()

    with pytest.raises(_Cancelled):
        run_assessment(tmp_path, port=CancelledBeforePublication(), spec="not-a-spec")
    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    assert [entry for entry in view.entries if type(entry) is IntentEntryView] == []
    rows, findings = _qualification(root)
    assert rows == () and findings == ()


def test_u9_wrong_operation_token_fails_qualification(certified_work):
    root, port = _port(certified_work, "u9")
    port.execute_fulfilling(
        _report_plan(sample_report(operation="import", token="other")),
        _append_operation(port, kind="import"),
    )
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-token" in _non_qualifying_reason(findings)


def test_u10_wrong_kind_report_fails_qualification(certified_work):
    root, port = _port(certified_work, "u10")
    port.execute_fulfilling(
        _report_plan(sample_report(operation="audit", token="tok")),
        _append_operation(port, kind="import"),
    )
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-kind" in _non_qualifying_reason(findings)


def test_u11_run_for_non_run_operation_fails_qualification(certified_work):
    root, port = _port(certified_work, "u11")
    _, _, plan = publication_plan(make_closure())
    port.execute_fulfilling(plan, _append_operation(port, kind="import"))
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=wrong-purpose" in _non_qualifying_reason(findings)


def test_u12_no_terminal_record_fails_qualification(certified_work):
    root, port = _port(certified_work, "u12")
    port.execute_fulfilling(
        (CreateOp("notes/no-terminal.md", b"nothing"),),
        _append_operation(port, kind="import"),
    )
    rows, findings = _qualification(root)
    assert rows[0].status == "attempt-without-recorded-outcome"
    assert "reason=no-record" in _non_qualifying_reason(findings)


def test_bridge_resolves_assessment_ref_and_stamped_basis(certified_work):
    root, port = _port(certified_work, "bridge")
    closure = make_closure(shape="dataset-production")
    minted = mint_dataset(closure, existing_bases={})
    record_id, _, plan = publication_plan(closure)
    port.execute(plan)
    assert minted.basis.run == closure.address() and ":" not in minted.basis.run
    assert run_ref(minted.basis.run) == record_id
    view = ReadView.opened_at(root)
    assert view.resolve(run_ref(minted.basis.run)) == record_id
    assessment = stored.assessment_node(
        "a" * 64,
        title="assessment",
        spec="s" * 64,
        run=record_id,
        proposition="proposition:" + "p" * 64,
        outcome="supported",
        interpretation_rule="rule:interpretation",
    )
    port.execute(
        (
            CreateOp(
                f"assessment/{'a' * 64}.md",
                node_to_markdown(assessment).encode("utf-8"),
            ),
        )
    )
    view = ReadView.opened_at(root)
    stored_run_field = stored.assessment_value(view.get("assessment:" + "a" * 64)).run
    assert view.resolve(stored_run_field) == record_id
    assert bare_address(record_id) == minted.basis.run


@pytest.mark.parametrize(
    "case",
    [
        "assessment-run-publication",
        "assessment-report",
        "operation-report",
        "production-run",
        "production-report",
    ],
)
def test_positive_matched_per_alternative(case, certified_work):
    root, port = _port(certified_work, f"positive-{case}")
    if case.startswith("assessment"):
        fulfills = _append_assessment(port)
    else:
        kind = "import" if case == "operation-report" else "run-attempt"
        fulfills = _append_operation(port, kind=kind)
    if case == "assessment-run-publication":
        _, _, plan = publication_plan(make_closure())
    elif case == "production-run":
        _, _, plan = publication_plan(make_closure(shape="dataset-production"))
    else:
        operation = "import" if case == "operation-report" else "run-attempt"
        plan = _report_plan(sample_report(operation=operation, token="tok"))
    port.execute_fulfilling(plan, fulfills)
    rows, findings = _qualification(root)
    assert rows[0].status == "matched" and rows[0].fulfilled_by is not None
    assert findings == ()


def test_decimal_round_trip_publishes_and_captures(certified_work):
    values = [Decimal("0.5"), "0.5", 1, Decimal("1.0")]
    root, port = _port(certified_work, "decimal")
    published = []
    for value in values:
        closure = make_closure(parameters={"threshold": value})
        _, path, plan = publication_plan(closure)
        port.execute(plan)
        published.append((closure, path))
    records = dict(capture_records(root, "corpus"))
    addresses = set()
    for closure, path in published:
        publication = decode_run_record(node_from_markdown(records[path].decode("utf-8")))
        assert publication is not None and publication.address == closure.address()
        addresses.add(publication.address)
    assert len(addresses) == 4
