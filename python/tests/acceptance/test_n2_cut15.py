"""Cut 15 declaration accounting and N2 audit."""

import subprocess
from concurrent.futures import ThreadPoolExecutor
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
from n2_arms_cut15 import CO_CITED, CUT15_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "superpowers" / "specs" / "2026-09-01-workflow-surface-design.md"
CUT15_FREEZE_COMMIT = "e2f9d71"

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut6.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut7.py": "117f37e",
    "python/tests/acceptance/n2_arms_cut8.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba",
    "python/tests/acceptance/n2_arms_cut10.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut11.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut12.py": "5dff360",
    "python/tests/acceptance/n2_arms_cut13.py": "7504d69",
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
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    root = tmp_path_factory.mktemp("n2-cut15")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(CUT15_ARMS)))


def test_the_inventory_is_seventeen_selected_and_eight_labeled() -> None:
    assert ROW_UNITS == {"R2": 2, "R16": 10, "R20": 2, "R21": 2, "R23": 1}
    assert sum(ROW_UNITS.values()) == 17
    assert LABELED_UNITS == tuple(f"K{number}" for number in range(1, 9))


def test_the_arm_rows_are_unique_and_counted() -> None:
    rows = [arm.row for arm in CUT15_ARMS]
    assert len(rows) == len(set(rows)) == 30


def test_every_declared_unit_is_carried_by_at_least_one_arm() -> None:
    carried = {unit_of(arm.row) for arm in CUT15_ARMS}
    assert set(ROW_UNITS) | set(LABELED_UNITS) <= carried


def test_every_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-15 check passes against the real package",
        sabotage=CUT15_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT15_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{finding.arm.label}: {finding.verdict}: {finding.detail}" for finding in unsound)


def test_the_frozen_cut_and_commit_state_the_same_accounting() -> None:
    text = FROZEN_CUT.read_text(encoding="utf-8")
    assert "**17 selected + 8 labeled = 25 units.**" in text
    assert "R2 = 2, R16 = 10, R20 = 2, R21 = 2, R23 = 1" in text
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT15_FREEZE_COMMIT, "HEAD"],
        check=False,
    )
    assert completed.returncode == 0


def test_every_arm_has_one_source_mutation_and_exact_check_nodes() -> None:
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT15_ARMS:
        assert arm.checks, arm.row
        assert len(arm.checks) == len(set(arm.checks)), arm.row
        assert arm.sabotage.before != arm.sabotage.after, arm.row
        assert arm.asserts.strip(), arm.row
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_frozen_prior_declarations_are_unchanged_and_not_reclaimed() -> None:
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
            check=False,
        )
        assert completed.returncode == 0, f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT15_ARMS:
        claimed = set(arm.checks) & prior
        assert claimed <= set(CO_CITED.get(arm.row, ())), arm.row
