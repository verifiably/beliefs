"""Cut 18 declaration accounting, freeze pin, and N2 audit."""

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
from n2_arms_cut18 import CO_CITED, CUT18_ARMS, DECLARATION_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

# Live facet-contract matcher migration, 2026-09-07; canonical table remains frozen at e0bc65c.
_LIVE_SABOTAGES = {
    "M3": Sabotage(
        module="audit.py",
        before="    findings = list(corpus_check(view, profile))\n",
        after='    from beliefs import corpus as _corpus_module\n\n    _corpus_module.standing_in_local_view(view, "corpus")\n    findings = list(corpus_check(view, profile))\n',
    ),
}
CUT18_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT18_ARMS
)

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-04-conformance-cut-18.md"
FROZEN_CUT_AT_FREEZE = "docs/designs/2026-09-04-conformance-cut-17.md"
CUT18_FREEZE_COMMIT = "c7d78f5"
RENUMBERING_AMENDMENT_COMMIT = "e0bc65c"
CUT18_FROZEN_SHA256 = "797775b5c591c3c7ade1d1e4f0f188097a4fac27f21435218dbb4fa7f8e54e29"

#: The renumbering is a rename, not a re-reading (cut document §8).
RENUMBERING_SUBSTITUTIONS = (
    ("cut 17", "cut 18"),
    ("Cut 17", "Cut 18"),
    ("cut-17", "cut-18"),
    ("cut16_acceptance", "cut17_acceptance"),
)

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
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut18")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT18_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_seventeen_frozen_units() -> None:
    assert DECLARATION_UNITS == (
        "G2c",
        "G8",
        "C6",
        "R5",
        "S5",
        "R23",
        "W16",
        "C1",
        "T8",
        "M13",
        "M11",
        "R19",
        "R22",
        "M1",
        "M3",
        "M5",
        "boundary-reresolution-after-delete",
    )
    assert len(DECLARATION_UNITS) == len(set(DECLARATION_UNITS)) == 17
    assert {unit_of(arm.row) for arm in CUT18_ARMS} == set(DECLARATION_UNITS)


def test_each_lettered_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT18_ARMS]
    assert len(rows) == len(set(rows))
    for arm in CUT18_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site() -> None:
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT18_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row


def test_every_declared_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-18 check passes against the real package",
        sabotage=CUT18_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT18_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{finding.arm.label}: {finding.verdict}: {finding.detail}" for finding in unsound)


def _frozen_body(text: str) -> str:
    start = text.index("## 2. The boundary")
    end = text.index("\n## 8.", start) if "\n## 8." in text[start:] else len(text)
    return text[start:end]


def _show(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_the_freeze_commit_and_sections_two_through_seven_are_pinned() -> None:
    """The frozen body survives the renumbering by pinning both commits.

    The cut froze as 17 at `CUT18_FREEZE_COMMIT` and was renumbered to 18 at
    `RENUMBERING_AMENDMENT_COMMIT` (cut document §8). §§2–7 must be byte-exact
    against the renumbering commit, and byte-exact against the freeze commit
    under exactly the four declared substitutions — so a later edit to the
    frozen body fails even though the section text moved once.
    """
    for commit in (CUT18_FREEZE_COMMIT, RENUMBERING_AMENDMENT_COMMIT):
        assert (
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
                check=False,
            ).returncode
            == 0
        ), commit
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT18_FREEZE_COMMIT, FROZEN_CUT_AT_FREEZE)
    amended = _show(RENUMBERING_AMENDMENT_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT18_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(amended)
    renumbered = _frozen_body(frozen)
    for before, after in RENUMBERING_SUBSTITUTIONS:
        renumbered = renumbered.replace(before, after)
    assert _frozen_body(current) == renumbered
    assert "**17 declaration units**" in current
    assert "Sixteen guarantee rows are read: **7 full/closed**" in current
    assert "**5 partial**" in current
    assert "**4 closed-row re-reads**" in current


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
            check=False,
        )
        assert completed.returncode == 0, f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT18_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED.get(arm.row, ())), arm.row
