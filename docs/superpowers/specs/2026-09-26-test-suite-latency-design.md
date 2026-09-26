# Test-suite latency — restore the gate and reduce repeated runtime work

- **Date:** 2026-09-26
- **Status:** draft for user review
- **Task:** `beliefs-9b248a` (P0)
- **Workspace:** `.worktrees/test-latency`
- **Related policy task:** `ops-5beefd` (cross-project detection and stop-work escalation)

## 1. Outcome and measured problem

The Python suite's real pipeline executions make normal development slow. The earlier
audit (`beliefs-f253a1`) added timing records and a parallel local loop, but the last
seven days of `tt-report --project beliefs` still show a **190.2-second median for
`just test-fast`** and a **1,243.3-second median for `just test`**. The fast loop is
useful, yet three minutes remains a long feedback cycle; the serial gate costs about
21 minutes. The 2026-09-12 audit found 97 pipeline call sites in 17 files. Its 60
slowest tests each took 5–24 seconds and consumed 669 of roughly 1,370 worker-seconds
in that run. There is no material sleep or network cost to remove.

The 2026-09-26 pilot gives a narrower diagnosis. One replay test took 15.25 seconds on
main and 14.26 seconds in the isolated worktree. It executes two runs, each with a
capture before recipe minting and another immediately before launch. A warm capture
of this environment's 8,465 artifacts took 2.001, 2.060 and 2.020 seconds. Three
calculations of each of three immutable manifests' identity had a 0.237-second
overall median. A `cProfile` diagnostic attributed more parent-process time to closure walks
and repeated identity projection than to the four Snakemake launches; its absolute
times are inflated by instrumentation and are **not** a speed baseline.

The baseline is also red. `just test-fast` in the hydrated worktree reported **5,704
passed, 1 skipped, 2 failed in 180.74 seconds**. Both failures are
`test_frozen_guards.py` pin checks, and the same two fail on main. Recent changes to
cut 5–8 acceptance runners falsified live and cited pins without completing the guard
maintenance. A performance result cannot be called green until those checks pass.

Success means the same guarantees with a materially shorter measured wait: a median
of **at most 90 seconds for `just test-fast`** and **at most 600 seconds for `just
test`**, on the certified host and volume tuple under the existing `host-budget run`
recipes. These are roughly twofold improvements over the recorded medians, not a
license to omit tests. If a safe optimization falls short, the P0 remains open and
the next design decision uses the measured residual cost; a recipe-only speedup does
not close it.

## 2. Decisions and boundaries

1. **Restore the existing gate first.** Repair the two frozen-guard failures as
   specified by the [frozen guard doctrine](2026-09-07-frozen-guard-doctrine-design.md):
   re-pin live machinery to the changed runner files; add the newly falsified pins to
   the cited-not-run registry; append dated citation amendments to affected cut
   records. Do not edit a cited-not-run guard or rewrite frozen evidence. The two
   failures are already reproduced on main; prove the repair in this worktree before
   taking a green performance baseline.

2. **Keep the two independent minimal-boundary captures.** `beliefs-5b28c5` records
   the user's prior ruling: the capture at recipe creation and the capture before
   launch detect a changed executing environment. `require_executing_environment`
   must continue to re-read and compare the closure. Confined runs keep their own
   capture, snapshot and pre/post-exit integrity checks from the
   [run-confinement design](../../designs/2026-08-30-run-confinement-design.md).
   A process-wide closure cache, digest cache across observations, skipped file
   checks or changed manifest bytes would weaken these guarantees and is rejected.

3. **Remove repeated pure work at its shared source.** First trial per-instance
   memoization of `EnvironmentManifest.identity()`: `EnvironmentManifest` is frozen,
   its artifact tuples and strings are immutable, and callers currently project and
   hash the same manifest more than once per run. Use only the standard library and
   keep the public `identity()` method and digest bytes unchanged. If the measured
   end-to-end gain does not exceed run variance, revert the trial.

4. **Then optimize the closure walk only where profiling pays for it.** The next
   candidate is the repeated path and metadata work in `adapter.py`'s `add_records`,
   `add_tree` and per-file location flow. Each candidate must still read and hash every
   required artifact on *each* capture, preserve symlink, root-precedence and escape
   handling, and produce exactly the same manifest, render plan and refusal behavior.
   Trial one local change at a time; keep it only if the representative tests and
   suite timing improve beyond observed noise. No new dependency or general cache is
   justified by the measurements.

5. **Use fixture sharing only for proven read-only duplicate runs.** If product-level
   work alone misses the target, inspect nonfrozen test modules such as the R4 negative
   family in `test_replay.py`. A shared module fixture is allowed only where every
   consumer reads the identical minted run without mutation and the test still
   exercises its own distinct behavior. Frozen conformance-cut bodies remain intact;
   no assertion or execution arm may be dropped to meet the time budget.

The alternative of making the full gate parallel or running it less often is rejected
as the primary fix: `just test-fast` already uses xdist, and the serial full run is the
required certified conformance gate. The cross-project policy that creates a P0 and
halts new lower-priority work belongs to `ops-5beefd`; its design and implementation
are separate from this repository's performance change.

## 3. Implementation shape

The implementation plan will divide work into measured, reviewable steps:

1. **Baseline repair.** Identify each falsified live and cited pin, make the doctrine's
   targeted updates, and prove both guard checks pass. Record the repair as a separate
   result from any speedup. The frozen-cut citation amendments explain the later
   change without altering the original discharge claim.
2. **Controlled baseline.** On the certified tuple, run a small representative case
   through its verdict, then record warm capture and identity microbenchmarks, replay
   test durations, a complete `just test-fast`, and the serial gate through `just
   test` or the pre-push hook. `tt` records the wall time and test count. Record CPU
   budget, Python version, commit and host load with each comparison.
3. **Pure-work trials.** Trial immutable manifest identity memoization and then
   measured closure-walk changes. For each, compare byte-identical manifest and
   identity results, boundary mutation/refusal tests, a representative pipeline case,
   and the fast suite before keeping it. Revert neutral or slower changes.
4. **Residual slow-tail pass.** If necessary, share only read-only baseline runs in
   mutable test files after checking every consumer. Measure each module and the whole
   loop. Preserve all conformance assertions and accepted runner inventories.
5. **Final verification and budget.** Run `just check`, `just test-fast`, and the full
   certified `just test` gate. Update the current-facing recipe and README timing
   claims with actual numbers; leave `tools/tt` and the existing recipes as the timing
   source. Record the final comparison and any unsuccessful trials on the P0 task.

No host launcher, symlink or service pointer is repointed at the worktree. Every live
test uses an explicit worktree path or a local environment override.

## 4. Verification contract

**Correctness.** The two existing frozen-guard failures must turn green through pin
maintenance, not skips. A changed artifact between the two minimal-boundary captures
must still refuse execution. Confined pre/post-exit mutation checks, closure escape
refusals, symlink handling, recipe identities and N2 capability-dependent arms must
retain their results. The full serial gate must pass on the certified tuple; a green
CI run on an uncertified runner cannot substitute for it.

**Performance.** Compare the same commands, warm dependency caches and host budget.
Use at least three warm samples for capture, identity and representative test timings;
use three complete fast-loop samples before and after a retained optimization. For the
expensive serial gate, use the recent `tt` distribution and one repaired-tree baseline,
then at least two post-change complete runs under comparable host load. Record median,
range, test count and failures. If the post-change samples straddle a target, add one
sample rather than declaring a win from the best run. Only a passing result that beats
run-to-run variance counts as an improvement.

The P0 closes when both time targets are met and the certified gate is green, or after
the user reviews a new design that explicitly changes the target based on measured
limits. `ops-5beefd` remains responsible for making a future sustained breach visible
and blocking lower-priority starts across projects.
