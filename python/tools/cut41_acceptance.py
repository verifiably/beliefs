"""Run cut 41 after the highest-numbered prior runner on the certified durable tuple."""

from __future__ import annotations

import sys
from pathlib import Path

from acceptance_runner import run_acceptance

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
REPO_ROOT = PYTHON_ROOT.parent
# Beside the main checkout, as cut 40's runner resolves it: a lane worktree
# under `.worktrees/` sits on storage the durability allowlist refuses.
MAIN_CHECKOUT = REPO_ROOT.parents[1] if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut41"

# Roadmap rule 5: the highest-numbered acceptance runner at freeze (the cut document's §5).
PREFIX_RUNNERS = ("cut40_acceptance.py",)
PHASE_MODULES = ("test_live_selection_acceptance.py", "test_n2_cut41.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and exercised guarantee rows from the frozen declaration."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut41 import CUT41_ARMS, DECLARATION_UNITS  # pyright: ignore[reportMissingImports]

    rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS}
    assert rows == {"Z1", "Z2", "Z3", "Z4", "Z5"}
    arms, units = len(CUT41_ARMS), len(DECLARATION_UNITS)
    assert (arms, units) == (12, 12)
    return arms, units, len(rows)


def main(argv: list[str]) -> int:
    result = run_acceptance(
        cut=41,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )

    if result == 0:
        print("guarantee rows exercised: 5 (5 newly closed: Z1, Z2, Z3, Z4, Z5)", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
