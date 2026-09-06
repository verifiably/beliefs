---
id: beliefs-754995
title: Deliver verification publication
status: doing
priority: 1
size: l
owner: feat/verification-publication
created: 2026-09-05T20:00:55Z
updated: 2026-09-06T11:27:34Z
depends: [beliefs-afbbff]
tags: [write-path, verification]
---

The write-path lane's second boundary (roadmap tier 1, on the path, #2): durable publication of verification records with admission evaluated over records read back. Confirmed on the path by the mm30 reproduction record (docs/designs/2026-09-05-mm30-reproduction.md, §3 row 10b and §5 question 3): no stored record carries the comparison report, and scope and verdict recover only by recomputation with in-process spec and rule implementations. Its slice design is its own work; cut 18's optional derivation member and admission_record's projection are the entry point. Blocked on the writer session (beliefs-afbbff) for the lane's order only.
