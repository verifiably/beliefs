"""Step 1b: hold mm30's canonical concept identifiers as a dataset."""

from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

import yaml

from beliefs import stored
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.identifiers import not_a_canonical_identifier
from beliefs.root import holdings_seam
from reproduction import findings, paths, state, world
from reproduction.authority import AUTHORITY

OBSERVER = "mm30-reproduction-observer"
INSTRUMENT = "mm30-reproduction/concepts.v1"
RESOURCE = "mm30-concepts.txt"


def concept_lines(predecessor: Path) -> bytes:
    ids: list[str] = []
    for path in sorted((predecessor / "entities" / "concepts").glob("*.md")):
        block = path.read_text(errors="replace").split("---", 2)
        front = yaml.safe_load(block[1]) if len(block) >= 3 else None
        if not isinstance(front, dict) or front.get("kind") != "concept" or not isinstance(front.get("id"), str):
            raise ValueError(f"{path}: not a concept record with an id")
        problem = not_a_canonical_identifier(front["id"])
        if problem is not None:
            raise ValueError(f"{path}: {front['id']!r} is not a canonical identifier: {problem}")
        ids.append(front["id"])
    return "".join(identifier + "\n" for identifier in sorted(ids)).encode()


def main() -> int:
    content = concept_lines(paths.PREDECESSOR)
    count = content.count(b"\n")
    digest = "sha256:" + sha256(content).hexdigest()
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name=RESOURCE, digest=digest),)))
    assert address is not None
    held_copy = paths.WORK / RESOURCE
    held_copy.write_bytes(content)
    state.save(concepts_address=address, concepts_file=str(held_copy), concepts_count=count)
    from reproduction import vocabulary

    vocabulary._document.cache_clear()
    world.adopt()
    st = state.load()
    ctx = ActContext(paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam(), profile=vocabulary.profile())
    write(ctx, StoreLocator(st["store_id"], f"mm30-concepts/{RESOURCE}"), content, expected=digest)
    node = stored.dataset_node(address.removeprefix("dataset:"), title="mm30 concept vocabulary", resources=[{"name": RESOURCE, "digest": digest}])
    minted = world.open_writer().add(node)
    state.save(concepts_ref=minted.id)
    findings.record(1, "closed", f"held {count} concept identifiers as {digest}; dataset {minted.id}; the line format is the tool's (design §6.3)")
    print(f"held {count} concepts as {digest}; dataset {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
