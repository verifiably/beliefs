---
id: beliefs-a77bf9
title: Balance the fast scheduler
status: done
priority: 0
size: m
complexity: mid
process: direct
owner: perf/test-latency
created: 2026-09-26T16:07:37Z
updated: 2026-09-26T16:35:36Z
started: 2026-09-26T16:22:43Z
completed: 2026-09-26T16:35:36Z
depends: []
parent: beliefs-9b248a
tags: [testing]
agent: codex
plan: docs/superpowers/plans/2026-09-26-test-suite-latency.md
step: "Task 1: Balance the fast scheduler"
---

Measure loadfile versus loadgroup and adopt the faster unchanged non-N2 fast-loop selection. N2 runs outside xdist in the later full-gate phase.

## Notes

- 2026-09-26T16:22:43Z (perf/test-latency): started
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T16:22:53Z (perf/test-latency): Claimed by Codex /root, pid 632270; direct execution in .worktrees/test-latency. First compare small loadfile/loadgroup selections, then the full fast loop.
- 2026-09-26T16:35:36Z (perf/test-latency): done
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T16:35:36Z (perf/test-latency): loadgroup preserved 5706-pass fast inventory and cut wall time from 183.50 to 139.91 s; fixture setup duplication measured and P0 remains open.
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
