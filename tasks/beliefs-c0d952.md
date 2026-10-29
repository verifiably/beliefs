---
id: beliefs-c0d952
title: Design ledgered publication retirement from the brief
status: doing
priority: 2
size: m
complexity: high
process: planned
owner: design/publication-retirement
created: 2026-10-24T09:56:24Z
updated: 2026-10-29T12:02:56Z
started: 2026-10-29T11:34:00Z
depends: []
parent: beliefs-182296
tags: [publication, design]
source: docs/notes/2026-10-24-publication-session-follow-ups-brief.md
agent: codex
spec: docs/superpowers/specs/2026-10-29-publication-retirement-door-design.md
---

Question: How can ScopedWriter.retire(corpus_id, *, evidence) execute World.retire under scoped registry authority and ledger a truthful retired transition, including retries after a ledger failure?

Where to start: [ref:brief] records the gap and constraints. Read python/src/beliefs/session/writer.py (admit_publication, _bind_sharing_evidence and _record_sharing), session/ledger.py (SharingEvidence and SharingLine), world/registry.py (World._terminal), and the session sharing design decisions 4, 5 and 11. The science commons source is sci-13050a; milestone 1b is sci-9104fb.

Bound: Design the kernel door, evidence binding, status-record evidence, refusal ordering, idempotency and recovery when retirement commits before the ledger append. Resolve different-actor retries explicitly. Science retains keep, dependency and supersession decisions. Do not implement the door or duplicate beliefs-918fd2's overlap design. Rule whether existing ledger fields suffice and whether any frozen guarantee needs a new cut.

Expected result: A reviewed design under docs/superpowers/specs/, linked to this task; record its decision and next implementation handoff on this task and in [ref:brief]. Identify checks for wrong evidence and corpus, stale or closed invocation, insufficient authority, terminal status and repeat calls, plus write/flush/fsync failure after the registry effect. Any new cut must carry both AGENTS.md cut obligations. Existing tests/test_session_sharing_doors.py, tests/test_session_ledger.py, tests/test_world_registry.py and the permit inventories are starting points; use the project's just test-one front door.

Ideas it wakes: On completion, run `tasks note beliefs-a989fb --no-reviewed "<retirement design finding>"` before this result's branch merges.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-publication-session-follow-ups-brief.md — scope, known behaviour and design questions

## Notes

- 2026-10-29T11:34:00Z (main): started
  provenance: {"harness_session":"claude-code:273e85cc-6b53-4247-a392-547603c4040c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T11:34:15Z (design/publication-retirement): resumed
  provenance: {"harness_session":"claude-code:273e85cc-6b53-4247-a392-547603c4040c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T11:50:35Z (design/publication-retirement): review: spec round 1 — verdict: revise; findings: question 1, inaccurate-claim 4; reviewer: claude-code
- 2026-10-29T11:50:44Z (design/publication-retirement): parked (waiting on user, review): user reviews docs/superpowers/specs/2026-10-29-publication-retirement-door-design.md at f72802f (branch design/publication-retirement, worktree .worktrees/publication-retirement); on approval: record the decision in the brief, wake beliefs-a989fb with its finding note, merge the branch
  provenance: {"harness_session":"claude-code:273e85cc-6b53-4247-a392-547603c4040c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T11:56:16Z (design/publication-retirement): review: spec round 2 — verdict: revise; findings: Important 1, Minor 1; reviewer: codex/gpt-6-astra
- 2026-10-29T11:56:18Z (design/publication-retirement): resumed
  provenance: {"harness_session":"claude-code:273e85cc-6b53-4247-a392-547603c4040c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T11:57:38Z (design/publication-retirement): parked (waiting on user, review): user reviews revision 3 of docs/superpowers/specs/2026-10-29-publication-retirement-door-design.md at 578a014 (branch design/publication-retirement, worktree .worktrees/publication-retirement); on approval: record the decision in the brief, wake beliefs-a989fb with its finding note, merge the branch
  provenance: {"harness_session":"claude-code:273e85cc-6b53-4247-a392-547603c4040c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T12:02:43Z (design/publication-retirement): review: spec round 3 — verdict: accept; findings: none; reviewer: codex/gpt-6-astra
- 2026-10-29T12:02:56Z (design/publication-retirement): resumed
  provenance: {"harness_session":"claude-code:273e85cc-6b53-4247-a392-547603c4040c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
