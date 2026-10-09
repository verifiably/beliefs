# Freeze pins hold modulo formatting

**Date:** 2026-10-09
**Task:** `beliefs-ea5ec7` (follows `beliefs-a555d6`, whose format exclude this retires)
**Measured against:** `main` at `f134ee9` — 43 guard modules (39 live, 4 cited not run),
942 table pins, ruff 0.16.1
**Amends:** `docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md` (new §8)

This is method, not a boundary: it closes no guarantee row, adds no row to the adoption
ledger, and changes no ranking.

## 1. Problem

A freeze pin claims a file is byte-exact: a commit pin (`git diff --quiet <commit> HEAD
-- <path>`) or a content pin (the SHA-256 of the bytes). `beliefs-a555d6` put
`ruff format` in the gate and had to exclude every Python file a freeze claims, because
formatting one would falsify its pins. That exclude is permanent as things stand and
grows with every freeze.

The byte-exact rule exists so "a reader can tell that the record they are citing is the
record that was made" (doctrine §3). Formatting changes no meaning, so the freeze can
keep that guarantee up to formatting, with the original bytes still recoverable from
git.

## 2. What the measurement found

A scratch copy of `f134ee9` with the exclude removed, formatted with ruff 0.16.1:

- **34 files reformat.** 31 of them are table-pinned, as the task recorded. Three more
  are claimed in other ways: `tests/n2_arms_cut46.py` (cut 46's scalar declaration pin
  only), and `tests/acceptance/test_n2_cut4.py` and `tests/n2_arms_cut4.py` (cited-not-run
  surfaces that no pin names).
- **All 34 pass the comparator in §3.** They have equal `ast.dump` once each docstring
  is compared after `inspect.cleandoc`, and an equal sequence of `COMMENT` tokens.
- **The live guards enforce these pins themselves.** The portable reader
  (`frozen_guards.holds`) mirrors checks that every live guard runs at discharge. 37 of
  the 39 live guards (cuts 7, 9 and 11–46, except cut 20; cuts 6 and 20 run no file pin
  check) loop over a `FROZEN_*` table
  with `git diff --quiet`. Cuts 14 and 17 also check content pins by SHA-256 (on cut 5's
  and cut 10's cited surfaces). Cuts 26–46 also pin their own declaration with
  `CUTN_DECLARATION_SHA256`, and some of them check the declaration against
  `_show(<commit>, FROZEN_DECLARATION)` too. Changing only the portable reader would
  leave every live guard red at the next discharge. The task's done-list does not cover
  this.
- **21 live pins assert absence.** Cuts 26–46 each pin `python/tests/n2_arms_cut25.py`
  at `5072609`, where the file does not exist, and it does not exist today either. The
  pin holds because `git diff` finds nothing. The task called it "an already-falsified
  pin", but it is a live pin that holds. A comparator that treats "missing at the pin"
  as broken would falsify all 21.
- **The pins broken today** are exactly the five in `test_n2_cut8.py` and the one in
  `test_n2_cut10.py`, both cited not run, all recorded in `cited_not_run.py`. Every live
  pin holds.

## 3. The comparator

A new module, `python/tests/pin_equivalence.py`, written against the stdlib only, so a
ruff upgrade cannot change a verdict:

```python
def equivalent(original: bytes, current: bytes, *, path: str) -> bool
```

- If `original == current`, the result is `True`.
- If `path` does not end in `.py`, the result is `False`: docs and every other target
  stay byte-exact.
- Otherwise both sides are read as Python reads source, from bytes. `ast.parse` and
  `tokenize.tokenize` both take the bytes and apply PEP 263 and the BOM themselves;
  nothing is decoded as UTF-8 by assumption. The two sides are equivalent when all four
  of these hold:
  1. **Encoding.** `tokenize.detect_encoding` returns the same encoding for both. A
     coding cookie that moves out of lines 1–2, or changes, breaks the pin even when the
     tree happens to agree.
  2. **Tree.** `ast.dump` (no position attributes) is equal after normalisation. The
     only normalisation is this: the docstring of a module, class or function (the
     leading `Expr` holding a `str` `Constant` in its body) is replaced by its
     `inspect.cleandoc` form. Every other string literal compares by value, including N2
     `before`/`after` texts and implicit concatenations, so a frozen arm declaration
     keeps its meaning. Because the bytes are parsed under their own encoding, the
     reviewer's latin-1 case (a moved cookie turning `'é'` into `'Ã©'`) differs here as
     well as in rule 1.
  3. **Comment attachment.** Each `COMMENT` token is reduced to its exact text plus an
     anchor, and the two sequences must be equal. The anchor is the statement the
     comment belongs to, named by its index in a pre-order walk of every `ast.stmt`
     (both trees are equal, so the indexes correspond). It is the innermost statement
     whose `lineno..end_lineno` contains the comment's line. A comment on a line no
     statement covers is anchored *before* the first statement that starts after it, or
     at the end of the module. A comment moved to a different statement therefore breaks
     the pin. A comment on line 1 or 2 (a shebang or a cookie) also keeps its line number.
  4. **Directive lines.** A directive comment is one whose text matches
     `#\s*(type:|noqa|pyright:|mypy:|pragma|fmt:|isort:|ruff:)`, case-insensitively.
     Its physical line's code, meaning the text before the comment decoded with the
     detected encoding and right-stripped, must be identical on both sides. A tool reads
     a directive by physical line, so a directive whose line formatting rewrote breaks
     the pin even when its statement anchor is unchanged. The 34 files hold no directive
     comments today; every match in them is inside an arm's string literal. The rule
     exists for future freezes.
- A decode, parse or tokenize failure on either side returns `False`. The comparator
  fails closed: it can be stricter than formatting needs, but never looser than these
  four rules.

Both sides are parsed by the same interpreter, so a difference in `ast.dump` between
Python 3.11 and 3.13 cannot split a verdict.

## 4. Pin resolution

`python/tests/frozen_guards.py` gains two path-level predicates. `holds(pin)` delegates
to them, and the live guards call them (§5).

```python
def commit_pin_holds(repo_root: Path, target: str, commit: str) -> bool
def content_pin_holds(repo_root: Path, target: str, digest: str) -> bool
```

**Commit pin.** The original is `git show <commit>:<target>`, and the current state is
the working file.

| at the pin | working file | verdict |
|---|---|---|
| absent | absent | holds (the 21 absence pins) |
| absent | present | broken |
| present | absent | broken |
| present | present | `equivalent(original, current, path=target)` |

"Absent at the pin" means `git cat-file -e <commit>:<target>` fails while the commit
itself resolves (`git cat-file -e <commit>^{commit}`). If the commit does not resolve,
the pin is broken. Today's reader compares against `HEAD`; the new one compares against
the working file, as content pins already do, so an uncommitted edit to a frozen file
shows up before it is committed. A discharge runs on a clean tree, so its verdicts do
not change.

**Content pin.** If the working file's SHA-256 equals the digest, the pin holds and
nothing else is read. Otherwise the original is resolved by scanning `target`'s history
from `HEAD` (`git rev-list HEAD -- <target>`, then each commit's blob at that path,
deduplicated) for a blob whose SHA-256 equals the digest. The pin holds when such a blob
exists and `equivalent(blob, current, path=target)`. If no blob resolves, the pin is
broken, never passed. Resolution is cached within a process, keyed by
`(repo_root.resolve(), target, digest)`: a blob found in one repository's history is
never evidence about another's.

**Scalar declaration pin.** It is a content pin over `FROZEN_DECLARATION` with the
guard's `CUTN_DECLARATION_SHA256`. A new reader, `declaration_digest(guard)`, returns
that constant (found by the `^CUT\d+_DECLARATION_SHA256$` name). Where a guard also has a
`CUTN_DECLARATION_COMMIT`, that commit's blob is a commit pin over the same target. The
portable suite has never checked scalar pins. It gains
`test_every_declaration_pin_in_a_live_guard_holds`, because formatting now touches ten of
those declarations.

## 5. The live guards' own checks

Doctrine §2 says a live guard's pin checks are machinery, so they may change. Each live
guard's pin-check code is rewritten to call the two predicates; its tables, constants,
arm declarations and assertion messages are unchanged:

- `git diff --quiet <pin> HEAD -- <path>` becomes
  `frozen_guards.commit_pin_holds(REPO_ROOT, path, pin)` (37 guards).
- `sha256((REPO_ROOT / path).read_bytes()).hexdigest() == expected` over a `.py` target
  becomes `frozen_guards.content_pin_holds(REPO_ROOT, path, expected)` (cuts 14, 17).
- The scalar declaration check, `sha256(current) == CUTN_DECLARATION_SHA256`, becomes
  `content_pin_holds(REPO_ROOT, FROZEN_DECLARATION, CUTN_DECLARATION_SHA256)`. Where a
  guard also compares the declaration with `_show(<commit>, FROZEN_DECLARATION)`, that
  comparison becomes `commit_pin_holds(REPO_ROOT, FROZEN_DECLARATION, <commit>)`.
- Checks over docs (`FROZEN_CUT` design bodies, `CUTN_FROZEN_SHA256`) are untouched.
  They are not `.py` and stay byte-exact.

No `FROZEN_*` table, digest constant, cited-not-run guard or declaration is edited
(doctrine §3). The four cited guards (cuts 4, 5, 8, 10) are refused collection and
keep their byte-exact code as evidence.

`tests/acceptance` is ignored by `addopts`, so the plan names the invocation that runs
each rewritten pin-check test outside a discharge. Each one runs green both before and
after the format commit.

## 6. Doctrine amendment (§8, dated 2026-10-09)

Appended to the frozen guard doctrine:

- A pin on a `.py` target holds when the target is byte-identical, or when it is
  equivalent to the pinned original under the comparator. Every other target stays
  byte-exact.
- This covers a cited-not-run surface's bytes as well: they are evidence up to
  formatting, and the original bytes stay recoverable.
- The amendment names the **last byte-exact commit**, the parent of the format commit.
  A SHA-256 that a frozen results record publishes for a formatted file can be checked
  there with `git show <that commit>:<path> | sha256sum`. Line numbers that a record
  cites in a formatted file are read at that commit.
- Re-pinning is still forbidden. Formatting is not a legitimate move that §2 would
  re-pin for: the pins keep naming the bytes the cut audited, and the comparator is what
  lets them hold.

## 7. Retiring the exclude

The pre-commit hook runs `ruff format --check .`, so the exclude is removed only after
the files it protects are already formatted. Every commit passes the gate as it stands,
in this order:

1. The comparator, the two predicates, the scalar check and the rewritten live-guard
   checks, with the exclude still in place.
2. The format commit: `ruff format --no-force-exclude` over exactly the 34 paths, and
   nothing else. The exclude still lists them, so `ruff format --check .` skips them and
   stays green. The tests that read the exclude also stay green: the exclude still
   equals the protected set, and an explicit path is still skipped.
3. Removal of the exclude, `protected_paths` and the three tests below. `ruff format
   --check .` now reads the 34 files and finds them formatted.
4. The format commit's SHA appended to `.git-blame-ignore-revs`, together with the
   doctrine §8 amendment (§6), which names the format commit's parent as the last
   byte-exact commit, and the `AGENTS.md` and ruff-format-gate spec updates.

What step 3 removes:

- `[tool.ruff.format] exclude` and its comment are removed from `python/pyproject.toml`.
  `force-exclude = true` stays: it keeps ruff's own exclusions in force for paths an
  editor passes explicitly.
- These are removed from `python/tests/test_frozen_guards.py`:
  `test_the_format_exclude_is_exactly_the_protected_set`,
  `test_an_explicit_path_cannot_format_a_protected_file` and
  `test_the_protected_set_reads_both_freeze_forms_and_cited_surfaces`.
  `frozen_guards.protected_paths` goes with them; nothing else calls it.
  `declaration_pin` stays, because the new scalar check reads it.
- `AGENTS.md`'s formatting sentence and the ruff-format-gate spec's pointer to this
  task are updated to say the exclude is gone.

## 8. Verification

- **Comparator unit tests:**
  - These hold: a formatting-only change, and a docstring that is only re-indented.
  - These break: a changed string literal, comment, statement or docstring text; a
    `# type: ignore[...]` moved to a different statement; a plain comment moved across a
    statement boundary; a directive whose physical line was reformatted; and a
    `# coding: latin-1` cookie moved below line 2 over a non-ASCII literal, the
    reviewer's reproduction.
  - These also break: a non-`.py` target that differs by one byte, and input that will
    not parse.
- **Resolution unit tests** on a scratch git repository: an absent→absent commit pin
  holds and absent→present breaks; a content pin whose blob is in history and is
  equivalent holds; one whose digest matches no blob breaks. Two repositories with the
  same target and digest, where only the first has the matching blob, give holds for the
  first and broken for the second, in that order, in one process.
- **Pin-map equality:** `{guard: broken_pins}` over all 43 guards is identical at three
  points: `f134ee9` with the old reader, the new reader before the format commit, and the
  new reader after it. That is the five cut-8 targets and the one cut-10 target, and
  nothing else.
- Every live guard's declaration pin holds before and after the format commit.
- The rewritten pin-check tests in every live guard pass before and after the format
  commit.
- The pre-commit hook passes on each of the four commits in §7, with no bypass.
- `ruff format --check` passes with no exclude, and `just gate` is green.

## 9. Rejected alternatives

- **Re-pin the live tables to the format commit,** the §2 route for a legitimate move.
  That means 37 guards' tables and a dated citation amendment on each cut record, and it
  repeats at every freeze. It also makes each pin claim the cut audited bytes that did
  not exist then, which is §3's objection, and it re-mints cut 14's and cut 17's content
  pins over cited surfaces, which §5 reverted once already.
- **A git `textconv` diff driver** that makes `git diff` ignore formatting. It is
  invisible at the call site, does not reach the SHA-256 checks, and depends on local git
  configuration.
- **Keep a cited-only exclude** for the two unpinned cited surfaces. That keeps a
  standing exclude for no benefit, since the comparator covers them like any other file.
