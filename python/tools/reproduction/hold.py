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
    Held,
    admission_state,
)
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.root import holdings_seam
from reproduction import findings, paths, state, world
from reproduction.authority import AUTHORITY
from reproduction.vocabulary import profile

OBSERVER = "mm30-reproduction-observer"
INSTRUMENT = "mm30-reproduction/hold.v1"


def dataset_record(*, name: str, digest: str, title: str, accession: str) -> tuple[Node, str]:
    node = stored.dataset_node(
        title=title,
        resources=[{"name": name, "digest": digest}],
        empirical_observation={"locator": f"accession:{accession}", "attested_by": AUTHORITY.actor},
    )
    return node, node.id


def main() -> int:
    target = yaml.safe_load(paths.TARGET.read_text())
    dataset_path = Path(target["dataset_path"])
    held = dataset_path / target["held_file"] if dataset_path.is_dir() else dataset_path
    if not held.is_file():
        print(f"REFUSED: held_file {held} is not a regular file; fix target.yaml (driver correction)")
        return 2
    content = held.read_bytes()
    digest = "sha256:" + sha256(content).hexdigest()
    st = state.load()
    relative = f"{target['dataset_id'].split(':', 1)[1]}/{held.name}"
    ctx = ActContext(
        paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam(), profile=profile()
    )
    published = write(ctx, StoreLocator(st["store_id"], relative), content, expected=digest)
    node, address = dataset_record(
        name=held.name,
        digest=digest,
        title=target["dataset_id"],
        accession=target["dataset_id"].split(":", 1)[1].upper(),
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
        "closed",
        "Source Ensembl gene rows retained; interpretation belongs to the explicit assay and mapping",
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


def source(name: str, content: bytes, *, empirical: bool = False) -> dict[str, str]:
    """Hold exact bytes in this run's existing store and retain both record addresses."""
    if Path(name).name != name or name in {"", ".", ".."}:
        raise ValueError("a held source name is one basename")
    st = state.load()
    digest = "sha256:" + sha256(content).hexdigest()
    relative = "phf19-sources/" + name
    ctx = ActContext(
        paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam(), profile=profile()
    )
    observation = write(ctx, StoreLocator(st["store_id"], relative), content, expected=digest)
    kwargs = (
        {"empirical_observation": {"locator": "accession:GSE179929", "attested_by": AUTHORITY.actor}}
        if empirical
        else {}
    )
    node = stored.dataset_node(title="PHF19 source " + name, resources=[{"name": name, "digest": digest}], **kwargs)
    minted = world.open_writer().add(node)
    return {
        "dataset": minted.id,
        "holdings": "holdings-observation:" + observation.record.identity(),
        "digest": digest,
        "relative": relative,
        "name": name,
    }


def restore(saved: dict, view) -> bytes:
    """Recover only through matching run-held dataset, observation, location and digest."""
    from beliefs.holdings.records import Found

    declared = stored.dataset_declaration(view.get(saved["dataset"]))
    (resource,) = declared.resources
    observation = stored.holdings_observation_value(view.get(saved["holdings"]))
    location = observation.location
    if (
        not isinstance(location, StoreLocator)
        or location.store_id != state.load()["store_id"]
        or location.relative_path != saved["relative"]
        or not isinstance(observation.outcome, Found)
        or resource.digest != saved["digest"]
        or observation.outcome.digest != saved["digest"]
        or observation.expected != saved["digest"]
        or resource.name != saved["name"]
    ):
        raise RuntimeError("held source record, location or digest mismatch")
    path = paths.STORE_ROOT / location.relative_path
    if not path.resolve().is_relative_to(paths.STORE_ROOT.resolve()):
        raise RuntimeError("held source escapes run store")
    content = path.read_bytes()
    if "sha256:" + sha256(content).hexdigest() != saved["digest"]:
        raise RuntimeError("held source digest mismatch")
    return content
