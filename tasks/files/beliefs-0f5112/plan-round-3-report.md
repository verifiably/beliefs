# Plan Review Round 3 — beliefs-0f5112

Reviewer: claude-code/claude-opus-5-5
Frozen Revision Verified: 7e4548c6edb6660a2219a6ca5f8244e2cdfe21ba:docs/superpowers/plans/2026-11-01-test-fast-latency.md
Verified Plan SHA-256: 4c629b793396587f923383dd1e64f078e66e760e9c21f55a3e34287881cfb10f
Verdict: revise
Summary Counts: Critical: 0, Important: 3, Minor: 8

## Plan review: round 3, verdict **revise**

I reviewed revision `7e4548c6edb6660a2219a6ca5f8244e2cdfe21ba:docs/superpowers/plans/2026-11-01-test-fast-latency.md`. Its sha256 matches `4c629b79…cfb10f`. The plan needs revising: three Important findings and eight Minor ones. I checked each claim against the code at 240a989. Under `python/` and `ts/` it is identical to 7e4548c, so the plan's baseline is exact. I changed nothing; the probe directories I created in the scratchpad have been deleted.

For the task note: `review: plan round 3 — verdict: revise; findings: Important 3, Minor 8; reviewer: claude-code/claude-opus-5-5`

### Confirmed sound
- **Sabotage anchors:** the five listed anchors (cut 3 `R13`/`R17`, cut 13 `K7a`–`c`) are the only N2 sabotages that target `adapter.py` across every arms file. No frozen-pin table covers `adapter.py`, `conftest.py` or the three test modules.
- **AST cache:** keying on bytes and filename is correct. The package has 116 modules, under `maxsize=256`. N2 audits run their checks in a subprocess (`test_n2.py:227`), so no stale cache can leak between arms. The two hoisted loops keep their semantics.
- **Session-door fixtures:**
  - The read-only items open sessions that write only under `operations_root`, which `scoped_source` moves into `tmp_path`.
  - Nothing else imports `shared` or `adopted`.
  - The `conftest`/acceptance separation in Task 2 Step 4 is correct.
  - The module-scoped fixture puts the whole sharing-doors module on one xdist worker; the spec already accounts for this (about 17.6 s per group).

### Important

**1. The `../` case in the RECORD test can never pass** (plan l.281–282)

`dist_base` is `alias_site`, a symlink at `tmp_path/alias_site`, and the RECORD lists `../../bin/tool`. Both the planned code and the current code run `os.path.normpath` before resolving the parent. That lexical step turns `tmp_path/alias_site/../../bin/tool` into `tmp_path.parent/bin/tool`, not `real_venv/bin/tool` (checked: `normpath('/a/alias/../../bin/tool') == '/bin/tool'`).

So the test fails after implementation. The obvious fix would be to resolve symlinks before `normpath`, which silently changes semantics the spec says stay "identical to `self.add(located)`".

Fix: test the `../` traversal from a real (non-symlinked) distribution base, and keep the symlinked parent only for `pkg/mod.py`. Or keep the crossing case and expect `MalformedClosure`, which pins the current behaviour.

**2. The `prunes_known_exclusions` RED is vacuous on Python 3.13** (l.290)

On 3.13, `pathlib.rglob` never calls `os.scandir` through the module attribute; a spy recorded 0 calls. The current code therefore passes the "site-packages never scanned" assertion, and the expected RED never happens.

Fix: add a positive control, such as asserting the spy recorded `site` itself. Then the RED fails for the right reason, and the assertion still means something after the change.

**3. Nothing compares the walker's output before and after** (Task 3 Step 4, l.305)

The refactor claims zero behaviour change, but no step compares `capture_closure()` output between 240a989 and the candidate. The existing checks cannot catch a dropped row:
- Probe parity cannot, because the sandbox layout is built from the walker's own rows.
- `just test-full` never runs `tests/acceptance`, because `addopts` contains `--ignore=tests/acceptance`.

Fix: in the same venv, dump `manifest.artifacts`, `rendered`, `loader_map`, `loader_elves` and the plan paths at both revisions. Require exact equality and record the digest in the results file. Each walk takes about 1.5 s.

### Minor

4. **Pruning drops files under `.pyc`-named directories.** `_stdlib_excluded` and `_path_tree_excluded` are not monotone: their `.pyc`-suffix arm excludes a directory named `x.pyc` but not its children (checked: `('x.pyc',)` → True, `('x.pyc','inner.py')` → False). Prune only on the names `site-packages`, `__pycache__` and `.git`.
5. **Unreadable directories become refusals.** Recursing with `os.scandir` raises `PermissionError` on an unreadable subdirectory; `rglob` skipped it silently (checked). The walk would then fail as `ClosureUnsupported`. Either keep the skip or record the stricter behaviour as deliberate.
6. **18–19-byte ELF prefixes change behaviour.** Today such a file raises `struct.error`, and `probe.py:84` says it uses "the same predicate". The planned code silently leaves it out of `elves()`. The `short19.bin` test bakes that change in, so decide it explicitly. Separately, Step 2's predicted RED is wrong: the current code fails with `struct.error` inside `add_native`, not with "reopened already-hashed file".
7. **Item counts are stale.** Counting by AST: sharing doors has 38 `certified_work` items across 25 functions; publish door has 22 across 15. So the expectation should be 6 passed, 60 skipped, with 14 mutating items (l.37, 234, 244). Round 2 deferred this to a task note, but since the plan needs a new revision anyway, fix it in the plan.
8. **The six-run benchmark needs one tracked shell.** The `trap` at l.336 only works if all six runs (about 10 min) happen in a single shell. Run them as one `run_in_background` script with a timeout of at least 15 min. Separate calls lose the trap and can leave the worktree detached.
9. **"Revert … and stop" has no next owner.** Replace it with a park that names the next step, and say whether the benchmark reruns after a revert.
10. **Python 3.11 is never checked.** The local venv is 3.13, and integration is a local merge with no push, so hosted CI (3.11 and 3.13) never sees the `adapter.py` change before `main` moves. Ask the user to approve a branch push before the merge, or disclose the gap in the closeout.
11. **Ordering and memory.**
    - Task 5 closes `beliefs-0f5112` in Step 3, before the Step 4 merge, so the done note cannot report integration state.
    - The AST cache keeps about 63 MiB of trees per worker for the whole run (measured over 116 modules); that is acceptable, but worth noting.
