# ruff format in the gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reformat `python/` once with ruff format, enforce `ruff format --check` in the gate, and leave every freeze pin holding and every live N2 arm auditing what its cut declared.

**Architecture:** A format-only exclude protects every file a freeze claims, derived from the guards (`frozen_guards.protected_paths`) and held equal to the pyproject list by a portable test. One generated commit reformats everything else. A committed tool derives each stale live arm's formatted twin with an exact-equivalence check, the guards carry them through `_LIVE_SABOTAGES`, and the gate gains the format check last.

**Tech Stack:** Python 3.11+, ruff 0.16.1 (pinned by `python/uv.lock`), pytest through `just test-one` / `just test-fast`, git, the N2 machinery under `python/tests/` (`frozen_guards.py`, `arm_staleness.py`, `cited_not_run.py`, `n2_arms.py`).

**Spec:** `docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md` (task `beliefs-a555d6`; follow-up `beliefs-ea5ec7` retires the exclude).

## Global Constraints

- Work in `.worktrees/ruff-format-gate` on branch `chore/ruff-format-gate`. Every path shown to the user is prefixed `.worktrees/ruff-format-gate/`.
- Run every ruff call as `uv run --frozen ruff …` from `python/`; ruff is 0.16.1 and is never upgraded in this branch.
- Never edit a file in the protected set (the 56 paths of Task 1), a `FROZEN_*` table, a `CUTN_*_SHA256`/`CUTN_*_COMMIT` constant, a declaration file `n2_arms_cutN.py`, or `cited_not_run.py`'s existing entries.
- A live arm is re-targeted only through its guard's `_LIVE_SABOTAGES` (plus `_LIVE_SABOTAGE_INDICES` in cut 7); a cited-not-run arm is only recorded in `cited_not_run.py`'s `stale_arms`.
- Commit order is the spec's §4: exclude, tool, reformat, re-targets, gate. The reformat commit holds only `ruff format` output plus the displaced suppression comments moved back.
- `root.py` is the one `atoms` importer (`test_capability_boundary.py`): no new or edited module imports `atoms`.
- This is not a conformance cut: no adoption-ledger row, no `test_recent_cut_acceptance.py` row, no cut document.
- Tests run through `just test-one <runner args>` (paths relative to `python/`) and `just test-fast`; never call pytest directly. The cut runner is a tool and runs as `host-budget run -- uv run --frozen python tools/cut46_acceptance.py`.
- Acceptance-touching runs start from the canonical path: `cd "$(pwd -P)"` inside the worktree first (an `open_root` ELOOP otherwise comes from the `.worktrees` symlink, not a regression).
- Long runs (the cut chain, `just gate`) go through Bash `run_in_background: true` with `set -o pipefail` and `tee` into `.work/ruff-format-gate/`, with a timeout that covers the run; never `nohup`, `&`, or `detached.sh`.
- Use conventional commits and no AI attribution trailer, co-author line, or session URL.

## Review Focus

1. A protected file formatted by explicit path (an editor's format-on-save, `ruff format tests/n2_arms_cut46.py`) must be left alone: `force-exclude = true` — Task 1 tests it through the ruff CLI.
2. A pin naming a file that no longer exists (`python/tests/n2_arms_cut25.py`) must not appear in the exclude, and a new freeze in a synthetic guard must enter the protected set by both pin forms — Task 1 tests both.
3. An arm already stale before the reformat (its `before` absent or doubled in the base source) must be refused, never re-targeted onto a guess — Task 2 tests zero and two occurrences.
4. A sabotage whose `after` is not valid Python must refuse with ruff's parse error named — Task 2 tests it.
5. `main` moving before landing must regenerate the reformat, never hand-merge it — Task 6 Step 1 checks and states the procedure.

---

### Task 1: The protected set and the format exclude

**Files:**
- Modify: `python/tests/frozen_guards.py` (rename `_module_constants` → `module_constants`; add `declaration_pin`, `protected_paths`)
- Modify: `python/pyproject.toml` (`[tool.ruff]` gains `force-exclude`; new `[tool.ruff.format]` table)
- Test: `python/tests/test_frozen_guards.py`

**Interfaces:**
- Produces: `frozen_guards.module_constants(tree: ast.Module) -> dict[str, str]`; `frozen_guards.declaration_pin(guard: Path) -> str | None` (a repository-relative path such as `"python/tests/n2_arms_cut46.py"`); `frozen_guards.protected_paths(repo_root: Path) -> frozenset[str]` (paths relative to `python/`, existing `.py` files only, e.g. `"tests/n2_arms_cut46.py"`).

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_frozen_guards.py`, adding `import tomllib` to the imports (alphabetical, after `import sys`):

```python
PYPROJECT = REPO_ROOT / "python" / "pyproject.toml"


def test_the_protected_set_reads_both_freeze_forms_and_cited_surfaces(tmp_path) -> None:
    """A freeze claims a file by table pin or by `FROZEN_DECLARATION`; either one protects it.

    The synthetic tree holds one guard using both forms. Cited-not-run surfaces are read from
    the real registry and filtered to files that exist, so none appears here.
    """
    python = tmp_path / "python"
    (python / "tests" / "acceptance").mkdir(parents=True)
    (python / "tools").mkdir()
    for name in ("tests/n2_arms_cut99.py", "tests/acceptance/test_n2_cut98.py", "tools/cut98_acceptance.py"):
        (python / name).write_text("x = 1\n", encoding="utf-8")
    (python / "tests" / "acceptance" / "test_n2_cut99.py").write_text(
        'FROZEN_DECLARATION = "python/tests/n2_arms_cut99.py"\n'
        "FROZEN_PRIOR_CUT_FILES = {\n"
        '    "python/tests/acceptance/test_n2_cut98.py": "abc1234",\n'
        '    "python/tools/cut98_acceptance.py": "abc1234",\n'
        '    "python/tests/n2_arms_cut97.py": "abc1234",\n'
        '    "docs/plans/cut-98-results.md": "abc1234",\n'
        "}\n",
        encoding="utf-8",
    )

    assert frozen_guards.declaration_pin(python / "tests" / "acceptance" / "test_n2_cut99.py") == (
        "python/tests/n2_arms_cut99.py"
    )
    assert frozen_guards.protected_paths(tmp_path) == frozenset(
        {"tests/n2_arms_cut99.py", "tests/acceptance/test_n2_cut98.py", "tools/cut98_acceptance.py"}
    )


def test_the_format_exclude_is_exactly_the_protected_set() -> None:
    """Formatting must not touch a file a freeze claims (spec 2026-10-09 §3.1).

    Pins are byte-exact, so ruff format excludes every file a guard pins, by table or by its
    scalar `FROZEN_DECLARATION`, plus every cited-not-run surface the doctrine makes evidence
    whether or not a pin names it. beliefs-ea5ec7 retires this list and this test together.
    """
    ruff = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["ruff"]
    exclude = ruff["format"]["exclude"]
    protected = frozen_guards.protected_paths(REPO_ROOT)

    assert ruff["force-exclude"] is True
    assert exclude == sorted(set(exclude))
    assert "tests/n2_arms_cut46.py" in protected  # the scalar form: no table pins it
    assert "tests/acceptance/test_n2_cut4.py" in protected  # cited, and no pin names it
    assert "tests/n2_arms_cut25.py" not in protected  # a falsified pin on a removed file
    assert set(exclude) == protected


def test_an_explicit_path_cannot_format_a_protected_file() -> None:
    """An editor formats by explicit path; `force-exclude` keeps the exclude in force there."""
    completed = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "tests/n2_arms_cut46.py"],
        cwd=REPO_ROOT / "python",
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_frozen_guards.py -k "protected or exclude or explicit_path"`
Expected: 3 failed — `AttributeError: module 'frozen_guards' has no attribute 'declaration_pin'`, `KeyError: 'format'`, and the explicit-path test reporting `Would reformat: tests/n2_arms_cut46.py`.

- [ ] **Step 3: Implement the protected set**

In `python/tests/frozen_guards.py`, rename `_module_constants` to `module_constants` (its one caller is `pins_in`), add `from cited_not_run import CITED_NOT_RUN` after the stdlib imports, and append:

```python
def declaration_pin(guard: Path) -> str | None:
    """The guard's scalar freeze: the declaration file its `CUTN_DECLARATION_SHA256` holds.

    Cuts 26 onwards name their own arm declaration as a module-level `FROZEN_DECLARATION`
    and pin it byte-exact with a scalar digest (cuts 27-30 add a `CUTN_DECLARATION_COMMIT`).
    `pins_in` reads only the `FROZEN_*` tables, so this is the second form a freeze takes.
    """
    return module_constants(ast.parse(guard.read_text(encoding="utf-8"))).get("FROZEN_DECLARATION")


def protected_paths(repo_root: Path) -> frozenset[str]:
    """Every existing Python file a freeze claims, relative to `python/`.

    A file is claimed when a guard pins it by table or by its scalar declaration pin, or
    when it is a cited-not-run surface (guard, declaration, runner), which doctrine §2
    makes evidence whether or not a later cut pinned it. Formatting excludes exactly
    this set (spec 2026-10-09 §3.1).
    """
    claimed: set[str] = set()
    for guard in guard_modules(repo_root):
        claimed.update(pin.target for pin in pins_in(guard))
        declaration = declaration_pin(guard)
        if declaration is not None:
            claimed.add(declaration)
    for name, standing in CITED_NOT_RUN.items():
        cut = standing.cut
        claimed.update(
            {
                f"python/tests/acceptance/{name}",
                f"python/tests/n2_arms_cut{cut}.py",
                f"python/tests/acceptance/n2_arms_cut{cut}.py",
                f"python/tools/cut{cut}_acceptance.py",
            }
        )
    return frozenset(
        path.removeprefix("python/")
        for path in claimed
        if path.startswith("python/") and path.endswith(".py") and (repo_root / path).is_file()
    )
```

- [ ] **Step 4: Add the exclude to `python/pyproject.toml`**

Replace the `[tool.ruff]` table with:

```toml
[tool.ruff]
line-length = 120
force-exclude = true

# Freeze-protected files: byte-exact under a guard's pin, or cited-not-run evidence.
# tests/test_frozen_guards.py holds this list equal to frozen_guards.protected_paths;
# beliefs-ea5ec7 makes pins hold modulo formatting and removes it.
[tool.ruff.format]
exclude = [
    "tests/acceptance/n2_arms_cut10.py",
    "tests/acceptance/n2_arms_cut11.py",
    "tests/acceptance/n2_arms_cut12.py",
    "tests/acceptance/n2_arms_cut13.py",
    "tests/acceptance/n2_arms_cut14.py",
    "tests/acceptance/n2_arms_cut15.py",
    "tests/acceptance/n2_arms_cut17.py",
    "tests/acceptance/n2_arms_cut19.py",
    "tests/acceptance/n2_arms_cut20.py",
    "tests/acceptance/n2_arms_cut21.py",
    "tests/acceptance/n2_arms_cut22.py",
    "tests/acceptance/n2_arms_cut23.py",
    "tests/acceptance/n2_arms_cut24.py",
    "tests/acceptance/n2_arms_cut25.py",
    "tests/acceptance/n2_arms_cut27.py",
    "tests/acceptance/n2_arms_cut28.py",
    "tests/acceptance/n2_arms_cut29.py",
    "tests/acceptance/n2_arms_cut30.py",
    "tests/acceptance/n2_arms_cut8.py",
    "tests/acceptance/n2_arms_cut9.py",
    "tests/acceptance/test_n2_cut10.py",
    "tests/acceptance/test_n2_cut4.py",
    "tests/acceptance/test_n2_cut5.py",
    "tests/acceptance/test_n2_cut6.py",
    "tests/acceptance/test_n2_cut8.py",
    "tests/n2_arms_cut16.py",
    "tests/n2_arms_cut18.py",
    "tests/n2_arms_cut20.py",
    "tests/n2_arms_cut26.py",
    "tests/n2_arms_cut3.py",
    "tests/n2_arms_cut31.py",
    "tests/n2_arms_cut32.py",
    "tests/n2_arms_cut33.py",
    "tests/n2_arms_cut34.py",
    "tests/n2_arms_cut35.py",
    "tests/n2_arms_cut36.py",
    "tests/n2_arms_cut37.py",
    "tests/n2_arms_cut38.py",
    "tests/n2_arms_cut39.py",
    "tests/n2_arms_cut4.py",
    "tests/n2_arms_cut40.py",
    "tests/n2_arms_cut41.py",
    "tests/n2_arms_cut42.py",
    "tests/n2_arms_cut43.py",
    "tests/n2_arms_cut44.py",
    "tests/n2_arms_cut45.py",
    "tests/n2_arms_cut46.py",
    "tests/n2_arms_cut5.py",
    "tests/n2_arms_cut6.py",
    "tests/n2_arms_cut7.py",
    "tools/cut10_acceptance.py",
    "tools/cut4_acceptance.py",
    "tools/cut5_acceptance.py",
    "tools/cut6_acceptance.py",
    "tools/cut7_acceptance.py",
    "tools/cut8_acceptance.py",
]
```

The list is in Python `sorted` order (byte order), which the test asserts. If the tree has moved since 2026-10-09 and the equality assertion reports a difference, the protected set is the authority: regenerate the list from `frozen_guards.protected_paths` and note the change on the task.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `just test-one tests/test_frozen_guards.py`
Expected: all pass, including the three new tests. Also run `cd python && uv run --frozen ruff check . && uv run --frozen pyright` — expected `All checks passed!` and `0 errors`.

- [ ] **Step 6: Commit**

```bash
git add python/tests/frozen_guards.py python/tests/test_frozen_guards.py python/pyproject.toml
git commit -m "test(guards): derive the freeze-protected set and exclude it from ruff format"
```

---

### Task 2: The re-target tool

**Files:**
- Create: `python/tools/retarget_formatted_arms.py`
- Test: `python/tests/test_retarget_formatted_arms.py`

**Interfaces:**
- Consumes: `arm_staleness.audited_arms`, `arm_staleness.audited_tree`, `arm_staleness.stale_arms`, `arm_staleness.working_tree`, `frozen_guards.live_guards` (existing, in `python/tests/`).
- Produces (module `retarget_formatted_arms`, importable from tests because `tools/` is on `pythonpath`):
  - `class RetargetRefused(Exception)`
  - `@dataclass(frozen=True) class Retarget: guard: str; index: int; row: str; module: str; original_before: str; original_after: str; before: str; after: str`
  - `Formatter = Callable[[str], str]`
  - `ruff_formatter(module: str) -> Formatter`
  - `derive_one(original: str, formatted: str, before: str, after: str, format_source: Formatter) -> tuple[str, str]`
  - `derive(base: str) -> tuple[tuple[Retarget, ...], tuple[str, ...]]` (entries, refusals)
  - `verify(base: str, entries: Sequence[Retarget]) -> tuple[str, ...]` (problems)
  - `render(entries: Sequence[Retarget]) -> str`
  - CLI: `derive --base <commit> --out <json> [--python]`, `verify --base <commit> --entries <json>`

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_retarget_formatted_arms.py`:

```python
"""The formatted twin of a sabotage: what `tools/retarget_formatted_arms.py` derives.

Every case runs the real pinned ruff, because the derivation's guarantee is about what ruff
does: the derived arm applied to the formatted source is exactly ruff's formatting of the
declared sabotage applied to the source before formatting.
"""

from __future__ import annotations

import pytest
from n2_arms import Sabotage
from retarget_formatted_arms import Retarget, RetargetRefused, derive_one, render, ruff_formatter

FORMAT = ruff_formatter("synthetic.py")


def _derive(original: str, before: str, after: str) -> tuple[str, str]:
    formatted = FORMAT(original)
    derived = derive_one(original, formatted, before, after, FORMAT)
    assert formatted.replace(*derived) == FORMAT(original.replace(before, after))
    return derived


def test_a_rewrapped_statement_carries_its_sabotage() -> None:
    original = "def f(a,b):\n    return a\n\nvalue = f(1,2)\n"

    assert _derive(original, "value = f(1,2)\n", "value = f(2,1)\n") == ("value = f(1, 2)\n", "value = f(2, 1)\n")


def test_an_after_that_rewraps_its_statement_is_taken_whole() -> None:
    original = "def f(*args):\n    return args\n\n\nvalue = f(1, 2)\n"
    long_call = "f(" + ", ".join(f"argument_number_{n}" for n in range(12)) + ")"

    before, after = _derive(original, "f(1, 2)", long_call)

    assert before == "value = f(1, 2)\n"
    assert after.count("\n") > 1


def test_a_sabotage_inside_one_line_becomes_that_whole_line() -> None:
    assert _derive("if x==1:\n    pass\n", "==1", "==2") == ("if x == 1:\n", "if x == 2:\n")


def test_a_region_that_is_not_unique_widens_until_it_is() -> None:
    original = "def a():\n    return None\n\n\ndef b():\n    return None\n"

    assert _derive(original, "def b():\n    return None", "def b():\n    return 1") == (
        "def b():\n    return None\n",
        "def b():\n    return 1\n",
    )


@pytest.mark.parametrize(
    ("original", "occurrences"),
    [("y = 2\n", 0), ("x = 1\nx = 1\n", 2)],
)
def test_an_arm_already_stale_before_formatting_is_refused(original: str, occurrences: int) -> None:
    with pytest.raises(RetargetRefused, match=f"occurs {occurrences} times"):
        derive_one(original, FORMAT(original), "x = 1\n", "x = 3\n", FORMAT)


def test_a_sabotage_formatting_erases_is_refused() -> None:
    original = "x = [1,2]\n"

    with pytest.raises(RetargetRefused, match="vanishes under formatting"):
        derive_one(original, FORMAT(original), "x = [1,2]\n", "x = [1, 2]\n", FORMAT)


def test_an_after_that_is_not_python_is_refused_with_ruffs_error() -> None:
    original = "x = 1\n"

    with pytest.raises(RetargetRefused, match="ruff cannot format"):
        derive_one(original, FORMAT(original), "x = 1\n", "def (\n", FORMAT)


def test_render_spells_entries_that_evaluate_back_to_themselves() -> None:
    entries = (
        Retarget("test_n2_cut99.py", 0, "Z1", "m.py", "a\n", "b\n", "    x = 1\n", "    x = 2\n"),
        Retarget("test_n2_cut99.py", 3, "Z2-a", "w/r.py", "c", "d", "if a:\n    b = '1'\n", 'if a:\n    b = "2"\n'),
    )

    table = eval("{" + render(entries) + "}", {"Sabotage": Sabotage})

    assert table == {
        "Z1": Sabotage(module="m.py", before="    x = 1\n", after="    x = 2\n"),
        "Z2-a": Sabotage(module="w/r.py", before="if a:\n    b = '1'\n", after='if a:\n    b = "2"\n'),
    }
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_retarget_formatted_arms.py`
Expected: collection error, `ModuleNotFoundError: No module named 'retarget_formatted_arms'`.

- [ ] **Step 3: Write the tool**

Create `python/tools/retarget_formatted_arms.py`:

```python
"""Carry live N2 arms across a formatting-only change to the kernel.

An arm's sabotage is a `before` block that must occur exactly once in a kernel module. A
formatter that re-wraps the module leaves the block matching nothing, and the arm goes
stale. Its formatted twin is derived, not hand-written. Let `S0` be the module before
formatting, `S1` after, and `(b, a)` the audited sabotage. Then `T1 = ruff(S0.replace(b, a))`
is the formatted program the arm used to audit, and `(b', a')` is the smallest line-aligned
region where `S1` and `T1` differ, widened until `b'` is unique in `S1`. The derivation is
accepted only when `S1.replace(b', a') == T1` byte for byte, so the re-targeted arm mutates
exactly the formatted form of what its cut declared.

Spec: docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md §3.3. From `python/`:

    uv run --frozen python tools/retarget_formatted_arms.py derive --base <commit> --out <json> [--python]
    uv run --frozen python tools/retarget_formatted_arms.py verify --base <commit> --entries <json>

`derive` runs on the formatted tree before any re-target lands, with `--base` the commit
before formatting; `verify` runs after the guards carry the entries.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType

PYTHON_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PYTHON_ROOT.parent
TESTS = PYTHON_ROOT / "tests"
ACCEPTANCE = TESTS / "acceptance"

Formatter = Callable[[str], str]


class RetargetRefused(Exception):
    """An arm the derivation cannot carry across formatting without changing what it mutates."""


@dataclass(frozen=True)
class Retarget:
    """One live arm's formatted twin, with the sabotage it replaces."""

    guard: str
    index: int
    row: str
    module: str
    original_before: str
    original_after: str
    before: str
    after: str


def ruff_formatter(module: str) -> Formatter:
    """Format source as the project formats `src/beliefs/<module>`, with its own configuration."""

    def format_source(source: str) -> str:
        completed = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--stdin-filename", f"src/beliefs/{module}", "-"],
            input=source,
            capture_output=True,
            text=True,
            cwd=PYTHON_ROOT,
            check=False,
        )
        if completed.returncode != 0:
            raise RetargetRefused(f"{module}: ruff cannot format the sabotaged source: {completed.stderr.strip()}")
        return completed.stdout

    return format_source


def derive_one(original: str, formatted: str, before: str, after: str, format_source: Formatter) -> tuple[str, str]:
    """The `(before, after)` that applied to `formatted` yields `format_source(original.replace(before, after))`."""
    occurrences = original.count(before)
    if occurrences != 1:
        raise RetargetRefused(f"the sabotage's before occurs {occurrences} times in the source before formatting")
    target = format_source(original.replace(before, after))
    old = formatted.splitlines(keepends=True)
    new = target.splitlines(keepends=True)
    if old == new:
        raise RetargetRefused("the sabotage vanishes under formatting")
    shortest = min(len(old), len(new))
    head = 0
    while head < shortest and old[head] == new[head]:
        head += 1
    tail = 0
    while tail < shortest - head and old[-1 - tail] == new[-1 - tail]:
        tail += 1
    start, old_end, new_end = head, len(old) - tail, len(new) - tail
    while True:
        derived_before = "".join(old[start:old_end])
        if derived_before and formatted.count(derived_before) == 1:
            break
        if start == 0 and old_end == len(old):
            raise RetargetRefused("no unique region of the formatted source carries the sabotage")
        if start > 0:
            start -= 1
        if old_end < len(old):
            old_end += 1
            new_end += 1
    derived_after = "".join(new[start:new_end])
    if formatted.replace(derived_before, derived_after) != target:
        raise RetargetRefused("the derived arm does not reproduce the formatted sabotage")
    return derived_before, derived_after


def _machinery() -> tuple[ModuleType, ModuleType]:
    for directory in (TESTS, ACCEPTANCE):
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    import arm_staleness
    import frozen_guards

    return arm_staleness, frozen_guards


def _source_at(commit: str, module: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:python/src/beliefs/{module}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RetargetRefused(f"{module} is not in {commit}")
    return completed.stdout


def derive(base: str) -> tuple[tuple[Retarget, ...], tuple[str, ...]]:
    """Every stale arm a live guard audits, carried across formatting from `base`; and the refusals."""
    arm_staleness, frozen_guards = _machinery()
    working = arm_staleness.working_tree(REPO_ROOT)
    entries: list[Retarget] = []
    refusals: list[str] = []
    for guard in frozen_guards.live_guards(REPO_ROOT):
        arms = arm_staleness.audited_arms(guard, repo_root=REPO_ROOT)
        audited = arm_staleness.audited_tree(guard, repo_root=REPO_ROOT)
        for stale in arm_staleness.stale_arms(guard.name, arms, audited):
            index = int(stale.key.rpartition("[")[2].removesuffix("]"))
            sabotage = arms[index].sabotage
            try:
                if sabotage.package != "beliefs":
                    raise RetargetRefused(f"a {sabotage.package} arm; only the beliefs kernel was formatted")
                formatted = working(sabotage.module)
                if formatted is None:
                    raise RetargetRefused(f"{sabotage.module} is not in the working tree")
                before, after = derive_one(
                    _source_at(base, sabotage.module),
                    formatted,
                    sabotage.before,
                    sabotage.after,
                    ruff_formatter(sabotage.module),
                )
            except RetargetRefused as refused:
                refusals.append(f"{guard.name}::{stale.key}: {refused}")
                continue
            entries.append(
                Retarget(
                    guard=guard.name,
                    index=index,
                    row=arms[index].row,
                    module=sabotage.module,
                    original_before=sabotage.before,
                    original_after=sabotage.after,
                    before=before,
                    after=after,
                )
            )
    return tuple(entries), tuple(refusals)


def verify(base: str, entries: Sequence[Retarget]) -> tuple[str, ...]:
    """Problems with the landed re-targets: each must re-derive identically and be what its guard audits."""
    arm_staleness, _ = _machinery()
    working = arm_staleness.working_tree(REPO_ROOT)
    problems: list[str] = []
    for entry in entries:
        label = f"{entry.guard}[{entry.index}] {entry.row}"
        try:
            expected = derive_one(
                _source_at(base, entry.module),
                working(entry.module) or "",
                entry.original_before,
                entry.original_after,
                ruff_formatter(entry.module),
            )
        except RetargetRefused as refused:
            problems.append(f"{label}: {refused}")
            continue
        if expected != (entry.before, entry.after):
            problems.append(f"{label}: re-derivation differs from the recorded entry")
        arm = arm_staleness.audited_arms(ACCEPTANCE / entry.guard, repo_root=REPO_ROOT)[entry.index]
        landed = (arm.row, arm.sabotage.module, arm.sabotage.before, arm.sabotage.after)
        if landed != (entry.row, entry.module, entry.before, entry.after):
            problems.append(f"{label}: the guard audits a different sabotage than the derived one")
    return tuple(problems)


def _literal(text: str, indent: str) -> str:
    lines = text.splitlines(keepends=True)
    if len(lines) <= 1:
        return repr(text)
    body = "".join(f"{indent}    {line!r}\n" for line in lines)
    return f"(\n{body}{indent})"


def render(entries: Sequence[Retarget]) -> str:
    """The entries as `_LIVE_SABOTAGES` dictionary items, grouped under a comment per guard."""
    out: list[str] = []
    for guard in dict.fromkeys(entry.guard for entry in entries):
        out.append(f"    # {guard}\n")
        for entry in (entry for entry in entries if entry.guard == guard):
            out.append(
                f"    {entry.row!r}: Sabotage(\n"
                f"        module={entry.module!r},\n"
                f"        before={_literal(entry.before, '        ')},\n"
                f"        after={_literal(entry.after, '        ')},\n"
                "    ),\n"
            )
    return "".join(out)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    derive_command = commands.add_parser("derive")
    derive_command.add_argument("--base", required=True)
    derive_command.add_argument("--out", required=True, type=Path)
    derive_command.add_argument("--python", action="store_true", help="also print the entries as table items")
    verify_command = commands.add_parser("verify")
    verify_command.add_argument("--base", required=True)
    verify_command.add_argument("--entries", required=True, type=Path)
    arguments = parser.parse_args(argv)

    if arguments.command == "derive":
        entries, refusals = derive(arguments.base)
        arguments.out.write_text(json.dumps([asdict(entry) for entry in entries], indent=1) + "\n", encoding="utf-8")
        if arguments.python:
            print(render(entries), end="")
        for refusal in refusals:
            print(f"refused: {refusal}", file=sys.stderr)
        print(f"{len(entries)} arms derived, {len(refusals)} refused", file=sys.stderr)
        return 1 if refusals else 0

    entries = tuple(Retarget(**item) for item in json.loads(arguments.entries.read_text(encoding="utf-8")))
    problems = verify(arguments.base, entries)
    for problem in problems:
        print(f"problem: {problem}", file=sys.stderr)
    print(f"{len(entries)} entries verified, {len(problems)} problems", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_retarget_formatted_arms.py`
Expected: 9 passed. Then `cd python && uv run --frozen ruff check . && uv run --frozen pyright` — expected clean (pyright does not check `tools/`, but the test module is checked).

- [ ] **Step 5: Smoke the CLI on today's tree**

Run, from `python/`: `mkdir -p ../.work/ruff-format-gate && uv run --frozen python tools/retarget_formatted_arms.py derive --base HEAD --out ../.work/ruff-format-gate/smoke.json`
Expected: `0 arms derived, 0 refused` and exit 0 — before the reformat no live arm is stale.

- [ ] **Step 6: Commit**

```bash
git add python/tools/retarget_formatted_arms.py python/tests/test_retarget_formatted_arms.py
git commit -m "feat(tools): derive formatted twins of stale live N2 arms"
```

---

### Task 3: The reformat commit

**Files:**
- Modify: every non-protected file `ruff format` rewrites under `python/` (313 at `a05273b`'s tree)
- Modify (hand): the displaced suppression comments, measured at five — `tests/verification_fixtures.py` (`# noqa: RUF022`, two errors), `tests/test_estimand.py`, `tests/test_profile_agreement.py`, `tests/acceptance/test_dataset_address_acceptance.py` (`# type: ignore[...]`)

**Interfaces:**
- Consumes: Task 1's exclude (must already be committed).
- Produces: the reformat commit, whose full hash (`REFORMAT`) Tasks 4 and 5 cite, and whose parent (`BASE`) Task 4 derives from.

- [ ] **Step 1: Snapshot the declared arms and broken pins before formatting**

From `python/`:

```bash
mkdir -p ../.work/ruff-format-gate
cat > ../.work/ruff-format-gate/snapshot.py <<'EOF'
"""Every guard's declared arms and broken pins, as JSON, for a before/after comparison."""
import json
import sys
from pathlib import Path

sys.path[:0] = ["tests", "tests/acceptance", "tools"]
import arm_staleness
import frozen_guards

root = Path("..").resolve()
snapshot = {}
for guard in frozen_guards.guard_modules(root):
    arms = arm_staleness.declared_arms(guard, repo_root=root)
    snapshot[guard.name] = {
        "declared": [
            [a.row, a.sabotage.package, a.sabotage.module, a.sabotage.before, a.sabotage.after, list(a.checks)]
            for a in arms
        ],
        "broken_pins": sorted(f"{p.table}:{p.target}" for p in frozen_guards.broken_pins(guard, repo_root=root)),
    }
Path(sys.argv[1]).write_text(json.dumps(snapshot, indent=1, sort_keys=True), encoding="utf-8")
print(len(snapshot), "guards")
EOF
uv run --frozen python ../.work/ruff-format-gate/snapshot.py ../.work/ruff-format-gate/before.json
```

Expected: `43 guards`.

- [ ] **Step 2: Format**

From `python/`: `uv run --frozen ruff format .`
Expected: `313 files reformatted, 197 files left unchanged` (counts may differ if `main` moved; record the actual). Then confirm no protected file changed:

```bash
PROTECTED=$(uv run --frozen python -c "import sys, pathlib; sys.path.insert(0, 'tests'); import frozen_guards; print(' '.join(sorted(frozen_guards.protected_paths(pathlib.Path('..').resolve()))))")
git diff --quiet -- $PROTECTED && echo "no protected file changed"
```

Expected: `no protected file changed`.

- [ ] **Step 3: Move the displaced suppression comments back**

Run from `python/`: `uv run --frozen ruff check .` and `uv run --frozen pyright`. Expected before fixing: 2 `RUF022` errors and 3 pyright errors, each on a line whose suppression the formatter moved onto a closing bracket. For each, move only the suppression comment onto the line the tool reports, leaving every other token as ruff wrote it. Example from `tests/test_estimand.py`:

```python
# as formatted (pyright reports the slot=0.5 line)
        (
            lambda: {"contrast": ContinuousContrast(slot=0.5, quantity=Referent(M, "EX:q"), increment=Decimal(1))},
            ContrastRefused,
            "integer",
        ),  # type: ignore[arg-type]
# fixed
        (
            lambda: {"contrast": ContinuousContrast(slot=0.5, quantity=Referent(M, "EX:q"), increment=Decimal(1))},  # type: ignore[arg-type]
            ContrastRefused,
            "integer",
        ),
```

and in `tests/verification_fixtures.py` the `# noqa: RUF022` moves from the closing `]` onto the `__all__ = [` line ruff reports, keeping the `# re-exported for the acceptance module` comment where it was. Re-run both tools until `All checks passed!` and `0 errors`, then `uv run --frozen ruff format --check .` — expected `… files already formatted` with no file to reformat (the moved comments must not themselves need formatting).

- [ ] **Step 4: Prove formatting changed no declaration and no pin**

From `python/`:

```bash
uv run --frozen python ../.work/ruff-format-gate/snapshot.py ../.work/ruff-format-gate/after.json
cmp ../.work/ruff-format-gate/before.json ../.work/ruff-format-gate/after.json && echo identical
```

Expected: `43 guards` then `identical`.

- [ ] **Step 5: Confirm the expected red, and only it**

Run: `just test-fast`
Expected: exactly 3 failures, all in `tests/test_arm_staleness.py` (`test_every_arm_a_live_guard_audits_applies_exactly_once`, `test_every_arm_the_registry_records_as_stale_really_is_and_no_other`, `test_a_live_guard_re_targets_every_declaration_the_tree_has_outgrown`). Any other failure stops the task: analyse it before going on.

- [ ] **Step 6: Commit**

```bash
git add -A python
git commit -m "style(python): format the tree with ruff format, excluding freeze-protected files"
git rev-parse HEAD~1 HEAD   # BASE, then REFORMAT
tasks note beliefs-a555d6 "reformat commit REFORMAT=<full hash>, BASE=<full hash>; N files; snapshot identical; test-fast red only in test_arm_staleness (3)"
```

The pre-commit hook runs `just check`, which does not yet include the format check; it must pass. Do not commit the task record in this commit (`git add -A python` stages only `python/`).

---

### Task 4: Re-target the live arms and record cut 10's

**Files:**
- Modify: `python/tests/acceptance/test_n2_cutN.py` for the 28 affected live guards (cuts 7, 9, 11, 13, 14, 16, 18, 19, 20, 21, 22, 23, 24, 27, 28, 31, 32, 34, 35, 37, 38, 39, 40, 41, 42, 43, 45, 46)
- Modify: `python/tests/cited_not_run.py` (one constant, three `stale_arms` entries in cut 10's registry entry)
- Create: `docs/plans/2026-10-09-ruff-format-retargets.json` (the derived entries, kept as evidence)

**Interfaces:**
- Consumes: Task 2's CLI; Task 3's `BASE` and `REFORMAT` hashes.
- Produces: guards whose audited arms match the formatted kernel; the entries file Task 6's evidence cites.

The 2026-10-09 pilot measured these stale audited arms (`row[index]`); the derive output is the authority if the tree moved:

| guard | stale arms | idiom |
|---|---|---|
| cut 7 | X10[20] | existing table, `(row, index)`-keyed |
| cut 9 | L10u9[13], V5[23], V8[26] | existing table |
| cut 11 | J1d[18], J7b[45], J8j[57], J9c[60], J12b[64] | existing table |
| cut 13 | R15u2[1], K1a[15] | new table |
| cut 14 | W11a[0], W17c[6], W17g[10], W17i[12] | existing table |
| cut 16 | W16e[6], C3[11], M3b[17], T2b[19], T2c[20] | existing table |
| cut 18 | M13[10], R19[13] | existing table |
| cut 19 | J1a[0], J1e[4], J2j[17], J4[21], J8g[37] | existing table |
| cut 20 | F4[4] | existing table (replace entry) |
| cut 21 | V2f[7] | existing table; `RETARGETED_ROWS` follows it |
| cut 22 | D6a[15] | existing table (replace entry) |
| cut 23 | R19e[22] | existing table (replace entry) |
| cut 24 | W15k[10] | existing table |
| cut 27 | W8a-a[0] | existing table (replace entry) |
| cut 28 | W7-h[7], W8-a[16], W8-c[18], W8b-b[20] | new table |
| cut 31 | Q3-d[8], Q4-a[12], Q7-b[20], Q10-b[25] | new table |
| cut 32 | U3-a[3], U5-a[11], U8-b[17], U8-e[20] | existing table |
| cut 34 | BI-5[12], BI-6[13] | new table |
| cut 35 | G9-a[2], R10-a[3], BI-8[23], BI-11b[27] | new table |
| cut 37 | L13-b2[2], BI-1[12] | new table |
| cut 38 | T2-g1[2], T2-j[7], BI-3[13] | new table |
| cut 39 | W17-p-b[1] | new table |
| cut 40 | Y6-a[2] | existing table (replace entry) |
| cut 41 | Z5-b[10] | new table |
| cut 42 | Y14-b[8], Y15-b[10] | new table |
| cut 43 | J15-b[7] | new table |
| cut 45 | G13-e[28] | new table |
| cut 46 | Y17-i[11], Y17-n[16], Y18-a[19], Y18-d[22], Y18-j[28], Y18-k[29], Y18-o[33] | new table |

- [ ] **Step 1: Derive**

From `python/`, with `BASE` from Task 3:

```bash
uv run --frozen python tools/retarget_formatted_arms.py derive --base "$BASE" \
  --out ../docs/plans/2026-10-09-ruff-format-retargets.json --python > ../.work/ruff-format-gate/retargets.txt
```

Expected on stderr: `70 arms derived, 0 refused`, exit 0. A refusal stops the task: the arm cannot be carried mechanically, and it is analysed and noted on the task before anything is hand-written.

- [ ] **Step 2: Write the comment once**

Every new or replaced entry is preceded by this comment (an earlier comment on a replaced entry stays, and this one is appended below it):

```python
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
```

Use the date of this commit if it is not 2026-10-09.

- [ ] **Step 3: Guards with an existing table (15)**

For each guard marked "existing table", paste its items from `retargets.txt` into its `_LIVE_SABOTAGES` dictionary: add an item for a new row, or replace the `before`/`after` of the row's existing item (keep its `module`). For cut 7, also add `("X10", 20)` to `_LIVE_SABOTAGE_INDICES`, so the three other X10 arms keep their declared sabotage:

```python
_LIVE_SABOTAGE_INDICES = {("X12", 25), ("W8a", 33), ("X10", 20)}
```

- [ ] **Step 4: Guards gaining a table (13)**

For each guard marked "new table", add `from dataclasses import replace` and `Sabotage` to its `from n2_arms import …` line where absent, then insert directly after the import block, in cut 16's shape (cut 46 shown):

```python
# Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
# anchored lines. Derived by tools/retarget_formatted_arms.py, so each arm applied to
# the formatted source is exactly the formatted declared sabotage. The frozen
# declaration remains unchanged.
_LIVE_SABOTAGES = {
    "Y17-i": Sabotage(
        module=...,  # pasted from retargets.txt, one item per row in the table above
        before=...,
        after=...,
    ),
}
CUT46_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT46_ARMS
)
```

The items are the pasted `retargets.txt` lines verbatim; the `...` above marks where they go, not text to keep. Each of these 13 guards has one arm per stale row (the pilot checked), so row keys are safe.

- [ ] **Step 5: Record cut 10's arms in the registry**

In `python/tests/cited_not_run.py`, after `MOVED_BY_WORKTREE_ROOT`, add (with `REFORMAT`'s first 7 characters):

```python
MOVED_BY_REFORMAT = (
    "moved at <REFORMAT short hash>, when ruff format re-wrapped the kernel; the cited "
    "declaration is excluded from formatting and left byte-identical (beliefs-a555d6)"
)
```

and add to the `stale_arms` of the `"test_n2_cut10.py"` entry:

```python
            "H1u1[0]": MOVED_BY_REFORMAT,
            "H2u1[3]": MOVED_BY_REFORMAT,
            "L7u1[16]": MOVED_BY_REFORMAT,
```

The derive output does not list these (cited guards are evidence); the staleness test names them if the set differs.

- [ ] **Step 6: Format the edited files and verify the transcription**

From `python/`:

```bash
uv run --frozen ruff format tests/acceptance tests/cited_not_run.py
uv run --frozen python tools/retarget_formatted_arms.py verify --base "$BASE" \
  --entries ../docs/plans/2026-10-09-ruff-format-retargets.json
```

Expected: `70 entries verified, 0 problems`, exit 0.

- [ ] **Step 7: Run the staleness and pin tests**

Run: `just test-one tests/test_arm_staleness.py tests/test_frozen_guards.py tests/test_retarget_formatted_arms.py`
Expected: all pass.

- [ ] **Step 8: Run every live guard's static tests (the scalar-pin backstop)**

From the worktree root, after `cd "$(pwd -P)"`:

```bash
MODS=$(cd python && uv run --frozen python -c "import sys, pathlib; sys.path.insert(0, 'tests'); import frozen_guards; print(' '.join('tests/acceptance/' + g.name for g in frozen_guards.live_guards(pathlib.Path('..').resolve())))")
just test-one $MODS -k "not sabotage and not pilot_arm and not live_check and not audit and not mutation and not vacuous"
```

Expected: 0 failed (about 290 selected, about 3 minutes). Every pin form a guard enforces — table, scalar digest, scalar commit, results-record check — runs here.

- [ ] **Step 9: Run the mutation pilot**

Run: `just test-one tests/acceptance/test_n2_cut46.py`
Expected: 13 passed in about 15 s — 36 arms, 7 of them re-targeted here, each through baseline, sabotage, check execution and a `sound` verdict. A failure stops here and is analysed before the chain (Task 6).

- [ ] **Step 10: Run the fast suite and the checks**

Run: `just test-fast`, then `just check`.
Expected: test-fast green (0 failed); check clean.

- [ ] **Step 11: Commit**

```bash
git add python/tests docs/plans/2026-10-09-ruff-format-retargets.json
git commit -m "test(n2): re-target live arms to the formatted kernel; record cut 10's"
tasks note beliefs-a555d6 "re-targets: 70 derived, 0 refused, verify 0 problems; static guard tests <n> passed; cut-46 pilot 13 passed in <s> s; cut 10 records 3 stale arms"
```

---

### Task 5: Enforce format in the gate

**Files:**
- Modify: `justfile` (`py_check_cmd`)
- Create: `.git-blame-ignore-revs`
- Modify: `AGENTS.md` (the `just check` line)

**Interfaces:**
- Consumes: `REFORMAT` from Task 3.
- Produces: `just check` (and through it `hook-pre-commit` and `ci-python`) failing on any unformatted, unprotected Python file.

- [ ] **Step 1: Show the gate is blind today**

```bash
printf 'x = [1,\n 2]\n' > python/tests/_format_probe.py
just check
```

Expected: passes — the gate does not see formatting (the RED).

- [ ] **Step 2: Add the format check**

In `justfile`, change line 32 to:

```just
py_check_cmd := "(cd python && uv run --frozen ruff check . && uv run --frozen ruff format --check . && uv run --frozen pyright)"
```

- [ ] **Step 3: Show the gate now sees it, then remove the probe**

Run: `just check` — expected: fails, naming `tests/_format_probe.py` as `Would reformat`.
Then `rm python/tests/_format_probe.py` and `just check` — expected: passes.

- [ ] **Step 4: Record the reformat for blame**

Create `.git-blame-ignore-revs`:

```
# Formatting-only commits, skipped by `git blame`. GitHub reads this file by name; for
# local blame, run once: git config blame.ignoreRevsFile .git-blame-ignore-revs
# ruff format over python/, excluding freeze-protected files (beliefs-a555d6)
<REFORMAT full hash>
```

Check: `git blame --ignore-revs-file .git-blame-ignore-revs python/tests/test_estimand.py | grep -c "<REFORMAT short hash>"` — expected `0` or only the hand-moved suppression lines.

- [ ] **Step 5: Update AGENTS.md**

Change the gate bullet's opening from `run \`just check\` (ruff, pyright, biome, tsc, \`tasks check\`)` to:

```markdown
- From the repository root, run `just check` (ruff check, ruff format --check, pyright, biome, tsc, `tasks check`) and `just test` (…unchanged…). Formatting excludes the freeze-protected files that `python/tests/test_frozen_guards.py` holds equal to the guards' pins (beliefs-ea5ec7 retires the exclude); `.git-blame-ignore-revs` lists the reformat.
```

(Keep the rest of that bullet as it is.)

- [ ] **Step 6: Commit**

```bash
git add justfile .git-blame-ignore-revs AGENTS.md
git commit -m "build(check): enforce ruff format in the gate"
```

---

### Task 6: Verify on the certified host and land

**Files:**
- Modify: `tasks/beliefs-a555d6.md` (through the `tasks` CLI only)

**Interfaces:**
- Consumes: the branch tip after Task 5.
- Produces: the chain and gate evidence on the task, the task closed, the branch merged.

- [ ] **Step 1: Check `main` has not moved and no lane is open**

```bash
git rev-list --count HEAD..main
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do echo "$b $(git rev-list --count main..$b)"; done
git worktree list
```

Expected: `0` commits on `main` not in the branch; every other branch 0 ahead of `main`; no worktree but the main checkout and this one. If `main` has moved: rebase Tasks 1–2 onto it, then redo Task 3 by running the command again (never resolve a conflict in the reformat by hand), then redo Task 4 from Step 1 and Task 5. If another lane holds unmerged kernel work, park the task `--reason dependency` naming it.

- [ ] **Step 2: Run the newest runner's chain**

From the worktree's `python/` after `cd "$(pwd -P)"`, through Bash with `run_in_background: true` and `timeout: 7200000`:

```bash
set -o pipefail && host-budget run -- uv run --frozen python tools/cut46_acceptance.py 2>&1 | tee ../.work/ruff-format-gate/cut46-chain.log
```

Expected: exit 0, every phase passes, and the final line reads `declared arms: …`. At cut 46 the chain reported about 3713 s of pytest time. A cap kill (exit 144, truncated log) is not detached: park `--reason environment` naming the cap. A failure is analysed from the completed phases before any retry.

- [ ] **Step 3: Run the full gate**

Through Bash with `run_in_background: true` and `timeout: 1800000`:

```bash
set -o pipefail && just gate 2>&1 | tee .work/ruff-format-gate/gate.log
```

Expected: exit 0; record the pytest summary lines.

- [ ] **Step 4: Record and close**

```bash
tasks note beliefs-a555d6 "verification: cut-46 chain passed (<phases> phases, <s> s pytest), just gate passed (<summary>)"
tasks check
tasks done beliefs-a555d6 "ruff format enforced in just check; 313 files reformatted at <REFORMAT short>, 56 freeze-protected files excluded; 70 live arms re-targeted mechanically, cut 10's 3 recorded"
git add tasks/
git commit -m "chore(tasks): close beliefs-a555d6"
```

`tasks check` must print nothing; report any warning.

- [ ] **Step 5: Land (after the final whole-branch review clears)**

From the main checkout:

```bash
git merge --no-ff chore/ruff-format-gate -m "merge: ruff format in the gate (beliefs-a555d6)"
```

Then run `just check` on `main`. The merge is a local merge in a personal repository; pushing is a separate step for the user.
