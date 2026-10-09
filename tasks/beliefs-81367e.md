---
id: beliefs-81367e
title: A recipient holding two overlapping publications cannot build an epoch (duplicate-location)
status: idea
priority: 2
created: 2026-09-27T13:50:26Z
updated: 2026-10-09T10:48:25Z
depends: []
parent: beliefs-a286e7
tags: [publication]
source: beliefs-3ce305
agent: claude-code/claude-opus-5-5
---

Found in cut-42 spec review round 3. Publishing keeps selected records' addresses and uids, so every republication of one view shares records with its predecessor; derive.address_map refuses one canonical address held in two corpora (duplicate-location), so a recipient's epoch and world view fail once a second publication is admitted. publication_tip avoids it by reading held roots alone (publish-act-remote spec decision 9, §13 item 3), but every other world read does not. Decide whether retiring the superseded corpus removes it from the index, or the recipient must consolidate; this is the precondition for a recipient reading its world after a second publication.

## Notes

- 2026-10-01T02:21:10Z (main): Science's commons design (science docs/specs/2026-09-30-science-commons-design.md §4.7) states the outcomes it requires of this resolution: identical records under one address in several mounted corpora read once; conflicting content under one address refuses explicitly, never by corpus order; competing assessments with distinct (spec, run, proposition) identities stay distinct. Its milestone 1b depends on this task.
- 2026-10-09T10:48:24Z (main): scope: briefed; parented under goal beliefs-a286e7 with design follow-up beliefs-918fd2 (commons §4.7/§10 rule out retirement-only and consolidation; lean is a multi-holder address map keyed by content identity); brief: docs/notes/2026-10-09-overlapping-publications-brief.md
