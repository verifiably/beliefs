---
id: beliefs-d52e6c
title: "Render seed_roots, and pin the engine's coercion"
status: done
priority: 1
size: s
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T00:58:44Z
depends: [beliefs-067ac2]
tags: [cut15]
plan: docs/plans/2026-09-01-workflow-surface.md
step: "Task 9: Render `seed_roots`, and pin the engine's coercion"
---

Cut 15, workflow-surface slice. Spec: docs/superpowers/specs/2026-09-01-workflow-surface-design.md. Plan step: docs/plans/2026-09-01-workflow-surface.md #Task 9.

## Notes

- 2026-09-02T00:58:44Z (design/workflow-surface): Focused Pyright exposed the two old BoundaryReceipt constructor sites. They now compose the existing launch as both members to keep the tree statically valid; Task 12 replaces that transitional shared evidence with the separately executed disposable planning launch.
- 2026-09-02T00:58:44Z (design/workflow-surface): Rendered one collision-free seed_roots mapping, pinned Snakemake's structured-value coercion, and migrated current receipt construction to the composed shape.
