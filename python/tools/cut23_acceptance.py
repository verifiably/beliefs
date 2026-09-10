"""Run cut 23 after cut 22 on the certified durable tuple."""

from __future__ import annotations

import sys
from pathlib import Path

from acceptance_runner import run_acceptance

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut23-acceptance"

PREFIX_RUNNERS = ("cut22_acceptance.py",)
PHASE_MODULES = ("test_world_view_acceptance.py", "test_n2_cut23.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and guarantee rows, counted from the declaration
    itself. Nothing here is a literal: a printed accounting that does not move
    with the table it reports is a claim about a cut that no longer exists."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut23 import CUT23_ARMS, DECLARATION_UNITS, unit_of  # pyright: ignore[reportMissingImports]

    return len(CUT23_ARMS), len(DECLARATION_UNITS), len({unit_of(arm.row) for arm in CUT23_ARMS})


def main(argv: list[str]) -> int:
    return run_acceptance(
        cut=23,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
