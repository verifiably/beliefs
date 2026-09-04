"""Run the explicit cut 17 inventory on the certified durable tuple."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TESTS = PYTHON_ROOT / "tests"
ACCEPTANCE = TESTS / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut17-acceptance"

PREFIX_RUNNERS: tuple[str, ...] = ()
PHASE_MODULES = (
    "test_n2_cut6.py",
    "test_n2_cut7.py",
    "test_n2_cut9.py",
    "test_intent_boundary_acceptance.py",
    "test_n2_cut11.py",
    "test_successor_admission_acceptance.py",
    "test_n2_cut12.py",
    "test_confinement_acceptance.py",
    "test_n2_cut13.py",
    "test_coordination_acceptance.py",
    "test_n2_cut14.py",
    "test_cut15_lineage.py",
    "test_n2_cut15.py",
    "test_relocation_acceptance.py",
    "test_n2_cut16.py",
    "test_permit_acceptance.py",
    "test_permit_boundary.py",
    "test_permit_entry_points.py",
    "test_n2_cut17.py",
)
PROBE_REFUSED = 2


def work_directory() -> Path:
    work = Path(os.environ.get("SCIENCE_CUT17_ROOT", DEFAULT_WORK))
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    from beliefs.confinement import host_prerequisites
    from beliefs.permit import Authority, WritePermit
    from beliefs.root import (
        init_corpus_root,
        init_store_root,
        init_world_root,
        metadata_root_for,
    )
    from beliefs.world import WorldConfig

    authority = Authority(WritePermit.full(), "cut17-probe")
    world_root = run / "probe-world"
    corpus_root = run / "probe-corpus"
    store_root = run / "probe-store"
    try:
        init_world_root(WorldConfig(world_root, "0" * 32, ()), authority=authority)
        init_corpus_root(corpus_root, authority=authority)
        init_store_root(store_root, authority=authority)
        reason = host_prerequisites()
        return f"ConfinementUnavailable: {reason}" if reason is not None else None
    except Exception as refused:  # noqa: BLE001 - report the exact prerequisite refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        for root in (world_root, corpus_root, store_root):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def declared_arm_count() -> int:
    for directory in (TESTS, ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut17 import CUT17_ARMS  # pyright: ignore[reportMissingImports]

    return len(CUT17_ARMS)


def cut_environment(run: Path) -> dict[str, str]:
    return {
        **os.environ,
        "XDG_CACHE_HOME": str(run / ".cache"),
        **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 18)},
    }


def phase_path(module: str) -> Path:
    acceptance = ACCEPTANCE / module
    return acceptance if acceptance.is_file() else TESTS / module


def main(argv: list[str]) -> int:
    paths = tuple(phase_path(module) for module in PHASE_MODULES)
    for module, path in zip(PHASE_MODULES, paths, strict=True):
        if not path.is_file():
            print(f"cut-17 required module is missing: {module}", file=sys.stderr)
            return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-17 acceptance cannot run here: a durable or confinement prerequisite refused.\n"
                f"  {refusal}\n"
                "  Set SCIENCE_CUT17_ROOT to a certified volume or satisfy the confinement gate. "
                "This is an error, not a skip.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        environment = cut_environment(run)
        for index, (module, path) in enumerate(zip(PHASE_MODULES, paths, strict=True), 1):
            print(f"[cut17 phase {index}/{len(paths)}] {module}", flush=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(path),
                    *(argv if index == len(paths) else []),
                ],
                cwd=PYTHON_ROOT,
                check=False,
                env=environment,
            )
            if completed.returncode != 0:
                return completed.returncode

        print(
            f"declared arms: {declared_arm_count()} (= 8 selected + 1 labeled units)",
            flush=True,
        )
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
