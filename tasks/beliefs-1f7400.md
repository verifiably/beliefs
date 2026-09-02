---
id: beliefs-1f7400
title: Deliver coordination and view kinds and discharge cut 14
status: doing
priority: 2
size: xl
owner: design/coordination-view-kinds
created: 2026-08-31T21:57:38Z
updated: 2026-09-02T10:03:06Z
depends: []
tags: [mutation-lane, coordination]
---

Implement the frozen coordination-and-view-kinds design (docs/superpowers/specs/2026-08-31-coordination-and-view-kinds-design.md, cut 14 frozen at c07bf72) as amended by §11 on 2026-09-02: the two-method coordination family door on CorpusWriter; the explicit path/profile-backed coordination resolver; coordination_facet_malformed; the coordination contract compiled into ProfileSpec with stored.WORLD_KINDS; the science.view-query.v1 parser and admission; W11, W12, W18, W17 except its intent-position clause, and W13’s two-projects negative; cut14_acceptance.py with the frozen prefix inventory and cut-5 citation; unscoped-note fixture moves; results record and re-rank. W17’s intent-position evidence stays with publish, its first operational consumer; cut 14 builds no synthetic helper. Joins the mutation lane at the next re-rank and runs on the certified volume beside the checkout.

## Notes

- 2026-09-02T02:51:41Z (design/coordination-view-kinds): Started in /mnt/ssd/Dropbox/beliefs/.worktrees/design/coordination-view-kinds on branch design/coordination-view-kinds from main c3d8d1b. First phase is architectural brainstorming against frozen design c07bf72; no implementation begins before the reviewed design/plan gate.
- 2026-09-02T09:58:53Z (design/coordination-view-kinds): Brainstorming approved 2026-09-02. Design §11 records the two-method mapping-based writer API, path/profile-backed live resolver, closed contract/query shapes, world exclusion, targeted verification posture, and the evidence-driven removal of the intent-position helper from cut 14. Current-facing ledger, roadmap, world-addressing design, and user-layer design were corrected without rewriting frozen §9 or W17.
- 2026-09-02T10:03:06Z (design/coordination-view-kinds): API self-review correction approved: revise_coordination takes explicit (kind, address, *, predecessors, content). Coordination addresses intentionally omit kind, so inferring it from the predecessor set would make W17 continuity circular.
