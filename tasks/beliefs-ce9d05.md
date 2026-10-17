---
id: beliefs-ce9d05
title: "Test latency over limit: test-fast 92.287 s against 90 s"
status: doing
priority: 0
size: m
complexity: high
process: planned
owner: perf/ce9d05-test-latency
created: 2026-10-16T20:01:01Z
updated: 2026-10-17T21:04:14Z
started: 2026-10-17T21:03:56Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-10-16T20:00:58Z"
---

Filed by tt-latency on titan: the median of successful, uncontended, unwidened runs over the trailing window is over the limit in latency.toml (ops). The beliefs project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-10-16T20:01:03Z (main): breach: titan window 2026-10-09T20:00:58Z..2026-10-16T20:00:58Z: test-fast median 92.287 s, limit 90 s, 8 runs on 3 days
- 2026-10-17T21:03:56Z (main): started
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-17T21:04:14Z (perf/ce9d05-test-latency): resumed
  provenance: {"harness_session":"codex:01a14bac-fd82-7f12-9cbf-35cafc4359ef","harness_session_source":"CODEX_THREAD_ID"}
