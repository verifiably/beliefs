"""Step 3: hold the dataset's bytes in the store; mint the dataset record under its content address.

The dataset record's id is its content address: the run publication names
observed inputs by the spec's `dataset:sha256:<hex>` address, and the
eligibility refusal resolves that string against the corpus. The bridge is
crossed here, once, and unit-tested.
"""

from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

import yaml
from nodes.core.node import Node

from beliefs import stored
from beliefs.dataset import (
    ByteObservation,
    DatasetDeclaration,
    Held,
    ResourceDeclaration,
    admission_state,
    dataset_address,
)
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.root import holdings_seam
from reproduction import findings, paths, state, world
from reproduction.authority import AUTHORITY
from reproduction.vocabulary import profile

OBSERVER = "mm30-reproduction-observer"
INSTRUMENT = "mm30-reproduction/hold.v1"


def dataset_record(*, name: str, digest: str, title: str, facet: dict) -> tuple[Node, str]:
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name=name, digest=digest),)))
    assert address is not None
    node = stored.dataset_node(
        address.removeprefix("dataset:"),
        title=title,
        resources=[{"name": name, "digest": digest}],
        empirical_observation=facet,
    )
    return node, address


def main() -> int:
    target = yaml.safe_load(paths.TARGET.read_text())
    dataset_path = Path(target["dataset_path"])
    held = dataset_path / target["held_file"] if dataset_path.is_dir() else dataset_path
    if not held.is_file():
        print(f"REFUSED: held_file {held} is not a regular file; fix target.yaml (driver correction, record §8)")
        return 2
    content = held.read_bytes()
    digest = "sha256:" + sha256(content).hexdigest()
    st = state.load()
    relative = f"{target['dataset_id'].split(':', 1)[1]}/{held.name}"
    ctx = ActContext(paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam(), profile=profile())
    published = write(ctx, StoreLocator(st["store_id"], relative), content, expected=digest)
    # P2: the facet payload is authored, not checked. Say what we claim and file the gap.
    node, address = dataset_record(
        name=held.name,
        digest=digest,
        title=target["dataset_id"],
        facet={"boundary": "acquisition", "source": target["dataset_id"], "asserted_by": AUTHORITY.actor},
    )
    minted = world.open_writer().add(node)
    verdict = admission_state(
        stored.dataset_declaration(minted),
        (ByteObservation(digest=digest, location=published.record.location.canonical()),),
    )
    if not isinstance(verdict, Held):
        findings.record(3, "defect", f"held bytes with a matching digest did not read as Held: {verdict!r}")
        return 2
    findings.record(
        3,
        "design-gap",
        "empirical-observation facet is presence-only: is_empirical_observation read our authored payload unchecked",
        filed="domain lane (facet payload contract, kernel §11)",
    )
    state.save(
        dataset_ref=minted.id,
        dataset_address=address,
        held_file=str(held),
        held_digest=digest,
        store_relative_path=relative,
        holdings_observation_ref=f"holdings-observation:{published.record.identity()}",
    )
    print(f"held {held.name} ({len(content)} bytes) as {digest}; dataset {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
