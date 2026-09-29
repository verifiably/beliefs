---
id: beliefs-95f461
title: Document the focused boundary check set through test-one
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-09-20T20:54:49Z
updated: 2026-09-29T22:34:01Z
depends: []
parent: beliefs-287026
tags: [testing]
agent: claude-code/opus
---

Why: the cut-35 Task 4 capability-boundary regression was found only during Task 5's fast suite (docs/plans/2026-09-20-url-retrieval-execution-ledger.md, Task 4 reopened; fixed by b065711). The test-one recipe added in 7fd039f now accepts multiple module paths, so the missing piece is explicit selection guidance.

Done: add a compact instruction in AGENTS.md's repository gates telling tasks that touch holdings/, corpus.py, root.py or session/ to run their focused behavioral checks plus:
just test-one tests/test_capability_boundary.py tests/test_permit_boundary.py tests/test_permit_entry_points.py tests/test_arm_staleness.py

Use the existing timed recipe; do not add another runner or change frozen historical plans. Verify the documented command succeeds and records a test-one run. Record its observed duration without promising the original ~15 s estimate. Retain just test-fast before committing code changes.

Where to look: AGENTS.md Repository gates and Cut plans, justfile test-one, python/tests/test_front_door.py, the four named modules, and the cut-35 execution ledger.

Original capture (retained):
The url-retrieval lane's per-task focused runs skipped test_capability_boundary.py, test_permit_boundary.py and test_permit_entry_points.py, so a Task-4 regression surfaced only at Task 5's just test-fast. A ~15 s recipe running the three inventory modules (plus test_arm_staleness.py) that plans name for every task touching holdings/, corpus.py, root.py or session/ would catch it in-task without the full suite.

## Notes

- 2026-09-29T22:34:01Z (main): scope: scoped; todo P3/xs/low/direct to document and verify four boundary modules through existing test-one instead of adding a recipe; retained original capture; brief: docs/notes/2026-09-29-testing-backlog-brief.md
