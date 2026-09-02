---
id: beliefs-a45800
title: N2 arms and the cut-15 acceptance command
status: done
priority: 1
size: l
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T02:22:18Z
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
- 2026-09-02T01:56:36Z (design/workflow-surface): Post-close review integration fix: legacy cut-3 seeded engine fixtures still used seed_model_initialization and flat .seeds reports, so boundary and confinement arms failed under the cut-15 renderer/reader.
- 2026-09-02T02:17:30Z (design/workflow-surface): Post-close review fixes verified: migrated legacy seeded fixtures to bind(config) and canonical job keys; rejected reserved seed-config collisions and unsupported derivation rules before launch; bound recorded target keys back to invocation/plan resolution; validated planned job keys and duplicate wildcard names; strengthened the cut-15 freeze and prior-cut pins; migrated stale v2 receipt tests to composed v3/v4 receipts.
- 2026-09-02T02:22:18Z (design/workflow-surface): Final review closed the typed/wire seam: unsupported derivation is MalformedClosure; duplicate wildcard bindings fail at TraceJob construction and decode; planned semantic keys are validated identically in memory and on wire.
