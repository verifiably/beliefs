# Spec Review — Round 2

- **Task:** beliefs-0f5112
- **Reviewer conversation:** `9506a55d-1b3b-470f-aa61-1c4578937121`
- **Reviewer:** `antigravity`
- **Frozen revision:** `fb26bebe081caf5b3ec7a6b3081f53ea232a72ff:docs/superpowers/specs/2026-11-01-test-fast-latency-design.md`
- **Completed at:** `2026-11-01T12:59:39Z`

---

Reviewer: antigravity
Frozen revision: fb26bebe081caf5b3ec7a6b3081f53ea232a72ff:docs/superpowers/specs/2026-11-01-test-fast-latency-design.md
Verdict: accept

### Round 2 Verification Summary

All three Important findings and all four Minor findings from the Round 1 report ([spec-round-1-report.md](file:///mnt/ssd3/work/beliefs/beliefs-0f5112/spec-round-1-report.md)) are completely and accurately resolved in `fb26bebe081caf5b3ec7a6b3081f53ea232a72ff:docs/superpowers/specs/2026-11-01-test-fast-latency-design.md`, and no new epistemic, capability-boundary, fixture-isolation, uncertified-host skip, `_Closure` equivalence, policy-off, or hygiene defect was introduced.

1. **Round 1 Important 1 (`add_records` parent-`realpath` resolution, `pathlib` `_IGNORED_ERRNOS`, special-file modes, and `PurePosixPath` formatting) — Resolved (`docs/superpowers/specs/2026-11-01-test-fast-latency-design.md:410-428, 444-472, 543-546`):**
   - Part 2.4 (`lines 457-462`) resolves `os.path.normpath(os.path.join(dist_base, raw_entry))` through [`_Closure._located`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L260-L265)'s per-walk parent-`realpath` cache before `os.lstat` and [`_Closure.sandbox_of`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L281-L287). Verified across all 65 distributions and 7,526 `RECORD` rows in `.worktrees/0f5112-test-latency/python/.venv` (including `../../../bin/...` entries) with 0 resolution or filter mismatches against [`_Closure.add_records`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L362-L380).
   - Parts 2.2 and 2.4 (`lines 417-428, 463-472`) share one `os.lstat` helper suppressing `pathlib`'s exact `_IGNORED_ERRNOS` (`{ENOENT, ENOTDIR, EBADF, ELOOP}`) as `None`, propagating permission and I/O `OSError`s for [`capture_closure`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L675-L681) to wrap as `ClosureUnsupported`, refusing non-regular/non-symlink modes (`S_ISDIR`, `S_ISFIFO`, `S_ISSOCK`, device nodes) before `sandbox_of()`, formatting `PurePosixPath(raw_entry)` on the cold `MalformedClosure` path, and delegating `S_ISLNK` entries to [`_Closure.add`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L289-L319).

2. **Round 1 Important 2 (live N2 sabotage anchors, cross-module imports, and `CITED_NOT_RUN` vs `tests/test_n2.py`) — Resolved (`docs/superpowers/specs/2026-11-01-test-fast-latency-design.md:207-238, 346-356, 392-395, 423-428, 470-472, 505-510, 519-550, 579-581`):**
   - `Constraints` (`lines 220-238`), Part 2 (`lines 392-395, 423-428`), and `What is left to the builder` (`lines 506-510`) pin all five exact `Sabotage.before` substrings and indentations in [.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py): `K7a` (20-space indent in [`_Closure.add_native`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L451)), `K7b` (12-space indent in [`_Closure.add`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L305-L306) with `target_root`, `located`, `target`, and `root` bound in scope for `Sabotage.after`), `K7c` (12-space indent in [`_Closure.add_pth`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L390)) from [.worktrees/0f5112-test-latency/python/tests/acceptance/n2_arms_cut13.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/acceptance/n2_arms_cut13.py#L306-L330), plus `R13` (12-space indent in [`capture_bundle`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L134)) and `R17` (8-space indent in [`build_argv`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L768)) from [.worktrees/0f5112-test-latency/python/tests/n2_arms_cut3.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/n2_arms_cut3.py#L441-L549).
   - Preserves [`_written`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py#L258-L259) and [`publishing_session`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py#L213-L222) imported by [.worktrees/0f5112-test-latency/python/tests/acceptance/test_owned_replica_publication_acceptance.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/acceptance/test_owned_replica_publication_acceptance.py#L34), preserves top-level [`test_y17_w_scoped_ownership`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py#L505-L540) guarded by [.worktrees/0f5112-test-latency/python/tests/n2_arms_cut47.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/n2_arms_cut47.py#L24) and [.worktrees/0f5112-test-latency/python/tests/acceptance/test_n2_cut47.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/acceptance/test_n2_cut47.py#L74-L76), and accurately records that cut-4/cut-8 N2 modules are retired in `CITED_NOT_RUN` while `just test-full` executes [.worktrees/0f5112-test-latency/python/tests/test_n2.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_n2.py)'s portable arms (`lines 211-213, 579-581`).

3. **Round 1 Important 3a (`scoped_source(readonly_source, tmp_path)` in `test_session_publish_door.py`) — Resolved (`docs/superpowers/specs/2026-11-01-test-fast-latency-design.md:346-361, 528-531`):**
   - Rebinding `ops = tmp_path / "ops"`, `dest = tmp_path / "dest"`, and `destination = Destination.local(str(dest))` on a shallow `SimpleNamespace` view `s` keeps [`publishing_session`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py#L218-L220), [`_door_publish`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py#L225-L233), [`_door_resume`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_session_publish_door.py#L236-L239), and all `assert not (s.ops / "publish").exists()` checks (`lines 150, 408, 419, 538`) targeting each test's own `tmp_path / "ops"`.
   - Verified against [`open_attended_session`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/session/__init__.py#L86-L201), [`ScopedWriter._publishing`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/session/writer.py#L715-L735), and [`open_world`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/root.py#L2012-L2076): none of the 8 items writes to `readonly_source.base`, and [`_forget_temporary_roots`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/conftest.py#L102-L120) evicts only `tmp_path` at function teardown without disturbing `readonly_source` mid-module.

4. **Round 1 Important 3b (shared regular-file hashing across `add`, `add_records`, and `add_native`'s `SANDBOX_LIB` branch, plus 18-byte `<H` check before 20-byte `EI_DATA` unpack) — Resolved (`docs/superpowers/specs/2026-11-01-test-fast-latency-design.md:473-496, 540-543`):**
   - Routing `add()`, `add_records()`, and `add_native()`'s `SANDBOX_LIB` branch (`guarded by if resolved not in self.rows:`) through one per-walk regular-file helper ensures `/science/env/lib/*` entries populate `self._hashed_files` and `self._loadable_elf_headers` once and undergo zero extra `open`/`read`/`close` syscalls across `elves()` fixpoint passes while keeping `self.rows`, `self.plan` (used by [`_carries_stdlib_module`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L434) and [`materialize_snapshot`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/confinement.py#L208)), `self.loader_map`, and `self.loader_elves` identical.
   - Checking [`_is_loadable_elf`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L484-L489)'s 18-byte `<H` predicate before storing `data[:20]` and unpacking [`_elf_architecture`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L492-L502)'s 20-byte `EI_DATA`-endian `e_machine` in [`_Closure.elves`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L462-L481) preserves exact short-file and foreign-endian behavior.

5. **Round 1 Minor 1–4 — Resolved:**
   - **Minor 1 (`certified_work_dir()` `try: ... finally:`):** Specified at `lines 296-303` and tested at `lines 531-532` against [.worktrees/0f5112-test-latency/python/tests/conftest.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/conftest.py#L152-L174).
   - **Minor 2 (`add_tree()` symlinked-directory handling):** `entry.is_symlink()` and `entry.is_file(follow_symlinks=False)` precede `entry.is_dir(follow_symlinks=False)` (`lines 435-438`, tested at `lines 546-548`), matching `sorted(root.rglob("*"))` (`recurse_symlinks=False`) in [`_Closure.add_tree`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/src/beliefs/adapter.py#L354-L360).
   - **Minor 3 (POSIX leading `"//"` collapse and `os.path.join(real_parent, tail)`):** Specified at `lines 402-405` and `414-416`.
   - **Minor 4 (`dirty: false` clean committed working tree for pilot and alternating `B_i`/`C_i` pairs):** Specified at `lines 551-559`.

6. **Cross-cutting invariants and hygiene — Verified clean:**
   - No new identifier in `adapter.py` collides with [`BYTE_MUTATION_PRIMITIVES`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_capability_boundary.py#L437-L453) or [`RAW_WRITE_ALLOWLIST`](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/test_capability_boundary.py#L464-L502); `root.py` remains the sole `atoms` importer; none of the five target files carries a freeze pin in [.worktrees/0f5112-test-latency/python/tests/frozen_guards.py](file:///mnt/ssd/Dropbox/beliefs/.worktrees/0f5112-test-latency/python/tests/frozen_guards.py); and commit `fb26bebe081caf5b3ec7a6b3081f53ea232a72ff` uses conventional commits with no emoji, no AI attribution, and no machine-specific paths.

---

### Critical

none

---

### Important

none

---

### Minor

none
