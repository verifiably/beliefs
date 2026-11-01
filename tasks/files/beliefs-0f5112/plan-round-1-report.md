# Plan Review Round 1 Report

Conversation: `d2fb42ce-f96f-40dd-a320-e988149558b0`
Reviewer: antigravity
Frozen Revision Verified: `3b23826555a485749e147061af91566b3e28e9eb:docs/superpowers/plans/2026-11-01-test-fast-latency.md` (verified SHA-256: `ee893be64291b4ca620be23fbafdce1b5de834877a11eaa0092150873ff11613`; baseline spec verified at `fb26bebe081caf5b3ec7a6b3081f53ea232a72ff:docs/superpowers/specs/2026-11-01-test-fast-latency-design.md`)
Verdict: revise
Summary Counts: Critical: 0, Important: 4, Minor: 3

### Strengths

- **Exact codebase alignment on targets, counts, and boundaries:** Every file path, line range, and symbol signature across Tasks 1-4 matches the live worktree at `.worktrees/0f5112-test-latency/`. Baseline and candidate counts are exact: `6,403` non-N2 Python tests + `7` new non-parametrized regression tests (`1` in Task 1, `2` in Task 2, `4` in Task 3) = `6,410 passed, 1 skipped`; standalone `tests/test_n2.py` = `46` items; full TypeScript suite = `155` tests; and the uncertified-host skip partition on the two session-door modules is `6 passed, 58 skipped` (`3 passed, 37 skipped` in `test_session_sharing_doors.py` and `3 passed, 21 skipped` in `test_session_publish_door.py`).
- **Sound `adapter.py` guard and sabotage-anchor preservation:** Tasks 3-4 strictly preserve `RAW_WRITE_ALLOWLIST["adapter.py"] == {"copy2"}` (zero new `BYTE_MUTATION_PRIMITIVES` names), keep all five N2 `Sabotage.before` anchors unique at exact indentation (`K7a` at `python/src/beliefs/adapter.py:451`, `K7b` plus `target_root`/`located`/`target`/`root` bindings at `adapter.py:303-306`, `K7c` at `adapter.py:390`, `R13` at `adapter.py:134`, `R17` at `adapter.py:768`), and maintain zero cross-call caching.
- **Safe read-only fixture sharing and teardown LIFO ordering:** Only `test_the_artifact_binding_searches_every_carrier` (`python/tests/test_session_sharing_doors.py:298-301`) previously accessed `x.s`, which `exported_publication.other_sibling` cleanly replaces; `open_attended_session` (`python/src/beliefs/session/__init__.py:86-190`) writes solely under `operations_root` (`s.ops / "sessions-root"`), so rebinding `ops` and `dest` into `tmp_path` keeps `readonly_source.base` byte-invariant across all 8 non-mutating items; and pytest's LIFO module teardown guarantees `readonly_source` asserts `_files(s.base) == before` before `certified_module_work` deletes the directory.
- **Clean benchmark methodology under `.tt.toml` policy-off:** Alternating detached `240a989` (`B1..B3`) and `perf/0f5112-test-latency` (`C1..C3`) runs work without worktree branch conflicts (`240a989` can be checked out detached in `.worktrees/0f5112-test-latency` while `main` holds `240a989`), piping through `tee` ensures `tools/tt` captures stdout and records `tests`, and the four keep-or-revert gates match the approved spec verbatim.

---

### Findings

#### Critical

None.

#### Important

1. **`scoped_source` calls `mkdir()` without `parents=True`, crashing Task 2's own planned regression test (`FileNotFoundError`)**
   - **Plan lines:** `150`, `204`, `228`
   - **Target code:** `.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py:94-153`
   - **What is wrong:** Task 2 Step 1's planned test `test_scoped_source_isolates_ops_and_dest_leaving_readonly_source_unchanged` (plan line `204`) calls `scoped = scoped_source(source, tmp_path / "per-test")` without first creating `tmp_path / "per-test"`. Yet Task 2 Step 3 item 3 (plan line `228`; see also Interfaces line `150`) instructs `scoped_source` to create `ops = tmp_path / "ops"` and `dest = tmp_path / "dest"` with `(ops.mkdir(), dest.mkdir())` (no `parents=True`).
   - **Why it matters:** Calling `(tmp_path / "per-test" / "ops").mkdir()` when `tmp_path / "per-test"` does not exist raises `FileNotFoundError` at runtime, causing Task 2's own new test to fail at Step 4 (`GREEN`).
   - **Concrete fix:** Update plan lines `150` and `228` so `scoped_source` creates directories with `ops.mkdir(parents=True, exist_ok=True)` and `dest.mkdir(parents=True, exist_ok=True)`.

2. **Task 2 Step 4 combines `tests/acceptance/...` and `tests/test_fixture_grouping.py` in a single `just test-one` command, crashing `test_fixture_grouping.py` via `sys.modules["conftest"]` shadowing (`TypeError`)**
   - **Plan lines:** `20`, `238`
   - **Target code:** `.worktrees/0f5112-test-latency/python/tests/test_fixture_grouping.py:7,44`, `.worktrees/0f5112-test-latency/python/tests/conftest.py:32`, `.worktrees/0f5112-test-latency/python/tests/acceptance/conftest.py:204`
   - **What is wrong:** Task 2 Step 4 (plan line `238`) runs `just test-one tests/test_session_sharing_doors.py tests/test_session_publish_door.py tests/acceptance/test_owned_replica_publication_acceptance.py tests/acceptance/test_n2_cut47.py tests/test_fixture_grouping.py` in one pytest invocation. Neither `python/tests/__init__.py` nor `python/tests/acceptance/__init__.py` exists and `python/pyproject.toml` uses default `importmode=prepend`. During `_set_initial_conftests` (before collecting any test module), pytest loads `tests/conftest.py` and then `tests/acceptance/conftest.py`, deleting and overwriting `sys.modules["conftest"]` with `tests/acceptance/conftest.py` (the exact mechanism Global Constraints line `20` warns about). When `tests/test_fixture_grouping.py:7` executes `from conftest import pytest_collection_modifyitems`, it receives `tests/acceptance/conftest.py:204`'s 3-argument hook `(session, config, items)` instead of `tests/conftest.py:32`'s 1-argument hook `(items)`.
   - **Why it matters:** `test_fixture_grouping.py:44` (`pytest_collection_modifyitems(items)`) fails deterministically with `TypeError: pytest_collection_modifyitems() missing 2 required positional arguments: 'config' and 'items'`. (In `just test-fast`, `pyproject.toml:43`'s `--ignore=tests/acceptance` prevents `tests/acceptance/conftest.py` from loading.)
   - **Concrete fix:** Split Task 2 Step 4 (plan line `238`) into two separate `just test-one` invocations:
     `just test-one tests/test_session_sharing_doors.py tests/test_session_publish_door.py tests/test_fixture_grouping.py && just test-one tests/acceptance/test_owned_replica_publication_acceptance.py tests/acceptance/test_n2_cut47.py`.

3. **Task 3 Step 1's `add_records()` `ELOOP` test specification fails to trigger `ELOOP` or `MalformedClosure` if implemented as a leaf self-referential symlink**
   - **Plan lines:** `283`, `299`
   - **Target code:** `.worktrees/0f5112-test-latency/python/tests/test_closure_capture.py` (new `test_add_records_resolves_symlinked_parents_relative_entries_pth_edges_and_refusals`), exercising `.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py:298-314,362-380`
   - **What is wrong:** Plan line `283` specifies: *"Verify `add_records()` raises `MalformedClosure` matching `r"RECORD lists a/missing\.py and no such file exists"` on a missing entry, a directory entry, and a self-referential symlink loop (`ELOOP`)."* Because `_lstat_mode(located_str)` calls `os.lstat(located_str)`, POSIX `lstat(2)` does not dereference the final path component. If an implementer creates a leaf self-referential symlink `(site / "a" / "missing.py").symlink_to("missing.py")`, `os.lstat` returns `S_IFLNK` (no `ELOOP`), `add_records()` delegates `stat.S_ISLNK(mode)` to `self.add(...)`, and `self.add(...)` (`adapter.py:298-314`) records `("symlink", "missing.py")`, sees `target_host.is_symlink() == True`, hits `if sandbox in self.rows: return sandbox`, and returns without raising any exception.
   - **Why it matters:** A natural implementation of `"a self-referential symlink loop"` at `a/missing.py` never exercises `errno.ELOOP` in `_lstat_mode` and fails the `pytest.raises(MalformedClosure, ...)` assertion. By contrast, making the **parent directory** a symlink loop — `(site / "a").symlink_to("a")` with `RECORD` listing `"a/missing.py"` — causes `os.path.realpath(".../site/a")` (`strict=False`) to return `".../site/a"` and `os.lstat(".../site/a/missing.py")` to raise `OSError(errno.ELOOP)`, returning `None` from `_lstat_mode` and raising the exact `MalformedClosure` message.
   - **Concrete fix:** Clarify plan line `283` so the three refusal sub-cases each list `"a/missing.py"` in `RECORD` against: (a) absent `a/missing.py`, (b) directory `(site / "a" / "missing.py").mkdir(parents=True)`, and (c) parent-directory symlink loop `(site / "a").symlink_to("a")`.

4. **Task 5 Step 3's scratch release contradicts `retained-item-records.md` on the raw-plus-portable layout fallback and omits Task 4-5 scratch files from manifest/park accounting**
   - **Plan lines:** `332`, `404`-`406`
   - **Target code / records:** `.worktrees/0f5112-test-latency/tasks/beliefs-0f5112.md:40-42`, `.worktrees/0f5112-test-latency/tasks/files/beliefs-0f5112/scratch-manifest-v1.json:1-58` (governed by `~/.agents/skills/references/retained-item-records.md:186-195,346-350,405-436`)
   - **What is wrong:**
     1. Plan line `404` instructs: *"use the raw-plus-portable fallback if `ops-check` flags host layout), verify `tasks show beliefs-0f5112` lists every attachment and SHA-256 digests match, then remove `$WORK_ROOT/beliefs/beliefs-0f5112` once every manifest member has a verified disposition and write its `retained:` `state: "released"` JSON note"*. Under `retained-item-records.md:195,349,416,425-435`, *"Attachment of a derivative never releases raw bytes"*: if the raw-plus-portable fallback is triggered for any file, its exact raw bytes must remain preserved in `$WORK_ROOT/beliefs/beliefs-0f5112` under an explicit `kind: "evidence"`, `state: "kept"` record owned by an open task, which blocks deleting or releasing `$WORK_ROOT/beliefs/beliefs-0f5112`. (Note also that `tools/ops-check:40-44,374-420` v16 already suppresses mechanical host layout on verified ledger-backed `tasks attach` files.)
     2. Plan line `404` checks *"every manifest member"*, while `tasks/beliefs-0f5112.md:41` currently pins `scratch-manifest-v1.json` (only the 9 pre-implementation files from spec park, using worktree path `"$WORK_ROOT/beliefs/.worktrees/0f5112-test-latency/tasks/files/beliefs-0f5112/scratch-manifest-v1.json"`). Tasks 4 and 5 add 11+ new files (`bench-pilot.log`, `bench-B{1,2,3}.log`, `bench-C{1,2,3}.log`, `cand-durations.log`, `cand-attribution.json`, `test-full.log`, `impl-round-<n>-report.md`) to `$WORK_ROOT/beliefs/beliefs-0f5112/`, and Task 4 Step 1 (line `332`) includes a conditional `tasks park --reason quiet` branch after writing or attempting `bench-pilot.log` without refreshing the manifest/checkpoint.
   - **Why it matters:** Deleting `$WORK_ROOT/beliefs/beliefs-0f5112` after taking the raw-plus-portable fallback violates `retained-item-records.md`, and parking at line `332` or releasing at line `404` against `scratch-manifest-v1.json` alone leaves the Task 4-5 files uninventoried.
   - **Concrete fix:**
     - On plan line `332` (and before any conditional park), state that if `$WORK_ROOT/beliefs/beliefs-0f5112/` contents changed, a fresh immutable manifest attachment and updated `retained:` + `retention checkpoint:` notes must be recorded before `tasks park`.
     - On plan line `404`, state that `$WORK_ROOT/beliefs/beliefs-0f5112` is removed and marked `state: "released"` **only** if no file required the raw-plus-portable layout fallback (if any file did, retain its raw copy in `$WORK_ROOT/beliefs/beliefs-0f5112` with an explicit `kind: "evidence"`, `state: "kept"` record transferred to an open follow-up task and keep the enclosing directory), and require the release `purpose` (or a final manifest attachment) to account for both all 9 `scratch-manifest-v1.json` entries and all Task 4-5 benchmark/review files (naming which were attached vs discarded as regenerable logs/profiles summarized in `docs/plans/2026-11-01-test-fast-latency-results.md`).

#### Minor

1. **Task 3 Test 1 `monkeypatch` target for `importlib.metadata.distributions` must be a callable, not a tuple**
   - **Plan line:** `272`
   - **Target code:** `.worktrees/0f5112-test-latency/python/tests/test_closure_capture.py` (calling `.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py:363`)
   - **What is wrong:** Plan line `272` says *"monkeypatch `importlib.metadata.distributions` to `(dist,)`"*, whereas `_Closure.add_records()` (`adapter.py:363`) calls `importlib.metadata.distributions()`. Patching the function to a tuple raises `TypeError: 'tuple' object is not callable`.
   - **Why it matters:** Causes a false test-authoring `TypeError` when writing Test 1.
   - **Concrete fix:** Change `"to (dist,)"` on plan line `272` to `"to lambda: (dist,)"`.

2. **`add_tree` `os.scandir` closing/file-exclusion wording and `sandbox_of` exact-root `"."` slice in Task 3**
   - **Plan lines:** `277`, `296`, `298`
   - **Target code:** `.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py:281-288,354-361` and `.worktrees/0f5112-test-latency/python/tests/test_closure_capture.py`
   - **What is wrong:**
     - On line `298`, `sorted(os.scandir(current_dir), key=lambda e: e.name)` omits a `with os.scandir(current_dir) as scan:` context manager (leaving the directory FD open until GC if an `OSError` aborts iteration early), and contrasts the pruned branch (*"When `excluded is _stdlib_excluded or excluded is _path_tree_excluded`, skip recursing into directories where `excluded(rel_parts)` is `True`"*) against *"for any other `excluded` callable, recurse into non-symlink directories and test `excluded(rel_parts)` per entry without pruning"* — which could be misread as omitting `excluded(rel_parts)` on non-directory entries (e.g., a `.pyc` file outside `__pycache__` or an excluded symlink) in the pruned branch. Test 2 (line `277`) only places a `.pyc` inside `__pycache__`, so it would not catch that misreading.
     - On line `296`, `sandbox_of` mentions *"string slicing in `root_of` and `sandbox_of`"* without repeating the spec's exact-root rule (`"."` when `located_str == real_str`, else `located_str[len(prefix_str):]`, spec line `409`); bare `located_str[len(prefix_str):]` evaluates to `""` (`f"{sandbox_root}/"`) instead of `f"{sandbox_root}/."` when `located == host_root`.
   - **Why it matters:** Prevents FD leak warnings on error paths and avoids edge-case divergence from `root.rglob("*")` and `os.path.relpath(located, host_root)`.
   - **Concrete fix:** On line `298`, use `with os.scandir(current_dir) as scan: entries = sorted(scan, key=lambda e: e.name)` and state explicitly that `excluded(rel_parts)` filters every entry (files, symlinks, and directories) for all predicates while directory pruning applies only to `_stdlib_excluded` and `_path_tree_excluded` (adding a top-level `site / "top.pyc"` exclusion check to Test 2 on line `277`). On line `296`, specify `relative = "." if located_str == real_str else located_str[len(prefix_str):].replace(os.sep, "/")`.

3. **Task 5 Step 3-4 sibling cleanup handoff omits bidirectional task linking, `--stamp` checkpoint attribution inspection, and basis ancestry verification before branch deletion**
   - **Plan lines:** `405`, `410`-`411`
   - **Target records:** `.worktrees/0f5112-test-latency/tasks/beliefs-0f5112.md` (governed by `~/.agents/skills/references/retained-item-records.md:257-270,393-395`)
   - **What is wrong:** Line `405` files `<cleanup-id>` without linking both task records (`beliefs-0f5112` and `<cleanup-id>`, required by `retained-item-records.md:393-394`) or specifying `tasks note beliefs-0f5112 "<checkpoint>" --stamp` plus explicit `observer session attribution unknown` recording when no `harness_session` stamp is emitted (`retained-item-records.md:257-262`). Line `410` deletes `perf/0f5112-test-latency` without explicitly verifying `git merge-base --is-ancestor <basis-commit> main` before/after branch deletion (`retained-item-records.md:265-270`).
   - **Why it matters:** Keeps Task 5's closeout checklist self-contained against all mandatory clauses of `retained-item-records.md`.
   - **Concrete fix:** Add bidirectional task notes/links between `beliefs-0f5112` and `<cleanup-id>` plus `--stamp` attribution handling to line `405`, and add `git merge-base --is-ancestor <basis-commit> main` verification around `git branch -d perf/0f5112-test-latency` on line `410`.

---

### Declined to judge

- Repo-wide `importmode = "importlib"` or adding `python/tests/__init__.py` to eliminate `sys.modules["conftest"]` collisions globally: outside `beliefs-0f5112`'s approved spec scope, which prohibits changing pytest configuration outside the targeted modules.
- Unhashed disk-read fallback behavior of `_is_loadable_elf` / `_elf_architecture` (`python/src/beliefs/adapter.py:484-503`) on synthetic 18-19-byte truncated `\x7fELF` files inserted directly into `rows`/`plan`: pre-existing behavior untouched by the approved spec.
- Hosted GitHub Actions runtime delta on 4-worker Linux runners: remote push is out of scope for local closeout (`do NOT push`), and the spec scopes quantitative verification to the local 16-worker certified host.
