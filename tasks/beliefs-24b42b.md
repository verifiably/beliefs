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
updated: 2026-09-15T10:24:47Z
started: 2026-09-15T09:53:48Z
depends: []
parent: beliefs-d248ba
tags: [world-read]
spec: docs/superpowers/specs/2026-09-15-world-resolution-slice-6-design.md
---

Slice 2b makes consolidate refuse two source replicas whose identifier maps or correction histories differ (HistoryDisagreement). Reconciling them — which history survives, how tokens merge, whether the union of held addresses is the redirect set — needs its own design (slice 2b section 7).

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Slice 2b section 7 and relocation._reconcile intentionally refuse unequal identifier maps/histories. Choosing survivor history, token reconciliation and redirect-set semantics is the task itself and remains undesigned.
- 2026-09-15T09:53:40Z (main): Process planned: slice 2b §7 defers survivor-history, token-merge and redirect-set semantics to their own design; nothing settles them yet. Opened 2026-09-15 as the world-read lane head after cut 29 (on-path row 1); once in flight, rule 6 admits estimand-typing Task 0 (beliefs-705507) as the second lane.
- 2026-09-15T10:03:31Z (design/world-resolution-slice-6): Design drafted 2026-09-15 in .worktrees/world-resolution-slice-6 (approach A: keep's chain is the spine, other's divergent suffix absorbed into one consolidation entry; prefix fast-forwards; maps still refuse). Spec held unstaged pending the checkout's design-doc rule; under review, not frozen.
- 2026-09-15T10:03:31Z (design/world-resolution-slice-6): parked (waiting on user, review): Review the slice 6 design spec; on approval invoke writing-plans
- 2026-09-15T10:24:47Z (design/world-resolution-slice-6): 2026-09-15 first review's two findings taken: reconciliation absorbs only unheld events (idempotent over an interrupted re-run, per the families design's recovery table), one token is one event across chains, fast-forward fixture is a B→C→B round trip. Spec committed at 65d6678 with AGENTS.md naming the doc directories; still parked for review.
