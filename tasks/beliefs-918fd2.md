---
id: beliefs-918fd2
title: Design overlapping-publication reads from the brief
status: todo
priority: 2
size: l
complexity: high
process: planned
created: 2026-10-09T10:48:20Z
updated: 2026-10-09T13:48:15Z
depends: []
parent: beliefs-a286e7
tags: [publication, design]
source: docs/notes/2026-10-09-overlapping-publications-brief.md
agent: claude-code/claude-opus-5-5
---

Write the conformance-cut spec that lets a world hold one address in several live corpora: identical content reads once, differing content refuses duplicate-location (consolidate stays the exit), uid-corruption unchanged. Settle the brief's unanswered questions: content identity (byte-equal vs uid+semantic hash), node_corpus attribution and NotPresent/Unknown with one holder absent, the retraction-discovery map, the address-map.yaml epoch format change. Supersede by citation the singular-map rule (derive.address_map), mount-citations decision 4 / cut-44 J17, and belief acceptance's singleton holder set (counts tried per holder). Absorb or sequence beliefs-354eae and beliefs-0e1acb. Global Constraints carry AGENTS.md's two cut obligations. Where to look: python/src/beliefs/world/derive.py address_map, corpus.py _one, world/read.py _address_map, world/live.py, docs/superpowers/specs/2026-10-01-mount-citations-design.md, docs/superpowers/specs/2026-10-02-belief-acceptance-design.md, science docs/specs/2026-09-30-science-commons-design.md §4.7 and §10. Also rule on two things (added 2026-10-09 from a review of the brief): (a) the world views owners check (world/view.py:382), which refuses any uid held by two corpora whatever the address map says. That is the overlapping case itself and is separate from derive.address_maps uid-corruption rule, so rule whether equal-content holders are exempt and keep it distinct from real uid corruption; live.pys copy (beliefs-0e1acb) follows. (b) Origin selection for publication attribution: _selected_attributions (publish.py:232) groups by read.corpus_of(ref), one holder, and identical bytes can arrive through carriers with different provenance. Rule which holders provenance a republication attributes, independent of holder order, and include a publish → adopt → republish arm with the holders reordered whose attribution must not move. On completion, note the ruling on beliefs-81367e.

## Notes

- 2026-10-09T11:14:09Z (main): Ride-along candidate from scoping: beliefs-cb2a39 (an N2 arm for gather's observes-loop held filter) wakes when this cut plans its arms.
- 2026-10-09T13:48:14Z (main): Scope widened 2026-10-09 after a review of the brief: the view's owners check (world/view.py:382) and publication attribution's origin selection (publish.py:232), with a reordered-holders publish → adopt → republish arm
