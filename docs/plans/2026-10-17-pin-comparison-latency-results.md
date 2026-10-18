# Pin-comparison latency results

**Task:** `beliefs-ce9d05`; implementation `beliefs-cf48c5`, verification `beliefs-d31eb1`.
**Status:** implemented and verified; incident and both implementation/verification tasks closed.
**Design:** [approved design](../superpowers/specs/2026-10-17-pin-comparison-latency-design.md).
**Plan:** [approved inline plan](../superpowers/plans/2026-10-17-pin-comparison-latency.md).
**Workspace:** `.worktrees/ce9d05-test-latency`.

## Change and correctness

The implementation adds only the standard-library import and
`@lru_cache(maxsize=128)` to the existing comparator. Its body, signature,
fresh working-file reads, git resolution, frozen pins, and comparison rules
are unchanged. Four regression tests cover reuse, changes to either byte
input, Python/non-Python path separation, and bounded eviction.

The reuse test was observed RED: both comparisons returned true, but the
second repeated the parse, giving four parser calls instead of two. After
the cache, all 40 comparator and pin-resolution tests passed in 9.64 seconds.
Those include working-file mutation after commit/content pin success,
absent/deleted targets, unresolved commits, cross-repository history, and
live table/scalar declaration pins. The parser spy delegates to the real
parser; no synthetic result is cached.

The refreshed unchanged fast baseline at `d591d71` passed 6,119 tests with
one skip in 78.773 seconds by `tt`. The unprofiled live-pin pilot's call time
fell from 13.10 to 5.02 seconds. Neither establishes the end-to-end decision.

## Alternating performance proof

Each row is a consecutive baseline/candidate pair, in B1/C1, B2/C2, B3/C3
order. Times are **recorded `tt` wall seconds**, including host-budget and
affected TypeScript selection. Lower is better; the baseline is the
uncached comparator and original test file. All runs used the same worktree
and installed environment, with the two byte-verified file snapshots restored
before each run. Each observed worker grant was 16, without an audio reservation.

| Valid pair | Baseline (s) | Candidate (s) | Baseline minus candidate (s) | Evidence labels |
| --- | ---: | ---: | ---: | --- |
| 1 | 73.723 | 65.127 | 8.596 | B1r / C1r |
| 2 | 73.369 | 65.141 | 8.228 | B2 / C2 |
| 3 | 70.476 | 68.406 | 2.070 | B3 / C3 |

- Baseline median: **73.369 s**; candidate median: **65.141 s**, below 90 s.
- Every paired reduction is positive; their median is **8.228 s**.
- Baseline range: 3.247 s; candidate range: 3.279 s. Median paired gain
  exceeds the approved conservative noise threshold, **3.279 s**.
- Verdict: **keep**. The median difference is about 11.2% of baseline time.

Every baseline passed 6,119 tests and every candidate passed 6,123: the only
inventory difference is the four added regression tests. Each had the same
one skip. TypeScript selected no changed tests and exited zero. No test,
assertion, capability check, or scheduler setting was removed or weakened.

One earlier pair, B1/C1, was excluded: indexing was active at B1 start and
ended during B1. The invalidation was recorded **before C1's verdict**, so
neither timing could influence it. Both successful logs are retained
(73.723/73.121 s). The six valid decision runs started afterward. Normal
desktop activity and brief post-run sync bursts remained visible in the
saved load samples; there was no sustained competing test grant or indexing
transition in the valid pairs. No service or host configuration was changed.

Baseline/candidate snapshots, full SHA-256 hashes, per-run revision and
dependency revisions, observed process grants, pre/post host load, complete
test logs, and `tt` records are retained in the ignored
`.worktrees/ce9d05-test-latency/.work/ce9d05-test-latency/` directory. Shared dependency revisions stayed unchanged
within each run and throughout the valid pairs.

## Attribution and complete certified suite

These two instrumented runs are outside the six-run decision. Their
`--durations=0` output gives sums of reported pytest setup/call/teardown
durations, not complete CPU accounting; phases below reporting precision
are omitted.

| Attribution measurement | Baseline | Candidate |
| --- | ---: | ---: |
| `tt` wall time (s) | 71.547 | 69.064 |
| Reported worker time (s) | 853.59 | 843.83 |
| Live-pin check call time (s) | 18.27 | 5.62 |

The complete certified `just test` passed in **213.675 s**, below 300 s:
6,123 ordinary Python tests plus one existing skip in 63.94 s, 46 standalone
N2 tests in 146.75 s, and all 155 TypeScript tests. The wrapper counted
6,324 executed tests. Capability failures were not converted into new skips;
the standalone N2 phase retained its full host allowance.

`beliefs-0180e2` retains its other follow-ups. This change supplies only the
memoization item, using exact byte keys rather than a digest-only cache.

## Review, integration, and incident verification

The final `just check`, post-documentation `just test-fast` (67.030 s), and
implementation commit hook passed. A fresh read-only Codex reviewer accepted
`533025e..c56b0c2` with no Critical, Important, or Minor findings, including
the paired timing proof and retained source snapshots. The full review is
retained in the plan workspace; its disposition is recorded on the incident.

The reviewed branch was fast-forwarded locally into main at `d5dc102`, whose
UTC commit timestamp, **2026-10-18T02:31:33Z**, is the remedy floor. Claims and
the execution ledger moved to main before incident verification.

| Fresh main run | Recorded wall time (s) | Python passed | Existing skips |
| --- | ---: | ---: | ---: |
| 1 | 67.182 | 6,123 | 1 |
| 2 | 68.671 | 6,123 | 1 |
| 3 | 71.800 | 6,123 | 1 |

All three started strictly after the remedy floor, had observed 16-worker
grants, and succeeded with unchanged affected TypeScript selection. The
verifier accepted all three as uncontended and unwidened. Their median was
**68.671 s**, below 90 s. `tt-latency verify beliefs-ce9d05 --after
2026-10-18T02:31:33Z` exited **0** and reported **every obligation met**.
The incident names one host; its identity and the full successful verifier
output are retained in [the incident record](../../tasks/beliefs-ce9d05.md).
Worktree pilots were excluded from this post-integration verification.

Execution ruling: review the whole branch before the plan's integration
task, because incident verification must follow integration. If that task
changes code, it needs another review. Post-integration closure is proved
separately; existing comparator-rule follow-ups and other latency bottlenecks
remain outside this reuse remedy. Their existing limitations/costs remain;
this change claims no improvement to them. No deferred minor findings.
