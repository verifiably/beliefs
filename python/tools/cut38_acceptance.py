"""Run cut 38 after cut 37 on the certified durable tuple."""

from __future__ import annotations

import sys
from pathlib import Path

from acceptance_runner import run_acceptance

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
REPO_ROOT = PYTHON_ROOT.parent
# "Beside the checkout" means beside the **main** checkout, as
# `tools/reproduction/paths.py` resolves it: a lane worktree under `.worktrees/`
# sits on storage the durability allowlist refuses, and the acceptance roots
# must sit where the certified volume is. `.work/acceptance/` rather than a
# dotted root at the project root: `test_project_root.py` names the legacy
# `.cut*-acceptance` roots individually and admits no new one.
MAIN_CHECKOUT = REPO_ROOT.parents[1] if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut38"

PREFIX_RUNNERS = ("cut37_acceptance.py",)
PHASE_MODULES = ("test_act_report_remainder_acceptance.py", "test_n2_cut38.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and exercised guarantee rows from the table."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut38 import CUT38_ARMS, DECLARATION_UNITS  # pyright: ignore[reportMissingImports]

    rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS if not unit.startswith("BI-")}
    assert rows == {"T2", "T5", "T6"}
    return len(CUT38_ARMS), len(DECLARATION_UNITS), len(rows)


def main(argv: list[str]) -> int:
    result = run_acceptance(
        cut=38,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )

    if result == 0:
        print(
            "guarantee rows exercised: 3 (1 newly closed: T2; T5 and T6 re-read for the new kinds; T7 partial under cross-root-publication)",
            flush=True,
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
