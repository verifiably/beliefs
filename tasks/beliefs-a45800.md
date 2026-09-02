---
id: beliefs-a45800
title: N2 arms and the cut-15 acceptance command
status: done
priority: 1
size: l
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T01:53:24Z
depends: [beliefs-59f1e0]
tags: [cut15]
plan: docs/plans/2026-09-01-workflow-surface.md
step: "Task 21: N2 arms and the cut-15 acceptance command"
---

Cut 15, workflow-surface slice. Spec: docs/superpowers/specs/2026-09-01-workflow-surface-design.md. Plan step: docs/plans/2026-09-01-workflow-surface.md #Task 21.

## Notes

- 2026-09-02T01:53:24Z (design/workflow-surface): N2 review corrected five vacuous arms: R16a and R16g now isolate their intended conformance levels; R21a holds other invocation members equal; K2 preserves exact-one-key validation while sabotaging shape dispatch; K4 uses a genuinely colliding pipe join. The initial full audit found the other 25 arms sound, and each corrected arm now audits sound.
- 2026-09-02T01:53:24Z (design/workflow-surface): cut15_acceptance.py refuses because cut14_acceptance.py is absent on this independent lane, preserving the frozen discharge serialization prerequisite.
- 2026-09-02T01:53:24Z (design/workflow-surface): Declared and audited 30 cut-15 N2 arms and added the serialized cut-15 acceptance runner.
