---
id: beliefs-89d663
title: The confined planning instance
status: done
priority: 1
size: m
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T01:22:20Z
depends: [beliefs-40769d]
tags: [cut15]
plan: docs/plans/2026-09-01-workflow-surface.md
step: "Task 16: The confined planning instance"
---

Cut 15, workflow-surface slice. Spec: docs/superpowers/specs/2026-09-01-workflow-surface-design.md. Plan step: docs/plans/2026-09-01-workflow-surface.md #Task 16.

## Notes

- 2026-09-02T01:20:04Z (design/workflow-surface): Corrected the plan assertion against the frozen design and MountPlan.identity(): the two launches share the canonical sandbox mount-plan identity; their scratch mappings, host mount mappings, and argv differ.
- 2026-09-02T01:22:20Z (design/workflow-surface): Ran planning and execution in separate confined instances over one verified snapshot, with distinct host mappings and one engine argv per attestation.
