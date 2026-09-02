---
id: beliefs-73be28
title: Deliver the full workflow surface
status: done
priority: 1
size: xl
owner: design/workflow-surface
created: 2026-08-31T00:38:27Z
updated: 2026-09-02T17:03:45Z
depends: [beliefs-739255, beliefs-ed3dc8, beliefs-f8bcbf, beliefs-0e6e32, beliefs-e4d001, beliefs-97f740, beliefs-f5bd5d, beliefs-9e5ee1, beliefs-067ac2, beliefs-d52e6c, beliefs-03cafe, beliefs-4dd087, beliefs-d1464c, beliefs-3b9f26, beliefs-f624d4, beliefs-40769d, beliefs-89d663, beliefs-2e7c1a, beliefs-3895aa, beliefs-bbb529, beliefs-59f1e0, beliefs-a45800, beliefs-a8b85e]
tags: [migration, execution, workflow]
---

Outcome: Beliefs supports the designed multi-rule, family, wildcard, definition-equality, and multi-product workflow surface beyond the cut-3 minimal adapter.

Acceptance evidence: Approve and freeze a cut after run confinement (cut 15, frozen 2026-09-01 in `docs/superpowers/specs/2026-09-01-workflow-surface-design.md`); implement the full workflow declarations and run paths without weakening confinement; discharge R2, R16, R20 and R21 in full and R23's local basis/composition disagreement -- NOT its replay-cardinality arm, which discharged at cut 3 -- with positive and negative tests; update the adoption ledger and roadmap, rewording their R23 assignment to name the local-disagreement clause; discharge after cut 14, naming cut14_acceptance.py; and pass the complete repository gates.

Plan: `docs/plans/2026-09-01-workflow-surface.md`, 22 chained tasks (beliefs-ed3dc8 .. beliefs-a8b85e). This task closes when the last of them does.

Sources: `docs/superpowers/specs/2026-09-01-workflow-surface-design.md`; `docs/plans/2026-08-29-implementation-roadmap.md` `workflow-surface`; `docs/designs/2026-08-02-computation-reproducibility-design.md` 6.2-6.4; cut 3's deferred workflow accounting; cut 5 3.2 and 6.1 item 2 for the R23 deferral.

## Notes

- 2026-09-01T14:32:53Z (design/workflow-surface): Design written and cut 15 frozen in docs/superpowers/specs/2026-09-01-workflow-surface-design.md; 17 selected + 8 labeled units; awaiting spec review before the implementation plan
- 2026-09-01T15:47:43Z (design/workflow-surface): Correction to the note above: cut 15 selects 16 units (R2 2, R16 10, R20 2, R21 2) + 8 labeled = 24. R23 is not selected -- its replay-cardinality arm discharged at cut 3; the residual local basis/composition clause belongs to run-boundary-remainder, and the ledger/roadmap assignment to workflow-surface is stale. Cut 15 discharges after cut 14 and names cut14_acceptance.py.
- 2026-09-01T20:53:55Z (design/workflow-surface): Supersedes the two notes above on R23: cut 15 selects 17 units (R2 2, R16 10, R20 2, R21 2, R23 1) + 8 labeled = 25. R23's selected unit is the local basis/composition disagreement, whose owner is workflow-surface as the run-family boundary (cut 5 3.2); the earlier run-boundary-remainder assignment was wrong -- cut 5 refuses respelling it as import behavior. Replay cardinality stays discharged at cut 3 and runs only as regression coverage.
- 2026-09-01T21:13:16Z (design/workflow-surface): Split into 22 plan tasks (beliefs-ed3dc8 .. beliefs-a8b85e), chained in plan order and joined to this task by depends; plan at docs/plans/2026-09-01-workflow-surface.md
- 2026-09-02T02:51:09Z (design/workflow-surface): Workflow-surface pause point: Tasks 1-21 landed through 6383a71; Task 22 is deliberately unstarted and now depends on beliefs-1f7400. Resume on design/workflow-surface only after cut 14 discharges, sync main, run the serialized cut-15 acceptance command, then bank and close Task 22 before this parent.
- 2026-09-02T15:14:52Z (design/workflow-surface): Resumed after cut 14: merged main 26b248b, resolving the composed-receipt test conflicts before cut-15 discharge and banking.
- 2026-09-02T15:52:23Z (design/workflow-surface): Merged cut 14 and resolved six conflicts; repaired stale composed-receipt callers plus five frozen cut-13 mutation seams. Focused conflict tests, affected cut-13/cut-15 sabotage audits, ruff, pyright, and tasks check pass.
- 2026-09-02T17:03:45Z (design/workflow-surface): Workflow surface delivered; cut 15 discharged at 17 selected + 8 labeled units
