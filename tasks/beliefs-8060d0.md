---
id: beliefs-8060d0
title: "Evidence aggregation beyond the unit-weight count: research the long-term direction"
status: todo
priority: 2
created: 2026-10-24T01:04:04Z
updated: 2026-10-24T01:44:53Z
depends: []
tags: [design, belief]
agent: claude-code/claude-opus-5-5
---

Why: science.belief.v1 is a signed count of independent directional assessments at unit weight, chosen deliberately as the smallest uncalibrated surface (belief-policy design §3, §8). It discards signal: a 1,000-patient and a 10-patient study count the same, effect size and precision are not read, inconclusive results move nothing, and partial dependence is treated as full. The successor design (beliefs-638318, shelved until a real belief needs unequal weights) would be easier to write well from research done ahead of it. Raised by the user 2026-10-23 after a guided tour of beliefs (vdocs-9ca77b). First milestone: the inventory of where signal is discarded. Then prior art and the graphical-model mapping, then one synthesis that recommends a direction. Research only: no kernel change, no successor policy design here. Related: beliefs-638318 (weighted-belief design), beliefs-8b26dc (observation-first direction), beliefs-a91959 (independent confirmation vs secondary analysis), beliefs-6cd85f (participant-overlap evidence).

## Notes

- 2026-10-24T01:44:53Z (main): attached: models-context-report.md (6246 bytes): What 2026-09-12 settled, what was handed to science and never filed, what is deferred, and proto-science's lessons
