"""§5.4: the production boundary's bearer check shares the publication lock."""

import pytest
from authority import ACTOR, FULL
from closure_fixtures import make_closure
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import ContractMismatch
from beliefs.runrecord import publication_plan


def corpus(tmp_path):
    port = OperationRecorder(tmp_path, authority=FULL, profile=BASE)
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE, operation_port=port)
    writer.adopt_manifest(profile=pins_for(BASE))
    return writer, port


def test_the_guard_runs_under_the_lock_and_selects_the_plan(tmp_path):
    _, port = corpus(tmp_path)
    _, _, plan = publication_plan(make_closure(shape="dataset-production"))
    reason = port.execute_fulfilling_guarded(plan, "ab" * 32, guard=lambda view: None, fallback=lambda r: ())
    assert reason is None and port.fulfilling[-1][0] == list(plan)


def test_a_reason_publishes_the_fallback_and_returns_it(tmp_path):
    _, port = corpus(tmp_path)
    _, _, plan = publication_plan(make_closure(shape="dataset-production"))
    marker = [("fallback", ())]
    reason = port.execute_fulfilling_guarded(plan, "ab" * 32, guard=lambda view: "acquisition-boundary", fallback=lambda r: marker)
    assert reason == "acquisition-boundary" and port.fulfilling[-1][0] == marker


def test_a_pin_mismatch_under_the_lock_publishes_neither_plan(tmp_path):
    _, port = corpus(tmp_path)
    text = (tmp_path / "corpus.yaml").read_text()
    (tmp_path / "corpus.yaml").write_text(text.replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
    _, _, plan = publication_plan(make_closure(shape="dataset-production"))
    with pytest.raises(ContractMismatch):
        port.execute_fulfilling_guarded(plan, "ab" * 32, guard=lambda view: None, fallback=lambda r: ())
    assert not port.fulfilling


def test_the_acquisition_guard_reads_the_produced_address(tmp_path):
    """The guard the production boundary installs (§5.4). The boundary path itself
    runs durably in Task 15's acceptance module through `fixtures_cut15`'s
    production helper."""
    from beliefs.boundary import acquisition_guard
    from beliefs.production import mint_dataset

    writer, _ = corpus(tmp_path)
    closure = make_closure(shape="dataset-production")
    address = mint_dataset(closure, existing_bases={}).address
    assert acquisition_guard(closure)(writer.read_view) is None
    writer.add(stored.dataset_node(
        address.removeprefix("dataset:"),
        title="bearer",
        resources=[{"name": name, "digest": digest} for name, digest in closure.result.outputs],
        empirical_observation={"locator": "url:x", "attested_by": ACTOR},
    ))
    assert acquisition_guard(closure)(writer.read_view) == "acquisition-boundary"


def test_production_publishes_a_refusal_when_the_guard_finds_a_bearer(tmp_path, monkeypatch):
    from fixtures_cut3 import MemoryPort, run_production

    from beliefs.boundary import RunMinted, RunRefused, acquisition_guard
    from beliefs.production import mint_dataset

    first = run_production(tmp_path / "first", port=MemoryPort())
    assert isinstance(first, RunMinted)
    writer, port = corpus(tmp_path / "corpus")
    dataset = mint_dataset(first.run, existing_bases={})
    writer.add(stored.dataset_node(
        dataset.address.removeprefix("dataset:"),
        title="bearer",
        resources=[{"name": name, "digest": digest} for name, digest in first.run.result.outputs],
        empirical_observation={"locator": "url:x", "attested_by": ACTOR},
    ))
    assert acquisition_guard(first.run)(writer.read_view) == "acquisition-boundary"
    monkeypatch.setattr("beliefs.boundary._execute_run", lambda **kwargs: first)

    outcome = run_production(tmp_path / "second", port=port)

    assert isinstance(outcome, RunRefused) and outcome.reason == "acquisition-boundary"
    assert port.fulfilling[-1][0][0].path.startswith("act-report/")
