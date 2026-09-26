# Test-suite latency implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the unchanged fast selection to a warm median of at most 90 seconds and the complete certified gate to at most 300 seconds.

**Architecture:** Use pytest-xdist `loadgroup` for the non-N2 fast selection, including the first phase of the full gate. Run N2 in a second serial pytest process so its session fixture is built once and its nested pool receives the full worker allowance. Memoize only the value identity of a validated environment manifest; keep both filesystem captures. Promote the two-phase command only after a certified pilot, then measure repeated end-to-end verdicts.

**Tech Stack:** Python 3.11+, pytest/pytest-xdist 3.8.0, `functools.lru_cache`, just, `host-budget`, `tools/tt`, GitHub Actions.

**Spec:** [Test-suite latency design](../specs/2026-09-26-test-suite-latency-design.md)

## Global Constraints

- Start from the merged local-main pin fix `2ec30ce`; `test_frozen_guards.py` passes 7/7 in this worktree. Do not make a second pin repair or change frozen conformance evidence.
- Preserve every selected test, assertion, capability-dependent failure, recipe identity byte, and the independent recipe and pre-launch closure captures required by `beliefs-5b28c5`.
- Use the certified kernel and volume tuple for the full gate. CI's `VERIFIABLY_UNCERTIFIED_HOST=1` skips only `CapabilityUnavailable` and is not evidence for those arms.
- `host-budget run` sets `OPS_WORKERS` and `PYTEST_XDIST_AUTO_NUM_WORKERS` locally. CI must set both to `4` explicitly. N2's nested pool stays within `OPS_WORKERS`.
- No new dependency or closure/digest cache. Keep the identity memo outside `EnvironmentManifest` fields, `vars()`, repr, equality and pickle; bound it to four entries.
- Before any long sweep, run a small selection through the same scheduler and N2 path to a verdict and read it. Record attempted trials, including failures, on `beliefs-9b248a`.
- The full-gate target is 300 seconds. Standalone N2 passed 46 tests in 193 seconds with a 16-worker pool; its measured cost is a likely residual if the target is missed. Keep the P0 open if either final target is missed.

## Review Focus

- N2 inherits xdist's one-worker pool and takes roughly 40 minutes: Task 3 runs it in a separate serial pytest phase and records its worker allowance and time.
- Splitting heavy files repeats module setup enough to erase the wall gain: Task 1 compares per-file wall time, worker-seconds and fixture setup under both schedulers.
- Equal manifests in different objects rehash while a changed row reuses the old digest: Task 2's spy test counts digest calls and compares identities.
- A cache field changes projected, compared or pickled manifests: Task 2 checks `fields`, `vars`, repr, equality and pickle after a warm identity call.
- CI accidentally omits a Python phase or oversubscribes the first phase: Task 3 checks the two `&&`-joined pytest commands and both CI env values, then runs a CI-shaped small pilot.

---

### Task 1: Balance the fast scheduler

**Files:**
- Modify: `justfile` (`py_fast_cmd` and scheduler comments)
- Evidence: `beliefs-9b248a` task notes, through `tasks note`

**Interfaces:**
- Consumes: existing `py_fast_cmd`, `host-budget run`, and pytest-xdist `loadgroup`.
- Produces: fast recipe using `-n auto --dist=loadgroup --ignore=tests/test_n2.py`, with no N2 marker.

- [x] **Step 1: Anchor the merged baseline.** Record the already-green 5,706-pass `loadfile` fast run from local main, the spec's per-file attribution, current commit, Python version, host load and worker count. The new per-file measurement follows the small scheduler pilot.
- [x] **Step 2: Pilot each scheduler on the four heavy files.** Under `host-budget run`, select one representative test from each file with `-n auto --dist=loadfile`, then the same four node IDs with `--dist=loadgroup`. Require both verdicts and selected IDs to agree before a full-loop sweep.
- [x] **Step 3: Change only `py_fast_cmd` to `loadgroup`.** Keep `--ignore=tests/test_n2.py` and TypeScript selection unchanged. Update the nearby justfile comment to explain that this scheduler is for tests outside N2.
- [x] **Step 4: Compare complete fast loops.** Run `just test-fast` after the change and a direct `loadfile` comparison on the same warm host budget with `-vv --durations=0`; collect selected/skipped counts, the four heavy files' durations, worker assignments, fixture setup and worker-seconds. Require unchanged collection and verdict; if `loadgroup` loses, revert the recipe change, record why, and keep the P0 open for a measured alternative.
- [x] **Step 5: Verify and commit.** Run `just check`, `tasks check` and `git diff --check`; close the Task 1 child with `tasks done` and commit the accepted scheduler and task record as `perf: balance test scheduler`. This task is complete only with a green fast loop.

### Task 2: Memoize the pure environment identity

**Files:**
- Modify: `python/src/beliefs/recipe.py` (`EnvironmentManifest.identity`)
- Modify: `python/tests/test_recipe.py` (one focused regression test)
- Evidence: `beliefs-9b248a` task notes, through `tasks note`

**Interfaces:**
- Consumes: `EnvironmentManifest.artifacts: tuple[tuple[str, str, str], ...]`, `_triples`, `v1.digest`, `ENVIRONMENT_DOMAIN`.
- Produces: unchanged `EnvironmentManifest.identity(self) -> str` backed by module-level `@lru_cache(maxsize=4) def _environment_identity(artifacts: tuple[tuple[str, str, str], ...]) -> str`, keyed only by the validated tuple.

- [ ] **Step 1: Write one failing test in `test_recipe.py`.** Construct two equal manifests and one with a changed digest row. Before spying, call `_environment_identity.cache_clear()` if the helper exists, so a prior test on the same worker cannot affect the count; this conditional permits a red run before the helper is added. Spy on `v1.digest`: the equal pair must invoke it once; the changed row must yield a different identity and a second digest call. After warming, assert `dataclasses.fields` names only `artifacts`, `vars(manifest)` still contains only `artifacts`, repr is unchanged, equality holds, and pickle round-trips.
- [ ] **Step 2: Run the focused test before implementation.** From `python/`, run `uv run --frozen pytest tests/test_recipe.py::<new-test-name>`; it must fail on the equal-pair digest count of two, not on setup or an unrelated assertion.
- [ ] **Step 3: Add the pure helper in `recipe.py`.** Import `functools.lru_cache`, decorate `_environment_identity` with `maxsize=4`, pass `self.artifacts`, and keep the existing `v1.digest(ENVIRONMENT_DOMAIN, {"artifacts": _triples(artifacts)})` calculation and public method return value. Do not store anything on the dataclass or cache capture results.
- [ ] **Step 4: Verify the behavior and gain.** Run the new test, `test_closure_capture.py`, `test_frozen_guards.py`, and `test_arm_staleness.py`, then time repeated calls on one manifest and a representative replay/boundary pipeline test. No frozen pin names `recipe.py` or `test_recipe.py`, and no N2 arm anchors on the body of `EnvironmentManifest.identity`; the two guard suites check this after the edit. Run `just test-fast` once and compare worker-seconds, closure-call counts and wall time with Task 1. Revert the memo if end-to-end gain is within measurement noise or any identity/refusal changes.
- [ ] **Step 5: Verify and commit.** Run `just check`, `tasks check` and `git diff --check`; close the Task 2 child with `tasks done` and commit the accepted memo, test and task record as `perf: memoize environment identity`, with measured evidence in the P0 task note.

### Task 3: Adopt the two-phase full gate

**Files:**
- Modify: `justfile` (`py_test_cmd`, current-facing comments)
- Modify: `.github/workflows/ci.yml` (Python worker count and comment)
- Modify: `AGENTS.md` (gate command and duration claims)
- Modify: `python/README.md` (current gate, fast loop and measurements)
- Evidence: `beliefs-9b248a` task notes, through `tasks note`

**Interfaces:**
- Consumes: Task 1's `loadgroup` fast recipe, Task 2's unchanged manifest identity, `py_test_cmd` shared by `just test`, pre-push and `ci-python`.
- Produces: `py_test_cmd := "(cd python && uv run --frozen pytest -n auto --dist=loadgroup --ignore=tests/test_n2.py && uv run --frozen pytest tests/test_n2.py)"`; CI Python env includes both `OPS_WORKERS: "4"` and `PYTEST_XDIST_AUTO_NUM_WORKERS: "4"`.

- [ ] **Step 1: Collect and pilot without changing the gate.** Compare the union of `--dist=loadgroup --ignore=tests/test_n2.py` and standalone `tests/test_n2.py` collection with the existing serial full collection, including skips and IDs. Run a small certified two-phase `&&` selection: one representative non-N2 boundary test under xdist, then one N2 harness test outside xdist that reaches a verdict without the full `findings` fixture. Check `OPS_WORKERS` is the full allowance in the second phase and read both verdicts before a full run. No N2 marker or four-worker grouped pilot is needed.
- [ ] **Step 2: Run one complete certified two-phase pilot.** From `python/`, run `host-budget run -- sh -c 'uv run --frozen pytest -n auto --dist=loadgroup --ignore=tests/test_n2.py && uv run --frozen pytest tests/test_n2.py'` to completion, then the TypeScript suite. Record each phase's selected/passed/skipped counts, N2 pool size and wall time, total wall time and worker-seconds; inspect every failure or skip. Compare with the seven-day serial distribution and the independent 193-second standalone N2 diagnostic. If 300 seconds is missed, attribute the residual and keep the P0 open rather than relaxing the target.
- [ ] **Step 3: Promote the shared command only if the pilot passes.** Change `py_test_cmd` once; `just test`, pre-push and `ci-python` inherit both `&&`-joined pytest phases. Set the CI xdist count to `4` beside `OPS_WORKERS: "4"`. Keep an explicit one-process `uv run --frozen pytest` documented for diagnosis.
- [ ] **Step 4: Correct current-facing documentation.** Update `AGENTS.md`, `python/README.md`, justfile and CI comments to name the two-phase full gate, N2's full pool, CI worker count, and measured timing. Preserve historical dated measurements and frozen cut bodies. State that CI's portable result does not certify host-dependent arms.
- [ ] **Step 5: Verify and commit.** Run `just check`, `tasks check` and `git diff --check`; check that `just --show ci-python`, `just --show hook-pre-push` and `just --show test` all use the same two-phase `py_test_cmd`. Close the Task 3 child with `tasks done` and commit the gate, documentation and task record as `perf: run full pytest gate in two phases`, with pilot evidence on the P0 task.

### Task 4: Prove the latency budget and close the P0

**Files:**
- Modify: current timing claims in `python/README.md` or `AGENTS.md` only if Task 3's pilot differs materially from final evidence
- Evidence: `beliefs-9b248a` task notes and completion, through `tasks` CLI

**Interfaces:**
- Consumes: `just test-fast`, `just test`, `just check`, `tt-report`, and Tasks 1–3's recorded baselines.
- Produces: repeatable fast and full verdicts with counts and timing evidence; a closed P0 only if both thresholds hold.

- [ ] **Step 1: Run the complete checks.** On the certified tuple and under comparable warm host load, run `just check`, three `just test-fast` runs, and two complete `just test` runs. If the full runs disagree materially, take a third. Read each `tools/tt` verdict and record Python/TypeScript counts, skips, range, per-file tail, N2 time and worker-seconds.
- [ ] **Step 2: Apply the acceptance arithmetic.** Require fast median ≤90 seconds and every accepted full run ≤300 seconds. Verify selected tests and certified capability checks stayed intact. If either target misses, keep the P0 open, name N2's measured share when relevant, profile the residual tail, and add only the next bounded measured change to this plan.
- [ ] **Step 3: Finish the record.** Update any current-facing timing claim that the final runs made stale. Run `tasks check` with zero errors and report all warnings. Close the Task 4 child and `beliefs-9b248a` with one-line outcomes in the same final commit as any remaining work; retain `ops-5beefd` as the separate cross-project policy task.
