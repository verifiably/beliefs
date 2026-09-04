---
id: beliefs-676a2c
title: "Deliver consolidate, move, and managed deletion"
status: doing
priority: 2
size: xl
owner: design/consolidate-family
created: 2026-08-31T00:38:27Z
updated: 2026-09-04T01:44:06Z
depends: []
tags: [migration, mutation, world]
---

Outcome: Beliefs completes the stored-record mutation family with consolidate, cross-corpus move, and managed deletion semantics, including the assigned run-boundary and formal-model ride-alongs.

Acceptance evidence: Freeze a mutation-lane cut; implement the family through the governed write boundary and world registry; prove digest invariance, history preservation, deletion negatives, replica behavior, explicit-import audit behavior, and retraction-graph ordering; discharge the roadmap rows; update current status; and pass all repository gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `consolidate-family`, `run-boundary-remainder`, and `formal-model-remainder`; `docs/designs/2026-08-19-family-adapters-design.md`; and `docs/designs/2026-08-03-correction-lifecycle-design.md`.

Uncertainty: The outcome is buildable, but the exact cut and interaction between consolidate and deletion need a dedicated design and plan.

## Notes

- 2026-09-04T00:01:51Z (design/consolidate-family): Banked the world-changing families design and froze relocation cut 16; implementation remains open.
- 2026-09-04T00:25:57Z (design/consolidate-family): Review round 1 corrected the ledger's current-state date and every inbound dated anchor.
- 2026-09-04T00:53:07Z (design/consolidate-family): Task 2 landed in-memory/stored record-mutation grammar with reviewed storage-reader coverage.
- 2026-09-04T01:04:04Z (design/consolidate-family): Task 3: added the explicit relocation refusal hierarchy and focused inheritance test; pytest, Ruff, and Pyright pass.
- 2026-09-04T01:16:26Z (design/consolidate-family): Task 4: lock-held add, replace, and delete seams passed 49 corpus-write tests; Ruff and Pyright clean.
- 2026-09-04T01:28:31Z (design/consolidate-family): Task 4 review fix 1/5: replacement-time deprecated-ID collisions now map to CollisionRefused; 50 corpus-write tests pass.
- 2026-09-04T01:44:06Z (design/consolidate-family): Task 5 RED: missing beliefs.relocation; GREEN: 21 focused relocation/accessor tests, Ruff, and Pyright pass.
