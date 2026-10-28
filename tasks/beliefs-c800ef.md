---
id: beliefs-c800ef
title: "Roadmap: a world-wide standing fold at derivation, not capture"
status: done
priority: 2
created: 2026-09-17T10:38:46Z
updated: 2026-10-28T19:58:40Z
completed: 2026-10-28T19:58:40Z
closed: 2026-10-28T19:58:40Z
depends: [beliefs-ae33ff, beliefs-918fd2]
parent: beliefs-0c50ed
tags: [conformance, world-read]
model: claude-fable-5-1
agent: codex/gpt-6
---

Slice 1 §11.1: epoch._standing_retractions folds per corpus, so a counter-retraction moved apart from what it counters is upheld in both corpora; the evaluator refuses the disagreement (RetractionResolutionDisagreement) rather than compute a wrong standing. The remedy is a fold over the whole capture at derivation — a new version of the retraction-enumeration rule, its fixtures and receipt identity. Slice 2's or contract-cut's to schedule.

## Scoping context (2026-09-29)

Current capture still folds per corpus; the v1 rule only enumerates captured resolutions. The existing split-counter test expects RetractionResolutionDisagreement. Slice 2 §14.2 retained this limit; the closed correction lane is not reopened by this idea. Before design, inventory whether the captured target/resolution projection contains the graph and reference-resolution information needed at derivation. Research: beliefs-ae33ff. Handoff: docs/notes/2026-09-29-retraction-standing-backlog-brief.md. No implementation scope is established yet.

## Notes

- 2026-09-29T22:50:05Z (main): scope: briefed; confirmed the per-corpus fold and fail-closed split; research beliefs-ae33ff will inventory derivation inputs and identity obligations; brief: docs/notes/2026-09-29-retraction-standing-backlog-brief.md
- 2026-10-17T13:01:48Z (main): scope: briefed; re-checked at 4580964: epoch._standing_retractions (world/epoch.py:1262) still folds per corpus and test_world_standing.py:189 still expects RetractionResolutionDisagreement; recorded the wait on research beliefs-ae33ff as a dep edge (it was named only in that task's Ideas it wakes); brief: docs/notes/2026-09-29-retraction-standing-backlog-brief.md
- 2026-10-28T13:14:37Z (design/918fd2-overlapping-publications): finding from beliefs-ae33ff via the overlapping-publications design (beliefs-918fd2, accepted e14315c, §4.5): the v1 rule input carries the node-arm graph (authored target ref plus every live and deprecated address across corpora) but not the target arm, which resolution cannot infer because route identities are authored strings; so the successor rule retraction-enumeration v2 takes a versioned input (science.rule-input.v2 = v1 projection plus arm per retraction member), the version held with the rule in rule.yaml and in its identity, read at build and validation; v1 input, fixtures, identities, subject domain and closure digest unchanged. Scoped to that design's cut; stays open until the v2 rule lands. Brief amendment: docs/notes/2026-09-29-retraction-standing-backlog-brief.md (2026-10-28).
- 2026-10-28T17:14:41Z (design/918fd2-overlapping-publications): ruling complete: cut 48 (beliefs-918fd2) ships the world-wide standing fold at derivation as the retraction-enumeration v2 rule (rules_v1/retraction_v2.py over science.rule-input.v2, v1 untouched); the test binding helpers and science's rebinding (filed) select v2. The moved counter is overturned under v2 (TestTheSplit); this record stays open for the user's call on closing it
- 2026-10-28T19:58:40Z (main): done
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T19:58:40Z (main): Landed by cut 48 (beliefs-918fd2): the world-wide standing fold runs at derivation as the retraction-enumeration v2 rule over science.rule-input.v2 (v1 untouched); the moved counter is overturned under v2 (TestTheSplit, BI-5's durable twin) and the shipped test bindings and science's rebinding (sci-73c80e) select v2. Closed at the user's direction
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
