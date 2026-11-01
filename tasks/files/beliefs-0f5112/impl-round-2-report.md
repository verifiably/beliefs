# beliefs-0f5112 implementation review, round 2 (scoped re-review of 0a61785)

Reviewer: claude-opus-5-5 (Claude Code subagent, fresh context, read-only). Saved by the controller.

## Verdict

Ready to merge? Yes. The fix restores the baseline's typed refusal with byte-identical message text, the new test guards it (it errors without the fix: `ValueError` is not caught by `pytest.raises(MalformedClosure)`), and the five `Sabotage.before` anchors and the forbidden-identifier counts are unchanged. Critical 0, Important 0, Minor 3.

## Strengths

- Behaviour matches the baseline. A probe ran `_Closure.add_records` from three revisions against a fake distribution whose RECORD lists `a/bad\x00name.py`:
  - 240a989 raised `MalformedClosure("distribution 'nul': RECORD lists a/bad\x00name.py and no such file exists")`.
  - 0a61785^ raised `ValueError('lstat: embedded null character in path')`.
  - 0a61785 raised `MalformedClosure` with byte-for-byte the baseline's text.
- `str(PackagePath(e)) == str(PurePosixPath(e))` holds for the NUL entry and for `a//b.py`, `./a/b.py`, `a/b.py/`, `/abs/x.py` and `a/./b`.
- The NUL guard runs before `_located_str`. That matters because `os.path.realpath` also raises `ValueError` on a NUL (checked on Python 3.13.12). It also catches a NUL in a directory component.
- The `.pth`/`__pycache__` filter still runs first, so `x\0.pth` is skipped exactly as `PackagePath(...).suffix` skipped it at baseline.
- The `_lstat_mode` docstring is now accurate.

## Other places that could now raise `ValueError`

Each walker method on the whole branch was traced against 240a989:

- **`add`:** a NUL in the final name would raise `ValueError` from `_lstat_mode` where the baseline raised `ClosureUnsupported`. No caller can supply one:
  - `add_tree` passes `scandir` results.
  - `add_pth` passes glob results, and a `candidate` only after `is_file()` is True.
  - The symlink branch of `add_records` runs after the guard.
  - Symlink targets come from `readlink`.
  - `add_chain` passes `sys.executable`.
  - `add_native` already raised at `_located`/`realpath` in the baseline.
- **`add_tree` and `_add_tree_level`:** the root is a stdlib path or a `.pth` line that has already passed `Path.is_dir()`, and entries come from `scandir`. Neither can carry a NUL.
- **`add_pth`:** unchanged; it uses `pathlib`, which returns False on a NUL.
- **`root_of`, `sandbox_of`, `_root_row`:** the baseline caught `commonpath`'s `ValueError` and returned None. The string-prefix match never raises and also returns None.

## Issues

Critical: none. Important: none.

Minor:

1. **Non-UTF-8 locale gap.** `python/src/beliefs/adapter.py:470-471`. `UnicodeEncodeError` is a `ValueError`, and the baseline's `Path.is_file()`/`is_symlink()` caught it. Under a non-UTF-8 filesystem encoding, a RECORD entry with a character that encoding cannot hold would raise a bare `UnicodeEncodeError` from `realpath`/`lstat`. This is unverified: this host's C locale still reports utf-8, and so does CI. A fix would catch `ValueError` around `_located_str`/`_lstat_mode` and treat it as absent.
2. **The test doesn't pin the full message.** `python/tests/test_closure_capture.py:876`. It matches only `"no such file exists"`. Matching `re.escape("distribution 'nul': RECORD lists a/bad\x00name.py and no such file exists")` would pin it.
3. **The test docstring says "unencodable".** `python/tests/test_closure_capture.py:869`. A NUL encodes fine; it just cannot be part of a path. Suggested: "an entry with an embedded NUL".

## Regression checks

- **Anchors:** each occurs exactly once (`K7a`, the full two-line `K7b` block per `n2_arms_cut13.py:320`, `K7c`, `R13`, `R17`).
- **Forbidden identifiers:** the per-name counts in `adapter.py` are identical before and after the commit.
- **Lint and types:** `ruff check` and `ruff format --check` pass on both files, and `pyright` reports 0 errors.
- **Tests:** `just test-one tests/test_closure_capture.py::test_a_record_entry_with_a_nul_byte_is_a_malformed_closure_not_a_raw_value_error tests/test_closure_capture.py` gave 50 passed in 2.40 s (focused only).

## Declined to judge

- **Python 3.11 behaviour:** only the 3.13 venv was run. On 3.11, `pathlib` also returns False on `ValueError`.
- **`base` containing a NUL:** looks unreachable, since `importlib.metadata`'s path search suppresses listing errors.
