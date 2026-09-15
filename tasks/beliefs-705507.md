---
id: beliefs-705507
title: Open the lane and freeze the cut
status: todo
priority: 3
size: s
complexity: mid
created: 2026-09-12T22:33:24Z
updated: 2026-09-15T16:27:04Z
depends: [beliefs-46847c]
parent: beliefs-59f846
tags: [belief, contract]
plan: docs/superpowers/plans/2026-09-12-estimand-typing.md
step: "Task 0: Open the lane and freeze the cut"
---

## Notes

- 2026-09-12T23:50:22Z (design/estimand-typing): 2026-09-12 rule-6 reading: no kernel lane open (doing empty; the other worktrees are design/review branches), but an on-path lane is startable: world-read's head, world-resolution slice 3 (beliefs-46847c), is in ready. An off-path lane opens only when no on-path lane is startable, so estimand-typing does not open today. Re-read when slice 3 is in flight or blocked.
- 2026-09-12T23:50:22Z (design/estimand-typing): parked (waiting on agent, dependency): Re-read rule 6 once world-resolution slice 3 (beliefs-46847c) is in flight; then claim the cut number and freeze
- 2026-09-14T03:10:08Z (design/estimand-typing): Rule-6 re-read 2026-09-13 after slice 3 merged at cut 27: an on-path lane is startable again (slice 4, beliefs-0e523a, opened in .worktrees/world-resolution-slice-4), so estimand-typing still does not open. Re-read when slice 4 is in flight or blocked; branch is 26 commits behind main and needs a rebase before opening.
- 2026-09-15T14:05:55Z (design/estimand-typing): Rule 6 re-read 2026-09-15 after cut 30: tier 1 has no on-path boundary; the off-path lane may open — rebase onto main first.
- 2026-09-15T16:27:04Z (design/estimand-typing): 2026-09-15 gate added: Step 3 (git mv of the draft into docs/designs, the freeze) waits on beliefs-18b03d, the natural-systems worked example on main, whose finding amends the draft pre-freeze. At the rebase onto main, swap the stale dependency: tasks dep beliefs-705507 --rm beliefs-46847c --on beliefs-18b03d (slice 3 merged at cut 27; 18b03d exists only on main until then).
