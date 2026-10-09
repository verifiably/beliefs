---
id: beliefs-bd85d0
title: A conformance-cut arm for _closing_hold's currency check
status: shelved
priority: 2
created: 2026-10-09T11:31:49Z
updated: 2026-10-09T11:32:03Z
depends: []
tags: [holdings, conformance]
source: beliefs-27d500
---

From beliefs-27d500 item 14 (cut-35 final review, deferred minor). `src/session/writer.py:469-477`: `_closing_hold` calls `_require_current` (:476), and no cut arm sabotages that line. Cut 38's BI-3 arm (`python/tests/n2_arms_cut38.py:256`) swaps the port, and cut 19's arm (`n2_arms_cut19.py:596`) predates `_closing_hold`. The arm deletes the `_require_current` call and expects the acquisition close to refuse a stale session. It needs a frozen cut, so it rides with the next cut whose lane rewrites `session/writer.py` and is never a cut of its own.

## Notes

- 2026-10-09T11:32:03Z (main): shelved: Wake when a conformance cut's lane rewrites session/writer.py: that cut's plan declares this arm as a ride-along
