---
id: beliefs-9b248a
title: Cut Beliefs test iteration cost while preserving conformance
status: todo
priority: 0
size: l
complexity: high
process: planned
created: 2026-09-12T10:10:50Z
updated: 2026-09-26T10:06:44Z
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
