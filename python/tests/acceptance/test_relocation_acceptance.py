"""Cut 16's relocation arms on registered durable corpus roots."""

from __future__ import annotations

import inspect
import os
import shutil
from dataclasses import replace
from hashlib import sha256
from itertools import count
from pathlib import Path

import pytest
import yaml
from authority import ACTOR, FULL
from durable_fixture import basis, route, slug
from fixtures_cut3 import report as sample_report
from fixtures_cut6 import PINS
from fixtures_cut15 import SNAKEFILE_CONSTANT_PRODUCTION, run_workflow
from nodes.core.errors import RefError
from nodes.core.frontmatter import node_from_markdown
from nodes.core.node import Node
from nodes.core.relations import Relation
from test_belief import scenario as belief_scenario
from test_world_epoch import derivation_bindings

from beliefs import relocation, root, runrecord, stored
from beliefs.belief import Belief, evaluate
from beliefs.boundary import RunMinted
from beliefs.consulted import CorpusPins
from beliefs.corpus import lineage_snapshot
from beliefs.errors import (
    AddressDisagreement,
    ContractPinDisagreement,
    MalformedRecord,
    RelocationKindExcluded,
    RelocationTargetMissing,
    SameRootRefused,
)
from beliefs.identity import v1
from beliefs.lineage import certify
from beliefs.production import mint_dataset
from beliefs.recipe import RecipeInput
from beliefs.runrecord import run_ref
from beliefs.world import WorldConfig, derive, epoch, registry, rules
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView

MOVE_FIELDS = {
    "observer": "observer",
    "instrument": "instrument",
    "opened_at": "2026-09-03T10:00:00Z",
    "closed_at": "2026-09-03T10:00:01Z",
}
CONSOLIDATE_FIELDS = {**MOVE_FIELDS, "rationale": "keep the authored record"}

_COUNTER = count()

_COREFERENCE_BALANCE = {
    "pairs": [
        {
            "endpoints": ["dataset:subject-a", "dataset:subject-b"],
            "balance": 1,
            "distinct_key_count": 1,
        }
    ]
}
_COREFERENCE_SOURCE = b'''def reduce_coreference(capture):
    return {
        "pairs": [
            {
                "endpoints": ["dataset:subject-a", "dataset:subject-b"],
                "balance": 1,
                "distinct_key_count": 1,
            }
        ]
    }
'''


@pytest.fixture()
def durable_factory(work_directory):
    """Mint isolated registered roots and remove each root and metadata peer."""
    managed: list[Path] = []

    def writer(label: str, pins: CorpusPins = PINS):
        corpus_root = work_directory / f"cut16-{os.getpid()}-{next(_COUNTER)}-{label}"
        root.init_corpus_root(corpus_root, authority=FULL)
        opened = root.open_corpus(corpus_root, authority=FULL)
        opened.adopt_manifest(profile=pins)
        managed.append(corpus_root)
        return opened

    def world(label: str, *writers):
        world_root = work_directory / f"cut16-{os.getpid()}-{next(_COUNTER)}-{label}-world"
        config = WorldConfig(world_root, f"{next(_COUNTER):032x}"[-32:], tuple(w.root for w in writers))
        root.init_world_root(config, authority=FULL)
        opened = root.open_world(config, authority=FULL)
        for corpus in writers:
            opened.admit(corpus.root, provenance=registry.Fresh())
        bindings = derivation_bindings(opened)
        managed.append(world_root)
        return opened, tuple(corpus.corpus_id for corpus in writers), bindings

    yield writer, world

    for managed_root in managed:
        shutil.rmtree(managed_root, ignore_errors=True)
        shutil.rmtree(root.metadata_root_for(managed_root), ignore_errors=True)


def _publish(case):
    world, coverage, bindings = case
    return epoch.build_epoch(world, coverage=frozenset(coverage), bindings=bindings)


def _with_coreference_balance(case):
    world, coverage, bindings = case
    fixture = yaml.safe_dump(
        {"input": {"coverage": [], "records": []}, "expected": _COREFERENCE_BALANCE},
        sort_keys=False,
    ).encode()
    binding = rules.install_rule_binding(
        world,
        rules.RuleBundle(
            symbol="reduce_coreference",
            fixtures=(("cut16.balance.yaml", fixture),),
            implementation=_COREFERENCE_SOURCE,
        ),
    )
    return world, coverage, replace(bindings, coreference=binding)


def _published_snapshot(published):
    snapshot = derive.producer_snapshot(yaml.safe_load(published.members["producer-snapshot.yaml"]))
    assert yaml.safe_load(published.members["producers-map.yaml"]) == derive.producers_map_projection(
        snapshot.producers
    )
    return snapshot


def _belief_digest(published):
    snapshot = _published_snapshot(published)
    address_map = yaml.safe_load(published.members["address-map.yaml"])["addresses"]
    ordinary = belief_scenario()
    result = evaluate(
        **{
            **ordinary,
            "context": replace(
                ordinary["context"],
                producer_snapshot_identity=snapshot.identity(),
                node_corpus={row["address"]: row["corpus_id"] for row in address_map},
            ),
        }
    )
    assert isinstance(result, Belief)
    return result.belief_input_digest


def _receipt_belief_input(published) -> str:
    carrier = published.receipts["producer-receipt.yaml"]
    assert carrier.subject_identity is not None
    assert carrier.corpus_states is not None
    binding = carrier.binding
    assert binding is not None
    receipt = derive.DerivationReceipt(
        kind="producer",
        subject_identity=carrier.subject_identity,
        corpus_states=carrier.corpus_states,
        rule_identity=binding[0],
        implementation_identity=binding[1],
    )
    return derive.belief_input_identity((receipt,))


def _move_produced_dataset(durable_factory):
    writer, make_world = durable_factory
    source = writer("move-source")
    destination = writer("move-destination")
    dataset = source.add(
        stored.dataset_node(
            "moved",
            title="moved",
            resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
        )
    )
    run = source.add(
        stored.run_node(
            "producer",
            title="producer",
            spec="analysis-spec:producer",
            produces=[dataset.id],
        )
    )
    world = make_world("move", source, destination)
    before = _publish(world)
    states_before = {corpus.corpus_id: registry.corpus_state_identity(corpus.root) for corpus in (source, destination)}
    entry_starts = {corpus.root: len(_entries(corpus.root)) for corpus in (source, destination)}
    moved, destination_report, source_report = relocation.move(source, destination, dataset.id, **MOVE_FIELDS)
    after = _publish(world)
    states_after = {corpus.corpus_id: registry.corpus_state_identity(corpus.root) for corpus in (source, destination)}
    for published in (before, after):
        assert dict(_published_snapshot(published).producers) == {dataset.id: (run.id,)}
    return {
        "source": source,
        "destination": destination,
        "dataset": dataset,
        "run": run,
        "moved": moved,
        "before": before,
        "after": after,
        "states_before": states_before,
        "states_after": states_after,
        "entry_starts": entry_starts,
        "destination_report": destination_report,
        "source_report": source_report,
    }


def _route(name: str) -> dict[str, object]:
    return {
        "identity": f"route:{name}",
        "run": f"run:{name}",
        "ancestor": f"dataset:{name}",
        "transforms": [f"dataset:{name}"],
    }


def _dataset(name: str, routes: list[str], *, tag: str = "single"):
    return stored.dataset_node(
        name,
        title=name,
        resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
        basis={"tag": tag, "routes": [_route(route) for route in routes]},
    )


def _entries(corpus_root: Path):
    view = root._log_seam().inspect_registered(corpus_root)
    assert type(view) is WellFormedView
    return view.entries


def _registrations_for_path(corpus_root: Path, path: str):
    return tuple(
        entry
        for entry in _entries(corpus_root)
        if type(entry) is RegisteredEntryView
        and path in {name for name, _state in (*entry.initial, *entry.final)}
    )


def _produce_single_basis(
    producer,
    writer,
    work_dir: Path,
    *,
    input_address: str,
    text: str,
    deprecated_ids: tuple[str, ...],
    relations: tuple[tuple[str, str, dict[str, str]], ...],
):
    held = work_dir / "data.txt"
    work_dir.mkdir(parents=True, exist_ok=True)
    held.write_text(text)
    digest = "sha256:" + sha256(held.read_bytes()).hexdigest()
    writer.add(
        stored.dataset_node(
            slug(input_address),
            title=slug(input_address),
            resources=[{"name": "data", "digest": digest}],
        )
    )
    assert producer._operation_port is not None
    outcome = run_workflow(
        work_dir / "workflow",
        port=producer._operation_port,
        snakefile=SNAKEFILE_CONSTANT_PRODUCTION,
        targets=("outputs/result.txt",),
        declared_outputs=("outputs/result.txt",),
        inputs=(RecipeInput(role="transforms", dataset=input_address, content=digest),),
        held_inputs={input_address: held},
    )
    assert isinstance(outcome, RunMinted)
    minted = mint_dataset(outcome.run, existing_bases={})
    assert minted.stamped is True
    assert minted.basis.run == outcome.run.address()
    _record_id, _path, (run_operation,) = runrecord.publication_plan(outcome.run)
    run_node = node_from_markdown(run_operation.content.decode())
    candidate = stored.dataset_node(
        slug(minted.address),
        title="duplicate",
        resources=[{"name": name, "digest": value} for name, value in outcome.run.result.outputs],
        basis=basis(
            route(
                run_ref(minted.basis.run),
                input_address,
                [input_address],
            )
        ),
    )
    candidate.deprecated_ids = list(deprecated_ids)
    candidate.relations = [
        Relation(source=candidate.id, predicate=predicate, target=target, attrs=attrs)
        for predicate, target, attrs in relations
    ]
    writer.import_bundle(
        [run_node, candidate],
        observer="observer",
        instrument="instrument",
        opened_at=MOVE_FIELDS["opened_at"],
        closed_at=MOVE_FIELDS["closed_at"],
    )
    record = writer.read_view.get(candidate.id)
    snapshot = lineage_snapshot(writer.read_view, (record.id,))
    assert snapshot.bases[record.id].tag == "single"
    assert all(item.resolved_run and item.resolved_ancestor for item in snapshot.bases[record.id].routes)
    return record, snapshot.bases[record.id]


def test_w5_move_changes_only_location_and_preserves_producer_semantics(durable_factory):
    writer, make_world = durable_factory
    source = writer("w5-source")
    destination = writer("w5-destination")
    paper = source.add(
        stored.source_node("paper", title="paper", identifiers={"doi": "10.1/paper"}).model_copy(
            update={"deprecated_ids": ["source:old-paper"]}
        )
    )
    inbound = source.add(
        Node(
            id="memo:citation",
            kind="memo",
            title="citation",
            relations=[Relation(source="memo:citation", predicate="cites", target=paper.id)],
        )
    )
    world = make_world("w5", source, destination)
    before = _publish(world)
    inbound_before = source.read_view.get(inbound.id)

    moved, _, _ = relocation.move(source, destination, paper.id, **MOVE_FIELDS)
    after = _publish(world)

    assert (moved.uid, moved.id, moved.deprecated_ids) == (
        paper.uid,
        paper.id,
        paper.deprecated_ids,
    )
    assert destination.read_view.get(paper.id) == paper
    with pytest.raises(RefError):
        source.read_view.get(paper.id)
    assert source.read_view.get(inbound.id) == inbound_before
    assert before.members["address-map.yaml"] != after.members["address-map.yaml"]
    assert _belief_digest(before) == _belief_digest(after)

    produced = _move_produced_dataset(durable_factory)
    assert produced["before"].members["producers-map.yaml"] == produced["after"].members["producers-map.yaml"]
    assert produced["states_before"] != produced["states_after"]
    assert all(
        produced["states_before"][corpus_id] != produced["states_after"][corpus_id]
        for corpus_id in produced["states_before"]
    )
    before_receipt = produced["before"].receipts["producer-receipt.yaml"]
    after_receipt = produced["after"].receipts["producer-receipt.yaml"]
    assert before_receipt.subject_identity == _published_snapshot(produced["before"]).identity()
    assert after_receipt.subject_identity == _published_snapshot(produced["after"]).identity()
    assert before_receipt.subject_identity == after_receipt.subject_identity
    assert before_receipt.identity != after_receipt.identity
    assert _belief_digest(produced["before"]) == _belief_digest(produced["after"])


def test_g3_location_is_not_a_belief_closure_member(durable_factory):
    moved = _move_produced_dataset(durable_factory)
    assert moved["before"].members["address-map.yaml"] != moved["after"].members["address-map.yaml"]
    assert _belief_digest(moved["before"]) == _belief_digest(moved["after"])


def test_c3_move_changes_exact_receipt_states_but_not_the_belief(durable_factory):
    moved = _move_produced_dataset(durable_factory)
    before = moved["before"].receipts["producer-receipt.yaml"]
    after = moved["after"].receipts["producer-receipt.yaml"]
    assert before.corpus_states == tuple(sorted(moved["states_before"].items()))
    assert after.corpus_states == tuple(sorted(moved["states_after"].items()))
    assert before.identity != after.identity
    assert _belief_digest(moved["before"]) == _belief_digest(moved["after"])


def test_r23_location_and_receipt_identity_are_not_belief_inputs(durable_factory):
    moved = _move_produced_dataset(durable_factory)
    before = moved["before"].receipts["producer-receipt.yaml"]
    after = moved["after"].receipts["producer-receipt.yaml"]
    assert moved["before"].members["producers-map.yaml"] == moved["after"].members["producers-map.yaml"]
    assert before.identity != after.identity
    assert before.subject_identity == after.subject_identity
    assert _receipt_belief_input(moved["before"]) == _receipt_belief_input(moved["after"])
    assert _belief_digest(moved["before"]) == _belief_digest(moved["after"])


def test_w16_consolidates_one_address_without_asserting_identity(durable_factory, tmp_path):
    writer, make_world = durable_factory
    keep_writer = writer("w16-keep")
    other_writer = writer("w16-other")
    keep_producer = writer("w16-keep-producer")
    other_producer = writer("w16-other-producer")
    for name in ("a", "z", "independent"):
        keep_writer.add(
            stored.dataset_node(
                name,
                title=name,
                resources=[{"name": "data", "digest": "sha256:" + "a" * 64}],
            )
        )
    keep, keep_basis = _produce_single_basis(
        keep_producer,
        keep_writer,
        tmp_path / "w16-keep-production",
        input_address="dataset:input",
        text="keep input",
        deprecated_ids=("dataset:old-a",),
        relations=(
            ("derived-from", "dataset:a", {}),
            ("shared", "dataset:shared", {"side": "keep"}),
        ),
    )
    other, other_basis = _produce_single_basis(
        other_producer,
        other_writer,
        tmp_path / "w16-other-production",
        input_address="dataset:input",
        text="other input",
        deprecated_ids=("dataset:old-b",),
        relations=(
            ("derived-from", "dataset:z", {}),
            ("shared", "dataset:shared", {"side": "other"}),
        ),
    )
    assert keep.id == other.id
    assert keep_basis.tag == other_basis.tag == "single"
    assert keep_basis.routes != other_basis.routes
    other_run = other_basis.routes[0].resolved_run
    assert other_run is not None
    relocation.move(other_writer, keep_writer, other_run, **MOVE_FIELDS)
    inbound = keep_writer.add(
        Node(
            id="memo:inbound",
            kind="memo",
            title="inbound",
            relations=[Relation(source="memo:inbound", predicate="cites", target=keep.id)],
        )
    )
    inbound_before = keep_writer.read_view.get(inbound.id)
    world, _coverage, bindings = _with_coreference_balance(make_world("w16", keep_writer, other_writer))
    before = _publish((world, (keep_writer.corpus_id,), bindings))
    assert yaml.safe_load(before.members["coreference-map.yaml"]) == _COREFERENCE_BALANCE
    assert all(
        lineage_snapshot(corpus.read_view, (record.id,)).bases[record.id].tag == "single"
        for corpus, record in ((keep_writer, keep), (other_writer, other))
    )

    survivor, _, _ = relocation.consolidate((keep_writer, keep.id), (other_writer, other.id), **CONSOLIDATE_FIELDS)
    after = _publish((world, (keep_writer.corpus_id,), bindings))

    assert survivor.uid == keep.uid and survivor.uid != other.uid
    assert survivor.id == keep.id
    assert survivor.deprecated_ids == ["dataset:old-a", "dataset:old-b"]
    assert keep.id not in survivor.deprecated_ids
    assert {(r.predicate, r.target) for r in survivor.relations} == {
        ("derived-from", "dataset:a"),
        ("derived-from", "dataset:z"),
        ("shared", "dataset:shared"),
    }
    shared = [r for r in survivor.relations if r.predicate == "shared"]
    assert len(shared) == 1 and shared[0].attrs == {"side": "keep"}
    assert survivor.facets[stored.LINEAGE_BASIS_FACET]["tag"] == "conflict"
    assert survivor.facets[stored.LINEAGE_BASIS_FACET]["routes"] == sorted(
        survivor.facets[stored.LINEAGE_BASIS_FACET]["routes"],
        key=v1.encode,
    )
    assert len(survivor.facets[stored.LINEAGE_BASIS_FACET]["routes"]) == 2
    assert yaml.safe_load(after.members["coreference-map.yaml"]) == _COREFERENCE_BALANCE
    assert before.members["coreference-map.yaml"] == after.members["coreference-map.yaml"]
    assert keep_writer.read_view.get(inbound.id) == inbound_before
    assert not other_writer.read_view.holds(other.id)
    assert [
        node.uid
        for corpus in (keep_writer, other_writer)
        for node in corpus.read_view.iter_stored()
        if node.id == keep.id
    ] == [keep.uid]
    assert not any(
        node.kind == "coreference-attestation"
        for corpus in (keep_writer, other_writer)
        for node in corpus.read_view.iter_stored()
    )
    snapshot = lineage_snapshot(keep_writer.read_view, (survivor.id,))
    assert snapshot.bases[survivor.id].tag == "conflict"
    assert all(route.resolved_run and route.resolved_ancestor for route in snapshot.bases[survivor.id].routes)
    verdict = certify(snapshot, (survivor.id,), ("dataset:independent",))
    assert verdict.state == "not-certified" and verdict.findings == ("lineage-divergent",)
    assert not {"route", "basis"} & set(inspect.signature(relocation.consolidate).parameters)

    shared_keep = writer("w16-shared-keep")
    shared_other = writer("w16-shared-other")
    shared_node = shared_keep.add(stored.source_node("same", title="kept", identifiers={"doi": "10.1/same"}))
    shared_other.add(shared_node.model_copy(update={"title": "replica"}))
    shared_survivor, _, _ = relocation.consolidate(
        (shared_keep, shared_node.id),
        (shared_other, shared_node.id),
        **CONSOLIDATE_FIELDS,
    )
    assert shared_survivor.uid == shared_node.uid

    for same_uid in (False, True):
        left = writer(f"w16-refuse-left-{same_uid}")
        right = writer(f"w16-refuse-right-{same_uid}")
        left_node = left.add(stored.source_node("left", title="left", identifiers={"doi": "10.1/left"}))
        right_node = stored.source_node("right", title="right", identifiers={"doi": "10.1/right"})
        if same_uid:
            right_node = right_node.model_copy(update={"uid": left_node.uid})
        right_node = right.add(right_node)
        with pytest.raises(AddressDisagreement):
            relocation.consolidate((left, left_node.id), (right, right_node.id), **CONSOLIDATE_FIELDS)

    with pytest.raises(MalformedRecord, match="conflict lineage basis"):
        stored.union_lineage_bases(
            _dataset("valid", ["a"]),
            _dataset("malformed", ["a"], tag="conflict"),
        )

    union_keep = writer("w16-union-keep")
    union_other = writer("w16-union-other")
    union_a = union_keep.add(_dataset("union", ["a", "c"], tag="conflict"))
    union_b = union_other.add(_dataset("union", ["b", "c"], tag="conflict"))
    unioned, _, _ = relocation.consolidate((union_keep, union_a.id), (union_other, union_b.id), **CONSOLIDATE_FIELDS)
    assert unioned.facets[stored.LINEAGE_BASIS_FACET] == {
        "tag": "conflict",
        "routes": [_route("a"), _route("b"), _route("c")],
    }


@pytest.mark.parametrize("operation", ["move", "consolidate"])
@pytest.mark.parametrize("fault", ["domain", "base", "missing"])
def test_d7_each_public_relocation_refuses_contract_disagreement(durable_factory, operation: str, fault: str):
    writer, _ = durable_factory
    if fault == "domain":
        source_pins = PINS
        destination_pins = CorpusPins(PINS.science_contract, {"biology": "biology:" + "c" * 64})
        node = Node(
            id="memo:relocated",
            kind="memo",
            title="relocated",
            facets={"biology/gene-axis": {}},
        )
    elif fault == "base":
        source_pins = PINS
        destination_pins = CorpusPins("science:" + "c" * 64, PINS.domains)
        node = stored.source_node("paper", title="paper", identifiers={"doi": "10.1/paper"})
    else:
        source_pins = PINS
        destination_pins = CorpusPins(PINS.science_contract, {})
        node = Node(
            id="memo:relocated",
            kind="memo",
            title="relocated",
            facets={"biology/gene-axis": {}},
        )

    source = writer(f"d7-{operation}-{fault}-source", source_pins)
    destination = writer(f"d7-{operation}-{fault}-destination", destination_pins)
    source_node = source.add(node)
    if operation == "move":
        call = lambda: relocation.move(source, destination, source_node.id, **MOVE_FIELDS)
    else:
        destination_node = destination.add(node.model_copy(update={"uid": "f" * 32}))
        call = lambda: relocation.consolidate(
            (destination, destination_node.id),
            (source, source_node.id),
            **CONSOLIDATE_FIELDS,
        )
    with pytest.raises(ContractPinDisagreement):
        call()


def test_m3_consolidates_retraction_replicas_without_touching_the_counter(durable_factory):
    writer, _ = durable_factory
    keep = writer("m3-keep")
    other = writer("m3-other")
    targets = []
    for corpus in (keep, other):
        observed = corpus.add(
            stored.dataset_node(
                "raw",
                title="raw",
                resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
                empirical_observation={"boundary": "instrument"},
            )
        )
        run = corpus.add(stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[observed.id]))
        proposition = corpus.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
        targets.append(
            corpus.add(
                stored.assessment_node(
                    "a1",
                    title="a1",
                    spec="analysis-spec:s1",
                    run=run.id,
                    proposition=proposition.id,
                    outcome="supported",
                    interpretation_rule="rule:threshold",
                )
            )
        )
    target_identity = stored.stored_semantic_hash(targets[0])
    assert target_identity is not None
    replica = stored.retraction_node(
        title="retraction",
        target=stored.NodeTarget(targets[0].id, targets[0].id, target_identity),
        reason="defective-code",
        rationale="invalid result",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="event-1",
    )
    first = keep.retract(replica)
    other.retract(replica)
    first_identity = stored.stored_semantic_hash(first)
    assert first_identity is not None
    counter = keep.retract(
        stored.retraction_node(
            title="counter",
            target=stored.NodeTarget(first.id, first.id, first_identity),
            reason="upstream-retraction",
            rationale="withdrawn",
            grounds=("verification:v2",),
            actor=ACTOR,
            event_token="event-2",
        )
    )
    counter_before = keep.read_view.get(counter.id)
    counter_path = keep._relative_path(counter)
    counter_registrations_before = _registrations_for_path(keep.root, counter_path)
    assert len(counter_registrations_before) == 1

    survivor, _, _ = relocation.consolidate((keep, first.id), (other, first.id), **CONSOLIDATE_FIELDS)

    assert stored.stored_semantic_hash(survivor) == first_identity
    assert keep.read_view.get(counter.id) == counter_before
    assert _registrations_for_path(keep.root, counter_path) == counter_registrations_before
    assert counter.relations[0].target == first.id


def test_t2_each_root_records_one_intent_before_one_qualifying_report(durable_factory):
    moved = _move_produced_dataset(durable_factory)
    writer, _ = durable_factory
    keep = writer("t2-keep")
    other = writer("t2-other")
    kept = keep.add(stored.source_node("same", title="keep", identifiers={"doi": "10.1/same"}))
    duplicate = other.add(stored.source_node("same", title="other", identifiers={"doi": "10.1/same"}))
    starts = {corpus.root: len(_entries(corpus.root)) for corpus in (keep, other)}
    _, keep_report, other_report = relocation.consolidate((keep, kept.id), (other, duplicate.id), **CONSOLIDATE_FIELDS)
    operations = (
        ("move", moved["destination"], moved["destination_report"], moved["dataset"], True),
        ("move", moved["source"], moved["source_report"], moved["dataset"], False),
        ("consolidate", keep, keep_report, kept, True),
        ("consolidate", other, other_report, duplicate, False),
    )
    for kind, corpus, report, record, retained in operations:
        assert report.opened_at == MOVE_FIELDS["opened_at"]
        assert report.closed_at == MOVE_FIELDS["closed_at"]
        start = starts[corpus.root] if kind == "consolidate" else moved["entry_starts"][corpus.root]
        entries = _entries(corpus.root)[start:]
        intents = [entry for entry in entries if type(entry) is IntentEntryView]
        assert len(intents) == 1
        payload = v1.decode(intents[0].payload)
        assert payload == {"kind": kind, "event_token": report.event_token, "actor": ACTOR}
        data_path = corpus._relative_path(record)
        data_acts = [
            entry
            for entry in entries
            if type(entry) is RegisteredEntryView
            and entry.fulfills is None
            and data_path in {name for name, _state in (*entry.initial, *entry.final)}
        ]
        assert len(data_acts) == 1
        fulfilling = [
            entry for entry in entries if type(entry) is RegisteredEntryView and entry.fulfills == intents[0].digest
        ]
        assert len(fulfilling) == 1
        assert entries.index(intents[0]) < entries.index(data_acts[0]) < entries.index(fulfilling[0])
        assert corpus.read_view.holds(record.id) is retained
        assert corpus.read_view.holds(f"act-report:{report.identity()}")
    assert moved["destination_report"].event_token == moved["source_report"].event_token
    assert keep_report.event_token == other_report.event_token


def _store_report(corpus, report) -> None:
    digest = corpus._append_operation_intent(report.operation, report.event_token, corpus.authority.actor)
    corpus._publish_operation_report(report, digest)


def test_t8_move_and_consolidate_refuse_act_reports(durable_factory):
    writer, _ = durable_factory
    move_source = writer("t8-move-source")
    move_destination = writer("t8-move-destination")
    report = sample_report()
    _store_report(move_source, report)
    move_before = {corpus.root: _entries(corpus.root) for corpus in (move_source, move_destination)}
    report_id = f"act-report:{report.identity()}"
    with pytest.raises(RelocationKindExcluded):
        relocation.move(
            move_source,
            move_destination,
            report_id,
            **MOVE_FIELDS,
        )
    assert move_source.read_view.holds(report_id)
    assert not move_destination.read_view.holds(report_id)
    assert {corpus.root: _entries(corpus.root) for corpus in (move_source, move_destination)} == move_before

    keep = writer("t8-consolidate-keep")
    other = writer("t8-consolidate-other")
    _store_report(keep, report)
    ordinary = other.add(stored.source_node("ordinary", title="ordinary", identifiers={"doi": "10.1/ordinary"}))
    consolidate_before = {corpus.root: _entries(corpus.root) for corpus in (keep, other)}
    with pytest.raises(RelocationKindExcluded):
        relocation.consolidate(
            (keep, report_id),
            (other, ordinary.id),
            **CONSOLIDATE_FIELDS,
        )
    assert keep.read_view.holds(report_id)
    assert other.read_view.holds(ordinary.id)
    assert {corpus.root: _entries(corpus.root) for corpus in (keep, other)} == consolidate_before


def test_boundary_reresolution_refuses_both_create_only_calls_after_real_move(durable_factory, monkeypatch):
    writer, _ = durable_factory

    source = writer("reresolve-retract-source")
    destination = writer("reresolve-retract-destination")
    observed = source.add(
        stored.dataset_node(
            "observation",
            title="observation",
            resources=[{"name": "data", "digest": "sha256:" + "d" * 64}],
            empirical_observation={"boundary": "instrument"},
        )
    )
    destination.add(observed)
    run = source.add(stored.run_node("producer", title="producer", spec="analysis-spec:p", observes=[observed.id]))
    destination.add(run)
    proposition = source.add(stored.proposition_node("claim", title="claim", claim={"operator": "affects"}))
    target = source.add(
        stored.assessment_node(
            "target",
            title="target",
            spec="analysis-spec:p",
            run=run.id,
            proposition=proposition.id,
            outcome="supported",
            interpretation_rule="rule:threshold",
        )
    )
    target_identity = stored.stored_semantic_hash(target)
    assert target_identity is not None
    retraction = stored.retraction_node(
        title="retraction",
        target=stored.NodeTarget(target.id, target.id, target_identity),
        reason="defective-code",
        rationale="invalid",
        grounds=("verification:v1",),
        actor=ACTOR,
        event_token="reresolve",
    )
    refuse = source._refuse

    def move_during_retract(node, **kwargs):
        relocation.move(source, destination, target.id, **MOVE_FIELDS)
        return refuse(node, **kwargs)

    monkeypatch.setattr(source, "_refuse", move_during_retract)
    with pytest.raises(RelocationTargetMissing) as caught:
        source.retract(retraction)
    assert isinstance(caught.value.__cause__, RefError)

    predecessor_source = writer("reresolve-supersede-source")
    predecessor_destination = writer("reresolve-supersede-destination")
    predecessor = predecessor_source.add(stored.proposition_node("p1", title="p1", claim={"operator": "affects"}))
    successor = stored.proposition_node("p2", title="p2", claim={"operator": "inhibits"})
    refuse = predecessor_source._refuse

    def move_during_supersede(node, **kwargs):
        relocation.move(
            predecessor_source,
            predecessor_destination,
            predecessor.id,
            **MOVE_FIELDS,
        )
        return refuse(node, **kwargs)

    monkeypatch.setattr(predecessor_source, "_refuse", move_during_supersede)
    with pytest.raises(RelocationTargetMissing) as caught:
        predecessor_source.supersede(successor, of=predecessor.id)
    assert isinstance(caught.value.__cause__, RefError)


def test_boundary_lock_deduplicates_resolved_same_root_before_refusal(durable_factory, tmp_path, monkeypatch):
    writer, _ = durable_factory
    corpus = writer("dedup")
    node = corpus.add(stored.source_node("paper", title="paper", identifiers={"doi": "10.1/paper"}))
    alias = tmp_path / "cut16-root-alias"
    alias.symlink_to(corpus.root, target_is_directory=True)
    twin = root.open_corpus(alias, authority=FULL)
    events: list[str] = []

    class RecordingLock:
        def __enter__(self):
            events.append("enter")

        def __exit__(self, *_exc):
            events.append("exit")

    lock = RecordingLock()
    monkeypatch.setattr(corpus, "_operation", lock)
    monkeypatch.setattr(twin, "_operation", lock)
    with pytest.raises(SameRootRefused):
        relocation.move(corpus, twin, node.id, **MOVE_FIELDS)
    assert events == ["enter", "exit"]
