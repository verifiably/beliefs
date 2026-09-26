"""Run cut 32 after cut 31 on the certified durable tuple."""

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
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut32"

PREFIX_RUNNERS = ("cut31_acceptance.py",)
PHASE_MODULES = ("test_composite_acceptance.py", "test_n2_cut32.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and guarantee rows, counted from the declaration
    itself. Nothing here is a literal: a printed accounting that does not move
    with the table it reports is a claim about a cut that no longer exists."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut32 import CUT32_ARMS, DECLARATION_UNITS, UNIT_CHECKS  # pyright: ignore[reportMissingImports]

    # Rows are counted from `UNIT_CHECKS` — one acceptance test per guarantee
    # row — and not from the arms' units: U10 is read from the reproduction's
    # recorded state and homes no sabotage (the cut document's §5).
    return len(CUT32_ARMS), len(DECLARATION_UNITS), len(set(UNIT_CHECKS))


def main(argv: list[str]) -> int:
    return run_acceptance(
        cut=32,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
