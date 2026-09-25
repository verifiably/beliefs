---
id: beliefs-1148ad
title: Session ledger records the current-project selection
status: doing
priority: 2
size: s
complexity: mid
process: planned
owner: main
created: 2026-09-24T10:43:33Z
updated: 2026-09-25T02:26:43Z
started: 2026-09-25T01:13:18Z
depends: []
tags: [session]
source: science docs/specs/2026-09-24-coordination-command-set-design.md §8 S2
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-09-24-session-selection-ledger-design.md
plan: docs/superpowers/plans/2026-09-24-session-selection-ledger.md
---

Requested by science's coordination command set design (§8 S2; projects design P3). LINE_KINDS is closed (session/ledger.py) and nothing records a selection. Requirement: a project value on session-open (coord address or null), and a new line kind carrying the invocation id, the new value (address or null) and the revision the address resolved to, appended append-then-fsync before the invocation closes. Exposed as one WriterSession method science's session port calls, and readable back by invocation id through the ledger reader — science rebuilds the project-select report (its 'selection block') from that line on first response, replay and continuation. Blocks science's project-select and launcher initial selection.

## Notes

- 2026-09-25T01:13:18Z (main): started
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T01:13:18Z (main): claimed by claude-code/claude-opus-5-5; process planned: spec in docs/superpowers/specs, worktree .worktrees/session-selection
- 2026-09-25T02:26:43Z (design/session-selection): parked (waiting on user, review): Plan docs/superpowers/plans/2026-09-24-session-selection-ledger.md (94768cf, worktree .worktrees/session-selection) awaits user review and an execution method
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
