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
        profile = inner.profile

        def append_intent(self, payload):
            inner.append_intent(payload)
            raise _Killed()

        def preflight(self, plan):
            raise AssertionError("no publication may run")

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


def test_kill_between_append_and_start_leaves_intent_only_operation_kind(certified_work, monkeypatch) -> None:
    root, inner = _observer_port(certified_work)

    class KilledAfterAppend:
        authority = inner.authority
        profile = inner.profile

        def append_intent(self, payload):
            inner.append_intent(payload)
            raise _Killed()

        def preflight(self, plan):
            raise AssertionError("no publication may run")

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
    from hashlib import sha256

    from fixtures_cut3 import DATA_ADDRESS, READS_ADDRESS, stage
    from nodes.core.frontmatter import node_to_markdown
    from nodes.core.paths import path_for_node_id
    from profiles import BASE

    from beliefs.audit import NO_EVIDENCE, audit_corpus
    from beliefs.boundary import execute_production_run
    from beliefs.corpus import ReadView, corpus_check
    from beliefs.recipe import MINIMAL_POLICY, RecipeInput
    from beliefs.spec import Deterministic

    root, port = _observer_port(certified_work)
    code, held = stage(certified_work / "work", snakefile=SNAKEFILE_PRODUCTION)
    supplied = {
        DATA_ADDRESS: held / "data.txt",
        READS_ADDRESS: held / "palette.txt",
    }
    raw_digest = "sha256:" + sha256(supplied[DATA_ADDRESS].read_bytes()).hexdigest()
    reads_digest = "sha256:" + sha256(supplied[READS_ADDRESS].read_bytes()).hexdigest()
    raw_dataset = stored.dataset_node(
        title="raw input",
        resources=[{"name": "data.txt", "digest": raw_digest}],
        empirical_observation={"locator": "url:https://example.org/raw", "attested_by": port.authority.actor},
    )
    reads_dataset = stored.dataset_node(
        title="auxiliary reads",
        resources=[{"name": "palette.txt", "digest": reads_digest}],
        empirical_observation={"locator": "url:https://example.org/reads", "attested_by": port.authority.actor},
    )
    port.execute(
        [
            CreateOp(
                path=path_for_node_id(raw_dataset.id),
                content=node_to_markdown(raw_dataset).encode("utf-8"),
            ),
            CreateOp(
                path=path_for_node_id(reads_dataset.id),
                content=node_to_markdown(reads_dataset).encode("utf-8"),
            ),
        ]
    )

    result = execute_production_run(
        inputs=(
            RecipeInput(role="transforms", dataset=raw_dataset.id, content=raw_digest),
            RecipeInput(role="reads", dataset=reads_dataset.id, content=reads_digest),
        ),
        parameters={},
        nondeterminism=Deterministic(),
        port=port,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION, family_streams={}),
        code_roots=(code,),
        held_inputs={raw_dataset.id: supplied[DATA_ADDRESS], reads_dataset.id: supplied[READS_ADDRESS]},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=certified_work / "work" / "scratch",
        cores=1,
        dataset_title="curated package",
    )
    assert type(result) is RunMinted
    entries = _entries(root)
    (intent,) = [entry for entry in entries if type(entry) is IntentEntryView]
    fulfilling_regs = [
        entry for entry in entries if type(entry) is RegisteredEntryView and entry.fulfills == intent.digest
    ]
    assert len(fulfilling_regs) == 1
    registration = fulfilling_regs[0]
    address = result.run.address()
    run_id = runrecord.run_ref(address)
    node = node_from_markdown((root / "run" / f"{address}.md").read_text())
    minted = mint_dataset(result.run, existing_bases={})
    assert stored.inputs_of(node, "produces") == (minted.address,)
    assert node.facets["run"] == {}

    dataset_rel_path = path_for_node_id(minted.address)
    assert {p for p, _ in registration.final} >= {f"run/{address}.md", dataset_rel_path}
    dataset_bytes = (root / dataset_rel_path).read_bytes()
    dataset_node = node_from_markdown(dataset_bytes.decode("utf-8"))
    assert dataset_node.id == minted.address
    assert dataset_node.title == "curated package"
    assert stored.lineage_basis(dataset_node) == {
        "tag": "single",
        "routes": [
            {
                "run": run_id,
                "ancestor": raw_dataset.id,
                "transforms": [raw_dataset.id],
            }
        ],
    }
    view = ReadView.opened_at(root)
    assert corpus_check(view, BASE) == ()
    assert audit_corpus(view, evidence=NO_EVIDENCE, profile=BASE) == ()

    # Second execution when dataset:sha256:<hex> is already held in the corpus:
    # commits only run:<addr2> via _DATASET_ALREADY_HELD, preserves dataset node and basis.
    second = execute_production_run(
        inputs=(
            RecipeInput(role="transforms", dataset=raw_dataset.id, content=raw_digest),
            RecipeInput(role="reads", dataset=reads_dataset.id, content=reads_digest),
        ),
        parameters={},
        nondeterminism=Deterministic(),
        port=port,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION, family_streams={}),
        code_roots=(code,),
        held_inputs={raw_dataset.id: supplied[DATA_ADDRESS], reads_dataset.id: supplied[READS_ADDRESS]},
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:05:00Z",
        host_realization="host-a",
        scratch_base=certified_work / "work" / "scratch-2",
        cores=1,
        dataset_title="different title that must not overwrite",
    )
    assert type(second) is RunMinted
    address2 = second.run.address()
    assert address2 != address
    assert (root / "run" / f"{address2}.md").is_file()
    assert (root / dataset_rel_path).read_bytes() == dataset_bytes

    entries_after = _entries(root)
    intents_after = [entry for entry in entries_after if type(entry) is IntentEntryView]
    assert len(intents_after) == 2
    (second_reg,) = [
        entry
        for entry in entries_after
        if type(entry) is RegisteredEntryView and entry.fulfills == intents_after[1].digest
    ]
    assert [p for p, _ in second_reg.final] == [f"run/{address2}.md"]

    view_after = ReadView.opened_at(root)
    preserved_dataset = view_after.get(minted.address)
    assert preserved_dataset.title == "curated package"
    assert stored.lineage_basis(preserved_dataset) == {
        "tag": "single",
        "routes": [
            {
                "run": run_id,
                "ancestor": raw_dataset.id,
                "transforms": [raw_dataset.id],
            }
        ],
    }
    assert corpus_check(view_after, BASE) == ()
    assert audit_corpus(view_after, evidence=NO_EVIDENCE, profile=BASE) == ()


def test_production_pre_intent_refusal_publishes_unfulfilling_report(certified_work) -> None:
    from fixtures_cut3 import DATA_ADDRESS, READS_ADDRESS, stage

    from beliefs.boundary import execute_production_run
    from beliefs.recipe import MINIMAL_POLICY, RecipeInput
    from beliefs.spec import Deterministic

    root, port = _observer_port(certified_work)
    code, held = stage(certified_work / "work", snakefile=SNAKEFILE_PRODUCTION)
    supplied = {
        DATA_ADDRESS: held / "data.txt",
        READS_ADDRESS: held / "palette.txt",
    }
    refused_transforms = execute_production_run(
        inputs=(),
        parameters={},
        nondeterminism=Deterministic(),
        port=port,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION, family_streams={}),
        code_roots=(code,),
        held_inputs=supplied,
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=certified_work / "work" / "scratch-1",
        cores=1,
    )
    assert type(refused_transforms) is RunRefused and refused_transforms.reason == "malformed-inputs"
    assert refused_transforms.registration is None and refused_transforms.report is not None
    assert (root / "act-report" / f"{refused_transforms.report.identity()}.md").is_file()

    refused_title = execute_production_run(
        inputs=(RecipeInput(role="transforms", dataset=DATA_ADDRESS, content="sha256:" + "a" * 64),),
        parameters={},
        nondeterminism=Deterministic(),
        port=port,
        boundary_policy=MINIMAL_POLICY,
        definition=definition(snakefile=SNAKEFILE_PRODUCTION, family_streams={}),
        code_roots=(code,),
        held_inputs=supplied,
        entrypoint="code/workflow/Snakefile",
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        observer="observer-1",
        started_at="2026-08-12T00:00:00Z",
        host_realization="host-a",
        scratch_base=certified_work / "work" / "scratch-2",
        cores=1,
        dataset_title="   ",
    )
    assert type(refused_title) is RunRefused and refused_title.reason == "malformed-inputs"
    assert refused_title.registration is None and refused_title.report is not None
    assert (root / "act-report" / f"{refused_title.report.identity()}.md").is_file()
    entries = _entries(root)
    assert [entry for entry in entries if type(entry) is IntentEntryView] == []


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
