---
id: beliefs-676a2c
title: "Deliver consolidate, move, and managed deletion"
status: doing
priority: 2
size: xl
owner: design/consolidate-family
created: 2026-08-31T00:38:27Z
updated: 2026-09-04T20:43:28Z
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
- 2026-09-04T03:45:11Z (design/consolidate-family): Task 7 review fix: writer-routed report minting, pre-intent destination add preflight, exact canonical occupancy, real published-snapshot belief evidence, exact report-op and symlink lock coverage; focused 47 and full 3152 pass.
- 2026-09-04T04:35:40Z (design/consolidate-family): Task 8: retract and supersede now re-resolve create-only targets under the lock; real moved-away rows and canonical local-absence taxonomy pass (3154 Python tests).
- 2026-09-04T05:21:33Z (design/consolidate-family): Task 9: consolidate now reconciles duplicate locations with tagged-basis, replacement-preflight, root-local report, retraction-replica, and ungoverned-kind coverage; 3180 Python tests pass.
- 2026-09-04T06:05:56Z (design/consolidate-family): Task 9 review fix: replacement collisions now refuse before intents and canonical-equal lineage routes retain decoded canonical mappings; 3182 Python tests pass.
- 2026-09-04T06:20:35Z (design/consolidate-family): Task 10: test-local run-then-raise seams pin all move/consolidate durable prefixes, data-only recovery, fresh SHA-256 intent digests, and exact T3 residue; 34 focused tests pass, Ruff and Pyright clean.
- 2026-09-04T07:39:04Z (design/consolidate-family): Task 11: durable cut-16 acceptance and 19 N2 arms normalize to the frozen 11 units; certified runner exited 0, full Python suite passed 3216 tests, Ruff and Pyright clean. Parent remains open for managed deletion and discharge.
- 2026-09-04T09:35:55Z (design/consolidate-family): Task 11 review fix: six vacuous evidence gaps now have exact durable assertions and eight new sabotages (27 arms normalized to the frozen 11 units); focused 23, full Python 3216, Ruff, Pyright, tasks check, and the actual cut-16 runner pass on the certified tuple. Parent remains open for managed deletion and discharge.
- 2026-09-04T09:54:50Z (design/consolidate-family): Relocation cut discharged: move and consolidate land, G3 and D7 close, W5 reads in full. Managed deletion and the ride-alongs remain; the deletion cut follows.
- 2026-09-04T10:22:24Z (design/consolidate-family): Task 12 review correction: promoted correction-remainder to tier 1 now that cut 16 discharged its consolidate prerequisite; mutation-lane order remains serial.
- 2026-09-04T14:21:24Z (design/consolidate-family): claimed by Claude Code (claude-fable-5-1), pid 3996794; resuming for the deletion cut in .worktrees/consolidate-family on design/consolidate-family
- 2026-09-04T15:30:03Z (design/consolidate-family): Task 2: public delete lands as an ordinary write; T8 and C1 re-read; re-resolution after delete pinned
- 2026-09-04T16:04:18Z (design/consolidate-family): Task 3: semantic audit lands, Omega-valid first, three contradiction findings, mints nothing
- 2026-09-04T17:14:08Z (design/consolidate-family): Task 4: explicit import refuses contradicted derivations before any payload write; R19 transition (b) runs end to end
- 2026-09-04T17:57:57Z (design/consolidate-family): Task 5: claim_from_stored lands; M11 and M13 re-read against the new route
- 2026-09-04T18:44:10Z (design/consolidate-family): Task 6: beliefs.evaluation lands; M1 containment holds and its sabotage shape fails
- 2026-09-04T19:42:32Z (design/consolidate-family): Task 7: portable row evidence for G2c, G8, C6, S5, R23, W16, M3 and M5 passes (3329 passed in 922.48s (0:15:22)); ruff and pyright clean
- 2026-09-04T20:43:28Z (design/consolidate-family): Task 8: durable arms pass on the certified tuple (16 passed)
