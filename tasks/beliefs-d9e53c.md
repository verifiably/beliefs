---
id: beliefs-d9e53c
title: "Task 7: lineage_snapshot, _producers_of and run_value over the world view"
status: done
priority: 2
size: m
owner: design/world-resolution
created: 2026-09-09T10:57:33Z
updated: 2026-09-09T13:25:57Z
depends: []
parent: beliefs-d248ba
tags: [world-read]
plan: docs/superpowers/plans/2026-09-09-world-resolution-slice-1.md
step: "Task 7: `lineage_snapshot`, `_producers_of` and `run_value` over the world view"
---

## Notes

- 2026-09-09T13:15:20Z (design/world-resolution): task7/controller pid2130612
- 2026-09-09T13:20:20Z (design/world-resolution): implemented world lineage absence and published-producer union; focused 61 tests, arm staleness 7, ruff and pyright pass
- 2026-09-09T13:20:26Z (design/world-resolution): World lineage snapshots now preserve recorded absences and published producers across absent corpus carriers.
- 2026-09-09T13:25:57Z (design/world-resolution): round1 review: exact NotPresent alone skips root traversal; unknown world and local roots retain RefError
