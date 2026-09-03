---
id: beliefs-aa2d4f
title: Raise the N2 audit worker count to 24
status: done
priority: 1
size: xs
owner: perf/n2-workers-24
created: 2026-09-02T03:41:06Z
updated: 2026-09-03T22:58:08Z
depends: []
tags: [performance, testing, n2]
---

Why: batching would save only about 7s of a 123s baseline and would stop proving that every check passes standalone. On this 16-core/32-thread host the baseline direction measured 154.56s at WORKERS=8, 89.47s at 16, and 79.13s at 24; the same constant governs the sabotage direction, for an estimated total saving of 130-150s.

Change: set tests/test_n2.py WORKERS from 8 to 24. Keep one pytest invocation per check, keep sabotage arms isolated, and do not add dynamic worker machinery.

Done when: both baseline and sabotage directions retain their standalone-check invariant; repeat N2 timing three times at 24 workers; run the Python repository gates.

## Notes

- 2026-09-02T10:38:27Z (perf/revise-test-tasks): Replaced unsound baseline batching with the measured one-line worker-count change.
- 2026-09-03T14:53:47Z (perf/n2-workers-24): At WORKERS=24, three complete N2 runs passed 38/38 in 160.59s, 147.37s, and 229.02s (median 160.59s); the wide third-run variance is preserved in the evidence.
- 2026-09-03T14:56:27Z (perf/n2-workers-24): Full pytest gate could not run on the certified tuple: host Linux 7.2.2-arch1-1/ext4 ('async', 'barrier=1', 'commit=5', 'data=ordered') differs from the singleton allowlist's Linux 7.1.11-arch1-1 tuple; five test_arrival_modes cases failed closed with CapabilityUnavailable before the run was stopped. Ruff and Pyright pass.
- 2026-09-03T14:56:41Z (perf/n2-workers-24): Implemented and N2-verified; full pytest requires the certified Linux 7.1.11-arch1-1/ext4 tuple, but this host runs 7.2.2-arch1-1.
- 2026-09-03T22:39:47Z (perf/n2-workers-24): Blocker cleared: Atoms e71aefb certifies Linux 7.2.2-arch1-1 on the current ext4 tuple; recertification focused tests and static gates passed.
- 2026-09-03T22:58:08Z (perf/n2-workers-24): Per user direction, do not spend another full-suite cycle on this one-line test-harness change; test-performance and selection work continues separately. The already-running gate completed with 3073 passed and one wheel-build failure at tests/test_world_rules.py::test_shipped_rules_install_from_a_built_wheel.
- 2026-09-03T22:58:08Z (perf/n2-workers-24): Raised N2 workers to 24; three complete N2 runs passed, Ruff/Pyright passed, and the unrelated full-suite packaging failure was recorded for separate follow-up.
