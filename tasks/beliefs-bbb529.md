---
id: beliefs-bbb529
title: R2's fan-out fixture under minimal-v1
status: done
priority: 1
size: s
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T01:36:36Z
depends: [beliefs-3895aa]
tags: [cut15]
plan: docs/plans/2026-09-01-workflow-surface.md
step: "Task 19: R2's fan-out fixture under `minimal-v1`"
---

Cut 15, workflow-surface slice. Spec: docs/superpowers/specs/2026-09-01-workflow-surface-design.md. Plan step: docs/plans/2026-09-01-workflow-surface.md #Task 19.

## Notes

- 2026-09-02T01:33:44Z (design/workflow-surface): Corrected Task 19 receipt-membership arm to use the seeded declaration required by SNAKEFILE_SCRATCH_KEYED_FANOUT; bind(config) intentionally refuses a deterministic recipe at Snakefile load.
- 2026-09-02T01:36:36Z (design/workflow-surface): Pinned scratch-keyed fan-out with differing trace, job IDs, and realized seeds under one minimal recipe.
