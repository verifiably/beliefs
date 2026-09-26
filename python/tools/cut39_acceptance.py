"""Run cut 39 after cut 38 on the certified durable tuple."""

from __future__ import annotations

import sys
from pathlib import Path

from acceptance_runner import run_acceptance
from checkout import MAIN_CHECKOUT

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
# "Beside the checkout" means beside the **main** checkout, as
# `checkout.py` resolves it: a lane worktree under `.worktrees/`
# sits on storage the durability allowlist refuses, and the acceptance roots
# must sit where the certified volume is. `.work/acceptance/` rather than a
# dotted root at the project root: `test_project_root.py` names the legacy
# `.cut*-acceptance` roots individually and admits no new one.
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut39"

PREFIX_RUNNERS = ("cut38_acceptance.py",)
PHASE_MODULES = ("test_publication_records_acceptance.py", "test_n2_cut39.py")

# The plan's accounting table, keyed by Task 0's two engine facts
# `(REPLACE_UNREGISTERED, ROLLBACK_MEANS != "unrun")`; the frozen cut selects one row.
ACCOUNTING = {
    ("accepted", True): (14, 13),
    ("refused", True): (13, 13),
    ("accepted", False): (13, 12),
    ("refused", False): (12, 12),
}


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and exercised guarantee rows from the table."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut39 import (  # pyright: ignore[reportMissingImports]
        CUT39_ARMS,
        DECLARATION_UNITS,
        REPLACE_UNREGISTERED,
        ROLLBACK_MEANS,
    )

    rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS}
    assert rows == {"W17", "Y1", "Y2", "Y3", "Y4"}
    arms, units = len(CUT39_ARMS), len(DECLARATION_UNITS)
    assert (arms, units) == ACCOUNTING[(REPLACE_UNREGISTERED, ROLLBACK_MEANS != "unrun")]
    return arms, units, len(rows)


def main(argv: list[str]) -> int:
    result = run_acceptance(
        cut=39,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )

    if result == 0:
        print("guarantee rows exercised: 5 (5 newly closed: W17, Y1, Y2, Y3, Y4)", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
