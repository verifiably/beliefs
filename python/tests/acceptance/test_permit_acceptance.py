"""Cut 17's durable arms: E1, E2, E7 and E8 through the composition root on the
certified volume (design §9.2). Chains and world roots are byte-identical before
and after every refusal."""
from __future__ import annotations

import os
import secrets
import shutil
from pathlib import Path

import pytest
from authority import ACTOR, FULL, lacking, narrowed
from fixtures_cut3 import DATA_ADDRESS, MINIMAL_POLICY, READS_ADDRESS, definition, freeze, spec_draft, spec_rules, stage
from fixtures_cut6 import PINS
from test_durable_families import proposition
from test_operation_port import durable_port

from beliefs import root as science_root
from beliefs import stored
from beliefs.boundary import RunRefused, execute_assessment_run
from beliefs.corpus import CorpusWriter
from beliefs.errors import PermitExceeded, PermitFact
from beliefs.holdings.boundary import ActContext, StoreLocator
from beliefs.holdings.boundary import write as holdings_write
from beliefs.relocation import move
from beliefs.root import (
    DurableOperationPort,
    holdings_seam,
    init_corpus_root,
    init_store_root,
    init_world_root,
    metadata_root_for,
    open_corpus,
    open_world,
)
from beliefs.world import Fresh, WorldConfig
from beliefs.world.logmodel import WellFormedView


def _head(root: Path):
    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return tuple(entry.digest for entry in view.entries)  # use the entry view's real digest attribute


def _entry_types(root: Path) -> tuple[str, ...]:
    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return tuple(type(entry).__name__ for entry in view.entries)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_e1_add_through_open_corpus_refuses_before_the_chain_moves(durable_root):
    writer = open_corpus(durable_root, authority=lacking(kinds=("proposition",)))
    before = _head(durable_root)
    with pytest.raises(PermitExceeded) as caught:
        writer.add(proposition("p1"))
    assert caught.value.requirement == PermitFact("kind", "proposition")
    assert _head(durable_root) == before
    assert open_corpus(durable_root, authority=FULL).add(proposition("p1")).kind == "proposition"


def test_e1_an_ungoverned_kind_mints_under_the_full_permit_and_refuses_under_a_governed_one(durable_root):
    from durable_fixture import memo

    with pytest.raises(PermitExceeded) as caught:
        open_corpus(durable_root, authority=narrowed(kinds=("proposition",), families=("corpus-write",))).add(memo("memo:m1"))
    assert caught.value.requirement == PermitFact("kind", "memo")
    assert open_corpus(durable_root, authority=FULL).add(memo("memo:m1")).kind == "memo"


def test_e2_the_composition_root_binds_one_authority_to_writer_and_port(durable_root):
    writer = open_corpus(durable_root, authority=FULL)
    assert writer.authority is FULL
    other = DurableOperationPort(
        durable_root, backend=science_root._PRODUCTION_BACKEND, storage=science_root.PRODUCTION_STORAGE,
        metadata_root=metadata_root_for(durable_root), authority=narrowed(),
    )
    with pytest.raises(ValueError, match="another authority"):
        CorpusWriter(durable_root, science_root.durable_executor_factory(), authority=FULL, operation_port=other)


def test_e7_the_run_boundary_refuses_with_no_intent_through_a_real_port(durable_root, tmp_path):
    port = durable_port(durable_root, authority=lacking(families=("run",)))
    before = _head(durable_root)
    code, held = stage(tmp_path)
    outcome = execute_assessment_run(
        spec=freeze(spec_draft(), held_rules=spec_rules()), port=port, boundary_policy=MINIMAL_POLICY,
        definition=definition(), code_roots=(code,),
        held_inputs={DATA_ADDRESS: held / "data.txt", READS_ADDRESS: held / "palette.txt"},
        entrypoint="code/workflow/Snakefile", targets=("outputs/result.txt",), declared_outputs=("outputs/result.txt",),
        observer="observer-1", started_at="2026-09-04T00:00:00Z", host_realization="host-a", scratch_base=tmp_path / "scratch",
    )
    assert isinstance(outcome, RunRefused) and outcome.reason == "permit-exceeded"
    assert outcome.report is None and outcome.intent is None
    assert _head(durable_root) == before


def test_e7_a_holdings_act_refuses_with_the_store_and_observer_chains_unchanged(work_directory):
    observer_root = work_directory / f"observer-{os.getpid()}-permit"
    store_root = work_directory / f"store-{os.getpid()}-permit"
    init_corpus_root(observer_root, authority=FULL)
    store_id = init_store_root(store_root, authority=FULL)
    ctx = ActContext(observer_root, store_root, "observer", "instrument", lacking(families=("holdings",)), holdings_seam())
    before = _head(observer_root), _tree_bytes(store_root)
    with pytest.raises(PermitExceeded):
        holdings_write(ctx, StoreLocator(store_id, "held.bin"), b"bytes")
    assert (_head(observer_root), _tree_bytes(store_root)) == before


def test_e7_world_admit_refuses_with_the_world_root_unchanged(durable_root, work_directory):
    open_corpus(durable_root, authority=FULL).adopt_manifest(profile=PINS)
    world_root = work_directory / f"world-{os.getpid()}-permit"
    config = WorldConfig(world_root, "0" * 32, (durable_root,))
    init_world_root(config, authority=FULL)
    world = open_world(config, authority=lacking(families=("registry",)))
    before = _tree_bytes(world_root)
    with pytest.raises(PermitExceeded):
        world.admit(durable_root, provenance=Fresh())
    assert _tree_bytes(world_root) == before
    assert open_world(config, authority=FULL).admit(durable_root, provenance=Fresh()).actor == ACTOR


def test_e8_an_unpermitted_member_refuses_the_bundle_with_the_chain_unchanged(durable_root):
    writer = open_corpus(durable_root, authority=lacking(kinds=("source",)))
    before = _head(durable_root)
    members = [proposition("p2"), stored.source_node("s1", title="s", identifiers={"doi": "10.1/x"})]
    with pytest.raises(PermitExceeded) as caught:
        writer.import_bundle(members, observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert caught.value.requirement == PermitFact("kind", "source")
    assert _head(durable_root) == before
    report = open_corpus(durable_root, authority=FULL).import_bundle(members, observer="o", instrument="i", opened_at="T0", closed_at="T1")
    assert report.actor == ACTOR
    assert _entry_types(durable_root)[len(before):] == (
        "IntentEntryView",
        "RegisteredEntryView",
        "SettledEntryView",
        "RegisteredEntryView",
        "SettledEntryView",
    )


def test_e1_relocation_refuses_before_either_intent_then_succeeds(work_directory):
    token = secrets.token_hex(6)
    a = work_directory / f"permit-move-{os.getpid()}-{token}-a"
    b = work_directory / f"permit-move-{os.getpid()}-{token}-b"
    try:
        for root in (a, b):
            init_corpus_root(root, authority=FULL)
            open_corpus(root, authority=FULL).adopt_manifest(profile=PINS)
        node = open_corpus(a, authority=FULL).add(proposition("moving"))
        before_a, before_b = _head(a), _head(b)
        with pytest.raises(PermitExceeded) as caught:
            move(
                open_corpus(a, authority=FULL),
                open_corpus(
                    b,
                    authority=narrowed(
                        kinds=("act-report",), families=("corpus-write",)
                    ),
                ),
                node.id,
                observer="o",
                instrument="i",
                opened_at="T0",
                closed_at="T1",
            )
        assert caught.value.requirement == PermitFact("kind", "proposition")
        assert (_head(a), _head(b)) == (before_a, before_b)

        moved, _, _ = move(
            open_corpus(a, authority=FULL),
            open_corpus(b, authority=FULL),
            node.id,
            observer="o",
            instrument="i",
            opened_at="T0",
            closed_at="T1",
        )
        assert moved.id == node.id
        expected = (
            "IntentEntryView",
            "RegisteredEntryView",
            "SettledEntryView",
            "RegisteredEntryView",
            "SettledEntryView",
        )
        assert _entry_types(a)[len(before_a):] == expected
        assert _entry_types(b)[len(before_b):] == expected
    finally:
        for root in (a, b):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)
