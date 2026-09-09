---
id: beliefs-2d9a55
title: Public store identity reader (beliefs.root.store_identity)
status: todo
priority: 1
size: xs
created: 2026-09-09T15:44:00Z
updated: 2026-09-09T15:44:00Z
depends: []
tags: [command-framework, dogfood]
---

Belief-path design (science docs/specs/2026-09-09-belief-path-commands-design.md §5): the science read context needs a store root's identity to build the resolution snapshot and match held paths (store:<id>:<relative>), and reads it without opening a session. The kernel holds that read as the private _read_existing_store_genesis. Required: beliefs.root.store_identity(store_root: Path) -> str | None, the public form of that read by detached inspection (no recovery, no writes), None when the root carries no store genesis. Split out of beliefs-5fe2e3 so science Task 3 (sci-98282e) and the read-only commands can proceed before the routes seam lands.
