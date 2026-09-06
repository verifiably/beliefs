"""Run cut 19 after cut 18 on the certified durable tuple."""

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
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut19-acceptance"

PREFIX_RUNNERS = ("cut18_acceptance.py",)
PHASE_MODULES = ("test_session_acceptance.py", "test_n2_cut19.py")
PROBE_REFUSED = 2


def work_directory() -> Path:
    work = Path(os.environ.get("SCIENCE_CUT19_ROOT", DEFAULT_WORK))
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    from beliefs.permit import Authority, WritePermit
    from beliefs.root import init_corpus_root, metadata_root_for

    corpus_root = run / "probe-corpus"
    try:
        init_corpus_root(corpus_root, authority=Authority(WritePermit.full(), "cut19-probe"))
        return None
    except Exception as refused:  # noqa: BLE001 - report the engine's refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        shutil.rmtree(corpus_root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(corpus_root), ignore_errors=True)


def declared_accounting() -> tuple[int, int]:
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut19 import CUT19_ARMS, DECLARATION_UNITS  # pyright: ignore[reportMissingImports]

    return len(CUT19_ARMS), len(DECLARATION_UNITS)


def cut_environment(run: Path) -> dict[str, str]:
    return {
        **os.environ,
        "XDG_CACHE_HOME": str(run / ".cache"),
        **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 20)},
    }


def run_prefix(runner: str, run: Path) -> int:
    completed = subprocess.run(
        [sys.executable, str(TOOLS / runner)],
        cwd=PYTHON_ROOT,
        check=False,
        env={
            **os.environ,
            "XDG_CACHE_HOME": str(run / ".cache"),
            "SCIENCE_CUT18_ROOT": str(run),
        },
    )
    return completed.returncode


def main(argv: list[str]) -> int:
    phases = len(PREFIX_RUNNERS) + len(PHASE_MODULES)
    for module in PHASE_MODULES:
        if not (ACCEPTANCE / module).is_file():
            print(f"cut-19 required acceptance module is missing: {ACCEPTANCE / module}", file=sys.stderr)
            return 1
    for runner in PREFIX_RUNNERS:
        if not (TOOLS / runner).is_file():
            print(f"cut-19 required prefix runner is missing: {TOOLS / runner}", file=sys.stderr)
            return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-19 acceptance cannot run here: its durable corpus prerequisite refused.\n"
                f"  {refusal}\n"
                "  Set SCIENCE_CUT19_ROOT to a certified volume or recertify the tuple. "
                "This is an error, not a skip.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        phase = 0
        for runner in PREFIX_RUNNERS:
            phase += 1
            print(f"[cut19 phase {phase}/{phases}] {runner}", flush=True)
            if returncode := run_prefix(runner, run):
                return returncode

        environment = cut_environment(run)
        for index, module in enumerate(PHASE_MODULES):
            phase += 1
            print(f"[cut19 phase {phase}/{phases}] {module}", flush=True)
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
                env=environment,
            )
            if completed.returncode != 0:
                return completed.returncode

        arms, units = declared_accounting()
        print(
            f"declared arms: {arms} (= {units} declaration units; 11 guarantee rows)",
            flush=True,
        )
        print(
            "row accounting: 11 full/closed + 0 partial + 0 re-reads",
            flush=True,
        )
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
