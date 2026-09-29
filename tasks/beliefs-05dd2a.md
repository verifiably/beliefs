---
id: beliefs-05dd2a
title: Should build_epoch refuse to publish a retracted producer identity?
status: shelved
priority: 2
created: 2026-09-19T18:52:15Z
updated: 2026-09-29T22:50:05Z
depends: []
parent: beliefs-0c50ed
tags: [conformance, correction]
---

Slice 2 §14.7: a same-coverage rebuild republishes a retracted S, is retained and may become current; reads refuse and import refuses the same carrier, so the state is coherent but asymmetric. Refusing at build changes world-index §5.3's closed refusal surface.

## Notes

- 2026-09-29T22:50:05Z (main): shelved: A concrete workflow is blocked by selecting a rebuilt but retracted producer snapshot, or contract-cut explicitly selects build-time standing enforcement; then review the closed build refusal surface.
- 2026-09-29T22:50:05Z (main): scope: shelved; same-coverage rebuild behavior is pinned by a passing test; changing it is an extension to the build contract; brief: docs/notes/2026-09-29-retraction-standing-backlog-brief.md
