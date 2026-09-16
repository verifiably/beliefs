---
id: beliefs-705507
title: Open the lane and freeze the cut
status: done
priority: 3
size: s
complexity: mid
process: direct
owner: design/estimand-typing
created: 2026-09-12T22:33:24Z
updated: 2026-09-15T16:45:35Z
started: 2026-09-15T16:45:12Z
completed: 2026-09-15T16:45:12Z
depends: [beliefs-18b03d]
parent: beliefs-59f846
tags: [belief, contract]
model: claude-fable-5-1
plan: docs/superpowers/plans/2026-09-12-estimand-typing.md
step: "Task 0: Open the lane and freeze the cut"
---

## Notes

- 2026-09-12T23:50:22Z (design/estimand-typing): 2026-09-12 rule-6 reading: no kernel lane open (doing empty; the other worktrees are design/review branches), but an on-path lane is startable: world-read's head, world-resolution slice 3 (beliefs-46847c), is in ready. An off-path lane opens only when no on-path lane is startable, so estimand-typing does not open today. Re-read when slice 3 is in flight or blocked.
- 2026-09-12T23:50:22Z (design/estimand-typing): parked (waiting on agent, dependency): Re-read rule 6 once world-resolution slice 3 (beliefs-46847c) is in flight; then claim the cut number and freeze
- 2026-09-14T03:10:08Z (design/estimand-typing): Rule-6 re-read 2026-09-13 after slice 3 merged at cut 27: an on-path lane is startable again (slice 4, beliefs-0e523a, opened in .worktrees/world-resolution-slice-4), so estimand-typing still does not open. Re-read when slice 4 is in flight or blocked; branch is 26 commits behind main and needs a rebase before opening.
- 2026-09-15T14:05:55Z (design/estimand-typing): Rule 6 re-read 2026-09-15 after cut 30: tier 1 has no on-path boundary; the off-path lane may open — rebase onto main first.
- 2026-09-15T16:27:04Z (design/estimand-typing): 2026-09-15 gate added: Step 3 (git mv of the draft into docs/designs, the freeze) waits on beliefs-18b03d, the natural-systems worked example on main, whose finding amends the draft pre-freeze. At the rebase onto main, swap the stale dependency: tasks dep beliefs-705507 --rm beliefs-46847c --on beliefs-18b03d (slice 3 merged at cut 27; 18b03d exists only on main until then).
- 2026-09-15T16:45:12Z (design/estimand-typing): Process direct: plan Task 0's three steps settle the work; the cut document follows cut 26's shape with cut 30's header lines.
- 2026-09-15T16:45:12Z (design/estimand-typing): Lane admitted under rule 6 (no kernel lane open, no on-path boundary after cut 30); cut 31 claimed after cut 30's runner; cut document written on cut 26's shape with cut 30's header; design moved into docs/designs as table Q's owner and its status set to frozen; Q registered in test_designs_corpus (tables, owner, row regexes, count words); README rows and counts (206 rows, nineteen tables, sixty-seven documents); guide cites the design and the cut; plan's arm count corrected to twenty-six.
- 2026-09-15T16:45:35Z (design/estimand-typing): cut 31 frozen at c2a2211c2d9a0889a59e7892dcb71f2008e20e46, sha256 3cd4409dd08d5b121d3f62bfaaa00e3d553335d6a54e7657471c70677854d93f
