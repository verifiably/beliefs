"""Cut 47 freeze pins, exact accounting and independent mutation proof."""

from __future__ import annotations

import ast
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import frozen_guards
import pytest
import test_n2_cut46 as prior
from n2_arms import Arm
from n2_arms_cut47 import CO_CITED, CUT47_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of
from test_n2 import audit, baseline, workers

REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs/designs/2026-10-27-conformance-cut-47.md"
CUT47_FREEZE_COMMIT = "d7d10a050c9975513fddd528f6a785d6f9981c78"
CUT47_FROZEN_SHA256 = "8155c24eab0900c221f82a81928bc9d9a069ccee0a26f712e4f5fca19fc87c7f"
FROZEN_DECLARATION = "python/tests/n2_arms_cut47.py"
CUT47_DECLARATION_SHA256 = "8639a5df6bdb4b619f2c2e518125d2d6267a8389d6475a41c5ee9a0547566c8b"
FROZEN_CONTENT_PINS = {
    "python/tests/n2_arms_cut46.py": "da3e36e19ecf87d3da17da009350bf0c82fcc29315323057f64e9c781cf6dc04",
}


def test_inventory_and_exact_unique_checks():
    assert DECLARATION_UNITS == ("Y5-f", "Y17-q", "Y17-r", "Y17-s", "Y17-t", "Y17-u", "Y17-v", "Y17-w", "Y17-x")
    assert len(CUT47_ARMS) == len(DECLARATION_UNITS) == 9
    assert {unit.split("-")[0] for unit in DECLARATION_UNITS} == {"Y5", "Y17"}
    assert tuple(arm.row for arm in CUT47_ARMS) == DECLARATION_UNITS
    assert set(UNIT_CHECKS) == set(DECLARATION_UNITS)
    assert len(set(UNIT_CHECKS.values())) == 9
    assert len({arm.sabotage.before for arm in CUT47_ARMS}) == 9
    assert CO_CITED == ()
    for arm in CUT47_ARMS:
        assert arm.sabotage.package == "beliefs" and arm.asserts.strip()
        assert arm.sabotage.before != arm.sabotage.after
        assert arm.checks == (UNIT_CHECKS[unit_of(arm.row)],)
        module, check = arm.checks[0].split("::")
        tree = ast.parse((REPO_ROOT / "python/tests" / module).read_text())
        assert check in {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable():
    for arm in CUT47_ARMS:
        source = (REPO_ROOT / "python/src/beliefs" / arm.sabotage.module).read_text()
        assert source.count(arm.sabotage.before) == 1, arm.row
        ast.parse(source.replace(arm.sabotage.before, arm.sabotage.after))


def test_every_live_check_resolves_and_passes_without_sabotage():
    all_checks = Arm(
        row="N2",
        asserts="all cut-47 baseline checks",
        sabotage=CUT47_ARMS[0].sabotage,
        checks=tuple(UNIT_CHECKS.values()),
    )
    finding = baseline(all_checks)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(tmp_path):
    with ThreadPoolExecutor(max_workers=workers()) as pool:
        findings = tuple(pool.map(lambda arm: audit(arm, tmp_path / arm.row), CUT47_ARMS))
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
    _git(tmp_path, "merge-base", "--is-ancestor", CUT47_FREEZE_COMMIT, "HEAD")
    frozen = _git(tmp_path, "show", f"{CUT47_FREEZE_COMMIT}:{FROZEN_CUT.relative_to(REPO_ROOT)}")
    current = FROZEN_CUT.read_text()
    assert sha256(frozen.encode()).hexdigest() == CUT47_FROZEN_SHA256
    assert prior._frozen_body(current) == prior._frozen_body(frozen)
    assert "**9 arms, 9 declaration units, two exercised rows**" in current
    assert '("cut46_acceptance.py",)' in current


def test_canonical_declaration_is_pinned():
    assert frozen_guards.content_pin_holds(REPO_ROOT, FROZEN_DECLARATION, CUT47_DECLARATION_SHA256)


def test_prior_declarations_and_check_ownership_are_preserved():
    prior.test_prior_declarations_are_frozen_and_no_check_is_reclaimed()
    for path, digest in FROZEN_CONTENT_PINS.items():
        assert frozen_guards.content_pin_holds(REPO_ROOT, path, digest)
    checks = {check for arm in (*prior.PRIOR_ARMS, *prior.CUT46_ARMS) for check in arm.checks}
    assert not set(UNIT_CHECKS.values()) & checks


def test_unit_parser_rejects_undeclared_rows():
    for row in DECLARATION_UNITS:
        assert unit_of(row) == row
    for row in ("", "Y5", "Y5-e", "Y17", "Y17-a", "Y17-qq", "Y18-q"):
        with pytest.raises(ValueError, match="is not a cut-47 row"):
            unit_of(row)


def test_cut47_pilot(tmp_path):
    (arm,) = (arm for arm in CUT47_ARMS if arm.row == "Y17-s")
    normal = baseline(arm)
    assert normal.verdict == "resolved", normal.detail
    mutated = audit(arm, tmp_path / arm.row)
    assert mutated.verdict == "sound", mutated.detail
