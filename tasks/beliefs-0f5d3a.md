---
id: beliefs-0f5d3a
title: Remove 0f5112 worktree after local main merge
status: todo
priority: 2
size: xs
complexity: low
process: direct
created: 2026-11-01T17:00:41Z
updated: 2026-11-01T17:00:41Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5-5
origin: agent
---

Dispose of .worktrees/0f5112-test-latency and local branch perf/0f5112-test-latency once the branch is merged locally into main: verify retention-checkpoint basis ancestry on main, inspect ignored files, check no host pointer resolves into the worktree, run tt-report, unlock and remove the worktree, delete the merged branch, and record the released worktree item on beliefs-0f5112.

## Notes

- 2026-11-01T17:00:41Z (add): created
  provenance: {"harness_session":"claude-code:f60df5b0-a52d-44ca-84ef-db0d992d02fa","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
