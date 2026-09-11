---
id: beliefs-fe22b0
title: "Task 3: The builder derives the address; migrate every call site"
status: done
priority: 2
size: m
owner: world-resolution-slice-2b
created: 2026-09-11T00:28:23Z
updated: 2026-09-11T09:02:23Z
depends: [beliefs-0da794]
parent: beliefs-b7994b
tags: [world-read]
plan: docs/superpowers/plans/2026-09-10-world-resolution-slice-2b.md
step: "Task 3: The builder derives the address; migrate every call site"
---

## Notes

- 2026-09-11T08:21:09Z (world-resolution-slice-2b): claimed by Codex implement_3, pid 2772021
- 2026-09-11T09:02:22Z (world-resolution-slice-2b): migrated 80 pre-existing source_node calls in 20 files; AST audit: 85 total calls, 0 positional; focused 118 passed, frozen guards 14 passed, TypeScript 142 passed, just check and pre-commit hook passed
- 2026-09-11T09:02:23Z (world-resolution-slice-2b): source_node now normalizes identifiers and derives its address; all measured callers and stale built-source refs migrated
