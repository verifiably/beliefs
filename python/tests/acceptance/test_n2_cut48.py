"""Cut 48 freeze pins, exact accounting and independent mutation proof."""

from __future__ import annotations

import ast
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import frozen_guards
import pytest
import test_n2_cut46 as prior46
import test_n2_cut47 as prior47
from n2_arms import Arm, Sabotage
from n2_arms_cut48 import CO_CITED, CUT48_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of
from test_n2 import audit, baseline, workers

_LIVE_SABOTAGES: dict[str, Sabotage] = {}
"""Re-targets of this cut's own declared arms; none yet."""

RIDE_ALONG_ARMS = (
    # beliefs-cb2a39's ride-along (cut 48 §3, "live-table arm beside the declaration, not
    # counted"): cut 22's frozen B4b mutation, dropping the `continue` on an unheld observed
    # target in gather's observes loop. The cut names the banked-reason check, but a covered
    # corpus's absence returns before the loop (slice 2 decision 7), so that check is vacuous
    # for this mutation; the arm is homed on the check that reaches the loop with an observed
    # dataset the epoch never mapped (ruled in Task 7, recorded in the results).
    Arm(
        row="B4b",
        asserts="An observed target the view does not hold is skipped at the facet read, never fetched.",
        sabotage=Sabotage(
            module="evaluation.py",
            before="            if not view.holds(target):\n                continue\n",
            after="",
        ),
        checks=(
            "test_world_view.py::TestEvaluationOverTheWorld::test_an_unknown_observed_dataset_is_skipped_at_the_facet_read",
        ),
    ),
)
DECLARED_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT48_ARMS
)
CUT48_ARMS = DECLARED_ARMS + RIDE_ALONG_ARMS
"""Everything this guard audits: the 33 declared arms, then the uncounted ride-along."""

REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs/designs/2026-10-28-conformance-cut-48.md"
CUT48_FREEZE_COMMIT = "5895d232ea47584baa91dcf249717d905735e1a6"
CUT48_FROZEN_SHA256 = "8ab350edad763dc15d4831de74d3cac13053f869c0da209338919fbbab475d4d"
FROZEN_DECLARATION = "python/tests/n2_arms_cut48.py"
CUT48_DECLARATION_SHA256 = "b16832c572d2be8718c25139e70c9741206a28bf1cb2285fadc84fcbaf2d100b"
FROZEN_CONTENT_PINS = {
    "python/tests/n2_arms_cut47.py": "8639a5df6bdb4b619f2c2e518125d2d6267a8389d6475a41c5ee9a0547566c8b",
}
ROWS = ("W19", "W20", "G14", "Y19", "J17", "J20")


def _names_one_test(check: str) -> bool:
    """The check names one test function, top level or a class's method."""
    module, *path = check.split("::")
    scope: list[ast.stmt] = ast.parse((REPO_ROOT / "python/tests" / module).read_text()).body
    for part in path[:-1]:
        found = next((node for node in scope if isinstance(node, ast.ClassDef) and node.name == part), None)
        if found is None:
            return False
        scope = found.body
    return path[-1] in {node.name for node in scope if isinstance(node, ast.FunctionDef)}


def test_inventory_and_exact_unique_checks():
    assert len(DECLARATION_UNITS) == 33 and len(DECLARED_ARMS) == 33
    assert {unit.split("-")[0] for unit in DECLARATION_UNITS} == set(ROWS)
    assert tuple(arm.row for arm in DECLARED_ARMS) == DECLARATION_UNITS
    assert set(UNIT_CHECKS) == set(DECLARATION_UNITS)
    assert len(set(UNIT_CHECKS.values())) == 33
    assert len({arm.sabotage.before for arm in DECLARED_ARMS}) == 33
    assert CO_CITED == ()
    for arm in CUT48_ARMS:
        assert arm.sabotage.package == "beliefs" and arm.asserts.strip()
        assert arm.sabotage.before != arm.sabotage.after
        assert len(arm.checks) == 1 and _names_one_test(arm.checks[0]), arm.row
    for arm in DECLARED_ARMS:
        assert arm.checks == (UNIT_CHECKS[unit_of(arm.row)],)
    assert [arm.row for arm in RIDE_ALONG_ARMS] == ["B4b"]


def test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable():
    for arm in CUT48_ARMS:
        source = (REPO_ROOT / "python/src/beliefs" / arm.sabotage.module).read_text()
        assert source.count(arm.sabotage.before) == 1, arm.row
        ast.parse(source.replace(arm.sabotage.before, arm.sabotage.after))


def test_every_live_check_resolves_and_passes_without_sabotage():
    all_checks = Arm(
        row="N2",
        asserts="all cut-48 baseline checks",
        sabotage=CUT48_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT48_ARMS for check in arm.checks)),
    )
    finding = baseline(all_checks)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(tmp_path):
    with ThreadPoolExecutor(max_workers=workers()) as pool:
        findings = tuple(pool.map(lambda arm: audit(arm, tmp_path / arm.row), CUT48_ARMS))
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{f.arm.label}: {f.verdict}: {f.detail}" for f in unsound)


def _git(tmp_path, *args):
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        env={"PATH": os.defpath, "HOME": str(tmp_path), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_freeze_commit_and_body_are_pinned(tmp_path):
    _git(tmp_path, "merge-base", "--is-ancestor", CUT48_FREEZE_COMMIT, "HEAD")
    frozen = _git(tmp_path, "show", f"{CUT48_FREEZE_COMMIT}:{FROZEN_CUT.relative_to(REPO_ROOT)}")
    current = FROZEN_CUT.read_text()
    assert sha256(frozen.encode()).hexdigest() == CUT48_FROZEN_SHA256
    assert prior46._frozen_body(current) == prior46._frozen_body(frozen)
    assert "**33 arms, 33 declaration units, six exercised rows**" in current
    assert '("cut47_acceptance.py",)' in current


def test_canonical_declaration_is_pinned():
    assert frozen_guards.content_pin_holds(REPO_ROOT, FROZEN_DECLARATION, CUT48_DECLARATION_SHA256)


def test_prior_declarations_and_check_ownership_are_preserved():
    prior46.test_prior_declarations_are_frozen_and_no_check_is_reclaimed()
    prior47.test_prior_declarations_and_check_ownership_are_preserved()
    for path, digest in FROZEN_CONTENT_PINS.items():
        assert frozen_guards.content_pin_holds(REPO_ROOT, path, digest)
    checks = {check for arm in (*prior46.PRIOR_ARMS, *prior46.CUT46_ARMS, *prior47.CUT47_ARMS) for check in arm.checks}
    assert not set(UNIT_CHECKS.values()) & checks


def test_unit_parser_rejects_undeclared_rows():
    for row in DECLARATION_UNITS:
        assert unit_of(row) == row
    for row in ("", "W19", "W19-h", "G14-j", "Y19-g", "J17-a", "J20-a", "B4b"):
        with pytest.raises(ValueError, match="is not a cut-48 row"):
            unit_of(row)


def test_cut48_pilot(tmp_path):
    (arm,) = (arm for arm in CUT48_ARMS if arm.row == "W20-b")
    normal = baseline(arm)
    assert normal.verdict == "resolved", normal.detail
    mutated = audit(arm, tmp_path / arm.row)
    assert mutated.verdict == "sound", mutated.detail
