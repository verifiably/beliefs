---
id: beliefs-2d9a55
title: Public store identity reader (beliefs.root.store_identity)
status: done
priority: 1
size: xs
owner: kernel-seams
created: 2026-09-09T15:44:00Z
updated: 2026-09-09T23:00:10Z
depends: []
tags: [command-framework, dogfood]
plan: docs/plans/2026-09-09-session-routes.md
step: "Task 1: The public store identity reader"
---

Belief-path design (science docs/specs/2026-09-09-belief-path-commands-design.md §5): the science read context needs a store root's identity to build the resolution snapshot and match held paths (store:<id>:<relative>), and reads it without opening a session. The kernel holds that read as the private _read_existing_store_genesis. Required: beliefs.root.store_identity(store_root: Path) -> str | None, the public form of that read by detached inspection (no recovery, no writes), None when the root carries no store genesis. Split out of beliefs-5fe2e3 so science Task 3 (sci-98282e) and the read-only commands can proceed before the routes seam lands.

## Notes

- 2026-09-09T22:57:50Z (kernel-seams): claimed by /root/seams_task1, pid 2
- 2026-09-09T23:00:10Z (kernel-seams): store_identity is the public detached genesis read; a corpus root refuses, an empty root reads None
