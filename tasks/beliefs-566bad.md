---
id: beliefs-566bad
title: Establish the retained evidence needed for periodic mm30 recreation
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-14T02:15:32Z
updated: 2026-10-14T02:15:32Z
depends: []
parent: beliefs-cde4d9
tags: [reproduction]
source: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md
agent: codex
---

Question: Which artifacts must a periodic mm30 recreation retain to preserve its verdict, diagnose a failure and support a later replay, and which fresh-run-only data can safely expire?
Where to start: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md; justfile::mm30-recreate; python/tools/reproduction/{paths,verdict,state,findings,rederive,run}.py; docs/designs/2026-09-05-mm30-reproduction.md §§25–26; beliefs-6f2c2b's explicit retention note.
Bound: Trace readers and path references and inspect the existing fresh run read-only if available. Produce one artifact/dependency inventory covering a passing run and an incomplete or failing run. Do not recreate a corpus, delete or relocate data, add scheduling, or implement a cleanup tool. If retained inputs are unavailable, record that limit and the smallest later pilot needed.
Expected result: Record in this task and the existing brief a retention table (artifact, consumer, path dependency, preserve/eligible-for-expiry condition), an explicit exclusion for fixtures, cut archives, predecessor data and the user-kept 2026-09-30 run, and a recommendation on a recurring tracker task versus cut-discharge execution. Distinguish rechecking saved assertions from fresh kernel execution. State whether the evidence is enough to scope a minimal cadence safely.
Ideas it wakes: On completion, run tasks note beliefs-a49ab4 --no-reviewed "<retention finding and cadence recommendation>" before this result's branch merges.
