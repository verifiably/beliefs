"""The cut-7 acceptance command — the whole epoch-carrier surface, on the certified tuple.

**It errors off the certified tuple. It never skips.** An environment where
durability cannot be exercised must not be able to report cut-7 discharge, and
a skip is exactly how that happens: the run is green, the count is short, and
nobody reads the count. So the tuple is probed first, once, and a refusal ends
the command with the engine's own words.

Three phases, in order, each one a whole command:

1. `tools/cut5_acceptance.py`, unedited;
2. `tools/cut6_acceptance.py`, unedited; and
3. `tests/acceptance/test_n2_cut7.py` — cut 7's declaration accounting, its N2
   audit, its portable journey, and its durable arms.

Cut 5's and cut 6's runners are historical and are never edited. Cut 7 §5
allows them as a prefix, so they are invoked as they stand and told only *where*
to work; nothing else about them is touched, and their own arguments are not
this command's to pass. Extra arguments reach phase 3's `pytest` and no other.
A prefix that fails stops the command, and the phase banners are what let a
reader attribute a count or a failure to the phase that produced it — the whole
point of a prefix is that its meaning is unchanged, and a run whose three
results are indistinguishable would have lost exactly that.

Usage::

    python tools/cut7_acceptance.py                # every phase
    python tools/cut7_acceptance.py -k journey     # further arguments reach phase 3

The work directory is `<repo>/.cut7-acceptance` unless `SCIENCE_CUT7_ROOT`
names another one — a host whose certified volume is not the one the checkout
lives on sets that. Every phase runs beneath one directory under it, so the
whole command occupies one certified volume and leaves nothing behind.

**Never run beside another acceptance command or the ordinary suite.** All four
cut roots are environment-scoped and two runs would delete each other's roots
mid-transaction, which reads as an engine failure and is not one.
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
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut7-acceptance"

PREFIX_RUNNERS = ("cut5_acceptance.py", "cut6_acceptance.py")
"""The prior cuts' own commands, in cut order, run as they stand."""

PROBE_REFUSED = 2
"""Distinct from pytest's own codes: *the arms did not run* is not *an arm
failed*, and a caller that cannot tell them apart learns nothing from either."""


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT7_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    """Register and drop one throwaway world root and one corpus root.

    Both, because cut 7's durable arms write to both: a world root carries the
    rules store and the epochs, and a corpus root carries the records the epoch
    captures. A probe that registered only one would pass on a host where the
    other refuses, which is the failure this command exists to make loud.
    """
    from beliefs.root import init_corpus_root, init_world_root, metadata_root_for
    from beliefs.world import WorldConfig

    world_root = run / "probe-world"
    corpus_root = run / "probe-corpus"
    try:
        init_world_root(WorldConfig(world_root, "0" * 32, ()))
        init_corpus_root(corpus_root)
        return None
    except Exception as refused:  # noqa: BLE001 - report the engine's own refusal
        return f"{type(refused).__name__}: {refused}"
    finally:
        for root in (world_root, corpus_root):
            shutil.rmtree(root, ignore_errors=True)
            shutil.rmtree(metadata_root_for(root), ignore_errors=True)


def run_prefix(runner: str, run: Path) -> int:
    """One prior cut's own command, unedited, working beneath `run`."""
    completed = subprocess.run(
        [sys.executable, str(TOOLS / runner)],
        cwd=PYTHON_ROOT,
        check=False,
        env={**os.environ, "SCIENCE_CUT5_ROOT": str(run), "SCIENCE_CUT6_ROOT": str(run)},
    )
    return completed.returncode


def main(argv: list[str]) -> int:
    n2 = ACCEPTANCE / "test_n2_cut7.py"
    if not n2.is_file():
        print(f"cut-7 required acceptance module is missing: {n2}", file=sys.stderr)
        return 1
    for runner in PREFIX_RUNNERS:
        if not (TOOLS / runner).is_file():
            print(f"cut-7 required prefix runner is missing: {TOOLS / runner}", file=sys.stderr)
            return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-7 acceptance cannot run here: the volume beneath "
                f"{work} is not on the engine's certified allowlist.\n"
                f"  the engine refused with {refusal}\n"
                "  set SCIENCE_CUT7_ROOT to a directory on a certified volume, or recertify with the\n"
                "  engine's own tooling. This is an error, not a skip: an environment that cannot\n"
                "  exercise durability must not be able to report cut-7 discharge.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        for index, runner in enumerate(PREFIX_RUNNERS, start=1):
            print(f"[cut7 phase {index}/3] {runner}", flush=True)
            returncode = run_prefix(runner, run)
            if returncode != 0:
                print(
                    f"cut-7 acceptance stopped: the {runner} prefix exited {returncode}.\n"
                    "  A prior cut's arms are its own claim and cut 7 runs them unchanged, so this is\n"
                    "  that cut's failure and not a cut-7 one. Cut 7's arms did not run and cut 7 is\n"
                    "  not discharged.",
                    file=sys.stderr,
                )
                return returncode

        print(f"[cut7 phase 3/3] {n2.name}", flush=True)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(n2), *argv],
            cwd=PYTHON_ROOT,
            check=False,
            env={
                **os.environ,
                "SCIENCE_CUT4_ROOT": str(run),
                "SCIENCE_CUT5_ROOT": str(run),
                "SCIENCE_CUT6_ROOT": str(run),
                "SCIENCE_CUT7_ROOT": str(run),
            },
        )
        return completed.returncode
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
