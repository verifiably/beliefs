# Test-suite latency — balanced iteration and a full certified gate

- **Date:** 2026-09-26
- **Status:** draft for user review, round 2
- **Task:** `beliefs-9b248a` (P0)
- **Workspace:** `.worktrees/test-latency`
- **Related policy task:** `ops-5beefd` (cross-project detection and stop-work escalation)

## 1. Outcome and current evidence

The wait that matters is the time to a trustworthy verdict. The last seven days of
`tt-report --project beliefs` show a 190.2-second median for `just test-fast` and a
1,243.3-second median for `just test`. The previous audit supplied a fast loop and
timing records, but did not bring either wait within an acceptable iteration budget.

One instrumented fast run on 2026-09-26 used the current suite, 16 xdist
workers and the existing `--dist=loadfile` recipe. It reported 5,704 passed, one
skipped and the same two frozen-guard failures in 179.6 seconds. The earlier
worktree run reported the same results in 180.74 seconds.

| Current fast-loop observation | Measured value |
| --- | ---: |
| Test time summed across workers | 1,210 seconds |
| `_walk_closure` | 188 calls, 423 seconds (35% of worker time) |
| `EnvironmentManifest.identity()` | 1,760 calls, 208 seconds (17%) |
| `test_boundary.py`, pinned to one worker | 175 seconds |
| `test_replay.py` / `test_verify.py` / `test_cut15_workflows.py` | 144 / 138 / 113 seconds |
| Workers idle after roughly 40 seconds | 8 of 16 |

The 1,210 worker-seconds imply a 76-second perfect-balance floor before any
optimization. In the current distribution, one file determines nearly the entire
180-second wall time. Heavy files have one or two module fixtures, so splitting a
file across workers may repeat expensive setup; the distribution must be measured,
not assumed to win.

The serial gate cannot plausibly reach the previous draft's 600-second target by
the permitted product changes alone. Capture plus identity account for about 52%
of the current Python worker time outside N2. Memoizing repeated identities could
save roughly 190 worker-seconds; even halving capture cost would save roughly 200
more. That still puts a serial whole-suite run near 850–900 seconds, and an
unrealistic removal of both costs leaves roughly 700 seconds once the other work
is included. These are attribution estimates, not a serial benchmark.

Parallel execution is a plausible full-gate lever: on 2026-09-04, the then-current
3,216-test full suite took 223.34 seconds with eight xdist workers and
`--dist=loadfile`, versus 868.15 seconds serially. That sample does not predict
the current suite's result, so the new full gate needs a fresh certified pilot.

The existing red baseline has a separate fix: `5ee9e24` on `design/publish`
updates the live guard pins, cited-not-run registry and dated cut 7/9 citations.
That branch passes all seven `test_frozen_guards.py` checks. The same change
reached local main as cherry-pick `2ec30ce`: the seven guard checks, `just check`
and `just test-fast` (5,706 passed, one skipped in 189.38 seconds) pass there.
The P0 branch must incorporate that main commit before its performance baseline.
This spec does not duplicate the pin repair. The underlying `117e97e`
work-root change affected runners 4–9 and 11–41, not only cuts 5–8.

Success is a median of **at most 90 seconds for the existing fast-loop
selection** (Python without N2, plus affected TypeScript tests) and **at most
600 seconds for a complete certified full gate** (all Python and TypeScript
tests, including N2). The full gate may run independent tests in parallel; its
meaning is coverage and verdict, not a serial schedule.
The serial command remains available for diagnosis, not as a completion threshold.
The targets apply to comparable warm runs on the certified host and volume under
`host-budget run`. A speedup that changes the selected tests or weakens a
capability-dependent check does not count.

## 2. Decisions

1. **Use the existing main fix, outside this P0.** Local main contains the
   verified cherry-pick `2ec30ce` of `5ee9e24`. The P0 plan starts from that
   guard-green tree; it does not create a competing pin change or rewrite frozen
   evidence.

2. **Balance the fast loop first.** `just test-fast` excludes N2, the only
   documented reason for its `--dist=loadfile` setting. Trial xdist `load`
   against the current `loadfile` command with identical collection and worker
   budget. Trial `worksteal` if `load` leaves a slow tail. Where a test actually
   needs worker affinity, apply a targeted `xdist_group` and use a scheduler
   that honors it; do not group a whole heavy file merely to preserve the old
   bottleneck. Record per-file wall time, worker assignment, fixture duplication
   and aggregate worker-seconds. A recipe change may satisfy the fast-loop wall
   target: developer wait is the outcome. It must keep all checks and pass on
   repeated runs.

3. **Memoize only the pure environment identity.** `EnvironmentManifest`
   validates exact tuples of exact strings, so equal artifact tuples have equal
   identity digests. Use a small bounded standard-library memo in `recipe.py`,
   keyed by those validated artifact tuples, outside the dataclass instance.
   The memo must not appear in `dataclasses.fields()`, `vars()`, equality, repr
   or pickle; existing code projects values through `vars()` in several places.
   Keep the public `identity()` method and its bytes unchanged. This is a
   pure value memo, not a cache of closure observations: every capture still
   reads and hashes every required artifact, and the pre-launch comparison still
   observes mutations. If end-to-end gain does not beat measurement noise,
   revert the memo.

4. **Make the routine full gate parallel after proving equivalence.** The done
   criterion of `beliefs-92e6fe` requires *full pytest*, and no banked
   guarantee found in the current design or N2 harness requires independent
   pytest files to run serially. N2 applies sabotages to copies, never to the
   working tree. Its session-scoped findings fixture must remain on one xdist
   worker so it is not recomputed on several workers; `--dist=loadfile` provides
   that affinity for the first full-gate pilot. N2's nested pool must stay
   within `OPS_WORKERS`. Only after the pilot passes on the certified tuple,
   repeated runs agree on collection and verdict, and the full gate meets its
   wall target should `just test`, pre-push and CI adopt the parallel command.
   The explicit serial pytest command remains available for diagnosis.
   Historical cut-specific acceptance commands, including records that used a
   serial command, and their evidence are unchanged.

5. **Keep the boundary guarantees.** The earlier user ruling in
   `beliefs-5b28c5` requires two independent captures for minimal runs:
   recipe capture and pre-launch recapture. Confined snapshot and pre/post-exit
   checks remain as specified by the
   [run-confinement design](../../designs/2026-08-30-run-confinement-design.md).
   No process-wide closure cache, cross-observation file-digest cache, skipped
   files, changed manifest bytes or weaker mutation refusal is allowed.

The closure walker is a measured secondary cost, not the first lever. If balancing,
identity memoization and a parallel full gate miss their targets, profile the
residual before proposing path-walk changes or read-only fixture sharing. Keep
frozen conformance-cut bodies and all assertions intact.

## 3. Delivery and measurement order

1. **Prerequisite.** Incorporate main's pin fix into the P0 branch and confirm
   the seven frozen-guard checks still pass. No second pin repair is planned.

2. **Per-file measurement and fast scheduler trial.** First record the current
   per-file breakdown, worker assignment and fixture cost, using the §1 table
   as the initial comparison. Run one representative test from each heavy file
   through a verdict under each proposed scheduler before a full-loop sweep.
   Then run `load`, and `worksteal` only if needed, against `loadfile` on the
   same warm worktree and host budget. Record commit, Python version, host load,
   `OPS_WORKERS` and test count. A mode that exposes
   order-dependent tests or repeats a module fixture enough to lose its wall
   benefit is not adopted. Keep the mode with the shortest repeatable wall time
   and full unchanged collection.

3. **Identity trial.** Add a small regression check for digest equality,
   immutability and invisibility to `fields`, `vars`, repr and pickle. Benchmark
   identity calls and a representative pipeline test, then the complete fast
   loop. Keep the bounded memo only if it produces a material end-to-end gain
   without changing closure capture counts, refusals or recorded identities.

4. **Full-gate pilot and adoption.** Run one certified full parallel pilot
   through its verdict using N2 affinity and a worker count within the host
   budget. Read the full result before a longer comparison. Compare with the
   seven-day serial distribution and the pilot's own per-file and N2 timings;
   adjust distribution only from that evidence. Once equivalent and stable,
   update the shared test command used by `just test`, pre-push and `ci-python`,
   plus the current-facing `AGENTS.md`, justfile and README claims. CI remains
   uncertified for capability-dependent arms; only the certified host proves
   those arms.

5. **Final evidence.** Run `just check`, three warm fast-loop runs and at least
   two complete certified full-gate runs under comparable load. Both full
   runs must meet the 600-second target; if they disagree materially, take a
   third. The median fast-loop time must meet 90 seconds. Record selected test
   counts, skips, worker-seconds, range and any failed/reverted trials on the
   P0 task. If either target remains unmet, keep the P0 open and use the
   residual timing to choose the next bounded change.

A live test runs the worktree code by explicit path or local environment
override. No host launcher, service or shared config pointer is repointed.

## 4. Verification contract

- The main baseline and final certified gate pass without converting failures
  into skips. N2 still audits every declared arm and retains its own copied
  workspaces; the full gate runs the same test inventory as serial pytest.
- Changing an artifact between the two minimal-boundary captures still refuses
  execution. Confined pre/post-exit mutation checks, symlink and escape
  refusals, recipe identities and frozen guard pins retain their results.
- The chosen scheduler passes repeated full runs on the certified tuple.
  Parallel execution must not make a module fixture or fixed work root produce
  an order-dependent result. If it does, diagnose that shared state before
  changing the gate; the serial command remains the gate until resolved.
- Wall time is compared with the same commands and warm caches. Report
  aggregate worker-seconds beside wall time so fixture duplication is visible.
  A green uncertified CI run is evidence about portable tests only.

`ops-5beefd` owns the separate cross-project policy for surfacing a sustained
budget breach as P0 and stopping lower-priority starts.
