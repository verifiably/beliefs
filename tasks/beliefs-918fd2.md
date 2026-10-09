---
id: beliefs-918fd2
title: Design overlapping-publication reads from the brief
status: todo
priority: 2
size: l
complexity: high
process: planned
created: 2026-10-09T10:48:20Z
updated: 2026-10-09T10:48:20Z
depends: []
parent: beliefs-a286e7
tags: [publication, design]
source: docs/notes/2026-10-09-overlapping-publications-brief.md
agent: claude-code/claude-opus-5-5
---

Write the conformance-cut spec that lets a world hold one address in several live corpora: identical content reads once, differing content refuses duplicate-location (consolidate stays the exit), uid-corruption unchanged. Settle the brief's unanswered questions: content identity (byte-equal vs uid+semantic hash), node_corpus attribution and NotPresent/Unknown with one holder absent, the retraction-discovery map, the address-map.yaml epoch format change. Supersede by citation the singular-map rule (derive.address_map), mount-citations decision 4 / cut-44 J17, and belief acceptance's singleton holder set (counts tried per holder). Absorb or sequence beliefs-354eae and beliefs-0e1acb. Global Constraints carry AGENTS.md's two cut obligations. Where to look: python/src/beliefs/world/derive.py address_map, corpus.py _one, world/read.py _address_map, world/live.py, docs/superpowers/specs/2026-10-01-mount-citations-design.md, docs/superpowers/specs/2026-10-02-belief-acceptance-design.md, science docs/specs/2026-09-30-science-commons-design.md §4.7 and §10. On completion, note the ruling on beliefs-81367e.
