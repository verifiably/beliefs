"""Mechanical coverage capture for the holdings reducer."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from nodes.core.projection import to_canonical_json

from science.corpus import ReadView, _root_state_for
from science.errors import CaptureDrift, CorpusStateMalformed, CoverageUnknown, ScienceError
from science.world import epoch, registry
from science.world.logmodel import (
    AbsentView,
    ChainView,
    GenesisEntryView,
    IntentEntryView,
    MalformedView,
    RegisteredEntryView,
    SettledEntryView,
)

StateFacts = Callable[[object], tuple[tuple[str, str], ...]]


def _surface(
    value: tuple[tuple[str, object], ...],
    state_facts: StateFacts,
) -> list[list[object]]:
    return [[path, [list(pair) for pair in state_facts(state)]] for path, state in value]


def _entry(entry: object, state_facts: StateFacts) -> dict[str, object]:
    if isinstance(entry, GenesisEntryView):
        return {
            "kind": "genesis",
            "payload": entry.payload.hex(),
            "baseline": _surface(entry.baseline, state_facts),
        }
    if isinstance(entry, IntentEntryView):
        return {"kind": "intent", "payload": entry.payload.hex()}
    if isinstance(entry, RegisteredEntryView):
        if entry.intent_digest is None or entry.consumer_tag is None:
            raise CorpusStateMalformed(f"{entry.digest}: a registered entry lacks its engine binding metadata")
        projected: dict[str, object] = {
            "kind": "registered",
            "txid": entry.txid,
            "intent_digest": entry.intent_digest,
            "consumer_tag": entry.consumer_tag,
            "initial": _surface(entry.initial, state_facts),
            "final": _surface(entry.final, state_facts),
        }
        if entry.fulfills is not None:
            projected["fulfills"] = entry.fulfills
        return projected
    if isinstance(entry, SettledEntryView):
        return {
            "kind": "settled",
            "txid": entry.txid,
            "registration": entry.registration,
            "outcome": "committed" if entry.committed else "rolled-back",
        }
    raise TypeError(f"unknown chain entry view: {type(entry).__name__}")


def _capture_one(
    world: registry.World,
    corpus_id: str,
    carrier: Path,
    chain_view: Callable[[Path], ChainView],
    state_facts: StateFacts,
) -> dict[str, object]:
    try:
        state = _root_state_for(carrier, world._corpus_executor_factory)
    except ScienceError:
        raise
    except Exception as caught:
        raise CorpusStateMalformed(f"{corpus_id}: {carrier}: capture could not open the corpus: {caught}") from caught
    with state.lock.capture():
        chain = chain_view(carrier)
        if isinstance(chain, (MalformedView, AbsentView)):
            raise CorpusStateMalformed(f"{corpus_id}: {carrier}: the corpus chain is not well formed")
        try:
            before = registry.corpus_state_identity(carrier)
        except CorpusStateMalformed as caught:
            raise CorpusStateMalformed(f"{corpus_id}: {carrier}: {caught}") from caught
        try:
            records = sorted(
                (
                    {"uid": node.uid, "canonical": to_canonical_json(node)}
                    for node in ReadView.opened_at(carrier).iter_stored()
                ),
                key=lambda record: record["uid"],
            )
        except Exception as caught:
            raise CorpusStateMalformed(f"{corpus_id}: {carrier}: record capture failed: {caught}") from caught
        chain_rows = [{"digest": entry.digest, "entry": _entry(entry, state_facts)} for entry in chain.entries]
        try:
            after = registry.corpus_state_identity(carrier)
        except CorpusStateMalformed as caught:
            raise CorpusStateMalformed(f"{corpus_id}: {carrier}: {caught}") from caught
        if before != after:
            raise CaptureDrift(
                f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                f"({before} -> {after}); the whole capture is discarded"
            )
    return {
        "corpus_id": corpus_id,
        "corpus_state": before,
        "chain_head": chain.tip,
        "records": records,
        "chain": chain_rows,
    }


def capture_coverage(
    world: registry.World,
    coverage: frozenset[str],
    *,
    chain_view: Callable[[Path], ChainView],
    state_facts: StateFacts,
) -> dict[str, object]:
    """Capture every stored record and the whole validated chain per corpus."""
    if not coverage:
        raise CoverageUnknown("a projection with no declared coverage is refused")
    carriers = epoch.resolve_coverage(world, coverage)
    return {
        "corpora": [
            _capture_one(world, corpus_id, carriers[corpus_id], chain_view, state_facts)
            for corpus_id in sorted(carriers)
        ]
    }
