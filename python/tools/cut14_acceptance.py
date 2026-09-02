from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut14-acceptance"
PREFIX_RUNNERS: tuple[str, ...] = ()
PHASE_MODULES = (
    "test_n2_cut6.py",
    "test_n2_cut7.py",
    "test_n2_cut9.py",
    "test_n2_cut10.py",
    "test_intent_boundary_acceptance.py",
    "test_n2_cut11.py",
    "test_successor_admission_acceptance.py",
    "test_n2_cut12.py",
    "test_confinement_acceptance.py",
    "test_n2_cut13.py",
    "test_coordination_acceptance.py",
    "test_n2_cut14.py",
)
PROBE_REFUSED = 2


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT14_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def cut_environment(run: Path) -> dict[str, str]:
    cache = run / "cache"
    cache.mkdir(exist_ok=True)
    return {
        **os.environ,
        "XDG_CACHE_HOME": str(cache),
        **{f"SCIENCE_CUT{number}_ROOT": str(run) for number in range(4, 15)},
    }


def declared_arm_count() -> int:
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut14 import CUT14_ARMS  # pyright: ignore[reportMissingImports]

    return len(CUT14_ARMS)


def probe(run: Path) -> str | None:
    from beliefs.confinement import host_prerequisites
    from beliefs.root import init_corpus_root, init_store_root, init_world_root, metadata_root_for
    from beliefs.world import WorldConfig

    world_root = run / "probe-world"
    corpus_root = run / "probe-corpus"
    store_root = run / "probe-store"
    try:
        init_world_root(WorldConfig(world_root, "0" * 32, ()))
        init_corpus_root(corpus_root)
        init_store_root(store_root)
        reason = host_prerequisites()
        return None if reason is None else f"ConfinementUnavailable: {reason}"
    except Exception as refused:  # noqa: BLE001 - expose the engine's refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        for root in (world_root, corpus_root, store_root):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def main(argv: list[str]) -> int:
    for module in PHASE_MODULES:
        if not (ACCEPTANCE / module).is_file():
            print(
                f"cut-14 required acceptance module is missing: {ACCEPTANCE / module}",
                file=sys.stderr,
            )
            return 1
    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                f"cut-14 acceptance cannot run here; this is an error, not a skip: {refusal}",
                file=sys.stderr,
            )
            return PROBE_REFUSED
        for phase, module in enumerate(PHASE_MODULES, 1):
            print(f"[cut14 phase {phase}/{len(PHASE_MODULES)}] {module}", flush=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(ACCEPTANCE / module),
                    *(argv if phase == len(PHASE_MODULES) else ()),
                ],
                cwd=PYTHON_ROOT,
                check=False,
                env=cut_environment(run),
            )
            if completed.returncode != 0:
                return completed.returncode
        try:
            arms = declared_arm_count()
        except Exception as failure:  # noqa: BLE001 - report, do not mask a green run
            print(
                f"cut-14 acceptance: could not compute declared-arm count: {failure}",
                file=sys.stderr,
            )
        else:
            print(f"declared arms: {arms} (= 29 selected units)", flush=True)
        return 0
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
