---
id: beliefs-8abd52
title: Design successor-actor publication recovery from the brief
status: todo
priority: 2
size: l
complexity: high
process: planned
created: 2026-10-24T09:56:26Z
updated: 2026-10-24T09:56:26Z
depends: []
parent: beliefs-182296
tags: [publication, design]
source: docs/notes/2026-10-24-publication-session-follow-ups-brief.md
agent: codex
---

Question: Which explicit authority can let a successor session resume one stranded publication attempt while preserving the original intent, recording succession and retaining fail-closed actor checks elsewhere?

Where to start: [ref:brief] records the frozen actor constraint and current pair blockage. Read python/src/beliefs/publish.py (publish, resume_publish, _resume_from_mark), publication_doors.py (intent and report actors), session/writer.py (_publishing and resume_publish), the local-publish design decision 9, the remote-publish design transport-mark rules, and the session sharing design decision 12. tests/acceptance/test_publish_act_acceptance.py:test_resume_refuses_another_actor_and_another_profile_writing_nothing pins the existing refusal.

Bound: Design operator-authorized recovery or an explicitly granted successor, comparing the two against the authority model; settle grant scope, actors and report evidence. Cover both sides of the transport mark, retained request/export validation, concurrent or stale sessions, replay and crash recovery. Never implement unrestricted same-world takeover, impersonate the dead session, or edit frozen cut bodies. Do not implement the recovery path in this task.

Expected result: A reviewed design under docs/superpowers/specs/, linked to this task; record the chosen authority, amended guarantees and implementation handoff on this task and in [ref:brief]. Specify checks for unauthorized and wrong-intent succession with no effects, authorized recovery to one binding/report, truthful original/successor provenance, concurrent recovery, corrupt request/mark/export and repeat recovery after crashes. Name each superseded cut row by citation and carry both AGENTS.md cut obligations for a new cut. Existing test_publish_remote_engine.py, test_session_publish_door.py and acceptance/test_publish_remote_acceptance.py supply the recovery fixtures; use just test-one.

Ideas it wakes: On completion, run `tasks note beliefs-b427db --no-reviewed "<successor recovery design finding>"` before this result's branch merges.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-publication-session-follow-ups-brief.md — scope, known behaviour and design questions
