---
id: beliefs-1b0827
title: "The N2 staleness probe checks that a pinned before-string still occurs, not that the sabotaged file still parses"
status: idea
priority: 2
created: 2026-09-16T06:31:02Z
updated: 2026-09-16T06:31:02Z
depends: []
tags: [conformance, testing]
agent: claude-code/claude-fable-5-1
---

Found at cut 31 (Task 8, cut 21's V8f): a pinned two-line before-block still occurred verbatim after a third line was appended below it, so the probe reported no drift, but substituting the block with 'pass' left the appended line orphaned — an IndentationError at collection, not a failure of the named check. Cut 31's guard (test_n2_cut31.py) adds an ast.parse over every mutated module for its own arms; the shared harness (tests/n2_arms.py / arm_staleness.py / test_n2.py) does not, so every earlier cut's arms remain exposed. Scope: add a parse check (and ideally an import check) to the shared audit so a syntax-breaking sabotage scores as its own verdict, never as 'sound'.
