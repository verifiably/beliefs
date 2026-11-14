"""Check the editable refs sibling before uv needs it; never edit its registry."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def setup(root: Path) -> None:
    root = root.resolve()
    sibling = root.parent / "refs"
    if not sibling.exists() and not sibling.is_symlink():
        listing = subprocess.run(
            ["git", "-C", str(root), "worktree", "list", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        main = Path(listing.splitlines()[0].removeprefix("worktree ")).resolve()
        target = main.parent / "refs"
        if main != root and (target / "python/pyproject.toml").is_file():
            sibling.symlink_to(target, target_is_directory=True)
    if not (sibling / "python/pyproject.toml").is_file():
        raise ValueError("missing refs sibling; clone refs beside the main checkout, then run just registry-sync there")
    registry = sibling / "registry"
    data = sibling / "python/src/refs/data"
    expected = {p.name: p.read_bytes() for p in registry.iterdir() if p.is_file()} if registry.is_dir() else {}
    actual = {p.name: p.read_bytes() for p in data.iterdir() if p.is_file()} if data.is_dir() else {}
    if not expected or actual != expected:
        raise ValueError("refs registry is missing or stale; run just registry-sync in the selected refs sibling")


if __name__ == "__main__":
    try:
        setup(Path(sys.argv[1]))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"setup: {exc}", file=sys.stderr)
        sys.exit(1)
