---
id: beliefs-3ea822
title: Certify publication persistence
status: todo
priority: 3
size: l
complexity: high
process: planned
created: 2026-08-31T00:38:28Z
updated: 2026-10-24T11:06:03Z
depends: [atoms-f5779f]
parent: beliefs-199aeb
tags: [migration, cross-repo, durability]
---

Outcome: Beliefs closes X2 and L1's inherited persistence arms with persistence-cut certification exercising the real publication and settlement paths through the Atoms durability boundary.

Acceptance evidence: Consume the harness delivered by atoms-f5779f, retaining the Atoms-local design gate and reviewing the Beliefs-side design and implementation plan before implementation. Extend the composition test without a duplicate transaction authority; keep root.py the sole Atoms importer. Record reproducible zero-violation evidence or fail closed, discharge X2 and the assigned L1 arms, update current status, and pass both affected repositories' complete gates.

Established at inspected main a7ce8ff on 2026-10-24: X2 means epoch publication, not simply the later corpus publish act. python/src/beliefs/world/epoch.py::build_epoch crosses registry._locked_barrier and submits _locked_publication_plan through the world executor. That plan includes every epoch member, epochs/current and the log-head records in one transaction. Cut 7's process-kill and registration evidence is not its deferred persistence-cut evidence: before the commit decision is durable, current must select the prior epoch; afterward recovery must select the new complete epoch, never missing or partial content.

L1, formally re-homed here at cut 36, adds all these obligations: kill the executor between entry durability and apply at every stage, leaving the entry present and pending until recovery settles it and the surface matches; crash after entry durability but before the transaction record stores its entry digest, with no second registration; and cut persistence at every settlement stage for BOTH committing and rolling-back transactions, producing one registration, one settlement and the backfilled binding, with neither outcome returned nor lease released before settlement durability.

Sources: docs/plans/2026-08-29-implementation-roadmap.md persistence-cut and Appendix B; docs/designs/2026-08-03-redesign-adoption-ledger.md persistence-cut row; docs/designs/2026-08-20-conformance-cut-7.md X2 accounting; docs/designs/2026-09-21-conformance-cut-36.md §3.2 and its results record §2; atoms-f5779f; and [ref:brief], which keeps the epoch/corpus-publication distinction and evidence limits explicit.

Uncertainty: The publication path exists, but its cross-repository harness, stage mapping and certified hardware scope are still undesigned here. atoms-f5779f remains open and planned; its 2026-10-14 re-scope establishes synthetic A8 machinery at Atoms 9391c72, not fresh consumer-path or physical certification. Confirm the current mapping with that owner rather than duplicate its harness work. Distinguish model, real-process recovery and physical power-fail evidence; this scope pass ran none of them.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-conformance-readiness-brief.md — current prerequisites, evidence limits and remaining decisions

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Cut 7 explicitly leaves X2 power-fail evidence open and atoms-f5779f still has no cross-repository harness design or certified hardware scope. Composing consumer publication stages with the sole Atoms recovery authority requires substantial design and certification judgment.
- 2026-09-21T11:54:12Z (event-level-l8): Gains L1's remaining arms from log-remainder at cut 36 (spec 2026-09-21-event-level-l8-design §2 decision 12, §10): kill the executor between entry durability and apply at every stage → entry present, pending; recovery settles it and the surface matches; crash after entry durability but before the transaction record stores the entry digest → no second registration; cut persistence at every stage of the settlement sequence for BOTH terminal arms (a committing and a rolling-back transaction) → one registration, one settlement, the binding backfilled, and neither outcome returned nor the lease released before the settlement is durable. L1 stays partial until this task reads them.
- 2026-09-21T15:28:32Z (event-level-l8): L1's arms formally re-homed here at cut 36 (results record §2; ledger persistence-cut row; roadmap Appendix B).
- 2026-10-24T11:06:03Z (main): scope: rescoped; at main a7ce8ff, established X2's build_epoch/current-pointer transaction path and incorporated all L1 arms re-homed by cut 36; retained P3/l/high and atoms-f5779f dependency, chose planned; upstream task's 2026-10-14 assessment is synthetic machinery evidence, not consumer or physical certification; brief: docs/notes/2026-10-24-conformance-readiness-brief.md
