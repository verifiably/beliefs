"""Run cut 6's durable arms on the certified tuple."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut6-acceptance"

PROBE_REFUSED = 2


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT6_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    from beliefs.root import init_world_root, metadata_root_for
    from beliefs.world import WorldConfig

    root = run / "probe-world"
    try:
        init_world_root(WorldConfig(root, "0" * 32, ()))
        return None
    except Exception as refused:  # noqa: BLE001 - report the engine's own refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def main(argv: list[str]) -> int:
    n2 = ACCEPTANCE / "test_n2_cut6.py"
    if not n2.is_file():
        print(f"cut-6 required acceptance module is missing: {n2}", file=sys.stderr)
        return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-6 acceptance cannot run here: the volume beneath "
                f"{work} is not on the engine's certified allowlist.\n"
                f"  the engine refused with {refusal}\n"
                "  set SCIENCE_CUT6_ROOT to a directory on a certified volume, or recertify with the\n"
                "  engine's own tooling. This is an error, not a skip: an environment that cannot\n"
                "  exercise durability must not be able to report cut-6 discharge.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(n2), *argv],
            cwd=PYTHON_ROOT,
            check=False,
            env={
                **os.environ,
                "SCIENCE_CUT4_ROOT": str(run),
                "SCIENCE_CUT5_ROOT": str(run),
                "SCIENCE_CUT6_ROOT": str(run),
            },
        )
        return completed.returncode
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
