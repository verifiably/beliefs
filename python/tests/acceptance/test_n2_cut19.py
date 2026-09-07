"""Cut 19 declaration accounting, freeze pin, and N2 audit."""

from __future__ import annotations

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
from n2_arms_cut19 import CO_CITED, CUT19_ARMS, DECLARATION_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-05-conformance-cut-19.md"
CUT19_FREEZE_COMMIT = "5cc2153"
CUT19_FROZEN_SHA256 = "30875b845b4db648622bcce7a7e722a022f2759f0788370543312e81a8b66796"

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
    "python/tests/acceptance/n2_arms_cut17.py": "1d8f293",
    "python/tests/n2_arms_cut18.py": "e0bc65c",
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
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut19")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT19_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_eleven_frozen_units() -> None:
    assert DECLARATION_UNITS == tuple(f"J{n}" for n in range(1, 12))
    assert len(DECLARATION_UNITS) == len(set(DECLARATION_UNITS)) == 11
    assert {unit_of(arm.row) for arm in CUT19_ARMS} == set(DECLARATION_UNITS)


def test_each_lettered_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT19_ARMS]
    assert len(rows) == len(set(rows))
    for arm in CUT19_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site() -> None:
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT19_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row


def test_every_declared_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-19 check passes against the real package",
        sabotage=CUT19_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT19_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{finding.arm.label}: {finding.verdict}: {finding.detail}" for finding in unsound)


def _frozen_body(text: str) -> str:
    """§§2–7: from the boundary heading to the first heading past the limitations.

    The freeze predates the mechanism amendment, so the frozen file ends at §7
    and the current one continues into §8. Trailing newlines are stripped so
    the two slices are the same text either way.
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
    """The cut was frozen once, so §§2–7 are byte-exact against that one commit.

    No renumbering substitution applies: cut 19 was numbered 19 at the freeze.
    The only later edit to the file is §8, the mechanism amendment, which sits
    entirely outside the slice compared here.
    """
    assert (
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT19_FREEZE_COMMIT, "HEAD"],
            check=False,
        ).returncode
        == 0
    ), CUT19_FREEZE_COMMIT
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT19_FREEZE_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT19_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(frozen)
    assert "**11 declaration units**" in current
    assert "Eleven guarantee rows are read, **11 full/closed** (J1–J11), 0 partial, 0" in current
    assert '("cut18_acceptance.py",)' in current


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
            check=False,
        )
        assert completed.returncode == 0, f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT19_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED), arm.row
