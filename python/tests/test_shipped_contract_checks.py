"""Distribution and hygiene checks for shipped contracts, registers and reproduction sources."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from conftest import REPO_ROOT

from beliefs.contract.domain import load_domain_contract
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.register import (
    AssumptionsRegister,
    RegisterEntry,
    register_entry_keys,
    register_from_projection,
    register_identity,
    register_projection,
)

_TOOL_PATH = Path(__file__).resolve().parents[1] / "tools" / "check_shipped_contracts.py"


def _load_checker():
    assert _TOOL_PATH.is_file(), f"missing {_TOOL_PATH}"
    spec = importlib.util.spec_from_file_location("check_shipped_contracts", _TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _copy_fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for rel in (
        "contracts",
        "domains",
        "python/src/beliefs/contracts",
        "python/src/beliefs/domains",
        "python/tools/reproduction",
    ):
        shutil.copytree(REPO_ROOT / rel, root / rel)
    return root


def _write_shipped_pack(root: Path, namespace: str, yaml_text: str) -> None:
    base = shipped_base_contract()
    domain_path = root / "domains" / namespace / "DOMAIN.yaml"
    pkg_domain_path = root / "python/src/beliefs/domains" / namespace / "DOMAIN.yaml"
    domain_path.parent.mkdir(parents=True, exist_ok=True)
    pkg_domain_path.parent.mkdir(parents=True, exist_ok=True)
    domain_path.write_text(yaml_text, encoding="utf-8")
    pkg_domain_path.write_text(yaml_text, encoding="utf-8")

    contract = load_domain_contract(domain_path, base=base, predecessor=None)
    entry = RegisterEntry("collapses", "licenses", "not established", status="provisional")
    reg = AssumptionsRegister(
        describes=f"{namespace}:{contract.content_identity}",
        previous=None,
        entries={key: entry for key in sorted(register_entry_keys(contract))},
    )
    reg_bytes = (json.dumps(register_projection(reg), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (root / "domains" / namespace / "REGISTER.json").write_bytes(reg_bytes)
    (root / "python/src/beliefs/domains" / namespace / "REGISTER.json").write_bytes(reg_bytes)


def test_real_repository_passes_with_current_phf19_and_no_heritage_sources(tmp_path: Path) -> None:
    checker = _load_checker()
    reproduction = REPO_ROOT / "python/tools/reproduction"
    for name in ("mm30.yaml", "mm30-cut22.yaml", "mm30-cut31.yaml", "mm30-reproduction.yaml", "mm30-modal-sorted.yaml"):
        assert not (reproduction / name).exists()
    assert (reproduction / "mm30-phf19.yaml").is_file()
    assert (reproduction / "mm30-phf19-register.json").is_file()
    assert checker.check(REPO_ROOT) == []
    assert checker.main([str(REPO_ROOT)]) == 0

    # Exercise CLI entrypoint in an isolated subprocess with an explicit allowlisted env.
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path),
    }
    completed = subprocess.run(
        [sys.executable, str(_TOOL_PATH), str(REPO_ROOT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_plain_workflow_yaml_passes_unchanged(tmp_path: Path) -> None:
    checker = _load_checker()
    root = _copy_fixture_root(tmp_path)
    # Plain workflow YAML without top-level `contract` may even hold floats/arbitrary keys.
    (root / "python/tools/reproduction/workflow-extra.yaml").write_text(
        "threshold: 0.05\nsteps:\n  - preflight\n", encoding="utf-8"
    )
    assert checker.check(root) == []


@pytest.mark.parametrize(
    ("content", "diagnostic"),
    [
        ("also: [biology]\ncontract:\n  contract: mm30\n  version: 1\n", "unknown field(s) also"),
        ("contract: [\n", "invalid YAML"),
    ],
)
def test_old_contract_location_is_parsed_and_invalid_sources_refuse(tmp_path: Path, content: str, diagnostic: str):
    checker = _load_checker()
    root = _copy_fixture_root(tmp_path)
    target = root / "python/tools/reproduction/mm30.yaml"
    target.write_text(content)
    errors = checker.check(root)
    assert len(errors) == 1
    assert "mm30.yaml" in errors[0] and diagnostic in errors[0]
    assert checker.main([str(root)]) == 1


def test_current_replacement_at_formerly_excluded_path_requires_admission(tmp_path: Path) -> None:
    checker = _load_checker()
    root = _copy_fixture_root(tmp_path)
    text = "contract: consumer\nversion: 1\nlineage: genesis\nsorts: {}\ndimensions: {}\ndefining_source: {id: urn:test:consumer}\n"
    target = root / "python/tools/reproduction/mm30.yaml"
    target.write_text(text)
    errors = checker.check(root)
    assert errors == [
        "python/tools/reproduction/mm30.yaml: unlisted reproduction contract; missing inventory register mapping"
    ]
    _admit(root, "consumer", target.relative_to(root).as_posix(), "python/tools/reproduction/consumer-register.json")
    _repin(checker, root)
    assert checker.check(root) == []
    target.write_text(text + "designs: {local-design: {definition: A design.}}\n")
    assert any("mm30.yaml" in error for error in checker.check(root))


@pytest.mark.parametrize(
    ("snippet", "expected_kind"),
    [
        ("quantity_kinds:\n  q:\n    dimension: dimensionless\n", "quantity-kind"),
        ("units:\n  u:\n    symbol: u\n    quantity_kind: general/relative-abundance\n", "unit"),
        ("constants:\n  c:\n    value: '2'\n    unit: general/u\n    exact: true\n", "constant"),
        (
            (
                "conversions:\n  conv:\n    kind: multiplicative\n    from: general/u1\n    to: general/u2\n"
                "    factor: '10'\n    exact: true\n"
            ),
            "conversion",
        ),
        (
            "transformations:\n  tx:\n    kind: identity\n    domain: real\n    invertible: true\n",
            "transformation",
        ),
        ("duration_conventions:\n  dc:\n    conversion: general/conv\n", "duration-convention"),
        ("identification_classes:\n  ic:\n    licenses_layers: [statistical]\n", "identification-class"),
        ("designs:\n  d:\n    definition: A design.\n", "design"),
        ("selection_mechanisms:\n  sm:\n    definition: A selection.\n", "selection-mechanism"),
        ("aggregation_rules:\n  ar:\n    definition: An aggregation.\n", "aggregation-rule"),
        (
            "assumption_kinds:\n  ak:\n    collapses: c\n    particulars: [dimensions]\n",
            "assumption-kind",
        ),
        (
            (
                "functionals:\n  fn:\n    form: quantity\n    arity: one\n"
                "    response_transformation: by-parameters\n    reversal: not-applicable\n"
                "    response_reversal: not-applicable\n    exchange: not-applicable\n    ties: not-applicable\n"
                "    output: declared\n    domain: not-applicable\n    'null': none\n    increment: not-applicable\n"
                "    uncertainty: exact\n    parameters:\n      mu: {typing: response-level, domain: real}\n"
            ),
            "functional",
        ),
        ("procedure_kinds:\n  pk:\n    fills_within_model: false\n", "procedure-kind"),
    ],
)
def test_each_former_placement_family_requires_ownership(tmp_path: Path, snippet: str, expected_kind: str) -> None:
    checker = _load_checker()
    root = _copy_fixture_root(tmp_path)
    text = f"contract: candidate\nversion: 1\nlineage: genesis\nsorts: {{}}\ndimensions: {{}}\ndefining_source: {{id: urn:test:candidate}}\n{snippet}"
    _write_shipped_pack(root, "candidate", text)
    _admit(root, "candidate")
    _repin(checker, root)
    assert checker.check(root) == []
    inv = _inventory(root)
    inv["lineages"]["candidate"]["source_id"] = inv["lineages"]["biology"]["source_id"]
    _save_inventory(root, inv)
    _repin(checker, root)
    errors = checker.check(root)
    assert any("owner" in e and "candidate" in e for e in errors), (expected_kind, errors)


def test_register_and_package_copy_defects_fail(tmp_path: Path) -> None:
    checker = _load_checker()

    # Divergent DOMAIN.yaml copy fails.
    root_div_domain = _copy_fixture_root(tmp_path / "div-domain")
    pkg_domain = root_div_domain / "python/src/beliefs/domains/general/DOMAIN.yaml"
    pkg_domain.write_text(pkg_domain.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert any("DOMAIN.yaml" in err for err in checker.check(root_div_domain))

    # Divergent REGISTER.json copy fails.
    root_div_reg = _copy_fixture_root(tmp_path / "div-reg")
    pkg_reg = root_div_reg / "python/src/beliefs/domains/general/REGISTER.json"
    pkg_reg.write_text(pkg_reg.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert any("REGISTER.json" in err for err in checker.check(root_div_reg))

    base_reg = json.loads((REPO_ROOT / "domains/general/REGISTER.json").read_text(encoding="utf-8"))

    def _mutate_register(name: str, mutated: dict[str, object]) -> list[str]:
        sub = _copy_fixture_root(tmp_path / name)
        encoded = (json.dumps(mutated, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        (sub / "domains/general/REGISTER.json").write_bytes(encoded)
        (sub / "python/src/beliefs/domains/general/REGISTER.json").write_bytes(encoded)
        return checker.check(sub)

    # Missing status fails.
    no_status_entries = {k: dict(v) for k, v in base_reg["entries"].items()}
    del no_status_entries["design:general/independent-groups"]["status"]
    assert _mutate_register("missing-status", {**base_reg, "entries": no_status_entries}) != []

    # Stale describes fails.
    assert _mutate_register("stale-describes", {**base_reg, "describes": f"general:{'f' * 64}"}) != []

    # Missing row fails.
    missing_row = dict(base_reg["entries"])
    missing_row.pop("procedure-kind:general/assay")
    assert _mutate_register("missing-row", {**base_reg, "entries": missing_row}) != []

    # Extra row fails.
    extra_row = {
        **base_reg["entries"],
        "design:general/unshipped-extra": {
            "collapses": "c",
            "licenses": "l",
            "not_established": "n",
            "status": "provisional",
        },
    }
    assert _mutate_register("extra-row", {**base_reg, "entries": extra_row}) != []

    # `previous: null` fails.
    assert _mutate_register("null-previous", {**base_reg, "previous": None}) != []


def test_generic_testing_fixture_contract_still_compiles() -> None:
    base = shipped_base_contract()
    testing = load_domain_contract(REPO_ROOT / "fixtures/contracts/testing.yaml", base=base, predecessor=None)
    compiled = compile_profile(base, [testing])
    assert "testing" in compiled.activated_contracts


def test_shadow_general_duplicate_register_keys_and_reference_doc_base_version(tmp_path: Path) -> None:
    checker = _load_checker()

    # Shadow `contract: general` under `python/tools/reproduction/` fails placement validation.
    shadow_root = _copy_fixture_root(tmp_path / "shadow-general")
    shadow_yaml = shadow_root / "python/tools/reproduction/shadow_general.yaml"
    shadow_yaml.write_text(
        "contract: general\n"
        "version: 1\n"
        "lineage: genesis\n"
        "sorts: {}\n"
        "dimensions: {}\n"
        "designs:\n"
        "  shadow-design: { definition: Shadow design outside domains/general. }\n",
        encoding="utf-8",
    )
    shadow_errors = checker.check(shadow_root)
    assert any(
        "python/tools/reproduction/shadow_general.yaml" in err and "domains/general/DOMAIN.yaml" in err
        for err in shadow_errors
    ), shadow_errors

    # Duplicate JSON keys in REGISTER.json fail even when post-deduplication keys match coverage.
    dup_root = _copy_fixture_root(tmp_path / "dup-reg-keys")
    orig_reg_text = (REPO_ROOT / "domains/general/REGISTER.json").read_text(encoding="utf-8")
    target_snippet = '"design:general/independent-groups": {'
    assert target_snippet in orig_reg_text
    dup_entry = (
        '"design:general/independent-groups": {\n'
        '      "collapses": "shadow",\n'
        '      "licenses": "shadow",\n'
        '      "not_established": "shadow",\n'
        '      "status": "provisional"\n'
        "    },\n    " + target_snippet
    )
    dup_text = orig_reg_text.replace(target_snippet, dup_entry, 1)
    (dup_root / "domains/general/REGISTER.json").write_text(dup_text, encoding="utf-8")
    (dup_root / "python/src/beliefs/domains/general/REGISTER.json").write_text(dup_text, encoding="utf-8")
    dup_errors = checker.check(dup_root)
    assert any("REGISTER.json" in err and "duplicate" in err.lower() for err in dup_errors), dup_errors

    # Reference documents name the actual shipped base, rather than a historical pin.
    from beliefs.profile import shipped_base_contract

    version = shipped_base_contract().version
    records_md = (REPO_ROOT / "docs/records.md").read_text(encoding="utf-8")
    contracts_md = (REPO_ROOT / "docs/contracts.md").read_text(encoding="utf-8")
    assert f"The shipped base contract is version {version}," in records_md
    assert "The shipped base contract is version 2," not in records_md
    assert f"cannot parse under\nbase v{version}." in contracts_md


def _inventory(root):
    return json.loads((root / "contracts/source-ownership/INVENTORY.json").read_text())


def _save_inventory(root, inventory):
    (root / "contracts/source-ownership/INVENTORY.json").write_text(json.dumps(inventory, indent=2) + "\n")


def _repin(checker, root):
    checker.SOURCE_INVENTORY_SHA256 = hashlib.sha256(
        (root / "contracts/source-ownership/INVENTORY.json").read_bytes()
    ).hexdigest()


def _admit(root, namespace, contract_path=None, register_path=None):
    cp = contract_path or f"domains/{namespace}/DOMAIN.yaml"
    rp = register_path or f"domains/{namespace}/REGISTER.json"
    c = load_domain_contract(root / cp, base=shipped_base_contract(), predecessor=None)
    if not (root / rp).exists():
        entry = RegisterEntry("c", "l", "n", status="provisional")
        reg = AssumptionsRegister(
            describes=f"{namespace}:{c.content_identity}",
            previous=None,
            entries={k: entry for k in register_entry_keys(c)},
        )
        (root / rp).write_text(json.dumps(register_projection(reg)))
    reg = register_from_projection(json.loads((root / rp).read_text()), source=rp)
    assert c.defining_source is not None
    sid = c.defining_source.id
    inv = _inventory(root)
    inv["sources"][sid] = {"aliases": [], "owner": {"namespace": namespace, "genesis": c.content_identity}}
    inv["lineages"][namespace] = {
        "genesis": c.content_identity,
        "source_id": sid,
        "revisions": [_row(root, cp, rp, c, reg)],
    }
    _save_inventory(root, inv)


def _row(root, cp, rp, c, reg):
    return {
        "contract_path": cp,
        "register_path": rp,
        "contract_identity": c.content_identity,
        "register_identity": register_identity(reg),
        "contract_sha256": hashlib.sha256((root / cp).read_bytes()).hexdigest(),
        "register_sha256": hashlib.sha256((root / rp).read_bytes()).hexdigest(),
        "source_pin": {"kind": "authored_pair"},
    }


def _successor(root):
    from beliefs.contract.shipped import load_domain_history

    base = shipped_base_contract()
    old = load_domain_history(
        "general", base=base, read_text=lambda p, root=root: (root / "domains/general" / p).read_text()
    )[-1]
    doc = yaml.safe_load((root / "domains/general/DOMAIN.yaml").read_text())
    doc.update(
        version=doc["version"] + 1,
        lineage={"successor": old.contract.content_identity},
        defining_source={"id": "urn:beliefs:definitions:shared-scientific-commitments"},
    )
    from beliefs.contract.domain import parse_domain_contract

    c = parse_domain_contract(doc, source="successor", base=base, predecessor=old.contract)
    reg = AssumptionsRegister(
        describes=f"general:{c.content_identity}",
        previous=register_identity(old.register),
        entries=old.register.entries,
    )
    inv = _inventory(root)
    row = inv["lineages"]["general"]["revisions"][-1]
    for prefix in ("domains/general", "python/src/beliefs/domains/general"):
        history = root / prefix / "history" / old.contract.content_identity
        history.mkdir(parents=True)
        for name in ("DOMAIN.yaml", "REGISTER.json"):
            shutil.copyfile(root / prefix / name, history / name)
        (root / prefix / "DOMAIN.yaml").write_text(yaml.safe_dump(doc))
        (root / prefix / "REGISTER.json").write_text(json.dumps(register_projection(reg)))
    for key, name in (("contract_path", "DOMAIN.yaml"), ("register_path", "REGISTER.json")):
        row[key] = f"domains/general/history/{old.contract.content_identity}/{name}"
    inv["lineages"]["general"]["revisions"].append(
        _row(root, "domains/general/DOMAIN.yaml", "domains/general/REGISTER.json", c, reg)
    )
    _save_inventory(root, inv)
    return old.contract.content_identity


def test_successor_moves_adopted_bytes_into_history(tmp_path):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    old = _successor(root)
    _repin(checker, root)
    assert checker.check(root) == []
    inv = _inventory(root)
    inv["lineages"]["general"]["revisions"].reverse()
    _save_inventory(root, inv)
    _repin(checker, root)
    assert any("order" in e for e in checker.check(root))
    inv["lineages"]["general"]["revisions"].reverse()
    _save_inventory(root, inv)
    _repin(checker, root)
    ancestor = f"history/{old}/DOMAIN.yaml"
    path = root / "python/src/beliefs/domains/general" / ancestor
    path.write_text(path.read_text() + "\n")
    assert any(ancestor in e and "differs" in e for e in checker.check(root))
    path.unlink()
    assert any(ancestor in e and "missing" in e for e in checker.check(root))


@pytest.mark.parametrize(
    "extra", ["history/invalid", "history/" + "0" * 64, ".hidden", "history/" + "a" * 64 + "/extra"]
)
def test_orphan_and_malformed_archive_entries_refuse(tmp_path, extra):
    root = _copy_fixture_root(tmp_path)
    (root / "domains/general" / extra).mkdir(parents=True)
    assert _load_checker().check(root)


def test_bad_ancestor_refuses_even_when_current_copies_are_valid(tmp_path):
    root = _copy_fixture_root(tmp_path)
    path = next((root / "domains/general/history").glob("*/REGISTER.json"))
    path.write_text("{}")
    assert any(path.relative_to(root).as_posix() in e for e in _load_checker().check(root))


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "pin",
        "duplicate",
        "constant",
        "version",
        "extra",
        "alias",
        "owner",
        "empty",
        "digest",
        "duplicate-row",
        "path",
        "external",
        "external-malformed",
        "lineage-source",
        "source-extra",
        "row-extra",
        "owner-extra",
        "alias-collision",
    ],
)
def test_inventory_shape_and_paths_refuse(tmp_path, mutation):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    inv = _inventory(root)
    path = root / "contracts/source-ownership/INVENTORY.json"
    source = next(iter(inv["sources"]))
    lineage = inv["lineages"]["biology"]
    row = lineage["revisions"][0]
    if mutation == "missing":
        path.unlink()
    elif mutation == "pin":
        path.write_text(path.read_text() + " ")
    elif mutation == "duplicate":
        path.write_text('{"version":1,"version":1,"sources":{},"lineages":{}}')
        _repin(checker, root)
    elif mutation == "constant":
        path.write_text('{"version":NaN,"sources":{},"lineages":{}}')
        _repin(checker, root)
    else:
        if mutation == "version":
            inv["version"] = True
        elif mutation == "extra":
            inv["extra"] = 1
        elif mutation == "alias":
            inv["sources"][source]["aliases"] = ["URN:bad"]
        elif mutation == "owner":
            inv["sources"][source]["owner"]["genesis"] = "a" * 64
        elif mutation == "empty":
            lineage["revisions"] = []
        elif mutation == "digest":
            row["contract_identity"] = "X" * 64
        elif mutation == "duplicate-row":
            lineage["revisions"].append(copy.deepcopy(row))
        elif mutation == "path":
            row["contract_path"] = "../outside.yaml"
        elif mutation == "external":
            row["source_pin"] = {
                "kind": "external",
                "documents": [
                    {"revision": "1", "sha256": "a" * 64, "held_ref": "held:1", "locator": "https://example.org"}
                ],
            }
        elif mutation == "external-malformed":
            row["source_pin"] = {"kind": "external", "documents": None}
        elif mutation == "lineage-source":
            lineage["source_id"] = "urn:unknown:source"
        elif mutation == "source-extra":
            inv["sources"][source]["extra"] = 1
        elif mutation == "row-extra":
            row["extra"] = 1
        elif mutation == "owner-extra":
            inv["sources"][source]["owner"]["extra"] = 1
        elif mutation == "alias-collision":
            inv["sources"][source]["aliases"] = [next(reversed(inv["sources"]))]
        _save_inventory(root, inv)
        _repin(checker, root)
    errors = checker.check(root)
    assert errors, mutation
    if mutation.startswith("external"):
        assert any("external" in e for e in errors)


@pytest.mark.parametrize(
    "target",
    [
        "domains",
        "domains/biology/DOMAIN.yaml",
        "python/src/beliefs/domains",
        "contracts/source-ownership/INVENTORY.json",
        "python/tools/reproduction",
    ],
)
def test_symlink_members_refuse_and_symlink_root_passes(tmp_path, target):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    link = tmp_path / "root-link"
    link.symlink_to(root, target_is_directory=True)
    assert checker.check(link) == []
    path = root / target
    outside = tmp_path / "outside"
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=outside.is_dir())
    assert any("symlink" in e for e in checker.check(root))


@pytest.mark.parametrize("target", ["contract", "register"])
def test_adoption_is_not_extended_by_repinning_inventory(tmp_path, target):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    inv = _inventory(root)
    row = inv["lineages"]["mm30"]["revisions"][0]
    path = root / row[target + "_path"]
    path.write_bytes(path.read_bytes() + b"\n")
    row[target + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    _save_inventory(root, inv)
    _repin(checker, root)
    assert any("adopt" in e for e in checker.check(root))


@pytest.mark.parametrize(
    "source", [None, "urn:unknown:source", "urn:biology:alias", "urn:beliefs:definitions:human-annotation-admissions"]
)
def test_one_owner_across_disjoint_profiles(tmp_path, source):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    text = "contract: candidate\nversion: 1\nlineage: genesis\nsorts: {}\ndimensions: {}\n"
    if source:
        text += f"defining_source: {{id: {source}}}\n"
    _write_shipped_pack(root, "candidate", text)
    if source:
        _admit(root, "candidate")
        inv = _inventory(root)
        if source == "urn:biology:alias":
            inv["sources"]["urn:beliefs:definitions:human-annotation-admissions"]["aliases"] = [source]
        elif source == "urn:unknown:source":
            del inv["sources"][source]
        _save_inventory(root, inv)
    _repin(checker, root)
    assert checker.check(root)


def test_complete_discovery_and_pair_coverage(tmp_path):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    shutil.copyfile(
        root / "python/tools/reproduction/mm30-phf19.yaml", root / "python/tools/reproduction/unlisted.yaml"
    )
    assert any("unlisted.yaml" in e for e in checker.check(root))
    for change in ("describes", "entries", "previous"):
        sub = _copy_fixture_root(tmp_path / change)
        p = sub / "python/tools/reproduction/mm30-phf19-register.json"
        reg = json.loads(p.read_text())
        if change == "describes":
            reg[change] = "mm30:" + "f" * 64
        elif change == "entries":
            reg[change] = {}
        else:
            reg[change] = "assumptions-register:" + "f" * 64
        p.write_text(json.dumps(reg))
        assert any("register" in e.lower() for e in checker.check(sub))


def test_reservation_pin_and_its_review_boundary(tmp_path):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    inv = _inventory(root)
    sid = inv["lineages"]["biology"]["source_id"]
    inv["sources"][sid]["aliases"] = ["urn:test:old-alias"]
    _save_inventory(root, inv)
    _repin(checker, root)
    assert checker.check(root) == []
    inv["sources"][sid]["aliases"] = []
    _save_inventory(root, inv)
    assert checker.check(root)
    _repin(checker, root)
    assert checker.check(root) == []  # Continuity across coordinated pin edits requires review.


@pytest.mark.parametrize(
    "path",
    [
        "/absolute",
        "C:/drive",
        "domains//biology/DOMAIN.yaml",
        "domains/./biology/DOMAIN.yaml",
        "domains/../biology/DOMAIN.yaml",
        "domains/biology/*.yaml",
        "domains\\biology\\DOMAIN.yaml",
    ],
)
def test_unsafe_inventory_paths_refuse(tmp_path, path):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    inv = _inventory(root)
    inv["lineages"]["biology"]["revisions"][0]["contract_path"] = path
    _save_inventory(root, inv)
    _repin(checker, root)
    assert checker.check(root)


@pytest.mark.parametrize("level", ["sources", "owner", "lineage", "row", "pin"])
def test_duplicate_json_keys_at_every_depth_refuse(tmp_path, level):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    p = root / "contracts/source-ownership/INVENTORY.json"
    text = p.read_text()
    key = {"sources": "aliases", "owner": "namespace", "lineage": "source_id", "row": "contract_path", "pin": "kind"}[
        level
    ]
    import re

    match = re.search(r'"' + key + r'": (\[\]|"[^"]*")', text)
    assert match
    text = text[: match.start()] + match.group(0) + ", " + match.group(0) + text[match.end() :]
    p.write_text(text)
    _repin(checker, root)
    assert any("duplicate JSON key" in e for e in checker.check(root))


def test_missing_field_is_refused_after_new_lineage_or_successor_repin(tmp_path):
    checker = _load_checker()
    for mode in ("lineage", "successor"):
        root = _copy_fixture_root(tmp_path / mode)
        if mode == "lineage":
            _write_shipped_pack(
                root, "candidate", "contract: candidate\nversion: 1\nlineage: genesis\nsorts: {}\ndimensions: {}\n"
            )
            # Build valid source evidence while keeping the contract metadata-free.
            inv = _inventory(root)
            cp = "domains/candidate/DOMAIN.yaml"
            rp = "domains/candidate/REGISTER.json"
            c = load_domain_contract(root / cp, base=shipped_base_contract(), predecessor=None)
            reg = register_from_projection(json.loads((root / rp).read_text()), source=rp)
            inv["sources"]["urn:test:candidate"] = {
                "aliases": [],
                "owner": {"namespace": "candidate", "genesis": c.content_identity},
            }
            inv["lineages"]["candidate"] = {
                "genesis": c.content_identity,
                "source_id": "urn:test:candidate",
                "revisions": [_row(root, cp, rp, c, reg)],
            }
            _save_inventory(root, inv)
        else:
            old = _successor(root)
            # A metadata-free adopted predecessor permits addition locally, but not omission in admission.
            from beliefs.contract.domain import parse_domain_contract
            from beliefs.contract.shipped import load_domain_history

            cp = "domains/general/DOMAIN.yaml"
            rp = "domains/general/REGISTER.json"
            doc = yaml.safe_load((root / cp).read_text())
            del doc["defining_source"]
            predecessor = load_domain_history(
                "general",
                base=shipped_base_contract(),
                read_text=lambda p, root=root: (root / "domains/general" / p).read_text(),
            )[-2].contract
            assert predecessor.content_identity == old
            c = parse_domain_contract(doc, source=cp, base=shipped_base_contract(), predecessor=predecessor)
            reg = register_from_projection(json.loads((root / rp).read_text()), source=rp)
            reg = AssumptionsRegister(
                describes=f"general:{c.content_identity}", previous=reg.previous, entries=reg.entries
            )
            for prefix in ("domains/general", "python/src/beliefs/domains/general"):
                (root / prefix / "DOMAIN.yaml").write_text(yaml.safe_dump(doc))
                (root / prefix / "REGISTER.json").write_text(json.dumps(register_projection(reg)))
            inv = _inventory(root)
            inv["lineages"]["general"]["revisions"][-1] = _row(root, cp, rp, c, reg)
            _save_inventory(root, inv)
        _repin(checker, root)
        assert any("missing defining_source" in e for e in checker.check(root))


@pytest.mark.parametrize(
    "defect", ["missing-ancestor", "orphan-fork", "wrong-previous", "stale-describes", "fresh-genesis"]
)
def test_successor_chain_defects_refuse(tmp_path, defect):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    old = _successor(root)
    if defect == "missing-ancestor":
        (root / f"domains/general/history/{old}/DOMAIN.yaml").unlink()
    elif defect == "orphan-fork":
        shutil.copytree(root / f"domains/general/history/{old}", root / "domains/general/history" / ("f" * 64))
    elif defect == "fresh-genesis":
        for prefix in ("domains/general", "python/src/beliefs/domains/general"):
            p = root / prefix / "DOMAIN.yaml"
            doc = yaml.safe_load(p.read_text())
            doc["lineage"] = "genesis"
            p.write_text(yaml.safe_dump(doc))
    else:
        for prefix in ("domains/general", "python/src/beliefs/domains/general"):
            p = root / prefix / "REGISTER.json"
            doc = json.loads(p.read_text())
            doc["previous" if defect == "wrong-previous" else "describes"] = (
                "assumptions-register:" + "f" * 64 if defect == "wrong-previous" else "general:" + "f" * 64
            )
            p.write_text(json.dumps(doc))
    _repin(checker, root)
    assert checker.check(root)


@pytest.mark.parametrize("external", [{"other": "x"}, {"ucum": ""}, {"qudt": 1}])
def test_source_metadata_does_not_waive_unit_checks(external):
    from beliefs.contract.domain import parse_domain_contract
    from beliefs.errors import MalformedContract

    doc = {
        "contract": "candidate",
        "version": 1,
        "lineage": "genesis",
        "sorts": {},
        "dimensions": {},
        "defining_source": {"id": "urn:test:candidate"},
        "units": {"u": {"symbol": "u", "quantity_kind": "general/relative-abundance", "external": external}},
    }
    with pytest.raises(MalformedContract, match="external"):
        parse_domain_contract(doc, source="unit-source", base=shipped_base_contract(), predecessor=None)


def test_plan_base_adoption_is_exact():
    vector = json.loads((REPO_ROOT / "fixtures/defining-source.json").read_text())
    checker = _load_checker()
    inventory = _inventory(REPO_ROOT)
    for row in vector["production"]:
        current = next(
            r
            for r in inventory["lineages"][row["namespace"]]["revisions"]
            if r["contract_identity"] == row["contract_identity"]
        )
        reg = register_from_projection(
            json.loads((REPO_ROOT / current["register_path"]).read_text()), source=current["register_path"]
        )
        assert register_identity(reg) == row["register_identity"]
        assert all(e.status == "provisional" for e in reg.entries.values())
        for part in ("contract", "register"):
            assert (
                hashlib.sha256((REPO_ROOT / current[part + "_path"]).read_bytes()).hexdigest() == row[part + "_sha256"]
            )
        assert checker.ADOPTED_SOURCE_REVISIONS[(row["namespace"], row["contract_identity"])] == tuple(
            row[k] for k in ("register_identity", "contract_sha256", "register_sha256", "source_id")
        )
    assert len(checker.ADOPTED_SOURCE_REVISIONS) == 4
    assert checker.check(REPO_ROOT) == []


@pytest.mark.parametrize("symlink_parent", [False, True], ids=["leaf", "parent"])
def test_inventory_selected_register_refuses_symlinks_before_outside_read(tmp_path, monkeypatch, symlink_parent):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    inventory = _inventory(root)
    row = inventory["lineages"]["mm30"]["revisions"][0]
    outside = tmp_path / "outside-registers"
    outside.mkdir()
    target = outside / "mm30.json"
    target.write_bytes((root / row["register_path"]).read_bytes())
    if symlink_parent:
        (root / "linked-registers").symlink_to(outside, target_is_directory=True)
        row["register_path"] = "linked-registers/mm30.json"
    else:
        (root / "register-link.json").symlink_to(target)
        row["register_path"] = "register-link.json"
    _save_inventory(root, inventory)
    _repin(checker, root)
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        assert path.resolve() != target, "outside register was opened before containment refusal"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    errors = checker.check(root)
    assert any("symlink" in e and row["register_path"].split("/")[0] in e for e in errors), errors


_MM30 = "python/tools/reproduction"
_MM30_HISTORY = f"{_MM30}/mm30-phf19-history"


def _mm30_successors(root, checker, *, successors=1, template_layer=None):
    from fixtures.phf19_history import phf19_history

    history = root / _MM30_HISTORY
    if history.exists():
        shutil.rmtree(history)
    pairs = phf19_history(root / _MM30, successors=successors, template_layer=template_layer)
    inventory = _inventory(root)
    old, *new = pairs
    rows = inventory["lineages"]["mm30"]["revisions"]
    del rows[1:]
    rows[0].update(
        contract_path=old.contract_path.relative_to(root).as_posix(),
        register_path=old.register_path.relative_to(root).as_posix(),
    )
    for pair in new:
        cp = pair.contract_path.relative_to(root).as_posix()
        rp = pair.register_path.relative_to(root).as_posix()
        rows.append(_row(root, cp, rp, pair.contract, pair.register))
    _save_inventory(root, inventory)
    _repin(checker, root)
    return pairs


@pytest.mark.parametrize("successors", [1, 2])
def test_standalone_successors_admit_with_historical_pins_and_receipts(tmp_path, successors):
    from reproduction import vocabulary
    from source_admission.metadata import check_continuity

    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    _mm30_successors(root, checker, successors=0)
    baseline = _inventory(root)
    *_, head = _mm30_successors(root, checker, successors=successors)
    candidate = _inventory(root)
    check_continuity(baseline, candidate)
    assert checker.check(root) == []
    errors, revisions = checker._inspect(root, checker._validate_inventory(candidate))
    assert not errors
    mm30 = [r for r in revisions if r.contract.namespace == "mm30"]
    rows = candidate["lineages"]["mm30"]["revisions"]
    assert [r.contract_path for r in mm30] == [row["contract_path"] for row in rows]
    assert [r.register_path for r in mm30] == [row["register_path"] for row in rows]
    assert [r.current for r in mm30] == [False] * successors + [True]
    assert {r.genesis for r in mm30} == {baseline["lineages"]["mm30"]["genesis"]}
    selected = vocabulary.revision(head.contract_path)
    assert selected.contract.content_identity == mm30[-1].contract.content_identity
    assert register_identity(selected.register) == rows[-1]["register_identity"]
    assert selected.register.describes == vocabulary.pins(head.contract_path).domains["mm30"]


@pytest.mark.parametrize("kind", ["absent", "empty", "file"])
def test_mm30_reserved_history_root_at_genesis(tmp_path, kind):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    _mm30_successors(root, checker, successors=0)
    history = root / _MM30_HISTORY
    if kind == "empty":
        history.mkdir()
    elif kind == "file":
        history.write_text("not a directory")
    errors = checker.check(root)
    if kind == "absent":
        assert errors == []
    else:
        assert any(error.startswith(f"{_MM30_HISTORY}:") for error in errors)


@pytest.mark.parametrize("extra", ["orphan", "malformed", "empty", "stray", "symlink"])
def test_mm30_unexpected_archive_members_refuse(tmp_path, extra):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    old, _ = _mm30_successors(root, checker)
    history = root / _MM30_HISTORY
    if extra == "orphan":
        path = history / ("f" * 64)
        shutil.copytree(old.contract_path.parent, path)
    elif extra == "malformed":
        path = history / "misspelled"
        path.mkdir()
        (path / "DOMAIN.yaml").write_text("contract: [")
    elif extra == "empty":
        path = old.contract_path.parent / "empty"
        path.mkdir()
    elif extra == "stray":
        path = history / ".stray"
        path.write_text("extraneous")
    else:
        path = old.register_path
        target = tmp_path / "register.json"
        path.rename(target)
        path.symlink_to(target)
    errors = checker.check(root)
    assert any(path.relative_to(root).as_posix() in error for error in errors)
    if extra == "malformed":
        assert any("misspelled/DOMAIN.yaml: invalid YAML" in error for error in errors)
    if extra == "symlink":
        assert any("symlink admission member refused" in error for error in errors)


@pytest.mark.parametrize("defect", ["json", "duplicates", "describes", "coverage", "skipped", "absent"])
def test_mm30_broken_register_fails_closed_after_a_successful_check(tmp_path, defect):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    genesis, prior, head = _mm30_successors(root, checker, successors=2)
    assert checker.check(root) == []
    register = head.register_path
    payload = json.loads(register.read_bytes())
    if defect == "skipped":
        payload["previous"] = register_identity(genesis.register)
    elif defect == "describes":
        payload["describes"] = genesis.register.describes
    elif defect == "coverage":
        del payload["entries"]["sort:mm30/cohort"]
    elif defect == "absent":
        register = prior.register_path
        register.unlink()
    if defect == "json":
        register.write_text("{")
    elif defect == "duplicates":
        register.write_text('{"describes":"mm30:duplicate",' + json.dumps(payload)[1:])
    elif defect != "absent":
        register.write_text(json.dumps(payload))

    relative = register.relative_to(root).as_posix()
    errors = checker.check(root)
    assert any(error.startswith(f"{relative}:") for error in errors)
    assert not any("no predecessor was supplied" in error for error in errors)
    _, revisions = checker._inspect(root, checker._validate_inventory(_inventory(root)))
    assert not any(revision.contract.namespace == "mm30" for revision in revisions)


@pytest.mark.parametrize(
    ("defect", "diagnostic"),
    [
        ("cycle", "lineage cycle"),
        ("absent", "required regular file is missing"),
        ("directory-identity", "content identity differs from its history directory"),
        ("wrong-link", "required regular file is missing"),
        ("wrong-namespace", "namespace"),
        ("drop", "drops claim-vocabulary"),
        ("redefine", "different canonical schema projection"),
    ],
)
def test_mm30_broken_contract_chain_names_physical_member(tmp_path, defect, diagnostic):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    genesis, head = _mm30_successors(root, checker)
    target = head.contract_path
    if defect in {"cycle", "absent", "directory-identity"}:
        target = genesis.contract_path
    doc = yaml.safe_load(target.read_bytes())
    if defect == "cycle":
        doc["lineage"] = {"successor": genesis.contract.content_identity}
    elif defect == "directory-identity":
        doc["version"] += 1
    elif defect == "wrong-link":
        digest = "0" * 64
        doc["lineage"] = {"successor": digest}
    elif defect == "wrong-namespace":
        doc["contract"] = "other"
    elif defect == "drop":
        del doc["sorts"]["stage-level"]
    elif defect == "redefine":
        doc["sorts"]["stage-level"]["identifier_class"]["pattern"] = "level:[a-z]+"
    if defect == "absent":
        target.unlink()
    else:
        target.write_text(yaml.safe_dump(doc))
    if defect == "wrong-link":
        target = root / _MM30_HISTORY / digest / "DOMAIN.yaml"
    relative = target.relative_to(root).as_posix()
    assert any(error.startswith(f"{relative}:") and diagnostic in error for error in checker.check(root))


def test_mm30_cannot_resurrect_an_archived_tombstone(tmp_path):
    from dataclasses import replace

    from beliefs.contract.domain import parse_domain_contract

    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    genesis, prior, head = _mm30_successors(root, checker, successors=2)
    doc = yaml.safe_load(prior.contract_path.read_bytes())
    doc["sorts"]["stage-level"]["retired"] = True
    retired = parse_domain_contract(doc, source="fixture", base=shipped_base_contract(), predecessor=genesis.contract)
    prior.contract_path.write_text(yaml.safe_dump(doc))
    prior.register_path.write_text(
        json.dumps(register_projection(replace(prior.register, describes=f"mm30:{retired.content_identity}")))
    )
    prior.contract_path.parent.rename(root / _MM30_HISTORY / retired.content_identity)
    doc = yaml.safe_load(head.contract_path.read_bytes())
    doc["lineage"] = {"successor": retired.content_identity}
    head.contract_path.write_text(yaml.safe_dump(doc))
    errors = checker.check(root)
    assert any(f"{_MM30}/mm30-phf19.yaml" in error and "un-retires" in error for error in errors)


@pytest.mark.parametrize("source_id", [None, "urn:test:phf19-alias", "urn:test:wrong-source"])
def test_mm30_successor_requires_canonical_defining_source(tmp_path, source_id):
    from dataclasses import replace

    from beliefs.contract.domain import parse_domain_contract

    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    old, head = _mm30_successors(root, checker)
    inv = _inventory(root)
    lineage = inv["lineages"]["mm30"]
    inv["sources"][lineage["source_id"]]["aliases"].append("urn:test:phf19-alias")
    doc = yaml.safe_load(head.contract_path.read_bytes())
    if source_id is None:
        del doc["defining_source"]
    else:
        doc["defining_source"]["id"] = source_id
    cp = head.contract_path.relative_to(root).as_posix()
    rp = head.register_path.relative_to(root).as_posix()
    contract = parse_domain_contract(doc, source=cp, base=shipped_base_contract(), predecessor=old.contract)
    register = replace(head.register, describes=f"mm30:{contract.content_identity}")
    head.contract_path.write_text(yaml.safe_dump(doc))
    head.register_path.write_text(json.dumps(register_projection(register)))
    lineage["revisions"][-1] = _row(root, cp, rp, contract, register)
    _save_inventory(root, inv)
    _repin(checker, root)
    message = "missing defining_source" if source_id is None else "must use canonical"
    assert any(error.startswith(f"{cp}:") and message in error for error in checker.check(root))


@pytest.mark.parametrize("mutation", ["changed-contract", "changed-register", "fresh-genesis", "stale", "reversed"])
def test_mm30_history_cannot_be_rewritten_or_omitted_by_repinning(tmp_path, mutation):
    from dataclasses import replace

    from beliefs.contract.domain import parse_domain_contract

    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    old, head = _mm30_successors(root, checker)
    inv = _inventory(root)
    lineage = inv["lineages"]["mm30"]
    rows = lineage["revisions"]
    message = "order/coverage"
    if mutation.startswith("changed-"):
        target = mutation.removeprefix("changed-")
        path = root / rows[0][f"{target}_path"]
        path.write_bytes(path.read_bytes() + b"\n")
        rows[0][f"{target}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        message = "missing defining_source outside exact adopted source revisions"
    elif mutation == "fresh-genesis":
        doc = yaml.safe_load(head.contract_path.read_bytes())
        doc["lineage"] = "genesis"
        cp, rp = rows[-1]["contract_path"], rows[-1]["register_path"]
        contract = parse_domain_contract(doc, source=cp, base=shipped_base_contract(), predecessor=None)
        register = replace(head.register, describes=f"mm30:{contract.content_identity}", previous=None)
        head.contract_path.write_text(yaml.safe_dump(doc))
        head.register_path.write_text(json.dumps(register_projection(register)))
        shutil.rmtree(old.contract_path.parent.parent)
        lineage["genesis"] = contract.content_identity
        inv["sources"][lineage["source_id"]]["owner"]["genesis"] = contract.content_identity
        lineage["revisions"] = [_row(root, cp, rp, contract, register)]
        message = "required adopted revision missing"
    elif mutation == "stale":
        rows.pop()
    else:
        rows.reverse()
    _save_inventory(root, inv)
    _repin(checker, root)
    assert any(message in error for error in checker.check(root))


def test_mm30_checker_rejects_a_head_incompatible_with_the_candidate_base(tmp_path):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    _mm30_successors(root, checker, template_layer="methodological")
    relative = "contracts/science/CONTRACT.yaml"
    doc = yaml.safe_load((root / relative).read_bytes())
    doc["claim_grammar"]["layers"].remove("methodological")
    restricted = yaml.safe_dump(doc)
    (root / relative).write_text(restricted)
    (root / "python/src/beliefs" / relative).write_text(restricted)
    errors = checker.check(root)
    assert any(f"{_MM30}/mm30-phf19.yaml" in error and "methodological" in error for error in errors)


def test_nested_contract_outside_phf19_history_still_needs_admission(tmp_path):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    _mm30_successors(root, checker)
    relative = f"{_MM30}/bundle/nested/other.yml"
    path = root / relative
    path.parent.mkdir(parents=True)
    path.write_text("contract: other\nversion: 1\nlineage: genesis\nsorts: {}\ndimensions: {}\n")
    assert any(error.startswith(f"{relative}: unlisted reproduction contract") for error in checker.check(root))


def test_checker_import_needs_no_reproduction_state_or_checkout(tmp_path):
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path),
        "PYTHONPATH": str(_TOOL_PATH.parent),
    }
    script = """
import importlib.abc
import sys

class BlockState(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'reproduction.paths', 'reproduction.state', 'checkout'}:
            raise AssertionError(fullname)

sys.meta_path.insert(0, BlockState())
from check_shipped_contracts import main

raise SystemExit(main(sys.argv[1:]))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script, str(REPO_ROOT)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr


def test_synthetic_fixture_resets_a_copy_with_an_admitted_history(tmp_path):
    root = _copy_fixture_root(tmp_path)
    checker = _load_checker()
    adopted, _, advanced = _mm30_successors(root, checker, successors=2)
    assert checker.check(root) == []

    genesis, successor = _mm30_successors(root, checker)
    assert genesis.contract.content_identity == adopted.contract.content_identity
    assert successor.contract.content_identity != advanced.contract.content_identity
    assert checker.check(root) == []
