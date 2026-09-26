---
id: beliefs-1a27bc
title: Adopt the two-phase full gate
status: doing
priority: 0
size: m
complexity: mid
process: direct
owner: perf/test-latency
created: 2026-09-26T16:07:45Z
updated: 2026-09-26T17:10:31Z
started: 2026-09-26T16:50:22Z
depends: [beliefs-141ecd]
parent: beliefs-9b248a
tags: [testing]
agent: codex
plan: docs/superpowers/plans/2026-09-26-test-suite-latency.md
step: "Task 3: Adopt the two-phase full gate"
---

Pilot certified non-N2 loadgroup plus standalone serial N2, set CI worker variables, and update the shared full gate and current-facing docs only after equivalence.

## Notes

- 2026-09-26T16:50:22Z (perf/test-latency): started
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T16:50:26Z (perf/test-latency): Claimed by Codex /root, pid 632270; piloting parallel non-N2 plus standalone N2 under one host-budget job before changing shared gate. Host currently grants 8 due Bitwig, so 16-worker target timing awaits idle host.
- 2026-09-26T17:10:31Z (perf/test-latency): Eight-worker certified two-phase pilot passed: collection 5708+46=5754 matches serial, non-N2 5707/1 skipped in 192.67 s, standalone N2 46 in 339.02 s, TypeScript 155 passed. Candidate shared recipe and CI/doc edits prepared; current audio-limited budget cannot prove 16-worker ≤300 s target, so child stays open for comparable pilot.
