"""N2 over cut 4's own selected arms.

The doctrine is already load-bearing inside cut 4's reading — it is what refuses
S4's vacuous form and what excludes G5 — so declaring this cut's arms is the
obligation the reading has been discharging in prose, not a new one.

**The audit runs here rather than in the portable harness**, and that placement
is the claim: most of cut 4's arms are durable, their checks name
`acceptance/…` node ids, and an audit that could pass off the certified tuple
would be scoring arms that never wrote to a store. `test_n2.py` keeps auditing
cuts 1–3 exactly as it did, portably, and neither file changes the other's
table.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from n2_arms import Arm
from n2_arms_cut4 import CUT4_ARMS
from test_n2 import MalformedArm, audit, baseline

WORKERS = 8


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    """Every cut-4 arm, audited once. Concurrent — each arm owns its own copy
    of the package, and each durable check its own corpus root."""
    root = tmp_path_factory.mktemp("n2-cut4")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(CUT4_ARMS)))


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(reason + "\n" + "\n".join(f"  {f.arm.label}\n    {f.detail}" for f in offending))


class TestEveryCut4ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report(
            "these cut-4 arms have a check that passes under their own sabotage, which makes them "
            "malformed contract content rather than failing tests:",
            findings,
            "vacuous",
        )

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report(
            "these cut-4 arms name a check that passes while a sibling fails — half the arm asserts nothing:",
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
        _report("these cut-4 sabotages no longer match the code they were written against:", findings, "stale")

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        # A class node is one invocation over many tests wearing a node id: the
        # aggregation the per-check verdict exists to end, reintroduced through
        # the id rather than the runner.
        for arm in CUT4_ARMS:
            for check in arm.checks:
                assert check.split("::")[-1].startswith("test_"), f"{arm.label}: {check}"
                assert len(check.split("::")) >= 2, f"{arm.label}: {check}"

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-4 check resolves and passes against the real package",
            sabotage=CUT4_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT4_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail
