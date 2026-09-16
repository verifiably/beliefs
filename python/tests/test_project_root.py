"""The project root's directory set is pinned.

Thirteen git-ignored work roots accumulated at the project root one variant at
a time (`.cut4-acceptance/` … `.mm30-reproduction-cut21/`), each added to
`.gitignore` as it appeared, until they outnumbered the genuine hidden
directories five to one, and nothing objected because nothing was watching.
The `.cut*-acceptance/` glob makes it worse: a new cut root appears with no
`.gitignore` edit at all. This test reads the directory itself, not git's
view of it, so an ignored directory is exactly what it sees.

Directories only. A stray file someone made by hand is not the signal; a
directory that a runner or a lane created is. The allowlist is explicit
names, never globs, so that the next `.cut32-acceptance/` is a red test rather
than the fourteenth silent variant.
"""

from __future__ import annotations

from pathlib import Path

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
        "caches — belong under .work/ (beliefs-5aad8c; set SCIENCE_CUT<n>_ROOT or the "
        "runner's DEFAULT_WORK there). Add a name to EXPECTED only for something that "
        "is not scratch."
    )

