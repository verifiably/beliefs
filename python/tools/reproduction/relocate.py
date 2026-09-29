"""Relocate the reproduced corpus and store into a world outside the checkout.

The science projects design (2026-09-23 §3.1) puts a research world at the
user's data location, outside every code checkout; the world beside the main
checkout stays the reproduction's measurement fixture and is not touched here.
Nothing is copied by hand: each root travels by `replicate_root` and is
admitted read-serviceable by `restore_root`, observed by a head artifact
exported from the fixture's world. `export_head_artifact` writes nothing, so
the fixture's world chain does not move. A world root is reconstructed, never
restored: the destination world is initialized fresh under a new `world_id`
and the replica arrives through `admit_arrival` with `ReplicaOf` provenance.

    uv run --frozen python -m reproduction.relocate <worlds directory>

creates `<worlds directory>/<world_id>/` holding `world/`, `corpora/mm30/`,
`store/`, the two exported head artifacts under `anchors/`, and
`relocation.json`, the record the reproduction record's addendum quotes.
"""

from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path

from beliefs.root import (
    LifecycleState,
    admit_arrival,
    export_head_artifact,
    init_world_root,
    open_world,
    read_lifecycle_state,
    replicate_root,
    restore_root,
)
from beliefs.world import WorldConfig, anchors, registry, verify
from reproduction import paths, state, world
from reproduction.authority import AUTHORITY


def _restore(source: Path, dest: Path, subject, artifact: bytes) -> verify.LogReport:
    # The engine publishes the replica into an existing parent; it creates only the leaf.
    dest.parent.mkdir(parents=True, exist_ok=True)
    replicate_root(source, dest, authority=AUTHORITY)
    report = restore_root(
        dest, subject, verify.ObserverSet((verify.ArtifactCarrier.from_bytes(artifact),)), authority=AUTHORITY
    )
    lifecycle = read_lifecycle_state(dest)
    if report.outcome != "validated" or lifecycle is not LifecycleState.READ_ONLY_SERVICEABLE:
        raise RuntimeError(f"{dest}: restore answered {report.outcome!r}, lifecycle {lifecycle.name}")
    return report


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    st = state.load()
    corpus_id, store_id = st["corpus_id"], st["store_id"]
    world_id = secrets.token_hex(16)
    home = Path(argv[1]).resolve() / world_id
    corpus_root, store_root = home / "corpora" / "mm30", home / "store"

    fixture = world.open_world()
    corpus_head = export_head_artifact(fixture, anchors.CorpusSubject(corpus_id))
    store_head = export_head_artifact(fixture, anchors.StoreSubject(store_id), store_root=paths.STORE_ROOT)
    (home / "anchors").mkdir(parents=True)
    (home / "anchors" / f"corpus-{corpus_id}.head").write_bytes(corpus_head)
    (home / "anchors" / f"store-{store_id}.head").write_bytes(store_head)

    corpus_report = _restore(paths.CORPUS_ROOT, corpus_root, anchors.CorpusSubject(corpus_id), corpus_head)
    store_report = _restore(paths.STORE_ROOT, store_root, anchors.StoreSubject(store_id), store_head)

    config = WorldConfig(home / "world", world_id, (corpus_root,))
    init_world_root(config, authority=AUTHORITY)
    record, arrival = admit_arrival(
        open_world(config, authority=AUTHORITY),
        corpus_root,
        registry.ReplicaOf(corpus_id),
        verify.ObserverSet((verify.ArtifactCarrier.from_bytes(corpus_head),)),
    )
    if arrival.outcome != "validated":
        raise RuntimeError(f"{corpus_root}: arrival answered {arrival.outcome!r}")

    relocation = {
        "world_id": world_id,
        "world_root": str(config.world_root),
        "corpus_root": str(corpus_root),
        "store_root": str(store_root),
        "corpus_id": record.corpus_id,
        "store_id": store_id,
        "source_world_id": st["world_id"],
        "source_corpus_root": str(paths.CORPUS_ROOT),
        "source_store_root": str(paths.STORE_ROOT),
        "restore": {"corpus": corpus_report.outcome, "store": store_report.outcome},
        "arrival": arrival.outcome,
        "admission": registry.provenance_projection(record.provenance),
    }
    (home / "relocation.json").write_text(json.dumps(relocation, indent=2, sort_keys=True) + "\n")
    print(json.dumps(relocation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
