---
id: beliefs-7a2ab6
title: Rewrite t@t commit authorship in this repository
status: doing
priority: 2
size: s
complexity: low
process: direct
owner: main
created: 2026-10-16T16:32:05Z
updated: 2026-10-16T19:14:18Z
started: 2026-10-16T19:12:54Z
depends: [ops-e5b39c]
tags: []
source: git-identity-leak-2026-10-07
agent: claude-code/claude-opus-5-5
---

Rewrite this repository's t <t@t> commits (from the 2026-10-07 global-config leak; see ops-5749d9) to Keith Hughitt <keith.hughitt@gmail.com>, following the runbook ops-e5b39c. Inventory on titan 2026-10-16: 126 t@t commits on all refs, 4 unpushed on main, 1 worktree(s); remote: verifiably/beliefs.

## Notes

- 2026-10-16T19:12:54Z (main): started
  provenance: {"harness_session":"claude-code:6159c002-c0bb-45da-b2c4-1f1a5b274e38","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-16T19:14:18Z (main): Direct history maintenance under ops-e5b39c's completed pilot procedure (as atoms-b12ec6, autonomy-0b4c52). User confirmed Europa quiet for beliefs. Inventory: 126 t@t commits, all on main; branches design/publish, feat/acceptance-filter, feat/publication-attribution, research/n2-preflight-pilot and tags pin/cut6-* carry none and stay unchanged; no stashes; one worktree (main) on Titan and Europa; Europa index stale for this record (preserve it, check tracked bytes). Remote verifiably/beliefs: main 445b4ee (lease) and design/publish (no t@t), no open PRs, main unprotected. Steps: bundle --all; mirror clone outside Dropbox; filter-repo --mailmap over all refs once; verify commit objects differ only in mapped parents and identity; guarded update-ref transaction; attach changed-entry SHA map; test-fast; push --force-with-lease=main:445b4ee with the pre-push gate.
