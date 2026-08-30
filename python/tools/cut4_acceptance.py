"""The cut-4 acceptance command — the durable arms, on the certified tuple.

**It errors off the certified tuple. It never skips.** An environment where
durability cannot be exercised must not be able to report cut-4 discharge, and
a skip is exactly how that happens: the run is green, the count is short, and
nobody reads the count. So the tuple is probed first, once, and a refusal ends
the command with the engine's own words.

Ordinary unit tests are a different command (`pytest`) and a different claim:
plan building, refusal ordering, the intent encoding and facade behaviour
against `DefaultExecutor` run anywhere, and **cannot claim cut-4 discharge**.

Usage::

    python -m tools.cut4_acceptance                # the whole acceptance suite
    python -m tools.cut4_acceptance -k lineage     # further arguments reach pytest

The work directory is `<repo>/.cut4-acceptance` unless `SCIENCE_CUT4_ROOT`
names another one — a host whose certified volume is not the one the checkout
lives on sets that.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut4-acceptance"

PROBE_REFUSED = 2
"""Distinct from pytest's own codes: *the arms did not run* is not *an arm
failed*, and a caller that cannot tell them apart learns nothing from either."""


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT4_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def run_directory(work: Path) -> Path:
    """This run's own directory under the work directory.

    One run never removes another's roots. The command cleans up after itself,
    and two invocations at once — or one beside an editor running the suite —
    would otherwise delete each other's corpora mid-transaction, which reads as
    an engine failure and is not one.
    """
    return Path(tempfile.mkdtemp(prefix="run-", dir=work))


def probe(run: Path) -> str | None:
    """Register and drop one throwaway root. Returns the engine's refusal, or
    `None` when the tuple is certified.

    The probe is the same act the arms perform, so a host that passes it and
    then fails an arm has failed the arm — which is the discrimination the
    command exists to keep.
    """
    from beliefs.root import init_corpus_root, metadata_root_for

    root = run / "probe"
    try:
        init_corpus_root(root)
        return None
    except Exception as refused:  # noqa: BLE001 - reported, whatever the engine raised
        return f"{type(refused).__name__}: {refused}"
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def main(argv: list[str]) -> int:
    work = work_directory()
    run = run_directory(work)
    refusal = probe(run)
    if refusal is not None:
        shutil.rmtree(run, ignore_errors=True)
        print(
            "cut-4 acceptance cannot run here: the volume beneath "
            f"{work} is not on the engine's certified allowlist.\n"
            f"  the engine refused with {refusal}\n"
            "  set SCIENCE_CUT4_ROOT to a directory on a certified volume, or recertify with the\n"
            "  engine's own tooling. This is an error, not a skip: an environment that cannot\n"
            "  exercise durability must not be able to report cut-4 discharge.",
            file=sys.stderr,
        )
        return PROBE_REFUSED

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(ACCEPTANCE), *argv],
        cwd=PYTHON_ROOT,
        check=False,
        env={**os.environ, "SCIENCE_CUT4_ROOT": str(run)},
    )
    shutil.rmtree(run, ignore_errors=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
