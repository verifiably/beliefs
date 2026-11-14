"""Entirely synthetic admission records; never publisher or semantic evidence."""

import copy
import hashlib
import json

import yaml
from conftest import REPO_ROOT
from test_shipped_contract_checks import _admit, _copy_fixture_root, _inventory, _save_inventory, _write_shipped_pack

SID = "urn:beliefs:source:bipm-si-brochure"
NS = "si-brochure"
INVENTORY = "contracts/source-ownership/INVENTORY.json"
QUDT = "http://qudt.org/vocab/unit/"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def pin(label):
    value = digest(label.encode())
    return {
        "revision": "fixture-1",
        "sha256": value,
        "held_ref": "sha256:" + value,
        "locator": "https://example.invalid/" + label,
    }


def candidate(tmp_path):
    root = _copy_fixture_root(tmp_path)
    baseline = (root / INVENTORY).read_bytes()
    doc = yaml.safe_load((REPO_ROOT / "fixtures/contracts/series-time.yaml").read_text())
    for name, code, local in (("second", "s", "SEC"), ("hour", "h", "HR"), ("hertz", "Hz", "HZ")):
        doc["units"][name]["external"] = {"ucum": code, "qudt": QUDT + local}
    _write_shipped_pack(root, NS, yaml.safe_dump(doc))
    _admit(root, NS)
    inv = _inventory(root)
    row = inv["lineages"][NS]["revisions"][0]
    row["source_pin"] = {"kind": "external", "documents": [pin("normative")]}
    _save_inventory(root, inv)
    manifest = {
        "version": 1,
        "source_id": SID,
        "namespace": NS,
        "contract_identity": row["contract_identity"],
        "documents": copy.deepcopy(row["source_pin"]["documents"]),
        "resources": {"ucum": pin("ucum"), "qudt": pin("qudt")},
        "units": {NS + "/" + k: v["external"] for k, v in doc["units"].items()},
        "semantic_review_sha256": digest(b"synthetic semantic review"),
    }
    receipt = {
        "version": 1,
        "verdict": "pass",
        "mechanism": {
            "beliefs_commit": "a" * 40,
            "refs_commit": "b" * 40,
            "registry_fingerprint": "c" * 64,
            "tracked_inputs": {"beliefs/" + INVENTORY: digest(baseline)},
            "registry_files": {"grammars.toml": "d" * 64},
            "distributions": {"rdflib": "7.6.0"},
        },
        "baseline": {"commit": "a" * 40, "sha256": digest(baseline), "inventory_utf8": baseline.decode()},
        "candidate": {
            "sha256": digest((root / INVENTORY).read_bytes()),
            "inventory_utf8": (root / INVENTORY).read_text(),
        },
        "coverage": {
            "source_id": SID,
            "owner": inv["sources"][SID]["owner"],
            "namespace": NS,
            "row": copy.deepcopy(row),
        },
        "manifest_sha256": digest(encode(manifest)),
        "semantic_review_sha256": manifest["semantic_review_sha256"],
        "resources": manifest["resources"],
        "mappings": {},
    }
    for key, mapping in manifest["units"].items():
        receipt["mappings"][key] = {
            "ucum": {
                "code": mapping["ucum"],
                "reference": "ucum:" + mapping["ucum"],
                "release": "fixture-1",
                "evidence_sha256": manifest["resources"]["ucum"]["sha256"],
                "verdict": "pass",
            },
            "qudt": {
                "iri": mapping["qudt"],
                "reference": "qudt.unit:" + mapping["qudt"][len(QUDT) :],
                "release": "fixture-1",
                "evidence_sha256": manifest["resources"]["qudt"]["sha256"],
                "verdict": "pass",
            },
        }
    return root, manifest, receipt


def install(checker, root, receipt):
    data = encode(receipt)
    relative = "contracts/source-ownership/receipts/" + digest(data) + ".json"
    path = root / relative
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(data)
    checker.RECEIPT_SHA256 = {relative: digest(data)}
    checker.SOURCE_INVENTORY_SHA256 = digest((root / INVENTORY).read_bytes())
    return path
