---
id: beliefs-05dd2a
title: Should build_epoch refuse to publish a retracted producer identity?
status: idea
priority: 2
created: 2026-09-19T18:52:15Z
updated: 2026-09-19T18:52:15Z
depends: []
tags: [conformance, correction]
---

Slice 2 §14.7: a same-coverage rebuild republishes a retracted S, is retained and may become current; reads refuse and import refuses the same carrier, so the state is coherent but asymmetric. Refusing at build changes world-index §5.3's closed refusal surface.
