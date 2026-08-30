"""Real act, capture, and reducer integration at the holdings crash windows."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from fixtures_cut6 import PINS
from nodes.core.frontmatter import node_to_markdown
from nodes.core.write_plan import CreateOp, DefaultExecutor
from test_world_build import ChainHeads

from beliefs import root as science_root
from beliefs import stored
from beliefs.holdings.boundary import ActContext, intent_payload, move, recheck, write
from beliefs.holdings.project import capture_coverage
from beliefs.holdings.records import Found, StoreLocator, holdings_observation
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.world import logmodel, registry, rules


def setup(root: Path):
    corpus_root = root / "corpus"
    science_root.init_corpus_root(corpus_root)
    manifest = science_root.open_corpus(corpus_root).adopt_manifest(profile=PINS)
    store_root = root / "store"
    store_id = science_root.init_store_root(store_root)
    world = registry.World(
        registry.WorldConfig(root / "world", "f" * 32, (corpus_root,)),
        DefaultExecutor,
        chain_head=ChainHeads(),
        corpus_executor_factory=science_root.durable_executor_factory(),
    )
    world.admit(corpus_root, provenance=registry.Fresh(), actor="alice")
    binding = rules.install_rule_binding(world, holdings_rule_bundle())
    context = ActContext(corpus_root, store_root, "observer", "instrument", "actor", science_root.holdings_seam())
    return context, store_id, manifest.corpus_id, world, binding


def captured_projection(context, corpus_id, world):
    seam = science_root._log_seam()
    return capture_coverage(
        world,
        frozenset({corpus_id}),
        chain_view=seam.inspect_registered,
        state_facts=seam.state_facts,
    )


def reduce(context, corpus_id, world, binding):
    captured = captured_projection(context, corpus_id, world)
    return cast(dict[str, Any], rules._resolve_rule_binding(world, binding).invoke(captured))


def test_the_kill_window_reads_unsettled_until_a_fulfilled_recheck_lifts_it(certified_work):
    context, store_id, corpus_id, world, binding = setup(certified_work)
    location = StoreLocator(store_id, "held.bin")
    context.seam.store_write(context.store_root, location.relative_path, b"original")

    def kill_before_write(_root, _path, _content):
        raise RuntimeError("kill")

    killed = replace(context, seam=replace(context.seam, store_write=kill_before_write))
    with pytest.raises(RuntimeError, match="kill"):
        write(killed, location, b"replacement")

    first = reduce(context, corpus_id, world, binding)
    assert first["active"] == []
    assert first["blocked"] == [{"location": location.canonical(), "reasons": ["unsettled"], "heads": []}]

    recheck(context, location)

    projection = cast(dict[str, Any], captured_projection(context, corpus_id, world))
    repaired = cast(dict[str, Any], rules._resolve_rule_binding(world, binding).invoke(projection))
    assert repaired["blocked"] == []
    assert [member["location"] for member in repaired["active"]] == [location.canonical()]
    chain = projection["corpora"][0]["chain"]
    intents = [row["digest"] for row in chain if row["entry"]["kind"] == "intent"]
    fulfillments = [
        row["entry"]["fulfills"]
        for row in chain
        if row["entry"]["kind"] == "registered" and "fulfills" in row["entry"]
    ]
    assert intents[0] not in fulfillments
    assert intents[1] in fulfillments


@pytest.mark.parametrize("case", ["wrong-location", "wrong-token", "no-observation"])
def test_nonqualifying_fulfillments_are_committed_and_leave_the_intent_unsettled(
    certified_work, case
):
    context, store_id, corpus_id, world, binding = setup(certified_work)
    location = StoreLocator(store_id, "held.bin")
    token = "intended-token"
    intent = context.seam.append_intent(
        context.observer_root,
        intent_payload(location=location, act_kind="write", event_token=token, actor=context.actor),
    )
    if case == "no-observation":
        node = stored.dataset_node("outside", title="Outside the holdings layout")
        path = "outside.md"
    else:
        record = holdings_observation(
            location=StoreLocator(store_id, "other.bin") if case == "wrong-location" else location,
            outcome=Found("sha256:" + "1" * 64),
            observer=context.observer,
            instrument=context.instrument,
            event_token="wrong-token" if case == "wrong-token" else token,
            observed_at="2026-08-24T12:00:00Z",
        )
        node = stored.holdings_observation_node(record)
        path = f"holdings-observation/{record.identity()}.md"
    context.seam.publish_fulfilling(
        context.observer_root,
        (CreateOp(path, node_to_markdown(node).encode("utf-8")),),
        intent,
    )

    viewed = science_root._log_seam().inspect_registered(context.observer_root)
    assert isinstance(viewed, logmodel.WellFormedView)
    assert any(
        isinstance(entry, logmodel.RegisteredEntryView) and entry.fulfills == intent
        for entry in viewed.entries
    )
    blocked = reduce(context, corpus_id, world, binding)["blocked"]
    assert len(blocked) == 1
    assert blocked[0]["location"] == location.canonical()
    assert blocked[0]["reasons"] == ["unsettled"]


def test_the_three_move_windows_read_exactly(certified_work):
    readings = []
    expected = []
    for name in ("between-appends", "before-mutation", "between-publications"):
        context, store_id, corpus_id, world, binding = setup(certified_work / name)
        source = StoreLocator(store_id, "source.bin")
        destination = StoreLocator(store_id, "destination.bin")
        context.seam.store_write(context.store_root, source.relative_path, b"payload")

        if name == "between-appends":
            original_append = context.seam.append_intent
            calls = 0

            def append(root, payload, original=original_append):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("kill")
                return original(root, payload)

            killed = replace(context, seam=replace(context.seam, append_intent=append))
        elif name == "before-mutation":
            def store_move(_root, _source, _destination):
                raise RuntimeError("kill")

            killed = replace(context, seam=replace(context.seam, store_move=store_move))
        else:
            original_publish = context.seam.publish_fulfilling
            calls = 0

            def publish(root, plan, fulfills, original=original_publish):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("kill")
                return original(root, plan, fulfills)

            killed = replace(context, seam=replace(context.seam, publish_fulfilling=publish))

        with pytest.raises(RuntimeError, match="kill"):
            move(killed, source, destination)
        result = reduce(context, corpus_id, world, binding)
        readings.append((
            [entry["location"] for entry in result["blocked"]],
            [member["location"] for member in result["active"]],
        ))
        if name == "between-appends":
            expected.append(([source.canonical()], []))
        elif name == "before-mutation":
            expected.append((sorted([source.canonical(), destination.canonical()]), []))
        else:
            expected.append(([destination.canonical()], [source.canonical()]))

    assert readings == expected
