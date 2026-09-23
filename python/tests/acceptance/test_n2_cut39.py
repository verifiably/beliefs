"""Cut 39 declaration accounting, freeze pin, and N2 audit."""

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
from n2_arms_cut36 import CUT36_ARMS
from n2_arms_cut37 import CUT37_ARMS
from n2_arms_cut38 import CUT38_ARMS
from n2_arms_cut39 import (
    CO_CITED,
    CUT39_ARMS,
    DECLARATION_UNITS,
    REPLACE_UNREGISTERED,
    ROLLBACK_MEANS,
    UNIT_CHECKS,
    unit_of,
)
from test_n2 import audit, baseline
from test_n2_cut25 import CUT25_ARMS
from test_n2_cut25 import RETARGETED_ROWS as CUT25_RETARGETED_ROWS

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-23-conformance-cut-39.md"
CUT39_FREEZE_COMMIT = "8e81e1ac72ac9838bc863d07b93e2cdbfa31ad8c"
CUT39_FROZEN_SHA256 = "b92c7a2052e97d2ccc75fbb7fbb07b5d53d90ecc99904be666c61d9dd9dd7a43"
FROZEN_DECLARATION = "python/tests/n2_arms_cut39.py"
CUT39_DECLARATION_SHA256 = "9a0d3036b8c6353772f57c7dcb193b0f4215225cc4bccbe2f3d36b28023854e8"

# The plan's accounting table, keyed by Task 0's two engine facts
# `(REPLACE_UNREGISTERED, ROLLBACK_MEANS != "unrun")`; the frozen cut selects one row.
ACCOUNTING = {
    ("accepted", True): (14, 13),
    ("refused", True): (13, 13),
    ("accepted", False): (13, 12),
    ("refused", False): (12, 12),
}
FROZEN_ARMS, FROZEN_UNITS = ACCOUNTING[(REPLACE_UNREGISTERED, ROLLBACK_MEANS != "unrun")]

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
    "python/tests/n2_arms_cut36.py": "5e9a9e4",
    "python/tests/n2_arms_cut37.py": "2223f95",
    "python/tests/n2_arms_cut38.py": "b4d71dd",
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
    *CUT36_ARMS,
    *CUT37_ARMS,
    *CUT38_ARMS,
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut39")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT39_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_frozen_rows_units() -> None:
    assert (REPLACE_UNREGISTERED, ROLLBACK_MEANS) == ("accepted", "patched create effect")
    assert DECLARATION_UNITS == (
        "W17-p-a",
        "W17-p-b",
        "W17-p-c",
        "W17-p-d",
        "W17-p-e",
        "W17-p-f",
        "Y1-a",
        "Y1-b",
        "Y2-a",
        "Y3-a",
        "Y4-a",
        "Y4-b",
        "Y4-c",
    )
    assert len(CUT39_ARMS) == FROZEN_ARMS and len(DECLARATION_UNITS) == FROZEN_UNITS
    assert all(arm.sabotage.package == "beliefs" for arm in CUT39_ARMS)
    assert set(UNIT_CHECKS) == set(DECLARATION_UNITS)
    assert {check for arm in CUT39_ARMS for check in arm.checks} == set(UNIT_CHECKS.values())
    homed = {unit: sum(unit_of(arm.row) == unit for arm in CUT39_ARMS) for unit in DECLARATION_UNITS}
    assert homed == {
        unit: {"W17-p-e": 2 if REPLACE_UNREGISTERED == "accepted" else 1}.get(unit, 1) for unit in DECLARATION_UNITS
    }


def test_each_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT39_ARMS]
    assert len(rows) == len(set(rows))
    befores = [arm.sabotage.before for arm in CUT39_ARMS]
    assert len(befores) == len(set(befores))
    for arm in CUT39_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable() -> None:
    """A syntax error never counts as killing the named acceptance check."""
    package = REPO_ROOT / "python" / "src" / "beliefs"
    for arm in CUT39_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        source = target.read_text(encoding="utf-8")
        assert source.count(arm.sabotage.before) == 1, arm.row
        mutated = source.replace(arm.sabotage.before, arm.sabotage.after)
        ast.parse(mutated)


def test_every_acceptance_test_the_arms_name_exists() -> None:
    """The cited set is a subset of the module's tests, with one member per unit."""
    module = REPO_ROOT / "python" / "tests" / "acceptance" / "test_publication_records_acceptance.py"
    names = {
        node.name
        for node in ast.parse(module.read_text(encoding="utf-8")).body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }
    cited = {check.rsplit("::", 1)[1] for check in UNIT_CHECKS.values()}
    assert cited <= names, cited - names
    assert len(cited) == len(DECLARATION_UNITS)


def test_every_live_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-39 check passes against the real package",
        sabotage=CUT39_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT39_ARMS for check in arm.checks)),
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
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT39_FREEZE_COMMIT, "HEAD"],
            check=False,
        ).returncode
        == 0
    ), CUT39_FREEZE_COMMIT
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT39_FREEZE_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT39_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(frozen)
    assert f"**{FROZEN_ARMS} arms, {FROZEN_UNITS} declaration units**" in current
    assert '("cut38_acceptance.py",)' in current


def test_the_declaration_is_byte_exact_against_its_pinned_digest() -> None:
    """The arms the guard audits are the arms the accounting freezes on."""
    current = (REPO_ROOT / FROZEN_DECLARATION).read_bytes()
    assert sha256(current).hexdigest() == CUT39_DECLARATION_SHA256
    shim = (REPO_ROOT / "python" / "tests" / "acceptance" / "n2_arms_cut39.py").read_text(encoding="utf-8")
    assert "n2_arms_cut39.py" in shim  # the acceptance copy re-exports, never restates


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    assert (
        tuple(
            frozen if live.row in CUT25_RETARGETED_ROWS else live
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
    for arm in CUT39_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED), arm.row


def test_row_parser_accepts_only_exact_declared_units() -> None:
    for unit in DECLARATION_UNITS:
        assert unit_of(unit) == unit
    assert unit_of("W17-p-e2") == "W17-p-e"
    for row in (
        "",
        "W17",
        "W17-p",
        "W17-a",
        "W17-p-g",
        "W17-p-e1",
        "W17-p-e3",
        "W17-p-a2",
        "W17-p-ee",
        "Y1",
        "Y1-c",
        "Y1-a2",
        "Y2-b",
        "Y3-b",
        "Y4-d",
        "Y5-a",
        "T2-e",
        "BI-1",
    ):
        with pytest.raises(ValueError, match="is not a cut-39 row"):
            unit_of(row)


# Export the live tuple so arm_staleness.audited_arms measures every audited arm.
