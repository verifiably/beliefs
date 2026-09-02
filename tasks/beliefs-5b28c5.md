---
id: beliefs-5b28c5
title: Remove the tautological minimal-boundary environment recapture
status: todo
priority: 0
size: s
created: 2026-09-02T03:41:06Z
updated: 2026-09-02T10:38:27Z
depends: []
tags: [performance, testing, confinement]
---

Why: capture_closure() costs 2.68-2.72s for 8,367 artifacts. _execute_run captures at boundary.py:386, projects that manifest into the locally minted recipe, then require_executing_environment(recipe.environment) at line 459 immediately captures again and compares the manifest with itself. Attribution found 44 captures totaling 119.99s in test_boundary.py; removing only the second capture reduced six boundary-running modules from 544.37s to 353.87s (35%) with 118 tests still passing.

Change: make an explicit design ruling that a recipe minted inside _execute_run uses its single caller capture, matching _execute_confined's one-capture rule. Add a direct check or N2 arm that makes the ruling load-bearing, then remove the tautological line 459 call. Preserve require_executing_environment for any path that executes a recipe received from elsewhere; do not add a test-only capture seam unless post-fix measurements still justify one.

Done when: the new coverage fails against the old double-capture behavior or otherwise directly enforces the one-capture ruling; externally supplied recipes still require an executing-environment check at their ingress; three before/after timings confirm the saving; the design/status docs and Python repository gates are current.

## Notes

- 2026-09-02T10:38:27Z (perf/revise-test-tasks): Rescoped from a test fixture seam to the measured product-level duplicate capture at boundary.py:459.
