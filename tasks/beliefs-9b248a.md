---
id: beliefs-9b248a
title: Cut Beliefs test iteration cost while preserving conformance
status: doing
priority: 0
size: l
complexity: high
process: planned
owner: perf/test-latency
created: 2026-09-12T10:10:50Z
updated: 2026-09-26T16:21:32Z
started: 2026-09-26T10:07:42Z
depends: []
tags: [testing]
source: beliefs-f253a1
spec: docs/superpowers/specs/2026-09-26-test-suite-latency-design.md
plan: docs/superpowers/plans/2026-09-26-test-suite-latency.md
---

Why: seven-day medians were 1243 s for just test and 190 s for just test-fast, slowing iteration for weeks. The current 5704-test attribution found 1210 aggregate worker-seconds, including 423 s in closure captures and 208 s in repeated environment identities, with the 175 s test_boundary.py worker setting fast-loop wall time. Local main pin fix 2ec30ce restores a green baseline. Standalone N2 passes 46 tests in 193 s with 16 workers; under grouped xdist its nested pool would fall to one worker.

Outcome: keep the same full test inventory and both independent environment captures; use loadgroup for non-N2 tests, run N2 as a second serial pytest phase with its full pool, and add a bounded pure identity memo. On the certified tuple require warm fast-loop median at most 90 s and complete full runs at most 300 s. Record counts, worker-seconds and verdicts; keep the P0 open if either target is missed. The cross-project stop-work policy belongs to ops-5beefd.

## Notes

- 2026-09-26T10:06:12Z (main): 2026-09-26 pilot: replay R4 negative A 15.25s; cProfile diagnostic 31.98s under instrumentation: four capture_closure calls 17.74s, ten recipe projections 9.22s, four run_engine calls 3.16s. Direct single capture 2.154s for 8465 artifacts. Profile timing is diagnostic, not a baseline. Prior two-capture ruling in beliefs-5b28c5 remains binding.
- 2026-09-26T10:06:44Z (main): Earlier audit (2026-09-12): 97 pipeline call sites in 17 files; 60 slowest tests 5-24s each, 669s worker time out of roughly 1370 in 4438-test 171.46s fast loop. No material sleeps or network. Candidate fixture sharing must not edit frozen cut bodies. Ops stop-work policy filed as ops-5beefd.
- 2026-09-26T10:07:42Z (perf/test-latency): started
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T10:07:42Z (perf/test-latency): claimed by codex/gpt-6, pid 632270; worktree .worktrees/test-latency. Planned design review pending before implementation.
- 2026-09-26T10:12:08Z (perf/test-latency): Baseline in .worktrees/test-latency after just setup: just test-fast ran 5704 passed, 1 skipped, 2 failed in 180.74s. Both failures are frozen guard pin checks; the same two fail on main in 2.90s, so this is an existing gate failure, not a worktree/setup artifact. The 117e97e work-root change moved cut5-8 acceptance runner files without matching live and cited guard pin maintenance. Repair or isolate this before claiming a green performance result.
- 2026-09-26T10:13:23Z (perf/test-latency): Warm direct probes in worktree: three closure captures 2.001/2.060/2.020s (8465 artifacts), nine uncached EnvironmentManifest.identity calls median 0.237s; one capture under cProfile 4.064s with add_records 2.059s, add_tree 1.497s, pathlib.relative_to 1.080s, digest reads 0.358s. These are instrumentation-local costs; preserve two captures and test any optimization against both mutation detection and an end-to-end fast-suite baseline.
- 2026-09-26T10:13:50Z (perf/test-latency): parked (waiting on user, review): User reviews the proposed latency design and targets in this session; on approval, codex resumes in .worktrees/test-latency, writes the committed spec, then writes the implementation plan for its review. First implementation step repairs baseline frozen-guard pins, then benchmarks capture/identity and verifies both environment captures remain.
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T15:09:09Z (perf/test-latency): resumed
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T15:09:09Z (perf/test-latency): User approved the in-chat Beliefs latency design on 2026-09-26 and asked for the written spec; resumed in .worktrees/test-latency. Spec review remains the next gate before implementation planning.
- 2026-09-26T15:12:02Z (perf/test-latency): parked (waiting on user, review): User reviews docs/superpowers/specs/2026-09-26-test-suite-latency-design.md in .worktrees/test-latency; on approval, codex resumes this task and writes the implementation plan for its separate review. No implementation code has changed.
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T15:40:51Z (perf/test-latency): resumed
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T15:40:52Z (perf/test-latency): User review round 1 requested revision: current per-file timing, xdist distribution for fast loop, reconsider parallel full gate, identity memo outside projections, and baseline pin fix via existing 5ee9e24 instead of duplicate work. Resumed spec only; code implementation remains gated.
- 2026-09-26T15:45:00Z (perf/test-latency): Baseline pin fix landed on local main as cherry-pick 2ec30ce of design/publish 5ee9e24; focused frozen guards 7/7, just check green, just test-fast 5706 passed and 1 skipped in 189.38s. The separate integration worktree was removed after confirming no host pointer targeted it. Remote origin/main has not been pushed.
- 2026-09-26T15:47:04Z (perf/test-latency): Spec review round 2: replaced stale 4438-test evidence with current 5704-pass worker attribution, made xdist balancing the fast-loop first lever, chose a parallel full gate conditional on certified N2-affinity validation, kept 90s/600s targets on the actual fast/full commands, and specified a bounded pure identity memo outside dataclass state. Local main now carries pin fix 2ec30ce; no duplicate repair in P0.
- 2026-09-26T15:47:04Z (perf/test-latency): parked (waiting on user, review): User reviews round-2 docs/superpowers/specs/2026-09-26-test-suite-latency-design.md in .worktrees/test-latency; on approval, codex incorporates local main pin fix and writes the implementation plan for its separate review. No latency implementation has started.
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T16:01:27Z (perf/test-latency): resumed
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T16:01:39Z (perf/test-latency): Claimed by Codex /root, pid 632270; user conditionally approved round-2 spec after loadgroup and 300 s target edits; writing implementation plan next.
- 2026-09-26T16:04:45Z (perf/test-latency): Merged local main (including verified pin fix 2ec30ce) into perf/test-latency; frozen guards pass 7/7 in this worktree. Spec finalized at f3f85d9; plan drafting only, no latency code changed.
- 2026-09-26T16:08:32Z (perf/test-latency): Implementation plan drafted in docs/superpowers/plans/2026-09-26-test-suite-latency.md with four ordered child tasks: loadgroup/N2, identity memo, parallel full gate, final evidence. User-approved spec includes 90 s fast and provisional 300 s full targets. tasks check and docs hook pass; no latency code implementation has started.
- 2026-09-26T16:08:37Z (perf/test-latency): parked (waiting on user, review): User reviews .worktrees/test-latency/docs/superpowers/plans/2026-09-26-test-suite-latency.md; after approval Codex resumes in that worktree, starts beliefs-a77bf9, and runs the four-file scheduler pilot before the first full sweep.
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T16:19:07Z (perf/test-latency): resumed
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T16:19:12Z (perf/test-latency): Claimed by Codex /root, pid 632270. Review found grouped N2 would receive OPS_WORKERS // PYTEST_XDIST_WORKER_COUNT = 1 here; changing the reviewed design to parallel non-N2 plus serial N2 in one gate, then implementing the four plan steps directly.
