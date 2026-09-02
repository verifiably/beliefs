---
id: beliefs-aa2d4f
title: Batch the N2 green baseline audit
status: todo
priority: 1
size: m
created: 2026-09-02T03:41:06Z
updated: 2026-09-02T03:41:06Z
depends: []
tags: [performance, testing, n2]
---

Why: the N2 audit consumed 281.70s of a 949.29s Python run; 120.61s was the unsabotaged baseline launching one pytest process per unique check.

Change: run all unique baseline checks in one pytest invocation. If it fails, rerun checks individually to preserve precise diagnostics. Keep sabotage arms isolated because aggregation can hide vacuous or uncollected checks.

Done when: the two N2 assertions retain their current guarantees and pass; record three before/after timings for tests/test_n2.py; show a material median reduction; run the Python repository gates.
