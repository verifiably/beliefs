---
id: beliefs-2be0ce
title: Pre-push hook must clear Git repository variables before running the gate
status: done
priority: 1
size: s
complexity: mid
process: direct
owner: design/publish
created: 2026-09-26T09:32:06Z
updated: 2026-09-26T09:35:22Z
started: 2026-09-26T09:32:10Z
completed: 2026-09-26T09:35:22Z
depends: []
tags: [testing]
source: 2026-09-26 push failure on design/publish
agent: codex
---

## Notes

- 2026-09-26T09:32:10Z (design/publish): started
  provenance: {"harness_session":"codex:01a0dce7-f7c2-7672-86a2-01b4a5fba35e","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T09:32:16Z (design/publish): claimed by codex/gpt-6, pid 193128; push hook exported GIT_DIR into tests, causing git init to rewrite shared repo state
- 2026-09-26T09:35:22Z (design/publish): done
  provenance: {"harness_session":"codex:01a0dce7-f7c2-7672-86a2-01b4a5fba35e","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-26T09:35:22Z (design/publish): Pre-push clears Git-local environment; isolated hook reproduction and corpus-state test pass
  provenance: {"harness_session":"codex:01a0dce7-f7c2-7672-86a2-01b4a5fba35e","harness_session_source":"CODEX_SESSION_ID"}
