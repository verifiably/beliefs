"""Mechanical holdings coverage capture under the closed schema."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import pytest
from atoms.chain.model import state_to_json
from atoms.core.fingerprint import PathState
from authority import FULL
from fixtures_cut6 import PINS
from nodes.core.projection import to_canonical_json
from nodes.core.write_plan import DefaultExecutor
from test_world_build import ALPHA, BETA, ChainHeads, corpus_at, make_world

from beliefs import root as science_root
from beliefs import stored
from beliefs.corpus import ReadView, _root_state_for
from beliefs.errors import CaptureDrift, CorpusStateMalformed, CoverageUnknown, ScienceError
from beliefs.holdings.boundary import ActContext, PublishedObservation, recheck
from beliefs.holdings.project import capture_coverage
from beliefs.holdings.records import Absent, StoreLocator, holdings_observation
from beliefs.world import logmodel, registry, verify

OPAQUE_ABSENT = object()


def corpora(capture: dict[str, object]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], capture["corpora"])


def absent_facts(state: object) -> tuple[tuple[str, str], ...]:
    assert state is OPAQUE_ABSENT
    return (("kind", "absent"),)


def observation_node():
    return stored.holdings_observation_node(
        holdings_observation(
            location=StoreLocator("1" * 32, "held.bin"),
            outcome=Absent(),
            observer="observer",
            instrument="instrument",
            event_token="event",
            observed_at="2026-08-24T12:00:00Z",
        )
    )


def admitted(tmp_path: Path, *nodes):
    root = corpus_at(tmp_path / "corpus", ALPHA, tuple(nodes))
    world = make_world(tmp_path, root, chain_head=ChainHeads())
    world.admit(root, provenance=registry.Fresh())
    return world, root


def whole_chain(_root: Path) -> logmodel.WellFormedView:
    genesis = logmodel.GenesisEntryView(
        digest="1" * 64,
        payload=b"\x00\xff",
        baseline=(("a", OPAQUE_ABSENT),),
    )
    intent = logmodel.IntentEntryView(digest="2" * 64, payload=b"intent")
    first = logmodel.RegisteredEntryView(
        digest="3" * 64,
        txid="tx-one",
        intent_digest="sha256:" + "4" * 64,
        consumer_tag="science-corpus-write-v1",
        initial=(("a", OPAQUE_ABSENT),),
        final=(("b", OPAQUE_ABSENT),),
        fulfills=None,
    )
    second = logmodel.RegisteredEntryView(
        digest="5" * 64,
        txid="tx-two",
        intent_digest="sha256:" + "6" * 64,
        consumer_tag="science-corpus-write-v1",
        initial=(),
        final=(),
        fulfills=intent.digest,
    )
    settled = logmodel.SettledEntryView(
        digest="7" * 64,
        txid="tx-two",
        registration=second.digest,
        committed=True,
    )
    return logmodel.WellFormedView(
        genesis=genesis,
        entries=(genesis, intent, first, second, settled),
        tip=settled.digest,
        pending=((first.txid, first.digest),),
    )


def test_each_entry_variant_has_the_exact_closed_serialization(tmp_path):
    dataset = stored.dataset_node("dataset", title="Dataset")
    observation = observation_node()
    world, _root = admitted(tmp_path, observation, dataset)

    encoded: list[object] = []

    def recording_facts(state: object) -> tuple[tuple[str, str], ...]:
        encoded.append(state)
        return absent_facts(state)

    captured = capture_coverage(
        world,
        frozenset({ALPHA}),
        chain_view=whole_chain,
        state_facts=recording_facts,
    )

    assert set(captured) == {"corpora"}
    corpus = corpora(captured)[0]
    assert set(corpus) == {"corpus_id", "corpus_state", "chain_head", "records", "chain"}
    assert corpus["corpus_id"] == ALPHA
    assert corpus["chain_head"] == "7" * 64
    assert [record["uid"] for record in corpus["records"]] == sorted([dataset.uid, observation.uid])
    assert all(set(record) == {"uid", "canonical"} for record in corpus["records"])
    assert corpus["chain"] == [
        {
            "digest": "1" * 64,
            "entry": {
                "kind": "genesis",
                "payload": "00ff",
                "baseline": [["a", [["kind", "absent"]]]],
            },
        },
        {"digest": "2" * 64, "entry": {"kind": "intent", "payload": "696e74656e74"}},
        {
            "digest": "3" * 64,
            "entry": {
                "kind": "registered",
                "txid": "tx-one",
                "intent_digest": "sha256:" + "4" * 64,
                "consumer_tag": "science-corpus-write-v1",
                "initial": [["a", [["kind", "absent"]]]],
                "final": [["b", [["kind", "absent"]]]],
            },
        },
        {
            "digest": "5" * 64,
            "entry": {
                "kind": "registered",
                "txid": "tx-two",
                "intent_digest": "sha256:" + "6" * 64,
                "consumer_tag": "science-corpus-write-v1",
                "fulfills": "2" * 64,
                "initial": [],
                "final": [],
            },
        },
        {
            "digest": "7" * 64,
            "entry": {
                "kind": "settled",
                "txid": "tx-two",
                "registration": "5" * 64,
                "outcome": "committed",
            },
        },
    ]
    assert "fulfills" not in corpus["chain"][2]["entry"]
    assert encoded == [OPAQUE_ABSENT, OPAQUE_ABSENT, OPAQUE_ABSENT]


def test_every_record_is_carried_without_a_kind_filter(tmp_path):
    dataset = stored.dataset_node("dataset", title="Dataset")
    observation = observation_node()
    world, _root = admitted(tmp_path, dataset, observation)

    captured = capture_coverage(world, frozenset({ALPHA}), chain_view=whole_chain, state_facts=absent_facts)

    assert {record["uid"] for record in corpora(captured)[0]["records"]} == {
        dataset.uid,
        observation.uid,
    }


def test_the_projection_matches_the_closed_schema(
    certified_work,
):
    corpus_root = certified_work / "corpus"
    science_root.init_corpus_root(corpus_root, authority=FULL)
    writer = science_root.open_corpus(corpus_root, authority=FULL)
    manifest = writer.adopt_manifest(profile=PINS)
    dataset = writer.add(
        stored.dataset_node(
            "dataset",
            title="Dataset",
            resources=[{"name": "data", "digest": "sha256:" + "ab" * 32}],
        )
    )
    store_root = certified_work / "store"
    store_id = science_root.init_store_root(store_root, authority=FULL)
    published = recheck(
        ActContext(
            corpus_root,
            store_root,
            "observer",
            "instrument",
            FULL,
            science_root.holdings_seam(),
        ),
        StoreLocator(store_id, "missing.bin"),
    )
    assert isinstance(published, PublishedObservation)
    observation = next(
        node for node in ReadView.opened_at(corpus_root).iter_stored() if node.kind == "holdings-observation"
    )
    world = registry.World(
        registry.WorldConfig(certified_work / "world", "f" * 32, (corpus_root,)),
        DefaultExecutor,
        chain_head=ChainHeads(),
        corpus_executor_factory=science_root.durable_executor_factory(),
        authority=FULL,
    )
    world.admit(corpus_root, provenance=registry.Fresh())
    seam = science_root._log_seam()
    viewed = seam.inspect_registered(corpus_root)
    assert isinstance(viewed, logmodel.WellFormedView)
    encoded: list[object] = []

    def recording_facts(state: object) -> tuple[tuple[str, str], ...]:
        encoded.append(state)
        return seam.state_facts(state)

    captured = capture_coverage(
        world,
        frozenset({manifest.corpus_id}),
        chain_view=seam.inspect_registered,
        state_facts=recording_facts,
    )

    corpus = corpora(captured)[0]
    assert set(captured) == {"corpora"}
    assert set(corpus) == {"corpus_id", "corpus_state", "chain_head", "records", "chain"}
    assert corpus["corpus_id"] == manifest.corpus_id
    assert [record["uid"] for record in corpus["records"]] == sorted([dataset.uid, observation.uid])
    assert all(set(record) == {"uid", "canonical"} for record in corpus["records"])
    assert {record["uid"] for record in corpus["records"]} == {
        dataset.uid,
        observation.uid,
    }
    assert corpus["corpus_state"] == registry.corpus_state_identity(corpus_root)
    entries = corpus["chain"]
    assert corpus["chain_head"] == viewed.tip
    assert [row["digest"] for row in entries] == [entry.digest for entry in viewed.entries]
    assert entries[0]["entry"]["kind"] == "genesis"
    assert {row["entry"]["kind"] for row in entries} == {
        "genesis",
        "intent",
        "registered",
        "settled",
    }
    assert any(row["entry"].get("outcome") == "committed" for row in entries)
    assert any(row["entry"]["kind"] == "registered" and "fulfills" not in row["entry"] for row in entries)
    for row in entries:
        assert set(row) == {"digest", "entry"}
        entry = row["entry"]
        if entry["kind"] == "genesis":
            assert set(entry) == {"kind", "payload", "baseline"}
        elif entry["kind"] == "intent":
            assert set(entry) == {"kind", "payload"}
        elif entry["kind"] == "registered":
            expected = {
                "kind",
                "txid",
                "intent_digest",
                "consumer_tag",
                "initial",
                "final",
            }
            if "fulfills" in entry:
                expected.add("fulfills")
            assert set(entry) == expected
        else:
            assert entry["kind"] == "settled"
            assert set(entry) == {"kind", "txid", "registration", "outcome"}
    expected_states: list[object] = []
    for viewed_entry, projected_row in zip(viewed.entries, entries, strict=True):
        projected_entry = projected_row["entry"]
        surfaces = (
            (("baseline", viewed_entry.baseline),)
            if isinstance(viewed_entry, logmodel.GenesisEntryView)
            else (
                (("initial", viewed_entry.initial), ("final", viewed_entry.final))
                if isinstance(viewed_entry, logmodel.RegisteredEntryView)
                else ()
            )
        )
        for name, surface in surfaces:
            expected_states.extend(state for _path, state in surface)
            assert projected_entry[name] == [
                [
                    path,
                    [list(pair) for pair in state_to_json(cast(PathState, state))],
                ]
                for path, state in surface
            ]
    assert encoded == expected_states


def test_corpora_are_sorted_by_declared_identity(tmp_path):
    beta = corpus_at(tmp_path / "beta", BETA)
    alpha = corpus_at(tmp_path / "alpha", ALPHA)
    world = make_world(tmp_path, beta, alpha, chain_head=ChainHeads())
    world.admit(beta, provenance=registry.Fresh())
    world.admit(alpha, provenance=registry.Fresh())

    captured = capture_coverage(
        world,
        frozenset({BETA, ALPHA}),
        chain_view=whole_chain,
        state_facts=absent_facts,
    )

    assert [corpus["corpus_id"] for corpus in corpora(captured)] == [ALPHA, BETA]


def test_the_canonical_text_is_the_state_identitys_own(tmp_path):
    dataset = stored.dataset_node("dataset", title="Dataset")
    world, root = admitted(tmp_path, dataset)

    captured = capture_coverage(world, frozenset({ALPHA}), chain_view=whole_chain, state_facts=absent_facts)
    corpus = corpora(captured)[0]

    assert corpus["records"] == [{"uid": dataset.uid, "canonical": to_canonical_json(dataset)}]
    assert corpus["corpus_state"] == registry.corpus_state_identity(root)


def test_an_undecodable_record_refuses_the_whole_capture(tmp_path):
    world, root = admitted(tmp_path, stored.dataset_node("dataset", title="Dataset"))
    garbage = root / "garbage.md"
    garbage.write_text("not a node", encoding="utf-8")

    with pytest.raises(CorpusStateMalformed, match=ALPHA):
        capture_coverage(world, frozenset({ALPHA}), chain_view=whole_chain, state_facts=absent_facts)


def test_an_initial_open_decode_failure_refuses_the_whole_capture(tmp_path):
    world, root = admitted(tmp_path)
    (root / "bad.md").write_bytes(b"---\n[not valid\n---\n")

    with pytest.raises(CorpusStateMalformed, match=ALPHA):
        capture_coverage(world, frozenset({ALPHA}), chain_view=whole_chain, state_facts=absent_facts)


def test_an_unresolvable_corpus_refuses_the_whole_projection(tmp_path):
    world, _root = admitted(tmp_path)

    with pytest.raises(CoverageUnknown, match=BETA):
        capture_coverage(
            world,
            frozenset({ALPHA, BETA}),
            chain_view=whole_chain,
            state_facts=absent_facts,
        )


def test_no_declared_coverage_refuses(tmp_path):
    world, _root = admitted(tmp_path)

    with pytest.raises(
        CoverageUnknown,
        match="^a projection with no declared coverage is refused$",
    ):
        capture_coverage(world, frozenset(), chain_view=whole_chain, state_facts=absent_facts)


@pytest.mark.parametrize(
    "view", [logmodel.AbsentView(), logmodel.MalformedView(logmodel.DefectView("cycle", "x", "bad"))]
)
def test_an_unvalidated_chain_refuses_the_whole_capture(tmp_path, view):
    world, _root = admitted(tmp_path)

    with pytest.raises(CorpusStateMalformed, match=ALPHA):
        capture_coverage(
            world,
            frozenset({ALPHA}),
            chain_view=lambda _root: view,
            state_facts=absent_facts,
        )


def test_a_frozen_stand_in_registration_cannot_enter_the_projection(tmp_path):
    world, _root = admitted(tmp_path)
    chain = whole_chain(_root)
    stand_in = logmodel.RegisteredEntryView(
        digest="8" * 64,
        txid="frozen",
        initial=(),
        final=(),
        fulfills=None,
    )
    view = logmodel.WellFormedView(
        genesis=chain.genesis,
        entries=(*chain.entries, stand_in),
        tip=stand_in.digest,
        pending=((stand_in.txid, stand_in.digest),),
    )

    with pytest.raises(CorpusStateMalformed, match="binding metadata"):
        capture_coverage(
            world,
            frozenset({ALPHA}),
            chain_view=lambda _root: view,
            state_facts=absent_facts,
        )


def test_an_unwired_state_encoder_propagates_its_refusal(tmp_path):
    world, _root = admitted(tmp_path)
    production = science_root._log_seam()
    unwired = verify.LogSeam(
        inspect_registered=production.inspect_registered,
        inspect_detached=production.inspect_detached,
        capture=production.capture,
        read_head=production.read_head,
        absent_state=production.absent_state,
        world_lock=production.world_lock,
        corpus_lock=production.corpus_lock,
    )

    with pytest.raises(AssertionError, match="wires no path-state fact encoder"):
        capture_coverage(
            world,
            frozenset({ALPHA}),
            chain_view=whole_chain,
            state_facts=unwired.state_facts,
        )


def test_an_executor_factory_mismatch_propagates_as_the_programming_error(tmp_path):
    world, root = admitted(tmp_path)
    _root_state_for(root, DefaultExecutor)

    def another_factory(carrier: Path):
        return DefaultExecutor(carrier)

    world._corpus_executor_factory = another_factory

    with pytest.raises(ScienceError, match="different executor factory") as refusal:
        capture_coverage(
            world,
            frozenset({ALPHA}),
            chain_view=whole_chain,
            state_facts=absent_facts,
        )
    assert type(refusal.value) is ScienceError


def test_capture_is_coherent_under_the_lock(monkeypatch, tmp_path):
    world, _root = admitted(tmp_path)
    states = iter(("a" * 64, "b" * 64))
    monkeypatch.setattr(registry, "corpus_state_identity", lambda _root: next(states))

    with pytest.raises(CaptureDrift, match=ALPHA):
        capture_coverage(world, frozenset({ALPHA}), chain_view=whole_chain, state_facts=absent_facts)


def test_the_world_barrier_is_released_before_a_corpus_lock_is_taken(monkeypatch, tmp_path):
    world, _root = admitted(tmp_path)

    class Lock:
        @contextmanager
        def capture(self):
            assert not world._state.lock.locked()
            yield

    class State:
        lock = Lock()

    from beliefs.holdings import project

    monkeypatch.setattr(project, "_root_state_for", lambda *_args: State())

    capture_coverage(world, frozenset({ALPHA}), chain_view=whole_chain, state_facts=absent_facts)
