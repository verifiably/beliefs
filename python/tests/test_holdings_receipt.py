"""The holdings reduction receipt and its re-running validator."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path

import pytest
from fixtures_cut6 import PINS
from nodes.core.corpus import Corpus
from nodes.core.write_plan import DefaultExecutor
from test_world_build import ALPHA, BETA, ChainHeads, corpus_at, make_world

from science import root as science_root
from science import stored
from science.corpus import _root_state_for
from science.holdings.boundary import intent_payload
from science.holdings.project import capture_coverage
from science.holdings.receipt import (
    HOLDINGS_RECEIPT_DOMAIN,
    derive_holdings,
    output_digest,
    validate_holdings_receipt,
)
from science.holdings.records import StoreLocator
from science.holdings.reduce import holdings_rule_bundle
from science.identity import v1
from science.world import logmodel, registry, rules

GENESIS = "1" * 64
NEXT = "2" * 64
FABRICATED = "f" * 64
STORE = "3" * 32
OPAQUE_STATE = object()


class MutableChains:
    def __init__(self) -> None:
        self.by_root: dict[Path, tuple[logmodel.EntryView, ...]] = {}

    def add(self, root: Path, *entries: logmodel.EntryView) -> None:
        genesis = logmodel.GenesisEntryView(
            digest=GENESIS,
            payload=b"genesis",
            baseline=(("held.bin", OPAQUE_STATE),),
        )
        self.by_root[root.resolve()] = (genesis, *entries)

    def __call__(self, root: Path) -> logmodel.WellFormedView:
        entries = self.by_root[root.resolve()]
        genesis = entries[0]
        assert isinstance(genesis, logmodel.GenesisEntryView)
        return logmodel.WellFormedView(
            genesis=genesis,
            entries=entries,
            tip=entries[-1].digest,
            pending=(),
        )


def state_facts(state: object) -> tuple[tuple[str, str], ...]:
    assert state is OPAQUE_STATE
    return (("kind", "absent"),)


def unmatched_intent(digest: str = NEXT) -> logmodel.IntentEntryView:
    payload = json.dumps(
        {
            "actor": "alice",
            "domain": "science.holdings-intent.v1",
            "event_token": "event",
            "kind": "write",
            "location": {
                "relative_path": "held.bin",
                "store_id": STORE,
                "type": "store",
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return logmodel.IntentEntryView(digest=digest, payload=payload)


def admitted_world(tmp_path: Path, *corpus_ids: str):
    roots = {corpus_id: corpus_at(tmp_path / corpus_id[0], corpus_id) for corpus_id in corpus_ids}
    world = make_world(tmp_path, *roots.values())
    for root in roots.values():
        world.admit(root, provenance=registry.Fresh(), actor="alice")
    binding = rules.install_rule_binding(world, holdings_rule_bundle())
    chains = MutableChains()
    for root in roots.values():
        chains.add(root)
    return world, binding, roots, chains


def derive(world, coverage, binding, chains, *, facts=state_facts):
    return derive_holdings(
        world,
        frozenset(coverage),
        binding,
        chain_view=chains,
        state_facts=facts,
    )


def validate(world, receipt, chains, *, facts=state_facts):
    return validate_holdings_receipt(
        world,
        receipt,
        chain_view=chains,
        state_facts=facts,
    )


def test_derive_mints_a_receipt_naming_states_heads_and_binding(tmp_path):
    world, binding, roots, chains = admitted_world(tmp_path, ALPHA)
    encoded: list[object] = []

    def recording_facts(state: object) -> tuple[tuple[str, str], ...]:
        encoded.append(state)
        return state_facts(state)

    active, blocked, receipt = derive(world, {ALPHA}, binding, chains, facts=recording_facts)

    assert active == []
    assert blocked == []
    assert receipt.coverage == ((ALPHA, registry.corpus_state_identity(roots[ALPHA]), GENESIS),)
    assert receipt.rule_identity == binding.rule_identity
    assert receipt.implementation_identity == binding.implementation_identity
    assert receipt.active_set_digest == output_digest(active) == sha256(v1.encode(active)).hexdigest()
    assert receipt.blocked_set_digest == output_digest(blocked) == sha256(v1.encode(blocked)).hexdigest()
    assert encoded == [OPAQUE_STATE]


def test_identity_digests_every_member(tmp_path):
    world, binding, _roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)
    expected = v1.digest(
        HOLDINGS_RECEIPT_DOMAIN,
        [
            "holdings-reduction",
            [[corpus, state, head] for corpus, state, head in receipt.coverage],
            binding.rule_identity,
            binding.implementation_identity,
            receipt.active_set_digest,
            receipt.blocked_set_digest,
        ],
    )
    mutations = {
        "kind": "other",
        "coverage": ((ALPHA, "a" * 64, GENESIS),),
        "rule_identity": "b" * 64,
        "implementation_identity": "c" * 64,
        "active_set_digest": "d" * 64,
        "blocked_set_digest": "e" * 64,
    }

    assert receipt.identity() == expected
    for member, value in mutations.items():
        doctored = replace(receipt)
        object.__setattr__(doctored, member, value)
        assert doctored.identity() != receipt.identity(), member


def test_validated_reproduces_byte_for_byte(tmp_path):
    world, binding, _roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)
    encoded: list[object] = []

    def recording_facts(state: object) -> tuple[tuple[str, str], ...]:
        encoded.append(state)
        return state_facts(state)

    assert validate(world, receipt, chains, facts=recording_facts).outcome == "validated"
    assert encoded == [OPAQUE_STATE]


def test_a_wrong_reduction_is_refuted(tmp_path):
    world, binding, _roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)

    outcome = validate(world, replace(receipt, blocked_set_digest="a" * 64), chains)

    assert outcome.outcome == "refuted"


def test_an_absent_implementation_is_unresolvable_never_refuted(tmp_path):
    world, binding, _roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)
    rules.remove_rule_binding(world, binding)

    outcome = validate(world, receipt, chains)

    assert outcome.outcome == "unresolvable"


def test_corpora_not_states_is_malformed_before_external_reads(tmp_path):
    world, binding, _roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)
    document = asdict(receipt)
    document["coverage"] = ((ALPHA, BETA, GENESIS),)
    rules.remove_rule_binding(world, binding)

    def unread(_root: Path):
        raise AssertionError("malformed validation consulted a corpus")

    outcome = validate_holdings_receipt(
        world,
        document,  # type: ignore[arg-type]
        chain_view=unread,
        state_facts=lambda _state: (_ for _ in ()).throw(AssertionError("state facts consulted")),
    )

    assert outcome.outcome == "malformed"


def test_a_bare_version_string_is_malformed(tmp_path):
    world, binding, _roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)
    with pytest.raises(ValueError, match="implementation_identity"):
        replace(receipt, implementation_identity="v1")
    document = asdict(receipt)
    document["implementation_identity"] = "v1"

    outcome = validate_holdings_receipt(
        world,
        document,  # type: ignore[arg-type]
        chain_view=lambda _root: (_ for _ in ()).throw(AssertionError("corpus consulted")),
        state_facts=lambda _state: (_ for _ in ()).throw(AssertionError("state facts consulted")),
    )

    assert outcome.outcome == "malformed"


def test_chain_heads_are_committed_inputs(tmp_path):
    world, binding, roots, chains = admitted_world(tmp_path, ALPHA)
    old_active, old_blocked, old_receipt = derive(world, {ALPHA}, binding, chains)
    chains.add(roots[ALPHA], unmatched_intent())

    old_outcome = validate(world, old_receipt, chains)
    new_active, new_blocked, new_receipt = derive(world, {ALPHA}, binding, chains)

    assert old_outcome.outcome == "validated"
    assert old_receipt.coverage[0][1] == new_receipt.coverage[0][1]
    assert old_receipt.coverage[0][2] != new_receipt.coverage[0][2]
    assert old_receipt.identity() != new_receipt.identity()
    assert (old_active, old_blocked) == ([], [])
    assert new_active == []
    assert new_blocked == [
        {"location": f"store:{STORE}:held.bin", "reasons": ["unsettled"], "heads": []}
    ]


def test_chain_heads_are_committed_inputs_through_the_production_seam(certified_work):
    corpus_root = certified_work / "corpus"
    science_root.init_corpus_root(corpus_root)
    manifest = science_root.open_corpus(corpus_root).adopt_manifest(profile=PINS)
    world = registry.World(
        registry.WorldConfig(certified_work / "world", "f" * 32, (corpus_root,)),
        DefaultExecutor,
        chain_head=ChainHeads(),
        corpus_executor_factory=science_root.durable_executor_factory(),
    )
    world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
    binding = rules.install_rule_binding(world, holdings_rule_bundle())
    seam = science_root._log_seam()
    old_active, old_blocked, old_receipt = derive_holdings(
        world,
        frozenset({manifest.corpus_id}),
        binding,
        chain_view=seam.inspect_registered,
        state_facts=seam.state_facts,
    )
    science_root.holdings_seam().append_intent(
        corpus_root,
        intent_payload(
            location=StoreLocator(STORE, "held.bin"),
            act_kind="write",
            event_token="event",
            actor="alice",
        ),
    )

    old_outcome = validate_holdings_receipt(
        world,
        old_receipt,
        chain_view=seam.inspect_registered,
        state_facts=seam.state_facts,
    )
    new_active, new_blocked, new_receipt = derive_holdings(
        world,
        frozenset({manifest.corpus_id}),
        binding,
        chain_view=seam.inspect_registered,
        state_facts=seam.state_facts,
    )

    assert old_outcome.outcome == "validated"
    assert (old_active, old_blocked) == ([], [])
    assert old_receipt.coverage[0][1] == new_receipt.coverage[0][1]
    assert old_receipt.coverage[0][2] != new_receipt.coverage[0][2]
    assert old_receipt.identity() != new_receipt.identity()
    assert new_active == []
    assert new_blocked == [
        {"location": f"store:{STORE}:held.bin", "reasons": ["unsettled"], "heads": []}
    ]


def test_a_missing_or_non_ancestor_head_is_unresolvable(tmp_path):
    world, binding, _roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)
    coverage = ((ALPHA, receipt.coverage[0][1], FABRICATED),)

    outcome = validate(world, replace(receipt, coverage=coverage), chains)

    assert outcome.outcome == "unresolvable"


@pytest.mark.parametrize("failure", ["absent-corpus", "moved-state"])
def test_an_absent_corpus_or_named_state_is_unresolvable(tmp_path, failure):
    world, binding, roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)
    if failure == "absent-corpus":
        world = registry.World(
            registry.WorldConfig(tmp_path / "other-world", "e" * 32, ()),
            DefaultExecutor,
            chain_head=lambda root: (GENESIS, GENESIS),
            corpus_executor_factory=DefaultExecutor,
        )
        rules.install_rule_binding(world, holdings_rule_bundle())
    else:
        Corpus(roots[ALPHA]).add(stored.dataset_node("new", title="new"))

    outcome = validate(world, receipt, chains)

    assert outcome.outcome == "unresolvable"


def test_an_active_writer_makes_the_named_state_unresolvable(tmp_path):
    world, binding, roots, chains = admitted_world(tmp_path, ALPHA)
    _active, _blocked, receipt = derive(world, {ALPHA}, binding, chains)

    with _root_state_for(roots[ALPHA], DefaultExecutor).lock:
        outcome = validate(world, receipt, chains)

    assert outcome.outcome == "unresolvable"


def test_signing_half_the_coverage_fails(tmp_path):
    world, binding, roots, chains = admitted_world(tmp_path, ALPHA, BETA)
    _active, _blocked, narrow = derive(world, {ALPHA}, binding, chains)
    chains.add(roots[BETA], unmatched_intent())
    captured = capture_coverage(
        world,
        frozenset({ALPHA, BETA}),
        chain_view=chains,
        state_facts=state_facts,
    )
    full_coverage = tuple(
        (row["corpus_id"], row["corpus_state"], row["chain_head"])
        for row in captured["corpora"]  # type: ignore[union-attr]
    )

    outcome = validate(world, replace(narrow, coverage=full_coverage), chains)

    assert outcome.outcome == "refuted"
