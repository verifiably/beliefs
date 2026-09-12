"""Every arm a live guard audits still names a line the kernel has.

An N2 arm's sabotage is a `before` block pinned verbatim to kernel source. When the source
moves, the block matches nothing, the mutation does nothing, and the arm scores `sound`
while asserting nothing — `test_n2.py`'s `stale` finding. The audits that report it live
under `tests/acceptance`, which `addopts` ignores, so between discharges staleness
accumulates unreported: eight arms were found stale after a whole slice, and the live
guards had to be re-targeted by hand (`_LIVE_SABOTAGES`) before the next cut could run.

This module is the portable measurement. It reads what each guard audits — the
re-targeted tuple, against the tree the guard pins — and holds it to the rule every
discharge applies: a sabotage occurs exactly once, or the arm is malformed. Cited-not-run
guards are evidence, not machinery (`docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`
§2), so their staleness is recorded in the registry and held to, never repaired.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import arm_staleness
import cited_not_run
import frozen_guards
import pytest
from n2_arms import ARMS, STALE_BY_CONSTRUCTION
from test_n2 import PORTABLE_ARMS

REPO_ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE = REPO_ROOT / "python" / "tests" / "acceptance"


@pytest.fixture(scope="module")
def git_checkout() -> None:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-dir"],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        pytest.skip("a historical tree is read through git")


def test_the_detector_reports_a_sabotage_the_tree_has_outgrown() -> None:
    """The detector's own proof: an arm stale by construction is reported, and a live one
    beside it is not — so a clean sweep below means the arms are clean, not the reader blind."""
    stale = arm_staleness.stale_arms(
        "by-construction", (ARMS[0], STALE_BY_CONSTRUCTION), arm_staleness.working_tree(REPO_ROOT)
    )

    assert [arm.key for arm in stale] == [f"{STALE_BY_CONSTRUCTION.row}[1]"]
    assert stale[0].matches == 0


def test_a_module_the_tree_no_longer_has_is_stale_not_an_error() -> None:
    """Cut 6's `world.py` became a package: an arm naming it must read as stale, with the
    absence said, rather than as a reader crash that hides every other finding."""
    read = arm_staleness.working_tree(REPO_ROOT)

    assert read("world.py") is None
    assert read("world/__init__.py") is not None
    assert read("core/registry.py", "nodes") is not None
    assert read("core/registry.py") is None  # a nodes module is not a beliefs module


def test_the_portable_harness_arms_apply_exactly_once() -> None:
    """Cuts 1–3 and 26, which `test_n2.py` audits and the fast loop ignores. Cut 26's arms
    are read from the installed `nodes` tree."""
    stale = arm_staleness.stale_arms("test_n2.py", PORTABLE_ARMS, arm_staleness.working_tree(REPO_ROOT))

    assert stale == ()


def test_every_arm_a_live_guard_audits_applies_exactly_once(git_checkout) -> None:
    """The gate. A live guard's arms are machinery, and the tuple it audits — after any
    `_LIVE_SABOTAGES` re-targeting, against the tree it pins — must match the kernel
    today. When a slice moves a pinned line, this is the test that goes red the same day,
    and the fix is the guard's re-targeting table: the arm, never the source."""
    stale = [
        f"{arm.guard}::{arm.key} in {arm.module} ({'absent' if arm.matches is None else f'{arm.matches} matches'})"
        for guard in frozen_guards.live_guards(REPO_ROOT)
        for arm in arm_staleness.stale_arms(
            guard.name,
            arm_staleness.audited_arms(guard, repo_root=REPO_ROOT),
            arm_staleness.audited_tree(guard, repo_root=REPO_ROOT),
        )
    ]

    assert stale == [], "a live guard audits a sabotage the kernel has moved from under; re-target it in the guard"


def test_cut_6_is_clean_only_against_the_tree_it_pins(git_checkout) -> None:
    """The historical read is load-bearing, not a courtesy: against the working tree cut
    6's `world.py` arms match nothing, and a sweep that read the working tree for every
    guard would either fail on cut 6 forever or be taught to skip it."""
    guard = ACCEPTANCE / "test_n2_cut6.py"
    arms = arm_staleness.audited_arms(guard, repo_root=REPO_ROOT)

    against_working_tree = arm_staleness.stale_arms(guard.name, arms, arm_staleness.working_tree(REPO_ROOT))
    against_pinned_tree = arm_staleness.stale_arms(
        guard.name, arms, arm_staleness.audited_tree(guard, repo_root=REPO_ROOT)
    )

    assert {arm.module for arm in against_working_tree} == {"world.py"}
    assert against_pinned_tree == ()


def test_every_arm_the_registry_records_as_stale_really_is_and_no_other(git_checkout) -> None:
    """A cited-not-run guard's declarations are the bytes that produced the discharge
    later cuts cite; the tree moving from under them is a fact to record, not a defect to
    repair. The registry says which arms, and this holds it to exactly those — an entry
    for an arm that still applies would excuse a staleness nobody measured, and a stale
    arm the registry omits is the silent accumulation this module exists to end."""
    for module, entry in cited_not_run.CITED_NOT_RUN.items():
        guard = ACCEPTANCE / module
        stale = arm_staleness.stale_arms(
            module, arm_staleness.declared_arms(guard, repo_root=REPO_ROOT), arm_staleness.working_tree(REPO_ROOT)
        )

        assert {arm.key for arm in stale} == set(entry.stale_arms), module


def test_a_live_guard_re_targets_every_declaration_the_tree_has_outgrown(git_checkout) -> None:
    """The mechanism the gate relies on, stated once.

    A live guard's declaration file is frozen under later cuts' pins, so when the kernel
    moves the guard does not edit it: it re-targets the row in `_LIVE_SABOTAGES` and
    audits the re-targeted tuple. This holds the two readings together — every declared
    arm the working tree has outgrown is a row the guard re-targets. Without it a guard
    could be clean above because its override table happens to cover today's drift while
    a declaration nobody re-read has gone stale beside it.
    """
    uncovered: list[str] = []
    for guard in frozen_guards.live_guards(REPO_ROOT):
        if guard.name == "test_n2_cut6.py":
            continue  # audits a pinned historical tree; its declarations are not meant to match today's
        re_targeted = arm_staleness.re_targeted_rows(guard, repo_root=REPO_ROOT)
        for arm in arm_staleness.stale_arms(
            guard.name, arm_staleness.declared_arms(guard, repo_root=REPO_ROOT), arm_staleness.working_tree(REPO_ROOT)
        ):
            row = arm.key.partition("[")[0]
            if row not in re_targeted:
                uncovered.append(f"{guard.name}::{arm.key}")

    assert uncovered == []
