---
id: beliefs-754995
title: Deliver verification publication
status: done
priority: 1
size: l
owner: feat/verification-publication
created: 2026-09-05T20:00:55Z
updated: 2026-09-08T03:35:02Z
depends: [beliefs-afbbff, beliefs-942b40]
tags: [write-path, verification]
---

The write-path lane's second boundary (roadmap tier 1, on the path, #2): durable publication of verification records with admission evaluated over records read back. Confirmed on the path by the mm30 reproduction record (docs/designs/2026-09-05-mm30-reproduction.md, §3 row 10b and §5 question 3): no stored record carries the comparison report, and scope and verdict recover only by recomputation with in-process spec and rule implementations. Its slice design is its own work; cut 18's optional derivation member and admission_record's projection are the entry point. Blocked on the writer session (beliefs-afbbff) for the lane's order only.

## Notes

- 2026-09-07T09:29:05Z (main): Implementation landed on main at 965fe7f (slice merged --no-ff; branch feat/verification-publication deleted). Tasks 0-11 of the plan are complete: V1-V8 are implemented and the portable suite is green at 3739 passed. This task stays open because cut 21 is UNDISCHARGED — the plan's Task 12 needs the domain lane's cut 20 discharged and merged into main first, and cut 20 is not on main. Every ruling made during execution, and the residuals handed forward, are in docs/plans/2026-09-06-verification-publication-execution.md.
- 2026-09-08T03:35:02Z (feat/verification-publication): cut 21 discharged: V1-V8 closed, R19's stored-verification limitation lifted; results record and re-rank landed
