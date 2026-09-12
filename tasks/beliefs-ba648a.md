---
id: beliefs-ba648a
title: "Fill in setup_cmd: npm ci in ts/ so a fresh worktree passes the pre-commit gate"
status: done
priority: 2
size: xs
owner: main
created: 2026-09-11T21:13:32Z
updated: 2026-09-12T10:00:49Z
started: 2026-09-12T09:58:26Z
completed: 2026-09-12T10:00:49Z
depends: []
tags: [testing]
source: ops-9c7dab
---

Piece of ops-9c7dab. The justfile's comment already says npm ci belongs to a fresh worktree, not a gate; give it a home: setup_cmd := "(cd ts && npm ci)" plus the setup recipe from ops templates/justfile, so just setup after git worktree add is enough for hook-pre-commit to pass. uv creates the python venv on demand, so nothing python-side is needed unless pyright needs a sync.

## Notes

- 2026-09-12T10:00:49Z (main): setup_cmd := (cd ts && npm ci) and the setup recipe; verified in a probe worktree: hook-pre-commit exit 2 before, 0 after just setup, venv created on demand by uv
