---
id: beliefs-f6f36a
title: "Adopt ops-check: vendor tools/ops-check, run it first in check_cmd, fix what it reports"
status: todo
priority: 2
size: s
created: 2026-09-07T11:55:34Z
updated: 2026-09-07T11:55:34Z
depends: []
tags: [hooks]
---

ops-25a144 ("every front-door project runs ops-check first in its check command") is done, and its dependency list names atoms, fam, forge, material, mind6, nodes, prism, sci and tasks. beliefs is absent because until 2026-09-07 it had no front door.

It has one now (beliefs-f253a1 step 1), and its check_cmd is the only one of the ten that does not start with `python3 tools/ops-check`. Vendor tools/ops-check from ops bin/ops-check, put it first in the justfile's check_cmd, and fix what it reports.

ops `just check` runs check-vendored, which compares tools/ops-check against bin/ops-check in every registered project that has one; it skips projects without the file, so beliefs is currently skipped rather than failing.
