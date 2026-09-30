---
id: beliefs-5cc080
title: Implement grouping and run the instrumented pilot
status: done
priority: 0
size: s
complexity: mid
process: direct
owner: perf/test-fast-remedy
created: 2026-09-30T18:20:32Z
updated: 2026-09-30T19:05:41Z
started: 2026-09-30T18:54:52Z
completed: 2026-09-30T19:05:41Z
depends: []
parent: beliefs-04d696
tags: []
agent: codex
plan: docs/superpowers/plans/2026-09-30-fixture-grouping-latency.md
step: "Task 1: Implement grouping and run the instrumented pilot"
---

Add scoped-fixture grouping and its focused checks. Run the 16-worker pilot; retain the change only if its total worker time, tt time, and setup gate pass.

## Notes

- 2026-09-30T18:54:52Z (perf/test-fast-remedy): started
  provenance: {"harness_session":"codex:01a0f1f2-8c7e-71c3-9d0e-3ec49cdcdfef","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T19:05:41Z (perf/test-fast-remedy): done
  provenance: {"harness_session":"codex:01a0f1f2-8c7e-71c3-9d0e-3ec49cdcdfef","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T19:05:41Z (perf/test-fast-remedy): 16-worker pilot passed: 1,136.9 worker-s, 88.667 s tt, 5,888 passed/1 skipped; scoped fixture setups reduced
  provenance: {"harness_session":"codex:01a0f1f2-8c7e-71c3-9d0e-3ec49cdcdfef","harness_session_source":"CODEX_SESSION_ID"}
