"""Shared machinery for the current acceptance runners."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

PROBE_REFUSED = 2


def _probe(run: Path, actor: str) -> str | None:
    from beliefs.permit import Authority, WritePermit
    from beliefs.root import init_corpus_root, metadata_root_for

    corpus_root = run / "probe-corpus"
    try:
        init_corpus_root(corpus_root, authority=Authority(WritePermit.full(), actor))
        return None
    except Exception as refused:  # noqa: BLE001 - report the engine's refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        shutil.rmtree(corpus_root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(corpus_root), ignore_errors=True)


def run_acceptance(
    *,
    cut: int,
    python_root: Path,
    default_work: Path,
    prefix_runners: tuple[str, ...],
    phase_modules: tuple[str, ...],
    declared_accounting: Callable[[], tuple[int, int, int]],
    argv: list[str],
) -> int:
    tools = python_root / "tools"
    acceptance = python_root / "tests" / "acceptance"
    root_key = f"SCIENCE_CUT{cut}_ROOT"
    phases = len(prefix_runners) + len(phase_modules)
    for module in phase_modules:
        if not (acceptance / module).is_file():
            print(f"cut-{cut} required acceptance module is missing: {acceptance / module}", file=sys.stderr)
            return 1
    for runner in prefix_runners:
        if not (tools / runner).is_file():
            print(f"cut-{cut} required prefix runner is missing: {tools / runner}", file=sys.stderr)
            return 1

    work = Path(os.environ.get(root_key, default_work))
    work.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = _probe(run, f"cut{cut}-probe")
        if refusal is not None:
            print(
                f"cut-{cut} acceptance cannot run here: its durable corpus prerequisite refused.\n"
                f"  {refusal}\n"
                f"  Set {root_key} to a certified volume or recertify the tuple. "
                "This is an error, not a skip.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        phase = 0
        for runner in prefix_runners:
            phase += 1
            print(f"[cut{cut} phase {phase}/{phases}] {runner}", flush=True)
            completed = subprocess.run(
                [sys.executable, str(tools / runner)],
                cwd=python_root,
                check=False,
                env={
                    **os.environ,
                    "XDG_CACHE_HOME": str(run / ".cache"),
                    f"SCIENCE_CUT{cut - 1}_ROOT": str(run),
                },
            )
            if completed.returncode != 0:
                return completed.returncode

        environment = {
            **os.environ,
            "XDG_CACHE_HOME": str(run / ".cache"),
            **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, cut + 1)},
        }
        for index, module in enumerate(phase_modules):
            phase += 1
            print(f"[cut{cut} phase {phase}/{phases}] {module}", flush=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(acceptance / module),
                    *(argv if index == len(phase_modules) - 1 else []),
                ],
                cwd=python_root,
                check=False,
                env=environment,
            )
            if completed.returncode != 0:
                return completed.returncode

        arms, units, rows = declared_accounting()
        print(f"declared arms: {arms} (= {units} declaration units; {rows} guarantee rows)", flush=True)
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)
