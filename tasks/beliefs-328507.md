---
id: beliefs-328507
title: "The publish act, local: request, snapshot, staging, export, reveal, recovery and arrival (cut 40)"
status: doing
priority: 2
size: xl
complexity: high
process: planned
owner: design/publish
created: 2026-09-22T22:08:29Z
updated: 2026-09-24T02:36:23Z
started: 2026-09-24T02:25:52Z
depends: [beliefs-d7d7d1]
parent: beliefs-1a5157
tags: [publication]
agent: claude-code/claude-opus-5-5
spec: docs/superpowers/specs/2026-09-23-publish-act-local-design.md
---

Slice 2 of publish: layer design 6.1 steps 0 (request record, durable create-only write, pins derivation, closure/empty refusals, selection snapshot answering the corpus-drifted retry problem), 1-7 and 9, the recovery table, transport as an injected seam with remotely-revealed orphans, marker-required arrival, and the act-report lifecycle entries. Designed after slice 1 discharges.

## Notes

- 2026-09-23T14:27:47Z (design/publish): Cut 40's recovery table must cover the unfinished publish intent: at cut 39 step 8, an exception before any effect (non-bool reveal, pin disagreement, unbound port, malformed binding arguments, a mismatched OpenedPublication, a guard exception other than LogEvidenceRefused, or a LogEvidenceRefused on the written root whose fallback cannot write) leaves the intent unfinished rather than orphaned, so a remotely revealed marker is recovered only from the unfinished intent (cut-39 results §3.3, Ruling 12).
- 2026-09-24T02:25:52Z (design/publish): started
  provenance: {"harness_session":"claude-code:99a95437-3bde-4503-a0dd-5f5a57cd7bd2","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T02:25:52Z (design/publish): claimed by claude-code opus-5-5, pid 3181057; brainstorming the cut-40 spec in .worktrees/publish
- 2026-09-24T02:26:25Z (design/publish): resumed
  provenance: {"harness_session":"claude-code:99a95437-3bde-4503-a0dd-5f5a57cd7bd2","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T02:26:25Z (design/publish): claimed by claude-code opus-5-5, pid 3181057; brainstorming the cut-40 spec in .worktrees/publish
- 2026-09-24T02:36:23Z (design/publish): User chose local-first split 2026-09-23: cut 40 = local act + marker-required arrival; cut 41 = transport seam, remote reveal/orphans (Ruling 12), remote recovery rows, divergent-publication. Spec drafted: docs/superpowers/specs/2026-09-23-publish-act-local-design.md
