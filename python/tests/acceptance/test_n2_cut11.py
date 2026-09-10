"""Cut 11's declaration accounting, N2 audit, and lettered-arm partition."""

from __future__ import annotations

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from n2_arms import Arm, Sabotage
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import CUT7_ARMS
from n2_arms_cut8 import CUT8_ARMS
from n2_arms_cut9 import CUT9_ARMS
from n2_arms_cut10 import CUT10_ARMS
from n2_arms_cut11 import (
    ATOMS_CITATIONS_BY_UNIT,
    CO_PASSING_INDEPENDENCE,
    CUT11_ARMS,
    LABELED_UNITS,
    ROW_UNITS,
    unit_of,
)
from test_n2 import FAILED, PASSED, MalformedArm, _run_check, _sabotage, audit, baseline
from test_n2_cut7 import assert_cut5_matcher_migration

import beliefs.root as science_root

# Live matcher migration, 2026-09-07: frozen declarations above stay byte-exact.
# The same sabotages now target guarded publication and compiled stamp coverage.
_LIVE_SABOTAGES = {
    "J3a": Sabotage(
        "session/writer.py",
        before="        authority = scoped_authority(required, self.actor)\n",
        after="        authority = Authority(self._ceiling, self.actor)\n",
    ),
    "J7b": Sabotage(
        "boundary.py",
        before="        reason = port.execute_fulfilling_guarded(plan, fulfills, guard=acquisition_guard(result.run), fallback=_fallback)\n",
        after="        port.execute(plan)\n        reason = None\n",
    ),
    "J9a": Sabotage(
        "stored.py",
        before="    {name: kind.covered for name, kind in _WORLD.items() if kind.domain is not None}\n",
        after='    {name: tuple(key for key in kind.covered if name != "run" or key != RUN_CLOSURE_FACET) for name, kind in _WORLD.items() if kind.domain is not None}\n',
    ),
}
CUT11_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT11_ARMS
)

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-27-conformance-cut-11.md"
CUT11_FREEZE_COMMIT = "9711886"
RENAME_COMMIT = "5a02ca2"
"""The whole-repo science→beliefs mechanical rename (ledger R7). Re-pins a
file whose only post-freeze edit was that rename's import strings."""

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "1e92471",  # exact R20 matcher amendment, validated below
    "python/tests/n2_arms_cut6.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut7.py": "117f37e",
    "python/tests/acceptance/n2_arms_cut8.py": RENAME_COMMIT,
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba",
    "python/tests/acceptance/n2_arms_cut10.py": RENAME_COMMIT,
}
# n2_arms_cut3.py is deliberately absent: Task 4 rebased its T2 replay arm
# onto the boundary gate, and the ordinary tests/test_n2.py audits it live.


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    root = tmp_path_factory.mktemp("n2-cut11")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], root / f"arm{pair[0]}"),
                enumerate(CUT11_ARMS),
            )
        )


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason
            + "\n"
            + "\n".join(
                f"  {finding.arm.label}\n    {finding.detail}" for finding in offending
            )
        )


class TestEveryCut11ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-11 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-11 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-11 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-11 sabotages no longer match exactly once:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-11 check passes on the real package",
            sabotage=CUT11_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT11_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


def declared_rows() -> tuple[str, ...]:
    return tuple(arm.row for arm in CUT11_ARMS)


class TestTheDeclarationTable:
    def test_the_declared_arms_are_unique_and_number_sixty_six(self):
        # 12 armed L7 units (u5 is a citation) + 3 extra L7u2 members,
        # plus 13 J units and 38 extra sub-arms = 66 lettered arms.
        rows = declared_rows()
        assert len(rows) == len(set(rows)) == len(CUT11_ARMS) == 66

    def test_the_labeled_units_appear_in_declaration_order(self):
        labeled = [unit_of(row) for row in declared_rows() if row.startswith("J")]
        assert tuple(dict.fromkeys(labeled)) == LABELED_UNITS

    def test_the_frozen_cut_states_the_same_accounting(self):
        flattened = re.sub(r"\s+", " ", FROZEN_CUT.read_text(encoding="utf-8"))
        total = re.search(
            r"\*\*(\d+) selected \+ (\d+) labeled = (\d+) declaration units\*\*",
            flattened,
        )
        assert total is not None
        assert tuple(map(int, total.groups())) == (13, 13, 26)
        pairs = re.search(r"Selected units: ((?:[A-Z]+\d+ \d+(?:, )?)+)", flattened)
        assert pairs is not None
        assert {
            row: int(count)
            for row, count in re.findall(r"([A-Z]+\d+) (\d+)", pairs.group(1))
        } == ROW_UNITS

    def test_the_frozen_cut_names_the_commit_this_audit_reads(self):
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "merge-base",
                "--is-ancestor",
                CUT11_FREEZE_COMMIT,
                "HEAD",
            ],
            check=False,
        )
        assert completed.returncode == 0

    def test_every_arm_has_one_source_mutation_and_exact_check_nodes(self):
        package = Path(science_root.__file__).resolve().parent
        for arm in CUT11_ARMS:
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

    def test_every_check_lives_in_a_cut11_file(self):
        assert {check.split("::")[0] for arm in CUT11_ARMS for check in arm.checks} == {
            "acceptance/test_intent_boundary_acceptance.py",
            "test_consumer_agreement.py",
            "test_identity_decode.py",
            "test_intent_evidence.py",
            "test_intent_gate.py",
            "test_intent_reduce.py",
            "test_operation_port.py",
            "test_record_capture.py",
            "test_report.py",
            "test_run_persistence.py",
            "test_runrecord.py",
            "test_world_arrival.py",
            "test_world_log_audit.py",
            "test_world_log_evaluator.py",
        }


class TestNoPriorCutDeclarationIsRehomedOrEdited:
    def test_the_frozen_prior_declaration_files_are_byte_identical(self):
        assert_cut5_matcher_migration(REPO_ROOT)
        for path, pin in FROZEN_PRIOR_CUT_FILES.items():
            completed = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
                check=False,
            )
            assert completed.returncode == 0, f"{path} moved since {pin}"

    def test_no_cut11_arm_claims_a_check_a_prior_cut_declared(self):
        prior = {
            check
            for arm in (
                *CUT5_ARMS,
                *CUT6_ARMS,
                *CUT7_ARMS,
                *CUT8_ARMS,
                *CUT9_ARMS,
                *CUT10_ARMS,
            )
            for check in arm.checks
        }
        ours = {check for arm in CUT11_ARMS for check in arm.checks}
        assert not prior & ours

    def test_the_j_prefix_names_no_frozen_prior_guarantee_unit(self):
        # J labels are cut-local (cut 10 spent its own J1–J11); the collision
        # that must never happen is with a prior cut's guarantee-named unit.
        prior = {
            arm.row
            for arm in (
                *CUT5_ARMS,
                *CUT6_ARMS,
                *CUT7_ARMS,
                *CUT8_ARMS,
                *CUT9_ARMS,
                *CUT10_ARMS,
            )
            if not arm.row.startswith("J")
        }
        assert not prior.intersection(LABELED_UNITS)


def test_the_partition_accounts_exactly_the_26_frozen_units() -> None:
    assert ROW_UNITS == {"L7": 13}
    assert LABELED_UNITS == tuple(f"J{number}" for number in range(1, 14))
    arm_units = {unit_of(arm.row) for arm in CUT11_ARMS}
    citation_units = set(ATOMS_CITATIONS_BY_UNIT)
    assert not arm_units & citation_units
    expected = {f"L7u{number}" for number in range(1, 14)} | {
        f"J{number}" for number in range(1, 14)
    }
    assert arm_units | citation_units == expected
    assert citation_units == {"L7u5"}


def test_the_citation_units_corroborating_checks_are_collected() -> None:
    collected = subprocess.run(
        [
            "uv",
            "run",
            "--frozen",
            "pytest",
            "--collect-only",
            "-q",
            "tests/acceptance/test_intent_boundary_acceptance.py::test_u5_raced_appends_serialize_into_one_chain",
        ],
        cwd=REPO_ROOT / "python",
        capture_output=True,
        text=True,
        check=False,
    )
    assert collected.returncode == 0


def _j3a_independence(arm: Arm, workspace: Path) -> tuple[int, int]:
    package = _sabotage(arm, workspace)
    assert package is not None
    failing = _run_check(
        "test_operation_port.py::test_oversized_postimage_refuses_before_any_write", package
    ).returncode
    passing = _run_check(
        "test_operation_port.py::test_non_port_writes_are_unaffected_by_the_ceiling", package
    ).returncode
    return failing, passing


def test_j3a_writer_ceiling_fails_while_the_non_port_write_passes(tmp_path):
    arm = next(arm for arm in CUT11_ARMS if arm.row == "J3a")
    assert CO_PASSING_INDEPENDENCE["J3a"] == (
        "test_operation_port.py::test_non_port_writes_are_unaffected_by_the_ceiling",
    )
    failing, passing = _j3a_independence(arm, tmp_path / "j3a")
    assert failing == FAILED
    assert passing == PASSED
