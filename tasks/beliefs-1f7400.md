---
id: beliefs-1f7400
title: Deliver coordination and view kinds and discharge cut 14
status: doing
priority: 2
size: xl
owner: design/coordination-view-kinds
created: 2026-08-31T21:57:38Z
updated: 2026-09-02T11:30:48Z
depends: [beliefs-f5bb04, beliefs-07a924, beliefs-05575d, beliefs-30cfd7, beliefs-4b9383, beliefs-b84a76, beliefs-fb5c38, beliefs-17bc0e, beliefs-42a702, beliefs-bdacf1, beliefs-48c8b6, beliefs-a03506]
tags: [mutation-lane, coordination]
---

Implement the approved coordination-and-view-kinds design (docs/superpowers/specs/2026-08-31-coordination-and-view-kinds-design.md, frozen cut 14 at c07bf72 and approved amendment at 09b0b58) through docs/plans/2026-09-02-coordination-view-kinds.md. The ordered implementation chain is beliefs-f5bb04, beliefs-07a924, beliefs-05575d, beliefs-30cfd7, beliefs-4b9383, beliefs-b84a76, beliefs-fb5c38, beliefs-17bc0e, beliefs-42a702, beliefs-bdacf1, beliefs-48c8b6, beliefs-a03506. It delivers the two-method coordination family door, explicit live path/profile resolver, coordination contract and view-query parser, world/belief exclusion, 29 selected N2 units, the frozen no-aggregate phase inventory, results record, banking, and re-rank. W17 intent-position remains deferred to publish and no synthetic helper is built.

## Notes

- 2026-09-02T02:51:41Z (design/coordination-view-kinds): Started in /mnt/ssd/Dropbox/beliefs/.worktrees/design/coordination-view-kinds on branch design/coordination-view-kinds from main c3d8d1b. First phase is architectural brainstorming against frozen design c07bf72; no implementation begins before the reviewed design/plan gate.
- 2026-09-02T09:58:53Z (design/coordination-view-kinds): Brainstorming approved 2026-09-02. Design §11 records the two-method mapping-based writer API, path/profile-backed live resolver, closed contract/query shapes, world exclusion, targeted verification posture, and the evidence-driven removal of the intent-position helper from cut 14. Current-facing ledger, roadmap, world-addressing design, and user-layer design were corrected without rewriting frozen §9 or W17.
- 2026-09-02T10:03:06Z (design/coordination-view-kinds): API self-review correction approved: revise_coordination takes explicit (kind, address, *, predecessors, content). Coordination addresses intentionally omit kind, so inferring it from the predecessor set would make W17 continuity circular.
- 2026-09-02T10:12:06Z (design/coordination-view-kinds): Implementation amendment approved 2026-09-02. Writing the task-by-task plan next; no production code starts until that plan is reviewed and its child tasks are registered.
- 2026-09-02T11:00:48Z (design/coordination-view-kinds): Implementation plan drafted at docs/plans/2026-09-02-coordination-view-kinds.md with 12 chained child tasks (beliefs-f5bb04 through beliefs-a03506); self-review fixes split world-map and belief-input N2 evidence into 28 selected units and kept the full Python suite to one discharge run.
- 2026-09-02T11:30:48Z (design/coordination-view-kinds): Plan review amendment: fixed executor-factory reuse, runner imports/error handling, tolerant ordinary-door lookup, duplicate YAML detection, missing imports, cut work-root ignore, prior-arm import, and W17/W18 evidence. Accounting is now 29 selected units: W11 2, W12 1, W13 1, W17 14, W18 11.
