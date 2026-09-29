---
id: beliefs-c800ef
title: "Roadmap: a world-wide standing fold at derivation, not capture"
status: idea
priority: 2
created: 2026-09-17T10:38:46Z
updated: 2026-09-29T22:50:05Z
depends: []
parent: beliefs-0c50ed
tags: [conformance, world-read]
agent: codex/gpt-6
---

Slice 1 §11.1: epoch._standing_retractions folds per corpus, so a counter-retraction moved apart from what it counters is upheld in both corpora; the evaluator refuses the disagreement (RetractionResolutionDisagreement) rather than compute a wrong standing. The remedy is a fold over the whole capture at derivation — a new version of the retraction-enumeration rule, its fixtures and receipt identity. Slice 2's or contract-cut's to schedule.

## Scoping context (2026-09-29)

Current capture still folds per corpus; the v1 rule only enumerates captured resolutions. The existing split-counter test expects RetractionResolutionDisagreement. Slice 2 §14.2 retained this limit; the closed correction lane is not reopened by this idea. Before design, inventory whether the captured target/resolution projection contains the graph and reference-resolution information needed at derivation. Research: beliefs-ae33ff. Handoff: docs/notes/2026-09-29-retraction-standing-backlog-brief.md. No implementation scope is established yet.

## Notes

- 2026-09-29T22:50:05Z (main): scope: briefed; confirmed the per-corpus fold and fail-closed split; research beliefs-ae33ff will inventory derivation inputs and identity obligations; brief: docs/notes/2026-09-29-retraction-standing-backlog-brief.md
