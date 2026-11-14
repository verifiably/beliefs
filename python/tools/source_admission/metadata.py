"""Portable admission metadata. This module never opens held evidence or imports refs."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import urlsplit

from beliefs.contract.domain import _defining_source_id, _name

__all__ = [
    "canonical_path",
    "check_continuity",
    "coverage_projection",
    "decode",
    "encode",
    "fields",
    "hex_digest",
    "mapping_fields",
    "parse_manifest",
    "parse_receipt",
    "validate_documents",
    "validate_pin",
]

Manifest = dict[str, Any]
Receipt = dict[str, Any]
QUDT_PREFIX = "http://qudt.org/vocab/unit/"
ROW_FIELDS = {
    "contract_path",
    "register_path",
    "contract_identity",
    "register_identity",
    "contract_sha256",
    "register_sha256",
    "source_pin",
}


def fields(value: Any, expected: set[str], where: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{where}: expected exactly {sorted(expected)}")


def text(value: Any, where: str) -> None:
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError(f"{where}: expected nonempty text without control characters")


def hex_digest(value: Any, where: str, prefix: str = "") -> None:
    if not isinstance(value, str) or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{where}: expected {prefix}64 lowercase hex")


def commit(value: Any, where: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError(f"{where}: expected full Git SHA")


def canonical_path(value: Any) -> None:
    if (
        not isinstance(value, str)
        or not value
        or any(x in value for x in ("\\", ":", "*", "?", "[", "]"))
        or any(p in ("", ".", "..") for p in value.split("/"))
    ):
        raise ValueError(f"inventory path {value!r}: expected normalized repository-relative path")


def decode(data: bytes) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"non-JSON constant: {value}")

    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def encode(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def version(value: Any) -> None:
    if type(value) is not int or value != 1:
        raise ValueError("version: expected integer 1")


def validate_pin(pin: Any) -> None:
    fields(pin, {"revision", "sha256", "held_ref", "locator"}, "external pin")
    text(pin["revision"], "external revision")
    hex_digest(pin["sha256"], "external sha256")
    if pin["held_ref"] != "sha256:" + pin["sha256"]:
        raise ValueError("external held_ref must equal sha256 content address")
    text(pin["locator"], "external locator")
    url = urlsplit(pin["locator"])
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username is not None
        or url.password is not None
        or "\\" in pin["locator"]
        or any(c.isspace() for c in pin["locator"])
    ):
        raise ValueError("external locator must be an absolute public HTTP(S) URL without credentials")


def validate_documents(documents: Any) -> None:
    if not isinstance(documents, list) or not documents:
        raise ValueError("external documents must be a nonempty ordered list")
    seen = set()
    for pin in documents:
        validate_pin(pin)
        if pin["held_ref"] in seen:
            raise ValueError("external duplicate document held_ref")
        seen.add(pin["held_ref"])


def resources(value: Any) -> None:
    fields(value, {"ucum", "qudt"}, "resources")
    for pin in value.values():
        validate_pin(pin)


def mapping_fields(value: Any) -> None:
    fields(value, {"ucum", "qudt"}, "unit mappings")
    text(value["ucum"], "UCUM code")
    if ":" in value["ucum"] or any(c.isspace() for c in value["ucum"]):
        raise ValueError("UCUM code must be bare and case-sensitive")
    if value["qudt"] is not None and (
        not isinstance(value["qudt"], str)
        or re.fullmatch(re.escape(QUDT_PREFIX) + r"[A-Za-z0-9][A-Za-z0-9_-]*", value["qudt"]) is None
    ):
        raise ValueError("QUDT mapping must be the exact full HTTP unit IRI or null")


def parse_manifest(data: bytes) -> Manifest:
    value = decode(data)
    fields(
        value,
        {
            "version",
            "source_id",
            "namespace",
            "contract_identity",
            "documents",
            "resources",
            "units",
            "semantic_review_sha256",
        },
        "manifest",
    )
    version(value["version"])
    _defining_source_id(value["source_id"], "manifest source_id")
    _name(value["namespace"], "manifest namespace")
    hex_digest(value["contract_identity"], "manifest contract_identity")
    hex_digest(value["semantic_review_sha256"], "semantic_review_sha256")
    validate_documents(value["documents"])
    resources(value["resources"])
    if not isinstance(value["units"], dict) or not value["units"]:
        raise ValueError("manifest units must be a nonempty map")
    for key, mapping in value["units"].items():
        if not key.startswith(value["namespace"] + "/"):
            raise ValueError("unit outside manifest namespace")
        _name(key.split("/", 1)[1], "unit name")
        mapping_fields(mapping)
    return value


def coverage_projection(source_id: str, owner: dict, row: dict) -> dict:
    return {
        "source_id": source_id,
        "owner": owner,
        **{k: row[k] for k in ROW_FIELDS - {"contract_path", "register_path"}},
    }


def check_continuity(baseline: dict, candidate: dict) -> None:
    """Every historical reservation and identity persists; locator paths may move."""
    for sid, source in baseline["sources"].items():
        current = candidate["sources"].get(sid)
        if (
            current is None
            or current["owner"] != source["owner"]
            or not set(source["aliases"]).issubset(current["aliases"])
        ):
            raise ValueError(f"baseline source reservation/owner/alias changed: {sid}")
    for ns, lineage in baseline["lineages"].items():
        current = candidate["lineages"].get(ns)
        if current is None or any(current[k] != lineage[k] for k in ("genesis", "source_id")):
            raise ValueError(f"baseline lineage changed: {ns}")
        rows = {r["contract_identity"]: r for r in current["revisions"]}
        for row in lineage["revisions"]:
            other = rows.get(row["contract_identity"])
            owner = baseline["sources"][lineage["source_id"]]["owner"]
            if other is None or coverage_projection(lineage["source_id"], owner, row) != coverage_projection(
                lineage["source_id"], owner, other
            ):
                raise ValueError(f"baseline historical row changed: {ns}/{row['contract_identity']}")


def parse_receipt(data: bytes) -> Receipt:
    value = decode(data)
    fields(
        value,
        {
            "version",
            "verdict",
            "mechanism",
            "baseline",
            "candidate",
            "coverage",
            "manifest_sha256",
            "semantic_review_sha256",
            "resources",
            "mappings",
        },
        "receipt",
    )
    version(value["version"])
    if value["verdict"] != "pass":
        raise ValueError("receipt verdict must be pass")
    for key in ("manifest_sha256", "semantic_review_sha256"):
        hex_digest(value[key], key)
    mech = value["mechanism"]
    fields(
        mech,
        {"beliefs_commit", "refs_commit", "registry_fingerprint", "tracked_inputs", "registry_files", "distributions"},
        "mechanism",
    )
    for key in ("beliefs_commit", "refs_commit"):
        commit(mech[key], key)
    hex_digest(mech["registry_fingerprint"], "registry_fingerprint")
    for key in ("tracked_inputs", "registry_files", "distributions"):
        if not isinstance(mech[key], dict) or not mech[key]:
            raise ValueError(f"mechanism {key}: expected nonempty map")
        for name, item in mech[key].items():
            canonical_path(name)
            if key == "distributions":
                text(item, "distribution version")
            else:
                hex_digest(item, name)
            if key == "tracked_inputs" and name.split("/", 1)[0] not in {"beliefs", "refs", "atoms", "nodes"}:
                raise ValueError("tracked input needs a repository qualifier")
            if key == "registry_files" and "/" in name:
                raise ValueError("registry_files keys must be filenames")
    for key in ("baseline", "candidate"):
        snapshot = value[key]
        fields(snapshot, {"sha256", "inventory_utf8"} | ({"commit"} if key == "baseline" else set()), key)
        hex_digest(snapshot["sha256"], key + " sha256")
        if (
            not isinstance(snapshot["inventory_utf8"], str)
            or hashlib.sha256(snapshot["inventory_utf8"].encode("utf-8")).hexdigest() != snapshot["sha256"]
        ):
            raise ValueError(f"{key} snapshot hash mismatch")
        fields(decode(snapshot["inventory_utf8"].encode()), {"version", "sources", "lineages"}, key + " inventory")
    if value["baseline"]["commit"] != mech["beliefs_commit"]:
        raise ValueError("baseline commit differs from mechanism")
    if mech["tracked_inputs"].get("beliefs/contracts/source-ownership/INVENTORY.json") != value["baseline"]["sha256"]:
        raise ValueError("baseline inventory is not bound to mechanism inputs")
    coverage = value["coverage"]
    fields(coverage, {"source_id", "owner", "namespace", "row"}, "coverage")
    _defining_source_id(coverage["source_id"], "receipt source_id")
    _name(coverage["namespace"], "receipt namespace")
    fields(coverage["owner"], {"namespace", "genesis"}, "owner")
    if coverage["owner"]["namespace"] != coverage["namespace"]:
        raise ValueError("coverage owner namespace mismatch")
    hex_digest(coverage["owner"]["genesis"], "owner genesis")
    row = coverage["row"]
    fields(row, ROW_FIELDS, "coverage row")
    for key in ("contract_identity", "contract_sha256", "register_sha256"):
        hex_digest(row[key], key)
    hex_digest(row["register_identity"], "register_identity", "assumptions-register:")
    for key in ("contract_path", "register_path"):
        canonical_path(row[key])
    fields(row["source_pin"], {"kind", "documents"}, "external source_pin")
    if row["source_pin"]["kind"] != "external":
        raise ValueError("receipt must cover external row")
    validate_documents(row["source_pin"]["documents"])
    resources(value["resources"])
    if not isinstance(value["mappings"], dict) or not value["mappings"]:
        raise ValueError("receipt mappings must be nonempty map")
    units = {}
    for key, mapping in value["mappings"].items():
        fields(mapping, {"ucum", "qudt"}, "receipt mapping")
        for scheme in ("ucum", "qudt"):
            result = mapping[scheme]
            if result is None and scheme == "qudt":
                continue
            primary = "code" if scheme == "ucum" else "iri"
            fields(result, {primary, "reference", "release", "evidence_sha256", "verdict"}, scheme + " result")
            if (
                result["verdict"] != "pass"
                or result["release"] != value["resources"][scheme]["revision"]
                or result["evidence_sha256"] != value["resources"][scheme]["sha256"]
            ):
                raise ValueError(f"{scheme} result disagrees with resource/verdict")
            text(result[primary], scheme)
            expected = (
                "ucum:" + result[primary] if scheme == "ucum" else "qudt.unit:" + result[primary][len(QUDT_PREFIX) :]
            )
            if result["reference"] != expected:
                raise ValueError(f"{scheme} reference spelling mismatch")
        units[key] = {"ucum": mapping["ucum"]["code"], "qudt": mapping["qudt"]["iri"] if mapping["qudt"] else None}
    # Reuse the manifest shape and mapping spelling checks; its historical byte digest
    # remains provenance because the original formatting is not embedded here.
    parse_manifest(
        encode(
            {
                "version": 1,
                "source_id": coverage["source_id"],
                "namespace": coverage["namespace"],
                "contract_identity": row["contract_identity"],
                "documents": row["source_pin"]["documents"],
                "resources": value["resources"],
                "units": units,
                "semantic_review_sha256": value["semantic_review_sha256"],
            }
        )
    )
    return value
