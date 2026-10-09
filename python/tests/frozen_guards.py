"""Reading a conformance guard's freeze pins without running it.

A guard module pins prior-cut files two ways: by commit, where the claim is *this file
has not changed since the commit named*, and by content, where the claim is *these
bytes*. On a `.py` target both claims hold up to formatting (`pin_equivalence`, frozen
guard doctrine §8). Both are module-level `FROZEN_*` dictionaries mapping a repository-
relative path to the pin. Nothing here executes a guard — the modules this reads import
the kernel and spawn audits, and a cited-not-run guard cannot be imported at all on a
tree that has moved past it, which is the whole reason its pins have to be readable
statically.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
from dataclasses import dataclass
from functools import cache
from hashlib import sha256
from pathlib import Path

import pin_equivalence

_SHA256_LENGTH = 64
_DECLARATION_DIGEST = re.compile(r"CUT\d+_DECLARATION_SHA256")
_DECLARATION_COMMIT = re.compile(r"CUT\d+_DECLARATION_COMMIT")


@dataclass(frozen=True)
class Pin:
    """One entry of one table: what it names, and what it claims about it."""

    guard: str
    table: str
    target: str
    pin: str

    @property
    def is_content_pin(self) -> bool:
        return len(self.pin) == _SHA256_LENGTH and all(c in "0123456789abcdef" for c in self.pin)


def module_constants(tree: ast.Module) -> dict[str, str]:
    """The module-level string names a table may spell its pins with.

    `RENAME_COMMIT = "5a02ca2"` and its siblings are how several guards avoid repeating
    one commit across a dozen entries, so a reader that only understood literals would
    silently see fewer pins than the guard enforces.
    """
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = node.value.value
    return constants


def pins_in(guard: Path) -> tuple[Pin, ...]:
    """Every freeze pin the guard declares, in declaration order."""
    tree = ast.parse(guard.read_text(encoding="utf-8"))
    constants = module_constants(tree)
    pins: list[Pin] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        table = next((name for name in names if name.startswith("FROZEN_")), None)
        if table is None:
            continue
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                pin = value.value
            elif isinstance(value, ast.Name) and value.id in constants:
                pin = constants[value.id]
            else:
                continue
            pins.append(Pin(guard=guard.name, table=table, target=key.value, pin=pin))
    return tuple(pins)


def _string_tuple(tree: ast.Module, name: str) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        if isinstance(node.value, ast.Tuple):
            return tuple(
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )
    return ()


def live_inventory(runner: Path) -> frozenset[str]:
    """Every acceptance module the runner runs, following its prefix runners.

    A runner names only its immediate prefix — cut 21 names cut 20 — so the whole
    current-tree inventory is reachable only transitively. A chain that re-roots, as cut
    17 does with an empty `PREFIX_RUNNERS` and an explicit list, ends the walk there:
    what an older runner would have run is not what the tree runs today.
    """
    tree = ast.parse(runner.read_text(encoding="utf-8"))
    modules = set(_string_tuple(tree, "PHASE_MODULES"))
    for prefix in _string_tuple(tree, "PREFIX_RUNNERS"):
        modules |= live_inventory(runner.parent / prefix)
    return frozenset(modules)


def newest_runner(repo_root: Path) -> Path:
    """The head of the chain: the highest-numbered cut runner in the tree.

    The newest cut's runner is the one that defines *live*, discharged or not. A cut
    being prepared has already re-rooted or extended the chain, and a guard it dropped
    is out of the live set from the moment the runner says so — which is when the
    dropping has to be ruled, not later.
    """
    runners = {
        int("".join(c for c in path.stem if c.isdigit())): path
        for path in (repo_root / "python" / "tools").glob("cut*_acceptance.py")
    }
    return runners[max(runners)]


def guard_modules(repo_root: Path) -> tuple[Path, ...]:
    """Every conformance guard module in the tree, oldest cut first."""
    acceptance = repo_root / "python" / "tests" / "acceptance"
    return tuple(
        sorted(acceptance.glob("test_n2_cut*.py"), key=lambda p: int("".join(c for c in p.stem if c.isdigit())))
    )


def live_guards(repo_root: Path) -> tuple[Path, ...]:
    """The guard modules the newest runner's chain actually runs."""
    inventory = live_inventory(newest_runner(repo_root))
    return tuple(guard for guard in guard_modules(repo_root) if guard.name in inventory)


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(repo_root), *args], check=False, capture_output=True)


@cache
def _commit_resolves(repo_root: Path, commit: str) -> bool:
    return _git(repo_root, "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0


def _blob(repo_root: Path, commit: str, target: str) -> bytes | None:
    shown = _git(repo_root, "cat-file", "blob", f"{commit}:{target}")
    return shown.stdout if shown.returncode == 0 else None


@cache
def _original_with_digest(repo_root: Path, target: str, digest: str) -> bytes | None:
    """The version of `target` in HEAD's history whose SHA-256 is `digest`, if any.

    The key carries the resolved repository root: a blob found in one repository's
    history is never evidence about another's.
    """
    listed = _git(repo_root, "rev-list", "--full-history", "HEAD", "--", target)
    if listed.returncode != 0:
        return None
    for commit in listed.stdout.decode("ascii").split():
        original = _blob(repo_root, commit, target)
        if original is not None and sha256(original).hexdigest() == digest:
            return original
    return None


def commit_pin_holds(repo_root: Path, target: str, commit: str) -> bool:
    """Whether the working file still is, up to formatting, what `commit` held at `target`.

    A target absent at the pin holds only while it stays absent; a commit that no longer
    resolves is a broken pin, never an absent target.
    """
    root = repo_root.resolve()
    if not _commit_resolves(root, commit):
        return False
    original = _blob(root, commit, target)
    path = root / target
    if original is None:
        return not os.path.lexists(path)  # a dangling symlink is present
    return path.is_file() and pin_equivalence.equivalent(original, path.read_bytes(), path=target)


def content_pin_holds(repo_root: Path, target: str, digest: str) -> bool:
    """Whether the working file still is, up to formatting, the bytes `digest` names.

    Identical bytes hold without reading history. Otherwise the digest must resolve to a
    version of `target` in HEAD's history, and the working file must be equivalent to it;
    a digest no version matches is a broken pin.
    """
    root = repo_root.resolve()
    path = root / target
    if not path.is_file():
        return False
    current = path.read_bytes()
    if sha256(current).hexdigest() == digest:
        return True
    original = _original_with_digest(root, target, digest)
    return original is not None and pin_equivalence.equivalent(original, current, path=target)


def holds(pin: Pin, *, repo_root: Path) -> bool:
    """Whether the tree still satisfies the pin's own claim, up to formatting (doctrine §8)."""
    if pin.is_content_pin:
        return content_pin_holds(repo_root, pin.target, pin.pin)
    return commit_pin_holds(repo_root, pin.target, pin.pin)


def broken_pins(guard: Path, *, repo_root: Path) -> tuple[Pin, ...]:
    """The guard's pins the tree has falsified."""
    return tuple(pin for pin in pins_in(guard) if not holds(pin, repo_root=repo_root))


def declaration_pin(guard: Path) -> str | None:
    """The guard's scalar freeze: the declaration file its `CUTN_DECLARATION_SHA256` holds.

    Cuts 26 onwards name their own arm declaration as a module-level `FROZEN_DECLARATION`
    and pin it with a scalar digest (cuts 27-30 add a `CUTN_DECLARATION_COMMIT`).
    `pins_in` reads only the `FROZEN_*` tables, so this is the second form a freeze takes.
    """
    return module_constants(ast.parse(guard.read_text(encoding="utf-8"))).get("FROZEN_DECLARATION")


def _named_constant(guard: Path, pattern: re.Pattern[str]) -> str | None:
    constants = module_constants(ast.parse(guard.read_text(encoding="utf-8")))
    matches = [value for name, value in constants.items() if pattern.fullmatch(name)]
    if len(matches) > 1:
        raise ValueError(f"{guard.name} declares more than one {pattern.pattern}")
    return matches[0] if matches else None


def declaration_digest(guard: Path) -> str | None:
    """The SHA-256 the guard's scalar freeze pins its `FROZEN_DECLARATION` to."""
    return _named_constant(guard, _DECLARATION_DIGEST)


def declaration_commit(guard: Path) -> str | None:
    """The commit cuts 27-30 also pin their `FROZEN_DECLARATION` to."""
    return _named_constant(guard, _DECLARATION_COMMIT)
