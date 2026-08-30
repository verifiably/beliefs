"""The cut-12 acceptance command — successor admission, on the certified tuple.

It errors off the certified tuple. It never skips. Three phases run in order:
the unedited cut-11 prefix, durable cut-12 arms, then cut-12's N2 audit.

Never run beside another acceptance command or the ordinary suite. All cut
roots are environment-scoped and concurrent runs would delete shared roots.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut12-acceptance"

PREFIX_RUNNERS = ("cut11_acceptance.py",)
PHASE_MODULES = ("test_successor_admission_acceptance.py", "test_n2_cut12.py")
PROBE_REFUSED = 2


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT12_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    """Register and drop one throwaway world root, corpus root, and store root."""
    from beliefs.root import (
        init_corpus_root,
        init_store_root,
        init_world_root,
        metadata_root_for,
    )
    from beliefs.world import WorldConfig

    world_root = run / "probe-world"
    corpus_root = run / "probe-corpus"
    store_root = run / "probe-store"
    try:
        init_world_root(WorldConfig(world_root, "0" * 32, ()))
        init_corpus_root(corpus_root)
        init_store_root(store_root)
        return None
    except Exception as refused:  # noqa: BLE001 - report the engine's own refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        for root in (world_root, corpus_root, store_root):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def declared_arm_count() -> int:
    """Return cut 12's declared arm count, ``len(CUT12_ARMS)``."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut12 import CUT12_ARMS  # pyright: ignore[reportMissingImports]

    return len(CUT12_ARMS)


def cut_environment(run: Path) -> dict[str, str]:
    return {
        **os.environ,
        **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 13)},
    }


def run_prefix(runner: str, run: Path) -> int:
    """Run the prior cut's command unchanged beneath ``run``."""
    completed = subprocess.run(
        [sys.executable, str(TOOLS / runner)],
        cwd=PYTHON_ROOT,
        check=False,
        env={**os.environ, "SCIENCE_CUT11_ROOT": str(run)},
    )
    return completed.returncode


def main(argv: list[str]) -> int:
    phases = len(PREFIX_RUNNERS) + len(PHASE_MODULES)
    for module in PHASE_MODULES:
        path = ACCEPTANCE / module
        if not path.is_file():
            print(f"cut-12 required acceptance module is missing: {path}", file=sys.stderr)
            return 1
    for runner in PREFIX_RUNNERS:
        path = TOOLS / runner
        if not path.is_file():
            print(f"cut-12 required prefix runner is missing: {path}", file=sys.stderr)
            return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-12 acceptance cannot run here: the volume beneath "
                f"{work} is not on the engine's certified allowlist.\n"
                f"  the engine refused with {refusal}\n"
                "  set SCIENCE_CUT12_ROOT to a directory on a certified volume, or recertify with\n"
                "  the engine's own tooling. This is an error, not a skip: an environment that\n"
                "  cannot exercise durability must not be able to report cut-12 discharge.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        phase = 0
        for runner in PREFIX_RUNNERS:
            phase += 1
            print(f"[cut12 phase {phase}/{phases}] {runner}", flush=True)
            returncode = run_prefix(runner, run)
            if returncode != 0:
                print(
                    f"cut-12 acceptance stopped: the {runner} prefix exited {returncode}.\n"
                    "  A prior cut's arms are its own claim and cut 12 runs them unchanged, so this\n"
                    "  is that cut's failure and not a cut-12 one. Cut 12's arms did not run and cut\n"
                    "  12 is not discharged.",
                    file=sys.stderr,
                )
                return returncode

        for index, module in enumerate(PHASE_MODULES):
            phase += 1
            last = index == len(PHASE_MODULES) - 1
            print(f"[cut12 phase {phase}/{phases}] {module}", flush=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(ACCEPTANCE / module),
                    *(argv if last else []),
                ],
                cwd=PYTHON_ROOT,
                check=False,
                env=cut_environment(run),
            )
            if completed.returncode != 0:
                return completed.returncode

        try:
            arms = declared_arm_count()
        except Exception as failure:  # noqa: BLE001 - report, do not mask run result
            print(
                f"cut-12 acceptance: could not compute declared-arm count: {failure}",
                file=sys.stderr,
            )
        else:
            print(
                f"declared arms: {arms} (= len(CUT12_ARMS), normalizing to the 24 frozen "
                "units pinned by test_the_partition_accounts_exactly_the_24_frozen_units, "
                "among the tests above; not itself a pytest total)",
                flush=True,
            )
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
