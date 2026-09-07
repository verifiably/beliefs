"""Every durable relocation prefix and the data-only recovery table."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import pytest
from authority import FULL
from fixtures_cut6 import PINS
from nodes.core.frontmatter import node_from_markdown
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import CreateOp, DefaultExecutor
from profiles import WITH_BIOLOGY

from beliefs import boundary, relocation, stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import DuplicateLocation, RelocationTargetMissing
from beliefs.identity import v1
from beliefs.report import (
    CLOSED,
    UNFINISHED,
    Consolidated,
    Moved,
    OperationIntent,
    Registration,
    completion,
)

MOVE_PREFIXES = (
    "destination-intent",
    "source-intent",
    "destination-create",
    "source-delete",
    "destination-report",
)
CONSOLIDATE_PREFIXES = (
    "keep-intent",
    "other-intent",
    "keep-replace",
    "other-delete",
    "keep-report",
)


@pytest.mark.parametrize(
    ("stop_after", "expected"),
    (
        ("destination-intent", (True, False, 0, 1, 0, 0, 0, 0)),
        ("source-intent", (True, False, 1, 1, 0, 0, 0, 0)),
        ("destination-create", (True, True, 1, 1, 0, 0, 0, 0)),
        ("source-delete", (False, True, 1, 1, 0, 0, 0, 0)),
        ("destination-report", (False, True, 1, 1, 0, 1, 0, 1)),
    ),
)
def test_move_prefixes_are_exactly_the_enumerated_states(tmp_path, monkeypatch, stop_after, expected):
    attempt = _interrupted_move(tmp_path, monkeypatch, stop_after)

    assert _move_state(attempt) == expected


def test_a_move_interrupted_at_the_destination_create_is_a_duplicate_location(tmp_path, monkeypatch):
    attempt = _interrupted_move(tmp_path, monkeypatch, "destination-create")

    with pytest.raises(DuplicateLocation):
        relocation.move(attempt.source, attempt.destination, attempt.ref, **MOVE_FIELDS)


def test_that_duplicate_location_is_repaired_by_consolidate(tmp_path, monkeypatch):
    attempt = _interrupted_move(tmp_path, monkeypatch, "destination-create")
    original = _operation_snapshot(attempt)

    survivor, _, _ = relocation.consolidate(
        (attempt.destination, attempt.ref),
        (attempt.source, attempt.ref),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.id == attempt.ref
    assert not attempt.source.read_view.holds(attempt.ref)
    assert attempt.destination.read_view.holds(attempt.ref)
    _assert_fresh_recovery(attempt, original)
    assert _original_completions(attempt, original) == (
        UNFINISHED,
        UNFINISHED,
    )


@pytest.mark.parametrize(
    ("stop_after", "expected"),
    (
        ("source-delete", (UNFINISHED, UNFINISHED)),
        ("destination-report", (UNFINISHED, CLOSED)),
    ),
)
def test_a_move_interrupted_after_the_source_delete_cannot_be_completed(tmp_path, monkeypatch, stop_after, expected):
    attempt = _interrupted_move(tmp_path, monkeypatch, stop_after)
    original = _operation_snapshot(attempt)

    with pytest.raises(RelocationTargetMissing):
        relocation.move(attempt.source, attempt.destination, attempt.ref, **MOVE_FIELDS)

    assert not attempt.source.read_view.holds(attempt.ref)
    assert attempt.destination.read_view.holds(attempt.ref)
    assert _original_completions(attempt, original) == expected


@pytest.mark.parametrize(
    ("stop_after", "expected"),
    (
        ("keep-intent", (True, True, False, 1, 0, 0, 0, 0, 0)),
        ("other-intent", (True, True, False, 1, 1, 0, 0, 0, 0)),
        ("keep-replace", (True, True, True, 1, 1, 0, 0, 0, 0)),
        ("other-delete", (True, False, True, 1, 1, 0, 0, 0, 0)),
        ("keep-report", (True, False, True, 1, 1, 1, 0, 1, 0)),
    ),
)
def test_consolidate_prefixes_are_exactly_the_enumerated_states(tmp_path, monkeypatch, stop_after, expected):
    attempt = _interrupted_consolidate(tmp_path, monkeypatch, stop_after)

    assert _consolidate_state(attempt) == expected


@pytest.mark.parametrize("stop_after", ["keep-intent", "other-intent", "keep-replace"])
def test_consolidate_prefixes_two_to_four_repair_data_and_strand_the_original(tmp_path, monkeypatch, stop_after):
    attempt = _interrupted_consolidate(tmp_path, monkeypatch, stop_after)
    original = _operation_snapshot(attempt)

    survivor, _, _ = relocation.consolidate(
        (attempt.keep, attempt.ref),
        (attempt.other, attempt.ref),
        **CONSOLIDATE_FIELDS,
    )

    assert survivor.relations == attempt.expected_relations
    assert attempt.keep.read_view.holds(attempt.ref)
    assert not attempt.other.read_view.holds(attempt.ref)
    _assert_fresh_recovery(attempt, original)
    assert all(reading == UNFINISHED for reading in _original_completions(attempt, original) if reading is not None)


@pytest.mark.parametrize(
    ("stop_after", "expected"),
    (
        ("other-delete", (UNFINISHED, UNFINISHED)),
        ("keep-report", (CLOSED, UNFINISHED)),
    ),
)
def test_consolidate_after_the_other_delete_cannot_be_completed(tmp_path, monkeypatch, stop_after, expected):
    attempt = _interrupted_consolidate(tmp_path, monkeypatch, stop_after)
    original = _operation_snapshot(attempt)

    with pytest.raises(RelocationTargetMissing):
        relocation.consolidate(
            (attempt.keep, attempt.ref),
            (attempt.other, attempt.ref),
            **CONSOLIDATE_FIELDS,
        )

    assert attempt.keep.read_view.holds(attempt.ref)
    assert not attempt.other.read_view.holds(attempt.ref)
    assert _original_completions(attempt, original) == expected


@pytest.mark.parametrize(
    ("operation", "stop_after", "expected"),
    (
        ("move", "destination-intent", (None, UNFINISHED)),
        ("move", "source-intent", (UNFINISHED, UNFINISHED)),
        ("move", "destination-create", (UNFINISHED, UNFINISHED)),
        ("move", "source-delete", (UNFINISHED, UNFINISHED)),
        ("move", "destination-report", (UNFINISHED, CLOSED)),
        ("consolidate", "keep-intent", (UNFINISHED, None)),
        ("consolidate", "other-intent", (UNFINISHED, UNFINISHED)),
        ("consolidate", "keep-replace", (UNFINISHED, UNFINISHED)),
        ("consolidate", "other-delete", (UNFINISHED, UNFINISHED)),
        ("consolidate", "keep-report", (CLOSED, UNFINISHED)),
    ),
)
def test_no_recovery_ever_closes_the_interrupted_operation(tmp_path, monkeypatch, operation, stop_after, expected):
    attempt = _interrupted(operation, tmp_path, monkeypatch, stop_after)
    original = _operation_snapshot(attempt)

    recovered = _recover_data(attempt, stop_after)

    if recovered:
        _assert_fresh_recovery(attempt, original)
    if operation == "move":
        assert not attempt.source.read_view.holds(attempt.ref)
        assert attempt.destination.read_view.holds(attempt.ref)
    else:
        assert attempt.keep.read_view.get(attempt.ref).relations == (attempt.expected_relations)
        assert not attempt.other.read_view.holds(attempt.ref)
    assert _original_completions(attempt, original) == expected


@pytest.mark.parametrize("stop_after", MOVE_PREFIXES)
def test_a_move_never_loses_the_record_at_any_prefix(tmp_path, monkeypatch, stop_after):
    attempt = _interrupted_move(tmp_path, monkeypatch, stop_after)

    assert attempt.source.read_view.holds(attempt.ref) or attempt.destination.read_view.holds(attempt.ref)


MOVE_FIELDS = {
    "observer": "recovery-observer",
    "instrument": "recovery-test",
    "opened_at": "2026-09-03T10:00:00Z",
    "closed_at": "2026-09-03T10:00:01Z",
}
CONSOLIDATE_FIELDS = {
    **MOVE_FIELDS,
    "rationale": "keep the selected survivor",
}


class _Stop(Exception):
    pass


@dataclass(frozen=True)
class _IntentRecord:
    payload: bytes
    digest: str


class _HashingOperationPort:
    profile = WITH_BIOLOGY
    def __init__(self, root: Path, authority=FULL):
        self._inner = DefaultExecutor(root)
        self.authority = authority
        self.intents: list[_IntentRecord] = []
        self.executed: list[list[object]] = []
        self.fulfilling: list[tuple[list[object], str]] = []

    def append_intent(self, payload: bytes) -> str:
        digest = sha256(payload).hexdigest()
        self.intents.append(_IntentRecord(payload, digest))
        return digest

    def execute(self, plan) -> None:
        operations = list(plan)
        self._inner.execute(operations)
        self.executed.append(operations)

    def execute_fulfilling(self, plan, fulfills: str) -> None:
        operations = list(plan)
        self._inner.execute(operations)
        self.fulfilling.append((operations, fulfills))

    def execute_fulfilling_guarded(self, plan, fulfills: str, *, guard, fallback):
        raise AssertionError("never reached")


@dataclass(frozen=True)
class _Attempt:
    operation: str
    left: CorpusWriter
    right: CorpusWriter
    ref: str
    expected_relations: list[Relation]

    @property
    def source(self) -> CorpusWriter:
        return self.left

    @property
    def destination(self) -> CorpusWriter:
        return self.right

    @property
    def keep(self) -> CorpusWriter:
        return self.left

    @property
    def other(self) -> CorpusWriter:
        return self.right

    @property
    def ports(self) -> tuple[_HashingOperationPort, _HashingOperationPort]:
        ports = self.left._operation_port, self.right._operation_port
        assert all(isinstance(port, _HashingOperationPort) for port in ports)
        return ports  # type: ignore[return-value]


def _writer(root: Path) -> CorpusWriter:
    writer = CorpusWriter(
        root,
        DefaultExecutor, authority=FULL,
        operation_port=_HashingOperationPort(root),
        profile=WITH_BIOLOGY,
    )
    writer.adopt_manifest(profile=PINS)
    return writer


def _stop_after(monkeypatch, target: object, method_name: str) -> None:
    real = getattr(target, method_name)

    def run_then_stop(*args, **kwargs):
        real(*args, **kwargs)
        raise _Stop

    monkeypatch.setattr(target, method_name, run_then_stop)


def _interrupted_move(tmp_path, monkeypatch, stop_after: str) -> _Attempt:
    source = _writer(tmp_path / stop_after / "source")
    destination = _writer(tmp_path / stop_after / "destination")
    node = source.add(stored.source_node("recovery", title="recovery", identifiers={"doi": "10.1/recovery"}))
    targets = {
        "destination-intent": (destination, "_append_operation_intent"),
        "source-intent": (source, "_append_operation_intent"),
        "destination-create": (destination, "_add_locked"),
        "source-delete": (source, "_delete_locked"),
        "destination-report": (destination, "_publish_operation_report"),
    }
    _stop_after(monkeypatch, *targets[stop_after])
    with pytest.raises(_Stop):
        relocation.move(source, destination, node.id, **MOVE_FIELDS)
    monkeypatch.undo()
    return _Attempt("move", source, destination, node.id, [])


def _interrupted_consolidate(tmp_path, monkeypatch, stop_after: str) -> _Attempt:
    keep_writer = _writer(tmp_path / stop_after / "keep")
    other_writer = _writer(tmp_path / stop_after / "other")
    ref = "discussion:recovery"
    keep_relation = Relation(source=ref, predicate="cites", target="discussion:a")
    other_relation = Relation(source=ref, predicate="derived-from", target="discussion:b")
    keep_writer.add(Node(id=ref, kind="discussion", title="keep", relations=[keep_relation]))
    other_writer.add(Node(id=ref, kind="discussion", title="other", relations=[other_relation]))
    targets = {
        "keep-intent": (keep_writer, "_append_operation_intent"),
        "other-intent": (other_writer, "_append_operation_intent"),
        "keep-replace": (keep_writer, "_replace_locked"),
        "other-delete": (other_writer, "_delete_locked"),
        "keep-report": (keep_writer, "_publish_operation_report"),
    }
    _stop_after(monkeypatch, *targets[stop_after])
    with pytest.raises(_Stop):
        relocation.consolidate(
            (keep_writer, ref),
            (other_writer, ref),
            **CONSOLIDATE_FIELDS,
        )
    monkeypatch.undo()
    return _Attempt(
        "consolidate",
        keep_writer,
        other_writer,
        ref,
        [keep_relation, other_relation],
    )


def _interrupted(operation: str, tmp_path, monkeypatch, stop_after: str) -> _Attempt:
    if operation == "move":
        return _interrupted_move(tmp_path, monkeypatch, stop_after)
    return _interrupted_consolidate(tmp_path, monkeypatch, stop_after)


def _report_count(writer: CorpusWriter) -> int:
    return sum(node.kind == "act-report" for node in writer.read_view.iter_stored())


def _move_state(attempt: _Attempt) -> tuple[object, ...]:
    source_port, destination_port = attempt.ports
    return (
        attempt.source.read_view.holds(attempt.ref),
        attempt.destination.read_view.holds(attempt.ref),
        len(source_port.intents),
        len(destination_port.intents),
        len(source_port.fulfilling),
        len(destination_port.fulfilling),
        _report_count(attempt.source),
        _report_count(attempt.destination),
    )


def _consolidate_state(attempt: _Attempt) -> tuple[object, ...]:
    keep_port, other_port = attempt.ports
    keep_holds = attempt.keep.read_view.holds(attempt.ref)
    return (
        keep_holds,
        attempt.other.read_view.holds(attempt.ref),
        keep_holds and attempt.keep.read_view.get(attempt.ref).relations == attempt.expected_relations,
        len(keep_port.intents),
        len(other_port.intents),
        len(keep_port.fulfilling),
        len(other_port.fulfilling),
        _report_count(attempt.keep),
        _report_count(attempt.other),
    )


def _operation_snapshot(
    attempt: _Attempt,
) -> tuple[tuple[_IntentRecord, ...], tuple[_IntentRecord, ...]]:
    return tuple(tuple(port.intents) for port in attempt.ports)  # type: ignore[return-value]


def _intent(record: _IntentRecord) -> OperationIntent:
    value = v1.decode(record.payload)
    assert isinstance(value, dict)
    return OperationIntent(value["kind"], value["event_token"], value["actor"])


def _completion_for(port: _HashingOperationPort, record: _IntentRecord) -> str:
    intent = _intent(record)
    matches = [operations for operations, fulfills in port.fulfilling if fulfills == record.digest]
    if not matches:
        return completion(intent, (), {})
    assert len(matches) == 1 and len(matches[0]) == 1
    operation = matches[0][0]
    assert isinstance(operation, CreateOp)
    node = node_from_markdown(operation.content.decode("utf-8"))
    facet = stored.act_report_facet(node)
    assert (facet["operation"], facet["event_token"]) == (
        intent.kind,
        intent.event_token,
    )
    report = _report_from_facet(intent, facet)
    assert node.id == f"act-report:{report.identity()}"
    registration = Registration(intent.event_token, report.identity())
    return completion(intent, (registration,), {report.identity(): report})


def _report_from_facet(intent: OperationIntent, facet):
    entry = facet["entries"][0]
    outcome = entry["outcome"]
    if outcome["type"] == "moved":
        result = Moved(
            outcome["source_corpus"],
            outcome["destination_corpus"],
            outcome["ref"],
        )
    else:
        result = Consolidated(
            outcome["kept_corpus"],
            outcome["kept_ref"],
            outcome["other_corpus"],
            outcome["other_ref"],
            tuple(outcome["retired_uids"]),
            outcome["rationale"],
        )
    return boundary._mint_relocation_report(
        intent,
        subject=entry["subject"],
        corpus=entry["corpus"],
        observer=facet["observer"],
        instrument=facet["instrument"],
        opened_at=facet["opened_at"],
        closed_at=facet["closed_at"],
        outcome=result,
    )


def _original_completions(
    attempt: _Attempt,
    original: tuple[tuple[_IntentRecord, ...], tuple[_IntentRecord, ...]],
) -> tuple[str | None, str | None]:
    return tuple(
        _completion_for(port, records[0]) if records else None
        for port, records in zip(attempt.ports, original, strict=True)
    )  # type: ignore[return-value]


def _assert_fresh_recovery(
    attempt: _Attempt,
    original: tuple[tuple[_IntentRecord, ...], tuple[_IntentRecord, ...]],
) -> None:
    old_tokens = {_intent(record).event_token for records in original for record in records}
    old_digests = {record.digest for records in original for record in records}
    new_by_root = tuple(
        tuple(port.intents[len(records) :]) for port, records in zip(attempt.ports, original, strict=True)
    )
    assert all(len(records) == 1 for records in new_by_root)
    new_tokens = {_intent(records[0]).event_token for records in new_by_root}
    new_digests = {records[0].digest for records in new_by_root}
    assert len(new_tokens) == len(new_digests) == 1
    assert new_tokens.isdisjoint(old_tokens)
    assert new_digests.isdisjoint(old_digests)
    for port, old_records, new_records in zip(attempt.ports, original, new_by_root, strict=True):
        fulfilled = {digest for _, digest in port.fulfilling}
        assert new_records[0].digest in fulfilled
        assert all(record.digest not in fulfilled for record in old_records)


def _recover_data(attempt: _Attempt, stop_after: str) -> bool:
    if attempt.operation == "move":
        if stop_after in {"destination-intent", "source-intent"}:
            relocation.move(
                attempt.source,
                attempt.destination,
                attempt.ref,
                **MOVE_FIELDS,
            )
            return True
        if stop_after == "destination-create":
            relocation.consolidate(
                (attempt.destination, attempt.ref),
                (attempt.source, attempt.ref),
                **CONSOLIDATE_FIELDS,
            )
            return True
        with pytest.raises(RelocationTargetMissing):
            relocation.move(
                attempt.source,
                attempt.destination,
                attempt.ref,
                **MOVE_FIELDS,
            )
        return False
    if stop_after in {"keep-intent", "other-intent", "keep-replace"}:
        relocation.consolidate(
            (attempt.keep, attempt.ref),
            (attempt.other, attempt.ref),
            **CONSOLIDATE_FIELDS,
        )
        return True
    with pytest.raises(RelocationTargetMissing):
        relocation.consolidate(
            (attempt.keep, attempt.ref),
            (attempt.other, attempt.ref),
            **CONSOLIDATE_FIELDS,
        )
    return False
