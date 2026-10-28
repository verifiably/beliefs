"""Run cut 48 after the highest-numbered prior runner on the certified durable tuple."""

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
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut48"

# Roadmap rule 5: the highest-numbered acceptance runner at freeze (the cut document's §5).
PREFIX_RUNNERS = ("cut47_acceptance.py",)
PHASE_MODULES = ("test_overlapping_publications_acceptance.py", "test_n2_cut48.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and exercised guarantee rows from the frozen declaration."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut48 import CUT47_ARMS, DECLARATION_UNITS  # pyright: ignore[reportMissingImports]

    rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS}
    assert rows == {"W19", "W20", "G14", "Y19", "J17", "J20"}
    arms, units = len(CUT47_ARMS), len(DECLARATION_UNITS)
    assert (arms, units) == (33, 33)
    return arms, units, len(rows)


def main(argv: list[str]) -> int:
    result = run_acceptance(
        cut=48,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )

    if result == 0:
        print(
            "guarantee rows exercised: 6 (4 newly closed: W19, W20, G14, Y19; J17 and J20 amendments reclosed)",
            flush=True,
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
