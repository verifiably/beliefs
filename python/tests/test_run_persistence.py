import inspect

import pytest
from authority import FULL
from fixtures_cut3 import (
    SNAKEFILE_DETERMINISTIC,
    SNAKEFILE_PRODUCTION,
    SNAKEFILE_SCRATCHY,
    definition,
    replay_of,
    run_assessment,
    run_production,
)
from nodes.core.errors import ExecutionError
from nodes.core.frontmatter import node_from_markdown
from nodes.core.write_plan import CreateOp
from test_operation_port import durable_port

from beliefs import root as science_root
from beliefs import runrecord, stored
from beliefs.boundary import RunMinted, RunRefused
from beliefs.production import mint_dataset
from beliefs.root import init_corpus_root
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView


def _observer_port(base):
    root = base / "observer"
    init_corpus_root(root, authority=FULL)
    return root, durable_port(root)


def _entries(root):
    chain = science_root._log_seam().inspect_registered(root)
    assert type(chain) is WellFormedView
    return chain.entries


def test_assessment_sequence_appends_intent_then_publishes_fulfilling(certified_work) -> None:
    root, port = _observer_port(certified_work)
    result = run_assessment(certified_work / "work", port=port)
    assert type(result) is RunMinted
    entries = _entries(root)
    intents = [entry for entry in entries if type(entry) is IntentEntryView]
    registrations = [entry for entry in entries if type(entry) is RegisteredEntryView]
    assert len(intents) == 1 and len(registrations) == 1
    assert entries.index(intents[0]) < entries.index(registrations[0])
    assert registrations[0].fulfills == intents[0].digest
    address = result.run.address()
    record = (root / "run" / f"{address}.md").read_bytes()
    publication = runrecord.decode_run_record(node_from_markdown(record.decode("utf-8")))
    assert publication is not None
    assert publication.address == address
    assert publication.spec_identity == result.run.recipe.spec_identity
    assert publication.event_token == result.intent.event_token


def test_pre_intent_refusal_publishes_unfulfilling_report(certified_work) -> None:
    root, port = _observer_port(certified_work)
    result = run_assessment(certified_work / "work", port=port, spec="not-a-spec")
    assert type(result) is RunRefused and result.registration is None
    entries = _entries(root)
    assert [type(entry) for entry in entries if type(entry) is IntentEntryView] == []
    (registration,) = [entry for entry in entries if type(entry) is RegisteredEntryView]
    assert registration.fulfills is None
    assert result.report is not None
    assert (root / "act-report" / f"{result.report.identity()}.md").exists()


def test_post_intent_refusal_publishes_fulfilling_report(certified_work) -> None:
    root, port = _observer_port(certified_work)
    result = run_assessment(
        certified_work / "work",
        port=port,
        snakefile=SNAKEFILE_DETERMINISTIC,
        definition_override=definition(snakefile=SNAKEFILE_SCRATCHY),
    )
    assert type(result) is RunRefused and result.reason == "definition-mismatch"
    entries = _entries(root)
    (intent_entry,) = [entry for entry in entries if type(entry) is IntentEntryView]
    (registration,) = [entry for entry in entries if type(entry) is RegisteredEntryView]
    assert registration.fulfills == intent_entry.digest


class _Killed(BaseException):
    pass


def test_kill_between_append_and_start_leaves_intent_only(certified_work, monkeypatch) -> None:
    root, inner = _observer_port(certified_work)

    class KilledAfterAppend:
        authority = inner.authority

        def append_intent(self, payload):
            inner.append_intent(payload)
            raise _Killed()

        def execute(self, plan):
            raise AssertionError("no publication may run")

        def execute_fulfilling(self, plan, fulfills):
            raise AssertionError("no publication may run")

    engine_calls: list[object] = []
    monkeypatch.setattr("beliefs.boundary.run_engine", lambda *args, **kwargs: engine_calls.append(args))
    with pytest.raises(_Killed):
        run_assessment(certified_work / "work", port=KilledAfterAppend())
    entries = _entries(root)
    assert all(type(entry) is not RegisteredEntryView for entry in entries)
    assert len([entry for entry in entries if type(entry) is IntentEntryView]) == 1
    assert engine_calls == []
    assert not (root / "run").exists() and not (root / "act-report").exists()


def test_kill_between_append_and_start_leaves_intent_only_operation_kind(
    certified_work, monkeypatch
) -> None:
    root, inner = _observer_port(certified_work)

    class KilledAfterAppend:
        authority = inner.authority

        def append_intent(self, payload):
            inner.append_intent(payload)
            raise _Killed()

        def execute(self, plan):
            raise AssertionError("no publication may run")

        def execute_fulfilling(self, plan, fulfills):
            raise AssertionError("no publication may run")

    engine_calls: list[object] = []
    monkeypatch.setattr("beliefs.boundary.run_engine", lambda *args, **kwargs: engine_calls.append(args))
    with pytest.raises(_Killed):
        run_production(certified_work / "work", port=KilledAfterAppend())
    entries = _entries(root)
    assert all(type(entry) is not RegisteredEntryView for entry in entries)
    assert len([entry for entry in entries if type(entry) is IntentEntryView]) == 1
    assert engine_calls == []
    assert not (root / "run").exists() and not (root / "act-report").exists()


def test_cross_root_publication_refuses(certified_work) -> None:
    root_a, root_b = certified_work / "a", certified_work / "b"
    init_corpus_root(root_a, authority=FULL)
    init_corpus_root(root_b, authority=FULL)
    port_a, port_b = durable_port(root_a), durable_port(root_b)
    port_b.execute([CreateOp(path="act-report/" + "0" * 64 + ".md", content=b"serviceable")])
    digest_on_a = port_a.append_intent(b'{"actor":"a","event_token":"t","kind":"import"}')
    with pytest.raises(ExecutionError):
        port_b.execute_fulfilling(
            [CreateOp(path="run/" + "1" * 64 + ".md", content=b"record")],
            digest_on_a,
        )
    assert not (root_a / "run").exists() and not (root_b / "run").exists()


def test_production_sequence_publishes_fulfilling_with_one_produces_edge(
    certified_work,
) -> None:
    root, port = _observer_port(certified_work)
    result = run_production(certified_work / "work", port=port)
    assert type(result) is RunMinted
    entries = _entries(root)
    (intent,) = [entry for entry in entries if type(entry) is IntentEntryView]
    (registration,) = [entry for entry in entries if type(entry) is RegisteredEntryView]
    assert registration.fulfills == intent.digest
    address = result.run.address()
    node = node_from_markdown((root / "run" / f"{address}.md").read_text())
    minted = mint_dataset(result.run, existing_bases={})
    assert stored.inputs_of(node, "produces") == (minted.address,)
    assert node.facets["run"] == {}


def test_replay_recipe_mismatch_publishes_refusal_not_run(certified_work) -> None:
    _, port = _observer_port(certified_work)
    original = run_assessment(certified_work / "original", port=port)
    assert type(original) is RunMinted
    replay_root = certified_work / "replay-observer"
    init_corpus_root(replay_root, authority=FULL)
    outcome = replay_of(
        original,
        certified_work / "replayed",
        port=durable_port(replay_root),
        snakefile=SNAKEFILE_SCRATCHY,
    )
    assert type(outcome) is RunRefused
    assert outcome.reason == "recipe-identity-mismatch"
    assert outcome.report is not None
    entries = _entries(replay_root)
    (intent_entry,) = [entry for entry in entries if type(entry) is IntentEntryView]
    (registration,) = [entry for entry in entries if type(entry) is RegisteredEntryView]
    assert registration.fulfills == intent_entry.digest
    assert not (replay_root / "run").exists()
    assert (replay_root / "act-report" / f"{outcome.report.identity()}.md").exists()


def test_replay_recipe_mismatch_publishes_refusal_not_run_production(certified_work) -> None:
    _, port = _observer_port(certified_work)
    original = run_production(certified_work / "original", port=port)
    assert type(original) is RunMinted
    changed = SNAKEFILE_PRODUCTION.replace(
        "import pathlib",
        "import pathlib  # changed recipe",
    )
    replay_root = certified_work / "replay-observer"
    init_corpus_root(replay_root, authority=FULL)
    outcome = replay_of(
        original,
        certified_work / "replayed",
        port=durable_port(replay_root),
        snakefile=changed,
    )
    assert type(outcome) is RunRefused
    assert outcome.reason == "recipe-identity-mismatch"
    assert outcome.report is not None
    entries = _entries(replay_root)
    (intent_entry,) = [entry for entry in entries if type(entry) is IntentEntryView]
    (registration,) = [entry for entry in entries if type(entry) is RegisteredEntryView]
    assert registration.fulfills == intent_entry.digest
    assert not (replay_root / "run").exists()
    assert (replay_root / "act-report" / f"{outcome.report.identity()}.md").exists()


def test_no_caller_supplied_fulfills_path_exists() -> None:
    from beliefs.boundary import execute_assessment_run, execute_production_run

    for entrypoint in (execute_assessment_run, execute_production_run):
        assert "fulfills" not in inspect.signature(entrypoint).parameters
