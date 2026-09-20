---
id: beliefs-95f461
title: A just test-boundary recipe for the inner loop
status: idea
priority: 2
created: 2026-09-20T20:54:49Z
updated: 2026-09-20T20:54:49Z
depends: []
tags: [testing]
agent: claude-code/opus
---

The url-retrieval lane's per-task focused runs skipped test_capability_boundary.py, test_permit_boundary.py and test_permit_entry_points.py, so a Task-4 regression surfaced only at Task 5's just test-fast. A ~15 s recipe running the three inventory modules (plus test_arm_staleness.py) that plans name for every task touching holdings/, corpus.py, root.py or session/ would catch it in-task without the full suite.
