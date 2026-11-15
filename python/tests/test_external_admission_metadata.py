"""Root-only receipt validation must never become an evidence admission shortcut."""

import copy
import importlib
from pathlib import Path

import pytest
from admission_fixtures import INVENTORY, NS, SID, candidate, digest, encode, install, pin
from test_shipped_contract_checks import _inventory, _load_checker, _repin, _save_inventory, _successor


def metadata():
    assert (Path(__file__).parents[1] / "tools/source_admission/metadata.py").is_file()
    return importlib.import_module("source_admission.metadata")


def test_candidate_inspection_does_not_grant_standing_admission(tmp_path):
    root, _, receipt = candidate(tmp_path)
    checker = _load_checker()
    assert hasattr(checker, "inspect_candidate")
    assert checker.inspect_candidate(root, (root / INVENTORY).read_bytes()) == []
    _repin(checker, root)
    assert any("receipt" in e for e in checker.check(root))
    install(checker, root, receipt)
    assert checker.check(root) == []


@pytest.mark.parametrize("document", ["manifest", "receipt"])
@pytest.mark.parametrize("mutation", ["extra", "version", "bool", "duplicate", "constant", "bad-digest"])
def test_strict_schemas(tmp_path, document, mutation):
    _, manifest, receipt = candidate(tmp_path)
    value = manifest if document == "manifest" else receipt
    if mutation == "extra":
        value["unexpected"] = 1
    if mutation == "version":
        value["version"] = 2
    if mutation == "bool":
        value["version"] = True
    if mutation == "bad-digest":
        value["semantic_review_sha256"] = "X" * 64
    data = encode(value)
    if mutation == "duplicate":
        data = data.replace(b'"version": 1', b'"version": 1, "version": 1')
    if mutation == "constant":
        data = data.replace(b'"version": 1', b'"version": NaN')
    with pytest.raises((ValueError, TypeError)):
        getattr(metadata(), "parse_" + document)(data)


@pytest.mark.parametrize(
    "mutation", ["snapshot", "failed", "mapping", "coverage", "baseline", "path", "resource", "receipt-pin", "unlisted"]
)
def test_invalid_receipt_refuses(tmp_path, mutation):
    root, _, receipt = candidate(tmp_path)
    checker = _load_checker()
    if mutation == "snapshot":
        receipt["candidate"]["inventory_utf8"] += " "
    if mutation == "failed":
        receipt["verdict"] = "fail"
    if mutation == "mapping":
        receipt["mappings"][NS + "/second"]["ucum"]["code"] = "h"
    if mutation == "coverage":
        receipt["coverage"]["owner"]["genesis"] = "e" * 64
    if mutation == "baseline":
        receipt["baseline"]["commit"] = "e" * 40
    if mutation == "path":
        receipt["mechanism"]["tracked_inputs"]["/host/private"] = "e" * 64
    if mutation == "resource":
        receipt["resources"]["ucum"]["locator"] = "file:///private/evidence"
    path = install(checker, root, receipt)
    if mutation == "receipt-pin":
        path.write_bytes(path.read_bytes() + b" ")
    if mutation == "unlisted":
        checker.RECEIPT_SHA256.clear()
    assert checker.check(root), mutation


def test_authored_successor_needs_no_external_payloads(tmp_path, monkeypatch):
    root, _, receipt = candidate(tmp_path)
    checker = _load_checker()
    install(checker, root, receipt)
    _successor(root)
    _repin(checker, root)
    original = Path.open

    def only_repository(path, *args, **kwargs):
        assert path.is_relative_to(root), f"held access attempted: {path}"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", only_repository)
    assert checker.check(root) == []


def test_projection_ignores_paths_only(tmp_path):
    _, _, receipt = candidate(tmp_path)
    coverage = receipt["coverage"]
    moved = copy.deepcopy(coverage["row"])
    moved["contract_path"] = "domains/si-brochure/history/" + moved["contract_identity"] + "/DOMAIN.yaml"
    project = metadata().coverage_projection
    assert project(SID, coverage["owner"], moved) == project(SID, coverage["owner"], coverage["row"])
    moved["source_pin"]["documents"][0]["revision"] = "changed"
    assert project(SID, coverage["owner"], moved) != project(SID, coverage["owner"], coverage["row"])


@pytest.mark.parametrize(
    "mutation", ["same-source", "cross-source", "duplicate-ref", "alias", "adoption", "shadow", "ancestor"]
)
def test_inventory_only_checks(tmp_path, mutation):
    root, _, _receipt = candidate(tmp_path)
    checker = _load_checker()
    assert hasattr(checker, "inspect_candidate")
    inv = _inventory(root)
    row = inv["lineages"][NS]["revisions"][0]
    if mutation == "same-source":
        # Two existing revisions in a single source may cite the same normative document.
        for other in inv["lineages"]["general"]["revisions"]:
            other["source_pin"] = {"kind": "external", "documents": [pin("general-doc")]}
    if mutation == "cross-source":
        inv["lineages"]["general"]["revisions"][0]["source_pin"] = row["source_pin"]
    if mutation == "duplicate-ref":
        row["source_pin"]["documents"] *= 2
    if mutation == "alias":
        inv["sources"][SID]["aliases"] = [next(iter(inv["sources"]))]
    if mutation == "adoption":
        other = inv["lineages"]["general"]["revisions"][0]
        path = root / other["contract_path"]
        path.write_bytes(path.read_bytes() + b"\n")
        (root / "python/src/beliefs" / other["contract_path"]).write_bytes(path.read_bytes())
        other["contract_sha256"] = digest(path.read_bytes())
    if mutation == "shadow":
        (root / "python/tools/reproduction/shadow.yaml").write_bytes(
            (root / "domains/general/DOMAIN.yaml").read_bytes()
        )
    if mutation == "ancestor":
        (root / inv["lineages"]["general"]["revisions"][0]["contract_path"]).unlink()
    _save_inventory(root, inv)
    errors = checker.inspect_candidate(root, (root / INVENTORY).read_bytes())
    assert (errors == []) == (mutation == "same-source"), errors


def test_manifest_requires_explicit_mapping_omission(tmp_path):
    _, manifest, _ = candidate(tmp_path)
    assert metadata().parse_manifest(encode(manifest)) == manifest
    del manifest["units"][NS + "/second"]["qudt"]
    with pytest.raises(ValueError):
        metadata().parse_manifest(encode(manifest))


def test_valid_receipt_and_manifest_roundtrip(tmp_path):
    _, manifest, receipt = candidate(tmp_path)
    assert metadata().parse_manifest(encode(manifest)) == manifest
    assert metadata().parse_receipt(encode(receipt)) == receipt


@pytest.mark.parametrize("mutation", ["revision", "held_ref", "locator", "digest", "documents", "extra"])
def test_external_pin_shape(tmp_path, mutation):
    root, _, _ = candidate(tmp_path)
    inv = _inventory(root)
    source_pin = inv["lineages"][NS]["revisions"][0]["source_pin"]
    document = source_pin["documents"][0]
    if mutation == "revision":
        document["revision"] = ""
    if mutation == "held_ref":
        document["held_ref"] = "sha256:" + "0" * 64
    if mutation == "locator":
        document["locator"] = "https://secret:password@example.invalid/resource"
    if mutation == "digest":
        document["sha256"] = "A" * 64
    if mutation == "documents":
        source_pin["documents"] = []
    if mutation == "extra":
        document["path"] = "/private"
    assert _load_checker().inspect_candidate(root, encode(inv))


def test_actual_external_predecessor_relocation_and_new_coverage(tmp_path):
    import shutil

    import yaml
    from test_shipped_contract_checks import _row

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.contract.shipped import load_domain_history
    from beliefs.profile import shipped_base_contract
    from beliefs.register import AssumptionsRegister, register_identity, register_projection

    root, _, receipt = candidate(tmp_path)
    checker = _load_checker()
    install(checker, root, receipt)
    first_pins = dict(checker.RECEIPT_SHA256)
    old = load_domain_history(
        NS, base=shipped_base_contract(), read_text=lambda p: (root / "domains" / NS / p).read_text()
    )[-1]
    doc = yaml.safe_load((root / "domains" / NS / "DOMAIN.yaml").read_text())
    doc.update(version=2, lineage={"successor": old.contract.content_identity})
    new = parse_domain_contract(doc, source="synthetic", base=shipped_base_contract(), predecessor=old.contract)
    reg = AssumptionsRegister(
        describes=f"{NS}:{new.content_identity}", previous=register_identity(old.register), entries=old.register.entries
    )
    inv = _inventory(root)
    row = inv["lineages"][NS]["revisions"][0]
    for prefix in (f"domains/{NS}", f"python/src/beliefs/domains/{NS}"):
        directory = root / prefix
        history = directory / "history" / old.contract.content_identity
        history.mkdir(parents=True)
        for name in ("DOMAIN.yaml", "REGISTER.json"):
            shutil.copyfile(directory / name, history / name)
        (directory / "DOMAIN.yaml").write_text(yaml.safe_dump(doc))
        (directory / "REGISTER.json").write_bytes(encode(register_projection(reg)))
    for key, name in (("contract_path", "DOMAIN.yaml"), ("register_path", "REGISTER.json")):
        row[key] = f"domains/{NS}/history/{old.contract.content_identity}/{name}"
    added = _row(root, f"domains/{NS}/DOMAIN.yaml", f"domains/{NS}/REGISTER.json", new, reg)
    added["source_pin"] = copy.deepcopy(row["source_pin"])
    inv["lineages"][NS]["revisions"].append(added)
    _save_inventory(root, inv)
    _repin(checker, root)
    assert any("missing receipt" in e for e in checker.check(root))
    second = copy.deepcopy(receipt)
    second["candidate"] = {
        "sha256": digest((root / INVENTORY).read_bytes()),
        "inventory_utf8": (root / INVENTORY).read_text(),
    }
    second["coverage"]["row"] = added
    install(checker, root, second)
    checker.RECEIPT_SHA256.update(first_pins)
    assert checker.check(root) == []
    row["source_pin"]["documents"][0]["revision"] = "altered"
    _save_inventory(root, inv)
    _repin(checker, root)
    assert any("historical row changed" in e for e in checker.check(root))


def test_root_checker_has_no_evidence_imports(tmp_path):
    import subprocess
    import sys

    from conftest import REPO_ROOT

    script = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
class RefuseEvidence:
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {'refs', 'rdflib'}:
            raise AssertionError('evidence imported: ' + fullname)
sys.meta_path.insert(0, RefuseEvidence())
import check_shipped_contracts
assert check_shipped_contracts.check(Path(sys.argv[2])) == []
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(REPO_ROOT / "python/tools"), str(REPO_ROOT)],
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_synthetic_baseline_survives_an_admitted_invoking_tree(tmp_path, monkeypatch):
    import admission_fixtures
    import test_shipped_contract_checks

    root, _, receipt = candidate(tmp_path / "already-admitted")
    checker = _load_checker()
    install(checker, root, receipt)
    monkeypatch.setattr(admission_fixtures, "REPO_ROOT", root)
    monkeypatch.setattr(test_shipped_contract_checks, "REPO_ROOT", root)
    fresh, _, fresh_receipt = candidate(tmp_path / "fresh")
    install(checker, fresh, fresh_receipt)
    assert checker.check(fresh) == []
    assert NS not in metadata().decode(fresh_receipt["baseline"]["inventory_utf8"].encode())["lineages"]
