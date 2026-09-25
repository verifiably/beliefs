---
id: beliefs-cc0aea
title: "Live, unpublished view-query evaluation for attention reads"
status: doing
priority: 2
size: m
complexity: high
process: planned
owner: main
created: 2026-09-24T10:43:33Z
updated: 2026-09-25T02:26:43Z
started: 2026-09-25T01:17:04Z
depends: []
tags: [world-read, coordination]
source: science docs/specs/2026-09-24-coordination-command-set-design.md §8 S1
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-09-24-live-query-evaluation-design.md
plan: docs/superpowers/plans/2026-09-24-live-query-evaluation.md
---

Requested by science's coordination command set design (docs/specs/2026-09-24-coordination-command-set-design.md §8 S1, decision 3). evaluate_query denotes a ViewQuery only over a WorldReadView at a published epoch and refuses corpus-drifted once any corpus moves past it (coordination-and-view-kinds §6.2), and no science command may publish an epoch (framework §4.4). A project's next would therefore refuse after the first write until an operator republished. Requirement: denote a ViewQuery over the mounted corpora's current captured state without building or publishing an epoch, returning a selection whose stamp names the capture rather than any epoch identity, so no consumer can mistake it for an epoch-bound answer. Publish and every epoch-bound read are unchanged. Rationale: the queue is attention, not belief input — §6.2's own argument for live coordination resolution ('no packaging step mediates seeing your own task edit') covers seeing your own new proposition in your project's queue. Function vs view type is the kernel's call. Blocks science's project-scoped next.

## Notes

- 2026-09-25T01:17:04Z (main): started
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T01:17:04Z (main): claimed by claude-code/claude-opus-5-5; process planned: spec in docs/superpowers/specs, worktree .worktrees/live-query
- 2026-09-25T02:26:43Z (design/live-query): parked (waiting on user, review): Plan docs/superpowers/plans/2026-09-24-live-query-evaluation.md (9680614, worktree .worktrees/live-query) awaits user review, an execution method, and the cut-number choice (cut 41 is unfrozen: take 41 or wait)
  provenance: {"harness_session":"claude-code:af80b7c9-5bc3-4364-b1cc-1d608fd7381f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
