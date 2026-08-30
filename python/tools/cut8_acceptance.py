"""The cut-8 acceptance command — log verification and anchoring, on the certified tuple.

**It errors off the certified tuple. It never skips.** An environment where
durability cannot be exercised must not be able to report cut-8 discharge, and
a skip is exactly how that happens: the run is green, the count is short, and
nobody reads the count. So the tuple is probed first, once, and a refusal ends
the command with the engine's own words.

Two phases, in order, each one a whole command:

1. `tools/cut7_acceptance.py`, unedited; and
2. `tests/acceptance/test_n2_cut8.py` — cut 8's declaration accounting, its N2
   audit, and its declaration-time obligations.

Cut 7's runner already chains cuts 5 and 6, so it is cut 8's **sole**
prior-cut prefix; invoking cut 5 or cut 6 again would run them twice. It is
historical and is never edited. **The frozen cut does not say this** — cut 8
§5 is its N2 obligations (fabrication well-formedness, count-claim
discipline), not a permission about prior runners, and no section of the
frozen cut mentions "prefix", "prior cut", or `cut7_acceptance`. The
authority for chaining it this way is the implementation plan's Task 11
(its Interfaces section), not the frozen cut, and that is stated here
rather than misattributed to it. It is invoked as it stands and told only
*where* to work; nothing else about it is touched, and its own arguments
are not this command's to pass. Extra arguments reach phase 2's `pytest`
and no other. A prefix that fails stops the command, and the phase banners
are what let a reader attribute a count or a failure to the phase that
produced it — the whole point of a prefix is that its meaning is unchanged,
and a run whose two results are indistinguishable would have lost exactly
that.

**Four numbers matter and only three are pytest summary lines.** Phase 1
prints cuts 5, 6, and 7's own N2 totals verbatim, unedited. Phase 2 prints
its own pytest total, which covers the 53-arm sabotage audit *plus* the
inventory, obligation, freeze, and guard checks made over the same
declarations — so it is not itself the fourth number. This command prints
one line after phase 2 naming that fourth number explicitly: the
**declared unit count** cut 8 §4 fixes (43 selected + 10 labeled), which is
`len(CUT8_ARMS)` and not a pytest total, pinned separately by
`test_the_declared_units_are_unique_and_number_fifty_three` among phase 2's
tests.

Usage::

    python tools/cut8_acceptance.py                # both phases
    python tools/cut8_acceptance.py -k obligation  # further arguments reach phase 2

The work directory is `<repo>/.cut8-acceptance` unless `SCIENCE_CUT8_ROOT`
names another one — a host whose certified volume is not the one the checkout
lives on sets that. Every phase runs beneath one directory under it, so the
whole command occupies one certified volume and leaves nothing behind.

**Never run beside another acceptance command or the ordinary suite.** All
five cut roots are environment-scoped and two runs would delete each other's
roots mid-transaction, which reads as an engine failure and is not one.
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
DEFAULT_WORK = PYTHON_ROOT.parent / ".cut8-acceptance"

PREFIX_RUNNERS = ("cut7_acceptance.py",)
"""The prior cut's own command, run as it stands. It already chains cuts 5
and 6, so it is the whole prior-cut prefix on its own."""

PROBE_REFUSED = 2
"""*The arms did not run* is not *an arm failed*, and a caller that cannot
tell them apart learns nothing from either. This is not, in fact, distinct
from pytest's own exit codes — `pytest.ExitCode.INTERRUPTED` is also 2 (cut-7
results §8) — so a caller must not tell a probe refusal from an interrupted
run by number alone; this command's own stderr names the refusal before
returning it, and that message is the actual signal."""


def work_directory() -> Path:
    configured = os.environ.get("SCIENCE_CUT8_ROOT")
    work = Path(configured) if configured else DEFAULT_WORK
    work.mkdir(parents=True, exist_ok=True)
    return work


def probe(run: Path) -> str | None:
    """Register and drop one throwaway world root and one corpus root.

    Both, because a host that cannot exercise durability must not be able to
    report cut-8 discharge either — a probe that registered only one would
    pass on a host where the other refuses, which is the failure this command
    exists to make loud.
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


def declared_unit_count() -> int:
    """Cut 8's declared unit count: `len(CUT8_ARMS)`, not a pytest total.

    `n2_arms_cut8` lives under `tests/acceptance`, which pytest puts on
    `sys.path` for its own run but this standalone script does not inherit —
    so both `tests/` and `tests/acceptance` are added here, for this one
    import, rather than assumed.

    The import is suppressed for the type checker because the path it resolves
    against is inserted three lines above, at call time: a static resolver
    cannot see that and reports the module missing. Suppressing it here keeps
    the project-wide `pyright` gate at its four known baseline diagnostics
    rather than teaching the whole project to resolve a test directory.
    """
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut8 import CUT8_ARMS  # pyright: ignore[reportMissingImports]

    return len(CUT8_ARMS)


def run_prefix(runner: str, run: Path) -> int:
    """The prior cut's own command, unedited, working beneath `run`."""
    completed = subprocess.run(
        [sys.executable, str(TOOLS / runner)],
        cwd=PYTHON_ROOT,
        check=False,
        env={**os.environ, "SCIENCE_CUT7_ROOT": str(run)},
    )
    return completed.returncode


def main(argv: list[str]) -> int:
    n2 = ACCEPTANCE / "test_n2_cut8.py"
    if not n2.is_file():
        print(f"cut-8 required acceptance module is missing: {n2}", file=sys.stderr)
        return 1
    for runner in PREFIX_RUNNERS:
        if not (TOOLS / runner).is_file():
            print(f"cut-8 required prefix runner is missing: {TOOLS / runner}", file=sys.stderr)
            return 1

    work = work_directory()
    run = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    try:
        refusal = probe(run)
        if refusal is not None:
            print(
                "cut-8 acceptance cannot run here: the volume beneath "
                f"{work} is not on the engine's certified allowlist.\n"
                f"  the engine refused with {refusal}\n"
                "  set SCIENCE_CUT8_ROOT to a directory on a certified volume, or recertify with the\n"
                "  engine's own tooling. This is an error, not a skip: an environment that cannot\n"
                "  exercise durability must not be able to report cut-8 discharge.",
                file=sys.stderr,
            )
            return PROBE_REFUSED

        for index, runner in enumerate(PREFIX_RUNNERS, start=1):
            print(f"[cut8 phase {index}/2] {runner}", flush=True)
            returncode = run_prefix(runner, run)
            if returncode != 0:
                print(
                    f"cut-8 acceptance stopped: the {runner} prefix exited {returncode}.\n"
                    "  A prior cut's arms are its own claim and cut 8 runs them unchanged, so this is\n"
                    "  that cut's failure and not a cut-8 one. Cut 8's arms did not run and cut 8 is\n"
                    "  not discharged.",
                    file=sys.stderr,
                )
                return returncode

        print(f"[cut8 phase 2/2] {n2.name}", flush=True)
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
                "SCIENCE_CUT8_ROOT": str(run),
            },
        )
        try:
            units = declared_unit_count()
        except Exception as failure:  # noqa: BLE001 - report, do not mask the run's own result
            print(f"cut-8 acceptance: could not compute the declared-unit count: {failure}", file=sys.stderr)
        else:
            print(
                f"declared units: {units} (pinned by "
                "test_the_declared_units_are_unique_and_number_fifty_three, among the tests "
                "above; not itself a pytest total)",
                flush=True,
            )
        return completed.returncode
    finally:
        shutil.rmtree(run, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
