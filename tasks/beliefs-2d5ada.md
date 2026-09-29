---
id: beliefs-2d5ada
title: Should the audit report a certification that retirement would change?
status: shelved
priority: 2
created: 2026-09-17T10:38:46Z
updated: 2026-09-29T22:50:05Z
depends: []
parent: beliefs-0c50ed
tags: [conformance, correction]
agent: codex/gpt-6
---

Slice 1 §11.5: corpus.lineage_snapshot returns retired empty and audit.check_lineage_basis reads the stored basis; retirement is a belief-input fact only. Decide whether an audit should report a dataset whose effective certification differs from its stored basis's.

## Notes

- 2026-09-19T18:53:40Z (design/correction-remainder): read at cut 34: unchanged by slice 2 (retirement is still a belief-input fact only); stays open
- 2026-09-29T22:50:05Z (main): shelved: A consumer needs an audit diagnostic comparing stored lineage certification with retirement-adjusted certification; provide one dataset and expected finding before designing it.
- 2026-09-29T22:50:05Z (main): scope: shelved; audit still checks stored basis against producers; retirement affects belief inputs and needs an explicit diagnostic contract; brief: docs/notes/2026-09-29-retraction-standing-backlog-brief.md
