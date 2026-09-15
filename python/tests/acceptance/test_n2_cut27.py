"""Cut 27 declaration accounting, freeze pin, and N2 audit."""

from __future__ import annotations

import ast
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
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
from n2_arms_cut27 import CO_CITED, CUT27_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of
from test_n2 import audit, baseline
from test_n2_cut25 import CUT25_ARMS

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-13-conformance-cut-27.md"
CUT27_FREEZE_COMMIT = "a04fc6a87fcd6fa49090d2344076cfd2d560fe7b"
CUT27_FROZEN_SHA256 = "7eb63bee70679bd4e79db7ed5fc41c3779eae3a4eac2a8a520cf63d2f9a3d4d1"
FROZEN_DECLARATION = "python/tests/acceptance/n2_arms_cut27.py"
CUT27_DECLARATION_COMMIT = "3674da8ab348fc3afdf0a5d7af09a141b9d665a3"
CUT27_DECLARATION_SHA256 = "564cd8fa93f5d0c22d374f90ba0b2bfbee3758504c977a5367cbd1930b15008f"

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
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut27")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT27_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_five_declared_units() -> None:
    assert DECLARATION_UNITS == ("R23", "W8a", "X5", "W13", "S9")
    assert {unit_of(arm.row) for arm in CUT27_ARMS} == set(DECLARATION_UNITS)
    assert len(CUT27_ARMS) == 27
    assert all(arm.sabotage.package == "beliefs" for arm in CUT27_ARMS)
    assert set(UNIT_CHECKS) == set(DECLARATION_UNITS)
    assert set(UNIT_CHECKS.values()) <= {check for arm in CUT27_ARMS for check in arm.checks}


def test_each_lettered_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT27_ARMS]
    assert len(rows) == len(set(rows))
    for arm in CUT27_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site() -> None:
    package = REPO_ROOT / "python" / "src" / "beliefs"
    for arm in CUT27_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        source = target.read_text(encoding="utf-8")
        assert source.count(arm.sabotage.before) == 1, arm.row
        ast.parse(source.replace(arm.sabotage.before, arm.sabotage.after))


def test_every_live_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-27 check passes against the real package",
        sabotage=CUT27_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT27_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{finding.arm.label}: {finding.verdict}: {finding.detail}" for finding in unsound)


def _frozen_body(text: str) -> str:
    """§§2–7: from the boundary heading to the first heading past the limitations.

    The dated supplemental live-arm evidence in §8 is outside the original
    freeze, using the same slicing rule as cut 19.
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
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT27_FREEZE_COMMIT, "HEAD"],
            check=False,
        ).returncode
        == 0
    ), CUT27_FREEZE_COMMIT
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT27_FREEZE_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT27_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(frozen)
    assert "**5 declaration units**" in current
    assert "Five guarantee rows are read, **3 full/closed** (X5, W13, S9)" in current
    assert '("cut26_acceptance.py",)' in current


def test_the_declaration_is_byte_exact_against_its_own_commit() -> None:
    """The declaring commit is a descendant of the freeze and an ancestor of HEAD."""
    for commit in (CUT27_FREEZE_COMMIT, CUT27_DECLARATION_COMMIT):
        assert (
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
                check=False,
            ).returncode
            == 0
        ), commit
    assert (
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT27_FREEZE_COMMIT, CUT27_DECLARATION_COMMIT],
            check=False,
        ).returncode
        == 0
    )
    current = (REPO_ROOT / FROZEN_DECLARATION).read_bytes()
    assert sha256(current).hexdigest() == CUT27_DECLARATION_SHA256
    assert current.decode("utf-8") == _show(CUT27_DECLARATION_COMMIT, FROZEN_DECLARATION)


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    # Live matcher migration, 2026-09-14 (slice 5): normalize only W1-a.
    assert tuple(
        replace(live, sabotage=frozen.sabotage) if live.row == "W1-a" else live
        for live, frozen in zip(
            CUT25_ARMS[: len(FROZEN_CUT25_ARMS)], FROZEN_CUT25_ARMS, strict=True
        )
    ) == FROZEN_CUT25_ARMS
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
            check=False,
        )
        assert completed.returncode == 0, f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT27_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED), arm.row


def test_row_parser_accepts_only_declared_units_and_one_letter_suffix() -> None:
    for unit in DECLARATION_UNITS:
        assert unit_of(unit) == unit
        assert unit_of(f"{unit}-a") == unit
        assert unit_of(f"{unit}-z") == unit
    for row in ("", "D1", "R23-", "R23a", "R23-A", "R23-1", "R23-aa", "R23-a-b"):
        with pytest.raises(ValueError, match="is not a cut-27 row"):
            unit_of(row)
