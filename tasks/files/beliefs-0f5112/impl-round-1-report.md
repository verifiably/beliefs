# beliefs-0f5112 implementation review, round 1

Reviewer: claude-opus-5-5 (Claude Code subagent, fresh context, read-only). Range: 240a989..HEAD of perf/0f5112-test-latency (code head 5de55eb, results c0c2a9e). Saved verbatim by the controller.

### Strengths

- **Plan alignment is close.** All three parts follow the spec's structure, helper shapes and constraints. The Task 2 ruling on the RED order and the Task 3 rulings on pyright and SONAME first-wins are well reasoned. I checked the first-wins change against K7a: one SONAME always maps to one canonical file, so the digest cannot differ.
- **Plan invariants hold, each checked in the tree:**
  - The five `Sabotage.before` anchors each occur exactly once in `adapter.py` (`grep -cxF`). K7b's `located`, `target`, `root` and `target_root` are still bound at 12 spaces.
  - The only `BYTE_MUTATION_PRIMITIVES` identifier in `adapter.py` is the existing `shutil.copy2` at line 135.
  - `root.py` is the only `atoms` importer under `src/`.
  - No machine-layout strings appear in added lines.
- **Review Focus 1 (AST cache) is met.** `parsed()` reads fresh bytes on every call, the key is `(bytes, filename)`, and the test covers hit, path separation, byte mutation and the 256 bound. I found no caller that mutates a returned tree, including `acceptance/test_durable_corpus.py`.
- **Review Focus 2 (`certified_work_dir`) is met.** The `try/finally` covers setup exceptions for all three fixtures, and the module-scoped fixture's teardown runs at module end. The forget calls use module attributes, so the test's monkeypatch is effective.
- **Review Focus 3 (`readonly_source`) is met.**
  - `scoped_source` rebinds `ops`, `dest` and `destination`, and the teardown asserts the source is byte-identical.
  - Two tests that now share the source gained `try/finally: session.close()`. That is needed: a writer session left open on the shared `written` root would leak into the next test.
  - Moving `sessions-root` to `tmp_path` is safe; baseline tests already open sessions there (`make_session(tmp_path)`).
- **Review Focus 4 and 5 (`add_records`, `add_tree`, `elves`): I traced each against the baseline and found them equivalent.**
  - `add_records`: lexical `normpath` comes before parent `realpath`. The `.pth` and `__pycache__`/`.pyc` filters match `PurePosixPath` (including `..pth` and a bare `.pth`). The refusal text is the same.
  - `add_tree`: sorting by name at each level of a depth-first walk gives the same order as `sorted(rglob)`. Symlinked directories become rows and are not entered. Pruning is limited to monotone names, and `.pyc`-named directories are not pruned.
  - `elves()`: the 18-byte predicate and the 20-byte header make 18–19-byte files raise `struct.error`, as the baseline does.
- **Error behaviour.** I checked CPython 3.13.12's `pathlib`: `is_file`/`is_symlink` still use `_ignore_error`, so `EACCES` propagated in the baseline too. `_lstat_mode` therefore introduces no permission-error regression.
- **Focused re-run.** `just test-one tests/test_closure_capture.py tests/test_capability_boundary.py -k "…new tests…"` gave 5 passed. The fifth new test is in the session-door module and was not re-run.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)

1. **A NUL byte in a RECORD entry now escapes `capture_closure` as a raw `ValueError`** (`python/src/beliefs/adapter.py`, `_lstat_mode` and `add_records`).
   - **Baseline:** `Path.is_file()`/`is_symlink()` catch `ValueError` (non-encodable path) and return False, so such an entry was refused as `MalformedClosure`.
   - **Candidate:** `_located_str` calls `os.path.realpath`, and `_lstat_mode` calls `os.lstat`. Both raise `ValueError: embedded null character` (I reproduced this on 3.13.12). `capture_closure` wraps only `OSError`.
   - **Effect:** a corrupt installed RECORD now crashes the walk instead of giving the typed refusal. It is very unlikely to happen.
   - **Fix:** in `add_records`, catch `ValueError` around `_located_str`/`_lstat_mode` and raise the existing `MalformedClosure` "no such file exists" message, or reject entries containing `"\0"` before joining. Also correct `_lstat_mode`'s docstring: it claims parity with `Path.is_file()`/`is_symlink()` but omits their `ValueError → False` arm.

2. **The pruned directory names in `add_tree` are hard-coded apart from the predicates they mirror** (`adapter.py` `add_tree`, the `excluded is _stdlib_excluded` / `_path_tree_excluded` branches).
   - **Hazard:** if someone later narrows `_stdlib_excluded` (stops excluding `site-packages`, say), pruning would still silently drop that subtree.
   - **Why the tests would not catch it:** the new test's assertion `not any("site-packages" in row …)` would keep passing because of the pruning.
   - **Fix:** add a check that every pruned name is excluded under any descendant, for example `assert all(pred((name, "x.py")) and pred(("a", name, "x.py")) for name in pruned)` per predicate. It could be a module-level assertion or a test case.

3. **`metadata_less_copy` no longer has a caller** (`python/tests/session_doors_fixture.py:143`, still listed in `__all__`). `exported_publication` inlines its `copytree` and sibling read instead. Either reuse the helper in `shared()` or delete it and its `__all__` entry.

4. **`exported_publication` has no read-only guard on its shared `export_root`** (`python/tests/test_session_sharing_doors.py`), although the plan's Global Constraints call both shared fixtures strictly read-only. `readonly_source` asserts on teardown; this fixture does not. Today every test touches only its own `x.copy`, so nothing is wrong now. A one-line teardown snapshot (the `tree(export_root)` before/after pattern the module already uses) would make the guarantee checked rather than assumed.

5. **The "no cross-call cache" test exercises less than the spec asks.**
   - The spec's verification 1(a) asks that file *or symlink* changes between two `capture_closure()` calls produce distinct manifests.
   - The plan narrowed this, and `test_root_matching_handles_double_slashes_and_walks_observe_live_mutations` uses two hand-built `_Closure` instances and a file change only.
   - The guarantee holds structurally (`_walk_closure` builds a new `_Closure`), so this is a coverage gap against the spec, not a defect.
   - Separately, the `rec_foreign_endian.so` case in the `elves` test is rejected by its `EI_DATA` mismatch alone. It does not prove that `e_machine` was unpacked in the flipped byte order; a same-`EI_DATA`, foreign-`e_machine` case would.

### Declined to judge

- **Benchmark validity under shared load** (B1's lower starting load) and the 395 s `test-full` timing: these are executor rulings on measurement conditions, not code.
- **The `add()` host-path normalization differences: two edge cases I set aside.**
  - **`..` as the last path component:** the `add()` path uses `_sandbox_of_str` without `_normalize_path_str`, so a host ending in `/..` would map to a different sandbox path than the baseline's `relpath`. No caller produces such a path; all are `normpath`'d, come from `realpath`, or come from `DirEntry`.
  - **Leading `//`:** `_located_str` keeps a leading `//`. This is a Linux no-op.
- **Distributions whose `locate_file` is not a plain path join** (zip or custom finders) with `str(dist.locate_file(""))` plus `os.path.join`: the baseline made the same path-like assumption, and no such distribution is in the closure.
- **`raw.decode("utf-8")` vs `read_text` newline translation in `parsed()`:** CRLF does not change any node the name scans read, and no caller uses source segments.
- **About 63 MiB of retained ASTs per worker:** the spec accepted this.
- **`DirEntry.is_*` raising `OSError` on filesystems without `d_type`:** it fails closed and `capture_closure` wraps it.
- **Placing the `certified_work_dir` exception test in `test_session_sharing_doors.py`** rather than a conftest-focused module: the plan specifies this location.
- **Hosted CI (3.11/3.13) not yet run on this branch:** it is a push decision, outside the review.

### Recommendations

- Fold Minors 1 and 2 into one small corrective commit. Each needs about three lines plus a focused test (`just test-one tests/test_closure_capture.py`).
- Minors 3–5 can go to the ledger as `minor (deferred)`.

### Assessment

**Ready to merge?** Yes.

**Reasoning:** The branch meets every Review Focus item and Global Constraint I could check. I traced the walker rewrite against the baseline and found it behaviour-equivalent apart from the documented `add_tree` fail-closed change and the NUL-byte edge in Minor 1. All findings are Minor and none weakens a test or a guarantee.

**Reviewer identity:** `claude-opus-5-5` (Claude Code subagent). I reviewed in a single pass: the adapter diff line by line, then the test fixtures, then the tests. Nothing was dispatched, and nothing in the checkout was changed.
