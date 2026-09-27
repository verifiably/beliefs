---
id: beliefs-f69178
title: Prove the latency budget and close the P0
status: done
priority: 0
size: s
complexity: mid
process: direct
owner: perf/test-latency
created: 2026-09-26T16:07:51Z
updated: 2026-09-26T18:35:51Z
started: 2026-09-26T18:02:24Z
completed: 2026-09-26T18:35:51Z
depends: [beliefs-1a27bc]
parent: beliefs-9b248a
tags: [testing]
agent: codex
plan: docs/superpowers/plans/2026-09-26-test-suite-latency.md
step: "Task 4: Prove the latency budget and close the P0"
---

Run repeated certified fast and full gates, record counts and timings, then close the P0 only if both targets hold.

## Notes

- 2026-09-26T18:02:24Z (perf/test-latency): started
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T18:02:28Z (perf/test-latency): Claimed by Codex /root, pid 632270. Certified 16-worker gate passes at tt 279.714 s, but fast loop is 109.716 s against 90 s. Attribute the non-N2 tail before choosing the next bounded change; keep P0 open.
- 2026-09-26T18:35:41Z (perf/test-latency): Final certified host-budget 16 acceptance: three warm just test-fast runs passed 5709/1 skipped, tt 86.936/87.167/87.424 s (median 87.167). Two just test runs passed 5709 non-N2/1 skipped + 46 N2 + 155 TS, tt 235.749/237.467 s; N2 alone 148.54/150.75 s. Instrumented worksteal run measured 1127.4 worker-s and 256 closure walks versus 1310.3 worker-s before path optimization; every walk still rehashes 8465 artifact rows. just check, focused closure/guard tests, tasks check and branch review passed. Reviewer found only stale scheduler text in P0 body, corrected via tasks edit.
- 2026-09-26T18:35:51Z (perf/test-latency): done
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T18:35:51Z (perf/test-latency): Certified 16-worker acceptance met both targets: fast median 87.167 s; two full gates 235.749 and 237.467 s with unchanged conformance coverage.
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
