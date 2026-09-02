---
id: beliefs-ed3dc8
title: The canonical semantic job key
status: done
priority: 1
size: s
owner: design/workflow-surface
created: 2026-09-01T21:13:05Z
updated: 2026-09-02T00:09:54Z
depends: []
tags: [cut15]
plan: docs/plans/2026-09-01-workflow-surface.md
step: "Task 1: The canonical semantic job key"
---

Cut 15, workflow-surface slice. Spec: docs/superpowers/specs/2026-09-01-workflow-surface-design.md. Plan step: docs/plans/2026-09-01-workflow-surface.md #Task 1.

## Notes

- 2026-09-02T00:09:54Z (design/workflow-surface): Red confirmed on the missing import; all four explicit job-key checks pass. The plan's '-k job_key' selector selects only two, so verification used the four node ids.
- 2026-09-02T00:09:54Z (design/workflow-surface): Added one RFC 8785 canonical job-key helper and TraceJob.job_key(), with four focused checks.
