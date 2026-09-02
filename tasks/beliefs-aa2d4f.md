---
id: beliefs-aa2d4f
title: Raise the N2 audit worker count to 24
status: todo
priority: 1
size: xs
created: 2026-09-02T03:41:06Z
updated: 2026-09-02T10:38:27Z
depends: []
tags: [performance, testing, n2]
---

Why: batching would save only about 7s of a 123s baseline and would stop proving that every check passes standalone. On this 16-core/32-thread host the baseline direction measured 154.56s at WORKERS=8, 89.47s at 16, and 79.13s at 24; the same constant governs the sabotage direction, for an estimated total saving of 130-150s.

Change: set tests/test_n2.py WORKERS from 8 to 24. Keep one pytest invocation per check, keep sabotage arms isolated, and do not add dynamic worker machinery.

Done when: both baseline and sabotage directions retain their standalone-check invariant; repeat N2 timing three times at 24 workers; run the Python repository gates.

## Notes

- 2026-09-02T10:38:27Z (perf/revise-test-tasks): Replaced unsound baseline batching with the measured one-line worker-count change.
