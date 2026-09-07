"""Cut 20 inventory, immutable freeze, and twelve real sabotages."""
from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import pytest
from n2_arms import Arm
from n2_arms_cut20 import CUT20_ARMS, DECLARATION_UNITS, UNIT_CHECKS, unit_of
from test_n2 import audit, baseline

import beliefs

ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = ROOT / "docs/designs/2026-09-05-conformance-cut-20.md"
CUT20_FREEZE_COMMIT = "5fa48a6"
CUT20_FROZEN_SHA256 = "3bf154b032c696c1b62954936262ff14137b1af055cc887c49fc0aa60b70cac5"


def test_the_inventory_is_exactly_the_eighteen_frozen_units():
    assert DECLARATION_UNITS == ("D1", "D2", "D4", "D5", "D8", "D9", "D10", "G5", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "parity-fixture-2", "boundary-no-read-entry-point-gained-an-argument")
    assert len(set(DECLARATION_UNITS)) == 18
    assert set(UNIT_CHECKS) == set(DECLARATION_UNITS)
    assert len(CUT20_ARMS) == len({arm.row for arm in CUT20_ARMS}) == 12
    assert {unit_of(arm.row) for arm in CUT20_ARMS} <= set(DECLARATION_UNITS)


def test_each_sabotage_names_one_real_source_site():
    package = Path(beliefs.__file__).resolve().parent
    for arm in CUT20_ARMS:
        assert arm.sabotage.before != arm.sabotage.after
        assert (package / arm.sabotage.module).read_text().count(arm.sabotage.before) == 1, arm.row
        assert arm.checks and all("::test_" in check for check in arm.checks)


def test_the_freeze_commit_and_frozen_body_are_pinned():
    subprocess.run(["git", "merge-base", "--is-ancestor", CUT20_FREEZE_COMMIT, "HEAD"], cwd=ROOT, check=True)
    frozen = subprocess.run(["git", "show", f"{CUT20_FREEZE_COMMIT}:{FROZEN_CUT.relative_to(ROOT)}"], cwd=ROOT, check=True, capture_output=True).stdout
    assert sha256(frozen).hexdigest() == CUT20_FROZEN_SHA256
    def body(data):
        return data[data.index(b"## 2."):]
    assert body(FROZEN_CUT.read_bytes()) == body(frozen)


def test_every_declared_check_resolves_and_passes_without_sabotage():
    checks = tuple(dict.fromkeys((*UNIT_CHECKS.values(), *(check for arm in CUT20_ARMS for check in arm.checks))))
    finding = baseline(Arm(row="N2", asserts="all eighteen units pass", sabotage=CUT20_ARMS[0].sabotage, checks=checks))
    assert finding.verdict == "resolved", finding.detail


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    work = tmp_path_factory.mktemp("n2-cut20")
    with ThreadPoolExecutor(max_workers=8) as pool:
        return tuple(pool.map(lambda item: audit(item[1], work / f"arm{item[0]}"), enumerate(CUT20_ARMS)))


def test_every_arm_fails_under_its_own_sabotage(findings):
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{f.arm.label}: {f.verdict}: {f.detail}" for f in unsound)
