# Fast-suite fixture grouping

- **Date:** 2026-09-30
- **Status:** proposed; awaiting written-spec review
- **Task:** `beliefs-04d696` (P0 test-latency halt)
- **Workspace:** `.worktrees/test-fast-remedy`

## Outcome and evidence

Restore the certified host's non-N2 `test-fast` median to at most 90 seconds without removing tests, changing assertions, weakening capability checks, or changing product behavior. The full gate, including N2 and TypeScript, retains its 300-second limit. `tt-latency verify beliefs-04d696 --after <remedy timestamp>` must pass on every host named in the incident's breach notes before it closes.

The seven-day escalation measured 120.71 seconds across ten uncontended runs on three days. On the current worktree at a 16-worker host budget, three diagnostic fast runs passed 5,887 Python tests with one skip: pytest took 94.08 seconds with top-30 durations, 91.59 seconds with all durations, and 91.77 seconds without duration reporting. The plain run is still over the 90-second limit; these are diagnostics, not post-remedy verification.

The all-durations run recorded 1,209.7 worker-seconds. `test_verify.py` incurred 12 setup phases totaling 129.1 seconds, and `test_replay.py` incurred seven totaling 85.1 seconds. Their module-scoped `pair` fixtures each run a real assessment and replay. The 28 verify tests and 18 replay tests using `pair` account for nearly all of that setup cost; their measured call time was only about ten seconds combined. Under `worksteal`, tests from either file can reach several workers, so each worker repeats the module fixture. The prior latency design tried unmarked `loadgroup` and rejected it: fixture duplication raised aggregate worker time to 1,975 seconds. That result does not measure grouping the fixture consumers explicitly.

## Design

Keep the fast and full Python test selection exactly as it is. Switch their non-N2 phase from `--dist=worksteal` to `--dist=loadgroup`. During pytest collection, mark only tests in `test_replay.py` and `test_verify.py` that request the expensive module-scoped `pair` fixture with `xdist_group`; use a different group name for each file. Give `test_verify.py`'s `production_pair` consumers a third group: the timing run showed two repeated setups of roughly 11 seconds each. Tests outside those groups remain individually schedulable. The grouping is test scheduling only: no fixture data is persisted across processes and no production code changes.

The collection hook belongs in the existing `python/tests/conftest.py`, where pytest already centralizes test hooks. It identifies tests by path and fixture name rather than a maintained list of test names. The justfile's one `py_fast_cmd` supplies both `test-fast` and the first phase of `test`; changing that command updates both without duplicating scheduler settings. The standalone N2 phase remains separate and receives the full host worker allowance.

This approach should reduce the 19 measured fixture setups to about one per fixture. The saved worker time is an estimate, not a promised wall-time gain: `loadgroup` may leave a longer tail elsewhere. A focused pilot must first show that each group's consumers land on one worker, while unrelated tests remain free to distribute. Then compare complete fast runs with the same test inventory, host budget, and low competing load. Revert the scheduler and grouping together if the median misses 90 seconds or the full gate regresses; record the residual bottleneck on the incident before choosing another remedy.

## Verification

1. Pin collection: the non-N2 Python count and skip count match the current baseline, and N2 still runs in the separate full-gate phase. The TypeScript commands and selected tests remain unchanged.
2. Pin distribution: a focused xdist run shows one setup of each grouped fixture and separate scheduling of an unrelated test. A test of the collection hook checks that only intended fixture consumers receive group marks.
3. Run `just check` and three warm `just test-fast` verdicts under `host-budget run`; record `tt` wall time, aggregate worker time, host load, and test counts. The median must be at most 90 seconds.
4. Run the complete certified `just test` gate once after the fast pilot; it must pass within 300 seconds with N2 and TypeScript included. If its result is close to the limit or differs materially from the prior 235–237-second evidence, repeat it.
5. After the remedy commit, run `tt-latency verify beliefs-04d696 --after <remedy timestamp>` on every host named in the breach notes. Keep the incident open until it exits zero; include its output in `tasks done`.

Frozen conformance-cut bodies, historical evidence, and the two independent environment captures are unchanged. Update the current-facing scheduler description in `justfile` and `AGENTS.md` with the scheduler change.
