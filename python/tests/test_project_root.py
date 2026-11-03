"""The project root's directory set is pinned.

Git-ignored work roots accumulated at the project root one variant at
a time (one per acceptance or reproduction variant), each added to
`.gitignore` as it appeared, until they outnumbered the genuine hidden
directories five to one, and nothing objected because nothing was watching.
A glob in `.gitignore` makes it worse: a new root appears with no
`.gitignore` edit at all. This test reads the directory itself, not git's
view of it, so an ignored directory is exactly what it sees.

Directories only. A stray file someone made by hand is not the signal; a
directory that a runner or a lane created is. The allowlist is explicit
names, never globs, so that the next new root is a red test rather
than one more silent variant.
"""

from __future__ import annotations

import os
from pathlib import Path

from checkout import MAIN_CHECKOUT

ROOT = Path(__file__).parents[2]

#: Tracked trees and the tool, harness and editor directories that belong at the root.
EXPECTED = frozenset(
    {
        "contracts",
        "docs",
        "domains",
        "fixtures",
        "python",
        "tasks",
        "tools",
        "ts",
        ".git",
        ".githooks",
        ".github",
        ".worktrees",
        ".work",
        ".tt",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
        ".claude",
        ".agents",
        ".codex",
        ".superpowers",
        ".vscode",
        ".idea",
    }
)

#: Work roots that predate `.work/` and still sit at the root of the main checkout.
#: Each is named, not globbed: `beliefs-5aad8c` retires them by moving the runner
#: defaults under `.work/acceptance/`, and a name leaves this set when its
#: directory does. Nothing is added here; a new work root goes under `.work/`.
LEGACY_WORK_ROOTS = frozenset(
    {
        ".cut4-acceptance",
        ".cut29-acceptance",
        ".cut30-acceptance",
        ".cut31-acceptance",
        ".lifecycle-wrappers-test",
    }
)


def test_the_project_root_holds_no_unlisted_directory() -> None:
    present = {entry.name for entry in ROOT.iterdir() if entry.is_dir()}
    unlisted = sorted(present - EXPECTED - LEGACY_WORK_ROOTS)
    assert not unlisted, (
        f"unlisted director{'y' if len(unlisted) == 1 else 'ies'} at the project root: "
        f"{', '.join(unlisted)}. Work roots — acceptance runs, reproduction corpora, "
        "caches — belong under .work/ (beliefs-5aad8c; set BELIEFS_TEST_ROOT or "
        "BELIEFS_ACCEPTANCE_ROOT there). Add a name to EXPECTED only for something that "
        "is not scratch."
    )


def test_an_empty_test_root_uses_the_main_checkout_fallback(monkeypatch, request):
    monkeypatch.setenv("BELIEFS_TEST_ROOT", "")
    work = request.getfixturevalue("certified_work")
    assert work.parent.resolve() == (MAIN_CHECKOUT / ".work" / "tests").resolve()


def test_an_old_cut_root_variable_names_its_replacement(monkeypatch):
    from acceptance_runner import refuse_old_roots

    monkeypatch.setenv("SCIENCE_CUT10_ROOT", "/x")
    message = refuse_old_roots(os.environ)
    assert message is not None and "BELIEFS_TEST_ROOT" in message
