---
id: beliefs-328507
title: "The publish act: request record, selection snapshot, staging, export, reveal and recovery (cut 40)"
status: todo
priority: 2
size: xl
complexity: high
process: planned
created: 2026-09-22T22:08:29Z
updated: 2026-09-23T14:27:47Z
depends: [beliefs-d7d7d1]
parent: beliefs-1a5157
tags: [publication]
agent: claude-code/claude-opus-5-5
---

Slice 2 of publish: layer design 6.1 steps 0 (request record, durable create-only write, pins derivation, closure/empty refusals, selection snapshot answering the corpus-drifted retry problem), 1-7 and 9, the recovery table, transport as an injected seam with remotely-revealed orphans, marker-required arrival, and the act-report lifecycle entries. Designed after slice 1 discharges.

## Notes

- 2026-09-23T14:27:47Z (design/publish): Cut 40's recovery table must cover the unfinished publish intent: at cut 39 step 8, an exception before any effect (non-bool reveal, pin disagreement, unbound port, malformed binding arguments, a mismatched OpenedPublication, a guard exception other than LogEvidenceRefused, or a LogEvidenceRefused on the written root whose fallback cannot write) leaves the intent unfinished rather than orphaned, so a remotely revealed marker is recovered only from the unfinished intent (cut-39 results §3.3, Ruling 12).
