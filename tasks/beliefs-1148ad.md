---
id: beliefs-1148ad
title: Session ledger records the current-project selection
status: todo
priority: 2
size: s
complexity: mid
process: planned
created: 2026-09-24T10:43:33Z
updated: 2026-09-24T10:43:33Z
depends: []
tags: [session]
source: science docs/specs/2026-09-24-coordination-command-set-design.md §8 S2
agent: claude-code/claude-opus-5-5
---

Requested by science's coordination command set design (§8 S2; projects design P3). LINE_KINDS is closed (session/ledger.py) and nothing records a selection. Requirement: a project value on session-open (coord address or null), and a new line kind carrying the invocation id, the new value (address or null) and the revision the address resolved to, appended append-then-fsync before the invocation closes. Exposed as one WriterSession method science's session port calls, and readable back by invocation id through the ledger reader — science rebuilds the project-select report (its 'selection block') from that line on first response, replay and continuation. Blocks science's project-select and launcher initial selection.
