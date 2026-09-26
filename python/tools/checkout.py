"""The main checkout, beside which every certified work root lives.

A lane worktree under `.worktrees/` can sit on storage the durability allowlist
refuses, and on a host that keeps `.worktrees/` on its WORK_ROOT the worktree's
resolved path is not under the main checkout at all. So the main checkout is
read from git's own worktree link (`.git` names the admin directory, whose
`commondir` names the shared `.git`), never inferred from the path.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main_checkout(repo_root: Path) -> Path:
    marker = repo_root / ".git"
    if marker.is_dir():
        return repo_root
    text = marker.read_text()
    if not text.startswith("gitdir: "):
        raise ValueError(f"{marker} is neither a git directory nor a worktree's gitdir link")
    admin = Path(text.removeprefix("gitdir: ").strip())
    common = admin / (admin / "commondir").read_text().strip()
    return Path(os.path.normpath(common)).parent


MAIN_CHECKOUT = main_checkout(REPO_ROOT)
