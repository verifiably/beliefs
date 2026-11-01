# Plan Review Round 2 — beliefs-0f5112

Conversation: `4d688557-c3e4-4041-af7f-a0a6476635b3`
Reviewer: antigravity
Frozen Revision Verified: 7e4548c6edb6660a2219a6ca5f8244e2cdfe21ba:docs/superpowers/plans/2026-11-01-test-fast-latency.md
Verified Plan SHA-256: 4c629b793396587f923383dd1e64f078e66e760e9c21f55a3e34287881cfb10f
Baseline Approved Spec Verified: fb26bebe081caf5b3ec7a6b3081f53ea232a72ff:docs/superpowers/specs/2026-11-01-test-fast-latency-design.md (SHA-256: d4833eec7e76a731bc93fa76aad5705ac760521570bfb273be8535480c15ba87)
Verdict: accept
Summary Counts: Critical: 0, Important: 0, Minor: 1

## Round 1 Findings Disposition

- **Round 1 Important 1 (`scoped_source` parent directory creation) — Resolved:** Both Task 2 Interfaces (`plan line 150`) and Task 2 Step 3 item 3 (`plan line 228`) now explicitly specify `ops.mkdir(parents=True, exist_ok=True)` and `dest.mkdir(parents=True, exist_ok=True)`, matching `scoped_source(source, tmp_path / "per-test")` in `test_scoped_source_isolates_ops_and_dest_leaving_readonly_source_unchanged` (`plan line 204`).
- **Round 1 Important 2 (`sys.modules["conftest"]` collision when combining `tests/test_fixture_grouping.py` and `tests/acceptance/...`) — Resolved:** Global Constraints (`plan line 20`) and Task 2 Step 4 (`plan line 238`) split `just test-one tests/test_session_sharing_doors.py tests/test_session_publish_door.py tests/test_fixture_grouping.py` from `just test-one tests/acceptance/test_owned_replica_publication_acceptance.py tests/acceptance/test_n2_cut47.py`. Audited all `from conftest import` sites across `.worktrees/0f5112-test-latency/python/tests/`; no `just test-one` command in Tasks 1–5 combines a root `conftest` importer with `tests/acceptance/...`.
- **Round 1 Important 3 (`ELOOP` test setup in `test_add_records_resolves_symlinked_parents_relative_entries_pth_edges_and_refusals`) — Resolved:** Task 3 Step 1 Test 3 (`plan line 283`) explicitly specifies the three `"a/missing.py"` refusal sub-cases: (a) absent `a/missing.py`, (b) directory `(site / "a" / "missing.py").mkdir(parents=True)`, and (c) parent-directory symlink loop `(site / "a").symlink_to("a")`. Verified against stdlib `posixpath.realpath(..., strict=False)` that `os.path.realpath(".../site/a")` returns `".../site/a"`, causing `os.lstat(".../site/a/missing.py")` to raise `OSError(errno.ELOOP)` so `_lstat_mode` returns `None` and `add_records()` raises `MalformedClosure` matching `r"RECORD lists a/missing\.py and no such file exists"`.
- **Round 1 Important 4 (Scratch manifest reconciliation across Task 1, conditional Task 4 park, and Task 5 closeout + raw-plus-portable fallback rule) — Resolved:** Task 1 Step 1 (`plan line 57`) checks against the latest pinned scratch manifest (`scratch-manifest-v2.json` or newer); Task 4 Step 1 (`plan line 332`) requires attaching a fresh immutable scratch manifest plus updated `retained:` and `retention checkpoint:` (`--stamp`, `observer session attribution unknown` handling) before any conditional park if `$WORK_ROOT/beliefs/beliefs-0f5112/` changed; and Task 5 Step 3 item 2 (`plan line 404`) inventories all final contents into `scratch-manifest-final.json` (via `/tmp/scratch-manifest-final.json` outside the container) and releases `$WORK_ROOT/beliefs/beliefs-0f5112` only when no file required the raw-plus-portable fallback and every manifest member has a verified disposition, strictly matching `~/.agents/skills/references/retained-item-records.md`.
- **Round 1 Minor 1 (`importlib.metadata.distributions` monkeypatch target) — Resolved:** Task 3 Step 1 Test 1 (`plan line 272`) now patches `importlib.metadata.distributions` to `lambda: (dist,)`, matching `for dist in importlib.metadata.distributions():` in `.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py:363`.
- **Round 1 Minor 2 (`os.scandir` context manager, all-entry `excluded(rel_parts)` filtering, and `sandbox_of` root-equality case) — Resolved:** Task 3 Step 3 (`plan lines 296, 298`) uses `with os.scandir(current_dir) as scan: entries = sorted(scan, key=lambda e: e.name)`, applies `excluded(rel_parts)` to every entry (pinned by top-level `site / "top.pyc"` in Test 2 on `plan lines 277-278`) while pruning directory recursion only for `_stdlib_excluded` and `_path_tree_excluded`, and computes `relative = "." if located_str == real_str else located_str[len(prefix_str):].replace(os.sep, "/")`.
- **Round 1 Minor 3 (Closeout bidirectional task notes, `--stamp` output inspection, and `git merge-base --is-ancestor` verification) — Resolved:** Task 5 Steps 3–4 (`plan lines 405, 410`) now include bidirectional `tasks note` linking between `beliefs-0f5112` and `<cleanup-id>`, explicit `--stamp` inspection recording `observer session attribution unknown` when no `harness_session` stamp is emitted, and `git merge-base --is-ancestor <basis-commit> main` checks both before worktree removal and after `git branch -d perf/0f5112-test-latency`.

## Strengths

- **Exact alignment with approved spec, step records, and hygiene gates:** All five `### Task 1:`..`### Task 5:` headings (`plan lines 44, 131, 255, 316, 379`) match the `step:` frontmatter fields of `beliefs-ef55af`, `beliefs-da58e8`, `beliefs-202076`, `beliefs-501cb2`, and `beliefs-516396` character for character, and the plan contains zero machine-layout strings (`titan`, `keith`, `/mnt/ssd`, `Dropbox`, `/home/`).
- **Verified architectural and N2 invariants:**
  - `parsed(path)` content-SHA-256 memoization + `copy.deepcopy` in `.worktrees/0f5112-test-latency/python/tests/test_capability_boundary.py` preserves all five cross-imported helpers (`imported_modules`, `modules`, `names_of`, `parsed`, `relative`), fresh disk-read semantics under N2 `PYTHONPATH` sabotage and `tmp_path` reuse, and caller AST mutation isolation.
  - All 8 `readonly_source` items in `.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py` (`test_the_preview_needs_no_authority`, `test_a_coordination_scoped_writer_refuses_the_permit_before_the_world_is_opened`, `test_a_session_without_a_resolver_refuses_coordination_unavailable`, and the 5 `test_y17_w_scoped_ownership` scenarios) are verified byte-invariant on `s.base`: `open_attended_session` inspects `s.written` only via `inspect_detached` and writes ledgers exclusively under `scoped_source`'s isolated `tmp_path / "ops"`, while `test_y17_w_scoped_ownership[forward]` closes its read-only `open_world` inspection inside `_publishing()` before invoking the monkeypatched `act.publish` spy.
  - Task 3's five zero-cache per-walk optimizations in `.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py` introduce zero `BYTE_MUTATION_PRIMITIVES` identifiers (`RAW_WRITE_ALLOWLIST["adapter.py"] == {"copy2"}` preserved), preserve all five `Sabotage.before` anchors (`K7a`, `K7b`, `K7c`, `R13`, `R17`), touch no `_Closure` private attributes referenced outside `adapter.py`, and cleanly separate `_hashed_files` from `_loadable_elf_headers` so `<20`-byte files, foreign-endian ELFs, and unhashed synthetic test rows in `elves()` behave identically without extra file opens.
- **Policy-off and statistical rigor:** Routine task commits use focused `just test-one` + `just check-hygiene` (plus `TT_FORCE=1 just check-code` on code tasks), while Task 4 runs the spec-mandated clean-tree 16-worker alternating `B1, C1, B2, C2, B3, C3` benchmark (`TT_FORCE=1 just test-fast`), separate `--durations=0` worker-time attribution, and one complete certified `just test-full` (`<= 300 s`, `6,410` non-N2 Python passed / `1` skipped, `46` N2 passed, `155` TypeScript passed).

## Findings

### Critical

None.

### Important

None.

### Minor

1. **Session-door capability-skip and mutating-item counts in Task 2 prose are off by one in each module (`60` skipped and `14` mutating items, not `58` skipped and `13` mutating items)**
   - **Plan lines:** `37`, `234`, `244`
   - **Target files/lines:** `.worktrees/0f5112-test-latency/python/tests/test_session_sharing_doors.py:134-602`, `.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py:98-505` (corroborated by `tasks/files/beliefs-067a8d/hosted-2-assessment.txt` reporting `76 / 2 = 38` and `44 / 2 = 22` capability skips per Python matrix job)
   - **What is wrong:**
     - In `test_session_sharing_doors.py`, the 25 capability-dependent functions expand to **38** pytest items (`20` unparametrized + `3 + 5 + 2 + 5 + 3 = 18` parametrized = `38`, not `37`), alongside `2` existing + `1` new = `3` portable items.
     - In `test_session_publish_door.py`, the 15 capability-dependent functions expand to **22** pytest items: `8` non-mutating `readonly_source` items across 4 functions (`1 + 1 + 1 + 5`) plus **14** mutating `certified_work` items across 11 functions (`8` unparametrized + `2 + 2 + 2 = 6` parametrized = `14`, not `13`), totaling `22` capability-dependent items (not `21`), alongside `2` existing + `1` new = `3` portable items.
     - As a result, Task 2 Step 5 (`plan line 244`, and Review Focus 2 on `plan line 37`) will report **`6 passed, 60 skipped`** (`3 portable passed + 38 skipped` in `test_session_sharing_doors.py`; `3 portable passed + 22 skipped` in `test_session_publish_door.py`), rather than `6 passed, 58 skipped`. (The full non-N2 suite totals in Task 4 — `6,403` baseline + `7` new tests = `6,410 passed, 1 skipped` — are unaffected and exact.)
   - **Why it matters:** No code, test logic, or command exit status is affected, so this does not block acceptance. However, during Task 2 Step 5 execution an implementer checking pytest's summary banner (`6 passed, 60 skipped`) against `Expected: 6 passed, 58 skipped` could misread the unchanged baseline skip partition (`38 + 22 = 60`) as a regression, or copy `58` instead of the observed `60` into `docs/plans/2026-11-01-test-fast-latency-results.md`.
   - **Concrete fix:** During Task 2 Step 5 execution and when writing `docs/plans/2026-11-01-test-fast-latency-results.md` in Task 4 Step 5, expect and record `6 passed, 60 skipped` (`3 portable passed + 38 skipped` in `test_session_sharing_doors.py`; `3 portable passed + 22 skipped` in `test_session_publish_door.py`, comprising `8` `readonly_source` items and `14` mutating `certified_work` items), noting the count correction in the execution ledger / task notes if the frozen plan text is left unedited.

## Declined to judge

None.
