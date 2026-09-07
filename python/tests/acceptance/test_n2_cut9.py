"""Cut 9's declaration accounting, its N2 audit, and its declaration-time obligations.

Structure mirrors `test_n2_cut8.py`: the arms are data in `n2_arms_cut9.py`,
this module reconciles them against the frozen cut
(`docs/designs/2026-08-23-conformance-cut-9.md`, frozen at `0977bde`), audits
every arm in both directions through the shared harness, and enforces the
cut's §5 declaration-time obligations and §6 freeze obligations as checks.

**Cut 8 is cited, not run, on this tree.** Task 4 of the root-lifecycle plan
deleted the shape-only store refusal cut 8's label 6 and store-refusal arms
certify, so those declarations fail on the current tree **by design** (the
execution ledger's R15). Cut 8's discharge stands as its frozen results record
(`docs/plans/2026-08-22-conformance-cut-8-results.md`); its declaration files
are pinned byte-identical below, exactly as every prior cut's are, and cut 9's
store units are the successor certification.
"""

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
from n2_arms_cut9 import (
    ATOMS_CITATIONS_BY_UNIT,
    CUT9_ARMS,
    LABELED_UNITS,
    ROW_UNITS,
)
from test_n2 import MalformedArm, audit, baseline
from test_n2_cut7 import assert_cut5_matcher_migration

import beliefs.root as science_root

WORKERS = 8

REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-23-conformance-cut-9.md"

CUT9_FREEZE_COMMIT = "0977bde"
"""The commit the frozen cut names for itself; §2's boundary is stated there."""

CUT8_BANK_COMMIT = "5a02ca2"
"""Where cut 8's declarations and runner last moved: the banking commit that
discharged it, re-pinned across the science→beliefs rename (ledger R7) — the
content is cut 8's frozen declarations verbatim, corrected only for the
package rename's import strings. `test_n2_cut8.py` no longer shares this
pin: R7's transitive fixpoint sweep (fix round 4) further edited it — to
carry that same fixpoint into cut 8's own table — after this commit, so it
needs its own, later pin below."""

CUT8_AUDIT_REPIN_COMMIT = "d0206c8"
"""Where `test_n2_cut8.py` itself last moved: fix round 3's completion of
R7's re-pin sweep, correcting *its own* `FROZEN_PRIOR_CUT_FILES` table for
the same rename. An authorized, disclosed edit, not a drift to chase — but
this table pins the file's bytes, so the pin has to follow to the commit
that made them (ledger R7's transitive-fixpoint principle, fix round 4)."""

CUT6_SOURCE_COMMIT = "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e"
CUT8_FREEZE_COMMIT = "117f37e"
RENAME_COMMIT = "5a02ca2"
"""The whole-repo science→beliefs mechanical rename (ledger R7). Re-pins a
file whose only post-freeze edit was that rename's import strings."""

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "1e92471",  # exact R20 matcher amendment, validated below
    "python/tests/n2_arms_cut6.py": CUT6_SOURCE_COMMIT,
    "python/tools/cut5_acceptance.py": RENAME_COMMIT,
    "python/tools/cut6_acceptance.py": RENAME_COMMIT,
    "python/tests/n2_arms_cut7.py": CUT8_FREEZE_COMMIT,
    "python/tools/cut7_acceptance.py": RENAME_COMMIT,
    # Cut 8's own declarations, audit, and runner: deliberately stale on this
    # tree (ledger R15) and exactly as frozen — staleness is a fact about the
    # tree, never a license to edit the declaration.
    "python/tests/acceptance/n2_arms_cut8.py": CUT8_BANK_COMMIT,
    "python/tests/acceptance/test_n2_cut8.py": CUT8_AUDIT_REPIN_COMMIT,
    "python/tools/cut8_acceptance.py": CUT8_BANK_COMMIT,
}
"""Each prior-cut surface and the commit whose content it must still hold."""


# --- the N2 audit -------------------------------------------------------------


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    """The 30 arms, audited against the present tree in both directions."""
    root_path = tmp_path_factory.mktemp("n2-cut9")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(lambda pair: audit(pair[1], root_path / f"arm{pair[0]}"), enumerate(CUT9_ARMS))
        )


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason + "\n" + "\n".join(f"  {finding.arm.label}\n    {finding.detail}" for finding in offending)
        )


class TestEveryCut9ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-9 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-9 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-9 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-9 sabotages no longer match exactly once:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-9 check resolves and passes against the real package",
            sabotage=CUT9_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT9_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


# --- the declaration table's own discipline ------------------------------------


def declared_units() -> tuple[str, ...]:
    return tuple(arm.row for arm in CUT9_ARMS)


class TestTheDeclarationTable:
    def test_the_declared_units_are_unique_and_number_thirty(self):
        units = declared_units()
        assert len(units) == len(set(units))
        assert len(units) == 30
        assert len(CUT9_ARMS) == 30

    def test_the_selected_partition_matches_the_frozen_accounting(self):
        selected = [unit for unit in declared_units() if not unit.startswith("V")]
        labeled = [unit for unit in declared_units() if unit.startswith("V")]
        assert len(selected) == 19
        assert tuple(labeled) == LABELED_UNITS
        per_row = Counter(unit.split("u")[0] for unit in selected)
        assert dict(per_row) == ROW_UNITS

    def test_the_frozen_cut_states_the_same_accounting(self):
        text = FROZEN_CUT.read_text(encoding="utf-8")
        flattened = re.sub(r"\s+", " ", text)
        total = re.search(
            r"\*\*(\d+) selected \+ (\d+) labeled = (\d+) declaration units\*\*", flattened
        )
        assert total is not None
        assert tuple(map(int, total.groups())) == (19, 11, 30)
        pairs = re.search(
            r"Selected units by row: ((?:[A-Z]+\d+ \d+(?:, )?)+)", flattened
        )
        assert pairs is not None
        stated = {
            row: int(count)
            for row, count in re.findall(r"([A-Z]+\d+) (\d+)", pairs.group(1))
        }
        assert stated == ROW_UNITS

    def test_every_arm_has_one_source_mutation_and_exact_check_nodes(self):
        for arm in CUT9_ARMS:
            assert arm.checks, arm.row
            assert len(arm.checks) == len(set(arm.checks)), arm.row
            assert arm.sabotage.before != arm.sabotage.after, arm.row
            assert arm.asserts.strip(), arm.row
            for check in arm.checks:
                parts = check.split("::")
                assert len(parts) >= 2, check
                assert parts[-1].startswith("test_"), check

    def test_every_sabotage_names_a_present_module_and_applies_exactly_once(self):
        package = Path(science_root.__file__).resolve().parent
        for arm in CUT9_ARMS:
            target = package / arm.sabotage.module
            assert target.is_file(), f"{arm.row}: {arm.sabotage.module} does not exist"
            source = target.read_text(encoding="utf-8")
            assert source.count(arm.sabotage.before) == 1, (
                f"{arm.row}: the sabotage pattern matches {source.count(arm.sabotage.before)} times in "
                f"{arm.sabotage.module}"
            )

    def test_every_check_lives_in_a_cut9_file(self):
        # Single-homing per this cut's table. Unlike cut 8's one-file-per-arm
        # rule, cut 9's frozen table crosses files inside three declarations
        # (W13 u2, D4, D6) — the declared homes below are the closed set, and
        # any node outside them has drifted.
        homes = {check.split("::")[0] for arm in CUT9_ARMS for check in arm.checks}
        assert homes == {
            "test_arrival_modes.py",
            "test_fork_acts.py",
            "test_lifecycle_wrappers.py",
            "test_restore_root.py",
            "test_store_root.py",
            "test_store_subjects.py",
        }


class TestTheAtomsCitationsAreMetadataNotChecks:
    def test_atoms_citations_are_metadata_not_checks(self):
        assert set(ATOMS_CITATIONS_BY_UNIT) == {
            "L10u4",
            "L10u5",
            "L10u7",
            "V1",
            "V2",
            "V3",
            "V4",
            "V5",
            "V6",
        }
        declared = set(declared_units())
        checks = {check for arm in CUT9_ARMS for check in arm.checks}
        for unit, citations in ATOMS_CITATIONS_BY_UNIT.items():
            assert unit in declared, unit
            assert citations, unit
            for citation in citations:
                assert re.fullmatch(
                    r"tests/test_lifecycle_commands\.py::test_[A-Za-z0-9_]+", citation
                ), citation
                assert citation not in checks, citation


class TestNoPriorCutDeclarationIsRehomedOrEdited:
    def test_the_frozen_prior_cut_files_are_byte_identical_to_their_pinned_versions(self):
        assert_cut5_matcher_migration(REPO_ROOT)
        for path, pin in FROZEN_PRIOR_CUT_FILES.items():
            completed = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
                check=False,
            )
            assert completed.returncode == 0, (
                f"{path} has moved since {pin}; cuts 5–8's declarations, runners and audits are frozen, "
                "and cut 9 edits none of them"
            )

    def test_no_cut9_arm_claims_a_check_a_prior_cut_declared(self):
        prior = {check for arm in (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS) for check in arm.checks}
        ours = {check for arm in CUT9_ARMS for check in arm.checks}
        assert not prior & ours

    def test_no_prior_cut_arm_claims_a_cut9_label(self):
        # Cut 9 re-numbers its selected units within rows cut 8 also read, so
        # an L-row unit id can collide with cut 8's as a *string* while naming
        # a different unit — the check-node overlap test above is what
        # enforces single-homing of the content. The labels take the V prefix
        # precisely so no labeled declaration ever collides across cuts.
        prior = {arm.row for arm in (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS, *CUT8_ARMS)}
        collisions = prior & set(declared_units())
        assert not {unit for unit in collisions if unit.startswith("V")}
        assert all(unit[0] == "L" or unit[0] == "W" for unit in collisions)


# --- §5's declaration-time obligations and §6's freeze obligations --------------
#
# The fixture assertions §5 items 2–8 require live inside the declared tests
# themselves; what is enforceable here without re-implementing them is that
# each named test still carries its obligation's assertion in source — the
# capability-boundary suite's source-scan pattern.

TESTS = Path(__file__).resolve().parents[1]

_OBLIGATION_SOURCES: tuple[tuple[str, str, str], ...] = (
    # (§ reference, test file, the assertion text the fixture must carry)
    ("§5.2 L6 u1 baseline-covered pre-log member", "test_fork_acts.py", "in no post-genesis entry"),
    ("§5.3 L6 u2 byte-difference and omission", "test_fork_acts.py", "assert rewritten != original_genesis_bytes"),
    (
        "§5.4 L4 u2 same subject, differing geneses",
        "test_fork_acts.py",
        "The fixture's obligations: same subject, differing geneses",
    ),
    (
        "§5.5 L10 u9 both roots metadata-less first",
        "test_restore_root.py",
        "The L10 u9 obligation: both roots are metadata-less first",
    ),
    ("§5 L2 u1 pending entry and no metadata", "test_lifecycle_wrappers.py", "the copy genuinely carries a pending"),
    ("§6 L10 u10 omission, never chain damage", "test_restore_root.py", "never chain\n        # damage"),
    (
        "§6 label-8 writable arm through register_root's own path",
        "test_arrival_modes.py",
        "The grant is register_root's own",
    ),
)


class TestTheObligationsAreCarriedInSource:
    @pytest.mark.parametrize(
        ("reference", "module", "needle"),
        _OBLIGATION_SOURCES,
        ids=[entry[0] for entry in _OBLIGATION_SOURCES],
    )
    def test_the_named_fixture_assertion_is_present(self, reference, module, needle):
        source = (TESTS / module).read_text(encoding="utf-8")
        assert needle in source, f"{reference}: {module} no longer carries its obligation"

    def test_the_l6_deletion_is_the_only_delta(self):
        # §6's second obligation: the anchored deletion interposes no other
        # mutation between the anchor and the deletion. The fixture derives
        # the anchor, unlinks the member, and audits — nothing else touches
        # the child between those acts.
        source = (TESTS / "test_fork_acts.py").read_text(encoding="utf-8")
        body = source.split("def test_l6_anchored_baseline_deletion_refutes")[1]
        body = body.split("def ")[0]
        assert "(child / member).unlink()" in body
        assert "write" not in body
        assert "executor" not in body
