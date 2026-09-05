---
id: beliefs-67cff1
title: "Permit-free read door: open_world_read binds the empty permit"
status: done
priority: 1
size: s
owner: read-door
created: 2026-09-05T08:44:46Z
updated: 2026-09-05T09:02:03Z
depends: []
tags: [authority]
---

The science read context (command-framework design section 4.2 and 9.2) opens a world for reads only and may not construct a permit, but open_world takes an Authority since a1f7408. Add permit.READ_ONLY (the empty permit under an actor no record can carry) and root.open_world_read(config) that binds it, so every act on the returned World refuses with PermitExceeded before any effect. Dated amendment to the write-permits design.

## Notes

- 2026-09-05T09:02:03Z (read-door): permit.READ_ONLY and root.open_world_read(config); tests in test_permit.py and test_root.py; design §16 amendment. Full gate green: pytest (15 min), ruff, pyright
