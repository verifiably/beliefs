---
id: beliefs-04c681
title: "In-use test-fast runs a median of 111 s, above the 90 s warm target"
status: idea
priority: 3
created: 2026-09-30T00:19:13Z
updated: 2026-09-30T10:37:37Z
depends: []
tags: [testing]
source: beliefs-0c1cc9
agent: claude-code/claude-fable-5-1
---

Why: beliefs-9b248a set and met a warm fast-loop target of 90 s on the certified host (87.17 s median, three runs, 2026-09-26). The recorded runs since then are slower. tt-report for 2026-09-27 to 2026-09-29 shows test-fast at a 111.4 s median and 143.6 s p90 over 15 runs (12 priced; 4 claude, 11 codex), test at 360.9 s over 2 runs against the 236 s benchmark, and one hook-pre-push at 2566.5 s. The run in beliefs-0c1cc9's worktree took 142.80 s for 5865 passed, 1 skipped.

Not established: the cause. Candidates are concurrent agents sharing the 16 workers, cold worktrees on WORK_ROOT storage, and suite growth (5704 tests at the benchmark, 5865 now). The 2566.5 s pre-push is one run and may be a full gate on a non-main ref under load.

Scope first as a measurement: split the recorded runs by concurrency and by worktree against main checkout before proposing any change. beliefs-f64cf1 covers N2 cost only, and N2 is not in the fast loop.

## Notes

- 2026-09-30T00:19:13Z (main): concerns: beliefs-9b248a extension — the 90 s target was defined warm on the certified host; recorded in-use runs sit at a 111 s median
- 2026-09-30T10:37:37Z (main): data point 2026-09-30: test-fast took 879 s (5887 passed) when host-budget sized it to 1 worker under load avg ~10; the in-use median should say whether such runs are in or out of its sample
