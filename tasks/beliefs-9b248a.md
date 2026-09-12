---
id: beliefs-9b248a
title: "The suite's slow tail is real pipeline executions: 97 call sites, 5-24s each"
status: idea
priority: 2
created: 2026-09-12T10:10:50Z
updated: 2026-09-12T10:10:50Z
depends: []
tags: [testing]
source: beliefs-f253a1
---

Measured 2026-09-12 under the fast loop (pytest -n 8 --dist=loadfile, N2 excluded, --durations=60; the run is recorded as target audit-durations): 4,438 tests in 171.46s. The 60 slowest tests are all executions of a real pipeline through the boundary (run_assessment / run_production / execute_*_run in test_replay, test_verify, test_boundary, test_cut15_workflows, test_assess, test_production, test_run_persistence), 5–24s each, 669s of worker time out of roughly 1,370 — about half the loop's compute, and the serial gate's median is 1066s. There are 97 such call sites across 17 files. No sleeps (one 0.25s) or network. Undetermined and therefore an idea: whether the cost is snakemake process startup per run (measure one run's breakdown first) or the work itself; whether read-only tests that each mint an identical baseline run (the test_r4_negative_* family builds the same run a in every test) can share a module-scoped one without changing what the conformance test asserts — several of these files are frozen cut evidence, so a change there is a supersession by citation, not an edit.
