"""Reading the arms a conformance guard audits, and whether the tree still matches them.

An N2 arm names a sabotage — a `before` block that must occur exactly once in one kernel
module — and the checks that must fail once it is applied. When the kernel moves under
the block, the sabotage matches nothing, the copy is left untouched, every check passes,
and the arm scores healthy: `test_n2.py` calls that finding **stale**, and it is the one
that accumulates silently, because the audit that would report it runs only at a
discharge. This module measures staleness without running any audit, the way
`frozen_guards` reads pin tables without running any guard.

What is measured is what the guard runs, not what the declaration file says. A live
guard may carry a `_LIVE_SABOTAGES` table that re-targets a frozen declaration at the
landed source — the declaration file stays byte-exact under its pins, the guard's
`CUTN_ARMS` is the re-targeted tuple — and a guard whose module names a
`CUTN_SOURCE_COMMIT` audits against that commit's tree rather than the working tree. A
cited-not-run guard cannot be imported on a tree that has moved past it, so its arms are
read from the declaration file it names, as evidence.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from n2_arms import Arm, installed_nodes_root

_CUT_NUMBER = re.compile(r"cut(\d+)")


@dataclass(frozen=True)
class StaleArm:
    """One arm whose sabotage no longer applies to the tree it is audited against."""

    guard: str
    key: str
    """`row[index]` — the row and the arm's position in the tuple the guard audits."""
    module: str
    matches: int | None
    """How many times the `before` block occurs; `None` when the module is not there."""


class TreeReader(Protocol):
    """A module's source in one package's tree, or `None` when the tree has no such module.

    `package` defaults so that every reader can be called with a module alone, as the
    Beliefs-only callers always have; a `nodes` arm passes its own package.
    """

    def __call__(self, module: str, package: str = "beliefs") -> str | None: ...


def cut_number(guard: Path) -> int:
    match = _CUT_NUMBER.search(guard.stem)
    if match is None:
        raise ValueError(f"{guard.name} is not a cut guard")
    return int(match.group(1))


def _load(path: Path, *, search: Sequence[Path]) -> object:
    """Import a module by path with `search` prepended for the module's own imports."""
    if path.stem in sys.modules:
        return sys.modules[path.stem]
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    inserted = [str(p) for p in search if str(p) not in sys.path]
    sys.path[:0] = inserted
    try:
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(path.stem, None)
        raise
    finally:
        for entry in inserted:
            sys.path.remove(entry)
    return module


def declared_arms(guard: Path, *, repo_root: Path) -> tuple[Arm, ...]:
    """The arms a guard's declaration file spells, read without importing the guard.

    The declaration module is the `from n2_arms_cutN import CUTN_ARMS` the guard names;
    it imports nothing but `n2_arms`, so it loads on any tree. This is the evidence
    reading — what a cited-not-run guard's arms were when the cut discharged.
    """
    tests = repo_root / "python" / "tests"
    own = f"n2_arms_cut{cut_number(guard)}"
    tree = ast.parse(guard.read_text(encoding="utf-8"))
    if not any(isinstance(node, ast.ImportFrom) and node.module == own for node in tree.body):
        raise ValueError(f"{guard.name} does not import {own}")
    declaration = next(p for p in (tests / f"{own}.py", tests / "acceptance" / f"{own}.py") if p.is_file())
    module = _load(declaration, search=(tests, tests / "acceptance"))
    return tuple(getattr(module, f"CUT{cut_number(guard)}_ARMS"))


def audited_arms(guard: Path, *, repo_root: Path) -> tuple[Arm, ...]:
    """The arms the guard audits — its `CUTN_ARMS` after any `_LIVE_SABOTAGES` re-targeting.

    This imports the guard, which a live guard permits: importing is what the
    discharge does before collecting it.
    """
    tests = repo_root / "python" / "tests"
    module = _load(guard, search=(tests, tests / "acceptance"))
    return tuple(getattr(module, f"CUT{cut_number(guard)}_ARMS"))


def re_targeted_rows(guard: Path, *, repo_root: Path) -> frozenset[str]:
    """The rows the guard's `_LIVE_SABOTAGES` table re-targets; empty when it has none."""
    tests = repo_root / "python" / "tests"
    module = _load(guard, search=(tests, tests / "acceptance"))
    return frozenset(getattr(module, "_LIVE_SABOTAGES", {}))


def audited_tree(guard: Path, *, repo_root: Path) -> TreeReader:
    """A reader for the kernel tree the guard's sabotages are applied to.

    The working tree, unless the guard pins a `CUTN_SOURCE_COMMIT` for its own cut — cut 6
    does, because its arms name a module the tree has since promoted to a package and
    the design forbids recreating as a shim. The package at a historical commit is found
    under its name at that commit: `science` before the rename at `5a02ca2`, `beliefs`
    after it.
    """
    tests = repo_root / "python" / "tests"
    module = _load(guard, search=(tests, tests / "acceptance"))
    commit = getattr(module, f"CUT{cut_number(guard)}_SOURCE_COMMIT", None)
    if commit is None:
        return working_tree(repo_root)
    return historical_tree(commit, repo_root=repo_root)


def working_tree(repo_root: Path) -> TreeReader:
    roots = {"beliefs": repo_root / "python" / "src" / "beliefs", "nodes": installed_nodes_root()}

    def read(module: str, package: str = "beliefs") -> str | None:
        path = roots[package] / module
        return path.read_text(encoding="utf-8") if path.is_file() else None

    return read


def historical_tree(commit: str, *, repo_root: Path) -> TreeReader:
    def read(module: str, package: str = "beliefs") -> str | None:
        if package != "beliefs":
            return None  # a nodes arm has no Beliefs commit to read from; it reads as stale here
        for source_package in ("python/src/science", "python/src/beliefs"):
            completed = subprocess.run(
                ["git", "-C", str(repo_root), "show", f"{commit}:{source_package}/{module}"],
                check=False,
                capture_output=True,
            )
            if completed.returncode == 0:
                return completed.stdout.decode("utf-8")
        return None

    return read


def stale_arms(guard: str, arms: Sequence[Arm], read: TreeReader) -> tuple[StaleArm, ...]:
    """Every arm whose `before` block does not occur exactly once in the tree `read` reads.

    Exactly once is `test_n2._sabotage`'s own rule: zero matches mutates nothing, and two
    would mutate both, so both are the same failure to say which line the arm means.
    """
    stale: list[StaleArm] = []
    for index, arm in enumerate(arms):
        source = read(arm.sabotage.module, arm.sabotage.package)
        matches = None if source is None else source.count(arm.sabotage.before)
        if matches != 1:
            stale.append(StaleArm(guard=guard, key=f"{arm.row}[{index}]", module=arm.sabotage.module, matches=matches))
    return tuple(stale)
