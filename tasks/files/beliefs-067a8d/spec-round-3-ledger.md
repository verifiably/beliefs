# Spec round 3 rulings — beliefs-067a8d

Review: claude-code/claude-opus-5-5 scoped re-review of frozen 2cee097 (spec-round-3-report.md). Controller: claude-code/claude-opus-5-5 (main session).
All 5 findings accepted and corrected in the next frozen revision; none deferred.

- Ruling N1: accept. Step 3 replaces just --set markers with the nodes route-test pattern: fixture checkout (justfile, tools/tt, pre-push), stub uv/npm/npx/tasks/host-budget/ssh on a key-by-key PATH plus stub ops-check/ops-docs, events log, FAIL_STEP env selector; no case runs a real suite or uses cwd=ROOT. Why: --set does not reach nested just, so markers would pass vacuously or recurse into the suite. Cost (if wrong): a larger fixture to maintain.
- Ruling M1: accept; baseline uses PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }-rfEs", preserving the host value and the default fE summary.
- Ruling M2: accept; broad_targets name test runs against a fixture policy (can fail pre-activation) and the live file; activation commit's focused list names test_front_door.py, the workflow contract tests and any README/docs-reading tests it touches; misplaced sentence moved.
- Ruling M3: accept; step 4 states the widened trigger and the main-only hook declaration as separate facts and rewrites the stale comment and AGENTS Remote CI line.
- Ruling M4: accept; any other ci_suite_refs shape fails the coverage test until specified.
