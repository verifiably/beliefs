---
id: beliefs-d8fae8
title: Guard the newest cut document's status line at discharge
status: todo
priority: 3
size: s
complexity: low
process: direct
created: 2026-09-16T10:03:27Z
updated: 2026-09-16T10:03:27Z
depends: []
tags: [conformance, docs]
agent: claude-code/claude-opus-5
---

Found 2026-09-16 in the docs review: cut 31's frozen document still read 'frozen 2026-09-15, before implementation … Q1–Q10 are open' a day after its results record landed, while cuts 27–30 had each rewritten that line at discharge. The status line sits outside the pinned §§2–7, so nothing holds it. Add one assertion to test_designs_corpus.py beside test_the_ledger_summary_names_the_newest_remaining_boundary: the cut document the newest results record cites carries 'discharged' in its Status line. Fails closed on a missing Status line.
