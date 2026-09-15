---
id: beliefs-24b42b
title: Reconcile divergent identifier-correction histories at consolidate
status: doing
priority: 3
size: m
complexity: high
process: planned
owner: design/world-resolution-slice-6
created: 2026-09-11T11:42:27Z
updated: 2026-09-15T11:21:54Z
started: 2026-09-15T09:53:48Z
depends: []
parent: beliefs-d248ba
tags: [world-read]
spec: docs/superpowers/specs/2026-09-15-world-resolution-slice-6-design.md
plan: docs/superpowers/plans/2026-09-15-world-resolution-slice-6.md
---

Slice 2b makes consolidate refuse two source replicas whose identifier maps or correction histories differ (HistoryDisagreement). Reconciling them — which history survives, how tokens merge, whether the union of held addresses is the redirect set — needs its own design (slice 2b section 7).

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Slice 2b section 7 and relocation._reconcile intentionally refuse unequal identifier maps/histories. Choosing survivor history, token reconciliation and redirect-set semantics is the task itself and remains undesigned.
- 2026-09-15T09:53:40Z (main): Process planned: slice 2b §7 defers survivor-history, token-merge and redirect-set semantics to their own design; nothing settles them yet. Opened 2026-09-15 as the world-read lane head after cut 29 (on-path row 1); once in flight, rule 6 admits estimand-typing Task 0 (beliefs-705507) as the second lane.
- 2026-09-15T10:03:31Z (design/world-resolution-slice-6): Design drafted 2026-09-15 in .worktrees/world-resolution-slice-6 (approach A: keep's chain is the spine, other's divergent suffix absorbed into one consolidation entry; prefix fast-forwards; maps still refuse). Spec held unstaged pending the checkout's design-doc rule; under review, not frozen.
- 2026-09-15T10:03:31Z (design/world-resolution-slice-6): parked (waiting on user, review): Review the slice 6 design spec; on approval invoke writing-plans
- 2026-09-15T10:24:47Z (design/world-resolution-slice-6): 2026-09-15 first review's two findings taken: reconciliation absorbs only unheld events (idempotent over an interrupted re-run, per the families design's recovery table), one token is one event across chains, fast-forward fixture is a B→C→B round trip. Spec committed at 65d6678 with AGENTS.md naming the doc directories; still parked for review.
- 2026-09-15T10:50:28Z (design/world-resolution-slice-6): parked (waiting on user, review): Review the implementation plan docs/superpowers/plans/2026-09-15-world-resolution-slice-6.md; on approval execute Tasks 1-8 in this worktree (subagent-driven)
- 2026-09-15T11:00:35Z (design/world-resolution-slice-6): 2026-09-15 plan review's three findings taken: ActReport.event_token (not .intent); reconcile takes Sequence[dict]; arm_staleness.re_targeted_rows reads RETARGETED_ROWS (Task 6, cut boundary); _COUNT_WORDS gains 65 (Task 1).
- 2026-09-15T11:16:42Z (design/world-resolution-slice-6): Second plan review fixed: Tasks 6–7 import cut 25's override set as CUT25_RETARGETED_ROWS in guards 26–30, preserving RETARGETED_ROWS for local overrides. Executed the planned detector test and checked all five importing guards in memory; all passed. Plan correction only; implementation children remain todo.
- 2026-09-15T11:20:46Z (design/world-resolution-slice-6): claimed by Codex SDD controller; user approved plan execution 2026-09-15; existing worktree reused
- 2026-09-15T11:21:00Z (design/world-resolution-slice-6): claimed by Codex SDD controller, pid 1349573
- 2026-09-15T11:21:54Z (design/world-resolution-slice-6): cut number scan 2026-09-15: highest claimed across worktrees is 29; this cut is 30
