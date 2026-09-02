"""Run cut 15 after cut 14 on the certified durable and confinement tuple."""

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
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut15-acceptance"

PREFIX_RUNNERS = ("cut14_acceptance.py",)
PHASE_MODULES = ("test_cut15_lineage.py", "test_confinement_acceptance.py", "test_n2_cut15.py")
PROBE_REFUSED = 2


def work_directory() -> Path:
    work = Path(os.environ.get("SCIENCE_CUT15_ROOT", DEFAULT_WORK))
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    from beliefs.root import init_corpus_root, init_store_root, init_world_root, metadata_root_for
    from beliefs.world import WorldConfig

    world_root = run / "probe-world"
    corpus_root = run / "probe-corpus"
    store_root = run / "probe-store"
    try:
        init_world_root(WorldConfig(world_root, "0" * 32, ()))
        init_corpus_root(corpus_root)
        init_store_root(store_root)
        from beliefs.confinement import host_prerequisites

        reason = host_prerequisites()
        return f"ConfinementUnavailable: {reason}" if reason is not None else None
    except Exception as refused:  # noqa: BLE001 - report the engine's refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        for root in (world_root, corpus_root, store_root):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def declared_arm_count() -> int:
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut15 import CUT15_ARMS  # pyright: ignore[reportMissingImports]

    return len(CUT15_ARMS)


def cut_environment(run: Path) -> dict[str, str]:
    return {**os.environ, **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 16)}}


def run_prefix(runner: str, run: Path) -> int:
    completed = subprocess.run(
        [sys.executable, str(TOOLS / runner)],
        cwd=PYTHON_ROOT,
        check=False,
        env={**os.environ, "SCIENCE_CUT14_ROOT": str(run)},
    )
    return completed.returncode


def main(argv: list[str]) -> int:
    phases = len(PREFIX_RUNNERS) + len(PHASE_MODULES)
    for module in PHASE_MODULES:
        if not (ACCEPTANCE / module).is_file():
            print(f"cut-15 required acceptance module is missing: {ACCEPTANCE / module}", file=sys.stderr)
            return 1
    for runner in PREFIX_RUNNERS:
        if not (TOOLS / runner).is_file():
            print(f"cut-15 required prefix runner is missing: {TOOLS / runner}", file=sys.stderr)
            return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-15 acceptance cannot run here: its durable or confinement prerequisite refused.\n"
                f"  {refusal}\n"
                "  Set SCIENCE_CUT15_ROOT to a certified volume or satisfy the confinement gate. "
                "This is an error, not a skip.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        phase = 0
        for runner in PREFIX_RUNNERS:
            phase += 1
            print(f"[cut15 phase {phase}/{phases}] {runner}", flush=True)
            if returncode := run_prefix(runner, run):
                return returncode

        for index, module in enumerate(PHASE_MODULES):
            phase += 1
            print(f"[cut15 phase {phase}/{phases}] {module}", flush=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(ACCEPTANCE / module),
                    *(argv if index == len(PHASE_MODULES) - 1 else []),
                ],
                cwd=PYTHON_ROOT,
                check=False,
                env=cut_environment(run),
            )
            if completed.returncode != 0:
                return completed.returncode

        print(
            f"declared arms: {declared_arm_count()} (= 17 selected + 8 labeled units)",
            flush=True,
        )
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
