---
id: beliefs-f6f36a
title: "Adopt ops-check: vendor tools/ops-check, run it first in check_cmd, fix what it reports"
status: done
priority: 2
size: s
owner: main
created: 2026-09-07T11:55:34Z
updated: 2026-09-07T22:01:43Z
depends: []
tags: [hooks]
---

ops-25a144 ("every front-door project runs ops-check first in its check command") is done, and its dependency list names atoms, fam, forge, material, mind6, nodes, prism, sci and tasks. beliefs is absent because until 2026-09-07 it had no front door.

It has one now (beliefs-f253a1 step 1), and its check_cmd is the only one of the ten that does not start with `python3 tools/ops-check`. Vendor tools/ops-check from ops bin/ops-check, put it first in the justfile's check_cmd, and fix what it reports.

ops `just check` runs check-vendored, which compares tools/ops-check against bin/ops-check in every registered project that has one; it skips projects without the file, so beliefs is currently skipped rather than failing.

## Notes

- 2026-09-07T22:01:43Z (main): tools/ops-check is vendored byte-identical from ops bin/ops-check at version 3 and runs first in check_cmd, so `just check` and the pre-commit hook run the shared hygiene checks. Its one finding: AGENTS.md backticked verifiably/beliefs, which is the GitHub org/repo slug and not a path claim, so the backticks are gone - the tool cannot learn that shape, since it is identical to a real two-segment path. Also corrected the justfile header, which still said the git hooks were not installed: core.hooksPath is .githooks and both hooks have been running. beliefs was the last of the ten front-door projects without ops-check; ops just check-vendored now compares it instead of skipping it. CI still runs the per-package recipes, so ops-check is in the local gate only, as tasks check already is.
