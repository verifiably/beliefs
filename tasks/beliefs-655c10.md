---
id: beliefs-655c10
title: "World view: a witness that mapped content and manifests are unchanged since an epoch, so coordination-only drift can be proved inert"
status: idea
priority: 2
created: 2026-10-01T22:21:05Z
updated: 2026-10-01T22:21:05Z
depends: []
tags: [world-read]
source: sci-dc0381
agent: claude-code/claude-opus-5-5
---

science's mount-citations consumer (science docs/specs/2026-10-01-mount-citations-consumer-design.md, decision 7 and limitation 2) treats any drift as epoch-stale, so every project/question/hypothesis write forces a new epoch before belief. A rule exempting drift made only of unmapped coordination records was rejected in plan review: open_world_view checks mapped addresses and uids, not content, and a mapped dataset facet revised beside a new coordination record was served changed while the rule called the drift inert. Needed: a cheap witness on WorldReadView (or the DriftReport) that every mapped record's content and every covered manifest are byte-identical to the epoch's capture. Measure first: sci-0d00d2 records how often coordination writes force a rebuild.
