"""Cut 36 declaration accounting, freeze pin, and N2 audit."""

from __future__ import annotations

import ast
import subprocess
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import pytest
from n2_arms import Arm
from n2_arms_cut3 import CUT3_ARMS
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import CUT7_ARMS
from n2_arms_cut8 import CUT8_ARMS
from n2_arms_cut9 import CUT9_ARMS
from n2_arms_cut10 import CUT10_ARMS
from n2_arms_cut11 import CUT11_ARMS
from n2_arms_cut12 import CUT12_ARMS
from n2_arms_cut13 import CUT13_ARMS
from n2_arms_cut14 import CUT14_ARMS
from n2_arms_cut15 import CUT15_ARMS
from n2_arms_cut16 import CUT16_ARMS
from n2_arms_cut17 import CUT17_ARMS
from n2_arms_cut18 import CUT18_ARMS
from n2_arms_cut19 import CUT19_ARMS
from n2_arms_cut20 import CUT20_ARMS
from n2_arms_cut21 import CUT21_ARMS
from n2_arms_cut22 import CUT22_ARMS
from n2_arms_cut23 import CUT23_ARMS
from n2_arms_cut24 import CUT24_ARMS
from n2_arms_cut25 import CUT25_ARMS as FROZEN_CUT25_ARMS
from n2_arms_cut26 import CUT26_ARMS
from n2_arms_cut27 import CUT27_ARMS
from n2_arms_cut28 import CUT28_ARMS
from n2_arms_cut29 import CUT29_ARMS
from n2_arms_cut30 import CUT30_ARMS
from n2_arms_cut31 import CUT31_ARMS
from n2_arms_cut32 import CUT32_ARMS
from n2_arms_cut33 import CUT33_ARMS
from n2_arms_cut34 import CUT34_ARMS
from n2_arms_cut35 import CUT35_ARMS
from n2_arms_cut36 import CO_CITED, CUT36_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of
from test_n2 import audit, baseline
from test_n2_cut25 import CUT25_ARMS
from test_n2_cut25 import RETARGETED_ROWS as CUT25_RETARGETED_ROWS

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-21-conformance-cut-36.md"
CUT36_FREEZE_COMMIT = "635345697562f71f23763b72bbd129fc8c19007b"
CUT36_FROZEN_SHA256 = "c4dea1fc153ecb2a0c5f90fc647ed9f67d3f891498c7e87f1d445366a4f4d6bb"
FROZEN_DECLARATION = "python/tests/n2_arms_cut36.py"
CUT36_DECLARATION_SHA256 = "1b66b97223ca6f4a2fc5117cebe21234e979f9e3ef14575838e5195e73e793b9"

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut3.py": "1e92471",
    "python/tests/n2_arms_cut5.py": "1e92471",
    "python/tests/n2_arms_cut6.py": "fdea7a7",
    "python/tests/n2_arms_cut7.py": "8ca085e",
    "python/tests/acceptance/n2_arms_cut8.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba",
    "python/tests/acceptance/n2_arms_cut10.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut11.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut12.py": "5dff360",
    "python/tests/acceptance/n2_arms_cut13.py": "7504d69",
    "python/tests/acceptance/n2_arms_cut14.py": "f982778",
    "python/tests/acceptance/n2_arms_cut15.py": "8a4d43b",
    "python/tests/n2_arms_cut16.py": "b0882d3",
    "python/tests/acceptance/n2_arms_cut17.py": "c367070",
    "python/tests/n2_arms_cut18.py": "e0bc65c",
    "python/tests/acceptance/n2_arms_cut19.py": "8723fac",
    "python/tests/n2_arms_cut20.py": "8639771",
    "python/tests/acceptance/n2_arms_cut20.py": "d5e203c",
    "python/tests/acceptance/n2_arms_cut21.py": "804cfac",
    "python/tests/acceptance/n2_arms_cut22.py": "4d93b64",
    "python/tests/acceptance/n2_arms_cut23.py": "2283527",
    "python/tests/acceptance/n2_arms_cut24.py": "79f118f",
    "python/tests/n2_arms_cut25.py": "5072609",
    "python/tests/acceptance/n2_arms_cut25.py": "515fc8b",
    "python/tests/n2_arms_cut26.py": "16926ad",
    "python/tests/acceptance/n2_arms_cut27.py": "3674da8",
    "python/tests/acceptance/n2_arms_cut28.py": "d11baf9",
    "python/tests/acceptance/n2_arms_cut29.py": "0e57a52",
    "python/tests/acceptance/n2_arms_cut30.py": "31b083e",
    "python/tests/n2_arms_cut31.py": "2977a83",
    "python/tests/n2_arms_cut32.py": "44343da",
    "python/tests/n2_arms_cut33.py": "d4d6432",
    "python/tests/n2_arms_cut34.py": "1b7e9f2",
    "python/tests/n2_arms_cut35.py": "d525b7d",
}

PRIOR_ARMS = (
    *CUT3_ARMS,
    *CUT5_ARMS,
    *CUT6_ARMS,
    *CUT7_ARMS,
    *CUT8_ARMS,
    *CUT9_ARMS,
    *CUT10_ARMS,
    *CUT11_ARMS,
    *CUT12_ARMS,
    *CUT13_ARMS,
    *CUT14_ARMS,
    *CUT15_ARMS,
    *CUT16_ARMS,
    *CUT17_ARMS,
    *CUT18_ARMS,
    *CUT19_ARMS,
    *CUT20_ARMS,
    *CUT21_ARMS,
    *CUT22_ARMS,
    *CUT23_ARMS,
    *CUT24_ARMS,
    *CUT25_ARMS,
    *CUT26_ARMS,
    *CUT27_ARMS,
    *CUT28_ARMS,
    *CUT29_ARMS,
    *CUT30_ARMS,
    *CUT31_ARMS,
    *CUT32_ARMS,
    *CUT33_ARMS,
    *CUT34_ARMS,
    *CUT35_ARMS,
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut36")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT36_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_sixteen_declared_units() -> None:
    assert DECLARATION_UNITS == (
        "L8-a",
        "L8-b",
        "L8-c",
        "L8-d",
        "L8-e",
        "L8-f",
        "L8-g",
        "L8-h",
        "L8-i",
        "L8-j",
        "L8-k",
        "L4-a",
        "L10-a",
        "BI-1",
        "BI-2",
        "BI-3",
    )
    assert len(CUT36_ARMS) == 18 and len(DECLARATION_UNITS) == 16
    assert all(arm.sabotage.package == "beliefs" for arm in CUT36_ARMS)
    assert set(UNIT_CHECKS) == set(DECLARATION_UNITS)
    assert {check for arm in CUT36_ARMS for check in arm.checks} == set(UNIT_CHECKS.values())
    homed = {unit: sum(unit_of(arm.row) == unit for arm in CUT36_ARMS) for unit in DECLARATION_UNITS}
    assert homed == {unit: 2 if unit in ("L8-a", "L8-j") else 1 for unit in DECLARATION_UNITS}


def test_each_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT36_ARMS]
    assert len(rows) == len(set(rows))
    befores = [arm.sabotage.before for arm in CUT36_ARMS]
    assert len(befores) == len(set(befores))
    for arm in CUT36_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable() -> None:
    """A syntax error never counts as killing the named acceptance check."""
    package = REPO_ROOT / "python" / "src" / "beliefs"
    for arm in CUT36_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        source = target.read_text(encoding="utf-8")
        assert source.count(arm.sabotage.before) == 1, arm.row
        mutated = source.replace(arm.sabotage.before, arm.sabotage.after)
        ast.parse(mutated)


def test_every_acceptance_test_the_arms_name_exists() -> None:
    module = REPO_ROOT / "python" / "tests" / "acceptance" / "test_event_order_acceptance.py"
    names = {
        node.name
        for node in ast.parse(module.read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    assert len(names) == len(DECLARATION_UNITS)
    for check in UNIT_CHECKS.values():
        assert check.rpartition("::")[2] in names, check


def test_every_live_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-36 check passes against the real package",
        sabotage=CUT36_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT36_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{finding.arm.label}: {finding.verdict}: {finding.detail}" for finding in unsound)


def _frozen_body(text: str) -> str:
    """§§2–7: from the boundary heading to the first heading past the limitations.

    A dated supplement in §8 is outside the original freeze, using the same
    slicing rule as cuts 19, 25, 30 and 31.
    """
    start = text.index("## 2. The boundary")
    end = text.index("\n## 8.", start) if "\n## 8." in text[start:] else len(text)
    return text[start:end].rstrip("\n")


def _show(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_the_freeze_commit_and_sections_two_through_seven_are_pinned() -> None:
    """Once frozen, §§2–7 are byte-exact against the freeze commit."""
    assert (
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT36_FREEZE_COMMIT, "HEAD"],
            check=False,
        ).returncode
        == 0
    ), CUT36_FREEZE_COMMIT
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT36_FREEZE_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT36_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(frozen)
    assert "**16 declaration units**" in current
    assert '("cut35_acceptance.py",)' in current


def test_the_declaration_is_byte_exact_against_its_pinned_digest() -> None:
    """The arms the guard audits are the arms the accounting freezes on: the
    canonical table's bytes are pinned here, so an edit to the table without an
    edit to this digest cannot pass silently. The declaration is written after
    the freeze commit — the cut document names the table it will carry, and
    this is where the bytes are held."""
    current = (REPO_ROOT / FROZEN_DECLARATION).read_bytes()
    assert sha256(current).hexdigest() == CUT36_DECLARATION_SHA256
    shim = (REPO_ROOT / "python" / "tests" / "acceptance" / "n2_arms_cut36.py").read_text(encoding="utf-8")
    assert "n2_arms_cut36.py" in shim  # the acceptance copy re-exports, never restates


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    assert (
        tuple(
            frozen if live.row in CUT25_RETARGETED_ROWS else live  # re-targeted rows: 2026-09-14 W1-a, 2026-09-15 W5a-m
            for live, frozen in zip(CUT25_ARMS[: len(FROZEN_CUT25_ARMS)], FROZEN_CUT25_ARMS, strict=True)
        )
        == FROZEN_CUT25_ARMS
    )
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
            check=False,
        )
        assert completed.returncode == 0, f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT36_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED), arm.row


def test_row_parser_accepts_only_exact_declared_units() -> None:
    for unit in DECLARATION_UNITS:
        assert unit_of(unit) == unit
    assert unit_of("L8-a1") == unit_of("L8-a2") == "L8-a"
    assert unit_of("L8-j1") == unit_of("L8-j2") == "L8-j"
    for row in ("", "L8", "L8-l", "L8-aa", "L8-b1", "L8-a3", "L4-a1", "BI", "BI-4", "BI-1a", "BI-11", "BI-1-a", "H4-a", "U1"):
        with pytest.raises(ValueError, match="is not a cut-36 row"):
            unit_of(row)


# Export the live tuple so arm_staleness.audited_arms measures every audited arm.
