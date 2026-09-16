---
id: beliefs-aa27da
title: Complete the correction lifecycle
status: todo
priority: 3
size: xl
complexity: high
process: planned
created: 2026-08-31T00:38:28Z
updated: 2026-09-16T22:47:03Z
depends: [beliefs-676a2c]
tags: [migration, mutation, correction]
---

Outcome: Beliefs completes standing-retraction evaluation, conflict semantics, semantic snapshots, coverage, audit reporting, and correction succession over the delivered consolidate family.

Acceptance evidence: Consolidate landed at cut 16 and deletion at cut 18. Design and freeze the correction cut; implement and test C7, C8, C9, C3’s coverage clauses and C10’s audit arm including uncovered corpora, exact-state receipts, mount and raw-write negatives; update the adoption ledger and roadmap; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `correction-remainder`; `docs/designs/2026-08-03-correction-lifecycle-design.md`; and the cut-5 correction accounting.

Uncertainty: Consolidate’s prerequisite is discharged; the semantic-snapshot kind and evaluator are this outcome's still-unplanned work.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: The correction design fixes standing and succession guarantees, and consolidate/deletion prerequisites landed, but the semantic-snapshot kind/evaluator and route standing must still compose coverage, exact-state receipts, import and audit outcomes. No concrete correction cut resolves that integration.
- 2026-09-16T22:47:03Z (main): 2026-09-16: process planned — roadmap tier-1 off-path row 1 with no lane open after cut 32; the stored semantic-snapshot kind, its evaluator and route standing are undesigned, so a slice design and cut freeze precede code. Cut 32's finding (retraction filtering the identification column inherits) and the src-touching cut-31/32 follow-ups (0521da, 1dd03f, 010c6e, b1245d) ride with this cut.
