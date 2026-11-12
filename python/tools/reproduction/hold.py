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


def _membership(inputs, original: bytes):
    import json
    from dataclasses import replace

    from reproduction import analysis_inputs

    members = analysis_inputs.hgnc_members(original)
    manifest = json.dumps(
        {
            "release": "2025-09-05",
            "source_sha256": sha256(original).hexdigest(),
            "parser_sha256": sha256(Path(analysis_inputs.__file__).read_bytes()).hexdigest(),
            "output_sha256": sha256(members).hexdigest(),
            "member_count": len(members.splitlines()),
        },
        sort_keys=True,
    ).encode()
    refs = {}
    for name, content in [("hgnc_members", members), ("hgnc_derivation", manifest)]:
        digest = "sha256:" + sha256(content).hexdigest()
        refs[name + "_sha256"] = digest.removeprefix("sha256:")
        refs[name + "_dataset"] = stored.dataset_node(title=name, resources=[{"name": name, "digest": digest}]).id
    return (
        replace(inputs, mapping=replace(inputs.mapping, reference={**inputs.mapping.reference, **refs})),
        members,
        manifest,
    )


def prepare_phf19(declaration, *, predecessor: Path, hgnc: Path, ensembl: Path) -> None:
    """Prepare only the checked selected route; every reference is held in this run."""
    import json

    from beliefs.profile import shipped_assumptions_register
    from beliefs.register import register_from_projection
    from reproduction import analysis_inputs, type_target, vocabulary

    checked = analysis_inputs.resolve_phf19(declaration, predecessor=predecessor, hgnc=hgnc, ensembl=ensembl)
    checked, members, manifest = _membership(checked, hgnc.read_bytes())
    locations = {**analysis_inputs.declared_paths(declaration, predecessor), "hgnc": hgnc, "ensembl": ensembl}
    sources = {key: source(path.name, path.read_bytes(), empirical=key == "matrix") for key, path in locations.items()}
    for name in vocabulary.HELD_SORTS:
        content = (Path(__file__).with_name("phf19-vocabulary") / (name + ".txt")).read_bytes()
        sources[name] = source(name + ".txt", content)
    sources["hgnc-members"] = source("hgnc-members.txt", members)
    sources["hgnc-derivation"] = source("hgnc-derivation.json", manifest)
    sources["mapping-members"] = source("mapping-members.tsv", checked.mapping_members)
    provenance = {"declaration": declaration, "source_datasets": {k: v["dataset"] for k, v in sources.items()}}
    sources["provenance"] = source("provenance.json", json.dumps(provenance, sort_keys=True).encode())
    parser, estimator = type_target.implementation_digests()
    assay, estimate, rule = type_target.procedures(checked, parser_digest=parser, estimator_digest=estimator)
    writer = world.open_writer()
    mapping_node = writer.add(stored.referent_mapping_node(checked.mapping))
    assay_node = writer.add(stored.procedure_node(assay))
    estimator_node = writer.add(stored.procedure_node(estimate))
    rule_node = writer.add(stored.classification_rule_node(rule))
    registers = [shipped_assumptions_register(ns) for ns in ("general", "biology")]
    registers.append(
        register_from_projection(
            json.loads(Path(__file__).with_name("mm30-phf19-register.json").read_text()),
            source="mm30-phf19-register.json",
        )
    )
    register_ids = [writer.add(stored.assumptions_register_node(r)).id for r in registers]
    state.save(
        sources=sources,
        assay_ref=assay_node.id,
        estimator_ref=estimator_node.id,
        mapping_ref=mapping_node.id,
        grouping_rule_ref=rule_node.id,
        registers=register_ids,
        dataset_address=sources["matrix"]["dataset"],
        dataset_ref=sources["matrix"]["dataset"],
        held_file=str(paths.STORE_ROOT / sources["matrix"]["relative"]),
        held_digest=sources["matrix"]["digest"],
    )
    import yaml

    paths.TARGET.write_text(
        yaml.safe_dump(
            {
                "value_row": checked.feature,
                "group_separator": checked.separator,
                "positive_level": "PD",
                "source_proposition": checked.source_proposition,
                "source_dataset": checked.source_dataset,
            },
            sort_keys=True,
        )
    )


def recover_inputs():
    """Recheck correspondence from run-held sources, independent of acquisition paths."""
    import json

    from beliefs.corpus import ReadView
    from beliefs.referent_mapping import mapping_from_stored
    from reproduction import analysis_inputs, vocabulary

    st = state.load()
    view = ReadView.opened_at(paths.CORPUS_ROOT)
    sources = st["sources"]
    for item in sources.values():
        restore(item, view)
    provenance = json.loads(restore(sources["provenance"], view))
    if provenance["source_datasets"] != {k: v["dataset"] for k, v in sources.items() if k != "provenance"}:
        raise RuntimeError("provenance source inventory differs from held closure")
    declaration = {
        **provenance["declaration"],
        "paths": {k: sources[k]["relative"] for k in ("proposition", "dataset", "matrix", "crosswalk")},
    }
    checked = analysis_inputs.resolve_phf19(
        declaration,
        predecessor=paths.STORE_ROOT,
        hgnc=paths.STORE_ROOT / sources["hgnc"]["relative"],
        ensembl=paths.STORE_ROOT / sources["ensembl"]["relative"],
    )
    checked, _members, _manifest = _membership(checked, restore(sources["hgnc"], view))
    if restore(sources["mapping-members"], view) != checked.mapping_members:
        raise RuntimeError("held mapping member bytes differ")
    vocabulary.check_members(
        restore(sources["hgnc"], view),
        restore(sources["hgnc-members"], view),
        restore(sources["hgnc-derivation"], view),
    )
    if mapping_from_stored(view.get(st["mapping_ref"])) != checked.mapping:
        raise RuntimeError("held mapping differs from checked sources")
    return checked


def verify_sources() -> bool:
    recover_inputs()
    return True
