---
id: beliefs-89542c
title: "arm_staleness measures only an arm's before block, so a stale after scores uncollected"
status: idea
priority: 2
created: 2026-09-16T20:09:06Z
updated: 2026-10-09T14:03:51Z
depends: [beliefs-f64cf1]
parent: beliefs-287026
tags: [conformance, testing]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
---

The shared staleness probe (tests/arm_staleness.py, tests/test_arm_staleness.py) asserts that each arm's pinned `before` string still occurs in its module; it never checks the `after`. Cut 20's D8a was found at cut 32 Task 8 with a stale `after` — it restated the domain parser's optional-field set literally, and Task 2 added `edges` to _CONTRACT_OPTIONAL — so the sabotaged parser refused a fixture, every tests/acceptance conftest failed to import, and the arm scored `uncollected` (pytest exit 4), which is not a failing check. A stale `after` therefore surfaces only as an uncollected arm in a later chain run, never as staleness. Extend the probe to apply each `after` and assert the module still loads and the pinned text is reachable.

## Notes

- 2026-09-29T22:34:00Z (main): scope: briefed; verified before-only detector and existing uncollected refusal; research beliefs-aa9f88 will compare parse/import/collection without duplicating beliefs-1b0827; brief: docs/notes/2026-09-29-testing-backlog-brief.md
- 2026-10-02T16:52:50Z (research/n2-preflight-pilot): pilot beliefs-aa9f88: faithful current D8a missing-edges replacement passes ast.parse and direct module import but named-check collection refuses exit4 through fixture profiles; control collects one test. Collection1.074-2.371s per single process, nine probes13.96s incl hydration. Recommendation: ready for later scope using existing syntax/N2 cost tasks; no gate implemented. Brief docs/notes/2026-09-29-testing-backlog-brief.md.
- 2026-10-09T14:03:50Z (main): scope: briefed; depends on beliefs-f64cf1 for placement: ~895 arm declarations across 43 guards at the pilot's 1.07–2.37 s per collection is ~16–35 serial min, so no always-on fast-suite collection; open choice is changed-target-module preflight vs N2-phase; brief: docs/notes/2026-09-29-testing-backlog-brief.md
