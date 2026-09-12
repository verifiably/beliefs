"""Run cut 26 after cut 25 on the certified durable tuple."""

from __future__ import annotations

import sys
from pathlib import Path

from acceptance_runner import run_acceptance

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut26-acceptance"

PREFIX_RUNNERS = ("cut25_acceptance.py",)
PHASE_MODULES = ("test_n2_cut26.py",)


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and guarantee rows, counted from the declaration
    itself. Nothing here is a literal: a printed accounting that does not move
    with the table it reports is a claim about a cut that no longer exists."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut26 import CUT26_ARMS, DECLARATION_UNITS, unit_of  # pyright: ignore[reportMissingImports]

    return len(CUT26_ARMS), len(DECLARATION_UNITS), len({unit_of(arm.row) for arm in CUT26_ARMS})


def main(argv: list[str]) -> int:
    return run_acceptance(
        cut=26,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
