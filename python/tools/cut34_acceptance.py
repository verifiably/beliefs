"""Run cut 34 after cut 33 on the certified durable tuple."""

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
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut34"

PREFIX_RUNNERS = ("cut33_acceptance.py",)
PHASE_MODULES = ("test_snapshot_retraction_acceptance.py", "test_n2_cut34.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and exercised guarantee rows from the table."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut34 import CUT34_ARMS, DECLARATION_UNITS  # pyright: ignore[reportMissingImports]

    rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS if unit.startswith("C")}
    return len(CUT34_ARMS), len(DECLARATION_UNITS), len(rows)


def main(argv: list[str]) -> int:
    result = run_acceptance(
        cut=34,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )

    if result == 0:
        print(
            "guarantee rows exercised: 2 (2 newly closed: C8, C9; the mutation lane has no open boundary)", flush=True
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
