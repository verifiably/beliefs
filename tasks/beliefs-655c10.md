---
id: beliefs-655c10
title: "World view: a witness that mapped content and manifests are unchanged since an epoch, so coordination-only drift can be proved inert"
status: shelved
priority: 2
created: 2026-10-01T22:21:05Z
updated: 2026-10-27T12:49:59Z
depends: []
parent: beliefs-03d483
tags: [world-read]
source: sci-dc0381
agent: claude-code/claude-opus-5-5
---

science's mount-citations consumer (science docs/specs/2026-10-01-mount-citations-consumer-design.md, decision 7 and limitation 2) treats any drift as epoch-stale, so every project/question/hypothesis write forces a new epoch before belief. A rule exempting drift made only of unmapped coordination records was rejected in plan review: open_world_view checks mapped addresses and uids, not content, and a mapped dataset facet revised beside a new coordination record was served changed while the rule called the drift inert. Needed: a cheap witness on WorldReadView (or the DriftReport) that every mapped record's content and every covered manifest are byte-identical to the epoch's capture. Measure first: sci-0d00d2 records how often coordination writes force a rebuild.

## Notes

- 2026-10-14T01:27:46Z (main): shelved: sci-0d00d2 records material coordination-only epoch rebuild frequency/cost, or beliefs-e02ef3 demonstrates a material mount-opening cost requiring a state witness. Then unshelve and re-scope using those results; settle canonical-projection versus raw-byte equality and the epoch's retained baseline before designing an API.
- 2026-10-14T01:27:49Z (main): scope: shelved; open_world_view still compares whole-corpus states and mapped address/uid identity, with no mapped-content witness; source sci-dc0381 decision 7's implementation amendment allows unmapped coordination kinds only at unchanged whole-corpus state. Reuse sci-0d00d2 and beliefs-e02ef3 measurements, not new research or a premature API. Equality needs clarification because world section 5 deliberately makes formatting inert; checked main 3e6a224; brief: docs/notes/2026-10-13-world-capture-safety-brief.md
- 2026-10-14T08:56:21Z (main): 2026-10-14 brief review: sci-0d00d2 committed only to total epoch build frequency and cost (consumer spec limitation 1; §7 assigns it limitations 1 and 3, not 2), so it was asked to tag each forced epoch by triggering write class; the wake condition is observable only through that tag. Re-scope hint: corpus_state_identity already computes a per-uid science.node-content.v1 identity (registry.py:763-772) and discards it; retaining it per epoch is a ready canonical-equality baseline.
- 2026-10-27T12:49:59Z (main): measured by science's second-project milestone (sci-0d00d2, record §6 M1): frozen schedule of 4 builds and 1 reuse; coordination-only rebuilds 2 (E3 after 4 project mints, E4 after 2 questions and 1 reuse), live 1.91 s and 1.94 s against evidence 1.44 s and initial 1.66 s (rehearsal replica in a synced tree: 8.03 s and 10.66 s against 7.69 s and 7.35 s). Each coordination-only rebuild costs about an evidence build; a next before the rebuild still renders, marking the stale row assessed-unevaluated (epoch-stale).
