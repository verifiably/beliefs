"""Cut 10's declaration accounting, N2 audit, and source obligations."""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from n2_arms import Arm
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import CUT7_ARMS
from n2_arms_cut8 import CUT8_ARMS
from n2_arms_cut9 import CUT9_ARMS
from n2_arms_cut10 import (
    ATOMS_CITATIONS_BY_UNIT,
    CUT10_ARMS,
    LABELED_UNITS,
    ROW_UNITS,
)
from test_n2 import FAILED, PASSED, MalformedArm, _run_check, _sabotage, audit, baseline

import science.root as science_root

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-24-conformance-cut-10.md"
CUT10_FREEZE_COMMIT = "5e0266f"

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut6.py": "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e",
    "python/tests/n2_arms_cut7.py": "117f37e",
    "python/tests/acceptance/n2_arms_cut8.py": "55b6de7",
    "python/tests/acceptance/n2_arms_cut9.py": "7a9fec8",
}


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    root = tmp_path_factory.mktemp("n2-cut10")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], root / f"arm{pair[0]}"),
                enumerate(CUT10_ARMS),
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


class TestEveryCut10ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-10 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-10 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-10 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-10 sabotages no longer match exactly once:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-10 check passes on the real package",
            sabotage=CUT10_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT10_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


def declared_units() -> tuple[str, ...]:
    return tuple(arm.row for arm in CUT10_ARMS)


class TestTheDeclarationTable:
    def test_the_declared_units_are_unique_and_number_thirty_one(self):
        units = declared_units()
        assert len(units) == len(set(units)) == len(CUT10_ARMS) == 31

    def test_the_selected_partition_matches_the_frozen_accounting(self):
        selected = [unit for unit in declared_units() if not unit.startswith("J")]
        labeled = [unit for unit in declared_units() if unit.startswith("J")]
        assert len(selected) == 20
        assert tuple(labeled) == LABELED_UNITS
        assert dict(Counter(unit.split("u")[0] for unit in selected)) == ROW_UNITS

    def test_the_frozen_cut_states_the_same_accounting(self):
        flattened = re.sub(r"\s+", " ", FROZEN_CUT.read_text(encoding="utf-8"))
        total = re.search(
            r"\*\*(\d+) selected \+ (\d+) labeled = (\d+) declaration units\*\*",
            flattened,
        )
        assert total is not None
        assert tuple(map(int, total.groups())) == (20, 11, 31)
        pairs = re.search(r"Selected units by row: ((?:[A-Z]+\d+ \d+(?:, )?)+)", flattened)
        assert pairs is not None
        assert {
            row: int(count)
            for row, count in re.findall(r"([A-Z]+\d+) (\d+)", pairs.group(1))
        } == ROW_UNITS

    def test_the_frozen_cut_names_the_commit_this_audit_reads(self):
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT10_FREEZE_COMMIT, "HEAD"],
            check=False,
        )
        assert completed.returncode == 0

    def test_every_arm_has_one_source_mutation_and_exact_check_nodes(self):
        package = Path(science_root.__file__).resolve().parent
        for arm in CUT10_ARMS:
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

    def test_every_check_lives_in_a_cut10_file(self):
        assert {check.split("::")[0] for arm in CUT10_ARMS for check in arm.checks} == {
            "test_holdings_adapter.py",
            "test_holdings_boundary.py",
            "test_holdings_capture.py",
            "test_holdings_receipt.py",
            "test_holdings_records.py",
            "test_holdings_reduce.py",
            "test_holdings_stored.py",
            "test_holdings_windows.py",
        }


class TestTheAtomsCitationsAreMetadataNotChecks:
    def test_every_atoms_certified_unit_cites_the_design_and_test_file(self):
        assert set(ATOMS_CITATIONS_BY_UNIT) == {
            "H1u1", "H1u3", "H4u2", "L10u1", "L10u2", "J1", "J2"
        }
        declared = set(declared_units())
        checks = {check for arm in CUT10_ARMS for check in arm.checks}
        for unit, citations in ATOMS_CITATIONS_BY_UNIT.items():
            assert unit in declared
            assert any(
                citation.startswith("docs/2026-08-24-holdings-read-and-evidence-commands-design.md §")
                for citation in citations
            )
            tests = [citation for citation in citations if citation.startswith("python/tests/")]
            assert tests
            assert all(
                re.fullmatch(r"python/tests/test_[A-Za-z0-9_]+\.py::test_[A-Za-z0-9_]+", citation)
                for citation in tests
            )
            assert not checks.intersection(citations)


class TestNoPriorCutDeclarationIsRehomedOrEdited:
    def test_the_frozen_prior_declaration_files_are_byte_identical(self):
        for path, pin in FROZEN_PRIOR_CUT_FILES.items():
            completed = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
                check=False,
            )
            assert completed.returncode == 0, f"{path} moved since {pin}"

    def test_no_cut10_arm_claims_a_check_a_prior_cut_declared(self):
        prior = {
            check
            for arm in (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS, *CUT9_ARMS)
            for check in arm.checks
        }
        ours = {check for arm in CUT10_ARMS for check in arm.checks}
        assert not prior & ours

    def test_the_j_prefix_names_no_frozen_prior_unit(self):
        prior = {
            arm.row for arm in (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS, *CUT9_ARMS)
        }
        assert not prior.intersection(LABELED_UNITS)


G9_CHECK = "test_holdings_adapter.py::test_a_different_digest_never_promotes_on_presence"
G9_COPASSING = (
    "test_holdings_adapter.py::test_adapter_absence_is_refused_by_the_g2b_admission_gate",
    "test_holdings_adapter.py::test_an_active_absent_ends_promotion",
    "test_holdings_records.py::test_url_locator_refuses_with_the_named_deferral",
)


def _g9_independence(arm: Arm, workspace: Path) -> tuple[int, tuple[int, ...]]:
    package = _sabotage(arm, workspace)
    assert package is not None
    failed = _run_check(G9_CHECK, package).returncode
    co_passing = tuple(_run_check(check, package).returncode for check in G9_COPASSING)
    return failed, co_passing


def test_g9_fails_while_g2b_r5_and_r10_pass_against_one_sabotaged_installation(tmp_path):
    arm = next(arm for arm in CUT10_ARMS if arm.row == "G9u1")
    failed, co_passing = _g9_independence(arm, tmp_path / "g9")
    assert failed == FAILED
    assert co_passing == (PASSED, PASSED, PASSED)


TESTS = Path(__file__).resolve().parents[1]

_OBLIGATION_SOURCES: tuple[tuple[str, str, str], ...] = (
    ("§5.1 fabricated records decode", "test_holdings_reduce.py", "stored.holdings_observation_value(Node.model_validate(json.loads(canonical)))"),
    ("§5.2 H2u1 no references", "test_holdings_reduce.py", 'assert all(not facet["supersedes"]'),
    ("§5.2 H2u1 only timestamps differ", "test_holdings_reduce.py", "assert normalized_first == normalized_swapped"),
    ("§5.3 H2u4 boundary append", "test_holdings_windows.py", "write(killed, location, b\"replacement\")"),
    ("§5.3 H2u4 unresolved inspected chain", "test_holdings_reduce.py", "view.pending == ((\"tx-pending\", registration_ref),)"),
    ("§5.4 H3u3 same corpus states", "test_holdings_receipt.py", "old_receipt.coverage[0][1] == new_receipt.coverage[0][1]"),
    ("§5.5 H4u2 standing unchanged", "test_holdings_boundary.py", "standing.record.identity() == standing_identity"),
    ("§5.6 L10u1 lifecycle", "test_holdings_boundary.py", "read_lifecycle_state(cold) is LifecycleState.METADATA_LESS"),
    ("§5.6 L10u2 lifecycle", "test_holdings_boundary.py", "read_lifecycle_state(replica) is LifecycleState.READ_ONLY_UNSERVICEABLE"),
    ("§5.7 G9 same installation", "acceptance/test_n2_cut10.py", "co_passing == (PASSED, PASSED, PASSED)"),
    ("§5.7 G9 G2b gate", "test_holdings_adapter.py", "result = admit(assessment, run, {address: answer.observations}, (verification,))"),
    ("§5.8 L7u2 boundary append", "test_holdings_boundary.py", "test_a_kill_between_intent_and_mutation_leaves_the_intent_unmatched"),
    ("§5.9 count claims", "acceptance/test_n2_cut10.py", "results record quote pytest's summary under pipefail"),
    ("§6 H1u2 undamaged", "test_holdings_boundary.py", "this construction keeps the store undamaged throughout"),
    ("§6 H2u3 stored decode", "test_holdings_reduce.py", "stored.holdings_observation_value(Node.model_validate(json.loads(canonical)))"),
    ("§6 L10 acts boundary", "test_holdings_boundary.py", "result = recheck(ctx, StoreLocator(store_id, \"held.bin\"))"),
    ("§6 G9 adapter seam", "acceptance/test_n2_cut10.py", "_g9_independence(arm, tmp_path / \"g9\")"),
    ("§6 L7u1 committed", "test_holdings_windows.py", "entry.fulfills == intent"),
)

# §5.9: Task 11's results record quote pytest's summary under pipefail; the
# acceptance runner owns the command, while this task keeps the obligation named.


class TestTheObligationsAreCarriedInSource:
    @pytest.mark.parametrize(
        ("reference", "module", "needle"),
        _OBLIGATION_SOURCES,
        ids=[row[0] for row in _OBLIGATION_SOURCES],
    )
    def test_the_named_fixture_assertion_is_present(self, reference, module, needle):
        source = (TESTS / module).read_text(encoding="utf-8")
        assert needle in source, f"{reference}: {module} no longer carries its obligation"

    def test_l7_nonqualifying_cases_are_the_three_frozen_constructions(self):
        source = (TESTS / "test_holdings_windows.py").read_text(encoding="utf-8")
        assert '["wrong-location", "wrong-token", "no-observation"]' in source
        body = source.split("def test_nonqualifying_fulfillments_are_committed")[1].split("def ")[0]
        assert "inspect_registered" in body
        assert "Read" not in body
