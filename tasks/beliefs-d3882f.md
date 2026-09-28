---
id: beliefs-d3882f
title: Take test_n2.py's serial tail off the per-change path
status: todo
priority: 1
size: m
complexity: mid
process: planned
created: 2026-09-28T10:28:44Z
updated: 2026-09-28T10:28:44Z
depends: []
tags: [testing]
source: ops-a5a7ef
agent: claude-code/claude-opus-5-5
---

ops docs/reports/2026-09-28-test-ci-audit-baselines.md §3.1: the full suite is the ~190 s parallel loop plus ~15 min of test_n2.py and TS, paid in 42 hand-run suites and 29 pushes (25.5 h) over 09-05..09-24. Options: parallelize N2's pool; run N2 only when its inputs change; CI carries it (see the act design's ci_suite_refs).
