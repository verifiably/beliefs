---
id: beliefs-89542c
title: "arm_staleness measures only an arm's before block, so a stale after scores uncollected"
status: idea
priority: 2
created: 2026-09-16T20:09:06Z
updated: 2026-09-16T20:09:06Z
depends: []
tags: [conformance, testing]
source: docs/plans/2026-09-16-conformance-cut-32-results.md
---

The shared staleness probe (tests/arm_staleness.py, tests/test_arm_staleness.py) asserts that each arm's pinned `before` string still occurs in its module; it never checks the `after`. Cut 20's D8a was found at cut 32 Task 8 with a stale `after` — it restated the domain parser's optional-field set literally, and Task 2 added `edges` to _CONTRACT_OPTIONAL — so the sabotaged parser refused a fixture, every tests/acceptance conftest failed to import, and the arm scored `uncollected` (pytest exit 4), which is not a failing check. A stale `after` therefore surfaces only as an uncollected arm in a later chain run, never as staleness. Extend the probe to apply each `after` and assert the module still loads and the pinned text is reachable.
