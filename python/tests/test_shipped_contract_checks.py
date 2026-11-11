"""Distribution and hygiene checks for shipped contracts, registers and reproduction sources."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT

from beliefs.contract.domain import load_domain_contract
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.register import AssumptionsRegister, RegisterEntry, register_entry_keys, register_projection

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
        "contracts/science/CONTRACT.yaml",
        "python/src/beliefs/contracts/science/CONTRACT.yaml",
        "domains/general/DOMAIN.yaml",
        "domains/general/REGISTER.json",
        "python/src/beliefs/domains/general/DOMAIN.yaml",
        "python/src/beliefs/domains/general/REGISTER.json",
        "python/tools/reproduction/analysis-inputs.yaml",
        "python/tools/reproduction/mm30.yaml",
        "python/tools/reproduction/mm30-reproduction.yaml",
        "python/tools/reproduction/mm30-cut22.yaml",
        "python/tools/reproduction/mm30-cut31.yaml",
        "python/tools/reproduction/mm30-modal-sorted.yaml",
    ):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, dst)
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


def test_real_repository_passes_with_zero_findings_and_empty_exceptions(tmp_path: Path) -> None:
    checker = _load_checker()
    assert dict(checker.REVIEWED_FIELD_SPECIFIC_EXCEPTIONS) == {}
    assert len(checker.HERITAGE_REPRODUCTION_EXCLUSIONS) == 5
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


def test_all_five_heritage_files_and_plain_workflow_yaml_pass_unchanged(tmp_path: Path) -> None:
    checker = _load_checker()
    root = _copy_fixture_root(tmp_path)
    # Plain workflow YAML without top-level `contract` may even hold floats/arbitrary keys.
    (root / "python/tools/reproduction/workflow-extra.yaml").write_text(
        "threshold: 0.05\nsteps:\n  - preflight\n", encoding="utf-8"
    )
    assert checker.check(root) == []


def test_unlisted_old_wrapper_changed_bytes_and_missing_heritage_file_fail(tmp_path: Path) -> None:
    checker = _load_checker()

    # Unlisted v1 contract wrapper under reproduction/ fails visibly.
    root_unlisted = _copy_fixture_root(tmp_path / "unlisted")
    shutil.copyfile(
        root_unlisted / "python/tools/reproduction/mm30.yaml",
        root_unlisted / "python/tools/reproduction/mm30-unlisted.yaml",
    )
    errors = checker.check(root_unlisted)
    assert any("python/tools/reproduction/mm30-unlisted.yaml" in err for err in errors)
    assert checker.main([str(root_unlisted)]) == 1

    # Listed heritage file with modified bytes fails naming its owner tasks.
    root_changed = _copy_fixture_root(tmp_path / "changed")
    target = root_changed / "python/tools/reproduction/mm30.yaml"
    target.write_text(target.read_text(encoding="utf-8") + "# edited\n", encoding="utf-8")
    errors = checker.check(root_changed)
    assert len(errors) == 1
    assert "python/tools/reproduction/mm30.yaml" in errors[0]
    assert "beliefs-709bd9" in errors[0] and "beliefs-dcce70" in errors[0]

    # Listed heritage file missing/renamed fails naming its owner tasks.
    root_missing = _copy_fixture_root(tmp_path / "missing")
    (root_missing / "python/tools/reproduction/mm30-cut22.yaml").rename(
        root_missing / "python/tools/reproduction/mm30-cut22-renamed.yaml"
    )
    errors = checker.check(root_missing)
    assert any("python/tools/reproduction/mm30-cut22.yaml" in err and "beliefs-dcce70" in err for err in errors)
    assert any("python/tools/reproduction/mm30-cut22-renamed.yaml" in err for err in errors)


def test_current_replacement_at_formerly_excluded_path_enters_full_validation(tmp_path: Path) -> None:
    checker = _load_checker()
    root = _copy_fixture_root(tmp_path)
    reduced_exclusions = {
        path: meta
        for path, meta in checker.HERITAGE_REPRODUCTION_EXCLUSIONS.items()
        if path != "python/tools/reproduction/mm30.yaml"
    }

    # Valid consumer replacement passes when exclusion is removed.
    valid_replacement = """contract: mm30
version: 1
lineage: genesis
sorts:
  gene:
    binding: {kind: release, namespace: hgnc, release: "2026-01"}
    identifier_class: {prefix: "HGNC:", pattern: "HGNC:[0-9]+"}
dimensions: {}
instantiations:
  gene-covaries:
    template: general/covaries-with
    roles:
      parties: [gene]
"""
    (root / "python/tools/reproduction/mm30.yaml").write_text(valid_replacement, encoding="utf-8")
    assert checker.check(root, exclusions=reduced_exclusions) == []

    # Invalid shared-table placement in replacement fails once exclusion is removed.
    bad_replacement = valid_replacement + "\ndesigns:\n  local-design:\n    definition: Not allowed outside general.\n"
    (root / "python/tools/reproduction/mm30.yaml").write_text(bad_replacement, encoding="utf-8")
    errors = checker.check(root, exclusions=reduced_exclusions)
    assert len(errors) == 1
    assert "python/tools/reproduction/mm30.yaml" in errors[0]
    assert "design" in errors[0] and "local-design" in errors[0]


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
def test_non_general_shared_tables_are_rejected_and_reviewed_exceptions_are_bounded(
    tmp_path: Path, snippet: str, expected_kind: str
) -> None:
    checker = _load_checker()
    root = _copy_fixture_root(tmp_path)
    yaml_text = f"contract: biology\nversion: 1\nlineage: genesis\nsorts: {{}}\ndimensions: {{}}\n{snippet}"
    _write_shipped_pack(root, "biology", yaml_text)

    errors = checker.check(root)
    assert len(errors) == 1
    assert "domains/biology/DOMAIN.yaml" in errors[0]
    assert expected_kind in errors[0]

    # Only `functional` and `procedure-kind` may be granted a reviewed source-path/kind/name exception.
    decl_name = snippet.splitlines()[1].strip().rstrip(":")
    exc_map = {("domains/biology/DOMAIN.yaml", expected_kind, decl_name): "Field-specific reviewed classification."}
    with_exc = checker.check(root, placement_exceptions=exc_map)
    if expected_kind in {"functional", "procedure-kind"}:
        assert with_exc == []
    else:
        assert with_exc != []


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
