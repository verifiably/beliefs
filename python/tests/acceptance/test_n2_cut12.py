"""Cut 12's declaration accounting, N2 audit, and lettered-arm partition."""

from __future__ import annotations

import re
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
from n2_arms_cut12 import CO_CITED, CUT12_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import MalformedArm, audit, baseline

import beliefs.root as science_root

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-29-conformance-cut-12.md"
CUT12_FREEZE_COMMIT = "b2f9593"

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut6.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut7.py": "117f37e",
    "python/tests/acceptance/n2_arms_cut8.py": "55b6de7",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba",
    "python/tests/acceptance/n2_arms_cut10.py": "22461e9",
    "python/tests/acceptance/n2_arms_cut11.py": "f0e65a6",
}
# n2_arms_cut3.py stays unpinned, as cut 11 left it: tests/test_n2.py audits
# it live, and cut 12's K5 arm holds its G4 anchor line byte-identical.

PRIOR_ARMS = (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS, *CUT9_ARMS, *CUT10_ARMS, *CUT11_ARMS)


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    root = tmp_path_factory.mktemp("n2-cut12")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], root / f"arm{pair[0]}"),
                enumerate(CUT12_ARMS),
            )
        )


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason
            + "\n"
            + "\n".join(f"  {finding.arm.label}\n    {finding.detail}" for finding in offending)
        )


class TestEveryCut12ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-12 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-12 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-12 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-12 sabotages no longer match exactly once:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-12 check passes on the real package",
            sabotage=CUT12_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT12_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


def declared_rows() -> tuple[str, ...]:
    return tuple(arm.row for arm in CUT12_ARMS)


class TestTheDeclarationTable:
    def test_the_declared_arms_are_unique_and_number_fifty(self):
        rows = declared_rows()
        assert len(rows) == len(set(rows)) == len(CUT12_ARMS) == 50

    def test_the_labeled_units_appear_in_declaration_order(self):
        labeled = [unit_of(row) for row in declared_rows() if row.startswith("K")]
        assert tuple(dict.fromkeys(labeled)) == LABELED_UNITS

    def test_the_frozen_cut_states_the_same_accounting(self):
        flattened = re.sub(r"\s+", " ", FROZEN_CUT.read_text(encoding="utf-8"))
        total = re.search(
            r"\*\*(\d+) selected \+ (\d+) labeled = (\d+) declaration units\*\*",
            flattened,
        )
        assert total is not None
        assert tuple(map(int, total.groups())) == (19, 5, 24)
        pairs = re.search(r"Selected units: ((?:[A-Z]+\d+ \d+(?:, )?)+)", flattened)
        assert pairs is not None
        assert {
            row: int(count) for row, count in re.findall(r"([A-Z]+\d+) (\d+)", pairs.group(1))
        } == ROW_UNITS

    def test_the_frozen_cut_names_the_commit_this_audit_reads(self):
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT12_FREEZE_COMMIT, "HEAD"],
            check=False,
        )
        assert completed.returncode == 0

    def test_every_arm_has_one_source_mutation_and_exact_check_nodes(self):
        package = Path(science_root.__file__).resolve().parent
        for arm in CUT12_ARMS:
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

    def test_every_check_lives_in_a_cut12_file(self):
        assert {check.split("::")[0] for arm in CUT12_ARMS for check in arm.checks} == {
            "acceptance/test_successor_admission_acceptance.py",
            "test_intent_evidence.py",
            "test_intent_reduce.py",
            "test_record_capture.py",
            "test_spec.py",
            "test_succession.py",
            "test_succession_errors.py",
        }


class TestNoPriorCutDeclarationIsRehomedOrEdited:
    def test_the_frozen_prior_declaration_files_are_byte_identical(self):
        for path, pin in FROZEN_PRIOR_CUT_FILES.items():
            completed = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
                check=False,
            )
            assert completed.returncode == 0, f"{path} moved since {pin}"

    def test_no_cut12_arm_claims_a_check_a_prior_cut_declared(self):
        prior = {check for arm in (*PRIOR_ARMS, *CUT3_ARMS) for check in arm.checks}
        for arm in CUT12_ARMS:
            allowed = set(CO_CITED.get(arm.row, ()))
            claimed = set(arm.checks) & prior
            assert claimed <= allowed, f"{arm.row} claims a prior cut's check: {sorted(claimed - allowed)}"

    def test_the_co_cited_checks_are_cut_3s_and_stand_beside_a_cut12_check(self):
        cut3_checks = {check for arm in CUT3_ARMS for check in arm.checks}
        for row, cited in CO_CITED.items():
            arm = next(arm for arm in CUT12_ARMS if arm.row == row)
            assert set(cited) <= cut3_checks
            assert set(arm.checks) - set(cited), f"{row} cites only prior checks"

    def test_the_k_prefix_names_no_frozen_prior_guarantee_unit(self):
        prior = {arm.row for arm in PRIOR_ARMS if not arm.row.startswith(("J", "K"))}
        assert not prior.intersection(LABELED_UNITS)


def test_the_partition_accounts_exactly_the_24_frozen_units() -> None:
    assert ROW_UNITS == {"G4": 14, "R12": 2, "L7": 3}
    assert LABELED_UNITS == tuple(f"K{number}" for number in range(1, 6))
    expected = (
        {f"G4u{number}" for number in range(1, 15)}
        | {"R12u1", "R12u2", "L7u14", "L7u15", "L7u16"}
        | set(LABELED_UNITS)
    )
    assert {unit_of(arm.row) for arm in CUT12_ARMS} == expected
