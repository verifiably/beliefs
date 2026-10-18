# Pin Comparison Latency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Steps use checkbox (`- [ ]`) syntax for tracking. The user approved this plan and inline execution.

**Goal:** Retain a bounded comparator cache only after three alternating baseline/candidate pairs prove an end-to-end gain and a candidate median of at most 90 seconds, then verify and close `beliefs-ce9d05`.

**Architecture:** Decorate the existing pure byte comparator with `functools.lru_cache(maxsize=128)`. Keep file reads and git resolution in their existing callers. Test reuse and freshness, compare both versions in the same worktree, and integrate only after correctness, timing, and branch review pass.

**Tech Stack:** Python's standard library, the locked pytest/pytest-xdist tools, just, `host-budget`, `tools/tt`, `tt-latency`, and the existing TypeScript suite.

**Spec:** [Approved design](../specs/2026-10-17-pin-comparison-latency-design.md)

## Global Constraints

- Reuse the locked, hydrated `.worktrees/ce9d05-test-latency` on `perf/ce9d05-test-latency`. Re-enter the worktree skill at execution setup; run the baseline before the first code change. No dependency change or second installer is needed.
- Keep `equivalent(original: bytes, current: bytes, *, path: str) -> bool` and its comparison body intact. Key the 128-entry cache on both complete byte strings and the complete path. Every xdist worker has its own cache; no persisted verdict or shared observation cache.
- Preserve every existing test, assertion, skip rule, pin, frozen cut body, scheduler, worker policy, and product behavior. This is test machinery, not a conformance cut; no new guarantee or recent-cut acceptance row is due.
- Use `just test-one` for every focused check and `just test-fast` before the implementation commit. The complete certified `just test` is required once because conformance machinery shares this comparator; retain its verdict within 300 seconds.
- Six comparable warm unprofiled runs, in order B1, C1, B2, C2, B3, C3, each at 16 workers. Each candidate must beat its paired baseline, its three-run median must be at most 90 seconds, and the median paired reduction must exceed the larger baseline/candidate range. Invalidate and repeat a whole pair if its host conditions materially change.
- Capture host load and background activity per run; do not overlap measurements with another long test run. Keep the existing host budget: a smaller grant invalidates comparability, not permission to force 16 workers.
- First read a focused pilot's verdict before the longer sweep. Plan about 20 minutes for the baseline, focused checks, six-run comparison, instrumentation, full suite, and pre-commit checks, then about 5 minutes for post-integration verification. If load refuses the work, record the refusal and park with the remaining phases and their expected minutes.
- No shared launcher or host pointer is repointed. Restore candidate files before a park, a commit, or integration. Runs remain harness-tracked; retain logs in the ignored evidence directory and run `host-load --section session` before yielding.
- Keep `beliefs-0180e2` open: only its memoization item belongs here. Do not implement its directive, edge-case, or documentation follow-ups.
- Preserve frozen historical evidence; update current-facing design status and add a dated results record when the outcome is established. Neither a faster focused check nor one sub-90-second run establishes incident acceptance.

## Review Focus

- A successful comparison followed by changed current bytes or changed original bytes must refuse; Task 1 adds a byte-key regression and runs existing mutable-working-file pin checks.
- The same unequal bytes compared as Python and as a non-Python path must produce different verdicts; Task 1 adds the path-key regression.
- More than 128 distinct comparisons must evict an old entry; Task 1 tests the bound and recomputation after eviction.
- Instrumenting `_tree` must not leave a poisoned cache for other tests; Task 1's reuse spy delegates to the real parser, and the bound test clears its entries in `finally`.
- Host drift between batches must not look like a cache gain; Task 1 records the three paired reductions and applies the approved paired and noise thresholds. Task 2 separately checks the three fresh main-checkout verification runs.

## Files and command context

Modify only:

- `.worktrees/ce9d05-test-latency/python/tests/pin_equivalence.py` — cache the existing pure function.
- `.worktrees/ce9d05-test-latency/python/tests/test_pin_equivalence.py` — four small regression tests.
- `.worktrees/ce9d05-test-latency/docs/superpowers/specs/2026-10-09-freeze-pins-modulo-formatting-design.md` — add a dated current-facing cache note, preserving the comparison rules.
- `.worktrees/ce9d05-test-latency/docs/superpowers/specs/2026-10-17-pin-comparison-latency-design.md` — update final status once established.

Create `.worktrees/ce9d05-test-latency/docs/plans/2026-10-17-pin-comparison-latency-results.md` for the measured outcome. Verify the two callers in `.worktrees/ce9d05-test-latency/python/tests/frozen_guards.py`; they need no changes.

All shell examples start in the main checkout. Set `task_tree=.worktrees/ce9d05-test-latency` and `evidence_dir="$task_tree/.work/ce9d05-test-latency"`; create that ignored directory if absent. `just -f "$task_tree/justfile"` runs in the worktree; its pytest selectors remain relative to the Python package as the project requires. Use `tasks -C "$task_tree"` for task writes until integration.

---

### Task 1: Implement and prove the comparator cache

**Task record:** `beliefs-cf48c5` (direct, mid complexity).

**Files:** The two Python files and three documentation files listed above; snapshots and logs under `$evidence_dir` are ignored evidence, not new shipped tooling.

**Interfaces:**
- Consumes: `equivalent(original: bytes, current: bytes, *, path: str) -> bool`; `frozen_guards.commit_pin_holds(repo_root: Path, target: str, commit: str) -> bool`; `content_pin_holds(repo_root: Path, target: str, digest: str) -> bool`.
- Produces: the same verdicts, with at most 128 cached byte/path comparisons; a results table containing B/C wall times, paired reductions, inventories, and the keep/revert decision. The standard decorator supplies `cache_info()` and `cache_clear()` for the bound test.

- [x] **Step 1: Start the child task, refresh the baseline, and preserve inputs.** Start the Task 1 record and run `trial-arm` as instructed. Verify clean tracked files, hooks, worktree lock, prior `just setup`, `host-budget show`, and `host-load --section load`. Record the revision and copy the unchanged comparator and test file into `$evidence_dir/baseline-pin_equivalence.py` and `$evidence_dir/baseline-test_pin_equivalence.py`. Run `just -f "$task_tree/justfile" test-fast` and `just -f "$task_tree/justfile" test-one tests/test_frozen_guards.py::test_every_pin_in_a_live_guard_holds --durations=0`, saving separate logs. Read both successful verdicts, `tt` times, selected counts, and the actual worker grant before editing. The prior diagnostic was 6,119 passed/one skipped; establish the current inventory rather than assuming it. This refresh is outside the six-run comparison.

- [x] **Step 2: Add the reuse test and prove RED.** Add the test below to the existing comparator test module, importing `patch` from `unittest.mock`. The unique path makes its first comparison cold; the spy calls the real `_tree`, so its cached result remains valid for later tests.

```python
def test_identical_comparisons_parse_only_once():
    with patch.object(pin_equivalence, "_tree", wraps=pin_equivalence._tree) as tree:
        assert pin_equivalence.equivalent(ORIGINAL, FORMATTED, path="reuse.py")
        assert tree.call_count == 2
        assert pin_equivalence.equivalent(ORIGINAL, FORMATTED, path="reuse.py")
        assert tree.call_count == 2
```

Run `just -f "$task_tree/justfile" test-one tests/test_pin_equivalence.py::test_identical_comparisons_parse_only_once`. Expected failure: the final count is four instead of two, after both semantic comparisons succeed. Diagnose a different failure before continuing.

- [x] **Step 3: Add the cache and finish the small regression set.** Import `lru_cache` from `functools` and add `@lru_cache(maxsize=128)` directly above the existing `equivalent` definition. Add three tests with the following exact behavior; no new fixture, wrapper, or dependency is needed:

```python
def test_changing_either_byte_string_recomputes_the_verdict():
    compare = pin_equivalence.equivalent
    assert compare(ORIGINAL, FORMATTED, path="bytes.py")
    assert not compare(ORIGINAL, FORMATTED.replace(b"a + b", b"a - b"), path="bytes.py")
    assert not compare(ORIGINAL.replace(b"a+b", b"a-b"), FORMATTED, path="bytes.py")
    assert compare(ORIGINAL, FORMATTED, path="bytes.py")


def test_the_path_is_part_of_the_comparison_key():
    assert pin_equivalence.equivalent(ORIGINAL, FORMATTED, path="path.py")
    assert not pin_equivalence.equivalent(ORIGINAL, FORMATTED, path="path.md")


def test_the_comparison_cache_is_bounded_and_eviction_recomputes():
    compare = pin_equivalence.equivalent
    compare.cache_clear()
    try:
        for index in range(129):
            assert compare(b"x=1\n", b"x = 1\n", path=f"bounded-{index}.py")
        info = compare.cache_info()
        assert (info.currsize, info.maxsize) == (128, 128)
        assert compare(b"x=1\n", b"x = 1\n", path="bounded-0.py")
        assert compare.cache_info().misses == info.misses + 1
    finally:
        compare.cache_clear()
```

- [x] **Step 4: Prove GREEN and read the focused pilot.** Run `just -f "$task_tree/justfile" test-one tests/test_pin_equivalence.py tests/test_frozen_guards.py`. All existing and new tests must pass, including commit/content mutations in one process, deleted/absent files, unresolved commits, cross-repository digest resolution, and live scalar declarations. Then repeat Step 1's exact focused live-pin command without profiling and compare its time. Save candidate snapshots of both Python files under `$evidence_dir/candidate-pin_equivalence.py` and `$evidence_dir/candidate-test_pin_equivalence.py`. If parsing reuse or the focused timing does not substantially improve, stop, restore both baseline files, and record the failed trial; do not launch the sweep.

- [x] **Step 5: Run the alternating six-run comparison.** Before each run, copy the matching baseline or candidate snapshots back to the two original Python paths and confirm both with `cmp`. Use the same worktree, installed environment, command, and warm-up policy. Warm each version once with the focused live-pin command; then perform B1, C1, B2, C2, B3, C3 with `just -f "$task_tree/justfile" test-fast`, logging each separately. Record revision, file hashes, host load/background activity before and after each run, actual worker grant, `tt` wall time, and selected counts. Candidate inventory should add exactly the four new regression tests to the refreshed baseline; skip count and TypeScript selection stay equal. A failed run, grant other than 16, or material host change invalidates its pair; diagnose before repeating the whole pair. Never drop a valid slow run. Restore candidate files when finished or interrupted; if putting work down, confirm that restoration in the task note.

- [x] **Step 6: Apply the keep/revert rule and attribute worker cost.** Let `D_i = B_i - C_i`. Require all three `D_i > 0`, `median(C) <= 90`, and `median(D) > max(max(B)-min(B), max(C)-min(C))`. Record all inputs and the verdict; the limit is the recorded `tt` time, not pytest time. Also run one comparable instrumented `test-fast` on each version with `--durations=0` appended to the existing `PYTEST_ADDOPTS`, restoring snapshots as in Step 5; these are attribution runs outside the six-run decision. Sum reported setup/call/teardown durations and inspect the live-pin check, retaining the counts and verdicts. Restore candidate. If correctness or the paired timing rule fails, restore baseline instead, record the cache as reverted and the measured residual, and keep the incident open. Do not proceed to integration; the next remedy needs its own decision and evidence.

- [x] **Step 7: Verify the complete gate and document the retained result.** Only for a passing remedy, run `just -f "$task_tree/justfile" test` once on the certified tuple: non-N2 Python, standalone N2, and full TypeScript must all pass, with recorded time at most 300 seconds. A failure or limit miss stops retention and integration; diagnose it and revert the remedy if it caused the regression. Add the dated cache note to the older formatting design and write the results record: RED/GREEN evidence, baseline/candidate hashes and counts, focused pilot, paired table/noise calculation, worker-seconds, full-suite result, and pending main verification. Update the incident design to implemented/pending verification. Note only the delivered memoization portion on `beliefs-0180e2`, leaving its remaining work open. Do not change historical measurements or doctrine rules.

- [ ] **Step 8: Check, commit, and obtain whole-branch review.** Run `just -f "$task_tree/justfile" check` and `just -f "$task_tree/justfile" test-fast` after the documentation updates, since docs are test inputs here. Run `tasks check` and `git diff --check`, inspect the intended implementation/evidence diff and plan progress, then stage only those files and commit conventionally as `perf(tests): reuse identical frozen-pin comparisons`, including the measured B/C medians in the body. Obtain the fresh final whole-branch review required by executing-plans, preserve its full returned text in the existing review workspace, and record its task note before acting. Correct Important/Critical findings and re-review under the repository's five-round rule; record deferred minors in the ledger. Close Task 1 after its commit and review pass. Preserve the branch and evidence if timing or review remains unresolved.

### Task 2: Integrate the accepted remedy and verify the incident

**Task record:** `beliefs-d31eb1` (direct, low complexity; depends on `beliefs-cf48c5`).

**Files:** The existing incident, child task records, and `.worktrees/ce9d05-test-latency/docs/plans/2026-10-17-pin-comparison-latency-results.md`; after integration use the corresponding main-checkout paths.

**Interfaces:**
- Consumes: Task 1's retained, reviewed commit and paired/full-suite evidence; the parent incident's complete `breach:` notes.
- Produces: local integration, three fresh main-checkout fast verdicts per named host, successful `tt-latency verify`, and task closure containing its full output. A missing host or failed verification leaves the halt open.

- [ ] **Step 1: Start the verification child and integrate locally.** Run its task start and trial instructions. Confirm Task 1 is closed and the branch review's rulings are settled. Check both checkouts are clean and main contains no unrelated unmerged work; merge main into the branch first if needed and refresh affected checks/review when that changes the reviewed remedy. For this personal repository, locally merge `perf/ce9d05-test-latency` into main as the bounded default; do not push or publish a PR. Run `tasks start` for the parent and verification child from main before any task writes there. Record main's integrated revision and its UTC commit timestamp as `remedy_after`. The registered checkout must hold the authoritative incident before the verifier writes its note.

- [ ] **Step 2: Collect new incident evidence in main.** Inspect all parent `breach:` notes again. On each named host, run three new, successful, uncontended, unwidened `just test-fast` verdicts in its registered main checkout, sequentially at comparable host conditions. Every run must start strictly after `remedy_after`; wait past its timestamp before the first if necessary. Use the current installed setup, capture host budget/load and counts, and retain the three `tt` records and logs. No worktree pilot counts toward this verification. If another named host is unavailable, leave the incident open with that precise remaining obligation.

- [ ] **Step 3: Verify, finish the results record, and close in order.** Run `tt-latency verify beliefs-ce9d05 --after "$remedy_after"` in main on every named host and read the full output and exit status. Each host must exit zero. Update the results record and incident design status with the integrated revision, paired result, full-suite result, and verifier output; run `tasks check` and the documentation commit's required hook. Close the verification child, then `tasks done beliefs-ce9d05` with the full successful verification output. Record a failure or refusal instead of closing if any obligation remains. The closeout is an explicit exception to pre-merge task closure: this incident requires fresh post-integration evidence.

- [ ] **Step 4: Preserve review and timing evidence and report.** Run `tt-report --project beliefs` and `host-load --section session`. State the measured paired gain, the post-integration verification result, remaining review rulings/minors, and any processes left running. Retain the locked worktree and its ignored evidence for this closeout; removal is a separate cleanup following ignored-file, review-ledger, host-pointer, and timing-harvest checks.

## Plan self-review

Spec coverage: Task 1 covers the four cache regressions, fresh pin reads, unchanged semantics, focused pilot, six alternating pairs, noise threshold, worker attribution, certified full suite, and keep/revert record. Task 2 covers review-before-integration, fresh main evidence, verifier output on every named host, closure, and evidence retention. Signatures match the existing code; no caller or export changes are required. Review Focus cases have either a new regression or an explicit existing check above. The user approved the plan for inline execution.
