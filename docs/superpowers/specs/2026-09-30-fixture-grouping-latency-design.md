# Fast-suite fixture grouping

- **Date:** 2026-09-30
- **Status:** implemented and verified on the certified host; incident `beliefs-04d696` closed
- **Task:** `beliefs-04d696` (P0 test-latency halt)
- **Workspace:** `.worktrees/test-fast-remedy`

## Outcome and evidence

Restore the certified host's non-N2 `test-fast` median to at most 90 seconds without removing tests, changing assertions, weakening capability checks, or changing product behavior. The full gate, including N2 and TypeScript, retains its 300-second limit. `tt-latency verify beliefs-04d696 --after <remedy timestamp>` must pass on every host named in the incident's breach notes before it closes.

The seven-day escalation measured 120.71 seconds across ten uncontended runs on three days. The latency checker applies the prior remedy's 2026-09-26T18:35:55Z floor, so these are post-remedy runs. They span an evolving suite and host load; the current worktree diagnostics are a narrower starting point. At a 16-worker host budget, three diagnostic fast runs passed 5,887 Python tests with one skip. The plain run took 91.77 seconds in pytest and **93.984 seconds in `tt`**, whose recorded `test-fast` time also includes host-budget, `uv run` startup, and Vitest's affected-test command. The runs with all durations and top-30 durations took 93.925 and 103.453 seconds in `tt`, respectively. None is post-remedy verification.

The all-durations run recorded 1,209.7 worker-seconds. `test_verify.py` incurred 12 setup phases totaling 129.1 seconds, and `test_replay.py` incurred seven totaling 85.1 seconds. Their module-scoped `pair` fixtures each run a real assessment and replay. The 28 verify tests and 18 replay tests using `pair` account for nearly all of that setup cost; their measured call time was only about ten seconds combined. Under `worksteal`, tests from either file can reach several workers, so each worker repeats the module fixture.

The previous latency design tried unmarked `loadgroup` at 16 workers: aggregate worker time rose from 1,222 to 1,975 seconds, with verify and replay setup rising to 363 and 197 seconds. Xdist 3.8 treats **every unmarked test as a separate work unit** under `loadgroup`; the cost outside verify and replay also rose substantially. `worksteal` first assigns contiguous collection blocks and later steals from the back of a busy queue, which keeps many tests from one file together. Grouping only the named `pair` consumers would leave the rest of the earlier regression intact.

The current all-durations worksteal run gives these per-file comparisons for test files defining module- or class-scoped fixtures (seconds, rounded to one decimal). These are sums of pytest's reported duration rows; phases below its reporting precision are omitted, so `0.0` means no reported duration:

| File | Reported worker time | Reported setup time |
| --- | ---: | ---: |
| `test_arm_staleness.py` | 0.5 | 0.0 |
| `test_assess.py` | 69.0 | 19.2 |
| `test_boundary.py` | 163.9 | 18.4 |
| `test_closure_capture.py` | 6.8 | 2.0 |
| `test_frozen_guards.py` | 4.8 | 0.0 |
| `test_intent_reduce.py` | 0.0 | 0.0 |
| `test_production.py` | 21.5 | 5.2 |
| `test_replay.py` | 177.7 | 85.1 |
| `test_typing_exercise.py` | 0.2 | 0.0 |
| `test_verify.py` | 171.4 | 129.1 |

## Design

Keep the fast and full Python test selection exactly as it is. Switch their non-N2 phase from `--dist=worksteal` to `--dist=loadgroup`. During pytest collection, inspect each test's resolved fixture definitions. A test using any module-scoped fixture receives an `xdist_group` named for its test file. A test using only class-scoped fixtures receives a group named for its test class. Tests using only function- or session-scoped fixtures remain unmarked and individually schedulable. This rule covers replay, verify, and every other file with scoped fixtures without a maintained fixture-name list; renaming a fixture cannot silently remove grouping. Where a test requests both module- and class-scoped fixtures, its file group wins. Grouping changes scheduling only: no fixture data is persisted across processes and no product code changes.

The collection hook belongs in the existing `python/tests/conftest.py`, where pytest already centralizes test hooks. It uses pytest's resolved fixture scopes, not fixture-name spelling. The justfile's one `py_fast_cmd` supplies both `test-fast` and the first phase of `test`; changing that command updates both without duplicating scheduler settings. The standalone N2 phase remains separate and receives the full host worker allowance. Xdist's default `--loadscope-reorder` starts larger groups first, but group size is not elapsed time, so the measured tail still decides whether this scheduler is acceptable.

This approach should reduce repeated setup across all scoped fixtures, including the 19 measured replay and verify setups. The saved worker time is an estimate, not a promised wall-time gain: grouping can still leave a long test tail. A focused pilot first checks group assignment. One instrumented, complete fast verdict at the same 16-worker budget then compares aggregate worker-seconds and setup occurrences and seconds **for every file with a module- or class-scoped fixture** against the worksteal baseline. Continue to a repeated fast sweep only if total worker time falls below 1,209.7 seconds, the instrumented `tt` time is no worse than its 93.925-second baseline, and no scoped-fixture file gains new setup duplication. Repeat that pilot once if host load makes the comparison inconclusive. Revert the scheduler and grouping together if that pilot fails, the repeated `tt` median misses 90 seconds, or the full gate regresses; record the measured residual on the incident before choosing another remedy.

## Verification

1. Pin collection: every existing non-N2 Python test remains selected, one permanent collection-hook test is added (baseline count plus one), and the skip count remains unchanged. N2 still runs in the separate full-gate phase. The TypeScript commands and selected tests remain unchanged.
2. Pin distribution: a focused xdist run shows grouped fixture consumers on one worker and an unrelated, unmarked test still schedulable. A collection-hook test checks module, class, function, and session fixture scopes and the module-over-class precedence. The instrumented 16-worker pilot compares total worker-seconds and each scoped-fixture file's setup count and time with the current worksteal run; its baseline is 1,209.7 worker-seconds and 93.984 seconds in `tt` for the plain fast run.
3. If the pilot passes, run `just check` and three warm `just test-fast` verdicts under `host-budget run`; record `tt` wall time, aggregate worker time, host load, and test counts. The median of `tt` times must be at most 90 seconds. These pre-commit runs select the remedy but do not satisfy incident verification.
4. Run the complete certified `just test` gate once after the fast pilot; it must pass within 300 seconds with N2 and TypeScript included. If its result is close to the limit or differs materially from the prior 235–237-second evidence, repeat it.
5. Merge the reviewed remedy into the registered main checkout, then record the merge commit's UTC timestamp and run **three new** `just test-fast` verdicts there on each host named in the breach notes. All must start strictly after that timestamp and finish successfully without contention: do not overlap them with each other, `just test`, or another long recorded run. Run `tt-latency verify beliefs-04d696 --after <merge timestamp>` from main on that host, then close the incident in main. `verify.min_runs` is three; pre-merge pilots do not count. The registered checkout is the authority for the halt and receives `verify`'s note. Keep the incident open until every host's verify exits zero; include the verify output in `tasks done`.

Frozen conformance-cut bodies, historical evidence, and the two independent environment captures are unchanged. Update the current-facing scheduler description in `justfile` and `AGENTS.md` with the scheduler change.
