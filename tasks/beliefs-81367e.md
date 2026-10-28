---
id: beliefs-81367e
title: A recipient holding two overlapping publications cannot build an epoch (duplicate-location)
status: idea
priority: 2
reviewed: true
reviewed_at: 2026-10-17T13:01:59Z
created: 2026-09-27T13:50:26Z
updated: 2026-10-28T17:14:38Z
depends: [beliefs-918fd2]
parent: beliefs-a286e7
tags: [publication]
source: beliefs-3ce305
agent: claude-code/claude-opus-5-5
---

Found in cut-42 spec review round 3. Publishing keeps selected records' addresses and uids, so every republication of one view shares records with its predecessor; derive.address_map refuses one canonical address held in two corpora (duplicate-location), so a recipient's epoch and world view fail once a second publication is admitted. publication_tip avoids it by reading held roots alone (publish-act-remote spec decision 9, §13 item 3), but every other world read does not. Decide whether retiring the superseded corpus removes it from the index, or the recipient must consolidate; this is the precondition for a recipient reading its world after a second publication.

## Notes

- 2026-10-01T02:21:10Z (main): Science's commons design (science docs/specs/2026-09-30-science-commons-design.md §4.7) states the outcomes it requires of this resolution: identical records under one address in several mounted corpora read once; conflicting content under one address refuses explicitly, never by corpus order; competing assessments with distinct (spec, run, proposition) identities stay distinct. Its milestone 1b depends on this task.
- 2026-10-09T10:48:24Z (main): scope: briefed; parented under goal beliefs-a286e7 with design follow-up beliefs-918fd2 (commons §4.7/§10 rule out retirement-only and consolidation; lean is a multi-holder address map keyed by content identity); brief: docs/notes/2026-10-09-overlapping-publications-brief.md
- 2026-10-17T13:01:59Z (main): scope: briefed; re-checked at 4580964: derive.address_map still refuses duplicate-location (world/derive.py:438) and no branch carries work on it; recorded the wait on design beliefs-918fd2 as a dep edge (its body asks it to note the ruling here); brief: docs/notes/2026-10-09-overlapping-publications-brief.md
- 2026-10-28T13:14:33Z (design/918fd2-overlapping-publications): ruling (beliefs-918fd2, design accepted at e14315c): a world holds one address in several live corpora when the copies have equal content identity (science.node-content.v1 digest of the canonical projection); the address map becomes multi-holder (AddressEntry uid/content/holders; new address-map.yaml shape, legacy admitted); differing content still refuses duplicate-location with consolidate as the exit, uid-corruption unchanged; reads label by the least present holder and decide acceptance, attribution and audit filing over the holder set; acceptance is a union over holders; attribution is own holder, else agreeing carriers, else the earliest origin in the held supersession order, else attribution-ambiguous; correction standing folds once at derivation in a retraction-enumeration v2 rule. Retirement stays science's policy; this task closes with the cut that implements the design. Spec: docs/superpowers/specs/2026-10-28-overlapping-publications-design.md
- 2026-10-28T17:14:38Z (design/918fd2-overlapping-publications): ruling complete: cut 48 (beliefs-918fd2, spec docs/superpowers/specs/2026-10-28-overlapping-publications-design.md) makes the address map multi-holder: a recipient holding two overlapping publications with equal content builds an epoch and reads the record once; differing content still refuses duplicate-location with consolidate as the exit. The remedy is implemented on the design branch (tasks 2 to 6) and proved by cut 48's guard; science's adopt checklist is the science task filed at discharge
