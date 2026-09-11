"""Cut 22 declaration accounting, freeze pin, and N2 audit."""

from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from n2_arms import Arm, Sabotage
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
from n2_arms_cut22 import CO_CITED, CUT22_ARMS, DECLARATION_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

# Final-review run membership, 2026-09-09; preserve the frozen declaration.
_LIVE_SABOTAGES = {
    "D6a": Sabotage(
        module="belief.py",
        before='    closure_nodes = tuple(a.identity() for a in matched) + tuple(stored.typed_ref("run", a.run) for a in matched) + observed\n',
        after='    closure_nodes = tuple(a.identity() for a in matched) + tuple(stored.typed_ref("run", a.run) for a in matched)\n',
    ),
}
CUT22_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT22_ARMS
)

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-08-conformance-cut-22.md"
CUT22_FREEZE_COMMIT = "99d5757"
CUT22_FROZEN_SHA256 = "49a3cbdd843afa0d090c9dbe685bbf136ed9d0d62da12a25d0739691409323a0"

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
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut22")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT22_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_nine_frozen_units() -> None:
    assert DECLARATION_UNITS == ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "D6", "M8")
    assert {unit_of(arm.row) for arm in CUT22_ARMS} == set(DECLARATION_UNITS)
    assert len(CUT22_ARMS) == 17


def test_each_lettered_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT22_ARMS]
    assert len(rows) == len(set(rows))
    for arm in CUT22_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site() -> None:
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT22_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row


def test_every_declared_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-22 check passes against the real package",
        sabotage=CUT22_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT22_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{finding.arm.label}: {finding.verdict}: {finding.detail}" for finding in unsound)


def _frozen_body(text: str) -> str:
    """§§2–7: from the boundary heading to the first heading past the limitations.

    No §8 exists yet on this cut, so the slice runs to the end of the file
    either way; the same slicing rule as cut 19's is kept so a later mechanism
    amendment (were one ever added) is excluded the same way.
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
    """The cut was frozen once, so §§2–7 are byte-exact against that one commit."""
    assert (
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT22_FREEZE_COMMIT, "HEAD"],
            check=False,
        ).returncode
        == 0
    ), CUT22_FREEZE_COMMIT
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT22_FREEZE_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT22_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(frozen)
    assert "**9 declaration units**" in current
    assert "Nine guarantee rows are read, **9 full/closed** (B1–B7, D6, M8), 1 partial" in current
    assert '("cut21_acceptance.py",)' in current


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
            check=False,
        )
        assert completed.returncode == 0, f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT22_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED), arm.row
