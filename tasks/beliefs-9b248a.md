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
updated: 2026-09-26T17:15:53Z
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
- 2026-09-26T16:23:21Z (perf/test-latency): Task 1 baseline: local main pin-fix fast run 5706 passed, 1 skipped, pytest 189.38 s / tt 191.4 s under loadfile; user instrumented pre-fix fast run 1210 worker-s, boundary 175 s, replay 144 s, verify 138 s, cut15 113 s. Current worktree 2f00489, Python 3.13.12, host-budget fan-out 16, host busy 1.4 at preflight.
- 2026-09-26T16:34:25Z (perf/test-latency): Task 1 measured on merged pin-fix tree: loadfile 5706 passed/1 skipped in 183.50 s, 1221.5 measured worker-s; loadgroup same inventory/verdict in 139.91 s, 1974.6 worker-s. Under loadgroup replay setup grew 18.0→196.7 s across 14 workers, verify 32.8→363.3 s across 16, boundary 7.9→32.2 s across 13. just test-fast loadgroup passed at 143.39 s. Keep scheduler for wall gain, but ≤90 s still open; fixture duplication is the measured residual.
- 2026-09-26T16:40:28Z (perf/test-latency): Task 1 post-commit just test-fast passed 5706/1 skipped in 244.14 s, but host-budget changed from 16 fan-out to 8 because Bitwig audio was active (busy 4.9); do not compare this wall time to the earlier 16-worker samples. Need comparable idle-host runs for final acceptance.
- 2026-09-26T16:47:55Z (perf/test-latency): Task 2 memo red-green: equal-manifest spy failed at 2 digest calls before and passed at 1 after; changed row required second call, fields/vars/repr/eq/pickle unchanged. Recipe+closure+frozen-guard+arm-staleness tests 121 passed; 8465-artifact direct 9 calls 2.376 s vs memoized 0.290 s, 8 hits/1 miss. 8-worker fast loop passed 5707/1 skipped in 197.53 s (pre-memo 244.14 s under audio); 16-worker target comparison deferred until host budget recovers.
- 2026-09-26T17:02:02Z (perf/test-latency): Task 3 certified two-phase pilot at host-budget 8 (Bitwig audio): collection 5754 serial = 5708 non-N2 + 46 N2 with no overlap/missing IDs; small && pilot passed 1+1. Full phase 1 passed 5707/1 skipped in 192.67 s; standalone N2 passed 46 in 339.02 s with full 8-worker pool; TypeScript passed 155/155. Python total ~531.69 s at 8 workers is correctness evidence, not 16-worker ≤300 s acceptance. Shared gate not changed yet.
- 2026-09-26T17:05:56Z (perf/test-latency): Residual scheduler trial after loadgroup tail: four-file worksteal pilot passed 4/4. At audio-limited host-budget 8, complete non-N2 worksteal passed 5707/1 skipped in 171.91 s, ~1201.7 measured worker-s; verify used 1 worker/setup 28.6 s, replay 3/setup 61.2 s. Same-budget memoized loadgroup fast run was 197.53 s. Worksteal reduces fixture duplication; test at comparable 16-worker budget before choosing a recipe.
- 2026-09-26T17:12:06Z (perf/test-latency): Verified tools/tt.parse_tests against the two-phase certified pilot plus TypeScript logs: 5908 executed tests counted (5707 non-N2 + 46 N2 + 155 TS), with the one skipped Python test excluded as designed. just --dry-run confirms test, hook-pre-push and ci-python expand the same shared two-phase Python command.
- 2026-09-26T17:15:53Z (perf/test-latency): parked (waiting on agent, dependency): After Codex completes the 16-worker scheduler and full-gate pilot on beliefs-1a27bc, Codex starts beliefs-f69178, runs three warm fast and two certified full gates, reviews the branch, and closes the P0 only if 90 s and 300 s targets hold.
  provenance: {"harness_session":"codex:01a0dd0c-461a-7d61-a6aa-c08f1b13c035","harness_session_source":"CODEX_SESSION_ID"}
