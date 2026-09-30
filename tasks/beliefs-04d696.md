---
id: beliefs-04d696
title: "Test latency over limit: test-fast 120.71 s against 90 s"
status: todo
priority: 0
size: m
complexity: high
process: planned
created: 2026-09-30T15:57:07Z
updated: 2026-09-30T15:57:08Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-09-30T15:57:06Z"
---

Filed by tt-latency on titan: the median of successful, uncontended runs over the trailing window is over the limit in latency.toml (ops). The beliefs project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-09-30T15:57:07Z (main): breach: titan window 2026-09-23T15:57:06Z..2026-09-30T15:57:06Z: test-fast median 120.71 s, limit 90 s, 10 runs on 3 days
