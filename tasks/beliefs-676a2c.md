---
id: beliefs-676a2c
title: "Deliver consolidate, move, and managed deletion"
status: doing
priority: 2
size: xl
owner: design/consolidate-family
created: 2026-08-31T00:38:27Z
updated: 2026-09-04T03:09:43Z
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
- 2026-09-04T01:54:05Z (design/consolidate-family): Task 5 review fix 1/5: source-missing used-domain pin now has direct typed-refusal coverage; 22 tests, Ruff, and Pyright pass.
- 2026-09-04T02:10:27Z (design/consolidate-family): Task 6 RED: missing relocation mint and writer helpers; GREEN: 117 focused tests plus 43 import regressions passed, Ruff and Pyright clean.
- 2026-09-04T02:25:05Z (design/consolidate-family): Task 6 review fix 1/5: import now publishes its exact prebuilt report operation; 117 focused tests and 44 import regressions pass, Ruff and Pyright clean.
- 2026-09-04T03:09:43Z (design/consolidate-family): Task 7: public destination-first move and frozen-row evidence pass 44 focused and 3149 full-suite tests; Ruff and Pyright clean.
