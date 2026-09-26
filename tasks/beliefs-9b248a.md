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
updated: 2026-09-26T10:13:50Z
started: 2026-09-26T10:07:42Z
depends: []
tags: [testing]
source: beliefs-f253a1
---

Why: the current seven-day median is 1243s for just test and 190s for just test-fast. This has continued to slow development after the September audit. The 2026-09-26 pilot test_r4_negative_a took 15.25s; profiling showed repeated runtime closure capture and manifest identity work, alongside four Snakemake launches. Prior ruling on beliefs-5b28c5 requires two independent captures for minimal-v1, and frozen conformance evidence must not be edited casually.

Outcome: measure representative capture, identity and launch costs on the certified host; choose and implement the smallest verified improvement that preserves both captures, environment mutation detection and frozen evidence; remeasure representative tests and the fast loop against the same baseline; set a tracked test-time budget and keep the serial conformance gate. Do not declare the issue resolved just because a faster local recipe exists.

First step: draft and review the design in an isolated worktree, with concrete before/after checks and a realistic target. Related policy task is in ops.

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
