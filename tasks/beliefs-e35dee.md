---
id: beliefs-e35dee
title: "A main commit can make a frozen N2 arm vacuous, unseen until the next cut's chained run"
status: todo
priority: 2
size: s
complexity: mid
created: 2026-09-24T16:14:31Z
updated: 2026-09-24T16:14:31Z
depends: []
tags: [conformance, testing]
source: docs/plans/2026-09-24-conformance-cut-40-results.md §3.1
agent: claude-code/claude-opus-5-5
---

Main commit 70ff54e (beliefs-40e593) made cut 19's frozen arm J2i vacuous: the durable port gained a second mark_root_unresolved, so J2i's single-site sabotage no longer failed its checks. Nothing noticed on main; it surfaced only when cut 40's runner chained every prior cut, a day later, and cost a bisect and a repair on the cut-40 branch (567edbf, beliefs-50067c). The pre-push gate runs the portable suite, which cannot see tests/acceptance (memory portable-suite-cannot-see-acceptance), and CI skips capability-dependent tests. Decide a cheap net: e.g. a recipe that runs every live test_n2_cut*.py guard's sabotage audit (the chain's N2 phases only, not the full acceptance phases) and a rule that kernel fixes to src/ run it before merge; or run the latest cut's chained runner as part of a src/ change's pre-merge checks. Measure the N2-only cost first.
