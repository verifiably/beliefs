---
id: beliefs-d1464c
title: The planning launch and the planned job set
status: done
priority: 1
size: l
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T01:11:01Z
depends: [beliefs-4dd087]
tags: [cut15]
plan: docs/plans/2026-09-01-workflow-surface.md
step: "Task 12: The planning launch and the planned job set"
---

Cut 15, workflow-surface slice. Spec: docs/superpowers/specs/2026-09-01-workflow-surface-design.md. Plan step: docs/plans/2026-09-01-workflow-surface.md #Task 12.

## Notes

- 2026-09-02T01:09:01Z (design/workflow-surface): The engine currently creates .snakemake in the execution scratch, so the plan's negative assertion was invalid. The structural guarantee is pinned instead: execution scratch survives, planning uses a distinct path, and that planning directory is discarded.
- 2026-09-02T01:11:01Z (design/workflow-surface): Added planned-job records and codecs, parsed deduplicated dry-run events, and ran an isolated disposable planning launch before minimal execution with separate receipt evidence.
