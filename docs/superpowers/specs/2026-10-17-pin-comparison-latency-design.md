# Reuse identical frozen-pin comparisons

**Date:** 2026-10-17  
**Task:** `beliefs-ce9d05` (P0 test-latency halt)  
**Status:** implemented and verified; incident `beliefs-ce9d05` closed

**Workspace:** `.worktrees/ce9d05-test-latency`

## Outcome

Restore a repeatable `test-fast` median of at most 90 seconds on the incident host while
preserving every existing test, assertion, skip rule, and frozen-pin verdict.
The incident closes only after `tt-latency verify beliefs-ce9d05 --after
<remedy timestamp>` exits zero on every host in its breach notes. The incident
currently names one host; the task record is authoritative for its identity.

The proposed remedy reuses the result of an identical, pure comparison of
two byte strings. It introduces no product behavior or dependency. This is
test machinery, not a conformance cut; it discharges no guarantee row.

## Evidence

The incident's trailing-window median is 92.287 seconds over eight successful,
uncontended, unwidened runs on three days, against a 90-second limit. Recent
individual runs vary substantially. One instrumented diagnostic run on the
unchanged task worktree at `77ce692` passed **6,119 tests with one skip**:

| Measurement | Result |
| --- | ---: |
| Recorded `tt` wall time, including affected TypeScript selection | 84.743 s |
| Pytest wall time | 82.54 s |
| Reported setup, call, and teardown time across 16 workers | 993.25 s |
| `test_boundary.py` total worker time | 172.10 s |
| `test_replay.py` total worker time | 116.12 s |
| `test_cut15_workflows.py` total worker time | 101.67 s |
| `test_every_pin_in_a_live_guard_holds` call time | 20.83 s |

The diagnostic used the current `just test-fast` command with
`--durations=0` added through `PYTEST_ADDOPTS`. TypeScript selected no changed
tests and exited zero. The host granted 16 workers with no audio reservation;
background indexing was present, so this single run establishes a diagnostic
baseline, not stable post-remedy acceptance.

A focused cProfile run of the live-pin check passed. It made 905 calls to
`pin_equivalence.equivalent`, taking 29.672 cumulative seconds under profiler
overhead, within a 35-second pytest run. It built 1,352 syntax trees and
comment projections. The 931 live table pins name only **69 distinct
target/pin pairs across 57 target paths**. Repeated guards therefore parse and
tokenize the same byte pairs many times. These profiler times attribute work;
they are not directly comparable to unprofiled timings.

A separate boundary-fixture profile confirms that two independent environment
captures still occur and dominate that fixture. Changing their filesystem
mapping would touch product code. Start with the smaller, measured repetition
in test machinery. `beliefs-0180e2` already records memoizing the comparator
among several deferred follow-ups; this incident takes only that performance
item. Its directive handling, edge cases, and documentation work remain there.

Diagnostic logs and profiles are retained in the worktree's ignored
`.work/ce9d05-test-latency/` directory.

## Design

Apply the standard library's `functools.lru_cache(maxsize=128)` directly to
`pin_equivalence.equivalent`. The cache key is the complete immutable
`original` bytes, `current` bytes, and `path` argument. Keep the function's
signature and comparison body intact. Python dictionary key equality checks
the bytes even when their hashes collide; no digest-only identity or custom
cache layer is needed.

The bound of 128 entries is the author's choice: it exceeds the currently
observed distinct pin pairs while bounding retained comparisons. It bounds
entry count, not total bytes. A process may retain both input byte strings
for each entry until eviction or exit. Every xdist worker has its own cache;
there is no file, cross-process cache, or persisted verdict.

Both callers in `frozen_guards.py` continue reading the working file before
calling the comparator. A file edit therefore supplies different bytes and
cannot reuse an earlier verdict. Original-byte changes likewise miss the
cache. Keeping the complete path in the key preserves the existing distinction
between Python and non-Python targets. Repository identity is unnecessary for
this pure function: equal bytes and paths mean the same comparison in every
checkout. Git resolution and working-file existence checks stay outside it.

Identical-byte acceptance, encoding, normalized syntax trees, comment anchors,
directive lines, non-Python byte identity, and malformed-input refusals keep
their current semantics. Boolean successes and refusals may both be cached;
exceptions that the existing function propagates remain propagated. No AST
or mutable comment projection is shared with callers.

## Scope and alternatives

The implementation reaches `python/tests/pin_equivalence.py`, its existing
tests, and a current-facing note in the formatting-equivalence design. The
two callers in `frozen_guards.py` need verification, not a new interface.
The results record documents measurements and the disposition of the
memoization item in `beliefs-0180e2` without closing its remaining scope.

Do not cache a path's verdict, file contents, git history lookups, or an
environment observation. Do not change scheduler settings, selected tests,
worker grants, latency limits, pins, frozen cut bodies, or product code.
Do not combine this trial with the other comparator follow-ups.

The rejected first approach is optimizing closure-path mapping in product
code: profiling shows a cost, but its guarantees need a broader change than
reusing a pure comparison. Retain that evidence if the bounded comparator
trial does not deliver a measurable end-to-end gain.

## Verification and keep-or-revert rule

Before editing code, refresh an unprofiled fast baseline and run a focused
live-pin verdict. Record revision, selected counts, worker grant, host load,
and `tt` time. Do not overlap measurement runs with another long test run.

Add small regression checks proving repeated identical input avoids a second
parse, changing either byte string recomputes the verdict, a different path
cannot reuse a Python verdict for a non-Python file, and the cache remains
bounded. Use the existing semantic comparator tests as the authority; keep
their assertions. Through `just test-one`, also exercise commit/content pins
that change working bytes in one process, and all current live-pin and scalar
declaration checks. First demonstrate the new reuse check failing without
the cache, then run it green with the focused suite.

Run the smallest focused pilot to its verdict before a sweep. It must retain
all verdicts and substantially reduce repeated parsing and live-pin check
time. Then take six comparable warm, unprofiled `just test-fast` runs as three
consecutive alternating baseline/candidate pairs: B1, C1, B2, C2, B3, C3, each
at a 16-worker grant. Record host load and background activity for each run;
if conditions change materially within a pair, invalidate and repeat that
whole pair. Read aggregate worker time from one comparable instrumented run
on each version. The full selection and existing skip count must match,
apart from explicitly added regression tests.

Keep the change only if correctness passes, the three candidate `tt` times
have a median of at most 90 seconds, and every candidate is faster than its
paired baseline. Record all three paired reductions. Their median must also
exceed the larger of the baseline and candidate timing ranges (maximum minus
minimum), a conservative noise check. A large focused improvement or separated
batch ranges alone is insufficient. If these conditions do not hold, revert
and record the residual. Do not keep an unproven cache merely because it is small.

Run `just check` and the required `just test-fast` before the implementation
commit. A complete certified `just test` run is warranted once because the
comparator is shared with conformance machinery; it must retain its verdict
and remain within the existing 300-second suite limit. N2 and TypeScript
remain part of that run. No global launcher or host config is repointed.

After review and local integration, record the remedy commit's UTC timestamp.
Run three new, successful, uncontended, unwidened `just test-fast` verdicts
in the registered main checkout, all starting strictly after that timestamp.
Pre-integration pilots do not count. Run `tt-latency verify` there and retain
its full output in the task completion message. If verification refuses or
misses the limit, leave the halt open and investigate its measured reason.

The user approved both the written design and implementation plan, including
inline execution. Retention and integration remain subject to the evidence above.
