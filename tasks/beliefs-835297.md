---
id: beliefs-835297
title: "Session ledger reader: hold act and invocation-close to the writer's currency rule"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-25T01:37:06Z
updated: 2026-09-25T01:37:06Z
depends: []
tags: [session]
agent: claude-code/claude-opus-5-5
---

The writer accepts an act or invocation-close only for the current invocation (writer-session §3.3, §5); _parse accepts either for any open invocation, including one abandoned by a later invocation-open. beliefs-1148ad's spec (docs/superpowers/specs/2026-09-24-session-selection-ledger-design.md decision 7) adds currency tracking for select only. Extend it to act and invocation-close after checking every ledger.v1 on disk still parses (science's dogfood operations root, acceptance leftovers); a ledger the writer could not have written becomes LedgerUnreadable evidence.
