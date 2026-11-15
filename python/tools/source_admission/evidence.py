"""Offline membership checks over one read of each explicitly bound regular file."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from pathlib import Path

from source_admission import metadata

__all__ = ["parse_bindings", "read_regular", "validate"]


def read_regular(path: Path) -> bytes:
    if not path.is_absolute():
        raise ValueError("held path must be absolute")
    if path != path.resolve():
        raise ValueError("held path must be explicitly resolved; record the resolved binding in the private run sheet")
    # O_NONBLOCK makes a concurrently substituted FIFO refuse without hanging.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("held input must be a regular file")
        return stream.read()


def parse_bindings(data: bytes) -> dict[str, Path]:
    value = metadata.decode(data)
    metadata.fields(value, {"version", "files"}, "bindings")
    metadata.version(value["version"])
    if not isinstance(value["files"], dict):
        raise TypeError("bindings files must be a mapping")
    result = {}
    for reference, path in value["files"].items():
        metadata.hex_digest(reference, "binding reference", "sha256:")
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError("binding path must be absolute")
        result[reference] = Path(path)
    return result


def validate(manifest: metadata.Manifest, bindings: dict[str, Path], refs_root: Path) -> dict:
    manifest = metadata.parse_manifest(metadata.encode(manifest))
    pins = {}
    for pin in [*manifest["documents"], *manifest["resources"].values()]:
        previous = pins.setdefault(pin["held_ref"], pin)
        if previous != pin:
            raise ValueError("inconsistent repeated held reference")
    review_ref = "sha256:" + manifest["semantic_review_sha256"]
    required = set(pins) | {review_ref}
    if set(bindings) != required:
        raise ValueError("missing or extra held bindings")
    held = {}
    for reference in sorted(required):
        data = read_regular(bindings[reference])
        if hashlib.sha256(data).hexdigest() != reference[len("sha256:") :]:
            raise ValueError("held SHA-256 mismatch")
        held[reference] = data
    if not held[review_ref].decode("utf-8").strip():
        raise ValueError("missing semantic review text")

    import refs
    from rdflib import RDF, Graph, URIRef

    if Path(refs.__file__).resolve().parents[3] != refs_root.resolve():
        raise ValueError("wrong imported refs root")
    registry = refs.Registry.default()
    resources = manifest["resources"]
    vocabularies = refs.parse_vocabularies(
        {
            prefix: {"issuer": "external", "release": resources[key]["revision"], "accepted": []}
            for key, prefix in (("ucum", "ucum"), ("qudt", "qudt.unit"))
        },
        registry,
    )
    try:
        with tempfile.TemporaryDirectory(prefix="beliefs-ucum-") as directory:
            copy = Path(directory) / "essence.xml"
            copy.write_bytes(held[resources["ucum"]["held_ref"]])
            table = refs.load_ucum_essence(copy)
        if not table.atoms:
            raise ValueError("UCUM table is empty")
        if table.version != resources["ucum"]["revision"]:
            raise ValueError("UCUM table release mismatch")
        tables = refs.UcumTables([table])
        graph = Graph()
        try:
            graph.parse(data=held[resources["qudt"]["held_ref"]], format="turtle")
        except Exception as exc:
            raise ValueError(f"invalid held QUDT Turtle: {type(exc).__name__}") from exc
        mappings = {}
        for name, mapping in sorted(manifest["units"].items()):
            code = mapping["ucum"]
            reference = "ucum:" + code
            refs.check_reference(reference, resources["ucum"]["revision"], registry, vocabularies, tables=tables)
            result = {
                "ucum": {
                    "code": code,
                    "reference": reference,
                    "release": resources["ucum"]["revision"],
                    "evidence_sha256": resources["ucum"]["sha256"],
                    "verdict": "pass",
                },
                "qudt": None,
            }
            iri = mapping["qudt"]
            if iri is not None:
                reference = "qudt.unit:" + iri[len(metadata.QUDT_PREFIX) :]
                curie = refs.check_reference(reference, resources["qudt"]["revision"], registry, vocabularies)
                pattern = registry.scheme(curie.prefix).uri_format
                if pattern is None or pattern.replace("$1", curie.local) != iri:
                    raise ValueError("QUDT expansion differs from stored IRI")
                if (URIRef(iri), RDF.type, URIRef("http://qudt.org/schema/qudt/Unit")) not in graph:
                    raise ValueError(f"QUDT release lacks exact unit subject: {iri}")
                result["qudt"] = {
                    "iri": iri,
                    "reference": reference,
                    "release": resources["qudt"]["revision"],
                    "evidence_sha256": resources["qudt"]["sha256"],
                    "verdict": "pass",
                }
            mappings[name] = result
    except refs.RefsError as exc:
        raise ValueError(f"refs membership refused: {exc}") from exc
    return {
        "mappings": mappings,
        "registry_fingerprint": registry.fingerprint,
        "digests": {ref: hashlib.sha256(data).hexdigest() for ref, data in held.items()},
    }
