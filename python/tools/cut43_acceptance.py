"""Run cut 43 after the highest-numbered prior runner on the certified durable tuple."""

from __future__ import annotations

import sys
from pathlib import Path

from acceptance_runner import run_acceptance
from checkout import MAIN_CHECKOUT

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
# Beside the main checkout, as `checkout.py` resolves it: a lane worktree
# under `.worktrees/` sits on storage the durability allowlist refuses.
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut43"

# Roadmap rule 5: the highest-numbered acceptance runner at freeze (the cut document's §5).
PREFIX_RUNNERS = ("cut42_acceptance.py",)
PHASE_MODULES = ("test_session_mounts_acceptance.py", "test_n2_cut43.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and exercised guarantee rows from the frozen declaration."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut43 import CUT43_ARMS, DECLARATION_UNITS  # pyright: ignore[reportMissingImports]

    rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS}
    assert rows == {"J12", "J13", "J14", "J15"}
    arms, units = len(CUT43_ARMS), len(DECLARATION_UNITS)
    assert (arms, units) == (9, 9)
    return arms, units, len(rows)


def main(argv: list[str]) -> int:
    result = run_acceptance(
        cut=43,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )

    if result == 0:
        print("guarantee rows exercised: 4 (4 newly closed: J12, J13, J14, J15)", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
