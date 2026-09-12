"""Cut 26 declaration accounting, freeze pin, and N2 audit."""

from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import pytest
from n2_arms import Arm, installed_nodes_root
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
from n2_arms_cut26 import CO_CITED, CUT26_ARMS, DECLARATION_UNITS, NODES_SOURCE_COMMIT, unit_of
from test_n2 import audit, baseline
from test_n2_cut25 import CUT25_ARMS

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-12-conformance-cut-26.md"
CUT26_FREEZE_COMMIT = "16926adfa33cae63f8bc33c65106a20de95df8ef"
CUT26_FROZEN_SHA256 = "9775b0de0dc7c3b1d5234a2ae9d55a839a3c0febeadb971b0d547cd7afc1d268"
FROZEN_DECLARATION = "python/tests/n2_arms_cut26.py"
CUT26_DECLARATION_SHA256 = "e507c6b4b2a8c660b98bad15456508555fd2ef7ed532476524a2e03fe1a1508f"

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
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut26")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT26_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_one_declared_unit() -> None:
    assert DECLARATION_UNITS == ("D1",)
    assert {unit_of(arm.row) for arm in CUT26_ARMS} == {"D1"}
    assert [arm.row for arm in CUT26_ARMS] == ["D1-a", "D1-b"]
    assert all(arm.sabotage.package == "nodes" for arm in CUT26_ARMS)


def test_each_lettered_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT26_ARMS]
    assert len(rows) == len(set(rows))
    for arm in CUT26_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site() -> None:
    package = installed_nodes_root()
    for arm in CUT26_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row


def test_the_nodes_gate_is_in_the_installed_tree() -> None:
    """STANDARD §2.3's sentence is what the arms check; the installed nodes must carry it.
    The commit itself is human-read (results §1): CI's nodes checkout has no history."""
    standard = installed_nodes_root().parents[2] / "docs" / "STANDARD.md"
    assert standard.is_file(), standard
    assert "opaque to the kernel" in standard.read_text(encoding="utf-8")
    assert len(NODES_SOURCE_COMMIT) >= 7


def test_every_live_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-26 check passes against the real package",
        sabotage=CUT26_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT26_ARMS for check in arm.checks)),
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
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT26_FREEZE_COMMIT, "HEAD"],
            check=False,
        ).returncode
        == 0
    ), CUT26_FREEZE_COMMIT
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT26_FREEZE_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT26_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(frozen)
    assert "**1 declaration unit**" in current
    assert "One guarantee row is read, **1 full/closed** (D1)" in current
    assert '("cut25_acceptance.py",)' in current


def test_the_declaration_is_byte_exact_against_the_freeze() -> None:
    """The arms the guard audits are the arms that were frozen: the canonical table's
    bytes at HEAD equal its bytes at the freeze commit, and that digest is pinned here
    so a rewrite of both the file and the commit reference cannot pass silently."""
    current = (REPO_ROOT / FROZEN_DECLARATION).read_bytes()
    assert sha256(current).hexdigest() == CUT26_DECLARATION_SHA256
    assert current.decode("utf-8") == _show(CUT26_FREEZE_COMMIT, FROZEN_DECLARATION)


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    assert CUT25_ARMS[: len(FROZEN_CUT25_ARMS)] == FROZEN_CUT25_ARMS
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
            check=False,
        )
        assert completed.returncode == 0, f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT26_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED), arm.row


def test_row_parser_accepts_only_declared_units_and_one_letter_suffix() -> None:
    for unit in DECLARATION_UNITS:
        assert unit_of(unit) == unit
        assert unit_of(f"{unit}-a") == unit
        assert unit_of(f"{unit}-z") == unit
    for row in ("", "D2", "D1-", "D1a", "D1-A", "D1-1", "D1-aa", "D1-a-b"):
        with pytest.raises(ValueError, match="is not a cut-26 row"):
            unit_of(row)
