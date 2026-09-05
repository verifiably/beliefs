---
id: beliefs-f860f1
title: Store the verification's comparison report
status: todo
priority: 1
size: m
created: 2026-09-05T20:00:55Z
updated: 2026-09-05T20:00:55Z
depends: []
parent: beliefs-754995
tags: [write-path, verification, reproduction-finding]
---

Finding from the mm30 reproduction record (docs/designs/2026-09-05-mm30-reproduction.md, §3 row 10b; prediction P5): comparison_report_stored is false; the stored verification names its derivation and both closures decode, so scope and verdict recompute — but only with the in-process FrozenSpec and rule implementations, since no reader restores either from a record. The slice gives the stored verification its comparison report so 10b passes from the corpus alone.
