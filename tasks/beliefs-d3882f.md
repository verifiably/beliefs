---
id: beliefs-d3882f
title: Take test_n2.py's serial tail off the per-change path
status: todo
priority: 1
size: m
complexity: mid
process: planned
created: 2026-09-28T10:28:44Z
updated: 2026-09-29T23:11:03Z
depends: []
tags: [testing]
source: ops-a5a7ef
agent: claude-code/claude-opus-5-5
---

ops docs/reports/2026-09-28-test-ci-audit-baselines.md §3.1: the full suite is the ~190 s parallel loop plus ~15 min of test_n2.py and TS, paid in 42 hand-run suites and 29 pushes (25.5 h) over 09-05..09-24. Options: parallelize N2's pool; run N2 only when its inputs change; CI carries it (see the act design's ci_suite_refs).

## Notes

- 2026-09-29T23:11:03Z (main): premise re-checked 2026-09-29 against main 35ad634: two of the three options have landed. beliefs-9b248a (09-26) put the complete gate at 236-237 s with N2 at ~174 s, not the ~15 min of the 09-05..09-24 baseline; beliefs-d4dc85 (7fd039f) takes N2 off test-fast and off pushes to origin/main, where CI carries it. N2 is still paid on every push to a non-main ref and on hand-run just test. Remaining option: run N2 only when its inputs change; the cost itself is beliefs-f64cf1's.
