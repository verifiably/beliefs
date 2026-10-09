# Freeze pins hold modulo formatting — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every freeze pin on a `.py` target hold up to formatting, in the portable reader and in each live guard's own checks, then format the 34 frozen files and retire `beliefs-a555d6`'s format exclude.

**Architecture:** A stdlib-only comparator (`python/tests/pin_equivalence.py`) decides whether two versions of a Python file differ only by formatting. `python/tests/frozen_guards.py` gains `commit_pin_holds` and `content_pin_holds`, which resolve a pin's original bytes from git and apply the comparator. `holds()` delegates to them, and 37 live guards call them in place of `git diff --quiet` and SHA-256 equality. The exclude goes only after the files it protected are already formatted, so every commit passes the pre-commit hook.

**Tech Stack:** Python 3.11+ (stdlib `ast`, `tokenize`, `inspect`), git, ruff 0.16.1 (pinned by `python/uv.lock`), pytest through `just test-one` / `just test-fast`.

**Spec:** `docs/superpowers/specs/2026-10-09-freeze-pins-modulo-formatting-design.md` (task `beliefs-ea5ec7`; amends `docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md` with §8).

## Global Constraints

- Work in `.worktrees/freeze-pins-modulo-format` on branch `freeze-pins-modulo-format`. Every path shown to the user is prefixed `.worktrees/freeze-pins-modulo-format/`. Run Python and git from the canonical path: `cd "$(pwd -P)"` inside the worktree first.
- No `FROZEN_*` table, `CUTN_*_SHA256` / `CUTN_*_COMMIT` constant, `FROZEN_DECLARATION` value, cited-not-run guard (`test_n2_cut4.py`, `test_n2_cut5.py`, `test_n2_cut8.py`, `test_n2_cut10.py`) or declaration file is edited by hand. The 34 frozen files change only in the Task 4 format commit, and only by `ruff format` output (doctrine §3).
- The comparator imports only the standard library, so a ruff upgrade cannot change a verdict. It fails closed.
- Every commit passes the pre-commit hook as it stands. Never `--no-verify`. The order is spec §7: Tasks 1–3 with the exclude in place, then Task 4 formats, then Task 5 removes the exclude.
- Run every ruff call as `uv run --frozen ruff …` from `python/`. Tests go through `just test-one <runner args>` (paths relative to `python/`) and `just test-fast` before each commit. Never call pytest directly. An explicit `tests/acceptance/…` path runs even though `addopts` ignores the directory.
- This is method, not a conformance cut: no adoption-ledger row, no `test_recent_cut_acceptance.py` row, no cut document. No module imports `atoms` (`root.py` stays the one importer).
- Use conventional commits, with no AI attribution trailer, co-author line or session URL.
- Each task has a child record (ids listed under **Task records** at the end). Run `tasks start <child>` in the worktree before the task's first change, and `tasks done <child> "<what landed>"` with the record staged in the task's commit. Task 4 is the exception: its commit holds only formatter output, so its child closes in a record-only commit right after. The parent `beliefs-ea5ec7` closes last (Task 6).
- Long runs (`just gate`) go through Bash `run_in_background: true`, with `set -o pipefail` and `tee` into `.work/freeze-pins-modulo-format/` and a timeout that covers the run. Never `nohup`, `&` or `detached.sh`.

## Review Focus

1. **A pin whose commit no longer resolves** (a history rewrite like the 2026-09-05 one) must break, not be read as "absent at the pin". Task 2 tests it.
2. **A frozen file whose line endings change** (CRLF↔LF), or whose trailing block comment is re-indented, is formatting and must hold. Task 1 tests both.
3. **A deleted target** must break both pin forms without raising. Task 2 tests a commit pin and a content pin.
4. **The content-resolution cache must not mask a later edit** to the working file, since it caches the original and never a verdict. Task 2 edits the file after a resolving call.
5. **A guard that names `FROZEN_DECLARATION` without a digest constant** must fail loudly, not be skipped. Task 2's portable test asserts the digest is present before checking it.

## Measured inputs (from the spec, re-verified 2026-10-09 at `a6b07e9`)

- 43 guard modules: 39 live (cuts 6, 7, 9, 11–46) and 4 cited not run (cuts 4, 5, 8, 10). 922 commit pins and 9 content pins sit in live tables. 21 live pins assert the absence of `python/tests/n2_arms_cut25.py` at `5072609`.
- Today's broken pins: `test_n2_cut8.py` → `python/tests/n2_arms_cut5.py`, `python/tools/cut5_acceptance.py`, `python/tools/cut6_acceptance.py`, `python/tests/acceptance/test_n2_cut6.py`, `python/tools/cut7_acceptance.py`; `test_n2_cut10.py` → `python/tests/n2_arms_cut5.py`. Both are recorded in `cited_not_run.py`, and `test_every_pin_the_registry_records_as_falsified_really_is` holds them exact.
- With the exclude removed, `ruff format` rewrites exactly these 34 paths (relative to `python/`):

```text
tests/acceptance/n2_arms_cut10.py
tests/acceptance/n2_arms_cut11.py
tests/acceptance/n2_arms_cut12.py
tests/acceptance/n2_arms_cut13.py
tests/acceptance/n2_arms_cut14.py
tests/acceptance/n2_arms_cut17.py
tests/acceptance/n2_arms_cut19.py
tests/acceptance/n2_arms_cut20.py
tests/acceptance/n2_arms_cut21.py
tests/acceptance/n2_arms_cut22.py
tests/acceptance/n2_arms_cut28.py
tests/acceptance/n2_arms_cut29.py
tests/acceptance/n2_arms_cut30.py
tests/acceptance/n2_arms_cut8.py
tests/acceptance/n2_arms_cut9.py
tests/acceptance/test_n2_cut10.py
tests/acceptance/test_n2_cut4.py
tests/acceptance/test_n2_cut5.py
tests/acceptance/test_n2_cut6.py
tests/acceptance/test_n2_cut8.py
tests/n2_arms_cut16.py
tests/n2_arms_cut18.py
tests/n2_arms_cut31.py
tests/n2_arms_cut32.py
tests/n2_arms_cut35.py
tests/n2_arms_cut37.py
tests/n2_arms_cut38.py
tests/n2_arms_cut3.py
tests/n2_arms_cut45.py
tests/n2_arms_cut46.py
tests/n2_arms_cut4.py
tests/n2_arms_cut5.py
tests/n2_arms_cut6.py
tests/n2_arms_cut7.py
```

- The live-guard pin-check selection is
  `just test-one $GUARDS -k "frozen or byte_exact or unchanged"`, where
  `GUARDS=$(for n in 6 7 9 $(seq 11 46); do printf "tests/acceptance/test_n2_cut%s.py " $n; done)`.
  Today it passes 96 tests with 338 deselected, in about 6 s.

---

### Task 1: The formatting-equivalence comparator

**Files:**
- Create: `python/tests/pin_equivalence.py`
- Test: `python/tests/test_pin_equivalence.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `pin_equivalence.equivalent(original: bytes, current: bytes, *, path: str) -> bool`. It returns `True` for identical bytes. For a non-`.py` path it is otherwise `False`. For a `.py` path it is `True` only when the encoding, the tree (docstrings via `inspect.cleandoc`), comment attachment and directive lines all agree (spec §3), and every failure is `False`.

- [ ] **Step 1: Write the failing tests** in `python/tests/test_pin_equivalence.py`:

```python
"""The formatting-equivalence comparator behind every `.py` freeze pin (doctrine §8)."""

from __future__ import annotations

import pin_equivalence

ORIGINAL = b'''"""A frozen declaration.

    Its docstring is indented the old way.
    """
from n2_arms import Arm
ARMS = (Arm(row='W1', asserts="x", before='    return None  # type: ignore[return-value]',
           after="pass"),)  # the arms

def f(a,b):
    # leading note
    return a+b
'''

# ORIGINAL as `ruff format` (0.16.1, line length 120) writes it.
FORMATTED = b'''"""A frozen declaration.

Its docstring is indented the old way.
"""

from n2_arms import Arm

ARMS = (Arm(row="W1", asserts="x", before="    return None  # type: ignore[return-value]", after="pass"),)  # the arms


def f(a, b):
    # leading note
    return a + b
'''


def same(original: bytes, current: bytes) -> bool:
    return pin_equivalence.equivalent(original, current, path="python/tests/n2_arms_cut99.py")


def test_identical_bytes_hold_for_any_target() -> None:
    assert pin_equivalence.equivalent(b"\xff not python", b"\xff not python", path="docs/x.md")


def test_a_formatting_only_change_holds() -> None:
    assert same(ORIGINAL, FORMATTED)


def test_line_endings_alone_hold() -> None:
    assert same(FORMATTED, FORMATTED.replace(b"\n", b"\r\n"))


def test_a_re_indented_trailing_block_comment_holds() -> None:
    assert same(b"if x:\n    y = 1\n    # done\nz = 2\n", b"if x:\n    y = 1\n# done\nz = 2\n")


def test_a_non_python_target_is_byte_exact() -> None:
    assert not pin_equivalence.equivalent(b"# Cut\n", b"# Cut \n", path="docs/designs/cut.md")


def test_a_changed_string_literal_breaks() -> None:
    assert not same(FORMATTED, FORMATTED.replace(b'asserts="x"', b'asserts="y"'))


def test_a_changed_statement_breaks() -> None:
    assert not same(FORMATTED, FORMATTED.replace(b"return a + b", b"return a - b"))


def test_a_changed_comment_breaks() -> None:
    assert not same(FORMATTED, FORMATTED.replace(b"# leading note", b"# leading notes"))


def test_a_changed_docstring_text_breaks_but_its_indentation_does_not() -> None:
    assert same(ORIGINAL, FORMATTED)
    assert not same(FORMATTED, FORMATTED.replace(b"the old way", b"the new way"))


def test_a_type_ignore_moved_to_another_statement_breaks() -> None:
    assert not same(
        b"x = f(1)  # type: ignore[arg-type]\ny = g(2)\n",
        b"x = f(1)\ny = g(2)  # type: ignore[arg-type]\n",
    )


def test_a_plain_comment_moved_across_a_statement_breaks() -> None:
    assert not same(b"x = 1\n# note\ny = 2\n", b"x = 1\ny = 2\n# note\n")


def test_a_directive_whose_line_was_reformatted_breaks() -> None:
    assert not same(
        b"def f(\n    a, b\n):  # type: ignore\n    pass\n",
        b"def f(a, b):  # type: ignore\n    pass\n",
    )


def test_a_coding_cookie_moved_below_line_two_breaks() -> None:
    """The review's reproduction: the moved cookie turns 'é' into 'Ã©' on execution."""
    literal = "é".encode("latin-1")
    original = b"# coding: latin-1\nx = '" + literal + b"'\n"
    moved = b"\n\n# coding: latin-1\nx = '" + literal + b"'\n"
    assert not same(original, moved)


def test_unparseable_input_breaks() -> None:
    assert not same(FORMATTED, FORMATTED + b"def (:\n")
    assert not same(b"x = 1\n", b"x = 1\0\n")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_pin_equivalence.py`
Expected: a collection error, `ModuleNotFoundError: No module named 'pin_equivalence'`.

- [ ] **Step 3: Write the comparator** in `python/tests/pin_equivalence.py`:

```python
"""Whether two versions of a frozen Python file differ only by formatting.

A freeze pin names the bytes a cut audited. Formatting changes no meaning, so a pin on a
`.py` target holds when the file is byte-identical to the pinned original or equivalent
to it under the four rules `equivalent` applies (frozen guard doctrine §8). Every other
target stays byte-exact. Only the standard library is read, so a formatter upgrade
cannot change a verdict. The comparison fails closed: it can be stricter than
formatting needs, never looser than its rules.
"""

from __future__ import annotations

import ast
import inspect
import io
import re
import tokenize
from collections.abc import Iterator

# A comment a tool reads by physical line: the line's code must survive unchanged.
_DIRECTIVE = re.compile(r"#\s*(type:|noqa|pyright:|mypy:|pragma|fmt:|isort:|ruff:)", re.IGNORECASE)
# A shebang or a coding cookie only works on these lines, so a comment there keeps its line.
_HEADER_LINES = 2
_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

Anchor = tuple[str, int]
Comment = tuple[str, Anchor, int | None, str | None]


def equivalent(original: bytes, current: bytes, *, path: str) -> bool:
    """Whether `current` keeps every meaning `original` had.

    Both sides are read as Python reads source, from bytes, so a coding cookie decides
    their text. Beyond byte identity they must agree on four things: the detected
    encoding; the syntax tree, with each docstring compared after `inspect.cleandoc`;
    every comment's text and the statement it belongs to; and, for a directive comment,
    the code on its physical line.
    """
    if original == current:
        return True
    if not path.endswith(".py"):
        return False
    try:
        if _encoding(original) != _encoding(current):
            return False
        before, after = _tree(original), _tree(current)
        if ast.dump(before) != ast.dump(after):
            return False
        return _comments(original, before) == _comments(current, after)
    except (SyntaxError, ValueError, tokenize.TokenError):
        return False


def _encoding(source: bytes) -> str:
    return tokenize.detect_encoding(io.BytesIO(source).readline)[0]


def _tree(source: bytes) -> ast.Module:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, _DOCSTRING_OWNERS) or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            first.value.value = inspect.cleandoc(first.value.value)
    return tree


def _preorder(node: ast.AST) -> Iterator[ast.AST]:
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _preorder(child)


def _comments(source: bytes, tree: ast.Module) -> list[Comment]:
    """Each comment as its text, its statement anchor, its header line, its directive line."""
    statements = [node for node in _preorder(tree) if isinstance(node, ast.stmt)]
    comments: list[Comment] = []
    for token in tokenize.tokenize(io.BytesIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        comments.append(
            (
                token.string,
                _anchor(statements, line),
                line if line <= _HEADER_LINES else None,
                token.line[: token.start[1]].rstrip() if _DIRECTIVE.match(token.string) else None,
            )
        )
    return comments


def _anchor(statements: list[ast.stmt], line: int) -> Anchor:
    """The innermost statement whose lines hold `line`, else the first one after it.

    Statements are numbered in pre-order, so a nested statement follows its parent and
    the last match is the innermost. Equal trees number their statements alike.
    """
    containing = [
        index
        for index, statement in enumerate(statements)
        if statement.lineno <= line <= (statement.end_lineno or statement.lineno)
    ]
    if containing:
        return ("in", containing[-1])
    following = next(
        (index for index, statement in enumerate(statements) if statement.lineno > line),
        len(statements),
    )
    return ("before", following)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_pin_equivalence.py`
Expected: `14 passed`.

- [ ] **Step 5: Confirm the comparator accepts the real reformat.** This measures without changing the tree: it formats a scratch copy and compares all 34 files.

```bash
cd "$(pwd -P)"
scratch=$(mktemp -d) && git archive HEAD python | tar -x -C "$scratch"
sed -i '/^\[tool.ruff.format\]/,/^\]/d' "$scratch/python/pyproject.toml"
(cd "$scratch/python" && uv run --project "$OLDPWD/python" --frozen ruff format -q .)
cd python && uv run --frozen python -I -c "
import sys; sys.path.insert(0, 'tests')
from pathlib import Path
import pin_equivalence
scratch = Path(sys.argv[1]) / 'python'
changed = [p for p in sys.argv[2:] if Path(p).read_bytes() != (scratch / p).read_bytes()]
bad = [p for p in changed if not pin_equivalence.equivalent(Path(p).read_bytes(), (scratch / p).read_bytes(), path=p)]
print(len(changed), 'reformatted;', 'not equivalent:', bad)
" "$scratch" tests/acceptance/n2_arms_cut10.py tests/acceptance/n2_arms_cut11.py tests/acceptance/n2_arms_cut12.py tests/acceptance/n2_arms_cut13.py tests/acceptance/n2_arms_cut14.py tests/acceptance/n2_arms_cut17.py tests/acceptance/n2_arms_cut19.py tests/acceptance/n2_arms_cut20.py tests/acceptance/n2_arms_cut21.py tests/acceptance/n2_arms_cut22.py tests/acceptance/n2_arms_cut28.py tests/acceptance/n2_arms_cut29.py tests/acceptance/n2_arms_cut30.py tests/acceptance/n2_arms_cut8.py tests/acceptance/n2_arms_cut9.py tests/acceptance/test_n2_cut10.py tests/acceptance/test_n2_cut4.py tests/acceptance/test_n2_cut5.py tests/acceptance/test_n2_cut6.py tests/acceptance/test_n2_cut8.py tests/n2_arms_cut16.py tests/n2_arms_cut18.py tests/n2_arms_cut31.py tests/n2_arms_cut32.py tests/n2_arms_cut35.py tests/n2_arms_cut37.py tests/n2_arms_cut38.py tests/n2_arms_cut3.py tests/n2_arms_cut45.py tests/n2_arms_cut46.py tests/n2_arms_cut4.py tests/n2_arms_cut5.py tests/n2_arms_cut6.py tests/n2_arms_cut7.py
rm -rf "$scratch"
```

Expected: `34 reformatted; not equivalent: []`.

- [ ] **Step 6: Commit**

```bash
just test-fast
git add python/tests/pin_equivalence.py python/tests/test_pin_equivalence.py tasks/
git commit -m "test(n2): compare frozen Python files modulo formatting"
```

### Task 2: Pin resolution through the comparator

**Files:**
- Modify: `python/tests/frozen_guards.py` (imports and module constants at the top; replace `holds`; add declaration readers after `declaration_pin`; the module docstring and `declaration_pin`'s docstring)
- Test: `python/tests/test_frozen_guards.py` (new tests inserted before `PYPROJECT = REPO_ROOT / …`)

**Interfaces:**
- Consumes: `pin_equivalence.equivalent` (Task 1).
- Produces, in `frozen_guards`:
  - `commit_pin_holds(repo_root: Path, target: str, commit: str) -> bool`
  - `content_pin_holds(repo_root: Path, target: str, digest: str) -> bool`
  - `declaration_digest(guard: Path) -> str | None` reads the `CUT\d+_DECLARATION_SHA256` constant.
  - `declaration_commit(guard: Path) -> str | None` reads the `CUT\d+_DECLARATION_COMMIT` constant. Both readers raise `ValueError` when a guard declares more than one.
  - `holds(pin, *, repo_root)` keeps its signature and delegates to the two predicates.

- [ ] **Step 1: Write the failing tests.** In `python/tests/test_frozen_guards.py`, add `from hashlib import sha256` to the imports (after `import tomllib`). Then insert this block immediately before the line `PYPROJECT = REPO_ROOT / "python" / "pyproject.toml"`:

```python
UNFORMATTED = b"ARMS = ('a',\n    'b')\n"
FORMATTED = b'ARMS = ("a", "b")\n'
CHANGED = b'ARMS = ("a", "c")\n'


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=pin-test",
            "-c",
            "user.email=pin-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _commit(root: Path, files: dict[str, bytes | None]) -> str:
    """Write (or, for None, delete) each file, commit everything, and return the commit."""
    for name, data in files.items():
        path = root / name
        if data is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "--allow-empty", "-m", "step")
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def scratch_repo(tmp_path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    return root


def test_a_commit_pin_holds_through_formatting_and_breaks_on_a_change(scratch_repo) -> None:
    pin = _commit(scratch_repo, {"arms.py": UNFORMATTED})
    _commit(scratch_repo, {"arms.py": FORMATTED})
    assert frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)

    (scratch_repo / "arms.py").write_bytes(CHANGED)  # the working file, uncommitted
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)


def test_an_absence_pin_holds_only_while_the_target_stays_absent(scratch_repo) -> None:
    pin = _commit(scratch_repo, {"other.py": FORMATTED})
    assert frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)

    (scratch_repo / "arms.py").write_bytes(FORMATTED)
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)


def test_a_present_target_that_was_deleted_breaks(scratch_repo) -> None:
    pin = _commit(scratch_repo, {"arms.py": FORMATTED})
    _commit(scratch_repo, {"arms.py": None})
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", pin)


def test_a_commit_that_does_not_resolve_is_broken_not_absent(scratch_repo) -> None:
    _commit(scratch_repo, {"other.py": FORMATTED})
    assert not frozen_guards.commit_pin_holds(scratch_repo, "arms.py", "0" * 40)


def test_a_content_pin_resolves_its_original_from_history(scratch_repo) -> None:
    digest = sha256(UNFORMATTED).hexdigest()
    _commit(scratch_repo, {"arms.py": UNFORMATTED})
    _commit(scratch_repo, {"arms.py": FORMATTED})
    assert frozen_guards.content_pin_holds(scratch_repo, "arms.py", digest)

    (scratch_repo / "arms.py").write_bytes(CHANGED)  # the cache holds the original, not a verdict
    assert not frozen_guards.content_pin_holds(scratch_repo, "arms.py", digest)


def test_a_content_pin_no_version_matches_is_broken(scratch_repo) -> None:
    _commit(scratch_repo, {"arms.py": FORMATTED})
    assert not frozen_guards.content_pin_holds(scratch_repo, "arms.py", sha256(UNFORMATTED).hexdigest())


def test_a_content_pin_on_a_deleted_target_is_broken(scratch_repo) -> None:
    _commit(scratch_repo, {"arms.py": FORMATTED})
    digest = sha256(FORMATTED).hexdigest()
    (scratch_repo / "arms.py").unlink()
    assert not frozen_guards.content_pin_holds(scratch_repo, "arms.py", digest)


def test_resolution_in_one_repository_is_not_evidence_about_another(tmp_path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    for root in (first, second):
        root.mkdir()
        _git(root, "init", "-q")
    digest = sha256(UNFORMATTED).hexdigest()
    _commit(first, {"arms.py": UNFORMATTED})
    _commit(first, {"arms.py": FORMATTED})
    _commit(second, {"arms.py": FORMATTED})

    assert frozen_guards.content_pin_holds(first, "arms.py", digest)
    assert not frozen_guards.content_pin_holds(second, "arms.py", digest)


def test_the_scalar_declaration_readers_find_the_digest_and_commit(tmp_path) -> None:
    guard = tmp_path / "test_n2_cut99.py"
    guard.write_text(
        'FROZEN_DECLARATION = "python/tests/n2_arms_cut99.py"\n'
        'CUT99_DECLARATION_SHA256 = "' + "a" * 64 + '"\n'
        'CUT99_DECLARATION_COMMIT = "abc1234"\n'
        'CUT99_FROZEN_SHA256 = "' + "b" * 64 + '"\n',
        encoding="utf-8",
    )

    assert frozen_guards.declaration_digest(guard) == "a" * 64
    assert frozen_guards.declaration_commit(guard) == "abc1234"


def test_every_declaration_pin_in_a_live_guard_holds(git_checkout) -> None:
    """The scalar freeze: each live guard's `FROZEN_DECLARATION` against its digest and,
    for cuts 27-30, its declaring commit. Formatting touches ten of these files, and no
    portable check read them before doctrine §8."""
    checked, broken = 0, []
    for guard in frozen_guards.live_guards(REPO_ROOT):
        declaration = frozen_guards.declaration_pin(guard)
        if declaration is None:
            continue
        digest = frozen_guards.declaration_digest(guard)
        assert digest is not None, f"{guard.name} names FROZEN_DECLARATION without its digest"
        checked += 1
        if not frozen_guards.content_pin_holds(REPO_ROOT, declaration, digest):
            broken.append(f"{guard.name}::digest")
        commit = frozen_guards.declaration_commit(guard)
        if commit is not None and not frozen_guards.commit_pin_holds(REPO_ROOT, declaration, commit):
            broken.append(f"{guard.name}::commit")

    assert checked >= 21  # cuts 26-46 at the time of writing
    assert not broken
```

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_frozen_guards.py`
Expected: the ten new tests fail with `AttributeError: module 'frozen_guards' has no attribute 'commit_pin_holds'` (or `content_pin_holds`, `declaration_digest`). The ten existing tests pass.

- [ ] **Step 3: Implement.** In `python/tests/frozen_guards.py`, replace the import block and constants:

```python
import ast
import re
import subprocess
from dataclasses import dataclass
from functools import cache
from hashlib import sha256
from pathlib import Path

import pin_equivalence
from cited_not_run import CITED_NOT_RUN

_SHA256_LENGTH = 64
_DECLARATION_DIGEST = re.compile(r"CUT\d+_DECLARATION_SHA256")
_DECLARATION_COMMIT = re.compile(r"CUT\d+_DECLARATION_COMMIT")
```

Replace the whole `def holds(pin: Pin, *, repo_root: Path) -> bool:` function with:

```python
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
        return not path.exists()
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
```

Insert this after `declaration_pin` (and before `protected_paths`):

```python
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
```

Correct the two current-facing claims the change makes stale:
- In the module docstring, replace `and by content, where the claim is *these exact
bytes*. Both are` with `and by content, where the claim is *these bytes*. On a `.py`
target both claims hold up to formatting (`pin_equivalence`, frozen guard doctrine §8).
Both are`. Re-wrap the paragraph at the module's width.
- In `declaration_pin`'s docstring, replace `and pin it byte-exact with a scalar digest`
with `and pin it with a scalar digest`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_frozen_guards.py tests/test_pin_equivalence.py`
Expected: `34 passed`. The pre-existing pin-map tests pass under the new reader: every live pin holds, and the cited registry is exact. That is the spec's "new reader before the format commit" equality point.

- [ ] **Step 5: Commit**

```bash
cd "$(pwd -P)/python" && uv run --frozen ruff check tests && uv run --frozen ruff format --check tests && uv run --frozen pyright tests/frozen_guards.py tests/test_frozen_guards.py tests/pin_equivalence.py; cd ..
just test-fast
git add python/tests/frozen_guards.py python/tests/test_frozen_guards.py tasks/
git commit -m "test(n2): resolve freeze pins through the formatting comparator"
```

### Task 3: The live guards' own pin checks

**Files:**
- Modify: `python/tests/acceptance/test_n2_cut{7,9,11..46}.py`. That is 37 modules, all live guards except cuts 6 and 20, which run no file pin check. The edits touch only pin-check statements and imports.

**Interfaces:**
- Consumes: `frozen_guards.commit_pin_holds` and `frozen_guards.content_pin_holds` (Task 2).
- Produces: nothing new. Every rewritten test keeps its name and assertion message.

The rewrite is mechanical, so a one-off script does it (not committed). It has four patterns:

| before | after | guards |
|---|---|---|
| `completed = subprocess.run([... "diff", "--quiet", pin, "HEAD", "--", path], check=False)` then `assert completed.returncode == 0, <msg>` | `assert frozen_guards.commit_pin_holds(REPO_ROOT, path, pin), <msg>` | 7, 9, 11–13, 15, 16, 18, 19, 21–46 |
| `assert (subprocess.run([... "diff", "--quiet", x, "HEAD", "--", path], …).returncode == 0)` | `assert frozen_guards.commit_pin_holds(REPO_ROOT, path, x)` | 14, 17 |
| `assert sha256((REPO_ROOT / path).read_bytes()).hexdigest() == expected` | `assert frozen_guards.content_pin_holds(REPO_ROOT, path, expected)` | 14, 17 |
| `current = (REPO_ROOT / FROZEN_DECLARATION).read_bytes()`, `assert sha256(current).hexdigest() == D`, optionally `assert current.decode("utf-8") == _show(C, FROZEN_DECLARATION)` | `assert frozen_guards.content_pin_holds(REPO_ROOT, FROZEN_DECLARATION, D)`, optionally `assert frozen_guards.commit_pin_holds(REPO_ROOT, FROZEN_DECLARATION, C)` | 26–46 |

Checks over docs (`FROZEN_CUT` bodies and `CUTN_FROZEN_SHA256`) are untouched, as is cut 7's `assert_cut5_matcher_migration`, which compares two historical commits.

- [ ] **Step 1: Make the RED tree.** Format the 34 files in the working tree only (not committed). The rewritten checks read the working file, so this tree exercises every pin over formatted bytes.

```bash
cd "$(pwd -P)/python"
uv run --frozen ruff format -q --no-force-exclude tests/acceptance/n2_arms_cut10.py tests/acceptance/n2_arms_cut11.py tests/acceptance/n2_arms_cut12.py tests/acceptance/n2_arms_cut13.py tests/acceptance/n2_arms_cut14.py tests/acceptance/n2_arms_cut17.py tests/acceptance/n2_arms_cut19.py tests/acceptance/n2_arms_cut20.py tests/acceptance/n2_arms_cut21.py tests/acceptance/n2_arms_cut22.py tests/acceptance/n2_arms_cut28.py tests/acceptance/n2_arms_cut29.py tests/acceptance/n2_arms_cut30.py tests/acceptance/n2_arms_cut8.py tests/acceptance/n2_arms_cut9.py tests/acceptance/test_n2_cut10.py tests/acceptance/test_n2_cut4.py tests/acceptance/test_n2_cut5.py tests/acceptance/test_n2_cut6.py tests/acceptance/test_n2_cut8.py tests/n2_arms_cut16.py tests/n2_arms_cut18.py tests/n2_arms_cut31.py tests/n2_arms_cut32.py tests/n2_arms_cut35.py tests/n2_arms_cut37.py tests/n2_arms_cut38.py tests/n2_arms_cut3.py tests/n2_arms_cut45.py tests/n2_arms_cut46.py tests/n2_arms_cut4.py tests/n2_arms_cut5.py tests/n2_arms_cut6.py tests/n2_arms_cut7.py
git diff --stat | tail -1
```

Expected: `34 files changed`.

- [ ] **Step 2: Run the pin-check selection to verify it fails**

```bash
cd "$(pwd -P)"
GUARDS=$(for n in 6 7 9 $(seq 11 46); do printf "tests/acceptance/test_n2_cut%s.py " $n; done)
just test-one $GUARDS -k "frozen or byte_exact or unchanged" -p no:cacheprovider
```

Expected: `12 failed, 84 passed, 338 deselected`. The failures are the working-file checks: the declaration digests of cuts 28–32, 35, 37, 38, 45 and 46, and the content pins of cuts 14 and 17. The commit-pin loops still pass because `git diff … HEAD` cannot see an uncommitted format, which is why the old code would fail them only after Task 4.

- [ ] **Step 3: Rewrite the checks**

```bash
cd "$(pwd -P)/python"
uv run --frozen python - tests/acceptance <<'PY'
"""One-off rewrite of the live guards' byte-exact pin checks (beliefs-ea5ec7, spec §5)."""

import re
import sys
from pathlib import Path

LIVE = [6, 7, 9, *range(11, 47)]
DIFF_LOOP = re.compile(
    r'completed = subprocess\.run\(\n\s*\["git", "-C", str\(REPO_ROOT\), "diff", "--quiet", (\w+), "HEAD", "--", (\w+)\],\n'
    r"\s*check=False,\n\s*\)\n\s*assert completed\.returncode == 0,"
)
DIFF_INLINE = re.compile(
    r'assert \(\n\s*subprocess\.run\(\n\s*\["git", "-C", str\(REPO_ROOT\), "diff", "--quiet", (\w+), "HEAD", "--", (\w+)\],'
    r"(?:\n\s*check=False,\n\s*| check=False\n\s*)\)\.returncode\n\s*== 0\n(\s*)\)"
)
CONTENT = re.compile(r"assert sha256\(\(REPO_ROOT / (\w+)\)\.read_bytes\(\)\)\.hexdigest\(\) == (\w+)")
DECLARATION = re.compile(
    r"current = \(REPO_ROOT / FROZEN_DECLARATION\)\.read_bytes\(\)\n(\s*)assert sha256\(current\)\.hexdigest\(\) == (\w+)"
    r"(?:\n\s*assert current\.decode\(\"utf-8\"\) == _show\((\w+), FROZEN_DECLARATION\))?"
)


def declaration(match: re.Match[str]) -> str:
    indent, digest, commit = match.groups()
    rewritten = f"assert frozen_guards.content_pin_holds(REPO_ROOT, FROZEN_DECLARATION, {digest})"
    if commit:
        rewritten += f"\n{indent}assert frozen_guards.commit_pin_holds(REPO_ROOT, FROZEN_DECLARATION, {commit})"
    return rewritten


def rewrite(source: str) -> str:
    source = DIFF_LOOP.sub(r"assert frozen_guards.commit_pin_holds(REPO_ROOT, \2, \1),", source)
    source = DIFF_INLINE.sub(r"assert frozen_guards.commit_pin_holds(REPO_ROOT, \2, \1)", source)
    source = CONTENT.sub(r"assert frozen_guards.content_pin_holds(REPO_ROOT, \1, \2)", source)
    source = DECLARATION.sub(declaration, source)
    if "frozen_guards." in source and "\nimport frozen_guards\n" not in source:
        source = source.replace("\nimport pytest\n", "\nimport frozen_guards\nimport pytest\n", 1)
    return source


acceptance = Path(sys.argv[1])
for cut in LIVE:
    path = acceptance / f"test_n2_cut{cut}.py"
    before = path.read_text(encoding="utf-8")
    after = rewrite(before)
    if after != before:
        path.write_text(after, encoding="utf-8")
        print(f"rewrote {path.name}")
PY
uv run --frozen ruff check --fix --select F401 tests/acceptance/
```

Expected: 37 `rewrote test_n2_cutN.py` lines, then `Found 3 errors (3 fixed, 0 remaining).` (the `sha256`/`subprocess` imports the rewrite orphaned).

- [ ] **Step 4: Confirm nothing byte-exact is left over a `.py` target**

```bash
cd "$(pwd -P)/python"
for n in 6 7 9 $(seq 11 46); do f=tests/acceptance/test_n2_cut$n.py; grep -Hn '"--quiet"\|sha256(current)\|read_bytes()).hexdigest() == expected\|_show([A-Z0-9_]*, FROZEN_DECLARATION)' $f; done
```

Expected: no output.

- [ ] **Step 5: Run the selection to verify it passes on the formatted tree**

Run the Step 2 command again.
Expected: `96 passed, 338 deselected`. Then run `just test-one tests/test_frozen_guards.py tests/test_pin_equivalence.py tests/test_arm_staleness.py` and expect `42 passed`. That is the pin map under the new reader over formatted bytes.

- [ ] **Step 6: Restore the 34 files and re-run on the unformatted tree**

```bash
cd "$(pwd -P)/python"
git checkout -- tests/acceptance/n2_arms_cut10.py tests/acceptance/n2_arms_cut11.py tests/acceptance/n2_arms_cut12.py tests/acceptance/n2_arms_cut13.py tests/acceptance/n2_arms_cut14.py tests/acceptance/n2_arms_cut17.py tests/acceptance/n2_arms_cut19.py tests/acceptance/n2_arms_cut20.py tests/acceptance/n2_arms_cut21.py tests/acceptance/n2_arms_cut22.py tests/acceptance/n2_arms_cut28.py tests/acceptance/n2_arms_cut29.py tests/acceptance/n2_arms_cut30.py tests/acceptance/n2_arms_cut8.py tests/acceptance/n2_arms_cut9.py tests/acceptance/test_n2_cut10.py tests/acceptance/test_n2_cut4.py tests/acceptance/test_n2_cut5.py tests/acceptance/test_n2_cut6.py tests/acceptance/test_n2_cut8.py tests/n2_arms_cut16.py tests/n2_arms_cut18.py tests/n2_arms_cut31.py tests/n2_arms_cut32.py tests/n2_arms_cut35.py tests/n2_arms_cut37.py tests/n2_arms_cut38.py tests/n2_arms_cut3.py tests/n2_arms_cut45.py tests/n2_arms_cut46.py tests/n2_arms_cut4.py tests/n2_arms_cut5.py tests/n2_arms_cut6.py tests/n2_arms_cut7.py
git status --short | grep -v '^ M tests/acceptance/test_n2_cut' ; cd ..
```

Expected: only `tasks/` lines, if any. Then run the Step 2 command again: `96 passed, 338 deselected`.

- [ ] **Step 7: Commit**

```bash
cd "$(pwd -P)/python" && uv run --frozen ruff check . && uv run --frozen ruff format --check . && uv run --frozen pyright; cd ..
just test-fast
git add python/tests/acceptance/ tasks/
git commit -m "test(n2): live guards check their pins modulo formatting"
```

### Task 4: The format commit

**Files:**
- Modify: exactly the 34 paths under **Measured inputs**, by `ruff format` alone.

**Interfaces:**
- Consumes: Tasks 1–3 committed.
- Produces: the format commit `F`. Task 5 cites `F` and `F^` (the last byte-exact commit).

- [ ] **Step 1: Format the 34 files while the exclude still lists them**

```bash
cd "$(pwd -P)/python"
uv run --frozen ruff format --no-force-exclude tests/acceptance/n2_arms_cut10.py tests/acceptance/n2_arms_cut11.py tests/acceptance/n2_arms_cut12.py tests/acceptance/n2_arms_cut13.py tests/acceptance/n2_arms_cut14.py tests/acceptance/n2_arms_cut17.py tests/acceptance/n2_arms_cut19.py tests/acceptance/n2_arms_cut20.py tests/acceptance/n2_arms_cut21.py tests/acceptance/n2_arms_cut22.py tests/acceptance/n2_arms_cut28.py tests/acceptance/n2_arms_cut29.py tests/acceptance/n2_arms_cut30.py tests/acceptance/n2_arms_cut8.py tests/acceptance/n2_arms_cut9.py tests/acceptance/test_n2_cut10.py tests/acceptance/test_n2_cut4.py tests/acceptance/test_n2_cut5.py tests/acceptance/test_n2_cut6.py tests/acceptance/test_n2_cut8.py tests/n2_arms_cut16.py tests/n2_arms_cut18.py tests/n2_arms_cut31.py tests/n2_arms_cut32.py tests/n2_arms_cut35.py tests/n2_arms_cut37.py tests/n2_arms_cut38.py tests/n2_arms_cut3.py tests/n2_arms_cut45.py tests/n2_arms_cut46.py tests/n2_arms_cut4.py tests/n2_arms_cut5.py tests/n2_arms_cut6.py tests/n2_arms_cut7.py
git diff --stat | tail -1
uv run --frozen ruff format --check .
```

Expected: `34 files reformatted`, `34 files changed`, and the check passes. The exclude still skips these paths, which is spec §7 step 2.

- [ ] **Step 2: Verify the pins over the formatted bytes before committing**

```bash
cd "$(pwd -P)"
just test-one tests/test_frozen_guards.py tests/test_pin_equivalence.py tests/test_arm_staleness.py
GUARDS=$(for n in 6 7 9 $(seq 11 46); do printf "tests/acceptance/test_n2_cut%s.py " $n; done)
just test-one $GUARDS -k "frozen or byte_exact or unchanged" -p no:cacheprovider
```

Expected: `42 passed`, then `96 passed, 338 deselected`.

- [ ] **Step 3: Commit only the formatter output**

```bash
git add python/tests/ python/tools/
git diff --cached --stat | tail -1
git commit -m "style(n2): format the frozen Python files (pins hold modulo formatting)"
```

Expected: the cached stat shows `34 files changed`. The pre-commit hook passes.

- [ ] **Step 4: Re-run the selection on the committed tree, then close the child in a record-only commit**

Run the Step 2 commands again and expect the same counts. This is the old code's failure point, `git diff … HEAD`, and the rewritten checks now pass it. Then:

```bash
tasks done beliefs-92bd6f "34 frozen Python files formatted at $(git rev-parse --short HEAD); every pin holds modulo formatting"
git add tasks/ && git commit -m "chore(tasks): close the frozen-file format commit"
```

### Task 5: Retire the exclude and amend the doctrine

**Files:**
- Modify: `python/pyproject.toml` (remove `[tool.ruff.format]` and its comment)
- Modify: `python/tests/frozen_guards.py` (remove `protected_paths` and the now-unused `CITED_NOT_RUN` import)
- Modify: `python/tests/test_frozen_guards.py` (remove three tests, `PYPROJECT` and `import tomllib`)
- Modify: `python/tests/arm_staleness.py` (one docstring clause)
- Modify: `.git-blame-ignore-revs`, `AGENTS.md`, `docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md` (new §8), `docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md` (status line)

**Interfaces:**
- Consumes: `F`, the Task 4 format commit. Set it once in the shell:
  `F=$(git log --format=%H -1 --grep='^style(n2): format the frozen Python files')`, and check that `git show --stat "$F" | tail -1` reads `34 files changed`.
- Produces: nothing new.

- [ ] **Step 1: Remove the exclude, its test and its derivation (spec §7 step 3)**
  - `python/pyproject.toml`: delete everything from the comment line `# Freeze-protected files: byte-exact under a guard's pin, or cited-not-run evidence.` through the `]` that closes `exclude`, including the `[tool.ruff.format]` header. Leave `[tool.ruff]` with `line-length = 120` and `force-exclude = true`, then one blank line, then the existing `[tool.pyright]` table.
  - `python/tests/test_frozen_guards.py`: delete `test_the_protected_set_reads_both_freeze_forms_and_cited_surfaces`, `test_the_format_exclude_is_exactly_the_protected_set` and `test_an_explicit_path_cannot_format_a_protected_file`, plus the `PYPROJECT = …` line and `import tomllib`.
  - `python/tests/frozen_guards.py`: delete `protected_paths` and `from cited_not_run import CITED_NOT_RUN`.
  - `python/tests/arm_staleness.py`: replace `the declaration file stays byte-exact under its pins` with `the declaration file stays unchanged under its pins`.

Run:

```bash
cd "$(pwd -P)/python" && uv run --frozen ruff check . && uv run --frozen ruff format --check . && uv run --frozen pyright; cd ..
grep -rn --exclude-dir=.venv "protected_paths\|tool.ruff.format" python/ AGENTS.md || echo clean
just test-fast
```

Expected: ruff reports `All checks passed!` and every file formatted, `0 errors`, then `clean`, then test-fast green.

```bash
git add python/ && git commit -m "build(check): retire the freeze-protected format exclude"
```

- [ ] **Step 2: Add the format commit to `.git-blame-ignore-revs`** by appending:

```text
# ruff format over the freeze-protected files; pins hold modulo formatting (beliefs-ea5ec7)
<the output of git rev-parse "$F">
```

Verify with `git blame --ignore-revs-file .git-blame-ignore-revs python/tests/n2_arms_cut46.py | grep -c "^$(git rev-parse --short=8 "$F")" || true`, which should print `0`.

- [ ] **Step 3: Amend the doctrine.** Append this to `docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`. Then fill in the last byte-exact commit with `sed -i "s/<F^>/$(git rev-parse "$F^")/g" docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`.

```markdown
## 8. Pins hold modulo formatting — dated amendment, 2026-10-09

A pin's claim was byte-exact, so `ruff format` had to exclude every file a freeze claims
(`beliefs-a555d6`), and that exclude grew with every freeze. Formatting changes no
meaning, so the claim now holds up to formatting:

- **A pin on a `.py` target** holds when the target is byte-identical to the pinned
  original, or equivalent to it under `python/tests/pin_equivalence.py`. Equivalent means
  the same detected encoding, the same syntax tree with docstrings compared after
  `inspect.cleandoc`, every comment's text on the same statement, and every directive
  comment's physical line unchanged. The comparator reads only the standard library and
  fails closed. **Every other target stays byte-exact.**
- **A commit pin** compares the working file with `git cat-file blob <commit>:<path>`.
  A target absent at the pin holds while it stays absent, and a commit that no longer
  resolves is broken. **A content pin** resolves its digest to the version of the
  target in `HEAD`'s history with those bytes. When no version matches, the pin is
  broken, never passed.
- **A cited-not-run surface's bytes** are evidence up to formatting, on the same terms.
- **Re-pinning is still forbidden.** The pins keep naming the bytes each cut audited, and
  formatting is not a move §2 re-pins for. The comparator is what lets them hold.
- **The last byte-exact commit is `<F^>`.** A SHA-256 that a frozen results record
  publishes for a file formatted after it is checked with
  `git show <F^>:<path> | sha256sum`, and line numbers a record cites in such a file are
  read at that commit.

`python/tests/frozen_guards.py` (`commit_pin_holds`, `content_pin_holds`) applies this
for the portable suite, and every live guard calls the same two predicates at discharge.
The design is `docs/superpowers/specs/2026-10-09-freeze-pins-modulo-formatting-design.md`.
```

Also update the doctrine's header line `**Enforced by:**` by adding `python/tests/pin_equivalence.py` to the list of enforcing modules.

- [ ] **Step 4: Correct the current-facing claims**
  - `AGENTS.md`, in the Repository gates bullet: replace `Formatting excludes the freeze-protected files that `python/tests/test_frozen_guards.py` holds equal to the guards’ pins (beliefs-ea5ec7 retires the exclude); `.git-blame-ignore-revs` lists the reformat.` with `Freeze pins on Python files hold modulo formatting (frozen guard doctrine §8), so formatting covers every file; `.git-blame-ignore-revs` lists both reformats.`
  - `docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md`: after its `**Doctrine:**` header line, add `**Status:** the format exclude this design adds (§3.1) was retired on 2026-10-09 by `beliefs-ea5ec7`; see `docs/superpowers/specs/2026-10-09-freeze-pins-modulo-formatting-design.md`.`

- [ ] **Step 5: Verify the doctrine's recovery claim on one real record.** `tests/n2_arms_cut46.py` is pinned by `CUT46_DECLARATION_SHA256`:

```bash
test "$(git show "$F^":python/tests/n2_arms_cut46.py | sha256sum | cut -d' ' -f1)" = "$(grep -oP 'CUT46_DECLARATION_SHA256 = "\K[0-9a-f]{64}' python/tests/acceptance/test_n2_cut46.py)" && echo recovered
```

Expected: `recovered`.

- [ ] **Step 6: Commit**

```bash
just test-fast
git add .git-blame-ignore-revs AGENTS.md docs/superpowers/specs/ tasks/
git commit -m "docs(doctrine): freeze pins hold modulo formatting"
```

### Task 6: Verify and land

**Files:** none (the plan's execution amendments and task records).

- [ ] **Step 1: Run the full gate**, in the background with `run_in_background: true` and a 3600000 ms timeout:

```bash
cd "$(pwd -P)" && mkdir -p .work/freeze-pins-modulo-format && set -o pipefail && just gate 2>&1 | tee .work/freeze-pins-modulo-format/gate.log
```

Expected: exit 0, and the summary lines show the portable, N2 and TypeScript phases passing. Report the counts from the log's pytest summary lines, not from `tail`.

- [ ] **Step 2: Re-measure the three equality points** from the spec's §8:

```bash
cd "$(pwd -P)/python"
GUARDS=$(for n in 6 7 9 $(seq 11 46); do printf "tests/acceptance/test_n2_cut%s.py " $n; done)
cd .. && just test-one tests/test_frozen_guards.py && just test-one $GUARDS -k "frozen or byte_exact or unchanged" -p no:cacheprovider
```

`test_every_pin_in_a_live_guard_holds` and `test_every_pin_the_registry_records_as_falsified_really_is` passing on `HEAD` is the "new reader after the format commit" point. The `f134ee9` point is recorded in **Measured inputs** above. The Task 2 Step 4 run is the middle point.

- [ ] **Step 3: Whole-branch review.** Dispatch a fresh reviewer on `f134ee9..HEAD` with the spec and this plan, then run the corrective rounds the global instructions describe. Record each round in **Execution amendments** below and as a `review: impl round <n> …` task note.

- [ ] **Step 4: Land.** This is a personal-profile checkout, so it merges locally: `git -C <main checkout> merge --no-ff freeze-pins-modulo-format`. Then run `just check` on `main`, `tasks done beliefs-ea5ec7 "<one line>"` in that merge's follow-up commit, and `tt-report` before removing the worktree.

## Task records

Task 1 `beliefs-d9839d`, Task 2 `beliefs-c09b8f`, Task 3 `beliefs-6c52aa`, Task 4 `beliefs-92bd6f`, Task 5 `beliefs-d9dadf`, Task 6 `beliefs-acbf7e`; parent `beliefs-ea5ec7`.

## Execution amendments
