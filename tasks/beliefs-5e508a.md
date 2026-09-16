---
id: beliefs-5e508a
title: "Task 0: Open the lane and freeze the cut"
status: done
priority: 2
size: s
complexity: low
process: direct
owner: design/composite-claim
created: 2026-09-13T01:56:09Z
updated: 2026-09-16T11:16:59Z
started: 2026-09-16T10:43:08Z
completed: 2026-09-16T11:16:59Z
depends: []
parent: beliefs-4bcf88
tags: [design]
plan: docs/superpowers/plans/2026-09-12-composite-claims.md
step: "Task 0: Open the lane and freeze the cut"
---

## Notes

- 2026-09-13T09:05:03Z (design/composite-claim): parked (waiting on agent, dependency): Open the lane once estimand-typing has merged into main and rule 6 admits an off-path lane; then claim the cut number and freeze
- 2026-09-16T09:22:58Z (design/composite-claim): 2026-09-16: estimand-typing merged into main at d25c7af1ea81346c7db0a77de64db44403459b37 (cut 31 discharged). Task 0's remaining gates: rebase design/composite-claim onto main, then re-read rule 6 (no on-path lane; this would be the only open kernel lane), then claim the next cut number (32 unless another worktree claims first) and freeze.
- 2026-09-16T10:43:08Z (design/composite-claim): process: direct — the plan's Task 0 names every step; the one judgment (rule 6) is read from the roadmap
- 2026-09-16T10:43:08Z (design/composite-claim): claimed by claude-code/claude-fable-5-1; step 1 done: rebased design/composite-claim onto main 8aa5903 (10 commits, clean) and just setup ran; cut number scan over ., audio-baseline, composite-claim tops at 31 so this lane claims 32
- 2026-09-16T11:16:59Z (design/composite-claim): Lane admitted under rule 6 at main 8aa5903 (no on-path boundary, no other kernel lane open); branch rebased onto main and set up; cut 32 claimed after scanning every worktree (highest 31); the design moved into docs/designs as table U's owner with its status rewritten; the pre-freeze drift review's 43 findings taken first; conformance cut 32 frozen 2026-09-16 with U1-U10 selected in full, 10 units, 26 arms, PREFIX_RUNNERS cut31; table U registered, README and guide updated; test_designs_corpus, test_check_guide, test_project_root green
