# Test-suite latency — balanced iteration and a full certified gate

- **Date:** 2026-09-26
- **Status:** approved with the 2026-09-26 review changes
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

Parallel execution is a plausible lever for the tests outside N2: on 2026-09-04,
the then-current 3,216-test full suite took 223.34 seconds with eight xdist
workers and `--dist=loadfile`, versus 868.15 seconds serially. That parallel
sample predates the nested-pool share rule and does not predict a current full
xdist run. Under the current rule N2 gets `OPS_WORKERS //
PYTEST_XDIST_WORKER_COUNT` inside a worker: with 16 xdist workers here its pool
would be one. A 2026-09-26 standalone `test_n2.py` run used its full 16-worker
pool, passed 46 tests in 193 seconds and consumed 2,514 CPU-seconds. Grouping
it under xdist would turn that CPU work into a roughly 40-minute tail. The
full gate therefore needs two Python phases and a fresh certified pilot.

The first certified two-phase pilot ran under an eight-worker host allowance
while audio was active: the non-N2 phase passed 5,707 tests with one skip in
192.67 seconds, standalone N2 passed 46 in 339.02 seconds, and TypeScript
passed 155. Collection matched the 5,754-test serial inventory exactly. This
proves the split verdict at eight workers; it does not measure the 16-worker
300-second target.

The existing red baseline has a separate fix: `5ee9e24` on `design/publish`
updates the live guard pins, cited-not-run registry and dated cut 7/9 citations.
That branch passes all seven `test_frozen_guards.py` checks. The same change
reached local main as cherry-pick `2ec30ce`: the seven guard checks, `just check`
and `just test-fast` (5,706 passed, one skipped in 189.38 seconds) pass there.
The P0 branch has incorporated that main commit and still passes the seven
guard checks. This spec does not duplicate the pin repair. The underlying `117e97e`
work-root change affected runners 4–9 and 11–41, not only cuts 5–8.

Success is a median of **at most 90 seconds for the existing fast-loop
selection** (Python without N2, plus affected TypeScript tests) and **at most
300 seconds for a complete certified full gate** (all Python and TypeScript
tests, including N2). The two-phase gate's current budget is tight: about 193
seconds for standalone N2 leaves roughly 107 seconds for the fast Python phase,
TypeScript and overhead. If it misses, name the measured residual, especially
N2, and keep the P0 open rather than relaxing the target to hide scheduler
share arithmetic. The full gate may run independent tests in parallel; its
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

2. **Balance the fast Python phase with `loadgroup`.** Trial xdist
   `--dist=loadgroup` against the current `loadfile` command with identical
   collection and worker budget. `test-fast` and the full gate's first Python
   phase exclude N2, so heavy files can spread across workers. N2 runs as a
   second, serial pytest invocation and retains its full nested pool. No N2
   `xdist_group` marker or grouped-worker pilot is needed. Record per-file wall
   time, worker assignment, fixture duplication and aggregate worker-seconds.
   A recipe change may satisfy the
   fast-loop wall target: developer wait is the outcome. It must keep all
   checks and pass on repeated runs. If `loadgroup` leaves a slow tail, profile
   that tail before proposing another scheduler.

3. **Memoize only the pure environment identity.** `EnvironmentManifest`
   validates exact tuples of exact strings, so equal artifact tuples have equal
   identity digests. Use `functools.lru_cache(maxsize=4)` in `recipe.py`,
   keyed by those validated artifact tuples, outside the dataclass instance.
   The memo must not appear in `dataclasses.fields()`, `vars()`, equality, repr
   or pickle; existing code projects values through `vars()` in several places.
   Keep the public `identity()` method and its bytes unchanged. This is a
   pure value memo, not a cache of closure observations: every capture still
   reads and hashes every required artifact, and the pre-launch comparison still
   observes mutations. If end-to-end gain does not beat measurement noise,
   revert the memo.

4. **Make the routine full gate two-phase after proving equivalence.** The done
   criterion of `beliefs-92e6fe` requires *full pytest*, and no banked
   guarantee found in the current design or N2 harness requires independent
   pytest files to run serially. N2 applies sabotages to copies, never to the
   working tree. Run `pytest -n auto --dist=loadgroup
   --ignore=tests/test_n2.py && pytest tests/test_n2.py` as the two Python
   phases, followed by TypeScript. The `&&` requires both verdicts, and
   `tools/tt` adds their pytest summary counts into one recorded gate. N2 runs
   outside xdist, so its session-scoped findings fixture is built once and its
   nested pool uses the full `OPS_WORKERS` allowance. `ci-python` has no
   `host-budget`, so CI sets both `OPS_WORKERS=4` for N2 and
   `PYTEST_XDIST_AUTO_NUM_WORKERS=4` for the first phase's `-n auto`;
   host-budget sets both on the certified host. Only after the pilot passes on
   the certified tuple,
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
   Then run `loadgroup` against `loadfile` on the same warm worktree and host
   budget. Record commit, Python version, host load, `OPS_WORKERS` and test
   count. A mode that exposes
   order-dependent tests or repeats a module fixture enough to lose its wall
   benefit is not adopted. Keep the mode with the shortest repeatable wall time
   and full unchanged collection. If neither mode reaches the fast-loop target,
   keep the P0 open and attribute the remaining tail.

3. **Identity trial.** Add a small regression check for digest equality,
   immutability and invisibility to `fields`, `vars`, repr and pickle. Benchmark
   identity calls and a representative pipeline test, then the complete fast
   loop. Keep the bounded memo only if it produces a material end-to-end gain
   without changing closure capture counts, refusals or recorded identities.

4. **Full-gate pilot and adoption.** Run one certified two-phase Python pilot
   through both verdicts: parallel `loadgroup` with N2 ignored, then serial N2
   with the full host allowance. Read each result before a longer comparison.
   Compare with the seven-day serial distribution and the pilot's own per-file
   and N2 timings; attribute any miss of 300 seconds to measured components.
   Once equivalent and stable,
   update the shared test command used by `just test`, pre-push and `ci-python`,
   plus the current-facing `AGENTS.md`, justfile and README claims. CI remains
   uncertified for capability-dependent arms; only the certified host proves
   those arms.

5. **Final evidence.** Run `just check`, three warm fast-loop runs and at least
   two complete certified full-gate runs under comparable load. Both full
   runs must meet the 300-second target; if they
   disagree materially, take a
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
- The chosen two-phase command passes repeated full runs on the certified tuple.
  Parallel execution must not make a module fixture or fixed work root produce
  an order-dependent result. If it does, diagnose that shared state before
  changing the gate; the serial command remains the gate until resolved.
- Wall time is compared with the same commands and warm caches. Report
  aggregate worker-seconds beside wall time so fixture duplication is visible.
  A green uncertified CI run is evidence about portable tests only.

`ops-5beefd` owns the separate cross-project policy for surfacing a sustained
budget breach as P0 and stopping lower-priority starts.
