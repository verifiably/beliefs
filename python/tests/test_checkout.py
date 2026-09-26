"""The main checkout is read from git's worktree link, never from the path.

A lane worktree on a host's WORK_ROOT resolves outside the main checkout, so
`REPO_ROOT.parents[1]` names a directory on the uncertified volume (beliefs-ad68df).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from checkout import main_checkout


def test_a_main_checkout_is_its_own_main_checkout(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    assert main_checkout(tmp_path) == tmp_path


def test_a_worktree_elsewhere_resolves_through_its_gitdir_link(tmp_path: Path) -> None:
    main = tmp_path / "main"
    admin = main / ".git" / "worktrees" / "lane"
    admin.mkdir(parents=True)
    (admin / "commondir").write_text("../..\n")
    worktree = tmp_path / "work-root" / "beliefs" / ".worktrees" / "lane"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {admin}\n")
    assert main_checkout(worktree) == main


def test_a_git_file_that_is_not_a_worktree_link_is_refused(tmp_path: Path) -> None:
    (tmp_path / ".git").write_text("not a link\n")
    with pytest.raises(ValueError, match="gitdir"):
        main_checkout(tmp_path)


def test_a_tree_outside_git_is_refused(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        main_checkout(tmp_path)
