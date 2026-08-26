"""N2 — every oracle row can fail, applied to cut 1's own selected arms.

The harness runs each declared arm twice: once unsabotaged, where its checks must
**pass**, and once with its sabotage applied, where they must **fail**. Both
directions are needed and neither is decoration.

* Without the first, a check that can never pass looks like a sound arm.
* Without the second, the arm asserts nothing about the property it names.

**One test function at a time, and only exit code 1 counts.** Every part of that
was learned by getting it wrong. Running an arm's checks in a single `pytest`
invocation and reading one exit code makes a failing check cover for a passing
one — three real arms in this table were carrying a check that passed under their
own sabotage, and the arm scored sound on the strength of the other. Splitting
the invocation is not enough either, because a **class node** is one invocation
over many tests wearing a node id, and reintroduces the same aggregation through
the check rather than the runner. And *"exited non-zero"* is not *"the check
failed"*: `pytest` exits **4** when it cannot collect the node id, so a sabotage
coarse enough to break the module's syntax, or a check that has been renamed
away, scores as a failing check while demonstrating only that unimportable code
does not import.

A sabotage is applied to a **copy** of the package, and the checks run in a
subprocess against it. Nothing writes to the working tree, which is what makes it
safe to run these concurrently and safe to interrupt — the hand-run matrices this
replaces mutated files in place and restored them in a `finally`, one `SIGINT`
away from leaving a sabotaged source on disk.

**Five findings, not one.** An arm can be `sound`, `vacuous` — every named check
passed under its own sabotage — `mixed` — some checks passed and some failed,
so half the arm asserts nothing while the passing half hides it — `uncollected`,
where a check never ran at all, or `stale`, where the sabotage no longer
matches the code it was written against. Staleness happened twice during this
build, and a stale sabotage is indistinguishable from a passing arm unless it
is looked for: the mutation silently does nothing, the checks pass, and the
harness reports the arm healthy. `mixed` is the defect three real cut-1 arms
actually had, found only once the verdict was taken over checks one at a time
rather than over a whole invocation. Each is malformed contract content in the
same way vacuity is, so each is reported the same way.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pytest
from n2_arms import (
    ARMS,
    CLASS_NODE_BY_CONSTRUCTION,
    CLASS_NODE_DISAGREEMENT,
    MIXED_BY_CONSTRUCTION,
    STALE_BY_CONSTRUCTION,
    UNCOLLECTED_BY_CONSTRUCTION,
    VACUOUS_BY_CONSTRUCTION,
    Arm,
    Sabotage,
)
from n2_arms_cut2 import CUT2_ARMS
from n2_arms_cut3 import CUT3_ARMS

PACKAGE = Path(__file__).resolve().parent.parent / "src" / "science"
TESTS = Path(__file__).resolve().parent
HARNESS = Path(__file__).name

WORKERS = 8

PASSED = 0
FAILED = 1
"""`pytest`'s two deciding exit codes, named because the rest do not decide.

`2`–`5` are interrupted, internal error, usage error and nothing-collected. None
of them is a verdict about the check: a node id that cannot be collected — either
because it was renamed away or because the sabotage broke the module it lives
in — is a **usage error**, and a usage error is not a failing test. They are the
same non-zero as `FAILED` to anything that only asks whether the run was clean.
"""


class MalformedArm(Exception):
    """An arm that does not do what an arm is for.

    N2's second clause: *construct a row whose check passes under sabotage and
    assert the row itself is reported as malformed contract content*. This is
    that report. It is deliberately not an assertion failure inside some test —
    the finding is about the **contract content**, not about the code under test,
    and a suite that could only say *"a test failed"* would file a defective row
    and a real regression under one heading.
    """


@dataclass(frozen=True)
class CheckRun:
    check: str
    returncode: int


@dataclass(frozen=True)
class Finding:
    arm: Arm
    verdict: str
    """`sound`, `vacuous`, `mixed`, `uncollected`, or `stale`."""

    detail: str = ""


def _run_check(check: str, package: Path | None) -> CheckRun:
    """Run one named check, optionally against a sabotaged copy of the package.

    One check per invocation, because the unit a verdict is taken over has to be
    the unit an arm names. An invocation carrying several node ids reports one
    exit code for all of them, and *"something in there failed"* is precisely the
    claim an arm must not be allowed to make.

    **The unit is a test function**, which is why having a `::` in it is not
    enough. A class node is a whole invocation wearing a node id: run
    `test_decode.py::TestM4TypedReferentsAndTheReceipt` under M4's first sabotage
    and one method fails while the rest pass, behind one class-level exit code —
    the aggregation defect this function exists to close, one level down. A
    **parametrized** id is where the rule stops, and deliberately: the parameters
    of one test function are its data, not separate assertions, so a check that
    fails on some rows of a vector and not others is a check that failed.
    """
    parts = check.split("::")
    if len(parts) < 2 or parts[0] == HARNESS or not parts[-1].startswith("test_"):
        # A check naming a directory, a module or a class runs whatever is under
        # it, and one naming this module re-enters the harness — whose every arm
        # invokes `pytest` again. That is a fork bomb rather than a weak arm, and
        # it is not hypothetical: it is what the first version of this harness's
        # own sabotage script did, and how this guard came to be written.
        raise MalformedArm(
            f"{check!r} does not name one test function outside {HARNESS}; a check must name the one test it means"
        )
    env = {"PATH": "/usr/bin:/bin", "HOME": str(Path.home())}
    for name in (
        "SCIENCE_CUT4_ROOT",
        "SCIENCE_CUT5_ROOT",
        "SCIENCE_CUT6_ROOT",
        "SCIENCE_CUT7_ROOT",
        "SCIENCE_CUT10_ROOT",
    ):
        if name in os.environ:
            env[name] = os.environ[name]
    if package is not None:
        env["PYTHONPATH"] = str(package.parent)
    # Node ids are declared relative to `tests/` and resolved to absolute paths
    # here, so an arm reads as the suite writes it and neither depends on where
    # the harness happened to be invoked from.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider", f"{TESTS}/{check}"],
        cwd=TESTS.parent,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return CheckRun(check, result.returncode)


def _sabotage(arm: Arm, into: Path) -> Path | None:
    """Copy the package into `into` and apply the arm's mutation. `None` if it does not apply."""
    package = into / "science"
    shutil.copytree(PACKAGE, package)
    target = package / arm.sabotage.module
    source = target.read_text(encoding="utf-8")
    if source.count(arm.sabotage.before) != 1:
        return None
    target.write_text(source.replace(arm.sabotage.before, arm.sabotage.after), encoding="utf-8")
    return package


def baseline(arm: Arm) -> Finding:
    """The other direction, and it is not a formality.

    A check that does not pass against the real package asserts nothing about
    what a sabotage does to it, because it was already red. The two directions
    overlap on a node id that has been renamed away — caught here as `unresolved`
    and under sabotage as `uncollected` — and diverge on a check that resolves
    and still fails, which only this direction can see.
    """
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        runs = list(pool.map(lambda check: _run_check(check, None), arm.checks))
    unresolved = [run for run in runs if run.returncode != PASSED]
    if unresolved:
        return Finding(
            arm,
            "unresolved",
            "\n".join(f"{run.check} exited {run.returncode} against the real package" for run in unresolved),
        )
    return Finding(arm, "resolved")


def audit(arm: Arm, workspace: Path) -> Finding:
    """One arm, one verdict, taken over its checks one at a time."""
    if not arm.checks:
        # Refused here rather than asserted over the table, because the table
        # assertion is not sabotageable: weakening `assert all(arm.checks ...)`
        # to `assert True` proves only that a deleted test does not run. An arm
        # naming no check runs nothing, and a verdict taken over nothing is
        # `sound` by the same vacuity the row exists to refuse.
        return Finding(arm, "stale", "an arm that names no check asserts nothing about the property it names")
    package = _sabotage(arm, workspace)
    if package is None:
        return Finding(
            arm,
            "stale",
            f"the sabotage does not apply to {arm.sabotage.module} exactly once — it was written against "
            "code that has since changed, and a mutation that does nothing scores as a passing arm",
        )
    runs = [_run_check(check, package) for check in arm.checks]
    survived = [run for run in runs if run.returncode == PASSED]
    undecided = [run for run in runs if run.returncode not in (PASSED, FAILED)]
    if survived or undecided:
        if survived and len(survived) == len(runs):
            verdict = "vacuous"  # every check survived
        elif survived:
            verdict = "mixed"  # some failed, some survived — a passing check hides a failing one
        else:
            verdict = "uncollected"
        return Finding(
            arm,
            verdict,
            "\n".join(
                [f"{run.check} passed with the sabotage applied" for run in survived]
                + [
                    f"{run.check} did not run — pytest exited {run.returncode}, which is not a failing check"
                    for run in undecided
                ]
            ),
        )
    return Finding(arm, "sound")


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple[Finding, ...]:
    """Every declared arm across cuts 1–3, audited once. Concurrent — each
    arm owns its own copy."""
    root = tmp_path_factory.mktemp("n2")
    all_arms = (*ARMS, *CUT2_ARMS, *CUT3_ARMS)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(all_arms)))


def _report(reason: str, findings: tuple[Finding, ...], verdict: str) -> None:
    offending = [f for f in findings if f.verdict == verdict]
    if offending:
        raise MalformedArm(reason + "\n" + "\n".join(f"  {f.arm.label}\n    {f.detail}" for f in offending))


class TestEveryArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report(
            "these arms have a check that passes under their own sabotage, which makes them malformed "
            "contract content rather than failing tests:",
            findings,
            "vacuous",
        )

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report(
            "these arms name a check that passes while a sibling fails — half the arm asserts nothing:",
            findings,
            "mixed",
        )

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report(
            "these sabotages kept a named check from running at all, so the arm shows only that broken code is broken:",
            findings,
            "uncollected",
        )

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these sabotages no longer match the code they were written against:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared check resolves and passes against the real package",
            sabotage=ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in (*ARMS, *CUT2_ARMS, *CUT3_ARMS) for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


def test_an_explicit_uncertified_acceptance_root_is_not_silently_replaced(monkeypatch):
    shm = Path("/dev/shm")
    if not shm.is_dir():
        raise AssertionError("/dev/shm is required for the N2 child-environment regression")
    root = shm / f"science-n2-env-{os.getpid()}"
    for name in ("SCIENCE_CUT4_ROOT", "SCIENCE_CUT5_ROOT", "SCIENCE_CUT6_ROOT"):
        monkeypatch.setenv(name, str(root))
    try:
        run = _run_check(
            "acceptance/test_durable_families.py::test_supersede_survives_facade_reload",
            None,
        )
        assert run.returncode == FAILED
        # And the same, one variable later, for the cut-7 root.
        #
        # The other three are **unset** first, and that is what makes this
        # non-vacuous rather than tidy: `cut7_work_directory` falls back to
        # `work_directory`, which reads `SCIENCE_CUT4_ROOT`, so leaving that
        # pointed at the uncertified directory would fail the child by a route
        # that says nothing about `SCIENCE_CUT7_ROOT`. With only the cut-7
        # variable set, the child reaches this directory through the forwarding
        # in `_run_check` or not at all — and not at all means falling back to
        # the certified default and reporting green for a root nobody certified.
        for name in ("SCIENCE_CUT4_ROOT", "SCIENCE_CUT5_ROOT", "SCIENCE_CUT6_ROOT"):
            monkeypatch.delenv(name)
        monkeypatch.setenv("SCIENCE_CUT7_ROOT", str(root))
        cut7 = _run_check(
            "acceptance/test_n2_cut7.py::test_publication_registration_names_epoch_and_current",
            None,
        )
        assert cut7.returncode == FAILED
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_an_explicit_uncertified_cut10_root_reaches_holdings_engine_checks(monkeypatch):
    shm = Path("/dev/shm")
    if not shm.is_dir():
        raise AssertionError("/dev/shm is required for the N2 child-environment regression")
    root = shm / f"science-n2-cut10-env-{os.getpid()}"
    for cut in range(4, 10):
        monkeypatch.delenv(f"SCIENCE_CUT{cut}_ROOT", raising=False)
    monkeypatch.setenv("SCIENCE_CUT10_ROOT", str(root))
    try:
        run = _run_check(
            "test_holdings_boundary.py::test_recheck_publishes_found_with_the_hash_the_engine_observed",
            None,
        )
        assert run.returncode == FAILED
        assert root.is_dir()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_an_empty_cut10_root_uses_the_repository_relative_fallback(monkeypatch, request):
    monkeypatch.setenv("SCIENCE_CUT10_ROOT", "")
    work = request.getfixturevalue("certified_work")
    assert work.parent.resolve() == (TESTS.parent.parent / ".lifecycle-wrappers-test").resolve()


class TestTheHarnessCanSeeAVacuousArm:
    """N2's second clause, and the reason this file is not just a test runner.

    *Construct a row whose check passes under sabotage, and assert the row itself
    is reported as malformed contract content.* The arm below is defective by
    construction in the exact way the seven vacuous tests found by hand were: the
    sabotage is a real defect, the check is a real check, and they are about
    different things. If the harness scores it `sound`, the harness cannot see
    the thing it exists to see, and every `sound` above means nothing.
    """

    def test_a_row_that_passes_under_its_own_sabotage_is_reported(self, tmp_path):
        finding = audit(VACUOUS_BY_CONSTRUCTION, tmp_path / "vacuous")
        assert finding.verdict == "vacuous", finding.detail

    def test_the_report_is_malformed_contract_content_not_a_failing_test(self, tmp_path):
        finding = audit(VACUOUS_BY_CONSTRUCTION, tmp_path / "vacuous")
        with pytest.raises(MalformedArm, match="malformed contract content"):
            TestEveryArmAssertsSomething().test_no_arm_survives_its_own_sabotage((finding,))

    def test_its_sabotage_is_a_real_defect_and_its_check_a_real_check(self, tmp_path):
        # Otherwise the demonstration is hollow: an arm can also "pass under
        # sabotage" because the sabotage does nothing, and that is staleness, a
        # different finding. This one mutates real code and the check really runs.
        package = _sabotage(VACUOUS_BY_CONSTRUCTION, tmp_path / "real")
        assert package is not None
        covering = (
            "test_decode.py::TestDecodeInvertsTheProjection::test_every_frozen_row_decodes_back_to_its_own_identity"
        )
        assert _run_check(covering, package).returncode == FAILED


class TestOneFailingCheckCannotCoverForAnother:
    """The verdict is taken per check, and this is what that buys.

    An arm naming two checks under one sabotage, where the first fails and the
    second passes: half the arm asserts what it says and half asserts nothing.
    Run in a single `pytest` invocation the pair exits non-zero and the arm reads
    as sound — which is how three arms in this table were sitting when the
    harness scored a whole invocation at a time.
    """

    def test_the_passing_check_is_reported_although_the_other_one_failed(self, tmp_path):
        finding = audit(MIXED_BY_CONSTRUCTION, tmp_path / "mixed")
        assert finding.verdict == "mixed", finding.detail
        assert "test_a_member_term_is_accepted_with_the_check_performed" in finding.detail

    def test_the_report_is_malformed_contract_content_not_a_failing_test(self, tmp_path):
        finding = audit(MIXED_BY_CONSTRUCTION, tmp_path / "mixed")
        with pytest.raises(MalformedArm, match="half the arm asserts nothing"):
            TestEveryArmAssertsSomething().test_no_arm_mixes_a_passing_check_with_a_failing_one((finding,))

    def test_the_two_checks_really_do_disagree(self, tmp_path):
        # The demonstration is only about coverage if the first check genuinely
        # fails: an arm where *both* checks passed is the plain vacuous case
        # above, and would prove nothing about which unit the verdict is taken
        # over.
        package = _sabotage(MIXED_BY_CONSTRUCTION, tmp_path / "mixed")
        assert package is not None
        first, second = MIXED_BY_CONSTRUCTION.checks
        assert _run_check(first, package).returncode == FAILED
        assert _run_check(second, package).returncode == PASSED


class TestAClassNodeIsTheSameDefectOneLevelDown:
    """Naming a check per invocation is not enough if a check can *be* one.

    A class node passes any test that only asks for a `::`, and running it is one
    `pytest` invocation over every method the class holds — the exact aggregation
    the per-check verdict was written to end, reintroduced by the node id rather
    than by the runner. So the rule is the unit, not the punctuation: a check
    names one **test function**.
    """

    def test_a_class_node_is_refused_rather_than_scored(self, tmp_path):
        with pytest.raises(MalformedArm, match="one test function"):
            audit(CLASS_NODE_BY_CONSTRUCTION, tmp_path / "class-node")

    def test_the_class_it_names_holds_methods_that_disagree_under_that_sabotage(self, tmp_path):
        # Which is what makes the refusal load-bearing rather than tidy. If every
        # method of the class failed together, a class node would be a clumsy way
        # of writing a sound arm; these two are in the same class, under the same
        # sabotage, and only one of them fails.
        package = _sabotage(CLASS_NODE_BY_CONSTRUCTION, tmp_path / "class-node")
        assert package is not None
        fails, passes = CLASS_NODE_DISAGREEMENT
        assert _run_check(fails, package).returncode == FAILED
        assert _run_check(passes, package).returncode == PASSED

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        # The runner refuses one; this says the table does not hold one, so the
        # refusal is a guard rather than a thing the suite routinely trips over.
        for arm in ARMS:
            for check in arm.checks:
                assert check.split("::")[-1].startswith("test_"), f"{arm.label}: {check}"


class TestASabotageThatStopsTheCheckRunningIsNotAFailingCheck:
    """Non-zero is not a verdict.

    A mutation coarse enough to break the module's syntax makes every check under
    it uncollectable, and `pytest` reports that as a **usage error**. Read as an
    exit code alone it is indistinguishable from a check that failed — so the
    coarsest possible sabotage, which demonstrates the least, would score highest.
    """

    def test_a_check_that_could_not_run_is_reported(self, tmp_path):
        finding = audit(UNCOLLECTED_BY_CONSTRUCTION, tmp_path / "uncollected")
        assert finding.verdict == "uncollected", finding.detail

    def test_it_is_not_reported_as_a_sound_arm(self, tmp_path):
        finding = audit(UNCOLLECTED_BY_CONSTRUCTION, tmp_path / "uncollected")
        with pytest.raises(MalformedArm, match="did not run"):
            TestEveryArmAssertsSomething().test_no_sabotage_stops_a_check_from_running((finding,))

    def test_the_exit_code_is_the_reason_it_had_to_be_looked_for(self, tmp_path):
        package = _sabotage(UNCOLLECTED_BY_CONSTRUCTION, tmp_path / "uncollected")
        assert package is not None
        run = _run_check(UNCOLLECTED_BY_CONSTRUCTION.checks[0], package)
        assert run.returncode != PASSED  # so "did the run come back clean?" says the arm is fine
        assert run.returncode != FAILED  # and the check never ran


class TestTheArmTableCoversTheCut:
    """The table is contract content, so its shape is asserted rather than assumed."""

    SELECTED = frozenset({"M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M13", "D3"})

    def test_every_row_cut_1_selects_has_at_least_one_arm(self):
        # N2 itself is the eleventh selected row and is not in this set: its arm
        # is this file, and an entry claiming to sabotage it would be circular.
        assert {arm.row for arm in ARMS} == self.SELECTED

    def test_no_arm_claims_a_row_the_cut_defers(self):
        deferred = {"M1", "M2", "M3", "M12", "D4", "D6", "G3", "G7", "S2", "S3", "S8"}
        assert not {arm.row for arm in ARMS} & deferred

    def test_every_arm_names_at_least_one_check(self):
        assert all(arm.checks for arm in ARMS)

    def test_an_arm_naming_no_check_is_refused_by_the_harness(self, tmp_path):
        empty = Arm(row="N2", asserts="an arm with nothing to check", sabotage=ARMS[0].sabotage, checks=())
        assert audit(empty, tmp_path / "empty").verdict == "stale"

    def test_the_runner_refuses_a_check_that_would_re_enter_this_file(self):
        # `audit` states the rule about naming no check; this states the one
        # about naming the wrong thing, and each is what makes the other
        # survivable. A check that resolves to a whole module — `""`, a bare
        # directory, or this file — collects the harness and re-enters it, which
        # is a fork bomb and not a slow test. The class node is here for the
        # other reason: it terminates, and is refused anyway.
        coarse = [
            "",
            "test_decode.py",
            "test_decode.py::TestM4TypedReferentsAndTheReceipt",
            f"{HARNESS}::TestEveryArmAssertsSomething::test_no_arm_survives_its_own_sabotage",
        ]
        for check in coarse:
            with pytest.raises(MalformedArm, match="must name the one test it means"):
                _run_check(check, package=None)


class TestTheCut2ArmTableCoversTheCut:
    """Cut 2's row selection, asserted the same way cut 1's is above."""

    SELECTED = frozenset(
        {
            "G1",
            "G2b",
            "G2c",
            "G3",
            "G6",
            "G8",
            "G9",
            "S5",
            "S6",
            "P1",
            "P2",
            "P3",
            "P4",
            "P5",
            "P6",
            "P7",
            "P8",
            "P9",
            "M6",
            "M8",
            "D3",
            "D6",
            "D7",
        }
    )
    # N2 is the 24th selected row; its arm is the harness itself (cut 1's rule).
    # M6 and M8 here are the completions — cut-1's arms for them stand in ARMS.

    def test_every_selected_row_has_at_least_one_arm(self):
        assert {arm.row for arm in CUT2_ARMS} == self.SELECTED

    def test_no_arm_claims_a_row_the_cut_defers(self):
        deferred = {"G2a", "G4", "G5", "G7", "S1", "S1a", "S7", "S8", "R5", "R10", "C6", "D4", "D5", "W3"}
        assert not {arm.row for arm in CUT2_ARMS} & deferred

    def test_every_arm_names_at_least_one_check(self):
        assert all(arm.checks for arm in CUT2_ARMS)

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        for arm in CUT2_ARMS:
            for check in arm.checks:
                assert check.split("::")[-1].startswith("test_"), f"{arm.label}: {check}"


class TestTheCut3ArmTableCoversTheCut:
    # Cut 3 §4.1/§4.2 as amended through §7.3. N2 is the 34th selected row;
    # its arm is the harness itself (cut 1's rule, inherited).
    SELECTED = frozenset(
        {
            "G2a",
            "G4",
            "M2",
            "R1",
            "R3",
            "R6",
            "R7",
            "R8",
            "R11",
            "R14",
            "R17",
            "R18",
            "T3",
            "T6",
            "T8",
            "G9",
            "R2",
            "R4",
            "R5",
            "R9",
            "R10",
            "R12",
            "R13",
            "R16",
            "R19",
            "R20",
            "R21",
            "R22",
            "R23",
            "T1",
            "T2",
            "T4",
            "T5",
        }
    )

    def test_every_selected_row_has_at_least_one_arm(self):
        assert {arm.row for arm in CUT3_ARMS} == self.SELECTED

    def test_no_arm_claims_a_row_the_cut_defers(self):
        deferred = {
            "R15",
            "T7",
            "H1",
            "H2",
            "H3",
            "H4",
            "G5",
            "G7",
            "W3",
            "S1",
            "L1",
            "C1",
            "X1",
            "N4",
            "P1",
            "D3",
            "M5",
        }
        assert not {arm.row for arm in CUT3_ARMS} & deferred

    def test_every_arm_names_at_least_one_check(self):
        assert all(arm.checks for arm in CUT3_ARMS)

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        for arm in CUT3_ARMS:
            for check in arm.checks:
                assert check.count("::") >= 1 and not check.endswith(".py")


class TestTheHarnessCanSeeAStaleArm:
    """The finding that vacuity alone does not cover.

    A vacuous arm is written wrong; a stale one **becomes** wrong, when the code
    moves under a table nobody re-reads. Both produce the same false report — the
    checks pass and the arm scores healthy — so a harness that only looked for
    vacuity would go quietly decorative over time rather than all at once.
    """

    def test_a_sabotage_that_no_longer_applies_is_reported(self, tmp_path):
        finding = audit(STALE_BY_CONSTRUCTION, tmp_path / "stale")
        assert finding.verdict == "stale", finding.detail

    def test_it_is_not_reported_as_a_sound_arm(self, tmp_path):
        finding = audit(STALE_BY_CONSTRUCTION, tmp_path / "stale")
        with pytest.raises(MalformedArm, match="no longer match"):
            TestEveryArmAssertsSomething().test_no_sabotage_has_gone_stale((finding,))

    def test_a_check_that_no_longer_resolves_is_caught_from_both_directions(self, tmp_path):
        ghost = Arm(
            row="N2",
            asserts="a check that has been renamed away",
            sabotage=ARMS[0].sabotage,
            checks=("test_decode.py::TestM4TypedReferentsAndTheReceipt::test_renamed_away_at_some_point",),
        )
        # Under sabotage it cannot reach `sound`: an unresolvable node id exits 4.
        assert audit(ghost, tmp_path / "ghost").verdict == "uncollected"
        # And the direction that also catches a check which resolves and fails.
        assert baseline(ghost).verdict == "unresolved"

    def test_a_sabotage_matching_twice_is_stale_too(self, tmp_path):
        # Not pedantry: a pattern that matches twice mutates somewhere the arm
        # did not name, so its checks may fail for a reason the arm knows nothing
        # about — which reads as a sound arm and is not one.
        ambiguous = Arm(
            row="N2",
            asserts="a sabotage must name one site",
            sabotage=Sabotage(
                module="resolution.py", before="    def projection(self)", after="    def projection(self)"
            ),
            checks=STALE_BY_CONSTRUCTION.checks,
        )
        assert audit(ambiguous, tmp_path / "ambiguous").verdict == "stale"
