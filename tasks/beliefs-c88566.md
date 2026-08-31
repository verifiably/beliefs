---
id: beliefs-c88566
title: "Design coordination and view kinds (sub-project 1, coordination-addressing)"
status: todo
priority: 1
size: l
created: 2026-08-30T20:21:43Z
updated: 2026-08-31T15:06:31Z
depends: []
tags: [mutation-lane, coordination]
---

Brainstorm and spec the tier-3 coordination-addressing answer per the user/autonomy layer design §4.1–§4.2 and §8 item 1 (docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md): opaque project identity minted like a corpus_id and carried by the project record; (project identity, local id) addressing for every other view/coordination record; the coordination revision family (one or more predecessor tips; the at-commit rule under the root lock and the intent-position rule for operation-minted revisions; one standing tip or Refused(divergent-view)); the coordination contract compiled into ProfileSpec, independently versioned from the base contract; W11, W12, W13's two-projects negative; the foundations.md extension. Opening design decision: the view query language — small and closed, not a query engine. Joins the roadmap's mutation lane at the next re-rank.

## Notes

- 2026-08-31T10:20:15Z (coordination-and-view-kinds): Design brainstormed and banked: opaque local ids ruled; science.view-query.v1 closed grammar; family door on CorpusWriter; coordination contract pinned as coordination:<hex> in domains; W17/W18 added; cut 14 frozen in spec §9
- 2026-08-31T14:41:01Z (coordination-and-view-kinds): Review round 1: import-bundle refusal, coordination resolver over explicit corpus set, stored identity model (uid revisions, @ pins), contract-carried query vocabulary, kind-schema projection into compiled_identity, unscoped note retired (cut-5 amendment at discharge)
- 2026-08-31T15:06:31Z (coordination-and-view-kinds): Review round 2: facet-based Node mapping with dot-slug ids, kind/address continuity (PredecessorMismatch), cut 14 unfrozen until review ends with cut-5 handled by prospective succession, 13 kinds enumerated as stored.WORLD_KINDS, mint raises / read returns unified
