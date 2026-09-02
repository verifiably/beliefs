---
id: beliefs-f5bd5d
title: decode_run_closure and RecipeVersionUnsupported
status: done
priority: 1
size: m
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T00:52:32Z
depends: [beliefs-97f740]
tags: [cut15]
plan: docs/plans/2026-09-01-workflow-surface.md
step: "Task 6: `decode_run_closure` and `RecipeVersionUnsupported`"
---

Cut 15, workflow-surface slice. Spec: docs/superpowers/specs/2026-09-01-workflow-surface-design.md. Plan step: docs/plans/2026-09-01-workflow-surface.md #Task 6.

## Notes

- 2026-09-02T00:30:07Z (design/workflow-surface): Blocked before implementation: the projection stores only environment.identity(), but Recipe requires the full EnvironmentManifest, so decode_run_closure cannot reconstruct a RunClosure or preserve its address without a design amendment.
- 2026-09-02T00:49:09Z (design/workflow-surface): Approved amendment recorded in the spec and plan: decode uses an opaque EnvironmentReference for the identity-only stored member; reprojection/address stay unchanged, while the shared execution check still requires a full EnvironmentManifest and refuses the reference.
- 2026-09-02T00:52:32Z (design/workflow-surface): Decoded v2 run closures with identity-only environment evidence, preserved addresses and conformance, and refused v1 typed decode and reference execution.
