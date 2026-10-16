---
id: beliefs-7a2ab6
title: Rewrite t@t commit authorship in this repository
status: done
priority: 2
size: s
complexity: low
process: direct
owner: main
created: 2026-10-16T16:32:05Z
updated: 2026-10-16T19:25:10Z
started: 2026-10-16T19:12:54Z
completed: 2026-10-16T19:25:10Z
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
- 2026-10-16T19:18:21Z (main): attached: 2026-10-16-identity-commit-map.txt (10623 bytes): Authorship rewrite map: 129 changed commit IDs; resolves historical SHA references (docs, task notes, cited_not_run.py) without editing append-only or frozen text.
- 2026-10-16T19:22:15Z (main): Verified all 2060 original commit objects byte-for-byte after substituting only mapped parent IDs and t@t author/committer identities: 126 commits corrected (252 identity lines), 129 hashes changed, every tree/message/timestamp preserved, zero t@t on all local refs, main tree unchanged (db734f8). filter-repo strips tag signatures, so the SSH-signed annotated tags pin/cut6-* were left at their original objects (their targets c8c0b12, 4a7dc19 are pre-window and unchanged); the four other branches and origin/design/publish were verified unchanged in the same update-ref transaction. Attached map resolves the old SHAs cited in docs/notes, docs/superpowers specs/plans, task notes and the prose string in python/tests/cited_not_run.py (left as recorded). .git-blame-ignore-revs was functional, so 7175e3f maps both reformat commits (03d91bd->67bbdba, ea6393a->5c94e23). Europa worktree bytes matched HEAD before the swap; its stale index is preserved and backed up. Bundle, both indexes, mirror, ref transaction and verification retained at WORK_ROOT/beliefs/identity-rewrite-20261016T191444Z on Titan. test-fast: 6119 passed, 1 skipped. Pushing main with --force-with-lease=refs/heads/main:445b4ee and the pre-push gate.
- 2026-10-16T19:25:10Z (main): done
  provenance: {"harness_session":"claude-code:6159c002-c0bb-45da-b2c4-1f1a5b274e38","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-16T19:25:10Z (main): Rewrote 126 t@t commits to Keith Hughitt (129 hashes changed; every tree, message, timestamp and parent relationship verified preserved across all 2060 commits); signed pin tags, other branches and origin/design/publish untouched; SHA map attached; .git-blame-ignore-revs remapped (7175e3f). Pushed main to verifiably/beliefs with lease 445b4ee through the pre-push gate (6119 Python + 155 TS passed); remote and Europa show zero t@t. Forced only past ops-e5b39c, whose completed pilot procedure was followed; obs re-indexing stays with the wider rollout.
  provenance: {"harness_session":"claude-code:6159c002-c0bb-45da-b2c4-1f1a5b274e38","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
