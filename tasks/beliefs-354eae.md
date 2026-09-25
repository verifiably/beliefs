---
id: beliefs-354eae
title: Give derive.address_map's retired-address collision a typed refusal instead of ValueError
status: todo
priority: 3
size: s
complexity: mid
created: 2026-09-25T13:10:53Z
updated: 2026-09-25T13:11:06Z
depends: []
tags: [world]
agent: claude-code
---

## Notes

- 2026-09-25T13:11:06Z (main): From beliefs-cc0aea's final review (2026-09-25): when one record's deprecated id equals another record's live address in a different corpus, derive.address_map raises a plain ValueError rather than a typed refusal. publish (and so evaluate_live_query, bound to publish's address-map behaviour by the live-query design's decision 7) surfaces it untyped. Fix it in derive, not in world/live.py (cut 41's frozen arm targets). A scratch probe during the review reproduced it over the same states for both paths.
