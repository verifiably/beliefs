---
id: beliefs-6134e0
title: Backfill complexity ratings for open tasks
status: done
priority: 2
size: m
complexity: high
owner: main
created: 2026-09-12T15:09:51Z
updated: 2026-09-12T16:29:09Z
started: 2026-09-12T16:24:18Z
completed: 2026-09-12T16:29:09Z
depends: []
tags: []
source: tasks-be447b
---

Rate every open scoped task in this project — status todo, doing, or blocked; ideas are rated when they are scoped, not before — plus any recurring task (`tasks list --periodic`), with the rubric in the tasks skill: low = approach established, relevant context identified, correctness has a clear check; mid = bounded investigation or implementation choices remain, scope and acceptance criteria clear; high = substantial discovery, subtle reasoning about interacting behaviour, or an unresolved architectural call. Read each task body, its notes, and any linked spec or plan first, and rate the judgment that remains after that preparation — not the size: a large mechanical change is low, a one-line subtle fix can be high. `tasks list --status todo --status doing --status blocked` lists the set; `tasks edit <id> --complexity <level>` sets each. Done when `tasks ready --max-complexity high` reports no "unassessed hidden" warning. Rated high itself because rating is judgment work reserved for a frontier session (tasks docs/specs/2026-09-12-task-complexity-design.md §3.3); it must not be picked under a cutoff.

## Notes

- 2026-09-12T16:24:18Z (main): claimed by Codex /root, pid 2159765; metadata backfill only; read open task bodies, notes, linked designs and current delivery evidence before rating.
- 2026-09-12T16:26:55Z (main): Claim process clarification: Codex /root runs under long-lived pid 2159765; the earlier note named a short-lived command process. Reviewed all 19 scoped records and relevant design sections, current code/history and parked D1 draft; backfilled 18 ratings (3 low, 3 mid, 12 high), retaining this task as high. No recurring tasks; ideas and other task statuses/owners/parks are unchanged.
- 2026-09-12T16:28:17Z (main): The CLI flagged a newer beliefs-928881 record in .worktrees/d1-cross-repo-negative. Read its linked plan and verified committed implementation/freeze through d3d4c07; rated remaining discharge work mid. Its worktree-only open child beliefs-af9fd8 is already mid. Preserve that branch metadata and notes when merging; this change updates only main task records.
- 2026-09-12T16:29:09Z (main): Backfilled all 18 unrated scoped tasks with evidence notes (3 low, 3 mid, 12 high); no recurring tasks or unassessed-hidden warning; just check and tasks check pass.
