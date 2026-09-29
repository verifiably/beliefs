---
id: beliefs-aa9f88
title: Determine whether a collection preflight catches stale N2 replacements affordably
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-09-29T22:33:07Z
updated: 2026-09-29T22:33:07Z
depends: []
parent: beliefs-287026
tags: [testing]
source: docs/notes/2026-09-29-testing-backlog-brief.md
agent: codex
---

Question: Can a bounded preflight detect syntactically valid stale sabotages that break test collection, beyond the ast.parse check already owned by beliefs-1b0827?

Where to start: docs/notes/2026-09-29-testing-backlog-brief.md; python/tests/arm_staleness.py::stale_arms; python/tests/test_n2.py::_sabotage, _run_check and audit; python/tests/acceptance/test_n2_cut20.py's D8a override; docs/plans/2026-09-16-conformance-cut-32-results.md §3.2–3.3; beliefs-1b0827, beliefs-e35dee and beliefs-f64cf1.

Bound: In an isolated worktree, compare parse-only, module import, and collection of the arm's named checks on one healthy control, one syntax-breaking mutation, and the documented D8a stale-after case (or a faithful minimal reproduction if historical dependencies prevent replay). Use copied packages, never live source mutation. Run through just test-one and record capability/environment limits. No full-arm sweep, implementation rollout, new gate or benchmark campaign.

Expected result: Record which probes distinguish each case, elapsed cost for this pilot, limitations of import versus pytest collection, and a recommendation with acceptance criteria on this task and in the brief. Coordinate with the existing syntax, vacuity and cost tasks rather than duplicate them. This is a measurement and recommendation task, not a promise that collection proves sabotage correctness.

Ideas it wakes: On completion, run tasks note beliefs-89542c with the finding in the same commit as the result; update the brief so a later scope pass can reconsider the idea.
