---
id: beliefs-c90220
title: "Task 5: The ledgered holdings seam and `holdings_context`"
status: done
priority: 1
size: s
owner: kernel-seams
created: 2026-09-09T22:14:30Z
updated: 2026-09-09T23:40:42Z
depends: [beliefs-b9edfe]
parent: beliefs-5fe2e3
tags: [dogfood, command-framework]
plan: docs/plans/2026-09-09-session-routes.md
step: "Task 5: The ledgered holdings seam and `holdings_context`"
---

## Notes

- 2026-09-09T23:35:32Z (kernel-seams): Task 5 implementation by seams_task5 process 2
- 2026-09-09T23:40:42Z (kernel-seams): ledgered_seam guards every member under the session lock, taken before the corpus lock; holdings_context binds the session store; both lock-order tests fail under the reversed order (verified)
