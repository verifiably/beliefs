---
id: beliefs-ce9d05
title: "Test latency over limit: test-fast 92.287 s against 90 s"
status: doing
priority: 0
size: m
complexity: high
process: planned
owner: main
created: 2026-10-16T20:01:01Z
updated: 2026-10-18T02:36:20Z
started: 2026-10-17T21:03:56Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-10-16T20:00:58Z"
spec: docs/superpowers/specs/2026-10-17-pin-comparison-latency-design.md
plan: docs/superpowers/plans/2026-10-17-pin-comparison-latency.md
---

Filed by tt-latency on titan: the median of successful, uncontended, unwidened runs over the trailing window is over the limit in latency.toml (ops). The beliefs project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-10-16T20:01:03Z (main): breach: titan window 2026-10-09T20:00:58Z..2026-10-16T20:00:58Z: test-fast median 92.287 s, limit 90 s, 8 runs on 3 days
- 2026-10-17T21:03:56Z (main): started
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-17T21:04:14Z (perf/ce9d05-test-latency): resumed
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-17T21:06:41Z (perf/ce9d05-test-latency): Investigation: not trial-enrolled; locked and hydrated .worktrees/ce9d05-test-latency. Diagnostic 16-worker test-fast passed 6119 tests, 1 skip in 84.743 s by tt (pytest 82.54 s), with 993.25 reported worker-seconds. Top files: boundary 172.10 s, replay 116.12 s, cut15 workflows 101.67 s; live frozen-pin check alone 20.83 s. No code changes; profiling representative costs before design.
- 2026-10-17T21:09:13Z (perf/ce9d05-test-latency): Root-cause profile: live-pin check calls equivalent 905 times, spending 29.672 cumulative seconds under cProfile; 931 live pins cover 69 distinct target/pin pairs. Proposed narrow remedy is bounded lru_cache over actual original/current bytes and path, preserving fresh reads and all comparison semantics. Reuses only the memoization item from beliefs-0180e2; remaining follow-ups stay there. Draft spec linked; fresh read-only builder review dispatched. No implementation changes.
- 2026-10-17T21:09:50Z (perf/ce9d05-test-latency): review: spec round 1 — verdict: accept; findings: none; reviewer: codex
- 2026-10-17T21:10:54Z (perf/ce9d05-test-latency): parked (waiting on user, review): User reviews docs/superpowers/specs/2026-10-17-pin-comparison-latency-design.md in .worktrees/ce9d05-test-latency; after approval the agent writes the implementation plan for review there. Design committed at 2dc3360; no implementation changes.
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-17T22:07:56Z (perf/ce9d05-test-latency): resumed
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-17T22:07:59Z (perf/ce9d05-test-latency): review: spec round 2 — verdict: revise; findings: measurement protocol 1; reviewer: human
- 2026-10-17T22:08:55Z (perf/ce9d05-test-latency): review: spec round 3 — verdict: accept; findings: none; reviewer: codex
- 2026-10-17T22:09:44Z (perf/ce9d05-test-latency): parked (waiting on user, review): User reviews the revised design at .worktrees/ce9d05-test-latency/docs/superpowers/specs/2026-10-17-pin-comparison-latency-design.md (be6234b); after approval the agent writes the implementation plan there for review. Three alternating baseline/candidate pairs and consistent paired improvement are required; scoped re-review accepted without findings and commit checks passed.
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-17T23:23:21Z (perf/ce9d05-test-latency): resumed
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-17T23:23:23Z (perf/ce9d05-test-latency): review: spec round 4 — verdict: accept; findings: none; reviewer: human
- 2026-10-17T23:27:03Z (perf/ce9d05-test-latency): Plan drafted and self-reviewed against the approved spec: two sequential steps, beliefs-cf48c5 for correctness and alternating paired performance proof, then the dependent integration/incident verification step. Inline execution recommended for one shared worktree and sequential measurements. No implementation or new performance runs; awaiting user review of the plan.
- 2026-10-17T23:27:35Z (perf/ce9d05-test-latency): review: plan round 1 — verdict: accept; findings: none; reviewer: codex (self-review)
- 2026-10-17T23:28:32Z (perf/ce9d05-test-latency): parked (waiting on user, review): User reviews .worktrees/ce9d05-test-latency/docs/superpowers/plans/2026-10-17-pin-comparison-latency.md (26285e8); after approval the agent executes inline, starting beliefs-cf48c5 in the existing worktree, then beliefs-d31eb1 after proof and review pass. Plan self-review and required commit checks passed. No implementation or new performance runs started.
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-18T01:58:55Z (perf/ce9d05-test-latency): resumed
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-18T01:58:57Z (perf/ce9d05-test-latency): review: plan round 2 — verdict: accept; findings: none; reviewer: human
- 2026-10-18T02:29:18Z (perf/ce9d05-test-latency): review: impl round 1 — verdict: accept; findings: none; reviewer: codex
- 2026-10-18T02:31:36Z (main): resumed
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-18T02:36:20Z (main): verified: titan after 2026-10-18T02:31:33Z: test-fast median 68.671 s, limit 90 s, 3 runs
