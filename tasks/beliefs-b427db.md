---
id: beliefs-b427db
title: Successor-actor resume for a publish stranded by a session that will never resume it
status: idea
priority: 2
created: 2026-10-23T01:56:37Z
updated: 2026-10-23T01:56:37Z
depends: []
tags: [publication]
source: beliefs-f24fe9
agent: claude-code
---

cut 40 decision 9 binds resume_publish to the intent's actor; under a service the actor is session:<id>, so a remote attempt stranded after its transport mark by a dead session leaves its (view, destination) pair refusing publish-unfinished from every later session (session doors design 2026-10-22 §2.12, §8). Design an operator-time or successor-actor resume against cut 40's actor rows, recording the succession in the report.
