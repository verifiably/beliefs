---
id: beliefs-d8fae8
title: Guard the newest cut document's status line at discharge
status: done
priority: 3
size: s
complexity: low
process: direct
owner: chore/docs-guards
created: 2026-09-16T10:03:27Z
updated: 2026-09-16T10:22:47Z
started: 2026-09-16T10:18:56Z
completed: 2026-09-16T10:22:47Z
depends: []
tags: [conformance, docs]
model: "claude-opus-5[1m]"
agent: claude-code/claude-opus-5
---

Found 2026-09-16 in the docs review: cut 31's frozen document still read 'frozen 2026-09-15, before implementation … Q1–Q10 are open' a day after its results record landed, while cuts 27–30 had each rewritten that line at discharge. The status line sits outside the pinned §§2–7, so nothing holds it. Add one assertion to test_designs_corpus.py beside test_the_ledger_summary_names_the_newest_remaining_boundary: the cut document the newest results record cites carries 'discharged' in its Status line. Fails closed on a missing Status line.

## Notes

- 2026-09-16T10:18:56Z (chore/docs-guards): claimed by claude-code/opus-5 in .worktrees/docs-guards (chore/docs-guards)
- 2026-09-16T10:22:47Z (chore/docs-guards): test_the_newest_cut_document_says_it_is_discharged in test_designs_corpus.py: the cut document the newest results record discharges must carry 'discharged' in its Status line; proved red on cut 31's pre-fix line.
