---
id: beliefs-79351f
title: The builder derives the id; migrate every call site
status: done
priority: 2
size: l
complexity: mid
process: direct
owner: design/world-resolution-slice-5
created: 2026-09-14T22:45:21Z
updated: 2026-09-15T01:16:27Z
started: 2026-09-15T00:13:19Z
completed: 2026-09-15T01:16:27Z
depends: [beliefs-b47830]
parent: beliefs-48214e
tags: [world-read]
agent: claude-code/claude-fable-5-1
plan: docs/superpowers/plans/2026-09-14-world-resolution-slice-5.md
step: "Task 3: The builder derives the id; migrate every call site"
---

## Notes

- 2026-09-15T00:13:19Z (design/world-resolution-slice-5): claimed by codex task3, pid 3648680
- 2026-09-15T01:16:27Z (design/world-resolution-slice-5): TDD complete: builder derives dataset ids; all callers migrated; portable 4636 passed; cut20 F8 live adapter baseline resolved/audit sound; frozen guards 14 passed; ruff, pyright, and tasks check green
- 2026-09-15T01:16:27Z (design/world-resolution-slice-5): Derived dataset ids from declarations and migrated every ordinary builder caller, with portable and live-guard verification green.
