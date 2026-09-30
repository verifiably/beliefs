---
id: beliefs-04d696
title: "Test latency over limit: test-fast 120.71 s against 90 s"
status: doing
priority: 0
size: m
complexity: high
process: planned
owner: perf/test-fast-remedy
created: 2026-09-30T15:57:07Z
updated: 2026-09-30T16:55:27Z
started: 2026-09-30T16:17:00Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-09-30T15:57:06Z"
spec: docs/superpowers/specs/2026-09-30-fixture-grouping-latency-design.md
---

Filed by tt-latency on titan: the median of successful, uncontended runs over the trailing window is over the limit in latency.toml (ops). The beliefs project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-09-30T15:57:07Z (main): breach: titan window 2026-09-23T15:57:06Z..2026-09-30T15:57:06Z: test-fast median 120.71 s, limit 90 s, 10 runs on 3 days
- 2026-09-30T16:17:00Z (perf/test-fast-remedy): started
  provenance: {"harness_session":"codex:01a0f1f2-8c7e-71c3-9d0e-3ec49cdcdfef","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T16:17:00Z (perf/test-fast-remedy): claimed by codex, pid 2688366
